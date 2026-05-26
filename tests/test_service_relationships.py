from __future__ import annotations

import pytest

from dewey_service.service import DeweyConflictError, DeweyNotFoundError, DeweyService


def test_artifact_set_member_lifecycle(service: DeweyService) -> None:
    _, artifact = service.register_artifact(
        artifact_type="vcf",
        storage_backend="s3",
        bucket="bucket-3",
        key="variants/sample.vcf.gz",
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
        idempotency_key="idem-artifact-set-artifact",
    )
    _, artifact_set = service.create_artifact_set(
        artifact_set_type="bundle",
        label=" Case Bundle ",
        description=" Primary bundle ",
        metadata={"program": "oncology"},
        idempotency_key="idem-artifact-set",
    )

    add_code, updated = service.add_artifact_set_member(
        artifact_set_euid=artifact_set["artifact_set_euid"],
        artifact_euid=artifact["artifact_euid"],
        idempotency_key="idem-artifact-set-add",
    )
    remove_code, removed = service.remove_artifact_set_member(
        artifact_set_euid=artifact_set["artifact_set_euid"],
        artifact_euid=artifact["artifact_euid"],
        idempotency_key="idem-artifact-set-remove",
    )

    assert add_code == 200
    assert updated["artifact_euids"] == [artifact["artifact_euid"]]
    assert updated["metadata"] == {"program": "oncology"}
    assert (
        service.get_artifact_set(artifact_set["artifact_set_euid"])["artifact_set_type"] == "bundle"
    )
    assert service.list_artifact_sets(artifact_set_type="bundle")[0]["label"] == "Case Bundle"
    assert remove_code == 200
    assert removed["artifact_euids"] == []

    with pytest.raises(DeweyNotFoundError):
        service.get_artifact_set("AS-999999")


def test_share_reference_behaviors(service: DeweyService) -> None:
    service._require_storage().seed_object(
        bucket="bucket-4", key="alignments/sample.bam", size=1024
    )
    _, artifact = service.register_artifact(
        artifact_type="bam",
        storage_backend="s3",
        bucket="bucket-4",
        key="alignments/sample.bam",
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
        idempotency_key="idem-share-artifact",
    )

    auto_code, auto_share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="download",
        scope=None,
        expires_at=None,
        issued_by="tester@example.com",
        transport="presigned_s3",
        ttl_seconds=120,
        idempotency_key="idem-share-auto",
    )
    explicit_code, explicit_share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose=None,
        scope="internal",
        expires_at="2026-04-01T00:00:00Z",
        issued_by=None,
        transport="presigned_s3",
        idempotency_key="idem-share-explicit",
    )

    assert auto_code == 201
    assert explicit_code == 201
    assert auto_share["issued_by"] == "tester@example.com"
    assert explicit_share["expires_at"] == "2026-04-01T00:00:00Z"
    assert auto_share["access_url"] == f"/share-references/{auto_share['share_reference_euid']}"
    opened_share = service.open_share_reference(auto_share["share_reference_euid"])
    assert opened_share["presigned_access_url"].startswith("https://downloads.example.com/")
    assert opened_share["access_count"] == 1
    assert (
        service.list_share_references(
            target_type="artifact",
            target_euid=artifact["artifact_euid"],
        )[0]["share_reference_euid"]
        == auto_share["share_reference_euid"]
    )
    access = service.issue_share_reference_access(
        auto_share["share_reference_euid"],
        accessed_by="recipient@example.com",
    )
    assert access["access_url"].startswith("https://downloads.example.com/")
    assert access["access_count"] == 2
    assert access["last_accessed_by"] == "recipient@example.com"
    revoked = service.revoke_share_reference(
        auto_share["share_reference_euid"],
        revoked_by="tester@example.com",
        reason="recipient request",
    )
    assert revoked["status"] == "revoked"
    assert revoked["revoked_by"] == "tester@example.com"
    assert revoked["access_url"] is None
    with pytest.raises(ValueError, match="revoked"):
        service.issue_share_reference_access(auto_share["share_reference_euid"])

    with pytest.raises(ValueError, match="target_type must be artifact or artifact_set"):
        service.create_share_reference(
            target_type="report",
            target_euid="AT-1",
            purpose=None,
            scope=None,
            expires_at=None,
            issued_by=None,
            transport="presigned_s3",
            idempotency_key="idem-share-bad-target",
        )

    with pytest.raises(ValueError, match="expires_at must be ISO8601"):
        service.create_share_reference(
            target_type="artifact",
            target_euid=artifact["artifact_euid"],
            purpose=None,
            scope=None,
            expires_at="not-a-date",
            issued_by=None,
            transport="presigned_s3",
            idempotency_key="idem-share-bad-expiry",
        )


def test_external_object_relation_lifecycle(service: DeweyService) -> None:
    _, artifact = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-5",
        key="reports/sample.json",
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
        idempotency_key="idem-external-artifact",
    )

    create_code, external_object = service.create_external_object(
        external_system="bloom",
        external_object_type="sample",
        external_object_id="sample-123",
        external_uri="https://bloom.example.com/samples/123",
        metadata={"tenant": "acme"},
        idempotency_key="idem-external-object",
    )
    replay_code, replay_external = service.create_external_object(
        external_system="bloom",
        external_object_type="sample",
        external_object_id="sample-123",
        external_uri="https://bloom.example.com/samples/123",
        metadata={"tenant": "acme"},
        idempotency_key="idem-external-object-2",
    )
    relation_code, relation = service.attach_external_object_relation(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        external_object_euid=external_object["external_object_euid"],
        relation_type="linked",
        metadata={"source": "sync"},
        idempotency_key="idem-external-relation",
    )
    existing_code, existing_relation = service.attach_external_object_relation(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        external_object_euid=external_object["external_object_euid"],
        relation_type="linked",
        metadata={"source": "sync"},
        idempotency_key="idem-external-relation-2",
    )

    assert create_code == 201
    assert replay_code == 200
    assert replay_external["external_object_euid"] == external_object["external_object_euid"]
    assert relation_code == 201
    assert existing_code == 200
    assert (
        existing_relation["external_object_relation_euid"]
        == relation["external_object_relation_euid"]
    )
    assert service.list_external_object_relations(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
    ) == [relation]

    with pytest.raises(ValueError, match="target_type must be artifact or artifact_set"):
        service.list_external_object_relations(target_type="report", target_euid="AT-1")

    with pytest.raises(DeweyConflictError, match="Idempotency-Key reuse"):
        service.attach_external_object_relation(
            target_type="artifact",
            target_euid=artifact["artifact_euid"],
            external_object_euid=external_object["external_object_euid"],
            relation_type="linked",
            metadata={"source": "changed"},
            idempotency_key="idem-external-relation",
        )
