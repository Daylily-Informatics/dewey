"""HTTP wiring tests; authorization policy is exercised by its dedicated tests.

These apps register the production routes and explicitly override the principal
dependency. No database, broker, storage provider, or browser is contacted.
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

import dewey_service.registry_api as registry_api
from dewey_service.registry_access import Principal, principal


ACTOR = Principal(subject="routing-fixture-user", email="recipient@example.test",
    roles=("READ_WRITE",), email_verified=True)
PRIVATE_HEADERS = {"X-Fixture-Private": "routing-fixture-assertion"}


class RecordingRegistry:
    methods = frozenset({"list_share_aliases", "claim_share_slug", "revoke_share_slug",
        "rebind_artifact_location", "sharing_report", "sharing_inventory", "share_registry",
        "preview_share_selection"})

    def __init__(self):
        self.calls = []
        self.share_status = 201

    def __getattr__(self, name):
        if name not in self.methods:
            raise AttributeError(name)

        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            result = {"operation": name}
            return (self.share_status, result) if name == "share_registry" else result

        return record


@pytest.fixture
def routing():
    service = RecordingRegistry()
    app = FastAPI()
    app.state.service = service
    app.state.settings = SimpleNamespace(share_trusted_proxy_peer="testclient",
        share_ingress_assertion="routing-fixture-assertion",
        share_ingress_assertion_header="X-Fixture-Private")
    state = SimpleNamespace(actor=ACTOR, public=True, private=False)
    # Route forwarding is deliberately isolated from independently tested auth.
    app.dependency_overrides[principal] = lambda: ACTOR

    @app.middleware("http")
    async def authorized_fixture(request, call_next):
        request.state.registry_principal = state.actor
        request.state.public_recipient = state.public
        request.state.trusted_tailnet = state.private
        return await call_next(request)

    templates = Jinja2Templates(directory=str(Path(registry_api.__file__).parent / "templates"))
    templates.env.globals["static_url"] = lambda filename: "/static/" + filename
    registry_api.attach_registry_api(app, templates=templates)
    with TestClient(app, base_url="https://dewey.example.test") as client:
        yield SimpleNamespace(client=client, service=service, state=state)


def test_alias_routes_forward_identifier_slug_and_policy_revision(routing):
    path = "/api/v1/registry/shares/share-fixture/aliases"
    assert routing.client.get(path).json() == {"operation": "list_share_aliases"}
    claimed = routing.client.post(path, json={"slug": "fixture-report", "policy_revision": 7})
    assert claimed.status_code == 201
    assert claimed.json() == {"operation": "claim_share_slug"}
    revoked = routing.client.post(path + "/fixture-report/revoke", json={"policy_revision": 8})
    assert revoked.status_code == 200
    assert revoked.json() == {"operation": "revoke_share_slug"}
    assert routing.service.calls == [
        ("list_share_aliases", ("share-fixture",), {}),
        ("claim_share_slug", ("share-fixture", "fixture-report"), {"policy_revision": 7}),
        ("revoke_share_slug", ("share-fixture", "fixture-report"), {"policy_revision": 8})]
    assert revoked.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("version_id", [None, "destination-version-fixture"])
def test_location_rebind_forwards_equivalence_inputs_and_revision(routing, version_id):
    body = {"storage_uri": "s3://fixture-bucket/reports/", "expected_location_revision": 3,
        "reason": "Move registered location after equivalence review", "version_id": version_id}
    response = routing.client.post("/api/v1/records/record-fixture/location-rebind", json=body)
    assert response.status_code == 200
    assert response.json() == {"operation": "rebind_artifact_location"}
    assert routing.service.calls == [("rebind_artifact_location", ("record-fixture",), body)]


@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("explicit_indefinite", [False, True])
def test_create_and_preview_preserve_omitted_versus_null_expiry(routing, preview, explicit_indefinite):
    body = {"allowed_users": ["recipient@example.test"], "content_mode": "download"}
    if explicit_indefinite:
        body["expires_at"] = None
    path = "/api/v1/records/record-fixture/shares" + ("/preview" if preview else "")
    response = routing.client.post(path, json=body, headers={"Idempotency-Key": "fixture-create-once"})
    method = "preview_share_selection" if preview else "share_registry"
    assert response.status_code == (200 if preview else 201)
    assert response.json() == {"operation": method}
    assert routing.service.calls == [(method, ("record-fixture", body),
        {} if preview else {"idempotency_key": "fixture-create-once"})]
    forwarded = routing.service.calls[0][1][1]
    assert ("expires_at" in forwarded) is explicit_indefinite
    assert "lifetime_days" not in forwarded


def test_share_create_preserves_service_idempotent_replay_status(routing):
    routing.service.share_status = 200
    response = routing.client.post("/api/v1/records/record-fixture/shares",
        json={"audience": "public_registered"}, headers={"Idempotency-Key": "fixture-replayed"})
    assert response.status_code == 200
    assert routing.service.calls == [("share_registry", ("record-fixture", {"audience": "public_registered"}),
        {"idempotency_key": "fixture-replayed"})]


FILTERS = {"owner_subject": "owner-fixture", "status": "active", "audience": "public_registered",
    "content_mode": "www", "created_from": "2026-10-01T00:00:00Z",
    "created_before": "2026-10-20T00:00:00Z", "older_than_days": 4, "never_accessed": True}


@pytest.mark.parametrize("inventory", [False, True])
def test_sharing_report_and_inventory_forward_all_filters_and_snapshot_pagination(routing, inventory):
    params = dict(FILTERS)
    if inventory:
        params.update(page=3, page_size=200, observed_at="2026-10-26T01:00:00Z",
            expected_inventory_sha256="a" * 64)
    else:
        params.update(starts_at="2026-10-01T00:00:00Z", ends_at="2026-10-26T00:00:00Z")
    method = "sharing_inventory" if inventory else "sharing_report"
    response = routing.client.get("/api/v1/registry/" + method.replace("_", "-"), params=params)
    assert response.status_code == 200
    assert response.json() == {"operation": method}
    assert routing.service.calls == [(method, (), params)]


@pytest.mark.parametrize("inventory", [False, True])
def test_sharing_report_and_inventory_defaults_do_not_invent_filters(routing, inventory):
    method = "sharing_inventory" if inventory else "sharing_report"
    params = {} if inventory else {"starts_at": "2026-10-01T00:00:00Z"}
    response = routing.client.get("/api/v1/registry/" + method.replace("_", "-"), params=params)
    assert response.status_code == 200
    expected = {key: None for key in FILTERS if key != "never_accessed"}
    expected["never_accessed"] = False
    if inventory:
        expected.update(page=1, page_size=100, observed_at=None, expected_inventory_sha256=None)
    else:
        expected.update(starts_at=params["starts_at"], ends_at=None)
    assert routing.service.calls == [(method, (), expected)]


@pytest.mark.parametrize("method,path,options", [
    ("GET", "/api/v1/registry/sharing-report", {}),
    ("GET", "/api/v1/registry/sharing-report", {"params": {"starts_at": "2026-10-01", "older_than_days": -1}}),
    ("GET", "/api/v1/registry/sharing-inventory", {"params": {"page": 0}}),
    ("GET", "/api/v1/registry/sharing-inventory", {"params": {"page_size": 201}}),
    ("POST", "/api/v1/registry/shares/share-fixture/aliases", {"json": {"slug": "fixture-report", "policy_revision": 0}}),
    ("POST", "/api/v1/registry/shares/share-fixture/aliases/fixture-report/revoke", {"json": {}}),
    ("POST", "/api/v1/records/record-fixture/location-rebind", {"json": {"storage_uri": "s3://fixture/path",
        "expected_location_revision": 1, "reason": ""}}),
    ("POST", "/api/v1/records/record-fixture/shares", {"json": {}}),
    ("POST", "/api/v1/records/record-fixture/shares/preview", {"json": {"allowed_groups": ["admins"]}}),
])
def test_invalid_sharing_http_contract_never_calls_service(routing, method, path, options):
    assert routing.client.request(method, path, **options).status_code == 422
    assert routing.service.calls == []


@pytest.mark.parametrize("public,actor", [(True, None), (True, ACTOR),
    (False, replace(ACTOR, recipient_only=True))])
def test_legacy_recipient_page_redirects_to_managed_fetch(routing, public, actor):
    routing.state.public, routing.state.actor = public, actor
    response = routing.client.get("/shares/share-fixture", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/fetch/share-fixture"
    assert routing.service.calls == []


def test_private_management_identity_retains_legacy_share_management_page(routing):
    routing.state.public, routing.state.private = False, True
    response = routing.client.get("/shares/share-fixture", headers=PRIVATE_HEADERS, follow_redirects=False)
    assert response.status_code == 200
    assert 'data-section="Share"' in response.text
    assert 'data-euid="share-fixture"' in response.text
    assert routing.service.calls == []


@pytest.mark.parametrize("actor", [None, replace(ACTOR, email_verified=False)])
def test_recipient_account_requires_verified_identity_and_preserves_deep_return(routing, actor):
    routing.state.actor = actor
    response = routing.client.get("/recipient/account", follow_redirects=False)
    assert response.status_code == 303
    location = urlsplit(response.headers["location"])
    assert location.path == "/auth/login"
    assert parse_qs(location.query) == {"next": ["/recipient/account"]}
    assert routing.service.calls == []


def test_recipient_account_rejects_service_identity(routing):
    routing.state.actor = replace(ACTOR, service=True)
    response = routing.client.get("/recipient/account", follow_redirects=False)
    assert response.status_code == 403
    assert response.json() == {"detail": "A registered recipient is required"}
    assert routing.service.calls == []


def test_recipient_account_renders_verified_email_without_password_collection(routing):
    routing.state.actor = replace(ACTOR, roles=("READ_ONLY",), recipient_only=True)
    response = routing.client.get("/recipient/account")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Signed in as recipient@example.test." in response.text
    assert 'name="lifetime_days"' in response.text and 'max="30"' in response.text
    assert 'type="password"' not in response.text and 'name="password"' not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert routing.service.calls == []
