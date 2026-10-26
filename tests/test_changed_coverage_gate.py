"""The release gate must not turn missing measurements into a passing percentage."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "changed_coverage_gate", Path(__file__).parents[1] / "scripts/check_changed_coverage.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_hunks_count_only_new_python_lines_and_ignore_deletions():
    diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,0 @@
-old
-old
@@ -10 +9,3 @@
+one
+two
+three
@@ -20 +21 @@
+single
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+first
+second
--- a/x.js
+++ b/x.js
@@ -1 +1 @@
+outside-python
"""
    assert gate.changed_lines(diff) == {"app.py": {9, 10, 11, 21}, "new.py": {1, 2}}


def test_line_and_branch_gates_are_independent_and_boundary_is_inclusive():
    measured = {
        "app.py": {
            "executed_lines": [1, 2, 3, 4],
            "missing_lines": [5, 99],
            "executed_branches": [[1, 2], [1, 3], [3, 4], [3, 5]],
            "missing_branches": [[5, -1], [99, 100]],
            "excluded_lines": [6],
        }
    }
    report = gate.assess({"app.py": set(range(1, 7))}, measured)
    assert report["status"] == "pass"
    assert report["totals"]["line_percent"] == report["totals"]["branch_percent"] == 80
    assert report["files"]["app.py"]["excluded_changed_lines"] == [6]
    assert (
        gate.assess({"app.py": set(range(1, 7))}, measured, minimum_branch=81)["status"] == "fail"
    )
    assert gate.assess({"app.py": set(range(1, 7))}, measured, minimum_line=81)["status"] == "fail"


def test_unmeasured_added_file_fails_closed_even_if_other_files_pass():
    report = gate.assess({"new.py": {1}, "deleted.py": set()}, {})
    assert report["status"] == "fail"
    assert report["unmeasured_files"] == ["new.py"]


def test_comment_only_change_and_no_new_branches_are_explicit_empty_denominators():
    report = gate.assess({"app.py": {2}}, {"app.py": {"executed_lines": [1], "missing_lines": []}})
    assert report["status"] == "pass"
    assert report["totals"]["total_lines"] == report["totals"]["total_branches"] == 0


def test_istanbul_keeps_distinct_inline_branches_and_uses_standard_line_coverage():
    location = {"start": {"line": 5}, "end": {"line": 5}}
    document = {
        "app.js": {
            "statementMap": {"0": location, "1": location},
            "s": {"0": 0, "1": 1},
            "branchMap": {"0": {"line": 5, "loc": location}},
            "b": {"0": [1, 0]},
        }
    }
    report = gate.assess({"app.js": {5}}, gate.istanbul_files(document))
    assert report["totals"]["line_percent"] == 100
    assert report["totals"]["branch_percent"] == 50
    assert report["status"] == "fail"
    assert report["files"]["app.js"]["missing_branches"] == [[5, "0:1"]]
