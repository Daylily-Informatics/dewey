"""Registry validation and authorization contracts missing from the release gate.

Native in-memory persistence retains production policy and attribution. SQL
compilation assertions check predicate construction without pretending that the
fixture implements a PostgreSQL engine.
"""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from daylily_tapdb import generic_instance
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from dewey_service.registry_access import (
    OPERATION_TEMPLATE,
    POLICY_TEMPLATE,
    TOKEN_TEMPLATE,
    Principal,
    RegistryPrincipalMiddleware,
    direct_record_clause,
    principal_context,
    validate_policy,
    visibility_clause,
)
from dewey_service.tapdb_backend import normalize_instance_payload
from tests.support.service_fakes import _FakeReferenceQuery
from tests.support.service_fakes import backend as backend
from tests.support.service_fakes import service as service
from tests.support.service_fakes import storage as storage

PERSON = Principal(
    subject="registry-fixture-person",
    email="owner@example.test",
    roles=("READ_WRITE",),
    internal=True,
    email_verified=True,
    identity_grant_id="registry-fixture-binding",
    identity_revision=2,
    identity_expires_at="2099-01-01T00:00:00+00:00",
)
DEFAULTS = {
    "share_lifetime_days": 30,
    "delivery_lifetime_seconds": 300,
    "listing_cache_ttl_seconds": 30,
}


def _defaults_row(service, **changes):
    with service.backend.session_scope(commit=True) as session:
        return service.backend.create_instance(
            session,
            template_code=POLICY_TEMPLATE,
            name="Explicit registry defaults fixture",
            json_addl={"policy_kind": "service_defaults", **DEFAULTS, **changes},
        )


@pytest.mark.parametrize("ttl", [True, -1, 301, "30"])
def test_persisted_cache_ttl_rejects_boolean_out_of_range_and_text(service, ttl):
    row = _defaults_row(service, listing_cache_ttl_seconds=ttl)
    original = deepcopy(row.json_addl)
    with pytest.raises(HTTPException) as error:
        service.registry_defaults()
    assert error.value.status_code == 503
    assert error.value.detail == "Invalid persisted listing cache TTL"
    assert row.json_addl == original


@pytest.mark.parametrize("changes", [{}, {"unregistered_setting": 1}])
def test_default_update_rejects_empty_or_unknown_configuration_before_write(service, changes):
    row = _defaults_row(service)
    original, calls = deepcopy(row.json_addl), len(service.backend.commits)
    with pytest.raises(ValueError, match="Only share lifetime"):
        service.update_registry_defaults(changes)
    assert row.json_addl == original
    assert len(service.backend.commits) == calls
    assert service.backend.instances.get(OPERATION_TEMPLATE, []) == []


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"share_lifetime_days": 0}, "Share lifetime exceeds"),
        ({"share_lifetime_days": True}, "Share lifetime exceeds"),
        ({"delivery_lifetime_seconds": 3601}, "Delivery lifetime must"),
        ({"delivery_lifetime_seconds": True}, "Delivery lifetime must"),
        ({"listing_cache_ttl_seconds": -1}, "Listing cache TTL must"),
        ({"listing_cache_ttl_seconds": True}, "Listing cache TTL must"),
    ],
)
def test_invalid_default_changes_preserve_native_policy_and_have_no_event(
    service, changes, message
):
    row = _defaults_row(service)
    original, revision = deepcopy(row.json_addl), row.record_revision
    with pytest.raises(ValueError, match=message):
        service.update_registry_defaults(changes)
    assert row.json_addl == original and row.record_revision == revision
    assert service.backend.external_locks == [("registry.defaults", "service_defaults")]
    assert service.backend.instances.get(OPERATION_TEMPLATE, []) == []


def test_default_update_records_native_event_and_disables_cache_explicitly(service, storage):
    row = _defaults_row(service)
    invalidations = []
    storage.listing_cache = SimpleNamespace(invalidate=lambda: invalidations.append(True))
    changes = {
        "share_lifetime_days": service.share_max_lifetime_days,
        "delivery_lifetime_seconds": 3600,
        "listing_cache_ttl_seconds": 0,
    }
    result = service.update_registry_defaults(changes)
    assert result == changes == service.registry_defaults()
    assert invalidations == [True]
    events = service.backend.list_children(
        service.backend, parent=row, relationship_type="has_storage_operation"
    )
    assert len(events) == 1
    event = normalize_instance_payload(events[0])
    assert event["operation"] == "registry.defaults.updated"
    assert event["actor"] == "fixture-service-operator"
    assert event["status"] == "complete"


