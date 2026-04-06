from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dewey_service.integrations import tapdb_runtime


def test_ensure_tapdb_version_accepts_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", lambda _name: "3.0.9")
    assert tapdb_runtime.ensure_tapdb_version() == "3.0.9"


def test_ensure_tapdb_version_requires_install(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str) -> str:
        raise tapdb_runtime.importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", _raise)
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="required but not installed"):
        tapdb_runtime.ensure_tapdb_version()


def test_tapdb_env_for_target_and_sqlalchemy_url() -> None:
    assert tapdb_runtime.tapdb_env_for_target("local") == "dev"
    assert tapdb_runtime.tapdb_env_for_target("aurora") == "prod"
    assert (
        tapdb_runtime._build_sqlalchemy_url(
            {
                "user": "alice",
                "password": "secret",
                "host": "db",
                "port": "5432",
                "database": "dewey",
            }
        )
        == "postgresql+psycopg2://alice:secret@db:5432/dewey"
    )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="Unsupported database target"):
        tapdb_runtime.tapdb_env_for_target("staging")


def test_resolve_tapdb_config_path_prefers_explicit_argument() -> None:
    assert (
        tapdb_runtime._resolve_tapdb_config_path(
            namespace="ignored",
            client_id="ignored",
            config_path="/tmp/custom-tapdb.yaml",
        )
        == "/tmp/custom-tapdb.yaml"
    )


def test_resolve_runtime_env_sets_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOYMENT_CODE", "local2")
    home = Path("/tmp/dewey-home")
    user_config = home / ".config" / "tapdb" / "dewey" / "dewey-local2" / "tapdb-config.yaml"
    user_config.parent.mkdir(parents=True, exist_ok=True)
    user_config.write_text("meta: {}\n", encoding="utf-8")
    monkeypatch.setattr(tapdb_runtime.Path, "home", classmethod(lambda cls: home))
    env = tapdb_runtime._resolve_runtime_env(
        target="local",
        client_id="dewey",
        profile="lsmc",
        region="us-west-2",
        namespace="dewey",
    )

    assert env["aws_profile"] == "lsmc"
    assert env["aws_region"] == "us-west-2"
    assert env["client_id"] == "dewey"
    assert env["database_name"] == "dewey"
    assert env["tapdb_env"] == "dev"
    assert env["config_path"].endswith(".config/tapdb/dewey/dewey-local2/tapdb-config.yaml")


def test_export_database_url_for_target_returns_url_without_mutating_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(
        tapdb_runtime,
        "_get_tapdb_db_config_for_env",
        lambda _env, **_kwargs: {
            "user": "dewey",
            "password": "secret",
            "host": "localhost",
            "port": "5439",
            "database": "dewey_dev",
        },
    )

    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    url = tapdb_runtime.export_database_url_for_target(target="local")

    assert url == "postgresql+psycopg2://dewey:secret@localhost:5439/dewey_dev"
    assert "DATABASE_URL" not in tapdb_runtime.os.environ


def test_run_tapdb_cli_builds_command_and_raises_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, cwd=None, env=None, text=None, capture_output=None):
        calls.append((cmd, env))
        return SimpleNamespace(returncode=1, stdout="bad", stderr="worse")

    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setattr(tapdb_runtime.subprocess, "run", fake_run)

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb command failed"):
        tapdb_runtime.run_tapdb_cli(
            ["bootstrap", "local"],
            target="local",
            config_path="/tmp/dewey-tapdb.yaml",
            check=True,
        )

    assert calls
    assert calls[0][0][:5] == [
        "tapdb",
        "--config",
        "/tmp/dewey-tapdb.yaml",
        "--env",
        "dev",
    ]


def test_run_tapdb_cli_returns_process_when_check_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setattr(
        tapdb_runtime.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )

    result = tapdb_runtime.run_tapdb_cli(
        ["db", "status"],
        target="local",
        config_path="/tmp/dewey-tapdb.yaml",
        check=False,
    )
    assert result.returncode == 0


def test_run_schema_drift_check_maps_exit_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tapdb_runtime,
        "ensure_tapdb_version",
        lambda: "3.0.9",
    )
    monkeypatch.setattr(
        tapdb_runtime,
        "run_tapdb_cli",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout='{"counts":{"expected":{"tables":7},"live":{"tables":7}}}',
            stderr="",
        ),
    )

    result = tapdb_runtime.run_schema_drift_check(target="local")

    assert result["status"] == "drift"
    assert result["tool_version"] == "3.0.9"
    assert result["environment"] == "dev"


def test_run_tapdb_cli_requires_tapdb_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "4.0.6")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: None)

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb CLI is not available"):
        tapdb_runtime.run_tapdb_cli(
            ["info"],
            target="local",
            config_path="/tmp/dewey-tapdb.yaml",
        )
