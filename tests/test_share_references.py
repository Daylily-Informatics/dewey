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
            "transport": "presigned_s3",
        },
    )
    assert share.status_code == 200
    payload = share.json()
    assert payload["status_code"] == 201
    assert payload["share_reference_euid"].startswith("SH-")
    assert payload["access_url"].startswith("https://downloads.example.com/")

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
