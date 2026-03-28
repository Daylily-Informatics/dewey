from __future__ import annotations

from types import SimpleNamespace

import pytest

from dewey_service.integrations import tapdb_runtime


def test_ensure_tapdb_version_accepts_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", lambda _name: "3.0.2")
    assert tapdb_runtime.ensure_tapdb_version("3.0.2") == "3.0.2"


def test_ensure_tapdb_version_rejects_lower_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", lambda _name: "3.0.1")
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="version mismatch"):
        tapdb_runtime.ensure_tapdb_version("3.0.2")


def test_tapdb_env_for_target_and_sqlalchemy_url() -> None:
    assert tapdb_runtime.tapdb_env_for_target("local") == "dev"
    assert tapdb_runtime.tapdb_env_for_target("aurora") == "prod"
    assert tapdb_runtime._build_sqlalchemy_url(
        {"user": "alice", "password": "secret", "host": "db", "port": "5432", "database": "dewey"}
    ) == "postgresql+psycopg2://alice:secret@db:5432/dewey"

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="Unsupported database target"):
        tapdb_runtime.tapdb_env_for_target("staging")


def test_resolve_tapdb_config_path_prefers_explicit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAPDB_CONFIG_PATH", "/tmp/custom-tapdb.yaml")
    assert tapdb_runtime._resolve_tapdb_config_path(namespace="ignored", client_id="ignored") == "/tmp/custom-tapdb.yaml"


def test_resolve_runtime_env_sets_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAPDB_CONFIG_PATH", raising=False)
    env = tapdb_runtime._resolve_runtime_env(
        target="local",
        client_id="dewey",
        profile="lsmc",
        region="us-west-2",
        namespace="dewey",
    )

    assert env["AWS_PROFILE"] == "lsmc"
    assert env["AWS_REGION"] == "us-west-2"
    assert env["TAPDB_CLIENT_ID"] == "dewey"
    assert env["TAPDB_DATABASE_NAME"] == "dewey"
    assert env["TAPDB_ENV"] == "dev"
    assert env["TAPDB_STRICT_NAMESPACE"] == "1"
    assert env["TAPDB_CONFIG_PATH"].endswith("config/tapdb-config-dewey.yaml")


def test_export_database_url_for_target_sets_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda required_version=tapdb_runtime.TAPDB_REQUIRED_VERSION: "3.0.2")
    monkeypatch.setattr(
        tapdb_runtime,
        "_get_tapdb_db_config_for_env",
        lambda _env: {
            "user": "dewey",
            "password": "secret",
            "host": "localhost",
            "port": "5439",
            "database": "dewey_dev",
        },
    )

    url = tapdb_runtime.export_database_url_for_target(target="local")

    assert url == "postgresql+psycopg2://dewey:secret@localhost:5439/dewey_dev"
    assert tapdb_runtime.os.environ["DATABASE_URL"] == url


def test_run_tapdb_cli_builds_command_and_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda required_version=tapdb_runtime.TAPDB_REQUIRED_VERSION: "3.0.2")
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, cwd=None, env=None, text=None, capture_output=None):
        calls.append((cmd, env))
        return SimpleNamespace(returncode=1, stdout="bad", stderr="worse")

    monkeypatch.setattr(tapdb_runtime.subprocess, "run", fake_run)

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb command failed"):
        tapdb_runtime.run_tapdb_cli(["bootstrap", "local"], target="local", check=True)

    assert calls
    assert calls[0][0][:6] == [
        tapdb_runtime.sys.executable,
        "-m",
        "daylily_tapdb.cli",
        "--client-id",
        "dewey",
        "--database-name",
    ]


def test_run_tapdb_cli_returns_process_when_check_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda required_version=tapdb_runtime.TAPDB_REQUIRED_VERSION: "3.0.2")
    monkeypatch.setattr(
        tapdb_runtime.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )

    result = tapdb_runtime.run_tapdb_cli(["db", "status"], target="local", check=False)
    assert result.returncode == 0
