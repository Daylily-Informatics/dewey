"""Authenticated, bounded S3 delivery with immutable outcome evidence."""
from __future__ import annotations

import logging
import re
import threading
from collections import Counter
from datetime import timezone
from email.utils import parsedate_to_datetime, format_datetime
from urllib.parse import quote

from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field

from dewey_service.registry_access import principal, principal_context
from dewey_service.share_context import require_share_context, share_context_context
from dewey_service.storage import storage_authorization_context, StorageObjectNotFoundError, StoragePermissionError
from dewey_service.audit import authenticated_user_email_context

_LOCK = threading.Lock()
_ACTIVE: Counter = Counter()
_CHUNK = 256 * 1024
_LOG = logging.getLogger(__name__)


class PresignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_euid: str
    relative_key: str = ""
    ttl_seconds: int = Field(default=900, ge=1, le=3600)


def exact_relative_key(value: str, *, allow_empty: bool = True) -> str:
    """Starlette already decoded URL input once. Never normalize/decode it again."""
    if (not isinstance(value, str) or (not value and not allow_empty) or value.startswith("/")
            or "\\" in value or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(part in {".", ".."} for part in value.split("/"))):
        raise HTTPException(400, "Invalid exact relative key")
    return value


def exact_read_authorizer(receipt: dict):
    def authorize(bucket, key, *, action):
        require_share_context()
        if bucket != receipt["bucket"] or key != receipt["key"] or action not in {"download", "metadata"}:
            raise HTTPException(403, "Storage request exceeds the canonical authorization receipt")
    return authorize


def _date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise HTTPException(400, "Invalid HTTP conditional date")


def _reserve(subject):
    with _LOCK:
        if sum(_ACTIVE.values()) >= 8 or _ACTIVE[subject] >= 2:
            raise HTTPException(429, "Download capacity reached", headers={"Retry-After": "5"})
        _ACTIVE[subject] += 1
    def release():
        with _LOCK:
            _ACTIVE[subject] -= 1
            if not _ACTIVE[subject]:
                del _ACTIVE[subject]
    return release


class AuditedObjectResponse(StreamingResponse):
    """Close resources even if response headers or the stream fail to send."""
    def __init__(self, *, body, metadata, headers, status_code, service, receipt, actor, context, release):
        self.body_stream, self.release = body, release
        self.service, self.receipt, self.actor, self.context = service, receipt, actor, context
        self.bytes_served, self.completed = 0, False
        async def chunks():
            if body is not None:
                while True:
                    chunk = await run_in_threadpool(body.read, _CHUNK)
                    if not chunk:
                        break
                    yield chunk
        super().__init__(chunks(), status_code=status_code, headers=headers)

    async def __call__(self, scope, receive, send):
        async def observed_send(message):
            await send(message)
            if message["type"] == "http.response.body":
                self.bytes_served += len(message.get("body", b""))
                if not message.get("more_body", False):
                    self.completed = True
        try:
            await super().__call__(scope, receive, observed_send)
        finally:
            close_failed = False
            try:
                if self.body_stream is not None:
                    self.body_stream.close()
            except Exception:
                close_failed = True
                _LOG.error("Object response close failed")
            finally:
                self.release()
            success = self.completed and not close_failed
            event = "gateway_response_completed" if success else "gateway_disconnect_or_failure"
            try:
                # The receipt fixes admission for this response; event append is
                # independent of any policy change while bytes were in flight.
                with principal_context(self.actor), share_context_context(self.context), authenticated_user_email_context(self.actor.email):
                    self.service.append_share_event(self.receipt["share_euid"], event_type=event,
                        decision="completed" if success else "unknown", grant_euid=self.receipt["grant_euid"],
                        target_euid=self.receipt["target_euid"], details={"server_bytes_sent": self.bytes_served,
                            "download_completion_observed": False, "response_completion_observed": self.completed,
                            "outcome": "close_failure" if close_failed else "completed" if self.completed else "disconnect_or_failure",
                            "key": self.receipt["key"], "version_id": self.receipt.get("version_id"),
                            "policy_revision": self.receipt["policy_revision"]})
            except Exception:
                _LOG.exception("Could not persist gateway outcome event")


