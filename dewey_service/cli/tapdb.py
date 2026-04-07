"""TapDB passthrough wrappers for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import REQUIRED_MUTATING, register_group_commands
from dewey_service.cli.common import PROJECT_ROOT
from dewey_service.integrations.tapdb_runtime import (
    DEFAULT_AWS_PROFILE,
    DEFAULT_AWS_REGION,
    DEFAULT_TAPDB_CLIENT_ID,
    DEFAULT_TAPDB_DATABASE_NAME,
    TapDBRuntimeError,
    run_tapdb_cli,
)

tapdb_app = typer.Typer(help="TapDB passthrough wrappers")


@tapdb_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_command(
    ctx: typer.Context,
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Run raw TapDB CLI arguments through the Dewey runtime context."""
    if not ctx.args:
        raise typer.BadParameter("Missing tapdb arguments")

    try:
        result = run_tapdb_cli(
            list(ctx.args),
            target=target,
            client_id=DEFAULT_TAPDB_CLIENT_ID,
            profile=profile,
            region=region,
            namespace=namespace,
            cwd=PROJECT_ROOT,
            check=False,
        )
    except TapDBRuntimeError as exc:
        ccyo_out.error(f"TapDB invocation failed: {exc}")
        raise typer.Exit(1) from exc

    if result.stdout:
        ccyo_out.print_text(result.stdout.rstrip())
    if result.stderr:
        ccyo_out.warning(result.stderr.rstrip())
    raise typer.Exit(result.returncode)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the tapdb command group."""
    _ = spec
    register_group_commands(
        registry,
        "tapdb",
        "TapDB passthrough wrappers",
        [
            ("run", run_command, REQUIRED_MUTATING),
        ],
    )
