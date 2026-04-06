"""HTTPS API/UI server management for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import typer
import uvicorn
from cli_core_yo import ccyo_out
from cli_core_yo.certs import ensure_certs
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
from typer.models import OptionInfo

from dewey_service.cli.common import PROJECT_ROOT
from dewey_service.defaults import DEFAULT_APP_PORT
from dewey_service.settings import clear_settings_cache, get_settings

server_app = typer.Typer(help="HTTPS API/UI server commands")

CERT_DIR = PROJECT_ROOT / "certs"
CERT_FILE = CERT_DIR / "cert.pem"
KEY_FILE = CERT_DIR / "key.pem"
GENERIC_CERT_ENV = "SSL_CERT_FILE"
GENERIC_KEY_ENV = "SSL_KEY_FILE"
DEFAULT_BIND_HOST = "127.0.0.1"
NCBI_API_KEY_FILE = Path("~/.config/ncbi/key.txt").expanduser()


def _state_dir() -> Path:
    from cli_core_yo.runtime import get_context

    return get_context().xdg_paths.state


def _log_dir() -> Path:
    return _state_dir() / "logs"


def _pid_file() -> Path:
    return _state_dir() / "server.pid"


def _runtime_meta_file() -> Path:
    return _state_dir() / "server-meta.json"


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
        ccyo_out.error(f"Configuration invalid: {exc}")
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

    ccyo_out.warning("Cognito URI port mismatches detected:")
    for err in errors:
        ccyo_out.bullet(f"   • {err}")
    ccyo_out.print_text(f"   Server is starting on port [cyan]{port}[/cyan]")
    ccyo_out.print_text("   Update Cognito config or use [dim]--no-check-cognito-uris[/dim] to skip\n")


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


def _normalize_option_default(value, fallback):
    if isinstance(value, OptionInfo):
        return fallback
    return value


def _maybe_set_ncbi_api_key() -> None:
    if os.environ.get("NCBI_API_KEY", "").strip():
        return
    try:
        key = NCBI_API_KEY_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return
    except OSError:
        return
    if key:
        os.environ["NCBI_API_KEY"] = key


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


def _resolve_deployment_code() -> str:
    return (
        os.environ.get("DEWEY_DEPLOYMENT_CODE", "").strip()
        or os.environ.get("DEPLOYMENT_CODE", "").strip()
        or os.environ.get("LSMC_DEPLOYMENT_CODE", "").strip()
        or "local"
    )


def _state_home() -> Path:
    raw = os.environ.get("XDG_STATE_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".local" / "state"


def _shared_cert_dir() -> Path:
    return _state_home() / "dayhoff" / _resolve_deployment_code() / "certs"


def _resolve_tls_pair_from_paths(
    cert_path: Path | None,
    key_path: Path | None,
    *,
    source: str,
) -> tuple[Path, Path] | None:
    if cert_path is None and key_path is None:
        return None
    if cert_path is None or key_path is None:
        raise typer.BadParameter(f"{source} requires both a cert path and a key path")
    cert_resolved = cert_path.expanduser()
    key_resolved = key_path.expanduser()
    if not cert_resolved.exists():
        raise typer.BadParameter(f"{source} cert file does not exist: {cert_resolved}")
    if not key_resolved.exists():
        raise typer.BadParameter(f"{source} key file does not exist: {key_resolved}")
    return cert_resolved, key_resolved


def _resolve_tls_pair_from_env(
    *,
    cert_env: str,
    key_env: str,
    source: str,
) -> tuple[Path, Path] | None:
    cert_raw = os.environ.get(cert_env, "").strip()
    key_raw = os.environ.get(key_env, "").strip()
    cert_path = Path(cert_raw) if cert_raw else None
    key_path = Path(key_raw) if key_raw else None
    return _resolve_tls_pair_from_paths(cert_path, key_path, source=source)


def _resolve_tls_material(
    *,
    ssl_enabled: bool,
    cert_path: Path | None,
    key_path: Path | None,
) -> tuple[Path | None, Path | None]:
    if not ssl_enabled:
        return None, None

    explicit = _resolve_tls_pair_from_paths(cert_path, key_path, source="CLI flags")
    if explicit is not None:
        return explicit

    generic = _resolve_tls_pair_from_env(
        cert_env=GENERIC_CERT_ENV,
        key_env=GENERIC_KEY_ENV,
        source="environment variables SSL_CERT_FILE/SSL_KEY_FILE",
    )
    if generic is not None:
        return generic

    shared_cert = _shared_cert_dir() / "cert.pem"
    shared_key = _shared_cert_dir() / "key.pem"
    if shared_cert.exists() and shared_key.exists():
        return shared_cert, shared_key

    if CERT_FILE.exists() and KEY_FILE.exists():
        return CERT_FILE, KEY_FILE

    try:
        return ensure_certs(_shared_cert_dir())
    except SystemExit as exc:
        raise typer.BadParameter(str(exc)) from exc


def _write_runtime_meta(*, ssl_enabled: bool) -> None:
    _runtime_meta_file().write_text(
        json.dumps({"ssl_enabled": ssl_enabled}, sort_keys=True),
        encoding="utf-8",
    )


def _clear_runtime_meta() -> None:
    _runtime_meta_file().unlink(missing_ok=True)


def _status_scheme() -> str:
    meta_file = _runtime_meta_file()
    if not meta_file.exists():
        return "https"
    try:
        payload = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return "https"
    return "https" if payload.get("ssl_enabled", True) else "http"


def _start_server(
    *,
    host: str,
    port: int,
    reload: bool,
    background: bool,
    ssl_enabled: bool,
    cert_path: Path | None,
    key_path: Path | None,
) -> None:
    _ensure_runtime_dirs()
    resolved_cert, resolved_key = _resolve_tls_material(
        ssl_enabled=ssl_enabled,
        cert_path=cert_path,
        key_path=key_path,
    )
    scheme = "https" if ssl_enabled else "http"

    pid = read_pid(_pid_file())
    if pid:
        ccyo_out.warning(f"Server already running (PID {pid})")
        ccyo_out.print_text(f"   URL: [cyan]{scheme}://{display_host(host)}:{port}[/cyan]")
        return

    _maybe_set_ncbi_api_key()

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
        if ssl_enabled:
            cmd.extend(
                [
                    "--ssl-certfile",
                    str(resolved_cert),
                    "--ssl-keyfile",
                    str(resolved_key),
                ]
            )
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
            ccyo_out.error("Server failed to start. Check logs:")
            ccyo_out.print_text(f"   [dim]{log_file}[/dim]")
            raise typer.Exit(1)

        write_pid(_pid_file(), proc.pid)
        _write_runtime_meta(ssl_enabled=ssl_enabled)
        ccyo_out.success(f"Server started (PID {proc.pid})")
        ccyo_out.print_text(f"   URL: [cyan]{scheme}://{display_host(host)}:{port}[/cyan]")
        ccyo_out.print_text(f"   Logs: [dim]{log_file}[/dim]")
        return

    uvicorn_kwargs: dict[str, object] = {
        "app": "dewey_service.app:create_app",
        "factory": True,
        "host": host,
        "port": port,
        "reload": reload,
    }
    if ssl_enabled:
        uvicorn_kwargs["ssl_certfile"] = str(resolved_cert)
        uvicorn_kwargs["ssl_keyfile"] = str(resolved_key)
    uvicorn.run(**uvicorn_kwargs)


def _stop_server() -> None:
    stopped, msg = stop_pid(_pid_file())
    if stopped:
        _clear_runtime_meta()
        ccyo_out.success(f"{msg}")
        return
    if "Permission" in msg:
        ccyo_out.error(f"{msg}")
        raise typer.Exit(1)
    ccyo_out.warning(f"{msg}")


@server_app.command("start")
def start(
    host: str = typer.Option(DEFAULT_BIND_HOST, "--host", help="Host to bind"),
    port: int = typer.Option(DEFAULT_APP_PORT, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload/--no-reload", help="Enable autoreload"),
    ssl_enabled: bool = typer.Option(True, "--ssl/--no-ssl", help="Serve over HTTPS"),
    cert: Path | None = typer.Option(None, "--cert", help="Path to TLS certificate PEM"),
    key: Path | None = typer.Option(None, "--key", help="Path to TLS private key PEM"),
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
    """Start the Dewey API/UI server."""
    ssl_enabled = _normalize_option_default(ssl_enabled, True)
    cert = _normalize_option_default(cert, None)
    key = _normalize_option_default(key, None)
    resolved_host = _resolve_host(host)
    resolved_port = _resolve_port(port)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=resolved_port, host=resolved_host)
    _start_server(
        host=resolved_host,
        port=resolved_port,
        reload=reload,
        background=background,
        ssl_enabled=ssl_enabled,
        cert_path=cert,
        key_path=key,
    )


@server_app.command("stop")
def stop() -> None:
    """Stop the Dewey API/UI server."""
    _stop_server()


@server_app.command("status")
def status() -> None:
    """Show Dewey API/UI server status."""
    pid = read_pid(_pid_file())
    if not pid:
        ccyo_out.print_text("Server is [dim]not running[/dim]")
        return

    host, port = _status_bind()
    log_file = latest_log(_log_dir())
    ccyo_out.success(f"Server is running (PID {pid})")
    ccyo_out.print_text(f"   URL: [cyan]{_status_scheme()}://{host}:{port}[/cyan]")
    if log_file:
        ccyo_out.print_text(f"   Logs: [dim]{log_file}[/dim]")


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
            ccyo_out.warning("No log files found.")
            return
        ccyo_out.print_text(f"[bold]Server log files ({len(entries)}):[/bold]")
        for entry in entries:
            ccyo_out.print_text(f"  {entry.name}  [dim]({entry.stat().st_size:,} bytes)[/dim]")
        return

    log_file = latest_log(_log_dir())
    if not log_file:
        ccyo_out.warning("No log file found. Start the server first.")
        return

    ccyo_out.print_text(f"[dim]Following {log_file.name} (Ctrl+C to stop)[/dim]\n")
    try:
        tail_follow(log_file, lines=lines)
    except KeyboardInterrupt:
        ccyo_out.print_text("")


@server_app.command("restart")
def restart(
    host: str = typer.Option(DEFAULT_BIND_HOST, "--host", help="Host to bind"),
    port: int = typer.Option(DEFAULT_APP_PORT, "--port", "-p", help="Port to bind"),
    ssl_enabled: bool = typer.Option(True, "--ssl/--no-ssl", help="Serve over HTTPS"),
    cert: Path | None = typer.Option(None, "--cert", help="Path to TLS certificate PEM"),
    key: Path | None = typer.Option(None, "--key", help="Path to TLS private key PEM"),
    check_cognito_uris: bool = typer.Option(
        True,
        "--check-cognito-uris/--no-check-cognito-uris",
        help="Validate Cognito callback/logout URI ports before startup",
    ),
) -> None:
    """Restart the Dewey API/UI server in background mode."""
    ssl_enabled = _normalize_option_default(ssl_enabled, True)
    cert = _normalize_option_default(cert, None)
    key = _normalize_option_default(key, None)
    resolved_host = _resolve_host(host)
    resolved_port = _resolve_port(port)
    _stop_server()
    time.sleep(1)
    if check_cognito_uris:
        _validate_cognito_uris_for_port(port=resolved_port, host=resolved_host)
    _start_server(
        host=resolved_host,
        port=resolved_port,
        reload=False,
        background=True,
        ssl_enabled=ssl_enabled,
        cert_path=cert,
        key_path=key,
    )


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register the server command group."""
    registry.add_typer_app(None, server_app, "server", "HTTPS API/UI server commands")
