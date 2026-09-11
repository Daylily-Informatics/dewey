"""Dewey auth and exact TapDB 10 mount contract, using the installed GUI/DAG factories."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException

from dewey_service.app import create_app
from dewey_service.integrations import tapdb_ui


def test_real_dag_v2_manifest_requires_auth_and_advertises_exact_paths(client):
    assert client.get("/api/dag/manifest").status_code == 401
    response = client.get("/api/dag/manifest", headers={"Authorization": "Bearer token-123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"] == "dag:v2"
    assert payload["service_id"] == "dewey"
    assert {item["path"] for item in payload["endpoints"]} == {
        "/api/dag/v2/object/{euid}",
        "/api/dag/v2/data",
        "/api/dag/v2/search",
    }
    assert payload["features"]["outbound_fetch"] is False
    for path in ("/api/dag/data", "/api/dag/search", "/api/dag/external"):
        assert client.get(path, headers={"Authorization": "Bearer token-123"}).status_code == 404


def test_actual_embedded_gui_rejects_anonymous_html_and_json(client):
    response = client.get("/tapdb/graph", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
    assert client.get("/tapdb/api/graph").status_code == 401


def test_observability_uses_successful_mount_manifest(client):
    response = client.get("/obs_services", headers={"Authorization": "Bearer token-123"})
    assert response.status_code == 200
    payload = response.json()
    assert "tapdb.dag_v2" in payload["extensions"]
    assert "tapdb.dag_v1" not in payload["extensions"]
    assert payload["tapdb_dag_contract_version"] == "dag:v2"
    assert payload["dag_v2"]["service_id"] == "dewey"
    assert "external_payload.tapdb_graph" not in payload.get("external_ref_models", [])


@pytest.mark.parametrize("config_path", ["", "relative.yaml", "/missing/dewey-config.yaml"])
def test_missing_config_fails_startup(test_settings, fake_service, config_path):
    test_settings.tapdb_config_path = config_path
    with pytest.raises(RuntimeError, match="config"):
        create_app(settings=test_settings, service=fake_service)


def test_failed_dag_mount_is_fatal(monkeypatch, test_settings):
    app = FastAPI()
    monkeypatch.setattr(
        tapdb_ui,
        "mount_tapdb_dag_surfaces",
        lambda *a, **k: SimpleNamespace(
            mounted=False,
            reason="invalid_config",
            diagnostic="scope mismatch",
        ),
    )
    with pytest.raises(RuntimeError, match="DAG v2 unavailable.*scope mismatch"):
        tapdb_ui.mount_tapdb_surfaces(app, settings=test_settings)
    assert not any(getattr(route, "path", None) == "/tapdb" for route in app.routes)


def test_dag_session_auth_projects_stable_subject(test_settings):
    import asyncio

    dependency = tapdb_ui.build_dag_auth_dependency(test_settings)
    result = asyncio.run(
        dependency({"service_principal": False, "profile": {"sub": "test-subject"}})
    )
    assert result == {"sub": "test-subject"}
    with pytest.raises(HTTPException):
        asyncio.run(
            dependency({"service_principal": False, "profile": {"email": "operator@example.test"}})
        )


def test_host_bridge_preserves_authenticated_role(monkeypatch, test_settings):
    monkeypatch.setattr(
        tapdb_ui,
        "require_ui_session",
        lambda request: {
            "sub": "test-subject",
            "email": "operator@example.test",
            "name": "Test Operator",
        },
    )
    monkeypatch.setattr(tapdb_ui, "profile_has_role", lambda profile, role: True)
    user = tapdb_ui.build_tapdb_host_bridge(test_settings).resolve_user(None)
    assert user["uid"] == "test-subject"
    assert user["role"] == "admin"


def test_gui_only_accepts_complete_authenticated_identity(monkeypatch):
    monkeypatch.setattr(
        tapdb_ui, "require_ui_session", lambda request: {"email": "operator@example.test"}
    )
    with pytest.raises(HTTPException):
        tapdb_ui._resolve_host_user(None)


def test_dag_v2_data_routes_reject_anonymous_requests(client):
    assert client.get("/api/dag/v2/data").status_code == 401
    assert client.get("/api/dag/v2/search").status_code == 401
    assert client.get("/api/dag/v2/object/persisted-object-test").status_code == 401


def test_graph_uses_native_gui_and_preferences_require_browser_session(client, monkeypatch):
    from tests.test_observability_contract import _login_operator

    assert client.get("/graph", follow_redirects=False).status_code == 401
    assert client.get("/api/v1/me/preferences").status_code == 401
    assert client.put("/api/v1/me/preferences", json={}).status_code == 401
    _login_operator(monkeypatch, client)
    graph = client.get("/graph")
    assert graph.status_code == 200
    assert 'src="/tapdb/graph"' in graph.text
    assert "/api/dag/data" not in graph.text
