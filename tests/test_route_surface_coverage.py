from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from starlette.routing import Mount, Route

from dewey_service.app import create_app
from dewey_service.settings import Settings
from tests.conftest import FakeDeweyService, explicit_application_settings

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
        **explicit_application_settings(),
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


def _build_runtime_app(*, monkeypatch, embed_tapdb: bool) -> FastAPI:
    # Both surfaces are required in Dewey 9; use the actual installed DAG v2 mount.
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


def _sample_path(expr: ast.AST, bindings=None, resolving=frozenset()) -> str | None:
    bindings = bindings or {}
    if isinstance(expr, ast.Name) and expr.id in bindings and expr.id not in resolving:
        return _sample_path(bindings[expr.id], bindings, resolving | {expr.id})
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value

    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append(_sample_path(value.value, bindings, resolving) or "{}")
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


def _function_bindings(node: ast.FunctionDef | ast.AsyncFunctionDef):
    cases = [{}]
    for decorator in node.decorator_list:
        if not (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "parametrize"
            and len(decorator.args) >= 2
        ):
            continue
        try:
            names = ast.literal_eval(decorator.args[0])
        except (ValueError, TypeError):
            continue
        if isinstance(names, str):
            names = [name.strip() for name in names.split(",")]
        rows = decorator.args[1]
        if not isinstance(names, (tuple, list)) or not isinstance(rows, (ast.Tuple, ast.List)):
            continue
        parameters = []
        for row in rows.elts:
            values = [row] if len(names) == 1 else getattr(row, "elts", [])
            if len(values) == len(names):
                parameters.append(dict(zip(names, values, strict=True)))
        if parameters:
            cases = [case | parameter for case in cases for parameter in parameters]
    assignments = {
        target.id: item.value
        for item in ast.walk(node)
        if isinstance(item, ast.Assign)
        for target in item.targets
        if isinstance(target, ast.Name)
    }
    return [case | assignments for case in cases]


def _request_samples_from_tree(tree: ast.AST) -> set[tuple[str, str]]:
    samples: set[tuple[str, str]] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for bindings in _function_bindings(function):
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                method = node.func.attr.upper()
                path_index = 0
                if method == "GOTO":
                    method = "GET"
                elif method == "REQUEST":
                    method_expr = (
                        node.args[0]
                        if node.args
                        else next(
                            (item.value for item in node.keywords if item.arg == "method"), None
                        )
                    )
                    method = (_sample_path(method_expr, bindings) or "").upper()
                    path_index = 1
                if method not in HTTP_METHODS:
                    continue
                sample = (
                    _sample_path(node.args[path_index], bindings)
                    if len(node.args) > path_index
                    else None
                )
                if sample is None:
                    for keyword in node.keywords:
                        if keyword.arg in {"url", "path"}:
                            sample = _sample_path(keyword.value, bindings)
                            if sample is not None:
                                break
                if sample is not None:
                    samples.add((method, _normalize_request_path(sample)))
    return samples


def _iter_direct_request_samples() -> set[tuple[str, str]]:
    samples: set[tuple[str, str]] = set()
    for path in REPO_ROOT.glob("tests/**/*.py"):
        samples.update(_request_samples_from_tree(ast.parse(path.read_text(encoding="utf-8"))))
    return samples


def test_request_inventory_resolves_explicit_cases_without_inventing_dynamic_routes():
    tree = ast.parse("""
@pytest.mark.parametrize("method,path", [("GET", "/known"), ("POST", "/known/item")])
def test_routes(client, method, path):
    client.request(method, path)
    alias = "/known/alias"
    client.get(alias)
    client.request("GET", route.path)
""")
    assert _request_samples_from_tree(tree) == {
        ("GET", "/known"),
        ("POST", "/known/item"),
        ("GET", "/known/alias"),
    }


