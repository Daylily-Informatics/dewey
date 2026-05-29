from __future__ import annotations

import importlib.metadata
from pathlib import Path

import pytest
from cli_core_yo import output
from cli_core_yo.app import run as run_cli

import dewey_service.cli as cli_module
import dewey_service.cli.server as server_cli
from dewey_service.defaults import (
    DEFAULT_TAPDB_CONFIG_DIR,
    DEFAULT_TAPDB_DOMAIN_REGISTRY_PATH,
    DEFAULT_TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH,
    build_default_config_template,
)
from dewey_service.settings import Settings


def _invoke(argv: list[str]) -> int:
    output._reset_console()
    return run_cli(cli_module._build_spec(), argv)


@pytest.fixture(autouse=True)
def _active_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONDA_PREFIX", "/tmp/dewey-conda")
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "DEWEY-local2")


def test_cli_help_renders(capsys) -> None:
    exit_code = _invoke(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage:" in captured.out
    assert "version" in captured.out
    assert "info" in captured.out
    assert "config" in captured.out
    assert "env" in captured.out
    assert "server" in captured.out


def test_cli_version_renders(capsys) -> None:
    exit_code = _invoke(["version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert importlib.metadata.version("dewey-service") in captured.out


def test_cli_info_renders(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: Settings(
            cognito_domain="auth.example.com",
            cognito_app_client_id="client-1",
            cognito_redirect_uri="https://localhost:8914/auth/callback",
            cognito_logout_url="https://localhost:8914/login",
        ),
    )

    exit_code = _invoke(["info"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Dewey Info" in captured.out
    assert "Database Backend" in captured.out
    assert "TapDB Namespace" in captured.out
    assert "TapDB Owner Repo" in captured.out
    assert "TapDB Domain" in captured.out


def test_server_status_reports_not_running(monkeypatch, capsys) -> None:
    monkeypatch.setattr(server_cli, "read_pid", lambda _pid_file: None)

    exit_code = _invoke(["server", "status"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not running" in captured.out


def test_server_restart_uses_background_start(monkeypatch, capsys) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        server_cli,
        "_stop_server",
        lambda: calls.append(("stop", None)),
    )
    monkeypatch.setattr(
        server_cli,
        "_start_server",
        lambda **kwargs: calls.append(("start", kwargs)),
    )
    monkeypatch.setattr(server_cli, "_validate_cognito_uris_for_port", lambda **kwargs: None)
    monkeypatch.setattr(server_cli.time, "sleep", lambda _seconds: None)

    exit_code = _invoke(["server", "restart"])
    capsys.readouterr()

    assert exit_code == 0
    assert calls == [
        ("stop", None),
        (
            "start",
            {
                "host": "127.0.0.1",
                "port": 8914,
                "reload": False,
                "background": True,
                "ssl_enabled": True,
                "cert_path": None,
                "key_path": None,
            },
        ),
    ]


def test_server_start_parses_tls_options(monkeypatch, capsys, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    cert = tmp_path / "tls-cert.pem"
    key = tmp_path / "tls-key.pem"

    monkeypatch.setattr(server_cli, "_validate_cognito_uris_for_port", lambda **kwargs: None)
    monkeypatch.setattr(server_cli, "_start_server", lambda **kwargs: calls.append(kwargs))

    exit_code = _invoke(
        [
            "server",
            "start",
            "--foreground",
            "--no-ssl",
            "--cert",
            str(cert),
            "--key",
            str(key),
        ]
    )
    capsys.readouterr()

    assert exit_code == 0
    assert calls == [
        {
            "host": "127.0.0.1",
            "port": 8914,
            "reload": False,
            "background": False,
            "ssl_enabled": False,
            "cert_path": cert,
            "key_path": key,
        }
    ]


def test_config_init_show_validate_and_status(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    init_exit = _invoke(["config", "init"])
    init_output = capsys.readouterr().out
    config_path = tmp_path / "dewey-local" / "dewey-config-local.yaml"

    assert init_exit == 0
    assert "Config file created" in init_output
    assert config_path.exists()
    config_text = config_path.read_text(encoding="utf-8")
    assert "storage:" in config_text
    assert "MERIDIAN_DOMAIN_CODE=Z" in config_text
    assert "TAPDB_OWNER_REPO=dewey" in config_text
    assert "owner_repo_name: dewey" in config_text
    assert "domain_code: Z" in config_text
    assert f"domain_registry_path: {DEFAULT_TAPDB_DOMAIN_REGISTRY_PATH}" in config_text
    assert (
        f"prefix_ownership_registry_path: {DEFAULT_TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH}"
        in config_text
    )
    assert (
        f"config_path: {DEFAULT_TAPDB_CONFIG_DIR / 'dewey' / 'dewey' / 'tapdb-config.yaml'}"
        in config_text
    )
    assert "session_secret_key: dewey-session-secret-change-me" not in config_text
    assert "allowed_email_domains:" in config_text
    assert "default_tenant_id: 00000000-0000-0000-0000-000000000000" in config_text
    assert "auto_provision_allowed_domains:" in config_text
    assert "ui:" in config_text
    assert "show_environment_chrome: true" in config_text
    assert 'profile: ""' in config_text

    show_exit = _invoke(["config", "show"])
    show_output = capsys.readouterr().out
    assert show_exit == 0
    assert "application:" in show_output
    assert "database:" in show_output
    assert "storage:" in show_output
    assert "show_environment_chrome" in show_output


def test_config_template_bytes_are_fresh() -> None:
    first = build_default_config_template()
    second = build_default_config_template()

    assert first != second
    assert b"session_secret_key: dewey-session-secret-change-me" not in first
    assert b"allowed_email_domains:" in first


def test_config_template_does_not_materialize_shell_aws_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")

    template = build_default_config_template().decode("utf-8")

    assert 'profile: ""' in template


def test_config_set_artifact_bucket(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "ci")

    init_exit = _invoke(["config", "init"])
    capsys.readouterr()
    assert init_exit == 0

    exit_code = _invoke(["config", "set-artifact-bucket", "dewey-artifacts-test"])
    captured = capsys.readouterr().out
    config_path = tmp_path / "dewey-ci" / "dewey-config-ci.yaml"

    assert exit_code == 0
    assert "Updated artifact bucket" in captured
    assert config_path.exists()
    assert "managed_bucket: dewey-artifacts-test" in config_path.read_text(encoding="utf-8")


def test_config_validate_and_status(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")

    init_exit = _invoke(["config", "init"])
    capsys.readouterr()
    assert init_exit == 0

    validate_exit = _invoke(["config", "validate"])
    validate_output = capsys.readouterr().out
    assert validate_exit == 0
    assert "Config is valid" in validate_output

    status_exit = _invoke(["config", "status"])
    status_output = capsys.readouterr().out
    assert status_exit == 0
    assert "Config path:" in status_output
    assert "dewey-config-local.yaml" in status_output.replace("\n", "")
    assert "database.namespace=dewey" in status_output
    assert "application.api_bearer_token=<redacted>" in status_output


def test_env_commands_render(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DEWEY_ACTIVE", "1")
    monkeypatch.setenv("DEWEY_PROJECT_ROOT", "/tmp/dewey")

    status_exit = _invoke(["env", "status"])
    status_output = capsys.readouterr().out
    assert status_exit == 0
    assert "active" in status_output
    assert "/tmp/dewey" in status_output

    activate_exit = _invoke(["env", "activate"])
    activate_output = capsys.readouterr().out
    assert activate_exit == 0
    assert f"source {cli_module.ACTIVATE_SCRIPT} <deploy-name>" in activate_output

    deactivate_exit = _invoke(["env", "deactivate"])
    deactivate_output = capsys.readouterr().out
    assert deactivate_exit == 0
    assert f"source {cli_module.DEACTIVATE_SCRIPT}" in deactivate_output

    reset_exit = _invoke(["env", "reset"])
    reset_output = capsys.readouterr().out
    assert reset_exit == 0
    assert f"source {cli_module.DEACTIVATE_SCRIPT}" in reset_output
    assert f"source {cli_module.ACTIVATE_SCRIPT} <deploy-name>" in reset_output
