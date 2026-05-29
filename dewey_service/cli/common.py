"""Shared CLI constants for Dewey."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console

PROJECT_ROOT = Path(__file__).resolve().parents[2]
console = Console()


def project_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["DAYHOFF_PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["DEWEY_PROJECT_ROOT"] = str(PROJECT_ROOT)
    return env
