from __future__ import annotations

from importlib import import_module
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


def test_resolve_tapdb_config_path_prefers_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAPDB_CONFIG_PATH", "/tmp/from-env-tapdb.yaml")

    assert (
        tapdb_runtime._resolve_tapdb_config_path(
            namespace="ignored",
            client_id="ignored",
            config_path="",
        )
        == "/tmp/from-env-tapdb.yaml"
    )


def test_resolve_runtime_env_sets_expected_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOYMENT_CODE", "local2")
    home = Path("/tmp/dewey-home")
    user_config = home / ".config" / "tapdb" / "dewey" / "dewey" / "tapdb-config.yaml"
    user_config.parent.mkdir(parents=True, exist_ok=True)
    user_config.write_text("meta: {}\n", encoding="utf-8")
    context_mod = import_module("daylily_tapdb.cli.context")
    monkeypatch.setattr(context_mod.Path, "home", classmethod(lambda cls: home))
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
    assert env["tapdb_env"] == "dev"
    assert env["config_path"].endswith(".config/tapdb/dewey/dewey/tapdb-config.yaml")


def test_resolve_runtime_env_uses_dewey_env_then_shell_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEWEY_AWS_PROFILE", "dewey-env-profile")
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "config-profile")
    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    env = tapdb_runtime._resolve_runtime_env(target="local", profile="")
    assert env["aws_profile"] == "dewey-env-profile"

    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    env = tapdb_runtime._resolve_runtime_env(target="local", profile="")
    assert env["aws_profile"] == "config-profile"

    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "")
    env = tapdb_runtime._resolve_runtime_env(target="local", profile="")
    assert env["aws_profile"] == "shell-profile"


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
    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "config-profile")

    url = tapdb_runtime.export_database_url_for_target(target="local")

    assert url == "postgresql+psycopg2://dewey:secret@localhost:5439/dewey_dev"
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
            target="local",
            profile="team-profile",
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
        target="local",
        profile="config-profile",
        config_path="/tmp/dewey-tapdb.yaml",
        check=False,
    )

    assert result.returncode == 0
    assert captured["cmd"][:5] == ["tapdb", "--config", "/tmp/dewey-tapdb.yaml", "--env", "dev"]
    assert captured["env"]["AWS_PROFILE"] == "config-profile"
    assert captured["env"]["MERIDIAN_DOMAIN_CODE"] == "D"
    assert captured["env"]["TAPDB_OWNER_REPO"] == "dewey"


def test_run_tapdb_cli_uses_shell_aws_profile_when_explicit_profile_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")
    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "")
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "3.0.9")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "tapdb")
    monkeypatch.setattr(
        tapdb_runtime,
        "_resolve_tapdb_config_path",
        lambda **_kwargs: "/tmp/dewey-tapdb.yaml",
    )

    def fake_run(cmd, cwd=None, env=None, text=None, capture_output=None):
        captured["env"] = env
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(tapdb_runtime.subprocess, "run", fake_run)

    tapdb_runtime.run_tapdb_cli(
        ["db", "status"],
        target="local",
        profile="",
        config_path="/tmp/dewey-tapdb.yaml",
        check=False,
    )

    assert captured["env"]["AWS_PROFILE"] == "shell-profile"


def test_resolve_runtime_env_requires_explicit_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "")

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="AWS profile is required"):
        tapdb_runtime._resolve_runtime_env(target="local", profile="")


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
        target="local",
        profile="config-profile",
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
    monkeypatch.setattr(tapdb_runtime, "ensure_tapdb_version", lambda: "4.1.1")
    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: None)
    monkeypatch.setattr(tapdb_runtime, "load_config_aws_profile", lambda: "config-profile")
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "D")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="tapdb CLI is not available"):
        tapdb_runtime.run_tapdb_cli(
            ["info"],
            target="local",
            config_path="/tmp/dewey-tapdb.yaml",
        )


