"""Recipient denials commit native audit history before the unchanged HTTP error."""

from contextlib import contextmanager
from copy import deepcopy
from types import MethodType, SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.tapdb_backend import TapDBBackend, normalize_instance_payload
from tests.support.sharing_v12_fakes import Harness, READER, actor, row


@pytest.fixture
def native_resolution(monkeypatch):
    """Keep real backend attribution/envelope guards; replace only persistence I/O."""
    h = Harness()
    target = h.artifact()
    share = h.share([target])
    connection = SimpleNamespace(app_username=None, attribution=None, session_scope=h.scope)
    h.backend.config_path = "/fixture/explicit-tapdb.yaml"
    h.backend.connection = SimpleNamespace(app_username="fixture-dewey")
    h.backend.settings = SimpleNamespace(auth_mode="external_broker",
        external_broker_handoff_exchange_url="https://login.example.test/auth/handoff/consume")
    h.backend.observability = None
    h.session.get_bind = lambda: None
    monkeypatch.setattr("dewey_service.tapdb_backend.get_db", lambda path: connection)
    monkeypatch.setattr("dewey_service.performance.instrument_engine", lambda engine: None)
    h.backend.session_scope = MethodType(TapDBBackend.session_scope, h.backend)
    with actor():
        with h.backend.session_scope(commit=True) as session:
            h.service._event(session, share, event_type="created", decision="change")
    return SimpleNamespace(h=h, share=share, target=target, connection=connection)


def native_events(h, share):
    return h.related(share, "share_event", "share_event")


def alias_for(h, share, *, status="active"):
    alias = h.add(row("share_alias", "fixture-alias", slug="reviewed-report", status=status))
    h.link(h.session, parent=alias, child=share, relationship_type="share_alias_target")
    return "reviewed-report"


@pytest.mark.parametrize("via_alias", [False, True])
@pytest.mark.parametrize(("failure", "detail"), [
    ("revoked", "Share is not available"),
    ("expired", "Share is not available"),
    ("denied_email", "Share is not available"),
    ("removed_grant", "No current recipient grant"),
    ("expired_grant", "No current recipient grant"),
    ("old_revision_grant", "No current recipient grant"),
])
def test_known_share_denial_commits_once_before_403(native_resolution, monkeypatch, via_alias, failure, detail):
    h, share = native_resolution.h, native_resolution.share
    grant = h.service._share_grants(h.session, share)[0]
    if failure == "revoked": share.json_addl["status"] = "revoked"
    elif failure == "expired": share.json_addl["expires_at"] = "2020-01-01T00:00:00Z"
    elif failure == "denied_email": share.json_addl["denied_emails"] = [READER.email]
    elif failure == "removed_grant": grant.json_addl["status"] = "revoked"
    elif failure == "expired_grant": grant.json_addl["expires_at"] = "2020-01-01T00:00:00Z"
    else: grant.json_addl["policy_revision"] = 0
    identifier = alias_for(h, share) if via_alias else share.euid
    originals = [(instance, deepcopy(vars(instance))) for instance in h.rows]
    old_edges, commits, rollbacks = list(h.edges), h.commits, h.rollbacks
    monkeypatch.setattr(h.service, "authorize_share_object",
        lambda *a, **k: pytest.fail("A resolution denial must not reach object authorization"))
    monkeypatch.setattr(h.service, "_artifact_member_from_instance",
        lambda *a, **k: pytest.fail("A resolution denial must not disclose target metadata"))

    with actor(READER):
        with pytest.raises(HTTPException) as denied:
            h.service.resolve_share_fetch(identifier)
        # The write scope already exited successfully when the caller sees403.
        assert h.commits == commits + 1 and h.rollbacks == rollbacks
    assert denied.value.status_code == 403 and denied.value.detail == detail
    events = native_events(h, share)
    assert len(events) == 2
    event = events[-1]
    payload = normalize_instance_payload(event)
    assert payload["event_type"] == "authorization" and payload["decision"] == "deny"
    assert payload["details"] == {"action": "resolve", "reason": detail, "status_code": 403}
    assert payload["policy_revision"] == share.json_addl["policy_revision"]
    assert payload["actor"] == READER.subject and payload["actor_email_verified"] is True
    assert payload["actor_service"] is False and payload["request_id"] == "fixture-request"
    assert payload["created_by_email"] == READER.email
    assert event.json_addl["properties"] == {"factory": "fresh"}
    assert h.edges == old_edges + [(share, event, "share_event")]
    assert all(vars(instance) == original for instance, original in originals)
    attribution = native_resolution.connection.attribution
    assert attribution.actor_kind == "human" and attribution.actor_subject == READER.subject
    assert attribution.actor_issuer == "https://login.example.test/auth/handoff/consume"
    assert attribution.service_identity == "dewey"


