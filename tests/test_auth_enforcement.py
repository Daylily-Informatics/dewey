from __future__ import annotations


def test_api_requires_bearer_token(client) -> None:
    response = client.get("/api/v1/artifacts")
    assert response.status_code == 401


def test_api_accepts_valid_bearer_token(client) -> None:
    response = client.get("/api/v1/artifacts", headers={"Authorization": "Bearer token-123"})
    assert response.status_code == 200
    assert response.json()["items"] == []
