"""Current sharing boundaries exercised through real policy and native envelopes."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.services import sharing
from dewey_service.storage import StorageObject
from tests.support.service_fakes import _FakeReferenceQuery
from tests.support.sharing_v12_fakes import READER, Harness, actor, row


def harness():
    h = Harness()
    # The real permission predicate is evaluated over persisted fixture rows;
    # the test actor has explicit administrator authority, never maintenance mode.
    h.session.query = lambda *models: _FakeReferenceQuery(h.rows, None)
    cache = {}
    h.service._idempotency_replay = lambda session, **kw: cache.get(kw["idempotency_key"])

    def store(session, **kw):
        cache[kw["idempotency_key"]] = SimpleNamespace(
            status_code=kw["status_code"], response=kw["response"]
        )

    h.service._store_idempotency = store
    return h


def persisted_state(h):
    return [(r.euid, deepcopy(vars(r))) for r in h.rows], list(h.edges)


def test_current_scope_rejects_cross_domain_native_target_before_disclosure():
    h = harness()
    target = h.artifact()
    share = h.share([target])
    target.domain_code = "different-fixture-domain"
    before = persisted_state(h)
    with actor(READER), pytest.raises(HTTPException) as denied:
        h.service.resolve_share_identifier(share.euid)
    assert denied.value.status_code == 503
    assert "invalid target lineage" in denied.value.detail
    assert persisted_state(h) == before


def test_deadline_crossed_during_admission_denies_and_commits_one_receipt(monkeypatch):
    h = harness()
    target = h.artifact()
    deadline = datetime.now(timezone.utc) + timedelta(minutes=1)
    share = h.share([target], expires_at=deadline.isoformat())
    times = iter([deadline - timedelta(seconds=1), deadline + timedelta(seconds=1)])

    class AdmissionClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return next(times)

    monkeypatch.setattr(sharing, "datetime", AdmissionClock)
    with actor(READER), pytest.raises(HTTPException) as expired:
        h.service.authorize_share_object(share.euid, target.euid)
    assert expired.value.status_code == 410
    events = h.related(share, "share_event", "share_event")
    assert len(events) == 1
    assert events[0].json_addl["decision"] == "deny"
    assert events[0].json_addl["details"]["action"] == "gateway"
    assert h.commits == 1 and h.rollbacks == 0


def test_recipient_cannot_turn_gateway_authority_into_an_unsupported_action():
    h = harness()
    target = h.artifact()
    share = h.share([target])
    before = persisted_state(h)
    with actor(READER), pytest.raises(ValueError, match="Unsupported share action"):
        h.service.authorize_share_object(share.euid, target.euid, action="delete")
    assert persisted_state(h) == before
    assert h.rollbacks == 1


def test_storage_lookup_uses_only_current_schema_and_literal_prefix_scope():
    h = harness()
    old = h.share([h.artifact("fixture-preserved-target", key="old/file.txt")])
    old.json_addl["schema_version"] = 2
    target = h.artifact("fixture-current-prefix", prefix=True)
    current = h.share([target])
    with actor(READER):
        receipt = h.service.authorize_shared_storage(
            "fixture-source", "root/nested/file.txt", action="gateway"
        )
        with pytest.raises(HTTPException) as outside:
            h.service.authorize_shared_storage("fixture-source", "root-lookalike/file.txt")
    assert outside.value.status_code == 403
    assert receipt["share_euid"] == current.euid
    assert receipt["relative_key"] == "nested/file.txt"
    assert not h.related(old, "share_event", "share_event")
    assert [e.json_addl["decision"] for e in h.related(current, "share_event", "share_event")] == [
        "allow"
    ]


@pytest.mark.parametrize("proposal", [{"ttl_seconds": 300}, {"targets": []}])
def test_create_rejects_removed_url_lifetime_and_empty_selection_without_persistence(proposal):
    h = harness()
    before = persisted_state(h)
    with actor(), pytest.raises(ValueError, match="Raw signed URL|selected S3 targets"):
        h.service.create_share(
            target_kind="mixed_set", expires_at=None, idempotency_key="fixture-invalid", **proposal
        )
    assert persisted_state(h) == before


def test_explicit_pending_grant_preserves_target_scope_and_unrestricted_delegation():
    h = harness()
    target = h.artifact()
    policy = h.add(row("registry_policy", "fixture-target-policy", explicit_restriction=False))
    h.link(h.session, parent=target, child=policy, relationship_type="registry_policy")
    h.service._registry_query = lambda *args, **kwargs: _FakeReferenceQuery([target], None)
    with actor():
        status, result = h.service.create_share(
            target_kind="artifact_object",
            target_euid=target.euid,
            grants=[
                {
                    "recipient_type": "email",
                    "recipient": READER.email,
                    "recipient_status": "pending",
                    "target_euids": [target.euid],
                }
            ],
            expires_at=None,
            idempotency_key="fixture-explicit-grant",
        )
    assert status == 201 and result["policy_revision"] == 1
    assert len(result["grants"]) == 1
    assert result["grants"][0]["recipient_status"] == "pending"
    assert result["grants"][0]["target_euids"] == [target.euid]
    with actor(READER):
        receipt = h.service.resolve_share_fetch(result["share_euid"])
    assert receipt["target_euid"] == target.euid and receipt["expires_at"] is None


@pytest.mark.parametrize("page,page_size", [(0, 25), (True, 25), (1, 0), (1, 101)])
def test_share_index_rejects_unbounded_or_ambiguous_pagination_before_native_read(page, page_size):
    h = harness()
    with actor(), pytest.raises(ValueError, match="page must be positive"):
        h.service.list_registry_shares(page=page, page_size=page_size)
    assert h.commits == h.rollbacks == 0 and h.rows == []


def test_share_index_reports_more_rows_without_disclosing_the_extra_row():
    h = harness()
    first = h.share([h.artifact()])
    h.share([h.artifact("fixture-second-target", key="root/second.txt")])
    with actor():
        result = h.service.list_registry_shares(page=1, page_size=1)
    assert [item["share_euid"] for item in result["items"]] == [first.euid]
    assert result["has_more"] is True and result["incomplete"] is False
    assert result["page"] == result["page_size"] == 1


@pytest.mark.parametrize("operation", ["edit", "revoke"])
def test_verified_recipient_cannot_mutate_or_revoke_manager_policy(operation):
    h = harness()
    share = h.share([h.artifact()])
    before = persisted_state(h)
    with actor(READER), pytest.raises(HTTPException) as denied:
        if operation == "edit":
            h.service.modify_registry_share(share.euid, {"policy_revision": 1, "name": "Denied"})
        else:
            h.service.revoke_share(share.euid, policy_revision=1, reason="Denied")
    assert denied.value.status_code == 403
    assert persisted_state(h) == before


@pytest.mark.parametrize("inactive", ["expired", "revoked"])
def test_manager_edit_cannot_reactivate_inactive_authority(inactive):
    h = harness()
    share = h.share([h.artifact()])
    if inactive == "expired":
        share.json_addl["expires_at"] = "2020-01-01T00:00:00+00:00"
    else:
        share.json_addl["status"] = "revoked"
    before = persisted_state(h)
    with actor(), pytest.raises(ValueError, match="cannot be reactivated"):
        h.service.modify_registry_share(share.euid, {"policy_revision": 1, "expires_at": None})
    assert persisted_state(h) == before


def test_target_edit_cannot_replace_all_members_with_an_empty_selection():
    h = harness()
    share = h.share([h.artifact()])
    before = persisted_state(h)
    with actor(), pytest.raises(ValueError, match="retain at least one target"):
        h.service.modify_registry_share(share.euid, {"policy_revision": 1, "targets": []})
    assert persisted_state(h) == before


def test_explicit_recipient_replacement_preserves_members_and_old_grant_history():
    h = harness()
    target = h.artifact()
    share = h.share([target])
    original = h.service._share_grants(h.session, share)[0]
    with actor():
        result = h.service.modify_registry_share(
            share.euid,
            {
                "policy_revision": 1,
                "grants": [{"recipient_type": "email", "recipient": "new-recipient@example.test"}],
            },
        )
    assert result["policy_revision"] == 2
    assert result["members"][0]["artifact_euid"] == target.euid
    assert [grant["recipient"] for grant in result["grants"]] == ["new-recipient@example.test"]
    assert original.json_addl["status"] == "superseded"
    assert len(h.related(share, "share_revision", "share_revision")) == 2
    with actor(READER), pytest.raises(HTTPException) as removed:
        h.service.resolve_share_identifier(share.euid)
    assert removed.value.status_code == 403


def test_duration_extension_does_not_extend_shorter_grants_or_restore_revoked_recipients():
    h = harness()
    target = h.artifact()
    now = datetime.now(timezone.utc)
    short = (now + timedelta(days=2)).isoformat()
    share = h.share(
        [target],
        audience="public_registered",
        expires_at=(now + timedelta(days=10)).isoformat(),
        grants=[
            {"recipient_type": "email", "recipient": READER.email, "expires_at": short},
            {"recipient_type": "email", "recipient": "removed@example.test"},
        ],
    )
    removed = h.service._share_grants(h.session, share)[1]
    removed.json_addl["status"] = "revoked"
    deadline = (now + timedelta(days=20)).isoformat()
    with actor():
        result = h.service.modify_registry_share(
            share.euid, {"policy_revision": 1, "expires_at": deadline}
        )
    current = {grant["recipient"]: grant for grant in result["grants"]}
    assert set(current) == {READER.email, "*"}
    assert current[READER.email]["expires_at"] == short
    assert current["*"]["expires_at"] == deadline
    assert removed.json_addl["status"] == "revoked"
    with actor(READER):
        resolved = h.service.resolve_share_identifier(share.euid)
    assert [member["artifact_euid"] for member in resolved["members"]] == [target.euid]


def test_selected_current_target_lists_only_its_authorized_object():
    h = harness()
    first = h.artifact()
    second = h.artifact("fixture-second-target", key="root/second.txt")
    share = h.share([first, second])
    with actor(READER):
        result = h.service.list_share_contents(share.euid, target_euid=second.euid)
    assert [item["target_euid"] for item in result["items"]] == [second.euid]
    assert result["continuation_token"] is None and result["incomplete"] is False


def test_unavailable_native_authority_during_listing_is_not_hidden_as_a_denied_file():
    h = harness()
    target = h.artifact()
    share = h.share([target])
    read_related = h.related
    target_reads = []

    def storage_read(parent, relationship, kind):
        if relationship == "share_revision_target":
            target_reads.append(parent.euid)
            if len(target_reads) == 2:
                raise HTTPException(503, "Native authority read unavailable")
        return read_related(parent, relationship, kind)

    h.related = storage_read
    before = persisted_state(h)
    with actor(READER), pytest.raises(HTTPException) as unavailable:
        h.service.list_share_contents(share.euid)
    assert unavailable.value.status_code == 503
    assert persisted_state(h) == before and h.rollbacks == 1


def preview_storage(h, target, paths, *, truncated=False):
    calls = []

    def listing(*, bucket, prefix, limit):
        assert bucket == target.json_addl["bucket"] and prefix == target.json_addl["key"]
        calls.append(limit)
        return {
            "objects": [
                StorageObject(bucket=bucket, key=prefix + path, size=7) for path in paths[:limit]
            ],
            "next_continuation_token": "fixture-next-page" if truncated else None,
        }

    h.service._require_storage = lambda: SimpleNamespace(list_share_candidates=listing)
    return calls


def test_selection_preview_applies_share_grant_and_registered_path_boundaries():
    h = harness()
    target = h.artifact(prefix=True)
    protected = h.artifact("fixture-archived-child", key="root/restricted/hidden.txt")
    protected.bstatus = "archived"
    h.service._registry_query = lambda *a, **kw: _FakeReferenceQuery([protected], None)
    calls = preview_storage(
        h,
        target,
        ["outside.txt", "public/visible.txt", "private/no-grant.txt", "restricted/hidden.txt"],
    )
    before = persisted_state(h)
    with actor():
        result = h.service.preview_share_selection(
            target.euid,
            {
                "expires_at": None,
                "include_patterns": ["public/**", "private/**", "restricted/**"],
                "grants": [
                    {
                        "recipient_type": "email",
                        "recipient": READER.email,
                        "include_patterns": ["public/**", "restricted/**"],
                    }
                ],
            },
        )
    assert result["items"] == [
        {
            "target_euid": target.euid,
            "kind": "object",
            "name": "public/visible.txt",
            "relative_key": "public/visible.txt",
            "size": 7,
        }
    ]
    assert result["incomplete"] is False and result["continuation_token"] is None
    assert calls == [200] and persisted_state(h) == before


def test_selection_preview_propagates_missing_native_policy_instead_of_hiding_the_file():
    h = harness()
    target = h.artifact(prefix=True)
    uninitialized = h.artifact("fixture-uninitialized-child", key="root/reports/file.txt")
    h.service._registry_query = lambda *a, **kw: _FakeReferenceQuery([uninitialized], None)
    preview_storage(h, target, ["reports/file.txt"])
    before = persisted_state(h)
    with actor(), pytest.raises(HTTPException) as unavailable:
        h.service.preview_share_selection(
            target.euid, {"allowed_users": [READER.email], "expires_at": None}
        )
    assert unavailable.value.status_code == 503
    assert "unique policy" in unavailable.value.detail
    assert persisted_state(h) == before


def test_preview_stops_at_review_limit_and_never_claims_recursive_completeness():
    h = harness()
    target = h.artifact(prefix=True)
    paths = [f"report-{index:03d}.txt" for index in range(201)]
    calls = preview_storage(h, target, paths, truncated=True)
    with actor():
        result = h.service.preview_share_selection(
            target.euid, {"allowed_users": [READER.email], "expires_at": None}
        )
    assert len(result["items"]) == 200
    assert result["items"][-1]["name"] == "report-199.txt"
    assert result["incomplete"] is True and result["continuation_token"] is None
    assert calls == [200] and h.commits == 0


def test_fetch_rejects_storage_basename_when_persisted_share_filename_is_different():
    h = harness()
    target = h.artifact(key="new-location/renamed.dat", original_filename="stable.txt")
    share = h.share([target])
    with actor(READER):
        with pytest.raises(HTTPException) as wrong_name:
            h.service.resolve_share_fetch(share.euid, "renamed.dat")
        receipt = h.service.resolve_share_fetch(share.euid, "stable.txt")
    assert wrong_name.value.status_code == 404
    assert receipt["key"] == "new-location/renamed.dat" and receipt["filename"] == "stable.txt"
