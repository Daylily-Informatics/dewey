#!/usr/bin/env python3
"""Prepare a hash-only review of existing native TapDB inventory receipts.

This offline helper has no database or service access. It does not generate a
conversion manifest, approve differences, or replace ``tapdb db identity verify``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

IDENTITY_VERSION = "tapdb-identity-inventory/v1"
SOURCE_VERSION = "tapdb-source-contract/v1"
MAX_INPUT_BYTES = 192 * 1024 * 1024


class EvidenceError(ValueError):
    """An offline input is missing, corrupt, or outside the supported format."""


def digest(value: Any) -> str:
    result = hashlib.sha256()
    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    for chunk in encoder.iterencode(value):
        result.update(chunk.encode("utf-8"))
    return result.hexdigest()


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("Duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(_: str) -> None:
    raise EvidenceError("Non-finite JSON number")


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


def _check_seal(payload: Any, version: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != version:
        raise EvidenceError(f"Expected native format {version}")
    if payload.get("sha256") != digest({k: v for k, v in payload.items() if k != "sha256"}):
        raise EvidenceError("Native receipt checksum mismatch")
    return payload


def read_inventory(
    path: Path, *, max_input_bytes: int = MAX_INPUT_BYTES
) -> tuple[dict[str, Any], dict[str, str]]:
    if type(max_input_bytes) is not int or not 1 <= max_input_bytes <= 2**63 - 1:
        raise EvidenceError("max_input_bytes must be an explicit positive 64-bit integer")
    if not path.is_absolute() or not path.is_file():
        raise EvidenceError("Inputs must be existing absolute files")
    with path.open("rb") as source:
        if os.fstat(source.fileno()).st_size > max_input_bytes:
            raise EvidenceError("Input exceeds the reviewed max_input_bytes limit")
        file_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
        source.seek(0)
        payload = json.load(source, object_pairs_hook=_object, parse_constant=_nonfinite)
    if not isinstance(payload, dict):
        raise EvidenceError("Expected a native JSON receipt object")
    if payload.get("schema_version") == SOURCE_VERSION:
        _check_seal(payload, SOURCE_VERSION)
        _check_seal(payload.get("sequence_inventory"), "tapdb-sequence-inventory/v1")
        if "recovery_family" in payload:
            _check_seal(payload["recovery_family"], "tapdb-recovery-family/v1")
        inventory = _check_seal(payload.get("identity_inventory"), IDENTITY_VERSION)
    else:
        inventory = _check_seal(payload, IDENTITY_VERSION)
    if not all(
        isinstance(inventory.get(key), dict) for key in ("target", "physical_target", "tables")
    ):
        raise EvidenceError("Incomplete native inventory")
    if (
        not inventory["target"]
        or not inventory["physical_target"]
        or not inventory.get("schema_name")
    ):
        raise EvidenceError("Missing configured or physical inventory identity")
    for table in inventory["tables"].values():
        if not isinstance(table, dict) or not isinstance(table.get("rows"), dict):
            raise EvidenceError("Incomplete table inventory")
        if not isinstance(table.get("columns"), list) or not isinstance(
            table.get("immutable_columns"), list
        ):
            raise EvidenceError("Incomplete column inventory")
        rows = table["rows"]
        for key, row in rows.items():
            if (
                not _is_digest(key)
                or not isinstance(row, dict)
                or not _is_digest(row.get("sha256"))
                or type(row.get("count")) is not int
                or row["count"] < 1
                or not isinstance(row.get("columns"), dict)
                or not all(_is_digest(value) for value in row["columns"].values())
            ):
                raise EvidenceError("Incomplete row inventory")
        if table.get("row_count") != sum(row["count"] for row in rows.values()):
            raise EvidenceError("Table row count disagrees with its recorded rows")
        if table.get("content_sha256") != digest(rows):
            raise EvidenceError("Table content checksum mismatch")
    return inventory, {
        "path": str(path),
        "file_sha256": file_sha256,
        "receipt_sha256": payload["sha256"],
        "identity_inventory_sha256": inventory["sha256"],
    }


def _changes(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            "before_present": field in before,
            "after_present": field in after,
            "before_sha256": digest(before[field]) if field in before else None,
            "after_sha256": digest(after[field]) if field in after else None,
        }
        for field in sorted(before.keys() | after.keys())
        if field not in before or field not in after or before[field] != after[field]
    ]


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Describe all differences without translating them into permissions."""
    old_tables, new_tables = before["tables"], after["tables"]
    tables = {}
    for name in sorted(old_tables.keys() | new_tables.keys()):
        old, new = old_tables.get(name), new_tables.get(name)
        if old is None or new is None:
            entry = new if old is None else old
            tables[name] = {
                "change": "added_table" if old is None else "missing_source_table",
                "row_count": entry["row_count"],
                "content_sha256": entry["content_sha256"],
                "row_keys": sorted(entry["rows"]),
            }
            continue
        old_rows, new_rows = old["rows"], new["rows"]
        immutable = set(old["immutable_columns"]) | set(new["immutable_columns"])
        changed_rows = {}
        for key in sorted(old_rows.keys() & new_rows.keys()):
            previous, current = old_rows[key], new_rows[key]
            columns = [
                {
                    "column": column,
                    "before_sha256": previous["columns"].get(column),
                    "after_sha256": current["columns"].get(column),
                    "native_immutable_column": column in immutable,
                }
                for column in sorted(previous["columns"].keys() | current["columns"].keys())
                if previous["columns"].get(column) != current["columns"].get(column)
            ]
            if (
                columns
                or previous["count"] != current["count"]
                or previous["sha256"] != current["sha256"]
            ):
                changed_rows[key] = {
                    "before_count": previous["count"],
                    "after_count": current["count"],
                    "before_sha256": previous["sha256"],
                    "after_sha256": current["sha256"],
                    "columns": columns,
                }
        content_keys = {"rows", "row_count", "content_sha256"}
        catalog = _changes(
            {k: v for k, v in old.items() if k not in content_keys},
            {k: v for k, v in new.items() if k not in content_keys},
        )
        added, missing = (
            sorted(new_rows.keys() - old_rows.keys()),
            sorted(old_rows.keys() - new_rows.keys()),
        )
        if catalog or changed_rows or added or missing:
            tables[name] = {
                "change": "changed_table",
                "before_row_count": old["row_count"],
                "after_row_count": new["row_count"],
                "catalog_changes": catalog,
                "added_row_keys": added,
                "missing_source_row_keys": missing,
                "changed_rows": changed_rows,
            }
    separately_reported = {"schema_name", "target", "physical_target", "tables", "sha256"}
    return {
        "schema_version": "dewey-tapdb10-inventory-review/v1",
        "status": "review_required",
        "native_verification_required": True,
        "schema_name_changed": before["schema_name"] != after["schema_name"],
        "target_changes": _changes(before["target"], after["target"]),
        "physical_target_changes": _changes(before["physical_target"], after["physical_target"]),
        "inventory_metadata_changes": _changes(
            {k: v for k, v in before.items() if k not in separately_reported},
            {k: v for k, v in after.items() if k not in separately_reported},
        ),
        "before_table_count": len(old_tables),
        "after_table_count": len(new_tables),
        "tables": tables,
    }


