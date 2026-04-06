"""Extra config subcommands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out

from dewey_service.settings import (
    clear_settings_cache,
    get_config_file_path,
    get_settings,
    persist_managed_storage_bucket,
)


def _status() -> None:
    """Show merged Dewey runtime settings."""
    clear_settings_cache()
    try:
        settings = get_settings()
    except Exception as exc:
        ccyo_out.error(f"Configuration invalid: {exc}")
        raise typer.Exit(1) from exc

    ccyo_out.print_text(f"Config path: [cyan]{get_config_file_path()}[/cyan]")
    ccyo_out.print_text(settings.model_dump_json(indent=2))


def _set_artifact_bucket(
    bucket: str = typer.Argument(
        ..., help="S3 bucket name for Dewey-managed artifact copies and uploads."
    ),
) -> None:
    """Persist the managed artifact bucket in the Dewey config file."""
    try:
        config_path, normalized = persist_managed_storage_bucket(bucket)
        settings = get_settings()
    except Exception as exc:
        ccyo_out.error(f"Could not update artifact bucket: {exc}")
        raise typer.Exit(1) from exc

    ccyo_out.success(f"Updated artifact bucket in {config_path}")
    ccyo_out.print_text(f"managed_storage_bucket={settings.managed_storage_bucket or normalized}")


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register Dewey-specific config subcommands."""
    registry.add_command("config", "status", _status, "Show merged Dewey runtime settings")
    registry.add_command(
        "config",
        "set-artifact-bucket",
        _set_artifact_bucket,
        "Set the S3 bucket Dewey uses for managed artifact storage.",
    )
