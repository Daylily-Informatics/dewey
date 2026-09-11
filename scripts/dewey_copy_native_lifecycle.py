#!/usr/bin/env python3
"""One explicit native TapDB 10.1.1rc1 operation per operator invocation.

The owning operator supplies a reviewed capsule JSON with actual copy identity.
This script never copies a database, reconnects to the frozen source, creates a
backup, binds a runtime principal, or automatically continues after a plan.
Operator execution records are deliberately distinct from native receipts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import subprocess
import uuid
from pathlib import Path

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
TAPDB = ROOT / "venv/bin/tapdb"
MAPPINGS = ROOT / "receipts/source-sequence-mappings-20260911T053316Z.json"
MAPPING_SHA = "5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8"
MANIFEST_SHA = "af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8"
HOST = "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com"
SCHEMA = "tapdb_dewey_lsmcok1_local"
STAGES = (
    "capture-copy", "verify-copy", "create-family", "migration-plan",
    "migration-apply", "capture-migrated", "verify-migrated", "prepare-floors",
    "sequence-plan", "sequence-apply", "sequence-verify", "exposure-plan",
)
INPUT_KEYS = {
    "schema_version", "database", "target_oid", "copy_config", "copy_config_sha256",
    "copy_receipt", "copy_receipt_sha256", "source_contract", "source_next_plan",
    "source_next_plan_sha256", "migration_manifest", "family_id", "journal_dir",
    "output_dir", "extra_next_plans", "control_config_sha256", "provider_contract_sha256",
}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def read(path):
    def nonfinite(_):
        raise ValueError("Non-finite JSON number")

    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=object_pairs, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("Expected an explicit JSON object")
    return value


def write_new(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def existing_path(value, *, directory=False):
    path = Path(value)
    if not path.is_absolute() or not path.is_relative_to(ROOT) or path.resolve() != path:
        raise ValueError("Use a canonical absolute path within the operator capsule")
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("An explicit input path is missing")
    return path


def expect_hash(path, expected):
    if file_hash(path) != expected:
        raise ValueError("An input file differs from its reviewed hash")


def sequence_content(inventory):
    """Permit only explicit physical/config relocation of an untouched copy."""
    return {key: value for key, value in inventory.items()
            if key not in {"sha256", "target", "physical_target"}}


def contract_projection(path):
    # Return only small projections before starting a child CLI process. The
    # complete 225 MB historical receipt must not stay resident alongside it.
    from daylily_tapdb.identity_inventory import validate_receipt

    document = read(path)
    validate_receipt(document, "tapdb-source-contract/v1")
    identity = document["identity_inventory"]
    sequences = document["sequence_inventory"]
    validate_receipt(identity, "tapdb-identity-inventory/v1")
    validate_receipt(sequences, "tapdb-sequence-inventory/v1")
    if identity["target"] != sequences["target"] or identity["physical_target"] != sequences["physical_target"]:
        raise ValueError("Source contract has inconsistent physical/config targets")
    return {"sha256": document["sha256"], "source_version": document["source_version"],
            "target": identity["target"], "physical_target": identity["physical_target"],
            "identity_sha256": identity["sha256"], "sequences": sequences,
            "family": document.get("recovery_family")}


def project_plan_floors(plan, provenance):
    """Retain every recorded boundary unchanged; no allocator arithmetic here."""
    from daylily_tapdb.backup.recovery import inventory_floors, recovery_family_state
    from daylily_tapdb.identity_inventory import validate_receipt
    from daylily_tapdb.sequences import build_sequence_advance_plan

    validate_receipt(plan, "tapdb-sequence-advance/v1")
    if "recovery_family" in plan:
        recovery_family_state(plan["recovery_family"], require_terminal=True)
    # This also checks the complete current family journals when one is present.
    expected = build_sequence_advance_plan(
        plan["inventory"],
        floors=plan["input_floors"] if "recovery_family" in plan else plan["floors"],
        recovery_family=plan.get("recovery_family"),
    )
    if expected != plan:
        raise ValueError("Native exposure plan no longer matches its complete retained history")
    result = inventory_floors(plan["inventory"], source=provenance)
    result.extend({**floor, "source": provenance + ":retained:" + floor["source"]}
                  for floor in plan["floors"])
    result.extend({"name": item["name"], "value": item["next_value"],
                   "source": provenance + ":native_planned_next"}
                  for item in plan["advances"])
    return result


class Capsule:
    def __init__(self, path):
        from daylily_tapdb.cli.db_config import get_db_config

        self.path = existing_path(path)
        self.hash = file_hash(self.path)
        self.data = data = read(self.path)
        if set(data) != INPUT_KEYS or data["schema_version"] != "dewey-native-copy-capsule/v1":
            raise ValueError("Unexpected capsule input contract")
        if data["database"] not in {"dewey_tapdb10_rehearsal_20260911", "dewey_prod_tapdb10"}:
            raise ValueError("Unapproved target database")
        if type(data["target_oid"]) is not int or data["target_oid"] <= 0 or data["target_oid"] in {5, 16749}:
            raise ValueError("Require the actual distinct copied database OID")
        if str(uuid.UUID(data["family_id"])) != data["family_id"]:
            raise ValueError("Require an explicit canonical family UUID")
        self.output = existing_path(data["output_dir"], directory=True)
        self.journal = existing_path(data["journal_dir"], directory=True)
        if self.output == self.journal:
            raise ValueError("Native journal and ordinary evidence need separate explicit directories")
        for key in ("copy_config", "copy_receipt", "source_contract", "source_next_plan", "migration_manifest"):
            existing_path(data[key])
        for key in ("copy_config", "copy_receipt", "source_next_plan"):
            expect_hash(data[key], data[key + "_sha256"])
        expect_hash(MAPPINGS, MAPPING_SHA)
        expect_hash(data["migration_manifest"], MANIFEST_SHA)
        self.control = ROOT / "control-operator.yaml"
        self.provider = ROOT / "receipts/aurora-provider-contract-20260911.json"
        expect_hash(self.control, data["control_config_sha256"])
        expect_hash(self.provider, data["provider_contract_sha256"])
        if not isinstance(data["extra_next_plans"], list):
            raise ValueError("Declare every additional exposure plan explicitly, including an empty list")
        for item in data["extra_next_plans"]:
            if not isinstance(item, dict) or set(item) != {"path", "file_sha256"}:
                raise ValueError("Each extra exposure plan requires path and file_sha256")
            expect_hash(existing_path(item["path"]), item["file_sha256"])
        cfg = get_db_config(config_path=Path(data["copy_config"]), client_id="dewey", database_name="dewey-day")
        expected = {"database": data["database"], "operator_user": "dayhoff", "host": HOST,
                    "engine_type": "aurora", "schema_name": SCHEMA, "domain_code": "M",
                    "owner_repo_name": "dewey", "cluster_identifier": "dayhoff-lsmcok1-tapdb"}
        if any(cfg.get(key) != value for key, value in expected.items()):
            raise ValueError("Operator configuration differs from the approved copy")
        self.copy = read(data["copy_receipt"])
        if self.copy["status"] != "copy_created_source_remains_fenced":
            raise ValueError("Copy must retain the original source outage")
        copied = self.copy["copied_database"]
        if copied["datname"] != data["database"] or copied["oid"] != data["target_oid"] or copied["owner"] != "dayhoff":
            raise ValueError("Capsule does not identify the operator-created copy")

    def out(self, name):
        return self.output / name

    def require(self, stage):
        done = read(self.out(stage + ".completed.json"))
        if done["returncode"] != 0 or done["capsule_file_sha256"] != self.hash:
            raise ValueError("Required stage has no successful matching execution record")
        for item in [*done["inputs"], *done["outputs"]]:
            expect_hash(item["path"], item["file_sha256"])

    def check_copy_projection(self, projection):
        target, physical = projection["target"], projection["physical_target"]
        if (target["database"] != self.data["database"] or target["host"] != HOST
                or target["config_identity"] != self.data["copy_config"]
                or target["schema_name"] != SCHEMA or target["domain_code"] != "M"
                or physical["database"] != self.data["database"]
                or physical["database_oid"] != self.data["target_oid"]):
            raise ValueError("Native inventory differs from the actual copied target")

    def native(self, stage, arguments, *, receipt=None, extra_outputs=(), review_reference=None):
        paths = [self.out(stage + suffix) for suffix in (".started.json", ".stdout", ".stderr", ".completed.json", ".rc")]
        outputs = ([] if receipt is None else [receipt]) + list(extra_outputs)
        for path in [*paths, *outputs]:
            if path.exists() or path.is_symlink():
                raise ValueError("An operation output exists; inspect it instead of replaying")
        # Schema migration emits its authoritative receipt file and explicitly
        # rejects global JSON mode. Identity and sequence commands support it.
        mode = [] if list(arguments[:3]) == ["db", "schema", "migrate"] else ["--json"]
        command = [str(TAPDB), "--config", self.data["copy_config"], *mode, *map(str, arguments)]
        inputs = [{"path": arg, "file_sha256": file_hash(arg)} for arg in command[1:]
                  if arg.startswith("/") and Path(arg).is_file()]
        write_new(paths[0], {"schema_version": "dewey-native-command/v1", "started_at": utc(),
                            "capsule_file_sha256": self.hash, "command": command,
                            "review_reference": review_reference})
        with paths[1].open("x") as stdout, paths[2].open("x") as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
        with paths[4].open("x") as rc_file:
            rc_file.write(str(result.returncode) + "\n")
        if result.returncode == 0 and any(not path.is_file() for path in outputs):
            raise ValueError("Native command returned without its required receipt")
        outputs.extend([paths[0], paths[1], paths[2], paths[4]])
        write_new(paths[3], {"schema_version": "dewey-native-command-completion/v1",
                            "completed_at": utc(), "capsule_file_sha256": self.hash,
                            "returncode": result.returncode, "inputs": inputs,
                            "outputs": [{"path": str(p), "file_sha256": file_hash(p)}
                                        for p in outputs if p.is_file()]})
        print(json.dumps({"stage": stage, "returncode": result.returncode,
                          "execution_record": str(paths[3])}))
        if result.returncode:
            raise RuntimeError("Native command failed; preserve all receipts/journals and inspect")


def execute(capsule, stage, reviewed_sha, review_reference):
    c, data = capsule, capsule.data
    untouched, historical = c.out("copy-untouched.json"), c.out("copy-historical.json")
    family, migrated = c.out("recovery-family.json"), c.out("copy-migrated.json")
    migration_plan, sequence_plan = c.out("migration-plan.json"), c.out("sequence-plan.json")
    floors = c.out("external-floors.json")
    mappings = ["--sequence-mappings", MAPPINGS]
    family_flags = ["--recovery-family", family]
    fence_flags = ["--receipts-dir", c.journal, "--establish-writer-fence",
                   "--control-config", c.control, "--provider-contract", c.provider]
    if stage.endswith("-apply"):
        if not reviewed_sha or not review_reference or not review_reference.strip():
            raise ValueError("Apply requires the independently reviewed plan file SHA and review reference")
        expect_hash(migration_plan if stage == "migration-apply" else sequence_plan, reviewed_sha)
    elif reviewed_sha or review_reference:
        raise ValueError("Review arguments belong only to an explicit apply invocation")

    if stage == "capture-copy":
        c.native(stage, ["db", "identity", "inventory", "--source-version", "9.0.9",
                         *mappings, "--receipt", untouched], receipt=untouched)
    elif stage == "verify-copy":
        # O may have captured this exact native input before preparing the full
        # capsule. Consume its actual receipt/terminal RC; never recapture it or
        # fabricate this helper's command-completion record.
        existing_path(untouched)
        if c.out("capture-copy.rc").read_text().strip() != "0":
            raise ValueError("Untouched native capture lacks its actual successful terminal RC")
        source = contract_projection(data["source_contract"])
        after = contract_projection(untouched)
        c.check_copy_projection(after)
        if (source["sha256"] != c.copy["source_contract_sha256"] or source["source_version"] != "9.0.9"
                or source["physical_target"]["database"] != "dewey_prod"
                or source["physical_target"]["database_oid"] != 16749
                or after["source_version"] != "9.0.9" or after["family"] is not None):
            raise ValueError("Historical copy/source evidence differs from the frozen cutoff")
        if sequence_content(source["sequences"]) != sequence_content(after["sequences"]):
            raise ValueError("Untouched copy changed generator definitions, mappings, state or boundaries")
        for key in ("server_address", "server_port"):
            if source["physical_target"][key] != after["physical_target"][key]:
                raise ValueError("Copy is not on the observed original source server")
        manifest = {"schema_version": "tapdb-identity-conversion/v1", "target": after["target"],
                    "tables": {}, "added_tables": []}
        manifest_path = c.out("copy-target-only-manifest.json")
        write_new(manifest_path, manifest)
        write_new(c.out("copy-sequence-comparison.json"), {
            "schema_version": "dewey-copy-sequence-comparison/v1", "equal_except_explicit_target": True,
            "source_sequence_sha256": source["sequences"]["sha256"],
            "copy_sequence_sha256": after["sequences"]["sha256"],
            "generator_count": len(after["sequences"]["sequences"]), "capsule_file_sha256": c.hash})
        c.native(stage, ["db", "identity", "verify", "--before", data["source_contract"],
                         "--after", untouched, "--conversion-manifest", manifest_path, *mappings])
    elif stage == "create-family":
        c.require("verify-copy")
        if family.exists() or family.is_symlink() or any(c.journal.iterdir()):
            raise ValueError("New family needs its explicit unused journal; retain any existing history")
        c.native(stage, ["db", "identity", "inventory", "--source-version", "9.0.9", *mappings,
                         "--new-recovery-family-id", data["family_id"], "--family-receipts-dir", c.journal,
                         "--family-receipt", family, "--receipt", historical], receipt=historical,
                 extra_outputs=(family,))
    elif stage == "migration-plan":
        c.require("create-family")
        before, after = contract_projection(untouched), contract_projection(historical)
        c.check_copy_projection(after)
        if before["identity_sha256"] != after["identity_sha256"] or before["sequences"] != after["sequences"]:
            raise ValueError("Copy changed before native family capture; review the actual state")
        if after["family"] != read(family):
            raise ValueError("Historical source does not contain the exact native family")
        c.native(stage, ["db", "schema", "migrate", "--dry-run", "--receipt", migration_plan,
                         "--source-contract", historical, *mappings, "--receipts-dir", c.journal,
                         *family_flags], receipt=migration_plan)
    elif stage == "migration-apply":
        c.require("migration-plan")
        result = c.out("migration-result.json")
        c.native(stage, ["db", "schema", "migrate", "--apply", "--preflight-receipt", migration_plan,
                         "--receipt", result, "--source-contract", historical,
                         *mappings, *family_flags, *fence_flags], receipt=result, review_reference=review_reference)
    elif stage == "capture-migrated":
        c.require("migration-apply")
        result = read(c.out("migration-result.json"))
        if (result.get("principal_binding_required") is not True
                or not all(result.get(key) for key in ("migration_result", "recovery_completion", "writer_fence_release"))):
            raise ValueError("Migration did not return a complete native success/release result")
        c.native(stage, ["db", "identity", "inventory", "--source-version", "10.1.1rc1",
                         *mappings, *family_flags, "--receipt", migrated], receipt=migrated)
    elif stage == "verify-migrated":
        c.require("capture-migrated")
        after = contract_projection(migrated)
        c.check_copy_projection(after)
        c.native(stage, ["db", "identity", "verify", "--before", historical, "--after", migrated,
                         "--conversion-manifest", data["migration_manifest"], *mappings])
    elif stage == "prepare-floors":
        c.require("verify-migrated")
        source = contract_projection(data["source_contract"])
        native_next = read(data["source_next_plan"])
        if (source["sha256"] != c.copy["source_contract_sha256"]
                or native_next["inventory"]["sha256"] != source["sequences"]["sha256"]):
            raise ValueError("Native next observation differs from the continuously frozen source")
        inputs = [{"path": data["source_next_plan"], "file_sha256": data["source_next_plan_sha256"]},
                  *data["extra_next_plans"]]
        records = []
        for item in inputs:
            plan = read(item["path"])
            provenance = f"{item['path']}:file_sha256={item['file_sha256']}:native_sha256={plan['sha256']}"
            records.extend(project_plan_floors(plan, provenance))
        write_new(floors, {"floors": records})
        write_new(c.out("prepare-floors.completed.json"), {
            "schema_version": "dewey-floor-projection/v1", "status": "prepared_for_independent_review",
            "returncode": 0, "capsule_file_sha256": c.hash, "inputs": inputs,
            "outputs": [{"path": str(floors), "file_sha256": file_hash(floors)}]})
        print(json.dumps({"stage": stage, "floors_file": str(floors),
                          "file_sha256": file_hash(floors), "retained_record_count": len(records)}))
    elif stage in {"sequence-plan", "exposure-plan"}:
        c.require("prepare-floors" if stage == "sequence-plan" else "sequence-verify")
        existing_path(floors)
        result = sequence_plan if stage == "sequence-plan" else c.out("exposure-plan.json")
        c.native(stage, ["db", "sequences", "advance", "--floors", floors,
                         "--receipt", result, *mappings, *family_flags], receipt=result)
    elif stage == "sequence-apply":
        c.require("sequence-plan")
        result = c.out("sequence-result.json")
        c.native(stage, ["db", "sequences", "advance", "--apply", "--floors", floors,
                         "--preflight-receipt", sequence_plan, "--receipt", result,
                         *mappings, *family_flags, *fence_flags], receipt=result, review_reference=review_reference)
    elif stage == "sequence-verify":
        c.require("sequence-apply")
        c.native(stage, ["db", "sequences", "verify", "--floors", floors, *mappings, *family_flags])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--capsule", type=Path, required=True)
    parser.add_argument("--reviewed-plan-sha256")
    parser.add_argument("--review-reference")
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu operator session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Require the immutable released RC")
    execute(Capsule(args.capsule), args.stage, args.reviewed_plan_sha256, args.review_reference)


if __name__ == "__main__":
    main()
