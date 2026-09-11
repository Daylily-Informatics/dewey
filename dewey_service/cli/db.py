"""Read-only Dewey verification and explicit TapDB lifecycle delegation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import EXEMPT, REQUIRED, register_group_commands

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec


db_app = typer.Typer(help="Verify existing Dewey data and review native TapDB lifecycle ownership")


@db_app.command("verify-templates")
def verify_templates() -> None:
    """Verify existing Dewey templates using SELECT-only runtime operations."""
    from dewey_service.tapdb_backend import TapDBBackend

    try:
        backend = TapDBBackend(app_username="dewey")
        with backend.session_scope(commit=False) as session:
            backend.ensure_templates(session)
        ccyo_out.success("Dewey required templates are present; no data changed")
    except RuntimeError as exc:
        ccyo_out.error(str(exc))
        raise typer.Exit(1) from exc


@db_app.command("lifecycle")
def lifecycle() -> None:
    """Show the external native lifecycle required before starting Dewey."""
    ccyo_out.print_text(
        "Dewey startup only verifies existing templates and runtime access. "
        "It never creates databases, migrates schemas, seeds templates or prepares principals.\n"
        "Use the reviewed migration ledger with an explicit absolute operator config: "
        "tapdb --config /absolute/operator-config.yaml --help.\n"
        "TapDB 10.1.1rc1 owns backup plan/create/verify/restore-plan/restore, "
        "db schema migrate, db identity inventory/verify, db sequences advance/verify/reconcile, "
        "and db runtime-principal bootstrap/bind.\n"
        "Application data preparation belongs in an explicitly reviewed native lifecycle, "
        "never a startup overlay. Preserve existing identities, domain/prefix bindings and "
        "allocator floors. Do not seed or overwrite historical Dewey templates.\n"
        "After preservation and runtime-principal binding, close old sessions and start "
        "Dewey with the exact bound runtime config."
    )


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register verification and lifecycle guidance, with no bootstrap aliases."""
    _ = spec
    register_group_commands(
        registry,
        "db",
        "Verify existing Dewey data and review native TapDB lifecycle ownership",
        [("verify-templates", verify_templates, REQUIRED), ("lifecycle", lifecycle, EXEMPT)],
    )
