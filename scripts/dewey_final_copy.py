"""Create the exact final Dewey copy from the continuously frozen source.

This approved operator SOP performs no backup, schema migration, sequence
mutation, runtime binding, source reopen, deletion, or automatic recovery.
Rehearsal acceptance remains an explicit coordinator gate before apply.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

from daylily_tapdb.runtime_principal import operator_connection, operator_session
from sqlalchemy import text

from dewey_rehearsal_copy import (
    ROOT, cfg_at, event, inspect_container, new_json, sessions, source_physical, utc,
)

TARGET = "dewey_prod_tapdb10"
COPY_RECEIPT = ROOT / "receipts/rehearsal-copy-sop-result.json"
COPY_SHA = "2e477de116715b8c42c127618188d9607ac26826fb97453059b7921dd6c6ba7c"
PLAN = ROOT / "receipts/final-copy-sop-plan.json"
RESULT = ROOT / "receipts/final-copy-sop-result.json"
EVENTS = ROOT / "receipts/final-copy-sop-events.jsonl"
SQL = [
    'CREATE DATABASE "dewey_prod_tapdb10" WITH TEMPLATE "dewey_prod" OWNER "dayhoff" ALLOW_CONNECTIONS false',
    'REVOKE CONNECT, TEMPORARY ON DATABASE "dewey_prod_tapdb10" FROM PUBLIC',
    'ALTER DATABASE "dewey_prod_tapdb10" ALLOW_CONNECTIONS true',
]


def observe(connection, *, target_absent):
    rows = [dict(row) for row in connection.execute(text(
        "SELECT datname,oid::bigint AS oid,pg_get_userbyid(datdba) AS owner,datallowconn "
        "FROM pg_catalog.pg_database WHERE datname IN ('dewey_prod','postgres','dewey_prod_tapdb10') ORDER BY datname"
    )).mappings()]
    named = {row["datname"]: row for row in rows}
    if named["postgres"]["oid"] != 5 or named["dewey_prod"] != {
        "datname": "dewey_prod", "oid": 16749, "owner": "dayhoff", "datallowconn": False,
    }:
        raise RuntimeError("Original source/control identity or continuous source gate changed")
    if target_absent and TARGET in named:
        raise RuntimeError("Exact final destination exists; do not overwrite or choose another name")
    if sessions(connection):
        raise RuntimeError("Frozen source has a session; inspect rather than terminate or continue")
    return named


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply"))
    parser.add_argument("--rehearsal-exposure-plan", type=Path, required=True)
    parser.add_argument("--acceptance-reference", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Exact RC required")
    if not args.acceptance_reference.strip():
        raise RuntimeError("Require the independent rehearsal acceptance reference")
    exposure = args.rehearsal_exposure_plan
    if not exposure.is_absolute() or exposure.resolve() != exposure or not exposure.is_relative_to(ROOT):
        raise RuntimeError("Require the exact protected canonical rehearsal exposure plan")
    if hashlib.sha256(COPY_RECEIPT.read_bytes()).hexdigest() != COPY_SHA:
        raise RuntimeError("Original frozen-copy receipt changed")
    frozen = json.loads(COPY_RECEIPT.read_text())
    if frozen["status"] != "copy_created_source_remains_fenced":
        raise RuntimeError("Original source was not continuously fenced")
    control = cfg_at("control-operator.yaml", "postgres")
    cfg_at("replacement-operator.yaml", TARGET)
    source = inspect_container()
    if source["running"]:
        raise RuntimeError("Original source container restarted")
    for path in (RESULT, EVENTS):
        if path.exists() or path.is_symlink():
            raise RuntimeError("An execution output exists; inspect instead of retrying")
    with operator_connection(control, read_only=True) as connection:
        observe(connection, target_absent=True)
        physical = source_physical(connection)
        if physical != frozen["fingerprint"]["source_physical"]:
            raise RuntimeError("Source physical server differs from the frozen cutoff")
    fingerprint = {
        "source": "dewey_prod", "source_oid": 16749, "target": TARGET,
        "source_physical": physical, "container_id": source["id"], "image": source["image"],
        "frozen_copy_receipt_sha256": COPY_SHA,
        "source_contract_sha256": frozen["source_contract_sha256"],
        "rehearsal_exposure_plan": str(exposure),
        "rehearsal_exposure_plan_sha256": hashlib.sha256(exposure.read_bytes()).hexdigest(),
        "acceptance_reference": args.acceptance_reference,
        "config_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                          for name in ("control-operator.yaml", "replacement-operator.yaml")},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "copy_helper_sha256": hashlib.sha256((Path(__file__).parent/"dewey_rehearsal_copy.py").read_bytes()).hexdigest(),
        "sql": SQL,
    }
    if args.operation == "plan":
        new_json(PLAN, {"planned_at": utc(), "fingerprint": fingerprint, "apply_performed": False,
                        "backup_created": False, "source_remains_fenced": True})
        print(json.dumps({"status": "planned", "receipt": str(PLAN)}))
        return
    if json.loads(PLAN.read_text())["fingerprint"] != fingerprint:
        raise RuntimeError("Final copy inputs changed after plan review")
    started = time.monotonic()
    with EVENTS.open("x") as events:
        with operator_session(control, isolation_level="AUTOCOMMIT") as connection:
            observe(connection, target_absent=True)
            if source_physical(connection) != physical or inspect_container()["running"]:
                raise RuntimeError("Source fence changed before final copy")
            event(events, "final_copy_create_intent", {"sql": SQL[0]})
            connection.execute(text(SQL[0]))
            copied = observe(connection, target_absent=False)[TARGET]
            if copied["owner"] != "dayhoff" or copied["datallowconn"] is not False:
                raise RuntimeError("Created final target identity/admission differs")
            event(events, "final_copy_created_closed", copied)
            connection.execute(text(SQL[1]))
            connection.execute(text(SQL[2]))
            final = observe(connection, target_absent=False)
            acl = [dict(row) for row in connection.execute(text(
                "SELECT a.grantee::bigint AS grantee,a.privilege_type,a.is_grantable,d.datdba::bigint AS owner_oid "
                "FROM pg_catalog.pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) a "
                "WHERE d.datname=:target ORDER BY a.grantee,a.privilege_type"
            ), {"target": TARGET}).mappings()]
            if final[TARGET]["oid"] != copied["oid"] or final[TARGET]["datallowconn"] is not True or not acl or any(r["grantee"] != r["owner_oid"] for r in acl):
                raise RuntimeError("Final copy is not open with owner-only access")
            state = inspect_container()
            if state["running"]:
                raise RuntimeError("Original source container restarted")
            result = {
                "completed_at": utc(), "elapsed_seconds": round(time.monotonic()-started,3),
                "status": "copy_created_source_remains_fenced", "fingerprint": fingerprint,
                "copied_database_at_creation": copied, "copied_database": final[TARGET],
                "final_database_gates": final, "copy_acl": acl, "source_container": state,
                "source_contract_sha256": frozen["source_contract_sha256"],
                "source_identity_sha256": frozen["source_identity_sha256"],
                "source_sequence_sha256": frozen["source_sequence_sha256"],
                "native_next_receipt": frozen["native_next_receipt"], "backup_created": False,
                "schema_migration_performed": False, "target_runtime_started": False,
            }
            new_json(RESULT, result)
            event(events, "final_copy_complete", {"result": str(RESULT), "target_oid": copied["oid"]})
    print(json.dumps({"status": result["status"], "receipt": str(RESULT)}))


if __name__ == "__main__":
    main()
