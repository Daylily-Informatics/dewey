from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from dewey_service.service import DeweyService
from dewey_service.storage import StorageObject, StorageObjectNotFoundError, StoragePrefix
from dewey_service.tapdb_backend import (
    ANOMALY_TEMPLATE,
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    LITERATURE_SAVE_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
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
            ANOMALY_TEMPLATE: 1,
            ARTIFACT_TEMPLATE: 1,
            ARTIFACT_SET_TEMPLATE: 1,
            SHARE_REFERENCE_TEMPLATE: 1,
            EXTERNAL_OBJECT_TEMPLATE: 1,
            EXTERNAL_OBJECT_RELATION_TEMPLATE: 1,
            LITERATURE_SAVE_TEMPLATE: 1,
            IDEMPOTENCY_TEMPLATE: 1,
            REGISTRATION_RECEIPT_TEMPLATE: 1,
            OUTBOX_EVENT_TEMPLATE: 1,
        }
        self.prefixes = {
            ANOMALY_TEMPLATE: "ANM",
            ARTIFACT_TEMPLATE: "AT",
            ARTIFACT_SET_TEMPLATE: "AS",
            SHARE_REFERENCE_TEMPLATE: "SH",
            EXTERNAL_OBJECT_TEMPLATE: "EX",
            EXTERNAL_OBJECT_RELATION_TEMPLATE: "ER",
            LITERATURE_SAVE_TEMPLATE: "SAV",
            IDEMPOTENCY_TEMPLATE: "KDP",
            REGISTRATION_RECEIPT_TEMPLATE: "RCP",
            OUTBOX_EVENT_TEMPLATE: "EVT",
        }

    @contextmanager
    def session_scope(self, commit: bool = False):
        _ = commit
        yield self

    def ensure_templates(self, session) -> None:
        _ = session
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
        _ = session
        _ = status
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

    def update_instance_json(
        self,
        session,
        instance: _FakeInstance,
        updates: dict[str, Any],
    ) -> None:
        _ = session
        payload = dict(instance.json_addl or {})
        payload.update(updates)
        instance.json_addl = payload

    def find_by_json_field(self, session, *, template_code: str, field: str, value: str):
        _ = session
        for instance in self.instances.get(template_code, []):
            if instance.is_deleted:
                continue
            if str(instance.json_addl.get(field)) == value:
                return instance
        return None

    def find_by_euid(self, session, *, template_code: str, euid: str, for_update: bool = False):
        _ = session
        _ = for_update
        for instance in self.instances.get(template_code, []):
            if not instance.is_deleted and instance.euid == euid:
                return instance
        return None

    def list_by_template(self, session, *, template_code: str, limit: int = 200):
        _ = session
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
        _ = session
        _ = name
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

    def delete_lineage(
        self,
        session,
        *,
        parent: _FakeInstance,
        child: _FakeInstance,
        relationship_type: str,
    ):
        _ = session
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

    def list_children(
        self,
        session,
        *,
        parent: _FakeInstance,
        relationship_type: str | None = None,
    ):
        _ = session
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

    def list_parents(self, session, *, child: _FakeInstance, relationship_type: str | None = None):
        _ = session
        parent_uids = [
            lineage.parent_uid
            for lineage in self.lineages
            if lineage.child_uid == child.uid
            and not lineage.is_deleted
            and (relationship_type is None or lineage.relationship_type == relationship_type)
        ]
        rows: list[_FakeInstance] = []
        for template_rows in self.instances.values():
            for row in template_rows:
                if row.uid in parent_uids and not row.is_deleted:
                    rows.append(row)
        return rows


