"""Recursive client contracts against controlled HTTP responses and local files."""

import hashlib
import json

import pytest
import requests

from dewey_service.cli import share_fetch


class Reply:
    def __init__(self, status=200, body=b"abcdef", headers=None, interrupt=False):
        self.status_code, self.body, self.interrupt = status, body, interrupt
        self.headers = {
            "ETag": '"fixture-validator"',
            "Content-Length": str(len(body)),
            **(headers or {}),
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, **kwargs):
        yield self.body
        if self.interrupt:
            raise requests.ConnectionError("fixture disconnect")


def _item():
    return {
        "fetch_path": "/fetch/share-fixture/nested/file.txt",
        "size": 6,
        "etag": '"fixture-validator"',
        "version_id": "version-fixture",
    }


def test_interrupted_file_resumes_only_with_matching_validator(monkeypatch, tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    destination = tmp_path / "nested" / "file.txt"
    calls = []
    replies = [
        Reply(body=b"abc", headers={"Content-Length": "6"}, interrupt=True),
        Reply(status=206, body=b"def", headers={"Content-Range": "bytes 3-5/6"}),
    ]

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return replies.pop(0)

    monkeypatch.setattr(share_fetch.requests, "request", request)
    options = {
        "base": "https://dewey.example.test",
        "token": "secret-fixture",
        "item": _item(),
        "destination": destination,
        "state_dir": state,
    }
    with pytest.raises(requests.ConnectionError):
        share_fetch.download_file(**options)
    assert not destination.exists()
    assert next(state.glob("*.part")).read_bytes() == b"abc"
    assert not list(state.glob("*.lock"))
    result = share_fetch.download_file(**options, resume=True)
    assert destination.read_bytes() == b"abcdef" and result["bytes_received"] == 3
    assert calls[1][2]["headers"]["Range"] == "bytes=3-"
    assert calls[1][2]["headers"]["If-Match"] == '"fixture-validator"'
    assert all(call[2]["allow_redirects"] is False for call in calls)
    receipt = json.loads(next(state.glob("*.json")).read_text())
    assert (
        receipt["status"] == "complete"
        and receipt["sha256"] == hashlib.sha256(b"abcdef").hexdigest()
    )
    assert "secret-fixture" not in json.dumps(receipt)
    assert share_fetch.download_file(**options, resume=True)["status"] == "already_complete"
    assert len(calls) == 2


def test_resume_refuses_changed_manifest_and_unclaimed_existing_files(monkeypatch, tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    destination = tmp_path / "file.txt"
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: Reply())
    options = {
        "base": "https://dewey.example.test",
        "token": "secret-fixture",
        "item": _item(),
        "destination": destination,
        "state_dir": state,
    }
    share_fetch.download_file(**options)
    with pytest.raises(ValueError, match="differs"):
        share_fetch.download_file(
            **{**options, "item": {**_item(), "etag": '"changed"'}}, resume=True
        )
    destination.write_bytes(b"edited")
    with pytest.raises(ValueError, match="no longer matches"):
        share_fetch.download_file(**options, resume=True)
    other = tmp_path / "unknown.txt"
    other.write_bytes(b"user data")
    with pytest.raises(ValueError, match="no matching"):
        share_fetch.download_file(
            **{
                **options,
                "item": {**_item(), "fetch_path": "/fetch/share-fixture/other.txt"},
                "destination": other,
            },
            resume=True,
        )
    assert other.read_bytes() == b"user data"


def test_resume_rejects_full_response_instead_of_appending_it(monkeypatch, tmp_path):
    state = tmp_path / ".state"
    state.mkdir()
    options = {
        "base": "https://dewey.example.test",
        "token": "secret-fixture",
        "item": _item(),
        "destination": tmp_path / "file.txt",
        "state_dir": state,
    }
    replies = [Reply(body=b"abc", headers={"Content-Length": "6"}, interrupt=True), Reply()]
    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: replies.pop(0))
    with pytest.raises(requests.ConnectionError):
        share_fetch.download_file(**options)
    with pytest.raises(RuntimeError, match="HTTP 200"):
        share_fetch.download_file(**options, resume=True)
    assert next(state.glob("*.part")).read_bytes() == b"abc"