@pytest.mark.parametrize("field", ["edit_users", "share_users"])
@pytest.mark.parametrize("value", ["owner@example.test", ["missing-domain"], [None]])
def test_delegation_policy_rejects_non_email_lists(field, value):
    with pytest.raises(ValueError, match=f"{field} must contain email addresses"):
        validate_policy({field: value})


def test_delegation_and_recipient_policy_normalizes_without_mutating_input():
    changes = {
        "edit_users": [" Editor@Example.Test ", "editor@example.test"],
        "share_users": ["Sharer@Example.Test"],
        "download": {
            "scope": "recipients",
            "users": [" Reader@Example.Test ", "reader@example.test"],
            "domains": [" Outside.Example "],
            "groups": [" CaseSensitiveGroup "],
        },
        "metadata": {"scope": "private"},
    }
    original = deepcopy(changes)
    result = validate_policy(changes)
    assert changes == original
    assert result == {
        "edit_users": ["editor@example.test"],
        "share_users": ["sharer@example.test"],
        "download": {
            "scope": "recipients",
            "users": ["reader@example.test"],
            "domains": ["outside.example"],
            "groups": ["CaseSensitiveGroup"],
        },
        "metadata": {"scope": "private", "users": [], "domains": [], "groups": []},
    }


@pytest.mark.parametrize("field", ["users", "domains", "groups"])
@pytest.mark.parametrize("value", ["not-a-list", [" "], [17]])
def test_audience_rejects_non_list_or_empty_recipient_values(field, value):
    with pytest.raises(ValueError, match=f"download.{field} must be a list of nonempty strings"):
        validate_policy({"download": {"scope": "recipients", field: value}})


@pytest.mark.parametrize(
    "recipients",
    [{"users": ["reader@example.test"]}, {"domains": ["outside.example"]}, {"groups": ["team"]}],
)
def test_private_policy_cannot_hide_additional_recipient_grants(recipients):
    with pytest.raises(ValueError, match="A private audience cannot include additional recipients"):
        validate_policy({"metadata": {"scope": "private", **recipients}})


@pytest.mark.parametrize("actor", [None, replace(PERSON, recipient_only=True)])
def test_unbound_and_recipient_only_actors_have_no_direct_record_capability(actor):
    with principal_context(actor):
        for capability in ("metadata", "download", "edit", "share"):
            condition = direct_record_clause(None, generic_instance, capability)
            assert str(condition.compile(dialect=postgresql.dialect())) == "false"


@pytest.mark.parametrize("types", [("storage_operation",), ("external_object",)])
def test_native_visibility_keeps_share_internals_closed_and_external_links_scoped(types):
    with principal_context(PERSON):
        condition = visibility_clause(None, generic_instance, types=types)
    compiled = condition.compile(dialect=postgresql.dialect())
    protected = next(
        set(value)
        for value in compiled.params.values()
        if isinstance(value, list) and "share_event" in value
    )
    assert {
        "share",
        "share_grant",
        "share_event",
        "share_revision",
        "share_alias",
        "artifact_location_revision",
    } <= protected
    if types == ("external_object",):
        assert "EXISTS" in str(compiled)
        assert "is_external_relation_for" in compiled.params.values()
        assert "has_external_relation" in compiled.params.values()
    else:
        assert "EXISTS" not in str(compiled)


@pytest.mark.parametrize(
    "op,value,sql_fragment,expected_bound",
    [
        ("eq", "fixture", "generic_instance.name =", "fixture"),
        ("neq", "fixture", "generic_instance.name !=", "fixture"),
        ("in", ["one", "two"], "generic_instance.name IN", ["one", "two"]),
        ("in", "one", "generic_instance.name IN", ["one"]),
        ("contains", "Mix%_", "lower(generic_instance.name) LIKE", "mix/%/_"),
        ("exists", True, "generic_instance.name IS NOT NULL", None),
        ("exists", False, "generic_instance.name IS NULL", None),
        ("gte", "fixture", "generic_instance.name >=", "fixture"),
        ("lte", "fixture", "generic_instance.name <=", "fixture"),
    ],
)
def test_direct_search_filters_compile_bound_predicates_without_interpolating_values(
    monkeypatch, service, op, value, sql_fragment, expected_bound
):
    # Keep the real registry scope/visibility and the existing query evaluator.
    # There are no stored records: this test checks the emitted SQL contract.
    captured = []
    original = _FakeReferenceQuery.filter

    def capture(query, *conditions):
        captured.extend(conditions)
        return original(query, *conditions)

    monkeypatch.setattr(_FakeReferenceQuery, "filter", capture)
    result = service.search_registry(
        {
            "scopes": ["artifact"],
            "property_filters": [{"path": "name", "op": op, "value": value}],
        }
    )
    assert result["items"] == [] and result["total"] == 0 and result["has_more"] is False
    compiled = captured[-1].compile(dialect=postgresql.dialect())
    assert sql_fragment in str(compiled)
    if expected_bound is not None:
        assert expected_bound in compiled.params.values()
    else:
        assert compiled.params == {}


