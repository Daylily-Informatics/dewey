"""QEO dispatch commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import REQUIRED_JSON, REQUIRED_MUTATING
from dewey_service.cli._service import build_cli_service
from dewey_service.settings import clear_settings_cache, get_settings


def _status() -> None:
    """Show explicit Dewey-to-QEO dispatch configuration status."""

    clear_settings_cache()
    settings = get_settings()
    ccyo_out.print_text(
        "qeo.dispatch_configured="
        + str(
            bool(settings.qeo_ingest_url and settings.qeo_api_token and settings.qeo_consumer_group)
        ).lower()
    )
    ccyo_out.print_text(f"qeo.ingest_url={settings.qeo_ingest_url or '<unset>'}")
    ccyo_out.print_text(f"qeo.api_token={'<redacted>' if settings.qeo_api_token else '<unset>'}")
    ccyo_out.print_text(f"qeo.consumer_group={settings.qeo_consumer_group or '<unset>'}")


def _dispatch(
    limit: int = typer.Option(100, min=1, max=1000, help="Maximum outbox rows to dispatch."),
    retry_errors: bool = typer.Option(False, help="Retry rows currently marked error."),
    event_id: list[str] | None = typer.Option(
        None,
        "--event-id",
        help="Dispatch only the matching Dewey outbox event id. Repeat for multiple ids.",
    ),
    artifact_set_euid: list[str] | None = typer.Option(
        None,
        "--artifact-set-euid",
        help="Dispatch only events for the matching Dewey artifact-set EUID. Repeat for multiple EUIDs.",
    ),
) -> None:
    """Dispatch pending Dewey outbox events to QEO."""

    def _normalize_repeated_option(value: object) -> set[str] | None:
        if value is None or not isinstance(value, (list, tuple, set)):
            return None
        return {str(item) for item in value}

    try:
        result = build_cli_service().dispatch_qeo_outbox(
            limit=limit,
            retry_errors=retry_errors,
            event_ids=_normalize_repeated_option(event_id),
            artifact_set_euids=_normalize_repeated_option(artifact_set_euid),
        )
    except Exception as exc:
        ccyo_out.error(f"QEO dispatch failed: {exc}")
        raise typer.Exit(1) from exc
    ccyo_out.emit_json(result)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register QEO dispatch commands."""

    _ = spec
    registry.add_command(
        "qeo",
        "status",
        _status,
        help_text="Show Dewey-to-QEO dispatch configuration status.",
        policy=REQUIRED_JSON,
    )
    registry.add_command(
        "qeo",
        "dispatch",
        _dispatch,
        help_text="Dispatch pending Dewey outbox events to QEO.",
        policy=REQUIRED_MUTATING,
    )


__all__ = ["register"]
