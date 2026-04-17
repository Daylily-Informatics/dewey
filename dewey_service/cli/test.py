"""Test commands for Dewey."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import REQUIRED, register_group_commands
from dewey_service.cli.common import PROJECT_ROOT

test_app = typer.Typer(help="Test commands")
_PYTEST_PASSTHROUGH = {"allow_extra_args": True, "ignore_unknown_options": True}


def _pytest_passthrough_args(ctx: typer.Context, default_args: list[str]) -> list[str]:
    """Return passthrough pytest arguments or a default invocation."""
    return list(ctx.args) if ctx.args else list(default_args)


def _require_pytest_cov() -> None:
    """Fail with a clear message when coverage support is not installed."""
    if importlib.util.find_spec("pytest_cov") is not None:
        return
    ccyo_out.error("pytest-cov is not installed; run `python -m pip install -e .`")
    raise typer.Exit(1)


@test_app.command("run", context_settings=_PYTEST_PASSTHROUGH)
def run_tests(
    ctx: typer.Context,
) -> None:
    """Run the Dewey test suite."""
    args = _pytest_passthrough_args(ctx, ["-q"])
    proc = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=PROJECT_ROOT, check=False)
    raise typer.Exit(proc.returncode)


@test_app.command("cov", context_settings=_PYTEST_PASSTHROUGH)
def run_coverage(
    ctx: typer.Context,
    html: bool = typer.Option(False, "--html", help="Generate HTML coverage report"),
) -> None:
    """Run the Dewey test suite with coverage assessment."""
    _require_pytest_cov()

    cmd = [sys.executable, "-m", "pytest", "--cov=dewey_service", "--cov-report=term-missing"]
    if html:
        cmd.append("--cov-report=html:htmlcov")
    cmd.extend(_pytest_passthrough_args(ctx, []))

    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    if html and proc.returncode == 0:
        ccyo_out.success("HTML report: htmlcov/index.html")
    raise typer.Exit(proc.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the test command group."""
    _ = spec
    register_group_commands(
        registry,
        "test",
        "Test commands",
        [
            ("run", run_tests, REQUIRED),
            ("cov", run_coverage, REQUIRED),
        ],
    )
