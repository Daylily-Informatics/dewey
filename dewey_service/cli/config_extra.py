"""Extra config subcommands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer

from dewey_service.cli.common import console
from dewey_service.settings import clear_settings_cache, get_config_file_path, get_settings


def _status() -> None:
    """Show merged Dewey runtime settings."""
    clear_settings_cache()
    try:
        settings = get_settings()
    except Exception as exc:
        console.print(f"[red]✗[/red] Configuration invalid: {exc}")
        raise typer.Exit(1) from exc

    console.print(f"Config path: [cyan]{get_config_file_path()}[/cyan]")
    console.print(settings.model_dump_json(indent=2))


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register Dewey-specific config subcommands."""
    registry.add_command("config", "status", _status, "Show merged Dewey runtime settings")
