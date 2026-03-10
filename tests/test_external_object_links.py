from __future__ import annotations


def test_create_external_object_and_relation(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-ext-art-1"},
        json={
            "artifact_type": "json",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "reports/report.json",
        },
    ).json()

    external_object = client.post(
        "/api/v1/external-objects",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-ext-obj-1"},
        json={
            "external_system": "atlas",
            "external_object_type": "document",
            "external_object_id": "DOC-1",
            "external_uri": "https://atlas.example/documents/DOC-1",
        },
    )
    assert external_object.status_code == 200
    external_object_euid = external_object.json()["external_object_euid"]

    relation = client.post(
        "/api/v1/external-object-relations",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-ext-rel-1"},
        json={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "external_object_euid": external_object_euid,
            "relation_type": "source_record",
        },
    )
    assert relation.status_code == 200

    list_relations = client.get(
        f"/api/v1/artifact/{artifact['artifact_euid']}/external-object-relations",
        headers={"Authorization": "Bearer token-123"},
    )
    assert list_relations.status_code == 200
    assert list_relations.json()["total"] == 1
