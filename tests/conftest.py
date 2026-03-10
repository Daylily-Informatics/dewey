from __future__ import annotations

import hashlib
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
        self.artifacts: dict[str, dict[str, Any]] = {}
        self.artifact_sets: dict[str, dict[str, Any]] = {}
        self.external_objects: dict[str, dict[str, Any]] = {}
        self.external_relations: list[dict[str, Any]] = []
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
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.artifacts[euid] = item
        self._remember("artifact.register", idempotency_key, payload, 201, item)
        return 201, dict(item)

    def import_artifact_from_uri(
        self,
        *,
        artifact_type: str,
        storage_uri: str,
        metadata: dict[str, Any],
        idempotency_key: str,
    ):
        if not storage_uri.startswith("s3://"):
            raise ValueError("import currently supports s3:// URIs only")
        bucket_and_key = storage_uri[5:]
        bucket, key = bucket_and_key.split("/", 1)
        return self.register_artifact(
            artifact_type=artifact_type,
            storage_backend="s3",
            bucket=bucket,
            key=key,
            version_id=None,
            size=metadata.get("size"),
            checksums=dict(metadata.get("checksums") or {}),
            content_type=metadata.get("content_type"),
            original_filename=metadata.get("original_filename"),
            producer_system=metadata.get("producer_system"),
            producer_object_euid=metadata.get("producer_object_euid"),
            storage_class=metadata.get("storage_class"),
            availability_status=metadata.get("availability_status"),
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

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
        idempotency_key: str,
    ):
        payload = {
            "target_type": target_type,
            "target_euid": target_euid,
            "purpose": purpose,
            "scope": scope,
            "expires_at": expires_at,
            "issued_by": issued_by,
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
            "expires_at": expires_at or "2026-03-10T12:00:00Z",
            "issued_by": issued_by,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self._remember("share_reference.create", idempotency_key, payload, 201, body)
        return 201, body

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


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="https://dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8913/auth/callback",
        cognito_logout_url="https://localhost:8913/login",
    )


@pytest.fixture
def fake_service() -> FakeDeweyService:
    return FakeDeweyService()


@pytest.fixture
def client(test_settings: Settings, fake_service: FakeDeweyService) -> TestClient:
    app = create_app(settings=test_settings, service=fake_service)
    with TestClient(app) as tc:
        yield tc
