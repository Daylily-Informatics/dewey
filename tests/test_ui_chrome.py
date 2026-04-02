from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import Settings


def _settings_with_deployment() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="https://dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        deployment_name="staging",
        deployment_color="#124e78",
        deployment_is_production=False,
    )


def test_login_page_renders_banner_and_favicon(fake_service) -> None:
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert "staging".upper() in response.text
    assert "#124e78" in response.text
    assert "/static/favicon.svg" in response.text
    assert "Dewey Access Login" in response.text


def test_ui_page_renders_banner_after_login(monkeypatch, fake_service) -> None:
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    monkeypatch.setattr(
        "daylily_cognito.web_session.exchange_authorization_code",
        lambda **kwargs: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@example.com",
            "sub": "sub-1",
            "cognito:groups": ["platform-admin"],
        },
    )

    with TestClient(app, base_url="https://localhost:8914") as client:
        login = client.get("/auth/login", follow_redirects=False)
        parsed = urlparse(login.headers["location"])
        state = parse_qs(parsed.query)["state"][0]
        callback = client.get(
            "/auth/callback",
            params={"code": "code-1", "state": state},
            follow_redirects=False,
        )
        assert callback.status_code == 302

        ui = client.get("/ui")
        admin = client.get("/admin")

    assert ui.status_code == 200
    assert "STAGING" in ui.text
    assert "/static/favicon.svg" in ui.text
    assert "/literature" in ui.text
    assert "/search" in ui.text
    assert "/ui/anomalies" in ui.text
    assert "/admin" in ui.text
    assert "Quick Register" in ui.text
    assert "Comprehensive Artifact Registry" in ui.text
    assert "dashboard_source_url" in ui.text
    assert "dashboard_source_s3_uri" in ui.text
    assert "Canonical file operations with registry discipline." not in ui.text
    assert admin.status_code == 200
    assert "Dewey Admin" in admin.text
    assert "Operator Anomalies" in admin.text
    assert "Open anomaly view" in admin.text
    assert "Managed Artifact Storage" in admin.text


def test_favicon_route_redirects_to_svg(fake_service) -> None:
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/favicon.ico", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/favicon.svg"
