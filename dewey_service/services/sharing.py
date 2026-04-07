"""Share-reference workflows for Dewey service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from dewey_service.services.base import DeweyNotFoundError
from dewey_service.storage import StorageObjectNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    SHARE_REFERENCE_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

DEFAULT_SHARE_HOST = "127.0.0.1"


class SharingServiceMixin:
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
                if str(artifact_payload.get("storage_kind") or "object").lower() != "object":
                    raise ValueError("artifact sharing requires an object-backed artifact")
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
                                entry["access_url"] = (
                                    self._require_storage().generate_presigned_get_url(
                                        bucket=str(artifact_payload.get("bucket") or ""),
                                        key=str(artifact_payload.get("key") or ""),
                                        version_id=str(
                                            artifact_payload.get("version_id") or ""
                                        ).strip()
                                        or None,
                                        expires_in=ttl_value,
                                    )
                                )
                            except StorageObjectNotFoundError:
                                entry["status"] = "error"
                                entry["detail"] = "artifact object missing"
                                errors += 1
                        manifest.append(entry)
                    status_value = "error" if errors == member_count and member_count else "active"
                else:
                    host = (
                        str(clean_transport_config.get("host") or DEFAULT_SHARE_HOST).strip()
                        or DEFAULT_SHARE_HOST
                    )
                    port = int(
                        clean_transport_config.get("port")
                        or (8080 if clean_transport == "rclone_http" else 8022)
                    )
                    username = (
                        str(
                            clean_transport_config.get("user")
                            or clean_transport_config.get("username")
                            or "user"
                        ).strip()
                        or "user"
                    )
                    password = (
                        str(
                            clean_transport_config.get("passwd")
                            or clean_transport_config.get("password")
                            or "passwd"
                        ).strip()
                        or "passwd"
                    )
                    bucket = (
                        str(
                            clean_transport_config.get("bucket")
                            or self.managed_storage_bucket
                            or ""
                        ).strip()
                        or None
                    )
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
