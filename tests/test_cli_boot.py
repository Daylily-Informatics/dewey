from __future__ import annotations

from typer.testing import CliRunner

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
