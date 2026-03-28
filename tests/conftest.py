from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import Settings


class FakeDeweyService:
    def __init__(self) -> None:
        self._artifact_seq = 1
        self._artifact_set_seq = 1
        self._share_seq = 1
        self._external_seq = 1
        self._external_rel_seq = 1
        self._upload_seq = 1
        self.artifacts: dict[str, dict[str, Any]] = {}
        self.artifact_sets: dict[str, dict[str, Any]] = {}
        self.share_references: dict[str, dict[str, Any]] = {}
        self.external_objects: dict[str, dict[str, Any]] = {}
        self.external_relations: list[dict[str, Any]] = []
        self.upload_sessions: dict[str, dict[str, Any]] = {}
        self.idempotency: dict[str, tuple[str, int, dict[str, Any]]] = {}

    @staticmethod
    def _fp(payload: dict[str, Any]) -> str:
        raw = repr(sorted(payload.items())).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _idempotent(self, op: str, key: str, payload: dict[str, Any]):
        lookup = f"{op}:{key}"
        fp = self._fp(payload)
        if lookup in self.idempotency:
            existing_fp, code, body = self.idempotency[lookup]
            if existing_fp != fp:
                from dewey_service.service import DeweyConflictError

                raise DeweyConflictError("Idempotency-Key reuse with different request payload")
            return code, body
        return None

    def _remember(
        self, op: str, key: str, payload: dict[str, Any], code: int, body: dict[str, Any]
    ) -> None:
        lookup = f"{op}:{key}"
        self.idempotency[lookup] = (self._fp(payload), code, dict(body))

    def bootstrap(self) -> None:
        return

    def register_artifact(self, *, idempotency_key: str, **kwargs):
        payload = dict(kwargs)
        replay = self._idempotent("artifact.register", idempotency_key, payload)
        if replay:
            return replay
        euid = f"AT-{self._artifact_seq:06d}"
        self._artifact_seq += 1
        item = {
            "artifact_euid": euid,
            "artifact_type": kwargs["artifact_type"],
            "storage_backend": kwargs["storage_backend"],
            "bucket": kwargs["bucket"],
            "key": kwargs["key"],
            "version_id": kwargs.get("version_id"),
            "size": kwargs.get("size"),
            "checksums": dict(kwargs.get("checksums") or {}),
            "content_type": kwargs.get("content_type"),
            "original_filename": kwargs.get("original_filename"),
            "producer_system": kwargs.get("producer_system"),
            "producer_object_euid": kwargs.get("producer_object_euid"),
            "storage_class": kwargs.get("storage_class"),
            "availability_status": kwargs.get("availability_status"),
            "metadata": dict(kwargs.get("metadata") or {}),
            "storage_uri": f"{kwargs['storage_backend']}://{kwargs['bucket']}/{kwargs['key']}",
            "source_uri": kwargs.get("source_uri")
            or f"{kwargs['storage_backend']}://{kwargs['bucket']}/{kwargs['key']}",
            "import_mode": kwargs.get("import_mode", "register"),
            "storage_status": kwargs.get("storage_status", "registered"),
            "storage_verified_at": kwargs.get("storage_verified_at"),
            "retention_mode": kwargs.get("retention_mode"),
            "retain_until": kwargs.get("retain_until"),
            "share_status": kwargs.get("share_status"),
            "share_last_issued_at": kwargs.get("share_last_issued_at"),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.artifacts[euid] = item
        self._remember("artifact.register", idempotency_key, payload, 201, item)
        return 201, dict(item)

    def import_artifact_from_uri(
        self,
        *,
        artifact_type: str,
        storage_uri: str | None = None,
        source_uri: str | None = None,
        import_mode: str | None = None,
        lock_after_import: bool = False,
        producer_system: str | None = None,
        producer_object_euid: str | None = None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        source = source_uri or storage_uri or ""
        meta = dict(metadata or {})
        if not source.startswith(("s3://", "https://", "http://")):
            raise ValueError("source_uri must use s3:// or https://")
        if (import_mode or "reference") == "reference":
            if not source.startswith("s3://"):
                raise ValueError("reference import requires an s3:// source_uri")
            bucket_and_key = source[5:]
            bucket, key = bucket_and_key.split("/", 1)
            return self.register_artifact(
                artifact_type=artifact_type,
                storage_backend="s3",
                bucket=bucket,
                key=key,
                version_id=None,
                size=meta.get("size"),
                checksums=dict(meta.get("checksums") or {}),
                content_type=meta.get("content_type"),
                original_filename=meta.get("original_filename"),
                producer_system=producer_system or meta.get("producer_system"),
                producer_object_euid=producer_object_euid or meta.get("producer_object_euid"),
                storage_class=meta.get("storage_class"),
                availability_status=meta.get("availability_status") or "available",
                metadata=meta,
                source_uri=source,
                import_mode="reference",
                storage_status="verified",
                storage_verified_at="2026-03-10T00:00:00Z",
                retention_mode="GOVERNANCE" if lock_after_import else None,
                retain_until="2126-03-10T00:00:00Z" if lock_after_import else None,
                idempotency_key=idempotency_key,
            )
        return self.register_artifact(
            artifact_type=artifact_type,
            storage_backend="s3",
            bucket="managed-bucket",
            key=f"imports/{artifact_type}/{source.split('/')[-1]}",
            version_id=None,
            size=meta.get("size"),
            checksums=dict(meta.get("checksums") or {}),
            content_type=meta.get("content_type"),
            original_filename=meta.get("original_filename") or source.split("/")[-1],
            producer_system=producer_system or meta.get("producer_system"),
            producer_object_euid=producer_object_euid or meta.get("producer_object_euid"),
            storage_class=meta.get("storage_class"),
            availability_status=meta.get("availability_status") or "available",
            metadata=meta,
            source_uri=source,
            import_mode="copy",
            storage_status="verified",
            storage_verified_at="2026-03-10T00:00:00Z",
            retention_mode="GOVERNANCE" if lock_after_import else None,
            retain_until="2126-03-10T00:00:00Z" if lock_after_import else None,
            idempotency_key=idempotency_key,
        )

    def create_upload_session(
        self,
        *,
        artifact_type: str,
        original_filename: str,
        content_type: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        metadata: dict[str, Any] | None,
        lock_after_import: bool,
        idempotency_key: str,
    ):
        payload = {
            "artifact_type": artifact_type,
            "original_filename": original_filename,
            "content_type": content_type,
            "producer_system": producer_system,
            "producer_object_euid": producer_object_euid,
            "metadata": dict(metadata or {}),
            "lock_after_import": lock_after_import,
        }
        replay = self._idempotent("artifact.upload_session.create", idempotency_key, payload)
        if replay:
            return replay
        token = f"upload-{self._upload_seq:06d}"
        self._upload_seq += 1
        session = {
            **payload,
            "bucket": "managed-bucket",
            "key": f"uploads/{token}/{original_filename}",
        }
        self.upload_sessions[token] = session
        body = {
            "upload_token": token,
            "upload_method": "PUT",
            "upload_url": f"https://uploads.example.com/{token}",
            "upload_headers": {"Content-Type": content_type} if content_type else {},
            "bucket": session["bucket"],
            "key": session["key"],
            "storage_uri": f"s3://{session['bucket']}/{session['key']}",
            "expires_in": 900,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self._remember("artifact.upload_session.create", idempotency_key, payload, 201, body)
        return 201, body

    def complete_upload_session(
        self,
        *,
        upload_token: str,
        checksums: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        from dewey_service.service import DeweyNotFoundError

        if upload_token not in self.upload_sessions:
            raise DeweyNotFoundError("Uploaded object not found")
        session = self.upload_sessions[upload_token]
        merged_metadata = dict(session.get("metadata") or {})
        merged_metadata.update(dict(metadata or {}))
        return self.register_artifact(
            artifact_type=session["artifact_type"],
            storage_backend="s3",
            bucket=session["bucket"],
            key=session["key"],
            version_id=None,
            size=None,
            checksums=dict(checksums or {}),
            content_type=session.get("content_type"),
            original_filename=session["original_filename"],
            producer_system=session.get("producer_system"),
            producer_object_euid=session.get("producer_object_euid"),
            storage_class=None,
            availability_status="available",
            metadata=merged_metadata,
            source_uri=f"s3://{session['bucket']}/{session['key']}",
            import_mode="upload",
            storage_status="verified",
            storage_verified_at="2026-03-10T00:00:00Z",
            retention_mode="GOVERNANCE" if session.get("lock_after_import") else None,
            retain_until="2126-03-10T00:00:00Z" if session.get("lock_after_import") else None,
            idempotency_key=idempotency_key,
        )

    def verify_artifact_storage(self, *, artifact_euid: str, idempotency_key: str):
        item = self.get_artifact(artifact_euid)
        item["storage_status"] = "verified"
        item["storage_verified_at"] = "2026-03-10T00:00:00Z"
        self.artifacts[artifact_euid] = item
        return 200, dict(item)

    def lock_artifact_storage(
        self,
        *,
        artifact_euid: str,
        mode: str,
        retain_until: str,
        idempotency_key: str,
    ):
        item = self.get_artifact(artifact_euid)
        item["retention_mode"] = mode
        item["retain_until"] = retain_until
        self.artifacts[artifact_euid] = item
        return 200, dict(item)

    def get_artifact(self, artifact_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        return dict(self.artifacts[artifact_euid])

    def list_artifacts(
        self,
        *,
        artifact_type: str | None = None,
        producer_system: str | None = None,
        limit: int = 200,
    ):
        rows = list(self.artifacts.values())
        if artifact_type:
            rows = [row for row in rows if row["artifact_type"] == artifact_type]
        if producer_system:
            rows = [row for row in rows if row.get("producer_system") == producer_system]
        return rows[:limit]

    def create_artifact_set(
        self,
        *,
        artifact_set_type: str,
        label: str | None,
        description: str | None,
        idempotency_key: str,
    ):
        payload = {
            "artifact_set_type": artifact_set_type,
            "label": label,
            "description": description,
        }
        replay = self._idempotent("artifact_set.create", idempotency_key, payload)
        if replay:
            return replay
        euid = f"AS-{self._artifact_set_seq:06d}"
        self._artifact_set_seq += 1
        item = {
            "artifact_set_euid": euid,
            "artifact_set_type": artifact_set_type,
            "label": label,
            "description": description,
            "artifact_euids": [],
            "members": [],
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.artifact_sets[euid] = item
        self._remember("artifact_set.create", idempotency_key, payload, 201, item)
        return 201, dict(item)

    def add_artifact_set_member(
        self, *, artifact_set_euid: str, artifact_euid: str, idempotency_key: str
    ):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        payload = {"artifact_set_euid": artifact_set_euid, "artifact_euid": artifact_euid}
        replay = self._idempotent("artifact_set.member.add", idempotency_key, payload)
        if replay:
            return replay
        aset = self.artifact_sets[artifact_set_euid]
        if artifact_euid not in aset["artifact_euids"]:
            aset["artifact_euids"].append(artifact_euid)
        aset["members"] = [self.artifacts[euid] for euid in aset["artifact_euids"]]
        self._remember("artifact_set.member.add", idempotency_key, payload, 200, dict(aset))
        return 200, dict(aset)

    def remove_artifact_set_member(
        self, *, artifact_set_euid: str, artifact_euid: str, idempotency_key: str
    ):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        payload = {"artifact_set_euid": artifact_set_euid, "artifact_euid": artifact_euid}
        replay = self._idempotent("artifact_set.member.remove", idempotency_key, payload)
        if replay:
            return replay
        aset = self.artifact_sets[artifact_set_euid]
        aset["artifact_euids"] = [e for e in aset["artifact_euids"] if e != artifact_euid]
        aset["members"] = [self.artifacts[euid] for euid in aset["artifact_euids"]]
        self._remember("artifact_set.member.remove", idempotency_key, payload, 200, dict(aset))
        return 200, dict(aset)

    def get_artifact_set(self, artifact_set_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        return dict(self.artifact_sets[artifact_set_euid])

    def list_artifact_sets(self, *, artifact_set_type: str | None = None, limit: int = 200):
        rows = list(self.artifact_sets.values())
        if artifact_set_type:
            rows = [row for row in rows if row["artifact_set_type"] == artifact_set_type]
        return rows[:limit]

    def resolve_artifact(self, artifact_euid: str):
        return self.get_artifact(artifact_euid)

    def resolve_artifact_set(self, artifact_set_euid: str):
        return self.get_artifact_set(artifact_set_euid)

    def create_share_reference(
        self,
        *,
        target_type: str,
        target_euid: str,
        purpose: str | None,
        scope: str | None,
        expires_at: str | None,
        issued_by: str | None,
        transport: str | None = None,
        ttl_seconds: int | None = None,
        idempotency_key: str,
    ):
        payload = {
            "target_type": target_type,
            "target_euid": target_euid,
            "purpose": purpose,
            "scope": scope,
            "expires_at": expires_at,
            "issued_by": issued_by,
            "transport": transport or "presigned_s3",
            "ttl_seconds": ttl_seconds,
        }
        replay = self._idempotent("share_reference.create", idempotency_key, payload)
        if replay:
            return replay
        if target_type == "artifact":
            self.get_artifact(target_euid)
        else:
            self.get_artifact_set(target_euid)
        euid = f"SH-{self._share_seq:06d}"
        self._share_seq += 1
        body = {
            "share_reference_euid": euid,
            "target_type": target_type,
            "target_euid": target_euid,
            "purpose": purpose,
            "scope": scope,
            "transport": transport or "presigned_s3",
            "status": "active",
            "starts_at": "2026-03-10T00:00:00Z",
            "expires_at": expires_at or "2026-03-10T12:00:00Z",
            "access_url": f"https://downloads.example.com/{euid}",
            "issued_by": issued_by,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.share_references[euid] = body
        if target_type == "artifact" and target_euid in self.artifacts:
            self.artifacts[target_euid]["share_status"] = "active"
            self.artifacts[target_euid]["share_last_issued_at"] = body["created_at"]
        self._remember("share_reference.create", idempotency_key, payload, 201, body)
        return 201, body

    def get_share_reference(self, share_reference_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if share_reference_euid not in self.share_references:
            raise DeweyNotFoundError(f"Share reference not found: {share_reference_euid}")
        return dict(self.share_references[share_reference_euid])

    def list_share_references(
        self,
        *,
        target_type: str | None = None,
        target_euid: str | None = None,
        limit: int = 200,
    ):
        rows = list(self.share_references.values())
        if target_type:
            rows = [row for row in rows if row["target_type"] == target_type]
        if target_euid:
            rows = [row for row in rows if row["target_euid"] == target_euid]
        return rows[:limit]

    def create_external_object(
        self,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        payload = {
            "external_system": external_system,
            "external_object_type": external_object_type,
            "external_object_id": external_object_id,
            "external_uri": external_uri,
            "metadata": dict(metadata or {}),
        }
        replay = self._idempotent("external_object.create", idempotency_key, payload)
        if replay:
            return replay
        euid = f"EO-{self._external_seq:06d}"
        self._external_seq += 1
        body = {
            "external_object_euid": euid,
            "external_system": external_system,
            "external_object_type": external_object_type,
            "external_object_id": external_object_id,
            "external_uri": external_uri,
            "metadata": dict(metadata or {}),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.external_objects[euid] = body
        self._remember("external_object.create", idempotency_key, payload, 201, body)
        return 201, body

    def attach_external_object_relation(
        self,
        *,
        target_type: str,
        target_euid: str,
        external_object_euid: str,
        relation_type: str,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        from dewey_service.service import DeweyNotFoundError

        payload = {
            "target_type": target_type,
            "target_euid": target_euid,
            "external_object_euid": external_object_euid,
            "relation_type": relation_type,
            "metadata": dict(metadata or {}),
        }
        replay = self._idempotent("external_object_relation.attach", idempotency_key, payload)
        if replay:
            return replay
        if target_type == "artifact":
            self.get_artifact(target_euid)
        else:
            self.get_artifact_set(target_euid)
        if external_object_euid not in self.external_objects:
            raise DeweyNotFoundError(f"External object not found: {external_object_euid}")
        euid = f"ER-{self._external_rel_seq:06d}"
        self._external_rel_seq += 1
        row = {
            "external_object_relation_euid": euid,
            "target_type": target_type,
            "target_euid": target_euid,
            "external_object_euid": external_object_euid,
            "relation_type": relation_type,
            "metadata": dict(metadata or {}),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.external_relations.append(row)
        self._remember("external_object_relation.attach", idempotency_key, payload, 201, row)
        return 201, row

    def list_external_object_relations(
        self, *, target_type: str, target_euid: str, limit: int = 200
    ):
        rows = [
            row
            for row in self.external_relations
            if row["target_type"] == target_type and row["target_euid"] == target_euid
        ]
        return rows[:limit]

    def query_search_v2(self, request: dict[str, Any] | None):
        query = dict(request or {})
        scopes = query.get("scopes") or ["artifact", "share_reference"]
        rows: list[dict[str, Any]] = []
        if "artifact" in scopes:
            rows.extend(
                {
                    "record_type": "artifact",
                    "source_kind": "dewey.artifact",
                    "euid": row["artifact_euid"],
                    "name": row.get("original_filename") or row["artifact_euid"],
                    "created_at": row["created_at"],
                    "modified_at": row["created_at"],
                    **row,
                }
                for row in self.artifacts.values()
            )
        if "share_reference" in scopes:
            rows.extend(
                {
                    "record_type": "share_reference",
                    "source_kind": "dewey.share_reference",
                    "euid": row["share_reference_euid"],
                    "name": row["share_reference_euid"],
                    "created_at": row["created_at"],
                    "modified_at": row["created_at"],
                    **row,
                }
                for row in self.share_references.values()
            )
        q = str(query.get("q") or "").strip().lower()
        if q:
            rows = [row for row in rows if q in json.dumps(row, sort_keys=True, default=str).lower()]
        page_size = int(query.get("page_size") or 25)
        return {
            "items": rows[:page_size],
            "facets": {
                "artifact": sum(1 for row in rows if row["record_type"] == "artifact"),
                "share_reference": sum(
                    1 for row in rows if row["record_type"] == "share_reference"
                ),
            },
            "total": len(rows),
            "page": int(query.get("page") or 1),
            "page_size": page_size,
            "has_more": False,
            "timing_ms": 1,
        }

    def collect_search_export_rows(self, request: dict[str, Any] | None):
        result = self.query_search_v2(request)
        return list(result["items"]), 1, False


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="https://dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


@pytest.fixture
def fake_service() -> FakeDeweyService:
    return FakeDeweyService()


@pytest.fixture
def client(test_settings: Settings, fake_service: FakeDeweyService) -> TestClient:
    app = create_app(settings=test_settings, service=fake_service)
    with TestClient(app) as tc:
        yield tc
