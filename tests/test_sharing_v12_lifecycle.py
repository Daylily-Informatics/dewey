"""Delegation, revision, alias, and recipient boundaries with native envelope validation."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from dewey_service.registry_access import Principal
from dewey_service.services.base import DeweyNotFoundError
from tests.support.sharing_v12_fakes import OWNER, READER, Harness, Rows, actor, row


def delegated(harness, monkeypatch):
    checked = []
    monkeypatch.setattr(
        "dewey_service.services.share_revisions.require_record",
        lambda backend, session, record, action: checked.append((record.euid, action)),
    )
    return checked


def test_create_replay_reports_current_revocation_without_reactivation(monkeypatch):
    h = Harness()
    member = h.artifact()
    checked = delegated(h, monkeypatch)
    cache = {}
    h.service._idempotency_replay = lambda session, **kwargs: cache.get(kwargs["idempotency_key"])

    def save(session, **kwargs):
        from types import SimpleNamespace

        cache[kwargs["idempotency_key"]] = SimpleNamespace(
            status_code=kwargs["status_code"], response=kwargs["response"]
        )

    h.service._store_idempotency = save
    with actor():
        code, created = h.service.create_share(
            target_kind="artifact_object",
            target_euid=member.euid,
            allowed_users=[READER.email],
            expires_at=None,
            idempotency_key="fixture-create",
        )
        assert code == 201 and created["expires_at"] is None
        assert created["owner_email"] == OWNER.email
        assert checked == [(member.euid, "share")]
        revoked = h.service.revoke_share(
            created["share_euid"], policy_revision=1, reason="review complete"
        )
        assert revoked["status"] == "revoked" and revoked["policy_revision"] == 2
        before = len(h.rows)
        _, replay = h.service.create_share(
            target_kind="artifact_object",
            target_euid=member.euid,
            allowed_users=[READER.email],
            expires_at=None,
            idempotency_key="fixture-create",
        )
        assert replay["status"] == "revoked" and len(h.rows) == before
    with actor(READER), pytest.raises(HTTPException) as denied:
        h.service.authorize_share_object(created["share_euid"], member.euid)
    assert denied.value.status_code == 403
    events = h.related(
        next(r for r in h.rows if r.euid == created["share_euid"]), "share_event", "share_event"
    )
    assert (
        events[-1].json_addl["decision"] == "deny"
    )  # The denial audit commits before the exception.


def test_atomic_target_edit_retains_history_but_removes_old_recipient_authority(monkeypatch):
    h = Harness()
    old, new = h.artifact(), h.artifact("fixture-replacement", key="new/location.txt")
    share = h.share([old])
    delegated(h, monkeypatch)
    with actor():
        result = h.service.modify_registry_share(
            share.euid,
            {
                "policy_revision": 1,
                "target_kind": "artifact_object",
                "target_euid": new.euid,
                "name": "Updated target",
            },
        )
    assert result["policy_revision"] == 2
    assert [m["artifact_euid"] for m in result["members"]] == [new.euid]
    assert h.service._historical_share_members(h.session, share) == [old, new]
    assert len(h.related(share, "share_revision", "share_revision")) == 2
    with actor(READER):
        with pytest.raises(HTTPException) as removed:
            h.service.authorize_share_object(share.euid, old.euid)
        assert removed.value.status_code == 403
        assert h.service.authorize_share_object(share.euid, new.euid)["key"] == "new/location.txt"
        event = h.service.append_share_event(
            share.euid,
            target_euid=old.euid,
            event_type="gateway_response_completed",
            decision="completed",
            details={"status_code": 200},
        )
    assert h.related(old, "share_target_event", "share_event")[-1].euid == event


def test_edit_failure_rolls_back_native_scope_grants_and_all_target_edges(monkeypatch):
    h = Harness()
    old, new = h.artifact(), h.artifact("fixture-replacement")
    share = h.share([old])
    delegated(h, monkeypatch)
    before = [(r.euid, deepcopy(vars(r))) for r in h.rows]
    edges = list(h.edges)
    link = h.backend.create_lineage

    def failing_link(session, **kwargs):
        if kwargs["relationship_type"] == "share_grant_target":
            raise RuntimeError("fixture lineage persistence failure")
        return link(session, **kwargs)

    h.backend.create_lineage = failing_link
    with actor(), pytest.raises(RuntimeError, match="lineage persistence"):
        h.service.modify_registry_share(
            share.euid,
            {"policy_revision": 1, "target_kind": "artifact_object", "target_euid": new.euid},
        )
    assert [(r.euid, vars(r)) for r in h.rows] == before
    assert h.edges == edges and h.rollbacks == 1


@pytest.mark.parametrize(
    ("changes", "status"),
    [
        ({"policy_revision": 0}, 409),
        ({"policy_revision": 1, "grant_everyone": True}, None),
        ({"policy_revision": True}, None),
    ],
)
def test_edit_rejects_stale_or_unsupported_proposals_without_writes(changes, status):
    h = Harness()
    share = h.share([h.artifact()])
    before = deepcopy(share.json_addl)
    with actor(), pytest.raises(HTTPException if status else ValueError) as caught:
        h.service.modify_registry_share(share.euid, changes)
    if status:
        assert caught.value.status_code == status
    assert share.json_addl == before


def test_edit_drops_nonoverlapping_scoped_grant_and_clamps_inherited_expiry(monkeypatch):
    h = Harness()
    one = h.artifact()
    two = h.artifact(
        "fixture-two", key="root/two.txt", storage_uri="s3://fixture-source/root/two.txt"
    )
    replacement = h.artifact(
        "fixture-three", key="root/three.txt", storage_uri="s3://fixture-source/root/three.txt"
    )
    share = h.share(
        [one, two],
        grants=[
            {"recipient_type": "email", "recipient": READER.email},
            {
                "recipient_type": "domain",
                "recipient": "specific.example",
                "target_euids": [one.euid],
            },
        ],
    )
    delegated(h, monkeypatch)
    deadline = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    with actor():
        result = h.service.modify_registry_share(
            share.euid,
            {
                "policy_revision": 1,
                "targets": [
                    {"target_kind": "artifact_object", "target_euid": two.euid},
                    {"target_kind": "artifact_object", "target_euid": replacement.euid},
                ],
                "expires_at": deadline,
            },
        )
    assert len(result["grants"]) == 1
    assert result["grants"][0]["expires_at"] == deadline
    assert {member["artifact_euid"] for member in result["members"]} == {two.euid, replacement.euid}
    assert set(result["grants"][0]["target_euids"]) == {two.euid, replacement.euid}


def test_alias_idempotency_conflict_tombstone_and_exact_native_authority():
    h = Harness()
    first, second = h.share([h.artifact()]), h.share([h.artifact("fixture-second")])
    with actor():
        claimed = h.service.claim_share_slug(first.euid, "reviewed-report", policy_revision=1)
        edge_count, event_count = len(h.edges), len(h.related(first, "share_event", "share_event"))
        assert (
            h.service.claim_share_slug(first.euid, "reviewed-report", policy_revision=1) == claimed
        )
        assert (
            len(h.edges) == edge_count
            and len(h.related(first, "share_event", "share_event")) == event_count
        )
        with pytest.raises(HTTPException) as collision:
            h.service.claim_share_slug(second.euid, "reviewed-report", policy_revision=1)
        assert collision.value.status_code == 409
        assert h.service.list_share_aliases(first.euid)[0]["slug"] == "reviewed-report"
    with actor(READER):
        assert h.service.resolve_share_identifier("reviewed-report")["share_euid"] == first.euid
    with actor():
        assert (
            h.service.revoke_share_slug(first.euid, "reviewed-report", policy_revision=1)[
                "reassignable"
            ]
            is False
        )
        with pytest.raises(HTTPException) as retired:
            h.service.claim_share_slug(first.euid, "reviewed-report", policy_revision=1)
        assert retired.value.status_code == 409
    with actor(READER), pytest.raises(HTTPException) as inaccessible:
        h.service.resolve_share_identifier("reviewed-report")
    assert inaccessible.value.status_code == 404


@pytest.mark.parametrize("operation", ["claim", "revoke", "list"])
def test_recipient_cannot_manage_aliases(operation):
    h = Harness()
    share = h.share([h.artifact()])
    with actor(READER), pytest.raises(HTTPException) as denied:
        if operation == "list":
            h.service.list_share_aliases(share.euid)
        else:
            getattr(h.service, operation + "_share_slug")(
                share.euid, "private-alias", policy_revision=1
            )
    assert denied.value.status_code == 403 and not h.claims


@pytest.mark.parametrize("operation", ["claim", "revoke"])
def test_alias_mutations_require_current_policy_revision(operation):
    h = Harness()
    share = h.share([h.artifact()])
    with actor(), pytest.raises(HTTPException) as stale:
        getattr(h.service, operation + "_share_slug")(
            share.euid, "reviewed-alias", policy_revision=2
        )
    assert stale.value.status_code == 409


def test_alias_missing_or_ambiguous_lineage_never_uses_copied_share_metadata():
    h = Harness()
    share = h.share([h.artifact()])
    alias = h.add(
        row(
            "share_alias",
            "fixture-alias",
            slug="broken-alias",
            status="active",
            share_euid=share.euid,
        )
    )
    with actor():
        with pytest.raises(HTTPException) as missing:
            h.service.revoke_share_slug(share.euid, "broken-alias", policy_revision=1)
        assert missing.value.status_code == 404
    with actor(READER), pytest.raises(HTTPException) as invalid:
        h.service.resolve_share_identifier("broken-alias")
    assert invalid.value.status_code == 503
    h.link(h.session, parent=alias, child=share, relationship_type="share_alias_target")
    h.link(h.session, parent=alias, child=share, relationship_type="share_alias_target")
    with actor(READER), pytest.raises(HTTPException) as duplicated:
        h.service.resolve_share_identifier("broken-alias")
    assert duplicated.value.status_code == 503


@pytest.mark.parametrize("identifier", [None, "", "a/b", "x" * 129])
def test_fetch_identifier_must_be_exact(identifier):
    h = Harness()
    with actor(READER), pytest.raises(ValueError):
        h.service.resolve_share_identifier(identifier)


def test_recipient_metadata_redacts_manager_fields_and_keeps_namespaced_subset():
    h = Harness()
    first, second = h.artifact(), h.artifact("fixture-second")
    share = h.share(
        [first, second],
        grants=[
            {"recipient_type": "email", "recipient": READER.email, "target_euids": [second.euid]}
        ],
    )
    with actor(READER):
        metadata = h.service.get_share(share.euid)
        assert not {
            "targets",
            "owner_email",
            "grants",
            "members",
            "include_patterns",
            "exclude_patterns",
        }.intersection(metadata)
        resolved = h.service.resolve_share_identifier(share.euid)
        assert (
            resolved["namespaced"] and resolved["is_collection"] and resolved["target_count"] == 1
        )
        assert resolved["members"][0]["artifact_euid"] == second.euid
        with pytest.raises(HTTPException) as bare:
            h.service.resolve_share_fetch(share.euid, "stable.txt")
        assert bare.value.status_code == 404
        receipt = h.service.resolve_share_fetch(share.euid, second.euid + "/stable.txt")
        assert receipt["target_euid"] == second.euid


@pytest.mark.parametrize(
    "relative", ["/file", "../file", "a/../file", "a//file", "a\\file", "a\0file"]
)
def test_fetch_rejects_path_traversal_and_ambiguous_separators(relative):
    h = Harness()
    share = h.share([h.artifact(prefix=True)])
    with actor(READER), pytest.raises(ValueError):
        h.service.resolve_share_fetch(share.euid, relative)


def test_prefix_fetch_requires_file_and_keeps_literal_relative_key():
    h = Harness()
    member = h.artifact(prefix=True)
    share = h.share([member])
    with actor(READER):
        with pytest.raises(HTTPException) as directory:
            h.service.resolve_share_fetch(share.euid)
        assert directory.value.status_code == 400
        result = h.service.resolve_share_fetch(share.euid, "report%20name.html")
        assert result["key"] == "root/report%20name.html"
        assert result["relative_key"] == "report%20name.html"


@pytest.mark.parametrize(
    "state",
    [
        "expired",
        "revoked",
        "archived",
        "unverified",
        "service",
        "denied",
        "wrong-email",
        "old-grant",
        "expired-grant",
    ],
)
def test_access_fails_closed_for_lifecycle_and_identity_changes(state):
    h = Harness()
    member = h.artifact()
    share = h.share([member])
    reader = READER
    if state == "expired":
        share.json_addl["expires_at"] = "2020-01-01T00:00:00Z"
    elif state == "revoked":
        share.json_addl["status"] = "revoked"
    elif state == "archived":
        share.bstatus = "archived"
    elif state == "unverified":
        reader = Principal(subject=READER.subject, email=READER.email)
    elif state == "service":
        reader = Principal(
            subject=READER.subject, email=READER.email, email_verified=True, service=True
        )
    elif state == "denied":
        share.json_addl["denied_emails"] = [READER.email]
    elif state == "wrong-email":
        reader = Principal(subject="other", email="other@example.test", email_verified=True)
    elif state == "old-grant":
        h.service._share_grants(h.session, share)[0].json_addl["policy_revision"] = 0
    elif state == "expired-grant":
        h.service._share_grants(h.session, share)[0].json_addl["expires_at"] = (
            "2020-01-01T00:00:00Z"
        )
    with actor(reader), pytest.raises(HTTPException) as denied:
        h.service._evaluate_share(h.session, share, member.euid, "", "gateway")
    assert denied.value.status_code == 403


def test_delegation_checks_explicit_descendant_policy_and_fails_missing_policy(monkeypatch):
    h = Harness()
    parent, child = h.artifact(prefix=True), h.artifact("fixture-child")
    h.service._registry_query = lambda *args, **kwargs: Rows([child])
    checked = delegated(h, monkeypatch)
    policy = h.add(row("registry_policy", "fixture-policy", explicit_restriction=True))
    h.link(h.session, parent=child, child=policy, relationship_type="registry_policy")
    with actor():
        h.service._assert_share_delegation(h.session, [parent])
    assert checked == [(parent.euid, "share"), (child.euid, "share")]
    h.edges.clear()
    with actor(), pytest.raises(HTTPException) as unavailable:
        h.service._assert_share_delegation(h.session, [parent])
    assert unavailable.value.status_code == 503


def test_report_selection_requires_native_member_and_stable_object_filename():
    h = Harness()
    one, two = (
        h.artifact(original_filename="stable.html"),
        h.artifact("fixture-prefix", prefix=True),
    )
    policy = {
        "content_mode": "www",
        "report_entrypoint": one.euid + "/stable.html",
        "report_bundle_root": "",
        "include_patterns": ["**"],
        "exclude_patterns": [],
    }
    h.service._validate_report_selection(policy, [one, two])
    for bad in ("unknown-target/report.html", "report.html", one.euid + "/file.txt"):
        with pytest.raises(ValueError):
            h.service._validate_report_selection({**policy, "report_entrypoint": bad}, [one, two])
    with pytest.raises(ValueError, match="empty bundle root"):
        h.service._validate_report_selection(
            {**policy, "report_bundle_root": "nested/"}, [one, two]
        )


def test_native_alias_query_requires_template_and_returns_typed_alias_descriptor():
    h = Harness()
    share = h.share([h.artifact()])
    alias = h.add(row("share_alias", "fixture-native-alias", slug="typed-alias", status="active"))
    h.link(h.session, parent=alias, child=share, relationship_type="share_alias_target")
    del h.service._find_share_alias
    del h.service._share_aliases
    h.query_rows = [alias]
    assert h.service._find_share_alias(h.session, "typed-alias", lock=True) is alias
    assert h.service._share_aliases(h.session, share) == [
        {
            "alias_euid": alias.euid,
            "slug": "typed-alias",
            "status": "active",
            "fetch_path": "/fetch/typed-alias",
        }
    ]
    h.backend.templates.get_template = lambda *args, **kwargs: None
    with pytest.raises(HTTPException) as missing:
        h.service._share_alias_query(h.session)
    assert missing.value.status_code == 503


@pytest.mark.parametrize("count", [0, 2])
def test_current_scope_requires_exactly_one_native_revision(count):
    h = Harness()
    share = h.share([h.artifact()])
    scope = h.related(share, "share_revision", "share_revision")[0]
    h.edges[:] = [edge for edge in h.edges if edge[2] != "share_revision"]
    for _ in range(count):
        h.link(h.session, parent=share, child=scope, relationship_type="share_revision")
    with pytest.raises(HTTPException) as unavailable:
        h.service._share_revision(h.session, share)
    assert unavailable.value.status_code == 503


@pytest.mark.parametrize("problem", ["nonmanager", "stale", "missing", "registered"])
def test_grant_revoke_fences_manager_revision_and_public_audience(problem):
    h = Harness()
    share = h.share([h.artifact()], audience="public_registered")
    grants = h.service._share_grants(h.session, share)
    target = grants[-1] if problem == "registered" else grants[0]
    grant_euid = "fixture-not-a-grant" if problem == "missing" else target.euid
    error = (
        ValueError
        if problem == "registered"
        else DeweyNotFoundError
        if problem == "missing"
        else HTTPException
    )
    with actor(READER if problem == "nonmanager" else OWNER), pytest.raises(error) as caught:
        h.service.revoke_share_grant(
            share.euid, grant_euid, policy_revision=2 if problem == "stale" else 1
        )
    if error is HTTPException:
        assert caught.value.status_code == (403 if problem == "nonmanager" else 409)
    assert share.json_addl["policy_revision"] == 1