@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("GET", "/account", 303),
        ("GET", "/add", 303),
        ("GET", "/admin/shares", 303),
        ("POST", "/api/v1/account/tokens", 401),
        ("POST", "/api/v1/account/tokens/token-fixture/revoke", 401),
        ("GET", "/api/v1/annotations/artifacts/artifact-fixture", 401),
        ("POST", "/api/v1/annotations/artifacts/artifact-fixture/access", 401),
        ("POST", "/api/v1/annotations/artifacts/artifact-fixture/context", 401),
        ("POST", "/api/v1/annotations/uploads/00000000-0000-4000-8000-000000000001", 401),
        ("POST", "/api/v1/annotations/uploads/00000000-0000-4000-8000-000000000001/complete", 401),
        ("POST", "/api/v1/annotations/uploads/00000000-0000-4000-8000-000000000001/resume", 401),
        ("POST", "/api/v1/records", 401),
        ("GET", "/api/v1/records/record-fixture", 401),
        ("PATCH", "/api/v1/records/record-fixture", 401),
        ("POST", "/api/v1/records/record-fixture/access", 401),
        ("GET", "/api/v1/records/record-fixture/activity", 401),
        ("POST", "/api/v1/records/record-fixture/archive", 403),
        ("GET", "/api/v1/records/record-fixture/contents", 401),
        ("GET", "/api/v1/records/record-fixture/members", 401),
        ("POST", "/api/v1/records/record-fixture/members", 401),
        ("DELETE", "/api/v1/records/record-fixture/members/member-fixture", 403),
        ("GET", "/api/v1/records/record-fixture/metadata", 401),
        ("PATCH", "/api/v1/records/record-fixture/owner", 401),
        ("PATCH", "/api/v1/records/record-fixture/permissions", 401),
        ("POST", "/api/v1/records/record-fixture/preview", 401),
        ("GET", "/api/v1/registry/defaults", 401),
        ("PATCH", "/api/v1/registry/defaults", 401),
        ("POST", "/api/v1/registry/search", 401),
        ("POST", "/api/v1/registry/search/counts", 401),
        ("GET", "/api/v1/registry/shares/share-fixture", 403),
        ("PATCH", "/api/v1/registry/shares/share-fixture", 403),
        ("GET", "/api/v1/registry/shares/share-fixture/activity", 403),
        ("GET", "/api/v1/registry/shares/share-fixture/contents", 403),
        ("POST", "/api/v1/registry/shares/share-fixture/grants/grant-fixture/revoke", 403),
        ("POST", "/api/v1/registry/shares/share-fixture/invite", 403),
        ("POST", "/api/v1/registry/shares/share-fixture/revoke", 403),
        ("POST", "/api/v1/registry/shares/share-fixture/preview", 403),
        ("POST", "/api/v1/registry/shares/share-fixture/preview/context-fixture/handoff", 403),
        ("POST", "/api/v1/share-roots", 403),
        ("POST", "/api/v1/share-roots/root-fixture/subsets", 403),
        ("POST", "/api/v1/shares/share-fixture/access-package", 403),
        ("GET", "/api/v1/shares/share-fixture/audit", 403),
        ("POST", "/api/v1/shares/share-fixture/revoke", 403),
        ("POST", "/api/v1/storage/access", 401),
        ("GET", "/api/v1/storage/buckets", 401),
        ("POST", "/api/v1/storage/deletions/preview", 403),
        ("POST", "/api/v1/storage/deletions/operation-fixture/execute", 403),
        ("GET", "/api/v1/storage/object", 401),
        ("GET", "/api/v1/storage/operations/operation-fixture", 401),
        ("POST", "/api/v1/storage/uploads", 401),
        ("POST", "/api/v1/storage/uploads/operation-fixture/abort", 403),
        ("POST", "/api/v1/storage/uploads/operation-fixture/complete", 401),
        ("PUT", "/api/v1/storage/uploads/operation-fixture/parts/1", 401),
        ("POST", "/api/v2/recipient/shares/share-fixture/preview", 403),
        ("GET", "/previews/retired-fixture.html", 410),
        ("GET", "/records/record-fixture", 303),
        ("GET", "/sets", 303),
        ("POST", "/share-roots/create", 403),
        ("POST", "/share-roots/root-fixture/subsets/create", 403),
        ("POST", "/shares/create", 403),
        ("GET", "/shares/share-fixture/files/target-fixture", 403),
        ("GET", "/storage", 303),
    ],
)
def test_uncovered_routes_reject_anonymous_before_backend_access(
    client, fake_service, method, path, expected
):
    """Explicit local requests prove denial/retirement, never count a discovered route as tested."""
    body = {}
    if path.startswith("/api/v1/annotations/"):
        if path.endswith(("/complete", "/resume")):
            body = {"upload_token": "annotation-upload-fixture"}
        elif path.endswith("/context") or "/uploads/" in path:
            body = {"target": {}, "target_url": "https://fixture.example.test/report"}
            if "/uploads/" in path:
                body.update(filename="note.txt", size=1)
    transactions = list(fake_service.backend.commits)
    response = client.request(method, path, json=body, follow_redirects=False)
    assert response.status_code == expected
    if expected == 303:
        destination = "/login" if path == "/admin/shares" else "/login?" + urlencode({"next": path})
        assert response.headers["location"] == destination
        assert "data-section=" not in response.text
    elif expected == 403:
        destructive = (
            method == "DELETE" or path.endswith(("/archive", "/abort")) or "/deletions/" in path
        )
        detail = (
            "Deletion is disabled in Dewey for all users, including administrators."
            if destructive
            else "Verified sharing ingress is required"
        )
        assert response.json() == {"detail": detail}
    elif expected == 410:
        assert response.headers["content-type"].startswith("text/html")
        assert response.text == (
            "Stored-issuer bearer report previews are retired; reopen through a managed share"
        )
    else:
        detail = (
            "A single human delegation credential is required"
            if path.startswith("/api/v1/annotations/")
            else "A verified Dewey principal is required"
        )
        assert response.json() == {"detail": detail}
    assert fake_service.backend.commits == transactions
    assert not fake_service.backend.instances
    assert not fake_service.artifacts and not fake_service.shares
    assert not fake_service.upload_sessions and not fake_service.idempotency


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

    assert missing == [], "\n".join(missing)


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
