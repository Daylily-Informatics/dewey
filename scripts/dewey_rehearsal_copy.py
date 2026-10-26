"""Freeze the source and create the in-cluster rehearsal copy; no backup.

This operator SOP complements released TapDB inventory/allocator validators.
It creates exactly one absent rehearsal database. It performs no schema or
sequence mutation. Failures retain the current state for explicit inspection;
there is no automatic cleanup, retry, rollback, or alternate destination.
The user authorized keeping Dewey offline through rehearsal and final cutover.
Successful completion leaves the original source closed and container stopped.
"""

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time

from daylily_tapdb.cli.db_config import get_db_config
from daylily_tapdb.runtime_principal import operator_connection, operator_session
from sqlalchemy import text

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
SOURCE = "dewey_prod"
TARGET = "dewey_tapdb10_rehearsal_20260911"
CONTAINER = "dayhoff-day-dewey-1"
CONTAINER_ID = "872434f0530335fd5a985a920f498fe39a36fd5eab40b9cb3934b185ceddeb36"
IMAGE = "sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f"
MAPPINGS = ROOT / "receipts/source-sequence-mappings-20260911T053316Z.json"
CUTOFF = ROOT / "receipts/rehearsal-source-cutoff.json"
NEXT = ROOT / "receipts/rehearsal-source-next-plan.json"
EMPTY = ROOT / "receipts/empty-observation-floors.json"
PLAN = ROOT / "receipts/rehearsal-copy-sop-plan.json"
RESULT = ROOT / "receipts/rehearsal-copy-sop-result.json"
EVENTS = ROOT / "receipts/rehearsal-copy-sop-events.jsonl"
NATIVE_LOGS = (ROOT / "logs/rehearsal-source-cutoff.log", ROOT / "logs/rehearsal-source-next-plan.log")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def new_json(path, data):
    with path.open("x") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def event(handle, phase, evidence):
    handle.write(json.dumps({"at": utc(), "phase": phase, "evidence": evidence}, sort_keys=True, default=str) + "\n")
    handle.flush()
    os.fsync(handle.fileno())
    print(json.dumps({"at": utc(), "phase": phase}), flush=True)


