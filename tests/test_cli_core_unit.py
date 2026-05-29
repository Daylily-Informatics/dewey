from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
import yaml
from cli_core_yo.registry import CommandRegistry

import dewey_service.cli as cli_module
import dewey_service.cli.config_extra as config_extra
import dewey_service.cli.qeo as qeo_cli
from dewey_service.cli._registry_v2 import REQUIRED, REQUIRED_MUTATING


def _minimal_config_yaml(**overrides: object) -> str:
    payload = {
        "application": {"name": "dewey"},
        "auth": {"cognito": {"enabled": True}},
        "database": {"backend": "tapdb", "target": "local"},
    }
    payload.update(overrides)
    return yaml.safe_dump(payload)


def test_validate_dewey_config_rejects_invalid_yaml_and_non_mapping_root() -> None:
    parse_errors = cli_module._validate_dewey_config("application: [")
    root_errors = cli_module._validate_dewey_config(yaml.safe_dump(["not", "a", "mapping"]))

    assert parse_errors and parse_errors[0].startswith("YAML parse error:")
    assert root_errors == ["Root YAML object must be a mapping"]


def test_validate_dewey_config_reports_section_and_backend_errors() -> None:
    missing_section_errors = cli_module._validate_dewey_config(yaml.safe_dump({"application": {}}))
    invalid_structure_errors = cli_module._validate_dewey_config(
        _minimal_config_yaml(
            auth={"cognito": "bad"},
            database={"backend": "sqlite", "target": "staging"},
        )
    )

    assert "Missing or empty required section: 'application'" in missing_section_errors
    assert "Missing or empty required section: 'auth'" in missing_section_errors
    assert "Missing or empty required section: 'database'" in missing_section_errors
    assert "auth.cognito is required and must be a mapping" in invalid_structure_errors
    assert "database.backend must be 'tapdb'" in invalid_structure_errors
    assert "database.target must be one of: local, aurora" in invalid_structure_errors


def test_validate_dewey_config_merges_yaml_defaults_into_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli_module,
        "_flatten_config",
        lambda _config: {"custom_setting": "present", "cognito_region": "eu-west-1"},
    )

    class FakeSettings:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(cli_module, "Settings", FakeSettings)

    errors = cli_module._validate_dewey_config(_minimal_config_yaml())

    assert errors == []
    assert captured["custom_setting"] == "present"
    assert captured["cognito_region"] == "eu-west-1"
    assert captured["cognito_redirect_uri"] == cli_module.default_cognito_redirect_uri()
    assert captured["cognito_logout_url"] == cli_module.default_cognito_logout_url()
    assert captured["deployment_is_production"] is False


def test_validate_dewey_config_reports_settings_validation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_module, "_flatten_config", lambda _config: {})

    class FakeSettings:
        def __init__(self, **kwargs: object) -> None:
            raise ValueError("bad settings")

    monkeypatch.setattr(cli_module, "Settings", FakeSettings)

    errors = cli_module._validate_dewey_config(_minimal_config_yaml())

    assert errors == ["settings validation failed: bad settings"]


def test_dewey_info_hook_reports_settings_and_running_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_calls: list[str] = []
    pid_file = tmp_path / "server.pid"
    pid_file.write_text("4321\n", encoding="utf-8")

    monkeypatch.setattr(cli_module, "clear_settings_cache", lambda: clear_calls.append("clear"))
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: SimpleNamespace(
            database_backend="tapdb",
            database_target="local",
            tapdb_client_id="dewey",
            tapdb_database_name="dewey",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_code="Z",
            host="127.0.0.1",
            port=8914,
            aws_profile="config-profile",
        ),
    )
    monkeypatch.setattr(
        "cli_core_yo.runtime.get_context",
        lambda: SimpleNamespace(xdg_paths=SimpleNamespace(state=tmp_path)),
    )
    monkeypatch.setattr(cli_module.os, "kill", lambda pid, sig: None)
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    rows = dict(cli_module._dewey_info_hook())

    assert clear_calls == ["clear"]
    assert rows["Project Root"] == str(cli_module.PROJECT_ROOT)
    assert rows["Database Backend"] == "tapdb"
    assert rows["TapDB Namespace"] == "dewey"
    assert rows["TapDB Owner Repo"] == "dewey"
    assert rows["TapDB Domain"] == "Z"
    assert rows["Host"] == "127.0.0.1"
    assert rows["Port"] == "8914"
    assert rows["AWS Profile"] == "config-profile"
    assert rows["AWS Region"] == "us-west-2"
    assert rows["Dev Server"] == "Running (PID 4321)"


def test_dewey_info_hook_handles_invalid_config_and_unknown_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setattr(cli_module, "clear_settings_cache", lambda: None)
    monkeypatch.setattr(
        cli_module,
        "get_settings",
        lambda: (_ for _ in ()).throw(ValueError("bad cfg")),
    )
    monkeypatch.setattr(
        "cli_core_yo.runtime.get_context",
        lambda: (_ for _ in ()).throw(RuntimeError("no runtime")),
    )

    rows = dict(cli_module._dewey_info_hook())

    assert rows["Config Status"] == "invalid (bad cfg)"
    assert rows["AWS Profile"] == "shell-profile"
    assert rows["Dev Server"] == "Unknown"


