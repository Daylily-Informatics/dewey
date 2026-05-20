"""Share-reference workflows for Dewey service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from secrets import token_urlsafe
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
ALLOWED_SHARE_TRANSPORTS = {"presigned_s3", "rclone_http", "rclone_sftp", "cloudfront"}
ALLOWED_CLOUDFRONT_VISIBILITIES = {"authenticated", "public"}
ALLOWED_CLOUDFRONT_MODES = {"snapshot", "live_prefix"}
ALLOWED_CLOUDFRONT_PERMISSIONS = {
    "view_metadata",
    "list",
    "download",
    "recursive_list",
    "recursive_download",
}
PUBLIC_SHARE_WRITER_GROUP = "lsmc:dewey:share-writer"


def _dedupe_clean(items: Any) -> list[str]:
    if items is None:
        return []
    raw = items
    if isinstance(items, str):
        raw = items.split(",")
    if not isinstance(raw, (list, tuple, set)):
        raise ValueError("share list fields must be strings or lists")
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        clean = str(item or "").strip()
        if clean and clean not in seen:
            out.append(clean)
            seen.add(clean)
    return out


def _normalize_email(value: str) -> str:
    email = str(value or "").strip().lower()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError(f"Invalid share recipient email: {value!r}")
    return email


def _normalize_email_list(items: Any) -> list[str]:
    return [_normalize_email(item) for item in _dedupe_clean(items)]


def _normalize_domain(value: str) -> str:
    domain = str(value or "").strip().lower().lstrip("@")
    if not domain or "@" in domain or "/" in domain:
        raise ValueError(f"Invalid share recipient domain: {value!r}")
    return domain


def _normalize_domain_list(items: Any) -> list[str]:
    return [_normalize_domain(item) for item in _dedupe_clean(items)]


def _email_domain(email: str) -> str:
    return _normalize_email(email).split("@", 1)[1]


def _normalize_permissions(items: Any, *, recursive: bool) -> list[str]:
    cleaned = _dedupe_clean(items)
    if not cleaned:
        cleaned = ["view_metadata", "download"]
        if recursive:
            cleaned.extend(["recursive_list", "recursive_download"])
    invalid = [item for item in cleaned if item not in ALLOWED_CLOUDFRONT_PERMISSIONS]
    if invalid:
        raise ValueError("Unsupported CloudFront share permissions: " + ", ".join(invalid))
    return cleaned


def _normalize_relative_path(value: str | None) -> str:
    raw = str(value or "").strip().strip("/")
    if not raw:
        return ""
    path = PurePosixPath(raw)
    parts = [part for part in path.parts if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError("relative_path must not contain path traversal")
    return "/".join(parts).rstrip("/") + "/"


def _direct_child_object(key: str, prefix: str) -> bool:
    remainder = str(key or "")[len(prefix) :]
    return bool(remainder) and "/" not in remainder.rstrip("/")


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
        visibility: str | None = None,
        permissions: list[str] | tuple[str, ...] | str | None = None,
        recipient_emails: list[str] | tuple[str, ...] | str | None = None,
        recipient_domains: list[str] | tuple[str, ...] | str | None = None,
        pending_recipient_emails: list[str] | tuple[str, ...] | str | None = None,
        mode: str | None = None,
        recursive: bool = False,
        relative_path: str | None = None,
        creator_profile: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        clean_target_euid = str(target_euid or "").strip()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")
        if not clean_target_euid:
            raise ValueError("target_euid is required")
        clean_transport = str(transport or "presigned_s3").strip().lower() or "presigned_s3"
        if clean_transport not in ALLOWED_SHARE_TRANSPORTS:
            raise ValueError("transport must be presigned_s3, rclone_http, rclone_sftp, or cloudfront")
        clean_transport_config = dict(transport_config or {})
        clean_visibility = str(visibility or "").strip().lower()
        clean_mode = str(mode or "").strip().lower()
        clean_permissions: list[str] = []
        clean_recipient_emails: list[str] = []
        clean_recipient_domains: list[str] = []
        clean_pending_recipient_emails: list[str] = []
        clean_relative_path = _normalize_relative_path(relative_path)
        public_share_id: str | None = None
        if clean_transport == "cloudfront":
            self._require_cloudfront_signer()
            clean_visibility = clean_visibility or "authenticated"
            if clean_visibility not in ALLOWED_CLOUDFRONT_VISIBILITIES:
                raise ValueError("visibility must be authenticated or public")
            clean_mode = clean_mode or "snapshot"
            if clean_mode not in ALLOWED_CLOUDFRONT_MODES:
                raise ValueError("mode must be snapshot or live_prefix")
            clean_permissions = _normalize_permissions(permissions, recursive=bool(recursive))
            clean_recipient_emails = _normalize_email_list(recipient_emails)
            clean_recipient_domains = _normalize_domain_list(recipient_domains)
            clean_pending_recipient_emails = _normalize_email_list(pending_recipient_emails)
            if clean_visibility == "public":
                self._validate_public_cloudfront_creator(
                    creator_profile=creator_profile,
                    issued_by=issued_by,
                )
                public_share_id = token_urlsafe(24)
            elif not (
                clean_recipient_emails
                or clean_recipient_domains
                or clean_pending_recipient_emails
            ):
                raise ValueError("authenticated CloudFront shares require recipient rules")
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
            "visibility": clean_visibility or None,
            "permissions": clean_permissions,
            "recipient_emails": clean_recipient_emails,
            "recipient_domains": clean_recipient_domains,
            "pending_recipient_emails": clean_pending_recipient_emails,
            "mode": clean_mode or None,
            "recursive": bool(recursive),
            "relative_path": clean_relative_path,
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
            cloudfront_payload: dict[str, Any] = {}
            if clean_transport == "cloudfront":
                cloudfront_payload = self._prepare_cloudfront_share_payload(
                    session=session,
                    target=target,
                    target_type=clean_target_type,
                    target_euid=clean_target_euid,
                    mode=clean_mode,
                    recursive=bool(recursive),
                    relative_path=clean_relative_path,
                )
                manifest = list(cloudfront_payload.get("manifest") or [])
                member_count = int(cloudfront_payload.get("member_count") or len(manifest))
            elif clean_target_type == "artifact":
                if clean_transport != "presigned_s3":
                    raise ValueError("artifact sharing requires transport presigned_s3")
                artifact_payload = normalize_instance_payload(target)
                if str(artifact_payload.get("storage_kind") or "object").lower() != "object":
                    raise ValueError("artifact sharing requires an object-backed artifact")
                if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                    raise ValueError("artifact sharing requires an s3-backed artifact")
                try:
                    self._require_storage().head_object(
                        bucket=str(artifact_payload.get("bucket") or ""),
                        key=str(artifact_payload.get("key") or ""),
                        version_id=str(artifact_payload.get("version_id") or "").strip() or None,
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
                elif clean_transport in {"rclone_http", "rclone_sftp"}:
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
                else:
                    raise ValueError("artifact set sharing requires a supported transport")

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
                    "visibility": clean_visibility or None,
                    "public_share_id": public_share_id,
                    "recipient_emails": clean_recipient_emails,
                    "recipient_domains": clean_recipient_domains,
                    "pending_recipient_emails": clean_pending_recipient_emails,
                    "permissions": clean_permissions,
                    "mode": clean_mode or None,
                    "recursive": bool(recursive),
                    "relative_path": clean_relative_path,
                    "cloudfront": cloudfront_payload,
                    "audit_events": [],
                    "last_denial_reason": None,
                    "programmatic_package_count": 0,
                    "managed_access": clean_target_type == "artifact"
                    and clean_transport == "presigned_s3",
                    "access_count": 0,
                    "last_accessed_at": None,
                    "created_at": utc_now_iso(),
                },
            )
            if (
                clean_target_type == "artifact"
                and clean_transport == "presigned_s3"
                and status_value == "active"
            ):
                access_url = f"/share-references/{instance.euid}"
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "access_url": access_url,
                        "managed_access": True,
                    },
                )
            if clean_transport == "cloudfront" and status_value == "active":
                access_url = (
                    f"/public-shares/{public_share_id}"
                    if public_share_id
                    else f"/share-references/{instance.euid}"
                )
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "access_url": access_url,
                        "managed_access": True,
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

    def _require_cloudfront_signer(self):
        signer = getattr(self, "cloudfront_signer", None)
        if signer is None:
            raise RuntimeError("CloudFront share transport requires explicit CloudFront signer config")
        return signer

    def _validate_public_cloudfront_creator(
        self,
        *,
        creator_profile: dict[str, Any] | None,
        issued_by: str | None,
    ) -> None:
        profile = dict(creator_profile or {})
        email = str(profile.get("email") or issued_by or "").strip().lower()
        if not email:
            raise ValueError("public CloudFront share creation requires a verified creator email")
        if _email_domain(email) != "lsmc.com":
            raise ValueError("public CloudFront shares require a verified lsmc.com creator email")
        groups = {str(item or "").strip() for item in list(profile.get("groups") or [])}
        if PUBLIC_SHARE_WRITER_GROUP not in groups:
            raise ValueError("public CloudFront shares require lsmc:dewey:share-writer")

    def _prepare_cloudfront_share_payload(
        self,
        *,
        session,
        target,
        target_type: str,
        target_euid: str,
        mode: str,
        recursive: bool,
        relative_path: str,
    ) -> dict[str, Any]:
        signer = self._require_cloudfront_signer()
        if target_type == "artifact_set":
            if mode != "snapshot":
                raise ValueError("artifact-set CloudFront shares require snapshot mode")
            members = self.backend.list_children(
                session,
                parent=target,
                relationship_type="artifact_set_member",
            )
            if not members:
                raise ValueError("artifact-set CloudFront shares require at least one member")
            manifest: list[dict[str, Any]] = []
            for member in members:
                payload = normalize_instance_payload(member)
                if str(payload.get("storage_kind") or "object").lower() != "object":
                    raise ValueError("artifact-set CloudFront shares require object-backed members")
                if str(payload.get("storage_backend") or "").lower() != "s3":
                    raise ValueError("artifact-set CloudFront shares require s3-backed members")
                bucket = str(payload.get("bucket") or "").strip()
                key = str(payload.get("key") or "").strip()
                self._require_storage().head_object(
                    bucket=bucket,
                    key=key,
                    version_id=str(payload.get("version_id") or "").strip() or None,
                )
                manifest.append(self._cloudfront_manifest_entry(member.euid, payload, signer))
            return {
                "target_kind": "artifact_set",
                "bucket": None,
                "prefix": None,
                "object_key": None,
                "snapshot_object_keys": [str(item["key"]) for item in manifest],
                "manifest": manifest,
                "member_count": len(manifest),
            }

        payload = normalize_instance_payload(target)
        if str(payload.get("storage_backend") or "").lower() != "s3":
            raise ValueError("CloudFront shares require an s3-backed target")
        bucket = str(payload.get("bucket") or "").strip()
        key = str(payload.get("key") or "").strip()
        storage_kind = str(payload.get("storage_kind") or "object").lower()
        if storage_kind == "object":
            if relative_path:
                raise ValueError("relative_path is only valid for prefix CloudFront shares")
            if mode != "snapshot":
                raise ValueError("object CloudFront shares require snapshot mode")
            self._require_storage().head_object(
                bucket=bucket,
                key=key,
                version_id=str(payload.get("version_id") or "").strip() or None,
            )
            entry = self._cloudfront_manifest_entry(target_euid, payload, signer)
            return {
                "target_kind": "artifact_object",
                "bucket": bucket,
                "prefix": None,
                "object_key": key,
                "snapshot_object_keys": [key],
                "manifest": [entry],
                "member_count": 1,
            }

        if storage_kind != "prefix":
            raise ValueError("CloudFront shares require object or prefix storage_kind")
        root_prefix = key.rstrip("/") + "/"
        share_prefix = f"{root_prefix}{relative_path}"
        objects = self._require_storage().list_objects(bucket=bucket, prefix=share_prefix, limit=1000)
        if not recursive:
            objects = [item for item in objects if _direct_child_object(item.key, share_prefix)]
        if not objects:
            raise ValueError("CloudFront prefix share target has no resolvable S3 objects")
        manifest = [
            {
                "artifact_euid": target_euid,
                "filename": item.key.rsplit("/", 1)[-1],
                "bucket": bucket,
                "key": item.key,
                "storage_uri": f"s3://{bucket}/{item.key}",
                "status": "active",
                "size": item.size,
                "cloudfront_resource": signer.resource_url(item.key),
            }
            for item in objects
        ]
        return {
            "target_kind": "directory" if relative_path else "prefix",
            "bucket": bucket,
            "prefix": share_prefix,
            "object_key": None,
            "snapshot_object_keys": [str(item["key"]) for item in manifest]
            if mode == "snapshot"
            else [],
            "manifest": manifest if mode == "snapshot" else [],
            "member_count": len(manifest),
        }

    def _cloudfront_manifest_entry(
        self,
        artifact_euid: str,
        payload: dict[str, Any],
        signer,
    ) -> dict[str, Any]:
        bucket = str(payload.get("bucket") or "").strip()
        key = str(payload.get("key") or "").strip()
        return {
            "artifact_euid": artifact_euid,
            "filename": str(payload.get("original_filename") or key.rsplit("/", 1)[-1] or artifact_euid),
            "bucket": bucket,
            "key": key,
            "storage_uri": str(payload.get("storage_uri") or f"s3://{bucket}/{key}"),
            "status": "active",
            "size": payload.get("size"),
            "cloudfront_resource": signer.resource_url(key),
        }

    def revoke_share_reference(
        self,
        *,
        share_reference_euid: str,
        revoked_by: str | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_euid = str(share_reference_euid or "").strip()
        if not clean_euid:
            raise ValueError("share_reference_euid is required")
        payload = {
            "share_reference_euid": clean_euid,
            "revoked_by": str(revoked_by or "").strip() or None,
        }
        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="share_reference.revoke",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response
            instance = self.backend.find_by_euid(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                euid=clean_euid,
                for_update=True,
            )
            if instance is None:
                raise DeweyNotFoundError(f"Share reference not found: {clean_euid}")
            current = normalize_instance_payload(instance)
            if current.get("status") != "revoked":
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "status": "revoked",
                        "revoked_at": utc_now_iso(),
                        "revoked_by": payload["revoked_by"],
                    },
                )
            body = self._share_reference_response(instance)
            self._store_idempotency(
                session,
                operation="share_reference.revoke",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def open_share_reference(
        self,
        share_reference_euid: str,
        *,
        viewer_email: str | None = None,
        viewer_groups: list[str] | tuple[str, ...] | None = None,
        access_mode: str = "download",
        requested_key: str | None = None,
    ) -> dict[str, Any]:
        clean_euid = str(share_reference_euid or "").strip()
        if not clean_euid:
            raise ValueError("share_reference_euid is required")
        now = datetime.now(timezone.utc)
        with self.backend.session_scope(commit=True) as session:
            instance = self.backend.find_by_euid(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                euid=clean_euid,
                for_update=True,
            )
            if instance is None:
                raise DeweyNotFoundError(f"Share reference not found: {clean_euid}")
            payload = normalize_instance_payload(instance)
            if str(payload.get("status") or "").lower() != "active":
                raise ValueError("Share reference is not active")
            expires_at = str(payload.get("expires_at") or "").strip()
            if not expires_at:
                raise ValueError("Share reference is missing expires_at")
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_dt <= now:
                self.backend.update_instance_json(session, instance, {"status": "expired"})
                raise ValueError("Share reference is expired")
            if str(payload.get("transport") or "").lower() == "cloudfront":
                payload["share_reference_euid"] = instance.euid
                return self._open_cloudfront_share_reference(
                    session=session,
                    instance=instance,
                    payload=payload,
                    viewer_email=viewer_email,
                    viewer_groups=viewer_groups,
                    access_mode=access_mode,
                    requested_key=requested_key,
                )
            if str(payload.get("target_type") or "").lower() != "artifact":
                raise ValueError("Dewey-gated browser access requires an artifact share reference")
            if str(payload.get("transport") or "").lower() != "presigned_s3":
                raise ValueError("Dewey-gated browser access requires presigned_s3 transport")
            target = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=str(payload.get("target_euid") or "").strip(),
            )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {payload.get('target_euid')}")
            artifact_payload = normalize_instance_payload(target)
            if str(artifact_payload.get("storage_kind") or "object").lower() != "object":
                raise ValueError("Share reference target is not an object-backed artifact")
            if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                raise ValueError("Share reference target is not s3-backed")
            self._require_storage().head_object(
                bucket=str(artifact_payload.get("bucket") or ""),
                key=str(artifact_payload.get("key") or ""),
                version_id=str(artifact_payload.get("version_id") or "").strip() or None,
            )
            access_url = self._require_storage().generate_presigned_get_url(
                bucket=str(artifact_payload.get("bucket") or ""),
                key=str(artifact_payload.get("key") or ""),
                version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                expires_in=900,
            )
            access_count = int(payload.get("access_count") or 0) + 1
            accessed_at = utc_now_iso()
            events = list(payload.get("access_events") or [])
            events.append({"accessed_at": accessed_at})
            self.backend.update_instance_json(
                session,
                instance,
                {
                    "access_count": access_count,
                    "last_accessed_at": accessed_at,
                    "access_events": events[-25:],
                },
            )
            body = self._share_reference_response(instance)
            body["presigned_access_url"] = access_url
            return body

    def get_share_reference_by_public_id(self, public_share_id: str) -> dict[str, Any]:
        clean = str(public_share_id or "").strip()
        if not clean:
            raise ValueError("public_share_id is required")
        with self.backend.session_scope(commit=False) as session:
            instance = self.backend.find_by_json_field(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                field="public_share_id",
                value=clean,
            )
            if instance is None:
                raise DeweyNotFoundError(f"Public share not found: {clean}")
            return self._share_reference_response(instance)

    def list_external_share_report(self, *, limit: int = 500) -> list[dict[str, Any]]:
        rows = self.list_share_references(limit=limit)
        return [row for row in rows if str(row.get("transport") or "").lower() == "cloudfront"]

    def _open_cloudfront_share_reference(
        self,
        *,
        session,
        instance,
        payload: dict[str, Any],
        viewer_email: str | None,
        viewer_groups: list[str] | tuple[str, ...] | None,
        access_mode: str,
        requested_key: str | None,
    ) -> dict[str, Any]:
        _ = viewer_groups
        mode = str(access_mode or "download").strip().lower()
        if mode not in {"download", "browse", "programmatic"}:
            raise ValueError("access_mode must be download, browse, or programmatic")
        try:
            self._authorize_cloudfront_viewer(payload, viewer_email=viewer_email)
            self._require_cloudfront_permission(payload, access_mode=mode, requested_key=requested_key)
            body = self._build_cloudfront_access_package(
                payload,
                access_mode=mode,
                requested_key=requested_key,
            )
        except ValueError as exc:
            self._record_share_access_event(
                session,
                instance,
                payload,
                allowed=False,
                access_mode=mode,
                viewer_email=viewer_email,
                reason=str(exc),
            )
            raise
        self._record_share_access_event(
            session,
            instance,
            payload,
            allowed=True,
            access_mode=mode,
            viewer_email=viewer_email,
            reason=None,
            programmatic=mode == "programmatic",
        )
        current = self._share_reference_response(instance)
        current.update(body)
        return current

    def _authorize_cloudfront_viewer(
        self,
        payload: dict[str, Any],
        *,
        viewer_email: str | None,
    ) -> None:
        visibility = str(payload.get("visibility") or "authenticated").strip().lower()
        if visibility == "public":
            return
        email = str(viewer_email or "").strip().lower()
        if not email:
            raise ValueError("missing_login")
        normalized = _normalize_email(email)
        pending = set(_normalize_email_list(payload.get("pending_recipient_emails") or []))
        if normalized in pending:
            raise ValueError("unverified_pending_recipient")
        emails = set(_normalize_email_list(payload.get("recipient_emails") or []))
        domains = set(_normalize_domain_list(payload.get("recipient_domains") or []))
        if normalized in emails or _email_domain(normalized) in domains:
            return
        raise ValueError("wrong_email_or_domain")

    def _require_cloudfront_permission(
        self,
        payload: dict[str, Any],
        *,
        access_mode: str,
        requested_key: str | None,
    ) -> None:
        permissions = set(_normalize_permissions(payload.get("permissions") or [], recursive=False))
        if access_mode == "browse" and not ({"list", "recursive_list"} & permissions):
            raise ValueError("insufficient_permission")
        if access_mode in {"download", "programmatic"} and not (
            {"download", "recursive_download"} & permissions
        ):
            raise ValueError("insufficient_permission")
        if requested_key:
            self._validate_cloudfront_requested_key(
                payload,
                requested_key=requested_key,
                recursive_download="recursive_download" in permissions,
            )

    def _build_cloudfront_access_package(
        self,
        payload: dict[str, Any],
        *,
        access_mode: str,
        requested_key: str | None,
    ) -> dict[str, Any]:
        signer = self._require_cloudfront_signer()
        cloudfront = dict(payload.get("cloudfront") or {})
        permissions = set(payload.get("permissions") or [])
        if access_mode == "browse":
            manifest = self._cloudfront_effective_manifest(payload)
            return {
                "browser_view_url": f"/shares/cloudfront/{payload.get('share_reference_euid', '')}/browse",
                "cloudfront_access": {
                    "type": "browse",
                    "manifest": [
                        {
                            **item,
                            "signed_url": signer.sign_url(key=str(item["key"])).access_url
                            if {"download", "recursive_download"} & permissions
                            else None,
                        }
                        for item in manifest
                    ],
                },
            }
        if access_mode == "programmatic":
            prefix = str(cloudfront.get("prefix") or "").strip()
            if (
                str(payload.get("mode") or "") == "live_prefix"
                and prefix
                and "recursive_download" in permissions
            ):
                signed = signer.sign_prefix_cookies(prefix=prefix)
                return {
                    "cloudfront_access": {
                        "type": "signed_cookies",
                        "resource": signed.resource,
                        "cookies": signed.cookies,
                        "expires_at": signed.expires_at,
                    }
                }
            manifest = self._cloudfront_effective_manifest(payload)
            return {
                "cloudfront_access": {
                    "type": "signed_url_manifest",
                    "manifest": [
                        {
                            **item,
                            "signed_url": signer.sign_url(key=str(item["key"])).access_url,
                        }
                        for item in manifest
                    ],
                }
            }
        key = str(requested_key or cloudfront.get("object_key") or "").strip()
        if not key:
            manifest = self._cloudfront_effective_manifest(payload)
            if len(manifest) != 1:
                return {"browser_view_url": f"/shares/cloudfront/{payload.get('share_reference_euid', '')}/browse"}
            key = str(manifest[0]["key"])
        self._validate_cloudfront_requested_key(
            payload,
            requested_key=key,
            recursive_download="recursive_download" in permissions,
        )
        signed = signer.sign_url(key=key)
        return {
            "presigned_access_url": signed.access_url,
            "cloudfront_access": {
                "type": "signed_url",
                "resource": signed.resource,
                "expires_at": signed.expires_at,
            },
        }

    def _cloudfront_effective_manifest(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        cloudfront = dict(payload.get("cloudfront") or {})
        manifest = [dict(item) for item in list(payload.get("manifest") or [])]
        if manifest:
            return manifest
        prefix = str(cloudfront.get("prefix") or "").strip()
        bucket = str(cloudfront.get("bucket") or "").strip()
        if not prefix or not bucket:
            return []
        objects = self._require_storage().list_objects(bucket=bucket, prefix=prefix, limit=1000)
        if not bool(payload.get("recursive")):
            objects = [item for item in objects if _direct_child_object(item.key, prefix)]
        signer = self._require_cloudfront_signer()
        return [
            {
                "bucket": bucket,
                "key": item.key,
                "filename": item.key.rsplit("/", 1)[-1],
                "storage_uri": f"s3://{bucket}/{item.key}",
                "status": "active",
                "size": item.size,
                "cloudfront_resource": signer.resource_url(item.key),
            }
            for item in objects
        ]

    def _validate_cloudfront_requested_key(
        self,
        payload: dict[str, Any],
        *,
        requested_key: str,
        recursive_download: bool,
    ) -> None:
        key = str(requested_key or "").strip().lstrip("/")
        if not key:
            raise ValueError("requested object key is required")
        cloudfront = dict(payload.get("cloudfront") or {})
        object_key = str(cloudfront.get("object_key") or "").strip()
        if object_key:
            if key != object_key:
                raise ValueError("object_outside_share")
            return
        snapshot_keys = {str(item or "") for item in list(cloudfront.get("snapshot_object_keys") or [])}
        if snapshot_keys:
            if key not in snapshot_keys:
                raise ValueError("object_outside_snapshot")
            return
        prefix = str(cloudfront.get("prefix") or "").strip()
        if not prefix or not key.startswith(prefix):
            raise ValueError("object_outside_prefix")
        if not bool(payload.get("recursive")) and not _direct_child_object(key, prefix):
            raise ValueError("non_recursive_descendant_denied")
        if "/" in key[len(prefix) :].rstrip("/") and not recursive_download:
            raise ValueError("recursive_access_without_permission")

    def _record_share_access_event(
        self,
        session,
        instance,
        payload: dict[str, Any],
        *,
        allowed: bool,
        access_mode: str,
        viewer_email: str | None,
        reason: str | None,
        programmatic: bool = False,
    ) -> None:
        event = {
            "accessed_at": utc_now_iso(),
            "allowed": bool(allowed),
            "access_mode": access_mode,
            "viewer_email": str(viewer_email or "").strip().lower() or None,
            "denial_reason": reason,
            "programmatic": bool(programmatic),
        }
        events = list(payload.get("audit_events") or [])
        events.append(event)
        updates = {
            "audit_events": events[-100:],
            "last_accessed_at": event["accessed_at"] if allowed else payload.get("last_accessed_at"),
            "last_denial_reason": None if allowed else reason,
        }
        if allowed:
            updates["access_count"] = int(payload.get("access_count") or 0) + 1
            if programmatic:
                updates["programmatic_package_count"] = (
                    int(payload.get("programmatic_package_count") or 0) + 1
                )
        self.backend.update_instance_json(session, instance, updates)

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
