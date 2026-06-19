from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from starlette.routing import Mount, Route

from dewey_service.app import create_app
from dewey_service.settings import Settings
from tests.conftest import FakeDeweyService

REPO_ROOT = Path(__file__).resolve().parents[1]
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
EXCLUDED_RUNTIME_ROUTES: dict[tuple[str, str], str] = {
    (
        "GET",
        "/tapdb/",
    ): (
        "Owned by the embedded TapDB web app mounted via "
        "dewey_service.integrations.tapdb_ui.mount_tapdb_surfaces."
    ),
}


@dataclass(frozen=True)
class RuntimeRoute:
    method: str
    path: str
    surface: str


def _build_settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


def _build_dummy_tapdb_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def tapdb_home() -> HTMLResponse:
        return HTMLResponse("<h1>TapDB Embedded</h1>")

    return app


def _build_dummy_dag_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/dag/data")
    async def dag_graph_data() -> dict[str, str]:
        return {"kind": "native"}

    @router.get("/api/dag/search")
    async def dag_object_search() -> dict[str, str]:
        return {"kind": "search"}

    @router.get("/api/dag/external")
    async def dag_external_graph() -> dict[str, str]:
        return {"kind": "external"}

    @router.get("/api/dag/external/object")
    async def dag_external_object_detail() -> dict[str, str]:
        return {"kind": "external-object"}

    @router.get("/api/dag/object/{euid}")
    async def dag_object_detail(euid: str) -> dict[str, str]:
        return {"euid": euid, "system": "dewey"}

    return router


def _build_runtime_app(*, monkeypatch, embed_tapdb: bool) -> FastAPI:
    if embed_tapdb:
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
    else:
        monkeypatch.setattr(
            "dewey_service.integrations.tapdb_ui.resolve_tapdb_config_path",
            lambda settings: "",
        )

    return create_app(settings=_build_settings(), service=FakeDeweyService())


def _iter_runtime_routes(app: FastAPI) -> set[RuntimeRoute]:
    routes: set[RuntimeRoute] = set()
    docs_url = app.docs_url or ""
    redoc_url = app.redoc_url or ""
    openapi_url = app.openapi_url or ""

    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in sorted(route.methods):
                if method in {"HEAD", "OPTIONS"}:
                    continue
                surface = "api" if route.path.startswith("/api/") else "gui"
                routes.add(RuntimeRoute(method=method, path=route.path, surface=surface))
            continue

        if isinstance(route, Route):
            path = route.path
            if path == openapi_url or path == redoc_url or (docs_url and path.startswith(docs_url)):
                routes.add(RuntimeRoute(method="GET", path=path, surface="docs"))
            continue

        if isinstance(route, Mount) and route.path == "/static":
            routes.add(RuntimeRoute(method="GET", path="/static/favicon.svg", surface="static"))
        elif isinstance(route, Mount) and route.path == "/tapdb":
            routes.add(RuntimeRoute(method="GET", path="/tapdb/", surface="tapdb_mount"))

    return routes


def _sample_path(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value

    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{}")
        return "".join(parts)

    return None


def _normalize_request_path(raw: str) -> str:
    candidate = str(raw or "").strip()
    if "://" in candidate:
        match = re.match(r"^[a-zA-Z]+://[^/]+(.*)$", candidate)
        if match:
            candidate = match.group(1) or "/"
    if candidate.startswith("{}/"):
        candidate = candidate[2:]
    elif candidate.startswith("{}"):
        candidate = candidate[2:] or "/"
    return candidate.split("?", 1)[0]


def _iter_direct_request_samples() -> set[tuple[str, str]]:
    samples: set[tuple[str, str]] = set()
    for path in REPO_ROOT.glob("tests/**/*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue

            method = node.func.attr.upper()
            if method == "GOTO":
                method = "GET"
            if method not in HTTP_METHODS:
                continue

            sample = None
            if node.args:
                sample = _sample_path(node.args[0])
            if sample is None:
                for keyword in node.keywords:
                    if keyword.arg in {"url", "path"}:
                        sample = _sample_path(keyword.value)
                        if sample is not None:
                            break
            if sample is None:
                continue
            samples.add((method, _normalize_request_path(sample)))
    return samples


def _route_matches(route: RuntimeRoute, sample: tuple[str, str]) -> bool:
    sample_method, sample_path = sample
    if route.method != sample_method:
        return False
    pattern = re.escape(route.path)
    pattern = re.sub(r"\\\{[^{}]+\\\}", r"[^/]+", pattern)
    return re.fullmatch(pattern, sample_path) is not None


def test_runtime_route_inventory_covers_first_party_surfaces(monkeypatch) -> None:
    default_app = _build_runtime_app(monkeypatch=monkeypatch, embed_tapdb=False)
    embedded_app = _build_runtime_app(monkeypatch=monkeypatch, embed_tapdb=True)
    runtime_routes = _iter_runtime_routes(default_app) | _iter_runtime_routes(embedded_app)
    request_samples = _iter_direct_request_samples()

    missing: list[str] = []
    for route in sorted(runtime_routes, key=lambda item: (item.path, item.method)):
        if route.surface == "tapdb_mount":
            if (route.method, route.path) not in EXCLUDED_RUNTIME_ROUTES:
                missing.append(
                    f"{route.method} {route.path} [tapdb mount missing ownership exclusion]"
                )
            continue
        if any(_route_matches(route, sample) for sample in request_samples):
            continue
        missing.append(f"{route.method} {route.path} [{route.surface}]")

    assert missing == []


def test_docs_and_static_runtime_routes_have_direct_request_coverage(client) -> None:
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/api/v1/share-references" not in openapi.json()["paths"]
    assert "/api/v1/shares" in openapi.json()["paths"]
    assert "/api/v1/share-roots" in openapi.json()["paths"]

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "Swagger UI" in docs.text

    docs_redirect = client.get("/docs/oauth2-redirect")
    assert docs_redirect.status_code == 200
    assert "oauth2" in docs_redirect.text.lower()

    redoc = client.get("/redoc")
    assert redoc.status_code == 200
    assert "ReDoc" in redoc.text

    asset = client.get("/static/favicon.svg")
    assert asset.status_code == 200
    assert "image/svg+xml" in asset.headers["content-type"]


def test_tapdb_mount_exclusion_has_owner_note() -> None:
    owner_note = EXCLUDED_RUNTIME_ROUTES.get(("GET", "/tapdb/"), "")
    assert "TapDB" in owner_note
    assert "mount_tapdb_surfaces" in owner_note
