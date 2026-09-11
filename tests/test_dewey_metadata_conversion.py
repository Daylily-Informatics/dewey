"""Focused offline checks for the one-time historical metadata conversion."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "dewey_metadata_conversion", Path(__file__).parents[1] / "scripts/dewey_metadata_conversion.py"
)
conversion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conversion)


def test_missing_envelope_preserves_all_existing_values_and_input():
    original = {"metadata": {"count": 8, "rate": 0.125, "text": "unchanged"}, "created_at": "historical"}
    before = deepcopy(original)
    changed, effects = conversion.convert_payload(original)
    assert effects == ["add_properties"]
    assert changed == {**before, "properties": {}}
    changed["metadata"]["count"] = 9
    assert original == before


def test_graph_is_archived_verbatim_and_active_key_removed():
    graph = [{"source_field": "dewey.external_object_relation", "display_label": "opaque fixture", "details": [1, None]}]
    original = {"metadata": {"keep": True}, "properties": {"other": 7, "external_payload": {"tapdb_graph": graph, "keep": "yes"}}}
    before = deepcopy(original)
    changed, effects = conversion.convert_payload(original)
    assert effects == ["archive_graph"]
    assert changed[conversion.ARCHIVE_KEY] == {conversion.GRAPH_PATH: graph}
    assert changed["properties"] == {"other": 7, "external_payload": {"keep": "yes"}}
    assert changed["metadata"] == before["metadata"]
    assert original == before


def test_existing_valid_envelope_is_unchanged_and_empty_graph_is_archived():
    original = {"properties": {"native": "retained"}, "flat_field": [1, 2]}
    assert conversion.convert_payload(original) == (original, [])
    changed, effects = conversion.convert_payload({"properties": {"external_payload": {"tapdb_graph": []}}})
    assert effects == ["archive_graph"]
    assert changed[conversion.ARCHIVE_KEY] == {conversion.GRAPH_PATH: []}
    assert "tapdb_graph" not in changed["properties"]["external_payload"]


@pytest.mark.parametrize("payload", [
    {"properties": None},
    {conversion.ARCHIVE_KEY: {}},
    {"properties": {"external_payload": {"tapdb_graph": [{"source_field": "unreviewed"}]}}},
    {"properties": {"target_object_euid": "opaque fixture"}},
])
def test_unreviewed_or_repeated_transformations_fail(payload):
    with pytest.raises(ValueError):
        conversion.convert_payload(payload)


def test_manifest_requires_exact_plan_and_observed_audit_additions():
    item = {"table": "generic_instance", "record_type": "instance", "uid": 1,
            "row_key": "row-hash", "json_before": "old-json", "json_after": "new-json",
            "modified_before": "old-time", "effects": ["add_properties"]}
    before = {"sha256": "before-seal", "target": {}, "physical_target": {},
              "tables": {"audit_log": {"rows": {"old-audit": {"sha256": "old"}}}}}
    after = {"target": {}, "physical_target": {}, "tables": {
        "generic_instance": {"rows": {"row-hash": {"columns": {"json_addl": "new-json", "modified_dt": "new-time"}}}},
        "audit_log": {"rows": {"old-audit": {"sha256": "old"}, "new-audit": {"sha256": "new"}}}}}
    result = {"plan": {"before_inventory_sha256": "before-seal", "changes": [item], "expected_audit_rows": 1},
              "applied_changes": [{**item, "modified_after": "new-time"}], "new_audit_rows": {"new-audit": "new"}}
    manifest = conversion.make_manifest(before, after, result)
    assert set(manifest["tables"]) == {"generic_instance", "audit_log"}
    assert set(manifest["tables"]["generic_instance"]["changed_columns"]) == {"json_addl", "modified_dt"}
    assert manifest["added_tables"] == []
    altered = deepcopy(result)
    altered["applied_changes"][0]["json_after"] = "unplanned"
    with pytest.raises(ValueError, match="reviewed plan"):
        conversion.make_manifest(before, after, altered)
    altered = deepcopy(after)
    altered["tables"]["audit_log"]["rows"]["unexpected"] = {"sha256": "unexpected"}
    with pytest.raises(ValueError, match="audit additions"):
        conversion.make_manifest(before, altered, result)
