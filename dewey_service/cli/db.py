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
    DEFAULT_AWS_PROFILE,
    DEFAULT_AWS_REGION,
    DEFAULT_TAPDB_CLIENT_ID,
    DEFAULT_TAPDB_DATABASE_NAME,
    TapDBRuntimeError,
    ensure_tapdb_version,
    export_database_url_for_target,
    run_tapdb_cli,
    tapdb_env_for_target,
)
from dewey_service.settings import load_config_aws_profile

db_app = typer.Typer(help="TapDB lifecycle and Dewey overlay commands")


def _resolve_cli_aws_profile(profile: str) -> str:
    resolved_profile = resolve_aws_profile(
        cli_profile=profile,
        config_profile=load_config_aws_profile(),
    )
    if resolved_profile:
        return resolved_profile
    raise TapDBRuntimeError(AWS_PROFILE_REQUIRED_MESSAGE)


def _confirm_db_delete(force: bool) -> bool:
    if force:
        return True
    return typer.confirm("This will delete the current TapDB DB target. Continue?")


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
        run_tapdb_cli(
            ["db", "delete", tapdb_env_for_target(target), "--force"],
            target=target,
            client_id=DEFAULT_TAPDB_CLIENT_ID,
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
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Bootstrap TapDB runtime and apply the Dewey overlay."""
    ensure_tapdb_version()
    try:
        settings = get_settings()
        resolved_config_path = str(settings.tapdb_config_path or "").strip()
        resolved_profile = _resolve_cli_aws_profile(profile)
        if target == "local":
            result = run_tapdb_cli(
                ["bootstrap", "local", "--no-gui"],
                target=target,
                client_id=DEFAULT_TAPDB_CLIENT_ID,
                profile=resolved_profile,
                region=region,
                namespace=namespace,
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
                    region,
                    "--no-gui",
                ],
                target=target,
                client_id=DEFAULT_TAPDB_CLIENT_ID,
                profile=resolved_profile,
                region=region,
                namespace=namespace,
                config_path=resolved_config_path,
                cwd=PROJECT_ROOT,
            )
        if result.stdout:
            ccyo_out.print_text(result.stdout.rstrip())

        db_url = export_database_url_for_target(
            target=target,
            client_id=DEFAULT_TAPDB_CLIENT_ID,
            profile=resolved_profile,
            region=region,
            namespace=namespace,
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
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Delete and rebuild the TapDB target, then apply the Dewey overlay."""
    resolved_profile = _resolve_cli_aws_profile(profile)
    _delete_db_target(
        force=force,
        target=target,
        profile=resolved_profile,
        region=region,
        namespace=namespace,
        config_path=str(get_settings().tapdb_config_path or "").strip(),
    )

    build(
        target=target,
        cluster=cluster,
        profile=resolved_profile,
        region=region,
        namespace=namespace,
    )


@db_app.command("nuke")
def nuke(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Delete the TapDB target without rebuilding."""
    resolved_profile = _resolve_cli_aws_profile(profile)
    _delete_db_target(
        force=force,
        target=target,
        profile=resolved_profile,
        region=region,
        namespace=namespace,
        config_path=str(get_settings().tapdb_config_path or "").strip(),
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
