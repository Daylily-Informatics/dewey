"""Local orchestration guards; never connect to TapDB, Aurora, AWS, or Docker."""

import importlib.util
import json
import stat
import sys
import types
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "dewey_copy_native_lifecycle",
    Path(__file__).parents[1] / "scripts/dewey_copy_native_lifecycle.py",
)
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)


def test_exclusive_private_output_preserves_existing_file(tmp_path):
    output = tmp_path / "operator-input.json"
    lifecycle.write_new(output, {"value": 9007199254740993})
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        lifecycle.write_new(output, {"value": 1})
    assert json.loads(output.read_text())["value"] == 9007199254740993


@pytest.mark.parametrize("text", ['{"a": 1, "a": 2}', '{"a": NaN}', '[]'])
def test_malformed_operator_input_fails_closed(tmp_path, text):
    path = tmp_path / "input.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        lifecycle.read(path)


def test_copy_comparison_preserves_every_nonphysical_field():
    original = {"target": {"database": "source"}, "physical_target": {"database_oid": 1},
                "sha256": "old", "sequences": [{"name": "ordinary_counter", "last_value": 8}],
                "sequence_mappings": {}, "future_catalog_evidence": {"owner": "operator"}}
    copied = {**original, "target": {"database": "copy"},
              "physical_target": {"database_oid": 2}, "sha256": "new"}
    assert lifecycle.sequence_content(original) == lifecycle.sequence_content(copied)
    copied["future_catalog_evidence"] = {"owner": "changed"}
    assert lifecycle.sequence_content(original) != lifecycle.sequence_content(copied)


class CommandRecorder:
    def __init__(self, directory):
        self.output = directory
        self.data = {"copy_config": str(directory / "operator.yaml")}
        self.journal = directory / "native-journal"
        self.control = directory / "control.yaml"
        self.provider = directory / "provider.json"
        self.calls = []

    def out(self, name):
        return self.output / name

    def require(self, stage):
        self.calls.append(("require", stage))

    def native(self, stage, args, **kwargs):
        self.calls.append(("native", stage, args, kwargs))


@pytest.mark.parametrize("sha,reference", [(None, None), ("wrong", "reviewed"), (None, "reviewed")])
def test_apply_refuses_missing_or_changed_review_before_native_call(tmp_path, sha, reference):
    capsule = CommandRecorder(tmp_path)
    capsule.out("migration-plan.json").write_text('{"actual": "plan"}')
    with pytest.raises(ValueError):
        lifecycle.execute(capsule, "migration-apply", sha, reference)
    assert capsule.calls == []


def test_reviewed_apply_runs_only_one_explicit_native_operation(tmp_path):
    capsule = CommandRecorder(tmp_path)
    plan = capsule.out("migration-plan.json")
    plan.write_text('{"actual": "plan"}')
    lifecycle.execute(capsule, "migration-apply", lifecycle.file_hash(plan), "independent-review-record")
    calls = [item for item in capsule.calls if item[0] == "native"]
    assert len(calls) == 1
    args = calls[0][2]
    assert args[:4] == ["db", "schema", "migrate", "--apply"]
    assert args[args.index("--preflight-receipt") + 1] == plan
    assert args[args.index("--control-config") + 1] == capsule.control
    assert "--establish-writer-fence" in args
    assert "--conversion-manifest" not in args


def test_floor_projection_keeps_large_next_values_and_lower_duplicate_evidence(monkeypatch):
    # Stub only the released validators. This tests our projection after native
    # validation, not the RC implementation or synthetic persisted identities.
    recovery = types.ModuleType("daylily_tapdb.backup.recovery")
    identity = types.ModuleType("daylily_tapdb.identity_inventory")
    sequences = types.ModuleType("daylily_tapdb.sequences")
    counter = "ordinary_counter"
    retained = {"name": counter, "value": 2, "source": "earlier_observation"}
    plan = {"inventory": {}, "floors": [retained, dict(retained)],
            "advances": [{"name": counter, "next_value": 9007199254740993}]}
    identity.validate_receipt = lambda value, version: None
    recovery.inventory_floors = lambda value, source: [
        {"name": counter, "value": 8, "source": source + ":assigned_floor"}]
    recovery.recovery_family_state = lambda *args, **kwargs: None
    sequences.build_sequence_advance_plan = lambda *args, **kwargs: plan
    for module in (recovery, identity, sequences):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    actual = lifecycle.project_plan_floors(plan, "retained_native_file")
    assert [row["value"] for row in actual] == [8, 2, 2, 9007199254740993]
    assert all(row["name"] == counter for row in actual)
    assert actual[-1]["source"].endswith(":native_planned_next")