def write_review(
    before_path: Path,
    after_path: Path,
    report_path: Path,
    *,
    max_input_bytes: int = MAX_INPUT_BYTES,
) -> None:
    if not report_path.is_absolute() or not report_path.parent.is_dir():
        raise EvidenceError("Report must name a new absolute file in an existing directory")
    before, before_ref = read_inventory(before_path, max_input_bytes=max_input_bytes)
    after, after_ref = read_inventory(after_path, max_input_bytes=max_input_bytes)
    report = {
        **compare(before, after),
        "before": before_ref,
        "after": after_ref,
        "max_input_bytes": max_input_bytes,
    }
    # Exclusive creation also refuses existing symlinks and input-file collisions.
    descriptor = os.open(report_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--before", type=Path, required=True, help="Absolute native inventory/source receipt"
    )
    parser.add_argument(
        "--after", type=Path, required=True, help="Absolute native inventory/source receipt"
    )
    parser.add_argument(
        "--report", type=Path, required=True, help="Absolute new hash-only review file"
    )
    parser.add_argument(
        "--max-input-bytes",
        type=int,
        required=True,
        help="Explicit reviewed finite limit for each complete input JSON file (not native evidence bytes)",
    )
    args = parser.parse_args()
    try:
        write_review(args.before, args.after, args.report, max_input_bytes=args.max_input_bytes)
    except EvidenceError as error:
        print(f"Inventory review refused: {error}; no acceptance was performed.")
        return 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Avoid printing untrusted receipt content, which can include identities.
        print(f"Inventory review refused ({type(error).__name__}); no acceptance was performed.")
        return 2
    print("Review written; native identity verification and independent review remain required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
