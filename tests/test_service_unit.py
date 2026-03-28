from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from dewey_service.service import DeweyConflictError, DeweyNotFoundError, DeweyService
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    SHARE_REFERENCE_TEMPLATE,
)


@dataclass
class _FakeInstance:
    uid: int
    euid: str
    template_code: str
    name: str
    json_addl: dict[str, Any]
    created_dt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_dt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    polymorphic_discriminator: str = "data_instance"


@dataclass
class _FakeLineage:
    parent_uid: int
    child_uid: int
    relationship_type: str
    is_deleted: bool = False


class _InMemoryBackend:
    def __init__(self) -> None:
        self.instances: dict[str, list[_FakeInstance]] = {}
        self.lineages: list[_FakeLineage] = []
        self.next_uid = 1
        self.next_by_prefix = {
            ARTIFACT_TEMPLATE: 1,
            ARTIFACT_SET_TEMPLATE: 1,
            SHARE_REFERENCE_TEMPLATE: 1,
            EXTERNAL_OBJECT_TEMPLATE: 1,
            EXTERNAL_OBJECT_RELATION_TEMPLATE: 1,
            IDEMPOTENCY_TEMPLATE: 1,
        }
        self.prefixes = {
            ARTIFACT_TEMPLATE: "AT",
            ARTIFACT_SET_TEMPLATE: "AS",
            SHARE_REFERENCE_TEMPLATE: "SH",
            EXTERNAL_OBJECT_TEMPLATE: "EX",
            EXTERNAL_OBJECT_RELATION_TEMPLATE: "ER",
            IDEMPOTENCY_TEMPLATE: "KDP",
        }

    @contextmanager
    def session_scope(self, commit: bool = False):
        yield self

    def ensure_templates(self, session) -> None:
        return

    def create_instance(
        self,
        session,
        *,
        template_code: str,
        name: str,
        json_addl: dict[str, Any],
        status: str = "active",
    ) -> _FakeInstance:
        prefix = self.prefixes[template_code]
        seq = self.next_by_prefix[template_code]
        self.next_by_prefix[template_code] += 1
        instance = _FakeInstance(
            uid=self.next_uid,
            euid=f"{prefix}-{seq:06d}",
            template_code=template_code,
            name=name,
            json_addl=dict(json_addl),
        )
        self.next_uid += 1
        self.instances.setdefault(template_code, []).append(instance)
        return instance

    def find_by_json_field(self, session, *, template_code: str, field: str, value: str):
        for instance in self.instances.get(template_code, []):
            if instance.is_deleted:
                continue
            if str(instance.json_addl.get(field)) == value:
                return instance
        return None

    def find_by_euid(self, session, *, template_code: str, euid: str, for_update: bool = False):
        for instance in self.instances.get(template_code, []):
            if not instance.is_deleted and instance.euid == euid:
                return instance
        return None

    def list_by_template(self, session, *, template_code: str, limit: int = 200):
        rows = [row for row in self.instances.get(template_code, []) if not row.is_deleted]
        rows.sort(key=lambda row: row.created_dt, reverse=True)
        return rows[:limit]

    def create_lineage(
        self,
        session,
        *,
        parent: _FakeInstance,
        child: _FakeInstance,
        relationship_type: str,
        name: str | None = None,
    ):
        for lineage in self.lineages:
            if (
                lineage.parent_uid == parent.uid
                and lineage.child_uid == child.uid
                and lineage.relationship_type == relationship_type
                and not lineage.is_deleted
            ):
                return lineage
        lineage = _FakeLineage(
            parent_uid=parent.uid,
            child_uid=child.uid,
            relationship_type=relationship_type,
        )
        self.lineages.append(lineage)
        return lineage

    def delete_lineage(self, session, *, parent: _FakeInstance, child: _FakeInstance, relationship_type: str):
        for lineage in self.lineages:
            if (
                lineage.parent_uid == parent.uid
                and lineage.child_uid == child.uid
                and lineage.relationship_type == relationship_type
                and not lineage.is_deleted
            ):
                lineage.is_deleted = True
                return True
        return False

    def list_children(self, session, *, parent: _FakeInstance, relationship_type: str | None = None):
        child_uids = [
            lineage.child_uid
            for lineage in self.lineages
            if lineage.parent_uid == parent.uid
            and not lineage.is_deleted
            and (relationship_type is None or lineage.relationship_type == relationship_type)
        ]
        rows: list[_FakeInstance] = []
        for template_rows in self.instances.values():
            for row in template_rows:
                if row.uid in child_uids and not row.is_deleted:
                    rows.append(row)
        return rows


