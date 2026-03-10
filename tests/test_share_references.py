from __future__ import annotations


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
        },
    )
    assert share.status_code == 200
    payload = share.json()
    assert payload["status_code"] == 201
    assert payload["share_reference_euid"].startswith("SH-")
