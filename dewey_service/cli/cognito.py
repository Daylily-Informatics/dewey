"""Cognito helper commands for Dewey."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import os
import shutil
import subprocess

import typer
from cli_core_yo import ccyo_out
from cli_core_yo.runtime import get_context

from dewey_service.cli._registry_v2 import REQUIRED_JSON, register_group_commands

cognito_app = typer.Typer(help="Cognito helper commands")


def _json_mode_enabled() -> bool:
    try:
        return bool(get_context().json_mode)
    except Exception:
        return False


@cognito_app.command("status")
def status() -> None:
    """Show daycog status for the Dewey runtime."""
    daycog_path = shutil.which("daycog")
    if not daycog_path:
        ccyo_out.error("daycog not found in PATH")
        raise typer.Exit(1)

    json_mode = _json_mode_enabled()
    cmd = [daycog_path, "status"]
    if json_mode:
        cmd.append("--json")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        ccyo_out.error("daycog not found in PATH")
        raise typer.Exit(1) from exc

    if json_mode:
        if proc.stdout:
            sys.stdout.write(proc.stdout if proc.stdout.endswith("\n") else f"{proc.stdout}\n")
            sys.stdout.flush()
        if proc.stderr:
            sys.stderr.write(proc.stderr if proc.stderr.endswith("\n") else f"{proc.stderr}\n")
            sys.stderr.flush()
        raise typer.Exit(proc.returncode)

    if proc.stdout:
        ccyo_out.print_text(proc.stdout.rstrip())
    if proc.stderr:
        ccyo_out.warning(proc.stderr.rstrip())
    raise typer.Exit(proc.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the cognito command group."""
    _ = spec
    register_group_commands(
        registry,
        "cognito",
        "Cognito helper commands",
        [
            ("status", status, REQUIRED_JSON),
        ],
    )
