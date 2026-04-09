from __future__ import annotations

import asyncio

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from dewey_service.app import create_app


def _build_dummy_tapdb_app():
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def tapdb_home() -> HTMLResponse:
        return HTMLResponse("<h1>TapDB Embedded</h1>")

    return app


def _build_dummy_dag_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/dag/data")
    async def dag_data() -> dict[str, object]:
        return {"items": [], "total": 0, "system": "dewey"}

    @router.get("/api/dag/external")
    async def dag_external() -> dict[str, object]:
        return {"items": [], "total": 0, "system": "dewey"}

    @router.get("/api/dag/external/object")
    async def dag_external_object() -> dict[str, object]:
        return {"items": [], "total": 0, "system": "dewey"}

    @router.get("/api/dag/object/{euid}")
    async def dag_object(euid: str) -> dict[str, str]:
        return {"euid": euid, "system": "dewey"}

    return router


def _configured_client(monkeypatch, test_settings, fake_service) -> TestClient:
    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_ui.resolve_tapdb_config_path",
        lambda settings: "/tmp/dewey-tapdb.yaml",
    )
    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_ui.create_tapdb_web_app",
        lambda **kwargs: _build_dummy_tapdb_app(),
    )
    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_ui.create_tapdb_dag_router",
        lambda **kwargs: _build_dummy_dag_router(),
    )
    app = create_app(settings=test_settings, service=fake_service)
    return TestClient(app, base_url="https://localhost:8914")


def test_obs_services_advertises_embedded_tapdb_dag(
    monkeypatch, test_settings, fake_service
) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        response = client.get(
            "/obs_services",
            headers={"Authorization": "Bearer token-123"},
        )
        assert response.status_code == 200
        body = response.json()
        paths = {item["path"] for item in body["endpoints"]}
        assert "/api/dag/object/{euid}" in paths
        assert "/api/dag/data" in paths
        assert "/api/dag/external" in paths
        assert "/api/dag/external/object" in paths
        assert "tapdb.dag_v1" in body["extensions"]


def test_dashboard_surfaces_tapdb_link_when_embedded(
    monkeypatch, test_settings, fake_service
) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        monkeypatch.setattr(
            "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
            lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
        )
        monkeypatch.setattr(
            "dewey_service.auth.decode_jwt_claims_noverify",
            lambda _token: {
                "email": "operator@lsmc.bio",
                "sub": "sub-1",
                "cognito:groups": ["operators"],
            },
        )

        login = client.get("/auth/login", follow_redirects=False)
        state = login.headers["location"].split("state=")[1].split("&")[0]
        client.get("/auth/callback", params={"code": "code-1", "state": state})

        response = client.get("/ui")
        assert response.status_code == 200
        assert "Open TapDB" in response.text
        assert 'href="/tapdb"' in response.text


def test_root_dag_router_uses_existing_dewey_auth(monkeypatch, test_settings, fake_service) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        response = client.get(
            "/api/dag/object/GX-123",
            headers={"Authorization": "Bearer token-123"},
        )
        assert response.status_code == 200
        assert response.json() == {"euid": "GX-123", "system": "dewey"}


def test_tapdb_mount_and_dag_routes_execute(monkeypatch, test_settings, fake_service) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        tapdb = client.get("/tapdb/")
        assert tapdb.status_code == 200
        assert "TapDB Embedded" in tapdb.text

        headers = {"Authorization": "Bearer token-123"}
        assert client.get("/api/dag/data", headers=headers).json()["system"] == "dewey"
        assert client.get("/api/dag/external", headers=headers).json()["system"] == "dewey"
        assert client.get("/api/dag/external/object", headers=headers).json()["system"] == "dewey"
