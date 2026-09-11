"""Dewey-specific adoption checks for released TapDB metadata and references."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from daylily_tapdb.external_references import ExternalIdentifierTarget, TapDBObjectTarget
from daylily_tapdb.services.graph_payloads import DagV2GraphContractError, build_graph_v2_payload

from dewey_service.integrations import tapdb_external_references as refs
from dewey_service.services.base import DeweyConflictError
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    TapDBBackend,
    validate_instance_envelope,
)

# This report identifier comes from O's already persisted Dewey acceptance fixture.
PERSISTED_DEWEY_REPORT = "M-DGX-NKDM"


def external_payload(**changes):
    return {
        "properties": {},
        "external_system": "dewey",
        "external_object_type": "artifact",
        "external_object_id": PERSISTED_DEWEY_REPORT,
        "reference_target": {"kind": "tapdb_object"},
        **changes,
    }


def instance(uid, kind, **changes):
    category, object_type = kind
    return SimpleNamespace(
        uid=uid,
        euid=f"fixture-object-{uid}",
        category=category,
        type=object_type,
        subtype="generic",
        version="1.0",
        is_deleted=False,
        domain_code="Z",
        issuer_app_code="dewey",
        tenant_id=None,
        created_dt=datetime(2026, 9, 1, tzinfo=UTC),
        json_addl={"properties": {}},
        **changes,
    )


def relation_fixture():
    source = instance(1, ("data", "artifact"))
    external = instance(2, ("integration", "external_object"))
    external.json_addl = external_payload()
    relation = instance(3, ("integration", "external_object_relation"))
    relation.json_addl = {
        "properties": {},
        "relation_type": "source_record",
        "target_euid": "untrusted-denormalized-source",
        "external_object_euid": "untrusted-denormalized-external",
    }
    rows = [
        SimpleNamespace(
            uid=4,
            child_instance_uid=3,
            parent_instance=source,
            relationship_type="has_external_relation",
            is_deleted=False,
            domain_code="Z",
            issuer_app_code="dewey",
            tenant_id=None,
        ),
        SimpleNamespace(
            uid=5,
            child_instance_uid=3,
            parent_instance=external,
            relationship_type="is_external_relation_for",
            is_deleted=False,
            domain_code="Z",
            issuer_app_code="dewey",
            tenant_id=None,
        ),
    ]

    from tests.support.service_fakes import _FakeReferenceQuery

    for row in rows:
        row.parent_instance_uid = row.parent_instance.uid
    session = SimpleNamespace(
        query=lambda model: _FakeReferenceQuery(
            rows if model is refs.generic_instance_lineage else [source, external], None
        )
    )
    return session, relation, source, external, rows


@pytest.mark.parametrize(
    "system,kind",
    [("dyec", "dayoa_analysis_directory"), ("ursa", "run_directory_analysis_trigger")],
)
@pytest.mark.parametrize("value", ["internal/path/identifier", PERSISTED_DEWEY_REPORT])
def test_operational_identifiers_never_become_public_or_federated_by_shape(system, kind, value):
    target = refs.build_external_target(
        {
            "external_system": system,
            "external_object_type": kind,
            "external_object_id": value,
        }
    )
    assert target == refs.NonFederatedTarget(system, kind, value)


def test_explicit_kind_cannot_override_reviewed_nonfederated_contract():
    with pytest.raises(refs.DeweyExternalReferenceError, match="contradicts"):
        refs.build_external_target(
            external_payload(
                external_system="ursa", external_object_type="run_directory_analysis_trigger"
            )
        )


def test_unknown_kind_requires_explicit_target_and_rejects_bad_descriptors():
    payload = external_payload()
    del payload["reference_target"]
    with pytest.raises(refs.DeweyExternalReferenceError, match="explicit reference_target"):
        refs.build_external_target(payload)
    for descriptor in ({"kind": "guessed"}, {"kind": "tapdb_object", "base_url": "https://unused"}):
        with pytest.raises(ValueError):
            refs.build_external_target({**payload, "reference_target": descriptor})


def test_native_target_identity_does_not_include_kind_descriptor():
    first = refs.build_external_target(external_payload())
    second = refs.build_external_target(external_payload(external_object_type="report"))
    assert isinstance(first, TapDBObjectTarget)
    assert first.identity_key == second.identity_key
    assert first.target_object_kind != second.target_object_kind


def test_public_literature_identifier_has_explicit_public_semantics():
    target = refs.build_external_target(
        {
            "external_system": "doi",
            "external_object_type": "doi",
            "external_object_id": "10.1000/example",
        }
    )
    assert isinstance(target, ExternalIdentifierTarget)
    assert target.scope == "public_global" and target.tenant_id is None


def test_relation_endpoints_and_assertion_ignore_copied_ids_and_replay_stably():
    session, relation, source, external, rows = relation_fixture()
    endpoints = refs.resolve_relation_endpoints(session, relation)
    assert endpoints.source is source and endpoints.external_object is external
    before = refs.build_external_link_spec(relation, endpoints)
    relation.json_addl["target_euid"] = "different-display-only-value"
    relation.json_addl["metadata"] = {"validated_at": "new-presentation-only-time"}
    after = refs.build_external_link_spec(
        relation, refs.resolve_relation_endpoints(session, relation)
    )
    assert before == after
    assert before.asserted_at == relation.created_dt
    assert before.assertion_authority == refs.ASSERTION_AUTHORITY
    assert '"source_lineage_uid":4' in before.assertion_provenance
    rows.append(rows[0])
    with pytest.raises(ValueError, match="exactly one"):
        refs.resolve_relation_endpoints(session, relation)


@pytest.mark.parametrize("failure", ["missing", "deleted", "owner", "tenant"])
def test_relation_endpoint_failures_are_not_rebuilt_from_metadata(failure):
    session, relation, source, external, rows = relation_fixture()
    if failure == "missing":
        rows.pop()
    elif failure == "deleted":
        external.is_deleted = True
    elif failure == "owner":
        source.issuer_app_code = "other"
    else:
        source.tenant_id = "explicit-other-tenant"
    with pytest.raises(ValueError):
        refs.resolve_relation_endpoints(session, relation)


@pytest.mark.parametrize("field", ["domain_code", "issuer_app_code", "tenant_id"])
def test_relation_lineage_scope_must_match_its_endpoints(field):
    session, relation, _, _, rows = relation_fixture()
    setattr(rows[0], field, "other-scope")
    with pytest.raises(ValueError, match="lineage scope mismatch"):
        refs.resolve_relation_endpoints(session, relation)


def test_adapter_invokes_only_native_attach_with_stable_spec(monkeypatch):
    session, relation, source, _, _ = relation_fixture()
    calls = []

    class Native:
        def __init__(self, passed_session):
            assert passed_session is session

        def attach(self, passed_source, spec):
            calls.append((passed_source, spec))
            return SimpleNamespace(status="existing")

    monkeypatch.setattr(refs, "ExternalReferenceService", Native)
    assert refs.attach_external_relation(session, relation).status == "existing"
    assert refs.attach_external_relation(session, relation).status == "existing"
    assert calls[0] == calls[1] and calls[0][0] is source


def test_nonfederated_disposition_never_invokes_native_xrf_writer(monkeypatch):
    session, relation, _, external, _ = relation_fixture()
    external.json_addl = {
        "external_system": "dyec",
        "external_object_type": "dayoa_analysis_directory",
        "external_object_id": "private/analysis/path",
        "properties": {},
    }
    monkeypatch.setattr(
        refs, "ExternalReferenceService", lambda *args: pytest.fail("native writer called")
    )
    result = refs.attach_external_relation(session, relation)
    assert result.status == "non_federated" and result.reference is None and result.lineage is None


@pytest.mark.parametrize("operation", ["attach", "ensure"])
@pytest.mark.parametrize("failure", ["missing", "mismatched"])
def test_existing_relation_never_repairs_authoritative_lineage(service, operation, failure):
    backend = service.backend
    with backend.session_scope(commit=True) as session:
        source = backend.create_instance(
            session, template_code=ARTIFACT_TEMPLATE, name="source", json_addl={}
        )
        external = backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            name="external",
            json_addl=external_payload(),
        )
        relation = backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
            name="relation",
            json_addl={
                "relation_type": "source_record",
                "relation_identity_key": f"artifact:{source.euid}:{external.euid}:source_record",
            },
        )
        backend.create_lineage(
            session,
            parent=external,
            child=relation,
            relationship_type="is_external_relation_for",
        )
        if failure == "mismatched":
            wrong_source = backend.create_instance(
                session, template_code=ARTIFACT_TEMPLATE, name="different source", json_addl={}
            )
            backend.create_lineage(
                session,
                parent=wrong_source,
                child=relation,
                relationship_type="has_external_relation",
            )
        count = len(backend.lineages)
        expected_error = ValueError if failure == "missing" else DeweyConflictError
        with pytest.raises(expected_error, match="exactly one|canonical lineage"):
            if operation == "ensure":
                service._ensure_external_object_relation(
                    session,
                    artifact_instance=source,
                    external_object=external,
                    relation_type="source_record",
                )
            else:
                service.attach_external_object_relation(
                    target_type="artifact",
                    target_euid=source.euid,
                    external_object_euid=external.euid,
                    relation_type="source_record",
                    metadata={},
                    idempotency_key="fixture-attach-existing-corrupt-relation",
                )
        assert len(backend.lineages) == count
        assert not backend.native_assertions


@pytest.mark.parametrize("properties", [None, [], "malformed"])
def test_new_instance_rejects_invalid_properties_before_factory_allocates(properties):
    backend = object.__new__(TapDBBackend)
    backend.factory = SimpleNamespace(create_instance=lambda **kwargs: pytest.fail("allocated"))
    with pytest.raises(ValueError, match="properties"):
        backend.create_instance(
            None, template_code=ARTIFACT_TEMPLATE, name="test", json_addl={"properties": properties}
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"properties": {"target_object_euid": "copied-id"}},
        {"properties": {"external_payload": {"tapdb_graph": []}}},
    ],
)
def test_stored_invalid_envelopes_are_rejected_without_fallback(payload):
    with pytest.raises(ValueError):
        validate_instance_envelope(payload)


def test_native_dag_accepts_retained_properties_and_flat_business_values():
    obj = instance(1, ("data", "artifact_set"))
    obj.json_addl = {"label": "retained business label"}
    with pytest.raises(DagV2GraphContractError, match="properties"):
        build_graph_v2_payload(
            obj, record_type="instance", service_id="dewey", depth=0, max_nodes=1
        )
    obj.json_addl = {"label": "retained business label", "properties": {}}
    validate_instance_envelope(obj.json_addl)
    graph = build_graph_v2_payload(
        obj, record_type="instance", service_id="dewey", depth=0, max_nodes=1
    )
    assert graph["elements"]["nodes"][0]["data"]["properties"] == {}
    assert obj.json_addl["label"] == "retained business label"


def test_batch_endpoint_resolution_uses_two_queries_and_rejects_duplicate_lineage():
    session, relation, source, external, rows = relation_fixture()
    query = session.query
    calls = []

    def counted(model):
        calls.append(model)
        return query(model)

    session.query = counted
    result = refs.resolve_relation_endpoints_many(session, [relation])
    assert result[relation.uid].source is source
    assert result[relation.uid].external_object is external
    assert len(calls) == 2
    rows.append(rows[0])
    with pytest.raises(ValueError, match="exactly one"):
        refs.resolve_relation_endpoints_many(session, [relation])
