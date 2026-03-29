from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def _login_operator(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@example.com",
            "sub": "sub-1",
            "cognito:groups": ["operators"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    redirect_url = login.headers["location"]
    parsed = urlparse(redirect_url)
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )


def _service_headers() -> dict[str, str]:
    return {"Authorization": "Bearer token-123"}


def test_healthz_is_public(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_reports_backend_state(client) -> None:
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"]["status"] == "unknown"
    assert body["database"]["detail"] == "backend unavailable"


def test_privileged_observability_routes_require_auth(client) -> None:
    for path in [
        "/health",
        "/obs_services",
        "/api_health",
        "/endpoint_health",
        "/db_health",
        "/auth_health",
        "/api/anomalies",
        "/api/anomalies/ANM-000001",
    ]:
        response = client.get(path)
        assert response.status_code == 401, path


def test_obs_services_advertises_canonical_capabilities(client) -> None:
    response = client.get("/obs_services", headers=_service_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["projection"]["state"] == "ready"
    assert body["endpoints"] == [
        {"path": "/healthz", "auth": "none", "kind": "liveness"},
        {"path": "/readyz", "auth": "none", "kind": "readiness"},
        {"path": "/health", "auth": "operator_or_service_token", "kind": "summary"},
        {"path": "/obs_services", "auth": "operator_or_service_token", "kind": "discovery"},
        {"path": "/api_health", "auth": "operator_or_service_token", "kind": "api_rollup"},
        {"path": "/endpoint_health", "auth": "operator_or_service_token", "kind": "endpoint_rollup"},
        {"path": "/db_health", "auth": "operator_or_service_token", "kind": "database"},
        {"path": "/my_health", "auth": "authenticated_self", "kind": "self"},
        {"path": "/auth_health", "auth": "operator_or_service_token", "kind": "auth"},
        {"path": "/api/anomalies", "auth": "operator_or_service_token", "kind": "anomaly_list"},
        {
            "path": "/api/anomalies/{anomaly_id}",
            "auth": "operator_or_service_token",
            "kind": "anomaly_detail",
        },
    ]
    assert body["extensions"] == ["dewey.operator_ui", "dewey.anomalies_v1"]


def test_health_payload_is_service_token_accessible(client) -> None:
    client.get("/readyz")
    response = client.get("/health", headers=_service_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "dewey"
    assert body["projection"]["state"] == "ready"
    assert "database" in body["checks"]
    assert body["checks"]["database"]["detail"] == "backend unavailable"


def test_api_and_endpoint_rollups_capture_traffic(client) -> None:
    client.get("/api/v1/artifacts", headers=_service_headers())
    client.get("/health", headers=_service_headers())

    api_response = client.get("/api_health", headers=_service_headers())
    assert api_response.status_code == 200
    api_body = api_response.json()
    families = {item["family"]: item for item in api_body["families"]}
    assert "artifacts" in families
    assert families["artifacts"]["request_count"] >= 1

    endpoint_response = client.get("/endpoint_health", headers=_service_headers())
    assert endpoint_response.status_code == 200
    endpoint_body = endpoint_response.json()
    items = endpoint_body["items"]
    assert items
    route_templates = {(item["method"], item["route_template"]) for item in items}
    assert ("GET", "/api/v1/artifacts") in route_templates
    assert ("GET", "/health") in route_templates
    assert "/api/v1/artifacts/AT-123" not in {item["route_template"] for item in items}


def test_db_health_reports_probe_and_rollups(client) -> None:
    response = client.get("/db_health", headers=_service_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["projection"]["state"] == "ready"
    assert body["database"]["status"] == "unknown"
    assert body["database"]["latest"]["fingerprint"]


def test_my_health_requires_session_and_rejects_bearer(monkeypatch, client) -> None:
    bearer_only = client.get("/my_health", headers=_service_headers())
    assert bearer_only.status_code == 401

    _login_operator(monkeypatch, client)
    response = client.get("/my_health")
    assert response.status_code == 200
    body = response.json()
    assert body["principal"]["email"] == "operator@example.com"
    assert body["principal"]["auth_mode"] == "cognito"
    assert body["principal"]["service_principal"] is False


def test_auth_health_reports_session_and_service_token_modes(monkeypatch, client) -> None:
    client.get("/health", headers=_service_headers())
    _login_operator(monkeypatch, client)
    client.get("/ui")

    response = client.get("/auth_health", headers=_service_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["projection"]["state"] == "ready"
    assert body["auth"]["cognito_configured"] is True
    assert body["auth"]["status_counts"]["ok"] >= 2
    modes = {item["mode"] for item in body["auth"]["recent"]}
    assert "service_token" in modes
    assert "cognito" in modes


def test_observability_page_renders_for_logged_in_operator(monkeypatch, client) -> None:
    _login_operator(monkeypatch, client)
    client.get("/api/v1/artifacts", headers=_service_headers())

    response = client.get("/ui/observability")
    assert response.status_code == 200
    assert "Observability" in response.text
    assert "/obs_services" in response.text
    assert "/api/v1/artifacts" in response.text
