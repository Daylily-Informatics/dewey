"""Validated MultiQC registration and explicitly reviewed existing-share repair."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, or_
from daylily_tapdb import generic_instance

from dewey_service.multiqc_bundle import MAX_DOCUMENT_BYTES, NotMultiQCReport, html_candidate, inspect_bundle, multiqc_candidate, saved_bundle
from dewey_service.storage import StorageObjectNotFoundError, storage_authorization_context
from dewey_service.tapdb_backend import normalize_instance_payload


class ReportBundleServiceMixin:
    def _prepare_multiqc_payload(self, session, payload):
        if not html_candidate(payload):
            return payload
        storage = self._require_storage()
        bucket = payload["bucket"]

        def authorize(bucket_name, key, action):
            self.require_storage_access(bucket_name, key, action=action, session=session)

        def response(key, *, head=False):
            self.require_storage_access(bucket, key, action="download", session=session)
            try:
                with storage_authorization_context(authorize):
                    return storage.object_response(bucket=bucket, key=key, head=head,
                        version_id=payload.get("version_id") if key == payload["key"] else None,
                        request_payer=self._request_payer_for_bucket(bucket))
            except StorageObjectNotFoundError as error:
                raise ValueError("MultiQC bundle is incomplete; missing asset: " + key) from error

        def read_document(key):
            value = response(key)
            body = value["Body"]
            try:
                content = body.read(MAX_DOCUMENT_BYTES + 1)
            finally:
                body.close()
            return content, value.get("ETag")

        try:
            bundle = inspect_bundle(payload["key"], read_document, lambda key: response(key, head=True))
        except NotMultiQCReport:
            if multiqc_candidate(payload) or payload.get("report_bundle"):
                raise
            return payload
        return {**payload, "report_bundle": bundle}

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
            prepared = self._prepare_multiqc_payload(session, payload)
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
