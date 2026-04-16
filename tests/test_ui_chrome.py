from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import (
    Settings,
    _stable_deployment_color_hex,
    _stable_region_color_hex,
)


def _settings_with_deployment() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        deployment_name="510x2",
        deployment_color="#124e78",
        deployment_is_production=False,
        aws_region="us-east-1",
    )


def test_login_page_renders_chrome_and_footer(monkeypatch, fake_service) -> None:
    monkeypatch.setattr(
        "dewey_service.app.resolve_package_version",
        lambda: "9.9.9",
    )
    monkeypatch.setattr(
        "dewey_service.app.resolve_git_metadata",
        lambda _repo_root=None: {
            "branch": "codex/dewey-gui-chrome-scm",
            "tag": "1.2.0",
            "commit": "abc1234",
        },
    )
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert "510X2" in response.text
    assert _stable_deployment_color_hex("510x2") in response.text
    assert _stable_region_color_hex("us-east-1") in response.text
    assert "/static/favicon.svg" in response.text
    assert "Dewey Access Login" in response.text
    assert "Version" in response.text
    assert "9.9.9" in response.text
    assert "Branch" in response.text
    assert "codex/dewey-gui-chrome-scm" in response.text
    assert "Tag" in response.text
    assert "1.2.0" in response.text
    assert "Commit" in response.text
    assert "abc1234" in response.text


def test_create_app_requires_explicit_aws_profile_for_runtime_startup(monkeypatch) -> None:
    settings = _settings_with_deployment()
    settings.aws_profile = ""
    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    with pytest.raises(RuntimeError, match="AWS profile is required"):
        create_app(settings=settings)


def test_create_app_accepts_shell_aws_profile_when_config_blank(monkeypatch) -> None:
    settings = _settings_with_deployment()
    settings.aws_profile = ""
    captured: dict[str, str] = {}

    class FakeService:
        def __init__(self, backend, **kwargs):
            self.backend = backend
            self.storage_client = kwargs["storage_client"]

        def bootstrap(self) -> None:
            return

    class FakeStorageClient:
        def __init__(self, *, profile: str | None = None, region: str | None = None) -> None:
            captured["profile"] = str(profile or "")
            captured["region"] = str(region or "")

    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setattr("dewey_service.app.TapDBBackend", lambda app_username="dewey": object())
    monkeypatch.setattr("dewey_service.app.S3StorageClient", FakeStorageClient)
    monkeypatch.setattr("dewey_service.app.DeweyService", FakeService)
    monkeypatch.setattr("dewey_service.app.MetapubAdapter", lambda **kwargs: None)

    app = create_app(settings=settings)

    assert app.state.service.storage_client is not None
    assert captured == {"profile": "shell-profile", "region": "us-east-1"}


def test_ui_page_renders_chrome_after_login(monkeypatch, fake_service) -> None:
    monkeypatch.setattr(
        "dewey_service.app.resolve_package_version",
        lambda: "9.9.9",
    )
    monkeypatch.setattr(
        "dewey_service.app.resolve_git_metadata",
        lambda _repo_root=None: {
            "branch": "codex/dewey-gui-chrome-scm",
            "tag": "1.2.0",
            "commit": "abc1234",
        },
    )
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@lsmc.bio",
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
    assert "510X2" in ui.text
    assert _stable_deployment_color_hex("510x2") in ui.text
    assert _stable_region_color_hex("us-east-1") in ui.text
    assert "/static/favicon.svg" in ui.text
    assert "/literature" in ui.text
    assert "/artifacts/dag" in ui.text
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
    assert "Runtime Config" in admin.text
    assert "ui.show_environment_chrome" in admin.text
    assert "Version" in admin.text
    assert "9.9.9" in admin.text


def test_environment_chrome_can_be_disabled(monkeypatch, fake_service) -> None:
    settings = _settings_with_deployment()
    settings.show_environment_chrome = False
    monkeypatch.setattr(
        "dewey_service.app.resolve_package_version",
        lambda: "9.9.9",
    )
    monkeypatch.setattr(
        "dewey_service.app.resolve_git_metadata",
        lambda _repo_root=None: {
            "branch": "codex/dewey-gui-chrome-scm",
            "tag": "1.2.0",
            "commit": "abc1234",
        },
    )
    app = create_app(settings=settings, service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert "510X2" not in response.text
    assert _stable_region_color_hex("us-east-1") not in response.text
    assert "abc1234" in response.text


def test_favicon_route_redirects_to_svg(fake_service) -> None:
    app = create_app(settings=_settings_with_deployment(), service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/favicon.ico", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/favicon.svg"


def test_prod_login_page_renders_deployment_banner_when_enabled(
    monkeypatch, fake_service
) -> None:
    settings = _settings_with_deployment()
    settings.deployment_name = "prod"
    settings.deployment_is_production = True
    monkeypatch.setattr(
        "dewey_service.app.resolve_package_version",
        lambda: "9.9.9",
    )
    monkeypatch.setattr(
        "dewey_service.app.resolve_git_metadata",
        lambda _repo_root=None: {
            "branch": "codex/dewey-gui-chrome-scm",
            "tag": "unreleased",
            "commit": "abc1234",
        },
    )

    app = create_app(settings=settings, service=fake_service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert "PROD" in response.text
    assert _stable_region_color_hex("us-east-1") in response.text
    assert "abc1234" in response.text
