"""Recipient manifests and complete-inventory, bounded-memory TAR delivery."""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import tarfile
import tempfile
from datetime import datetime
from urllib.parse import quote

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from dewey_service.audit import authenticated_user_email_context
from dewey_service.registry_access import principal, principal_context
from dewey_service.share_context import require_share_context, share_context_context
from dewey_service.share_gateway import _CHUNK, _reserve, exact_read_authorizer, exact_relative_key
from dewey_service.storage import storage_authorization_context

_LOG = logging.getLogger(__name__)
_MAX_INVENTORY_BYTES = 256 * 1024 * 1024
_MAX_INVENTORY_OBJECTS = 1_000_000


def fetch_path(share_euid: str, path: str = "") -> str:
    root = "/fetch/" + quote(share_euid, safe="")
    return root + ("/" + quote(path, safe="/") if path else "")


def member_path(resolved: dict, item: dict) -> str:
    """One persisted target namespace; names never depend on an S3 location."""
    member = next((m for m in resolved["members"] if m["artifact_euid"] == item["target_euid"]), None)
    if member is None:
        raise HTTPException(409, "Share target changed during inventory")
    relative = (member["filename"] if member["target_kind"] == "artifact_object" else item.get("relative_key") or item["name"])
    exact_relative_key(relative, allow_empty=False)
    if resolved["namespaced"]:
        return item["target_euid"] + "/" + relative
    return relative


def selection(resolved: dict, path: str = "") -> tuple[str | None, str]:
    exact_relative_key(path)
    members = resolved["members"]
    if not resolved["namespaced"] and len(members) == 1:
        member = members[0]
        if member["target_kind"] == "artifact_object":
            if path and path != member["filename"]:
                raise HTTPException(404, "The requested path is outside this share")
            return member["artifact_euid"], ""
        return member["artifact_euid"], path
    if not path:
        return None, ""
    target, _, relative = path.partition("/")
    member = next((m for m in members if m["artifact_euid"] == target), None)
    if member is None:
        raise HTTPException(404, "The requested target is outside this share")
    if member["target_kind"] == "artifact_object":
        if relative and relative != member["filename"]:
            raise HTTPException(404, "The requested path is outside this share")
        relative = ""
    return target, relative


def _pinned_entry(service, resolved: dict, item: dict) -> dict:
    receipt = service.authorize_share_object(resolved["share_euid"], item["target_euid"],
        item["relative_key"], action="gateway")
    member = next((m for m in resolved["members"] if m["artifact_euid"] == item["target_euid"]), None)
    if (receipt["policy_revision"] != resolved["policy_revision"] or member is None
            or receipt["location_revision"] != member["location_revision"]):
        raise HTTPException(409, "Share changed while enumerating; restart the inventory")
    with storage_authorization_context(exact_read_authorizer(receipt)):
        metadata = service._require_storage().object_response(bucket=receipt["bucket"], key=receipt["key"],
            version_id=receipt.get("version_id"), head=True,
            request_payer=service._request_payer_for_bucket(receipt["bucket"]))
    if not metadata.get("ETag"):
        raise HTTPException(503, "Object storage did not supply an inventory validator")
    path = member_path(resolved, item)
    modified = metadata.get("LastModified")
    return {"path": path, "target_euid": item["target_euid"], "relative_key": item["relative_key"],
        "size": int(metadata["ContentLength"]), "etag": metadata["ETag"],
        "version_id": metadata.get("VersionId") or receipt.get("version_id"),
        "last_modified": modified.isoformat() if modified else None,
        "location_revision": receipt["location_revision"], "receipt": receipt,
        "fetch_path": fetch_path(resolved["share_euid"], path) + ("?download=true" if path.endswith("/") else "")}


def manifest_page(service, resolved: dict, *, path: str = "", limit: int = 200,
                  continuation_token: str | None = None) -> dict:
    require_share_context()
    target, prefix = selection(resolved, path)
    page = service.list_share_contents(resolved["share_euid"], target_euid=target, prefix=prefix,
        limit=limit, continuation_token=continuation_token)
    entries = [_pinned_entry(service, resolved, item) for item in page["items"]]
    for entry in entries:
        del entry["receipt"]
    more = page.get("continuation_token")
    if bool(page.get("incomplete")) != bool(more):
        raise HTTPException(502, "Share inventory pagination was inconsistent")
    service.append_share_event(resolved["share_euid"], event_type="manifest_page", decision="allow",
        details={"policy_revision": resolved["policy_revision"], "object_count": len(entries),
            "total_bytes": sum(e["size"] for e in entries), "inventory_complete": not bool(more), "format": "manifest"})
    return {"share_euid": resolved["share_euid"], "policy_revision": resolved["policy_revision"],
        "items": entries, "continuation_token": more, "incomplete": bool(more),
        "page_complete": True, "enumeration_complete": not bool(more),
        "consistency": "live-prefix; each listed object is version/ETag pinned; follow every continuation token"}


