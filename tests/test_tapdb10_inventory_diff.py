"""Offline structural fixtures only; none represent persisted Dewey objects."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tapdb10_inventory_diff.py"
SPEC = importlib.util.spec_from_file_location("tapdb10_inventory_diff", SCRIPT)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


def sealed(payload):
    result = copy.deepcopy(payload)
    result.pop("sha256", None)
    result["sha256"] = review.digest(result)
    return result


def table(*, count=1):
    # Integer and plain-label fixtures, never Meridian-style EUIDs.
    values = {"uid": 1, "is_deleted": True, "payload": "private fixture text"}
    rows = {
        review.digest([1]): {
            "sha256": review.digest(values),
            "count": count,
            "columns": {key: review.digest(value) for key, value in values.items()},
            "identity": {"uid": 1, "fixture_marker": "private fixture identity"},
        }
    }
    return {
        "kind": "r",
        "columns": [{"name": column} for column in values],
        "immutable_columns": ["uid"],
        "primary_key": ["uid"],
        "rls_forced": True,
        "rows": rows,
        "row_count": count,
        "content_sha256": review.digest(rows),
    }


def inventory():
    return sealed(
        {
            "schema_version": review.IDENTITY_VERSION,
            "schema_name": "offline_fixture_schema",
            "target": {"database": "offline_fixture_source"},
            "physical_target": {"database_oid": 1},
            "tables": {"fixture_history": table()},
        }
    )


def reseal_inventory(payload):
    for entry in payload["tables"].values():
        entry["row_count"] = sum(row["count"] for row in entry["rows"].values())
        entry["content_sha256"] = review.digest(entry["rows"])
    return sealed(payload)


def save(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_no_differences_still_requires_native_and_independent_review():
    baseline = inventory()
    result = review.compare(baseline, baseline)
    assert result["status"] == "review_required"
    assert result["native_verification_required"] is True
    assert result["tables"] == {}
    assert "ok" not in result
    assert "conversion_manifest" not in result


def test_deleted_rows_lineage_and_additional_tables_are_never_filtered():
    before = inventory()
    before["tables"]["fixture_lineage"] = table(count=2)
    before["tables"]["fixture_integration"] = table()
    after = copy.deepcopy(before)
    after["tables"]["fixture_history"]["rows"].clear()
    next(iter(after["tables"]["fixture_lineage"]["rows"].values()))["count"] = 1
    del after["tables"]["fixture_integration"]
    after["tables"]["new_native_table"] = table()
    result = review.compare(reseal_inventory(before), reseal_inventory(after))
    assert result["tables"]["fixture_history"]["missing_source_row_keys"] == [review.digest([1])]
    lineage = result["tables"]["fixture_lineage"]["changed_rows"][review.digest([1])]
    assert (lineage["before_count"], lineage["after_count"]) == (2, 1)
    assert result["tables"]["fixture_integration"]["change"] == "missing_source_table"
    assert result["tables"]["new_native_table"]["change"] == "added_table"


def test_cell_catalog_and_physical_changes_are_visible_without_row_values():
    before, after = inventory(), inventory()
    row = next(iter(after["tables"]["fixture_history"]["rows"].values()))
    row["columns"]["uid"] = review.digest(2)
    row["columns"]["payload"] = review.digest("different fixture text")
    after["tables"]["fixture_history"]["rls_forced"] = False
    after["physical_target"]["database_oid"] = 2
    after["target"]["database"] = "offline_fixture_destination"
    result = review.compare(before, reseal_inventory(after))
    changed = result["tables"]["fixture_history"]
    cells = changed["changed_rows"][review.digest([1])]["columns"]
    assert {cell["column"]: cell["native_immutable_column"] for cell in cells} == {
        "payload": False,
        "uid": True,
    }
    assert [field["field"] for field in changed["catalog_changes"]] == ["rls_forced"]
    assert result["physical_target_changes"][0]["field"] == "database_oid"
    encoded = json.dumps(result)
    assert "private fixture" not in encoded
    assert "different fixture text" not in encoded
    assert "offline_fixture_destination" not in encoded


def test_prefix_binding_cells_are_reported_even_without_native_immutable_marking():
    before = inventory()
    row = next(iter(before["tables"]["fixture_history"]["rows"].values()))
    row["columns"]["entity_prefix"] = review.digest("DGX")
    after = copy.deepcopy(before)
    next(iter(after["tables"]["fixture_history"]["rows"].values()))["columns"]["entity_prefix"] = (
        review.digest("TPX")
    )
    result = review.compare(reseal_inventory(before), reseal_inventory(after))
    cells = result["tables"]["fixture_history"]["changed_rows"][review.digest([1])]["columns"]
    assert cells == [
        {
            "column": "entity_prefix",
            "before_sha256": review.digest("DGX"),
            "after_sha256": review.digest("TPX"),
            "native_immutable_column": False,
        }
    ]


def test_historical_contract_retains_exact_input_file_references(tmp_path):
    identity = inventory()
    contract = sealed(
        {
            "schema_version": review.SOURCE_VERSION,
            "source_version": "9.0.9",
            "source_version_evidence": "operator_declared",
            "identity_inventory": identity,
            "sequence_inventory": sealed({"schema_version": "tapdb-sequence-inventory/v1"}),
            "recovery_family": sealed({"schema_version": "tapdb-recovery-family/v1"}),
        }
    )
    path = save(tmp_path / "source.json", contract)
    actual, reference = review.read_inventory(path)
    assert actual == identity
    assert reference["receipt_sha256"] == contract["sha256"]
    assert reference["identity_inventory_sha256"] == identity["sha256"]
    contract["sequence_inventory"]["unexpected"] = True
    with pytest.raises(review.EvidenceError, match="checksum"):
        review.read_inventory(save(path, sealed(contract)))


@pytest.mark.parametrize(
    "failure",
    ["version", "seal", "nested_content", "row_count", "row_key", "cell_hash", "negative_count"],
)
def test_corrupt_or_incomplete_evidence_is_refused(tmp_path, failure):
    payload = inventory()
    entry = payload["tables"]["fixture_history"]
    row = next(iter(entry["rows"].values()))
    if failure == "version":
        payload["schema_version"] = "unsupported"
    elif failure == "seal":
        payload["sha256"] = "corrupt"
    elif failure == "nested_content":
        entry["content_sha256"] = review.digest("wrong content")
    elif failure == "row_count":
        entry["row_count"] = 8
    elif failure == "row_key":
        entry["rows"]["raw identity must not reach report"] = entry["rows"].pop(review.digest([1]))
    elif failure == "cell_hash":
        row["columns"]["payload"] = "raw text must not reach report"
    elif failure == "negative_count":
        row["count"] = -1
    if failure != "seal":
        payload = sealed(payload)
    with pytest.raises(review.EvidenceError):
        review.read_inventory(save(tmp_path / "bad.json", payload))


@pytest.mark.parametrize("raw", ['{"schema_version":"a","schema_version":"b"}', '{"value":NaN}'])
def test_ambiguous_json_is_refused(tmp_path, raw):
    path = tmp_path / "ambiguous.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(review.EvidenceError):
        review.read_inventory(path)


def test_report_is_exclusive_private_and_cannot_overwrite_an_input(tmp_path):
    before = save(tmp_path / "before.json", inventory())
    after = save(tmp_path / "after.json", inventory())
    report = tmp_path / "review.json"
    review.write_review(before, after, report)
    assert report.stat().st_mode & 0o777 == 0o600
    assert json.loads(report.read_text())["before"]["path"] == str(before)
    with pytest.raises(FileExistsError):
        review.write_review(before, after, report)
    original = before.read_bytes()
    with pytest.raises(FileExistsError):
        review.write_review(before, after, before)
    assert before.read_bytes() == original


def test_missing_or_relative_inputs_do_not_create_a_report(tmp_path):
    before = save(tmp_path / "before.json", inventory())
    report = tmp_path / "review.json"
    for missing in (Path("relative.json"), tmp_path / "missing.json"):
        with pytest.raises(review.EvidenceError):
            review.write_review(before, missing, report)
    assert not report.exists()
