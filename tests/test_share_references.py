from __future__ import annotations

import asyncio
import json
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.service import DeweyService


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


def _register_s3_artifact(
    service: DeweyService,
    *,
    bucket: str,
    key: str,
    idempotency_key: str,
) -> dict:
    _, artifact = service.register_artifact(
        artifact_type="pdf",
        storage_backend="s3",
        bucket=bucket,
        key=key,
        version_id=None,
        size=None,
        checksums=None,
        content_type=None,
        original_filename=None,
        producer_system=None,
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata=None,
        idempotency_key=idempotency_key,
    )
    return artifact


def _fake_retryable_error_share(fake_service) -> str:
    share_euid = "SH-ERROR"
    fake_service.share_references[share_euid] = {
        "share_reference_euid": share_euid,
        "target_type": "artifact",
        "target_euid": "AT-MISSING",
        "purpose": "download",
        "scope": "external",
        "transport": "presigned_s3",
        "status": "error",
        "starts_at": "2026-03-10T00:00:00Z",
        "expires_at": "2026-03-10T12:00:00Z",
        "access_url": None,
        "diagnostic": {
            "diagnostic_code": "storage_object_missing",
            "diagnostic_summary": "Target artifact object was not found in configured storage.",
            "last_checked_at": "2026-03-10T00:00:00Z",
            "retryable": True,
            "admin_detail": "private-bucket/sensitive-key.pdf",
        },
        "manifest": [],
        "connection": {},
        "member_count": 0,
        "transport_config": {},
        "issued_by": "operator@lsmc.bio",
        "recipient_email": None,
        "managed_access": True,
        "access_count": 0,
        "last_accessed_at": None,
        "revoked_at": None,
        "revoked_by": None,
        "created_at": "2026-03-10T00:00:00Z",
    }
    return share_euid


def test_missing_target_object_creates_error_with_sanitized_diagnostic(
    service: DeweyService,
) -> None:
    artifact = _register_s3_artifact(
        service,
        bucket="private-bucket",
        key="sensitive/path/report.pdf",
        idempotency_key="idem-share-missing-artifact",
    )

    status_code, share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="download",
        scope="external",
        expires_at=None,
        issued_by="operator@lsmc.bio",
        transport="presigned_s3",
        ttl_seconds=600,
        idempotency_key="idem-share-missing",
    )

    assert status_code == 201
    assert share["status"] == "error"
    assert share["access_url"] is None
    assert share["diagnostic"]["diagnostic_code"] == "storage_object_missing"
    assert share["diagnostic"]["retryable"] is True
    diagnostic_text = json.dumps(share["diagnostic"], sort_keys=True)
    assert "private-bucket" not in diagnostic_text
    assert "sensitive/path/report.pdf" not in diagnostic_text

    with pytest.raises(ValueError, match="share reference is error"):
        service.issue_share_reference_access(share["share_reference_euid"])


def test_retry_succeeds_after_repaired_storage_metadata(
    service: DeweyService,
) -> None:
    artifact = _register_s3_artifact(
        service,
        bucket="repair-bucket",
        key="reports/repaired.pdf",
        idempotency_key="idem-share-repair-artifact",
    )
    _, share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="download",
        scope="external",
        expires_at=None,
        issued_by="operator@lsmc.bio",
        transport="presigned_s3",
        ttl_seconds=600,
        idempotency_key="idem-share-repair",
    )
    assert share["status"] == "error"

    service._require_storage().seed_object(bucket="repair-bucket", key="reports/repaired.pdf")
    retried = service.retry_share_reference(
        share["share_reference_euid"],
        retried_by="admin@lsmc.bio",
    )

    assert retried["status"] == "active"
    assert retried["access_url"] == f"/share-references/{share['share_reference_euid']}"
    assert retried["diagnostic"] == {}
    access = service.issue_share_reference_access(share["share_reference_euid"])
    assert access["access_url"].startswith("https://downloads.example.com/")


