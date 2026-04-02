from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def _login_user(monkeypatch, client, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "daylily_cognito.web_session.exchange_authorization_code",
        lambda **kwargs: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {"email": "operator@example.com", "sub": "sub-1", "cognito:groups": groups or ["dewey-readwrite"]},
    )
    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )


def test_storage_verify_and_lock_routes(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-storage-art-1"},
        json={
            "artifact_type": "vcf",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "variants/sample.vcf.gz",
        },
    ).json()

    verify = client.post(
        f"/api/v1/artifacts/{artifact['artifact_euid']}/storage/verify",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-storage-verify-1"},
    )
    assert verify.status_code == 200
    assert verify.json()["storage_status"] == "verified"

    lock = client.post(
        f"/api/v1/artifacts/{artifact['artifact_euid']}/storage/lock",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-storage-lock-1"},
        json={"mode": "GOVERNANCE", "retain_until": "2027-01-01T00:00:00Z"},
    )
    assert lock.status_code == 200
    assert lock.json()["retention_mode"] == "GOVERNANCE"


def test_search_api_query_and_export(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-search-art-1"},
        json={
            "artifact_type": "report",
            "storage_backend": "s3",
            "bucket": "bucket-2",
            "key": "reports/case-report.pdf",
            "producer_system": "atlas",
            "producer_object_euid": "REL-1",
            "original_filename": "case-report.pdf",
        },
    ).json()
    client.post(
        "/api/v1/share-references",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-search-share-1"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "purpose": "download",
            "transport": "presigned_s3",
        },
    )

    query = client.post(
        "/api/search/v2/query",
        headers={"Authorization": "Bearer token-123"},
        json={"q": "case-report", "scopes": ["artifact"], "page": 1, "page_size": 25},
    )
    assert query.status_code == 200
    assert query.json()["total"] >= 1
    assert query.json()["items"][0]["record_type"] == "artifact"

    alias_query = client.post(
        "/api/v1/search/v2/query",
        headers={"Authorization": "Bearer token-123"},
        json={"q": "case-report", "scopes": ["artifact"], "page": 1, "page_size": 25},
    )
    assert alias_query.status_code == 200
    assert alias_query.headers["Deprecation"] == "true"
    assert alias_query.headers["Link"] == '</api/search/v2/query>; rel="successor-version"'

    export = client.post(
        "/api/v1/search/v2/export",
        headers={"Authorization": "Bearer token-123"},
        json={"format": "tsv", "scopes": ["artifact", "share_reference"], "max_rows": 25},
    )
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/tab-separated-values")
    assert "case-report.pdf" in export.text

    canonical_export = client.post(
        "/api/search/v2/export",
        headers={"Authorization": "Bearer token-123"},
        json={"format": "json", "scopes": ["artifact", "share_reference"], "max_rows": 25},
    )
    assert canonical_export.status_code == 200
    assert canonical_export.json()["row_count"] == 2
    assert {item["record_type"] for item in canonical_export.json()["items"]} == {
        "artifact",
        "share_reference",
    }


def test_search_page_renders_after_login(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    response = client.get("/search")
    assert response.status_code == 200
    assert "Artifact and Share Search" in response.text


def test_search_export_page_returns_authenticated_json_results(monkeypatch, client) -> None:
    client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-search-export-art-1"},
        json={
            "artifact_type": "report",
            "storage_backend": "s3",
            "bucket": "bucket-3",
            "key": "reports/operator-view.pdf",
            "original_filename": "operator-view.pdf",
        },
    )
    _login_user(monkeypatch, client)

    response = client.get(
        "/search/export",
        params={"format": "json", "q": "operator-view", "scope": "artifact", "max_rows": 10},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] == 1
    assert payload["items"][0]["record_type"] == "artifact"
    assert payload["items"][0]["name"] == "operator-view.pdf"
