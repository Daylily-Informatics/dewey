"""Dewey CLI, patterned after Atlas command groups."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import typer
import uvicorn
from cli_core_yo.oauth import runtime_oauth_host, validate_uri_list_ports
from cli_core_yo.server import (
    display_host,
    latest_log,
    list_logs,
    new_log_path,
    read_pid,
    stop_pid,
    write_pid,
)
from rich.console import Console

from dewey_service.integrations.tapdb_runtime import (
    DEFAULT_AWS_PROFILE,
    DEFAULT_AWS_REGION,
    DEFAULT_TAPDB_CLIENT_ID,
    DEFAULT_TAPDB_DATABASE_NAME,
    TapDBRuntimeError,
    ensure_tapdb_version,
    export_database_url_for_target,
    run_tapdb_cli,
)
from dewey_service.settings import get_settings

console = Console()
cli = typer.Typer(help="Dewey service commands")
server_app = typer.Typer(help="HTTPS API/UI server commands")
db_app = typer.Typer(help="TapDB lifecycle and Dewey overlay commands")
tapdb_app = typer.Typer(help="TapDB passthrough wrappers")
cognito_app = typer.Typer(help="Cognito helper commands")
test_app = typer.Typer(help="Test commands")
quality_app = typer.Typer(help="Quality commands")
config_app = typer.Typer(help="Config and environment inspection commands")
env_app = typer.Typer(help="Shell environment helper commands")

cli.add_typer(server_app, name="server")
cli.add_typer(db_app, name="db")
cli.add_typer(tapdb_app, name="tapdb")
cli.add_typer(cognito_app, name="cognito")
cli.add_typer(test_app, name="test")
cli.add_typer(quality_app, name="quality")
cli.add_typer(config_app, name="config")
cli.add_typer(env_app, name="env")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CERT_DIR = PROJECT_ROOT / "certs"
CERT_FILE = CERT_DIR / "cert.pem"
KEY_FILE = CERT_DIR / "key.pem"
CONFIG_DIR = Path.home() / ".config" / "dewey"
LOG_DIR = CONFIG_DIR / "logs"
PID_FILE = CONFIG_DIR / "server.pid"


def _validate_cognito_uris_for_port(port: int, host: str) -> None:
    """Warn if Cognito redirect/logout URIs don't match the runtime port."""
    try:
        settings = get_settings()
    except Exception:
        return  # Settings validation will catch errors later

    oauth_host = runtime_oauth_host(host)
    uris_to_check = [
        (settings.cognito_redirect_uri, "cognito_redirect_uri"),
        (settings.cognito_logout_url, "cognito_logout_url"),
    ]
    all_errors: list[str] = []
    for uri, label in uris_to_check:
        if not uri:
            continue
        errors = validate_uri_list_ports(
            uris=[uri],
            label=label,
            expected_port=port,
            runtime_host=oauth_host,
        )
        all_errors.extend(errors)

    if all_errors:
        console.print("[yellow]⚠[/yellow]  Cognito URI port mismatches detected:")
        for err in all_errors:
            console.print(f"   • {err}")
        console.print(f"   Server is starting on port [cyan]{port}[/cyan]")
        console.print("   Update Cognito config or use [dim]--no-check-cognito-uris[/dim] to skip\n")


