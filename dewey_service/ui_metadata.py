"""Runtime metadata helpers for Dewey GUI and observability surfaces."""

from __future__ import annotations

import subprocess
import os
import re
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
    if os.environ.get("DEWEY_EXECUTION_BACKEND") == "dewey-container":
        revision = os.environ.get("DEWEY_BUILD_SHA", "")
        branch = os.environ.get("DEWEY_BUILD_BRANCH", "")
        if not re.fullmatch(r"[0-9a-f]{40}", revision) or revision != os.environ.get("LSMC_RELEASE_SHA") or not branch:
            raise RuntimeError("Container release identity requires matching full SHAs and DEWEY_BUILD_BRANCH")
        return {"branch": branch, "tag": resolve_package_version(), "commit": revision, "source": "tagged-image"}
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
