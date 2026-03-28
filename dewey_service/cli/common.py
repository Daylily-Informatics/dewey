"""Shared CLI constants for Dewey."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

PROJECT_ROOT = Path(__file__).resolve().parents[2]
console = Console()
