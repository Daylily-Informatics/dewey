"""QEO dispatch commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out
from cli_core_yo.spec import CommandPolicy

from dewey_service.cli._registry_v2 import REQUIRED_JSON, REQUIRED_MUTATING
from dewey_service.cli._service import build_cli_service
from dewey_service.qeo_package_contract import PackageRegistration
from dewey_service.qeo_resolver_auth import issue_resolver_credential
from dewey_service.settings import clear_settings_cache, get_settings


def _resolver_credential_create(
    token_output_file: Path = typer.Option(
        ..., help="New absolute private token file; never printed."
    ),
    lifetime_days: int = typer.Option(90, min=1, max=366),
) -> None:
    """Issue QEO-only resolver credential locally; does not configure any running service."""
    try:
        result = issue_resolver_credential(token_output_file, lifetime_days=lifetime_days)
    except (ValueError, OSError) as exc:
        ccyo_out.error(f"Resolver credential creation failed: {exc}")
        raise typer.Exit(1) from exc
    ccyo_out.emit_json(result)


def _package_register(
    manifest: Path = typer.Option(..., help="Absolute JSON manifest of existing artifact EUIDs."),
    idempotency_key: str = typer.Option(..., help="Stable operator-selected registration key."),
) -> None:
    """Atomically register an explicit complete MultiQC package and member lineage."""
    try:
        if not manifest.is_absolute() or not idempotency_key.strip():
            raise ValueError("An absolute manifest and nonempty idempotency key are required")
        request = PackageRegistration.model_validate_json(manifest.read_text())
        _, result = build_cli_service().register_qeo_package(
            request, idempotency_key=idempotency_key
        )
    except Exception as exc:
        ccyo_out.error(f"Package registration failed: {exc}")
        raise typer.Exit(1) from exc
    ccyo_out.emit_json(result)


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
        "resolver-credential-create",
        _resolver_credential_create,
        help_text="Create a dedicated resolver token in a new private local file.",
        policy=CommandPolicy(runtime_guard="exempt", mutates_state=True, supports_json=True),
    )
    registry.add_command(
        "qeo",
        "package-register",
        _package_register,
        help_text="Register a complete MultiQC package of existing Dewey artifacts.",
        policy=REQUIRED_MUTATING,
    )
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
