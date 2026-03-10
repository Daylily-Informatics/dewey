"""Dewey domain service built on TapDB persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    SHARE_REFERENCE_TEMPLATE,
    TapDBBackend,
    normalize_instance_payload,
    utc_now_iso,
)


class DeweyNotFoundError(KeyError):
    """Raised when an entity is missing."""


class DeweyConflictError(RuntimeError):
    """Raised when a conflict occurs."""


@dataclass(frozen=True)
class IdempotencyReplay:
    status_code: int
    response: dict[str, Any]


class DeweyService:
    """Persistent Dewey artifact service."""

    def __init__(self, backend: TapDBBackend, *, default_share_ttl_seconds: int = 3600):
        self.backend = backend
        self.default_share_ttl_seconds = max(60, int(default_share_ttl_seconds))

    def bootstrap(self) -> None:
        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)

    @staticmethod
    def _fingerprint(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_storage(
        *,
        storage_backend: str,
        bucket: str,
        key: str,
        version_id: str | None,
    ) -> tuple[str, str, str, str | None, str]:
        backend = str(storage_backend or "s3").strip().lower() or "s3"
        bucket_value = str(bucket or "").strip()
        key_value = str(key or "").strip().lstrip("/")
        version_value = str(version_id or "").strip() or None
        if not bucket_value:
            raise ValueError("bucket is required")
        if not key_value:
            raise ValueError("key is required")
        storage_uri = f"{backend}://{bucket_value}/{key_value}"
        return backend, bucket_value, key_value, version_value, storage_uri

    def import_artifact_from_uri(
        self,
        *,
        artifact_type: str,
        storage_uri: str,
        metadata: dict[str, Any],
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        parsed = urlparse(str(storage_uri or "").strip())
        if parsed.scheme.lower() != "s3":
            raise ValueError("import currently supports s3:// URIs only")
        bucket = str(parsed.netloc or "").strip()
        key = str(parsed.path or "").strip().lstrip("/")
        return self.register_artifact(
            artifact_type=artifact_type,
            storage_backend="s3",
            bucket=bucket,
            key=key,
            version_id=None,
            size=metadata.get("size"),
            checksums=dict(metadata.get("checksums") or {}),
            content_type=str(
                metadata.get("content_type") or metadata.get("mime_type") or ""
            ).strip()
            or None,
            original_filename=str(metadata.get("original_filename") or "").strip() or None,
            producer_system=str(metadata.get("producer_system") or "").strip() or None,
            producer_object_euid=str(metadata.get("producer_object_euid") or "").strip() or None,
            storage_class=str(metadata.get("storage_class") or "").strip() or None,
            availability_status=str(metadata.get("availability_status") or "").strip() or None,
            metadata=dict(metadata or {}),
            idempotency_key=idempotency_key,
        )

    def register_artifact(
        self,
        *,
        artifact_type: str,
        storage_backend: str,
        bucket: str,
        key: str,
        version_id: str | None,
        size: int | None,
        checksums: dict[str, Any] | None,
        content_type: str | None,
        original_filename: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        storage_class: str | None,
        availability_status: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_artifact_type = str(artifact_type or "").strip().lower()
        if not clean_artifact_type:
            raise ValueError("artifact_type is required")
        backend, bucket_value, key_value, version_value, storage_uri = self._normalize_storage(
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=version_id,
        )

        payload = {
            "artifact_type": clean_artifact_type,
            "storage_backend": backend,
            "bucket": bucket_value,
            "key": key_value,
            "version_id": version_value,
            "size": int(size) if size is not None else None,
            "checksums": dict(checksums or {}),
            "content_type": str(content_type or "").strip() or None,
            "original_filename": str(original_filename or "").strip() or None,
            "producer_system": str(producer_system or "").strip() or None,
            "producer_object_euid": str(producer_object_euid or "").strip() or None,
            "storage_class": str(storage_class or "").strip() or None,
            "availability_status": str(availability_status or "").strip() or None,
            "metadata": dict(metadata or {}),
            "storage_uri": storage_uri,
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="artifact.register",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            identity_key = self._artifact_identity_key(payload)
            existing = self.backend.find_by_json_field(
                session,
                template_code=ARTIFACT_TEMPLATE,
                field="artifact_identity_key",
                value=identity_key,
            )
            if existing is not None:
                body = self._artifact_response(existing)
                self._store_idempotency(
                    session,
                    operation="artifact.register",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body

            now_iso = utc_now_iso()
            artifact = self.backend.create_instance(
                session,
                template_code=ARTIFACT_TEMPLATE,
                name=f"{clean_artifact_type}:{bucket_value}/{key_value}",
                json_addl={
                    "artifact_type": clean_artifact_type,
                    "storage_backend": backend,
                    "bucket": bucket_value,
                    "key": key_value,
                    "version_id": version_value,
                    "size": payload["size"],
                    "checksums": payload["checksums"],
                    "content_type": payload["content_type"],
                    "original_filename": payload["original_filename"],
                    "producer_system": payload["producer_system"],
                    "producer_object_euid": payload["producer_object_euid"],
                    "storage_class": payload["storage_class"],
                    "availability_status": payload["availability_status"],
                    "metadata": payload["metadata"],
                    "artifact_identity_key": identity_key,
                    "storage_uri": storage_uri,
                    "created_at": now_iso,
                },
            )
            body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.register",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def get_artifact(self, artifact_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=str(artifact_euid or "").strip(),
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
            return self._artifact_response(artifact)

    def list_artifacts(
        self,
        *,
        artifact_type: str | None = None,
        producer_system: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_type = str(artifact_type or "").strip().lower()
        clean_producer = str(producer_system or "").strip().lower()
        with self.backend.session_scope(commit=False) as session:
            items = self.backend.list_by_template(
                session,
                template_code=ARTIFACT_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            rows: list[dict[str, Any]] = []
            for item in items:
                payload = normalize_instance_payload(item)
                if clean_type and str(payload.get("artifact_type") or "").lower() != clean_type:
                    continue
                if (
                    clean_producer
                    and str(payload.get("producer_system") or "").lower() != clean_producer
                ):
                    continue
                rows.append(self._artifact_response(item))
            return rows

    def create_artifact_set(
        self,
        *,
        artifact_set_type: str,
        label: str | None,
        description: str | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_type = str(artifact_set_type or "").strip().lower()
        if not clean_type:
            raise ValueError("artifact_set_type is required")

        payload = {
            "artifact_set_type": clean_type,
            "label": str(label or "").strip() or None,
            "description": str(description or "").strip() or None,
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            now_iso = utc_now_iso()
            artifact_set = self.backend.create_instance(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                name=payload["label"] or f"artifact_set:{clean_type}",
                json_addl={
                    "artifact_set_type": clean_type,
                    "label": payload["label"],
                    "description": payload["description"],
                    "created_at": now_iso,
                },
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def add_artifact_set_member(
        self,
        *,
        artifact_set_euid: str,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_set_euid": str(artifact_set_euid or "").strip(),
            "artifact_euid": str(artifact_euid or "").strip(),
        }
        if not payload["artifact_set_euid"]:
            raise ValueError("artifact_set_euid is required")
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")

        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.member.add",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=payload["artifact_set_euid"],
                for_update=True,
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {payload['artifact_set_euid']}")

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            self.backend.create_lineage(
                session,
                parent=artifact_set,
                child=artifact,
                relationship_type="artifact_set_member",
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.member.add",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def remove_artifact_set_member(
        self,
        *,
        artifact_set_euid: str,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_set_euid": str(artifact_set_euid or "").strip(),
            "artifact_euid": str(artifact_euid or "").strip(),
        }
        if not payload["artifact_set_euid"]:
            raise ValueError("artifact_set_euid is required")
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")

        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.member.remove",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=payload["artifact_set_euid"],
                for_update=True,
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {payload['artifact_set_euid']}")

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            self.backend.delete_lineage(
                session,
                parent=artifact_set,
                child=artifact,
                relationship_type="artifact_set_member",
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.member.remove",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def get_artifact_set(self, artifact_set_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=str(artifact_set_euid or "").strip(),
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
            return self._artifact_set_response(session, artifact_set)

    def list_artifact_sets(
        self,
        *,
        artifact_set_type: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_type = str(artifact_set_type or "").strip().lower()
        with self.backend.session_scope(commit=False) as session:
            items = self.backend.list_by_template(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            rows: list[dict[str, Any]] = []
            for item in items:
                payload = normalize_instance_payload(item)
                if clean_type and str(payload.get("artifact_set_type") or "").lower() != clean_type:
                    continue
                rows.append(self._artifact_set_response(session, item))
            return rows

    def resolve_artifact(self, artifact_euid: str) -> dict[str, Any]:
        return self.get_artifact(artifact_euid)

    def resolve_artifact_set(self, artifact_set_euid: str) -> dict[str, Any]:
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
    ) -> tuple[int, dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        clean_target_euid = str(target_euid or "").strip()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")
        if not clean_target_euid:
            raise ValueError("target_euid is required")

        if clean_target_type == "artifact":
            self.get_artifact(clean_target_euid)
        else:
            self.get_artifact_set(clean_target_euid)

        expiry = self._normalize_expiry(expires_at)
        payload = {
            "target_type": clean_target_type,
            "target_euid": clean_target_euid,
            "purpose": str(purpose or "").strip() or None,
            "scope": str(scope or "").strip() or None,
            "expires_at": expiry,
            "issued_by": str(issued_by or "").strip() or None,
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="share_reference.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            instance = self.backend.create_instance(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                name=f"share:{clean_target_type}:{clean_target_euid}",
                json_addl={
                    "target_type": clean_target_type,
                    "target_euid": clean_target_euid,
                    "purpose": payload["purpose"],
                    "scope": payload["scope"],
                    "expires_at": payload["expires_at"],
                    "issued_by": payload["issued_by"],
                    "created_at": utc_now_iso(),
                },
            )
            body = self._share_reference_response(instance)
            self._store_idempotency(
                session,
                operation="share_reference.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
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
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "external_system": str(external_system or "").strip().lower(),
            "external_object_type": str(external_object_type or "").strip().lower(),
            "external_object_id": str(external_object_id or "").strip(),
            "external_uri": str(external_uri or "").strip() or None,
            "metadata": dict(metadata or {}),
        }
        if not payload["external_system"]:
            raise ValueError("external_system is required")
        if not payload["external_object_type"]:
            raise ValueError("external_object_type is required")
        if not payload["external_object_id"]:
            raise ValueError("external_object_id is required")

        fingerprint = self._fingerprint(payload)
        identity_key = f"{payload['external_system']}:{payload['external_object_type']}:{payload['external_object_id']}"

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="external_object.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            existing = self.backend.find_by_json_field(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                field="external_identity_key",
                value=identity_key,
            )
            if existing is not None:
                body = self._external_object_response(existing)
                self._store_idempotency(
                    session,
                    operation="external_object.create",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body

            created = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                name=identity_key,
                json_addl={
                    **payload,
                    "external_identity_key": identity_key,
                    "created_at": utc_now_iso(),
                },
            )
            body = self._external_object_response(created)
            self._store_idempotency(
                session,
                operation="external_object.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
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
    ) -> tuple[int, dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")

        payload = {
            "target_type": clean_target_type,
            "target_euid": str(target_euid or "").strip(),
            "external_object_euid": str(external_object_euid or "").strip(),
            "relation_type": str(relation_type or "").strip() or "linked",
            "metadata": dict(metadata or {}),
        }
        if not payload["target_euid"]:
            raise ValueError("target_euid is required")
        if not payload["external_object_euid"]:
            raise ValueError("external_object_euid is required")

        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="external_object_relation.attach",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            if clean_target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=payload["target_euid"],
                )
            else:
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=payload["target_euid"],
                )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {payload['target_euid']}")

            external_object = self.backend.find_by_euid(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                euid=payload["external_object_euid"],
            )
            if external_object is None:
                raise DeweyNotFoundError(
                    f"External object not found: {payload['external_object_euid']}"
                )

            relation_identity = (
                f"{payload['target_type']}:{payload['target_euid']}:"
                f"{payload['external_object_euid']}:{payload['relation_type']}"
            )
            existing = self.backend.find_by_json_field(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                field="relation_identity_key",
                value=relation_identity,
            )
            if existing is not None:
                body = self._external_object_relation_response(existing)
                self._store_idempotency(
                    session,
                    operation="external_object_relation.attach",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body

            relation = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                name=relation_identity,
                json_addl={
                    **payload,
                    "relation_identity_key": relation_identity,
                    "created_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=target,
                child=relation,
                relationship_type="has_external_relation",
            )
            self.backend.create_lineage(
                session,
                parent=external_object,
                child=relation,
                relationship_type="is_external_relation_for",
            )

            body = self._external_object_relation_response(relation)
            self._store_idempotency(
                session,
                operation="external_object_relation.attach",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def list_external_object_relations(
        self,
        *,
        target_type: str,
        target_euid: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")

        with self.backend.session_scope(commit=False) as session:
            if clean_target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=str(target_euid or "").strip(),
                )
            else:
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=str(target_euid or "").strip(),
                )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {target_euid}")

            rows = self.backend.list_children(
                session,
                parent=target,
                relationship_type="has_external_relation",
            )
            return [self._external_object_relation_response(row) for row in rows[:limit]]

    def _artifact_identity_key(self, payload: dict[str, Any]) -> str:
        checksum_value = ""
        checksums = payload.get("checksums") or {}
        if isinstance(checksums, dict):
            checksum_value = str(checksums.get("sha256") or checksums.get("md5") or "").strip()
        return ":".join(
            [
                str(payload.get("producer_system") or ""),
                str(payload.get("producer_object_euid") or ""),
                str(payload.get("artifact_type") or ""),
                str(payload.get("storage_backend") or ""),
                str(payload.get("bucket") or ""),
                str(payload.get("key") or ""),
                str(payload.get("version_id") or ""),
                checksum_value,
            ]
        )

    def _artifact_response(self, artifact_instance) -> dict[str, Any]:
        payload = normalize_instance_payload(artifact_instance)
        return {
            "artifact_euid": artifact_instance.euid,
            "artifact_type": str(payload.get("artifact_type") or ""),
            "storage_backend": str(payload.get("storage_backend") or ""),
            "bucket": str(payload.get("bucket") or ""),
            "key": str(payload.get("key") or ""),
            "version_id": payload.get("version_id"),
            "size": payload.get("size"),
            "checksums": dict(payload.get("checksums") or {}),
            "content_type": payload.get("content_type"),
            "original_filename": payload.get("original_filename"),
            "producer_system": payload.get("producer_system"),
            "producer_object_euid": payload.get("producer_object_euid"),
            "storage_class": payload.get("storage_class"),
            "availability_status": payload.get("availability_status"),
            "metadata": dict(payload.get("metadata") or {}),
            "storage_uri": str(payload.get("storage_uri") or ""),
            "created_at": str(payload.get("created_at") or utc_now_iso()),
        }

    def _artifact_set_response(self, session, artifact_set_instance) -> dict[str, Any]:
        payload = normalize_instance_payload(artifact_set_instance)
        members = self.backend.list_children(
            session,
            parent=artifact_set_instance,
            relationship_type="artifact_set_member",
        )
        artifact_euids = [member.euid for member in members]
        return {
            "artifact_set_euid": artifact_set_instance.euid,
            "artifact_set_type": str(payload.get("artifact_set_type") or ""),
            "label": payload.get("label"),
            "description": payload.get("description"),
            "artifact_euids": artifact_euids,
            "members": [self._artifact_response(member) for member in members],
            "created_at": str(payload.get("created_at") or utc_now_iso()),
        }

    def _share_reference_response(self, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        return {
            "share_reference_euid": instance.euid,
            "target_type": payload.get("target_type"),
            "target_euid": payload.get("target_euid"),
            "purpose": payload.get("purpose"),
            "scope": payload.get("scope"),
            "expires_at": payload.get("expires_at"),
            "issued_by": payload.get("issued_by"),
            "created_at": payload.get("created_at"),
        }

    def _external_object_response(self, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        return {
            "external_object_euid": instance.euid,
            "external_system": payload.get("external_system"),
            "external_object_type": payload.get("external_object_type"),
            "external_object_id": payload.get("external_object_id"),
            "external_uri": payload.get("external_uri"),
            "metadata": dict(payload.get("metadata") or {}),
            "created_at": payload.get("created_at"),
        }

    def _external_object_relation_response(self, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        return {
            "external_object_relation_euid": instance.euid,
            "target_type": payload.get("target_type"),
            "target_euid": payload.get("target_euid"),
            "external_object_euid": payload.get("external_object_euid"),
            "relation_type": payload.get("relation_type"),
            "metadata": dict(payload.get("metadata") or {}),
            "created_at": payload.get("created_at"),
        }

    def _idempotency_replay(
        self,
        session,
        *,
        operation: str,
        idempotency_key: str,
        fingerprint: str,
    ) -> IdempotencyReplay | None:
        clean_key = str(idempotency_key or "").strip()
        if not clean_key:
            raise ValueError("Idempotency-Key is required")
        lookup = f"{operation}:{clean_key}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=IDEMPOTENCY_TEMPLATE,
            field="idempotency_lookup_key",
            value=lookup,
        )
        if existing is None:
            return None
        payload = normalize_instance_payload(existing)
        stored_fingerprint = str(payload.get("request_fingerprint") or "")
        if stored_fingerprint != fingerprint:
            raise DeweyConflictError("Idempotency-Key reuse with different request payload")
        status_code = int(payload.get("status_code") or 200)
        response = payload.get("response")
        if not isinstance(response, dict):
            raise DeweyConflictError("Invalid stored idempotent response payload")
        return IdempotencyReplay(status_code=status_code, response=dict(response))

    def _store_idempotency(
        self,
        session,
        *,
        operation: str,
        idempotency_key: str,
        fingerprint: str,
        status_code: int,
        response: dict[str, Any],
    ) -> None:
        clean_key = str(idempotency_key or "").strip()
        if not clean_key:
            raise ValueError("Idempotency-Key is required")
        lookup = f"{operation}:{clean_key}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=IDEMPOTENCY_TEMPLATE,
            field="idempotency_lookup_key",
            value=lookup,
        )
        if existing is not None:
            return
        self.backend.create_instance(
            session,
            template_code=IDEMPOTENCY_TEMPLATE,
            name=lookup,
            json_addl={
                "operation": operation,
                "idempotency_key": clean_key,
                "idempotency_lookup_key": lookup,
                "request_fingerprint": fingerprint,
                "status_code": int(status_code),
                "response": dict(response),
                "created_at": utc_now_iso(),
            },
        )

    def _normalize_expiry(self, expires_at: str | None) -> str:
        clean = str(expires_at or "").strip()
        if clean:
            try:
                parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("expires_at must be ISO8601") from exc
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        auto = datetime.now(timezone.utc) + timedelta(seconds=self.default_share_ttl_seconds)
        return auto.isoformat().replace("+00:00", "Z")
