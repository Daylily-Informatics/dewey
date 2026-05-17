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
from dewey_service.defaults import AWS_PROFILE_REQUIRED_MESSAGE, resolve_aws_profile
from dewey_service.integrations.tapdb_runtime import (
    TapDBRuntimeError,
    run_tapdb_cli,
)
from dewey_service.settings import get_settings, load_config_aws_profile

tapdb_app = typer.Typer(help="TapDB passthrough wrappers")


def _resolve_cli_aws_profile(profile: str) -> str:
    explicit_profile = str(profile or "").strip()
    if explicit_profile:
        return explicit_profile
    resolved_profile = resolve_aws_profile(
        cli_profile="",
        config_profile=load_config_aws_profile(),
    )
    if resolved_profile:
        return resolved_profile
    raise TapDBRuntimeError(AWS_PROFILE_REQUIRED_MESSAGE)


@tapdb_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_command(
    ctx: typer.Context,
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option("", "--profile", help="AWS profile"),
    region: str = typer.Option("", "--region", help="AWS region"),
    namespace: str = typer.Option("", "--namespace", help="TapDB namespace"),
) -> None:
    """Run raw TapDB CLI arguments through the Dewey runtime context."""
    if not ctx.args:
        raise typer.BadParameter("Missing tapdb arguments")

    try:
        settings = get_settings()
        resolved_profile = _resolve_cli_aws_profile(profile)
        resolved_region = str(region or settings.aws_region or "").strip()
        if not resolved_region:
            raise TapDBRuntimeError("--region or settings.aws_region is required")
        resolved_namespace = str(namespace or settings.tapdb_database_name or "").strip()
        if not resolved_namespace:
            raise TapDBRuntimeError("--namespace or settings.tapdb_database_name is required")
        resolved_client_id = str(settings.tapdb_client_id or "").strip()
        if not resolved_client_id:
            raise TapDBRuntimeError("settings.tapdb_client_id is required")
        result = run_tapdb_cli(
            list(ctx.args),
            target=target,
            client_id=resolved_client_id,
            profile=resolved_profile,
            region=resolved_region,
            namespace=resolved_namespace,
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
