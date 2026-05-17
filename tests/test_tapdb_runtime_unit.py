from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

from dewey_service.integrations import tapdb_runtime


def _runtime_kwargs(**overrides: str) -> dict[str, str]:
    values = {
        "target": "local",
        "client_id": "dewey",
        "profile": "config-profile",
        "region": "us-west-2",
        "namespace": "dewey",
        "config_path": "/tmp/dewey-tapdb.yaml",
    }
    values.update(overrides)
    return values


def _drift_kwargs(**overrides: str) -> dict[str, str]:
    values = _runtime_kwargs(**overrides)
    values.pop("config_path", None)
    return values


def test_ensure_tapdb_version_accepts_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", lambda _name: "3.0.9")
    assert tapdb_runtime.ensure_tapdb_version() == "3.0.9"


def test_ensure_tapdb_version_requires_install(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str) -> str:
        raise tapdb_runtime.importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", _raise)
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="required but not installed"):
        tapdb_runtime.ensure_tapdb_version()


def test_validate_database_target_and_sqlalchemy_url() -> None:
    assert tapdb_runtime.validate_database_target("local") == "local"
    assert tapdb_runtime.validate_database_target("aurora") == "aurora"
    assert (
        tapdb_runtime._build_sqlalchemy_url(
            {
                "user": "alice",
                "password": "secret",
                "host": "db",
                "port": "5432",
                "database": "dewey",
                "schema_name": "tapdb_dewey_dev",
            }
        )
        == "postgresql+psycopg2://alice:secret@db:5432/dewey"
        "?options=-csearch_path%3Dtapdb_dewey_dev"
    )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="Unsupported database target"):
        tapdb_runtime.validate_database_target("staging")


def test_resolve_tapdb_config_path_prefers_explicit_argument() -> None:
    assert tapdb_runtime._resolve_tapdb_config_path(
        namespace="ignored",
        client_id="ignored",
        config_path="/tmp/custom-tapdb.yaml",
    ) == str(Path("/tmp/custom-tapdb.yaml").resolve())


def test_resolve_tapdb_config_path_prefers_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAPDB_CONFIG_PATH", "/tmp/from-env-tapdb.yaml")

    assert tapdb_runtime._resolve_tapdb_config_path(
        namespace="ignored",
        client_id="ignored",
        config_path="",
    ) == str(Path("/tmp/from-env-tapdb.yaml").resolve())


def test_resolve_runtime_env_sets_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "TAPDB_CONFIG_PATH", "/tmp/dewey-home/.config/tapdb/dewey/dewey/tapdb-config.yaml"
    )
    env = tapdb_runtime._resolve_runtime_env(
        target="local",
        client_id="dewey",
        profile="config-profile",
        region="us-west-2",
        namespace="dewey",
    )

    assert env["aws_profile"] == "config-profile"
    assert env["aws_region"] == "us-west-2"
    assert env["client_id"] == "dewey"
    assert env["database_name"] == "dewey"
    assert env["config_path"] == str(
        Path("/tmp/dewey-home/.config/tapdb/dewey/dewey/tapdb-config.yaml").resolve()
    )


def test_resolve_runtime_env_requires_explicit_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    env = tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(config_path=""))
    assert env["aws_profile"] == "config-profile"

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="client_id is required"):
        tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(client_id="", config_path=""))
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="database_name/namespace"):
        tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(namespace="", config_path=""))
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="AWS profile"):
        tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(profile="", config_path=""))
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="AWS region"):
        tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(region="", config_path=""))


def test_export_database_url_for_target_returns_url_without_mutating_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(
        tapdb_runtime,
        "_get_tapdb_db_config",
        lambda **_kwargs: {
            "user": "dewey",
            "password": "secret",
            "host": "localhost",
            "port": "5439",
            "database": "dewey_dev",
            "schema_name": "tapdb_dewey_dev",
        },
    )

    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )
    url = tapdb_runtime.export_database_url_for_target(**_runtime_kwargs())

    assert url == (
        "postgresql+psycopg2://dewey:secret@localhost:5439/dewey_dev"
        "?options=-csearch_path%3Dtapdb_dewey_dev"
    )
    assert "DATABASE_URL" not in tapdb_runtime.os.environ


