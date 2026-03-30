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


def test_admin_page_links_to_anomaly_view(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {
            "email": "admin@example.com",
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