def _ensure_runtime_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _start_server(
    *,
    host: str,
    port: int,
    reload: bool,
    background: bool,
) -> None:
    _ensure_runtime_dirs()

    if not CERT_FILE.exists() or not KEY_FILE.exists():
        raise typer.BadParameter(
            "HTTPS certs are missing. Create certs at certs/cert.pem and certs/key.pem"
        )

    pid = read_pid(PID_FILE)
    if pid:
        dh = display_host(host)
        console.print(f"[yellow]⚠[/yellow] Server already running (PID {pid})")
        console.print(f"   URL: [cyan]https://{dh}:{port}[/cyan]")
        return

    if background:
        python = shutil.which("python") or sys.executable
        cmd = [
            python,
            "-m",
            "uvicorn",
            "dewey_service.app:create_app",
            "--factory",
            "--host",
            host,
            "--port",
            str(port),
        ]
        if reload:
            cmd.append("--reload")
        cmd.extend(["--ssl-certfile", str(CERT_FILE), "--ssl-keyfile", str(KEY_FILE)])

        log_file = new_log_path(LOG_DIR)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        with open(log_file, "w", buffering=1) as log_f:
            proc = subprocess.Popen(
                cmd,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                cwd=PROJECT_ROOT,
                env=env,
            )

        time.sleep(2)
        if proc.poll() is not None:
            console.print("[red]✗[/red] Server failed to start. Check logs:")
            console.print(f"   [dim]{log_file}[/dim]")
            raise typer.Exit(1)

        write_pid(PID_FILE, proc.pid)
        dh = display_host(host)
        console.print(f"[green]✓[/green] Server started (PID {proc.pid})")
        console.print(f"   URL: [cyan]https://{dh}:{port}[/cyan]")
        console.print(f"   Logs: [dim]{log_file}[/dim]")
        return

    uvicorn_kwargs = {
        "app": "dewey_service.app:create_app",
        "factory": True,
        "host": host,
        "port": port,
        "reload": reload,
        "ssl_certfile": str(CERT_FILE),
        "ssl_keyfile": str(KEY_FILE),
    }
    uvicorn.run(**uvicorn_kwargs)


def _stop_server(pid_file: Path = PID_FILE) -> None:
    stopped, msg = stop_pid(pid_file)
    if stopped:
        console.print(f"[green]✓[/green] {msg}")
    elif "Permission" in msg:
        console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)
    else:
        console.print(f"[yellow]⚠[/yellow] {msg}")


@cli.command("info")
def info() -> None:
    """Show runtime info."""
    settings = get_settings()
    console.print("[bold]Dewey Runtime[/bold]")
    console.print(f"backend: [cyan]{settings.database_backend}[/cyan]")
    console.print(f"target: [cyan]{settings.database_target}[/cyan]")
    console.print(f"tapdb client: [cyan]{settings.tapdb_client_id}[/cyan]")
    console.print(f"tapdb namespace: [cyan]{settings.tapdb_database_name}[/cyan]")
    console.print(f"tapdb env: [cyan]{settings.tapdb_env}[/cyan]")
    console.print(f"host: [cyan]{settings.host}[/cyan]")
    console.print(f"port: [cyan]{settings.port}[/cyan]")


@server_app.command("start")
def server_start(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8914, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload/--no-reload", help="Enable autoreload"),
    background: bool = typer.Option(
        True,
        "--background/--foreground",
        help="Run in background (default)",
    ),
    check_cognito_uris: bool = typer.Option(
        True,
        "--check-cognito-uris/--no-check-cognito-uris",
        help="Validate Cognito callback/logout URI ports before startup",
    ),
) -> None:
    """Start Dewey API/UI server over HTTPS."""
    # Allow env vars to override CLI defaults (same pattern as Ursa)
    port = int(os.environ.get("DEWEY_PORT", port))
    host = os.environ.get("DEWEY_HOST", host)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=port, host=host)
    _start_server(host=host, port=port, reload=reload, background=background)


@server_app.command("stop")
def server_stop() -> None:
    """Stop the Dewey API/UI server."""
    _stop_server()


@server_app.command("status")
def server_status() -> None:
    """Show Dewey API/UI server status."""
    pid = read_pid(PID_FILE)
    if pid:
        port = os.environ.get("DEWEY_RUNTIME__PORT", "8914")
        host = os.environ.get("DEWEY_RUNTIME__HOST", "0.0.0.0")
        dh = display_host(host)
        log_file = latest_log(LOG_DIR)
        console.print(f"[green]●[/green] Server is [green]running[/green] (PID {pid})")
        console.print(f"   URL: [cyan]https://{dh}:{port}[/cyan]")
        if log_file:
            console.print(f"   Logs: [dim]{log_file}[/dim]")
        return
    console.print("[dim]○[/dim] Server is [dim]not running[/dim]")


