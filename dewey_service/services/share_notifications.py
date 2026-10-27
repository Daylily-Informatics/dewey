"""Durable request-bound notifications for explicit share email grants."""
from datetime import datetime, timezone
from urllib.parse import urlsplit, quote
import os
import requests
from fastapi import HTTPException
from dewey_service.registry_access import OPERATION_TEMPLATE, principal
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso


class ShareNotificationMixin:
    def _notification_rows(self, session, share):
        return [r for r in self._share_related(session, share,
                    relationship="has_storage_operation", kind="storage_operation")
                if normalize_instance_payload(r).get("operation") == "share_notification"]

    def _explicit_notification_emails(self, grants, denied):
        now = datetime.now(timezone.utc)
        return {g["recipient"].strip().lower() for g in grants
                if g["recipient_type"] == "email" and g.get("status", "active") == "active"
                and g["recipient"].strip().lower() not in denied
                and (g.get("expires_at") is None or
                     datetime.fromisoformat(g["expires_at"].replace("Z", "+00:00")) > now)}

    def _prepare_share_notifications(self, session, share, grants, previous=()):
        data = normalize_instance_payload(share)
        current = self._explicit_notification_emails(grants, data["denied_emails"])
        # Removal cancels unsent intent even when re-addition occurs in a later request.
        for row in self._notification_rows(session, share):
            item = normalize_instance_payload(row)
            if item["status"] == "pending" and item["recipient_email"] not in current:
                self.backend.update_instance_json(session, row, {"status": "cancelled", "completed_at": utc_now_iso()})
        emails = current - set(previous)
        for email in sorted(emails):
            row = self.backend.create_instance(session, template_code=OPERATION_TEMPLATE,
                name="Share recipient notification", json_addl={
                    "operation": "share_notification", "status": "pending",
                    "actor": principal().subject, "recipient_email": email,
                    "policy_revision": data["policy_revision"], "created_at": utc_now_iso(),
                    "share_name": data.get("name") or "Shared report",
                    "sharer_email": data["owner_email"],
                    "expires_at": data["expires_at"],
                    "report_entrypoint": data.get("report_entrypoint") if data["content_mode"] == "www" else None})
            self.backend.create_lineage(session, parent=share, child=row,
                                        relationship_type="has_storage_operation")

    def _share_notification_status(self, session, share):
        return [{"notification_euid": r.euid,
                 **{k: v for k, v in normalize_instance_payload(r).items()
                    if k in {"recipient_email", "status", "policy_revision", "created_at",
                             "started_at", "completed_at", "delivery", "last_error"}}}
                for r in self._notification_rows(session, share)]

    def _dispatch_share_notifications(self, share_euid):
        from dewey_service.settings import get_settings
        settings = get_settings()
        endpoint = os.environ.get("LSMC_AUTH_BROKER_SHARE_NOTIFICATION_URL", "")
        parsed = urlsplit(endpoint)
        origin = urlsplit(settings.external_broker_callback_url)
        configured = (parsed.scheme == "https" and parsed.netloc and not parsed.username
                      and not parsed.password and not parsed.fragment and not parsed.query
                      and origin.scheme == "https" and origin.netloc and not origin.username
                      and not origin.password and settings.external_broker_service_token)
        with self.backend.session_scope(commit=True) as session:
            share = self._canonical_share(session, share_euid, lock=True)
            if not self._registry_share_manager(session, share):
                raise HTTPException(403, "Share management permission required for notification dispatch")
            data = normalize_instance_payload(share)
            rows = self._notification_rows(session, share)
            operations = []
            for row in rows:
                item = normalize_instance_payload(row)
                if item["status"] != "pending":
                    continue
                if not configured:
                    self.backend.update_instance_json(session, row, {
                        "last_error": "Explicit broker notification URL/credential is required"})
                    continue
                grants = [normalize_instance_payload(g) for g in self._share_grants(session, share)
                          if normalize_instance_payload(g).get("policy_revision") == data["policy_revision"]]
                deadline = data["expires_at"]
                valid = (data["status"] == "active" and
                         (deadline is None or datetime.fromisoformat(deadline.replace("Z", "+00:00")) > datetime.now(timezone.utc)))
                if not valid or item["recipient_email"] not in self._explicit_notification_emails(grants, data["denied_emails"]):
                    self.backend.update_instance_json(session, row, {"status": "cancelled"})
                    continue
                # Capture current metadata once with the durable submission fence.
                # Per-grant expiry may be earlier than the containing share.
                deadlines = [g["expires_at"] for g in grants
                             if g["recipient_type"] == "email"
                             and g["recipient"].strip().lower() == item["recipient_email"]
                             and g.get("status", "active") == "active" and g.get("expires_at")]
                if deadline:
                    deadlines.append(deadline)
                effective_expiry = min(deadlines, key=lambda d: datetime.fromisoformat(d.replace("Z", "+00:00"))) if deadlines else None
                item.update(share_name=data.get("name") or "Shared report",
                            sharer_email=data["owner_email"], expires_at=effective_expiry,
                            report_entrypoint=data.get("report_entrypoint") if data["content_mode"] == "www" else None)
                # A crash after commit is uncertain, never an automatic resend.
                self.backend.update_instance_json(session, row, {
                    **item, "status": "uncertain", "started_at": utc_now_iso(), "last_error": None})
                operations.append((row.euid, item))
        for operation_euid, item in operations:
            url = f"{origin.scheme}://{origin.netloc}/fetch/{share_euid}"
            if item.get("report_entrypoint"):
                url += "/" + quote(item["report_entrypoint"], safe="/")
            state, delivery = "uncertain", None
            try:
                result = requests.post(endpoint, json={
                    "notification_id": operation_euid, "recipient_email": item["recipient_email"],
                    "share_ref_euid": share_euid, "share_url": url,
                    "share_name": item["share_name"], "sharer_email": item["sharer_email"],
                    "expires_at": item["expires_at"]},
                    headers={"Authorization": "Bearer " + settings.external_broker_service_token,
                             "x-lsmc-service-id": "dewey"}, timeout=(10, 30),
                    allow_redirects=False, verify=settings.external_broker_ca_bundle or True)
                body = result.json()
                notice = body.get("notification", {}) if isinstance(body, dict) else {}
                if (notice.get("notification_id") == operation_euid
                        and notice.get("status") in {"accepted", "failed", "uncertain", "captured"}):
                    state, delivery = notice["status"], notice.get("delivery")
                elif 400 <= result.status_code < 500:
                    state = "failed"
            except (requests.RequestException, ValueError, AttributeError):
                pass
            with self.backend.session_scope(commit=True) as session:
                # Dispatch is authorized by share management, not original creator.
                share = self._canonical_share(session, share_euid, lock=True)
                row = next((r for r in self._notification_rows(session, share)
                            if r.euid == operation_euid), None)
                if row is None:
                    raise ValueError("Notification operation is not bound to this share")
                self.backend.update_instance_json(session, row, {"status": state,
                    "delivery": delivery, "completed_at": utc_now_iso()})
        with self.backend.session_scope(commit=False) as session:
            share = self._canonical_share(session, share_euid)
            return self._share_notification_status(session, share)
