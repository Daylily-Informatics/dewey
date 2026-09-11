"""Focused tests of new acceptance orchestration, with no network or database."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "docs/plans/20260911T070000Z_dewey_application_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location("dewey_acceptance_capsule", SCRIPT)
assert SPEC and SPEC.loader
capsule = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capsule)


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8914",
        "http://localhost:8914",
        "http://127.0.0.1",
        "http://127.0.0.1:8914/",
        "http://user@127.0.0.1:8914",
        "http://127.0.0.1:8914?next=remote",
    ],
)
def test_capsule_rejects_noncanonical_or_nonloopback_urls(url):
    with pytest.raises(capsule.AcceptanceError):
        capsule.validate_base_url(url)


@pytest.mark.parametrize("suffix", ["?", "#"])
def test_capsule_rejects_trailing_empty_query_or_fragment(suffix):
    with pytest.raises(capsule.AcceptanceError, match="Canonical loopback"):
        capsule.validate_base_url("http://127.0.0.1:8914" + suffix)


def make_capsule(tmp_path, phase="read"):
    token = tmp_path / "resolver-token"
    token.write_text("test-only-resolver-secret")
    token.chmod(0o600)
    args = SimpleNamespace(
        phase=phase,
        lane="rehearsal",
        receipt=str(tmp_path / "receipt.json"),
        resolver_token_file=str(token),
        base_url="http://127.0.0.1:8914",
        prior_receipt="unused",
    )
    settings = SimpleNamespace(
        api_bearer_token="primary-test-secret",
        api_tokens=lambda: {
            "primary-test-secret",
            "additional-test-secret-a",
            "additional-test-secret-b",
        },
        qeo_resolver_token_sha256=hashlib.sha256(token.read_bytes()).hexdigest(),
        qeo_resolver_token_expires_at="2099-01-01T00:00:00+00:00",
    )
    return capsule.Capsule(
        args,
        settings,
        {"image": "reviewed-image"},
        {"report_artifact_euid": "persisted-report-fixture"},
    )


class FakeResponse:
    def __init__(self, status, payload):
        self.code = status
        self.body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.body[:limit]


def test_primary_token_selected_and_response_ids_persist_before_status_failure(tmp_path):
    item = make_capsule(tmp_path)
    requests = []

    def open_request(request, *, timeout):
        requests.append(request)
        return FakeResponse(201, {"artifact_set_euid": "service-returned-set"})

    item.opener = SimpleNamespace(open=open_request)
    with pytest.raises(capsule.AcceptanceError, match="HTTP status"):
        item.request("POST", "/api/v1/artifact-sets", body={})
    item.handle.close()
    assert requests[0].headers["Authorization"] == "Bearer primary-test-secret"
    receipt_text = Path(item.args.receipt).read_text()
    assert "primary-test-secret" not in receipt_text
    assert "test-only-resolver-secret" not in receipt_text
    assert json.loads(receipt_text)["checks"][0]["returned_identifiers"] == {
        "artifact_set_euid": "service-returned-set"
    }


def test_partial_write_retains_service_returned_id_without_inventing_retry(tmp_path, monkeypatch):
    item = make_capsule(tmp_path, "write")
    monkeypatch.setattr(item, "accepted_prior", lambda *_: {})
    calls = []

    def request(method, path, **kwargs):
        calls.append(path)
        if len(calls) == 1:
            return {"artifact_set_euid": "service-returned-set", "status_code": 201}
        raise capsule.AcceptanceError("controlled second request failure")

    monkeypatch.setattr(item, "request", request)
    with pytest.raises(capsule.AcceptanceError, match="second request"):
        item.run()
    receipt = json.loads(Path(item.args.receipt).read_text())
    assert receipt["status"] == "failed"
    assert receipt["returned_artifact_set_euid"] == "service-returned-set"
    assert len(calls) == 2


def test_replay_uses_receipt_id_and_identical_original_response(tmp_path, monkeypatch):
    item = make_capsule(tmp_path, "replay")
    created = {"artifact_set_euid": "service-returned-set", "status_code": 201}
    member = {"status_code": 201, "artifact_set_euid": "service-returned-set"}
    prior = {
        "persisted_artifact_set_euid": "service-returned-set",
        "create_response_sha256": capsule.digest(created),
        "membership_response_sha256": capsule.digest(member),
    }
    monkeypatch.setattr(item, "accepted_prior", lambda *_: prior)
    calls = []

    def request(method, path, **kwargs):
        calls.append((path, kwargs))
        return [created, member, {"detail": "conflict"}][len(calls) - 1]

    monkeypatch.setattr(item, "request", request)
    item.run()
    assert calls[1][0] == "/api/v1/artifact-sets/service-returned-set/members"
    assert calls[2][1]["expected"] == 409
    assert calls[0][1]["key"] == calls[2][1]["key"]
    assert (
        json.loads(Path(item.args.receipt).read_text())["persisted_artifact_set_euid"]
        == "service-returned-set"
    )


def test_changed_image_rejects_prior_stage(tmp_path):
    item = make_capsule(tmp_path)
    prior_path = tmp_path / "prior.json"
    prior = {"inputs": {"image": "different-image"}, "phase": "read", "status": "passed"}
    prior_path.write_text(json.dumps({**prior, "sha256": capsule.digest(prior)}))
    prior_path.chmod(0o600)
    with pytest.raises(capsule.AcceptanceError, match="input/image/config changed"):
        item.accepted_prior(str(prior_path), "read")
    item.handle.close()


def test_capsule_refuses_receipt_overwrite(tmp_path):
    item = make_capsule(tmp_path)
    item.handle.close()
    with pytest.raises(FileExistsError):
        make_capsule(tmp_path)


def test_redirect_handler_never_follows_redirect():
    assert (
        capsule.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://outside")
        is None
    )
