#!/usr/bin/env python3
"""One-time native XRF assertions from Dewey's preserved authoritative lineage."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from dewey_metadata_conversion import (
    SCHEMA,
    canonical_path,
    file_hash,
    inventory,
    read,
    write_new,
)

ADAPTER_SHA = "f433e4a3382ba5738cf4d75de00c1d5e254e8f3420db2387b73357825503d298"
PAIRS = {
    ("atlas", "patient"): 1, ("bloom", "sequencer"): 1,
    ("bloom", "sequencing_run"): 131, ("ursa", "analysis"): 1,
    ("ursa", "analysis_job"): 152, ("dyec", "dayoa_analysis_directory"): 6,
    ("ursa", "run_directory_analysis_trigger"): 148,
}
NON_FEDERATED = {("dyec", "dayoa_analysis_directory"), ("ursa", "run_directory_analysis_trigger")}
RUNTIME_PATHS = {
    "dewey_tapdb10_rehearsal_20260911": (
        "/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml", "dewey_rehearsal_9"),
    "dewey_prod_tapdb10": ("/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml", "dewey_runtime_9"),
}


def register_identity(targets, assertions, source_uid, spec):
    """Native identity excludes object kind; distinct provenance is not deduplication."""
    target = spec.target
    identity = target.identity_key
    descriptor = (target.target_object_kind, str(target.target_tenant_id) if target.target_tenant_id is not None else None)
    if identity in targets:
        previous = targets[identity]
        if any(old is not None and new is not None and old != new for old, new in zip(previous, descriptor, strict=True)):
            raise ValueError("Conflicting non-null descriptors for one exact native target identity")
        # This specific conversion must create each new target with its complete
        # descriptor once. Do not silently enrich it during a later assertion.
        if previous != descriptor:
            raise ValueError("Target descriptor enrichment requires its own explicit reviewed disposition")
    targets[identity] = descriptor
    assertion = (source_uid, identity, spec.relationship_type)
    if assertion in assertions:
        raise ValueError("Multiple historical relations claim the same native assertion identity")
    assertions.add(assertion)


def adapter_at(path):
    canonical_path(path)
    if file_hash(path) != ADAPTER_SHA:
        raise ValueError("Require the exact independently accepted Dewey adapter")
    spec = importlib.util.spec_from_file_location("dewey_conversion_native_adapter", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load explicit adapter file")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def raw_row(session, model, uid):
    from sqlalchemy import Text, cast, func, select

    raw = session.execute(select(cast(func.to_jsonb(model.__table__.table_valued()), Text)).where(model.uid == uid)).scalar_one()
    return json.loads(raw, parse_float=str)


def collect(session, before, adapter):
    from daylily_tapdb.external_references import TapDBObjectTarget
    from daylily_tapdb.identity_inventory import content_hash
    from daylily_tapdb.models.instance import generic_instance
    from daylily_tapdb.models.lineage import generic_instance_lineage
    from sqlalchemy import select

    # Fresh-conversion admission is explicit; do not replay or reactivate a
    # previous partial conversion or hide an ambiguous native winner.
    existing = session.execute(select(generic_instance.uid).where(
        generic_instance.category == "reference", generic_instance.type == "external_identifier")).scalars().all()
    existing_links = session.execute(select(generic_instance_lineage.uid).where(
        generic_instance_lineage.subtype == "external_reference")).scalars().all()
    if existing or existing_links:
        raise ValueError("Existing scoped native external references require explicit recovery review")
    statement = select(generic_instance).where(
        generic_instance.category == "integration", generic_instance.type == "external_object_relation",
        generic_instance.subtype == "generic", generic_instance.version == "1.0").order_by(generic_instance.uid)
    objects, records, targets, assertions, originals = {}, [], {}, set(), {}
    pairs, dispositions = Counter(), Counter()
    for relation in session.execute(statement).scalars():
        endpoints = adapter.resolve_relation_endpoints(session, relation)
        for obj in (relation, endpoints.source, endpoints.external_object, endpoints.source_lineage, endpoints.external_lineage):
            table = obj.__tablename__
            if (table, obj.uid) not in originals:
                raw = raw_row(session, type(obj), obj.uid)
                key = content_hash([obj.uid])
                original = before["tables"][table]["rows"].get(key)
                if (original is None or original["count"] != 1 or original["sha256"] != content_hash(raw)
                        or raw["domain_code"] != "M" or raw["issuer_app_code"] != "dewey"
                        or raw["tenant_id"] is not None or raw["is_deleted"]
                        or not isinstance(obj.json_addl.get("properties"), dict)):
                    raise ValueError("Original lineage participant differs from the accepted native baseline")
                originals[(table, obj.uid)] = {"table": table, "uid": obj.uid, "row_key": key, "sha256": original["sha256"]}
        payload = endpoints.external_object.json_addl
        pair = (payload["external_system"], payload["external_object_type"])
        if pair not in PAIRS:
            raise ValueError("Unexpected historical external type outside the accepted seven pairs")
        pairs[pair] += 1
        spec = adapter.build_external_link_spec(relation, endpoints)
        disposition = "non_federated" if pair in NON_FEDERATED else "native_tapdb_object"
        if (spec is None) != (disposition == "non_federated"):
            raise ValueError("Adapter disposition differs from the explicit historical type decision")
        dispositions[disposition] += 1
        record = {"relation_uid": relation.uid, "source_uid": endpoints.source.uid,
                  "external_object_uid": endpoints.external_object.uid,
                  "source_lineage_uid": endpoints.source_lineage.uid,
                  "external_lineage_uid": endpoints.external_lineage.uid,
                  "system": pair[0], "object_type": pair[1], "disposition": disposition}
        if spec is not None:
            if not isinstance(spec.target, TapDBObjectTarget):
                raise ValueError("This historical conversion creates only canonical TapDB object targets")
            register_identity(targets, assertions, endpoints.source.uid, spec)
            record.update({"target_identity_sha256": content_hash(spec.target.identity_key),
                "relationship_type": spec.relationship_type, "assertion_authority": spec.assertion_authority,
                "asserted_at": spec.asserted_at.isoformat(),
                "assertion_provenance_sha256": content_hash(spec.assertion_provenance),
                "target_kind": spec.target.target_object_kind,
                "target_tenant_id": str(spec.target.target_tenant_id) if spec.target.target_tenant_id is not None else None})
        records.append(record)
        objects[relation.uid] = (relation, endpoints, spec)
    if dict(pairs) != PAIRS or dispositions != {"native_tapdb_object": 286, "non_federated": 154}:
        raise ValueError("Actual historical relation census differs from the reviewed input")
    counts = {"relations": len(records), "native_assertions": len(assertions), "native_targets": len(targets),
              "non_federated": dispositions["non_federated"], "original_participants": len(originals),
              "new_audit_rows": len(targets) + len(assertions)}
    return {"records": records, "counts": counts,
            "original_rows": sorted(originals.values(), key=lambda row: (row["table"], row["uid"]))}, objects


def capture_additions(session, before, outcomes, actor, expected_counts):
    from daylily_tapdb.identity_inventory import content_hash
    from daylily_tapdb.models.audit import audit_log
    from daylily_tapdb.models.instance import generic_instance
    from daylily_tapdb.models.lineage import generic_instance_lineage
    from sqlalchemy import Text, cast, func, select

    targets = {(item["reference_uid"], item["reference_euid"]) for item in outcomes}
    links = {(item["lineage_uid"], item["lineage_euid"]) for item in outcomes}
    expected = {"generic_instance": targets, "generic_instance_lineage": links}
    if len(targets) != expected_counts["native_targets"] or len(links) != expected_counts["native_assertions"]:
        raise ValueError("Native persisted target or assertion count differs from the exact plan")
    additions, audit_seen = {}, set()
    for table, model in (("generic_instance", generic_instance), ("generic_instance_lineage", generic_instance_lineage), ("audit_log", audit_log)):
        highest_uid = max(row["identity"]["uid"] for row in before["tables"][table]["rows"].values())
        statement = select(cast(func.to_jsonb(model.__table__.table_valued()), Text)).where(model.uid > highest_uid).order_by(model.uid)
        rows, actual = {}, set()
        for raw in session.execute(statement).scalars():
            row = json.loads(raw, parse_float=str)
            if row["domain_code"] != "M" or row["issuer_app_code"] != "dewey" or row["tenant_id"] is not None or row["is_deleted"]:
                raise ValueError("Native addition has unexpected scope or deletion state")
            key = content_hash([row["uid"]])
            if key in before["tables"][table]["rows"]:
                raise ValueError("Native allocation reused an original persisted UID")
            if table == "audit_log":
                target = (row["rel_table_name"], row["rel_table_uid_fk"], row["rel_table_euid_fk"])
                if (row["changed_by"] != actor or row["operation_type"] != "INSERT" or row["column_name"] is not None
                        or row["old_value"] is not None or row["new_value"] is not None or target in audit_seen
                        or (target[1], target[2]) not in expected.get(target[0], set())):
                    raise ValueError("Native audit additions differ from exact created rows and actor")
                audit_seen.add(target)
            else:
                actual.add((row["uid"], row["euid"]))
                if table == "generic_instance" and (row["euid_prefix"] != "XRF" or (
                        row["category"], row["type"], row["subtype"], row["version"]) != (
                        "reference", "external_identifier", "tapdb_object", "1.0")):
                    raise ValueError("Native reference creation returned an unexpected typed object")
                if table == "generic_instance_lineage" and row["subtype"] != "external_reference":
                    raise ValueError("Native reference creation added an unrelated lineage")
            rows[key] = content_hash(row)
        if table != "audit_log" and actual != expected[table]:
            raise ValueError("Native additions include missing or unplanned objects/lineages")
        additions[table] = rows
    if len(audit_seen) != expected_counts["new_audit_rows"]:
        raise ValueError("Native operation did not create exact one audit insert per new row")
    return additions


def make_manifest(before, after, result):
    if (before["sha256"] != result["plan"]["before_inventory_sha256"]
            or before["target"] != after["target"] or before["physical_target"] != after["physical_target"]):
        raise ValueError("Native reference proof changed baseline or physical/config target")
    expected_tables = {"generic_instance", "generic_instance_lineage", "audit_log"}
    if set(result["new_rows"]) != expected_tables:
        raise ValueError("Native result must account for all exact addition tables")
    planned = [(row["relation_uid"], row["source_uid"], row["target_identity_sha256"])
               for row in result["plan"]["records"] if row["disposition"] == "native_tapdb_object"]
    actual_outcomes = [(row["relation_uid"], row["source_uid"], row["target_identity_sha256"])
                       for row in result["outcomes"]]
    if planned != actual_outcomes:
        raise ValueError("Committed native outcomes differ from the exact planned assertions")
    expected_counts = {"generic_instance": result["plan"]["counts"]["native_targets"],
                       "generic_instance_lineage": result["plan"]["counts"]["native_assertions"],
                       "audit_log": result["plan"]["counts"]["new_audit_rows"]}
    for table, expected in result["new_rows"].items():
        actual = {key: row["sha256"] for key, row in after["tables"][table]["rows"].items()
                  if key not in before["tables"][table]["rows"]}
        if actual != expected or len(actual) != expected_counts[table]:
            raise ValueError("Fresh native inventory additions differ from committed native outcomes")
    return {"schema_version": "tapdb-identity-conversion/v1",
            "tables": {table: {"added_rows": True} for table in ("generic_instance", "generic_instance_lineage", "audit_log")},
            "added_tables": []}


def runtime_connection(cfg, config, actor, *, read_only):
    from daylily_tapdb import TAPDBConnection

    if cfg["iam_auth"] not in {"True", "False", "true", "false"}:
        raise ValueError("Require the explicit configured native IAM boolean")
    ca_path = Path(cfg["sslrootcert"])
    if not ca_path.is_absolute() or not ca_path.is_file():
        raise ValueError("Require the exact configured existing CA file; no certificate discovery")
    db = TAPDBConnection(db_hostname=f"{cfg['host']}:{cfg['port']}", db_user=cfg["user"],
        db_pass=cfg["password"], db_name=cfg["database"], app_username=actor,
        engine_type=cfg["engine_type"], region=cfg["region"], iam_auth=cfg["iam_auth"].lower() == "true",
        secret_arn=cfg["secret_arn"] or None, domain_code=cfg["domain_code"], owner_repo_name=cfg["owner_repo_name"],
        schema_name=cfg["schema_name"], tenant_id=cfg["tenant_id"] or None,
        allow_global_rows=cfg["allow_global_claims"], config_identity=str(config), connection_role="runtime",
        aws_profile=cfg["aws_profile"] or None, sslrootcert=cfg["sslrootcert"],
        db_hostaddr=cfg.get("hostaddr"), server_port=int(cfg["server_port"]) if "server_port" in cfg else None)
    db.engine.update_execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=read_only)
    return db


def main():
    from daylily_tapdb.cli.db_config import get_db_config
    from daylily_tapdb.identity_inventory import (
        content_hash,
        physical_target,
        require_snapshot,
        validate_receipt,
    )
    from daylily_tapdb.runtime_principal import operator_connection
    from dewey_rehearsal_copy import cfg_at
    from dewey_xrf_template_setup_port_fix import definitions, frozen_source, template_state
    from sqlalchemy import text

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply", "manifest"))
    parser.add_argument("--operator-config", type=Path, required=True)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--metadata-verification", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target-oid", type=int, required=True)
    parser.add_argument("--candidate-container", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--reviewed-plan-sha256")
    parser.add_argument("--review-reference")
    parser.add_argument("--after", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use the approved targeted sudo from the retained ubuntu operator session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Require exact immutable TapDB 10.1.1rc1")
    for path in (args.operator_config, args.adapter, args.before, args.metadata_verification):
        canonical_path(path)
    canonical_path(args.output_dir, directory=True)
    if not args.actor.strip() or args.actor != args.actor.strip():
        raise ValueError("Require exact explicit audit actor")
    before = inventory(args.before)
    metadata_proof = read(args.metadata_verification)
    validate_receipt(metadata_proof, "tapdb-identity-verification/v1")
    if metadata_proof["ok"] is not True or metadata_proof["violations"] or metadata_proof["after_sha256"] != before["sha256"]:
        raise ValueError("Require successful native metadata proof for this exact before inventory")
    operator = get_db_config(config_path=args.operator_config, client_id="dewey", database_name="dewey-day")
    database = operator["database"]
    if (database not in RUNTIME_PATHS or operator["operator_user"] != "dayhoff"
            or before["target"]["database"] != database or before["target"]["config_identity"] != str(args.operator_config)
            or before["physical_target"]["database_oid"] != args.target_oid):
        raise ValueError("Wrong explicit native baseline or copy operator")
    runtime_path, runtime_user = RUNTIME_PATHS[database]
    if str(args.runtime_config) != runtime_path or args.runtime_config.resolve() != args.runtime_config or not args.runtime_config.is_file():
        raise ValueError("Require the exact separately bound runtime config pathname")
    cfg = get_db_config(config_path=args.runtime_config, client_id="dewey", database_name="dewey-day")
    for field in ("database", "host", "port", "schema_name", "domain_code", "owner_repo_name", "region", "engine_type"):
        if cfg[field] != operator[field]:
            raise ValueError("Runtime and operator name different explicit targets")
    if (cfg["schema_name"] != SCHEMA or cfg["domain_code"] != "M" or cfg["owner_repo_name"] != "dewey"
            or cfg["engine_type"] != "aurora" or cfg["user"] != runtime_user or cfg["operator_configured"]
            or cfg["tenant_id"] != "" or cfg["allow_global_claims"] is not False):
        raise ValueError("Runtime principal/config scope differs from the accepted bound role")
    inputs = {"operator_config": args.operator_config, "runtime_config": args.runtime_config,
        "adapter": args.adapter, "before": args.before, "metadata_verification": args.metadata_verification,
        "script": Path(__file__), "metadata_helper": Path(__file__).parent / "dewey_metadata_conversion.py",
        "template_helper": Path(__file__).parent / "dewey_xrf_template_setup_port_fix.py",
        "copy_helper": Path(__file__).parent / "dewey_rehearsal_copy.py"}
    fingerprint = {"schema_version": "dewey-native-reference-plan/v1", "inputs": {
        key: {"path": str(path), "file_sha256": file_hash(path)} for key, path in inputs.items()},
        "before_inventory_sha256": before["sha256"], "target": before["target"], "physical_target": before["physical_target"],
        "actor": args.actor, "target_oid": args.target_oid, "candidate_container": args.candidate_container,
        "metadata_verification_sha256": metadata_proof["sha256"]}
    plan_path, result_path = args.output_dir / "reference-plan.json", args.output_dir / "reference-result.json"
    if args.operation == "manifest":
        if args.after is None:
            raise ValueError("Require the fresh native after inventory")
        canonical_path(args.after)
        result = read(result_path)
        if (result["status"] != "committed" or result["plan"] != read(plan_path)
                or result["plan_file_sha256"] != file_hash(plan_path)
                or any(result["plan"][key] != value for key, value in fingerprint.items())):
            raise ValueError("Require exact committed native plan and unchanged inputs")
        manifest = make_manifest(before, inventory(args.after), result)
        path = args.output_dir / "reference-conversion-manifest.json"
        write_new(path, manifest)
        print(json.dumps({"status": "manifest_prepared", "path": str(path), "file_sha256": file_hash(path)}))
        return
    if args.operation == "apply":
        if not args.reviewed_plan_sha256 or file_hash(plan_path) != args.reviewed_plan_sha256 or not str(args.review_reference or "").strip():
            raise ValueError("Require exact independently reviewed plan hash and reference")
        for name in ("reference-apply.started.json", "reference-result.json"):
            if (args.output_dir / name).exists() or (args.output_dir / name).is_symlink():
                raise FileExistsError("Prior write evidence exists; inspect instead of replaying")
    source = frozen_source(cfg_at("control-operator.yaml", "postgres"))
    candidate = json.loads(subprocess.check_output(["docker", "inspect", args.candidate_container], text=True))[0]
    if candidate["State"]["Running"]:
        raise RuntimeError("Candidate writer must remain stopped during conversion")
    with operator_connection(operator, read_only=True) as connection:
        if physical_target(connection, before["target"]) != before["physical_target"]:
            raise ValueError("Operator physical database differs from native before")
        if connection.execute(text("SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")).scalar_one() != 0:
            raise RuntimeError("Another target session exists")
    adapter = adapter_at(args.adapter)
    _, template_definitions = definitions()
    db = runtime_connection(cfg, args.runtime_config, args.actor, read_only=args.operation == "plan")
    try:
        with db.session_scope(commit=args.operation == "apply") as session:
            connection = session.connection()
            require_snapshot(connection)
            if physical_target(connection, before["target"]) != before["physical_target"]:
                raise ValueError("Runtime physical database differs from native before")
            if connection.execute(text("SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")).scalar_one() != 0:
                raise RuntimeError("Another target session appeared before native conversion")
            scoped_templates = template_state(session, template_definitions)
            if len(scoped_templates["existing_scoped_uids"]) != 2:
                raise ValueError("Runtime cannot see both exact newly bound canonical templates")
            collection, objects = collect(session, before, adapter)
            plan = {**fingerprint, **collection, "source_freeze": source,
                "candidate": {"id": candidate["Id"], "image": candidate["Image"]}, "runtime_templates": scoped_templates}
            if args.operation == "plan":
                write_new(plan_path, plan)
                print(json.dumps({"status": "planned", "path": str(plan_path), "file_sha256": file_hash(plan_path), "counts": plan["counts"]}))
                return
            if plan != read(plan_path):
                raise ValueError("Native relation inputs differ from the exact reviewed plan")
            write_new(args.output_dir / "reference-apply.started.json", {
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat(), "plan_file_sha256": file_hash(plan_path),
                "review_reference": args.review_reference,
                "warning": "Failed/ambiguous native allocations remain future floors; retain evidence and do not blindly replay"})
            outcomes = []
            for item in plan["records"]:
                relation, endpoints, spec = objects[item["relation_uid"]]
                outcome = adapter.attach_external_relation(session, relation)
                if item["disposition"] == "non_federated":
                    if outcome.status != "non_federated" or outcome.reference is not None or outcome.lineage is not None:
                        raise ValueError("Native adapter changed an explicitly non-federated relation")
                    continue
                reference, lineage = outcome.reference, outcome.lineage
                if (outcome.status != "created" or reference is None or lineage is None
                        or reference.identity_key != spec.target.identity_key
                        or lineage.parent_instance_uid != endpoints.source.uid or lineage.child_instance_uid != reference.uid
                        or lineage.relationship_type != spec.relationship_type
                        or lineage.json_addl["properties"]["assertion_authority"] != spec.assertion_authority
                        or lineage.json_addl["properties"]["asserted_at"] != spec.asserted_at.isoformat()
                        or lineage.json_addl["properties"]["assertion_provenance"] != spec.assertion_provenance):
                    raise ValueError("Native lifecycle outcome differs from exact persisted assertion plan")
                outcomes.append({"relation_uid": relation.uid, "source_uid": endpoints.source.uid,
                    "target_identity_sha256": content_hash(spec.target.identity_key),
                    "reference_uid": reference.uid, "reference_euid": reference.euid,
                    "lineage_uid": lineage.uid, "lineage_euid": lineage.euid})
            session.flush()
            additions = capture_additions(session, before, outcomes, args.actor, plan["counts"])
    finally:
        db.close()
    write_new(result_path, {"schema_version": "dewey-native-reference-result/v1", "status": "committed",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(), "plan": plan,
        "plan_file_sha256": file_hash(plan_path), "review_reference": args.review_reference,
        "outcomes": outcomes, "new_rows": additions})
    print(json.dumps({"status": "committed", "path": str(result_path), "counts": plan["counts"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "stopped", "error_class": type(exc).__name__}))
        raise SystemExit(1) from None
