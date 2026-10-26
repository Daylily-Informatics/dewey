"""Real native PostgreSQL contracts; an explicit isolated, preinitialized database is required.

Prerequisites: DEWEY_TEST_DATABASE_DSN and absolute DEWEY_TEST_TAPDB_CONFIG,
with TapDB 11.0.9 schema/runtime principal and the Dewey repository templates
installed by the supported lifecycle CLI. No production target is inferred.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.engine import make_url

from dewey_service.audit import (
    authenticated_user_email_context,
    explicit_attribution_context,
    request_audit_context,
)
from dewey_service.registry_access import POLICY_TEMPLATE, Principal, principal_context
from dewey_service.share_context import share_context_context

OWNER = Principal(
    subject="sharing-contract-owner",
    email="owner@example.test",
    roles=("ADMIN",),
    email_verified=True,
)
RECIPIENT = Principal(
    subject="sharing-contract-recipient",
    email="recipient@example.test",
    roles=("READ_ONLY",),
    email_verified=True,
)


@contextmanager
def request_scope(actor=OWNER, *, maintenance=False):
    with (
        request_audit_context(),
        principal_context(actor, maintenance=maintenance),
        authenticated_user_email_context(actor.email),
        share_context_context(
            {"trusted_tailnet": True, "managed_origin": True, "request_id": str(uuid4())}
        ),
    ):
        yield


@pytest.fixture(scope="module")
def native_service_factory():
    from daylily_tapdb import InstanceFactory, TemplateManager
    from daylily_tapdb.cli.context import set_cli_context
    from daylily_tapdb.cli.db_config import get_db_config
    from daylily_tapdb.web.runtime import get_db

    from dewey_service.service import DeweyService
    from dewey_service.tapdb_backend import TapDBBackend

    dsn, config = (
        os.environ.get("DEWEY_TEST_DATABASE_DSN"),
        os.environ.get("DEWEY_TEST_TAPDB_CONFIG"),
    )
    if not dsn or not config:
        pytest.fail(
            "Explicit isolated DEWEY_TEST_DATABASE_DSN and DEWEY_TEST_TAPDB_CONFIG are required"
        )
    url = make_url(dsn)
    if url.host not in {"localhost", "127.0.0.1", "::1"} or not (
        "test" in str(url.database).lower() or url.database == "dewey12_contract"
    ):
        pytest.fail("Native sharing tests refuse non-local or non-test database names")
    path = Path(config)
    if not path.is_absolute() or not path.is_file():
        pytest.fail("Native sharing tests require an existing absolute config")
    cfg = get_db_config(config_path=str(path))
    set_cli_context(config_path=str(path))
    if (
        cfg["engine_type"] != "local"
        or str(cfg["host"]) != url.host
        or int(cfg["port"]) != url.port
        or cfg["database"] != url.database
    ):
        pytest.fail("Explicit native test config does not match the isolated DSN")

    def build():
        backend = object.__new__(TapDBBackend)
        backend.config_path = str(path)
        backend.settings = SimpleNamespace(
            auth_mode="external_broker",
            external_broker_handoff_exchange_url="https://login.example.test/auth/handoff/consume",
        )
        backend.connection = get_db(str(path))
        backend.connection.app_username = "sharing-contract-tests"
        backend.domain_code = cfg["domain_code"]
        backend.templates = TemplateManager()
        backend.factory = InstanceFactory(backend.templates, domain_code=backend.domain_code)
        backend.observability = None
        service = object.__new__(DeweyService)
        service.backend = backend
        service.share_max_lifetime_days = 365
        service.requester_pays_buckets = set()
        return service

    service = build()
    with request_scope(), service.backend.session_scope(commit=True) as session:
        service.backend.ensure_templates(session)
        marker = service.backend.find_by_json_field(
            session,
            template_code=POLICY_TEMPLATE,
            field="policy_kind",
            value="sharing_schema",
            for_update=True,
        )
        if marker is None:
            service.backend.create_instance(
                session,
                template_code=POLICY_TEMPLATE,
                name="Isolated sharing contract schema",
                json_addl={
                    "policy_kind": "sharing_schema",
                    "schema_version": 3,
                    "status": "verified",
                },
            )
    return build


def artifact(service):
    from dewey_service.tapdb_backend import ARTIFACT_TEMPLATE

    token = uuid4().hex
    with request_scope(), service.backend.session_scope(commit=True) as session:
        obj = service.backend.create_instance(
            session,
            template_code=ARTIFACT_TEMPLATE,
            name="Controlled sharing fixture",
            json_addl={
                "storage_backend": "s3",
                "storage_kind": "object",
                "node_kind": "file",
                "bucket": "controlled-fixture",
                "key": token + ".txt",
                "storage_uri": "s3://controlled-fixture/" + token + ".txt",
                "original_filename": token + ".txt",
                "artifact_identity_key": token,
            },
        )
        return obj.euid


def share(service, target):
    with request_scope():
        code, result = service.create_share(
            target_kind="artifact_object",
            target_euid=target,
            expires_at=None,
            grants=[{"recipient_type": "email", "recipient": RECIPIENT.email}],
            idempotency_key=uuid4().hex,
        )
    assert code == 201
    return result["share_euid"]


def test_native_atomic_slug_claim_and_permanent_tombstone(native_service_factory):
    service = native_service_factory()
    target = artifact(service)
    shares = [share(service, target), share(service, target)]
    slug = "contract-" + uuid4().hex
    barrier = Barrier(2)

    def claim(euid):
        with request_scope():
            barrier.wait(timeout=10)
            try:
                return native_service_factory().claim_share_slug(euid, slug, policy_revision=1)
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, shares))
    assert sum(isinstance(r, dict) for r in results) == 1
    assert results.count(409) == 1
    winner = next(r for r in results if isinstance(r, dict))
    with request_scope():
        service.revoke_share_slug(winner["share_euid"], slug, policy_revision=1)
        with pytest.raises(HTTPException) as conflict:
            service.claim_share_slug(winner["share_euid"], slug, policy_revision=1)
    assert conflict.value.status_code == 409


def test_native_competing_edits_and_removed_target_lineage(native_service_factory):
    service = native_service_factory()
    old = artifact(service)
    new = artifact(service)
    euid = share(service, old)
    barrier = Barrier(2)

    def edit(name):
        with request_scope():
            barrier.wait(timeout=10)
            try:
                return native_service_factory().modify_registry_share(
                    euid, {"name": name, "policy_revision": 1}
                )
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(edit, ["first proposal", "second proposal"]))
    assert sum(isinstance(r, dict) for r in results) == 1
    assert results.count(409) == 1
    with request_scope():
        result = service.modify_registry_share(
            euid, {"target_kind": "artifact_object", "target_euid": new, "policy_revision": 2}
        )
        assert [m["artifact_euid"] for m in result["members"]] == [new]
        with service.backend.session_scope(commit=False) as session:
            obj = service._canonical_share(session, euid)
            assert {m.euid for m in service._historical_share_members(session, obj)} == {old, new}
            assert (
                len(
                    service._share_related(
                        session, obj, relationship="share_revision", kind="share_revision"
                    )
                )
                == 3
            )
    with request_scope(RECIPIENT):
        with pytest.raises(HTTPException) as removed:
            service.authorize_share_object(euid, old)
        assert removed.value.status_code == 403
        assert service.authorize_share_object(euid, new)["target_euid"] == new


def test_native_preserving_v3_migration_and_idempotent_receipt(native_service_factory, tmp_path):
    from daylily_tapdb.security_context import Attribution

    from dewey_service import share_upgrade_v3
    from dewey_service.tapdb_backend import SHARE_TEMPLATE, normalize_instance_payload

    service = native_service_factory()
    target = artifact(service)
    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    with request_scope(), service.backend.session_scope(commit=True) as session:
        member = service._registry_record(session, target)
        obj = service.backend.create_instance(
            session,
            template_code=SHARE_TEMPLATE,
            name="Preserved schema2 fixture",
            json_addl={
                "schema_version": 2,
                "policy_revision": 1,
                "owner_subject": OWNER.subject,
                "owner_email": OWNER.email,
                "status": "active",
                "audience": "recipients",
                "expires_at": deadline,
                "delivery_modes": ["gateway", "presigned"],
                "denied_emails": [],
                "include_patterns": ["**"],
                "exclude_patterns": [],
                "target_kind": "artifact_object",
                "target_euid": target,
            },
        )
        service.backend.create_lineage(
            session, parent=member, child=obj, relationship_type="has_share"
        )
        service._write_grants(
            session,
            obj,
            [
                {
                    "recipient_type": "email",
                    "recipient": RECIPIENT.email,
                    "include_subdomains": False,
                    "include_patterns": ["**"],
                    "exclude_patterns": [],
                    "expires_at": deadline,
                    "target_euids": [target],
                }
            ],
            [member],
            1,
        )
        native_euid = obj.euid
        grant_euids = [g.euid for g in service._share_grants(session, obj)]
        marker = service.backend.find_by_json_field(
            session,
            template_code=POLICY_TEMPLATE,
            field="policy_kind",
            value="sharing_schema",
            for_update=True,
        )
        service.backend.update_instance_json(
            session, marker, {"schema_version": 2, "status": "verified"}
        )
    envelope = Attribution(
        actor_kind="human",
        actor_issuer="https://login.example.test",
        actor_subject=OWNER.subject,
        service_identity="dewey",
        request_id=uuid4().hex,
        operation_id=uuid4().hex,
    )
    attribution = tmp_path / "attribution.json"
    attribution.write_text(envelope.to_json())
    with request_scope(maintenance=True), explicit_attribution_context(attribution):
        reviewed = share_upgrade_v3.inventory(service)
        assert not reviewed["ambiguous"]
        receipt = share_upgrade_v3.apply(service, reviewed, reviewed["inventory_sha256"])
        assert receipt["retired"] == receipt["deleted"] == 0
        assert (
            share_upgrade_v3.verify(service, reviewed, reviewed["inventory_sha256"])["status"]
            == "verified"
        )
        assert share_upgrade_v3.apply(service, reviewed, reviewed["inventory_sha256"])[
            "already_applied"
        ]
    with request_scope(), service.backend.session_scope(commit=False) as session:
        migrated = service._canonical_share(session, native_euid)
        assert normalize_instance_payload(migrated)["expires_at"] == deadline
        assert [g.euid for g in service._share_grants(session, migrated)] == grant_euids
        assert [m.euid for m in service._share_members(session, migrated)] == [target]


def test_native_audit_reconciles_archive_report_http_and_preserved_history(native_service_factory):
    from dewey_service.tapdb_backend import SHARE_TEMPLATE

    service = native_service_factory()
    target = artifact(service)
    owner = Principal(
        subject="audit-owner-" + uuid4().hex,
        email="audit-owner@example.test",
        roles=("ADMIN",),
        email_verified=True,
    )
    euids = []
    with request_scope(owner):
        for _ in range(3):
            _, created = service.create_share(
                target_kind="artifact_object",
                target_euid=target,
                expires_at=None,
                grants=[{"recipient_type": "email", "recipient": RECIPIENT.email}],
                idempotency_key=uuid4().hex,
            )
            euids.append(created["share_euid"])
        with service.backend.session_scope(commit=True) as session:
            service.backend.create_instance(
                session,
                template_code=SHARE_TEMPLATE,
                name="Preserved inactive audit fixture",
                json_addl={
                    "schema_version": 1,
                    "status": "retired",
                    "owner_subject": owner.subject,
                },
            )
    with request_scope(RECIPIENT):
        for euid, event, decision, details in [
            (euids[0], "authorization", "allow", {"action": "gateway"}),
            (euids[0], "archive_started", "allow", {"method": "GET"}),
            (
                euids[0],
                "archive_completed",
                "completed",
                {"method": "GET", "server_bytes_sent": 1024},
            ),
            (euids[0], "report_context_created", "allow", {}),
            (
                euids[1],
                "gateway_response_completed",
                "completed",
                {"method": "GET", "status_code": 200, "server_bytes_sent": 10},
            ),
            (
                euids[1],
                "gateway_condition_result",
                "not_modified",
                {"method": "GET", "status_code": 304, "server_bytes_sent": 0},
            ),
            (
                euids[1],
                "gateway_response_completed",
                "completed",
                {"method": "HEAD", "status_code": 200, "server_bytes_sent": 0},
            ),
            (
                euids[1],
                "gateway_disconnect_or_failure",
                "unknown",
                {"method": "GET", "status_code": 200, "server_bytes_sent": 5},
            ),
            (euids[1], "archive_started", "allow", {"method": "GET"}),
            (
                euids[1],
                "archive_interrupted",
                "unknown",
                {"method": "GET", "server_bytes_sent": 100},
            ),
        ]:
            service.append_share_event(euid, event_type=event, decision=decision, details=details)
    with request_scope(owner):
        report = service.sharing_report(
            starts_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            owner_subject=owner.subject,
        )
        assert report["shares"]["total"] == report["shares"]["indefinite"] == 3
        assert report["shares"]["duration_buckets"] == {"indefinite": 3}
        assert report["shares"]["current_lifecycle_counts"] == {"active": 3}
        assert report["shares"]["never_accessed"] == 1
        assert report["coverage"]["historical_legacy"]["total"] == 1
        assert report["metrics"]["authorization_evaluations"] == 1
        assert (
            report["metrics"]["archive_attempts"] == 2
            and report["metrics"]["archive_completions"] == 1
        )
        assert report["metrics"]["report_entries"] == 1
        assert report["metrics"]["file_responses_completed"] == 1
        assert (
            report["metrics"]["head_responses"] == report["metrics"]["not_modified_responses"] == 1
        )
        assert report["metrics"]["server_bytes_sent"] == 1139
        assert report["metrics"]["client_downloads_completed"] is None
        inventory = service.sharing_inventory(owner_subject=owner.subject, page_size=2)
        assert inventory["total"] == 3 and inventory["has_more"] and not inventory["complete"]
        second = service.sharing_inventory(
            owner_subject=owner.subject,
            page=2,
            page_size=2,
            observed_at=inventory["observed_at"],
            expected_inventory_sha256=inventory["inventory_sha256"],
        )
        rows = {row["share_euid"]: row for row in inventory["items"] + second["items"]}
        assert (
            rows[euids[0]]["successful_access_events"] == 2
            and rows[euids[0]]["successful_get_responses"] == 0
        )
        assert (
            rows[euids[0]]["unique_verified_viewers"] == 1 and not rows[euids[0]]["never_accessed"]
        )
        assert rows[euids[1]]["successful_get_responses"] == 2 and rows[euids[2]]["never_accessed"]
        service.modify_registry_share(
            euids[0], {"name": "Changed after export review", "policy_revision": 1}
        )
        with pytest.raises(HTTPException) as changed:
            service.sharing_inventory(
                owner_subject=owner.subject,
                page=2,
                page_size=2,
                observed_at=inventory["observed_at"],
                expected_inventory_sha256=inventory["inventory_sha256"],
            )
        assert changed.value.status_code == 409


def test_native_continuation_rejects_changed_location(native_service_factory):
    service = native_service_factory()
    targets = [artifact(service), artifact(service)]
    with request_scope():
        _, created = service.create_share(
            target_kind="mixed_set",
            targets=[{"target_kind": "artifact_object", "target_euid": t} for t in targets],
            grants=[{"recipient_type": "email", "recipient": RECIPIENT.email}],
            expires_at=None,
            idempotency_key=uuid4().hex,
        )
    with request_scope(RECIPIENT):
        page = service.list_share_contents(created["share_euid"], limit=1)
        assert page["incomplete"] and page["continuation_token"]
    with request_scope(), service.backend.session_scope(commit=True) as session:
        target = service._registry_record(session, targets[0], action="edit", lock=True)
        service.backend.update_instance_json(
            session, target, {"location_revision": 2, "key": "reviewed-fixture-new-location.txt"}
        )
    with request_scope(RECIPIENT), pytest.raises(HTTPException) as changed:
        service.list_share_contents(
            created["share_euid"], limit=1, continuation_token=page["continuation_token"]
        )
    assert changed.value.status_code == 409
