from __future__ import annotations

from typer.testing import CliRunner

import dewey_service.cli as cli_module
from dewey_service.cli import cli
from dewey_service.settings import Settings

runner = CliRunner()


def test_cli_help_renders() -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Dewey service commands" in result.stdout


def test_cli_info_renders(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: Settings(
            cognito_domain="https://auth.example.com",
            cognito_app_client_id="client-1",
            cognito_redirect_uri="https://localhost:8914/auth/callback",
            cognito_logout_url="https://localhost:8914/login",
        ),
    )
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
    assert "Dewey Runtime" in result.stdout


def test_server_status_reports_not_running(monkeypatch) -> None:
    from cli_core_yo import server as server_mod

    monkeypatch.setattr(server_mod, "read_pid", lambda _pid_file: None)
    result = runner.invoke(cli, ["server", "status"])
    assert result.exit_code == 0
    assert "not running" in result.stdout


def test_server_restart_uses_background_start(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        cli_module,
        "_stop_server",
        lambda _pid_file=cli_module.PID_FILE: calls.append(("stop", None)),
    )
    monkeypatch.setattr(
        cli_module,
        "_start_server",
        lambda **kwargs: calls.append(("start", kwargs)),
    )
    monkeypatch.setattr(cli_module, "_validate_cognito_uris_for_port", lambda **kwargs: None)
    monkeypatch.setattr(cli_module.time, "sleep", lambda _seconds: None)

    result = runner.invoke(cli, ["server", "restart"])

    assert result.exit_code == 0
    assert calls == [
        ("stop", None),
        (
            "start",
            {
                "host": "0.0.0.0",
                "port": 8914,
                "reload": False,
                "background": True,
            },
        ),
    ]