def test_revoked_and_error_refs_do_not_generate_access_url(service: DeweyService) -> None:
    service._require_storage().seed_object(bucket="safe-bucket", key="reports/active.pdf")
    artifact = _register_s3_artifact(
        service,
        bucket="safe-bucket",
        key="reports/active.pdf",
        idempotency_key="idem-share-no-access-artifact",
    )
    _, active_share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="download",
        scope="external",
        expires_at=None,
        issued_by="operator@lsmc.bio",
        transport="presigned_s3",
        ttl_seconds=600,
        idempotency_key="idem-share-no-access",
    )
    service.revoke_share_reference(
        active_share["share_reference_euid"],
        revoked_by="operator@lsmc.bio",
        reason="cleanup",
    )
    with pytest.raises(ValueError, match="revoked"):
        service.issue_share_reference_access(active_share["share_reference_euid"])

    missing_artifact = _register_s3_artifact(
        service,
        bucket="missing-bucket",
        key="reports/missing.pdf",
        idempotency_key="idem-share-error-no-access-artifact",
    )
    _, error_share = service.create_share_reference(
        target_type="artifact",
        target_euid=missing_artifact["artifact_euid"],
        purpose="download",
        scope="external",
        expires_at=None,
        issued_by="operator@lsmc.bio",
        transport="presigned_s3",
        ttl_seconds=600,
        idempotency_key="idem-share-error-no-access",
    )
    with pytest.raises(ValueError, match="share reference is error"):
        service.issue_share_reference_access(error_share["share_reference_euid"])


def test_retry_share_reference_api_route(client, fake_service) -> None:
    share_euid = _fake_retryable_error_share(fake_service)

    retry = client.post(
        f"/api/v1/share-references/{share_euid}/retry",
        headers={"Authorization": "Bearer token-123"},
    )

    assert retry.status_code == 200
    payload = retry.json()
    assert payload["status"] == "active"
    assert payload["access_url"] == f"/share-references/{share_euid}"
    assert payload["diagnostic"] == {}


def test_search_ui_shows_sanitized_share_error_and_admin_retry(
    monkeypatch,
    client,
    fake_service,
) -> None:
    share_euid = _fake_retryable_error_share(fake_service)

    _login_user(monkeypatch, client)
    ordinary = client.get("/search", params={"scope": "share_reference", "q": share_euid})
    assert ordinary.status_code == 200
    assert "Target artifact object was not found in configured storage." in ordinary.text
    assert "private-bucket/sensitive-key.pdf" not in ordinary.text
    assert "Retry share" not in ordinary.text

    client.cookies.clear()
    _login_user(monkeypatch, client, groups=["platform-admin"])
    admin = client.get("/search", params={"scope": "share_reference", "q": share_euid})
    assert admin.status_code == 200
    assert "Retry share" in admin.text
    assert "private-bucket/sensitive-key.pdf" not in admin.text

    retried = client.post(
        f"/share-references/{share_euid}/retry",
        data={"return_to": "search"},
        follow_redirects=False,
    )
    assert retried.status_code == 303
    assert retried.headers["location"] == "/search"


