from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse


def _login_user(monkeypatch, client, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@lsmc.bio",
            "sub": "sub-1",
            "cognito:groups": groups or ["dewey-readwrite"],
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


def test_literature_page_requires_login(client) -> None:
    response = client.get("/literature", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fliterature"
    assert 'data-section="Literature"' not in response.text


def test_literature_page_and_search_render_after_login(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    response = client.get("/literature", params={"q": "gene therapy"})
    assert response.status_code == 200
    assert 'data-section="Literature"' in response.text
    assert "/static/registry.js" in response.text
    search = client.post(
        "/api/v1/literature/search",
        json={"query": "gene therapy", "page": 1, "page_size": 20},
    )
    assert search.status_code == 200
    item = search.json()["items"][0]
    assert item["title"] == "Gene Therapy For Example Disease"
    assert item["pmid"] == "123456"
    assert item["already_in_dewey"] is False
    assert item["saved_by_me"] is False


def test_literature_search_and_save_routes(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    search = client.post(
        "/api/v1/literature/search",
        json={"query": "gene therapy", "page": 1, "page_size": 20},
    )
    assert search.status_code == 200
    assert search.json()["items"][0]["pmid"] == "123456"

    missing_idempotency = client.post(
        "/api/v1/literature/save",
        json={"pmid": "123456", "save_mode": "auto", "visibility_scope": "private"},
    )
    assert missing_idempotency.status_code == 400

    saved = client.post(
        "/api/v1/literature/save",
        headers={"Idempotency-Key": "lit-route-save-1"},
        json={
            "pmid": "123456",
            "save_mode": "auto",
            "visibility_scope": "restricted",
            "allowed_users": ["auditor@example.com"],
            "allowed_groups": ["dewey-readwrite"],
        },
    )
    assert saved.status_code == 200
    payload = saved.json()
    assert payload["status_code"] == 201
    assert payload["artifact"]["artifact_type"] == "literature"
    assert payload["literature_save"]["visibility_scope"] == "restricted"

    mine = client.get("/api/v1/literature/saves/mine")
    assert mine.status_code == 200
    assert mine.json()["total"] == 1
    assert mine.json()["items"][0]["artifact"]["pmid"] == "123456"

    patch_missing_idempotency = client.patch(
        f"/api/v1/literature/saves/{payload['literature_save']['literature_save_euid']}",
        json={"visibility_scope": "all_users"},
    )
    assert patch_missing_idempotency.status_code == 400

    patch = client.patch(
        f"/api/v1/literature/saves/{payload['literature_save']['literature_save_euid']}",
        headers={"Idempotency-Key": "lit-route-save-1-patch"},
        json={"visibility_scope": "all_users"},
    )
    assert patch.status_code == 200
    assert patch.json()["visibility_scope"] == "all_users"


def test_literature_search_page_shows_saved_badges(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    saved = client.post(
        "/api/v1/literature/save",
        headers={"Idempotency-Key": "lit-route-save-2"},
        json={"pmid": "123456", "save_mode": "auto", "visibility_scope": "all_users"},
    )
    assert saved.status_code == 200

    response = client.get(
        "/search",
        params={"q": "123456", "scope": "artifact", "page_size": 25},
    )
    assert response.status_code == 200
    assert 'data-section="Library"' in response.text
    search = client.post(
        "/api/v1/literature/search",
        json={"query": "123456", "page": 1, "page_size": 25},
    )
    assert search.status_code == 200
    item = search.json()["items"][0]
    assert item["title"] == "Gene Therapy For Example Disease"
    assert item["saved_by_me"] is True
    assert item["artifact_euid"] == saved.json()["artifact"]["artifact_euid"]


def test_literature_endpoints_return_503_when_unavailable(
    monkeypatch, client, fake_service
) -> None:
    fake_service.literature = None
    _login_user(monkeypatch, client)

    response = client.post(
        "/api/v1/literature/search",
        json={"query": "gene therapy", "page": 1, "page_size": 20},
    )
    assert response.status_code == 503
    assert "metapub" in response.json()["detail"].lower()


def test_literature_page_returns_503_for_runtime_config_failure(
    monkeypatch, client, fake_service
) -> None:
    class BrokenLiteratureAdapter:
        def search(self, **_kwargs):
            raise RuntimeError("NCBI key missing")

    fake_service.literature = BrokenLiteratureAdapter()
    _login_user(monkeypatch, client)

    response = client.get("/literature", params={"q": "PTEN"})

    assert response.status_code == 200
    assert 'data-section="Literature"' in response.text
    search = client.post(
        "/api/v1/literature/search",
        json={"query": "PTEN", "page": 1, "page_size": 20},
    )
    assert search.status_code == 503
    assert "Literature search is unavailable" in search.json()["detail"]
    assert "NCBI" in search.json()["detail"]
