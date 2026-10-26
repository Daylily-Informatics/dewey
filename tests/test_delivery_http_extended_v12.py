"""Recipient HTTP and streaming failure boundaries using existing controlled I/O fixtures."""
from __future__ import annotations

import asyncio
import io
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, HTTPException

import dewey_service.share_exports as exports
from dewey_service.registry_access import principal_context
from dewey_service.share_context import share_context_context
from dewey_service.share_gateway import attach_share_gateway
from tests.test_fetch_delivery_v12 import ACTOR, CONTEXT, Service, delivery


def test_browser_listing_escapes_names_preserves_canonical_pagination_and_head(delivery):
    client, service, app = delivery
    service.resolved["name"] = "<script>untrusted-name</script>"
    service.storage.objects = {"source/a&b.txt": b"a", "source/nested/c.txt": b"c"}
    response = client.get("/fetch/friendly-fixture?limit=1", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "&lt;script&gt;untrusted-name&lt;/script&gt;" in response.text
    assert "a&amp;b.txt" in response.text and "/fetch/share-fixture/a%26b.txt" in response.text
    assert "/fetch/share-fixture?continuation_token=1" in response.text
    assert "files on this page; more pages follow." in response.text
    assert client.head("/fetch/share-fixture", headers={"Accept": "text/html"}).content == b""
    assert client.head("/fetch/share-fixture?format=manifest").content == b""
    service.storage.objects.clear()
    empty = client.get("/fetch/share-fixture", headers={"Accept": "text/html"})
    assert "No permitted files" in empty.text and "final page" in empty.text


@pytest.mark.parametrize("path", [
    "/fetch/share-fixture?format=zip",
    "/fetch/share-fixture?format=tar&continuation_token=1",
    "/fetch/share-fixture/file.txt?continuation_token=1",
])
def test_incompatible_fetch_options_fail_before_storage(delivery, path):
    client, service, app = delivery
    assert client.get(path).status_code == 400
    assert service.storage.calls == []


def test_recipient_metadata_and_contents_never_include_storage_coordinates(delivery):
    client, service, app = delivery
    metadata = client.get("/api/v2/recipient/shares/friendly-fixture").json()
    assert metadata["share_euid"] == "share-fixture" and metadata["expires_at"] is None
    assert not {"members", "bucket", "key", "owner_email"} & metadata.keys()
    contents = client.get("/api/v2/recipient/shares/share-fixture/contents?path=&limit=1").json()
    assert contents["enumeration_complete"] and len(contents["items"]) == 1
    assert "receipt" not in contents["items"][0]


def test_www_root_head_and_explicit_download_follow_distinct_paths(delivery):
    client, service, app = delivery
    service.storage.objects = {"source/report.html": b"<h1>controlled report</h1>", "source/side.css": b"body{}"}
    service.resolved.update(content_mode="www", report_entrypoint="report.html")
    head = client.head("/fetch/share-fixture", headers={"Accept": "text/html"})
    assert head.status_code == 200 and not head.content
    assert head.headers["referrer-policy"] == "strict-origin"
    assert int(head.headers["content-length"]) > 0 and not service.storage.calls
    download = client.get("/fetch/share-fixture/report.html?download=true", headers={"Accept": "text/html"})
    assert download.content == b"<h1>controlled report</h1>" and "attachment" in download.headers["content-disposition"]
    sidecar = client.get("/fetch/share-fixture/side.css", headers={"Accept": "text/html"})
    assert sidecar.content == b"body{}"


def test_single_object_root_and_stable_filename_selection(delivery):
    client, service, app = delivery
    member = service.resolved["members"][0]
    member.update(target_kind="artifact_object", key="source/file.txt", filename="stable.txt")
    assert client.get("/fetch/share-fixture").content == b"contents"
    assert exports.selection(service.resolved, "stable.txt") == ("target-fixture", "")
    with pytest.raises(HTTPException) as denied:
        exports.selection(service.resolved, "current-storage-name.txt")
    assert denied.value.status_code == 404
    service.resolved["namespaced"] = True
    assert exports.selection(service.resolved, "") == (None, "")
    assert exports.selection(service.resolved, "target-fixture/stable.txt") == ("target-fixture", "")
    with pytest.raises(HTTPException):
        exports.selection(service.resolved, "target-fixture/other.txt")
    assert exports.member_path(service.resolved, {"target_euid": "target-fixture", "name": "physical.txt"}) == "target-fixture/stable.txt"
    with pytest.raises(HTTPException) as missing:
        exports.member_path(service.resolved, {"target_euid": "removed-fixture"})
    assert missing.value.status_code == 409


def test_retired_presign_route_does_not_contact_storage(delivery):
    client, service, app = delivery
    router = APIRouter(prefix="/api/v1")
    attach_share_gateway(app, router, service)
    app.include_router(router)
    response = client.post("/api/v1/registry/shares/share-fixture/presign", json={"target_euid": "target-fixture"})
    assert response.status_code == 410 and "/fetch" in response.json()["detail"]
    assert not service.storage.calls


@pytest.mark.parametrize("change", ["location", "etag", "pagination"])
def test_manifest_never_labels_unpinned_or_inconsistent_inventory_complete(delivery, monkeypatch, change):
    client, service, app = delivery
    if change == "location":
        service.location_revision = 2
    elif change == "etag":
        original = service.storage.object_response
        def without_validator(**kwargs):
            result = original(**kwargs)
            result.pop("ETag")
            return result
        monkeypatch.setattr(service.storage, "object_response", without_validator)
    else:
        monkeypatch.setattr(service, "list_share_contents", lambda *args, **kwargs:
                            {"items": [], "continuation_token": "next-fixture", "incomplete": False})
    response = client.get("/fetch/share-fixture?format=manifest")
    assert response.status_code == {"location": 409, "etag": 503, "pagination": 502}[change]
    assert not any(event["event_type"] == "manifest_page" for event in service.events)


@pytest.mark.parametrize("case", ["duplicate", "object_limit", "metadata_limit", "nonempty_directory"])
def test_tar_inventory_rejects_unrepresentable_or_over_capacity_content(monkeypatch, case):
    inventory = exports.Inventory()
    try:
        entry = {"path": "file.txt", "size": 0, "last_modified": None}
        expected = 409
        if case == "duplicate":
            inventory.append(entry)
        elif case == "object_limit":
            monkeypatch.setattr(exports, "_MAX_INVENTORY_OBJECTS", 0)
            expected = 413
        elif case == "metadata_limit":
            monkeypatch.setattr(exports, "_MAX_INVENTORY_BYTES", 1)
            expected = 413
        else:
            entry.update(path="directory/", size=1)
        with pytest.raises(HTTPException) as rejected:
            inventory.append(entry)
        assert rejected.value.status_code == expected
    finally:
        inventory.close()
        inventory.close()


@pytest.mark.parametrize("case", ["cursor", "policy"])
def test_incomplete_archive_inventory_is_closed_before_error(delivery, monkeypatch, case):
    client, service, app = delivery
    created, original = [], exports.Inventory
    class ObservedInventory(original):
        def __init__(self):
            super().__init__()
            created.append(self)
    monkeypatch.setattr(exports, "Inventory", ObservedInventory)
    resolved = service.resolve_share_identifier("share-fixture")
    if case == "cursor":
        monkeypatch.setattr(service, "list_share_contents", lambda *args, **kwargs:
                            {"items": [], "continuation_token": "repeated-fixture", "incomplete": True})
    else:
        monkeypatch.setattr(service, "list_share_contents", lambda *args, **kwargs:
                            {"items": [], "continuation_token": None, "incomplete": False})
        service.revision += 1
    with principal_context(ACTOR), share_context_context(CONTEXT), pytest.raises(HTTPException) as failure:
        exports.complete_inventory(service, resolved)
    assert failure.value.status_code == (502 if case == "cursor" else 409)
    assert created[0].closed and not service.storage.bodies


def test_archive_head_counts_no_member_downloads(delivery):
    client, service, app = delivery
    response = client.head("/fetch/share-fixture?format=tar")
    assert response.status_code == 200 and not response.content
    assert int(response.headers["content-length"]) > 1024
    assert all(call["head"] for call in service.storage.calls)
    assert service.events[-1]["details"]["archive_members_completed"] == 0
    assert service.events[-1]["details"]["server_bytes_sent"] == 0


def archive_response(service, settings, released):
    with principal_context(ACTOR), share_context_context(CONTEXT):
        resolved = service.resolve_share_identifier("share-fixture")
        inventory = exports.complete_inventory(service, resolved)
    return exports.AuditedArchiveResponse(service=service, resolved=resolved, inventory=inventory,
        release=lambda: released.append(True), actor=ACTOR, context=CONTEXT, settings=settings)


def run_response(response):
    messages = []
    async def run():
        async def receive():
            raise AssertionError("ASGI2.4 streaming does not need a synthetic disconnect")
        async def send(message):
            messages.append(message)
        await response({"type": "http", "asgi": {"spec_version": "2.4"}}, receive, send)
    asyncio.run(run())
    return messages


@pytest.mark.parametrize("failure", ["short", "extra", "close"])
def test_archive_stream_failure_never_records_completed_download(delivery, monkeypatch, failure):
    client, service, app = delivery
    released = []
    response = archive_response(service, app.state.settings, released)
    class BrokenBody(io.BytesIO):
        def close(self):
            super().close()
            if failure == "close":
                raise RuntimeError("controlled close failure")
    data = b"short" if failure == "short" else b"contents-extra" if failure == "extra" else b"contents"
    body = BrokenBody(data)
    monkeypatch.setattr(response, "_open_member", lambda entry: {"Body": body})
    with pytest.raises(RuntimeError):
        run_response(response)
    assert body.closed and response.inventory.closed and released == [True]
    assert service.events[-1]["event_type"] == "archive_interrupted"
    assert service.events[-1]["details"]["download_completion_observed"] is False
    assert service.events[-1]["details"]["outcome"] == ("close_failure" if failure == "close" else "disconnect_or_failure")


def test_archive_identity_change_stops_next_member_before_s3(delivery, monkeypatch):
    import dewey_service.recipient_identity as identity
    client, service, app = delivery
    response = archive_response(service, app.state.settings, [])
    entry = next(response.inventory.entries())
    initial = len(service.storage.calls)
    monkeypatch.setattr(identity, "verify_recipient_binding", lambda *args, **kwargs:
                        {"canonical_user_id": "other-fixture", "email": ACTOR.email, "email_verified": True})
    try:
        with pytest.raises(HTTPException) as failure:
            response._open_member(entry)
        assert failure.value.status_code == 401 and len(service.storage.calls) == initial
    finally:
        response.inventory.close()


def test_archive_metadata_mismatch_closes_open_source(delivery, monkeypatch):
    client, service, app = delivery
    response = archive_response(service, app.state.settings, [])
    entry = next(response.inventory.entries())
    original = service.storage.object_response
    def changed(**kwargs):
        result = original(**kwargs)
        result["ContentLength"] += 1
        return result
    monkeypatch.setattr(service.storage, "object_response", changed)
    try:
        with pytest.raises(HTTPException) as failure:
            response._open_member(entry)
        assert failure.value.status_code == 409 and service.storage.bodies[-1].closed
    finally:
        response.inventory.close()


def test_archive_start_failure_releases_reservation_and_inventory(delivery, monkeypatch):
    client, service, app = delivery
    released, created = [], []
    original = exports.complete_inventory
    def inventory(*args, **kwargs):
        result = original(*args, **kwargs)
        created.append(result)
        return result
    monkeypatch.setattr(exports, "complete_inventory", inventory)
    monkeypatch.setattr(exports, "_reserve", lambda subject: lambda: released.append(True))
    monkeypatch.setattr(service, "append_share_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit unavailable")))
    request = SimpleNamespace(headers={}, method="GET", app=app)
    with principal_context(ACTOR), share_context_context(CONTEXT), pytest.raises(RuntimeError, match="audit unavailable"):
        exports.archive_delivery(request, service, service.resolve_share_identifier("share-fixture"))
    assert created[0].closed and released == [True]
