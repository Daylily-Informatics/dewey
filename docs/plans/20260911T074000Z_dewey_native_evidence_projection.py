#!/usr/bin/env python3
"""Project retained Dewey migration evidence; no database or acceptance action.

Run after the native commands and existing inventory diff have completed:
  python THIS_FILE --native-dir ABSOLUTE_NATIVE_DIRECTORY --output NEW_ABSOLUTE_JSON

Inputs are the exact standard filenames used by the reviewed lifecycle capsule.
The verified native identity stdout is a root JSON object, not an envelope.
Reads the large receipts sequentially, copies only explicit metadata fields,
and does not recompute native seals or rerun comparisons. Full row-bearing
receipts remain private. Output contains catalog DDL, hashes and counts, never
row identity/cell values. Any missing/unknown catalog field fails explicitly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

TARGET_FIELDS = ("engine_type", "host", "port", "server_port", "database", "schema_name",
                 "config_identity", "domain_code", "owner_repo_name")
PHYSICAL_FIELDS = ("database", "database_oid", "server_address", "server_port")
CATALOG_SCALARS = ("kind", "owner", "rls_enabled", "rls_forced", "is_partition")
CATALOG_ARRAYS = {
    "columns": ("name", "data_type", "nullable", "default", "identity", "generated", "position", "collation"),
    "constraints": ("name", "kind", "definition", "validated", "columns", "referenced_schema",
                    "referenced_table", "referenced_columns"),
    "indexes": ("name", "definition"),
    "triggers": ("name", "definition", "enabled"),
    "policies": ("name", "command", "permissive", "using", "with_check"),
    "dependencies": ("kind", "dependent", "referenced"),
}
NULL_HASH = hashlib.sha256(b"null").hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def pick(document, names):
    if not isinstance(document, dict):
        raise ValueError("Expected a metadata object")
    return {name: document[name] for name in names if name in document}


def family(document):
    return {**pick(document, ("schema_version", "family_id", "receipts_dirs", "sha256")),
            "origin": {"target": pick(document["origin"]["target"], TARGET_FIELDS),
                       "physical_target": pick(document["origin"]["physical_target"], PHYSICAL_FIELDS)}}


def verification(document):
    violations = document["violations"]
    result = pick(document, ("schema_version", "sha256", "ok", "before_sha256", "after_sha256",
                             "inventory_sha256"))
    result.update(violations_count=len(violations), violations_sha256=digest(violations))
    # A failure message can embed row identifiers; retain only its digest/count.
    if not violations:
        result["violations"] = []
    return result


def completion(document):
    return {**pick(document, ("schema_version", "completed_at", "returncode", "capsule_file_sha256")),
            "inputs": [pick(item, ("path", "file_sha256")) for item in document["inputs"]],
            "outputs": [pick(item, ("path", "file_sha256")) for item in document["outputs"]]}


def catalog(table):
    result = {name: table[name] for name in CATALOG_SCALARS}
    for name, fields in CATALOG_ARRAYS.items():
        result[name] = [pick(item, fields) for item in table[name]]
    result.update(primary_key=table["primary_key"], immutable_columns=table["immutable_columns"])
    return result


class Inputs:
    def __init__(self, directory):
        self.directory = directory
        self.references = {}

    def read(self, name):
        path = self.directory / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing exact regular input: {name}")
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            checksum = hashlib.file_digest(handle, "sha256").hexdigest()
            handle.seek(0)
            document = json.load(handle)
            after = os.fstat(handle.fileno())
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f"Input changed during projection: {name}")
        if not isinstance(document, dict):
            raise ValueError(f"Input must be a root JSON object: {name}")
        self.references[name] = {"path": str(path), "file_sha256": checksum, "file_bytes": before.st_size}
        return document


def migration_summary(document):
    result = document["migration_result"]
    post = result["postflight"]
    recovery = document["recovery_completion"]
    allocator = recovery["allocator_result"]
    released = document["writer_fence_release"]
    return {
        "principal_binding_required": document["principal_binding_required"],
        "migration_result": {
            **pick(result, ("receipt_version", "status", "commit_status", "result_sha256",
                            "preflight_evidence_sha256", "postflight_evidence_sha256", "applied_migrations")),
            "target": pick(result["target"], TARGET_FIELDS),
            "postflight": {**pick(post, ("receipt_version", "evidence_sha256")),
                           "identity_inventory_sha256": post["identity_inventory"]["sha256"],
                           "sequence_inventory_sha256": post["sequence_inventory"]["sha256"]},
        },
        "recovery_completion": {
            **pick(recovery, ("status", "receipt_id", "receipt_sha256")),
            "allocator_result": {
                **pick(allocator, ("schema_version", "phase", "sha256", "plan_sha256", "intent_receipt_id")),
                "inventory_sha256": allocator["inventory"]["sha256"],
                "verification": verification(allocator["verification"]),
            },
        },
        "writer_fence_release": {
            **pick(released, ("schema_version", "phase", "sha256", "fence_sha256", "result_sha256", "intent_receipt_id")),
            "target": pick(released["target"], TARGET_FIELDS),
            "physical_target": pick(released["physical_target"], PHYSICAL_FIELDS),
            "recovery_family": family(released["recovery_family"]),
        },
    }


def inventory_summary(document, original_instance_keys=None):
    identity = document["identity_inventory"]
    sequence = document["sequence_inventory"]
    tables = {}
    for name, table in identity["tables"].items():
        metadata = catalog(table)
        tables[name] = {"row_count": table["row_count"], "content_sha256": table["content_sha256"],
                        "catalog": metadata, "catalog_sha256": digest(metadata)}
    summary = {
        **pick(document, ("schema_version", "source_version", "source_version_evidence", "sha256")),
        "identity_inventory_sha256": identity["sha256"], "sequence_inventory_sha256": sequence["sha256"],
        "target": pick(identity["target"], TARGET_FIELDS),
        "physical_target": pick(identity["physical_target"], PHYSICAL_FIELDS),
        "recovery_family": family(document["recovery_family"]),
        "limits": pick(identity["limits"], ("max_rows", "max_row_bytes", "max_receipt_bytes")),
        "usage": pick(identity["usage"], ("rows", "evidence_bytes", "largest_source_row_bytes")),
        "table_count": len(tables), "row_count": sum(item["row_count"] for item in tables.values()),
        "generator_count": len(sequence["sequences"]), "tables": tables,
    }
    rows = identity["tables"]["generic_instance"]["rows"]
    if original_instance_keys is None:
        return summary, set(rows)
    nulls = nonnulls = absent = matched = 0
    for key in original_instance_keys:
        if key not in rows:
            continue  # Missing keys are reported by the existing authoritative diff.
        row = rows[key]
        matched += row["count"]
        if "identity_key" not in row["columns"]:
            absent += row["count"]
        elif row["columns"]["identity_key"] == NULL_HASH:
            nulls += row["count"]
        else:
            nonnulls += row["count"]
    summary["original_instance_identity_key_counts"] = {
        "original_distinct_key_count": len(original_instance_keys), "after_rows_at_original_keys": matched,
        "null_rows": nulls, "nonnull_rows": nonnulls, "column_absent_rows": absent,
        "native_null_value_sha256": NULL_HASH,
    }
    return summary


def diff_summary(report, before, after):
    result = {**pick(report, ("schema_version", "status", "native_verification_required", "schema_name_changed",
                             "before_table_count", "after_table_count", "max_input_bytes")),
              "before": pick(report["before"], ("path", "file_sha256", "receipt_sha256", "identity_inventory_sha256")),
              "after": pick(report["after"], ("path", "file_sha256", "receipt_sha256", "identity_inventory_sha256")),
              "tables": {}}
    for name in ("target_changes", "physical_target_changes", "inventory_metadata_changes"):
        result[name] = [pick(item, ("field", "before_present", "after_present", "before_sha256", "after_sha256"))
                        for item in report[name]]
    for name, change in report["tables"].items():
        entry = pick(change, ("change", "row_count", "content_sha256", "before_row_count", "after_row_count"))
        for key in ("row_keys", "added_row_keys", "missing_source_row_keys"):
            if key in change:
                entry[key] = change[key]  # These are native SHA-256 keys, not object identifiers.
                if any(not isinstance(value, str) or len(value) != 64
                       or any(c not in "0123456789abcdef" for c in value) for value in change[key]):
                    raise ValueError("Diff contains a non-hash row key")
                entry[key + "_count"] = len(change[key])
                entry[key + "_aggregate_sha256"] = digest(change[key])
        old_catalog = before["tables"][name]["catalog"] if name in before["tables"] else {}
        new_catalog = after["tables"][name]["catalog"] if name in after["tables"] else {}
        entry["catalog_changes"] = []
        for item in change.get("catalog_changes", []):
            field = item["field"]
            if field not in {*CATALOG_SCALARS, *CATALOG_ARRAYS, "primary_key", "immutable_columns"}:
                raise ValueError("Unrecognized catalog field; inspect the private diff")
            entry["catalog_changes"].append({
                **pick(item, ("field", "before_present", "after_present", "before_sha256", "after_sha256")),
                "before": old_catalog.get(field), "after": new_catalog.get(field)})
        changed = change.get("changed_rows", {})
        original_columns = {column["name"] for column in old_catalog.get("columns", [])}
        counts = Counter()
        multiplicity = original_changed_rows = 0
        for row in changed.values():
            original_changes = [item for item in row["columns"] if item["column"] in original_columns]
            counts.update(item["column"] for item in original_changes)
            original_changed_rows += bool(original_changes)
            multiplicity += row["before_count"] != row["after_count"]
        entry.update(changed_row_key_count=len(changed), changed_rows_aggregate_sha256=digest(changed),
                     original_column_changed_key_count=original_changed_rows,
                     original_column_change_counts=dict(sorted(counts.items())),
                     multiplicity_changed_key_count=multiplicity)
        result["tables"][name] = entry
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.native_dir.is_absolute() or not args.native_dir.is_dir():
        raise ValueError("--native-dir must be an explicit existing absolute directory")
    if not args.output.is_absolute() or not args.output.parent.is_dir():
        raise ValueError("--output must be an absolute file in an existing directory")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Preserve the existing output; do not overwrite it")
    inputs = Inputs(args.native_dir)
    migration = migration_summary(inputs.read("migration-result.json"))
    old, original_keys = inventory_summary(inputs.read("copy-historical.json"))
    new = inventory_summary(inputs.read("copy-migrated.json"), original_keys)
    report = diff_summary(inputs.read("migration-diff-review.json"), old, new)
    if (report["before"]["file_sha256"] != inputs.references["copy-historical.json"]["file_sha256"]
            or report["after"]["file_sha256"] != inputs.references["copy-migrated.json"]["file_sha256"]):
        raise ValueError("Existing diff is attributed to different input files")
    output = {
        "schema_version": "dewey-native-evidence-projection/v1", "status": "projection_requires_independent_review",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "native_seals_recomputed": False, "database_calls": 0,
        "migration": migration, "historical": old, "migrated": new, "existing_diff": report,
        "migration_command": completion(inputs.read("migration-apply.completed.json")),
        "capture_command": completion(inputs.read("capture-migrated.completed.json")),
        "verification_command": completion(inputs.read("verify-migrated.completed.json")),
        "native_verification": verification(inputs.read("verify-migrated.stdout")),
        "source_files": inputs.references,
    }
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), "status": output["status"]}))


if __name__ == "__main__":
    main()