@pytest.mark.parametrize(
    "path",
    ["../escape", "/absolute", "a/../b", "a//b", "a\\b", ".dewey-download-state/token", "C:drive"],
)
def test_recursive_client_rejects_unsafe_paths(tmp_path, path):
    with pytest.raises(ValueError):
        share_fetch._safe_destination(tmp_path, path)


def test_recursive_client_refuses_symlink_traversal(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "output"
    root.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic link"):
        share_fetch._safe_destination(root, "link/file.txt")


def test_all_manifest_pages_are_followed_and_policy_changes_fail(monkeypatch):
    from dewey_service.cli import registry

    calls = []

    def request(method, path, **kwargs):
        calls.append(kwargs["params"].get("continuation_token"))
        return {
            "share_euid": "share-fixture",
            "policy_revision": 1,
            "items": [],
            "incomplete": len(calls) == 1,
            "continuation_token": "cursor-fixture" if len(calls) == 1 else None,
        }

    monkeypatch.setattr(registry, "_request", request)
    assert len(list(share_fetch._pages("friendly-fixture"))) == 2
    assert calls == [None, "cursor-fixture"]
    pages = [
        {
            "share_euid": "share-fixture",
            "policy_revision": 1,
            "items": [],
            "incomplete": True,
            "continuation_token": "cursor-fixture",
        },
        {
            "share_euid": "share-fixture",
            "policy_revision": 2,
            "items": [],
            "incomplete": False,
            "continuation_token": None,
        },
    ]
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: pages.pop(0))
    with pytest.raises(RuntimeError, match="Share changed"):
        list(share_fetch._pages("friendly-fixture"))


def test_manifests_cannot_send_credentials_to_another_origin():
    for path in (
        "https://other.example.test/fetch/x",
        "//other.example.test/fetch/x",
        "/api/v1/secrets",
        "/fetch/x#fragment",
    ):
        with pytest.raises(ValueError):
            share_fetch._url("https://dewey.example.test", path)


def test_cli_registers_major_version_fetch_and_manager_commands():
    from dewey_service.cli.registry import register

    commands = {}

    class Registry:
        def add_group(self, group):
            pass

        def add_command(self, group, name, command, **kwargs):
            commands[group, name] = command

    register(Registry(), None)
    for name in ("fetch", "manifest", "claim-slug", "retire-slug", "aliases", "audit-report"):
        assert ("shares", name) in commands
    assert ("artifacts", "location-rebind") in commands
    assert ("shares", "presign") not in commands
    assert ("shares", "download") not in commands


def test_inventory_export_freezes_all_pages_and_preserves_coverage(monkeypatch, tmp_path):
    from dewey_service.cli import registry

    calls = []

    def request(method, path, *, params):
        calls.append(dict(params))
        page = len(calls)
        return {
            "items": [{"share_euid": "share-fixture-" + str(page)}],
            "page": page,
            "total": 2,
            "has_more": page == 1,
            "observed_at": "2026-01-01T00:00:00+00:00",
            "inventory_sha256": "digest-fixture",
            "coverage": {"client_downloads_observed": False},
        }

    monkeypatch.setattr(registry, "_request", request)
    output = tmp_path / "inventory.json"
    result = registry._export_sharing_inventory({"page": 1, "page_size": 1}, output)
    assert result["shares"] == 2
    assert calls[1]["observed_at"] == "2026-01-01T00:00:00+00:00"
    assert calls[1]["expected_inventory_sha256"] == "digest-fixture"
    data = json.loads(output.read_text())
    assert data["complete"] and len(data["items"]) == 2
    assert data["coverage"]["client_downloads_observed"] is False


def test_inventory_export_never_publishes_a_changed_snapshot(monkeypatch, tmp_path):
    from dewey_service.cli import registry

    pages = [
        {
            "items": [],
            "page": 1,
            "total": 0,
            "has_more": True,
            "observed_at": "2026-01-01T00:00:00+00:00",
            "inventory_sha256": "initial",
        },
        {
            "items": [],
            "page": 2,
            "total": 0,
            "has_more": False,
            "observed_at": "2026-01-01T00:00:00+00:00",
            "inventory_sha256": "changed",
        },
    ]
    monkeypatch.setattr(registry, "_request", lambda *args, **kwargs: pages.pop(0))
    output = tmp_path / "inventory.json"
    with pytest.raises(RuntimeError, match="inventory changed"):
        registry._export_sharing_inventory({"page": 1}, output)
    assert not output.exists() and output.with_name("inventory.json.partial").exists()
