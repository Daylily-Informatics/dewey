"""Shared helpers and public facade primitives for Dewey service mixins."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import quote

from itsdangerous import URLSafeTimedSerializer

from dewey_service.literature import LiteratureUnavailableError
from dewey_service.settings import get_settings
from dewey_service.storage import S3StorageClient
from dewey_service.tapdb_backend import (
    ANOMALY_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
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


class BaseDeweyService:
    """Shared state and helpers for Dewey domain mixins."""

    def __init__(
        self,
        backend: TapDBBackend,
        *,
        default_share_ttl_seconds: int = 3600,
        storage_client: S3StorageClient | None = None,
        managed_storage_bucket: str = "",
        managed_storage_prefix: str = "artifacts",
        upload_session_ttl_seconds: int = 900,
        upload_token_secret: str = "",
        search_export_max_rows: int = 1000,
        literature_adapter: Any | None = None,
        literature_allowed_domains: set[str] | None = None,
        literature_request_timeout_seconds: int = 10,
    ):
        self.backend = backend
        self.default_share_ttl_seconds = max(60, int(default_share_ttl_seconds))
        self.storage = storage_client
        self.managed_storage_bucket = str(managed_storage_bucket or "").strip()
        self.managed_storage_prefix = str(managed_storage_prefix or "artifacts").strip().strip("/")
        self.upload_session_ttl_seconds = max(60, int(upload_session_ttl_seconds))
        self.search_export_max_rows = max(100, int(search_export_max_rows))
        self.literature = literature_adapter
        self.literature_allowed_domains = {
            str(item or "").strip().lower()
            for item in (literature_allowed_domains or set())
            if str(item or "").strip()
        }
        self.literature_request_timeout_seconds = max(1, int(literature_request_timeout_seconds))
        self._upload_serializer = URLSafeTimedSerializer(
            str(upload_token_secret or "dewey-upload-secret"),
            salt="dewey-upload-session-v1",
        )

    def bootstrap(self) -> None:
        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            self._seed_default_anomalies(session)

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

    def _require_storage(self) -> S3StorageClient:
        if self.storage is None:
            raise RuntimeError("Storage operations are not configured for Dewey")
        return self.storage

    def _require_literature(self):
        if self.literature is None:
            raise LiteratureUnavailableError(
                "Literature endpoints require metapub to be installed from the forked source repo."
            )
        return self.literature

    @staticmethod
    def _safe_filename(value: str | None) -> str:
        candidate = str(value or "").strip()
        if not candidate:
            raise ValueError("artifact filename is required")
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip("-.")
        if not cleaned:
            raise ValueError(f"artifact filename {value!r} has no safe characters")
        return cleaned

    def _seed_default_anomalies(self, session) -> None:
        for payload in self._default_anomaly_payloads():
            existing = self.backend.find_by_json_field(
                session,
                template_code=ANOMALY_TEMPLATE,
                field="anomaly_identity_key",
                value=str(payload.get("anomaly_identity_key") or ""),
            )
            if existing is None:
                self.backend.create_instance(
                    session,
                    template_code=ANOMALY_TEMPLATE,
                    name=str(payload.get("title") or payload["anomaly_identity_key"]),
                    json_addl=payload,
                )

    def _default_anomaly_payloads(self) -> list[dict[str, Any]]:
        now_iso = utc_now_iso()
        return [
            {
                "anomaly_identity_key": "dewey.readiness.bootstrap_gap",
                "category": "readiness",
                "severity": "medium",
                "status": "open",
                "title": "Readiness probe observed a bootstrap gap",
                "summary": (
                    "The local readiness surface recorded a brief backend-unavailable "
                    "state during bootstrap."
                ),
                "source": "readyz",
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
                "occurrence_count": 1,
                "redacted_context": {"database_status": "unknown"},
                "recommended_action": "Review readiness and database startup timing.",
                "created_at": now_iso,
                "updated_at": now_iso,
            },
            {
                "anomaly_identity_key": "dewey.auth.session_activity_low",
                "category": "auth",
                "severity": "low",
                "status": "monitoring",
                "title": "Operator session activity is sparse",
                "summary": (
                    "No recent browser-session auth events are present in the local anomaly record."
                ),
                "source": "auth_health",
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
                "occurrence_count": 1,
                "redacted_context": {"recent_successes": 0},
                "recommended_action": (
                    "Confirm an operator can complete browser login during smoke testing."
                ),
                "created_at": now_iso,
                "updated_at": now_iso,
            },
            {
                "anomaly_identity_key": "dewey.storage.review_pending",
                "category": "storage",
                "severity": "high",
                "status": "open",
                "title": "Artifact storage review is pending",
                "summary": (
                    "This local anomaly record tracks artifacts that need a storage "
                    "verification review."
                ),
                "source": "storage",
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
                "occurrence_count": 1,
                "redacted_context": {"scope": "local demo record"},
                "recommended_action": (
                    "Inspect storage verification and retention status for recent artifacts."
                ),
                "created_at": now_iso,
                "updated_at": now_iso,
            },
        ]

    def list_anomalies(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=ANOMALY_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            payloads = [self._anomaly_response(item) for item in rows]
            severity_rank = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
                "info": 4,
            }
            payloads.sort(
                key=lambda item: (
                    severity_rank.get(str(item.get("severity") or "").lower(), 99),
                    str(item.get("title") or ""),
                    str(item.get("anomaly_id") or ""),
                )
            )
            return payloads

    def get_anomaly(self, anomaly_id: str) -> dict[str, Any]:
        clean_id = str(anomaly_id or "").strip()
        with self.backend.session_scope(commit=False) as session:
            anomaly = self.backend.find_by_euid(
                session,
                template_code=ANOMALY_TEMPLATE,
                euid=clean_id,
            )
            if anomaly is None:
                raise DeweyNotFoundError(f"Anomaly not found: {anomaly_id}")
            return self._anomaly_response(anomaly)

    @staticmethod
    def _parse_iso8601(value: str | None, *, field_name: str) -> datetime:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError(f"{field_name} is required")
        try:
            parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} must be ISO8601") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

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
                str(payload.get("storage_kind") or "object"),
                str(payload.get("node_kind") or "file"),
                str(payload.get("storage_backend") or ""),
                str(payload.get("bucket") or ""),
                str(payload.get("key") or ""),
                str(payload.get("version_id") or ""),
                checksum_value,
            ]
        )

    def _artifact_storage_console_url(self, payload: dict[str, Any]) -> str | None:
        if str(payload.get("storage_backend") or "").strip().lower() != "s3":
            return None
        bucket = str(payload.get("bucket") or "").strip()
        key = str(payload.get("key") or "").strip()
        if not bucket or not key:
            return None
        return (
            "https://s3.console.aws.amazon.com/s3/buckets/"
            f"{quote(bucket, safe='')}"
            f"?prefix={quote(key, safe='/')}&showversions=false"
        )

    def _artifact_response(self, artifact_instance) -> dict[str, Any]:
        payload = normalize_instance_payload(artifact_instance)
        storage_kind = str(payload.get("storage_kind") or "object").strip().lower() or "object"
        node_kind = str(payload.get("node_kind") or "file").strip().lower() or "file"
        is_terminal_raw = payload.get("is_terminal")
        is_terminal = bool(is_terminal_raw) if storage_kind == "prefix" else True
        return {
            "artifact_euid": artifact_instance.euid,
            "artifact_type": str(payload.get("artifact_type") or ""),
            "storage_kind": storage_kind,
            "node_kind": node_kind,
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
            "storage_console_url": self._artifact_storage_console_url(payload),
            "source_uri": payload.get("source_uri"),
            "import_mode": payload.get("import_mode"),
            "storage_status": payload.get("storage_status"),
            "storage_verified_at": payload.get("storage_verified_at"),
            "is_terminal": is_terminal,
            "retention_mode": payload.get("retention_mode"),
            "retain_until": payload.get("retain_until"),
            "share_status": payload.get("share_status"),
            "share_last_issued_at": payload.get("share_last_issued_at"),
            "created_at": str(payload.get("created_at") or utc_now_iso()),
        }

    def _anomaly_response(self, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        environment = str(
            payload.get("environment")
            or get_settings().deployment_name
            or get_settings().environment
            or "unknown"
        )
        fingerprint = str(
            payload.get("fingerprint") or payload.get("anomaly_identity_key") or instance.euid
        )
        summary = str(payload.get("summary") or payload.get("title") or "")
        return {
            "id": instance.euid,
            "service": str(payload.get("service") or "dewey"),
            "environment": environment,
            "fingerprint": fingerprint,
            "summary": summary,
            "anomaly_id": instance.euid,
            "anomaly_identity_key": payload.get("anomaly_identity_key"),
            "category": payload.get("category"),
            "severity": payload.get("severity"),
            "status": payload.get("status"),
            "title": payload.get("title"),
            "source": payload.get("source"),
            "first_seen_at": payload.get("first_seen_at"),
            "last_seen_at": payload.get("last_seen_at"),
            "occurrence_count": int(payload.get("occurrence_count") or 0),
            "redacted_context": dict(payload.get("redacted_context") or {}),
            "recommended_action": payload.get("recommended_action"),
            "source_view_url": f"/ui/anomalies/{instance.euid}",
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
            "metadata": dict(payload.get("metadata") or {}),
            "artifact_euids": artifact_euids,
            "member_count": len(artifact_euids),
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
            "transport": payload.get("transport"),
            "status": payload.get("status"),
            "starts_at": payload.get("starts_at"),
            "expires_at": payload.get("expires_at"),
            "access_url": payload.get("access_url"),
            "manifest": list(payload.get("manifest") or []),
            "connection": dict(payload.get("connection") or {}),
            "member_count": int(payload.get("member_count") or 0),
            "transport_config": dict(payload.get("transport_config") or {}),
            "issued_by": payload.get("issued_by"),
            "recipient_email": payload.get("recipient_email"),
            "managed_access": bool(payload.get("managed_access")),
            "access_count": int(payload.get("access_count") or 0),
            "last_accessed_at": payload.get("last_accessed_at"),
            "revoked_at": payload.get("revoked_at"),
            "revoked_by": payload.get("revoked_by"),
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
