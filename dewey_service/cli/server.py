"""HTTPS API/UI server management for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

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
    tail_follow,
    write_pid,
)

from dewey_service.cli.common import PROJECT_ROOT, console
from dewey_service.settings import clear_settings_cache, get_settings

server_app = typer.Typer(help="HTTPS API/UI server commands")

CERT_DIR = PROJECT_ROOT / "certs"
CERT_FILE = CERT_DIR / "cert.pem"
KEY_FILE = CERT_DIR / "key.pem"


def _state_dir() -> Path:
    from cli_core_yo.runtime import get_context

    return get_context().xdg_paths.state


def _log_dir() -> Path:
    return _state_dir() / "logs"


def _pid_file() -> Path:
    return _state_dir() / "server.pid"


def _ensure_runtime_dirs() -> None:
    _state_dir().mkdir(parents=True, exist_ok=True)
    _log_dir().mkdir(parents=True, exist_ok=True)


def _load_settings():
    clear_settings_cache()
    return get_settings()


def _validate_cognito_uris_for_port(port: int, host: str) -> None:
    """Warn when Cognito callback/logout URIs do not match the runtime port."""
    try:
        settings = _load_settings()
    except Exception as exc:
        console.print(f"[red]✗[/red] Configuration invalid: {exc}")
        raise typer.Exit(1) from exc

    oauth_host = runtime_oauth_host(host)
    uris_to_check = [
        (settings.cognito_redirect_uri, "cognito_redirect_uri"),
        (settings.cognito_logout_url, "cognito_logout_url"),
    ]
    errors: list[str] = []
    for uri, label in uris_to_check:
        if not uri:
            continue
        errors.extend(
            validate_uri_list_ports(
                uris=[uri],
                label=label,
                expected_port=port,
                runtime_host=oauth_host,
            )
        )

    if not errors:
        return

    console.print("[yellow]⚠[/yellow] Cognito URI port mismatches detected:")
    for err in errors:
        console.print(f"   • {err}")
    console.print(f"   Server is starting on port [cyan]{port}[/cyan]")
    console.print("   Update Cognito config or use [dim]--no-check-cognito-uris[/dim] to skip\n")


def _resolve_port(value: int) -> int:
    raw = os.environ.get("DEWEY_PORT", "").strip()
    if not raw:
        return value
    try:
        return int(raw)
    except ValueError as exc:
        raise typer.BadParameter("DEWEY_PORT must be an integer") from exc


def _resolve_host(value: str) -> str:
    return os.environ.get("DEWEY_HOST", "").strip() or value


def _status_bind() -> tuple[str, str]:
    host = os.environ.get("DEWEY_HOST", "").strip()
    port = os.environ.get("DEWEY_PORT", "").strip()
    if host and port:
        return display_host(host), port

    try:
        settings = _load_settings()
    except Exception:
        resolved_host = display_host(host) if host else "unknown"
        resolved_port = port or "unknown"
        return resolved_host, resolved_port

    resolved_host = display_host(host or settings.host)
    resolved_port = port or str(settings.port)
    return resolved_host, resolved_port


def _start_server(*, host: str, port: int, reload: bool, background: bool) -> None:
    _ensure_runtime_dirs()

    if not CERT_FILE.exists() or not KEY_FILE.exists():
        raise typer.BadParameter(
            "HTTPS certs are missing. Create certs at certs/cert.pem and certs/key.pem"
        )

    pid = read_pid(_pid_file())
    if pid:
        console.print(f"[yellow]⚠[/yellow] Server already running (PID {pid})")
        console.print(f"   URL: [cyan]https://{display_host(host)}:{port}[/cyan]")
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
            "--ssl-certfile",
            str(CERT_FILE),
            "--ssl-keyfile",
            str(KEY_FILE),
        ]
        if reload:
            cmd.append("--reload")

        log_file = new_log_path(_log_dir())
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

        write_pid(_pid_file(), proc.pid)
        console.print(f"[green]✓[/green] Server started (PID {proc.pid})")
        console.print(f"   URL: [cyan]https://{display_host(host)}:{port}[/cyan]")
        console.print(f"   Logs: [dim]{log_file}[/dim]")
        return

    uvicorn.run(
        app="dewey_service.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        ssl_certfile=str(CERT_FILE),
        ssl_keyfile=str(KEY_FILE),
    )


def _stop_server() -> None:
    stopped, msg = stop_pid(_pid_file())
    if stopped:
        console.print(f"[green]✓[/green] {msg}")
        return
    if "Permission" in msg:
        console.print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)
    console.print(f"[yellow]⚠[/yellow] {msg}")


@server_app.command("start")
def start(
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
    """Start the Dewey API/UI server over HTTPS."""
    resolved_host = _resolve_host(host)
    resolved_port = _resolve_port(port)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=resolved_port, host=resolved_host)
    _start_server(host=resolved_host, port=resolved_port, reload=reload, background=background)


@server_app.command("stop")
def stop() -> None:
    """Stop the Dewey API/UI server."""
    _stop_server()


@server_app.command("status")
def status() -> None:
    """Show Dewey API/UI server status."""
    pid = read_pid(_pid_file())
    if not pid:
        console.print("[dim]○[/dim] Server is [dim]not running[/dim]")
        return

    host, port = _status_bind()
    log_file = latest_log(_log_dir())
    console.print(f"[green]●[/green] Server is [green]running[/green] (PID {pid})")
    console.print(f"   URL: [cyan]https://{host}:{port}[/cyan]")
    if log_file:
        console.print(f"   Logs: [dim]{log_file}[/dim]")


@server_app.command("logs")
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    all_logs: bool = typer.Option(False, "--all", "-a", help="List all log files"),
) -> None:
    """View and follow server logs."""
    _ensure_runtime_dirs()

    if all_logs:
        entries = list_logs(_log_dir())
        if not entries:
            console.print("[yellow]⚠[/yellow] No log files found.")
            return
        console.print(f"[bold]Server log files ({len(entries)}):[/bold]")
        for entry in entries:
            console.print(f"  {entry.name}  [dim]({entry.stat().st_size:,} bytes)[/dim]")
        return

    log_file = latest_log(_log_dir())
    if not log_file:
        console.print("[yellow]⚠[/yellow] No log file found. Start the server first.")
        return

    console.print(f"[dim]Following {log_file.name} (Ctrl+C to stop)[/dim]\n")
    try:
        tail_follow(log_file, lines=lines)
    except KeyboardInterrupt:
        console.print()


@server_app.command("restart")
def restart(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8914, "--port", "-p", help="Port to bind"),
    check_cognito_uris: bool = typer.Option(
        True,
        "--check-cognito-uris/--no-check-cognito-uris",
        help="Validate Cognito callback/logout URI ports before startup",
    ),
) -> None:
    """Restart the Dewey API/UI server in background mode over HTTPS."""
    resolved_host = _resolve_host(host)
    resolved_port = _resolve_port(port)
    _stop_server()
    time.sleep(1)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=resolved_port, host=resolved_host)
    _start_server(host=resolved_host, port=resolved_port, reload=False, background=True)


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the server command group."""
    registry.add_typer_app(None, server_app, "server", "HTTPS API/UI server commands")
