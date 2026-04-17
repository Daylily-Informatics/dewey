from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

import dewey_service.cli.test as test_cli


def _proc(returncode: int = 0) -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode)


def test_run_tests_defaults_to_quiet_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        calls.append({"cmd": cmd, "cwd": cwd, "check": check})
        return _proc()

    monkeypatch.setattr(test_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        test_cli.run_tests(SimpleNamespace(args=[]))

    assert exc.value.exit_code == 0
    assert calls == [
        {
            "cmd": [sys.executable, "-m", "pytest", "-q"],
            "cwd": test_cli.PROJECT_ROOT,
            "check": False,
        }
    ]


def test_run_tests_passes_through_pytest_args(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == test_cli.PROJECT_ROOT
        assert check is False
        calls.append(cmd)
        return _proc()

    monkeypatch.setattr(test_cli.subprocess, "run", fake_run)

    with pytest.raises(typer.Exit) as exc:
        test_cli.run_tests(SimpleNamespace(args=["tests/test_cli_boot.py", "-q"]))

    assert exc.value.exit_code == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/test_cli_boot.py", "-q"]]


def test_run_coverage_requires_pytest_cov(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.setattr(test_cli.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(test_cli.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        test_cli.run_coverage(SimpleNamespace(args=[]), html=False)

    assert exc.value.exit_code == 1
    assert errors == ["pytest-cov is not installed; run `python -m pip install -e .`"]


def test_run_coverage_builds_pytest_cov_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    success_messages: list[str] = []

    monkeypatch.setattr(test_cli.importlib.util, "find_spec", lambda name: object())

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> SimpleNamespace:
        assert cwd == test_cli.PROJECT_ROOT
        assert check is False
        calls.append(cmd)
        return _proc()

    monkeypatch.setattr(test_cli.subprocess, "run", fake_run)
    monkeypatch.setattr(
        test_cli.ccyo_out, "success", lambda message: success_messages.append(message)
    )

    with pytest.raises(typer.Exit) as exc:
        test_cli.run_coverage(
            SimpleNamespace(args=["tests/test_cli_boot.py", "-q"]),
            html=True,
        )

    assert exc.value.exit_code == 0
    assert calls == [
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=dewey_service",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "tests/test_cli_boot.py",
            "-q",
        ]
    ]
    assert success_messages == ["HTML report: htmlcov/index.html"]