def test_main_runs_prebuilt_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(passed_spec: object) -> int:
        seen["spec"] = passed_spec
        return 7

    monkeypatch.setattr(cli_module, "run", fake_run)

    with pytest.raises(SystemExit) as exc:
        cli_module.main()

    assert exc.value.code == 7
    assert seen["spec"] is cli_module.spec


def test_config_status_prints_runtime_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_calls: list[str] = []
    printed: list[str] = []
    settings = SimpleNamespace()

    monkeypatch.setattr(config_extra, "clear_settings_cache", lambda: clear_calls.append("clear"))
    monkeypatch.setattr(config_extra, "get_config_file_path", lambda: "/tmp/dewey-config.yaml")
    monkeypatch.setattr(config_extra, "get_settings", lambda: settings)
    monkeypatch.setattr(
        config_extra,
        "build_effective_config_rows",
        lambda passed_settings, *, config_path: [
            {"path": "application.api_bearer_token", "value": "<redacted>"},
            {"path": "qeo.api_token", "value": "<redacted>"},
        ]
        if passed_settings is settings and str(config_path) == "/tmp/dewey-config.yaml"
        else [],
    )
    monkeypatch.setattr(
        config_extra.ccyo_out, "print_text", lambda message: printed.append(message)
    )

    config_extra._status()

    assert clear_calls == ["clear"]
    assert printed == [
        "Config path: [cyan]/tmp/dewey-config.yaml[/cyan]",
        "application.api_bearer_token=<redacted>",
        "qeo.api_token=<redacted>",
    ]


def test_config_status_exits_on_invalid_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.setattr(config_extra, "clear_settings_cache", lambda: None)
    monkeypatch.setattr(
        config_extra,
        "get_settings",
        lambda: (_ for _ in ()).throw(ValueError("invalid config")),
    )
    monkeypatch.setattr(config_extra.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        config_extra._status()

    assert exc.value.exit_code == 1
    assert errors == ["Configuration invalid: invalid config"]


def test_qeo_status_redacts_token(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    monkeypatch.setattr(qeo_cli, "clear_settings_cache", lambda: None)
    monkeypatch.setattr(
        qeo_cli,
        "get_settings",
        lambda: SimpleNamespace(
            qeo_ingest_url="https://qeo.example.com/api/v1/ingest/dewey-events",
            qeo_api_token="secret-token",
            qeo_consumer_group="qeo.dewey",
        ),
    )
    monkeypatch.setattr(qeo_cli.ccyo_out, "print_text", lambda message: printed.append(message))

    qeo_cli._status()

    assert "qeo.dispatch_configured=true" in printed
    assert "qeo.api_token=<redacted>" in printed
    assert all("secret-token" not in line for line in printed)


def test_qeo_dispatch_cli_emits_result(monkeypatch: pytest.MonkeyPatch) -> None:
    emitted: list[dict[str, object]] = []

    class FakeService:
        def dispatch_qeo_outbox(self, *, limit: int, retry_errors: bool):
            return {
                "attempted": 1,
                "limit": limit,
                "retry_errors": retry_errors,
            }

    monkeypatch.setattr(qeo_cli, "build_cli_service", lambda: FakeService())
    monkeypatch.setattr(qeo_cli.ccyo_out, "emit_json", lambda payload: emitted.append(payload))

    qeo_cli._dispatch(limit=3, retry_errors=True)

    assert emitted == [{"attempted": 1, "limit": 3, "retry_errors": True}]


def test_set_artifact_bucket_persists_and_prints(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    successes: list[str] = []

    monkeypatch.setattr(
        config_extra,
        "persist_managed_storage_bucket",
        lambda bucket: ("/tmp/dewey-config.yaml", bucket.removeprefix("s3://")),
    )
    monkeypatch.setattr(
        config_extra,
        "get_settings",
        lambda: SimpleNamespace(managed_storage_bucket="dewey-artifacts-local"),
    )
    monkeypatch.setattr(config_extra.ccyo_out, "success", lambda message: successes.append(message))
    monkeypatch.setattr(
        config_extra.ccyo_out, "print_text", lambda message: printed.append(message)
    )

    config_extra._set_artifact_bucket("s3://dewey-artifacts-local")

    assert successes == ["Updated artifact bucket in /tmp/dewey-config.yaml"]
    assert printed == ["managed_storage_bucket=dewey-artifacts-local"]


def test_set_artifact_bucket_exits_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.setattr(
        config_extra,
        "persist_managed_storage_bucket",
        lambda _bucket: (_ for _ in ()).throw(RuntimeError("write failed")),
    )
    monkeypatch.setattr(config_extra.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        config_extra._set_artifact_bucket("bucket")

    assert exc.value.exit_code == 1
    assert errors == ["Could not update artifact bucket: write failed"]


def test_config_extra_registers_commands() -> None:
    registry = CommandRegistry()

    config_extra.register(registry, object())

    status_cmd = registry.get_command(("config", "status"))
    bucket_cmd = registry.get_command(("config", "set-artifact-bucket"))

    assert status_cmd is not None
    assert status_cmd.callback is config_extra._status
    assert status_cmd.help_text == "Show merged Dewey runtime settings"
    assert status_cmd.policy == REQUIRED

    assert bucket_cmd is not None
    assert bucket_cmd.callback is config_extra._set_artifact_bucket
    assert bucket_cmd.help_text == "Set the S3 bucket Dewey uses for managed artifact storage."
    assert bucket_cmd.policy == REQUIRED_MUTATING
