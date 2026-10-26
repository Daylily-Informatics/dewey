"""Audit population SQL, lifecycle export, and HTTP/archive metric reconciliation."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import column, select, table
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from daylily_tapdb import generic_instance
from tests.support.sharing_v12_fakes import Harness, OWNER, READER, actor, row


NOW = datetime.now(timezone.utc)-timedelta(minutes=1)
START = (NOW-timedelta(days=10)).isoformat()
END = NOW.isoformat()


def sql(expression):
    return str(expression.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


@pytest.mark.parametrize("status", [None, "active", "expired", "revoked"])
@pytest.mark.parametrize("admin", [False, True])
def test_population_sql_applies_owner_lifecycle_and_usage_filters_before_aggregation(status, admin):
    h = Harness()
    session = Session()  # Query construction only; no engine is bound or contacted.
    h.service._share_query = lambda session: session.query(generic_instance)
    identity = OWNER if admin else READER
    with actor(identity):
        query, activity = h.service._report_population(session, owner_subject=identity.subject,
            status=status, audience="recipients", content_mode="www", created_from=START,
            created_before=END, older_than_days=2, never_accessed=True, observed_at=NOW)
    rendered = sql(query.statement)
    assert identity.subject in rendered
    assert "schema_version" in rendered and "'3'" in rendered
    assert "actor_email_verified" in rendered and "actor_service" in rendered
    assert "archive_completed" in rendered and "report_context_created" in rendered
    assert "last_access IS NULL" in rendered and "'www'" in rendered
    assert "share_event" in rendered and "is_deleted IS false" in rendered
    if not admin:
        assert identity.email in rendered  # owner_clause supports the existing verified owner binding.
    if status in {"active", "expired"}:
        assert "expires_at" in rendered
    assert set(activity.c.keys()) == {"share_uid", "last_access", "viewers", "successful_gets", "successful_accesses"}
    session.close()


@pytest.mark.parametrize("filters", [
    {"status": "retired"}, {"audience": "anonymous"}, {"content_mode": "html"},
    {"older_than_days": -1}, {"older_than_days": True}, {"never_accessed": "yes"},
])
def test_population_rejects_invalid_filter_semantics(filters):
    h = Harness()
    with actor(), pytest.raises(ValueError):
        h.service._report_population(None, **filters)


def test_nonadmin_cannot_report_another_owner():
    h = Harness()
    with actor(READER), pytest.raises(HTTPException) as denied:
        h.service._report_population(None, owner_subject=OWNER.subject)
    assert denied.value.status_code == 403


class AggregateQuery:
    """Programmed DB result rows; expressions still come from production SQL construction."""
    def __init__(self, state, entities=(), filters=()):
        self.state, self.entities, self.filters = state, entities, filters
    def filter(self, *expressions): return AggregateQuery(self.state, self.entities, self.filters+expressions)
    def with_entities(self, *expressions): return AggregateQuery(self.state, expressions, self.filters)
    def group_by(self, *args): return self
    def join(self, *args): return self
    def order_by(self, *args): return self
    def offset(self, value): self.state["offset"] = value; return self
    def limit(self, value): self.state["limit"] = value; return self
    def subquery(self): return select(generic_instance.uid).subquery()
    def count(self):
        text = " ".join(sql(expr) for expr in self.filters)
        if "last_access" in text: return self.state.get("never", 0)
        if "created_dt" in text: return self.state.get("created", 0)
        return self.state.get("total", 0)
    def one(self): return self.state.get("durations", (0, None))
    def scalar(self):
        text = sql(self.entities[0])
        if "string_agg" in text:
            self.state["digest_sql"] = text
            values = self.state.setdefault("digest_values", ["fixture-authority"])
            return values.pop(0) if len(values) > 1 else values[0]
        return self.state.get("last")
    def all(self):
        if not self.entities: return self.state.get("rows", [])
        if self.entities[0] is generic_instance: return self.state.get("rows", [])
        text = sql(self.entities[0])
        if "CASE" in text:
            return self.state["duration_buckets"] if "indefinite" in text else self.state["lifecycle"]
        return self.state.get("groups", [])


def reports_harness():
    h = Harness()
    activity = table("fixture_activity", *(column(name) for name in
        ("share_uid", "last_access", "viewers", "successful_gets", "successful_accesses")))
    population = {"total": 3, "created": 2, "never": 1, "last": NOW-timedelta(hours=1),
        "durations": (1, 86400.0), "groups": [("recipients", "download", "active", 3)],
        "duration_buckets": [("indefinite", 1), ("up_to_7_days", 2)], "lifecycle": [("active", 2), ("expired", 1)]}
    events = {"groups": [], "last": None}
    h.service._report_population = lambda *args, **kwargs: (AggregateQuery(population), activity)
    h.service._legacy_history_coverage = lambda *args, **kwargs: {"total": 1, "excluded_from_schema3_metrics": True}
    h.session.query = lambda *args: AggregateQuery(events)
    return h, population, events


def test_report_reconciles_server_events_without_inventing_client_downloads():
    h, population, events = reports_harness()
    events["groups"] = [
        ("authorization", "allow", "unknown", "unknown", "false", 3, 0),
        ("authorization", "deny", "unknown", "unknown", "false", 2, 0),
        ("report_context_created", "allow", "unknown", "unknown", "false", 1, 0),
        ("gateway_response_completed", "completed", "GET", "200", "true", 2, 100),
        ("gateway_response_completed", "completed", "GET", "200", "false", 1, 50),
        ("gateway_response_completed", "completed", "GET", "206", "false", 2, 20),
        ("gateway_response_completed", "completed", "HEAD", "200", "false", 1, 0),
        ("gateway_condition_result", "not_modified", "GET", "304", "false", 1, 0),
        ("gateway_disconnect_or_failure", "unknown", "GET", "200", "false", 1, 7),
        ("archive_started", "allow", "GET", "unknown", "false", 2, 0),
        ("archive_completed", "completed", "GET", "unknown", "false", 1, 1000),
        ("archive_interrupted", "unknown", "GET", "unknown", "false", 1, 10),
    ]
    events["last"] = NOW-timedelta(seconds=1)
    with actor(): result = h.service.sharing_report(starts_at=START, ends_at=END)
    assert result["metrics"] == {"events": 18, "authorization_evaluations": 5, "denials": 2,
        "file_responses_completed": 3, "report_entries": 1, "report_sidecars": 2, "head_responses": 1,
        "not_modified_responses": 1, "range_responses": 2, "archive_attempts": 2, "archive_completions": 1,
        "server_bytes_sent": 1187, "client_downloads_completed": None}
    assert result["shares"]["total"] == 3 and result["shares"]["created_in_window"] == 2
    assert result["shares"]["mean_finite_duration_seconds"] == 86400.0
    assert result["shares"]["duration_buckets"] == {"indefinite": 1, "up_to_7_days": 2}
    assert result["coverage"]["event_watermark"] == events["last"].isoformat()
    assert result["coverage"]["client_persistence_observed"] is False
    assert result["coverage"]["inventory_sha256"] == sha256(b"fixture-authority").hexdigest()
    assert "record_revision" in population["digest_sql"] and "successful_accesses" in population["digest_sql"]


def test_empty_report_is_complete_and_explicit_about_missing_access_evidence():
    h, population, _ = reports_harness()
    population.update(total=0, created=0, never=0, last=None, durations=(0, None), groups=[], duration_buckets=[], lifecycle=[])
    with actor(): result = h.service.sharing_report(starts_at=START)
    assert result["metrics"]["events"] == 0 and result["shares"]["mean_finite_duration_seconds"] is None
    assert result["coverage"]["event_watermark"] is None and result["coverage"]["complete"] is True


@pytest.mark.parametrize("kwargs", [
    {"starts_at": None}, {"starts_at": END, "ends_at": START},
    {"starts_at": START, "ends_at": (NOW+timedelta(days=1)).isoformat()},
    {"starts_at": START, "status": "retired"}, {"starts_at": START, "audience": "public"},
    {"starts_at": START, "content_mode": "html"},
])
def test_report_invalid_windows_and_filters_fail_before_query(kwargs):
    h = Harness()
    with actor(), pytest.raises(ValueError): h.service.sharing_report(**kwargs)


def test_nonadmin_report_cannot_select_another_owner_before_query():
    h = Harness()
    with actor(READER), pytest.raises(HTTPException) as denied:
        h.service.sharing_report(starts_at=START, owner_subject=OWNER.subject)
    assert denied.value.status_code == 403


@pytest.mark.parametrize("operation", ["report", "inventory"])
def test_population_change_during_read_rejects_mixed_snapshot(operation):
    h, population, _ = reports_harness()
    population["digest_values"] = ["reviewed-before", "changed-during-read"]
    with actor(), pytest.raises(HTTPException) as changed:
        if operation == "report": h.service.sharing_report(starts_at=START, ends_at=END)
        else: h.service.sharing_inventory()
    assert changed.value.status_code == 409


@pytest.mark.parametrize("kwargs", [{"page": 0}, {"page": True}, {"page_size": 0}, {"page_size": 201},
    {"page_size": False}, {"observed_at": (NOW+timedelta(days=1)).isoformat()}])
def test_inventory_rejects_unbounded_or_future_exports(kwargs):
    h = Harness()
    with actor(), pytest.raises(ValueError): h.service.sharing_inventory(**kwargs)


def test_inventory_precisely_reports_expiry_archival_and_current_recipient_counts():
    h, population, _ = reports_harness()
    target = h.artifact()
    active = h.share([target], audience="public_registered")
    expired = h.share([target], expires_at="2020-01-01T00:00:00Z")
    archived = h.share([target]); archived.bstatus = "archived"
    grants = h.service._share_grants(h.session, active)
    old = h.add(row("share_grant", "fixture-old-grant", status="active", policy_revision=0, expires_at=None))
    h.link(h.session, parent=active, child=old, relationship_type="share_grant")
    population["rows"] = [(active, NOW-timedelta(hours=1), 2, 3, 5), (expired, None, None, None, None),
                          (archived, None, 0, 0, 0)]
    population["total"] = 3
    with actor():
        result = h.service.sharing_inventory(page_size=3, observed_at=END)
    assert result["complete"] and not result["has_more"]
    assert [item["status"] for item in result["items"]] == ["active", "expired", "archived"]
    first = result["items"][0]
    assert first["recipient_grant_counts"] == {"email": 1, "domain": 0, "registered": 1}
    assert first["public_registered_population_unbounded"] is True
    assert first["unique_verified_viewers"] == 2 and first["successful_access_events"] == 5
    assert first["duration_days"] is None and first["never_accessed"] is False
    assert result["items"][1]["recipient_grant_counts"] == {"email": 0, "domain": 0, "registered": 0}
    assert result["items"][1]["never_accessed"] is True
    with actor(), pytest.raises(HTTPException) as changed:
        h.service.sharing_inventory(expected_inventory_sha256="different-review")
    assert changed.value.status_code == 409


@pytest.mark.parametrize("admin", [False, True])
def test_legacy_coverage_keeps_unknown_historical_fields_explicit(admin):
    h = Harness()
    state = {"groups": [(None, None, "archived", 2), ("1", "retired", "active", 3)]}
    query = AggregateQuery(state)
    h.service._share_query = lambda session: query
    with actor(OWNER if admin else READER):
        result = h.service._legacy_history_coverage(h.session, owner_subject="fixture-owner",
            created_from=START, created_before=END, older_than_days=2, observed_at=NOW)
    assert result["total"] == 5 and result["excluded_from_schema3_metrics"] is True
    assert result["groups"][0]["schema_version"] is None and result["groups"][0]["stored_status"] is None
