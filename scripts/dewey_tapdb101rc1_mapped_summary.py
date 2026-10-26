"""Index the existing mapped receipt without reading the live database.

Keep application rows private. This is an operator review index, not a native
preservation receipt, allocator advancement, or production acceptance.
"""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path


ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911/receipts")


def main():
    os.umask(0o077)
    source = ROOT / "source-mapped-inventory-10.1.1rc1.json"
    output = ROOT / "source-mapped-summary-10.1.1rc1.json"
    if output.exists() or output.is_symlink():
        raise RuntimeError("Retained summary exists; do not overwrite it")
    with source.open("rb") as handle:
        file_sha = hashlib.file_digest(handle, "sha256").hexdigest()
    data = json.loads(source.read_text())
    inventory = data["identity_inventory"]
    tables = inventory["tables"]
    sequence = data["sequence_inventory"]
    unresolved = [
        row["name"] for row in sequence["sequences"]
        if row["mapping"]["kind"] == "unmapped"
    ]
    if unresolved or sequence["missing_generators"]:
        raise RuntimeError("Native inventory still contains unresolved generators")
    null_hash = hashlib.sha256(b"null").hexdigest()
    empty_hash = hashlib.sha256(b'""').hexdigest()
    fields = (("audit_log", "changed_by"), ("generic_template", "validator_ref"))
    null_empty = {}
    for table_name, field in fields:
        rows = tables[table_name]["rows"].values()
        null_empty[f"{table_name}.{field}"] = {
            "null": sum(row["count"] for row in rows if row["columns"].get(field) == null_hash),
            "empty_string": sum(row["count"] for row in rows if row["columns"].get(field) == empty_hash),
            "column_exists": field in {column["name"] for column in tables[table_name]["columns"]},
        }
    scope = {}
    for table_name, table in tables.items():
        scope[table_name] = {}
        for field in ("tenant_id", "issuer_app_code", "machine_uuid"):
            values = Counter()
            for row in table["rows"].values():
                if field in row["identity"]:
                    values[json.dumps(row["identity"][field], sort_keys=True)] += row["count"]
            scope[table_name][field] = {
                "null_rows": values.get("null", 0),
                "non_null_rows": sum(n for value, n in values.items() if value != "null"),
                "distinct_non_null_values": sum(value != "null" for value in values),
                "field_observed": bool(values),
            }
    result = {
        "purpose": "Sanitized mapped native discovery review index; not fenced evidence",
        "source_path": str(source),
        "source_file_sha256": file_sha,
        "source_file_bytes": source.stat().st_size,
        "source_contract_sha256": data["sha256"],
        "source_version": data["source_version"],
        "identity_sha256": inventory["sha256"],
        "physical_target": inventory["physical_target"],
        "target": inventory["target"],
        "limits": inventory["limits"],
        "usage": inventory["usage"],
        "sequence_inventory": sequence,
        "tables": {
            name: {"row_count": table["row_count"], "content_sha256": table["content_sha256"],
                   "columns": [column["name"] for column in table["columns"]]}
            for name, table in tables.items()
        },
        "migration_identities": [row["identity"] for row in tables["_tapdb_migrations"]["rows"].values()],
        "null_empty_review": null_empty,
        "scope_counts": scope,
        "execution": json.loads((ROOT / "source-mapped-inventory-10.1.1rc1-execution.json").read_text()),
    }
    with output.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(output)


if __name__ == "__main__":
    main()
