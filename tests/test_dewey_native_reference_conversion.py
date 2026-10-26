"""New offline guards for canonical identity and exact additive conversion proof."""

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

scripts = Path(__file__).parents[1] / "scripts"
metadata_spec = importlib.util.spec_from_file_location(
    "dewey_metadata_conversion", scripts / "dewey_metadata_conversion.py"
)
metadata = importlib.util.module_from_spec(metadata_spec)
metadata_spec.loader.exec_module(metadata)
sys.modules[metadata_spec.name] = metadata
spec = importlib.util.spec_from_file_location(
    "dewey_native_reference_conversion", scripts / "dewey_native_reference_conversion.py"
)
conversion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conversion)


def native_spec(*, kind="kind-a", tenant=None, relationship="asserts"):
    # Deliberately opaque synthetic identity: no fabricated owning-service EUID.
    return SimpleNamespace(
        target=SimpleNamespace(
            identity_key="synthetic-native-identity",
            target_object_kind=kind,
            target_tenant_id=tenant,
        ),
        relationship_type=relationship,
    )


def test_same_native_identity_cannot_split_by_kind_or_conflicting_tenant():
    targets, assertions = {}, set()
    conversion.register_identity(targets, assertions, 1, native_spec())
    with pytest.raises(ValueError, match="Conflicting non-null"):
        conversion.register_identity(targets, assertions, 2, native_spec(kind="kind-b"))
    targets, assertions = {}, set()
    conversion.register_identity(targets, assertions, 1, native_spec(tenant="opaque-tenant-a"))
    with pytest.raises(ValueError, match="Conflicting non-null"):
        conversion.register_identity(targets, assertions, 2, native_spec(tenant="opaque-tenant-b"))


def test_duplicate_assertion_is_rejected_before_native_writer():
    targets, assertions = {}, set()
    conversion.register_identity(targets, assertions, 1, native_spec())
    with pytest.raises(ValueError, match="same native assertion"):
        conversion.register_identity(targets, assertions, 1, native_spec())
    conversion.register_identity(
        targets, assertions, 1, native_spec(relationship="different-relation")
    )
    conversion.register_identity(targets, assertions, 2, native_spec())
    assert len(targets) == 1 and len(assertions) == 3


def test_unreviewed_descriptor_enrichment_is_explicitly_rejected():
    targets, assertions = {}, set()
    conversion.register_identity(targets, assertions, 1, native_spec(kind=None))
    with pytest.raises(ValueError, match="enrichment"):
        conversion.register_identity(targets, assertions, 2, native_spec())


def test_manifest_only_accepts_exact_planned_outcomes_and_native_additions():
    tables = ("generic_instance", "generic_instance_lineage", "audit_log")
    before = {
        "sha256": "before-seal",
        "target": {},
        "physical_target": {},
        "tables": {name: {"rows": {"old": {"sha256": "old"}}} for name in tables},
    }
    after = {
        "target": {},
        "physical_target": {},
        "tables": {
            name: {"rows": {"old": {"sha256": "old"}, "new": {"sha256": "new"}}} for name in tables
        },
    }
    record = {
        "relation_uid": 3,
        "source_uid": 2,
        "target_identity_sha256": "opaque-hash",
        "disposition": "native_tapdb_object",
    }
    result = {
        "plan": {
            "before_inventory_sha256": "before-seal",
            "records": [record],
            "counts": {"native_targets": 1, "native_assertions": 1, "new_audit_rows": 1},
        },
        "outcomes": [{key: value for key, value in record.items() if key != "disposition"}],
        "new_rows": {name: {"new": "new"} for name in tables},
    }
    manifest = conversion.make_manifest(before, after, result)
    assert manifest == {
        "schema_version": "tapdb-identity-conversion/v1",
        "tables": {name: {"added_rows": True} for name in tables},
        "added_tables": [],
    }
    altered = deepcopy(result)
    altered["outcomes"][0]["source_uid"] = 7
    with pytest.raises(ValueError, match="planned assertions"):
        conversion.make_manifest(before, after, altered)
    altered = deepcopy(after)
    altered["tables"]["generic_instance"]["rows"]["unexpected"] = {"sha256": "unplanned"}
    with pytest.raises(ValueError, match="additions"):
        conversion.make_manifest(before, altered, result)
    altered = deepcopy(result)
    del altered["new_rows"]["audit_log"]
    with pytest.raises(ValueError, match="addition tables"):
        conversion.make_manifest(before, after, altered)
