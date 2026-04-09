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
    assert related_payload["items"][0]["share_reference_euid"] == share_reference["share_reference_euid"]
