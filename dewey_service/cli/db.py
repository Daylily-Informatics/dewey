"""TapDB lifecycle and Dewey overlay commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import subprocess
import sys

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import (
    REQUIRED_MUTATING,
    REQUIRED_MUTATING_INTERACTIVE,
    register_group_commands,
)
from dewey_service.cli.common import PROJECT_ROOT
from dewey_service.defaults import AWS_PROFILE_REQUIRED_MESSAGE, resolve_aws_profile
from dewey_service.integrations.tapdb_runtime import (
    TapDBRuntimeError,
    ensure_tapdb_version,
    export_database_url_for_target,
    run_tapdb_cli,
)
from dewey_service.settings import get_settings, load_config_aws_profile

db_app = typer.Typer(help="TapDB lifecycle and Dewey overlay commands")


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


def _confirm_db_delete(force: bool) -> bool:
    if force:
        return True
    return typer.confirm("This will delete the current TapDB DB target. Continue?")


def _confirm_target_label(*, namespace: str) -> str:
    settings = get_settings()
    from daylily_tapdb.cli.db_config import get_db_config

    client_id = str(settings.tapdb_client_id or "").strip()
    if not client_id:
        raise TapDBRuntimeError("settings.tapdb_client_id is required")
    cfg = get_db_config(
        config_path=settings.tapdb_config_path,
        client_id=client_id,
        database_name=namespace,
    )
    schema_name = str(cfg.get("schema_name") or "").strip()
    physical_database = str(cfg.get("database") or namespace).strip()
    if not schema_name:
        raise TapDBRuntimeError("TapDB config is missing schema_name for destructive confirmation")
    return f"{client_id}/{namespace}/{schema_name}@{physical_database}"


def _delete_db_target(
    *,
    force: bool,
    target: str,
    profile: str,
    region: str,
    namespace: str,
    config_path: str,
) -> None:
    if not _confirm_db_delete(force):
        raise typer.Exit(0)

    try:
        settings = get_settings()
        client_id = str(settings.tapdb_client_id or "").strip()
        if not client_id:
            raise TapDBRuntimeError("settings.tapdb_client_id is required")
        run_tapdb_cli(
            ["db", "delete", "--confirm-target", _confirm_target_label(namespace=namespace)],
            target=target,
            client_id=client_id,
            profile=profile,
            region=region,
            namespace=namespace,
            config_path=config_path,
            cwd=PROJECT_ROOT,
        )
    except TapDBRuntimeError as exc:
        ccyo_out.error(f"Delete failed: {exc}")
        raise typer.Exit(1) from exc


@db_app.command("build")
def build(
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    cluster: str = typer.Option("", "--cluster", help="Aurora cluster ID for aurora target"),
    profile: str = typer.Option("", "--profile", help="AWS profile"),
    region: str = typer.Option("", "--region", help="AWS region"),
    namespace: str = typer.Option("", "--namespace", help="TapDB namespace"),
) -> None:
    """Bootstrap TapDB runtime and apply the Dewey overlay."""
    ensure_tapdb_version()
    try:
        settings = get_settings()
        resolved_config_path = str(settings.tapdb_config_path or "").strip()
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
        if target == "local":
            result = run_tapdb_cli(
                ["bootstrap", "local", "--no-gui"],
                target=target,
                client_id=resolved_client_id,
                profile=resolved_profile,
                region=resolved_region,
                namespace=resolved_namespace,
                config_path=resolved_config_path,
                cwd=PROJECT_ROOT,
            )
        else:
            if not cluster.strip():
                raise TapDBRuntimeError("--cluster is required for aurora target")
            result = run_tapdb_cli(
                [
                    "bootstrap",
                    "aurora",
                    "--cluster",
                    cluster.strip(),
                    "--region",
                    resolved_region,
                    "--no-gui",
                ],
                target=target,
                client_id=resolved_client_id,
                profile=resolved_profile,
                region=resolved_region,
                namespace=resolved_namespace,
                config_path=resolved_config_path,
                cwd=PROJECT_ROOT,
            )
        if result.stdout:
            ccyo_out.print_text(result.stdout.rstrip())

        db_url = export_database_url_for_target(
            target=target,
            client_id=resolved_client_id,
            profile=resolved_profile,
            region=resolved_region,
            namespace=resolved_namespace,
            config_path=resolved_config_path,
        )
        ccyo_out.print_text(f"[green]DATABASE_URL[/green] resolved: [dim]{db_url}[/dim]")

        subprocess.run(
            [sys.executable, "-m", "dewey_service.db_seed"], cwd=PROJECT_ROOT, check=True
        )
        ccyo_out.success("Dewey TapDB overlay complete")
    except (TapDBRuntimeError, subprocess.CalledProcessError) as exc:
        ccyo_out.error(f"DB build failed: {exc}")
        raise typer.Exit(1) from exc


@db_app.command("seed")
def seed() -> None:
    """Apply the Dewey TapDB template overlay only."""
    try:
        subprocess.run(
            [sys.executable, "-m", "dewey_service.db_seed"], cwd=PROJECT_ROOT, check=True
        )
    except subprocess.CalledProcessError as exc:
        raise typer.Exit(exc.returncode) from exc


@db_app.command("reset")
def reset(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    cluster: str = typer.Option("", "--cluster", help="Aurora cluster ID for aurora target"),
    profile: str = typer.Option("", "--profile", help="AWS profile"),
    region: str = typer.Option("", "--region", help="AWS region"),
    namespace: str = typer.Option("", "--namespace", help="TapDB namespace"),
) -> None:
    """Delete and rebuild the TapDB target, then apply the Dewey overlay."""
    settings = get_settings()
    resolved_profile = _resolve_cli_aws_profile(profile)
    resolved_region = str(region or settings.aws_region or "").strip()
    if not resolved_region:
        raise typer.BadParameter("--region or settings.aws_region is required")
    resolved_namespace = str(namespace or settings.tapdb_database_name or "").strip()
    if not resolved_namespace:
        raise typer.BadParameter("--namespace or settings.tapdb_database_name is required")
    _delete_db_target(
        force=force,
        target=target,
        profile=resolved_profile,
        region=resolved_region,
        namespace=resolved_namespace,
        config_path=str(settings.tapdb_config_path or "").strip(),
    )

    build(
        target=target,
        cluster=cluster,
        profile=resolved_profile,
        region=resolved_region,
        namespace=resolved_namespace,
    )


@db_app.command("nuke")
def nuke(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option("", "--profile", help="AWS profile"),
    region: str = typer.Option("", "--region", help="AWS region"),
    namespace: str = typer.Option("", "--namespace", help="TapDB namespace"),
) -> None:
    """Delete the TapDB target without rebuilding."""
    settings = get_settings()
    resolved_profile = _resolve_cli_aws_profile(profile)
    resolved_region = str(region or settings.aws_region or "").strip()
    if not resolved_region:
        raise typer.BadParameter("--region or settings.aws_region is required")
    resolved_namespace = str(namespace or settings.tapdb_database_name or "").strip()
    if not resolved_namespace:
        raise typer.BadParameter("--namespace or settings.tapdb_database_name is required")
    _delete_db_target(
        force=force,
        target=target,
        profile=resolved_profile,
        region=resolved_region,
        namespace=resolved_namespace,
        config_path=str(settings.tapdb_config_path or "").strip(),
    )


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the db command group."""
    _ = spec
    register_group_commands(
        registry,
        "db",
        "TapDB lifecycle and overlay commands",
        [
            ("build", build, REQUIRED_MUTATING),
            ("seed", seed, REQUIRED_MUTATING),
            ("reset", reset, REQUIRED_MUTATING_INTERACTIVE),
            ("nuke", nuke, REQUIRED_MUTATING_INTERACTIVE),
        ],
    )
