"""Report scope and delivery failure contracts missing from the PR coverage receipt."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest
import requests
from daylily_tapdb import generic_instance
from sqlalchemy.orm import Session

from dewey_service.cli import share_fetch
from dewey_service.settings import Settings
from tests.support.sharing_v12_fakes import READER, Harness, actor
from tests.test_report_preview_attribution import ACTOR
from tests.test_report_preview_attribution import preview as preview
from tests.test_share_fetch_cli_v12 import Reply, _item
from tests.test_sharing_v12_reports import AggregateQuery, sql


def test_unfiltered_report_population_still_limits_owner_and_observation_time():
    harness = Harness()
    observed = datetime(2026, 10, 1, tzinfo=timezone.utc)
    harness.service._share_query = lambda session: session.query(generic_instance)
    with Session() as session, actor(READER):
        population, activity = harness.service._report_population(session, observed_at=observed)
        rendered = sql(population.statement)

    assert READER.subject in rendered and READER.email in rendered
    assert "schema_version" in rendered and "'3'" in rendered
    assert "2026-10-01 00:00:00+00:00" in rendered
    assert "generic_instance.created_dt <" in rendered
    assert "actor_email_verified" in rendered and "actor_service" in rendered
    assert "last_access IS NULL" not in rendered
    assert "audience" not in rendered and "content_mode" not in rendered
    assert "expires_at" not in rendered
    assert set(activity.c.keys()) == {
        "share_uid",
        "last_access",
        "viewers",
        "successful_gets",
        "successful_accesses",
    }


def test_unfiltered_history_counts_unknown_schema_without_fabricating_live_policy():
    harness = Harness()
    state = {"groups": [(None, None, "archived", 2)], "predicates": []}

    class HistoryQuery(AggregateQuery):
        def filter(self, *expressions):
            self.state["predicates"].extend(sql(expression) for expression in expressions)
            return self

    harness.service._share_query = lambda session: HistoryQuery(state)
    with actor(READER):
        result = harness.service._legacy_history_coverage(
            harness.session, observed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
        )

    rendered = " AND ".join(state["predicates"])
    assert READER.subject in rendered and READER.email in rendered
    assert "schema_version" in rendered and "created_dt <" in rendered
    assert "expires_at" not in rendered and "created_dt >=" not in rendered
    assert result["total"] == 2 and result["excluded_from_schema3_metrics"] is True
    assert result["groups"] == [
        {"schema_version": None, "stored_status": None, "native_status": "archived", "count": 2}
    ]
    assert "not inferred" in result["access_coverage"]


@pytest.mark.parametrize(
    "change", [{"status": "revoked"}, {"expires_at": "2020-01-01T00:00:00+00:00"}]
)
def test_expired_or_revoked_report_context_cannot_issue_host_cookie(preview, change):
    preview.context.json_addl.update(change)
    before = deepcopy(preview.context.json_addl)
    response = preview.client.get("/__dewey_preview/challenge")
    assert response.status_code == 410
    assert "set-cookie" not in response.headers
    assert preview.context.json_addl == before
    assert not preview.state.storage_calls
    assert all(commit is False for commit, _ in preview.database.transactions)


@pytest.mark.parametrize("body", [{}, {"challenge": 123}, {"challenge": "not-a-digest"}])
def test_report_handoff_rejects_malformed_challenge_without_context_change(preview, body):
    endpoint = (
        f"https://dewey.example.test/api/v2/recipient/shares/{preview.share.euid}"
        f"/preview/{preview.context.euid}/handoff"
    )
    before = deepcopy(preview.context.json_addl)
    revision = preview.context.record_revision
    response = preview.client.post(endpoint, json=body)
    assert response.status_code == 400
    assert preview.context.json_addl == before
    assert preview.context.record_revision == revision
    assert not preview.state.storage_calls
    assert all(
        attribution.actor_subject == ACTOR.subject
        for commit, attribution in preview.database.transactions
        if commit
    )


def test_report_handoff_does_not_accept_a_different_host_cookie_challenge(preview):
    assert preview.client.get("/__dewey_preview/challenge").status_code == 200
    challenge = preview.context.json_addl["cookie_sha256"]
    wrong = ("1" if challenge[0] == "0" else "0") + challenge[1:]
    endpoint = (
        f"https://dewey.example.test/api/v2/recipient/shares/{preview.share.euid}"
        f"/preview/{preview.context.euid}/handoff"
    )
    response = preview.client.post(endpoint, json={"challenge": wrong})
    assert response.status_code == 403
    assert preview.context.json_addl["status"] == "challenged"
    assert "handoff_sha256" not in preview.context.json_addl
    assert not preview.state.storage_calls


def test_report_handoff_requires_form_encoding_even_with_correct_origin(preview):
    response = preview.client.post(
        "/__dewey_preview/handoff",
        headers={"Origin": preview.settings.share_application_origin},
        json={"token": "fixture-token"},
    )
    assert response.status_code == 415
    assert preview.context.json_addl["status"] == "pending"
    assert not preview.database.transactions and not preview.state.storage_calls


def test_download_path_rechecks_resolution_after_symlink_race(monkeypatch, tmp_path):
    root, outside = tmp_path / "downloads", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    destination = root / "pivot" / "report.html"
    original = Path.resolve
    inserted = []

    def resolve_after_symlink_swap(path, *args, **kwargs):
        if path == destination and not inserted:
            (root / "pivot").symlink_to(outside, target_is_directory=True)
            inserted.append(True)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_after_symlink_swap)
    with pytest.raises(ValueError, match="escapes its selected directory"):
        share_fetch._safe_destination(root, "pivot/report.html")
    assert inserted == [True] and not (outside / "report.html").exists()


@pytest.mark.parametrize("user_output", [False, True])
def test_partial_download_requires_resume_and_never_overwrites_user_output(
    monkeypatch, tmp_path, user_output
):
    state = tmp_path / "state"
    state.mkdir()
    destination = tmp_path / "download.txt"
    calls = []

    def interrupted_request(*args, **kwargs):
        calls.append((args, kwargs))
        return Reply(body=b"abc", headers={"Content-Length": "6"}, interrupt=True)

    monkeypatch.setattr(share_fetch.requests, "request", interrupted_request)
    options = {
        "base": "https://dewey.example.test",
        "token": "fixture-download-token",
        "item": _item(),
        "destination": destination,
        "state_dir": state,
    }
    with pytest.raises(requests.ConnectionError, match="fixture disconnect"):
        share_fetch.download_file(**options)
    receipt = next(state.glob("*.json"))
    before = receipt.read_bytes()
    if user_output:
        destination.write_bytes(b"independent user file")
    with pytest.raises(ValueError, match="never overwrites" if user_output else "use --resume"):
        share_fetch.download_file(**options, resume=user_output)
    assert len(calls) == 1
    assert receipt.read_bytes() == before
    assert next(state.glob("*.part")).read_bytes() == b"abc"
    assert not list(state.glob("*.lock"))
    if user_output:
        assert destination.read_bytes() == b"independent user file"
    else:
        assert not destination.exists()


def test_empty_transport_chunks_do_not_change_file_or_received_byte_count(monkeypatch, tmp_path):
    class ChunkedReply(Reply):
        def iter_content(self, **kwargs):
            yield from (b"", b"abc", b"", b"def", b"")

    monkeypatch.setattr(share_fetch.requests, "request", lambda *args, **kwargs: ChunkedReply())
    state = tmp_path / "state"
    state.mkdir()
    destination = tmp_path / "download.txt"
    result = share_fetch.download_file(
        base="https://dewey.example.test",
        token="fixture-download-token",
        item=_item(),
        destination=destination,
        state_dir=state,
    )
    assert result["status"] == "complete" and result["bytes_received"] == 6
    assert destination.read_bytes() == b"abcdef"
    assert sha256(destination.read_bytes()).hexdigest() in next(state.glob("*.json")).read_text()
    assert not list(state.glob("*.part")) and not list(state.glob("*.lock"))


def test_partial_file_symlink_is_rejected_before_network_or_local_write(monkeypatch, tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    outside = tmp_path / "independent.txt"
    outside.write_bytes(b"independent user file")
    base, item = "https://dewey.example.test", _item()
    key = sha256((base + item["fetch_path"]).encode()).hexdigest()
    partial = state / (key + ".part")
    partial.symlink_to(outside)

    def unexpected_network(*args, **kwargs):
        pytest.fail("A symbolic download path must fail before contacting Dewey")

    monkeypatch.setattr(share_fetch.requests, "request", unexpected_network)
    with pytest.raises(ValueError, match="must not be symbolic links"):
        share_fetch.download_file(
            base=base,
            token="fixture-download-token",
            item=item,
            destination=tmp_path / "download.txt",
            state_dir=state,
            resume=True,
        )
    assert outside.read_bytes() == b"independent user file" and partial.is_symlink()
    assert not list(state.glob("*.json")) and not list(state.glob("*.lock"))


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"share_application_origin": "https://dewey.example.test/fetch"}, "exact HTTPS origin"),
        ({"share_content_host_suffix": "*.content.example.test"}, "lowercase DNS suffix"),
        (
            {
                "registry_service_principals": {
                    "not-a-sha256": {"subject": "fixture-service", "roles": ["READ_ONLY"]}
                }
            },
            "SHA256 fingerprint and explicit subject",
        ),
        (
            {
                "registry_service_principals": {
                    sha256(b"fixture-token").hexdigest(): {
                        "subject": "fixture-service",
                        "roles": ["OWNER"],
                    }
                }
            },
            "explicit valid roles",
        ),
    ],
)
def test_delivery_configuration_rejects_ambiguous_origin_or_service_authority(
    test_settings, changes, message
):
    values = test_settings.model_dump()
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        Settings.model_validate(values)
