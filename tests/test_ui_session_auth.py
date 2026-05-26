from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest
from daylily_auth_cognito.browser.session import CONFIG_STATE_KEY
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.auth import build_cognito_web_session_config
from dewey_service.settings import Settings


def _set_explicit_config_path(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "dewey-config-test.yaml"
    monkeypatch.setenv("DEWEY_CONFIG", str(config_path))


def _login_user(
    monkeypatch,
    client,
    *,
    email: str = "operator@lsmc.com",
    sub: str = "sub-1",
    name: str = "Operator Example",
    groups: list[str] | None = None,
) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": email,
            "sub": sub,
            "name": name,
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    redirect_url = login.headers["location"]
    parsed = urlparse(redirect_url)
    state = parse_qs(parsed.query)["state"][0]
    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["location"] == "/ui"


def test_html_login_redirect_preserves_next_path(client) -> None:
    response = client.get("/ui", headers={"accept": "text/html"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login?next=%2Fui"

    login_page = client.get(response.headers["location"])
    assert login_page.status_code == 200
    assert 'href="/auth/login?next=%2Fui"' in login_page.text


def test_root_redirects_to_ui(client) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui"


def test_ui_requires_session_login(client) -> None:
    response = client.get("/ui")
    assert response.status_code == 401


def test_cognito_callback_sets_session(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "Dewey Console" in ui.text
    assert "Quick Register" in ui.text
    assert "/admin" not in ui.text


def test_cognito_callback_rejects_disallowed_email_domain(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@gmail.com",
            "sub": "sub-1",
            "name": "Operator Example",
            "cognito:groups": ["dewey-readwrite"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    redirect_url = login.headers["location"]
    parsed = urlparse(redirect_url)
    state = parse_qs(parsed.query)["state"][0]
    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )

    assert callback.status_code in {302, 303}
    assert callback.headers["location"] == "/auth/error?reason=not_authorized"


@pytest.mark.parametrize(
    "params",
    [
        {"code": "code-1"},
        {"code": "code-1", "state": "wrong-state"},
    ],
)
def test_cognito_callback_rejects_missing_or_invalid_state(monkeypatch, client, params) -> None:
    response = client.get("/auth/callback", params=params, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/error?reason=invalid_state"


def test_auth_error_page_renders(client) -> None:
    response = client.get("/auth/error", params={"reason": "invalid_state"})

    assert response.status_code == 403
    assert "Sign-in was blocked" in response.text


def test_auth_error_page_renders_human_readable_logout_misconfiguration(client) -> None:
    response = client.get(
        "/auth/error",
        params={"reason": "cognito_logout_misconfigured"},
    )

    assert response.status_code == 403
    assert "Dewey cleared your local session" in response.text


def test_auth_login_redirects_to_local_auth_error_when_cognito_is_misconfigured(
    monkeypatch, client
) -> None:
    monkeypatch.setattr(
        "dewey_service.app.start_browser_login",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("callback mismatch")),
    )

    response = client.get("/auth/login?next=/ui", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/error?reason=cognito_sign_in_misconfigured"


def test_session_expiration_redirects_to_auth_error(monkeypatch, client, test_settings) -> None:
    _login_user(monkeypatch, client)

    stale_config = build_cognito_web_session_config(
        settings=test_settings,
        server_instance_id="restart-2",
    )
    client.app.state.web_session_config = stale_config
    client.app.state.__dict__[CONFIG_STATE_KEY] = stale_config

    response = client.get("/ui", headers={"accept": "text/html"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/auth/error?reason=session_expired"


def test_dashboard_quick_register_infers_artifact_type_for_local_file(
    monkeypatch, client, fake_service
) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={"artifact_type": "n/a", "artifact_tags": "tumor urgent"},
        files=[("file_data", ("sample.vcf.gz", b"##fileformat=VCF", "application/gzip"))],
    )

    assert response.status_code == 200
    assert "Registered sample.vcf.gz as vcf." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "vcf"
    assert artifact["metadata"]["tags"] == ["tumor", "urgent"]

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert f'href="/artifacts/euid/{artifact["artifact_euid"]}"' in ui.text
    assert f'action="/artifacts/euid/{artifact["artifact_euid"]}/download"' in ui.text


def test_dashboard_quick_register_imports_public_url(monkeypatch, client, fake_service) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={
            "artifact_type": "n/a",
            "source_url": "https://example.com/results/report.pdf",
        },
    )

    assert response.status_code == 200
    assert "Imported https://example.com/results/report.pdf as pdf." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "pdf"
    assert artifact["import_mode"] == "copy"
    assert artifact["source_uri"] == "https://example.com/results/report.pdf"


def test_dashboard_quick_register_references_s3_uri(monkeypatch, client, fake_service) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={
            "artifact_type": "n/a",
            "source_s3_uri": "s3://demo-bucket/path/sample.bam",
        },
    )

    assert response.status_code == 200
    assert "Registered s3://demo-bucket/path/sample.bam as bam." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "bam"
    assert artifact["import_mode"] == "reference"
    assert artifact["storage_uri"] == "s3://demo-bucket/path/sample.bam"


def test_admin_session_exposes_admin_tab_and_page(monkeypatch, tmp_path, client) -> None:
    _set_explicit_config_path(monkeypatch, tmp_path)
    _login_user(monkeypatch, client, groups=["platform-admin"])

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "/admin" in ui.text

    admin = client.get("/admin")
    assert admin.status_code == 200
    assert "Dewey Admin" in admin.text
    assert "Operator Anomalies" in admin.text


def test_logout_clears_session_and_redirects_to_cognito(monkeypatch, client, test_settings) -> None:
    _login_user(monkeypatch, client)

    logout = client.post("/auth/logout", follow_redirects=False)
    assert logout.status_code == 303

    parsed = urlparse(logout.headers["location"])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "dewey-auth.example.com"
    assert parsed.path == "/logout"
    assert params["client_id"] == [test_settings.cognito_app_client_id]
    assert params["redirect_uri"] == [test_settings.cognito_redirect_uri.rstrip("/")]
    assert params["response_type"] == ["code"]
    assert params["state"][0]

    ui = client.get("/ui")
    assert ui.status_code == 401


def test_logout_get_clears_session_and_redirects_to_cognito(
    monkeypatch, client, test_settings
) -> None:
    _login_user(monkeypatch, client)

    logout = client.get("/auth/logout", follow_redirects=False)
    assert logout.status_code == 303

    parsed = urlparse(logout.headers["location"])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "dewey-auth.example.com"
    assert parsed.path == "/logout"
    assert params["client_id"] == [test_settings.cognito_app_client_id]
    assert params["redirect_uri"] == [test_settings.cognito_redirect_uri.rstrip("/")]
    assert params["response_type"] == ["code"]


def test_plain_logout_post_clears_session_and_redirects_to_cognito(
    monkeypatch, client, test_settings
) -> None:
    _login_user(monkeypatch, client)

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 303

    parsed = urlparse(logout.headers["location"])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "dewey-auth.example.com"
    assert parsed.path == "/logout"
    assert params["client_id"] == [test_settings.cognito_app_client_id]
    assert params["redirect_uri"] == [test_settings.cognito_redirect_uri.rstrip("/")]
    assert params["response_type"] == ["code"]


def test_logout_redirects_to_local_auth_error_when_cognito_is_misconfigured(
    monkeypatch, client
) -> None:
    _login_user(monkeypatch, client)
    monkeypatch.setattr(
        "dewey_service.app.build_cognito_logout_url",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("logout mismatch")),
    )

    logout = client.post("/auth/logout", follow_redirects=False)

    assert logout.status_code == 303
    assert logout.headers["location"] == "/auth/error?reason=cognito_logout_misconfigured"


def test_two_browsers_can_keep_distinct_authenticated_sessions(monkeypatch, client) -> None:
    _login_user(
        monkeypatch,
        client,
        email="operator-a@lsmc.com",
        sub="sub-a",
        name="Operator A",
    )

    with TestClient(client.app, base_url="https://localhost:8914") as other_client:
        _login_user(
            monkeypatch,
            other_client,
            email="operator-b@daylilyinformatics.com",
            sub="sub-b",
            name="Operator B",
        )

        ui_a = client.get("/ui")
        ui_b = other_client.get("/ui")

        assert ui_a.status_code == 200
        assert ui_b.status_code == 200
        assert "operator-a@lsmc.com" in ui_a.text
        assert "operator-b@daylilyinformatics.com" not in ui_a.text
        assert "operator-b@daylilyinformatics.com" in ui_b.text
        assert "operator-a@lsmc.com" not in ui_b.text


def test_logout_from_one_browser_does_not_clear_the_other(monkeypatch, client) -> None:
    _login_user(
        monkeypatch,
        client,
        email="shared@lsmc.bio",
        sub="sub-shared",
        name="Shared Operator",
    )

    with TestClient(client.app, base_url="https://localhost:8914") as other_client:
        _login_user(
            monkeypatch,
            other_client,
            email="shared@lsmc.bio",
            sub="sub-shared",
            name="Shared Operator",
        )

        logout = client.post("/auth/logout", follow_redirects=False)
        assert logout.status_code == 303

        assert client.get("/ui").status_code == 401
        ui_other = other_client.get("/ui")
        assert ui_other.status_code == 200
        assert "shared@lsmc.bio" in ui_other.text


def test_external_broker_login_sets_admin_session(monkeypatch, tmp_path, fake_service) -> None:
    _set_explicit_config_path(monkeypatch, tmp_path)
    settings = Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        auth_mode="external_broker",
        external_broker_service_id="dewey",
        external_broker_login_url="https://dev.login.lsmc.com:8916/login",
        external_broker_handoff_exchange_url="https://dev.login.lsmc.com:8916/api/handoff/exchange",
        external_broker_service_token="dewey-service-token",
        external_broker_callback_url="https://localhost:8914/auth/lsmc/callback",
        external_broker_logout_url="https://dev.login.lsmc.com:8916/logout",
    )

    async def _exchange(*_args, **_kwargs):
        return {
            "user": {
                "email": "johnm@lsmc.com",
                "canonical_user_id": "user-johnm",
                "display_name": "John M",
                "groups": ["lsmc:global-admin"],
                "service_entitlements": [
                    {"service": "dewey", "roles": ["admin"]},
                ],
            }
        }

    monkeypatch.setattr("dewey_service.auth.exchange_external_broker_handoff", _exchange)
    app = create_app(settings=settings, service=fake_service)
    with TestClient(app, base_url="https://localhost:8914") as broker_client:
        login = broker_client.get("/auth/login?next=/admin", follow_redirects=False)
        assert login.status_code == 303
        parsed = urlparse(login.headers["location"])
        params = parse_qs(parsed.query)
        assert parsed.netloc == "dev.login.lsmc.com:8916"
        assert params["service"] == ["dewey"]
        assert params["callback_url"] == ["https://localhost:8914/auth/lsmc/callback"]

        callback = broker_client.get(
            "/auth/lsmc/callback",
            params={"code": "handoff-1", "state": params["state"][0]},
            follow_redirects=False,
        )
        assert callback.status_code == 303
        assert callback.headers["location"] == "/admin"

        admin = broker_client.get("/admin")
        assert admin.status_code == 200
        assert "Dewey Admin" in admin.text

        logout = broker_client.post("/auth/logout", follow_redirects=False)
        assert logout.status_code == 303
        assert logout.headers["location"] == "https://dev.login.lsmc.com:8916/logout"


def test_external_broker_callback_rejects_missing_roles(monkeypatch, fake_service) -> None:
    settings = Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        auth_mode="external_broker",
        external_broker_service_id="dewey",
        external_broker_login_url="https://dev.login.lsmc.com:8916/login",
        external_broker_handoff_exchange_url="https://dev.login.lsmc.com:8916/api/handoff/exchange",
        external_broker_service_token="dewey-service-token",
        external_broker_callback_url="https://localhost:8914/auth/lsmc/callback",
        external_broker_logout_url="https://dev.login.lsmc.com:8916/logout",
    )

    async def _exchange(*_args, **_kwargs):
        return {
            "user": {
                "email": "viewer@lsmc.com",
                "canonical_user_id": "user-viewer",
                "groups": [],
            }
        }

    monkeypatch.setattr("dewey_service.auth.exchange_external_broker_handoff", _exchange)
    app = create_app(settings=settings, service=fake_service)
    with TestClient(app, base_url="https://localhost:8914") as broker_client:
        login = broker_client.get("/auth/login", follow_redirects=False)
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        callback = broker_client.get(
            "/auth/lsmc/callback",
            params={"code": "handoff-1", "state": state},
            follow_redirects=False,
        )

    assert callback.status_code == 303
    assert callback.headers["location"] == "/auth/error?reason=not_authorized"
