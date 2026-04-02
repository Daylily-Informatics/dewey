from __future__ import annotations


def test_artifact_detail_and_storage_routes(client) -> None:
    created = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-art-1"},
        json={
            "artifact_type": "vcf",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "variants/sample.vcf.gz",
            "metadata": {"source": "coverage-gap"},
        },
    )
    assert created.status_code == 200
    artifact_euid = created.json()["artifact_euid"]

    fetched = client.get(
        f"/api/v1/artifacts/{artifact_euid}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["artifact_euid"] == artifact_euid
    assert fetched.json()["metadata"] == {"source": "coverage-gap"}

    verified = client.post(
        f"/api/v1/artifacts/{artifact_euid}/storage/verify",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-art-verify"},
    )
    assert verified.status_code == 200
    assert verified.json()["storage_status"] == "verified"
    assert verified.json()["storage_verified_at"].startswith("2026-03-10T00:00:00")

    locked = client.post(
        f"/api/v1/artifacts/{artifact_euid}/storage/lock",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-art-lock"},
        json={"mode": "COMPLIANCE", "retain_until": "2028-01-01T00:00:00Z"},
    )
    assert locked.status_code == 200
    assert locked.json()["retention_mode"] == "COMPLIANCE"
    assert locked.json()["retain_until"] == "2028-01-01T00:00:00Z"


def test_upload_session_complete_route_round_trip(client) -> None:
    created = client.post(
        "/api/v1/artifacts/upload-sessions",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-upload-create"},
        json={
            "artifact_type": "report",
            "original_filename": "coverage-gap.pdf",
            "content_type": "application/pdf",
            "producer_system": "atlas",
            "producer_object_euid": "REL-coverage-gap",
        },
    )
    assert created.status_code == 200
    upload_token = created.json()["upload_token"]

    completed = client.post(
        f"/api/v1/artifacts/upload-sessions/{upload_token}/complete",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-gap-upload-complete",
        },
        json={"checksums": {"sha256": "abc123"}, "metadata": {"stage": "gap"}},
    )
    assert completed.status_code == 200
    payload = completed.json()
    assert payload["status_code"] == 201
    assert payload["artifact_type"] == "report"
    assert payload["original_filename"] == "coverage-gap.pdf"
    assert payload["import_mode"] == "upload"


def test_share_reference_lookup_and_external_object_relation_routes(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-share-art"},
        json={
            "artifact_type": "json",
            "storage_backend": "s3",
            "bucket": "bucket-2",
            "key": "reports/share-gap.json",
        },
    ).json()

    share = client.post(
        "/api/v1/share-references",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-gap-share-ref"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "purpose": "download",
            "scope": "external",
            "transport": "presigned_s3",
        },
    )
    assert share.status_code == 200
    share_reference_euid = share.json()["share_reference_euid"]

    fetched_share = client.get(
        f"/api/v1/share-references/{share_reference_euid}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched_share.status_code == 200
    assert fetched_share.json()["share_reference_euid"] == share_reference_euid

    listed_share_refs = client.get(
        f"/api/v1/artifacts/{artifact['artifact_euid']}/share-references",
        headers={"Authorization": "Bearer token-123"},
    )
    assert listed_share_refs.status_code == 200
    assert listed_share_refs.json()["total"] == 1

    external_object = client.post(
        "/api/v1/external-objects",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-gap-external-object",
        },
        json={
            "external_system": "atlas",
            "external_object_type": "document",
            "external_object_id": "DOC-GAP-1",
            "external_uri": "https://atlas.example/documents/DOC-GAP-1",
        },
    )
    assert external_object.status_code == 200
    external_object_euid = external_object.json()["external_object_euid"]

    relation = client.post(
        "/api/v1/external-object-relations",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-gap-external-relation",
        },
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "external_object_euid": external_object_euid,
            "relation_type": "source_record",
        },
    )
    assert relation.status_code == 200

    listed_relations = client.get(
        f"/api/v1/artifact/{artifact['artifact_euid']}/external-object-relations",
        headers={"Authorization": "Bearer token-123"},
    )
    assert listed_relations.status_code == 200
    assert listed_relations.json()["total"] == 1
