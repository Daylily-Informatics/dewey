from __future__ import annotations

from cli_core_yo import output
from cli_core_yo.app import run as run_cli

import dewey_service.cli as cli_module
import dewey_service.cli.db as db_cli


def _invoke(argv: list[str]) -> int:
    output._reset_console()
    return run_cli(cli_module.spec, argv)


def test_db_build_invokes_overlay(monkeypatch, capsys) -> None:
    calls: dict[str, int] = {"tapdb": 0, "dburl": 0, "seed": 0}

    class _Result:
        returncode = 0
        stdout = "ok"

    def _fake_tapdb(*args, **kwargs):
        calls["tapdb"] += 1
        return _Result()

    def _fake_db_url(*args, **kwargs):
        calls["dburl"] += 1
        return "postgresql+psycopg2://u:p@localhost:5439/dewey"

    def _fake_run(cmd, cwd=None, check=False):
        calls["seed"] += 1
        return _Result()

    monkeypatch.setattr(db_cli, "ensure_tapdb_version", lambda: "3.0.6")
    monkeypatch.setattr(db_cli, "run_tapdb_cli", _fake_tapdb)
    monkeypatch.setattr(db_cli, "export_database_url_for_target", _fake_db_url)
    monkeypatch.setattr(db_cli.subprocess, "run", _fake_run)

    exit_code = _invoke(["db", "build", "--target", "local"])
    capsys.readouterr()

    assert exit_code == 0
    assert calls["tapdb"] == 1
    assert calls["dburl"] == 1
    assert calls["seed"] == 1
