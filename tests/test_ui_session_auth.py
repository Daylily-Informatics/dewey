from __future__ import annotations

from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import Settings
from dewey_service.store import InMemoryArtifactStore


def _app():
    settings = Settings(
        api_bearer_token="token-123",
        operator_username="operator",
        operator_password="pw-123",
        session_secret_key="session-secret",
    )
    return create_app(settings=settings, store=InMemoryArtifactStore())


def test_ui_requires_session_login() -> None:
    with TestClient(_app()) as client:
        response = client.get("/ui")
    assert response.status_code == 401


def test_login_sets_session_and_allows_ui() -> None:
    with TestClient(_app()) as client:
        login = client.post(
            "/login",
            data={"username": "operator", "password": "pw-123"},
            follow_redirects=False,
        )
        assert login.status_code == 303
        assert login.headers["location"] == "/ui"

        ui = client.get("/ui")
        assert ui.status_code == 200
        assert "Dewey Artifacts" in ui.text
