"""Persistence-only fakes for exercising real sharing workflows and native envelopes."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

from dewey_service.audit import authenticated_user_email_context
from dewey_service.registry_access import Principal, principal_context
from dewey_service.service import DeweyService
from dewey_service.services.share_policy import normalized_policy
from dewey_service.share_context import share_context_context
from dewey_service.tapdb_backend import TapDBBackend


OWNER = Principal(subject="fixture-owner", email="owner@example.test", roles=("ADMIN",), email_verified=True)
READER = Principal(subject="fixture-reader", email="reader@outside.example", roles=("READ_ONLY",), email_verified=True)


@contextmanager
def actor(actor=OWNER, *, maintenance=False):
    with (principal_context(actor, maintenance=maintenance), authenticated_user_email_context(actor.email),
          share_context_context({"request_id": "fixture-request", "managed_origin": True, "trusted_tailnet": True})):
        yield


def row(kind, label, **payload):
    stamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return SimpleNamespace(type=kind, euid=label, uid=label, name=label, domain_code="fixture",
        bstatus="active", is_deleted=False, record_revision=1, created_dt=stamp, modified_dt=stamp,
        json_addl={"properties": {}, "action_groups": {}, "audit_log": [], **deepcopy(payload)})


class Rows:
    def __init__(self, rows):
        self.rows = list(rows)
    def filter_by(self, **values):
        return Rows([r for r in self.rows if all(getattr(r, key) == value for key, value in values.items())])
    def filter(self, *expressions): return self
    def order_by(self, *values): return self
    def with_for_update(self): return self
    def join(self, *values): return self
    def offset(self, value): return Rows(self.rows[value:])
    def limit(self, value): return Rows(self.rows[:value])
    def all(self): return list(self.rows)
    def count(self): return len(self.rows)
    def first(self): return self.rows[0] if self.rows else None
    def one_or_none(self):
        assert len(self.rows) <= 1
        return self.first()
    def one(self):
        assert len(self.rows) == 1
        return self.rows[0]


class Harness:
    def __init__(self):
        self.rows, self.edges, self.claims, self.locks = [], [], {}, []
        self.commits = self.rollbacks = 0
        self.on_expire = lambda instance: None
        self.query_rows = []
        self.session = SimpleNamespace(refresh=lambda instance: None, expire=lambda instance: self.on_expire(instance),
            execute=lambda query, params: self.locks.append((str(query), params)), query=lambda *args: Rows(self.query_rows))
        backend = self.backend = object.__new__(TapDBBackend)
        backend.domain_code = "fixture"
        backend.templates = SimpleNamespace(get_template=lambda *a, **k: SimpleNamespace(uid="fixture-template"))
        backend.factory = SimpleNamespace(create_instance=self.create)
        backend.session_scope = self.scope
        backend.update_persisted_fields = self.update
        backend.create_lineage = self.link
        backend.find_by_euid = lambda session, *, template_code, euid: next((r for r in self.rows if r.euid == euid), None)
        backend.list_parents = lambda session, *, child, relationship_type: [p for p,c,k in self.edges if c is child and k == relationship_type]
        backend.list_children = lambda session, *, parent, relationship_type: [c for p,c,k in self.edges if p is parent and k == relationship_type]
        backend.lock_external_key = lambda session, **kwargs: self.locks.append(kwargs)
        backend.claim_global_instance = self.claim
        backend.ensure_templates = lambda *args, **kwargs: None
        service = self.service = object.__new__(DeweyService)
        service.backend = backend
        service.share_max_lifetime_days = 365
        service.requester_pays_buckets = set()
        service.sharing_upgrade_ready = lambda: True
        service._share_query = lambda session: Rows([r for r in self.rows if r.type == "share"])
        service._share_related = lambda session, parent, *, relationship, kind: self.related(parent, relationship, kind)
        service._grant_targets = lambda session, grant: self.related(grant, "share_grant_target", "artifact")
        service._historical_share_members = lambda session, share: [p for p,c,k in self.edges if c is share and k == "has_share"]
        service._registry_record = lambda session, euid, **kwargs: next(r for r in self.rows if r.euid == euid)
        service._registry_query = lambda *args, **kwargs: Rows([])
        service._share_aliases = lambda session, share: [
            {"slug": p.json_addl["slug"], "status": p.json_addl["status"], "alias_euid": p.euid}
            for p,c,k in self.edges if c is share and k == "share_alias_target"]
        service._find_share_alias = lambda session, slug, **kwargs: next((r for r in self.rows if r.type == "share_alias" and r.json_addl["slug"] == slug), None)

    def add(self, instance):
        self.rows.append(instance)
        return instance

    def create(self, *, session, template_code, name, properties, create_children):
        assert session is self.session and properties == {} and create_children is False
        instance = row(template_code.split("/")[1], f"fixture-created-{len(self.rows)}")
        instance.name = name
        instance.json_addl = {"properties": {"factory": "fresh"}, "action_groups": {}, "audit_log": []}
        return self.add(instance)

    def update(self, session, instance, changes, **kwargs):
        for key, value in changes.items():
            setattr(instance, key, deepcopy(value))
        instance.record_revision += 1

    def link(self, session, *, parent, child, relationship_type):
        self.edges.append((parent, child, relationship_type))
        return SimpleNamespace(euid=f"fixture-lineage-{len(self.edges)}")

    def related(self, parent, relationship, kind):
        return [c for p,c,k in self.edges if p is parent and k == relationship and c.type == kind]

    def claim(self, session, *, template_code, identity_key, name, json_addl, command_evidence):
        if identity_key in self.claims:
            return self.claims[identity_key], False
        instance = self.backend.create_instance(session, template_code=template_code, name=name, json_addl=json_addl)
        self.claims[identity_key] = instance
        return instance, True

    @contextmanager
    def scope(self, *, commit):
        originals = [(r, deepcopy(vars(r))) for r in self.rows]
        edges, claims = list(self.edges), dict(self.claims)
        try:
            yield self.session
        except Exception:
            if commit:
                for instance, values in originals:
                    vars(instance).clear()
                    vars(instance).update(values)
                self.rows[:] = [instance for instance, _ in originals]
                self.edges[:], self.claims = edges, claims
                self.rollbacks += 1
            raise
        else:
            self.commits += int(commit)

    def artifact(self, label="fixture-artifact", *, prefix=False, **changes):
        payload = {"storage_backend": "s3", "storage_kind": "prefix" if prefix else "object",
            "bucket": "fixture-source", "key": "root/" if prefix else "root/file.txt", "version_id": None,
            "storage_uri": "s3://fixture-source/" + ("root/" if prefix else "root/file.txt"),
            "original_filename": "stable.txt", "location_revision": 1, "size": 5, **changes}
        payload["artifact_identity_key"] = self.service._artifact_identity_key(payload)
        return self.add(row("artifact", label, **payload))

    def share(self, members, *, grants=None, **changes):
        rules = grants if grants is not None else [{"recipient_type": "email", "recipient": READER.email}]
        policy = normalized_policy({"grants": rules, **changes}, share_expiry=changes.get("expires_at"), member_euids=[m.euid for m in members])
        grant_values = policy.pop("grants")
        share = self.add(row("share", f"fixture-share-{len(self.rows)}", **{
            **policy, "status": "active", "policy_revision": 1, "owner_subject": OWNER.subject,
            "owner_email": OWNER.email, "expires_at": None, "target_kind": "mixed_set",
            "member_count": len(members), **changes}))
        with actor():
            self.service._write_share_revision(self.session, share, members, 1, policy=policy)
            self.service._write_grants(self.session, share, grant_values, members, 1)
        for member in members:
            self.link(self.session, parent=member, child=share, relationship_type="has_share")
        return share
