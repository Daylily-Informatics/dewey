#!/usr/bin/env python3
"""Explicit one-time historical metadata conversion through TapDB public APIs.

No application startup, XRF creation, template change, sequence manipulation,
backup, source reconnect, or automatic continuation. O owns the writer outage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import subprocess
from collections import Counter
from copy import deepcopy
from pathlib import Path

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
SCHEMA = "tapdb_dewey_lsmcok1_local"
ARCHIVE_KEY = "dewey_tapdb10_archive"
GRAPH_PATH = "properties.external_payload.tapdb_graph"
EXPECTED = {
    "generic_instance": {"rows": 12200, "changed": 12200, "add_properties": 12091, "archive_graph": 109},
    "generic_instance_lineage": {"rows": 1015, "changed": 1014, "add_properties": 1014, "archive_graph": 0},
}


def read(path):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    def nonfinite(_):
        raise ValueError("Non-finite JSON number")

    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_new(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def canonical_path(path, *, directory=False):
    if not path.is_absolute() or path.resolve() != path or not path.is_relative_to(ROOT):
        raise ValueError("Require an explicit canonical path in the protected operator root")
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("Explicit input path does not exist")
    return path


def convert_payload(payload):
    """Retain every old value; add the envelope and archive only the old projection."""
    if not isinstance(payload, dict):
        raise ValueError("Historical json_addl must be an object")
    if ARCHIVE_KEY in payload:
        raise ValueError("Archive key already exists; do not overwrite or replay")
    result = deepcopy(payload)
    effects = []
    if "properties" not in result:
        result["properties"] = {}
        effects.append("add_properties")
    properties = result["properties"]
    if not isinstance(properties, dict):
        raise ValueError("Existing properties must be an object; missing is the only envelope conversion")
    forbidden = {key for key in properties if key in {"object_euid", "target_object_euid"} or key.endswith("_object_euid")}
    if forbidden:
        raise ValueError("Unexpected pseudo-edge field requires a separate reviewed disposition")
    external = properties.get("external_payload")
    if external is not None and not isinstance(external, dict):
        raise ValueError("Existing external_payload must be an object")
    if isinstance(external, dict) and "tapdb_graph" in external:
        graph = external["tapdb_graph"]
        if not isinstance(graph, list):
            raise ValueError("Historical graph projection must be its observed list shape")
        if any(not isinstance(item, dict) or item.get("source_field") != "dewey.external_object_relation" for item in graph):
            raise ValueError("Unknown graph projection owner; no metadata-to-lineage inference")
        result[ARCHIVE_KEY] = {GRAPH_PATH: deepcopy(graph)}
        del external["tapdb_graph"]
        effects.append("archive_graph")
    return result, effects


def inventory(path):
    from daylily_tapdb.backup.source_contract import validate_source_contract
    from daylily_tapdb.identity_inventory import validate_receipt

    document = read(path)
    if document["schema_version"] == "tapdb-source-contract/v1":
        validate_source_contract(document)
        document = document["identity_inventory"]
    validate_receipt(document, "tapdb-identity-inventory/v1")
    return document


def native_value_hash(value):
    from daylily_tapdb.identity_inventory import content_hash

    # Match the public inventory's PostgreSQL JSON float normalization. The
    # caller also compares the raw PostgreSQL cell, refusing lossy ORM reads.
    serialized = json.dumps(value, allow_nan=False)
    return content_hash(json.loads(serialized, parse_float=str))


def input_fingerprint(args, before):
    return {
        "schema_version": "dewey-metadata-conversion-plan/v1",
        "config": str(args.config), "config_file_sha256": file_hash(args.config),
        "before": str(args.before), "before_file_sha256": file_hash(args.before),
        "before_inventory_sha256": before["sha256"],
        "target": before["target"], "physical_target": before["physical_target"],
        "actor": args.actor, "target_oid": args.target_oid,
        "candidate_container": args.candidate_container,
        "script_file_sha256": file_hash(Path(__file__)),
        "setup_helper_sha256": file_hash(Path(__file__).parent / "dewey_xrf_template_setup_port_fix.py"),
        "copy_helper_sha256": file_hash(Path(__file__).parent / "dewey_rehearsal_copy.py"),
        "archive_contract": {"root_key": ARCHIVE_KEY, "source_path": GRAPH_PATH},
    }


def collect(session, before, *, lock=False):
    from daylily_tapdb.identity_inventory import content_hash
    from daylily_tapdb.models.instance import generic_instance
    from daylily_tapdb.models.lineage import generic_instance_lineage
    from sqlalchemy import Text, cast, func, select

    changes, objects, counts = [], {}, {}
    for table, model in (("generic_instance", generic_instance), ("generic_instance_lineage", generic_instance_lineage)):
        statement = select(model, cast(func.to_jsonb(model.json_addl), Text), cast(func.to_jsonb(model.modified_dt), Text)).where(
            model.domain_code == "M", model.issuer_app_code == "dewey")
        if table == "generic_instance":
            statement = statement.where(model.euid_prefix == "DGX")
        statement = statement.order_by(model.uid)
        if lock:
            statement = statement.with_for_update()
        observed = Counter(rows=0, changed=0, add_properties=0, archive_graph=0)
        for obj, raw_payload, raw_modified in session.execute(statement):
            observed["rows"] += 1
            key = content_hash([obj.uid])
            original = before["tables"][table]["rows"].get(key)
            if original is None or original["count"] != 1:
                raise ValueError("Selected original row is absent or ambiguous in native inventory")
            old_hash = content_hash(json.loads(raw_payload, parse_float=str))
            old_modified = content_hash(None if raw_modified is None else json.loads(raw_modified))
            if (old_hash != original["columns"]["json_addl"]
                    or old_modified != original["columns"]["modified_dt"]
                    or native_value_hash(obj.json_addl) != old_hash):
                raise ValueError("Original cell changed or ORM JSON decoding loses native precision")
            proposed, effects = convert_payload(obj.json_addl)
            if not effects:
                continue
            if obj.is_deleted:
                raise ValueError("Public update_object refuses deleted rows; preserve and review explicitly")
            if table == "generic_instance_lineage" and (obj.parent_instance.is_deleted or obj.child_instance.is_deleted):
                raise ValueError("Lineage metadata update has a deleted endpoint; preserve and review explicitly")
            observed["changed"] += 1
            observed.update(effects)
            entry = {"table": table, "record_type": "instance" if table == "generic_instance" else "lineage",
                     "uid": obj.uid, "row_key": key, "json_before": old_hash,
                     "json_after": native_value_hash(proposed), "modified_before": old_modified, "effects": effects}
            changes.append(entry)
            objects[(table, obj.uid)] = (obj, proposed)
        counts[table] = dict(observed)
    if counts != EXPECTED:
        raise ValueError("Historical metadata scope differs from the reviewed actual census")
    return changes, objects, counts


def make_manifest(before, after, result):
    """Only exact planned JSON and DB-owned timestamp changes, plus new audit rows."""
    if before["sha256"] != result["plan"]["before_inventory_sha256"]:
        raise ValueError("Before inventory differs from committed operation")
    if after["target"] != before["target"] or after["physical_target"] != before["physical_target"]:
        raise ValueError("Metadata proof cannot relocate the database or config")
    if [{key: value for key, value in item.items() if key != "modified_after"} for item in result["applied_changes"]] != result["plan"]["changes"]:
        raise ValueError("Applied change set differs from the exact reviewed plan")
    new_audit = {key: row["sha256"] for key, row in after["tables"]["audit_log"]["rows"].items()
                 if key not in before["tables"]["audit_log"]["rows"]}
    if new_audit != result["new_audit_rows"] or len(new_audit) != result["plan"]["expected_audit_rows"]:
        raise ValueError("Fresh native audit additions differ from the exact observed transaction")
    tables = {"audit_log": {"added_rows": True}}
    for item in result["applied_changes"]:
        key, name = item["row_key"], item["table"]
        current = after["tables"][name]["rows"][key]["columns"]
        if current["json_addl"] != item["json_after"] or current["modified_dt"] != item["modified_after"]:
            raise ValueError("Fresh native inventory differs from exact applied cells")
        changed = tables.setdefault(name, {"changed_columns": {}})["changed_columns"]
        for column, old, new in (("json_addl", item["json_before"], item["json_after"]),
                                 ("modified_dt", item["modified_before"], item["modified_after"])):
            changed.setdefault(column, {"kind": "exact_value_hashes", "changes": {}})["changes"][key] = {"before": old, "after": new}
    return {"schema_version": "tapdb-identity-conversion/v1", "tables": tables, "added_tables": []}


def check_new_audit(session, before, changes, objects, actor):
    from daylily_tapdb.identity_inventory import content_hash
    from daylily_tapdb.models.audit import audit_log
    from sqlalchemy import Text, cast, func, select

    original_rows = before["tables"]["audit_log"]["rows"]
    highest_uid = max(row["identity"]["uid"] for row in original_rows.values())
    expected = {(item["table"], item["uid"], column): item for item in changes for column in ("created_dt", "json_addl", "modified_dt")}
    observed, hashes = set(), {}
    statement = select(cast(func.to_jsonb(audit_log.__table__.table_valued()), Text)).where(audit_log.uid > highest_uid).order_by(audit_log.uid)
    for raw in session.execute(statement).scalars():
        row = json.loads(raw, parse_float=str)
        key = (row["rel_table_name"], row["rel_table_uid_fk"], row["column_name"])
        if (key not in expected or key in observed or row["changed_by"] != actor or row["operation_type"] != "UPDATE"
                or row["domain_code"] != "M" or row["issuer_app_code"] != "dewey" or row["tenant_id"] is not None
                or row["is_deleted"] or row["rel_table_euid_fk"] != objects[(key[0], key[1])][0].euid):
            raise ValueError("Unexpected audit addition, target, scope or attribution")
        item = expected[key]
        if key[2] == "json_addl" and (content_hash(json.loads(row["old_value"], parse_float=str)) != item["json_before"]
                or content_hash(json.loads(row["new_value"], parse_float=str)) != item["json_after"]):
            raise ValueError("Audit does not retain the exact original and converted metadata")
        if key[2] == "created_dt":
            # The released trigger compares SQL timestamp text with JSON text.
            # Preserve its audit row while requiring the original instant exactly.
            original_hash = before["tables"][key[0]]["rows"][item["row_key"]]["columns"]["created_dt"]
            old_instant = dt.datetime.fromisoformat(row["old_value"])
            new_instant = dt.datetime.fromisoformat(row["new_value"])
            if (old_instant.tzinfo is None or new_instant.tzinfo is None
                    or old_instant != new_instant
                    or new_instant != objects[(key[0], key[1])][0].created_dt
                    or content_hash(row["new_value"]) != original_hash):
                raise ValueError("Native creation audit must retain the exact original timestamp")
        observed.add(key)
        hashes[content_hash([row["uid"]])] = content_hash(row)
    if observed != set(expected):
        raise ValueError("Expected exact three native audit additions per changed original row")
    return hashes


def main():
    from daylily_tapdb.cli.db_config import get_db_config
    from daylily_tapdb.identity_inventory import content_hash, physical_target
    from daylily_tapdb.runtime_principal import operator_connection
    from daylily_tapdb.security_context import (
        TapdbTransactionContext,
        apply_transaction_context,
        assert_operator_role,
    )
    from daylily_tapdb.services.object_operations import ObjectSelector, update_object
    from dewey_rehearsal_copy import cfg_at
    from dewey_xrf_template_setup_port_fix import frozen_source
    from sqlalchemy import Text, cast, func, select, text
    from sqlalchemy.orm import Session

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply", "manifest"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--target-oid", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--candidate-container", required=True)
    parser.add_argument("--reviewed-plan-sha256")
    parser.add_argument("--review-reference")
    parser.add_argument("--after", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu operator session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Require the exact released RC")
    for path in (args.config, args.before):
        canonical_path(path)
    canonical_path(args.output_dir, directory=True)
    if not args.actor.strip() or args.actor.strip() != args.actor:
        raise ValueError("Require an explicit exact audit actor")
    before = inventory(args.before)
    cfg = get_db_config(config_path=args.config, client_id="dewey", database_name="dewey-day")
    if (cfg["database"] not in {"dewey_tapdb10_rehearsal_20260911", "dewey_prod_tapdb10"}
            or cfg["operator_user"] != "dayhoff" or cfg["schema_name"] != SCHEMA
            or cfg["domain_code"] != "M" or cfg["owner_repo_name"] != "dewey"
            or before["target"]["config_identity"] != str(args.config)
            or before["target"]["database"] != cfg["database"]
            or before["physical_target"]["database_oid"] != args.target_oid):
        raise ValueError("Wrong explicit operator/copy/native before identity")
    plan_path = args.output_dir / "metadata-plan.json"
    result_path = args.output_dir / "metadata-result.json"
    fingerprint = input_fingerprint(args, before)
    if args.operation == "manifest":
        if args.after is None:
            raise ValueError("Require fresh native after inventory")
        canonical_path(args.after)
        result = read(result_path)
        if (result["status"] != "committed" or result["plan"] != read(plan_path)
                or result["plan_file_sha256"] != file_hash(plan_path)
                or any(result["plan"][key] != value for key, value in fingerprint.items())):
            raise ValueError("Require exact committed plan/inputs")
        after = inventory(args.after)
        manifest = make_manifest(before, after, result)
        write_new(args.output_dir / "metadata-conversion-manifest.json", manifest)
        print(json.dumps({"status": "manifest_prepared", "manifest": str(args.output_dir / "metadata-conversion-manifest.json")}))
        return
    if args.operation == "apply":
        if not args.reviewed_plan_sha256 or file_hash(plan_path) != args.reviewed_plan_sha256 or not str(args.review_reference or "").strip():
            raise ValueError("Apply requires exact reviewed plan file hash and independent review reference")
        for name in ("metadata-apply.started.json", "metadata-result.json"):
            if (args.output_dir / name).exists() or (args.output_dir / name).is_symlink():
                raise FileExistsError("Prior apply evidence exists; inspect instead of retrying")
    source = frozen_source(cfg_at("control-operator.yaml", "postgres"))
    candidate = json.loads(subprocess.check_output(["docker", "inspect", args.candidate_container], text=True))[0]
    if candidate["State"]["Running"]:
        raise RuntimeError("Candidate writer must remain stopped for metadata conversion")
    with operator_connection(cfg, isolation_level="REPEATABLE READ", read_only=args.operation == "plan") as connection:
        if physical_target(connection, before["target"]) != before["physical_target"]:
            raise ValueError("Live physical target differs from native before inventory")
        with Session(bind=connection, expire_on_commit=False) as session:
            context = TapdbTransactionContext(config_identity=str(args.config), schema_name=SCHEMA,
                domain_code="M", owner_repo_name="dewey", tenant_id=cfg["tenant_id"] or None,
                actor=args.actor, allow_global_rows=cfg["allow_global_claims"])
            apply_transaction_context(session, context, assert_runtime_role=False)
            assert_operator_role(session, schema_name=SCHEMA, operator_user="dayhoff")
            if connection.execute(text("SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")).scalar_one() != 0:
                raise RuntimeError("Another target session exists; preserve outage and inspect")
            from daylily_tapdb.models.audit import audit_log

            original_audit_uid = max(row["identity"]["uid"] for row in before["tables"]["audit_log"]["rows"].values())
            if session.execute(select(func.count()).select_from(audit_log).where(audit_log.uid > original_audit_uid)).scalar_one():
                raise ValueError("Persisted audit additions exist after the exact before inventory; reconcile before applying")
            changes, objects, counts = collect(session, before, lock=args.operation == "apply")
            plan = {**fingerprint, "counts": counts, "changes": changes,
                    "source_freeze": source, "candidate": {"id": candidate["Id"], "image": candidate["Image"]},
                    "expected_audit_rows": 3 * len(changes)}
            if args.operation == "plan":
                write_new(plan_path, plan)
                print(json.dumps({"status": "planned", "plan": str(plan_path), "file_sha256": file_hash(plan_path), "counts": counts}))
                return
            if plan != read(plan_path):
                raise ValueError("Actual metadata or inputs changed after reviewed plan")
            write_new(args.output_dir / "metadata-apply.started.json", {
                "plan_file_sha256": file_hash(plan_path), "review_reference": args.review_reference,
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "warning": "Any ambiguous/failing write may consume sequence values; retain evidence and capture floors before recovery"})
            applied = []
            raw_timestamp = session.execute(select(cast(func.to_jsonb(func.current_timestamp()), Text))).scalar_one()
            timestamp_hash = content_hash(json.loads(raw_timestamp))
            for item in changes:
                obj, proposed = objects[(item["table"], item["uid"])]
                update_object(session, ObjectSelector(uid=item["uid"], record_type=item["record_type"]),
                              {"json_addl": proposed}, actor=args.actor, dry_run=False)
                raw_json, raw_modified = session.execute(select(cast(func.to_jsonb(type(obj).json_addl), Text),
                    cast(func.to_jsonb(type(obj).modified_dt), Text)).where(type(obj).uid == item["uid"])).one()
                if content_hash(json.loads(raw_json, parse_float=str)) != item["json_after"]:
                    raise ValueError("Database JSON differs from lossless planned metadata")
                modified_hash = content_hash(None if raw_modified is None else json.loads(raw_modified))
                if modified_hash == item["modified_before"] or modified_hash != timestamp_hash:
                    raise ValueError("Expected exact DB transaction timestamp change was absent")
                applied.append({**item, "modified_after": modified_hash})
            session.flush()
            audit_rows = check_new_audit(session, before, changes, objects, args.actor)
    # This record exists only after operator_connection's real commit returned.
    write_new(result_path, {"schema_version": "dewey-metadata-conversion-result/v1", "status": "committed",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(), "plan": plan,
        "plan_file_sha256": file_hash(plan_path), "review_reference": args.review_reference,
        "applied_changes": applied, "new_audit_rows": audit_rows})
    print(json.dumps({"status": "committed", "receipt": str(result_path), "changed_rows": len(applied)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        frames = traceback.extract_tb(exc.__traceback__)
        print(json.dumps({"status": "stopped", "error_class": type(exc).__name__,
                          "locations": [{"file": Path(frame.filename).name, "line": frame.lineno} for frame in frames]}))
        raise SystemExit(1) from None
