from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
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

    @router.get("/api/dag/search")
    async def dag_search() -> dict[str, object]:
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
        "dewey_service.integrations.tapdb_ui.create_tapdb_gui_app",
        lambda **kwargs: _build_dummy_tapdb_app(),
    )
    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_ui.create_tapdb_dag_router",
        lambda **kwargs: _build_dummy_dag_router(),
    )
    app = create_app(settings=test_settings, service=fake_service)
    return TestClient(app, base_url="https://localhost:8914")


def _login_operator(monkeypatch, client: TestClient) -> None:
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
        assert "/api/dag/search" in paths
        assert "/api/dag/external" in paths
        assert "/api/dag/external/object" in paths
        assert "tapdb.dag_v1" in body["extensions"]
        assert "object_search" in body["capabilities"]
        assert "typed_external_identifier" in body["external_ref_models"]
        assert body["tapdb_dag_contract_version"] == "dag:v1"


def test_dashboard_surfaces_tapdb_link_when_embedded(
    monkeypatch, test_settings, fake_service
) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        _login_operator(monkeypatch, client)

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
        assert client.get("/api/dag/search", headers=headers).json()["system"] == "dewey"
        assert client.get("/api/dag/external", headers=headers).json()["system"] == "dewey"
        assert client.get("/api/dag/external/object", headers=headers).json()["system"] == "dewey"


def test_tapdb_graph_page_renders_for_logged_in_user(
    monkeypatch, test_settings, fake_service
) -> None:
    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        _login_operator(monkeypatch, client)

        response = client.get("/graph")

    assert response.status_code == 200
    assert "Dewey TapDB Object Graph" in response.text
    assert "/api/dag/search" in response.text
    assert "hold z while wheeling to zoom" in response.text
    assert "Arrowheads point to parent nodes." in response.text


def test_tapdb_graph_template_requires_z_for_wheel_zoom_and_parent_arrows() -> None:
    template = Path("dewey_service/templates/tapdb_graph.html").read_text(encoding="utf-8")

    assert "configureCytoscapeInteractions(mount);" in template
    assert '"wheel"' in template
    assert "stopImmediatePropagation()" in template
    assert 'toLowerCase() === "z"' in template
    assert '"source-arrow-shape": "triangle"' in template
    assert '"target-arrow-shape": "none"' in template


def test_user_preferences_proxy_routes_call_broker(
    monkeypatch, test_settings, fake_service
) -> None:
    calls: list[tuple[str, str, dict[str, str], dict[str, str] | None]] = []

    class FakeAsyncClient:
        def __init__(self, *, timeout: float):
            assert timeout == 5.0

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str, *, headers: dict[str, str]) -> httpx.Response:
            calls.append(("GET", url, headers, None))
            return httpx.Response(
                200,
                json={"preferences": {"theme": "dark"}},
            )

        async def put(
            self, url: str, *, headers: dict[str, str], json: dict[str, str | None]
        ) -> httpx.Response:
            calls.append(("PUT", url, headers, json))
            return httpx.Response(204)

    monkeypatch.setenv(
        "LSMC_AUTH_BROKER_USER_PREFERENCES_URL",
        "https://login.example.test/api/users/{email}/preferences",
    )
    monkeypatch.setenv("LSMC_AUTH_BROKER_SERVICE_TOKEN", "broker-token")
    monkeypatch.setenv("LSMC_AUTH_BROKER_SERVICE_ID", "dewey")
    monkeypatch.setattr("dewey_service.app.httpx.AsyncClient", FakeAsyncClient)

    with _configured_client(monkeypatch, test_settings, fake_service) as client:
        _login_operator(monkeypatch, client)

        get_response = client.get("/api/v1/me/preferences")
        assert get_response.status_code == 200
        assert get_response.json()["preferences"]["theme"] == "dark"

        put_response = client.put("/api/v1/me/preferences", json={"theme": "light"})
        assert put_response.status_code == 200
        assert put_response.json()["preferences"]["theme"] == "dark"

    assert calls == [
        (
            "GET",
            "https://login.example.test/api/users/operator%40lsmc.bio/preferences",
            {"Authorization": "Bearer broker-token", "X-LSMC-Service-ID": "dewey"},
            None,
        ),
        (
            "PUT",
            "https://login.example.test/api/users/operator%40lsmc.bio/preferences",
            {"Authorization": "Bearer broker-token", "X-LSMC-Service-ID": "dewey"},
            {"theme": "light"},
        ),
        (
            "GET",
            "https://login.example.test/api/users/operator%40lsmc.bio/preferences",
            {"Authorization": "Bearer broker-token", "X-LSMC-Service-ID": "dewey"},
            None,
        ),
    ]