@server_app.command("logs")
def server_logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    all_logs: bool = typer.Option(False, "--all", "-a", help="List all log files"),
) -> None:
    """View and follow server logs (Ctrl+C to stop)."""
    _ensure_runtime_dirs()

    if all_logs:
        log_entries = list_logs(LOG_DIR)
        if not log_entries:
            console.print("[yellow]⚠[/yellow] No log files found.")
            return
        console.print(f"[bold]Server log files ({len(log_entries)}):[/bold]")
        for lf in log_entries[:20]:
            size = lf.stat().st_size
            console.print(f"  {lf.name}  [dim]({size:,} bytes)[/dim]")
        return

    log_file = latest_log(LOG_DIR)
    if not log_file:
        console.print("[yellow]⚠[/yellow] No log file found. Start the server first.")
        return

    console.print(f"[dim]Following {log_file.name} (Ctrl+C to stop)[/dim]\n")
    try:
        subprocess.run(["tail", "-f", "-n", str(lines), str(log_file)])
    except KeyboardInterrupt:
        console.print("\n")



@server_app.command("restart")
def server_restart(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8914, "--port", "-p", help="Port to bind"),
    check_cognito_uris: bool = typer.Option(
        True,
        "--check-cognito-uris/--no-check-cognito-uris",
        help="Validate Cognito callback/logout URI ports before startup",
    ),
) -> None:
    """Restart the Dewey API/UI server in background mode over HTTPS."""
    # Allow env vars to override CLI defaults (same pattern as Ursa)
    port = int(os.environ.get("DEWEY_PORT", port))
    host = os.environ.get("DEWEY_HOST", host)
    _stop_server()
    time.sleep(1)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=port, host=host)
    _start_server(host=host, port=port, reload=False, background=True)


@db_app.command("build")
def db_build(
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    cluster: str = typer.Option("", "--cluster", help="Aurora cluster ID for aurora target"),
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Bootstrap TapDB runtime and apply Dewey overlay."""
    ensure_tapdb_version()
    try:
        if target == "local":
            result = run_tapdb_cli(
                ["bootstrap", "local", "--no-gui"],
                target=target,
                client_id=DEFAULT_TAPDB_CLIENT_ID,
                profile=profile,
                region=region,
                namespace=namespace,
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
                profile=profile,
                region=region,
                namespace=namespace,
                cwd=PROJECT_ROOT,
            )
        if result.stdout:
            console.print(result.stdout.rstrip())
        db_url = export_database_url_for_target(
            target=target,
            client_id=DEFAULT_TAPDB_CLIENT_ID,
            profile=profile,
            region=region,
            namespace=namespace,
        )
        console.print(f"[green]DATABASE_URL[/green] resolved: [dim]{db_url}[/dim]")

        # Overlay step: bootstrap Dewey templates through app service.
        subprocess.run(
            [sys.executable, "-m", "dewey_service.db_seed"], cwd=PROJECT_ROOT, check=True
        )
        console.print("[green]Dewey TapDB overlay complete[/green]")
    except (TapDBRuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]DB build failed:[/red] {exc}")
        raise typer.Exit(1) from exc


@db_app.command("seed")
def db_seed() -> None:
    """Apply Dewey TapDB template overlay only."""
    try:
        subprocess.run(
            [sys.executable, "-m", "dewey_service.db_seed"], cwd=PROJECT_ROOT, check=True
        )
    except subprocess.CalledProcessError as exc:
        raise typer.Exit(exc.returncode) from exc


@db_app.command("reset")
def db_reset(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Delete and rebuild TapDB target then apply Dewey overlay."""
    if not force and not typer.confirm("This will delete the current TapDB DB target. Continue?"):
        raise typer.Exit(0)
    try:
        tapdb_env = "dev" if target == "local" else "prod"
        run_tapdb_cli(
            ["db", "delete", tapdb_env, "--force"],
            target=target,
            client_id=DEFAULT_TAPDB_CLIENT_ID,
            profile=profile,
            region=region,
            namespace=namespace,
            cwd=PROJECT_ROOT,
        )
    except TapDBRuntimeError as exc:
        console.print(f"[red]Delete failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    db_build(target=target, profile=profile, region=region, namespace=namespace)


@tapdb_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def tapdb_run(
    ctx: typer.Context,
    target: str = typer.Option("local", "--target", help="TapDB target: local|aurora"),
    profile: str = typer.Option(DEFAULT_AWS_PROFILE, "--profile", help="AWS profile"),
    region: str = typer.Option(DEFAULT_AWS_REGION, "--region", help="AWS region"),
    namespace: str = typer.Option(
        DEFAULT_TAPDB_DATABASE_NAME, "--namespace", help="TapDB namespace"
    ),
) -> None:
    """Run raw tapdb CLI arguments through Dewey runtime context."""
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
        console.print(f"[red]TapDB invocation failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    if result.stdout:
        console.print(result.stdout.rstrip())
    if result.stderr:
        console.print(result.stderr.rstrip(), style="yellow")
    raise typer.Exit(result.returncode)


@cognito_app.command("status")
def cognito_status() -> None:
    """Show daycog status for Dewey runtime."""
    daycog_path = shutil.which("daycog")
    if not daycog_path:
        console.print("[red]daycog not found in PATH[/red]")
        raise typer.Exit(1)
    try:
        proc = subprocess.run(
            [daycog_path, "status"],
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
    except FileNotFoundError as exc:
        console.print("[red]daycog not found in PATH[/red]")
        raise typer.Exit(1) from exc

    if proc.stdout:
        console.print(proc.stdout.rstrip())
    if proc.stderr:
        console.print(proc.stderr.rstrip(), style="yellow")
    raise typer.Exit(proc.returncode)


@test_app.command("run")
def test_run(
    pytest_args: list[str] = typer.Argument(
        None,
        help="Optional pytest arguments, e.g. tests/test_app_boot.py -q",
    ),
) -> None:
    """Run Dewey tests."""
    args = list(pytest_args or ["-q"])
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=PROJECT_ROOT,
        check=False,
    )
    raise typer.Exit(proc.returncode)


@quality_app.command("lint")
def quality_lint() -> None:
    """Run Ruff lint checks."""
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=PROJECT_ROOT, check=False
    )
    raise typer.Exit(proc.returncode)


@quality_app.command("format")
def quality_format(
    check: bool = typer.Option(True, "--check/--fix", help="Check or apply formatting"),
) -> None:
    """Run Ruff formatter."""
    cmd = [sys.executable, "-m", "ruff", "format", "."]
    if check:
        cmd.append("--check")
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    raise typer.Exit(proc.returncode)


@quality_app.command("check")
def quality_check() -> None:
    """Run lint then tests."""
    lint = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=PROJECT_ROOT, check=False
    )
    if lint.returncode != 0:
        raise typer.Exit(lint.returncode)
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=PROJECT_ROOT, check=False)
    raise typer.Exit(tests.returncode)


