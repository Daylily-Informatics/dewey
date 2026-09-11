#!/usr/bin/env python3
"""One-time exact bundled XRF template setup; no runtime startup or old template rewrite."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
from pathlib import Path

from dewey_rehearsal_copy import (
    ROOT,
    cfg_at,
    inspect_container,
    new_json,
    sessions,
    source_physical,
    utc,
)

FIELDS = ("name", "polymorphic_discriminator", "category", "type", "subtype", "version",
          "instance_prefix", "is_singleton", "bstatus", "json_addl", "json_addl_schema")
CODES = {("reference", "external_identifier", "tapdb_object", "1.0"),
         ("reference", "external_identifier", "opaque", "1.0")}


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def definitions():
    from daylily_tapdb.templates.loader import find_tapdb_core_config_dir, load_template_configs

    core = find_tapdb_core_config_dir()
    selected = [row for row in load_template_configs(core)
                if tuple(row.get(key) for key in ("category", "type", "subtype", "version")) in CODES]
    if len(selected) != 2 or {row["subtype"] for row in selected} != {"tapdb_object", "opaque"} or any(row["instance_prefix"] != "XRF" for row in selected):
        raise ValueError("Installed RC does not supply the exact two canonical XRF templates")
    return core, sorted(selected, key=lambda row: row["subtype"])


def template_state(session, templates):
    from daylily_tapdb.identity_inventory import content_hash
    from daylily_tapdb.models.template import generic_template
    from sqlalchemy import Text, cast, func, select

    rows = session.execute(select(cast(func.to_jsonb(generic_template.__table__.table_valued()), Text))
                           .order_by(generic_template.uid)).scalars().all()
    documents = [json.loads(row, parse_float=str) for row in rows]
    existing = []
    for definition in templates:
        matches = [row for row in documents if row["domain_code"] == "M" and row["issuer_app_code"] == "dewey"
                   and all(row[key] == definition[key] for key in ("category", "type", "subtype", "version"))]
        if len(matches) > 1:
            raise ValueError("Ambiguous scoped canonical template")
        if matches:
            row = matches[0]
            if row["is_deleted"] or any(row[field] != definition.get(field) for field in FIELDS):
                raise ValueError("Existing scoped XRF template is divergent; never overwrite it")
            existing.append(row["uid"])
    return {"row_count": len(documents), "original_rows": {str(row["uid"]): content_hash(row) for row in documents},
            "existing_scoped_uids": sorted(existing)}


def frozen_source(control):
    from daylily_tapdb.runtime_principal import operator_connection
    from sqlalchemy import text

    container = inspect_container()
    if container["running"]:
        raise RuntimeError("Original source container restarted")
    with operator_connection(control, read_only=True) as connection:
        state = source_physical(connection)
        admission = connection.execute(text("SELECT datallowconn FROM pg_catalog.pg_database WHERE oid=16749 AND datname='dewey_prod' AND pg_get_userbyid(datdba)='dayhoff'")).scalar_one()
        if admission is not False or sessions(connection):
            raise RuntimeError("Original source is not continuously closed and session-free")
    frozen = json.loads((ROOT / "receipts/rehearsal-copy-sop-result.json").read_text())
    if (digest(ROOT / "receipts/rehearsal-copy-sop-result.json") != "2e477de116715b8c42c127618188d9607ac26826fb97453059b7921dd6c6ba7c"
            or state != frozen["fingerprint"]["source_physical"]):
        raise RuntimeError("Original source physical identity changed")
    return {"physical": state, "container_id": container["id"], "image": container["image"]}


def main():
    from daylily_tapdb.identity_inventory import content_hash, physical_target
    from daylily_tapdb.runtime_principal import operator_connection
    from daylily_tapdb.security_context import (
        TapdbTransactionContext,
        apply_transaction_context,
        assert_operator_role,
    )
    from daylily_tapdb.templates.loader import seed_templates
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply"))
    parser.add_argument("--lane", choices=("rehearsal", "production"), required=True)
    parser.add_argument("--target-oid", type=int, required=True)
    parser.add_argument("--candidate-container", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--reviewed-plan-sha256")
    parser.add_argument("--review-reference")
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Exact released RC required")
    if not args.actor.strip() or args.actor != args.actor.strip():
        raise ValueError("An exact audit actor is required")
    if not args.receipt.is_absolute() or args.receipt.resolve() != args.receipt or not args.receipt.is_relative_to(ROOT) or not args.receipt.parent.is_dir():
        raise ValueError("Require an exact new receipt in the existing protected operator root")
    filename, database = (("rehearsal-operator.yaml", "dewey_tapdb10_rehearsal_20260911")
                          if args.lane == "rehearsal" else ("replacement-operator.yaml", "dewey_prod_tapdb10"))
    cfg = cfg_at(filename, database)
    control = cfg_at("control-operator.yaml", "postgres")
    source = frozen_source(control)
    candidate = json.loads(subprocess.check_output(["docker", "inspect", args.candidate_container], text=True))[0]
    if candidate["State"]["Running"]:
        raise RuntimeError("Stop the exact candidate container before template plan/apply")
    core, templates = definitions()
    paths = [ROOT / filename, ROOT / "control-operator.yaml", Path(__file__),
             Path(__file__).parent / "dewey_rehearsal_copy.py", Path(cfg["domain_registry_path"]),
             Path(cfg["prefix_ownership_registry_path"]), *{Path(row["_source_file"]) for row in templates}]
    target = {"engine_type": cfg["engine_type"], "host": cfg["host"], "port": cfg["port"],
              "database": database, "schema_name": cfg["schema_name"], "config_identity": str(ROOT / filename),
              "domain_code": "M", "owner_repo_name": "dewey"}
    result_path = args.receipt.with_name(args.receipt.stem + ".result.json")
    intent_path = args.receipt.with_name(args.receipt.stem + ".apply-started.json")
    if any(path.exists() or path.is_symlink() for path in (result_path, intent_path)):
        raise FileExistsError("Prior apply evidence exists; preserve it and inspect actual state")
    if args.operation == "plan" and (args.receipt.exists() or args.receipt.is_symlink()):
        raise FileExistsError("Plan already exists")
    if args.operation == "apply" and (not args.reviewed_plan_sha256 or digest(args.receipt) != args.reviewed_plan_sha256 or not str(args.review_reference or "").strip()):
        raise ValueError("Apply requires the unchanged independently reviewed plan")
    with operator_connection(cfg, isolation_level="REPEATABLE READ", read_only=args.operation == "plan") as connection:
        physical = physical_target(connection, target)
        if physical["database_oid"] != args.target_oid or args.target_oid in {5, 16749}:
            raise ValueError("Wrong actual copy OID")
        with Session(bind=connection, expire_on_commit=False) as session:
            apply_transaction_context(session, TapdbTransactionContext(config_identity=str(ROOT / filename),
                schema_name=cfg["schema_name"], domain_code="M", owner_repo_name="dewey", tenant_id=cfg["tenant_id"] or None,
                actor=args.actor, allow_global_rows=cfg["allow_global_claims"]), assert_runtime_role=False)
            assert_operator_role(session, schema_name=cfg["schema_name"], operator_user="dayhoff")
            if connection.execute(text("SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")).scalar_one() != 0:
                raise RuntimeError("Another target session exists; preserve outage and inspect")
            before = template_state(session, templates)
            plan = {"schema_version": "dewey-xrf-template-setup/v1", "lane": args.lane, "actor": args.actor,
                    "target": target, "physical_target": physical, "source_freeze": source,
                    "candidate": {"name": args.candidate_container, "id": candidate["Id"], "image": candidate["Image"]},
                    "inputs": {str(path): digest(path) for path in paths}, "templates_before": before,
                    "canonical_definition_hashes": {row["subtype"]: content_hash({key: row.get(key) for key in FIELDS}) for row in templates},
                    "expected_inserted": 2 - len(before["existing_scoped_uids"]), "overwrite": False}
            if args.operation == "plan":
                new_json(args.receipt, plan)
                print(json.dumps({"status": "planned", "receipt": str(args.receipt), "sha256": digest(args.receipt), "expected_inserted": plan["expected_inserted"]}))
                return
            if plan != json.loads(args.receipt.read_text()):
                raise ValueError("Template setup input/physical/catalog changed after plan")
            new_json(intent_path, {"started_at": utc(), "plan_file_sha256": digest(args.receipt), "review_reference": args.review_reference})
            summary = seed_templates(session, templates, overwrite=False, core_config_dir=core,
                domain_code="M", owner_repo_name="dewey", domain_registry_path=Path(cfg["domain_registry_path"]),
                prefix_registry_path=Path(cfg["prefix_ownership_registry_path"]))
            after = template_state(session, templates)
            if (len(after["existing_scoped_uids"]) != 2 or after["row_count"] != before["row_count"] + plan["expected_inserted"]
                    or any(after["original_rows"].get(key) != value for key, value in before["original_rows"].items())
                    or summary.inserted != plan["expected_inserted"] or summary.updated != 0):
                raise ValueError("Scoped setup changed an original template or did not create exact canonical rows")
    new_json(result_path, {"status": "committed", "completed_at": utc(), "plan_file_sha256": digest(args.receipt),
             "review_reference": args.review_reference, "plan": plan, "templates_after": after,
             "inserted": summary.inserted, "updated": summary.updated, "skipped": summary.skipped})
    print(json.dumps({"status": "committed", "receipt": str(result_path)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "stopped", "error_class": type(exc).__name__}))
        raise SystemExit(1) from None
