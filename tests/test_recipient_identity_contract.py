from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from daylily_auth_cognito.browser.session import (
    CognitoWebSessionConfig,
    configure_session_middleware,
    load_session_principal,
    store_session_principal,
)
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from dewey_service import auth, recipient_identity


def settings():
    return SimpleNamespace(
        external_broker_service_id="dewey",
        external_broker_service_token="fixture-service-credential",
        external_broker_ca_bundle="",
        external_broker_identity_url="https://login.example.test/api/v1/dewey/identity/introspect",
        external_broker_identity_mint_url="https://login.example.test/api/v1/dewey/identity/credentials",
        external_broker_identity_revoke_url="https://login.example.test/api/v1/dewey/identity/revoke",
        external_broker_share_login_url="https://login.example.test/auth/share",
        external_broker_login_url="https://login.example.test/auth/login",
        external_broker_callback_url="https://dewey.example.test/auth/lsmc/callback",
        cognito_group_role_map={},
    )


def binding(**changes):
    result = {
        "grant_id": "fixture-recipient-grant",
        "revision": 1,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "kind": "browser",
        "audience": "dewey",
        "active": True,
        "canonical_user_id": "fixture-canonical",
        "provider_subject": "fixture-provider-subject",
        "email": "recipient@example.test",
        "email_verified": True,
        "recipient_only": True,
    }
    result.update(changes)
    return result


def test_deep_fetch_login_uses_explicit_recipient_entry_and_keeps_destination():
    config = settings()
    request = Request(
        {"type": "http", "method": "GET", "path": "/auth/login", "headers": [], "session": {}}
    )
    target = "/fetch/fixture-share/report.html?view=detail"
    response = auth.start_external_broker_login(request, settings=config, next_path=target)
    parsed = urlparse(response.headers["location"])
    assert parsed.path == "/auth/share"
    assert parse_qs(parsed.query)["next"] == [target]
    assert request.session[auth._EXTERNAL_BROKER_NEXT_KEY] == target
    account = auth.start_external_broker_login(
        request, settings=config, next_path="/recipient/account"
    )
    assert urlparse(account.headers["location"]).path == "/auth/share"
    response = auth.start_external_broker_login(request, settings=config, next_path="/ui")
    assert urlparse(response.headers["location"]).path == "/auth/login"


def test_recipient_projection_cannot_inherit_administrator_groups():
    config = settings()
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/auth/lsmc/callback",
            "headers": [],
            "app": SimpleNamespace(state=SimpleNamespace(settings=config)),
        }
    )
    user = {
        "canonical_user_id": "fixture-canonical",
        "email": "recipient@example.test",
        "email_verified": True,
        "verification_state": "verified",
        "groups": ["lsmc:global-admin"],
        "recipient_identity": binding(),
    }
    principal = auth.resolve_external_broker_principal(user, request)
    assert principal.roles == ["READ_ONLY"]
    assert principal.app_context["recipient_only"] is True


def test_bulky_broker_user_cookie_fits_browser_limit_and_roundtrips(monkeypatch):
    """Exercise real shared ASGI cookie serialization, not just a principal dict."""
    app = FastAPI()
    app.state.settings = settings()
    app.state.settings.share_session_generation = ""
    app.state.settings.validate_cognito_email_domain = lambda email: (True, "")
    config = CognitoWebSessionConfig(
        domain="login.example.test",
        client_id="dewey",
        redirect_uri="https://dewey.example.test/auth/lsmc/callback",
        logout_uri="https://dewey.example.test",
        public_base_url="https://dewey.example.test",
        session_secret_key="fixture-session-signing-key",
        session_cookie_name="__Host-dewey_session",
        server_instance_id="fixture-server-instance",
        auth_mode="external_broker",
    )
    app.state.web_session_config = config
    configure_session_middleware(app, config)
    current_binding = binding(recipient_only=False)
    user = {
        "canonical_user_id": "fixture-canonical",
        "email": "recipient@example.test",
        "email_verified": True,
        "verification_state": "verified",
        "display_name": "Fixture administrator",
        "groups": ["lsmc:global-admin", "lsmc:internal-user"],
        "providers": [
            {"provider": "fixture", "subject": "provider-history-" + str(i)} for i in range(80)
        ],
        "service_entitlements": [
            {"service": "dewey", "roles": ["admin"], "groups": ["dewey-admin"]}
        ],
        "preferences": {"fixture": "x" * 5000},
        "audit_metadata": {"fixture": "y" * 5000},
    }

    async def handoff(**kwargs):
        return {"user": user, "recipient_identity": current_binding}

    def native_binding(request, session_config, **kwargs):
        principal = load_session_principal(request)
        store_session_principal(
            request,
            session_config,
            replace(
                principal,
                app_context={
                    **principal.app_context,
                    "dewey_session_binding_euid": "fixture-session-binding",
                },
            ),
        )

    monkeypatch.setattr(auth, "exchange_external_broker_handoff", handoff)
    monkeypatch.setattr("dewey_service.preview_sessions.establish_session_binding", native_binding)

    @app.get("/auth/login")
    def start(request: Request):
        return auth.start_external_broker_login(
            request, settings=app.state.settings, next_path="/session"
        )

    @app.get("/auth/lsmc/callback")
    async def callback(request: Request, code: str, state: str):
        return await auth.complete_external_broker_login(request, config, code=code, state=state)

    @app.get("/session")
    def session_view(request: Request):
        profile = auth._load_ui_profile(request)
        assert profile is not None
        return {"profile": profile, "app_context": load_session_principal(request).app_context}

    client = TestClient(app, base_url="https://dewey.example.test")
    started = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
    completed = client.get(
        "/auth/lsmc/callback",
        params={"code": "fixture-handoff", "state": state},
        follow_redirects=False,
    )
    assert completed.status_code == 303
    assert completed.headers["location"] == "/session"
    cookie = completed.headers["set-cookie"]
    assert len(cookie.encode("utf-8")) < 4096
    assert "secure" in cookie.lower() and "httponly" in cookie.lower()
    loaded = client.get("/session")
    assert loaded.status_code == 200
    result = loaded.json()
    assert set(result["profile"]["roles"]) == {"ADMIN", "READ_WRITE"}
    assert result["app_context"]["canonical_user"] == {"canonical_user_id": "fixture-canonical"}
    assert result["app_context"]["recipient_identity"] == current_binding
    assert result["app_context"]["recipient_only"] is False
    assert result["app_context"]["dewey_session_binding_euid"] == "fixture-session-binding"
    assert result["profile"]["identity_grant_id"] == current_binding["grant_id"]


@pytest.mark.parametrize(
    "change",
    [
        {"email_verified": False},
        {"active": False},
        {"audience": "another-service"},
        {"expires_at": "2020-01-01T00:00:00+00:00"},
        {"recipient_only": None},
    ],
)
def test_invalid_broker_identity_is_denied(monkeypatch, change):
    monkeypatch.setattr(recipient_identity, "_request", lambda *args: binding(**change))
    with pytest.raises(HTTPException) as failure:
        recipient_identity.verify_recipient_binding(
            settings(), grant_id="fixture-recipient-grant", revision=1
        )
    assert failure.value.status_code == 401


def test_identity_grant_and_revision_must_match_exactly(monkeypatch):
    monkeypatch.setattr(recipient_identity, "_request", lambda *args: binding(revision=2))
    with pytest.raises(HTTPException) as failure:
        recipient_identity.verify_recipient_binding(
            settings(), grant_id="fixture-recipient-grant", revision=1
        )
    assert failure.value.status_code == 401
