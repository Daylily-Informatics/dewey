"""Grant revision writes use the real backend envelope guard, with persistence faked."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from dewey_service.audit import authenticated_user_email_context
from dewey_service.registry_access import Principal, principal_context
from dewey_service.services.share_policy import GRANT_TEMPLATE, normalized_policy
from dewey_service.services.sharing import SharingServiceMixin
from dewey_service.share_context import share_context_context
from dewey_service.tapdb_backend import TapDBBackend, normalize_instance_payload

POLICY_FIELDS = (
    "recipient_type",
    "recipient",
    "include_subdomains",
    "include_patterns",
    "exclude_patterns",
    "expires_at",
    "recipient_status",
)
OLD_CREATED = "2020-01-01T00:00:00Z"


def row(kind, fixture_id, **payload):
    stamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        type=kind,
        euid=fixture_id,
        uid=fixture_id,
        name=fixture_id,
        bstatus="active",
        domain_code="fixture",
        created_dt=stamp,
        modified_dt=stamp,
        json_addl={
            "properties": {"old_native": fixture_id},
            "action_groups": {"old_group": fixture_id},
            "audit_log": [{"old_event": fixture_id}],
            "created_at": OLD_CREATED,
            "created_by_email": "old@example.test",
            **deepcopy(payload),
        },
    )


class Persistence:
    """Only SQL/factory I/O is replaced; backend payload validation remains real."""

    def __init__(self):
        self.rows = []
        self.edges = []
        self.commits = 0
        self.rollbacks = 0
        self.factory_calls = []
        self.fail_grant_number = None
        self.session = SimpleNamespace(refresh=lambda instance: None)
        self.backend = object.__new__(TapDBBackend)
        self.backend.domain_code = "fixture"
        self.backend.templates = SimpleNamespace(get_template=lambda *args, **kwargs: object())
        self.backend.factory = SimpleNamespace(create_instance=self.create)
        self.backend.update_persisted_fields = self.update
        self.backend.create_lineage = self.link
        self.backend.session_scope = self.scope

    def create(self, *, session, template_code, name, properties, create_children):
        assert session is self.session
        assert properties == {} and create_children is False
        self.factory_calls.append(template_code)
        if (
            template_code == GRANT_TEMPLATE
            and self.fail_grant_number is not None
            and self.factory_calls.count(GRANT_TEMPLATE) == self.fail_grant_number
        ):
            raise RuntimeError("injected native grant creation failure")
        created = row(template_code.split("/")[1], f"fixture-created-{len(self.rows)}")
        created.name = name
        created.json_addl = {
            "properties": {"factory_only": "fresh"},
            "action_groups": {"factory_group": "fresh"},
            "audit_log": [{"factory_event": "fresh"}],
        }
        self.rows.append(created)
        return created

    def update(self, session, instance, changes, **kwargs):
        assert session is self.session
        for name, value in changes.items():
            setattr(instance, name, deepcopy(value))

    def link(self, session, *, parent, child, relationship_type):
        assert session is self.session
        self.edges.append((parent, child, relationship_type))

    def related(self, parent, relationship, kind):
        return [
            child
            for source, child, relation in self.edges
            if source is parent and relation == relationship and child.type == kind
        ]

    @contextmanager
    def scope(self, *, commit):
        assert commit is True
        originals = [(instance, deepcopy(vars(instance))) for instance in self.rows]
        original_edges = list(self.edges)
        try:
            yield self.session
        except Exception:
            for instance, values in originals:
                vars(instance).clear()
                vars(instance).update(values)
            self.rows[:] = [instance for instance, _ in originals]
            self.edges[:] = original_edges
            self.rollbacks += 1
            raise
        else:
            self.commits += 1


@contextmanager
def actor_context():
    actor = Principal(
        subject="fixture-manager",
        email="manager@example.test",
        roles=("ADMIN",),
        email_verified=True,
    )
    with (
        principal_context(actor),
        authenticated_user_email_context(actor.email),
        share_context_context(
            {"request_id": "fixture-request", "trusted_tailnet": True, "managed_origin": True}
        ),
    ):
        yield


def fixture(public_registered=False):
    store = Persistence()
    members = [row("artifact", "fixture-target-a"), row("artifact", "fixture-target-b")]
    policy = normalized_policy(
        {
            "audience": "public_registered" if public_registered else "recipients",
            "grants": [
                {"recipient_type": "email", "recipient": "remove@example.test"},
                {
                    "recipient_type": "email",
                    "recipient": "keep@example.test",
                    "recipient_status": "verified_on_access",
                    "target_euids": [members[0].euid],
                    "include_patterns": ["reports/**"],
                    "exclude_patterns": ["reports/private/**"],
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                },
                {
                    "recipient_type": "domain",
                    "recipient": "outside.example",
                    "include_subdomains": True,
                    "target_euids": [members[1].euid],
                    "expires_at": None,
                },
            ],
        },
        share_expiry=None,
        member_euids=[member.euid for member in members],
    )
    rules = policy.pop("grants")
    share = row(
        "share", "fixture-share", **policy, status="active", policy_revision=3, expires_at=None
    )
    scope = row("share_revision", "fixture-scope", policy=policy, policy_revision=3)
    grants = [
        row(
            "share_grant",
            f"fixture-grant-{index}",
            **{key: value for key, value in rule.items() if key != "target_euids"},
            status="active",
            policy_revision=3,
        )
        for index, rule in enumerate(rules)
    ]
    historical = row(
        "share_grant",
        "fixture-historical",
        recipient_type="email",
        recipient="historical@example.test",
        status="superseded",
        policy_revision=2,
    )
    store.rows.extend([share, scope, *members, *grants, historical])
    store.link(store.session, parent=share, child=scope, relationship_type="share_revision")
    for member in members:
        store.link(
            store.session, parent=scope, child=member, relationship_type="share_revision_target"
        )
    for grant, rule in zip(grants, rules):
        store.link(store.session, parent=share, child=grant, relationship_type="share_grant")
        for member in members:
            if member.euid in rule["target_euids"]:
                store.link(
                    store.session,
                    parent=grant,
                    child=member,
                    relationship_type="share_grant_target",
                )
    store.link(store.session, parent=share, child=historical, relationship_type="share_grant")
    service = SharingServiceMixin()
    service.backend = store.backend
    service.sharing_upgrade_ready = lambda: True

    def canonical(session, euid, *, lock=False):
        assert session is store.session and euid == share.euid and lock is True
        return share

    service._canonical_share = canonical
    service._registry_share_manager = lambda session, value: value is share
    service._share_related = lambda session, parent, *, relationship, kind: store.related(
        parent, relationship, kind
    )
    service._grant_targets = lambda session, grant: store.related(
        grant, "share_grant_target", "artifact"
    )
    service._canonical_response = lambda session, value, *, manager: normalize_instance_payload(
        value
    )
    return SimpleNamespace(
        store=store,
        service=service,
        share=share,
        scope=scope,
        members=members,
        grants=grants,
        rules=rules,
        historical=historical,
    )


@pytest.mark.parametrize("public_registered", [False, True])
def test_revoke_preserves_grants_and_history_with_fresh_native_envelopes(public_registered):
    f = fixture(public_registered)
    historical_before = deepcopy(f.historical.json_addl)
    original_grants = [deepcopy(grant.json_addl) for grant in f.grants]
    original_edges = list(f.store.edges)
    # Reproduce the production defect with the actual guard, without weakening it.
    with pytest.raises(ValueError, match="TapDB owns instance action_groups and audit_log"):
        f.store.backend.create_instance(
            f.store.session,
            template_code=GRANT_TEMPLATE,
            name="invalid clone",
            json_addl=normalize_instance_payload(f.grants[1]),
        )
    assert f.store.factory_calls == []

    with actor_context():
        result = f.service.revoke_share_grant(
            f.share.euid, f.grants[0].euid, policy_revision=3, reason="Controlled recipient removal"
        )

    assert result["policy_revision"] == 4
    assert f.store.commits == 1 and f.store.rollbacks == 0
    assert f.historical.json_addl == historical_before
    assert f.store.edges[: len(original_edges)] == original_edges
    for index, old in enumerate(f.grants):
        assert old.json_addl["policy_revision"] == 3
        assert old.json_addl["status"] == ("revoked" if index == 0 else "superseded")
        assert old.json_addl["revoked_at"] if index == 0 else old.json_addl["revoked_at"] is None
        for key in (
            *POLICY_FIELDS,
            "properties",
            "action_groups",
            "audit_log",
            "created_at",
            "created_by_email",
        ):
            assert old.json_addl[key] == original_grants[index][key]
    current = [
        grant
        for grant in f.service._share_grants(f.store.session, f.share)
        if grant.json_addl.get("policy_revision") == 4
    ]
    assert len(current) == len(f.rules) - 1
    for new, rule in zip(current, f.rules[1:]):
        payload = new.json_addl
        assert {key: payload[key] for key in POLICY_FIELDS} == {
            key: rule[key] for key in POLICY_FIELDS
        }
        assert payload["status"] == "active"
        assert payload["properties"] == {"factory_only": "fresh"}
        assert payload["action_groups"] == {"factory_group": "fresh"}
        assert payload["audit_log"] == [{"factory_event": "fresh"}]
        assert payload["created_by_email"] == payload["updated_by_email"] == "manager@example.test"
        assert payload["created_at"] != OLD_CREATED
        assert not {"euid", "name", "updated_at", "revoked_at", "target_euids"}.intersection(
            payload
        )
        assert [target.euid for target in f.service._grant_targets(f.store.session, new)] == rule[
            "target_euids"
        ]
    new_scope = f.service._share_revision(f.store.session, f.share)
    assert new_scope.json_addl["policy"] == f.scope.json_addl["policy"]
    assert f.service._share_members(f.store.session, f.share) == f.members
    (event,) = f.store.related(f.share, "share_event", "share_event")
    assert event.json_addl["event_type"] == "recipient_revoked"
    assert event.json_addl["policy_revision"] == 4
    assert f.store.related(f.grants[0], "grant_event", "share_event") == [event]


def test_native_failure_during_replacement_grants_rolls_back_the_whole_revision():
    f = fixture(public_registered=True)
    before = [(instance.euid, deepcopy(vars(instance))) for instance in f.store.rows]
    original_edges = list(f.store.edges)
    f.store.fail_grant_number = 2  # Failure follows old-status writes and one new grant.
    with (
        actor_context(),
        pytest.raises(RuntimeError, match="injected native grant creation failure"),
    ):
        f.service.revoke_share_grant(f.share.euid, f.grants[0].euid, policy_revision=3)
    assert f.store.factory_calls.count(GRANT_TEMPLATE) == 2
    assert f.store.commits == 0 and f.store.rollbacks == 1
    assert [(instance.euid, vars(instance)) for instance in f.store.rows] == before
    assert f.store.edges == original_edges
    assert f.share.json_addl["policy_revision"] == 3


def test_common_grant_writer_projects_policy_before_native_creation():
    f = fixture()
    source = {**normalize_instance_payload(f.grants[1]), "target_euids": [f.members[0].euid]}
    with actor_context(), f.store.backend.session_scope(commit=True) as session:
        f.service._write_grants(session, f.share, [source], f.members, 4)
    created = f.store.rows[-1]
    source["include_patterns"].append("changed-after-write/**")
    assert created.json_addl["include_patterns"] == ["reports/**"]
    assert created.json_addl["properties"] == {"factory_only": "fresh"}
    assert created.json_addl["created_by_email"] == "manager@example.test"
    assert not {"euid", "name", "updated_at", "target_euids"}.intersection(created.json_addl)
    assert f.service._grant_targets(f.store.session, created) == [f.members[0]]
