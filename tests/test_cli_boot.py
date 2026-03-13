from __future__ import annotations

from typer.testing import CliRunner

import dewey_service.cli as cli_module
from dewey_service.cli import cli

runner = CliRunner()


def test_cli_help_renders() -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Dewey service commands" in result.stdout


def test_cli_info_renders(monkeypatch) -> None:
    monkeypatch.setenv("DEWEY_COGNITO_DOMAIN", "https://auth.example.com")
    monkeypatch.setenv("DEWEY_COGNITO_APP_CLIENT_ID", "client-1")
    monkeypatch.setenv("DEWEY_COGNITO_REDIRECT_URI", "https://localhost:8913/auth/callback")
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
    assert "Dewey Runtime" in result.stdout


def test_server_status_reports_not_running(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_get_pid", lambda _pid_file=cli_module.PID_FILE: None)
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
    monkeypatch.setattr(cli_module.time, "sleep", lambda _seconds: None)

    result = runner.invoke(cli, ["server", "restart"])

    assert result.exit_code == 0
    assert calls == [
        ("stop", None),
        (
            "start",
            {
                "host": "127.0.0.1",
                "port": 8913,
                "reload": False,
                "ssl": True,
                "background": True,
            },
        ),
    ]