def test_non_admin_share_search_rejects_recipient_private_property_filters(service):
    with principal_context(PERSON), pytest.raises(ValueError, match="restricted to administrators"):
        service.search_registry(
            {
                "scopes": ["share"],
                "property_filters": [{"path": "denied_emails", "op": "contains", "value": "@"}],
            }
        )
    assert not any(service.backend.commits)


@pytest.mark.parametrize(
    "actor,name,days",
    [
        (replace(PERSON, service=True), "Fixture", 1),
        (replace(PERSON, email=""), "Fixture", 1),
        (PERSON, " ", 1),
        (PERSON, "Fixture", 0),
        (PERSON, "Fixture", 31),
    ],
)
def test_personal_token_input_rejection_precedes_broker_or_native_write(
    monkeypatch, service, actor, name, days
):
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid token input reached the identity broker")

    monkeypatch.setattr("dewey_service.recipient_identity.mint_personal_identity", unexpected)
    with principal_context(actor), pytest.raises(ValueError, match="lifetime of 1..30 days"):
        service.issue_registry_token(name=name, lifetime_days=days)
    assert service.backend.commits == []
    assert service.backend.instances == {}


@pytest.mark.parametrize(
    "changed", [{"email": "other@example.test"}, {"canonical_user_id": "other-user"}]
)
def test_minted_identity_must_still_match_the_issuing_user(monkeypatch, service, changed):
    binding = {
        "email": PERSON.email,
        "canonical_user_id": PERSON.subject,
        **changed,
    }
    calls = []

    def mint(_settings, **kwargs):
        calls.append(kwargs)
        return binding

    monkeypatch.setattr("dewey_service.recipient_identity.mint_personal_identity", mint)
    with principal_context(PERSON), pytest.raises(HTTPException) as error:
        service.issue_registry_token(name="Fixture", lifetime_days=1)
    assert error.value.status_code == 401
    assert error.value.detail == "Recipient identity changed; sign in again"
    assert calls == [{"grant_id": PERSON.identity_grant_id, "revision": 2, "lifetime_days": 1}]
    assert service.backend.instances == {}


def test_revoking_legacy_unbound_token_is_local_and_does_not_contact_identity_broker(
    monkeypatch, service
):
    with service.backend.session_scope(commit=True) as session:
        token = service.backend.create_instance(
            session,
            template_code=TOKEN_TEMPLATE,
            name="Legacy token fixture",
            json_addl={"subject": PERSON.subject, "status": "active", "token_sha256": "a" * 64},
        )
    revision = token.record_revision

    def unexpected(*args, **kwargs):
        pytest.fail("An unbound legacy token has no broker identity to revoke")

    monkeypatch.setattr("dewey_service.recipient_identity.revoke_recipient_identity", unexpected)
    assert service.revoke_registry_token(token.euid) == {"euid": token.euid, "status": "revoked"}
    assert token.json_addl["status"] == "revoked" and token.json_addl["revoked_at"]
    assert token.record_revision > revision


@pytest.mark.parametrize(
    "changed", [{"email": "other@example.test"}, {"canonical_user_id": "other-user"}]
)
def test_request_identity_change_is_denied_before_registry_handler(monkeypatch, changed):
    profile = {
        "email": PERSON.email,
        "sub": PERSON.subject,
        "roles": list(PERSON.roles),
        "groups": [],
        "identity_grant_id": PERSON.identity_grant_id,
        "identity_revision": 2,
    }
    monkeypatch.setattr("dewey_service.auth._load_ui_profile", lambda request: profile)
    monkeypatch.setattr(
        "dewey_service.recipient_identity.verify_recipient_binding",
        lambda settings, **kwargs: {
            "email": PERSON.email,
            "canonical_user_id": PERSON.subject,
            **changed,
        },
    )
    app = FastAPI()
    app.state.settings = SimpleNamespace(registry_internal_domains=[])
    app.add_middleware(RegistryPrincipalMiddleware)

    @app.get("/api/v1/registry/search")
    def forbidden_handler():
        pytest.fail("A changed identity reached the registry handler")

    with TestClient(app) as client:
        response = client.get("/api/v1/registry/search")
    assert response.status_code == 401
    assert response.json()["detail"] == "Recipient identity changed; sign in again"
