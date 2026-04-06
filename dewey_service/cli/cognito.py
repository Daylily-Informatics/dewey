"""Cognito helper commands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import os
import shutil
import subprocess

import typer

from dewey_service.cli.common import console
from cli_core_yo import ccyo_out

cognito_app = typer.Typer(help="Cognito helper commands")


@cognito_app.command("status")
def status() -> None:
    """Show daycog status for the Dewey runtime."""
    daycog_path = shutil.which("daycog")
    if not daycog_path:
        ccyo_out.error("daycog not found in PATH")
        raise typer.Exit(1)

    try:
        proc = subprocess.run(
            [daycog_path, "status"],
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        ccyo_out.error("daycog not found in PATH")
        raise typer.Exit(1) from exc

    if proc.stdout:
        ccyo_out.print_text(proc.stdout.rstrip())
    if proc.stderr:
        ccyo_out.print_text(proc.stderr.rstrip(), style="yellow")
    raise typer.Exit(proc.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the cognito command group."""
    registry.add_typer_app(None, cognito_app, "cognito", "Cognito helper commands")
