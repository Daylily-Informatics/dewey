#!/usr/bin/env python3
"""Bounded Labcore acceptance on the retained isolated Aurora rehearsal only."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from sqlalchemy import text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert args.config.is_absolute() and args.output.is_absolute()
    cfg = yaml.safe_load(args.config.read_text())
    tap = Path(cfg["database"]["config_path"])
    target = yaml.safe_load(tap.read_text())["target"]
    assert target["database"] == "dewey_tapdb10_rehearsal_20260911"
    os.environ["DEWEY_CONFIG"] = str(args.config)
    os.environ["TAPDB_CONFIG_PATH"] = str(tap)
    os.environ["DEWEY_DEPLOYMENT_CODE"] = "day"
    from dewey_service.labcore_owner_command import (
        COMMAND_TYPE,
        COMMAND_VERSION,
        HASH_DOMAIN,
        LabcoreSequencingRunRegistrationCommandV2,
        bind_registration_command,
    )
    from dewey_service.labcore_owner_contracts import bind_request_hash
    from dewey_service.service import DeweyConflictError, DeweyService
    from dewey_service.tapdb_backend import (
        ARTIFACT_TEMPLATE,
        EXTERNAL_OBJECT_TEMPLATE,
        REGISTRATION_RECEIPT_TEMPLATE,
        TapDBBackend,
    )

    backend = TapDBBackend()
    service = DeweyService(backend)
    prefix = "labcore-acceptance-" + uuid.uuid4().hex
    outcomes = {}
    with backend.session_scope() as session:
        assert session.execute(text("select current_database()")).scalar() == target["database"]
        backend.ensure_templates(session)
        assert (
            session.execute(
                text("select has_database_privilege(current_user,current_database(),'TEMP')")
            ).scalar()
            is False
        )
    golden = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "contracts/dynamic_workflow/labcore_sequencing_run_owner.v1.golden.json"
        ).read_text()
    )["raw"]

    def command(label, *, run=None, tenant="isolated-tenant", test="isolated-test"):
        raw = dict(golden)
        raw.update(
            external_object_id=run or f"{prefix}-{label}",
            labcore_sequencing_run_euid=run or f"{prefix}-{label}",
            tenant_euid=tenant,
            processing_site_euid="isolated-site",
            labcore_binding_receipt_id=f"{prefix}-{label}-binding",
            dataset_root_uri=f"s3://isolated-acceptance/{prefix}/{label}/",
        )
        owner = {
            key: raw[key]
            for key in (
                "tenant_euid",
                "processing_site_euid",
                "platform",
                "dataset_root_uri",
                "dataset_revision",
                "inventory_sha256",
                "labcore_binding_receipt_id",
                "labcore_binding_receipt_sha256",
                "labcore_sequencing_run_euid",
                "expected_files",
            )
        }
        owner["test_euid"] = test
        with backend.session_scope(commit=True) as session:
            artifact = backend.create_instance(
                session,
                template_code=ARTIFACT_TEMPLATE,
                name=f"{prefix}-{label}",
                json_addl={
                    "artifact_type": "sequencing_run",
                    "storage_kind": "prefix",
                    "storage_backend": "s3",
                    "storage_uri": raw["dataset_root_uri"],
                    "producer_system": "labcore",
                    "producer_object_euid": raw["external_object_id"],
                    "metadata": {"labcore_owner": owner},
                },
            )
            raw["target_euid"] = artifact.euid
        return LabcoreSequencingRunRegistrationCommandV2.model_validate(
            bind_registration_command(
                {
                    "command_type": COMMAND_TYPE,
                    "command_version": COMMAND_VERSION,
                    "hash_domain": HASH_DOMAIN,
                    "test_euid": test,
                    "owner_request": bind_request_hash(raw),
                }
            )
        )

    def submit(value):
        try:
            return service.register_labcore_sequencing_run_owner(
                request_body=value, principal_id="isolated-labcore-caller"
            )
        except DeweyConflictError:
            return 409, {}

    native = backend.claim_global_instance

    def concurrent(values):
        barrier = threading.Barrier(2)
        pids = []

        def synchronized(session, **kwargs):
            pids.append(session.execute(text("select pg_backend_pid()")).scalar())
            barrier.wait(timeout=15)
            return native(session, **kwargs)

        backend.claim_global_instance = synchronized
        try:
            with ThreadPoolExecutor(2) as pool:
                result = list(pool.map(submit, values))
            assert len(set(pids)) == 2
            return sorted(code for code, _ in result), result
        finally:
            backend.claim_global_instance = native

    first = command("identical")
    codes, results = concurrent([first, first])
    assert codes == [200, 201]
    assert results[0][1] == results[1][1]
    outcomes["identical_separate_sessions"] = codes
    receipt = results[0][1]
    with backend.session_scope() as session:
        from dewey_service.integrations.tapdb_external_references import resolve_relation_endpoints
        from dewey_service.tapdb_backend import EXTERNAL_OBJECT_RELATION_TEMPLATE

        relation = backend.find_by_euid(
            session,
            template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
            euid=receipt["external_object_relation_euid"],
        )
        endpoints = resolve_relation_endpoints(session, relation)
        assert endpoints.source.euid == first.owner_request.target_euid
        assert endpoints.external_object.euid == receipt["external_object_euid"]
        r = backend.find_by_euid(
            session,
            template_code=REGISTRATION_RECEIPT_TEMPLATE,
            euid=receipt["registration_receipt_euid"],
        )
        assert r.json_addl["principal_id"] == "isolated-labcore-caller"
        assert (
            len(
                backend.list_parents(session, child=r, relationship_type="has_registration_receipt")
            )
            == 3
        )
        # The native attach is in the same transaction; verify its authoritative XRF child.
        children = backend.list_children(
            session, parent=endpoints.source, relationship_type="labcore_sequencing_run"
        )
        assert len(children) == 1 and children[0].type == "external_identifier"
    outcomes["lineage_receipt_native_xrf"] = "passed"
    shared = f"{prefix}-divergent"
    a, b = command("a", run=shared), command("b", run=shared, test="different-test")
    codes, _ = concurrent([a, b])
    assert codes == [201, 409]
    outcomes["divergent"] = codes
    shared = f"{prefix}-cross-tenant"
    a, b = command("c", run=shared), command("d", run=shared, tenant="other-tenant")
    codes, _ = concurrent([a, b])
    assert codes == [201, 409]
    outcomes["cross_tenant_global_identity"] = codes

    for rollback in (False, True):
        value = command("rollback" if rollback else "commit")
        claimed = threading.Event()
        release = threading.Event()
        waiter = threading.Event()
        waiter_pid = []

        def held(session, **kwargs):
            if threading.current_thread().name.endswith("_0"):
                result = native(session, **kwargs)
                claimed.set()
                assert release.wait(15)
                if rollback:
                    raise RuntimeError("deliberate isolated rollback")
                return result
            waiter_pid.append(session.execute(text("select pg_backend_pid()")).scalar())
            waiter.set()
            return native(session, **kwargs)

        backend.claim_global_instance = held
        try:
            with ThreadPoolExecutor(2, thread_name_prefix="claim") as pool:
                owner = pool.submit(submit, value)
                assert claimed.wait(15)
                second = pool.submit(submit, value)
                assert waiter.wait(15)
                locked = False
                for _ in range(50):
                    with backend.session_scope() as session:
                        locked = (
                            session.execute(
                                text("select wait_event_type from pg_stat_activity where pid=:pid"),
                                {"pid": waiter_pid[0]},
                            ).scalar()
                            == "Lock"
                        )
                    if locked:
                        break
                    time.sleep(0.1)
                release.set()
                assert locked, "waiter did not reach a PostgreSQL lock wait"
                if rollback:
                    try:
                        owner.result(timeout=15)
                        raise AssertionError("owner should roll back")
                    except RuntimeError as error:
                        assert str(error) == "deliberate isolated rollback"
                    assert second.result(timeout=15)[0] == 201
                else:
                    assert owner.result(timeout=15)[0] == 201
                    assert second.result(timeout=15)[0] == 200
        finally:
            release.set()
            backend.claim_global_instance = native
        outcomes["rollback_waiter" if rollback else "commit_waiter"] = "passed"

    a, b = command("independent-a"), command("independent-b")
    codes, _ = concurrent([a, b])
    assert codes == [201, 201]
    outcomes["independent_keys"] = codes
    old = backend.create_instance
    value = command("failed-receipt")

    def fail_receipt(session, **kwargs):
        if kwargs["template_code"] == REGISTRATION_RECEIPT_TEMPLATE:
            raise RuntimeError("deliberate receipt failure")
        return old(session, **kwargs)

    backend.create_instance = fail_receipt
    try:
        submit(value)
        raise AssertionError("receipt must fail")
    except RuntimeError as error:
        assert str(error) == "deliberate receipt failure"
    finally:
        backend.create_instance = old
    with backend.session_scope() as session:
        assert (
            backend.find_by_json_field(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                field="external_identity_key",
                value="labcore:sequencing_run:" + value.owner_request.external_object_id,
            )
            is None
        )
    assert submit(value)[0] == 201
    outcomes["atomic_receipt_failure_retry"] = "passed"
    with backend.session_scope(commit=True) as session:
        row = backend.find_by_euid(
            session, template_code=EXTERNAL_OBJECT_TEMPLATE, euid=receipt["external_object_euid"]
        )
        row.is_deleted = True
    assert submit(first)[0] == 409
    outcomes["soft_deleted_identity_reserved"] = "passed"
    args.output.write_text(
        json.dumps(
            {
                "status": "passed",
                "database": target["database"],
                "fixture_prefix": prefix,
                "cases": outcomes,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"status": "passed", "cases": outcomes}))


if __name__ == "__main__":
    main()