@pytest.mark.parametrize(("failure", "status"), [
    ("unknown", 404), ("retired_alias", 404), ("unlinked_alias", 503),
    ("ambiguous_alias", 503), ("old_schema", 503), ("archived", 410),
])
def test_unresolved_or_noncanonical_identifier_does_not_invent_audit_lineage(native_resolution, failure, status):
    h, share = native_resolution.h, native_resolution.share
    identifier = share.euid
    if failure == "unknown": identifier = "unknown-share"
    elif failure == "old_schema": share.json_addl["schema_version"] = 2
    elif failure == "archived": share.bstatus = "archived"
    else:
        identifier = alias_for(h, share, status="retired" if failure == "retired_alias" else "active")
        if failure == "unlinked_alias":
            h.edges[:] = [edge for edge in h.edges if edge[2] != "share_alias_target"]
        elif failure == "ambiguous_alias":
            alias = next(instance for instance in h.rows if instance.type == "share_alias")
            h.link(h.session, parent=alias, child=share, relationship_type="share_alias_target")
    originals, edges, commits = list(h.rows), list(h.edges), h.commits
    with actor(READER), pytest.raises(HTTPException) as rejected:
        h.service.resolve_share_identifier(identifier)
    assert rejected.value.status_code == status
    assert h.rows == originals and h.edges == edges and h.commits == commits
    assert len(native_events(h, share)) == 1


@pytest.mark.parametrize("identifier", ["", "bad/path", "a" * 129, None])
def test_invalid_identifier_is_rejected_without_opening_native_transaction(native_resolution, identifier):
    h = native_resolution.h
    commits, rollbacks = h.commits, h.rollbacks
    with actor(READER), pytest.raises(ValueError, match="exact share EUID or slug"):
        h.service.resolve_share_identifier(identifier)
    assert (h.commits, h.rollbacks) == (commits, rollbacks)
    assert len(native_events(h, native_resolution.share)) == 1


@pytest.mark.parametrize("excluded", [False, True])
def test_admitted_resolution_leaves_object_authorizer_as_single_event_writer(native_resolution, excluded):
    h, share = native_resolution.h, native_resolution.share
    if excluded:
        share.json_addl["exclude_patterns"] = ["stable.txt"]
    with actor(READER):
        resolved = h.service.resolve_share_identifier(share.euid)
        assert resolved["members"][0]["artifact_euid"] == native_resolution.target.euid
        assert len(native_events(h, share)) == 1
        if excluded:
            with pytest.raises(HTTPException) as denied:
                h.service.resolve_share_fetch(share.euid)
            assert denied.value.status_code == 403
        else:
            receipt = h.service.resolve_share_fetch(share.euid)
            assert receipt["share_euid"] == share.euid
    events = native_events(h, share)
    assert len(events) == 2
    assert events[-1].json_addl["decision"] == ("deny" if excluded else "allow")
    assert events[-1].json_addl["details"]["action"] == "gateway"


@pytest.mark.parametrize("failure", ["write", "commit"])
def test_failed_native_denial_write_never_claims_a_committed_receipt(native_resolution, monkeypatch, failure):
    h, share = native_resolution.h, native_resolution.share
    share.json_addl["status"] = "revoked"
    originals, edges, commits = list(h.rows), list(h.edges), h.commits
    if failure == "write":
        def fail_create(**kwargs):
            raise RuntimeError("injected native write failure")
        monkeypatch.setattr(h.backend.factory, "create_instance", fail_create)
    else:
        @contextmanager
        def fail_commit(*, commit):
            with h.scope(commit=commit) as session:
                yield session
                raise RuntimeError("injected native commit failure")
        native_resolution.connection.session_scope = fail_commit
    with actor(READER), pytest.raises(RuntimeError, match="injected native"):
        h.service.resolve_share_identifier(share.euid)
    assert h.rows == originals and h.edges == edges and h.commits == commits
    assert len(native_events(h, share)) == 1


def test_nonpermission_failure_is_not_misreported_as_access_denial(native_resolution, monkeypatch):
    h, share = native_resolution.h, native_resolution.share
    def unavailable(*args):
        raise HTTPException(503, "injected identity outage")
    monkeypatch.setattr(h.service, "_require_recipient", unavailable)
    commits = h.commits
    with actor(READER), pytest.raises(HTTPException) as rejected:
        h.service.resolve_share_identifier(share.euid)
    assert rejected.value.status_code == 503
    assert h.commits == commits and len(native_events(h, share)) == 1
