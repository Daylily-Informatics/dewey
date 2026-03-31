"""Dewey domain service built on TapDB persistence."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from dewey_service.literature import (
    LiteratureUnavailableError,
    ViewerContext,
    classify_fulltext,
    dedupe_strings,
    normalize_doi,
    normalize_email_list,
    normalize_group_list,
    normalize_pmcid,
    normalize_pmid,
)
from dewey_service.storage import (
    S3StorageClient,
    StorageObject,
    StorageObjectNotFoundError,
    StoragePermissionError,
)
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ANOMALY_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    LITERATURE_SAVE_TEMPLATE,
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
    def _safe_filename(value: str | None, fallback: str = "artifact.bin") -> str:
        candidate = str(value or "").strip() or fallback
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip("-.")
        return cleaned or fallback

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
                "summary": "The local readiness surface recorded a brief backend-unavailable state during bootstrap.",
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
                "summary": "No recent browser-session auth events are present in the local anomaly record.",
                "source": "auth_health",
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
                "occurrence_count": 1,
                "redacted_context": {"recent_successes": 0},
                "recommended_action": "Confirm an operator can complete browser login during smoke testing.",
                "created_at": now_iso,
                "updated_at": now_iso,
            },
            {
                "anomaly_identity_key": "dewey.storage.review_pending",
                "category": "storage",
                "severity": "high",
                "status": "open",
                "title": "Artifact storage review is pending",
                "summary": "This local anomaly record tracks artifacts that need a storage verification review.",
                "source": "storage",
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
                "occurrence_count": 1,
                "redacted_context": {"scope": "local demo record"},
                "recommended_action": "Inspect storage verification and retention status for recent artifacts.",
                "created_at": now_iso,
                "updated_at": now_iso,
            },
        ]

    @staticmethod
    def _parse_s3_uri(uri: str) -> tuple[str, str]:
        parsed = urlparse(str(uri or "").strip())
        if parsed.scheme.lower() != "s3":
            raise ValueError("source_uri must use s3:// for S3 import flows")
        bucket = str(parsed.netloc or "").strip()
        key = str(parsed.path or "").strip().lstrip("/")
        if not bucket or not key:
            raise ValueError("source_uri must include bucket and key")
        return bucket, key

    @staticmethod
    def _source_filename(source_uri: str, original_filename: str | None = None) -> str:
        explicit = str(original_filename or "").strip()
        if explicit:
            return explicit
        parsed = urlparse(str(source_uri or "").strip())
        candidate = str(parsed.path or "").strip().rstrip("/").split("/")[-1]
        return candidate or "artifact.bin"

    def expand_s3_sources(self, source_uri: str, *, limit: int = 1000) -> list[str]:
        bucket, key = self._parse_s3_uri(source_uri)
        storage = self._require_storage()
        clean_uri = str(source_uri or "").strip()
        if clean_uri.endswith("/"):
            objects = storage.list_objects(bucket=bucket, prefix=key, limit=limit)
            if not objects:
                raise DeweyNotFoundError(f"No S3 objects found for prefix: {source_uri}")
            return [self._storage_uri("s3", bucket, item.key) for item in objects]
        try:
            storage.head_object(bucket=bucket, key=key)
            return [self._storage_uri("s3", bucket, key)]
        except StorageObjectNotFoundError:
            prefix = key.rstrip("/") + "/"
            objects = storage.list_objects(bucket=bucket, prefix=prefix, limit=limit)
            if not objects:
                raise DeweyNotFoundError(f"S3 object or prefix not found: {source_uri}")
            return [self._storage_uri("s3", bucket, item.key) for item in objects]

    @staticmethod
    def _filename_suffix(value: str) -> str:
        candidate = str(value or "").strip()
        if not candidate:
            return ""
        suffixes = Path(candidate).suffixes
        return "".join(suffixes) if suffixes else ""

    @staticmethod
    def _dedupe_filename(filename: str, used: set[str]) -> str:
        if filename not in used:
            used.add(filename)
            return filename
        stem = Path(filename).stem or "artifact"
        suffix = "".join(Path(filename).suffixes)
        counter = 2
        while True:
            candidate = f"{stem}-{counter}{suffix}"
            if candidate not in used:
                used.add(candidate)
                return candidate
            counter += 1

    def _download_filename(self, artifact: dict[str, Any], naming_mode: str) -> str:
        clean_mode = str(naming_mode or "hybrid").strip().lower() or "hybrid"
        original_name = self._safe_filename(
            artifact.get("original_filename"),
            fallback=f"{artifact['artifact_euid']}.bin",
        )
        suffix = self._filename_suffix(original_name)
        if clean_mode == "dewey":
            return self._safe_filename(f"{artifact['artifact_euid']}{suffix or '.bin'}")
        if clean_mode == "orig":
            return original_name
        return self._safe_filename(f"{artifact['artifact_euid']}.{original_name}")

    def _download_artifact_bytes(self, artifact: dict[str, Any]) -> bytes:
        backend = str(artifact.get("storage_backend") or "").strip().lower()
        if backend == "s3":
            return self._require_storage().get_object_bytes(
                bucket=str(artifact.get("bucket") or ""),
                key=str(artifact.get("key") or ""),
                version_id=str(artifact.get("version_id") or "").strip() or None,
            )
        source_uri = str(artifact.get("source_uri") or "").strip()
        if source_uri.startswith(("https://", "http://")):
            response = requests.get(source_uri, timeout=60)
            response.raise_for_status()
            return bytes(response.content)
        raise ValueError(f"direct download unsupported for storage backend: {backend or 'unknown'}")

    def build_artifact_download_archive(
        self,
        *,
        artifact_euids: list[str],
        naming_mode: str = "hybrid",
        include_metadata: bool = True,
    ) -> tuple[str, bytes]:
        selected = [str(item or "").strip() for item in artifact_euids if str(item or "").strip()]
        if not selected:
            raise ValueError("at least one artifact_euid is required")
        seen: set[str] = set()
        buffer = io.BytesIO()
        archive_name = f"dewey-artifacts-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.zip"
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for artifact_euid in selected:
                artifact = self.get_artifact(artifact_euid)
                filename = self._dedupe_filename(
                    self._download_filename(artifact, naming_mode),
                    seen,
                )
                zf.writestr(filename, self._download_artifact_bytes(artifact))
                if include_metadata:
                    metadata_name = self._dedupe_filename(f"{filename}.dewey.yaml", seen)
                    zf.writestr(
                        metadata_name,
                        yaml.safe_dump(
                            artifact,
                            sort_keys=True,
                            allow_unicode=False,
                        ),
                    )
        return archive_name, buffer.getvalue()

    def _managed_key(self, *, namespace: str, seed: str, filename: str) -> str:
        prefix = "/".join(
            item
            for item in [
                self.managed_storage_prefix,
                namespace,
                self._fingerprint({"seed": seed})[:16],
            ]
            if item
        )
        return f"{prefix}/{self._safe_filename(filename)}"

    @staticmethod
    def _storage_uri(storage_backend: str, bucket: str, key: str) -> str:
        return f"{storage_backend}://{bucket}/{key}"

    @staticmethod
    def _object_updates(obj: StorageObject) -> dict[str, Any]:
        return {
            "version_id": obj.version_id,
            "size": obj.size,
            "content_type": obj.content_type,
            "storage_class": obj.storage_class,
            "availability_status": "available",
        }

    def _artifact_payload(
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
        source_uri: str | None = None,
        import_mode: str | None = None,
        storage_status: str | None = None,
        storage_verified_at: str | None = None,
        retention_mode: str | None = None,
        retain_until: str | None = None,
        share_status: str | None = None,
        share_last_issued_at: str | None = None,
        artifact_identity_key: str | None = None,
    ) -> dict[str, Any]:
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
            "source_uri": str(source_uri or storage_uri).strip() or storage_uri,
            "import_mode": str(import_mode or "register").strip().lower() or "register",
            "storage_status": str(storage_status or "registered").strip().lower() or "registered",
            "storage_verified_at": str(storage_verified_at or "").strip() or None,
            "retention_mode": str(retention_mode or "").strip().upper() or None,
            "retain_until": str(retain_until or "").strip() or None,
            "share_status": str(share_status or "").strip().lower() or None,
            "share_last_issued_at": str(share_last_issued_at or "").strip() or None,
        }
        payload["artifact_identity_key"] = str(
            artifact_identity_key or ""
        ).strip() or self._artifact_identity_key(payload)
        return payload

    def _tag_artifact_object(
        self,
        *,
        artifact_payload: dict[str, Any],
        artifact_euid: str,
        tolerate_permission_errors: bool = False,
    ) -> None:
        if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
            return
        storage = self._require_storage()
        tags = {
            "dewey_artifact_euid": artifact_euid,
            "dewey_artifact_type": str(artifact_payload.get("artifact_type") or ""),
        }
        original_filename = str(artifact_payload.get("original_filename") or "").strip()
        if original_filename:
            tags["dewey_original_file_name"] = original_filename
        try:
            storage.put_object_tags(
                bucket=str(artifact_payload.get("bucket") or ""),
                key=str(artifact_payload.get("key") or ""),
                tags=tags,
            )
        except StoragePermissionError:
            if not tolerate_permission_errors:
                raise

    def _lock_artifact_payload(
        self,
        *,
        artifact_payload: dict[str, Any],
        mode: str,
        retain_until: datetime,
    ) -> None:
        if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
            raise ValueError("storage lock requires an s3-backed artifact")
        storage = self._require_storage()
        storage.set_retention(
            bucket=str(artifact_payload.get("bucket") or ""),
            key=str(artifact_payload.get("key") or ""),
            mode=mode,
            retain_until=retain_until,
        )

    def _upsert_artifact_record(
        self,
        session,
        *,
        payload: dict[str, Any],
        created_at: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        existing = self.backend.find_by_json_field(
            session,
            template_code=ARTIFACT_TEMPLATE,
            field="artifact_identity_key",
            value=str(payload.get("artifact_identity_key") or ""),
        )
        if existing is not None:
            return 200, self._artifact_response(existing)

        artifact = self.backend.create_instance(
            session,
            template_code=ARTIFACT_TEMPLATE,
            name=f"{payload['artifact_type']}:{payload['bucket']}/{payload['key']}",
            json_addl={
                **payload,
                "created_at": created_at or utc_now_iso(),
            },
        )
        return 201, self._artifact_response(artifact)

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
    ) -> tuple[int, dict[str, Any]]:
        source_value = str(source_uri or storage_uri or "").strip()
        if not source_value:
            raise ValueError("source_uri is required")

        mode = str(import_mode or "").strip().lower() or "reference"
        if mode not in {"copy", "reference"}:
            raise ValueError("import_mode must be copy or reference")

        meta = dict(metadata or {})
        clean_producer_system = (
            str(producer_system or meta.get("producer_system") or "").strip() or None
        )
        clean_producer_euid = (
            str(producer_object_euid or meta.get("producer_object_euid") or "").strip() or None
        )
        original_filename = self._source_filename(
            source_value,
            str(meta.get("original_filename") or "").strip() or None,
        )
        payload = {
            "artifact_type": str(artifact_type or "").strip().lower(),
            "source_uri": source_value,
            "import_mode": mode,
            "lock_after_import": bool(lock_after_import),
            "producer_system": clean_producer_system,
            "producer_object_euid": clean_producer_euid,
            "metadata": meta,
        }
        fingerprint = self._fingerprint(payload)
        parsed = urlparse(source_value)
        scheme = str(parsed.scheme or "").strip().lower()
        if scheme not in {"s3", "https", "http"}:
            raise ValueError("source_uri must use s3:// or https://")
        if mode == "reference" and scheme != "s3":
            raise ValueError("reference import requires an s3:// source_uri")

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.import",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            now_iso = utc_now_iso()
            storage = self._require_storage()

            if mode == "reference":
                source_bucket, source_key = self._parse_s3_uri(source_value)
                source_object = storage.head_object(bucket=source_bucket, key=source_key)
                artifact_payload = self._artifact_payload(
                    artifact_type=payload["artifact_type"],
                    storage_backend="s3",
                    bucket=source_bucket,
                    key=source_key,
                    version_id=source_object.version_id,
                    size=meta.get("size") or source_object.size,
                    checksums=dict(meta.get("checksums") or {}),
                    content_type=(
                        str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                        or source_object.content_type
                    ),
                    original_filename=original_filename,
                    producer_system=clean_producer_system,
                    producer_object_euid=clean_producer_euid,
                    storage_class=str(meta.get("storage_class") or "").strip()
                    or source_object.storage_class,
                    availability_status=str(meta.get("availability_status") or "").strip()
                    or "available",
                    metadata=meta,
                    source_uri=source_value,
                    import_mode="reference",
                    storage_status="verified",
                    storage_verified_at=now_iso,
                )
                status_code, body = self._upsert_artifact_record(
                    session,
                    payload=artifact_payload,
                    created_at=now_iso,
                )
                if status_code == 201:
                    self._tag_artifact_object(
                        artifact_payload=artifact_payload,
                        artifact_euid=body["artifact_euid"],
                        tolerate_permission_errors=True,
                    )
                if lock_after_import:
                    artifact = self.backend.find_by_euid(
                        session,
                        template_code=ARTIFACT_TEMPLATE,
                        euid=body["artifact_euid"],
                        for_update=True,
                    )
                    if artifact is None:
                        raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                    retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                    self._lock_artifact_payload(
                        artifact_payload=artifact_payload,
                        mode="GOVERNANCE",
                        retain_until=retain_until,
                    )
                    self.backend.update_instance_json(
                        session,
                        artifact,
                        {
                            "retention_mode": "GOVERNANCE",
                            "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                        },
                    )
                    body = self._artifact_response(artifact)
                self._store_idempotency(
                    session,
                    operation="artifact.import",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=status_code,
                    response=body,
                )
                return status_code, body

            if not self.managed_storage_bucket:
                raise ValueError("managed_storage_bucket is required for copy imports")

            dest_key = self._managed_key(
                namespace="imports",
                seed=f"{payload['artifact_type']}:{source_value}",
                filename=original_filename,
            )
            dest_object: StorageObject
            try:
                dest_object = storage.head_object(
                    bucket=self.managed_storage_bucket,
                    key=dest_key,
                )
            except StorageObjectNotFoundError:
                if scheme == "s3":
                    source_bucket, source_key = self._parse_s3_uri(source_value)
                    storage.head_object(bucket=source_bucket, key=source_key)
                    dest_object = storage.copy_object(
                        source_bucket=source_bucket,
                        source_key=source_key,
                        dest_bucket=self.managed_storage_bucket,
                        dest_key=dest_key,
                    )
                else:
                    response = requests.get(source_value, timeout=60)
                    response.raise_for_status()
                    dest_object = storage.put_bytes(
                        bucket=self.managed_storage_bucket,
                        key=dest_key,
                        body=response.content,
                        content_type=(
                            str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                            or str(response.headers.get("content-type") or "").strip()
                            or None
                        ),
                    )

            artifact_payload = self._artifact_payload(
                artifact_type=payload["artifact_type"],
                storage_backend="s3",
                bucket=self.managed_storage_bucket,
                key=dest_key,
                version_id=dest_object.version_id,
                size=meta.get("size") or dest_object.size,
                checksums=dict(meta.get("checksums") or {}),
                content_type=(
                    str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                    or dest_object.content_type
                ),
                original_filename=original_filename,
                producer_system=clean_producer_system,
                producer_object_euid=clean_producer_euid,
                storage_class=str(meta.get("storage_class") or "").strip()
                or dest_object.storage_class,
                availability_status=str(meta.get("availability_status") or "").strip()
                or "available",
                metadata=meta,
                source_uri=source_value,
                import_mode="copy",
                storage_status="verified",
                storage_verified_at=now_iso,
            )
            status_code, body = self._upsert_artifact_record(
                session,
                payload=artifact_payload,
                created_at=now_iso,
            )
            if status_code == 201:
                self._tag_artifact_object(
                    artifact_payload=artifact_payload,
                    artifact_euid=body["artifact_euid"],
                )
            if lock_after_import:
                artifact = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=body["artifact_euid"],
                    for_update=True,
                )
                if artifact is None:
                    raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                self._lock_artifact_payload(
                    artifact_payload=artifact_payload,
                    mode="GOVERNANCE",
                    retain_until=retain_until,
                )
                self.backend.update_instance_json(
                    session,
                    artifact,
                    {
                        "retention_mode": "GOVERNANCE",
                        "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                    },
                )
                body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.import",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

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
    ) -> tuple[int, dict[str, Any]]:
        if not self.managed_storage_bucket:
            raise ValueError("managed_storage_bucket is required for upload sessions")
        clean_type = str(artifact_type or "").strip().lower()
        if not clean_type:
            raise ValueError("artifact_type is required")
        clean_filename = self._safe_filename(original_filename, fallback="upload.bin")
        payload = {
            "artifact_type": clean_type,
            "original_filename": clean_filename,
            "content_type": str(content_type or "").strip() or None,
            "producer_system": str(producer_system or "").strip() or None,
            "producer_object_euid": str(producer_object_euid or "").strip() or None,
            "metadata": dict(metadata or {}),
            "lock_after_import": bool(lock_after_import),
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.upload_session.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            storage = self._require_storage()
            key = self._managed_key(
                namespace="uploads",
                seed=f"{idempotency_key}:{fingerprint}",
                filename=clean_filename,
            )
            upload = storage.generate_presigned_upload(
                bucket=self.managed_storage_bucket,
                key=key,
                expires_in=self.upload_session_ttl_seconds,
                content_type=payload["content_type"],
            )
            token = self._upload_serializer.dumps(
                {
                    **payload,
                    "bucket": self.managed_storage_bucket,
                    "key": key,
                    "storage_uri": self._storage_uri("s3", self.managed_storage_bucket, key),
                }
            )
            body = {
                "upload_token": token,
                "upload_method": upload["method"],
                "upload_url": upload["url"],
                "upload_headers": upload["headers"],
                "bucket": self.managed_storage_bucket,
                "key": key,
                "storage_uri": self._storage_uri("s3", self.managed_storage_bucket, key),
                "expires_in": self.upload_session_ttl_seconds,
                "created_at": utc_now_iso(),
            }
            self._store_idempotency(
                session,
                operation="artifact.upload_session.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def complete_upload_session(
        self,
        *,
        upload_token: str,
        checksums: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        try:
            token_payload = self._upload_serializer.loads(
                str(upload_token or "").strip(),
                max_age=self.upload_session_ttl_seconds,
            )
        except SignatureExpired as exc:
            raise ValueError("upload_token has expired") from exc
        except BadSignature as exc:
            raise ValueError("upload_token is invalid") from exc

        if not isinstance(token_payload, dict):
            raise ValueError("upload_token is invalid")

        merged_metadata = dict(token_payload.get("metadata") or {})
        merged_metadata.update(dict(metadata or {}))
        payload = {
            "upload_token": str(upload_token or "").strip(),
            "checksums": dict(checksums or {}),
            "metadata": merged_metadata,
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.upload_session.complete",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            storage = self._require_storage()
            try:
                obj = storage.head_object(
                    bucket=str(token_payload.get("bucket") or "").strip(),
                    key=str(token_payload.get("key") or "").strip(),
                )
            except StorageObjectNotFoundError as exc:
                raise DeweyNotFoundError("Uploaded object not found") from exc

            now_iso = utc_now_iso()
            artifact_payload = self._artifact_payload(
                artifact_type=str(token_payload.get("artifact_type") or ""),
                storage_backend="s3",
                bucket=str(token_payload.get("bucket") or "").strip(),
                key=str(token_payload.get("key") or "").strip(),
                version_id=obj.version_id,
                size=obj.size,
                checksums=dict(checksums or {}),
                content_type=(
                    str(
                        merged_metadata.get("content_type")
                        or merged_metadata.get("mime_type")
                        or ""
                    ).strip()
                    or str(token_payload.get("content_type") or "").strip()
                    or obj.content_type
                ),
                original_filename=str(token_payload.get("original_filename") or "").strip() or None,
                producer_system=str(token_payload.get("producer_system") or "").strip() or None,
                producer_object_euid=str(token_payload.get("producer_object_euid") or "").strip()
                or None,
                storage_class=obj.storage_class,
                availability_status="available",
                metadata=merged_metadata,
                source_uri=str(token_payload.get("storage_uri") or "").strip() or None,
                import_mode="upload",
                storage_status="verified",
                storage_verified_at=now_iso,
            )
            status_code, body = self._upsert_artifact_record(
                session,
                payload=artifact_payload,
                created_at=now_iso,
            )
            if status_code == 201:
                self._tag_artifact_object(
                    artifact_payload=artifact_payload,
                    artifact_euid=body["artifact_euid"],
                )
            if bool(token_payload.get("lock_after_import")):
                artifact = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=body["artifact_euid"],
                    for_update=True,
                )
                if artifact is None:
                    raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                self._lock_artifact_payload(
                    artifact_payload=artifact_payload,
                    mode="GOVERNANCE",
                    retain_until=retain_until,
                )
                self.backend.update_instance_json(
                    session,
                    artifact,
                    {
                        "retention_mode": "GOVERNANCE",
                        "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                    },
                )
                body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.upload_session.complete",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def upload_artifact_bytes(
        self,
        *,
        artifact_type: str,
        original_filename: str,
        body: bytes,
        content_type: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        metadata: dict[str, Any] | None,
        lock_after_import: bool,
        idempotency_key: str,
        checksums: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        _, upload = self.create_upload_session(
            artifact_type=artifact_type,
            original_filename=original_filename,
            content_type=content_type,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            metadata=metadata,
            lock_after_import=lock_after_import,
            idempotency_key=f"{idempotency_key}:create",
        )
        self._require_storage().put_bytes(
            bucket=str(upload.get("bucket") or ""),
            key=str(upload.get("key") or ""),
            body=body,
            content_type=content_type,
        )
        return self.complete_upload_session(
            upload_token=str(upload.get("upload_token") or ""),
            checksums=checksums,
            metadata=metadata,
            idempotency_key=f"{idempotency_key}:complete",
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
        payload = self._artifact_payload(
            artifact_type=artifact_type,
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=version_id,
            size=size,
            checksums=checksums,
            content_type=content_type,
            original_filename=original_filename,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            storage_class=storage_class,
            availability_status=availability_status,
            metadata=metadata,
            source_uri=self._storage_uri(
                str(storage_backend or "s3").strip().lower() or "s3",
                str(bucket or "").strip(),
                str(key or "").strip().lstrip("/"),
            ),
            import_mode="register",
            storage_status="registered",
        )
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

            status_code, body = self._upsert_artifact_record(
                session,
                payload=payload,
                created_at=utc_now_iso(),
            )
            self._store_idempotency(
                session,
                operation="artifact.register",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

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

    def verify_artifact_storage(
        self,
        *,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {"artifact_euid": str(artifact_euid or "").strip()}
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.storage.verify",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
                for_update=True,
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            artifact_payload = normalize_instance_payload(artifact)
            storage = self._require_storage()
            updates: dict[str, Any]
            status_code = 200
            try:
                obj = storage.head_object(
                    bucket=str(artifact_payload.get("bucket") or ""),
                    key=str(artifact_payload.get("key") or ""),
                    version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                )
                updates = {
                    **self._object_updates(obj),
                    "storage_status": "verified",
                    "storage_verified_at": utc_now_iso(),
                }
            except StorageObjectNotFoundError:
                updates = {
                    "availability_status": "missing",
                    "storage_status": "missing",
                    "storage_verified_at": utc_now_iso(),
                }
            self.backend.update_instance_json(session, artifact, updates)
            body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.storage.verify",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def lock_artifact_storage(
        self,
        *,
        artifact_euid: str,
        mode: str,
        retain_until: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_euid": str(artifact_euid or "").strip(),
            "mode": str(mode or "GOVERNANCE").strip().upper() or "GOVERNANCE",
            "retain_until": str(retain_until or "").strip(),
        }
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")
        retain_until_dt = self._parse_iso8601(payload["retain_until"], field_name="retain_until")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.storage.lock",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
                for_update=True,
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            artifact_payload = normalize_instance_payload(artifact)
            self._lock_artifact_payload(
                artifact_payload=artifact_payload,
                mode=payload["mode"],
                retain_until=retain_until_dt,
            )
            self.backend.update_instance_json(
                session,
                artifact,
                {
                    "retention_mode": payload["mode"],
                    "retain_until": retain_until_dt.isoformat().replace("+00:00", "Z"),
                },
            )
            body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.storage.lock",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def get_share_reference(self, share_reference_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            instance = self.backend.find_by_euid(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                euid=str(share_reference_euid or "").strip(),
            )
            if instance is None:
                raise DeweyNotFoundError(f"Share reference not found: {share_reference_euid}")
            return self._share_reference_response(instance)

    def list_share_references(
        self,
        *,
        target_type: str | None = None,
        target_euid: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        clean_target_euid = str(target_euid or "").strip()
        if clean_target_type and clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")

        with self.backend.session_scope(commit=False) as session:
            if clean_target_type and clean_target_euid:
                template_code = (
                    ARTIFACT_TEMPLATE if clean_target_type == "artifact" else ARTIFACT_SET_TEMPLATE
                )
                target = self.backend.find_by_euid(
                    session,
                    template_code=template_code,
                    euid=clean_target_euid,
                )
                if target is None:
                    raise DeweyNotFoundError(f"Target not found: {clean_target_euid}")
                rows = self.backend.list_children(
                    session,
                    parent=target,
                    relationship_type="has_share_reference",
                )
                return [self._share_reference_response(row) for row in rows[:limit]]

            rows = self.backend.list_by_template(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            return [self._share_reference_response(row) for row in rows]

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

    def search_literature(
        self,
        *,
        viewer: ViewerContext,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        adapter = self._require_literature()
        started = perf_counter()
        raw_items = adapter.search(query=query, page=page, page_size=page_size)
        with self.backend.session_scope(commit=False) as session:
            items = [
                self._enrich_literature_search_item(
                    session,
                    record=item,
                    viewer=viewer,
                )
                for item in raw_items
            ]
        timing_ms = int((perf_counter() - started) * 1000)
        return {
            "items": items,
            "total": len(items),
            "page": max(1, int(page)),
            "page_size": max(1, int(page_size)),
            "has_more": len(items) >= max(1, int(page_size)),
            "timing_ms": timing_ms,
        }

    def save_literature(
        self,
        *,
        viewer: ViewerContext,
        pmid: str,
        save_mode: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_mode = str(save_mode or "").strip().lower() or "auto"
        if clean_mode not in {"auto", "managed_artifact", "external_reference"}:
            raise ValueError("save_mode must be auto, managed_artifact, or external_reference")
        visibility = self._normalize_literature_visibility(
            visibility_scope=visibility_scope,
            allowed_users=allowed_users,
            allowed_groups=allowed_groups,
        )
        clean_pmid = normalize_pmid(pmid)
        fingerprint_payload = {
            "viewer_subject": viewer.subject,
            "pmid": clean_pmid,
            "save_mode": clean_mode,
            **visibility,
        }
        fingerprint = self._fingerprint(fingerprint_payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="literature.save",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            adapter = self._require_literature()
            record = adapter.fetch_record(clean_pmid)
            artifact_status_code, artifact = self._create_or_update_literature_artifact(
                session,
                record=record,
                save_mode=clean_mode,
            )
            artifact_instance = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=artifact["artifact_euid"],
                for_update=True,
            )
            if artifact_instance is None:
                raise DeweyNotFoundError(f"Artifact not found: {artifact['artifact_euid']}")

            self._ensure_literature_external_identities(
                session,
                artifact_instance=artifact_instance,
                record=record,
            )
            save_status_code, literature_save = self._upsert_literature_save(
                session,
                artifact_instance=artifact_instance,
                viewer=viewer,
                visibility=visibility,
            )
            body = {
                "artifact": self._artifact_response(artifact_instance),
                "literature_save": literature_save,
            }
            status_code = 201 if artifact_status_code == 201 or save_status_code == 201 else 200
            self._store_idempotency(
                session,
                operation="literature.save",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def update_literature_save_visibility(
        self,
        *,
        viewer: ViewerContext,
        literature_save_euid: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        visibility = self._normalize_literature_visibility(
            visibility_scope=visibility_scope,
            allowed_users=allowed_users,
            allowed_groups=allowed_groups,
        )
        payload = {
            "viewer_subject": viewer.subject,
            "literature_save_euid": str(literature_save_euid or "").strip(),
            **visibility,
        }
        if not payload["literature_save_euid"]:
            raise ValueError("literature_save_euid is required")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="literature.save.visibility.update",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            instance = self.backend.find_by_euid(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                euid=payload["literature_save_euid"],
                for_update=True,
            )
            if instance is None:
                raise DeweyNotFoundError(
                    f"Literature save not found: {payload['literature_save_euid']}"
                )

            existing_payload = normalize_instance_payload(instance)
            if str(existing_payload.get("owner_subject") or "") != viewer.subject:
                raise DeweyConflictError("Only the owner can update literature save visibility")

            self.backend.update_instance_json(
                session,
                instance,
                {
                    **visibility,
                    "updated_at": utc_now_iso(),
                },
            )
            body = self._literature_save_response(session, instance)
            self._store_idempotency(
                session,
                operation="literature.save.visibility.update",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def list_my_literature_saves(
        self,
        *,
        viewer: ViewerContext,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                limit=max(1, min(int(limit), 2000)),
            )
            return [
                self._literature_save_response(session, row)
                for row in rows
                if str(normalize_instance_payload(row).get("owner_subject") or "") == viewer.subject
            ]

    def _normalize_literature_visibility(
        self,
        *,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
    ) -> dict[str, Any]:
        clean_scope = str(visibility_scope or "").strip().lower() or "private"
        if clean_scope not in {"private", "restricted", "all_users"}:
            raise ValueError("visibility_scope must be private, restricted, or all_users")
        if clean_scope == "private":
            return {
                "visibility_scope": "private",
                "allowed_users": [],
                "allowed_groups": [],
            }
        if clean_scope == "all_users":
            return {
                "visibility_scope": "all_users",
                "allowed_users": [],
                "allowed_groups": [],
            }
        return {
            "visibility_scope": "restricted",
            "allowed_users": normalize_email_list(allowed_users),
            "allowed_groups": normalize_group_list(allowed_groups),
        }

    def _enrich_literature_search_item(
        self,
        session,
        *,
        record: dict[str, Any],
        viewer: ViewerContext,
    ) -> dict[str, Any]:
        artifact = self._resolve_literature_artifact(
            session,
            pmid=record.get("pmid"),
            doi=record.get("doi"),
            pmcid=record.get("pmcid"),
        )
        visibility = {
            "saved_by_me": False,
            "saved_by_others_count": 0,
            "visible_owner_labels": [],
        }
        artifact_euid = None
        storage_mode = "external_reference"
        if artifact is not None:
            artifact_payload = self._artifact_response(artifact)
            artifact_euid = artifact.euid
            metadata = dict(artifact_payload.get("metadata") or {})
            storage_mode = str(metadata.get("storage_mode") or "external_reference")
            visibility = self._visible_literature_save_summary(session, artifact, viewer)
        fulltext = classify_fulltext(
            best_fulltext_url=record.get("best_fulltext_url"),
            findit_reason=record.get("findit_reason"),
            allowed_domains=self.literature_allowed_domains,
        )
        if artifact is None:
            storage_mode = "managed" if fulltext["downloadable"] else "external_reference"
        return {
            **record,
            **fulltext,
            "storage_mode": storage_mode,
            "artifact_euid": artifact_euid,
            "already_in_dewey": artifact is not None,
            **visibility,
        }

    def _create_or_update_literature_artifact(
        self,
        session,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> tuple[int, dict[str, Any]]:
        existing = self._resolve_literature_artifact(
            session,
            pmid=record.get("pmid"),
            doi=record.get("doi"),
            pmcid=record.get("pmcid"),
        )
        desired = self._determine_literature_storage(record=record, save_mode=save_mode)
        if desired["storage_mode"] == "managed":
            try:
                managed = self._download_managed_literature_pdf(record)
            except Exception:
                payload = self._literature_external_artifact_payload(
                    record=record, save_mode=save_mode
                )
            else:
                payload = self._literature_managed_artifact_payload(
                    record=record,
                    save_mode=save_mode,
                    managed=managed,
                )
        else:
            payload = self._literature_external_artifact_payload(record=record, save_mode=save_mode)

        if existing is None:
            artifact = self.backend.create_instance(
                session,
                template_code=ARTIFACT_TEMPLATE,
                name=f"literature:{record['pmid']}",
                json_addl={
                    **payload,
                    "created_at": utc_now_iso(),
                },
            )
            if payload["storage_backend"] == "s3":
                self._tag_artifact_object(
                    artifact_payload=payload,
                    artifact_euid=artifact.euid,
                )
            return 201, self._artifact_response(artifact)

        current = normalize_instance_payload(existing)
        current_metadata = dict(current.get("metadata") or {})
        if (
            str(current_metadata.get("storage_mode") or "") == "managed"
            and str(dict(payload.get("metadata") or {}).get("storage_mode") or "") != "managed"
        ):
            payload = {
                **payload,
                "storage_backend": str(
                    current.get("storage_backend") or payload.get("storage_backend") or ""
                ),
                "bucket": str(current.get("bucket") or payload.get("bucket") or ""),
                "key": str(current.get("key") or payload.get("key") or ""),
                "version_id": current.get("version_id"),
                "size": current.get("size"),
                "content_type": current.get("content_type"),
                "storage_class": current.get("storage_class"),
                "availability_status": current.get("availability_status"),
                "storage_uri": current.get("storage_uri"),
                "source_uri": current.get("source_uri"),
                "import_mode": current.get("import_mode"),
                "storage_status": current.get("storage_status"),
                "storage_verified_at": current.get("storage_verified_at"),
                "metadata": {
                    **dict(payload.get("metadata") or {}),
                    "storage_mode": "managed",
                    "fulltext_status": "downloadable",
                    "best_fulltext_url": current_metadata.get("best_fulltext_url")
                    or dict(payload.get("metadata") or {}).get("best_fulltext_url"),
                },
            }
        updates = dict(current)
        updates.update(payload)
        updates["updated_at"] = utc_now_iso()
        self.backend.update_instance_json(session, existing, updates)
        if payload["storage_backend"] == "s3":
            self._tag_artifact_object(
                artifact_payload=payload,
                artifact_euid=existing.euid,
            )
        return 200, self._artifact_response(existing)

    def _determine_literature_storage(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> dict[str, str]:
        fulltext = classify_fulltext(
            best_fulltext_url=record.get("best_fulltext_url"),
            findit_reason=record.get("findit_reason"),
            allowed_domains=self.literature_allowed_domains,
        )
        if save_mode == "external_reference":
            return {
                "storage_mode": "external_reference",
                "fulltext_status": fulltext["fulltext_status"],
            }
        if fulltext["downloadable"] and self.managed_storage_bucket:
            return {"storage_mode": "managed", "fulltext_status": "downloadable"}
        return {
            "storage_mode": "external_reference",
            "fulltext_status": "external_link_only"
            if fulltext["external_link_only"]
            else "unavailable",
        }

    def _literature_external_artifact_payload(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> dict[str, Any]:
        landing_url = self._literature_landing_url(record)
        storage_backend, bucket, key = self._external_url_storage_parts(landing_url)
        return self._artifact_payload(
            artifact_type="literature",
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=None,
            size=None,
            checksums=None,
            content_type=None,
            original_filename=str(record.get("title") or "").strip() or None,
            producer_system="pubmed",
            producer_object_euid=str(record.get("pmid") or ""),
            storage_class=None,
            availability_status="external_only",
            metadata=self._literature_metadata(
                record=record,
                storage_mode="external_reference",
                acquisition_mode=save_mode,
                fulltext_status=self._determine_literature_storage(
                    record=record, save_mode=save_mode
                )["fulltext_status"],
            ),
            source_uri=landing_url,
            import_mode="reference",
            storage_status="registered",
            artifact_identity_key=f"literature:pmid:{record['pmid']}",
        )

    def _literature_managed_artifact_payload(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
        managed: dict[str, Any],
    ) -> dict[str, Any]:
        obj = managed["storage_object"]
        return self._artifact_payload(
            artifact_type="literature",
            storage_backend="s3",
            bucket=str(obj.bucket or ""),
            key=str(obj.key or ""),
            version_id=obj.version_id,
            size=obj.size,
            checksums=None,
            content_type=obj.content_type or "application/pdf",
            original_filename=f"pmid-{record['pmid']}.pdf",
            producer_system="pubmed",
            producer_object_euid=str(record.get("pmid") or ""),
            storage_class=obj.storage_class,
            availability_status="available",
            metadata=self._literature_metadata(
                record=record,
                storage_mode="managed",
                acquisition_mode=save_mode,
                fulltext_status="downloadable",
            ),
            source_uri=str(record.get("best_fulltext_url") or self._literature_landing_url(record)),
            import_mode="copy",
            storage_status="verified",
            storage_verified_at=utc_now_iso(),
            artifact_identity_key=f"literature:pmid:{record['pmid']}",
        )

    def _literature_metadata(
        self,
        *,
        record: dict[str, Any],
        storage_mode: str,
        acquisition_mode: str,
        fulltext_status: str,
    ) -> dict[str, Any]:
        return {
            "record_family": "literature",
            "title": str(record.get("title") or "").strip(),
            "authors": list(record.get("authors") or []),
            "journal": record.get("journal"),
            "year": record.get("year"),
            "abstract": record.get("abstract"),
            "abstract_snippet": record.get("abstract_snippet"),
            "pmid": str(record.get("pmid") or ""),
            "doi": normalize_doi(record.get("doi")),
            "pmcid": normalize_pmcid(record.get("pmcid")),
            "source_urls": dedupe_strings(list(record.get("source_urls") or [])),
            "best_fulltext_url": record.get("best_fulltext_url"),
            "findit_reason": record.get("findit_reason"),
            "storage_mode": storage_mode,
            "acquisition_mode": acquisition_mode,
            "fulltext_status": fulltext_status,
        }

    def _literature_landing_url(self, record: dict[str, Any]) -> str:
        return (
            str(record.get("best_fulltext_url") or "").strip()
            or next(
                (item for item in list(record.get("source_urls") or []) if str(item or "").strip()),
                "",
            )
            or f"https://pubmed.ncbi.nlm.nih.gov/{record['pmid']}/"
        )

    def _external_url_storage_parts(self, url: str) -> tuple[str, str, str]:
        parsed = urlparse(str(url or "").strip())
        backend = str(parsed.scheme or "https").strip().lower() or "https"
        bucket = str(parsed.netloc or "").strip()
        path = str(parsed.path or "").strip().lstrip("/")
        if parsed.query:
            path = f"{path}?{parsed.query}" if path else f"landing?{parsed.query}"
        key = path or "landing"
        if backend not in {"http", "https"}:
            raise ValueError("literature external URLs must use http or https")
        if not bucket:
            raise ValueError("literature landing URL must include a host")
        return backend, bucket, key

    def _download_managed_literature_pdf(self, record: dict[str, Any]) -> dict[str, Any]:
        if not self.managed_storage_bucket:
            raise ValueError("managed_storage_bucket is required for managed literature copies")
        source_url = str(record.get("best_fulltext_url") or "").strip()
        if not source_url:
            raise ValueError("Managed literature save requires a verified fulltext URL")
        response = requests.get(source_url, timeout=self.literature_request_timeout_seconds)
        response.raise_for_status()
        body = response.content
        content_type = str(response.headers.get("content-type") or "").strip().lower()
        if not body.startswith(b"%PDF-"):
            raise ValueError("Managed literature save requires a PDF response body")
        key = self._managed_key(
            namespace="literature",
            seed=f"pmid:{record['pmid']}",
            filename=f"pmid-{record['pmid']}.pdf",
        )
        storage = self._require_storage()
        obj = storage.put_bytes(
            bucket=self.managed_storage_bucket,
            key=key,
            body=body,
            content_type="application/pdf" if "pdf" not in content_type else content_type,
        )
        return {"storage_object": obj}

    def _ensure_literature_external_identities(
        self,
        session,
        *,
        artifact_instance,
        record: dict[str, Any],
    ) -> None:
        for external_system, external_type, external_id in [
            ("pubmed", "pmid", record.get("pmid")),
            ("pubmedcentral", "pmcid", record.get("pmcid")),
            ("doi", "doi", record.get("doi")),
        ]:
            clean_id = str(external_id or "").strip()
            if not clean_id:
                continue
            external = self._find_or_create_external_object(
                session,
                external_system=external_system,
                external_object_type=external_type,
                external_object_id=clean_id,
                external_uri=self._external_identity_uri(
                    external_system=external_system,
                    external_id=clean_id,
                ),
            )
            self._ensure_external_object_relation(
                session,
                artifact_instance=artifact_instance,
                external_object=external,
                relation_type="source_record",
            )

    def _external_identity_uri(self, *, external_system: str, external_id: str) -> str | None:
        if external_system == "pubmed":
            return f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/"
        if external_system == "pubmedcentral":
            return f"https://pmc.ncbi.nlm.nih.gov/articles/{external_id}/"
        if external_system == "doi":
            return f"https://doi.org/{external_id}"
        return None

    def _find_or_create_external_object(
        self,
        session,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
    ):
        identity_key = f"{external_system}:{external_object_type}:{external_object_id}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            field="external_identity_key",
            value=identity_key,
        )
        if existing is not None:
            return existing
        return self.backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            name=identity_key,
            json_addl={
                "external_system": external_system,
                "external_object_type": external_object_type,
                "external_object_id": external_object_id,
                "external_uri": external_uri,
                "metadata": {},
                "external_identity_key": identity_key,
                "created_at": utc_now_iso(),
            },
        )

    def _ensure_external_object_relation(
        self,
        session,
        *,
        artifact_instance,
        external_object,
        relation_type: str,
    ) -> None:
        relation_identity = (
            f"artifact:{artifact_instance.euid}:{external_object.euid}:{relation_type}"
        )
        existing = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
            field="relation_identity_key",
            value=relation_identity,
        )
        if existing is None:
            existing = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                name=relation_identity,
                json_addl={
                    "target_type": "artifact",
                    "target_euid": artifact_instance.euid,
                    "external_object_euid": external_object.euid,
                    "relation_type": relation_type,
                    "metadata": {},
                    "relation_identity_key": relation_identity,
                    "created_at": utc_now_iso(),
                },
            )
        self.backend.create_lineage(
            session,
            parent=artifact_instance,
            child=existing,
            relationship_type="has_external_relation",
        )
        self.backend.create_lineage(
            session,
            parent=external_object,
            child=existing,
            relationship_type="is_external_relation_for",
        )

    def _resolve_literature_artifact(
        self,
        session,
        *,
        pmid: str | None,
        doi: str | None,
        pmcid: str | None,
    ):
        normalized_pmid = normalize_pmid(pmid) if str(pmid or "").strip() else None
        for external_system, external_type, external_id in [
            ("pubmed", "pmid", normalized_pmid),
            ("pubmedcentral", "pmcid", normalize_pmcid(pmcid)),
            ("doi", "doi", normalize_doi(doi)),
        ]:
            if not external_id:
                continue
            artifact = self._find_artifact_by_external_identity(
                session,
                external_system=external_system,
                external_object_type=external_type,
                external_object_id=external_id,
            )
            if artifact is not None:
                return artifact
        if normalized_pmid:
            return self.backend.find_by_json_field(
                session,
                template_code=ARTIFACT_TEMPLATE,
                field="artifact_identity_key",
                value=f"literature:pmid:{normalized_pmid}",
            )
        return None

    def _find_artifact_by_external_identity(
        self,
        session,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
    ):
        external = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            field="external_identity_key",
            value=f"{external_system}:{external_object_type}:{external_object_id}",
        )
        if external is None:
            return None
        relations = self.backend.list_children(
            session,
            parent=external,
            relationship_type="is_external_relation_for",
        )
        for relation in relations:
            parents = self.backend.list_parents(
                session,
                child=relation,
                relationship_type="has_external_relation",
            )
            if parents:
                return parents[0]
        return None

    def _upsert_literature_save(
        self,
        session,
        *,
        artifact_instance,
        viewer: ViewerContext,
        visibility: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        identity_key = f"{artifact_instance.euid}:{viewer.subject}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=LITERATURE_SAVE_TEMPLATE,
            field="literature_save_identity_key",
            value=identity_key,
        )
        if existing is None:
            instance = self.backend.create_instance(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                name=identity_key,
                json_addl={
                    "artifact_euid": artifact_instance.euid,
                    "owner_subject": viewer.subject,
                    "owner_email": viewer.email,
                    "owner_label": viewer.owner_label,
                    **visibility,
                    "literature_save_identity_key": identity_key,
                    "created_at": utc_now_iso(),
                    "updated_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=artifact_instance,
                child=instance,
                relationship_type="has_literature_save",
            )
            return 201, self._literature_save_response(session, instance)
        self.backend.update_instance_json(
            session,
            existing,
            {
                **visibility,
                "owner_email": viewer.email,
                "owner_label": viewer.owner_label,
                "updated_at": utc_now_iso(),
            },
        )
        self.backend.create_lineage(
            session,
            parent=artifact_instance,
            child=existing,
            relationship_type="has_literature_save",
        )
        return 200, self._literature_save_response(session, existing)

    def _user_can_view_literature_save(
        self,
        payload: dict[str, Any],
        *,
        viewer: ViewerContext,
    ) -> bool:
        owner_subject = str(payload.get("owner_subject") or "")
        if owner_subject == viewer.subject:
            return True
        scope = str(payload.get("visibility_scope") or "private")
        if scope == "all_users":
            return True
        if scope != "restricted":
            return False
        allowed_users = set(normalize_email_list(payload.get("allowed_users")))
        if viewer.email and viewer.email in allowed_users:
            return True
        allowed_groups = set(normalize_group_list(payload.get("allowed_groups")))
        return bool(set(viewer.groups) & allowed_groups)

    def _visible_literature_save_summary(
        self,
        session,
        artifact_instance,
        viewer: ViewerContext,
    ) -> dict[str, Any]:
        saves = self.backend.list_children(
            session,
            parent=artifact_instance,
            relationship_type="has_literature_save",
        )
        saved_by_me = False
        visible_owners: list[str] = []
        for item in saves:
            payload = normalize_instance_payload(item)
            if not self._user_can_view_literature_save(payload, viewer=viewer):
                continue
            owner_label = str(
                payload.get("owner_label")
                or payload.get("owner_email")
                or payload.get("owner_subject")
                or ""
            ).strip()
            if str(payload.get("owner_subject") or "") == viewer.subject:
                saved_by_me = True
            elif owner_label and owner_label not in visible_owners:
                visible_owners.append(owner_label)
        return {
            "saved_by_me": saved_by_me,
            "saved_by_others_count": len(visible_owners),
            "visible_owner_labels": visible_owners,
        }

    def _literature_save_response(self, session, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        artifact = self.backend.find_by_euid(
            session,
            template_code=ARTIFACT_TEMPLATE,
            euid=str(payload.get("artifact_euid") or ""),
        )
        artifact_summary = None
        if artifact is not None:
            artifact_payload = self._artifact_response(artifact)
            metadata = dict(artifact_payload.get("metadata") or {})
            artifact_summary = {
                "artifact_euid": artifact.euid,
                "title": metadata.get("title"),
                "pmid": metadata.get("pmid"),
                "doi": metadata.get("doi"),
                "pmcid": metadata.get("pmcid"),
                "storage_mode": metadata.get("storage_mode"),
                "fulltext_status": metadata.get("fulltext_status"),
            }
        return {
            "literature_save_euid": instance.euid,
            "artifact_euid": payload.get("artifact_euid"),
            "owner_subject": payload.get("owner_subject"),
            "owner_email": payload.get("owner_email"),
            "owner_label": payload.get("owner_label"),
            "visibility_scope": payload.get("visibility_scope"),
            "allowed_users": normalize_email_list(payload.get("allowed_users")),
            "allowed_groups": normalize_group_list(payload.get("allowed_groups")),
            "artifact": artifact_summary,
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at") or payload.get("created_at"),
        }

    def query_search_v2(
        self,
        request: dict[str, Any] | None,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        query = dict(request or {})
        scopes = self._normalize_search_scopes(query.get("scopes"))
        page = max(1, int(query.get("page") or 1))
        page_size = max(1, min(int(query.get("page_size") or 25), self.search_export_max_rows))
        sort_field = str(query.get("sort_field") or "created_at").strip() or "created_at"
        sort_dir = str(query.get("sort_dir") or "desc").strip().lower() or "desc"

        with self.backend.session_scope(commit=False) as session:
            rows: list[dict[str, Any]] = []
            if "artifact" in scopes:
                rows.extend(self._search_artifact_items(session, viewer_context=viewer_context))
            if "artifact_set" in scopes:
                rows.extend(self._search_artifact_set_items(session))
            if "share_reference" in scopes:
                rows.extend(self._search_share_reference_items(session))

        filtered = self._apply_search_filters(rows, query)
        filtered = self._sort_search_rows(filtered, sort_field=sort_field, sort_dir=sort_dir)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = filtered[start:end]
        timing_ms = int((perf_counter() - started) * 1000)
        facets = {
            "artifact": sum(1 for row in filtered if row["record_type"] == "artifact"),
            "artifact_set": sum(1 for row in filtered if row["record_type"] == "artifact_set"),
            "share_reference": sum(
                1 for row in filtered if row["record_type"] == "share_reference"
            ),
        }
        return {
            "items": items,
            "facets": facets,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": end < total,
            "timing_ms": timing_ms,
        }

    def collect_search_export_rows(
        self,
        request: dict[str, Any] | None,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> tuple[list[dict[str, Any]], int, bool]:
        started = perf_counter()
        query = dict(request or {})
        max_rows = max(
            1,
            min(
                int(query.get("max_rows") or self.search_export_max_rows),
                self.search_export_max_rows,
            ),
        )
        query["page"] = 1
        query["page_size"] = max_rows
        result = self.query_search_v2(query, viewer_context=viewer_context)
        filtered_total = int(result["total"])
        items = list(result["items"])
        truncated = filtered_total > max_rows
        timing_ms = int((perf_counter() - started) * 1000)
        return items, timing_ms, truncated

    @staticmethod
    def _normalize_search_scopes(raw: Any) -> list[str]:
        allowed = {"artifact", "artifact_set", "share_reference"}
        if raw is None:
            return ["artifact", "share_reference"]
        values = raw if isinstance(raw, list) else [raw]
        scopes = [str(item or "").strip().lower() for item in values if str(item or "").strip()]
        normalized = [scope for scope in scopes if scope in allowed]
        return normalized or ["artifact", "share_reference"]

    def _search_artifact_items(
        self,
        session,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(session, template_code=ARTIFACT_TEMPLATE, limit=5000)
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._artifact_response(row)
            payload["external_objects"] = self._artifact_external_objects(session, row)
            metadata = dict(payload.get("metadata") or {})
            if str(payload.get("artifact_type") or "") == "literature":
                payload.update(
                    {
                        "title": metadata.get("title"),
                        "pmid": metadata.get("pmid"),
                        "doi": metadata.get("doi"),
                        "pmcid": metadata.get("pmcid"),
                        "storage_mode": metadata.get("storage_mode"),
                        "fulltext_status": metadata.get("fulltext_status"),
                        "authors": list(metadata.get("authors") or []),
                        "journal": metadata.get("journal"),
                        "year": metadata.get("year"),
                        "abstract_snippet": metadata.get("abstract_snippet"),
                    }
                )
                if viewer_context is not None:
                    payload.update(
                        self._visible_literature_save_summary(session, row, viewer_context)
                    )
                else:
                    payload.update(
                        {
                            "saved_by_me": False,
                            "saved_by_others_count": 0,
                            "visible_owner_labels": [],
                        }
                    )
            items.append(
                {
                    "record_type": "artifact",
                    "source_kind": "dewey.artifact",
                    "euid": payload["artifact_euid"],
                    "name": (
                        payload.get("title")
                        or payload.get("original_filename")
                        or payload["artifact_euid"]
                    ),
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _artifact_external_objects(self, session, artifact_instance) -> list[dict[str, Any]]:
        relations = self.backend.list_children(
            session,
            parent=artifact_instance,
            relationship_type="has_external_relation",
        )
        rows: list[dict[str, Any]] = []
        for relation in relations:
            relation_payload = self._external_object_relation_response(relation)
            external = self.backend.find_by_euid(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                euid=str(relation_payload.get("external_object_euid") or ""),
            )
            if external is None:
                continue
            rows.append(
                {
                    **self._external_object_response(external),
                    "relation_type": relation_payload.get("relation_type"),
                }
            )
        return rows

    def _search_share_reference_items(self, session) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(
            session,
            template_code=SHARE_REFERENCE_TEMPLATE,
            limit=5000,
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._share_reference_response(row)
            items.append(
                {
                    "record_type": "share_reference",
                    "source_kind": "dewey.share_reference",
                    "euid": payload["share_reference_euid"],
                    "name": payload["share_reference_euid"],
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _search_artifact_set_items(self, session) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(
            session,
            template_code=ARTIFACT_SET_TEMPLATE,
            limit=5000,
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._artifact_set_response(session, row)
            items.append(
                {
                    "record_type": "artifact_set",
                    "source_kind": "dewey.artifact_set",
                    "euid": payload["artifact_set_euid"],
                    "name": payload.get("label") or payload["artifact_set_euid"],
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _apply_search_filters(
        self,
        rows: list[dict[str, Any]],
        query: dict[str, Any],
    ) -> list[dict[str, Any]]:
        q = str(query.get("q") or "").strip().lower()
        created_at_start = str(query.get("created_at_start") or "").strip()
        created_at_end = str(query.get("created_at_end") or "").strip()
        property_filters = query.get("property_filters") or []
        filtered: list[dict[str, Any]] = []

        for row in rows:
            if q and not self._row_matches_text(row, q):
                continue
            if created_at_start and not self._row_in_created_range(
                row, created_at_start, is_start=True
            ):
                continue
            if created_at_end and not self._row_in_created_range(
                row, created_at_end, is_start=False
            ):
                continue
            if not all(self._row_matches_property_filter(row, item) for item in property_filters):
                continue
            filtered.append(row)
        return filtered

    @staticmethod
    def _row_matches_text(row: dict[str, Any], query: str) -> bool:
        haystacks = [
            str(row.get("euid") or ""),
            str(row.get("name") or ""),
            str(row.get("artifact_type") or ""),
            str(row.get("artifact_set_type") or ""),
            str(row.get("label") or ""),
            str(row.get("description") or ""),
            str(row.get("producer_system") or ""),
            str(row.get("title") or ""),
            str(row.get("pmid") or ""),
            str(row.get("doi") or ""),
            str(row.get("journal") or ""),
            str(row.get("year") or ""),
            str(row.get("abstract_snippet") or ""),
            str(row.get("storage_uri") or ""),
            str(row.get("target_euid") or ""),
            str(row.get("purpose") or ""),
            json.dumps(row.get("metadata") or {}, sort_keys=True),
            json.dumps(row.get("manifest") or [], sort_keys=True),
            json.dumps(row.get("connection") or {}, sort_keys=True),
            json.dumps(row.get("external_objects") or [], sort_keys=True),
            json.dumps(row.get("visible_owner_labels") or [], sort_keys=True),
        ]
        return any(query in item.lower() for item in haystacks if item)

    def _row_in_created_range(self, row: dict[str, Any], raw_value: str, *, is_start: bool) -> bool:
        row_value = str(row.get("created_at") or "").strip()
        if not row_value:
            return False
        row_dt = self._parse_iso8601(row_value, field_name="created_at")
        bound = self._parse_iso8601(raw_value, field_name="created_at")
        return row_dt >= bound if is_start else row_dt <= bound

    def _row_matches_property_filter(self, row: dict[str, Any], raw_filter: Any) -> bool:
        if not isinstance(raw_filter, dict):
            return True
        path = str(raw_filter.get("path") or "").strip()
        op = str(raw_filter.get("op") or "eq").strip().lower()
        value = raw_filter.get("value")
        values = self._extract_path_values(row, path)
        if op == "exists":
            return bool(values) if bool(value or value is None) else not bool(values)
        if op == "eq":
            return any(candidate == value for candidate in values)
        if op == "neq":
            return bool(values) and all(candidate != value for candidate in values)
        if op == "contains":
            needle = str(value or "").lower()
            return any(needle in str(candidate or "").lower() for candidate in values)
        if op == "in":
            acceptable = value if isinstance(value, list) else [value]
            return any(candidate in acceptable for candidate in values)
        if op in {"gte", "lte"}:
            if not values:
                return False
            left = values[0]
            if self._looks_like_datetime(str(left or "")) and self._looks_like_datetime(
                str(value or "")
            ):
                left_value = self._parse_iso8601(str(left), field_name=path)
                right_value = self._parse_iso8601(str(value), field_name=path)
            else:
                try:
                    left_value = float(left)
                    right_value = float(value)
                except (TypeError, ValueError):
                    return False
            return left_value >= right_value if op == "gte" else left_value <= right_value
        return True

    @staticmethod
    def _looks_like_datetime(value: str) -> bool:
        return "T" in value and ("Z" in value or "+" in value or "-" in value[10:])

    def _extract_path_values(self, payload: Any, path: str) -> list[Any]:
        if not path:
            return []
        parts = [part for part in path.split(".") if part]
        if not parts:
            return []
        return self._extract_nested_values(payload, parts)

    def _extract_nested_values(self, payload: Any, parts: list[str]) -> list[Any]:
        if not parts:
            return [payload]
        head, *tail = parts
        values: list[Any] = []
        if isinstance(payload, list):
            for item in payload:
                values.extend(self._extract_nested_values(item, parts))
            return values
        if not isinstance(payload, dict):
            return []
        if head not in payload:
            return []
        return self._extract_nested_values(payload[head], tail)

    @staticmethod
    def _sort_search_rows(
        rows: list[dict[str, Any]],
        *,
        sort_field: str,
        sort_dir: str,
    ) -> list[dict[str, Any]]:
        reverse = sort_dir != "asc"
        key_name = (
            sort_field
            if sort_field in {"created_at", "modified_at", "name", "euid"}
            else "created_at"
        )
        return sorted(
            rows,
            key=lambda item: (
                str(item.get(key_name) or ""),
                str(item.get("euid") or ""),
            ),
            reverse=reverse,
        )

    def create_artifact_set(
        self,
        *,
        artifact_set_type: str,
        label: str | None,
        description: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_type = str(artifact_set_type or "").strip().lower()
        if not clean_type:
            raise ValueError("artifact_set_type is required")

        payload = {
            "artifact_set_type": clean_type,
            "label": str(label or "").strip() or None,
            "description": str(description or "").strip() or None,
            "metadata": dict(metadata or {}),
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
                    "metadata": payload["metadata"],
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
        transport: str | None = None,
        transport_config: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        clean_target_euid = str(target_euid or "").strip()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")
        if not clean_target_euid:
            raise ValueError("target_euid is required")
        clean_transport = str(transport or "presigned_s3").strip().lower() or "presigned_s3"
        allowed_transports = {"presigned_s3", "rclone_http", "rclone_sftp"}
        if clean_transport not in allowed_transports:
            raise ValueError("transport must be presigned_s3, rclone_http, or rclone_sftp")
        clean_transport_config = dict(transport_config or {})
        expiry = self._normalize_expiry(expires_at, ttl_seconds=ttl_seconds)
        starts_at = utc_now_iso()
        payload = {
            "target_type": clean_target_type,
            "target_euid": clean_target_euid,
            "purpose": str(purpose or "").strip() or None,
            "scope": str(scope or "").strip() or None,
            "expires_at": expiry,
            "issued_by": str(issued_by or "").strip() or None,
            "transport": clean_transport,
            "transport_config": clean_transport_config,
            "ttl_seconds": int(ttl_seconds) if ttl_seconds is not None else None,
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

            if clean_target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=clean_target_euid,
                    for_update=True,
                )
            else:
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=clean_target_euid,
                    for_update=True,
                )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {clean_target_euid}")

            access_url: str | None = None
            status_value = "active"
            manifest: list[dict[str, Any]] = []
            connection: dict[str, Any] | None = None
            member_count = 0
            if clean_target_type == "artifact":
                if clean_transport != "presigned_s3":
                    raise ValueError("artifact sharing requires transport presigned_s3")
                artifact_payload = normalize_instance_payload(target)
                if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                    raise ValueError("artifact sharing requires an s3-backed artifact")
                expires_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                ttl_value = max(
                    60,
                    int((expires_dt - datetime.now(timezone.utc)).total_seconds()),
                )
                try:
                    self._require_storage().head_object(
                        bucket=str(artifact_payload.get("bucket") or ""),
                        key=str(artifact_payload.get("key") or ""),
                        version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                    )
                    access_url = self._require_storage().generate_presigned_get_url(
                        bucket=str(artifact_payload.get("bucket") or ""),
                        key=str(artifact_payload.get("key") or ""),
                        version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                        expires_in=ttl_value,
                    )
                except StorageObjectNotFoundError:
                    status_value = "error"
                self.backend.update_instance_json(
                    session,
                    target,
                    {
                        "share_status": status_value,
                        "share_last_issued_at": starts_at,
                    },
                )
            else:
                members = self.backend.list_children(
                    session,
                    parent=target,
                    relationship_type="artifact_set_member",
                )
                member_count = len(members)
                if clean_transport == "presigned_s3":
                    expires_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    ttl_value = max(
                        60,
                        int((expires_dt - datetime.now(timezone.utc)).total_seconds()),
                    )
                    errors = 0
                    for member in members:
                        artifact_payload = normalize_instance_payload(member)
                        entry = {
                            "artifact_euid": member.euid,
                            "filename": str(
                                artifact_payload.get("original_filename") or member.euid
                            ),
                            "storage_uri": str(artifact_payload.get("storage_uri") or ""),
                        }
                        if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                            entry["status"] = "error"
                            entry["detail"] = "artifact is not s3-backed"
                            errors += 1
                        else:
                            try:
                                self._require_storage().head_object(
                                    bucket=str(artifact_payload.get("bucket") or ""),
                                    key=str(artifact_payload.get("key") or ""),
                                    version_id=str(artifact_payload.get("version_id") or "").strip()
                                    or None,
                                )
                                entry["status"] = "active"
                                entry["access_url"] = self._require_storage().generate_presigned_get_url(
                                    bucket=str(artifact_payload.get("bucket") or ""),
                                    key=str(artifact_payload.get("key") or ""),
                                    version_id=str(artifact_payload.get("version_id") or "").strip()
                                    or None,
                                    expires_in=ttl_value,
                                )
                            except StorageObjectNotFoundError:
                                entry["status"] = "error"
                                entry["detail"] = "artifact object missing"
                                errors += 1
                        manifest.append(entry)
                    status_value = "error" if errors == member_count and member_count else "active"
                else:
                    host = str(clean_transport_config.get("host") or "0.0.0.0").strip() or "0.0.0.0"
                    port = int(clean_transport_config.get("port") or (8080 if clean_transport == "rclone_http" else 8022))
                    username = str(clean_transport_config.get("user") or clean_transport_config.get("username") or "user").strip() or "user"
                    password = str(clean_transport_config.get("passwd") or clean_transport_config.get("password") or "passwd").strip() or "passwd"
                    bucket = str(clean_transport_config.get("bucket") or self.managed_storage_bucket or "").strip() or None
                    endpoint = (
                        f"http://{host}:{port}/"
                        if clean_transport == "rclone_http"
                        else f"sftp://{username}@{host}:{port}/"
                    )
                    connection = {
                        "host": host,
                        "port": port,
                        "bucket": bucket,
                        "username": username,
                        "password": password,
                        "endpoint": endpoint,
                    }
                    access_url = endpoint if clean_transport == "rclone_http" else None

            instance = self.backend.create_instance(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                name=f"share:{clean_target_type}:{clean_target_euid}",
                json_addl={
                    "target_type": clean_target_type,
                    "target_euid": clean_target_euid,
                    "purpose": payload["purpose"],
                    "scope": payload["scope"],
                    "transport": clean_transport,
                    "status": status_value,
                    "starts_at": starts_at,
                    "expires_at": payload["expires_at"],
                    "access_url": access_url,
                    "issued_by": payload["issued_by"],
                    "manifest": manifest,
                    "connection": connection or {},
                    "member_count": member_count,
                    "transport_config": clean_transport_config,
                    "created_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=target,
                child=instance,
                relationship_type="has_share_reference",
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
            "source_uri": payload.get("source_uri"),
            "import_mode": payload.get("import_mode"),
            "storage_status": payload.get("storage_status"),
            "storage_verified_at": payload.get("storage_verified_at"),
            "retention_mode": payload.get("retention_mode"),
            "retain_until": payload.get("retain_until"),
            "share_status": payload.get("share_status"),
            "share_last_issued_at": payload.get("share_last_issued_at"),
            "created_at": str(payload.get("created_at") or utc_now_iso()),
        }

    def _anomaly_response(self, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        return {
            "anomaly_id": instance.euid,
            "anomaly_identity_key": payload.get("anomaly_identity_key"),
            "category": payload.get("category"),
            "severity": payload.get("severity"),
            "status": payload.get("status"),
            "title": payload.get("title"),
            "summary": payload.get("summary"),
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

    def _normalize_expiry(self, expires_at: str | None, ttl_seconds: int | None = None) -> str:
        clean = str(expires_at or "").strip()
        if clean:
            try:
                parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("expires_at must be ISO8601") from exc
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        ttl_value = (
            self.default_share_ttl_seconds if ttl_seconds is None else max(60, int(ttl_seconds))
        )
        auto = datetime.now(timezone.utc) + timedelta(seconds=ttl_value)
        return auto.isoformat().replace("+00:00", "Z")