def cfg_at(filename, database):
    path = ROOT / filename
    cfg = get_db_config(config_path=path, client_id="dewey", database_name="dewey-day")
    expected = {"database": database, "operator_user": "dayhoff", "schema_name": "tapdb_dewey_lsmcok1_local",
                "domain_code": "M", "engine_type": "aurora", "cluster_identifier": "dayhoff-lsmcok1-tapdb",
                "host": "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com"}
    if any(cfg.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Configuration differs from the reviewed copy binding")
    return cfg


def inspect_container():
    doc = json.loads(subprocess.check_output(["docker", "inspect", CONTAINER], text=True))[0]
    if doc["Id"] != CONTAINER_ID or doc["Image"] != IMAGE or doc["HostConfig"]["RestartPolicy"]["Name"] != "unless-stopped":
        raise RuntimeError("Source container identity/restart policy changed")
    return {"id": doc["Id"], "image": doc["Image"], "running": doc["State"]["Running"],
            "pid": doc["State"]["Pid"], "exit_code": doc["State"]["ExitCode"], "oom_killed": doc["State"]["OOMKilled"]}


def inspect_databases(connection, target_absent):
    rows = [dict(row) for row in connection.execute(text("SELECT datname, oid::bigint AS oid, pg_get_userbyid(datdba) AS owner, datallowconn FROM pg_catalog.pg_database WHERE datname IN (:source,:target,:final,:control) ORDER BY datname"),
            {"source": SOURCE, "target": TARGET, "final": "dewey_prod_tapdb10", "control": "postgres"}).mappings()]
    named = {row["datname"]: row for row in rows}
    if named["postgres"]["oid"] != 5 or named[SOURCE]["oid"] != 16749 or named[SOURCE]["owner"] != "dayhoff":
        raise RuntimeError("Source/control physical identity changed")
    if "dewey_prod_tapdb10" in named or (target_absent and TARGET in named):
        raise RuntimeError("An exact destination already exists; do not overwrite it")
    return named


def sessions(connection):
    return [dict(row) for row in connection.execute(text("SELECT pid,usename,client_addr::text,state FROM pg_catalog.pg_stat_activity WHERE datname=:source ORDER BY pid"), {"source": SOURCE}).mappings()]


def source_physical(connection):
    return dict(connection.execute(text("SELECT datname AS database, oid::bigint AS database_oid, inet_server_addr()::text AS server_address, inet_server_port() AS server_port FROM pg_catalog.pg_database WHERE datname=:source"), {"source": SOURCE}).mappings().one())


def copy_acl(connection):
    return [dict(row) for row in connection.execute(text("SELECT a.grantee::bigint AS grantee, a.privilege_type, a.is_grantable, d.datdba::bigint AS owner_oid FROM pg_catalog.pg_database d CROSS JOIN LATERAL aclexplode(COALESCE(d.datacl,acldefault('d',d.datdba))) a WHERE d.datname=:target ORDER BY a.grantee,a.privilege_type"), {"target": TARGET}).mappings()]


def native(arguments, log_path, handle):
    command = [str(ROOT / "venv/bin/tapdb"), "--config", str(ROOT / "source-operator.yaml"), "--json", *arguments]
    event(handle, "native_start", {"command": command, "log": str(log_path)})
    with log_path.open("x") as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    event(handle, "native_complete", {"returncode": result.returncode, "log": str(log_path)})
    if result.returncode:
        raise RuntimeError("Native source capture/plan failed; inspect retained log")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply"))
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from interactive ubuntu")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Exact RC required")
    cfg_at("source-operator.yaml", SOURCE)
    control = cfg_at("control-operator.yaml", "postgres")
    cfg_at("rehearsal-operator.yaml", TARGET)
    if hashlib.sha256(MAPPINGS.read_bytes()).hexdigest() != "5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8":
        raise RuntimeError("Mapping input changed")
    container = inspect_container()
    if not container["running"]:
        raise RuntimeError("Source already stopped; inspect before beginning this capsule")
    with operator_connection(control, read_only=True) as connection:
        databases = inspect_databases(connection, target_absent=True)
        if databases[SOURCE]["datallowconn"] is not True:
            raise RuntimeError("Source admission is already closed")
        settings = connection.execute(text("SELECT setrole FROM pg_catalog.pg_db_role_setting WHERE setdatabase=16749")).all()
        if settings:
            raise RuntimeError("Source has database-level settings needing explicit copy review")
        observed_sessions = sessions(connection)
        physical = source_physical(connection)
    fingerprint = {
        "source": SOURCE, "source_oid": 16749, "target": TARGET, "control": "postgres", "control_oid": 5,
        "container_id": CONTAINER_ID, "image": IMAGE,
        "source_physical": physical,
        "success_state": "source_closed_container_stopped_copy_operator_only",
        "config_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ("source-operator.yaml", "control-operator.yaml", "rehearsal-operator.yaml")},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sql": ["ALTER DATABASE \"dewey_prod\" ALLOW_CONNECTIONS false",
                "CREATE DATABASE \"dewey_tapdb10_rehearsal_20260911\" WITH TEMPLATE \"dewey_prod\" OWNER \"dayhoff\" ALLOW_CONNECTIONS false",
                "REVOKE CONNECT, TEMPORARY ON DATABASE \"dewey_tapdb10_rehearsal_20260911\" FROM PUBLIC",
                "ALTER DATABASE \"dewey_tapdb10_rehearsal_20260911\" ALLOW_CONNECTIONS true"],
    }
    if args.operation == "plan":
        new_json(PLAN, {"planned_at": utc(), "fingerprint": fingerprint, "observed_sessions": observed_sessions,
                        "steps": ["Gracefully stop exact Dewey container", "Require zero source sessions", "Capture native source and native read-only next plan", "Close source admission", "Create closed exact copy", "Restrict copy to owner access and open operator admission", "Verify source remains closed and container stopped"],
                        "backup_created": False, "apply_performed": False})
        print(json.dumps({"plan": str(PLAN), "status": "ready_for_independent_review"}))
        return
    approved = json.loads(PLAN.read_text())
    if approved["fingerprint"] != fingerprint:
        raise RuntimeError("Reviewed copy plan inputs changed")
    for path in (CUTOFF, NEXT, EMPTY, RESULT, EVENTS, *NATIVE_LOGS):
        if not path.parent.is_dir() or path.parent.is_symlink():
            raise RuntimeError("Operation output parent is absent or symlinked")
        if path.exists() or path.is_symlink():
            raise RuntimeError("An operation output exists; inspect instead of retrying")
    clock = time.monotonic()
    with EVENTS.open("x") as events:
        event(events, "stop_source_start", container)
        stopped = subprocess.run(["docker", "stop", "--time", "300", CONTAINER], capture_output=True, text=True)
        state = inspect_container()
        event(events, "stop_source_complete", {"returncode": stopped.returncode, **state})
        if stopped.returncode or state["running"] or state["oom_killed"] or state["exit_code"] not in (0,143):
            raise RuntimeError("Source did not stop gracefully; retain stopped state and inspect")
        with operator_connection(control, read_only=True) as connection:
            if sessions(connection):
                raise RuntimeError("Source sessions remain; do not terminate unknown writers")
        new_json(EMPTY, {"floors": []})
        native(["db","identity","inventory","--source-version","9.0.9","--sequence-mappings",str(MAPPINGS),"--receipt",str(CUTOFF)], NATIVE_LOGS[0], events)
        native(["db","sequences","advance","--floors",str(EMPTY),"--sequence-mappings",str(MAPPINGS),"--receipt",str(NEXT)], NATIVE_LOGS[1], events)
        source = json.loads(CUTOFF.read_text())
        planned = json.loads(NEXT.read_text())
        if planned["inventory"]["sha256"] != source["sequence_inventory"]["sha256"]:
            raise RuntimeError("Native next observation differs from the frozen source")
        with operator_session(control, isolation_level="AUTOCOMMIT") as connection:
            before = inspect_databases(connection, target_absent=True)
            observed_physical = source_physical(connection)
            if observed_physical != physical or source["identity_inventory"]["physical_target"] != observed_physical or source["sequence_inventory"]["physical_target"] != observed_physical or planned["inventory"]["physical_target"] != observed_physical:
                raise RuntimeError("Native cutoff/next physical identities differ from reviewed source/control")
            if not before[SOURCE]["datallowconn"] or sessions(connection):
                raise RuntimeError("Source admission/session state changed before copy")
            event(events, "source_gate_close_intent", {"source_oid": 16749})
            connection.execute(text(fingerprint["sql"][0]))
            event(events, "copy_create_intent", {"sql": fingerprint["sql"][1]})
            connection.execute(text(fingerprint["sql"][1]))
            copied = inspect_databases(connection, target_absent=False)[TARGET]
            if copied["owner"] != "dayhoff" or copied["datallowconn"] is not False:
                raise RuntimeError("Copy identity/admission differs")
            event(events, "copy_created_closed", copied)
            connection.execute(text(fingerprint["sql"][2]))
            connection.execute(text(fingerprint["sql"][3]))
            final_databases = inspect_databases(connection, target_absent=False)
            final_acl = copy_acl(connection)
            if final_databases[SOURCE]["datallowconn"] is not False or final_databases[TARGET]["datallowconn"] is not True or final_databases[TARGET]["oid"] != copied["oid"] or sessions(connection):
                raise RuntimeError("Final source/copy admission or identity differs")
            if not final_acl or any(row["grantee"] != row["owner_oid"] for row in final_acl):
                raise RuntimeError("Copy admission is not owner-only")
            event(events, "copy_operator_only_source_fenced", {"databases": final_databases, "copy_acl": final_acl})
        state = inspect_container()
        if state["running"]:
            raise RuntimeError("Original source container restarted unexpectedly")
        event(events, "source_container_remains_stopped", state)
        result = {"completed_at": utc(), "status": "copy_created_source_remains_fenced",
                  "elapsed_seconds": round(time.monotonic()-clock,3), "fingerprint": fingerprint,
                  "copied_database_at_creation": copied, "copied_database": final_databases[TARGET],
                  "final_database_gates": final_databases, "copy_acl": final_acl, "source_container": state,
                  "source_contract_sha256": source["sha256"],
                  "source_identity_sha256": source["identity_inventory"]["sha256"],
                  "source_sequence_sha256": source["sequence_inventory"]["sha256"],
                  "native_next_receipt": str(NEXT), "backup_created": False,
                  "schema_migration_performed": False, "target_runtime_started": False}
        new_json(RESULT, result)
        event(events, "copy_capsule_complete", {"result": str(RESULT)})


if __name__ == "__main__":
    main()