class _FakeStorageClient:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], StorageObject] = {}
        self.object_bodies: dict[tuple[str, str], bytes] = {}
        self.tags: dict[tuple[str, str], dict[str, str]] = {}
        self.retentions: dict[tuple[str, str], dict[str, str]] = {}

    def seed_object(
        self,
        *,
        bucket: str,
        key: str,
        size: int = 128,
        content_type: str | None = "application/octet-stream",
        storage_class: str | None = "STANDARD",
        version_id: str | None = None,
    ) -> StorageObject:
        obj = StorageObject(
            bucket=bucket,
            key=key,
            version_id=version_id,
            size=size,
            content_type=content_type,
            storage_class=storage_class,
            etag="etag-1",
        )
        self.objects[(bucket, key)] = obj
        return obj

    def head_object(self, *, bucket: str, key: str, version_id: str | None = None) -> StorageObject:
        _ = version_id
        obj = self.objects.get((bucket, key))
        if obj is None:
            raise StorageObjectNotFoundError(f"{bucket}/{key}")
        return obj

    def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageObject:
        source = self.head_object(bucket=source_bucket, key=source_key)
        return self.seed_object(
            bucket=dest_bucket,
            key=dest_key,
            size=source.size or 0,
            content_type=source.content_type,
            storage_class=source.storage_class,
            version_id=source.version_id,
        )

    def put_bytes(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> StorageObject:
        obj = self.seed_object(
            bucket=bucket,
            key=key,
            size=len(body),
            content_type=content_type,
            storage_class="STANDARD",
        )
        self.object_bodies[(bucket, key)] = bytes(body)
        return obj

    def list_objects(self, *, bucket: str, prefix: str, limit: int = 1000) -> list[StorageObject]:
        rows = [
            obj
            for (obj_bucket, _), obj in self.objects.items()
            if obj_bucket == bucket and obj.key.startswith(prefix)
        ]
        rows.sort(key=lambda item: item.key)
        return rows[:limit]

    def browse_prefix(
        self,
        *,
        bucket: str,
        prefix: str = "",
        limit: int = 200,
        continuation_token: str | None = None,
    ) -> dict[str, Any]:
        _ = continuation_token
        prefixes: set[str] = set()
        objects: list[StorageObject] = []
        for (obj_bucket, _), obj in self.objects.items():
            if obj_bucket != bucket or not obj.key.startswith(prefix):
                continue
            remainder = obj.key[len(prefix) :]
            if not remainder:
                continue
            if "/" in remainder:
                child = remainder.split("/", 1)[0]
                prefixes.add(f"{prefix}{child}/")
            else:
                objects.append(obj)
        return {
            "prefixes": [
                StoragePrefix(bucket=bucket, prefix=item) for item in sorted(prefixes)[:limit]
            ],
            "objects": sorted(objects, key=lambda item: item.key)[:limit],
            "is_truncated": False,
            "next_continuation_token": None,
        }

    def get_object_bytes(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str | None = None,
    ) -> bytes:
        _ = version_id
        self.head_object(bucket=bucket, key=key)
        if (bucket, key) in self.object_bodies:
            return self.object_bodies[(bucket, key)]
        return f"payload:{bucket}/{key}".encode("utf-8")

    def put_object_tags(self, *, bucket: str, key: str, tags: dict[str, str]) -> None:
        self.head_object(bucket=bucket, key=key)
        merged = dict(self.tags.get((bucket, key), {}))
        merged.update(tags)
        self.tags[(bucket, key)] = merged

    def set_retention(self, *, bucket: str, key: str, mode: str, retain_until: datetime) -> None:
        self.head_object(bucket=bucket, key=key)
        self.retentions[(bucket, key)] = {
            "mode": mode,
            "retain_until": retain_until.isoformat(),
        }

    def generate_presigned_get_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        version_id: str | None = None,
    ) -> str:
        _ = version_id
        self.head_object(bucket=bucket, key=key)
        return f"https://downloads.example.com/{bucket}/{key}?expires_in={expires_in}"

    def generate_presigned_upload(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        _ = expires_in
        return {
            "method": "PUT",
            "url": f"https://uploads.example.com/{bucket}/{key}",
            "headers": {"Content-Type": content_type} if content_type else {},
        }


class _FakeLiteratureAdapter:
    def __init__(self) -> None:
        self.records = {
            "123456": {
                "pmid": "123456",
                "doi": "10.1000/example-123456",
                "pmcid": "PMC123456",
                "title": "Gene Therapy For Example Disease",
                "journal": "Example Journal",
                "year": "2024",
                "authors": ["Example A", "Author B"],
                "abstract": "Long abstract for example paper.",
                "abstract_snippet": "Long abstract for example paper.",
                "source_urls": [
                    "https://pubmed.ncbi.nlm.nih.gov/123456/",
                    "https://doi.org/10.1000/example-123456",
                ],
                "best_fulltext_url": "https://europepmc.org/articles/PMC123456?pdf=render",
                "findit_reason": None,
            },
            "789012": {
                "pmid": "789012",
                "doi": "10.1000/example-789012",
                "pmcid": "PMC789012",
                "title": "External Reference Only Example",
                "journal": "Example Journal",
                "year": "2023",
                "authors": ["Example C"],
                "abstract": "External-only abstract.",
                "abstract_snippet": "External-only abstract.",
                "source_urls": ["https://pubmed.ncbi.nlm.nih.gov/789012/"],
                "best_fulltext_url": "https://publisher.example.com/article.pdf",
                "findit_reason": "PAYWALL: publisher requires subscription",
            },
        }

    def search(self, *, query: str, page: int = 1, page_size: int = 20) -> list[dict[str, Any]]:
        _ = page
        lowered = str(query or "").strip().lower()
        rows = [row for row in self.records.values() if lowered in json.dumps(row).lower()]
        return rows[:page_size]

    def fetch_record(self, pmid: str) -> dict[str, Any]:
        return dict(self.records[str(pmid)])


@pytest.fixture
def backend() -> _InMemoryBackend:
    return _InMemoryBackend()


@pytest.fixture
def storage() -> _FakeStorageClient:
    return _FakeStorageClient()


@pytest.fixture
def service(backend: _InMemoryBackend, storage: _FakeStorageClient) -> DeweyService:
    return DeweyService(
        backend,
        default_share_ttl_seconds=120,
        storage_client=storage,
        managed_storage_bucket="managed-bucket",
        managed_storage_prefix="artifacts",
        upload_session_ttl_seconds=900,
        upload_token_secret="upload-secret",
        search_export_max_rows=1000,
        literature_adapter=_FakeLiteratureAdapter(),
        literature_allowed_domains={"europepmc.org", "ncbi.nlm.nih.gov"},
        literature_request_timeout_seconds=5,
    )


__all__ = [
    "backend",
    "service",
    "storage",
    "_FakeLiteratureAdapter",
    "_FakeStorageClient",
    "_InMemoryBackend",
]
