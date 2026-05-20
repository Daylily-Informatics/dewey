from __future__ import annotations

from fastapi.testclient import TestClient

from dewey_service.app import create_app


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


def test_create_share_reference_prepares_external_recipient(
    monkeypatch,
    test_settings,
    fake_service,
) -> None:
    calls: list[dict] = []
    test_settings.external_broker_share_recipient_prepare_url = (
        "https://dev.login.lsmc.com/api/v1/dewey/share-recipient/prepare"
    )

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
        def __init__(self, *, timeout: float, verify: bool = True) -> None:
            self.timeout = timeout
            self.verify = verify

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, *, json: dict) -> _Response:
            calls.append({"url": url, "json": json, "timeout": self.timeout})
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
