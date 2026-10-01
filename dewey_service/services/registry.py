"""EUID-first registry operations shared by HTTP, browser, and CLI clients."""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import HTTPException
from sqlalchemy import String, and_, cast, exists, func, literal, or_, select, text
from sqlalchemy.dialects.postgresql import JSONB, JSONPATH
from sqlalchemy.orm import aliased

from dewey_service.registry_access import (
    POLICY_TEMPLATE, TOKEN_TEMPLATE, OPERATION_TEMPLATE, Principal, default_policy, maintenance_mode,
    principal, record_clause, require_record, validate_policy, visibility_clause,
)
from dewey_service.services.base import DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE, ARTIFACT_SET_TEMPLATE, SHARE_TEMPLATE,
    normalize_instance_payload, utc_now_iso,
)


class RegistryServiceMixin:
    def _registry_event(self, session, record, action):
        receipt = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name=action,
            json_addl={"operation": action, "actor": principal().subject, "created_at": utc_now_iso(), "status": "complete"})
        self.backend.create_lineage(session, parent=record, child=receipt, relationship_type="has_storage_operation")

    def registry_defaults(self):
        with self.backend.session_scope(commit=False) as session:
            row = self.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE,
                field="policy_kind", value="service_defaults")
            if row is None:
                raise HTTPException(503, "Run dewey db initialize-performance-settings with the explicit service configuration")
            data = normalize_instance_payload(row)
            keys = ("share_lifetime_days", "delivery_lifetime_seconds", "listing_cache_ttl_seconds")
            if any(key not in data for key in keys):
                raise HTTPException(503, "Dewey performance settings have not been explicitly initialized")
            if type(data["listing_cache_ttl_seconds"]) is not int or not 0 <= data["listing_cache_ttl_seconds"] <= 300:
                raise HTTPException(503, "Invalid persisted listing cache TTL")
            return {key: data[key] for key in keys}

    def update_registry_defaults(self, changes):
        if not principal().admin:
            raise HTTPException(403, "Admin access required")
        if not changes or set(changes) - {"share_lifetime_days", "delivery_lifetime_seconds", "listing_cache_ttl_seconds"}:
            raise ValueError("Only share lifetime, delivery lifetime and listing cache TTL may be changed")
        with self.backend.session_scope(commit=True) as session:
            self.backend.lock_external_key(session, operation="registry.defaults", key="service_defaults")
            row = self.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE,
                field="policy_kind", value="service_defaults", for_update=True)
            if row is None or "listing_cache_ttl_seconds" not in normalize_instance_payload(row):
                raise HTTPException(503, "Dewey performance settings have not been explicitly initialized")
            data = {**normalize_instance_payload(row), **changes}
            if type(data["share_lifetime_days"]) is not int or not 1 <= data["share_lifetime_days"] <= self.share_max_lifetime_days:
                raise ValueError("Share lifetime exceeds the configured range")
            if type(data["delivery_lifetime_seconds"]) is not int or not 1 <= data["delivery_lifetime_seconds"] <= 3600:
                raise ValueError("Delivery lifetime must be 1..3600 seconds")
            if type(data["listing_cache_ttl_seconds"]) is not int or not 0 <= data["listing_cache_ttl_seconds"] <= 300:
                raise ValueError("Listing cache TTL must be 0..300 seconds; zero disables caching")
            self.backend.update_instance_json(session, row, changes)
            self._registry_event(session, row, "registry.defaults.updated")
            result = {key: data[key] for key in ("share_lifetime_days", "delivery_lifetime_seconds", "listing_cache_ttl_seconds")}
        if self.storage is not None:
            self.storage.listing_cache.invalidate()
        return result

    def register_registry(self, data: dict[str, Any], *, idempotency_key: str):
        """Register one explicit object, prefix, or set; never discover members."""
        from urllib.parse import urlsplit
        from dewey_service.services.registry_storage import parse_s3_uri
        actor = principal()
        if not actor.writable:
            raise HTTPException(403, "Registration requires write access")
        allowed = {"kind", "uri", "name", "description", "metadata", "member_euids", "producer_system", "version_id", "artifact_type"}
        if set(data) - allowed:
            raise ValueError("Unknown registration fields: " + ", ".join(sorted(set(data) - allowed)))
        kind = data.get("kind")
        if kind not in {"object", "prefix", "set"}:
            raise ValueError("kind must explicitly be object, prefix, or set")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        name = str(data.get("name") or "").strip()
        fingerprint = self._fingerprint(data)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(session, operation="registry.register", idempotency_key=idempotency_key, fingerprint=fingerprint)
            if replay is not None:
                return replay.status_code, replay.response
            if kind == "set":
                if data.get("uri") or not name:
                    raise ValueError("A set requires a name and explicitly selected member EUIDs")
                euids = data.get("member_euids", [])
                if not isinstance(euids, list) or any(not isinstance(euid, str) for euid in euids):
                    raise ValueError("member_euids must be a list of Object or Prefix EUIDs")
                members = [self._registry_record(session, euid) for euid in dict.fromkeys(euids)]
                if any(member.type != "artifact" for member in members):
                    raise ValueError("Sets can contain objects and prefixes; nested sets are not supported")
                record = self.backend.create_instance(session, template_code=ARTIFACT_SET_TEMPLATE, name=name,
                    json_addl={"artifact_set_type": "artifact_set", "label": name, "description": data.get("description"),
                        "metadata": metadata, "created_at": utc_now_iso()})
                for member in members:
                    self.backend.create_lineage(session, parent=record, child=member, relationship_type="artifact_set_member")
                code = 201
            else:
                if data.get("member_euids"):
                    raise ValueError("Only sets accept member_euids")
                uri = data.get("uri")
                if not isinstance(uri, str):
                    raise ValueError("An explicit S3 or HTTP(S) URI is required")
                if uri.startswith("s3://"):
                    bucket, key, uri = parse_s3_uri(uri, prefix=kind == "prefix")
                    if kind == "object" and not key:
                        raise ValueError("An object requires an exact S3 key")
                    backend = "s3"
                    self.require_storage_access(bucket, key, action="metadata", session=session)
                else:
                    parsed = urlsplit(uri)
                    if kind != "object" or parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
                        raise ValueError("URL references require an HTTP(S) object URL without embedded credentials")
                    backend, bucket, key = parsed.scheme, parsed.netloc, parsed.path + ("?" + parsed.query if parsed.query else "")
                payload = {"storage_kind": kind, "node_kind": "folder" if kind == "prefix" else "file",
                    "is_terminal": kind == "object", "artifact_type": data.get("artifact_type") or kind,
                    "storage_backend": backend, "bucket": bucket, "key": key, "storage_uri": uri,
                    "source_uri": uri, "version_id": data.get("version_id"), "metadata": metadata,
                    "description": data.get("description"), "original_filename": name or key.rstrip("/").rpartition("/")[2] or bucket,
                    "producer_system": data.get("producer_system") or "dewey", "checksums": {},
                    "storage_status": "registered", "import_mode": "register"}
                payload["artifact_identity_key"] = self._artifact_identity_key(payload)
                lock_key = int.from_bytes(sha256((uri + "\0" + str(data.get("version_id") or "")).encode()).digest()[:8], "big", signed=True)
                session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
                existing = self._registry_query(session, scopes=("artifact",), authorize=False).filter(
                    generic_instance.json_addl["storage_uri"].astext == uri,
                    generic_instance.json_addl["storage_kind"].astext == kind,
                    func.coalesce(generic_instance.json_addl["version_id"].astext, "") == str(data.get("version_id") or ""),
                ).order_by(generic_instance.created_dt, generic_instance.euid).all()
                for match in existing:
                    require_record(self.backend, session, match, "metadata")
                if existing:
                    record, code = existing[0], 200
                else:
                    code, result = self._upsert_artifact_record(session, payload=payload, created_at=utc_now_iso())
                    record = self._registry_record(session, result["artifact_euid"])
            body = self._registry_payload(session, record)
            self._store_idempotency(session, operation="registry.register", idempotency_key=idempotency_key,
                fingerprint=fingerprint, status_code=code, response=body)
            return code, body

    def _registry_query(self, session, *, scopes=("artifact", "artifact_set"), authorize=True):
        codes = {"artifact": ARTIFACT_TEMPLATE, "artifact_set": ARTIFACT_SET_TEMPLATE, "share": SHARE_TEMPLATE}
        if not scopes or set(scopes) - set(codes):
            raise ValueError("Invalid registry scopes")
        templates = [self.backend.templates.get_template(session, codes[s], domain_code=self.backend.domain_code) for s in scopes]
        if any(t is None for t in templates):
            raise RuntimeError("Required registry templates are missing")
        query = session.query(generic_instance).filter(
            generic_instance.template_uid.in_([t.uid for t in templates]),
            generic_instance.type.in_(scopes),
            generic_instance.is_deleted.is_(False),
        )
        return query.filter(generic_instance.bstatus != "archived", visibility_clause(session, generic_instance, types=scopes)) if authorize else query

    def _registry_record(self, session, euid: str, *, action="metadata", lock=False):
        query = self._registry_query(session, authorize=False).filter(generic_instance.euid == euid,
            generic_instance.bstatus != "archived", record_clause(session, generic_instance, action))
        record = (query.with_for_update() if lock else query).first()
        if record is None:
            raise DeweyNotFoundError("Dewey record not found or not visible")
        return record

    def _registry_policy(self, session, record):
        rows = self.backend.list_children(session, parent=record, relationship_type="registry_policy")
        if len(rows) != 1:
            raise RuntimeError(f"Record {record.euid} requires exactly one initialized registry policy")
        return rows[0]

    def _registry_payload(self, session, record, *, details=True, summary=False):
        if summary:
            data = normalize_instance_payload(record)
            value = {key: data[key] for key in ("storage_kind", "storage_uri", "storage_backend", "key",
                "size", "content_type", "artifact_type", "producer_system", "created_at", "original_filename", "label") if key in data}
            kind = "set" if record.type == "artifact_set" else data["storage_kind"]
            value["created_at"] = data.get("created_at") or record.created_dt.isoformat()
        elif record.type == "artifact":
            value = self._artifact_response(record)
            kind = value["storage_kind"]
        elif record.type == "artifact_set":
            value = self._artifact_set_response(session, record)
            kind = "set"
        elif record.type == "share":
            value = self._share_response(record)
            kind = "share"
        else:
            raise ValueError("Unsupported registry record")
        value.update({
            "euid": record.euid, "kind": kind, "record_type": record.type,
            "source_kind": f"dewey.{record.type}", "name": record.name,
            "modified_at": record.modified_dt.isoformat() if record.modified_dt else None,
            "status": record.bstatus if record.type != "share" else value["status"],
            "dewey_path": f"/records/{record.euid}",
            "description": normalize_instance_payload(record).get("description"),
        })
        if details and record.type in {"artifact", "artifact_set"}:
            actions = ("metadata", "download", "edit", "share")
            allowed = session.query(*(record_clause(session, generic_instance, action) for action in actions)).select_from(
                generic_instance).filter(generic_instance.uid == record.uid).one()
            capabilities = dict(zip(actions, map(bool, allowed)))
            value["capabilities"] = capabilities
            policy = normalize_instance_payload(self._registry_policy(session, record))
            value["owner"] = policy.get("owner_email") or policy["owner_subject"]
            actor = principal()
            capabilities["owner"] = actor.writable and (actor.admin or policy["owner_subject"] == actor.subject or bool(actor.email and policy.get("owner_email") == actor.email))
            if capabilities["edit"] or capabilities["share"]:
                value["permissions"] = {k: policy[k] for k in ("metadata", "download", "edit_users", "share_users")}
            value["links"] = {
                "self": f"/api/v1/records/{record.euid}",
                "contents": f"/api/v1/records/{record.euid}/contents",
                "access": f"/api/v1/records/{record.euid}/access",
                "share": f"/api/v1/records/{record.euid}/shares",
                "web": value["dewey_path"],
            }
            if not summary:
                operations = session.query(generic_instance).join(generic_instance_lineage,
                    generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                    generic_instance_lineage.parent_instance_uid == record.uid,
                    generic_instance_lineage.relationship_type == "has_storage_operation",
                    generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
                ).order_by(generic_instance.created_dt.desc()).limit(50).all()
                value["activity"] = [{"euid": op.euid, **{key: normalize_instance_payload(op).get(key)
                    for key in ("operation", "created_at", "status")}} for op in operations]
        return value

    def resolve_registry(self, euid: str, *, projection="full"):
        if projection not in {"full", "summary"}:
            raise ValueError("Record projection must be full or summary")
        with self.backend.session_scope(commit=False) as session:
            return self._registry_payload(session, self._registry_record(session, euid), summary=projection == "summary")

    def registry_section(self, euid, section, *, page=1, limit=25):
        if section not in {"metadata", "activity", "members"}:
            raise ValueError("Unknown record section")
        with self.backend.session_scope(commit=False) as session:
            record = self._registry_record(session, euid)
            if section == "metadata":
                data = normalize_instance_payload(record)
                return {"euid": euid, "metadata": data.get("metadata", {})}
            relation = "artifact_set_member" if section == "members" else "has_storage_operation"
            if section == "members" and record.type != "artifact_set":
                raise ValueError("Only sets have members")
            query = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.parent_instance_uid == record.uid,
                generic_instance_lineage.relationship_type == relation,
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False))
            if section == "members":
                query = query.filter(generic_instance.type == "artifact",
                    record_clause(session, generic_instance))
            rows = query.distinct().order_by(generic_instance.created_dt.desc(), generic_instance.euid).offset(
                (page - 1) * limit).limit(limit + 1).all()
            more = len(rows) > limit
            if section == "members":
                items = self._registry_summary_items(session, rows[:limit])
            else:
                items = [{"euid": op.euid, **{key: normalize_instance_payload(op).get(key)
                    for key in ("operation", "created_at", "status")}} for op in rows[:limit]]
            return {"items": items, "page": page, "has_more": more}

    def _registry_summary_items(self, session, records):
        """Project the visible page without hydrating set members or external detail."""
        set_uids = [record.uid for record in records if record.type == "artifact_set"]
        member_counts = dict.fromkeys(set_uids, 0)
        if set_uids:
            counts = session.query(
                generic_instance_lineage.parent_instance_uid,
                func.count(func.distinct(generic_instance.uid)),
            ).select_from(generic_instance_lineage).join(
                generic_instance,
                generic_instance_lineage.child_instance_uid == generic_instance.uid,
            ).filter(
                generic_instance_lineage.parent_instance_uid.in_(set_uids),
                generic_instance.type == "artifact",
                generic_instance_lineage.relationship_type == "artifact_set_member",
                generic_instance_lineage.is_deleted.is_(False),
                generic_instance.is_deleted.is_(False),
                visibility_clause(session, generic_instance, types=("artifact",)),
            ).group_by(generic_instance_lineage.parent_instance_uid).all()
            member_counts.update(counts)
        fields = (
            "euid", "kind", "record_type", "source_kind", "name", "label",
            "original_filename", "producer_system", "created_at", "modified_at",
            "status", "dewey_path", "member_count", "audience", "allowed_users",
            "allowed_domains", "allowed_groups", "expires_at", "owner_email",
            "last_accessed_at",
        )
        items = []
        for record in records:
            payload = normalize_instance_payload(record)
            created_at = payload.get("created_at")
            if not created_at and record.created_dt is not None:
                created_at = record.created_dt.isoformat()
            if not isinstance(created_at, str) or not created_at.strip():
                raise RuntimeError(f"Record {record.euid} has no recorded creation timestamp")
            if record.type == "artifact_set":
                value = {
                    "euid": record.euid, "kind": "set", "record_type": record.type,
                    "source_kind": "dewey.artifact_set", "name": record.name,
                    "label": payload.get("label"), "status": record.bstatus,
                    "created_at": created_at,
                    "modified_at": record.modified_dt.isoformat() if record.modified_dt else None,
                    "dewey_path": f"/records/{record.euid}",
                    "member_count": member_counts[record.uid],
                }
            else:
                value = self._registry_payload(session, record, details=False)
                value["created_at"] = created_at
            items.append({key: value[key] for key in fields if key in value})
        return items

    def share_registry(self, euid: str, data: dict[str, Any], *, idempotency_key: str):
        from dewey_service.settings import get_settings
        allowed = {"name", "purpose", "audience", "allowed_users", "allowed_domains", "expires_at", "lifetime_days"}
        if set(data) - allowed:
            raise ValueError("Unknown share fields")
        audience = data.get("audience", "private")
        policy = validate_policy({"metadata": {"scope": audience,
            "users": data.get("allowed_users", []), "domains": data.get("allowed_domains", [])}})["metadata"]
        defaults = self.registry_defaults()
        days = int(data.get("lifetime_days", defaults["share_lifetime_days"]))
        if not 1 <= days <= self.share_max_lifetime_days:
            raise ValueError("Share lifetime exceeds the configured range")
        expiry = self._normalize_share_expiry(data.get("expires_at") or (datetime.now(timezone.utc) + timedelta(days=days)).isoformat())
        fingerprint = self._fingerprint({"euid": euid, **data})
        with self.backend.session_scope(commit=True) as session:
            target = self._registry_record(session, euid, action="share")
            replay = self._idempotency_replay(session, operation="registry.share", idempotency_key=idempotency_key, fingerprint=fingerprint)
            if replay is not None:
                return replay.status_code, replay.response
            targets = [target]
            if target.type == "artifact_set":
                # Share only members the issuer can themselves share. Membership alone grants nothing.
                members = session.query(generic_instance).join(generic_instance_lineage,
                    generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                    generic_instance_lineage.parent_instance_uid == target.uid,
                    generic_instance_lineage.relationship_type == "artifact_set_member",
                    generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False)).all()
                for member in members:
                    require_record(self.backend, session, member, "share")
                targets.extend(members)
            kind = "artifact_set" if target.type == "artifact_set" else "artifact_" + normalize_instance_payload(target)["storage_kind"]
            actor = principal()
            share = self.backend.create_instance(session, template_code=SHARE_TEMPLATE, name=data.get("name") or target.name,
                json_addl={"target_kind": kind, "target_euid": euid, "name": data.get("name") or target.name,
                    "purpose": data.get("purpose"), "owner_subject": actor.subject, "owner_email": actor.email,
                    "audience": audience, "allowed_users": policy["users"], "allowed_domains": policy["domains"],
                    "allowed_groups": [], "expires_at": expiry, "status": "active", "starts_at": utc_now_iso(),
                    "created_at": utc_now_iso(), "delivery_modes": ["dewey_html_browser", "presigned_s3_manifest"],
                    "default_signed_ttl_seconds": defaults["delivery_lifetime_seconds"],
                    "member_count": len(targets) - 1 if kind == "artifact_set" else 1, "audit_events": []})
            for item in targets:
                self.backend.create_lineage(session, parent=item, child=share, relationship_type="has_share")
            body = {**self._share_response(share), "euid": share.euid, "web_path": f"/shares/{share.euid}", "audience": audience}
            self._store_idempotency(session, operation="registry.share", idempotency_key=idempotency_key,
                fingerprint=fingerprint, status_code=201, response=body)
            return 201, body

    def registry_share_detail(self, euid: str):
        with self.backend.session_scope(commit=False) as session:
            share = self.backend.find_by_euid(session, template_code=SHARE_TEMPLATE, euid=euid)
            if share is None:
                raise DeweyNotFoundError("Share not found or not visible")
            data = normalize_instance_payload(share)
            actor = principal()
            manager = self._registry_share_manager(session, share)
            value = self._share_response(share)
            if not manager:
                for field in ("allowed_users", "allowed_domains", "allowed_groups", "last_accessed_by"):
                    value.pop(field, None)
            value.update(euid=euid, audience=data.get("audience", "recipients"), can_manage=manager,
                web_path=f"/shares/{euid}", delivery_window_seconds=3600,
                default_delivery_seconds=self.registry_defaults()["delivery_lifetime_seconds"],
                live_prefix=data.get("target_kind") == "artifact_prefix")
            if manager:
                value["activity"] = data.get("audit_events", [])
                operations = self.backend.list_children(session, parent=share, relationship_type="has_storage_operation")
                value["activity"] = value["activity"] + [{"euid": op.euid,
                    **{key: normalize_instance_payload(op).get(key) for key in ("operation", "actor", "created_at", "expires_in", "status")}}
                    for op in operations]
            return value

    def _registry_share_manager(self, session, share):
        actor = principal()
        data = normalize_instance_payload(share)
        if actor.admin or data.get("owner_subject") == actor.subject or actor.email and data.get("owner_email") == actor.email:
            return True
        return bool(session.query(generic_instance.uid).join(generic_instance_lineage,
            generic_instance_lineage.parent_instance_uid == generic_instance.uid).filter(
            generic_instance_lineage.child_instance_uid == share.uid,
            generic_instance_lineage.relationship_type == "has_share", generic_instance_lineage.is_deleted.is_(False),
            generic_instance.is_deleted.is_(False), record_clause(session, generic_instance, "share")).first())

    def modify_registry_share(self, euid: str, changes: dict[str, Any]):
        if not changes or set(changes) - {"name", "purpose", "audience", "allowed_users", "allowed_domains", "expires_at"}:
            raise ValueError("Unsupported share changes")
        with self.backend.session_scope(commit=True) as session:
            share = self.backend.find_by_euid(session, template_code=SHARE_TEMPLATE, euid=euid, for_update=True)
            if share is None:
                raise DeweyNotFoundError("Share not found")
            data = normalize_instance_payload(share)
            actor = principal()
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share owner or admin access is required")
            if data["status"] != "active" or datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                raise ValueError("Revoked and expired shares cannot be reactivated")
            targets = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.parent_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.child_instance_uid == share.uid,
                generic_instance_lineage.relationship_type == "has_share", generic_instance_lineage.is_deleted.is_(False),
                generic_instance.is_deleted.is_(False)).all()
            for target in targets:
                require_record(self.backend, session, target, "share")
            merged = {**data, **changes}
            audience = validate_policy({"metadata": {"scope": merged.get("audience", "recipients"),
                "users": merged.get("allowed_users", []), "domains": merged.get("allowed_domains", [])}})["metadata"]
            updates = {**changes, "allowed_users": audience["users"], "allowed_domains": audience["domains"]}
            if "expires_at" in changes:
                updates["expires_at"] = self._normalize_share_expiry(changes["expires_at"])
            self.backend.update_instance_json(session, share, updates)
            self._append_share_audit(session, share, self._share_audit_event(route="modify", decision="change",
                actor_email=actor.email, actor_groups=list(actor.groups)))
            return self._share_response(share)

    def invite_registry_recipient(self, euid: str, email: str):
        import os
        import requests
        from urllib.parse import urlsplit
        from dewey_service.settings import get_settings
        from dewey_service.registry_access import share_clause
        settings = get_settings()
        email = str(email).strip().lower()
        if email.count("@") != 1 or any(c.isspace() for c in email) or not principal().writable:
            raise ValueError("An explicit recipient email and write access are required")
        endpoint = os.environ.get("LSMC_AUTH_BROKER_SHARE_RECIPIENT_PREPARE_URL", "")
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or not settings.external_broker_service_token:
            raise HTTPException(503, "Registered Dewey broker invitation configuration is required")
        with self.backend.session_scope(commit=True) as session:
            share = self.backend.find_by_euid(session, template_code=SHARE_TEMPLATE, euid=euid)
            if share is None or not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission is required")
            data = normalize_instance_payload(share)
            if data["status"] != "active" or datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                raise ValueError("Only active, unexpired shares can send invitations")
            recipient = Principal(subject="recipient:" + email, email=email, roles=("READ_ONLY",),
                internal=email.rpartition("@")[2] in settings.registry_internal_domains)
            allowed = session.query(generic_instance.uid).filter(generic_instance.uid == share.uid,
                share_clause(generic_instance.json_addl, recipient)).first()
            if not allowed:
                raise ValueError("This email is not included in the share audience")
            origin = urlsplit(settings.external_broker_callback_url)
            share_url = f"{origin.scheme}://{origin.netloc}/shares/{euid}"
            receipt = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name="Share invitation",
                json_addl={"operation": "share_invitation", "actor": principal().subject, "created_at": utc_now_iso(),
                    "status": "sending", "recipient_email": email})
            self.backend.create_lineage(session, parent=share, child=receipt, relationship_type="has_storage_operation")
            operation_euid = receipt.euid
        state = "uncertain_failure"
        try:
            response = requests.post(endpoint, json={"recipient_email": email, "share_ref_euid": euid,
                "share_url": share_url, "expires_at": data["expires_at"]},
                headers={"Authorization": "Bearer " + settings.external_broker_service_token, "x-lsmc-service-id": "dewey"},
                timeout=(10, 30), allow_redirects=False, verify=settings.external_broker_ca_bundle or True)
            if 200 <= response.status_code < 300:
                state = "sent"
        except requests.RequestException:
            pass
        with self.backend.session_scope(commit=True) as session:
            row, _ = self._storage_operation(session, operation_euid, lock=True)
            self.backend.update_instance_json(session, row, {"status": state, "completed_at": utc_now_iso()})
        if state != "sent":
            raise HTTPException(502, f"Invitation was not confirmed; inspect operation {operation_euid} before retrying")
        return {"share_euid": euid, "operation_euid": operation_euid, "status": state}

    def update_registry(self, euid: str, changes: dict[str, Any]):
        if not changes or set(changes) - {"name", "description", "metadata"}:
            raise ValueError("Editable fields are name, description and metadata")
        if "metadata" in changes and not isinstance(changes["metadata"], dict):
            raise ValueError("metadata must be a JSON object")
        with self.backend.session_scope(commit=True) as session:
            record = self._registry_record(session, euid, action="edit", lock=True)
            updates = {k: v for k, v in changes.items() if k != "name"}
            if "name" in changes:
                name = str(changes["name"]).strip()
                if not name:
                    raise ValueError("name cannot be empty")
                self.backend.update_persisted_fields(session, record, {"name": name})
                updates["label" if record.type == "artifact_set" else "original_filename"] = name
            self.backend.update_instance_json(session, record, updates)
            self._registry_event(session, record, "metadata_updated")
            return self._registry_payload(session, record)

    def archive_registry(self, euid: str):
        with self.backend.session_scope(commit=True) as session:
            record = self._registry_record(session, euid, action="edit", lock=True)
            self.backend.update_instance_json(session, record, {
                "archived_at": utc_now_iso(), "archived_by": principal().subject,
            })
            self.backend.update_persisted_fields(session, record, {"bstatus": "archived"})
            self._registry_event(session, record, "registration_archived")
            shares = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.parent_instance_uid == record.uid,
                generic_instance_lineage.relationship_type == "has_share",
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False),
            ).all()
            for share in shares:
                self.backend.update_instance_json(session, share, {
                    "status": "revoked", "revoked_at": utc_now_iso(),
                    "revoked_by": principal().subject, "revocation_reason": "Registration archived",
                })
            return {"euid": euid, "status": "archived", "storage_deleted": False}

    def update_registry_permissions(self, euid: str, changes: dict[str, Any]):
        normalized = validate_policy(changes)
        with self.backend.session_scope(commit=True) as session:
            record = self._registry_record(session, euid, action="share", lock=True)
            policy = self._registry_policy(session, record)
            self.backend.update_instance_json(session, policy, {
                **normalized, "explicit_restriction": True,
                "changed_by": principal().subject, "changed_at": utc_now_iso(),
            })
            self._registry_event(session, record, "permissions_updated")
            return self._registry_payload(session, record)

    def transfer_registry_owner(self, euid: str, email: str):
        email = str(email).strip().lower()
        if email.count("@") != 1 or not all(email.split("@")) or any(c.isspace() for c in email):
            raise ValueError("An explicit owner email is required")
        actor = principal()
        if not actor.writable:
            raise HTTPException(403, "Ownership changes require write access")
        with self.backend.session_scope(commit=True) as session:
            record = self._registry_record(session, euid, lock=True)
            policy = self._registry_policy(session, record)
            prior = normalize_instance_payload(policy)
            if not (actor.admin or prior["owner_subject"] == actor.subject or actor.email and prior.get("owner_email") == actor.email):
                raise HTTPException(403, "Only the owner or an administrator may transfer ownership")
            self.backend.update_instance_json(session, policy, {"owner_subject": "email:" + email,
                "owner_email": email, "changed_by": actor.subject, "changed_at": utc_now_iso()})
            self._registry_event(session, record, "ownership_transferred")
            return {"euid": euid, "owner": email, "changed_by": actor.subject}

    def search_registry(self, request: dict[str, Any] | None, *, counts_only=False):
        from time import perf_counter
        started = perf_counter()
        data = dict(request or {})
        include_totals = data.get("include_totals", True)
        if type(include_totals) is not bool:
            raise ValueError("include_totals must be a boolean")
        projection = data.get("projection", "full")
        if projection not in ("full", "summary"):
            raise ValueError("Registry projection must be full or summary")
        scopes = data.get("scopes") or ["artifact", "artifact_set"]
        self._validate_property_filters(data.get("property_filters"))
        page = max(1, int(data.get("page") or 1))
        page_size = max(1, min(int(data.get("page_size") or 25), self.search_export_max_rows))
        sort = data.get("sort_field", "created_at")
        direction = data.get("sort_dir", "desc")
        columns = {"created_at": generic_instance.created_dt, "modified_at": generic_instance.modified_dt,
                   "name": generic_instance.name, "euid": generic_instance.euid}
        if sort not in columns or direction not in {"asc", "desc"}:
            raise ValueError("Invalid registry sort")
        with self.backend.session_scope(commit=False) as session:
            query = self._registry_query(session, scopes=scopes)
            if data.get("owner") or data.get("owned_by_me"):
                from dewey_service.registry_access import owner_clause
                policy = aliased(generic_instance)
                policy_edge = aliased(generic_instance_lineage)
                criterion = owner_clause(policy.json_addl, principal()) if data.get("owned_by_me") else or_(
                    policy.json_addl["owner_email"].astext == str(data["owner"]).lower(),
                    policy.json_addl["owner_subject"].astext == str(data["owner"]))
                query = query.filter(exists(select(literal(1)).select_from(policy_edge).join(policy,
                    policy.uid == policy_edge.child_instance_uid).where(policy_edge.parent_instance_uid == generic_instance.uid,
                    policy_edge.relationship_type == "registry_policy", policy_edge.is_deleted.is_(False), policy.is_deleted.is_(False), criterion)).correlate(generic_instance))
            needle = str(data.get("q") or "").strip()
            if needle:
                external = aliased(generic_instance)
                relation_edge = aliased(generic_instance_lineage)
                external_edge = aliased(generic_instance_lineage)
                external_match = exists(select(literal(1)).select_from(relation_edge).join(
                    external_edge, external_edge.child_instance_uid == relation_edge.child_instance_uid
                ).join(external, external.uid == external_edge.parent_instance_uid).where(
                    relation_edge.parent_instance_uid == generic_instance.uid,
                    relation_edge.relationship_type == "has_external_relation",
                    external_edge.relationship_type == "is_external_relation_for",
                    relation_edge.is_deleted.is_(False), external_edge.is_deleted.is_(False), external.is_deleted.is_(False),
                    func.lower(cast(external.json_addl, String)).contains(needle.lower(), autoescape=True),
                )).correlate(generic_instance)
                query = query.filter(or_(
                    func.lower(generic_instance.euid).contains(needle.lower(), autoescape=True),
                    func.lower(generic_instance.name).contains(needle.lower(), autoescape=True),
                    and_(literal(principal().admin) | (generic_instance.type != "share"),
                        func.lower(cast(generic_instance.json_addl, String)).contains(needle.lower(), autoescape=True)),
                    and_(generic_instance.type == "share", func.lower(generic_instance.json_addl["purpose"].astext).contains(needle.lower(), autoescape=True)),
                    external_match,
                ))
            for key, op in (("created_at_start", "gte"), ("created_at_end", "lte")):
                if data.get(key):
                    value = self._parse_iso8601(data[key], field_name=key)
                    query = query.filter(generic_instance.created_dt >= value if op == "gte" else generic_instance.created_dt <= value)
            for rule in data.get("property_filters") or []:
                path = str(rule["path"]).strip()
                op = str(rule.get("op", "eq")).strip().lower()
                value = rule.get("value")
                if "share" in scopes and not principal().admin and path not in {
                    "euid", "share_euid", "name", "record_type", "status", "created_at", "expires_at", "audience", "owner_email"
                }:
                    raise ValueError("This share filter is restricted to administrators")
                direct = {"euid": generic_instance.euid, "artifact_euid": generic_instance.euid,
                    "artifact_set_euid": generic_instance.euid, "share_euid": generic_instance.euid,
                    "name": generic_instance.name, "record_type": generic_instance.type}
                if path in direct:
                    column = direct[path]
                    if op == "eq": condition = column == value
                    elif op == "neq": condition = column != value
                    elif op == "in": condition = column.in_(value if isinstance(value, list) else [value])
                    elif op == "contains": condition = func.lower(column).contains(str(value).lower(), autoescape=True)
                    elif op == "exists": condition = column.is_not(None) if value is not False else column.is_(None)
                    else: condition = column >= value if op == "gte" else column <= value
                else:
                    external_path = path.startswith("external_objects.")
                    if external_path:
                        path = path.removeprefix("external_objects.")
                    elif path in {"title", "pmid", "doi", "pmcid", "storage_mode", "fulltext_status", "authors", "journal", "year", "abstract_snippet"}:
                        path = "metadata." + path
                    json_path = "$" + "".join("." + json.dumps(part) for part in path.split("."))
                    operators = {"eq": "==", "neq": "!=", "gte": ">=", "lte": "<="}
                    if op in operators:
                        expression = f"{json_path} ? (@ {operators[op]} $value)"
                    elif op == "in":
                        expression = f"{json_path} ? (@ == $value[*])"
                        value = value if isinstance(value, list) else [value]
                    elif op == "contains":
                        import re
                        expression = f"{json_path} ? (@ like_regex {json.dumps(re.escape(str(value or '')))} flag \"i\")"
                    else:
                        expression = json_path
                    filter_external = aliased(generic_instance) if external_path else None
                    condition = func.jsonb_path_exists(
                        filter_external.json_addl if external_path else generic_instance.json_addl, cast(literal(expression), JSONPATH),
                        literal({"value": value}, type_=JSONB),
                    )
                    if external_path:
                        relation_link = aliased(generic_instance_lineage)
                        external_link = aliased(generic_instance_lineage)
                        condition = exists(select(literal(1)).select_from(relation_link).join(
                            external_link, external_link.child_instance_uid == relation_link.child_instance_uid
                        ).join(filter_external, filter_external.uid == external_link.parent_instance_uid).where(
                            relation_link.parent_instance_uid == generic_instance.uid,
                            relation_link.relationship_type == "has_external_relation",
                            external_link.relationship_type == "is_external_relation_for",
                            relation_link.is_deleted.is_(False), external_link.is_deleted.is_(False),
                            filter_external.is_deleted.is_(False), condition,
                        )).correlate(generic_instance)
                    if op == "exists" and value is False:
                        condition = ~condition
                query = query.filter(condition)
            facets = total = None
            if include_totals or counts_only:
                facets = {key: 0 for key in ("artifact", "artifact_set", "share")}
                for kind, count in query.with_entities(generic_instance.type, func.count()).group_by(generic_instance.type).all():
                    facets[kind] = count
                total = sum(facets.values())
            if counts_only:
                return {"total": total, "facets": facets, "timing_ms": int((perf_counter() - started) * 1000)}
            order = columns[sort].asc() if direction == "asc" else columns[sort].desc()
            records = query.order_by(order, generic_instance.euid).offset((page - 1) * page_size).limit(
                page_size if include_totals else page_size + 1).all()
            has_more = page * page_size < total if include_totals else len(records) > page_size
            records = records[:page_size]
            if projection == "summary":
                items = self._registry_summary_items(session, records)
                return {"items": items, "facets": facets, "total": total, "page": page,
                        "page_size": page_size, "has_more": has_more,
                        "projection": projection, "timing_ms": int((perf_counter() - started) * 1000)}
            items = [self._registry_payload(session, record, details=False) for record in records]
            for item, record in zip(items, records):
                if record.type == "artifact":
                    item["external_objects"] = self._artifact_external_objects(session, record)
                    if item.get("artifact_type") == "literature":
                        from dewey_service.literature import ViewerContext
                        actor = principal()
                        item.update(self._visible_literature_save_summary(session, record,
                            ViewerContext(subject=actor.subject, email=actor.email, groups=actor.groups)))
                        metadata = item.get("metadata", {})
                        for key in ("title", "pmid", "doi", "pmcid", "storage_mode", "fulltext_status", "authors", "journal", "year", "abstract_snippet"):
                            item[key] = metadata.get(key)
            return {"items": items, "facets": facets, "total": total, "page": page,
                    "page_size": page_size, "has_more": has_more,
                    "timing_ms": int((perf_counter() - started) * 1000)}

    def issue_registry_token(self, *, name: str, lifetime_days: int = 30, role: str | None = None):
        actor = principal()
        if actor.service or not actor.email or not name.strip() or not 1 <= lifetime_days <= 90:
            raise ValueError("A signed-in user, token name, and lifetime of 1..90 days are required")
        permitted = {"READ_ONLY"}
        if actor.writable:
            permitted.add("READ_WRITE")
        if actor.admin:
            permitted.add("ADMIN")
        if role is not None and role not in permitted:
            raise HTTPException(403, "Token role exceeds the issuing user's access")
        roles = [role] if role is not None else list(actor.roles)
        token = "dewey_user_" + secrets.token_urlsafe(48)
        expires = (datetime.now(timezone.utc) + timedelta(days=lifetime_days)).isoformat()
        with self.backend.session_scope(commit=True) as session:
            row = self.backend.create_instance(session, template_code=TOKEN_TEMPLATE, name=name.strip(), json_addl={
                "token_sha256": sha256(token.encode()).hexdigest(), "subject": actor.subject,
                "email": actor.email, "roles": roles, "groups": list(actor.groups),
                "internal": actor.internal, "expires_at": expires, "status": "active",
            })
            return {"euid": row.euid, "token": token, "expires_at": expires, "roles": roles, "display_once": True}

    def authenticate_registry_token(self, token: str):
        with self.backend.session_scope(commit=False) as session:
            template = self.backend.templates.get_template(session, TOKEN_TEMPLATE, domain_code=self.backend.domain_code)
            if template is None:
                raise HTTPException(503, "User token template is not installed")
            row = session.query(generic_instance).filter(
                generic_instance.template_uid == template.uid, generic_instance.is_deleted.is_(False),
                generic_instance.json_addl["token_sha256"].astext == sha256(token.encode()).hexdigest(),
            ).first()
            if row is None:
                raise HTTPException(401, "Invalid Dewey user token")
            data = normalize_instance_payload(row)
            if data["status"] != "active" or datetime.fromisoformat(data["expires_at"]) <= datetime.now(timezone.utc):
                raise HTTPException(401, "Dewey user token is revoked or expired")
            return Principal(subject=data["subject"], email=data["email"], roles=tuple(data["roles"]),
                groups=tuple(data["groups"]), internal=data["internal"])

    def registry_tokens(self):
        actor = principal()
        with self.backend.session_scope(commit=False) as session:
            query = self.backend._template_query(session, template_code=TOKEN_TEMPLATE)
            if not actor.admin:
                query = query.filter(generic_instance.json_addl["subject"].astext == actor.subject)
            return [{"euid": r.euid, "name": r.name, "email": normalize_instance_payload(r)["email"],
                "status": normalize_instance_payload(r)["status"], "expires_at": normalize_instance_payload(r)["expires_at"]}
                for r in query.order_by(generic_instance.created_dt.desc()).all()]

    def revoke_registry_token(self, euid: str):
        actor = principal()
        with self.backend.session_scope(commit=True) as session:
            row = self.backend.find_by_euid(session, template_code=TOKEN_TEMPLATE, euid=euid, for_update=True)
            if row is None or (not actor.admin and normalize_instance_payload(row)["subject"] != actor.subject):
                raise DeweyNotFoundError("Token not found")
            self.backend.update_instance_json(session, row, {"status": "revoked", "revoked_at": utc_now_iso()})
            return {"euid": euid, "status": "revoked"}
