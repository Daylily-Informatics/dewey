"""Preserving migration review fences and reconciliation, with native-shaped I/O fixtures."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from dewey_service import share_upgrade_v3 as migration
from dewey_service.registry_conversion import digest
from tests.support.sharing_v12_fakes import OWNER, READER, Harness, Rows, actor, row

DATABASE = {"database": "isolated-test", "schema": "fixture", "database_oid": 19}


class AuthorityRows(Rows):
    def filter(self, *expressions):
        rows = self.rows
        for expression in expressions:
            sql = str(expression)
            values = [
                v for v in expression.compile().params.values() if isinstance(v, (list, tuple))
            ]
            if not values:
                continue
            allowed = set().union(*map(set, values))
            if "parent_instance_uid" in sql or "child_instance_uid" in sql:
                rows = [
                    r
                    for r in rows
                    if r.parent_instance_uid in allowed or r.child_instance_uid in allowed
                ]
            else:
                rows = [r for r in rows if r.euid in allowed]
        return AuthorityRows(rows)


def setup(monkeypatch, *, disposition="convert_preserving"):
    h = Harness()
    member = h.artifact()
    share = h.add(
        row(
            "share",
            "fixture-preserved-share",
            schema_version=2,
            status="active",
            policy_revision=1,
            owner_subject=OWNER.subject,
            owner_email=OWNER.email,
            audience="private",
            expires_at=None,
            delivery_modes=["gateway", "presigned"],
            denied_emails=[],
            include_patterns=["**"],
            exclude_patterns=[],
            target_kind="artifact_object",
            target_euid=member.euid,
        )
    )
    h.link(h.session, parent=member, child=share, relationship_type="has_share")
    with actor():
        h.service._write_grants(
            h.session,
            share,
            [
                {
                    "recipient_type": "email",
                    "recipient": READER.email,
                    "include_subdomains": False,
                    "include_patterns": ["**"],
                    "exclude_patterns": [],
                    "expires_at": None,
                    "recipient_status": "pending",
                    "target_euids": [member.euid],
                }
            ],
            [member],
            1,
        )
        h.service._event(h.session, share, event_type="historical-access", decision="allow")
    if disposition == "preserve_inactive_history":
        share.json_addl.update(schema_version=1, status="retired")
    elif disposition == "already_v3":
        share.json_addl.update(schema_version=3, content_mode="download")
        with actor():
            h.service._write_share_revision(
                h.session, share, [member], 1, policy={"schema_version": 3}
            )
    marker = h.add(
        row(
            "registry_policy",
            "fixture-schema-marker",
            policy_kind="sharing_schema",
            schema_version=2,
            status="verified",
        )
    )
    h.backend.find_by_json_field = lambda *args, **kwargs: marker
    h.edge_revisions = {}

    def query(entity):
        if getattr(entity, "__name__", "") == "generic_instance_lineage":
            values = [
                SimpleNamespace(
                    euid=f"fixture-lineage-{index}",
                    record_revision=h.edge_revisions.get(index, 1),
                    is_deleted=False,
                    parent_instance_uid=p.uid,
                    child_instance_uid=c.uid,
                    relationship_type=k,
                )
                for index, (p, c, k) in enumerate(h.edges)
            ]
            return AuthorityRows(values)
        return AuthorityRows(h.rows)

    h.session.query = query
    monkeypatch.setattr(migration, "identity", lambda session: deepcopy(DATABASE))
    monkeypatch.setattr(
        "dewey_service.audit.current_explicit_attribution",
        lambda: SimpleNamespace(request_id="fixture-explicit-maintenance"),
    )
    return h, share, member, marker


def reviewed(h):
    with actor(maintenance=True):
        return migration.inventory(h.service)


@pytest.mark.parametrize(
    "disposition", ["convert_preserving", "preserve_inactive_history", "already_v3"]
)
def test_preserving_apply_verify_and_replay_never_retire_or_reissue_existing_authority(
    monkeypatch, disposition
):
    h, share, member, marker = setup(monkeypatch, disposition=disposition)
    before = reviewed(h)
    assert not before["ambiguous"] and before["shares"][0]["disposition"] == disposition
    grants = [(g.euid, deepcopy(g.json_addl)) for g in h.service._share_grants(h.session, share)]
    original_scope_count = len(h.related(share, "share_revision", "share_revision"))
    with actor(maintenance=True):
        receipt = migration.apply(h.service, before, before["inventory_sha256"])
        assert receipt["retired"] == receipt["deleted"] == 0
        assert receipt["converted"] == int(disposition == "convert_preserving")
        assert receipt["readiness"] == "blocked_until_verify"
        assert (
            migration.verify(h.service, before, before["inventory_sha256"])["status"] == "verified"
        )
        assert (
            migration.apply(h.service, before, before["inventory_sha256"])["already_applied"]
            is True
        )
    assert [(g.euid, g.json_addl) for g in h.service._share_grants(h.session, share)] == grants
    assert len(h.related(share, "share_revision", "share_revision")) == original_scope_count + int(
        disposition == "convert_preserving"
    )
    assert marker.json_addl["status"] == "verified"
    if disposition == "convert_preserving":
        assert share.json_addl["schema_version"] == 3 and share.json_addl["delivery_modes"] == [
            "gateway"
        ]
        assert h.service._share_members(h.session, share) == [member]


@pytest.mark.parametrize(
    "problem", ["schema", "revision", "audience", "members", "grant-revision", "grant-targets"]
)
def test_inventory_reports_ambiguity_and_apply_refuses_it(monkeypatch, problem):
    h, share, member, marker = setup(monkeypatch)
    grant = h.service._share_grants(h.session, share)[0]
    if problem == "schema":
        share.json_addl["schema_version"] = 1
    elif problem == "revision":
        share.json_addl["policy_revision"] = 0
    elif problem == "audience":
        share.json_addl["audience"] = "public_registered"
    elif problem == "members":
        h.edges[:] = [edge for edge in h.edges if edge[2] != "has_share"]
    elif problem == "grant-revision":
        grant.json_addl["policy_revision"] = 2
    elif problem == "grant-targets":
        h.edges[:] = [edge for edge in h.edges if edge[2] != "share_grant_target"]
    inventory = reviewed(h)
    assert inventory["ambiguous"][0]["euid"] == share.euid
    assert inventory["inventory_sha256"] == digest(
        {k: v for k, v in inventory.items() if k != "inventory_sha256"}
    )
    with actor(maintenance=True), pytest.raises(ValueError, match="Ambiguous"):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    assert marker.json_addl["schema_version"] == 2 and h.commits == 0


def test_proposal_ignores_inactive_grants_but_never_uses_their_native_envelope(monkeypatch):
    h, share, _, _ = setup(monkeypatch)
    inactive = h.add(
        row(
            "share_grant",
            "fixture-inactive-grant",
            status="revoked",
            policy_revision=0,
            recipient_type="unsupported",
            recipient="historical",
        )
    )
    h.link(h.session, parent=share, child=inactive, relationship_type="share_grant")
    assert not reviewed(h)["ambiguous"]


@pytest.mark.parametrize("tamper", ["digest", "format", "unsigned"])
def test_reviewed_inventory_is_cryptographically_bound_before_any_write(monkeypatch, tamper):
    h, _, _, marker = setup(monkeypatch)
    inventory = reviewed(h)
    expected = inventory["inventory_sha256"]
    if tamper == "digest":
        expected = "wrong-digest"
    elif tamper == "format":
        inventory["format"] = "unsupported"
    else:
        inventory["share_count"] += 1
    with actor(maintenance=True), pytest.raises(ValueError, match="digest or format"):
        migration.apply(h.service, inventory, expected)
    assert marker.json_addl["status"] == "verified" and not h.locks


@pytest.mark.parametrize(("admin", "maintenance"), [(True, False), (False, True)])
def test_conversion_requires_both_admin_and_explicit_maintenance(monkeypatch, admin, maintenance):
    h, _, _, _ = setup(monkeypatch)
    inventory = reviewed(h)
    identity = OWNER if admin else READER
    with (
        actor(identity, maintenance=maintenance),
        pytest.raises(ValueError, match="administrator maintenance"),
    ):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    assert not h.locks


@pytest.mark.parametrize("state", ["missing", "not-verified", "wrong-schema", "different-v3"])
def test_apply_requires_exact_verified_predecessor_marker(monkeypatch, state):
    h, _, _, marker = setup(monkeypatch)
    inventory = reviewed(h)
    if state == "missing":
        h.backend.find_by_json_field = lambda *args, **kwargs: None
    elif state == "not-verified":
        marker.json_addl["status"] = "applied"
    elif state == "wrong-schema":
        marker.json_addl["schema_version"] = 1
    else:
        marker.json_addl.update(schema_version=3, v3_inventory_sha256="different-review")
    with actor(maintenance=True), pytest.raises(ValueError):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    assert h.rollbacks == 1


def test_apply_refuses_authority_drift_after_inventory_review(monkeypatch):
    h, share, _, marker = setup(monkeypatch)
    inventory = reviewed(h)
    share.json_addl["purpose"] = "changed after review"
    with actor(maintenance=True), pytest.raises(ValueError, match="inventory changed"):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    assert marker.json_addl["schema_version"] == 2
    assert not h.related(share, "share_revision", "share_revision")


def test_apply_rolls_back_scope_and_share_if_conversion_event_cannot_persist(monkeypatch):
    h, share, _, marker = setup(monkeypatch)
    inventory = reviewed(h)
    original_rows = [(r.euid, deepcopy(vars(r))) for r in h.rows]
    original_edges = list(h.edges)

    def fail(*args, **kwargs):
        raise RuntimeError("native conversion audit unavailable")

    h.service._event = fail
    with actor(maintenance=True), pytest.raises(RuntimeError, match="audit unavailable"):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    assert [(r.euid, vars(r)) for r in h.rows] == original_rows and h.edges == original_edges
    assert marker.json_addl["schema_version"] == 2


@pytest.mark.parametrize(
    "problem",
    [
        "missing-marker",
        "marker",
        "database",
        "domain",
        "share-set",
        "receipt",
        "grant",
        "member",
        "history",
        "lineage",
        "scope",
    ],
)
def test_verify_fails_closed_when_preservation_cannot_be_reconciled(monkeypatch, problem):
    h, share, member, marker = setup(monkeypatch)
    inventory = reviewed(h)
    with actor(maintenance=True):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    if problem == "missing-marker":
        h.backend.find_by_json_field = lambda *a, **k: None
    elif problem == "marker":
        marker.json_addl["status"] = "unexpected"
    elif problem == "database":
        monkeypatch.setattr(migration, "identity", lambda session: {**DATABASE, "database_oid": 20})
    elif problem == "domain":
        h.backend.domain_code = "different-domain"
    elif problem == "share-set":
        h.add(row("share", "fixture-unreviewed-share", schema_version=3))
    elif problem == "receipt":
        marker.json_addl["v3_receipts"][0]["record_revision"] += 1
    elif problem == "grant":
        h.service._share_grants(h.session, share)[0].json_addl["recipient"] = (
            "unreviewed@example.test"
        )
    elif problem == "member":
        member.json_addl["key"] = "unreviewed-key"
    elif problem == "history":
        h.related(share, "share_event", "share_event")[0].json_addl["decision"] = "rewritten"
    elif problem == "lineage":
        h.edge_revisions[0] = 2
    elif problem == "scope":
        h.service._share_revision = lambda *args: SimpleNamespace(euid="fixture-wrong-scope")
    with actor(maintenance=True), pytest.raises(ValueError):
        migration.verify(h.service, inventory, inventory["inventory_sha256"])
    assert marker.json_addl["status"] != "verified"


def test_verify_detects_rewritten_inactive_history(monkeypatch):
    h, share, _, marker = setup(monkeypatch, disposition="preserve_inactive_history")
    inventory = reviewed(h)
    with actor(maintenance=True):
        migration.apply(h.service, inventory, inventory["inventory_sha256"])
    share.json_addl["purpose"] = "history rewritten"
    with actor(maintenance=True), pytest.raises(ValueError, match="historical share was modified"):
        migration.verify(h.service, inventory, inventory["inventory_sha256"])
    assert marker.json_addl["status"] == "applied"
