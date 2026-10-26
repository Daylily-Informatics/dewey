from __future__ import annotations

import json
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from daylily_tapdb import generic_instance, generic_instance_lineage

from dewey_service.registry_access import Principal, principal_context
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
    SHARE_ROOT_TEMPLATE,
    SHARE_TEMPLATE,
    TEMPLATE_DEFINITIONS,
    TapDBBackend,
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
    domain_code: str = "Z"
    issuer_app_code: str = "dewey"
    tenant_id: None = None
    template_uid: int = 0
    bstatus: str = "active"
    record_revision: int = 1
    identity_key: str | None = None

    @property
    def category(self):
        return self.template_code.split("/")[0]

    @property
    def type(self):
        return self.template_code.split("/")[1]

    @property
    def subtype(self):
        return self.template_code.split("/")[2]

    @property
    def version(self):
        return self.template_code.split("/")[3]


@dataclass
class _FakeLineage:
    parent_uid: int
    child_uid: int
    relationship_type: str
    is_deleted: bool = False
    uid: int = 0
    parent_instance: _FakeInstance | None = None
    domain_code: str = "Z"
    issuer_app_code: str = "dewey"
    tenant_id: None = None
    bstatus: str = "active"
    record_revision: int = 1
    child_instance: _FakeInstance | None = None

    @property
    def parent_instance_uid(self):
        return self.parent_uid

    @property
    def child_instance_uid(self):
        return self.child_uid


class _FakeReferenceQuery:
    """Persistence-only SQL subset; unsupported predicates fail explicitly."""

    def __init__(self, rows, backend):
        self.rows, self.backend = list(rows), backend
        self.entities = ()
        self.grouped = False

    @staticmethod
    def _value(expression, row):
        from sqlalchemy.sql import operators
        from sqlalchemy.sql.elements import (
            BindParameter,
            BooleanClauseList,
            Cast,
            False_,
            Grouping,
            Null,
            True_,
        )
        from sqlalchemy.sql.functions import FunctionElement

        value = _FakeReferenceQuery._value
        if isinstance(expression, (True_, False_)):
            return isinstance(expression, True_)
        if isinstance(expression, Null):
            return None
        if isinstance(expression, BindParameter):
            return expression.value
        if isinstance(expression, (Grouping, Cast)):
            inner = expression.element if isinstance(expression, Grouping) else expression.clause
            return value(inner, row)
        if isinstance(expression, BooleanClauseList):
            children = (value(child, row) for child in expression.clauses)
            return all(children) if expression.operator is operators.and_ else any(children)
        if isinstance(expression, FunctionElement):
            args = [value(child, row) for child in expression.clauses]
            if expression.name == "length":
                assert len(args) == 1 and isinstance(args[0], str)
                return len(args[0])
            if expression.name == "left":
                assert len(args) == 2 and isinstance(args[0], str)
                assert type(args[1]) is int and args[1] >= 0
                return args[0][: args[1]]
            if expression.name == "jsonb_path_exists":
                data, path, variables = args
                match = re.fullmatch(r'(\$(?:\."[^"]+")+)(?: \? \(@ == \$value\))?', path)
                assert match, f"Unsupported fake JSONPath: {path}"
                for part in re.findall(r'\."([^"]+)"', match[1]):
                    if not isinstance(data, dict) or part not in data:
                        return False
                    data = data[part]
                return data == variables["value"] if " ? " in path else True
            raise AssertionError(f"Unsupported fake SQL function: {expression.name}")
        operator = getattr(expression, "operator", None)
        if operator is not None and hasattr(expression, "left"):
            left, right = value(expression.left, row), value(expression.right, row)
            if operator in (operators.eq, operators.is_):
                return left == right
            if operator in (operators.ne, operators.is_not):
                return left != right
            if operator is operators.in_op:
                return left in right
            if operator is operators.not_in_op:
                return left not in right
            if (
                operator is operators.json_getitem_op
                or getattr(operator, "opstring", None) == "->>"
            ):
                return left.get(right)
            raise AssertionError(f"Unsupported fake SQL operator: {expression}")
        key = getattr(expression, "key", None)
        if key is not None:
            table = getattr(getattr(expression, "table", None), "name", None)
            if table == "generic_instance" and isinstance(row, _FakeLineage):
                row = row.child_instance
            return getattr(row, key)
        raise AssertionError(f"Unsupported fake expression: {expression}")

    def filter_by(self, **filters):
        return _FakeReferenceQuery(
            [row for row in self.rows if all(getattr(row, k) == v for k, v in filters.items())],
            self.backend,
        )

    def filter(self, *expressions):
        rows = self.rows
        for expression in expressions:
            rows = [row for row in rows if self._value(expression, row)]
        return _FakeReferenceQuery(rows, self.backend)

    def join(self, *args):
        return self

    def order_by(self, *columns):
        from sqlalchemy.sql import operators

        rows = self.rows
        for column in reversed(columns):
            descending = getattr(column, "modifier", None) is operators.desc_op
            value = getattr(column, "element", column)
            rows = sorted(rows, key=lambda row: self._value(value, row), reverse=descending)
        return _FakeReferenceQuery(rows, self.backend)

    def offset(self, count):
        return _FakeReferenceQuery(self.rows[count:], self.backend)

    def limit(self, count):
        return _FakeReferenceQuery(self.rows[:count], self.backend)

    def with_entities(self, *entities):
        query = _FakeReferenceQuery(self.rows, self.backend)
        query.entities = entities
        return query

    def group_by(self, column):
        assert column is generic_instance.type
        self.grouped = True
        return self

    def options(self, *options):
        return self

    def with_for_update(self):
        self.backend.source_locks.extend(row.uid for row in self.rows)
        return self

    def all(self):
        if self.grouped:
            counts = {}
            for row in self.rows:
                counts[row.type] = counts.get(row.type, 0) + 1
            return list(counts.items())
        if self.entities:
            return [
                tuple(
                    row if entity is generic_instance else self._value(entity, row)
                    for entity in self.entities
                )
                for row in self.rows
            ]
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None

    def one_or_none(self):
        assert len(self.rows) <= 1
        return self.rows[0] if self.rows else None


