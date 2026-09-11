"""Summarize retained native discovery receipts without exporting application rows.

This reads files only. The summary is an index to protected native evidence,
not a preservation comparison or migration acceptance receipt.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")


def main() -> None:
    os.umask(0o077)
    receipts = ROOT / "receipts"
    destination = receipts / "source-summary-10.1.1rc1.json"
    if destination.exists() or destination.is_symlink():
        raise RuntimeError("Summary already exists; do not overwrite retained evidence")
    source_path = receipts / "source-inventory-10.1.1rc1.json"
    with source_path.open("rb") as handle:
        file_sha = hashlib.file_digest(handle, "sha256").hexdigest()
    with source_path.open() as handle:
        source = json.load(handle)
    with (receipts / "source-census-10.1.1rc1.json").open() as handle:
        census = json.load(handle)
    identity = source["identity_inventory"]
    table_summary = {}
    true_hash = hashlib.sha256(b"true").hexdigest()
    for name, table in identity["tables"].items():
        rows = table["rows"].values()
        table_summary[name] = {
            "row_count": table["row_count"],
            "content_sha256": table["content_sha256"],
            "columns": [column["name"] for column in table["columns"]],
            "primary_key": table["primary_key"],
            "owner": table["owner"],
            "rls_enabled": table["rls_enabled"],
            "rls_forced": table["rls_forced"],
            "deleted_rows": sum(
                row["count"] for row in rows
                if row["columns"].get("is_deleted") == true_hash
            ),
            "prefix_counts": dict(Counter({
                prefix: sum(
                    row["count"] for row in rows
                    if row["identity"].get("euid_prefix") == prefix
                )
                for prefix in {
                    row["identity"]["euid_prefix"] for row in rows
                    if "euid_prefix" in row["identity"]
                }
            })),
            "domains": sorted({
                row["identity"]["domain_code"] for row in rows
                if row["identity"].get("domain_code") is not None
            }),
        }
    template_fields = (
        "category", "type", "subtype", "version", "domain_code",
        "euid_prefix", "instance_prefix",
    )
    result = {
        "purpose": "Sanitized discovery index, not fenced evidence or migration acceptance",
        "source_path": str(source_path),
        "source_file_bytes": source_path.stat().st_size,
        "source_file_sha256": file_sha,
        "source_contract_sha256": source["sha256"],
        "source_version": source["source_version"],
        "physical_target": identity["physical_target"],
        "target": identity["target"],
        "identity_sha256": identity["sha256"],
        "limits": identity["limits"],
        "usage": identity["usage"],
        "tables": table_summary,
        "template_bindings": [
            {key: row["identity"][key] for key in template_fields if key in row["identity"]}
            for row in identity["tables"]["generic_template"]["rows"].values()
        ],
        "sequence_inventory": source["sequence_inventory"],
        "census": {
            key: census[key] for key in (
                "sha256", "authenticated_operator", "physical_target",
                "database_checks", "scope_bindings", "effective_privileges", "activity",
            )
        },
        "census_counts": {
            key: len(census[key]) for key in (
                "roles", "objects", "memberships", "iam_memberships", "default_acls",
            )
        },
        "executions": {
            operation: json.loads(
                (receipts / f"source-{operation}-10.1.1rc1-execution.json").read_text()
            )
            for operation in ("census", "inventory")
        },
    }
    with destination.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(str(destination))


if __name__ == "__main__":
    main()
