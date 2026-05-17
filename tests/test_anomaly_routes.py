from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import yaml

from dewey_service.defaults import build_default_config_template
from dewey_service.services.base import BaseDeweyService


def _login_operator(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@lsmc.bio",
            "sub": "sub-1",
            "cognito:groups": ["operators"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )


def _service_headers() -> dict[str, str]:
    return {"Authorization": "Bearer token-123"}


def test_anomaly_api_requires_bearer_token(client) -> None:
    response = client.get("/api/anomalies")
    assert response.status_code == 401


def test_anomaly_ui_requires_login(client) -> None:
    response = client.get("/ui/anomalies", follow_redirects=False)
    assert response.status_code == 401


def test_anomaly_api_and_ui_view_round_trip(monkeypatch, client) -> None:
    _login_operator(monkeypatch, client)

    response = client.get("/api/anomalies", headers=_service_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    anomaly = body["items"][0]
    assert anomaly["id"] == anomaly["anomaly_id"]
    assert anomaly["service"] == "dewey"
    assert anomaly["environment"]
    assert anomaly["fingerprint"] == anomaly["anomaly_identity_key"]
    assert anomaly["anomaly_id"].startswith("ANM-")
    assert anomaly["source_view_url"] == f"/ui/anomalies/{anomaly['anomaly_id']}"

    detail = client.get(f"/api/anomalies/{anomaly['anomaly_id']}", headers=_service_headers())
    assert detail.status_code == 200
    assert detail.json()["anomaly_id"] == anomaly["anomaly_id"]

    view = client.get("/ui/anomalies")
    assert view.status_code == 200
    assert "Anomalies" in view.text
    assert anomaly["title"] in view.text

    detail_view = client.get(f"/ui/anomalies/{anomaly['anomaly_id']}")
    assert detail_view.status_code == 200
    assert anomaly["title"] in detail_view.text
    assert anomaly["source_view_url"] in detail_view.text


def test_base_service_anomaly_response_includes_canonical_and_legacy_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        "dewey_service.services.base.get_settings",
        lambda: SimpleNamespace(deployment_name="lsdmc10", environment="development"),
    )
    service = BaseDeweyService(backend=SimpleNamespace())
    instance = SimpleNamespace(
        euid="ANM-123456",
        name="Readiness probe observed a bootstrap gap",
        created_dt=datetime.now(UTC),
        modified_dt=datetime.now(UTC),
        json_addl={
            "anomaly_identity_key": "dewey.readiness.bootstrap_gap",
            "category": "readiness",
            "severity": "medium",
            "status": "open",
            "title": "Readiness probe observed a bootstrap gap",
            "summary": "Canonical Dewey anomaly summary",
            "source": "readyz",
            "first_seen_at": "2026-03-10T00:00:00Z",
            "last_seen_at": "2026-03-10T00:00:00Z",
            "occurrence_count": 1,
            "redacted_context": {"database_status": "unknown"},
        },
    )

    payload = service._anomaly_response(instance)

    assert payload["id"] == "ANM-123456"
    assert payload["service"] == "dewey"
    assert payload["environment"] == "lsdmc10"
    assert payload["fingerprint"] == "dewey.readiness.bootstrap_gap"
    assert payload["summary"] == "Canonical Dewey anomaly summary"
    assert payload["anomaly_id"] == "ANM-123456"
    assert payload["anomaly_identity_key"] == "dewey.readiness.bootstrap_gap"


def test_admin_page_links_to_anomaly_view(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "admin@lsmc.bio",
            "sub": "sub-admin",
            "cognito:groups": ["platform-admin"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )

    response = client.get("/admin")
    assert response.status_code == 200
    assert "/ui/anomalies" in response.text
    assert "Operator Anomalies" in response.text


def test_admin_page_updates_managed_artifact_bucket(monkeypatch, client, tmp_path) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "admin@lsmc.bio",
            "sub": "sub-admin",
            "cognito:groups": ["platform-admin"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )

    config_path = tmp_path / "dewey-config-local.yaml"
    config_path.write_bytes(build_default_config_template(session_secret_key="test-session-secret"))
    monkeypatch.setattr("dewey_service.app.get_config_file_path", lambda: config_path)

    def _persist(bucket: str):
        from dewey_service.settings import persist_managed_storage_bucket

        return persist_managed_storage_bucket(bucket, config_path=config_path)

    monkeypatch.setattr("dewey_service.app.persist_managed_storage_bucket", _persist)

    response = client.post(
        "/admin/artifact-storage",
        data={"managed_storage_bucket": "dewey-artifacts-admin"},
    )

    assert response.status_code == 200
    assert "Managed artifact bucket updated" in response.text
    assert "dewey-artifacts-admin" in response.text
    assert client.app.state.settings.managed_storage_bucket == "dewey-artifacts-admin"
    assert getattr(client.app.state.service, "managed_storage_bucket") == "dewey-artifacts-admin"

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert raw["storage"]["managed_bucket"] == "dewey-artifacts-admin"