def test_create_share_reference(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-art-1"},
        json={
            "artifact_type": "pdf",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "reports/report.pdf",
        },
    ).json()

    share = client.post(
        "/api/v1/share-references",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-1"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "purpose": "download",
            "scope": "external",
            "transport": "presigned_s3",
        },
    )
    assert share.status_code == 200
    payload = share.json()
    assert payload["status_code"] == 201
    assert payload["share_reference_euid"].startswith("SH-")
    assert payload["access_url"].startswith("/share-references/SH-")

    listed = client.get(
        f"/api/v1/artifacts/{artifact['artifact_euid']}/share-references",
        headers={"Authorization": "Bearer token-123"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    fetched = client.get(
        f"/api/v1/share-references/{payload['share_reference_euid']}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["share_reference_euid"] == payload["share_reference_euid"]

    access = client.post(
        f"/api/v1/share-references/{payload['share_reference_euid']}/access",
        headers={"Authorization": "Bearer token-123"},
    )
    assert access.status_code == 200
    assert access.json()["access_count"] == 1

    revoked = client.post(
        f"/api/v1/share-references/{payload['share_reference_euid']}/revoke",
        headers={"Authorization": "Bearer token-123"},
        json={"reason": "test cleanup"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"


def test_create_share_reference_prepares_external_recipient(
    monkeypatch,
    test_settings,
    fake_service,
) -> None:
    calls: list[dict] = []
    test_settings.external_broker_share_recipient_prepare_url = (
        "https://dev.login.lsmc.com/api/v1/dewey/share-recipient/prepare"
    )
    test_settings.external_broker_service_token = "dewey-service-token"

    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return {
                "recipient_email": "johnm@lsmc.life",
                "canonical_user_id": "email:johnm@lsmc.life",
                "verification_required": True,
                "cognito_default_email_suppressed": True,
                "invite_email": {"backend": "capture", "sent": True},
            }

    class _AsyncClient:
        def __init__(self, *, timeout: float, verify: object = True) -> None:
            self.timeout = timeout
            self.verify = verify

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, *, json: dict, headers: dict[str, str]) -> _Response:
            calls.append(
                {
                    "url": url,
                    "json": json,
                    "headers": headers,
                    "timeout": self.timeout,
                    "verify": self.verify,
                }
            )
            return _Response()

    monkeypatch.setattr("dewey_service.app.httpx.AsyncClient", _AsyncClient)
    app = create_app(settings=test_settings, service=fake_service)
    with TestClient(app, base_url="https://localhost:8914") as client:
        artifact = client.post(
            "/api/v1/artifacts",
            headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-art-ext"},
            json={
                "artifact_type": "pdf",
                "storage_backend": "s3",
                "bucket": "bucket-1",
                "key": "reports/report.pdf",
            },
        ).json()
        share = client.post(
            "/api/v1/share-references",
            headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-ext"},
            json={
                "target_type": "artifact",
                "target_euid": artifact["artifact_euid"],
                "purpose": "download",
                "scope": "external",
                "transport": "presigned_s3",
                "recipient_email": "JOHNM@LSMC.LIFE",
            },
        )

    assert share.status_code == 200
    payload = share.json()
    assert payload["broker_recipient"]["recipient_email"] == "johnm@lsmc.life"
    assert payload["broker_recipient"]["cognito_default_email_suppressed"] is True
    assert len(calls) == 1
    assert calls[0]["url"] == "https://dev.login.lsmc.com/api/v1/dewey/share-recipient/prepare"
    assert calls[0]["json"]["recipient_email"] == "JOHNM@LSMC.LIFE"
    assert calls[0]["json"]["share_ref_euid"] == payload["share_reference_euid"]
    assert calls[0]["json"]["share_url"].startswith("https://localhost:8914/share-references/")
    assert calls[0]["headers"] == {
        "Authorization": "Bearer dewey-service-token",
        "X-LSMC-Service-ID": "dewey",
    }


def test_create_share_reference_requires_broker_url_for_external_recipient(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-share-art-no-broker",
        },
        json={
            "artifact_type": "pdf",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "reports/report.pdf",
        },
    ).json()

    share = client.post(
        "/api/v1/share-references",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-no-broker"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "purpose": "download",
            "scope": "external",
            "transport": "presigned_s3",
            "recipient_email": "johnm@lsmc.life",
        },
    )

    assert share.status_code == 502
    assert "external_broker_share_recipient_prepare_url" in share.json()["detail"]


def test_atlas_result_lookup_share_reference_contract(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-art-atlas"},
        json={
            "artifact_type": "report",
            "storage_backend": "s3",
            "bucket": "bucket-2",
            "key": "results/atlas-result.json",
            "producer_system": "atlas",
            "producer_object_euid": "REL-123",
        },
    ).json()

    created = client.post(
        "/api/v1/share-references",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-share-atlas"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "purpose": "atlas-result-lookup",
            "scope": "external",
            "transport": "presigned_s3",
        },
    )
    assert created.status_code == 200
    share_reference = created.json()

    lookup = client.get(
        f"/api/v1/share-references/{share_reference['share_reference_euid']}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert lookup.status_code == 200
    lookup_payload = lookup.json()
    assert lookup_payload["share_reference_euid"] == share_reference["share_reference_euid"]
    assert lookup_payload["target_euid"] == artifact["artifact_euid"]

    related = client.get(
        f"/api/v1/artifacts/{artifact['artifact_euid']}/share-references",
        headers={"Authorization": "Bearer token-123"},
    )
    assert related.status_code == 200
    related_payload = related.json()
    assert related_payload["total"] == 1
    assert (
        related_payload["items"][0]["share_reference_euid"]
        == share_reference["share_reference_euid"]
    )
