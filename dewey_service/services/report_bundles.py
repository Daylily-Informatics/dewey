"""Validated MultiQC registration and explicitly reviewed existing-share repair."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, or_
from daylily_tapdb import generic_instance

from dewey_service.multiqc_bundle import MAX_DOCUMENT_BYTES, NotMultiQCReport, RequiredExternalAssets, html_candidate, inspect_bundle, multiqc_candidate, saved_bundle
from dewey_service.storage import StorageObjectNotFoundError, storage_authorization_context
from dewey_service.registry_access import principal
from dewey_service.tapdb_backend import normalize_instance_payload


# Bound the policy query and the lifetime of each exact-path authorization batch.
_REPORT_AUTHORIZATION_BATCH_SIZE = 100


class ReportBundleServiceMixin:
    def _require_report_access_batch(self, session, bucket, keys):
        if principal().admin:
            return
        if session is None:
            with self.backend.session_scope(commit=False) as opened:
                return self._require_report_access_batch(opened, bucket, keys)
        authorized, _ = self._storage_access_batch(session, bucket, keys, action="download")
        if not all(authorized.get(key, False) for key in keys):
            raise HTTPException(
                403, "This S3 path requires independent access or an exact share-scoped operation"
            )

    @staticmethod
    def _report_batch_authorizer(bucket, keys):
        # This is a request-local, bounded set of exact coordinates, never a
        # prefix grant. It lives only while this authorized batch is consumed.
        allowed = frozenset(keys)

        def authorize(bucket_name, key, action):
            if bucket_name != bucket or key not in allowed or action != "download":
                raise HTTPException(403, "Storage operation is outside the authorized report batch")
        return authorize

    def _prepare_multiqc_payload(self, session, payload, *, observations=None):
        """Inspect with caller-owned sessions, or short-lived authorization sessions.

        Detached registration scans authorize each discovered exact dependency
        frontier in bounded batches and close the DB session before reading it.
        The registration caller must revalidate the observations before writing.
        """
        if not html_candidate(payload):
            return payload
        storage = self._require_storage()
        bucket = payload["bucket"]

        detached = session is None
        if detached and observations is None:
            raise ValueError("Detached report inspection requires an observation inventory")
        documents = {}
        fetched = set()
        pending_documents = {}

        def authorize(bucket_name, key, action):
            self.require_storage_access(bucket_name, key, action=action, session=session)

        def response(key, *, head=False, authorization=authorize):
            try:
                # The S3 adapter still requires an explicit exact-path callback.
                with storage_authorization_context(authorization):
                    value = storage.object_response(bucket=bucket, key=key, head=head,
                        version_id=payload.get("version_id") if key == payload["key"] else None,
                        request_payer=self._request_payer_for_bucket(bucket))
                if observations is not None:
                    etag = value.get("ETag")
                    if not etag:
                        if not head:
                            value["Body"].close()
                        raise ValueError("Report inspection requires an S3 ETag for every object")
                    identity = (etag, value.get("VersionId"))
                    if key in observations and observations[key] != identity:
                        if not head:
                            value["Body"].close()
                        raise HTTPException(409, "Report object changed during inspection; retry registration")
                    observations[key] = identity
                return value
            except StorageObjectNotFoundError as error:
                raise ValueError("MultiQC bundle is incomplete; missing asset: " + key) from error

        def consume_document(value, key):
            body = value["Body"]
            try:
                content = body.read(MAX_DOCUMENT_BYTES + 1)
            finally:
                body.close()
            # Reject a large dependency before retaining its bytes. The original
            # source is classified first by inspect_bundle: an oversized ordinary
            # non-MultiQC HTML must still be left unchanged, while a MultiQC source
            # fails its existing size check before any dependencies are read.
            if len(content) > MAX_DOCUMENT_BYTES and key != payload["key"]:
                raise ValueError("MultiQC document exceeds the supported 64 MiB inspection limit")
            return content, value.get("ETag")

        def prepare_batch(operations):
            pending = list(dict.fromkeys(op for op in operations if op not in fetched))
            document_keys = list(dict.fromkeys(
                key for key, head in pending if not head and key not in pending_documents
            ))
            for offset in range(0, len(document_keys), _REPORT_AUTHORIZATION_BATCH_SIZE):
                keys = document_keys[offset:offset + _REPORT_AUTHORIZATION_BATCH_SIZE]
                batch = {"keys": keys, "remaining": set(keys), "authorization": None}
                for key in keys:
                    pending_documents[key] = batch
            asset_keys = list(dict.fromkeys(key for key, head in pending if head))
            for offset in range(0, len(asset_keys), _REPORT_AUTHORIZATION_BATCH_SIZE):
                keys = asset_keys[offset:offset + _REPORT_AUTHORIZATION_BATCH_SIZE]
                self._require_report_access_batch(None, bucket, keys)
                authorization = self._report_batch_authorizer(bucket, keys)
                for key in keys:
                    response(key, head=True, authorization=authorization)
                    fetched.add((key, True))

        def read_document(key):
            if detached:
                if (key, False) not in fetched:
                    batch = pending_documents.get(key)
                    if batch is None:
                        raise RuntimeError("Report document was not in an authorized discovery frontier")
                    if batch["authorization"] is None:
                        # Close the batch's DB session before GET/body reads.
                        self._require_report_access_batch(None, bucket, batch["keys"])
                        batch["authorization"] = self._report_batch_authorizer(bucket, batch["keys"])
                    value = response(key, authorization=batch["authorization"])
                    # Read only the requested document, allowing the scanner to
                    # parse/fail before allocating bytes for the next document.
                    documents[key] = consume_document(value, key)
                    fetched.add((key, False))
                    del pending_documents[key]
                    batch["remaining"].remove(key)
                    if not batch["remaining"]:
                        batch["authorization"] = None
                return documents[key]
            return consume_document(response(key), key)

        def require_asset(key):
            if detached:
                if (key, True) not in fetched:
                    raise RuntimeError("Report asset was not in an authorized discovery frontier")
                return
            response(key, head=True)

        try:
            def registered_parent(key):
                if session is None:
                    # A saved parent only pins its own ETag, not its dependency
                    # versions. Inspect its closure afresh for this detached scan.
                    return None
                row = self._registry_query(session, scopes=("artifact",)).filter(
                    generic_instance.json_addl["bucket"].astext == bucket,
                    generic_instance.json_addl["key"].astext == key).first()
                return saved_bundle(normalize_instance_payload(row)) if row is not None else None
            bundle = inspect_bundle(payload["key"], read_document, require_asset, registered_parent,
                                    declared_multiqc=multiqc_candidate(payload),
                                    prepare_batch=prepare_batch if detached else None)
            if not detached:
                for asset in bundle["required_assets"]:
                    self.require_storage_access(bucket, bundle["root_key"] + asset, action="download", session=session)
        except NotMultiQCReport:
            if multiqc_candidate(payload) or payload.get("report_bundle"):
                raise
            return payload
        return {**payload, "report_bundle": bundle}

    def _revalidate_multiqc_inspection(self, session, payload, prepared, observations):
        """Reauthorize and conditionally HEAD the scan before its transaction commits.

        No HTML bodies are downloaded here. S3 cannot participate in the database
        transaction: mutable objects can still change after HEAD, as they could
        after the former in-transaction GET. Retain the inspected ETag and all
        existing delivery-time integrity enforcement; never assert an S3 lock.
        """
        storage = self._require_storage()
        bucket = payload["bucket"]

        keys = list(observations)
        bundle = prepared.get("report_bundle")
        required = {payload["key"]}
        if bundle is not None:
            required.update(bundle["root_key"] + asset for asset in bundle["required_assets"])
        if not required.issubset(observations):
            raise ValueError("Report inspection did not capture every required object")

        for offset in range(0, len(keys), _REPORT_AUTHORIZATION_BATCH_SIZE):
            batch = keys[offset:offset + _REPORT_AUTHORIZATION_BATCH_SIZE]
            self._require_report_access_batch(session, bucket, batch)
            authorization = self._report_batch_authorizer(bucket, batch)
            for key in batch:
                etag, observed_version = observations[key]
                try:
                    with storage_authorization_context(authorization):
                        current = storage.object_response(
                            bucket=bucket, key=key, head=True, if_match=etag,
                            version_id=payload.get("version_id") if key == payload["key"] else None,
                            request_payer=self._request_payer_for_bucket(bucket),
                        )
                except StorageObjectNotFoundError as error:
                    raise HTTPException(409, "Report object disappeared after inspection; retry registration") from error
                except HTTPException as error:
                    if error.status_code == 412:
                        raise HTTPException(409, "Report object changed after inspection; retry registration") from error
                    raise
                if current.get("ETag") != etag or current.get("VersionId") != observed_version:
                    raise HTTPException(409, "Report object changed after inspection; retry registration")
        # Reevaluate policy after the HEADs as well: a revocation during network
        # I/O must not become persisted registration evidence. Like the previous
        # sequential final pass, this is not a lock on concurrent policy writes.
        for offset in range(0, len(keys), _REPORT_AUTHORIZATION_BATCH_SIZE):
            self._require_report_access_batch(
                session, bucket, keys[offset:offset + _REPORT_AUTHORIZATION_BATCH_SIZE]
            )

    def multiqc_registration_candidates(self, *, page=1, limit=100):
        page, limit = max(1, page), max(1, min(limit, 1000))
        with self.backend.session_scope(commit=False) as session:
            query = self._registry_query(session, scopes=("artifact",)).filter(
                generic_instance.json_addl["storage_kind"].astext == "object",
                generic_instance.json_addl["storage_backend"].astext == "s3",
                or_(func.lower(generic_instance.json_addl["key"].astext).like("%.html"),
                    func.lower(generic_instance.json_addl["key"].astext).like("%.htm")))
            rows = query.order_by(generic_instance.euid).offset((page-1)*limit).limit(limit+1).all()
            return {"items": [self._registry_payload(session, row) for row in rows[:limit]],
                    "page": page, "has_more": len(rows) > limit}

    def inspect_multiqc_registration(self, euid):
        with self.backend.session_scope(commit=False) as session:
            record = self._registry_record(session, euid, action="edit")
            payload = normalize_instance_payload(record)
            if not html_candidate(payload):
                raise ValueError("Select an S3 HTML object registration")
            try:
                prepared = self._prepare_multiqc_payload(session, payload)
            except RequiredExternalAssets as error:
                return {"euid": euid, "bundle": None, "blocked_reason": str(error),
                        "required_external_assets": error.assets, "storage_uri": payload.get("storage_uri"),
                        "shares": self.list_shares(limit=2000, target_euid=euid)}
            if not prepared.get("report_bundle"):
                return {"euid": euid, "bundle": None, "classification": "other_html", "shares": []}
            return {"euid": euid, "bundle": prepared["report_bundle"],
                    "location_revision": int(payload.get("location_revision", 1)),
                    "already_registered": saved_bundle(payload) == prepared["report_bundle"],
                    "bundle_digest": self._fingerprint(prepared["report_bundle"]),
                    "shares": self.list_shares(limit=2000, target_euid=euid)}

    def repair_multiqc_registration(self, euid, *, expected_bundle_digest, repair_shares=False):
        with self.backend.session_scope(commit=True) as session:
            record = self._registry_record(session, euid, action="edit", lock=True)
            payload = normalize_instance_payload(record)
            if not html_candidate(payload):
                raise ValueError("Select an S3 HTML object registration")
            bundle = self._prepare_multiqc_payload(session, payload).get("report_bundle")
            if bundle is None:
                raise ValueError("This HTML is not a MultiQC report and needs no bundle repair")
            if expected_bundle_digest != self._fingerprint(bundle):
                raise HTTPException(409, "MultiQC dependencies changed; review the bundle again")
            changed = payload.get("report_bundle") != bundle
            if changed:
                self.backend.update_instance_json(session, record, {"report_bundle": bundle})
                self._registry_event(session, record, "multiqc.bundle.registered")
        result = {"euid": euid, "bundle": bundle, "registration_changed": changed, "shares": []}
        if not repair_shares or bundle["mode"] == "standalone":
            return result
        shares = self.list_shares(limit=2000, target_euid=euid)
        if len(shares) >= 2000:
            raise ValueError("Share enumeration is incomplete; do not silently truncate MultiQC repair")
        for share in shares:
            detail = self.get_share(share.get("share_euid") or share["euid"])
            if not detail.get("can_manage"):
                result["shares"].append({"euid": detail["euid"], "status": "blocked_not_share_manager"})
                continue
            if detail["content_mode"] != "www" or detail["status"] != "active":
                result["shares"].append({"euid": detail["euid"], "status": "unchanged_inactive_or_download"})
                continue
            if len(detail.get("targets", [])) == 1 and detail["report_entrypoint"] != bundle["entrypoint"]:
                result["shares"].append({"euid": detail["euid"], "status": "blocked_entrypoint_migration",
                                        "reason": "Preserving the existing direct report path requires a reviewed entrypoint migration",
                                        "current_entrypoint": detail["report_entrypoint"], "bundle_entrypoint": bundle["entrypoint"]})
                continue
            if detail.get("expiry_policy", {}).get("requires_explicit_review"):
                result["shares"].append({"euid": detail["euid"], "status": "blocked_expiry_policy_review",
                                        "reason": "Existing expiration requires explicit review; repair will not change it"})
                continue
            if detail.get("report_bundles", {}).get(euid) == bundle:
                result["shares"].append({"euid": detail["euid"], "status": "already_repaired"})
                continue
            if detail["include_patterns"] != ["**"] or detail["exclude_patterns"] or any(
                    g["status"] == "active" and (g["include_patterns"] != ["**"] or g["exclude_patterns"])
                    for g in detail["grants"]):
                result["shares"].append({"euid": detail["euid"], "status": "blocked_custom_file_selection",
                    "reason": "Review existing file exclusions/includes before adding report assets"})
                continue
            snapshots = {**detail.get("report_bundles", {}), euid: bundle}
            try:
                updated = self.modify_registry_share(detail["euid"], {"policy_revision": detail["policy_revision"],
                                                           "report_bundles": snapshots})
            except (ValueError, HTTPException) as error:
                result["shares"].append({"euid": detail["euid"], "status": "blocked",
                                        "reason": str(error.detail if isinstance(error, HTTPException) else error)})
            else:
                result["shares"].append({"euid": updated["euid"], "status": "repaired",
                                        "policy_revision": updated["policy_revision"]})
        return result
