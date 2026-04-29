"""Runtime metadata helpers for Dewey GUI and observability surfaces."""

from __future__ import annotations

import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from shutil import which


def resolve_package_version() -> str:
    """Return the installed Dewey package version derived from SCM packaging metadata."""
    try:
        return package_version("dewey-service")
    except PackageNotFoundError as exc:  # pragma: no cover - installation contract failure
        raise RuntimeError(
            "dewey-service package metadata is unavailable; install the package from the SCM-tagged build."
        ) from exc


def _git_output(repo_root: Path, *args: str) -> str:
    git_executable = which("git")
    if git_executable is None:
        raise RuntimeError("git executable is required to resolve repository metadata")
    completed = subprocess.run(
        [git_executable, "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return str(completed.stdout or "").strip()


def resolve_git_metadata(repo_root: Path | None = None) -> dict[str, str]:
    """Resolve git branch, exact tag, and short commit once at app startup."""
    root = repo_root or Path(__file__).resolve().parents[1]
    try:
        branch = _git_output(root, "branch", "--show-current") or "detached"
        try:
            tag = _git_output(root, "describe", "--tags", "--exact-match", "--match", "[0-9]*")
        except subprocess.CalledProcessError:
            tag = "unreleased"
        commit = _git_output(root, "rev-parse", "--short", "HEAD")
        return {
            "branch": branch or "detached",
            "tag": tag or "unreleased",
            "commit": commit or "unavailable",
        }
    except Exception:
        return {
            "branch": "unavailable",
            "tag": "unreleased",
            "commit": "unavailable",
        }
