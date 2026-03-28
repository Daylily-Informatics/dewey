"""Test commands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import subprocess
import sys

import typer

from dewey_service.cli.common import PROJECT_ROOT

test_app = typer.Typer(help="Test commands")


@test_app.command("run")
def run_tests(
    pytest_args: list[str] = typer.Argument(
        None,
        help="Optional pytest arguments, e.g. tests/test_app_boot.py -q",
    ),
) -> None:
    """Run the Dewey test suite."""
    args = list(pytest_args or ["-q"])
    proc = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=PROJECT_ROOT, check=False)
    raise typer.Exit(proc.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the test command group."""
    registry.add_typer_app(None, test_app, "test", "Test commands")
