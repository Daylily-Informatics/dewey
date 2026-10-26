"""Current-identity token admission and public own-account boundaries."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from dewey_service.recipient_api import attach_recipient_account
from dewey_service.registry_access import Principal, RegistryPrincipalMiddleware, principal, principal_context
from dewey_service.services.base import DeweyNotFoundError
from dewey_service.services.registry import RegistryServiceMixin
from dewey_service.share_context import require_share_context, share_context_context


ACTOR = Principal(subject="user-fixture", email="manager@example.test", roles=("ADMIN",),
    email_verified=True, identity_grant_id="browser-binding-fixture", identity_revision=3,
    identity_expires_at="2099-01-01T00:00:00+00:00")
INGRESS = {"public_recipient": True, "managed_origin": True, "request_id": "request-fixture"}


class Query:
    def __init__(self, rows):
        self.rows = list(rows)
        self.clauses = []

    def filter(self, *clauses):
        self.clauses.extend(clauses)
        for clause in clauses:
            values = list(clause.compile().params.values())
            for field in ("subject", "token_sha256"):
                if field in values:
                    self.rows = [r for r in self.rows if r.json_addl.get(field) == clause.right.value]
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class Backend:
    domain_code = "fixture"

    def __init__(self):
        self.rows, self.events = [], []
        self.templates = SimpleNamespace(get_template=lambda *args, **kwargs: SimpleNamespace(uid=1))

    @contextmanager
    def session_scope(self, *, commit):
        yield self
        if commit:
            self.events.append("commit")

    def query(self, *args):
        return Query(self.rows)

    def _template_query(self, *args, **kwargs):
        return Query(self.rows)

    def create_instance(self, session, *, template_code, name, json_addl):
        now = datetime.now(timezone.utc)
        row = SimpleNamespace(euid="token-fixture-" + str(len(self.rows) + 1), uid=len(self.rows) + 1,
            name=name, json_addl={"properties": {}, **json_addl}, created_dt=now, modified_dt=now)
        self.rows.append(row)
        return row

    def find_by_euid(self, session, *, template_code, euid, **kwargs):
        return next((row for row in self.rows if row.euid == euid), None)

    def update_instance_json(self, session, row, changes):
        row.json_addl.update(changes)
        self.events.append("update")


@pytest.fixture
def tokens(monkeypatch):
    import dewey_service.recipient_identity as identity
    import dewey_service.settings as settings
    service = RegistryServiceMixin()
    service.backend = Backend()
    personal = {"grant_id": "personal-binding-fixture", "revision": 1, "kind": "personal",
        "canonical_user_id": ACTOR.subject, "email": ACTOR.email, "email_verified": True,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
    calls = []
    def mint(settings, **kwargs):
        calls.append(kwargs)
        return dict(personal)
    monkeypatch.setattr(settings, "get_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(identity, "mint_personal_identity", mint)
    monkeypatch.setattr(identity, "verify_recipient_binding", lambda *args, **kwargs: dict(personal))
    monkeypatch.setattr(identity, "revoke_recipient_identity", lambda *args, **kwargs: {"status": "revoked"})
    return service, personal, calls, identity


def test_public_token_mint_forces_read_only_and_hashes_secret(tokens):
    service, personal, calls, identity = tokens
    with principal_context(ACTOR):
        issued = service.issue_registry_token(name="CLI fixture", lifetime_days=30, role="READ_ONLY", recipient_only=True)
    row = service.backend.rows[0]
    assert calls == [{"grant_id": "browser-binding-fixture", "revision": 3, "lifetime_days": 30}]
    assert row.json_addl["roles"] == ["READ_ONLY"] and row.json_addl["recipient_only"] is True
    assert row.json_addl["token_sha256"] == sha256(issued["token"].encode()).hexdigest()
    assert issued["token"] not in str(row.json_addl)
    assert issued["expires_at"] == personal["expires_at"] and issued["display_once"] is True
    actor = service.authenticate_registry_token(issued["token"])
    assert actor.roles == ("READ_ONLY",) and actor.recipient_only and actor.email_verified
    assert actor.identity_grant_id == "personal-binding-fixture"


def test_private_manager_token_preserves_reviewed_role_and_rechecks_identity(tokens, monkeypatch):
    service, personal, calls, identity = tokens
    with principal_context(ACTOR):
        issued = service.issue_registry_token(name="Manager fixture", lifetime_days=1, role="READ_WRITE")
    actor = service.authenticate_registry_token(issued["token"])
    assert actor.roles == ("READ_WRITE",) and not actor.recipient_only
    checks = []
    def revoked(settings, **kwargs):
        checks.append(kwargs)
        raise HTTPException(401, "Provider revoked the current identity")
    monkeypatch.setattr(identity, "verify_recipient_binding", revoked)
    with pytest.raises(HTTPException) as failure:
        service.authenticate_registry_token(issued["token"])
    assert failure.value.status_code == 401
    assert checks == [{"grant_id": "personal-binding-fixture", "revision": 1}]


def test_token_cannot_change_verified_email_or_canonical_user(tokens, monkeypatch):
    service, personal, calls, identity = tokens
    with principal_context(ACTOR):
        issued = service.issue_registry_token(name="Fixture", recipient_only=True)
    monkeypatch.setattr(identity, "verify_recipient_binding", lambda *args, **kwargs: {**personal, "email": "other@example.test"})
    with pytest.raises(HTTPException) as failure:
        service.authenticate_registry_token(issued["token"])
    assert failure.value.status_code == 401


def test_unverified_user_cannot_mint_and_old_unbound_token_cannot_share(tokens):
    service, personal, calls, identity = tokens
    with principal_context(replace(ACTOR, email_verified=False, identity_grant_id="")):
        with pytest.raises(HTTPException) as failure:
            service.issue_registry_token(name="Fixture")
    assert failure.value.status_code == 401 and not calls
    with principal_context(ACTOR):
        issued = service.issue_registry_token(name="Fixture")
    service.backend.rows[0].json_addl.pop("identity_grant_id")
    actor = service.authenticate_registry_token(issued["token"])
    assert actor.email_verified is False
    with principal_context(actor), share_context_context(INGRESS), pytest.raises(HTTPException):
        require_share_context()


def test_own_only_listing_and_revocation_apply_even_to_admin(tokens):
    service, personal, calls, identity = tokens
    with principal_context(ACTOR):
        mine = service.issue_registry_token(name="Mine")
        other = service.issue_registry_token(name="Other fixture")
        service.backend.rows[-1].json_addl.update(subject="other-user-fixture", email="other@example.test")
        assert [item["euid"] for item in service.registry_tokens(own_only=True)] == [mine["euid"]]
        assert len(service.registry_tokens()) == 2
        with pytest.raises(DeweyNotFoundError):
            service.revoke_registry_token(other["euid"], own_only=True)
    assert service.backend.rows[-1].json_addl["status"] == "active"


def test_local_token_revocation_commits_before_broker_failure(tokens, monkeypatch):
    service, personal, calls, identity = tokens
    with principal_context(ACTOR):
        issued = service.issue_registry_token(name="Fixture")
        def unavailable(settings, **kwargs):
            assert service.backend.events[-1] == "commit"
            assert service.backend.rows[0].json_addl["status"] == "revoked"
            raise HTTPException(503, "Broker unavailable")
        monkeypatch.setattr(identity, "revoke_recipient_identity", unavailable)
        with pytest.raises(HTTPException) as failure:
            service.revoke_registry_token(issued["euid"], own_only=True)
    assert failure.value.status_code == 503
    with pytest.raises(HTTPException) as denied:
        service.authenticate_registry_token(issued["token"])
    assert denied.value.status_code == 401


def test_public_api_forces_own_only_and_rejects_roles_or_excess_lifetime():
    calls = []
    service = SimpleNamespace(registry_tokens=lambda **kwargs: calls.append(("list", kwargs)) or [],
        issue_registry_token=lambda **kwargs: calls.append(("issue", kwargs)) or {"euid": "token-fixture"},
        revoke_registry_token=lambda euid, **kwargs: calls.append(("revoke", kwargs)) or {"status": "revoked"})
    app = FastAPI()
    @app.middleware("http")
    async def context(request, call_next):
        with principal_context(ACTOR), share_context_context(INGRESS):
            return await call_next(request)
    attach_recipient_account(app, service, None)
    with TestClient(app) as client:
        assert client.get("/api/v2/recipient/tokens").status_code == 200
        assert client.post("/api/v2/recipient/tokens", json={"name": "Fixture", "lifetime_days": 30}).status_code == 201
        assert client.post("/api/v2/recipient/tokens/token-fixture/revoke").status_code == 200
        assert client.post("/api/v2/recipient/tokens", json={"name": "Fixture", "role": "ADMIN"}).status_code == 422
        assert client.post("/api/v2/recipient/tokens", json={"name": "Fixture", "lifetime_days": 31}).status_code == 422
    assert calls == [("list", {"own_only": True}),
        ("issue", {"name": "Fixture", "lifetime_days": 30, "role": "READ_ONLY", "recipient_only": True}),
        ("revoke", {"own_only": True})]


def test_recipient_only_middleware_blocks_management_and_auth_flow_survives_revocation(monkeypatch):
    import dewey_service.auth as auth
    import dewey_service.recipient_identity as identity
    profile = {"sub": ACTOR.subject, "email": ACTOR.email, "roles": ["READ_ONLY"], "groups": [],
        "identity_grant_id": ACTOR.identity_grant_id, "identity_revision": 3, "recipient_only": True}
    monkeypatch.setattr(auth, "_load_ui_profile", lambda request: profile)
    current = {"canonical_user_id": ACTOR.subject, "email": ACTOR.email, "email_verified": True,
        "grant_id": ACTOR.identity_grant_id, "revision": 3, "expires_at": ACTOR.identity_expires_at}
    checks = []
    def verify(settings, **kwargs):
        checks.append(kwargs)
        return current
    monkeypatch.setattr(identity, "verify_recipient_binding", verify)
    app = FastAPI()
    app.state.settings = SimpleNamespace(registry_internal_domains=[], registry_service_principals={}, api_tokens=lambda: [])
    app.add_middleware(RegistryPrincipalMiddleware)
    @app.get("/fetch/share-fixture/file.txt")
    def content():
        return {"email_verified": principal().email_verified, "recipient_only": principal().recipient_only}
    @app.get("/api/v1/registry/shares")
    def management():
        pytest.fail("Recipient-only principal reached a management handler")
    @app.get("/auth/login")
    def login():
        return JSONResponse({"login": "ready"})
    with TestClient(app) as client:
        assert client.get("/fetch/share-fixture/file.txt").json() == {"email_verified": True, "recipient_only": True}
        assert client.get("/api/v1/registry/shares").status_code == 403
        assert len(checks) == 2
        def revoked(settings, **kwargs):
            raise HTTPException(401, "Revoked identity")
        monkeypatch.setattr(identity, "verify_recipient_binding", revoked)
        assert client.get("/fetch/share-fixture/file.txt").status_code == 401
        assert client.get("/auth/login").status_code == 200
