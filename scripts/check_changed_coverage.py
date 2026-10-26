#!/usr/bin/env python3
"""Gate executable changed lines and branch origins using coverage.py JSON.

The baseline is explicit and recorded. Unmeasured changed Python files fail closed.
Deleted lines, unchanged legacy code and non-executable lines are not a denominator.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess


def changed_lines(diff, suffix=".py"):
    result = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            name = line[4:]
            current = name[2:] if name.startswith("b/") and name.endswith(suffix) else None
            if current:
                result.setdefault(current, set())
        elif current and line.startswith("@@ "):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if not match:
                raise ValueError("Unsupported Git diff hunk")
            start = int(match[1])
            count = int(match[2]) if match[2] is not None else 1
            result[current].update(range(start, start + count))
    return result


def percentage(covered, total):
    return 100.0 if not total else 100.0 * covered / total


def assess(changes, measured, *, minimum_line=80, minimum_branch=80):
    files = {}
    unmeasured = []
    for name, added in sorted(changes.items()):
        if not added:
            continue
        if name not in measured:
            unmeasured.append(name)
            continue
        data = measured[name]
        executed = set(data["executed_lines"])
        missing = set(data["missing_lines"])
        relevant = added & (executed | missing)
        executed_arcs = {tuple(arc) for arc in data.get("executed_branches", []) if arc[0] in added}
        missing_arcs = {tuple(arc) for arc in data.get("missing_branches", []) if arc[0] in added}
        branches = executed_arcs | missing_arcs
        files[name] = {
            "covered_lines": len(relevant & executed),
            "total_lines": len(relevant),
            "missing_lines": sorted(relevant & missing),
            "covered_branches": len(executed_arcs),
            "total_branches": len(branches),
            "missing_branches": sorted(map(list, missing_arcs)),
            "excluded_changed_lines": sorted(added & set(data.get("excluded_lines", []))),
        }
    total = {key: sum(value[key] for value in files.values()) for key in
             ("covered_lines", "total_lines", "covered_branches", "total_branches")}
    total["line_percent"] = percentage(total["covered_lines"], total["total_lines"])
    total["branch_percent"] = percentage(total["covered_branches"], total["total_branches"])
    passed = not unmeasured and total["line_percent"] >= minimum_line and total["branch_percent"] >= minimum_branch
    return {"status": "pass" if passed else "fail", "thresholds": {
                "changed_lines": minimum_line, "changed_branch_origins": minimum_branch},
            "totals": total, "unmeasured_files": unmeasured, "files": files}


def git(root, *args):
    return subprocess.check_output(["git", "-c", "core.quotePath=false", "-C", str(root), *args], text=True)


def istanbul_files(document):
    """Normalize standard Istanbul line counts and distinct branch alternatives."""
    result = {}
    for name, value in document.items():
        lines = {}
        for key, location in value["statementMap"].items():
            line = location["start"]["line"]
            lines[line] = max(lines.get(line, 0), value["s"][key])
        covered, missing = [], []
        for key, location in value["branchMap"].items():
            origin = location.get("line", location["loc"]["start"]["line"])
            for index, count in enumerate(value["b"][key]):
                (covered if count else missing).append([origin, f"{key}:{index}"])
        result[name] = {
            "executed_lines": [line for line, count in lines.items() if count],
            "missing_lines": [line for line, count in lines.items() if not count],
            "executed_branches": covered, "missing_branches": missing,
        }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--coverage-json", type=Path, required=True)
    parser.add_argument("--format", choices=("python", "istanbul"), default="python")
    parser.add_argument("--source", action="append", required=True,
                        help="Repository-relative Python source path; repeat for multiple scopes")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-line", type=float, default=80)
    parser.add_argument("--minimum-branch", type=float, default=80)
    args = parser.parse_args(argv)
    if not all(0 <= value <= 100 for value in (args.minimum_line, args.minimum_branch)):
        parser.error("Coverage thresholds must be between 0 and 100")
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    for source in args.source:
        if Path(source).is_absolute() or ".." in Path(source).parts or source.startswith("-"):
            parser.error("Source scopes must be repository-relative paths")
    baseline = git(root, "rev-parse", "--verify", "--end-of-options", args.baseline + "^{commit}").strip()
    suffix = ".py" if args.format == "python" else ".js"
    changes = changed_lines(git(root, "diff", "--no-ext-diff", "--no-renames", "--unified=0",
                                baseline, "--", *args.source), suffix=suffix)
    for name in git(root, "ls-files", "--others", "--exclude-standard", "--", *args.source).splitlines():
        if name.endswith(suffix):
            changes[name] = set(range(1, len((root / name).read_text().splitlines()) + 1))
    coverage = json.loads(args.coverage_json.read_text())
    if args.format == "python" and not coverage.get("meta", {}).get("branch_coverage"):
        parser.error("coverage.py JSON must include branch coverage")
    source_files = coverage["files"] if args.format == "python" else istanbul_files(coverage)
    measured = {}
    for name, data in source_files.items():
        path = Path(name)
        absolute = path.resolve() if path.is_absolute() else (root / path).resolve()
        if absolute.is_relative_to(root):
            measured[str(absolute.relative_to(root))] = data
    report = assess(changes, measured, minimum_line=args.minimum_line, minimum_branch=args.minimum_branch)
    report.update(baseline_commit=baseline, head_commit=git(root, "rev-parse", "HEAD").strip(),
                  working_tree_changes=bool(git(root, "status", "--porcelain", "--", *args.source)),
                  source_paths=args.source, coverage_timestamp=coverage.get("meta", {}).get("timestamp"),
                  format=args.format,
                  metric="Executable added/modified lines and branches whose source line changed")
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    totals = report["totals"]
    print(f"Changed coverage {report['status']}: lines {totals['line_percent']:.2f}% "
          f"({totals['covered_lines']}/{totals['total_lines']}), branches {totals['branch_percent']:.2f}% "
          f"({totals['covered_branches']}/{totals['total_branches']}); "
          f"unmeasured files {len(report['unmeasured_files'])}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