def test_run_tapdb_cli_builds_command_and_raises_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    calls: list[tuple[list[str], dict[str, str]]] = []
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")

    def fake_run(cmd, cwd=None, env=None, text=None, capture_output=None):
        calls.append((cmd, env))
        return SimpleNamespace(returncode=1, stdout="bad", stderr="worse")

    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setattr(tapdb_runtime.subprocess, "run", fake_run)

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb command failed"):
        tapdb_runtime.run_tapdb_cli(
            ["bootstrap", "local"],
            **_runtime_kwargs(profile="team-profile"),
            check=True,
        )

    assert calls
    assert calls[0][0][:3] == [
        "tapdb",
        "--config",
        str(Path("/tmp/dewey-tapdb.yaml").resolve()),
    ]


def test_run_tapdb_cli_exports_resolved_profile_and_identity_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")
    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    def fake_run(cmd, cwd=None, env=None, text=None, capture_output=None):
        captured["cmd"] = cmd
        captured["env"] = env
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(tapdb_runtime.subprocess, "run", fake_run)

    result = tapdb_runtime.run_tapdb_cli(
        ["db", "status"],
        **_runtime_kwargs(),
        check=False,
    )

    assert result.returncode == 0
    assert captured["cmd"][:3] == ["tapdb", "--config", "/tmp/dewey-tapdb.yaml"]
    assert captured["env"]["AWS_PROFILE"] == "config-profile"
    assert captured["env"]["MERIDIAN_DOMAIN_CODE"] == "D"
    assert captured["env"]["TAPDB_OWNER_REPO"] == "dewey"


def test_run_tapdb_cli_rejects_blank_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="AWS profile"):
        tapdb_runtime.run_tapdb_cli(
            ["db", "status"],
            **_runtime_kwargs(profile=""),
            check=False,
        )


def test_resolve_runtime_env_requires_explicit_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="AWS profile is required"):
        tapdb_runtime._resolve_runtime_env(**_runtime_kwargs(profile=""))


def test_run_tapdb_cli_returns_process_when_check_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")
    monkeypatch.setattr(
        tapdb_runtime.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )

    result = tapdb_runtime.run_tapdb_cli(
        ["db", "status"],
        **_runtime_kwargs(),
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

    result = tapdb_runtime.run_schema_drift_check(**_drift_kwargs())

    assert result["status"] == "drift"
    assert result["tool_version"] == "3.0.9"
    assert result["target"] == "local"


def test_run_tapdb_cli_requires_tapdb_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "4.1.1")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: None)
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb CLI is not available"):
        tapdb_runtime.run_tapdb_cli(
            ["info"],
            **_runtime_kwargs(),
        )


def test_sanitize_and_resolve_deployment_code(monkeypatch: pytest.MonkeyPatch) -> None:
    assert tapdb_runtime._sanitize_deployment_code(" local/dev ") == "local-dev"
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="deployment code is required"):
        tapdb_runtime._sanitize_deployment_code("###")

    monkeypatch.setenv("DEPLOYMENT_CODE", "from-deployment")
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "from-dewey")
    monkeypatch.setenv("LSMC_DEPLOYMENT_CODE", "from-lsmc")
    assert tapdb_runtime._resolve_deployment_code() == "from-deployment"

    monkeypatch.delenv("DEPLOYMENT_CODE", raising=False)
    assert tapdb_runtime._resolve_deployment_code() == "from-dewey"
    monkeypatch.delenv("DEWEY_DEPLOYMENT_CODE", raising=False)
    assert tapdb_runtime._resolve_deployment_code() == "from-lsmc"


