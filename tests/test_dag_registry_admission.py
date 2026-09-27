"""Offline middleware/dependency boundary checks; no TapDB or service requests."""
from hashlib import sha256
from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from dewey_service import auth
from dewey_service.integrations.tapdb_ui import build_dag_auth_dependency
from dewey_service.registry_access import RegistryPrincipalMiddleware

TOKEN = "dewey_dag_offline_boundary_check"


@pytest.fixture
def boundary(monkeypatch):
    profile = {"value": None}
    monkeypatch.setattr(auth, "_load_ui_profile", lambda request: profile["value"])
    app = FastAPI()
    settings = SimpleNamespace(
        dag_read_token_sha256=sha256(TOKEN.encode()).hexdigest(),
        dag_read_actor="dewey-dag-reader-offline",
        registry_internal_domains=[], registry_service_principals={}, api_tokens=lambda: set(),
    )
    app.state.settings = settings
    dependency = build_dag_auth_dependency(settings)
    reached = []

    async def dag(request: Request, actor=Depends(dependency)):
        reached.append(request.url.path)
        return {"actor": actor, "registry_principal": request.state.registry_principal is not None}

    for path in ("/api/dag/manifest", "/api/dag/v2/data", "/api/dag/v2/search", "/api/dag/v2/object/{euid}"):
        app.add_api_route(path, dag, methods=["GET", "POST"])
    app.add_api_route("/admin", dag, methods=["GET"])
    app.add_api_route("/api/v1/objects", dag, methods=["POST"])
    app.add_middleware(RegistryPrincipalMiddleware)
    with TestClient(app) as client:
        yield client, reached, profile


def test_verified_reader_reaches_all_canonical_get_dependencies_without_registry_role(boundary):
    client, reached, _ = boundary
    paths = ("/api/dag/manifest", "/api/dag/v2/data", "/api/dag/v2/search",
             "/api/dag/v2/object/persisted-object-fixture")
    for path in paths:
        response = client.get(path, headers={"Authorization": f"Bearer {TOKEN}"})
        assert response.status_code == 200
        assert response.json() == {"actor": {"username": "dewey-dag-reader-offline"}, "registry_principal": False}
    assert reached == list(paths)


def test_invalid_dedicated_reader_is_rejected_before_native_endpoint(boundary):
    client, reached, _ = boundary
    response = client.get("/api/dag/manifest", headers={"Authorization": "Bearer dewey_dag_wrong"})
    assert response.status_code == 401
    assert reached == []


def test_reader_does_not_gain_write_admin_or_legacy_route_admission(boundary):
    client, reached, _ = boundary
    headers = {"Authorization": f"Bearer {TOKEN}"}
    assert client.post("/api/dag/v2/data", headers=headers).status_code == 403
    assert client.post("/api/v1/objects", headers=headers).status_code == 403
    assert client.get("/admin", headers=headers, follow_redirects=False).status_code == 303
    assert client.get("/api/dag/data", headers=headers).status_code == 403
    assert reached == []


def test_existing_human_admin_admission_is_preserved(boundary):
    client, reached, profile = boundary
    profile["value"] = {"sub": "offline-admin", "email": "admin@example.test", "roles": ["ADMIN"], "groups": []}
    response = client.get("/api/dag/manifest")
    assert response.status_code == 200
    assert response.json() == {"actor": {"sub": "offline-admin"}, "registry_principal": True}
    assert reached == ["/api/dag/manifest"]
