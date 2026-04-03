"""Artifact and storage workflows for Dewey service."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from itsdangerous import BadSignature, SignatureExpired

from dewey_service.artifact_ui import resolve_artifact_type
from dewey_service.services.base import DeweyNotFoundError
from dewey_service.storage import (
    StorageObject,
    StorageObjectNotFoundError,
    StoragePermissionError,
)
from dewey_service.tapdb_backend import ARTIFACT_TEMPLATE, normalize_instance_payload, utc_now_iso


class ArtifactServiceMixin:
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
        archive_name = (
            f"dewey-artifacts-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.zip"
        )
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
        clean_artifact_type = resolve_artifact_type(
            artifact_type, original_filename, key, source_uri
        )
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
        resolved_artifact_type = resolve_artifact_type(
            artifact_type, original_filename, source_value
        )
        payload = {
            "artifact_type": resolved_artifact_type,
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
        clean_type = resolve_artifact_type(artifact_type, original_filename)
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
