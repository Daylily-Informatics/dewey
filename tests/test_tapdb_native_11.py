"""Focused 11.0.2 transaction and optimistic concurrency contracts."""
from types import SimpleNamespace
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from daylily_tapdb.revisions import RevisionConflict
from dewey_service.audit import transaction_attribution, request_audit_context, qeo_dispatch_attribution_context, explicit_attribution_context
from dewey_service.registry_access import Principal, principal_context
from dewey_service.tapdb_backend import TapDBBackend
from dewey_service.integrations.tapdb_external_references import attach_observed_reference

SETTINGS = SimpleNamespace(auth_mode="external_broker", external_broker_handoff_exchange_url="https://login.example.test/handoff")


def test_human_subject_and_service_are_distinct_and_fresh():
    with request_audit_context(), principal_context(Principal(subject="canonical-subject", email="display@example.test")):
        first = transaction_attribution(SETTINGS, "update", commit=True)
        second = transaction_attribution(SETTINGS, "update", commit=True)
    assert first.actor_kind == "human"
    assert first.actor_subject == "canonical-subject"
    assert first.request_id == second.request_id
    assert first.operation_id != second.operation_id
    with pytest.raises(ValueError, match="verified"):
        transaction_attribution(SETTINGS, "outbox", commit=True)
    assert transaction_attribution(SETTINGS, "read", commit=False) is None
    with qeo_dispatch_attribution_context():
        background = transaction_attribution(SETTINGS, "outbox", commit=True)
    assert background.actor_kind == "service"
    assert background.actor_subject == "dewey:qeo-dispatch"
    with request_audit_context(), pytest.raises(ValueError, match="verified"):
        transaction_attribution(SETTINGS, "update", commit=True)


def test_observed_revision_is_forwarded_without_retry(monkeypatch):
    calls = []
    def update(*args, **kwargs):
        calls.append(kwargs)
        raise RevisionConflict("stale revision")
    monkeypatch.setattr("dewey_service.tapdb_backend.update_object", update)
    backend = object.__new__(TapDBBackend)
    backend.connection = SimpleNamespace(app_username="display-only")
    obj = SimpleNamespace(euid="owner-returned-object", record_revision=6)
    with pytest.raises(RevisionConflict):
        backend.update_persisted_fields(None, obj, {"name": "proposal"})
    assert len(calls) == 1
    assert calls[0]["expected_revision"] == 6


def test_pooled_transactions_have_separate_wrappers_and_conflicts_are_409(monkeypatch):
    connections = []
    @contextmanager
    def scope(**kwargs):
        yield SimpleNamespace(get_bind=lambda: None)
    def connect(path):
        conn = SimpleNamespace(session_scope=scope)
        connections.append(conn)
        return conn
    monkeypatch.setattr("dewey_service.tapdb_backend.get_db", connect)
    monkeypatch.setattr("dewey_service.performance.instrument_engine", lambda engine: None)
    backend = object.__new__(TapDBBackend)
    backend.config_path = "/explicit/config.yaml"
    backend.settings = SETTINGS
    backend.connection = SimpleNamespace(app_username="dewey")
    backend.observability = None
    with qeo_dispatch_attribution_context(), pytest.raises(HTTPException) as caught:
        with backend.session_scope(commit=True):
            raise RevisionConflict("stale revision")
    assert caught.value.status_code == 409
    with qeo_dispatch_attribution_context():
        with backend.session_scope(commit=True): pass
    assert len(connections) == 2
    assert connections[0] is not connections[1]
    assert connections[0].attribution.request_id != connections[1].attribution.request_id


@pytest.mark.parametrize("revision", [None, 12])
def test_reference_attach_uses_observed_lineage(monkeypatch, revision):
    class Query:
        def join(self, *args): return self
        def filter(self, *args): return self
        def one_or_none(self):
            return None if revision is None else SimpleNamespace(record_revision=revision)
    captured = {}
    def attach(source, spec, **kwargs): captured.update(kwargs)
    monkeypatch.setattr("dewey_service.integrations.tapdb_external_references.ExternalReferenceService",
        lambda session: SimpleNamespace(attach=attach))
    source = SimpleNamespace(uid=4, record_revision=8)
    spec = SimpleNamespace(relationship_type="evidence", target=SimpleNamespace(identity_key="fixture-identity"))
    attach_observed_reference(SimpleNamespace(query=lambda *args: Query()), source, spec)
    assert captured == {"expected_source_revision": 8, "expected_lineage_revision": revision}


