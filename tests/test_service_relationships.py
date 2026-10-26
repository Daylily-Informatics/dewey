from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from dewey_service.service import DeweyConflictError, DeweyNotFoundError, DeweyService
from dewey_service.tapdb_backend import EXTERNAL_OBJECT_TEMPLATE
from tests.support.sharing_v12_fakes import OWNER, READER, Harness, actor


def _managed_share_harness() -> Harness:
    harness = Harness()
    harness.backend.find_by_json_field = lambda session, *, template_code, field, value: next(
        (
            instance
            for instance in harness.rows
            if instance.type == template_code.split("/")[1]
            and instance.json_addl.get(field) == value
        ),
        None,
    )
    return harness


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
    with pytest.raises(HTTPException) as removal:
        service.remove_artifact_set_member(
            artifact_set_euid=artifact_set["artifact_set_euid"],
            artifact_euid=artifact["artifact_euid"],
            idempotency_key="idem-artifact-set-remove",
        )
    assert removal.value.status_code == 403
    assert "Deletion is disabled" in removal.value.detail

    assert add_code == 200
    assert updated["artifact_euids"] == [artifact["artifact_euid"]]
    assert updated["metadata"] == {"program": "oncology"}
    assert (
        service.get_artifact_set(artifact_set["artifact_set_euid"])["artifact_set_type"] == "bundle"
    )
    assert service.list_artifact_sets(artifact_set_type="bundle")[0]["label"] == "Case Bundle"
    assert service.get_artifact_set(artifact_set["artifact_set_euid"])["artifact_euids"] == [
        artifact["artifact_euid"]
    ]

    with pytest.raises(DeweyNotFoundError):
        service.get_artifact_set("AS-999999")


def test_share_behaviors() -> None:
    harness = _managed_share_harness()
    service = harness.service
    artifact = harness.artifact()
    harness.query_rows = [artifact]
    now = datetime.now(timezone.utc)
    explicit_expiry = (now + timedelta(days=1)).isoformat()

    with actor():
        auto_code, auto_share = service.create_share(
            target_kind="artifact_object",
            target_euid=artifact.euid,
            name="download share",
            allowed_users=[READER.email],
            delivery_modes=["gateway"],
            idempotency_key="idem-share-auto",
        )
        explicit_code, explicit_share = service.create_share(
            target_kind="artifact_object",
            target_euid=artifact.euid,
            name="explicit share",
            allowed_users=[READER.email],
            delivery_modes=["gateway"],
            expires_at=explicit_expiry,
            idempotency_key="idem-share-explicit",
        )
        assert auto_code == explicit_code == 201
        assert auto_share["owner_email"] == OWNER.email
        assert explicit_share["expires_at"] == explicit_expiry
        deadline = datetime.fromisoformat(auto_share["expires_at"])
        assert (
            now + timedelta(days=30) <= deadline <= datetime.now(timezone.utc) + timedelta(days=30)
        )
        artifact_shares = service.list_shares(
            target_kind="artifact_object", target_euid=artifact.euid
        )
        assert {item["share_euid"] for item in artifact_shares} == {
            auto_share["share_euid"],
            explicit_share["share_euid"],
        }

    with actor(READER):
        access = service.create_share_access_package(auto_share["share_euid"])
        assert access == {
            "share_euid": auto_share["share_euid"],
            "delivery_mode": "gateway",
            "browser_path": f"/fetch/{auto_share['share_euid']}",
            "manifest_path": f"/fetch/{auto_share['share_euid']}?format=manifest",
            "archive_path": f"/fetch/{auto_share['share_euid']}?format=tar",
        }
        for removed_mode in ("presigned_s3", "presigned_s3_manifest"):
            with pytest.raises(HTTPException) as removed:
                service.create_share_access_package(
                    auto_share["share_euid"], delivery_mode=removed_mode
                )
            assert removed.value.status_code == 410

    with actor():
        revoked = service.revoke_share(
            auto_share["share_euid"], reason="recipient request", policy_revision=1
        )
        assert revoked["status"] == "revoked" and revoked["policy_revision"] == 2
        assert revoked["revoked_by"] == OWNER.subject
        with pytest.raises(ValueError, match="target_kind must be"):
            service.create_share(
                target_kind="report",
                target_euid=artifact.euid,
                allowed_users=[READER.email],
                idempotency_key="idem-share-bad-target",
            )
        with pytest.raises(ValueError, match="timezone-bearing ISO8601"):
            service.create_share(
                target_kind="artifact_object",
                target_euid=artifact.euid,
                allowed_users=[READER.email],
                expires_at="not-a-date",
                idempotency_key="idem-share-bad-expiry",
            )

    with actor(READER), pytest.raises(HTTPException) as denied:
        service.create_share_access_package(auto_share["share_euid"])
    assert denied.value.status_code == 403


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
        reference_target={"kind": "non_federated"},
    )
    replay_code, replay_external = service.create_external_object(
        external_system="bloom",
        external_object_type="sample",
        external_object_id="sample-123",
        external_uri="https://bloom.example.com/samples/123",
        metadata={"tenant": "acme"},
        idempotency_key="idem-external-object-2",
        reference_target={"kind": "non_federated"},
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
    assert service.backend.commits[-1] is False
    assert "external_graph_ref" not in relation
    assert service.backend.source_locks
    assert not service.backend.native_assertions  # Explicit non-federated target.

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


def test_generic_external_object_lane_reserves_labcore_owner_authority(
    service: DeweyService,
) -> None:
    with pytest.raises(DeweyConflictError, match="v2 Labcore owner API"):
        service.create_external_object(
            external_system="Labcore",
            external_object_type="Sequencing_Run",
            external_object_id="labcore-run-test",
            external_uri=None,
            metadata=None,
            idempotency_key="idem-reserved-labcore-object",
        )

    _, artifact = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-5",
        key="reports/labcore-owner-test.json",
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
        idempotency_key="idem-reserved-labcore-artifact",
    )
    with service.backend.session_scope(commit=True) as session:
        labcore_external = service.backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            name="labcore:sequencing_run:labcore-run-test",
            json_addl={
                "external_system": "labcore",
                "external_object_type": "sequencing_run",
                "external_object_id": "labcore-run-test",
                "external_identity_key": "labcore:sequencing_run:labcore-run-test",
            },
        )
        ordinary_external = service.backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            name="atlas:document:doc-test",
            json_addl={
                "external_system": "atlas",
                "external_object_type": "document",
                "external_object_id": "doc-test",
                "external_identity_key": "atlas:document:doc-test",
            },
        )

    for external_object_euid, relation_type in (
        (labcore_external.euid, "linked"),
        (ordinary_external.euid, "labcore_sequencing_run"),
    ):
        with pytest.raises(DeweyConflictError, match="v2 Labcore owner API"):
            service.attach_external_object_relation(
                target_type="artifact",
                target_euid=artifact["artifact_euid"],
                external_object_euid=external_object_euid,
                relation_type=relation_type,
                metadata=None,
                idempotency_key=f"idem-reserved-labcore-relation-{external_object_euid}",
            )