def test_sanitize_and_resolve_deployment_code(monkeypatch: pytest.MonkeyPatch) -> None:
    assert tapdb_runtime._sanitize_deployment_code(" local/dev ") == "local-dev"
    assert tapdb_runtime._sanitize_deployment_code("###") == "local"

    monkeypatch.setenv("DEPLOYMENT_CODE", "from-deployment")
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "from-dewey")
    monkeypatch.setenv("LSMC_DEPLOYMENT_CODE", "from-lsmc")
    assert tapdb_runtime._resolve_deployment_code() == "from-deployment"

    monkeypatch.delenv("DEPLOYMENT_CODE", raising=False)
    assert tapdb_runtime._resolve_deployment_code() == "from-dewey"
    monkeypatch.delenv("DEWEY_DEPLOYMENT_CODE", raising=False)
    assert tapdb_runtime._resolve_deployment_code() == "from-lsmc"


def test_resolve_tapdb_config_path_supports_user_repo_and_missing_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("TAPDB_CONFIG_PATH", raising=False)
    home = tmp_path / "home"
    shared_config = home / ".config" / "tapdb" / "dewey" / "dewey" / "tapdb-config.yaml"
    shared_config.parent.mkdir(parents=True, exist_ok=True)
    shared_config.write_text("meta: {}\n", encoding="utf-8")
    context_mod = import_module("daylily_tapdb.cli.context")

    class _Context:
        def config_path(self) -> Path:
            return shared_config

    monkeypatch.setattr(
        context_mod,
        "resolve_context",
        lambda **kwargs: _Context(),
    )

    assert tapdb_runtime._resolve_tapdb_config_path(namespace="dewey", client_id="dewey") == str(
        shared_config
    )

    shared_config.unlink()
    assert tapdb_runtime._resolve_tapdb_config_path(namespace="dewey", client_id="dewey") == str(
        shared_config
    )


def test_require_config_path_and_cli_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    assert (
        tapdb_runtime._require_config_path({"config_path": " /tmp/tapdb.yaml "})
        == "/tmp/tapdb.yaml"
    )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="TapDB config path is required"):
        tapdb_runtime._require_config_path({"config_path": ""})

    monkeypatch.setattr(tapdb_runtime.shutil, "which", lambda _name: "/usr/local/bin/tapdb")
    assert tapdb_runtime._resolve_tapdb_cli_executable() == "/usr/local/bin/tapdb"


def test_get_tapdb_db_config_for_env_and_sqlalchemy_url(monkeypatch: pytest.MonkeyPatch) -> None:
    db_config_mod = import_module("daylily_tapdb.cli.db_config")
    seen: list[tuple[object, object, object, object]] = []

    monkeypatch.setattr(
        db_config_mod,
        "get_db_config_for_env",
        lambda env, *, config_path, client_id, database_name: (
            seen.append((env, config_path, client_id, database_name))
            or {
                "user": "postgres",
                "password": "",
                "host": "db",
                "port": "5432",
                "database": "dewey_dev",
            }
        ),
    )

    cfg = tapdb_runtime._get_tapdb_db_config_for_env(
        "dev",
        config_path="/tmp/tapdb.yaml",
        client_id="dewey",
        database_name="dewey",
    )

    assert seen == [("dev", "/tmp/tapdb.yaml", "dewey", "dewey")]
    assert cfg["database"] == "dewey_dev"
    assert (
        tapdb_runtime._build_sqlalchemy_url(cfg)
        == "postgresql+psycopg2://postgres@db:5432/dewey_dev"
    )

    monkeypatch.setattr(
        db_config_mod,
        "get_db_config_for_env",
        lambda *args, **kwargs: {},
    )
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="No TapDB database config resolved"):
        tapdb_runtime._get_tapdb_db_config_for_env(
            "dev",
            config_path="/tmp/tapdb.yaml",
            client_id="dewey",
            database_name="dewey",
        )

    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="missing database name"):
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
    clean = tapdb_runtime.run_schema_drift_check(target="local")

    assert clean == {
        "status": "clean",
        "checked_at": "2026-04-05T18:00:00+00:00",
        "environment": "dev",
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
    failed = tapdb_runtime.run_schema_drift_check(target="local", tapdb_env="prod")

    assert failed == {
        "status": "check_failed",
        "checked_at": "2026-04-05T18:00:00+00:00",
        "environment": "prod",
        "tool_version": "4.1.1",
        "summary": "schema drift report unavailable",
        "report": {"raw_stdout": "not-json"},
        "strict": False,
        "stderr": "boom",
    }