def test_explicit_native_envelope_has_fresh_operations_and_is_reset(tmp_path):
    from daylily_tapdb.security_context import Attribution
    path = tmp_path / "attribution.json"
    envelope = Attribution(actor_kind="human", actor_issuer="https://login.example.test",
        actor_subject="canonical-subject", service_identity="dewey",
        request_id="explicit-invocation", operation_id="incoming-operation")
    path.write_text(envelope.to_json())
    with explicit_attribution_context(path):
        first = transaction_attribution(SETTINGS, "write", commit=True)
        second = transaction_attribution(SETTINGS, "write", commit=True)
    assert first.actor_subject == second.actor_subject == envelope.actor_subject
    assert first.request_id == second.request_id == envelope.request_id
    assert first.operation_id != second.operation_id
    with pytest.raises(ValueError, match="verified"):
        transaction_attribution(SETTINGS, "write", commit=True)


@pytest.mark.parametrize("outcome", ["network", "invalid-json", "http-error", "parsed", "rejected"])
def test_outbox_completion_never_overwrites_a_concurrent_dispatch(monkeypatch, outcome):
    import httpx
    from daylily_tapdb.revisions import require_revision
    from dewey_service.services.outbox import OutboxServiceMixin
    # Candidate observation precedes another dispatcher's committed completion.
    row = SimpleNamespace(euid="owner-returned-outbox", type="outbox_event", record_revision=7,
        json_addl={"properties": {}, "event_id": "fixture-event", "event_type": "lsmc.dewey.fixture",
            "dispatch_status": "pending", "dispatch_attempt_count": 0})
    backend = object.__new__(TapDBBackend)
    backend.connection = SimpleNamespace(app_username="explicit-dispatcher")
    @contextmanager
    def scope(**kwargs):
        try:
            yield object()
        except RevisionConflict as exc:
            raise HTTPException(409, str(exc)) from exc
    backend.session_scope = scope
    backend.list_by_template = lambda *args, **kwargs: [row]
    backend.find_by_euid = lambda *args, **kwargs: row
    monkeypatch.setattr("dewey_service.services.outbox.normalize_instance_payload",
        lambda item: {**item.json_addl, "euid": item.euid})
    service = OutboxServiceMixin()
    service.backend = backend
    candidates = service._list_qeo_outbox_candidates(
        limit=1, statuses={"pending"}, event_ids=set(), artifact_set_euids=set())
    assert candidates[0]["tapdb_record_revision"] == 7
    service._event_from_outbox_row = lambda observed: SimpleNamespace(model_dump=lambda **kwargs: {})
    calls = []
    def update(session, selector, changes, **kwargs):
        calls.append(kwargs["expected_revision"])
        require_revision(row, kwargs["expected_revision"])
        pytest.fail("Stale completion must be rejected before persisted assignment")
    monkeypatch.setattr("dewey_service.tapdb_backend.update_object", update)
    def post(*args, **kwargs):
        row.record_revision = 8
        row.json_addl.update(dispatch_status="dispatched", dispatch_attempt_count=1)
        if outcome == "network":
            raise httpx.ConnectError("fixture network failure")
        def response_json():
            if outcome == "invalid-json":
                raise ValueError("fixture invalid JSON")
            return {"payload": {"status": "PARSED" if outcome == "parsed" else "REJECTED"}}
        return SimpleNamespace(json=response_json, is_error=outcome == "http-error", status_code=502 if outcome == "http-error" else 200)
    monkeypatch.setattr("dewey_service.services.outbox.httpx.post", post)
    with pytest.raises(HTTPException) as caught:
        service._dispatch_qeo_outbox_row(candidates[0], ingest_url="https://qeo.example.test/ingest",
            token="fixture-token", consumer_group="fixture-consumer", timeout=1, verify=True)
    assert caught.value.status_code == 409
    assert calls == [7]
    assert row.json_addl["dispatch_status"] == "dispatched"
    assert row.json_addl["dispatch_attempt_count"] == 1


def test_outbox_missing_observation_fails_before_remote_delivery(monkeypatch):
    from dewey_service.services.outbox import OutboxServiceMixin
    monkeypatch.setattr("dewey_service.services.outbox.httpx.post",
        lambda *args, **kwargs: pytest.fail("No delivery without original revision"))
    with pytest.raises(HTTPException) as caught:
        OutboxServiceMixin()._dispatch_qeo_outbox_row({}, ingest_url="https://qeo.example.test/ingest",
            token="fixture-token", consumer_group="fixture-consumer", timeout=1, verify=True)
    assert caught.value.status_code == 409
