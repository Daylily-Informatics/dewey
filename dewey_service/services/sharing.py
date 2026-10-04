"""Dewey managed share workflows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from dewey_service.services.base import DeweyNotFoundError
from dewey_service.registry_access import principal, require_record
from fastapi import HTTPException
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    SHARE_ROOT_TEMPLATE,
    SHARE_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

SHARE_TARGET_KINDS = {"artifact_object", "artifact_prefix", "artifact_set", "mixed_set"}
SHARE_DELIVERY_MODES = {
    "gateway",
    "presigned",
}


def _clean_list(values: list[Any] | tuple[Any, ...] | set[Any] | None) -> list[str]:
    return [str(item or "").strip() for item in (values or []) if str(item or "").strip()]


class SharingServiceMixin:
    @staticmethod
    def _parse_share_s3_uri(value: str, *, require_prefix: bool = False) -> tuple[str, str, str]:
        raw = str(value or "")
        if not raw.startswith("s3://"):
            raise ValueError("root_uri must use s3://")
        body = raw[5:]
        bucket, sep, key = body.partition("/")
        if not bucket or any(c.isspace() for c in bucket):
            raise ValueError("S3 bucket is required")
        if require_prefix:
            key = key.rstrip("/") + "/" if key else ""
        normalized = f"s3://{bucket}/{key}" if key else f"s3://{bucket}/"
        return bucket, key, normalized

    def _request_payer_for_bucket(self, bucket: str) -> str | None:
        return "requester" if str(bucket or "").strip() in self.requester_pays_buckets else None

    def _normalize_share_expiry(
        self, expires_at: str | None, ttl_seconds: int | None = None
    ) -> str:
        expiry = self._normalize_expiry(expires_at, ttl_seconds=None if expires_at else self.registry_defaults()["share_lifetime_days"] * 86400)
        parsed = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        max_expiry = datetime.now(timezone.utc) + timedelta(days=int(self.share_max_lifetime_days))
        if parsed <= datetime.now(timezone.utc):
            raise ValueError("Share expiry must be in the future")
        if parsed > max_expiry:
            raise ValueError("share expires_at exceeds configured maximum share lifetime")
        return expiry

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
        key = str(payload.get("key") or "")
        if not bucket or not key and storage_kind != "prefix":
            raise ValueError("share target artifact is missing bucket/key")
        target_kind = "artifact_prefix" if storage_kind == "prefix" else "artifact_object"
        return {
            "target_kind": target_kind,
            "artifact_euid": artifact_instance.euid,
            "bucket": bucket,
            "key": key + "/" if target_kind == "artifact_prefix" and key and not key.endswith("/") else key,
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
            raise ValueError(
                "target_kind must be artifact_object, artifact_prefix, artifact_set, or mixed_set"
            )
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
            from daylily_tapdb import generic_instance, generic_instance_lineage
            members = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.parent_instance_uid == artifact_set.uid,
                generic_instance_lineage.relationship_type == "artifact_set_member",
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False)).all()
            for member in members:
                require_record(self.backend, session, member, "share")
            return [self._artifact_member_from_instance(member) for member in members]

        if clean_euid:
            share = self._canonical_share(session, clean_euid)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required")
            members = self._share_members(session, share)
            for member in members:
                require_record(self.backend, session, member, "share")
            return [self._artifact_member_from_instance(member) for member in members]
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

    def _share_query(self, session):
        from daylily_tapdb import generic_instance
        template = self.backend.templates.get_template(session, SHARE_TEMPLATE, domain_code=self.backend.domain_code)
        if template is None:
            raise HTTPException(503, "Canonical share template is missing")
        return session.query(generic_instance).filter(generic_instance.template_uid == template.uid,
            generic_instance.type == "share", generic_instance.is_deleted.is_(False))

    def _share_members(self, session, share):
        from daylily_tapdb import generic_instance, generic_instance_lineage
        return session.query(generic_instance).join(generic_instance_lineage,
            generic_instance_lineage.parent_instance_uid == generic_instance.uid).filter(
            generic_instance_lineage.child_instance_uid == share.uid,
            generic_instance_lineage.relationship_type == "has_share",
            generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
            generic_instance.type == "artifact", generic_instance.domain_code == self.backend.domain_code).all()

    def _grant_targets(self, session, grant):
        from daylily_tapdb import generic_instance, generic_instance_lineage
        return session.query(generic_instance).join(generic_instance_lineage,
            generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
            generic_instance_lineage.parent_instance_uid == grant.uid,
            generic_instance_lineage.relationship_type == "share_grant_target",
            generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
            generic_instance.type == "artifact", generic_instance.domain_code == self.backend.domain_code).all()

    def _share_related(self, session, share, *, relationship, kind):
        from daylily_tapdb import generic_instance, generic_instance_lineage
        return session.query(generic_instance).join(generic_instance_lineage,
            generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
            generic_instance_lineage.parent_instance_uid == share.uid,
            generic_instance_lineage.relationship_type == relationship,
            generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
            generic_instance.type == kind, generic_instance.domain_code == self.backend.domain_code).all()

    def _share_grants(self, session, share):
        return self._share_related(session, share, relationship="share_grant", kind="share_grant")

    def sharing_upgrade_ready(self):
        from dewey_service.registry_access import POLICY_TEMPLATE
        from dewey_service.services.share_policy import SCHEMA_VERSION
        with self.backend.session_scope(commit=False) as session:
            marker = self.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE,
                field="policy_kind", value="sharing_schema")
            return bool(marker and normalize_instance_payload(marker).get("schema_version") == SCHEMA_VERSION
                and normalize_instance_payload(marker).get("status") == "verified")

    def _require_sharing(self):
        from dewey_service.share_context import require_share_context
        require_share_context()
        if not self.sharing_upgrade_ready():
            raise HTTPException(503, "Canonical sharing upgrade must be explicitly applied and verified")

    def _canonical_share(self, session, euid, *, lock=False):
        query = self._share_query(session).filter_by(euid=euid)
        share = (query.with_for_update() if lock else query).first()
        if share is None:
            raise DeweyNotFoundError("Share not found")
        if share.bstatus == "archived":
            raise HTTPException(410, "Share is archived")
        if normalize_instance_payload(share).get("schema_version") != 2:
            raise HTTPException(503, "Share requires explicit canonical upgrade")
        return share

    def _write_grants(self, session, share, grants, members, revision):
        from dewey_service.services.share_policy import GRANT_TEMPLATE
        targets = {member.euid: member for member in members}
        for data in grants:
            grant = self.backend.create_instance(session, template_code=GRANT_TEMPLATE,
                name="Share recipient grant", json_addl={k: v for k, v in {
                    **data, "status": "active", "policy_revision": revision, "created_at": utc_now_iso()}.items() if k != "target_euids"})
            self.backend.create_lineage(session, parent=share, child=grant, relationship_type="share_grant")
            for euid in data["target_euids"]:
                self.backend.create_lineage(session, parent=grant, child=targets[euid], relationship_type="share_grant_target")

    def _event(self, session, share, *, event_type, decision, grant=None, target=None, details=None):
        from dewey_service.services.share_policy import EVENT_TEMPLATE
        allowed = {"action", "reason", "policy_revision", "relative_key", "bytes_sent", "status_code",
            "outcome", "expires_in", "request_method", "range", "network", "source_event_index",
            "key", "version_id", "etag", "method", "server_bytes_sent", "response_completion_observed",
            "download_completion_observed", "inline_report", "expires_at", "ttl_seconds", "bearer_url_forwardable",
            "bundle_root", "context_euid", "historical_timestamp", "historical_actor", "historical_route"}
        clean = {k: v for k, v in (details or {}).items() if k in allowed}
        from dewey_service.share_context import current_share_audit_context
        from dewey_service.registry_access import maintenance_mode
        context = current_share_audit_context()
        request_id = context.get("request_id")
        trusted_tailnet = context.get("trusted_tailnet")
        managed_origin = context.get("managed_origin")
        if maintenance_mode():
            from dewey_service.audit import current_explicit_attribution
            attribution = current_explicit_attribution()
            if attribution is None or not attribution.request_id:
                raise ValueError("Native sharing conversion requires explicit request attribution")
            request_id = attribution.request_id
            # Native lifecycle work does not assert a web ingress observation.
            trusted_tailnet = None
            managed_origin = None
        elif not request_id:
            raise ValueError("Managed-share audit requires server request correlation")
        revision = clean.get("policy_revision", normalize_instance_payload(share).get("policy_revision"))
        if type(revision) is not int or revision < 1:
            raise ValueError("Managed-share audit requires the observed policy revision")
        row = self.backend.create_instance(session, template_code=EVENT_TEMPLATE, name=str(event_type),
            json_addl={"event_type": str(event_type), "decision": str(decision), "actor": principal().subject,
                "created_at": utc_now_iso(), "details": clean, "request_id": request_id,
                "trusted_tailnet": trusted_tailnet, "managed_origin": managed_origin,
                "policy_revision": revision})
        self.backend.create_lineage(session, parent=share, child=row, relationship_type="share_event")
        if grant is not None:
            self.backend.create_lineage(session, parent=grant, child=row, relationship_type="grant_event")
        if target is not None:
            self.backend.create_lineage(session, parent=target, child=row, relationship_type="share_target_event")
        return row.euid

    def append_share_event(self, share_euid, *, event_type, decision, grant_euid=None, target_euid=None, details=None):
        # Gateway calls this after authorization, including stream termination. No credentials are accepted.
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid)
            grant = next((g for g in self._share_grants(session, share) if g.euid == grant_euid), None)
            target = next((t for t in self._share_members(session, share) if t.euid == target_euid), None)
            if grant_euid and grant is None or target_euid and target is None:
                raise ValueError("Audit relationship is outside this share")
            return self._event(session, share, event_type=event_type, decision=decision, grant=grant, target=target, details=details)

    def _protected_share_path(self, session, bucket, key, *, action):
        from daylily_tapdb import generic_instance
        from dewey_service.registry_access import direct_record_clause
        from sqlalchemy import and_, or_, func, literal
        records = self._registry_query(session, scopes=("artifact",), authorize=False).filter(
            generic_instance.json_addl["storage_backend"].astext == "s3",
            generic_instance.json_addl["bucket"].astext == bucket,
            or_(generic_instance.json_addl["key"].astext == key, and_(
                generic_instance.json_addl["storage_kind"].astext == "prefix",
                func.left(literal(key), func.length(generic_instance.json_addl["key"].astext)) == generic_instance.json_addl["key"].astext))).all()
        for row in records:
            if row.bstatus == "archived":
                raise HTTPException(403, "A registered ancestor is archived")
            policies = self.backend.list_children(session, parent=row, relationship_type="registry_policy")
            if len(policies) != 1:
                raise HTTPException(503, "A registered ancestor lacks a unique policy")
            if normalize_instance_payload(policies[0]).get("explicit_restriction"):
                allowed = session.query(generic_instance.uid).filter(generic_instance.uid == row.uid,
                    direct_record_clause(session, generic_instance, "metadata" if action == "metadata" else "download")).first()
                if not allowed:
                    raise HTTPException(403, "A registered ancestor restricts this path")

    def _evaluate_share(self, session, share, target_euid, relative_key, action):
        from dewey_service.services.share_policy import expiry, selected, recipient_matches
        data = normalize_instance_payload(share)
        actor = principal()
        now = datetime.now(timezone.utc)
        if data.get("status") != "active" or share.bstatus == "archived" or expiry(data["expires_at"]) <= now:
            raise HTTPException(410, "Share is inactive or expired")
        if actor.email.lower() in data["denied_emails"]:
            raise HTTPException(403, "Share access denied")
        mode = "presigned" if action == "presign" else "gateway"
        if action not in {"metadata", "gateway", "report", "presign"}:
            raise ValueError("Unsupported share action")
        if action != "metadata" and mode not in data["delivery_modes"]:
            raise HTTPException(403, "Delivery mode is not enabled")
        target = next((t for t in self._share_members(session, share) if t.euid == target_euid), None)
        if target is None:
            raise HTTPException(403, "Target is not a persisted share member")
        member = self._artifact_member_from_instance(target)
        if member["target_kind"] == "artifact_object":
            if relative_key:
                raise ValueError("An object target does not accept relative_key")
            path, key = member["key"].rsplit("/", 1)[-1], member["key"]
        else:
            if not isinstance(relative_key, str) or "\x00" in relative_key:
                raise ValueError("relative_key must be a literal root-relative S3 key")
            path, key = relative_key, member["key"] + relative_key
        if not selected(path, data["include_patterns"], data["exclude_patterns"]):
            raise HTTPException(403, "Path is excluded from this share")
        self._protected_share_path(session, member["bucket"], key, action=action)
        candidates = []
        for grant in self._share_grants(session, share):
            rule = normalize_instance_payload(grant)
            if grant.type != "share_grant" or rule.get("status") != "active" or rule.get("policy_revision") != data["policy_revision"]:
                continue
            if expiry(rule["expires_at"]) <= now or not recipient_matches(rule, actor.email):
                continue
            if not any(t.euid == target_euid for t in self._grant_targets(session, grant)):
                continue
            if selected(path, rule["include_patterns"], rule["exclude_patterns"]):
                candidates.append((expiry(rule["expires_at"]), grant))
        if not candidates:
            raise HTTPException(403, "No current recipient grant permits this path")
        deadline, grant = max(candidates, key=lambda pair: pair[0])
        return {"bucket": member["bucket"], "key": key, "version_id": member.get("version_id"),
            "share_euid": share.euid, "target_euid": target.euid, "grant_euid": grant.euid,
            "policy_revision": data["policy_revision"], "expires_at": min(deadline, expiry(data["expires_at"])).isoformat(),
            "relative_key": relative_key, "filename": key.rsplit("/", 1)[-1]}

    def authorize_share_object(self, share_euid, target_euid, relative_key="", action="gateway"):
        self._require_sharing()
        denied = None
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid)
            try:
                result = self._evaluate_share(session, share, target_euid, relative_key, action)
            except HTTPException as exc:
                self._event(session, share, event_type="authorization", decision="deny", details={"action": action, "reason": str(exc.detail)})
                denied = exc
            else:
                grant = next(g for g in self._share_grants(session, share) if g.euid == result["grant_euid"])
                target = next(t for t in self._share_members(session, share) if t.euid == target_euid)
                self._event(session, share, event_type="authorization", decision="allow", grant=grant, target=target,
                    details={"action": action, "relative_key": relative_key, "policy_revision": result["policy_revision"]})
        if denied:
            raise denied
        return result

    def authorize_shared_storage(self, bucket, key, *, action="metadata"):
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            for share in self._share_query(session).filter_by(bstatus="active").all():
                if normalize_instance_payload(share).get("schema_version") != 2:
                    continue
                for target in self._share_members(session, share):
                    member = self._artifact_member_from_instance(target)
                    if member["bucket"] != bucket:
                        continue
                    relative = key[len(member["key"]):] if member["target_kind"] == "artifact_prefix" and key.startswith(member["key"]) else ""
                    if key != member["key"] and not relative:
                        continue
                    try:
                        self._evaluate_share(session, share, target.euid, relative, action)
                        return self.authorize_share_object(share.euid, target.euid, relative, action)
                    except HTTPException as exc:
                        if exc.status_code not in {403, 410}:
                            raise
        raise HTTPException(403, "No current share permits this S3 path")

    def create_share(self, *, target_kind, target_euid=None, targets=None, name=None, purpose=None,
            owner_email=None, allowed_users=None, allowed_domains=None, allowed_groups=None,
            delivery_modes=None, expires_at=None, ttl_seconds=None, idempotency_key,
            grants=None, include_patterns=None, exclude_patterns=None, denied_emails=None):
        from dewey_service.services.share_policy import normalized_policy
        self._require_sharing()
        actor = principal()
        if not actor.writable:
            raise HTTPException(403, "Sharing requires write access")
        signed_ttl = 900 if ttl_seconds is None else int(ttl_seconds)
        if not 1 <= signed_ttl <= 3600:
            raise ValueError("Signed URL lifetime must be 1..3600 seconds")
        source = {"allowed_users": allowed_users or [], "allowed_domains": allowed_domains or [],
            "allowed_groups": allowed_groups or [], "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns, "denied_emails": denied_emails or []}
        if grants is not None: source["grants"] = grants
        if delivery_modes is not None:
            source["delivery_modes"] = [{"dewey_html_browser": "gateway", "presigned_s3": "presigned", "presigned_s3_manifest": "presigned"}.get(m, m) for m in delivery_modes]
        fingerprint = self._fingerprint({**source, "actor_subject": actor.subject, "target_kind": target_kind, "target_euid": target_euid,
            "targets": targets, "expires_at": expires_at, "name": name, "purpose": purpose, "signed_ttl": signed_ttl})
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(session, operation="share.create", idempotency_key=idempotency_key, fingerprint=fingerprint)
            if replay is not None:
                share = self._canonical_share(session, replay.response["share_euid"])
                if not self._registry_share_manager(session, share):
                    raise HTTPException(403, "Current share management permission is required for creation replay")
                # A replay reports current lifecycle state, including revocation/expiry.
                # It cannot reactivate a share or disclose an old privileged snapshot.
                return replay.status_code, self._canonical_response(session, share, manager=True)
            deadline = self._normalize_share_expiry(expires_at)
            members = self._expand_share_targets(session, target_kind=target_kind, target_euid=target_euid, targets=targets)
            records = [self._registry_record(session, m["artifact_euid"], action="share") for m in members]
            if not records: raise ValueError("Share requires selected S3 targets")
            root = self._registry_record(session, target_euid, action="share") if target_euid and target_kind != "mixed_set" else None
            policy = normalized_policy(source, share_expiry=deadline, member_euids=[r.euid for r in records])
            grant_values = policy.pop("grants")
            share = self.backend.create_instance(session, template_code=SHARE_TEMPLATE, name=name or "Managed share",
                json_addl={**policy, "policy_revision": 1, "target_kind": target_kind, "target_euid": target_euid,
                    "targets": targets or [], "name": name, "purpose": purpose, "owner_subject": actor.subject,
                    "owner_email": actor.email, "audience": "recipients", "expires_at": deadline, "status": "active", "starts_at": utc_now_iso(),
                    "created_at": utc_now_iso(), "member_count": len(records), "default_signed_ttl_seconds": signed_ttl})
            for record in records + ([root] if root is not None and root.euid not in {r.euid for r in records} else []):
                self.backend.create_lineage(session, parent=record, child=share, relationship_type="has_share")
            self._write_grants(session, share, grant_values, records, 1)
            self._event(session, share, event_type="created", decision="change", details={"policy_revision": 1})
            body = self._canonical_response(session, share, manager=True)
            self._store_idempotency(session, operation="share.create", idempotency_key=idempotency_key,
                fingerprint=fingerprint, status_code=201, response=body)
            return 201, body

    def _canonical_response(self, session, share, *, manager):
        data = normalize_instance_payload(share)
        value = {**self._share_response(share), "euid": share.euid, "web_path": f"/shares/{share.euid}",
            "policy_revision": data["policy_revision"], "include_patterns": data["include_patterns"],
            "exclude_patterns": data["exclude_patterns"], "can_manage": manager, "schema_version": 2}
        if manager:
            value["denied_emails"] = data["denied_emails"]
            value["grants"] = [{**normalize_instance_payload(g), "grant_euid": g.euid,
                "target_euids": [t.euid for t in self._grant_targets(session, g)]} for g in self._share_grants(session, share)
                if normalize_instance_payload(g).get("policy_revision") == data["policy_revision"]]
            value["members"] = [self._artifact_member_from_instance(t) for t in self._share_members(session, share)]
            value["targets"] = [{"euid": t.euid, "name": t.name, "kind": normalize_instance_payload(t)["storage_kind"]} for t in self._share_members(session, share)]
        else:
            for name in ("target_euid", "targets", "member_count", "owner_email", "allowed_users", "allowed_domains", "allowed_groups", "include_patterns", "exclude_patterns"):
                value.pop(name, None)
        return value

    def get_share(self, share_euid):
        self._require_sharing()
        from dewey_service.services.share_policy import recipient_matches, expiry
        with self.backend.session_scope(commit=False) as session:
            share = self._canonical_share(session, share_euid)
            manager = self._registry_share_manager(session, share)
            data = normalize_instance_payload(share)
            if not manager:
                now = datetime.now(timezone.utc)
                if share.bstatus == "archived" or data["status"] != "active" or expiry(data["expires_at"]) <= now or principal().email.lower() in data["denied_emails"]:
                    raise HTTPException(403, "Share is not available")
                if not any(normalize_instance_payload(g).get("status") == "active" and
                        normalize_instance_payload(g).get("policy_revision") == data["policy_revision"] and
                        expiry(normalize_instance_payload(g)["expires_at"]) > now and
                        recipient_matches(normalize_instance_payload(g), principal().email) for g in self._share_grants(session, share)):
                    raise HTTPException(403, "No current recipient grant")
            return self._canonical_response(session, share, manager=manager)

    def _authorized_share_index_query(self, session):
        """Native recipient predicates precede search, ordering and pagination.

        This discovers share containers only. Every disclosed file still passes
        the canonical path evaluator and protected-ancestor checks separately.
        """
        from daylily_tapdb import generic_instance, generic_instance_lineage
        from sqlalchemy import DateTime, and_, cast, exists, literal, or_, select
        from sqlalchemy.orm import aliased
        from dewey_service.registry_access import owner_clause
        actor = principal()
        data = generic_instance.json_addl
        grant = aliased(generic_instance)
        edge = aliased(generic_instance_lineage)
        rule = grant.json_addl
        email = actor.email.lower()
        domain = email.rpartition("@")[2]
        suffixes = [".".join(domain.split(".")[index:]) for index in range(len(domain.split(".")))]
        recipient = or_(
            and_(rule["recipient_type"].astext == "email", rule["recipient"].astext == email),
            and_(rule["recipient_type"].astext == "domain", or_(
                rule["recipient"].astext == domain,
                and_(rule["include_subdomains"].astext == "true", rule["recipient"].astext.in_(suffixes)),
            )),
        )
        now = datetime.now(timezone.utc)
        recipient_grant = exists(select(literal(1)).select_from(edge).join(grant,
            grant.uid == edge.child_instance_uid).where(
            edge.parent_instance_uid == generic_instance.uid,
            edge.relationship_type == "share_grant", edge.is_deleted.is_(False),
            grant.is_deleted.is_(False), grant.type == "share_grant",
            grant.domain_code == generic_instance.domain_code,
            rule["status"].astext == "active",
            rule["policy_revision"].astext == data["policy_revision"].astext,
            cast(rule["expires_at"].astext, DateTime(timezone=True)) > now, recipient,
        )).correlate(generic_instance)
        manage = literal(True) if actor.admin else owner_clause(data, actor)
        current_recipient = and_(generic_instance.bstatus != "archived", data["status"].astext == "active",
            cast(data["expires_at"].astext, DateTime(timezone=True)) > now,
            ~data["denied_emails"].contains([email]), recipient_grant)
        return self._share_query(session).filter(data["schema_version"].astext == "2", or_(manage, current_recipient))

    def list_registry_shares(self, *, page=1, page_size=25, q="", sort="created_at"):
        from daylily_tapdb import generic_instance
        from sqlalchemy import or_
        self._require_sharing()
        if type(page) is not int or page < 1 or type(page_size) is not int or not 1 <= page_size <= 100:
            raise ValueError("Share page must be positive and page_size must be 1..100")
        if not isinstance(q, str) or len(q) > 200:
            raise ValueError("Share search must contain at most 200 characters")
        columns = {"created_at": generic_instance.created_dt, "modified_at": generic_instance.modified_dt,
            "name": generic_instance.name, "expires_at": generic_instance.json_addl["expires_at"].astext}
        descending = sort.startswith("-") or sort in {"created_at", "modified_at"}
        key = sort.removeprefix("-")
        if key not in columns:
            raise ValueError("Unsupported share sort")
        with self.backend.session_scope(commit=False) as session:
            query = self._authorized_share_index_query(session)
            if q:
                literal_query = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
                query = query.filter(or_(generic_instance.name.ilike(literal_query, escape="\\"),
                    generic_instance.json_addl["purpose"].astext.ilike(literal_query, escape="\\")))
            column = columns[key]
            query = query.order_by(column.desc() if descending else column.asc(), generic_instance.euid)
            rows = query.offset((page - 1) * page_size).limit(page_size + 1).all()
            items = [self._canonical_response(session, share,
                manager=self._registry_share_manager(session, share)) for share in rows[:page_size]]
            return {"items": items, "has_more": len(rows) > page_size, "page": page,
                "page_size": page_size, "incomplete": False}

    def list_shares(self, *, limit=200, target_kind=None, target_euid=None):
        from daylily_tapdb import generic_instance, generic_instance_lineage
        from sqlalchemy import exists, literal, select
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            query = self._authorized_share_index_query(session)
            if target_kind:
                query = query.filter(generic_instance.json_addl["target_kind"].astext == target_kind)
            if target_euid:
                from sqlalchemy.orm import aliased
                member = aliased(generic_instance)
                edge = aliased(generic_instance_lineage)
                query = query.filter(exists(select(literal(1)).select_from(edge).join(member,
                    member.uid == edge.parent_instance_uid).where(
                    edge.child_instance_uid == generic_instance.uid, edge.relationship_type == "has_share",
                    edge.is_deleted.is_(False), member.is_deleted.is_(False), member.euid == target_euid,
                )).correlate(generic_instance))
            rows = query.order_by(generic_instance.created_dt.desc(), generic_instance.euid).limit(max(1, min(int(limit), 2000))).all()
            return [self._canonical_response(session, share, manager=self._registry_share_manager(session, share)) for share in rows]

    def modify_registry_share(self, euid, changes):
        from dewey_service.services.share_policy import normalized_policy, expiry
        self._require_sharing()
        allowed = {"name", "purpose", "grants", "include_patterns", "exclude_patterns", "denied_emails", "delivery_modes", "expires_at", "policy_revision", "allowed_users", "allowed_domains"}
        if set(changes) - allowed or type(changes.get("policy_revision")) is not int:
            raise ValueError("Supported changes and the reviewed policy_revision are required")
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, euid, lock=True)
            if not self._registry_share_manager(session, share): raise HTTPException(403, "Share management permission required")
            data = normalize_instance_payload(share)
            if changes["policy_revision"] != data["policy_revision"]: raise HTTPException(409, "Share policy changed; reload before editing")
            if data["status"] != "active" or expiry(data["expires_at"]) <= datetime.now(timezone.utc):
                raise ValueError("Expired or revoked shares cannot be reactivated")
            members = self._share_members(session, share)
            for member in members: require_record(self.backend, session, member, "share")
            current = self._canonical_response(session, share, manager=True)
            grant_data = [{k: v for k, v in g.items() if k in {"recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at", "target_euids"}} for g in current["grants"] if g["status"] == "active"]
            merged = {**data, "grants": grant_data, **changes}
            if "grants" not in changes and ({"allowed_users", "allowed_domains"} & set(changes)):
                merged.pop("grants")
            deadline = self._normalize_share_expiry(merged["expires_at"])
            policy = normalized_policy(merged, share_expiry=deadline, member_euids=[m.euid for m in members])
            grants = policy.pop("grants")
            revision = data["policy_revision"] + 1
            for grant in self._share_grants(session, share):
                if normalize_instance_payload(grant).get("status") == "active":
                    self.backend.update_instance_json(session, grant, {"status": "superseded"})
            self._write_grants(session, share, grants, members, revision)
            self.backend.update_instance_json(session, share, {**policy, "policy_revision": revision,
                "expires_at": deadline, "name": merged.get("name"), "purpose": merged.get("purpose")})
            self._event(session, share, event_type="policy_updated", decision="change", details={"policy_revision": revision})
            session.refresh(share)
            return self._canonical_response(session, share, manager=True)

    def revoke_share_grant(self, share_euid, grant_euid, *, policy_revision, reason=None):
        self._require_sharing()
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid, lock=True)
            if not self._registry_share_manager(session, share): raise HTTPException(403, "Share management permission required")
            data = normalize_instance_payload(share)
            if data["policy_revision"] != policy_revision: raise HTTPException(409, "Share policy changed; reload")
            grant = next((g for g in self._share_grants(session, share) if g.euid == grant_euid), None)
            if grant is None: raise DeweyNotFoundError("Grant not found")
            revision = data["policy_revision"] + 1
            self.backend.update_instance_json(session, grant, {"status": "revoked", "revoked_at": utc_now_iso()})
            for other in self._share_grants(session, share):
                if other.euid != grant.euid and normalize_instance_payload(other).get("status") == "active":
                    self.backend.update_instance_json(session, other, {"policy_revision": revision})
            self.backend.update_instance_json(session, share, {"policy_revision": revision})
            self._event(session, share, event_type="recipient_revoked", decision="revoke", grant=grant,
                details={"reason": reason, "policy_revision": revision})
            session.refresh(share)
            return self._canonical_response(session, share, manager=True)

    def revoke_share(self, share_euid, *, revoked_by=None, reason=None, policy_revision=None):
        self._require_sharing()
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid, lock=True)
            if not self._registry_share_manager(session, share): raise HTTPException(403, "Share management permission required")
            data = normalize_instance_payload(share)
            if policy_revision is None or data["policy_revision"] != policy_revision:
                raise HTTPException(409, "The current policy_revision is required")
            self.backend.update_instance_json(session, share, {"status": "revoked", "policy_revision": policy_revision + 1,
                "revoked_at": utc_now_iso(), "revoked_by": principal().subject, "revocation_reason": reason})
            self._event(session, share, event_type="revoked", decision="revoke", details={"reason": reason, "policy_revision": policy_revision + 1})
            session.refresh(share)
            return self._canonical_response(session, share, manager=True)

    def list_share_audit(self, share_euid, *, limit=200, continuation_token=None):
        from daylily_tapdb import generic_instance, generic_instance_lineage
        from sqlalchemy import or_, and_
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            share = self._canonical_share(session, share_euid)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required")
            query = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.parent_instance_uid == share.uid,
                generic_instance_lineage.relationship_type == "share_event",
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
                generic_instance.type == "share_event")
            if continuation_token:
                cursor = query.filter(generic_instance.euid == continuation_token).first()
                if cursor is None: raise ValueError("Unknown audit continuation token")
                query = query.filter(or_(generic_instance.created_dt > cursor.created_dt,
                    and_(generic_instance.created_dt == cursor.created_dt, generic_instance.euid > cursor.euid)))
            limit = max(1, min(int(limit), 200))
            rows = query.order_by(generic_instance.created_dt, generic_instance.euid).limit(limit + 1).all()
            more = len(rows) > limit
            page = [{"euid": e.euid, **normalize_instance_payload(e)} for e in rows[:limit]]
            return {"share_euid": share.euid, "items": page,
                "continuation_token": page[-1]["euid"] if more and page else None, "incomplete": more}

    def _listing_cursor(self, session, share, continuation_token, context):
        from dewey_service.registry_access import OPERATION_TEMPLATE
        if not continuation_token:
            return {"member_index": 0, "s3_token": None}
        row = self.backend.find_by_euid(session, template_code=OPERATION_TEMPLATE, euid=continuation_token)
        if row is None:
            raise ValueError("Unknown continuation token")
        data = normalize_instance_payload(row)
        if data.get("operation") != "share_listing_cursor" or data.get("actor") != principal().subject or data.get("context") != context:
            raise HTTPException(409, "Listing cursor differs from current viewer, policy or selection")
        from dewey_service.services.share_policy import expiry
        if expiry(data["expires_at"]) <= datetime.now(timezone.utc):
            raise HTTPException(410, "Listing cursor expired")
        parents = self.backend.list_parents(session, child=row, relationship_type="share_listing_cursor")
        if not any(p.euid == share.euid for p in parents):
            # Parent visibility is independent of grant authority; check the exact native lineage.
            from daylily_tapdb import generic_instance_lineage
            if not session.query(generic_instance_lineage.uid).filter_by(parent_instance_uid=share.uid,
                    child_instance_uid=row.uid, relationship_type="share_listing_cursor", is_deleted=False).first():
                raise ValueError("Cursor does not belong to this share")
        return data["position"]

    def _save_listing_cursor(self, session, share, context, position):
        from dewey_service.registry_access import OPERATION_TEMPLATE
        row = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name="Share listing cursor",
            json_addl={"operation": "share_listing_cursor", "actor": principal().subject, "context": context,
                "position": position, "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()})
        self.backend.create_lineage(session, parent=share, child=row, relationship_type="share_listing_cursor")
        return row.euid

    def list_share_contents(self, share_euid, *, target_euid=None, prefix="", limit=200, continuation_token=None):
        from dewey_service.storage import storage_authorization_context
        self.get_share(share_euid)
        limit = max(1, min(int(limit), 200))
        if not isinstance(prefix, str) or "\x00" in prefix:
            raise ValueError("prefix must be literal root-relative S3 text")
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid)
            data = normalize_instance_payload(share)
            members = sorted(self._share_members(session, share), key=lambda m: m.euid)
            if target_euid:
                members = [m for m in members if m.euid == target_euid]
                if not members: raise HTTPException(403, "Target is outside this share")
            context = self._fingerprint({"share": share.euid, "revision": data["policy_revision"],
                "target": target_euid, "prefix": prefix, "limit": limit})
            position = self._listing_cursor(session, share, continuation_token, context)
            index, s3_token = position["member_index"], position["s3_token"]
            items = []
            scanned = 0
            while index < len(members) and len(items) < limit and scanned < 1000:
                member = self._artifact_member_from_instance(members[index])
                if member["target_kind"] == "artifact_object":
                    candidates = [{"key": member["key"], "size": member.get("size"), "relative_key": ""}]
                    next_s3 = None
                else:
                    root = member["key"] + prefix
                    def scope(bucket, key, action):
                        if bucket != member["bucket"] or key != root or action != "metadata":
                            raise HTTPException(403, "Storage request exceeds share listing scope")
                    with storage_authorization_context(scope):
                        page = self._require_storage().list_share_candidates(bucket=member["bucket"], prefix=root,
                            limit=min(limit - len(items), 1000 - scanned), continuation_token=s3_token,
                            request_payer=self._request_payer_for_bucket(member["bucket"]))
                    candidates = [{"key": obj.key, "size": obj.size, "relative_key": obj.key[len(member["key"]):]} for obj in page["objects"]]
                    next_s3 = page["next_continuation_token"]
                for candidate in candidates:
                    scanned += 1
                    if prefix and member["target_kind"] == "artifact_object" and not member["key"].rsplit("/", 1)[-1].startswith(prefix):
                        continue
                    try:
                        receipt = self._evaluate_share(session, share, members[index].euid, candidate["relative_key"], "metadata")
                    except HTTPException as exc:
                        if exc.status_code in {403, 410}: continue
                        raise
                    items.append({"target_euid": members[index].euid, "kind": "object",
                        "name": candidate["relative_key"] or receipt["filename"], "relative_key": candidate["relative_key"],
                        "size": candidate["size"], "grant_euid": receipt["grant_euid"]})
                if next_s3:
                    s3_token = next_s3
                else:
                    index += 1
                    s3_token = None
            more = index < len(members)
            token = self._save_listing_cursor(session, share, context, {"member_index": index, "s3_token": s3_token}) if more else None
            self._event(session, share, event_type="contents", decision="allow", details={"policy_revision": data["policy_revision"]})
            return {"share_euid": share.euid, "items": items, "continuation_token": token, "incomplete": more}

    def preview_share_selection(self, euid, payload):
        from dewey_service.services.share_policy import normalized_policy, selected, expiry
        from dewey_service.storage import storage_authorization_context
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            target = self._registry_record(session, euid, action="share")
            kind = "artifact_set" if target.type == "artifact_set" else "artifact_" + normalize_instance_payload(target)["storage_kind"]
            members = self._expand_share_targets(session, target_kind=kind, target_euid=euid)
            deadline = self._normalize_share_expiry(payload.get("expires_at"))
            policy = normalized_policy(payload, share_expiry=deadline, member_euids=[m["artifact_euid"] for m in members])
            items = []
            incomplete = False
            for member in members:
                self._registry_record(session, member["artifact_euid"], action="share")
                if member["target_kind"] == "artifact_object":
                    candidates = [("", member["key"].rsplit("/", 1)[-1], member.get("size"))]
                else:
                    # Preview uses the manager's independent storage authorization.
                    page = self._require_storage().list_share_candidates(bucket=member["bucket"], prefix=member["key"], limit=200)
                    candidates = [(o.key[len(member["key"]):], o.key[len(member["key"]):], o.size) for o in page["objects"]]
                    incomplete = incomplete or bool(page["next_continuation_token"])
                for relative, path, size in candidates:
                    if not selected(path, policy["include_patterns"], policy["exclude_patterns"]): continue
                    matching = [g for g in policy["grants"] if member["artifact_euid"] in g["target_euids"] and
                        expiry(g["expires_at"]) > datetime.now(timezone.utc) and selected(path, g["include_patterns"], g["exclude_patterns"])]
                    if not matching: continue
                    try: self._protected_share_path(session, member["bucket"], member["key"] + relative if relative else member["key"], action="metadata")
                    except HTTPException as exc:
                        if exc.status_code == 403: continue
                        raise
                    items.append({"target_euid": member["artifact_euid"], "kind": "object", "name": path, "relative_key": relative, "size": size})
                    if len(items) >= 200:
                        incomplete = True
                        break
                if len(items) >= 200: break
            return {"items": items, "continuation_token": None, "incomplete": incomplete}

    def create_share_access_package(self, share_euid, *, delivery_mode="gateway", actor_email=None,
            actor_groups=None, ip=None, user_agent=None, signed_ttl_seconds=None):
        mode = {"dewey_html_browser": "gateway", "presigned_s3": "presigned", "presigned_s3_manifest": "presigned"}.get(delivery_mode, delivery_mode)
        if mode not in {"gateway", "presigned"}: raise ValueError("Unsupported delivery mode")
        page = self.list_share_contents(share_euid, limit=200)
        if page["incomplete"]:
            raise ValueError("Access package exceeds one bounded page; use share contents and exact-object issuance")
        if mode == "gateway":
            from urllib.parse import quote
            return {"share_euid": share_euid, "delivery_mode": "gateway", "browser_path": f"/shares/{share_euid}",
                "manifest": [{**item, "web_path": f"/shares/{share_euid}/files/{item['target_euid']}?relative_key={quote(item['relative_key'], safe='')}"} for item in page["items"]]}
        return {"share_euid": share_euid, "delivery_mode": "presigned", "manifest": [
            self.presign_share_object(share_euid, item["target_euid"], relative_key=item["relative_key"], ttl_seconds=signed_ttl_seconds) for item in page["items"]]}

    def presign_share_object(self, share_euid, target_euid, *, relative_key="", ttl_seconds=None):
        from dewey_service.storage import storage_authorization_context
        from dewey_service.services.share_policy import expiry
        receipt = self.authorize_share_object(share_euid, target_euid, relative_key, action="presign")
        ttl = 900 if ttl_seconds is None else int(ttl_seconds)
        if not 1 <= ttl <= 3600: raise ValueError("Presign lifetime must be 1..3600 seconds")
        ttl = min(ttl, int((expiry(receipt["expires_at"]) - datetime.now(timezone.utc)).total_seconds()))
        if ttl < 1: raise HTTPException(410, "Share grant expired")
        def scope(bucket, key, action):
            if (bucket, key) != (receipt["bucket"], receipt["key"]) or action not in {"metadata", "download"}:
                raise HTTPException(403, "Storage request exceeds authorized object")
        with storage_authorization_context(scope):
            url = self._require_storage().generate_presigned_get_url(bucket=receipt["bucket"], key=receipt["key"],
                version_id=receipt["version_id"], expires_in=ttl,
                request_payer=self._request_payer_for_bucket(receipt["bucket"]))
        from urllib.parse import parse_qs, urlsplit
        signed_fields = parse_qs(urlsplit(url).query)
        try:
            signed_at = datetime.strptime(signed_fields["X-Amz-Date"][0], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            signed_ttl = int(signed_fields["X-Amz-Expires"][0])
            signed_expiry = signed_at + timedelta(seconds=signed_ttl)
        except (KeyError, ValueError, IndexError) as exc:
            raise HTTPException(503, "S3 signer did not return the required explicit expiration") from exc
        if signed_ttl != ttl or signed_expiry > expiry(receipt["expires_at"]) or signed_expiry <= datetime.now(timezone.utc):
            raise HTTPException(410, "S3 signing could not stay within the current grant deadline")
        event = self.append_share_event(share_euid, event_type="raw_s3_presign_issued", decision="allow",
            grant_euid=receipt["grant_euid"], target_euid=target_euid,
            details={"expires_in": ttl, "expires_at": signed_expiry.isoformat(), "relative_key": relative_key,
                "key": receipt["key"], "version_id": receipt["version_id"], "bearer_url_forwardable": True,
                "policy_revision": receipt["policy_revision"], "outcome": "credential_issued"})
        return {"share_euid": share_euid, "target_euid": target_euid, "relative_key": relative_key,
            "url": url, "signed_url": url, "expires_in": ttl, "expires_at": signed_expiry.isoformat(),
            "receipt_euid": event, "delivery": "presigned_s3", "bearer_url_forwardable": True,
            "authentication_required_for_consumption": False, "download_completion_observed": False}

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
        self._require_sharing()
        if not principal().writable:
            raise HTTPException(403, "Share root creation requires write access")
        modes = _clean_list(allowed_delivery_modes) or ["gateway"]
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
        self._require_sharing()
        if not principal().writable:
            raise HTTPException(403, "Share root management requires write access")
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
        grants: list[dict[str, Any]] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        denied_emails: list[str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        self._require_sharing()
        with self.backend.session_scope(commit=False) as session:
            root = self.backend.find_by_euid(
                session,
                template_code=SHARE_ROOT_TEMPLATE,
                euid=str(share_root_euid or "").strip(),
            )
            if root is None:
                raise DeweyNotFoundError(f"Share root not found: {share_root_euid}")
            root_payload = normalize_instance_payload(root)
            requested_modes = delivery_modes if delivery_modes is not None else ["gateway"]
            if set(requested_modes) - set(root_payload.get("allowed_delivery_modes", [])):
                raise ValueError("Delivery mode exceeds this share root permission")
            root_bucket = str(root_payload.get("bucket") or "")
            root_prefix = str(root_payload.get("prefix") or "")
            members = self._expand_share_targets(
                session,
                target_kind="mixed_set",
                targets=targets,
            )
            for member in members:
                if str(member["bucket"]) != root_bucket or not str(member["key"]).startswith(
                    root_prefix
                ):
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
            grants=grants, include_patterns=include_patterns,
            exclude_patterns=exclude_patterns, denied_emails=denied_emails,
        )

    def _normalize_expiry(self, expires_at: str | None, ttl_seconds: int | None = None) -> str:
        clean = str(expires_at or "").strip()
        if clean:
            try:
                parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("expires_at must be ISO8601") from exc
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("expires_at must include a timezone")
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        ttl_value = (
            self.default_share_ttl_seconds if ttl_seconds is None else max(60, int(ttl_seconds))
        )
        auto = datetime.now(timezone.utc) + timedelta(seconds=ttl_value)
        return auto.isoformat().replace("+00:00", "Z")
