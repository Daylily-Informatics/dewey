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


def test_share_behaviors(service: DeweyService) -> None:
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

    auto_code, auto_share = service.create_share(
        target_kind="artifact_object",
        target_euid=artifact["artifact_euid"],
        targets=[],
        name="download share",
        purpose="download",
        owner_email="tester@example.com",
        allowed_users=[],
        allowed_domains=[],
        allowed_groups=[],
        delivery_modes=["presigned_s3"],
        expires_at=None,
        ttl_seconds=120,
        idempotency_key="idem-share-auto",
    )
    explicit_code, explicit_share = service.create_share(
        target_kind="artifact_object",
        target_euid=artifact["artifact_euid"],
        targets=[],
        name="explicit share",
        purpose=None,
        owner_email="tester@example.com",
        allowed_users=[],
        allowed_domains=[],
        allowed_groups=[],
        delivery_modes=["presigned_s3"],
        expires_at="2026-04-01T00:00:00Z",
        ttl_seconds=None,
        idempotency_key="idem-share-explicit",
    )

    assert auto_code == 201
    assert explicit_code == 201
    assert auto_share["owner_email"] == "tester@example.com"
    assert explicit_share["expires_at"] == "2026-04-01T00:00:00Z"
    opened_share = service.create_share_access_package(
        auto_share["share_euid"],
        delivery_mode="presigned_s3",
        actor_email="tester@example.com",
        actor_groups=[],
    )
    assert opened_share["signed_url"].startswith("https://downloads.example.com/")
    artifact_shares = service.list_shares(
        target_kind="artifact_object",
        target_euid=artifact["artifact_euid"],
    )
    assert {item["share_euid"] for item in artifact_shares} >= {
        auto_share["share_euid"],
        explicit_share["share_euid"],
    }
    access = service.create_share_access_package(
        auto_share["share_euid"],
        delivery_mode="presigned_s3",
        actor_email="tester@example.com",
        actor_groups=[],
    )
    assert access["signed_url"].startswith("https://downloads.example.com/")
    assert service.get_share(auto_share["share_euid"])["access_count"] == 2
    revoked = service.revoke_share(
        auto_share["share_euid"],
        revoked_by="tester@example.com",
        reason="recipient request",
    )
    assert revoked["status"] == "revoked"
    assert revoked["revoked_by"] == "tester@example.com"
    with pytest.raises(ValueError, match="not active"):
        service.create_share_access_package(
            auto_share["share_euid"],
            delivery_mode="presigned_s3",
            actor_email="tester@example.com",
            actor_groups=[],
        )

    with pytest.raises(ValueError, match="target_kind must be"):
        service.create_share(
            target_kind="report",
            target_euid="AT-1",
            targets=[],
            name=None,
            purpose=None,
            owner_email=None,
            allowed_users=[],
            allowed_domains=[],
            allowed_groups=[],
            delivery_modes=["presigned_s3"],
            expires_at=None,
            ttl_seconds=None,
            idempotency_key="idem-share-bad-target",
        )

    with pytest.raises(ValueError, match="expires_at must be ISO8601"):
        service.create_share(
            target_kind="artifact_object",
            target_euid=artifact["artifact_euid"],
            targets=[],
            name=None,
            purpose=None,
            owner_email="tester@example.com",
            allowed_users=[],
            allowed_domains=[],
            allowed_groups=[],
            delivery_modes=["presigned_s3"],
            expires_at="not-a-date",
            ttl_seconds=None,
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
