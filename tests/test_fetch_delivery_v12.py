"""Changed-code recipient delivery contracts; no AWS, broker or database calls."""
from __future__ import annotations

import asyncio
import hashlib
import io
import tarfile
from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from dewey_service.fetch import attach_fetch_routes
from dewey_service.registry_access import Principal, principal_context
from dewey_service.share_context import share_context_context
from dewey_service.share_exports import (AuditedArchiveResponse, Inventory, complete_inventory,
    member_path, selection)


ACTOR = Principal(subject="recipient-fixture", email="recipient@example.test", roles=("READ_ONLY",),
    identity_grant_id="grant-fixture", identity_revision=1,
    identity_expires_at="2099-01-01T00:00:00+00:00", email_verified=True, recipient_only=True)
CONTEXT = {"trusted_tailnet": True, "managed_origin": True, "request_id": "request-fixture"}


class Storage:
    def __init__(self, objects):
        self.objects = dict(objects)
        self.calls = []
        self.bodies = []

    def object_response(self, **kwargs):
        self.calls.append(kwargs)
        key = kwargs["key"]
        if key not in self.objects:
            raise HTTPException(404, "Object unavailable")
        data = self.objects[key]
        etag = '"' + hashlib.sha256(data).hexdigest() + '"'
        if kwargs.get("if_match") and kwargs["if_match"] != etag:
            raise HTTPException(412, "Source changed")
        if kwargs.get("if_none_match") == etag:
            raise HTTPException(304, "Not modified")
        result = {"ETag": etag, "ContentLength": len(data), "ContentType": "application/octet-stream",
            "VersionId": "version-fixture", "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc)}
        if kwargs.get("byte_range"):
            first, last = kwargs["byte_range"][6:].split("-")
            start = int(first) if first else max(0, len(data) - int(last))
            end = min(int(last), len(data) - 1) if first and last else len(data) - 1
            if start >= len(data):
                raise HTTPException(416, "Invalid range")
            result["ContentRange"] = f"bytes {start}-{end}/{len(data)}"
            data = data[start:end + 1]
            result["ContentLength"] = len(data)
        if not kwargs.get("head"):
            body = io.BytesIO(data)
            self.bodies.append(body)
            result["Body"] = body
        return result


class Service:
    def __init__(self, objects=None):
        self.storage = Storage(objects or {"source/file.txt": b"contents"})
        self.events = []
        self.revoked = False
        self.revision = 1
        self.location_revision = 1
        self.resolved = {"share_euid": "share-fixture", "euid": "share-fixture", "name": "Fixture files",
            "fetch_path": "/fetch/share-fixture", "policy_revision": 1, "content_mode": "download",
            "expires_at": None, "namespaced": False, "report_entrypoint": None, "report_bundle_root": "",
            "members": [{"artifact_euid": "target-fixture", "target_kind": "artifact_prefix", "bucket": "bucket-fixture",
                "key": "source/", "version_id": None, "filename": "", "location_revision": 1}]}

    def resolve_share_identifier(self, identifier):
        if self.revoked:
            raise HTTPException(403, "Share revoked")
        if identifier not in {"share-fixture", "friendly-fixture"}:
            raise HTTPException(404, "Share unavailable")
        return {**self.resolved, "policy_revision": self.revision}

    def resolve_share_fetch(self, identifier, relative_path=""):
        resolved = self.resolve_share_identifier(identifier)
        target, relative = selection(resolved, relative_path)
        return self.authorize_share_object(resolved["share_euid"], target, relative)

    def authorize_share_object(self, share, target, relative, action="gateway"):
        self.resolve_share_identifier(share)
        member = next((m for m in self.resolved["members"] if m["artifact_euid"] == target), None)
        if member is None:
            raise HTTPException(403, "Target unavailable")
        key = member["key"] + relative if member["target_kind"] == "artifact_prefix" else member["key"]
        return {"share_euid": share, "target_euid": target, "grant_euid": "recipient-grant-fixture",
            "bucket": member["bucket"], "key": key, "version_id": None, "relative_key": relative,
            "filename": key.rsplit("/", 1)[-1], "expires_at": None, "policy_revision": self.revision,
            "location_revision": self.location_revision, "content_mode": self.resolved["content_mode"]}

    def list_share_contents(self, share, *, target_euid=None, prefix="", limit=200, continuation_token=None):
        self.resolve_share_identifier(share)
        rows = [{"target_euid": "target-fixture", "name": key[7:], "relative_key": key[7:], "size": len(data)}
            for key, data in sorted(self.storage.objects.items()) if key.startswith("source/" + prefix)]
        start = int(continuation_token or 0)
        page = rows[start:start + limit]
        more = start + limit < len(rows)
        return {"items": page, "continuation_token": str(start + limit) if more else None, "incomplete": more}

    def _require_storage(self):
        return self.storage

    def _request_payer_for_bucket(self, bucket):
        return None

    def append_share_event(self, share, **event):
        self.events.append(event)


@pytest.fixture
def delivery(monkeypatch):
    import dewey_service.fetch as fetch_module
    import dewey_service.recipient_identity as identity_module
    service = Service()
    app = FastAPI()
    app.state.settings = SimpleNamespace(share_application_origin="https://dewey.example.test",
        share_content_host_suffix="content.example.test", share_session_generation="generation-fixture")
    app.state.authenticated = True
    app.state.actor = ACTOR
    monkeypatch.setattr(fetch_module, "require_share_ingress", lambda request: None)
    monkeypatch.setattr(identity_module, "verify_recipient_binding", lambda *args, **kwargs: {
        "canonical_user_id": ACTOR.subject, "email": ACTOR.email, "email_verified": True,
        "grant_id": ACTOR.identity_grant_id, "revision": 1, "expires_at": ACTOR.identity_expires_at, "kind": "share"})

    @app.middleware("http")
    async def identity(request, call_next):
        with principal_context(app.state.actor if app.state.authenticated else None), share_context_context(CONTEXT):
            return await call_next(request)

    attach_fetch_routes(app, service)
    with TestClient(app, base_url="https://dewey.example.test") as client:
        yield client, service, app


def test_browser_deep_return_and_machine_unauthorized(delivery):
    client, service, app = delivery
    app.state.authenticated = False
    response = client.get("/fetch/friendly-fixture/sub/report.html?download=true", headers={"Accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 303
    assert parse_qs(urlsplit(response.headers["location"]).query)["next"] == ["/fetch/friendly-fixture/sub/report.html?download=true"]
    machine = client.get("/fetch/share-fixture/file.txt", follow_redirects=False)
    assert machine.status_code == 401
    assert machine.headers["www-authenticate"] == "Bearer"
    assert not service.storage.calls


def test_existing_unverified_manager_session_is_sent_through_sharing_login(delivery):
    client, service, app = delivery
    app.state.actor = Principal(subject="manager-fixture", email="manager@example.test", roles=("READ_WRITE",))
    response = client.get("/fetch/friendly-fixture/file.txt", headers={"Accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 303
    assert parse_qs(urlsplit(response.headers["location"]).query)["next"] == ["/fetch/friendly-fixture/file.txt"]
    assert client.get("/fetch/friendly-fixture/file.txt").status_code == 401
    assert not service.storage.calls


def test_alias_get_head_range_condition_and_audit(delivery):
    client, service, app = delivery
    response = client.get("/fetch/friendly-fixture/file.txt", headers={"Range": "bytes=1-3"})
    assert response.status_code == 206 and response.content == b"ont"
    assert response.headers["content-range"] == "bytes 1-3/8"
    assert response.headers["cache-control"] == "no-store"
    assert "attachment" in response.headers["content-disposition"]
    assert service.storage.bodies[-1].closed
    head = client.head("/fetch/share-fixture/file.txt", headers={"Range": "bytes=1-3"})
    assert head.status_code == 200 and head.content == b""
    assert head.headers["content-length"] == "8"
    unchanged = client.get("/fetch/share-fixture/file.txt", headers={"If-None-Match": head.headers["etag"]})
    assert unchanged.status_code == 304
    events = [e for e in service.events if e["event_type"] == "gateway_response_completed"]
    assert events[0]["details"]["server_bytes_sent"] == 3
    assert events[0]["details"]["download_completion_observed"] is False
    assert events[-1]["details"]["method"] == "HEAD"


def test_if_range_mismatch_sends_full_validator_pinned_object(delivery):
    client, service, app = delivery
    response = client.get("/fetch/share-fixture/file.txt", headers={"Range": "bytes=1-3", "If-Range": '"old"'})
    assert response.status_code == 200 and response.content == b"contents"
    assert service.storage.calls[-1]["if_match"] == '"' + hashlib.sha256(b"contents").hexdigest() + '"'
    assert service.storage.calls[-1]["byte_range"] is None
    assert service.storage.calls[-1]["version_id"] == "version-fixture"


def test_path_decodes_once_and_rejects_traversal(delivery):
    client, service, app = delivery
    service.storage.objects["source/%2e%2e/file.txt"] = b"literal encoded name"
    # Starlette TestClient unquotes httpx.URL.path a second time. ASGITransport
    # uses URL.path directly, matching Uvicorn's one decode from raw_path.
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://dewey.example.test") as transport:
            rejected = await transport.get("/fetch/share-fixture/%2e%2e/file.txt")
            assert rejected.status_code == 400
            response = await transport.get("/fetch/share-fixture/%252e%252e/file.txt")
            assert response.status_code == 200 and response.content == b"literal encoded name"
    asyncio.run(run())
    assert service.storage.calls[-1]["key"] == "source/%2e%2e/file.txt"


@pytest.mark.parametrize("value", ["bytes=1-2,4-5", "bytes=-0", "bytes=5-2"])
def test_invalid_range_does_not_open_storage(delivery, value):
    client, service, app = delivery
    response = client.get("/fetch/share-fixture/file.txt", headers={"Range": value})
    assert response.status_code == 416
    assert not service.storage.calls


def test_manifest_exhausts_pages_and_never_contains_raw_storage_url(delivery):
    client, service, app = delivery
    service.storage.objects = {f"source/nested/{i:03}.txt": str(i).encode() for i in range(205)}
    first = client.get("/fetch/share-fixture?format=manifest").json()
    assert len(first["items"]) == 200 and first["incomplete"] and not first["enumeration_complete"]
    last = client.get("/fetch/share-fixture", params={"format": "manifest", "continuation_token": first["continuation_token"]}).json()
    assert len(last["items"]) == 5 and last["enumeration_complete"] and last["continuation_token"] is None
    assert first["items"][0]["fetch_path"].startswith("/fetch/share-fixture/nested/")
    assert "bucket" not in first["items"][0] and "receipt" not in first["items"][0]
    assert first["items"][0]["etag"] and first["items"][0]["version_id"]


def test_archive_includes_recursive_files_and_precise_completion(delivery):
    client, service, app = delivery
    service.storage.objects = {"source/a.txt": b"a", "source/sub/b.txt": b"b" * 513,
        "source/sub/empty/": b"", "source/sub/café.txt": b"c"}
    response = client.get("/fetch/share-fixture?format=tar")
    assert response.status_code == 200
    assert len(response.content) == int(response.headers["content-length"])
    assert response.headers["accept-ranges"] == "none"
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:") as archive:
        assert archive.getnames() == ["a.txt", "sub/b.txt", "sub/café.txt", "sub/empty"]
        assert archive.extractfile("sub/b.txt").read() == b"b" * 513
    assert all(body.closed for body in service.storage.bodies)
    outcome = service.events[-1]
    assert outcome["event_type"] == "archive_completed"
    assert outcome["details"]["archive_members_completed"] == 4
    assert outcome["details"]["server_bytes_sent"] == len(response.content)
    assert outcome["details"]["inventory_complete"] is True
    assert outcome["details"]["download_completion_observed"] is False


def test_archive_has_no_range_resume_or_conditional_shortcut(delivery):
    client, service, app = delivery
    assert client.get("/fetch/share-fixture?format=tar", headers={"Range": "bytes=1-"}).status_code == 416
    assert client.get("/fetch/share-fixture?format=tar", headers={"If-None-Match": '"etag"'}).status_code == 400
    assert not service.storage.calls


def test_share_revocation_prevents_next_fetch(delivery):
    client, service, app = delivery
    assert client.get("/fetch/share-fixture/file.txt").status_code == 200
    count = len(service.storage.calls)
    service.revoked = True
    assert client.get("/fetch/share-fixture/file.txt").status_code == 403
    assert len(service.storage.calls) == count


def test_www_entry_is_only_trusted_shell_on_application_origin(delivery):
    client, service, app = delivery
    service.storage.objects = {"source/report.html": b"<script>untrusted-report()</script>"}
    service.resolved.update(content_mode="www", report_entrypoint="report.html", name="<script>name</script>")
    response = client.get("/fetch/friendly-fixture/report.html", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "untrusted-report()" not in response.text
    assert "&lt;script&gt;name&lt;/script&gt;" in response.text
    assert "sandbox=\"allow-scripts allow-same-origin\"" in response.text
    assert "frame-src https://*.content.example.test" in response.headers["content-security-policy"]
    assert "/api/v2/recipient/shares/share-fixture/preview" in response.text
    assert not service.storage.calls
    downloaded = client.get("/fetch/share-fixture/report.html", headers={"Accept": "application/octet-stream"})
    assert downloaded.content == b"<script>untrusted-report()</script>"
    assert "attachment" in downloaded.headers["content-disposition"]


def test_namespaced_paths_do_not_collapse_for_one_visible_target():
    resolved = Service().resolved
    resolved["namespaced"] = True
    item = {"target_euid": "target-fixture", "relative_key": "nested/file.txt", "name": "nested/file.txt"}
    assert member_path(resolved, item) == "target-fixture/nested/file.txt"
    assert selection(resolved, "target-fixture/nested/") == ("target-fixture", "nested/")
    with pytest.raises(HTTPException):
        selection(resolved, "nested/")


@pytest.mark.parametrize("paths", [("a", "a/b"), ("a/b", "a"), ("a", "a/"), ("a//b",)])
def test_tar_rejects_colliding_or_ambiguous_paths_before_stream(paths):
    inventory = Inventory()
    try:
        with pytest.raises(HTTPException):
            for path in paths:
                inventory.append({"path": path, "size": 0, "last_modified": None})
    finally:
        inventory.close()
    assert inventory.closed


@pytest.mark.parametrize("change", ["content", "revoked", "rebound"])
def test_archive_rechecks_each_member_before_open(delivery, change):
    client, service, app = delivery
    with principal_context(ACTOR), share_context_context(CONTEXT):
        resolved = service.resolve_share_identifier("share-fixture")
        inventory = complete_inventory(service, resolved)
        response = AuditedArchiveResponse(service=service, resolved=resolved, inventory=inventory,
            release=lambda: None, actor=ACTOR, context=CONTEXT, settings=app.state.settings)
        entry = next(inventory.entries())
        if change == "content":
            service.storage.objects["source/file.txt"] = b"changed"
        elif change == "revoked":
            service.revoked = True
        else:
            service.location_revision += 1
        try:
            with pytest.raises(HTTPException) as failure:
                response._open_member(entry)
            assert failure.value.status_code in {403, 409, 412}
        finally:
            inventory.close()


def test_archive_disconnect_closes_inventory_and_records_partial_outcome(delivery):
    client, service, app = delivery
    released = []
    with principal_context(ACTOR), share_context_context(CONTEXT):
        resolved = service.resolve_share_identifier("share-fixture")
        inventory = complete_inventory(service, resolved)
        response = AuditedArchiveResponse(service=service, resolved=resolved, inventory=inventory,
            release=lambda: released.append(True), actor=ACTOR, context=CONTEXT, settings=app.state.settings)
    async def run():
        async def receive():
            await asyncio.sleep(3600)
        async def send(message):
            if message["type"] == "http.response.body":
                raise OSError("fixture disconnect")
        await response({"type": "http", "asgi": {"spec_version": "2.4"}}, receive, send)
    with pytest.raises(Exception):
        asyncio.run(run())
    assert inventory.closed and released == [True]
    assert all(body.closed for body in service.storage.bodies)
    assert service.events[-1]["event_type"] == "archive_interrupted"
    assert service.events[-1]["details"]["download_completion_observed"] is False
