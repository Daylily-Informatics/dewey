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
    SHARE_ROOT_TEMPLATE,
    SHARE_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

DEFAULT_SHARE_HOST = "127.0.0.1"
SHARE_TARGET_KINDS = {"artifact_object", "artifact_prefix", "artifact_set", "mixed_set"}
SHARE_DELIVERY_MODES = {
    "presigned_s3",
    "presigned_s3_manifest",
    "cloudfront_signed_url",
    "cloudfront_signed_cookie",
    "dewey_html_browser",
}


def _clean_list(values: list[Any] | tuple[Any, ...] | set[Any] | None) -> list[str]:
    return [str(item or "").strip() for item in (values or []) if str(item or "").strip()]


class SharingServiceMixin:
    @staticmethod
    def _parse_share_s3_uri(value: str, *, require_prefix: bool = False) -> tuple[str, str, str]:
        raw = str(value or "").strip()
        if not raw.startswith("s3://"):
            raise ValueError("root_uri must use s3://")
        body = raw[5:]
        bucket, sep, key = body.partition("/")
        bucket = bucket.strip()
        key = key.strip().lstrip("/")
        if not bucket:
            raise ValueError("S3 bucket is required")
        if require_prefix:
            key = key.rstrip("/") + "/" if key else ""
        normalized = f"s3://{bucket}/{key}" if key else f"s3://{bucket}/"
        return bucket, key, normalized

    def _request_payer_for_bucket(self, bucket: str) -> str | None:
        return "requester" if str(bucket or "").strip() in self.requester_pays_buckets else None

    def _require_cloudfront_signer(self):
        signer = getattr(self, "cloudfront_signer", None)
        if signer is None:
            raise RuntimeError("CloudFront delivery requires explicit CloudFront signer config")
        return signer

    def _validate_cloudfront_origin(self, *, bucket: str, key: str) -> None:
        storage_uri = f"s3://{str(bucket or '').strip()}/{str(key or '').strip().lstrip('/')}"
        approved = [item.rstrip("/") for item in getattr(self, "share_approved_origins", [])]
        if not approved:
            raise RuntimeError("CloudFront delivery requires explicit approved share origins")
        if any(storage_uri == origin or storage_uri.startswith(origin.rstrip("/") + "/") for origin in approved):
            return
        raise ValueError(f"CloudFront origin is not approved for sharing: s3://{bucket}")

    def _normalize_share_expiry(self, expires_at: str | None, ttl_seconds: int | None = None) -> str:
        expiry = self._normalize_expiry(expires_at, ttl_seconds=ttl_seconds)
        parsed = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        max_expiry = datetime.now(timezone.utc) + timedelta(days=int(self.share_max_lifetime_days))
        if parsed > max_expiry:
            raise ValueError("share expires_at exceeds configured maximum share lifetime")
        return expiry

    def _share_policy_allows(
        self,
        *,
        payload: dict[str, Any],
        actor_email: str | None,
        actor_groups: list[str] | tuple[str, ...] | set[str] | None,
    ) -> bool:
        email = str(actor_email or "").strip().lower()
        if not email:
            return False
        owner = str(payload.get("owner_email") or "").strip().lower()
        if owner and email == owner:
            return True
        allowed_users = {item.lower() for item in _clean_list(payload.get("allowed_users"))}
        if email in allowed_users:
            return True
        _, _, domain = email.partition("@")
        allowed_domains = {item.lower().lstrip("@") for item in _clean_list(payload.get("allowed_domains"))}
        if domain and domain in allowed_domains:
            return True
        groups = {str(item or "").strip() for item in (actor_groups or []) if str(item or "").strip()}
        allowed_groups = set(_clean_list(payload.get("allowed_groups")))
        return bool(groups & allowed_groups)

    @staticmethod
    def _share_audit_event(
        *,
        route: str,
        decision: str,
        actor_email: str | None,
        actor_groups: list[str] | tuple[str, ...] | set[str] | None,
        ip: str | None = None,
        user_agent: str | None = None,
        delivery_mode: str | None = None,
        denial_reason: str | None = None,
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "timestamp": utc_now_iso(),
            "route": str(route or "").strip(),
            "decision": str(decision or "").strip(),
            "actor_email": str(actor_email or "").strip().lower() or None,
            "actor_groups": _clean_list(actor_groups),
            "ip": str(ip or "").strip() or None,
            "user_agent": str(user_agent or "").strip() or None,
            "delivery_mode": str(delivery_mode or "").strip() or None,
            "denial_reason": str(denial_reason or "").strip() or None,
            "target": dict(target or {}),
        }

    def _append_share_audit(self, session, share_instance, event: dict[str, Any]) -> None:
        payload = normalize_instance_payload(share_instance)
        events = list(payload.get("audit_events") or [])
        events.append(dict(event))
        updates = {
            "audit_events": events[-500:],
            "last_audit_at": event.get("timestamp") or utc_now_iso(),
        }
        if event.get("decision") == "allow":
            updates["last_accessed_at"] = event.get("timestamp") or utc_now_iso()
            updates["last_accessed_by"] = event.get("actor_email")
            updates["access_count"] = int(payload.get("access_count") or 0) + 1
        self.backend.update_instance_json(session, share_instance, updates)

    def _artifact_member_from_instance(
        self,
        artifact_instance,
        *,
        expected_kind: str | None = None,
    ) -> dict[str, Any]:
        payload = normalize_instance_payload(artifact_instance)
        storage_kind = str(payload.get("storage_kind") or "object").strip().lower()
        if expected_kind == "artifact_object" and storage_kind != "object":
            raise ValueError("artifact_object target requires an object-backed artifact")
        if expected_kind == "artifact_prefix" and storage_kind != "prefix":
            raise ValueError("artifact_prefix target requires a prefix artifact")
        if str(payload.get("storage_backend") or "").strip().lower() != "s3":
            raise ValueError("share targets must be s3-backed")
        bucket = str(payload.get("bucket") or "").strip()
        key = str(payload.get("key") or "").strip().lstrip("/")
        if not bucket or not key:
            raise ValueError("share target artifact is missing bucket/key")
        target_kind = "artifact_prefix" if storage_kind == "prefix" else "artifact_object"
        return {
            "target_kind": target_kind,
            "artifact_euid": artifact_instance.euid,
            "bucket": bucket,
            "key": key.rstrip("/") + "/" if target_kind == "artifact_prefix" else key,
            "version_id": str(payload.get("version_id") or "").strip() or None,
            "filename": str(payload.get("original_filename") or artifact_instance.euid),
            "storage_uri": str(payload.get("storage_uri") or f"s3://{bucket}/{key}"),
            "content_type": payload.get("content_type"),
            "size": payload.get("size"),
        }

    def _expand_share_targets(
        self,
        session,
        *,
        target_kind: str,
        target_euid: str | None = None,
        targets: list[dict[str, Any]] | None = None,
        depth: int = 0,
        visited: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        if depth > 8:
            raise ValueError("mixed_set expansion exceeded maximum depth")
        visited = visited or set()
        clean_kind = str(target_kind or "").strip().lower()
        if clean_kind not in SHARE_TARGET_KINDS:
            raise ValueError("target_kind must be artifact_object, artifact_prefix, artifact_set, or mixed_set")
        clean_euid = str(target_euid or "").strip()
        if clean_kind in {"artifact_object", "artifact_prefix"}:
            target = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=clean_euid,
            )
            if target is None:
                raise DeweyNotFoundError(f"Artifact not found: {clean_euid}")
            return [self._artifact_member_from_instance(target, expected_kind=clean_kind)]
        if clean_kind == "artifact_set":
            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=clean_euid,
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {clean_euid}")
            members = self.backend.list_children(
                session,
                parent=artifact_set,
                relationship_type="artifact_set_member",
            )
            return [self._artifact_member_from_instance(member) for member in members]

        if clean_euid:
            if clean_euid in visited:
                raise ValueError("mixed_set target cycle detected")
            visited.add(clean_euid)
            share = self.backend.find_by_euid(
                session,
                template_code=SHARE_TEMPLATE,
                euid=clean_euid,
            )
            if share is None:
                raise DeweyNotFoundError(f"Mixed set share not found: {clean_euid}")
            payload = normalize_instance_payload(share)
            if str(payload.get("target_kind") or "").strip().lower() != "mixed_set":
                raise ValueError("mixed_set target_euid must refer to a mixed_set share")
            raw_targets = list(payload.get("targets") or [])
        else:
            raw_targets = list(targets or [])
        expanded: list[dict[str, Any]] = []
        for raw_target in raw_targets:
            if not isinstance(raw_target, dict):
                raise ValueError("mixed_set targets must be objects")
            expanded.extend(
                self._expand_share_targets(
                    session,
                    target_kind=str(raw_target.get("target_kind") or ""),
                    target_euid=str(raw_target.get("target_euid") or ""),
                    depth=depth + 1,
                    visited=set(visited),
                )
            )
        deduped: dict[tuple[str, str, str | None], dict[str, Any]] = {}
        for item in expanded:
            deduped[(str(item["bucket"]), str(item["key"]), item.get("version_id"))] = item
        return list(deduped.values())

    def create_share(
        self,
        *,
        target_kind: str,
        target_euid: str | None,
        targets: list[dict[str, Any]] | None,
        name: str | None,
        purpose: str | None,
        owner_email: str | None,
        allowed_users: list[str] | None,
        allowed_domains: list[str] | None,
        allowed_groups: list[str] | None,
        delivery_modes: list[str] | None,
        expires_at: str | None,
        ttl_seconds: int | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_kind = str(target_kind or "").strip().lower()
        if clean_kind not in SHARE_TARGET_KINDS:
            raise ValueError("target_kind must be artifact_object, artifact_prefix, artifact_set, or mixed_set")
        clean_modes = _clean_list(delivery_modes) or ["presigned_s3_manifest"]
        invalid_modes = sorted(set(clean_modes) - SHARE_DELIVERY_MODES)
        if invalid_modes:
            raise ValueError("unsupported delivery modes: " + ", ".join(invalid_modes))
        clean_targets = [dict(item) for item in list(targets or [])]
        if clean_kind == "mixed_set" and not clean_targets and not str(target_euid or "").strip():
            raise ValueError("mixed_set requires targets")
        expiry = self._normalize_share_expiry(expires_at, ttl_seconds=ttl_seconds)
        created_at = utc_now_iso()
        payload = {
            "target_kind": clean_kind,
            "target_euid": str(target_euid or "").strip() or None,
            "targets": clean_targets,
            "name": str(name or "").strip() or None,
            "purpose": str(purpose or "").strip() or None,
            "owner_email": str(owner_email or "").strip().lower() or None,
            "allowed_users": [item.lower() for item in _clean_list(allowed_users)],
            "allowed_domains": [item.lower().lstrip("@") for item in _clean_list(allowed_domains)],
            "allowed_groups": _clean_list(allowed_groups),
            "delivery_modes": clean_modes,
            "expires_at": expiry,
            "default_signed_ttl_seconds": int(ttl_seconds or self.share_default_signed_ttl_seconds),
        }
        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="share.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response
            members = self._expand_share_targets(
                session,
                target_kind=clean_kind,
                target_euid=payload["target_euid"],
                targets=clean_targets,
            )
            if not members:
                raise ValueError("share target expansion produced no members")
            if any(mode.startswith("cloudfront") or mode == "dewey_html_browser" for mode in clean_modes):
                self._require_cloudfront_signer()
                for member in members:
                    self._validate_cloudfront_origin(
                        bucket=str(member["bucket"]),
                        key=str(member["key"]),
                    )
            share = self.backend.create_instance(
                session,
                template_code=SHARE_TEMPLATE,
                name=payload["name"] or f"share:{clean_kind}",
                json_addl={
                    **payload,
                    "status": "active",
                    "starts_at": created_at,
                    "created_at": created_at,
                    "member_count": len(members),
                    "access_count": 0,
                    "last_accessed_at": None,
                    "last_accessed_by": None,
                    "audit_events": [],
                    "revoked_at": None,
                    "revoked_by": None,
                    "revocation_reason": None,
                    "cloudfront": {
                        "distribution_domain": getattr(
                            getattr(self, "cloudfront_signer", None),
                            "distribution_domain",
                            None,
                        )
                    }
                    if any(mode.startswith("cloudfront") or mode == "dewey_html_browser" for mode in clean_modes)
                    else {},
                },
            )
            for raw_target in ([{"target_kind": clean_kind, "target_euid": payload["target_euid"]}] if clean_kind != "mixed_set" else clean_targets):
                raw_kind = str(raw_target.get("target_kind") or "").strip().lower()
                raw_euid = str(raw_target.get("target_euid") or "").strip()
                template_code = (
                    ARTIFACT_SET_TEMPLATE
                    if raw_kind == "artifact_set"
                    else SHARE_TEMPLATE
                    if raw_kind == "mixed_set"
                    else ARTIFACT_TEMPLATE
                )
                target = self.backend.find_by_euid(session, template_code=template_code, euid=raw_euid)
                if target is not None:
                    self.backend.create_lineage(
                        session,
                        parent=target,
                        child=share,
                        relationship_type="has_share",
                    )
            body = self._share_response(share)
            self._store_idempotency(
                session,
                operation="share.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def get_share(self, share_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            share = self.backend.find_by_euid(
                session,
                template_code=SHARE_TEMPLATE,
                euid=str(share_euid or "").strip(),
            )
            if share is None:
                raise DeweyNotFoundError(f"Share not found: {share_euid}")
            return self._share_response(share)

    def list_shares(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=SHARE_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            return [self._share_response(row) for row in rows]

    def create_share_access_package(
        self,
        share_euid: str,
        *,
        delivery_mode: str,
        actor_email: str | None,
        actor_groups: list[str] | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        signed_ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        clean_mode = str(delivery_mode or "").strip().lower() or "presigned_s3_manifest"
        if clean_mode not in SHARE_DELIVERY_MODES:
            raise ValueError("unsupported delivery mode")
        with self.backend.session_scope(commit=True) as session:
            share = self.backend.find_by_euid(
                session,
                template_code=SHARE_TEMPLATE,
                euid=str(share_euid or "").strip(),
                for_update=True,
            )
            if share is None:
                raise DeweyNotFoundError(f"Share not found: {share_euid}")
            payload = normalize_instance_payload(share)
            if str(payload.get("status") or "").lower() != "active":
                event = self._share_audit_event(
                    route="access_package",
                    decision="deny",
                    actor_email=actor_email,
                    actor_groups=actor_groups,
                    ip=ip,
                    user_agent=user_agent,
                    delivery_mode=clean_mode,
                    denial_reason="inactive_or_revoked",
                )
                self._append_share_audit(session, share, event)
                raise ValueError("share is not active")
            expires_at = str(payload.get("expires_at") or "").strip()
            if expires_at:
                expiry_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expiry_dt <= datetime.now(timezone.utc):
                    self.backend.update_instance_json(session, share, {"status": "expired"})
                    event = self._share_audit_event(
                        route="access_package",
                        decision="deny",
                        actor_email=actor_email,
                        actor_groups=actor_groups,
                        ip=ip,
                        user_agent=user_agent,
                        delivery_mode=clean_mode,
                        denial_reason="expired",
                    )
                    self._append_share_audit(session, share, event)
                    raise ValueError("share has expired")
            if clean_mode not in set(payload.get("delivery_modes") or []):
                event = self._share_audit_event(
                    route="access_package",
                    decision="deny",
                    actor_email=actor_email,
                    actor_groups=actor_groups,
                    ip=ip,
                    user_agent=user_agent,
                    delivery_mode=clean_mode,
                    denial_reason="delivery_mode_not_allowed",
                )
                self._append_share_audit(session, share, event)
                raise ValueError("delivery mode is not allowed for this share")
            if not self._share_policy_allows(
                payload=payload,
                actor_email=actor_email,
                actor_groups=actor_groups,
            ):
                event = self._share_audit_event(
                    route="access_package",
                    decision="deny",
                    actor_email=actor_email,
                    actor_groups=actor_groups,
                    ip=ip,
                    user_agent=user_agent,
                    delivery_mode=clean_mode,
                    denial_reason="policy_denied",
                )
                self._append_share_audit(session, share, event)
                raise PermissionError("share access denied")
            ttl_limit = max(60, int(signed_ttl_seconds or payload.get("default_signed_ttl_seconds") or self.share_default_signed_ttl_seconds))
            members = self._expand_share_targets(
                session,
                target_kind=str(payload.get("target_kind") or ""),
                target_euid=str(payload.get("target_euid") or "").strip() or None,
                targets=list(payload.get("targets") or []),
            )
            package: dict[str, Any] = {
                "share_euid": share.euid,
                "delivery_mode": clean_mode,
                "expires_in": ttl_limit,
                "manifest": [],
            }
            if clean_mode in {"presigned_s3", "presigned_s3_manifest"}:
                manifest = []
                for member in members:
                    if member["target_kind"] != "artifact_object":
                        if clean_mode == "presigned_s3":
                            raise ValueError("presigned_s3 is only valid for one object target")
                        manifest.append({**member, "status": "prefix_not_presigned"})
                        continue
                    request_payer = self._request_payer_for_bucket(str(member["bucket"]))
                    self._require_storage().head_object(
                        bucket=str(member["bucket"]),
                        key=str(member["key"]),
                        version_id=member.get("version_id"),
                        request_payer=request_payer,
                    )
                    signed_url = self._require_storage().generate_presigned_get_url(
                        bucket=str(member["bucket"]),
                        key=str(member["key"]),
                        version_id=member.get("version_id"),
                        expires_in=ttl_limit,
                        request_payer=request_payer,
                    )
                    manifest.append(
                        {
                            **member,
                            "status": "active",
                            "signed_url": signed_url,
                            "requester_pays": request_payer == "requester",
                            "curl": f"curl -L {signed_url!r} -o {member['filename']!r}",
                            "wget": f"wget -O {member['filename']!r} {signed_url!r}",
                        }
                    )
                if clean_mode == "presigned_s3" and len(manifest) == 1:
                    package["signed_url"] = manifest[0].get("signed_url")
                package["manifest"] = manifest
            elif clean_mode == "cloudfront_signed_url":
                signer = self._require_cloudfront_signer()
                manifest = []
                for member in members:
                    if member["target_kind"] != "artifact_object":
                        raise ValueError("cloudfront_signed_url requires object targets")
                    self._validate_cloudfront_origin(bucket=str(member["bucket"]), key=str(member["key"]))
                    signed = signer.sign_url(key=str(member["key"]), expires_in=ttl_limit)
                    manifest.append({**member, "signed_url": signed.access_url, "resource": signed.resource, "expires_at": signed.expires_at})
                package["manifest"] = manifest
                if len(manifest) == 1:
                    package["signed_url"] = manifest[0]["signed_url"]
            elif clean_mode in {"cloudfront_signed_cookie", "dewey_html_browser"}:
                signer = self._require_cloudfront_signer()
                prefixes = []
                for member in members:
                    key = str(member["key"])
                    prefix = key if member["target_kind"] == "artifact_prefix" else key.rsplit("/", 1)[0] + "/" if "/" in key else ""
                    self._validate_cloudfront_origin(bucket=str(member["bucket"]), key=prefix or key)
                    signed = signer.sign_prefix_cookies(prefix=prefix or key, expires_in=ttl_limit)
                    prefixes.append({**member, "resource": signed.resource, "cookies": signed.cookies, "expires_at": signed.expires_at})
                package["manifest"] = prefixes
                if prefixes:
                    package["cookies"] = prefixes[0].get("cookies", {})
            event = self._share_audit_event(
                route="access_package",
                decision="allow",
                actor_email=actor_email,
                actor_groups=actor_groups,
                ip=ip,
                user_agent=user_agent,
                delivery_mode=clean_mode,
            )
            self._append_share_audit(session, share, event)
            return package

    def revoke_share(
        self,
        share_euid: str,
        *,
        revoked_by: str | None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        with self.backend.session_scope(commit=True) as session:
            share = self.backend.find_by_euid(
                session,
                template_code=SHARE_TEMPLATE,
                euid=str(share_euid or "").strip(),
                for_update=True,
            )
            if share is None:
                raise DeweyNotFoundError(f"Share not found: {share_euid}")
            self.backend.update_instance_json(
                session,
                share,
                {
                    "status": "revoked",
                    "revoked_at": utc_now_iso(),
                    "revoked_by": str(revoked_by or "").strip() or None,
                    "revocation_reason": str(reason or "").strip() or None,
                },
            )
            self._append_share_audit(
                session,
                share,
                self._share_audit_event(
                    route="revoke",
                    decision="revoke",
                    actor_email=revoked_by,
                    actor_groups=[],
                    denial_reason=str(reason or "").strip() or None,
                ),
            )
            return self._share_response(share)

    def list_share_audit(self, share_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            share = self.backend.find_by_euid(
                session,
                template_code=SHARE_TEMPLATE,
                euid=str(share_euid or "").strip(),
            )
            if share is None:
                raise DeweyNotFoundError(f"Share not found: {share_euid}")
            payload = normalize_instance_payload(share)
            return {"share_euid": share.euid, "items": list(payload.get("audit_events") or [])}

    def create_share_root(
        self,
        *,
        root_uri: str,
        name: str | None,
        purpose: str | None,
        owner_email: str | None,
        allowed_delivery_modes: list[str] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        bucket, prefix, normalized_uri = self._parse_share_s3_uri(
            root_uri,
            require_prefix=True,
        )
        modes = _clean_list(allowed_delivery_modes) or ["presigned_s3_manifest", "cloudfront_signed_cookie"]
        invalid_modes = sorted(set(modes) - SHARE_DELIVERY_MODES)
        if invalid_modes:
            raise ValueError("unsupported delivery modes: " + ", ".join(invalid_modes))
        payload = {
            "root_uri": normalized_uri,
            "bucket": bucket,
            "prefix": prefix,
            "name": str(name or "").strip() or None,
            "purpose": str(purpose or "").strip() or None,
            "owner_email": str(owner_email or "").strip().lower() or None,
            "allowed_delivery_modes": modes,
        }
        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="share_root.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response
            root = self.backend.create_instance(
                session,
                template_code=SHARE_ROOT_TEMPLATE,
                name=payload["name"] or f"share_root:{normalized_uri}",
                json_addl={
                    **payload,
                    "status": "active",
                    "created_at": utc_now_iso(),
                    "auto_register_children": False,
                },
            )
            body = self._share_root_response(root)
            self._store_idempotency(
                session,
                operation="share_root.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def list_share_roots(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=SHARE_ROOT_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            return [self._share_root_response(row) for row in rows]

    def create_share_root_subset(
        self,
        share_root_euid: str,
        *,
        targets: list[dict[str, Any]],
        name: str | None,
        purpose: str | None,
        owner_email: str | None,
        allowed_users: list[str] | None,
        allowed_domains: list[str] | None,
        allowed_groups: list[str] | None,
        delivery_modes: list[str] | None,
        expires_at: str | None,
        ttl_seconds: int | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            root = self.backend.find_by_euid(
                session,
                template_code=SHARE_ROOT_TEMPLATE,
                euid=str(share_root_euid or "").strip(),
            )
            if root is None:
                raise DeweyNotFoundError(f"Share root not found: {share_root_euid}")
            root_payload = normalize_instance_payload(root)
            root_bucket = str(root_payload.get("bucket") or "")
            root_prefix = str(root_payload.get("prefix") or "")
            members = self._expand_share_targets(
                session,
                target_kind="mixed_set",
                targets=targets,
            )
            for member in members:
                if str(member["bucket"]) != root_bucket or not str(member["key"]).startswith(root_prefix):
                    raise ValueError("subset target is outside the registered share root")
        return self.create_share(
            target_kind="mixed_set",
            target_euid=None,
            targets=targets,
            name=name,
            purpose=purpose,
            owner_email=owner_email,
            allowed_users=allowed_users,
            allowed_domains=allowed_domains,
            allowed_groups=allowed_groups,
            delivery_modes=delivery_modes,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _share_reference_diagnostic(
        *,
        code: str,
        summary: str,
        retryable: bool,
        checked_at: str | None = None,
        admin_detail: str | None = None,
    ) -> dict[str, Any]:
        diagnostic = {
            "diagnostic_code": str(code or "").strip(),
            "diagnostic_summary": str(summary or "").strip(),
            "last_checked_at": checked_at or utc_now_iso(),
            "retryable": bool(retryable),
        }
        detail = str(admin_detail or "").strip()
        if detail:
            diagnostic["admin_detail"] = detail
        return diagnostic

    @classmethod
    def _missing_storage_object_diagnostic(cls, checked_at: str | None = None) -> dict[str, Any]:
        return cls._share_reference_diagnostic(
            code="storage_object_missing",
            summary="Target artifact object was not found in configured storage.",
            retryable=True,
            checked_at=checked_at,
            admin_detail=(
                "Repair the artifact storage metadata or restore the target object, then retry "
                "the share reference."
            ),
        )

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

    def issue_share_reference_access(
        self,
        share_reference_euid: str,
        *,
        accessed_by: str | None = None,
        presign_ttl_seconds: int = 900,
    ) -> dict[str, Any]:
        accessed_at = utc_now_iso()
        ttl_limit = max(60, min(3600, int(presign_ttl_seconds)))
        with self.backend.session_scope(commit=True) as session:
            instance = self.backend.find_by_euid(
                session,
                template_code=SHARE_REFERENCE_TEMPLATE,
                euid=str(share_reference_euid or "").strip(),
                for_update=True,
            )
            if instance is None:
                raise DeweyNotFoundError(f"Share reference not found: {share_reference_euid}")
            payload = normalize_instance_payload(instance)
            if payload.get("revoked_at") or str(payload.get("status") or "").lower() == "revoked":
                raise ValueError("share reference has been revoked")
            expires_at = str(payload.get("expires_at") or "").strip()
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                seconds_remaining = int((expires_dt - datetime.now(timezone.utc)).total_seconds())
                if seconds_remaining <= 0:
                    raise ValueError("share reference has expired")
                ttl_limit = max(60, min(ttl_limit, seconds_remaining))
            status_value = str(payload.get("status") or "").lower()
            if status_value and status_value != "active":
                raise ValueError(f"share reference is {status_value}; retry after repair")

            access_url = str(payload.get("access_url") or "").strip() or None
            manifest: list[dict[str, Any]] = []
            target_type = str(payload.get("target_type") or "").lower()
            transport = str(payload.get("transport") or "").lower()
            if transport == "presigned_s3" and target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=str(payload.get("target_euid") or "").strip(),
                )
                if target is None:
                    raise DeweyNotFoundError(f"Target not found: {payload.get('target_euid')}")
                artifact_payload = normalize_instance_payload(target)
                try:
                    self._require_storage().head_object(
                        bucket=str(artifact_payload.get("bucket") or ""),
                        key=str(artifact_payload.get("key") or ""),
                        version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                    )
                except StorageObjectNotFoundError as exc:
                    diagnostic = self._missing_storage_object_diagnostic(checked_at=accessed_at)
                    self.backend.update_instance_json(
                        session,
                        instance,
                        {
                            "status": "error",
                            "access_url": None,
                            "diagnostic": diagnostic,
                            "last_checked_at": accessed_at,
                        },
                    )
                    raise ValueError(diagnostic["diagnostic_summary"]) from exc
                access_url = self._require_storage().generate_presigned_get_url(
                    bucket=str(artifact_payload.get("bucket") or ""),
                    key=str(artifact_payload.get("key") or ""),
                    version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                    expires_in=ttl_limit,
                )
            elif transport == "presigned_s3" and target_type == "artifact_set":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=str(payload.get("target_euid") or "").strip(),
                )
                if target is None:
                    raise DeweyNotFoundError(f"Target not found: {payload.get('target_euid')}")
                for member in self.backend.list_children(
                    session,
                    parent=target,
                    relationship_type="artifact_set_member",
                ):
                    artifact_payload = normalize_instance_payload(member)
                    entry = {
                        "artifact_euid": member.euid,
                        "filename": str(artifact_payload.get("original_filename") or member.euid),
                        "storage_uri": str(artifact_payload.get("storage_uri") or ""),
                    }
                    if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                        entry["status"] = "error"
                        entry["detail"] = "artifact is not s3-backed"
                    else:
                        self._require_storage().head_object(
                            bucket=str(artifact_payload.get("bucket") or ""),
                            key=str(artifact_payload.get("key") or ""),
                            version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                        )
                        entry["status"] = "active"
                        entry["access_url"] = self._require_storage().generate_presigned_get_url(
                            bucket=str(artifact_payload.get("bucket") or ""),
                            key=str(artifact_payload.get("key") or ""),
                            version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                            expires_in=ttl_limit,
                        )
                    manifest.append(entry)

            access_count = int(payload.get("access_count") or 0) + 1
            self.backend.update_instance_json(
                session,
                instance,
                {
                    "last_accessed_at": accessed_at,
                    "last_accessed_by": str(accessed_by or "").strip() or None,
                    "access_count": access_count,
                },
            )
            body = self._share_reference_response(instance)
            if access_url:
                body["access_url"] = access_url
            if manifest:
                body["manifest"] = manifest
            return body

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
            diagnostic: dict[str, Any] | None = None
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
                try:
                    self._require_storage().head_object(
                        bucket=str(artifact_payload.get("bucket") or ""),
                        key=str(artifact_payload.get("key") or ""),
                        version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                    )
                except StorageObjectNotFoundError:
                    status_value = "error"
                    diagnostic = self._missing_storage_object_diagnostic(checked_at=starts_at)
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
                    "diagnostic": diagnostic,
                    "manifest": manifest,
                    "connection": connection or {},
                    "member_count": member_count,
                    "transport_config": clean_transport_config,
                    "managed_access": clean_target_type == "artifact"
                    and clean_transport == "presigned_s3",
                    "access_count": 0,
                    "last_accessed_at": None,
                    "last_accessed_by": None,
                    "revoked_at": None,
                    "revoked_by": None,
                    "revocation_reason": None,
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

    def retry_share_reference(
        self,
        share_reference_euid: str,
        *,
        retried_by: str | None = None,
    ) -> dict[str, Any]:
        clean_euid = str(share_reference_euid or "").strip()
        if not clean_euid:
            raise ValueError("share_reference_euid is required")
        checked_at = utc_now_iso()
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
            status_value = str(payload.get("status") or "").lower()
            if payload.get("revoked_at") or status_value == "revoked":
                raise ValueError("share reference has been revoked")
            expires_at = str(payload.get("expires_at") or "").strip()
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expires_dt <= datetime.now(timezone.utc):
                    self.backend.update_instance_json(session, instance, {"status": "expired"})
                    raise ValueError("share reference has expired")
            if str(payload.get("target_type") or "").lower() != "artifact":
                raise ValueError("retry is only supported for artifact share references")
            if str(payload.get("transport") or "").lower() != "presigned_s3":
                raise ValueError("retry is only supported for presigned_s3 share references")
            if not payload.get("managed_access"):
                raise ValueError("retry is only supported for Dewey-managed share references")

            target = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=str(payload.get("target_euid") or "").strip(),
            )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {payload.get('target_euid')}")
            artifact_payload = normalize_instance_payload(target)
            if str(artifact_payload.get("storage_kind") or "object").lower() != "object":
                raise ValueError("share reference target is not an object-backed artifact")
            if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
                raise ValueError("share reference target is not s3-backed")

            try:
                self._require_storage().head_object(
                    bucket=str(artifact_payload.get("bucket") or ""),
                    key=str(artifact_payload.get("key") or ""),
                    version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                )
            except StorageObjectNotFoundError:
                diagnostic = self._missing_storage_object_diagnostic(checked_at=checked_at)
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "status": "error",
                        "access_url": None,
                        "diagnostic": diagnostic,
                        "last_checked_at": checked_at,
                        "last_retried_at": checked_at,
                        "last_retried_by": str(retried_by or "").strip() or None,
                    },
                )
                return self._share_reference_response(instance)

            access_url = f"/share-references/{instance.euid}"
            self.backend.update_instance_json(
                session,
                instance,
                {
                    "status": "active",
                    "access_url": access_url,
                    "managed_access": True,
                    "diagnostic": None,
                    "last_checked_at": checked_at,
                    "last_retried_at": checked_at,
                    "last_retried_by": str(retried_by or "").strip() or None,
                },
            )
            self.backend.update_instance_json(
                session,
                target,
                {
                    "share_status": "active",
                    "share_last_issued_at": checked_at,
                },
            )
            return self._share_reference_response(instance)

    def revoke_share_reference(
        self,
        share_reference_euid: str = "",
        *,
        revoked_by: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | tuple[int, dict[str, Any]]:
        clean_euid = str(share_reference_euid or "").strip()
        if not clean_euid:
            raise ValueError("share_reference_euid is required")
        payload = {
            "share_reference_euid": clean_euid,
            "revoked_by": str(revoked_by or "").strip() or None,
            "revocation_reason": str(reason or "").strip() or None,
        }
        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            if idempotency_key:
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
            manifest = []
            for entry in list(current.get("manifest") or []):
                clean_entry = dict(entry)
                clean_entry.pop("access_url", None)
                clean_entry["status"] = "revoked"
                manifest.append(clean_entry)
            if current.get("status") != "revoked":
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "status": "revoked",
                        "revoked_at": utc_now_iso(),
                        "revoked_by": payload["revoked_by"],
                        "revocation_reason": payload["revocation_reason"],
                        "access_url": None,
                        "manifest": manifest,
                    },
                )
            body = self._share_reference_response(instance)
            if idempotency_key:
                self._store_idempotency(
                    session,
                    operation="share_reference.revoke",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body
            return body

    def open_share_reference(self, share_reference_euid: str) -> dict[str, Any]:
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
            try:
                self._require_storage().head_object(
                    bucket=str(artifact_payload.get("bucket") or ""),
                    key=str(artifact_payload.get("key") or ""),
                    version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                )
            except StorageObjectNotFoundError as exc:
                diagnostic = self._missing_storage_object_diagnostic(checked_at=utc_now_iso())
                self.backend.update_instance_json(
                    session,
                    instance,
                    {
                        "status": "error",
                        "access_url": None,
                        "diagnostic": diagnostic,
                        "last_checked_at": diagnostic["last_checked_at"],
                    },
                )
                raise ValueError(diagnostic["diagnostic_summary"]) from exc
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