def object_delivery(request: Request, service, receipt: dict, *, inline: bool = False,
                    extra_headers: dict | None = None):
    context = require_share_context()
    actor = principal()
    release = None
    body = None
    try:
        release = _reserve(actor.subject)
        storage = service._require_storage()
        request_payer = service._request_payer_for_bucket(receipt["bucket"])
        # HTTP Range applies to GET; HEAD reports the full selected object's
        # metadata without opening a body or returning a partial length.
        ranges = request.headers.getlist("range") if request.method == "GET" else []
        range_value = ranges[0] if ranges else None
        if len(ranges) > 1 or (range_value and not re.fullmatch(r"bytes=(?:\d+-\d*|-\d+)", range_value)):
            raise HTTPException(416, "Only one bytes range is supported")
        if range_value and range_value.startswith("bytes=-") and int(range_value[7:]) == 0:
            raise HTTPException(416, "Invalid byte range")
        if range_value and "-" in range_value[6:] and not range_value.startswith("bytes=-"):
            first, last = range_value[6:].split("-")
            if last and int(first) > int(last):
                raise HTTPException(416, "Invalid byte range")
        if_match = request.headers.get("if-match")
        if_none_match = request.headers.get("if-none-match")
        modified = _date(request.headers.get("if-modified-since")) if not if_none_match else None
        unmodified = _date(request.headers.get("if-unmodified-since")) if not if_match else None
        with storage_authorization_context(exact_read_authorizer(receipt)):
            if range_value and request.headers.get("if-range"):
                head = storage.object_response(bucket=receipt["bucket"], key=receipt["key"],
                    version_id=receipt.get("version_id"), head=True, if_match=if_match,
                    if_none_match=if_none_match, if_modified_since=modified, if_unmodified_since=unmodified,
                    request_payer=request_payer)
                validator = request.headers["if-range"]
                if validator.startswith('"'):
                    matched = validator == head.get("ETag")
                elif validator.startswith("W/"):
                    matched = False
                else:
                    matched = head.get("LastModified") is not None and head["LastModified"] <= _date(validator)
                if not matched:
                    range_value = None
                # Pin the object seen by HEAD, even when If-Range chooses full bytes.
                receipt = {**receipt, "version_id": head.get("VersionId") or receipt.get("version_id")}
                if not head.get("ETag"):
                    raise HTTPException(503, "S3 did not supply a validator for the resumed object")
                if_match = head["ETag"]
            metadata = storage.object_response(bucket=receipt["bucket"], key=receipt["key"],
                version_id=receipt.get("version_id"), head=request.method == "HEAD", byte_range=range_value,
                if_match=if_match, if_none_match=if_none_match, if_modified_since=modified, if_unmodified_since=unmodified,
                request_payer=request_payer)
        body = metadata.get("Body")
        receipt = {**receipt, "version_id": metadata.get("VersionId") or receipt.get("version_id")}
        filename = receipt["key"].rsplit("/", 1)[-1]
        ascii_name = re.sub(r'[^A-Za-z0-9._ -]', '_', filename)[:180] or "download"
        headers = {"Cache-Control": "no-store", "Accept-Ranges": "bytes", "Referrer-Policy": "no-referrer",
                   "X-Content-Type-Options": "nosniff", "Content-Type": metadata.get("ContentType") or "application/octet-stream",
                   "Content-Length": str(metadata["ContentLength"])}
        if not inline:
            headers["Content-Disposition"] = f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename, safe="")}'
            headers["Content-Security-Policy"] = "sandbox; default-src 'none'"
        if metadata.get("ETag"):
            headers["ETag"] = metadata["ETag"]
        if metadata.get("LastModified"):
            headers["Last-Modified"] = format_datetime(metadata["LastModified"].astimezone(timezone.utc), usegmt=True)
        if metadata.get("ContentRange"):
            headers["Content-Range"] = metadata["ContentRange"]
        headers.update(extra_headers or {})
        status = 206 if metadata.get("ContentRange") else 200
        service.append_share_event(receipt["share_euid"], event_type="gateway_response_started", decision="allow",
            grant_euid=receipt["grant_euid"], target_euid=receipt["target_euid"], details={
                "key": receipt["key"], "version_id": receipt.get("version_id"), "etag": metadata.get("ETag"),
                "method": request.method, "status_code": status, "range": range_value,
                "policy_revision": receipt["policy_revision"], "inline_report": inline})
        return AuditedObjectResponse(body=body, metadata=metadata, headers=headers, status_code=status,
            service=service, receipt=receipt, actor=actor, context=context, release=release)
    except Exception as exc:
        close_failed = False
        try:
            if body is not None:
                body.close()
        except Exception:
            close_failed = True
            _LOG.error("Object setup close failed")
        finally:
            if release is not None:
                release()
        status = (exc.status_code if isinstance(exc, HTTPException) else
                  404 if isinstance(exc, StorageObjectNotFoundError) else
                  403 if isinstance(exc, StoragePermissionError) else 502)
        service.append_share_event(receipt["share_euid"], event_type="gateway_condition_result" if status == 304 else "gateway_setup_failed",
            decision="not_modified" if status == 304 else "failed",
            grant_euid=receipt["grant_euid"], target_euid=receipt["target_euid"], details={
                "key": receipt["key"], "version_id": receipt.get("version_id"), "status_code": status,
                "method": request.method, "server_bytes_sent": 0,
                "outcome": "close_failure" if close_failed else "not_modified" if status == 304 else "setup_failed",
                "policy_revision": receipt["policy_revision"]})
        if isinstance(exc, StorageObjectNotFoundError):
            raise HTTPException(404, "Object not available") from exc
        if isinstance(exc, StoragePermissionError):
            raise HTTPException(403, "Object storage access denied") from exc
        if isinstance(exc, HTTPException) and exc.status_code == 304:
            return Response(status_code=304, headers={"Cache-Control": "no-store", **(exc.headers or {})})
        raise


def attach_share_gateway(app, router, service):
    @app.api_route("/shares/{share_euid}/files/{target_euid}", methods=["GET", "HEAD"], tags=["Managed sharing"])
    def share_file(share_euid: str, target_euid: str, request: Request, relative_key: str = ""):
        require_share_context()
        exact_relative_key(relative_key)
        receipt = service.authorize_share_object(share_euid, target_euid, relative_key, action="gateway")
        return object_delivery(request, service, receipt)

    @router.post("/registry/shares/{share_euid}/presign", tags=["Managed sharing"])
    def share_presign(share_euid: str, body: PresignRequest):
        require_share_context()
        exact_relative_key(body.relative_key)
        return service.presign_share_object(share_euid, body.target_euid,
            relative_key=body.relative_key, ttl_seconds=body.ttl_seconds)