def test_resolve_tapdb_config_path_returns_none_without_explicit_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAPDB_CONFIG_PATH", raising=False)
    assert tapdb_runtime._resolve_tapdb_config_path(namespace="dewey", client_id="dewey") is None


def test_resolve_tapdb_config_path_rejects_relative_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="absolute file path"):
        tapdb_runtime._resolve_tapdb_config_path(
            namespace="dewey",
            client_id="dewey",
            config_path="relative/tapdb.yaml",
        )

    monkeypatch.setenv("TAPDB_CONFIG_PATH", "relative/tapdb.yaml")
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="absolute file path"):
        tapdb_runtime._resolve_tapdb_config_path(namespace="dewey", client_id="dewey")


def test_require_config_path_and_cli_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    assert (
        tapdb_runtime._require_config_path({"config_path": " /tmp/tapdb.yaml "})
        == "/tmp/tapdb.yaml"
    )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="TapDB config path is required"):
        tapdb_runtime._require_config_path({"config_path": ""})

    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "/usr/local/bin/tapdb")
    assert tapdb_runtime._resolve_tapdb_cli_executable() == "/usr/local/bin/tapdb"


def test_get_tapdb_db_config_and_sqlalchemy_url(monkeypatch: pytest.MonkeyPatch) -> None:
    db_config_mod = import_module("daylily_tapdb.cli.db_config")
    seen: list[tuple[object, object, object]] = []

    monkeypatch.setattr(
        db_config_mod,
        "get_db_config",
        lambda *, config_path, client_id, database_name: (
            seen.append((config_path, client_id, database_name))
            or {
                "user": "postgres",
                "password": "",
                "host": "db",
                "port": "5432",
                "database": "dewey_dev",
                "schema_name": "tapdb_dewey_dev",
            }
        ),
    )

    cfg = tapdb_runtime._get_tapdb_db_config(
        config_path="/tmp/tapdb.yaml",
        client_id="dewey",
        database_name="dewey",
    )

    assert seen == [("/tmp/tapdb.yaml", "dewey", "dewey")]
    assert cfg["database"] == "dewey_dev"
    assert (
        tapdb_runtime._build_sqlalchemy_url(cfg)
        == "postgresql+psycopg2://postgres@db:5432/dewey_dev"
        "?options=-csearch_path%3Dtapdb_dewey_dev"
    )

    monkeypatch.setattr(
        db_config_mod,
        "get_db_config",
        lambda *args, **kwargs: {},
    )
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="No TapDB database config resolved"):
        tapdb_runtime._get_tapdb_db_config(
            config_path="/tmp/tapdb.yaml",
            client_id="dewey",
            database_name="dewey",
        )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="missing host"):
        tapdb_runtime._build_sqlalchemy_url({"user": "postgres"})


def test_run_schema_drift_check_covers_clean_invalid_json_and_failed_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "4.1.1")
    monkeypatch.setattr(tapdb_runtime, "_utcnow", lambda: "2026-04-05T18:00:00+00:00")

    monkeypatch.setattr(
        tapdb_runtime,
        "run_tapdb_cli",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    clean = tapdb_runtime.run_schema_drift_check(**_drift_kwargs())

    assert clean == {
        "status": "clean",
        "checked_at": "2026-04-05T18:00:00+00:00",
        "target": "local",
        "tool_version": "4.1.1",
        "summary": "no schema drift reported",
        "report": {},
        "strict": False,
    }

    monkeypatch.setattr(
        tapdb_runtime,
        "run_tapdb_cli",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="not-json", stderr="boom"),
    )
    failed = tapdb_runtime.run_schema_drift_check(**_drift_kwargs())

    assert failed == {
        "status": "check_failed",
        "checked_at": "2026-04-05T18:00:00+00:00",
        "target": "local",
        "tool_version": "4.1.1",
        "summary": "schema drift report unavailable",
        "report": {"raw_stdout": "not-json"},
        "strict": False,
        "stderr": "boom",
    }