class Inventory:
    """Disk-backed metadata only. No file contents or credentials are persisted."""
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="dewey-share-inventory-")
        self.db = sqlite3.connect(self.directory.name + "/inventory.sqlite", check_same_thread=False)
        self.db.execute("CREATE TABLE entries (seq INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")
        self.count = self.total_bytes = self.metadata_bytes = self.tar_bytes = 0
        self.digest = hashlib.sha256()
        self.closed = False

    def append(self, entry: dict):
        path = exact_relative_key(entry["path"], allow_empty=False)
        if any(not part for part in path.rstrip("/").split("/")):
            raise HTTPException(409, "Empty path segments cannot be represented safely in a TAR archive")
        if path.endswith("/") and entry["size"]:
            raise HTTPException(409, "Nonempty objects ending in a slash cannot be represented in a TAR archive")
        # TAR extraction must not turn a file into another entry's parent.
        parts = path.rstrip("/").split("/")
        if path.endswith("/") and self.db.execute("SELECT 1 FROM entries WHERE path = ?", (path.rstrip("/"),)).fetchone():
            raise HTTPException(409, "Share paths collide as files and directories; download files individually")
        for end in range(1, len(parts)):
            ancestor = "/".join(parts[:end])
            if self.db.execute("SELECT 1 FROM entries WHERE path = ?", (ancestor,)).fetchone():
                raise HTTPException(409, "Share paths collide as files and directories; download files individually")
        if not path.endswith("/") and self.db.execute(
                "SELECT 1 FROM entries WHERE path >= ? AND path < ? LIMIT 1", (path + "/", path + "0")).fetchone():
            raise HTTPException(409, "Share paths collide as files and directories; download files individually")
        payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        length = len(payload.encode("utf-8"))
        if self.count >= _MAX_INVENTORY_OBJECTS or self.metadata_bytes + length > _MAX_INVENTORY_BYTES:
            raise HTTPException(413, "Archive inventory exceeds server capacity; use the paginated manifest and recursive client")
        try:
            self.db.execute("INSERT INTO entries(path,payload) VALUES (?,?)", (path, payload))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Share contains duplicate archive paths") from exc
        self.count += 1
        self.total_bytes += entry["size"]
        self.metadata_bytes += length
        self.digest.update(payload.encode("utf-8") + b"\n")
        self.tar_bytes += len(_tar_header(entry)) + ((entry["size"] + 511) // 512) * 512

    def entries(self):
        self.db.commit()
        for (payload,) in self.db.execute("SELECT payload FROM entries ORDER BY seq"):
            yield json.loads(payload)

    def close(self):
        if not self.closed:
            self.closed = True
            self.db.close()
            self.directory.cleanup()


def _tar_header(entry: dict) -> bytes:
    header = tarfile.TarInfo(entry["path"])
    header.mode = 0o755 if entry["path"].endswith("/") else 0o644
    header.size = entry["size"]
    if entry["path"].endswith("/"):
        header.type = tarfile.DIRTYPE
    if entry.get("last_modified"):
        header.mtime = int(datetime.fromisoformat(entry["last_modified"]).timestamp())
    return header.tobuf(format=tarfile.PAX_FORMAT, encoding="utf-8", errors="strict")


def complete_inventory(service, resolved: dict, *, path: str = "") -> Inventory:
    target, prefix = selection(resolved, path)
    inventory = Inventory()
    try:
        token = None
        while True:
            page = service.list_share_contents(resolved["share_euid"], target_euid=target,
                prefix=prefix, limit=200, continuation_token=token)
            for item in page["items"]:
                inventory.append(_pinned_entry(service, resolved, item))
            next_token = page.get("continuation_token")
            if bool(page.get("incomplete")) != bool(next_token) or (next_token and next_token == token):
                raise HTTPException(502, "Share inventory pagination was inconsistent")
            if not next_token:
                break
            token = next_token
        current = service.resolve_share_identifier(resolved["share_euid"])
        if current["policy_revision"] != resolved["policy_revision"]:
            raise HTTPException(409, "Share changed during inventory; restart the archive")
        return inventory
    except BaseException:
        inventory.close()
        raise


class AuditedArchiveResponse(StreamingResponse):
    def __init__(self, *, service, resolved, inventory, release, actor, context, settings, head=False):
        self.service, self.resolved, self.inventory = service, resolved, inventory
        self.release, self.actor, self.context = release, actor, context
        self.bytes_served = self.members_completed = 0
        self.completed = False
        self.current_body = None
        self.head = head
        self.settings = settings
        async def chunks():
            if head:
                return
            iterator = inventory.entries()
            while True:
                entry = await run_in_threadpool(next, iterator, None)
                if entry is None:
                    break
                metadata = await run_in_threadpool(self._open_member, entry)
                self.current_body = metadata.get("Body")
                try:
                    yield _tar_header(entry)
                    remaining = entry["size"]
                    while remaining:
                        chunk = await run_in_threadpool(self.current_body.read, min(_CHUNK, remaining))
                        if not chunk:
                            raise RuntimeError("Archive source ended before its pinned length")
                        remaining -= len(chunk)
                        yield chunk
                    if self.current_body is not None and await run_in_threadpool(self.current_body.read, 1):
                        raise RuntimeError("Archive source exceeded its pinned length")
                    if entry["size"] % 512:
                        yield b"\0" * (512 - entry["size"] % 512)
                    self.members_completed += 1
                finally:
                    if self.current_body is not None:
                        self.current_body.close()
                        self.current_body = None
            yield b"\0" * 1024
        headers = {"Content-Type": "application/x-tar", "Content-Length": str(inventory.tar_bytes + 1024),
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(resolved['share_euid'], safe='')}.tar",
            "Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox; default-src 'none'", "Accept-Ranges": "none",
            "X-Dewey-Inventory-SHA256": inventory.digest.hexdigest(), "X-Dewey-Object-Count": str(inventory.count)}
        super().__init__(chunks(), headers=headers)

    def _open_member(self, entry):
        from dewey_service.recipient_identity import verify_recipient_binding
        identity = verify_recipient_binding(self.settings, grant_id=self.actor.identity_grant_id,
            revision=self.actor.identity_revision)
        if (identity.get("canonical_user_id") != self.actor.subject or identity.get("email") != self.actor.email
                or identity.get("email_verified") is not True):
            raise HTTPException(401, "Download identity changed; sign in again")
        with principal_context(self.actor), share_context_context(self.context), authenticated_user_email_context(self.actor.email):
            receipt = self.service.authorize_share_object(self.resolved["share_euid"], entry["target_euid"],
                entry["relative_key"], action="gateway")
            previous = entry["receipt"]
            if (receipt["policy_revision"] != self.resolved["policy_revision"]
                    or any(receipt.get(k) != previous.get(k) for k in ("bucket", "key", "version_id", "location_revision"))):
                raise HTTPException(409, "Share or source changed during archive delivery; restart the download")
            with storage_authorization_context(exact_read_authorizer(receipt)):
                result = self.service._require_storage().object_response(bucket=receipt["bucket"], key=receipt["key"],
                    version_id=entry["version_id"], if_match=entry["etag"],
                    request_payer=self.service._request_payer_for_bucket(receipt["bucket"]))
            if int(result["ContentLength"]) != entry["size"] or result.get("ETag") != entry["etag"]:
                if result.get("Body") is not None:
                    result["Body"].close()
                raise HTTPException(409, "Archive source no longer matches its inventory")
            return result

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
                if self.current_body is not None:
                    self.current_body.close()
            except Exception:
                close_failed = True
                _LOG.exception("Could not close archive source")
            finally:
                self.inventory.close()
                self.release()
            success = self.completed and not close_failed
            try:
                with principal_context(self.actor), share_context_context(self.context), authenticated_user_email_context(self.actor.email):
                    self.service.append_share_event(self.resolved["share_euid"],
                        event_type="archive_completed" if success else "archive_interrupted",
                        decision="completed" if success else "unknown", details={
                            "policy_revision": self.resolved["policy_revision"], "format": "tar",
                            "method": "HEAD" if self.head else "GET", "server_bytes_sent": self.bytes_served,
                            "response_completion_observed": self.completed, "download_completion_observed": False,
                            "outcome": "close_failure" if close_failed else "completed" if success else "disconnect_or_failure",
                            "archive_members_completed": self.members_completed,
                            "object_count": self.inventory.count, "total_bytes": self.inventory.total_bytes,
                            "manifest_sha256": self.inventory.digest.hexdigest(), "inventory_complete": True})
            except Exception:
                _LOG.exception("Could not persist archive outcome event")


def archive_delivery(request, service, resolved: dict, *, path: str = ""):
    context, actor = require_share_context(), principal()
    if request.headers.get("range"):
        raise HTTPException(416, "TAR downloads restart from the beginning; resume individual files using the manifest",
            headers={"Accept-Ranges": "none"})
    if any(request.headers.get(name) for name in ("if-match", "if-none-match", "if-range", "if-modified-since", "if-unmodified-since")):
        raise HTTPException(400, "Archive conditions are unsupported; use individual file validators")
    release = _reserve(actor.subject)
    inventory = None
    try:
        inventory = complete_inventory(service, resolved, path=path)
        service.append_share_event(resolved["share_euid"], event_type="archive_started", decision="allow",
            details={"policy_revision": resolved["policy_revision"], "format": "tar", "method": request.method,
                "object_count": inventory.count, "total_bytes": inventory.total_bytes,
                "manifest_sha256": inventory.digest.hexdigest(), "inventory_complete": True})
        return AuditedArchiveResponse(service=service, resolved=resolved, inventory=inventory,
            release=release, actor=actor, context=context, settings=request.app.state.settings, head=request.method == "HEAD")
    except BaseException:
        if inventory is not None:
            inventory.close()
        release()
        raise
