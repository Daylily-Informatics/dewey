"""Read-only Dewey verification and explicit TapDB lifecycle delegation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import EXEMPT, REQUIRED, REQUIRED_MUTATING, register_group_commands

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


def registry_conversion(
    mode: str = typer.Argument(..., help="plan, apply, or reverse; never runs at startup."),
    actor: str = typer.Option(...),
    manifest: Path = typer.Option(...),
    receipt: Path | None = typer.Option(None),
    expected_sha256: str | None = typer.Option(None),
) -> None:
    """Plan or execute the explicit Dewey 10 data conversion with private receipts."""
    from dewey_service.registry_conversion import main
    import os
    config = os.environ.get("DEWEY_CONFIG", "")
    if not config or not Path(config).is_absolute():
        raise typer.BadParameter("Set DEWEY_CONFIG to the explicit absolute service configuration")
    if mode not in {"plan", "apply", "reverse"} or not manifest.is_absolute() or receipt is not None and not receipt.is_absolute():
        raise typer.BadParameter("Choose plan/apply/reverse and absolute manifest/receipt paths")
    args = [mode, "--actor", actor, "--manifest", str(manifest)]
    if receipt is not None:
        args += ["--receipt", str(receipt)]
    if expected_sha256:
        args += ["--expected-sha256", expected_sha256]
    main(args)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register verification and lifecycle guidance, with no bootstrap aliases."""
    _ = spec
    register_group_commands(
        registry,
        "db",
        "Verify existing Dewey data and review native TapDB lifecycle ownership",
        [("verify-templates", verify_templates, REQUIRED), ("lifecycle", lifecycle, EXEMPT),
         ("registry-conversion", registry_conversion, REQUIRED_MUTATING)],
    )
