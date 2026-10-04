"""Authorized S3 navigation and durable, explicitly selected storage operations."""
from __future__ import annotations

import math
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import HTTPException
from sqlalchemy import DateTime, and_, cast, func, literal, or_
from sqlalchemy.orm import aliased

from dewey_service.registry_access import OPERATION_TEMPLATE, principal, record_clause, require_record, share_clause
from dewey_service.storage import StorageObjectNotFoundError
from dewey_service.services.base import DeweyNotFoundError
from dewey_service.tapdb_backend import ARTIFACT_TEMPLATE, normalize_instance_payload, utc_now_iso


def parse_s3_uri(uri: str, *, prefix: bool = False):
    if not isinstance(uri, str) or not uri.startswith("s3://"):
        raise ValueError("An explicit s3:// URI is required")
    bucket, separator, key = uri[5:].partition("/")
    if not bucket or any(c.isspace() for c in bucket) or any(c in bucket for c in "?#@:"):
        raise ValueError("Invalid S3 bucket")
    if prefix and key and not key.endswith("/"):
        key += "/"
    return bucket, key, f"s3://{bucket}/{key}"


class RegistryStorageServiceMixin:
    def _storage_locations_batch(self, session, locations, *, action="metadata"):
        """Evaluate each relevant registered ancestor once, preserving the SQL policy contract."""
        actor = principal()
        locations = list(dict.fromkeys(locations))
        if not locations:
            return {}, {}
        action_key = "download" if action == "download" else "edit" if action == "upload" else "metadata"
        key_column = generic_instance.json_addl["key"].astext
        grouped = {}
        for bucket, key in locations:
            grouped.setdefault(bucket, []).append(key)
        paths = []
        for bucket, keys in grouped.items():
            paths.append(and_(generic_instance.json_addl["bucket"].astext == bucket,
                or_(key_column.in_(keys), and_(
                    generic_instance.json_addl["storage_kind"].astext == "prefix",
                    or_(*(func.left(literal(key), func.length(key_column)) == key_column for key in keys))))))
        query = self._registry_query(session, scopes=("artifact",), authorize=False).filter(
            generic_instance.json_addl["storage_backend"].astext == "s3", or_(*paths))
        records = query.with_entities(generic_instance, record_clause(session, generic_instance, action_key)).all()
        policies = {}
        if records and not actor.admin:
            # Policy objects themselves have no independent registry visibility restriction.
            rows = session.query(generic_instance_lineage.parent_instance_uid, generic_instance).select_from(generic_instance_lineage).join(
                generic_instance, generic_instance.uid == generic_instance_lineage.child_instance_uid).filter(
                generic_instance_lineage.parent_instance_uid.in_([r.uid for r, _ in records]),
                generic_instance_lineage.relationship_type == "registry_policy",
                generic_instance.type == "registry_policy",
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False)).all()
            for parent_uid, policy in rows:
                policies.setdefault(parent_uid, {})[policy.uid] = policy
            for record, _ in records:
                if len(policies.get(record.uid, {})) != 1:
                    raise RuntimeError(f"Record {record.euid} requires exactly one initialized registry policy")
        authorized = dict.fromkeys(locations, bool(actor.internal or actor.admin))
        denied = set()
        registered = {}
        for record, allowed in records:
            data = normalize_instance_payload(record)
            path = data["key"]
            policy = {} if actor.admin else normalize_instance_payload(next(iter(policies[record.uid].values())))
            location = (data["bucket"], path)
            if allowed and location in authorized and location not in registered:
                registered[location] = record
            for bucket, key in locations:
                if bucket != data["bucket"]:
                    continue
                exact = path == key
                if not exact and not (data["storage_kind"] == "prefix" and key.startswith(path)):
                    continue
                if not allowed and (exact or policy.get("explicit_restriction") or record.bstatus == "archived"):
                    denied.add((bucket, key))
                authorized[(bucket, key)] = authorized[(bucket, key)] or bool(allowed)
        for key in denied:
            authorized[key] = False
        return authorized, registered

    def _storage_access_batch(self, session, bucket, keys, *, action="metadata"):
        allowed, registered = self._storage_locations_batch(session, [(bucket, key) for key in keys], action=action)
        return ({key: value for (_, key), value in allowed.items()},
                {key: value for (_, key), value in registered.items()})

    def require_storage_access(self, bucket: str, key: str, *, action: str, session=None):
        actor = principal()
        if action in {"upload", "delete"}:
            if not actor.writable or not (actor.internal or actor.admin):
                raise HTTPException(403, "S3 changes require internal LSMC write access")
            if action == "delete" and not actor.admin:
                raise HTTPException(403, "S3 deletion requires admin access")
        if actor.admin:
            return
        if session is None:
            with self.backend.session_scope(commit=False) as opened:
                return self.require_storage_access(bucket, key, action=action, session=opened)
        authorized, _ = self._storage_access_batch(session, bucket, [key], action=action)
        if not authorized[key]:
            raise HTTPException(403, "This S3 path requires independent access or an exact share-scoped operation")

    def registry_buckets(self, continuation_token=None, locations_page=1, refresh=False):
        actor = principal()
        owned = {"items": [], "next_continuation_token": None}
        if actor.internal or actor.admin:
            owned = self._require_storage().list_buckets(continuation_token=continuation_token,
                cache_ttl=self.registry_defaults()["listing_cache_ttl_seconds"], refresh=refresh)
            if not actor.admin:
                with self.backend.session_scope(commit=False) as session:
                    allowed, _ = self._storage_locations_batch(session, [(b["name"], "") for b in owned["items"]])
                owned["items"] = [b for b in owned["items"] if allowed[(b["name"], "")]]
        with self.backend.session_scope(commit=False) as session:
            query = self._registry_query(session, scopes=("artifact",)).filter(
                generic_instance.json_addl["storage_backend"].astext == "s3",
                generic_instance.json_addl["storage_kind"].astext == "prefix",
            )
            if actor.internal or actor.admin:
                query = query.filter(generic_instance.json_addl["key"].astext == "")
            page = max(1, int(locations_page))
            roots = query.order_by(generic_instance.name, generic_instance.euid).offset((page - 1) * 100).limit(101).all()
            more = len(roots) > 100
            roots = roots[:100]
            locations = [{"euid": row.euid, "name": row.name, "uri": normalize_instance_payload(row)["storage_uri"]} for row in roots]
        return {**owned, "registered_locations": locations, "credential_mode": "service",
            "next_locations_page": page + 1 if more else None}

    def registry_browse(self, root_uri: str, *, limit=100, continuation_token=None, refresh=False):
        bucket, prefix, uri = parse_s3_uri(root_uri, prefix=True)
        result = self._require_storage().browse_prefix(bucket=bucket, prefix=prefix, limit=limit,
            continuation_token=continuation_token, refresh=refresh,
            cache_ttl=self.registry_defaults()["listing_cache_ttl_seconds"])
        crumbs = [{"label": bucket, "uri": f"s3://{bucket}/", "key": ""}]
        for index, character in enumerate(prefix):
            if character == "/":
                part = prefix[:index + 1]
                crumbs.append({"label": part[:-1].rpartition("/")[2] or "/", "uri": f"s3://{bucket}/{part}", "key": part})
        entries = [("prefix", item.prefix, item) for item in result["prefixes"]]
        entries += [("object", item.key, item) for item in result["objects"]]
        keys = [prefix, *(key for _, key, _ in entries), *(c["key"] for c in crumbs)]
        with self.backend.session_scope(commit=False) as session:
            authorized, registered = self._storage_access_batch(session, bucket, keys)
            if not authorized[prefix]:
                raise HTTPException(403, "This S3 path is restricted or has not been shared with you")
            rows = []
            for kind, key, item in entries:
                if not authorized[key]:
                    continue
                registration = registered.get(key)
                row = {"kind": kind, "name": key[len(prefix):], "key": key,
                       "uri": f"s3://{bucket}/{key}", "euid": registration.euid if registration is not None else None}
                if kind == "object":
                    row.update(size=item.size, etag=item.etag)
                rows.append(row)
            current = registered.get(prefix)
            current_artifact = self._artifact_response(current) if current is not None else None
        visible_crumbs = [{"label": c["label"], "uri": c["uri"]} for c in crumbs if authorized[c["key"]]]
        return {"root_uri": uri, "bucket": bucket, "prefix": prefix, "items": rows,
                "current_artifact": current_artifact,
                "breadcrumbs": visible_crumbs, "parent_uri": visible_crumbs[-2]["uri"] if len(visible_crumbs) > 1 else None,
                "next_continuation_token": result["next_continuation_token"], "is_truncated": result["is_truncated"]}

    def registry_object(self, uri: str):
        bucket, key, _ = parse_s3_uri(uri)
        with self.backend.session_scope(commit=False) as session:
            independent, _ = self._storage_access_batch(session, bucket, [key], action="metadata")
        if not independent[key]:
            from dewey_service.storage import storage_authorization_context
            receipt = self.authorize_shared_storage(bucket, key, action="metadata")
            def scope(request_bucket, request_key, action):
                if (request_bucket, request_key) != (bucket, key) or action != "metadata":
                    raise HTTPException(403, "Storage request exceeds the shared object")
            with storage_authorization_context(scope):
                result = asdict(self._require_storage().head_object(bucket=bucket, key=key, version_id=receipt["version_id"],
                    request_payer=self._request_payer_for_bucket(bucket)))
            return {**result, "uri": uri, "registered_artifact": None}
        result = asdict(self._require_storage().head_object(bucket=bucket, key=key))
        with self.backend.session_scope(commit=False) as session:
            result["registered_artifact"] = self._artifact_for_storage_uri(session, storage_uri=uri)
        return {**result, "uri": uri}

    def registry_contents(self, euid: str, *, relative_prefix="", continuation_token=None, limit=100, refresh=False):
        value = self.resolve_registry(euid, projection="summary")
        if value["kind"] == "set":
            return {"euid": euid, "kind": "set", "items": self.resolve_registry(euid)["members"]}
        if value["kind"] != "prefix":
            raise ValueError("This EUID is an object; use its access action")
        # S3 keys are literal; never normalize away repeated separators or spaces.
        root = value["storage_uri"]
        result = self.registry_browse(root + relative_prefix, continuation_token=continuation_token, limit=limit, refresh=refresh)
        return {**result, "euid": euid}

    def registry_download(self, *, euid: str | None = None, uri: str | None = None, relative_key="", version_id=None, ttl_seconds=None):
        actor = principal()
        # Determine the exact bytes first. A share-only right must pass the same explicit
        # presign capability check as the share-scoped endpoint, including raw-URI aliases.
        share_location = None
        with self.backend.session_scope(commit=False) as session:
            if euid:
                candidate = self._registry_query(session, scopes=("artifact",), authorize=False).filter(
                    generic_instance.euid == euid).first()
                if candidate is not None:
                    raw = normalize_instance_payload(candidate)
                    if raw.get("storage_backend") == "s3" and (raw.get("storage_kind") == "object" or relative_key):
                        if raw.get("storage_kind") == "object" and relative_key:
                            raise ValueError("relative_key is only valid for a Prefix EUID")
                        share_location = (raw["bucket"], raw["key"] + relative_key)
            elif uri:
                share_location = parse_s3_uri(uri)[:2]
            if share_location:
                independently_allowed, _ = self._storage_locations_batch(session, [share_location], action="download")
                if not independently_allowed[share_location]:
                    receipt = self.authorize_shared_storage(*share_location, action="presign")
                    if version_id is not None and version_id != receipt["version_id"]:
                        raise ValueError("Requested version differs from the shared target")
                    return self.presign_share_object(receipt["share_euid"], receipt["target_euid"],
                        relative_key=receipt["relative_key"], ttl_seconds=ttl_seconds)
        if euid:
            with self.backend.session_scope(commit=False) as session:
                record = self._registry_record(session, euid, action="download")
                value = self._registry_payload(session, record)
                if value["kind"] == "set":
                    members = self._registry_query(session, scopes=("artifact",), authorize=False).join(
                        generic_instance_lineage, generic_instance_lineage.child_instance_uid == generic_instance.uid).filter(
                        generic_instance_lineage.parent_instance_uid == record.uid,
                        generic_instance_lineage.relationship_type == "artifact_set_member",
                        generic_instance_lineage.is_deleted.is_(False), generic_instance.bstatus != "archived",
                        record_clause(session, generic_instance, "download")).all()
                    return {"euid": euid, "kind": "set", "items": [
                        {"euid": item.euid, "access_path": f"/api/v1/records/{item.euid}/access"}
                        for item in members], "delivery": "member_manifest"}
            if value["kind"] == "prefix":
                if not relative_key:
                    return {"euid": euid, "kind": "prefix", "browser_path": f"/records/{euid}",
                            "contents_path": f"/api/v1/records/{euid}/contents", "delivery": "folder_browser"}
                uri = value["storage_uri"] + relative_key
            else:
                if relative_key:
                    raise ValueError("relative_key is only valid for a Prefix EUID")
                uri = value["storage_uri"]
                version_id = value["version_id"]
                if value["storage_backend"] in {"http", "https", "url"}:
                    source = value.get("source_uri") or uri
                    if not source.startswith(("https://", "http://")):
                        raise ValueError("Unsupported reference URL")
                    return {"euid": euid, "delivery": "external_reference", "url": source,
                            "revocation_scope": "Dewey access only; external host permissions are unchanged"}
        if not uri:
            raise ValueError("An EUID or explicit S3 URI is required")
        bucket, key, _ = parse_s3_uri(uri)
        self.require_storage_access(bucket, key, action="download")
        storage = self._require_storage()
        obj = storage.head_object(bucket=bucket, key=key, version_id=version_id, permission="download")
        ttl = int(ttl_seconds if ttl_seconds is not None else self.registry_defaults()["delivery_lifetime_seconds"])
        if not 1 <= ttl <= 3600:
            raise ValueError("Delivery lifetime must be 1..3600 seconds")
        with self.backend.session_scope(commit=True) as session:
            shares = []
            url = storage.generate_presigned_get_url(bucket=bucket, key=key, version_id=obj.version_id, expires_in=ttl)
            receipt = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE,
                name="Download credential issued", json_addl={"operation": "download_issued", "actor": actor.subject,
                    "uri": uri, "expires_in": ttl, "created_at": utc_now_iso(), "status": "issued"})
            if euid:
                target = self._registry_record(session, euid, action="download")
                self.backend.create_lineage(session, parent=target, child=receipt, relationship_type="has_storage_operation")
            for share in shares:
                self.backend.create_lineage(session, parent=share, child=receipt, relationship_type="has_storage_operation")
            receipt_euid = receipt.euid
        return {"euid": euid, "url": url, "delivery": "presigned_s3", "expires_in": ttl,
                "receipt_euid": receipt_euid, "download_completion_observed": False}

    def begin_registry_upload(self, *, uri: str, size: int, content_type: str, replace_etag=None):
        actor = principal()
        bucket, key, _ = parse_s3_uri(uri)
        if not key or size < 0 or size > 5 * 1024 ** 4:
            raise ValueError("Upload requires an object key and size from 0 bytes through 5 TiB")
        self.require_storage_access(bucket, key, action="upload")
        if replace_etag and not actor.admin:
            raise HTTPException(403, "Replacement requires admin access")
        storage = self._require_storage()
        try:
            existing = storage.head_object(bucket=bucket, key=key, permission="upload")
        except StorageObjectNotFoundError:
            existing = None
        if existing and (not replace_etag or replace_etag.strip('"') != existing.etag):
            raise HTTPException(409, "An object already exists; choose a new key or explicitly review admin replacement")
        if not existing and replace_etag:
            raise HTTPException(409, "The reviewed replacement object no longer exists")
        part_size = max(16 * 1024 ** 2, math.ceil(size / 10000))
        with self.backend.session_scope(commit=True) as session:
            row = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name=f"Upload {key}", json_addl={
                "operation": "upload", "actor": actor.subject, "bucket": bucket, "key": key,
                "uri": uri, "size": size, "part_size": part_size, "upload_id": None,
                "parts": {}, "replace_etag": replace_etag, "status": "preparing", "created_at": utc_now_iso(),
            })
            operation_euid = row.euid
        try:
            upload_id = storage.begin_multipart(bucket=bucket, key=key, content_type=content_type)
            with self.backend.session_scope(commit=True) as session:
                operation, _ = self._storage_operation(session, operation_euid, lock=True)
                self.backend.update_instance_json(session, operation, {"upload_id": upload_id, "status": "uploading"})
        except Exception:
            # An uncertain S3 response is never retried automatically.
            raise HTTPException(503, f"Upload initialization did not complete; inspect operation {operation_euid}") from None
        return {"operation_euid": operation_euid, "part_size": part_size, "size": size, "status": "uploading"}

    def _storage_operation(self, session, euid, *, lock=False):
        row = self.backend.find_by_euid(session, template_code=OPERATION_TEMPLATE, euid=euid, for_update=lock)
        if row is None:
            raise DeweyNotFoundError("Storage operation not found")
        data = normalize_instance_payload(row)
        if data["actor"] != principal().subject and not principal().admin:
            raise HTTPException(403, "This storage operation belongs to another principal")
        return row, data

    def upload_registry_part(self, euid: str, number: int, body: bytes):
        with self.backend.session_scope(commit=True) as session:
            row, data = self._storage_operation(session, euid, lock=True)
            if data["status"] != "uploading" or data["operation"] != "upload":
                raise ValueError("Upload is not accepting parts")
            count = max(1, math.ceil(data["size"] / data["part_size"]))
            expected = data["part_size"] if number < count else data["size"] - (count - 1) * data["part_size"]
            if not 1 <= number <= count or len(body) != expected:
                raise ValueError("Upload part number or byte length differs from the declared upload")
            self.require_storage_access(data["bucket"], data["key"], action="upload")
            etag = self._require_storage().upload_part(bucket=data["bucket"], key=data["key"], upload_id=data["upload_id"], part_number=number, body=body)
            parts = dict(data["parts"])
            parts[str(number)] = {"ETag": etag, "PartNumber": number, "size": len(body)}
            self.backend.update_instance_json(session, row, {"parts": parts})
            return {"operation_euid": euid, "part": number, "uploaded_bytes": sum(p["size"] for p in parts.values())}

    def complete_registry_upload(self, euid: str, *, abort=False):
        with self.backend.session_scope(commit=True) as session:
            row, data = self._storage_operation(session, euid, lock=True)
            if data.get("operation") != "upload":
                raise ValueError("This operation is not an upload")
            if data["status"] == "complete" and not abort:
                return {"operation_euid": euid, "status": "complete", "uri": data["uri"], "registered": False}
            if data["status"] == "aborted" and abort:
                return {"operation_euid": euid, "status": "aborted", "uri": data["uri"], "registered": False}
            if data["status"] != "uploading":
                raise HTTPException(409, "Upload outcome requires inspection; no completion or abort was retried")
            self.require_storage_access(data["bucket"], data["key"], action="upload")
            if data.get("replace_etag") and not principal().admin:
                raise HTTPException(403, "Replacement requires current admin access")
            parts = sorted(data["parts"].values(), key=lambda p: p["PartNumber"])
            if not abort and (sum(p["size"] for p in parts) != data["size"] or not parts):
                raise ValueError("Upload does not yet contain all declared bytes")
            self.backend.update_instance_json(session, row, {"status": "aborting" if abort else "completing",
                "finalization_started_at": utc_now_iso()})
        storage = self._require_storage()
        try:
            if abort:
                storage.abort_multipart(bucket=data["bucket"], key=data["key"], upload_id=data["upload_id"])
                state = "aborted"
            else:
                storage.complete_multipart(bucket=data["bucket"], key=data["key"], upload_id=data["upload_id"],
                    parts=[{k: p[k] for k in ("ETag", "PartNumber")} for p in parts], replace_etag=data["replace_etag"])
                state = "complete"
        except Exception:
            with self.backend.session_scope(commit=True) as session:
                row, _ = self._storage_operation(session, euid, lock=True)
                self.backend.update_instance_json(session, row, {"status": "uncertain_failure",
                    "failure_at": utc_now_iso(), "requested_action": "abort" if abort else "complete"})
            raise HTTPException(503, f"Upload outcome is uncertain; inspect operation {euid} before any further action") from None
        with self.backend.session_scope(commit=True) as session:
            row, _ = self._storage_operation(session, euid, lock=True)
            self.backend.update_instance_json(session, row, {"status": state, "completed_at": utc_now_iso()})
        return {"operation_euid": euid, "status": state, "uri": data["uri"], "registered": False}

    def preview_registry_delete(self, *, uri: str, kind: str, max_objects=10000):
        bucket, key, _ = parse_s3_uri(uri, prefix=kind == "prefix")
        self.require_storage_access(bucket, key, action="delete")
        if kind not in {"object", "prefix"} or not key:
            raise ValueError("Select an object or non-root folder; bucket deletion is not supported")
        storage = self._require_storage()
        versioning = storage.bucket_versioning(bucket)
        items = storage.list_objects(bucket=bucket, prefix=key, limit=max_objects + 1) if kind == "prefix" else [storage.head_object(bucket=bucket, key=key)]
        if len(items) > max_objects:
            raise ValueError(f"This preview exceeds {max_objects} objects; select a narrower folder")
        if not items:
            raise ValueError("There are no objects to delete")
        manifest = [{"Key": item.key, "ETag": item.etag, "size": item.size} for item in items]
        if any(not item["ETag"] for item in manifest):
            raise ValueError("Every deletion target requires an observed ETag")
        digest = self._fingerprint(manifest)
        with self.backend.session_scope(commit=True) as session:
            row = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name=f"Delete review {uri}", json_addl={
                "operation": "delete", "actor": principal().subject, "uri": uri, "bucket": bucket,
                "manifest": manifest, "manifest_sha256": digest, "versioning": versioning,
                "status": "preview", "created_at": utc_now_iso(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(), "results": [],
            })
            return {"operation_euid": row.euid, "manifest_sha256": digest, "targets": manifest,
                    "count": len(manifest), "bytes": sum(item["size"] or 0 for item in manifest), "versioning": versioning,
                    "effect": "Create delete markers; retain version history" if versioning == "Enabled" else "Remove current objects; unversioned bytes may be permanently deleted"}

    def execute_registry_delete(self, euid: str, *, manifest_sha256: str, confirmation: str):
        if not principal().admin:
            raise HTTPException(403, "S3 deletion requires admin access")
        with self.backend.session_scope(commit=True) as session:
            row, data = self._storage_operation(session, euid, lock=True)
            if data["operation"] != "delete" or data["status"] != "preview":
                raise ValueError("Only a pending reviewed deletion can be executed")
            if confirmation != "DELETE" or data["manifest_sha256"] != manifest_sha256:
                raise ValueError("Confirm DELETE and the exact reviewed manifest digest")
            if datetime.fromisoformat(data["expires_at"]) <= datetime.now(timezone.utc):
                raise ValueError("Deletion preview expired; review the current objects again")
            self.backend.update_instance_json(session, row, {"status": "executing", "confirmed_at": utc_now_iso()})
        results = []
        state = "complete"
        try:
            for start in range(0, len(data["manifest"]), 1000):
                batch = [{"Key": item["Key"], "ETag": item["ETag"]} for item in data["manifest"][start:start + 1000]]
                response = self._require_storage().delete_reviewed_objects(bucket=data["bucket"], objects=batch)
                results.extend({"status": "deleted", **item} for item in response.get("Deleted", []))
                results.extend({"status": "failed", **item} for item in response.get("Errors", []))
                observed = {item["Key"] for item in response.get("Deleted", []) + response.get("Errors", [])}
                missing = [item for item in batch if item["Key"] not in observed]
                results.extend({"Key": item["Key"], "status": "unknown"} for item in missing)
                if response.get("Errors") or missing: state = "partial_failure"
                with self.backend.session_scope(commit=True) as session:
                    row, _ = self._storage_operation(session, euid, lock=True)
                    self.backend.update_instance_json(session, row, {"results": results})
        except Exception:
            state = "uncertain_failure"
            raise
        finally:
            with self.backend.session_scope(commit=True) as session:
                row, _ = self._storage_operation(session, euid, lock=True)
                self.backend.update_instance_json(session, row, {"status": state, "results": results, "completed_at": utc_now_iso()})
        return {"operation_euid": euid, "status": state, "results": results}