@config_app.command("path")
def config_path() -> None:
    """Print resolved Dewey config paths."""
    settings = get_settings()
    console.print(
        f"DEWEY config path: [cyan]{os.environ.get('XDG_CONFIG_HOME', '~/.config')}/dewey/config.yaml[/cyan]"
    )
    console.print(
        f"TAPDB config path: [cyan]{settings.tapdb_config_path or os.environ.get('TAPDB_CONFIG_PATH', '')}[/cyan]"
    )


@config_app.command("show")
def config_show() -> None:
    """Show loaded runtime settings."""
    settings = get_settings()
    console.print(settings.model_dump_json(indent=2))


@config_app.command("validate")
def config_validate() -> None:
    """Validate runtime settings load."""
    get_settings()
    console.print("[green]Configuration is valid[/green]")


@env_app.command("status")
def env_status() -> None:
    """Show key Dewey shell environment values."""
    keys = [
        "DATABASE_BACKEND",
        "DATABASE_TARGET",
        "TAPDB_CLIENT_ID",
        "TAPDB_DATABASE_NAME",
        "TAPDB_ENV",
        "TAPDB_STRICT_NAMESPACE",
        "TAPDB_CONFIG_PATH",
        "AWS_PROFILE",
        "AWS_REGION",
    ]
    for key in keys:
        console.print(f"{key}={os.environ.get(key, '')}")


@env_app.command("activate")
def env_activate() -> None:
    """Print activation command for this shell."""
    console.print("Run: [cyan]source dewey_activate[/cyan]")


@env_app.command("deactivate")
def env_deactivate() -> None:
    """Print deactivation command for this shell."""
    console.print("Run: [cyan]dewey_deactivate[/cyan]")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