class _InMemoryBackend:
    def __init__(self, settings=None) -> None:
        self.domain_code = "Z"
        self.settings = settings
        self.connection = SimpleNamespace(app_username="fixture-operator")
        self.factory = SimpleNamespace(create_instance=self._allocate_instance)
        self.instances: dict[str, list[_FakeInstance]] = {}
        self.lineages: list[_FakeLineage] = []
        self.session_scope_errors = 0
        self.source_locks = []
        self.external_locks = []
        self.coordinate_locks = []
        self.commits = []
        self.native_assertions = {}
        self.next_uid = 1
        self.next_by_prefix = {
            ANOMALY_TEMPLATE: 1,
            ARTIFACT_TEMPLATE: 1,
            ARTIFACT_SET_TEMPLATE: 1,
            SHARE_TEMPLATE: 1,
            SHARE_ROOT_TEMPLATE: 1,
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
            SHARE_TEMPLATE: "SHR",
            SHARE_ROOT_TEMPLATE: "SRT",
            EXTERNAL_OBJECT_TEMPLATE: "EX",
            EXTERNAL_OBJECT_RELATION_TEMPLATE: "ER",
            LITERATURE_SAVE_TEMPLATE: "SAV",
            IDEMPOTENCY_TEMPLATE: "KDP",
            REGISTRATION_RECEIPT_TEMPLATE: "RCP",
            OUTBOX_EVENT_TEMPLATE: "EVT",
        }
        self._templates = {
            code: SimpleNamespace(uid=index, type=code.split("/")[1], instance_prefix="DGX")
            for index, code in enumerate(TEMPLATE_DEFINITIONS, 1)
        }
        for code in TEMPLATE_DEFINITIONS:
            self.next_by_prefix.setdefault(code, 1)
            self.prefixes.setdefault(code, f"fixture-{code.split('/')[1]}")
        self.templates = SimpleNamespace(get_template=self._get_template)

    def _get_template(self, session, code, *, domain_code=None):
        assert domain_code in (None, self.domain_code)
        return self._templates.get(code)

    @contextmanager
    def session_scope(self, commit: bool = False):
        self.commits.append(commit)
        try:
            yield self
        except Exception:
            self.session_scope_errors += 1
            raise

    def query(self, model):
        if model is generic_instance_lineage:
            return _FakeReferenceQuery(self.lineages, self)
        assert model is generic_instance or model is generic_instance.uid
        return _FakeReferenceQuery([row for rows in self.instances.values() for row in rows], self)

    def ensure_templates(self, session, template_codes=TEMPLATE_DEFINITIONS) -> None:
        _ = session
        assert all(code in self._templates for code in template_codes)

    def lock_external_key(self, session, *, operation, key):
        assert session is self
        self.external_locks.append((operation, key))

    def execute(self, statement, parameters):
        assert str(statement) == "SELECT pg_advisory_xact_lock(:key)"
        assert set(parameters) == {"key"} and type(parameters["key"]) is int
        self.coordinate_locks.append(parameters["key"])

    def _allocate_instance(self, *, session, template_code, name, properties, create_children):
        assert session is self and properties == {} and create_children is False
        prefix = self.prefixes[template_code]
        seq = self.next_by_prefix[template_code]
        self.next_by_prefix[template_code] += 1
        instance = _FakeInstance(
            uid=self.next_uid,
            euid=f"{prefix}-{seq:06d}",
            template_code=template_code,
            name=name,
            json_addl={"properties": {}, "action_groups": {}, "audit_log": []},
            template_uid=self._templates[template_code].uid,
        )
        self.next_uid += 1
        self.instances.setdefault(template_code, []).append(instance)
        return instance

    # Exercise Dewey's real native envelope, revision and policy creation contracts;
    # only allocation and persistence are replaced by in-memory I/O.
    create_instance = TapDBBackend.create_instance
    update_instance_json = TapDBBackend.update_instance_json

    def update_persisted_fields(self, session, instance, changes, *, expected_revision=None):
        assert expected_revision is None or instance.record_revision == expected_revision
        for key, value in changes.items():
            setattr(instance, key, value)
        instance.record_revision += 1

    def delete_persisted(self, session, instance):
        self.update_persisted_fields(session, instance, {"is_deleted": True})

    def find_by_json_field(
        self, session, *, template_code: str, field: str, value: str, for_update: bool = False
    ):
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
            uid=len(self.lineages) + 1,
            parent_instance=parent,
            child_instance=child,
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

    def list_children_many(self, session, *, parents, relationship_type):
        return {
            parent.uid: self.list_children(
                session, parent=parent, relationship_type=relationship_type
            )
            for parent in parents
        }

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
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def seed_object(
        self,
        *,
        bucket: str,
        key: str,
        size: int = 128,
        content_type: str | None = "application/octet-stream",
        storage_class: str | None = "STANDARD",
        version_id: str | None = None,
        sha256: str | None = None,
    ) -> StorageObject:
        obj = StorageObject(
            bucket=bucket,
            key=key,
            version_id=version_id,
            size=size,
            content_type=content_type,
            storage_class=storage_class,
            etag="etag-1",
            sha256=sha256,
        )
        self.objects[(bucket, key)] = obj
        return obj

    def head_object(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str | None = None,
        request_payer: str | None = None,
    ) -> StorageObject:
        _ = version_id
        _ = request_payer
        self.calls.append(
            ("head_object", {"bucket": bucket, "key": key, "request_payer": request_payer})
        )
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
            sha256=source.sha256,
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

    def list_objects(
        self,
        *,
        bucket: str,
        prefix: str,
        limit: int = 1000,
        request_payer: str | None = None,
    ) -> list[StorageObject]:
        _ = request_payer
        self.calls.append(
            ("list_objects", {"bucket": bucket, "prefix": prefix, "request_payer": request_payer})
        )
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
        request_payer: str | None = None,
        cache_ttl: int,
        refresh: bool = False,
    ) -> dict[str, Any]:
        _ = continuation_token
        _ = request_payer
        self.calls.append(
            (
                "browse_prefix",
                {
                    "bucket": bucket,
                    "prefix": prefix,
                    "request_payer": request_payer,
                    "cache_ttl": cache_ttl,
                    "refresh": refresh,
                },
            )
        )
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
        request_payer: str | None = None,
    ) -> bytes:
        _ = version_id
        _ = request_payer
        self.calls.append(
            ("get_object_bytes", {"bucket": bucket, "key": key, "request_payer": request_payer})
        )
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
        request_payer: str | None = None,
    ) -> str:
        _ = version_id
        _ = request_payer
        self.head_object(bucket=bucket, key=key)
        payer = "&x-amz-request-payer=requester" if request_payer == "requester" else ""
        return f"https://downloads.example.com/{bucket}/{key}?expires_in={expires_in}{payer}"

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
def service(backend: _InMemoryBackend, storage: _FakeStorageClient, monkeypatch) -> DeweyService:
    class NativeReferenceRecorder:
        def __init__(self, session):
            assert session is backend

        def attach(self, source, spec, *, expected_source_revision, expected_lineage_revision):
            assert source.uid in backend.source_locks
            assert expected_source_revision == source.record_revision
            assert expected_lineage_revision is None
            key = (source.uid, spec.target.identity_key, spec.relationship_type)
            if key in backend.native_assertions:
                assert backend.native_assertions[key] == spec
                return SimpleNamespace(status="existing")
            backend.native_assertions[key] = spec
            return SimpleNamespace(status="created")

    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_external_references.ExternalReferenceService",
        NativeReferenceRecorder,
    )
    instance = DeweyService(
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
        qeo_ingest_url="https://qeo.test/api/v1/ingest/dewey-events",
        qeo_api_token="qeo-token",
        qeo_consumer_group="qeo.test",
    )
    actor = Principal(
        subject="fixture-service-operator",
        email="operator@example.test",
        roles=("ADMIN",),
        internal=True,
        service=True,
        email_verified=True,
    )
    with principal_context(actor):
        yield instance


__all__ = [
    "backend",
    "service",
    "storage",
    "_FakeLiteratureAdapter",
    "_FakeStorageClient",
    "_InMemoryBackend",
]
