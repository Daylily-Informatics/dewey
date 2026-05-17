from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
from cli_core_yo.registry import CommandRegistry

import dewey_service.cli.cognito as cognito_cli
import dewey_service.cli.quality as quality_cli
import dewey_service.cli.tapdb as tapdb_cli
from dewey_service.cli._registry_v2 import REQUIRED, REQUIRED_JSON, REQUIRED_MUTATING
from dewey_service.integrations.tapdb_runtime import TapDBRuntimeError


def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        aws_region="us-west-2",
        tapdb_client_id="dewey",
        tapdb_database_name="dewey",
    )


def test_cognito_status_requires_daycog(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.setattr(cognito_cli.shutil, "which", lambda _name: None)
    monkeypatch.setattr(cognito_cli.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        cognito_cli.status()

    assert exc.value.exit_code == 1
    assert errors == ["daycog not found in PATH"]


def test_cognito_status_handles_missing_binary_after_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []

    monkeypatch.setattr(cognito_cli.shutil, "which", lambda _name: "/usr/bin/daycog")
    monkeypatch.setattr(cognito_cli.ccyo_out, "error", lambda message: errors.append(message))

    def fake_run(*args, **kwargs) -> SimpleNamespace:
        raise FileNotFoundError("daycog")

    monkeypatch.setattr(cognito_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        cognito_cli.status()

    assert exc.value.exit_code == 1
    assert errors == ["daycog not found in PATH"]


def test_cognito_status_runs_daycog_and_emits_output(monkeypatch: pytest.MonkeyPatch) -> None:
    prints: list[str] = []
    warnings: list[str] = []
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(cognito_cli.shutil, "which", lambda _name: "/usr/bin/daycog")
    monkeypatch.setattr(cognito_cli.ccyo_out, "print_text", lambda message: prints.append(message))
    monkeypatch.setattr(cognito_cli.ccyo_out, "warning", lambda message: warnings.append(message))

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        env: dict[str, str],
    ) -> SimpleNamespace:
        calls.append(
            {
                "cmd": cmd,
                "capture_output": capture_output,
                "text": text,
                "check": check,
                "env_has_path": "PATH" in env,
            }
        )
        return _proc(returncode=7, stdout="ok\n", stderr="warn\n")

    monkeypatch.setattr(cognito_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        cognito_cli.status()

    assert exc.value.exit_code == 7
    assert prints == ["ok"]
    assert warnings == ["warn"]
    assert calls == [
        {
            "cmd": ["/usr/bin/daycog", "status"],
            "capture_output": True,
            "text": True,
            "check": False,
            "env_has_path": True,
        }
    ]


def test_cognito_status_forwards_json_output_in_json_mode(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(cognito_cli.shutil, "which", lambda _name: "/usr/bin/daycog")
    monkeypatch.setattr(cognito_cli, "get_context", lambda: SimpleNamespace(json_mode=True))

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        env: dict[str, str],
    ) -> SimpleNamespace:
        calls.append(cmd)
        return _proc(returncode=0, stdout='{"ok": true}\n')

    monkeypatch.setattr(cognito_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        cognito_cli.status()

    captured = capsys.readouterr()
    assert exc.value.exit_code == 0
    assert calls == [["/usr/bin/daycog", "status", "--json"]]
    assert captured.out == '{"ok": true}\n'
    assert captured.err == ""


def test_cognito_registers_v2_command() -> None:
    registry = CommandRegistry()

    cognito_cli.register(registry, object())

    cmd = registry.get_command(("cognito", "status"))

    assert cmd is not None
    assert cmd.callback is cognito_cli.status
    assert cmd.policy == REQUIRED_JSON


def test_tapdb_run_requires_passthrough_args() -> None:
    with pytest.raises(typer.BadParameter, match="Missing tapdb arguments"):
        tapdb_cli.run_command(SimpleNamespace(args=[]))


def test_tapdb_run_invokes_runtime_and_emits_output(monkeypatch: pytest.MonkeyPatch) -> None:
    prints: list[str] = []
    warnings: list[str] = []
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(tapdb_cli.ccyo_out, "print_text", lambda message: prints.append(message))
    monkeypatch.setattr(tapdb_cli.ccyo_out, "warning", lambda message: warnings.append(message))
    monkeypatch.setattr(tapdb_cli, "get_settings", _settings)

    def fake_run_tapdb_cli(
        args: list[str],
        *,
        target: str,
        client_id: str,
        profile: str,
        region: str,
        namespace: str,
        cwd: Path,
        check: bool,
    ) -> SimpleNamespace:
        calls.append(
            {
                "args": args,
                "target": target,
                "client_id": client_id,
                "profile": profile,
                "region": region,
                "namespace": namespace,
                "cwd": cwd,
                "check": check,
            }
        )
        return _proc(returncode=5, stdout="tapdb ok\n", stderr="tapdb warn\n")

    monkeypatch.setattr(tapdb_cli, "run_tapdb_cli", fake_run_tapdb_cli)

    with pytest.raises(typer.Exit) as exc:
        tapdb_cli.run_command(
            SimpleNamespace(args=["db", "status"]),
            target="aurora",
            profile="profile-1",
            region="us-west-1",
            namespace="ns1",
        )

    assert exc.value.exit_code == 5
    assert prints == ["tapdb ok"]
    assert warnings == ["tapdb warn"]
    assert calls == [
        {
            "args": ["db", "status"],
            "target": "aurora",
            "client_id": "dewey",
            "profile": "profile-1",
            "region": "us-west-1",
            "namespace": "ns1",
            "cwd": tapdb_cli.PROJECT_ROOT,
            "check": False,
        }
    ]


def test_tapdb_run_resolves_profile_from_config_when_flag_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setattr(tapdb_cli, "get_settings", _settings)
    monkeypatch.setattr(tapdb_cli, "load_config_aws_profile", lambda: "config-profile")
    monkeypatch.setattr(
        tapdb_cli,
        "run_tapdb_cli",
        lambda args, **kwargs: calls.append(kwargs) or _proc(returncode=0, stdout="", stderr=""),
    )

    with pytest.raises(typer.Exit) as exc:
        tapdb_cli.run_command(
            SimpleNamespace(args=["db", "status"]),
            target="local",
            profile="",
            region="us-west-2",
            namespace="dewey",
        )

    assert exc.value.exit_code == 0
    assert calls == [
        {
            "target": "local",
            "client_id": "dewey",
            "profile": "config-profile",
            "region": "us-west-2",
            "namespace": "dewey",
            "cwd": tapdb_cli.PROJECT_ROOT,
            "check": False,
        }
    ]


def test_tapdb_run_handles_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.setattr(
        tapdb_cli,
        "run_tapdb_cli",
        lambda *args, **kwargs: (_ for _ in ()).throw(TapDBRuntimeError("boom")),
    )
    monkeypatch.setattr(tapdb_cli, "get_settings", _settings)
    monkeypatch.setattr(tapdb_cli, "load_config_aws_profile", lambda: "config-profile")
    monkeypatch.setattr(tapdb_cli.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        tapdb_cli.run_command(SimpleNamespace(args=["db", "status"]))

    assert exc.value.exit_code == 1
    assert errors == ["TapDB invocation failed: boom"]


def test_tapdb_run_requires_profile_source(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(tapdb_cli, "get_settings", _settings)
    monkeypatch.setattr(tapdb_cli, "load_config_aws_profile", lambda: "")
    monkeypatch.setattr(tapdb_cli.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        tapdb_cli.run_command(
            SimpleNamespace(args=["db", "status"]),
            target="local",
            profile="",
            region="us-west-2",
            namespace="dewey",
        )

    assert exc.value.exit_code == 1
    assert errors == [
        "TapDB invocation failed: AWS profile is required; set --profile, DEWEY_AWS_PROFILE, aws.profile, or AWS_PROFILE."
    ]


def test_tapdb_registers_v2_command() -> None:
    registry = CommandRegistry()

    tapdb_cli.register(registry, object())

    cmd = registry.get_command(("tapdb", "run"))

    assert cmd is not None
    assert cmd.callback is tapdb_cli.run_command
    assert cmd.policy == REQUIRED_MUTATING


def test_quality_lint_runs_ruff_check(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        calls.append((cmd, cwd, check))
        return _proc(returncode=3)

    monkeypatch.setattr(quality_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        quality_cli.lint()

    assert exc.value.exit_code == 3
    assert calls == [
        ([sys.executable, "-m", "ruff", "check", "."], quality_cli.PROJECT_ROOT, False)
    ]


@pytest.mark.parametrize(
    ("check_mode", "expected_cmd"),
    [
        (True, [sys.executable, "-m", "ruff", "format", ".", "--check"]),
        (False, [sys.executable, "-m", "ruff", "format", "."]),
    ],
)
def test_quality_format_runs_expected_command(
    monkeypatch: pytest.MonkeyPatch,
    check_mode: bool,
    expected_cmd: list[str],
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == quality_cli.PROJECT_ROOT
        assert check is False
        calls.append(cmd)
        return _proc(returncode=0)

    monkeypatch.setattr(quality_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        quality_cli.format_code(check=check_mode)

    assert exc.value.exit_code == 0
    assert calls == [expected_cmd]


def test_quality_check_stops_after_lint_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == quality_cli.PROJECT_ROOT
        assert check is False
        calls.append(cmd)
        return _proc(returncode=2)

    monkeypatch.setattr(quality_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        quality_cli.check_all()

    assert exc.value.exit_code == 2
    assert calls == [[sys.executable, "-m", "ruff", "check", "."]]


def test_quality_check_runs_tests_after_clean_lint(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == quality_cli.PROJECT_ROOT
        assert check is False
        calls.append(cmd)
        return _proc(returncode=0 if len(calls) == 1 else 4)

    monkeypatch.setattr(quality_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        quality_cli.check_all()

    assert exc.value.exit_code == 4
    assert calls == [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "pytest", "-q"],
    ]


def test_quality_registers_v2_commands() -> None:
    registry = CommandRegistry()

    quality_cli.register(registry, object())

    lint_cmd = registry.get_command(("quality", "lint"))
    format_cmd = registry.get_command(("quality", "format"))
    check_cmd = registry.get_command(("quality", "check"))

    assert lint_cmd is not None
    assert lint_cmd.callback is quality_cli.lint
    assert lint_cmd.policy == REQUIRED_MUTATING

    assert format_cmd is not None
    assert format_cmd.callback is quality_cli.format_code
    assert format_cmd.policy == REQUIRED_MUTATING

    assert check_cmd is not None
    assert check_cmd.callback is quality_cli.check_all
    assert check_cmd.policy == REQUIRED
