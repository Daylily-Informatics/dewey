"""Code quality commands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import subprocess
import sys

import typer

from dewey_service.cli._registry_v2 import REQUIRED, REQUIRED_MUTATING, register_group_commands
from dewey_service.cli.common import PROJECT_ROOT, project_subprocess_env

quality_app = typer.Typer(help="Quality commands")


@quality_app.command("lint")
def lint() -> None:
    """Run Ruff lint checks."""
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=PROJECT_ROOT, check=False
    )
    raise typer.Exit(proc.returncode)


@quality_app.command("format")
def format_code(
    check: bool = typer.Option(True, "--check/--fix", help="Check or apply formatting"),
) -> None:
    """Run Ruff formatter."""
    cmd = [sys.executable, "-m", "ruff", "format", "."]
    if check:
        cmd.append("--check")
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    raise typer.Exit(proc.returncode)


@quality_app.command("check")
def check_all() -> None:
    """Run lint then tests."""
    lint_proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=PROJECT_ROOT, check=False
    )
    if lint_proc.returncode != 0:
        raise typer.Exit(lint_proc.returncode)

    tests_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT,
        env=project_subprocess_env(),
        check=False,
    )
    raise typer.Exit(tests_proc.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the quality command group."""
    _ = spec
    register_group_commands(
        registry,
        "quality",
        "Quality commands",
        [
            ("lint", lint, REQUIRED_MUTATING),
            ("format", format_code, REQUIRED_MUTATING),
            ("check", check_all, REQUIRED),
        ],
    )
