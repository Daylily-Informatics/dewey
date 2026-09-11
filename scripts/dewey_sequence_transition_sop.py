#!/usr/bin/env python3
"""Verify one committed sequence transition, then retain future exposure floors.

Explicit one-time operator SOP for TapDB 10.1.1rc1. This never advances a
sequence, rewrites a journal, or accepts a failed legacy verification record.
Each invocation runs one separately selected operation using a reviewed capsule.
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
from pathlib import Path

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
MAPPINGS = ROOT / "receipts/source-sequence-mappings-20260911T053316Z.json"
MAPPINGS_SHA = "5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8"


def read(path):
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Expected an explicit JSON object")
    return value


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_new(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def references(paths):
    return [{"path": str(path), "file_sha256": file_hash(path)} for path in paths]


def check_references(values):
    for item in values:
        if file_hash(item["path"]) != item["file_sha256"]:
            raise ValueError("A reviewed input or completed proof changed")


def floor_records(values):
    return Counter((item["name"], item["value"], item["source"]) for item in values)


def evidence(capsule_path):
    from daylily_tapdb.identity_inventory import seal_receipt, validate_receipt

    capsule = read(capsule_path)
    if capsule["schema_version"] != "dewey-native-copy-capsule/v1":
        raise ValueError("Require the reviewed copy capsule")
    directory = Path(capsule["output_dir"])
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("Require the exact existing native output directory")
    config = Path(capsule["copy_config"])
    if (file_hash(config) != capsule["copy_config_sha256"]
            or file_hash(MAPPINGS) != MAPPINGS_SHA):
        raise ValueError("Operator config or mappings changed")
    paths = [capsule_path, config, MAPPINGS,
             directory / "sequence-plan.json", directory / "sequence-result.json",
             directory / "sequence-apply.completed.json", directory / "recovery-family.json"]
    plan, result, completed, family = (read(path) for path in paths[3:])
    if completed["returncode"] != 0 or completed["capsule_file_sha256"] != file_hash(capsule_path):
        raise ValueError("Require the successful exact-capsule sequence apply")
    check_references([*completed["inputs"], *completed["outputs"]])
    validate_receipt(plan, "tapdb-sequence-advance/v1")
    validate_receipt(result, "tapdb-sequence-apply/v1")
    validate_receipt(result["verification"], "tapdb-sequence-verification/v1")
    validate_receipt(result["inventory"], "tapdb-sequence-inventory/v1")
    released = result["writer_fence_release"]
    validate_receipt(released, "tapdb-writer-fence/v1")
    prior = result["verification"]
    own_reservations = [{"name": row["name"], "value": row["next_value"],
                         "source": "sequence_advance_intent"} for row in plan["advances"]]
    if (result["phase"] != "committed" or result["plan_sha256"] != plan["sha256"]
            or prior["ok"] is not True or prior["violations"] != []
            or prior["floors"] != plan["floors"]
            or prior["inventory_sha256"] != result["inventory"]["sha256"]
            or result["floors"] != plan["floors"] + own_reservations):
        raise ValueError("Result does not prove the exact completed transition and retained future reservations")
    if (released["phase"] != "released"
            or released["result_sha256"] != seal_receipt(
                {key: value for key, value in result.items() if key != "writer_fence_release"})["sha256"]
            or released["physical_target"] != result["inventory"]["physical_target"]
            or released["target"] != result["inventory"]["target"]
            or released["target"] != plan["target"]
            or released["physical_target"]["database_oid"] != capsule["target_oid"]
            or released["target"]["database"] != capsule["database"]
            or released["target"]["config_identity"] != str(config)
            or not (released["recovery_family"] == result["recovery_family"] == plan["recovery_family"] == family)):
        raise ValueError("Commit, release, target or full family attribution differs")
    return directory, capsule, plan, result, family, references(paths)


def main():
    from daylily_tapdb.backup.recovery import recovery_family_state

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "verify-completed", "exposure-plan"))
    parser.add_argument("--capsule", type=Path, required=True)
    parser.add_argument("--review-reference", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu operator session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Require the immutable published RC")
    if not args.capsule.is_absolute() or not args.review_reference.strip():
        raise ValueError("Require the exact absolute capsule and independent SOP review reference")
    directory, capsule, plan, result, family, inputs = evidence(args.capsule)
    floors_path = directory / "completed-transition-floors.json"
    preparation_path = directory / "completed-transition-preparation.json"
    state = recovery_family_state(family, require_terminal=True)
    if args.operation == "prepare":
        if floors_path.exists() or preparation_path.exists():
            raise FileExistsError("Preserve the existing prepared transition inputs")
        if floor_records(state["floors"]) != floor_records(result["floors"]):
            raise ValueError("Family history differs from this completed operation; review the actual changed history")
        write_new(floors_path, {"floors": plan["floors"]})
        write_new(preparation_path, {
            "schema_version": "dewey-completed-transition-input/v1", "review_reference": args.review_reference,
            "inputs": inputs, "floors_file": references([floors_path])[0],
            "applicable_floor_count": len(plan["floors"]), "future_floor_count": len(result["floors"]),
            "expected_inventory_sha256": result["inventory"]["sha256"],
            "expected_verification_sha256": result["verification"]["sha256"],
            "family_sha256": state["family_sha256"], "journal_heads": state["journal_heads"],
            "pending": state["pending"], "scope": "completed operation only; future history retained unchanged"})
        print(json.dumps({"operation": "prepare", "floors": str(floors_path), "file_sha256": file_hash(floors_path)}))
        return

    prepared = read(preparation_path)
    check_references([*prepared["inputs"], prepared["floors_file"]])
    if read(floors_path) != {"floors": plan["floors"]}:
        raise ValueError("Completed-transition input does not retain every exact prior floor")
    if args.operation == "verify-completed":
        if state["journal_heads"] != prepared["journal_heads"]:
            raise ValueError("Family changed after preparation; do not narrow a later operation")
        stem = "completed-transition-verify"
        arguments = ["db", "sequences", "verify", "--floors", str(floors_path),
                     "--sequence-mappings", str(MAPPINGS)]
        native_receipt = None
    else:
        # Explicit new prerequisite, never an OR condition accepting the old RC 1.
        proof_path = directory / "completed-transition-verify.completed.json"
        proof = read(proof_path)
        if proof["returncode"] != 0 or proof["native_verification_sha256"] != result["verification"]["sha256"]:
            raise ValueError("Require this completed transition's successful native verification")
        check_references([*proof["inputs"], *proof["outputs"]])
        stem = "exposure-after-completed-transition"
        native_receipt = directory / (stem + "-plan.json")
        external_floors = directory / "external-floors.json"
        arguments = ["db", "sequences", "advance", "--floors", str(external_floors),
                     "--sequence-mappings", str(MAPPINGS), "--recovery-family", str(directory / "recovery-family.json"),
                     "--receipt", str(native_receipt)]
        inputs.extend(references([proof_path, external_floors]))

    outputs = [directory / (stem + suffix) for suffix in (".started.json", ".stdout", ".stderr", ".rc", ".completed.json")]
    for path in outputs + ([] if native_receipt is None else [native_receipt]):
        if path.exists() or path.is_symlink():
            raise FileExistsError("A new operation output already exists; preserve it and inspect")
    command = [str(ROOT / "venv/bin/tapdb"), "--config", capsule["copy_config"], "--json", *arguments]
    inputs.extend(references([preparation_path, floors_path]))
    write_new(outputs[0], {"schema_version": "dewey-sequence-sop-command/v1", "command": command,
                           "review_reference": args.review_reference, "inputs": inputs,
                           "started_at": dt.datetime.now(dt.timezone.utc).isoformat()})
    with outputs[1].open("x") as stdout, outputs[2].open("x") as stderr:
        executed = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    with outputs[3].open("x") as handle:
        handle.write(str(executed.returncode) + "\n")
    if executed.returncode:
        raise RuntimeError("Native SOP operation failed; retain its real output and do not retry blindly")
    if native_receipt is None:
        actual = read(outputs[1])
        if actual != result["verification"]:
            raise ValueError("Fresh completed-transition verification differs from the exact committed inventory or floors")
        if recovery_family_state(family, require_terminal=True)["journal_heads"] != prepared["journal_heads"]:
            raise ValueError("Family changed during the completed-transition verification")
        verification_sha = actual["sha256"]
    else:
        if not native_receipt.is_file():
            raise ValueError("Native exposure plan receipt was not produced")
        verification_sha = None
    write_new(outputs[4], {"schema_version": "dewey-sequence-sop-completion/v1", "returncode": executed.returncode,
                           "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "native_verification_sha256": verification_sha,
                           "inputs": inputs, "outputs": references(outputs[:4] + ([] if native_receipt is None else [native_receipt]))})
    print(json.dumps({"operation": args.operation, "returncode": executed.returncode, "completion": str(outputs[4])}))


if __name__ == "__main__":
    main()