@pytest.fixture
def backend() -> _InMemoryBackend:
    return _InMemoryBackend()


@pytest.fixture
def service(backend: _InMemoryBackend) -> DeweyService:
    return DeweyService(backend, default_share_ttl_seconds=120)


def test_register_artifact_replay_and_identity_reuse(service: DeweyService) -> None:
    service.bootstrap()

    status_code, created = service.register_artifact(
        artifact_type="FASTQ",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-1",
    )

    replay_code, replay = service.register_artifact(
        artifact_type="fastq",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-1",
    )

    reused_code, reused = service.register_artifact(
        artifact_type="fastq",
        storage_backend="s3",
        bucket="bucket-1",
        key="reads/r1.fastq.gz",
        version_id=None,
        size=123,
        checksums={"sha256": "abc"},
        content_type="application/gzip",
        original_filename="r1.fastq.gz",
        producer_system="atlas",
        producer_object_euid="OBJ-1",
        storage_class="standard",
        availability_status="ready",
        metadata={"lane": 1},
        idempotency_key="idem-2",
    )

    assert status_code == 201
    assert replay_code == 201
    assert replay["artifact_euid"] == created["artifact_euid"]
    assert reused_code == 200
    assert reused["artifact_euid"] == created["artifact_euid"]
    assert service.get_artifact(created["artifact_euid"])["storage_uri"] == "s3://bucket-1/reads/r1.fastq.gz"
    assert service.list_artifacts(artifact_type="fastq", producer_system="atlas") == [created]


def test_import_artifact_and_validation_errors(service: DeweyService) -> None:
    with pytest.raises(ValueError, match="s3://"):
        service.import_artifact_from_uri(
            artifact_type="fastq",
            storage_uri="gs://bucket/object",
            metadata={},
            idempotency_key="idem-import-bad",
        )

    with pytest.raises(ValueError, match="bucket is required"):
        service.register_artifact(
            artifact_type="fastq",
            storage_backend="s3",
            bucket="",
            key="reads/r2.fastq.gz",
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
            idempotency_key="idem-invalid",
        )

    status_code, imported = service.import_artifact_from_uri(
        artifact_type="fastq",
        storage_uri="s3://bucket-2/reads/r2.fastq.gz",
        metadata={"content_type": "application/gzip", "producer_system": "ursa"},
        idempotency_key="idem-import-good",
    )

    assert status_code == 201
    assert imported["bucket"] == "bucket-2"
    assert imported["producer_system"] == "ursa"


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
    assert service.get_artifact_set(artifact_set["artifact_set_euid"])["artifact_set_type"] == "bundle"
    assert service.list_artifact_sets(artifact_set_type="bundle")[0]["label"] == "Case Bundle"
    assert remove_code == 200
    assert removed["artifact_euids"] == []

    with pytest.raises(DeweyNotFoundError):
        service.get_artifact_set("AS-999999")


def test_share_reference_behaviors(service: DeweyService) -> None:
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
        idempotency_key="idem-share-auto",
    )
    explicit_code, explicit_share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose=None,
        scope="internal",
        expires_at="2026-04-01T00:00:00Z",
        issued_by=None,
        idempotency_key="idem-share-explicit",
    )

    assert auto_code == 201
    assert explicit_code == 201
    assert auto_share["issued_by"] == "tester@example.com"
    assert explicit_share["expires_at"] == "2026-04-01T00:00:00Z"

    with pytest.raises(ValueError, match="target_type must be artifact or artifact_set"):
        service.create_share_reference(
            target_type="report",
            target_euid="AT-1",
            purpose=None,
            scope=None,
            expires_at=None,
            issued_by=None,
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
    assert existing_relation["external_object_relation_euid"] == relation["external_object_relation_euid"]
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
