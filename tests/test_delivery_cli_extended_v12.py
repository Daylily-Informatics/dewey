"""Changed recipient CLI journeys: controlled HTTP, real private output files, no network."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import requests

from dewey_service.cli import registry, share_fetch


class Reply:
    def __init__(self, body=b"abcdef", *, status=200, headers=None, interrupted=False, chunks=None):
        self.status_code = status
        self.headers = {"ETag": '"fixture-etag"', "Content-Length": str(len(body)), **(headers or {})}
        self.chunks = [body] if chunks is None else chunks
        self.interrupted = interrupted
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def iter_content(self, **kwargs):
        yield from self.chunks
        if self.interrupted:
            raise requests.ConnectionError("controlled interrupted transfer")


@pytest.fixture
def emitted(monkeypatch):
    results = []
    monkeypatch.setattr(registry, "_emit", lambda action: results.append(action()))
    monkeypatch.setattr(registry, "_connection", lambda: ("https://dewey.example.test", "credential-fixture"))
    return results


def item(path="nested/file.txt", size=6):
    return {"path": path, "fetch_path": "/fetch/share-fixture/" + path, "size": size,
            "etag": '"fixture-etag"', "version_id": None}


def page(items, token=None):
    return {"share_euid": "share-fixture", "policy_revision": 4, "items": items,
            "incomplete": bool(token), "continuation_token": token}


def test_recursive_command_follows_pages_preserves_empty_directories_and_verifies_completed_resume(monkeypatch, tmp_path, emitted):
    calls, pages = [], []
    entries = [item("first.txt", 3), item("nested/second.txt", 3)]

    def metadata(method, path, *, params):
        pages.append(params["continuation_token"])
        return page([entries[0], item("empty/", 0)], "next-fixture") if params["continuation_token"] is None else page([entries[1]])

    def download(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Reply(body=b"abc")

    monkeypatch.setattr(registry, "_request", metadata)
    monkeypatch.setattr(share_fetch.requests, "request", download)
    output = tmp_path / "bundle"
    share_fetch.fetch("friendly-fixture", output=output, relative_path="", recursive=True, resume=False)
    assert emitted[-1]["files"] == 2 and emitted[-1]["bytes_received"] == 6
    assert emitted[-1]["enumeration_complete"] is True
    assert (output / "empty").is_dir()
    assert (output / "nested/second.txt").read_bytes() == b"abc"
    assert pages == [None, "next-fixture"]
    assert all(call[2]["headers"]["If-Match"] == '"fixture-etag"' and call[2]["allow_redirects"] is False for call in calls)
    share_fetch.fetch("friendly-fixture", output=output, relative_path="", recursive=True, resume=True)
    assert emitted[-1]["already_complete"] == 2 and emitted[-1]["bytes_received"] == 0
    assert len(calls) == 2


def test_single_file_command_heads_then_fetches_exact_attachment(monkeypatch, tmp_path, emitted):
    calls = []
    monkeypatch.setattr(share_fetch.requests, "head", lambda url, **kwargs: (calls.append(("HEAD", url, kwargs)) or Reply()))
    monkeypatch.setattr(share_fetch.requests, "request", lambda method, url, **kwargs: (calls.append((method, url, kwargs)) or Reply()))
    output = tmp_path / "file.txt"
    share_fetch.fetch("share fixture", output=output, relative_path="nested/name with spaces.txt", recursive=False, resume=False)
    assert output.read_bytes() == b"abcdef"
    assert [call[0] for call in calls] == ["HEAD", "GET"]
    assert calls[0][1] == "https://dewey.example.test/fetch/share%20fixture/nested/name%20with%20spaces.txt?download=true"
    assert emitted[-1]["files"] == 1 and emitted[-1]["already_complete"] == 0


@pytest.mark.parametrize("headers,status", [({}, 404), ({"ETag": ""}, 200)])
def test_single_file_command_does_not_download_without_authorized_validator(monkeypatch, tmp_path, emitted, headers, status):
    monkeypatch.setattr(share_fetch.requests, "head", lambda *args, **kwargs: Reply(status=status, headers=headers))
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: pytest.fail("Body fetch must not occur"))
    with pytest.raises(RuntimeError, match="metadata returned"):
        share_fetch.fetch("share-fixture", output=tmp_path / "file", relative_path="", recursive=False, resume=False)
    assert not (tmp_path / "file").exists()


@pytest.mark.parametrize("link", ["output", "state"])
def test_fetch_command_refuses_output_or_state_symlink(monkeypatch, tmp_path, emitted, link):
    outside = tmp_path / "outside"
    outside.mkdir()
    output = tmp_path / "output"
    if link == "output":
        output.symlink_to(outside, target_is_directory=True)
    else:
        output.mkdir()
        (output / ".dewey-download-state").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: pytest.fail("No enumeration through a symlink"))
    with pytest.raises(ValueError, match="symbolic link"):
        share_fetch.fetch("share-fixture", output=output, relative_path="", recursive=True, resume=False)


def test_recursive_fetch_rejects_nonempty_directory_marker(monkeypatch, tmp_path, emitted):
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: page([item("folder/", 1)]))
    with pytest.raises(ValueError, match="Nonempty S3 keys"):
        share_fetch.fetch("share-fixture", output=tmp_path / "out", relative_path="", recursive=True, resume=False)


def test_manifest_command_publishes_all_pages_atomically(monkeypatch, tmp_path, emitted):
    pages = [page([item("one")], "next-fixture"), page([item("two")])]
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: pages.pop(0))
    output = tmp_path / "manifest.json"
    share_fetch.manifest("share-fixture", output=output, relative_path="")
    result = json.loads(output.read_text())
    assert [entry["path"] for entry in result["items"]] == ["one", "two"]
    assert result["enumeration_complete"] and result["policy_revision"] == 4
    assert emitted[-1]["objects"] == 2
    assert not output.with_name("manifest.json.partial").exists()
    with pytest.raises(ValueError, match="already exists"):
        share_fetch.manifest("share-fixture", output=output, relative_path="")


def test_manifest_interruption_keeps_partial_without_claiming_complete(monkeypatch, tmp_path, emitted):
    def pages(*args):
        yield page([item()], "next-fixture")
        raise RuntimeError("controlled page failure")
    monkeypatch.setattr(share_fetch, "_pages", pages)
    output = tmp_path / "manifest.json"
    with pytest.raises(RuntimeError, match="page failure"):
        share_fetch.manifest("share-fixture", output=output, relative_path="")
    assert not output.exists()
    assert output.with_name("manifest.json.partial").exists()
    assert not emitted


@pytest.mark.parametrize("pages", [
    [dict(page([]), incomplete=True)],
    [dict(page([], "next-fixture"), incomplete=False)],
    [page([], "next-fixture"), page([], "next-fixture")],
])
def test_manifest_cursor_contradictions_fail_loudly(monkeypatch, pages):
    responses = list(pages)
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: responses.pop(0))
    with pytest.raises(RuntimeError, match="inconsistent inventory cursor"):
        list(share_fetch._pages("share-fixture"))


@pytest.fixture
def partial_download(monkeypatch, tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    options = {"base": "https://dewey.example.test", "token": "credential-fixture", "item": item(),
               "destination": tmp_path / "file.txt", "state_dir": state}
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs:
                        Reply(body=b"abc", headers={"Content-Length": "6"}, interrupted=True))
    with pytest.raises(requests.ConnectionError):
        share_fetch.download_file(**options)
    return options, next(state.glob("*.part"))


@pytest.mark.parametrize("reply,match", [
    (Reply(body=b"def", status=206, headers={"ETag": '"changed"'}), "different object validator"),
    (Reply(body=b"def", status=206, headers={"Content-Range": "bytes 2-4/6"}), "range does not match"),
    (Reply(body=b"def", status=206, headers={"Content-Range": "bytes 3-5/6", "Content-Length": "4"}), "length differs"),
    (Reply(body=b"defg", status=206, headers={"Content-Range": "bytes 3-5/6", "Content-Length": "3"}), "exceeded its pinned length"),
    (Reply(body=b"de", status=206, headers={"Content-Range": "bytes 3-5/6", "Content-Length": "3"}), "ended early"),
])
def test_resume_never_publishes_malformed_or_truncated_response(monkeypatch, partial_download, reply, match):
    options, partial = partial_download
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: reply)
    with pytest.raises(RuntimeError, match=match):
        share_fetch.download_file(**options, resume=True)
    assert partial.exists() and not options["destination"].exists()
    assert not list(options["state_dir"].glob("*.lock"))
    assert reply.closed


def test_complete_partial_is_verified_by_head_without_refetching_body(monkeypatch, tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    options = {"base": "https://dewey.example.test", "token": "credential-fixture", "item": item(),
               "destination": tmp_path / "file.txt", "state_dir": state}
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: Reply(interrupted=True))
    with pytest.raises(requests.ConnectionError):
        share_fetch.download_file(**options)
    methods = []
    monkeypatch.setattr(share_fetch.requests, "request", lambda method, *args, **kwargs: (methods.append(method) or Reply()))
    result = share_fetch.download_file(**options, resume=True)
    assert methods == ["HEAD"] and result["bytes_received"] == 0
    assert options["destination"].read_bytes() == b"abcdef"


def test_resume_refuses_oversized_local_partial_and_unrequested_replay(monkeypatch, partial_download):
    options, partial = partial_download
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: pytest.fail("Invalid local receipt must not fetch"))
    with pytest.raises(ValueError, match="use --resume"):
        share_fetch.download_file(**options)
    partial.write_bytes(b"too large")
    with pytest.raises(ValueError, match="exceeds its expected length"):
        share_fetch.download_file(**options, resume=True)


def test_download_lock_and_incomplete_state_update_are_not_overwritten(tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    target = state / "receipt.json"
    target.with_suffix(".new").write_text("retain interrupted update")
    with pytest.raises(ValueError, match="prior state update"):
        share_fetch._write_state(target, {})
    key = hashlib.sha256(b"https://dewey.example.test/fetch/share-fixture/nested/file.txt").hexdigest()
    (state / (key + ".lock")).write_text("existing owner")
    with pytest.raises(ValueError, match="active or has an interrupted lock"):
        share_fetch.download_file(base="https://dewey.example.test", token="credential-fixture", item=item(),
                                  destination=tmp_path / "file", state_dir=state)
    assert (state / (key + ".lock")).read_text() == "existing owner"


@pytest.mark.parametrize("size,etag", [(-1, '"validator"'), (1, "")])
def test_download_rejects_unpinned_manifest_before_network(monkeypatch, tmp_path, size, etag):
    state = tmp_path / ".state"
    state.mkdir()
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: pytest.fail("Unpinned source"))
    with pytest.raises(ValueError, match="exact size and object validator"):
        share_fetch.download_file(base="https://dewey.example.test", token="credential-fixture",
                                  item={**item(size=size), "etag": etag}, destination=tmp_path / "file", state_dir=state)


def report_options(**changes):
    return {"starts_at": "2026-01-01T00:00:00Z", "ends_at": None, "owner_subject": None, "status": None,
            "audience": None, "content_mode": None, "older_than_days": None, "never_accessed": False,
            "inventory": False, "page": 1, "observed_at": None, "expected_inventory_sha256": None,
            "created_from": None, "created_before": None, "output": None, **changes}


@pytest.mark.parametrize("changes", [{"page": 2}, {"inventory": True, "page": 2}, {"output": Path("new.json")},
                                      {"inventory": True, "page": 2, "observed_at": "stamp", "expected_inventory_sha256": "digest", "output": Path("new.json")}])
def test_audit_cli_requires_frozen_pages_and_complete_export_start(monkeypatch, emitted, changes):
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: pytest.fail("Invalid export must not request"))
    with pytest.raises(ValueError):
        registry._sharing_report(**report_options(**changes))


def test_audit_cli_selects_report_or_frozen_inventory_endpoint(monkeypatch, emitted):
    calls = []
    monkeypatch.setattr(registry, "_request", lambda method, path, **kwargs: (calls.append((path, kwargs["params"])) or {}))
    registry._sharing_report(**report_options(audience="public_registered", never_accessed=True))
    registry._sharing_report(**report_options(inventory=True, page=2, observed_at="stamp", expected_inventory_sha256="digest"))
    assert calls[0][0].endswith("/sharing-report") and calls[0][1]["never_accessed"] is True
    assert calls[1][0].endswith("/sharing-inventory") and calls[1][1]["expected_inventory_sha256"] == "digest"


def test_inventory_export_refuses_existing_output_and_false_complete_total(monkeypatch, tmp_path):
    output = tmp_path / "inventory.json"
    output.write_text("preserve")
    with pytest.raises(ValueError, match="already exists"):
        registry._export_sharing_inventory({}, output)
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: {"items": [], "has_more": False,
                        "observed_at": "stamp", "inventory_sha256": "digest", "total": 1})
    with pytest.raises(RuntimeError, match="count differs"):
        registry._export_sharing_inventory({}, tmp_path / "new.json")
    assert output.read_text() == "preserve" and not (tmp_path / "new.json").exists()


def test_management_cli_preserves_revision_and_exact_identifier_contracts(monkeypatch, emitted):
    calls = []
    monkeypatch.setattr(registry, "_request", lambda method, path, **kwargs: (calls.append((method, path, kwargs)) or {}))
    registry._share_contents("share fixture", relative_path="exact/sub/", continuation_token="cursor-fixture", limit=17)
    registry._share_revoke_grant("share fixture", "grant fixture", policy_revision=3, reason="reviewed removal")
    registry._alias("share fixture", "friendly-name", policy_revision=3)
    registry._alias_list("share fixture")
    registry._alias_revoke("share fixture", "friendly/name", policy_revision=4)
    registry._rebind("artifact fixture", storage_uri="s3://bucket-fixture/new/file", expected_location_revision=2, reason="equivalent", version_id=None)
    assert calls[0][1] == "/api/v2/recipient/shares/share%20fixture/contents"
    assert calls[0][2]["params"]["path"] == "exact/sub/"
    assert calls[1][2]["data"]["policy_revision"] == 3
    assert calls[4][1].endswith("/aliases/friendly%2Fname/revoke")
    assert calls[5][2]["data"]["expected_location_revision"] == 2


@pytest.mark.parametrize("entry", [None, "nested/report name.html"])
def test_report_command_returns_durable_browser_url_without_credentials(monkeypatch, emitted, entry):
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: {"share_euid": "share-fixture", "report_entrypoint": entry})
    registry._share_report("friendly fixture")
    expected = "https://dewey.example.test/fetch/friendly%20fixture" + ("/nested/report%20name.html" if entry else "")
    assert emitted[-1]["browser_url"] == expected
    assert "credential-fixture" not in json.dumps(emitted[-1])
