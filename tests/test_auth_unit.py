from __future__ import annotations

import asyncio
import base64
import json
from types import SimpleNamespace

import pytest
from daylily_auth_cognito.browser.session import SessionPrincipal
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import dewey_service.auth as auth_mod
from dewey_service.rbac import Role
from dewey_service.settings import Settings


def _settings() -> Settings:
    return Settings(
        cognito_domain="auth.example.com",
        cognito_app_client_id="client-1",
        cognito_app_client_secret="secret-1",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


def _jwt(payload: dict[str, object]) -> str:
    raw = json.dumps(payload).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    return f"header.{encoded}.signature"


def test_decode_jwt_claims_noverify_handles_valid_and_invalid_tokens() -> None:
    assert auth_mod.decode_jwt_claims_noverify(_jwt({"email": "user@example.com"})) == {
        "email": "user@example.com"
    }
    assert auth_mod.decode_jwt_claims_noverify("not-a-jwt") == {}
    assert auth_mod.decode_jwt_claims_noverify("header.invalid.signature") == {}


def test_generate_state_returns_unique_nonce() -> None:
    first = auth_mod.generate_state()
    second = auth_mod.generate_state()

    assert first
    assert second
    assert first != second


def test_build_cognito_login_url_accepts_bare_host(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_build_authorization_url(**kwargs: str) -> str:
        seen.update(kwargs)
        return "https://login.example.com/oauth2/authorize"

    monkeypatch.setattr(auth_mod, "build_authorization_url", fake_build_authorization_url)

    url = auth_mod.build_cognito_login_url(settings=_settings(), state="state-123")

    assert url == "https://login.example.com/oauth2/authorize"
    assert seen == {
        "domain": "auth.example.com",
        "client_id": "client-1",
        "redirect_uri": "https://localhost:8914/auth/callback",
        "state": "state-123",
    }


def test_build_cognito_logout_url_includes_state() -> None:
    url = auth_mod.build_cognito_logout_url(settings=_settings(), state="logout-state")

    assert url.startswith("https://auth.example.com/logout?")
    assert "client_id=client-1" in url
    assert "redirect_uri=https%3A%2F%2Flocalhost%3A8914%2Fauth%2Fcallback" in url
    assert "response_type=code" in url
    assert "state=logout-state" in url


def test_exchange_code_success_and_error_wrapping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "abc", "access_token": "xyz"}),
    )

    payload = asyncio.run(auth_mod.exchange_code(settings=_settings(), code="code-123"))
    assert payload["id_token"] == "abc"

    def fail_exchange(**kwargs: str) -> dict[str, str]:
        raise RuntimeError("exchange failed")

    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        fail_exchange,
    )
    with pytest.raises(auth_mod.AuthError, match="exchange failed"):
        asyncio.run(auth_mod.exchange_code(settings=_settings(), code="bad-code"))


def test_require_api_auth_validates_tokens() -> None:
    dependency = auth_mod.require_api_auth(_settings())
    good = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dewey-dev-token")
    bad = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-token")

    assert dependency(good) == "dewey-dev-token"

    with pytest.raises(HTTPException) as missing_exc:
        dependency(None)
    assert missing_exc.value.status_code == 401
    assert missing_exc.value.detail == "Missing bearer token"

    with pytest.raises(HTTPException) as invalid_exc:
        dependency(bad)
    assert invalid_exc.value.status_code == 401
    assert invalid_exc.value.detail == "Invalid bearer token"


def test_require_ui_session_requires_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace(
        session={},
        app=SimpleNamespace(state=SimpleNamespace(settings=_settings())),
        state=SimpleNamespace(),
    )
    monkeypatch.setattr(
        auth_mod,
        "load_session_principal",
        lambda _request: SessionPrincipal(
            user_sub="sub-1",
            email="user@example.com",
            cognito_groups=["dewey-readwrite"],
            roles=[Role.READ_WRITE.value],
        ),
    )
    profile = auth_mod.require_ui_session(request)
    assert profile["email"] == "user@example.com"
    assert profile["roles"] == [Role.READ_WRITE.value]

    monkeypatch.setattr(auth_mod, "load_session_principal", lambda _request: None)
    with pytest.raises(HTTPException) as exc:
        auth_mod.require_ui_session(
            SimpleNamespace(
                session={},
                app=SimpleNamespace(state=SimpleNamespace(settings=_settings())),
                state=SimpleNamespace(),
            )
        )
    assert exc.value.status_code == 401
    assert exc.value.detail == "Login required"


def test_require_ui_admin_session_requires_admin_role(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace(
        session={},
        app=SimpleNamespace(state=SimpleNamespace(settings=_settings())),
        state=SimpleNamespace(),
    )
    monkeypatch.setattr(
        auth_mod,
        "load_session_principal",
        lambda _request: SessionPrincipal(
            user_sub="sub-1",
            email="user@example.com",
            cognito_groups=["platform-admin"],
            roles=[Role.ADMIN.value],
        ),
    )
    assert auth_mod.require_ui_admin_session(request)["email"] == "user@example.com"

    monkeypatch.setattr(
        auth_mod,
        "load_session_principal",
        lambda _request: SessionPrincipal(
            user_sub="sub-1",
            email="user@example.com",
            cognito_groups=["dewey-readwrite"],
            roles=[Role.READ_WRITE.value],
        ),
    )
    with pytest.raises(HTTPException) as exc:
        auth_mod.require_ui_admin_session(
            SimpleNamespace(
                session={},
                app=SimpleNamespace(state=SimpleNamespace(settings=_settings())),
                state=SimpleNamespace(),
            )
        )
    assert exc.value.status_code == 403


def test_resolve_operator_principal_accepts_allowed_email_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                settings=Settings(
                    cognito_domain="auth.example.com",
                    cognito_app_client_id="client-1",
                    cognito_app_client_secret="secret-1",
                    cognito_redirect_uri="https://localhost:8914/auth/callback",
                    cognito_logout_url="https://localhost:8914/login",
                )
            )
        )
    )
    monkeypatch.setattr(
        auth_mod,
        "decode_jwt_claims_noverify",
        lambda _token: {
            "email": "operator@lsmc.com",
            "sub": "sub-1",
            "name": "Operator",
            "cognito:groups": ["dewey-readonly"],
        },
    )

    principal = auth_mod.resolve_operator_principal({"id_token": "token"}, request)

    assert principal.email == "operator@lsmc.com"
    assert principal.roles == [Role.READ_ONLY.value]


def test_resolve_operator_principal_rejects_disallowed_email_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                settings=Settings(
                    cognito_domain="auth.example.com",
                    cognito_app_client_id="client-1",
                    cognito_app_client_secret="secret-1",
                    cognito_redirect_uri="https://localhost:8914/auth/callback",
                    cognito_logout_url="https://localhost:8914/login",
                )
            )
        )
    )
    monkeypatch.setattr(
        auth_mod,
        "decode_jwt_claims_noverify",
        lambda _token: {
            "email": "operator@gmail.com",
            "sub": "sub-1",
            "name": "Operator",
            "cognito:groups": ["dewey-readonly"],
        },
    )

    with pytest.raises(auth_mod.CognitoWebAuthError) as exc:
        auth_mod.resolve_operator_principal({"id_token": "token"}, request)

    assert exc.value.reason == "not_authorized"
