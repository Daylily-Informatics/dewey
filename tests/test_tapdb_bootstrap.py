from __future__ import annotations

from typer.testing import CliRunner

from dewey_service.cli import cli

runner = CliRunner()


def test_db_build_invokes_overlay(monkeypatch) -> None:
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

    monkeypatch.setattr("dewey_service.cli.ensure_tapdb_version", lambda: "3.0.2")
    monkeypatch.setattr("dewey_service.cli.run_tapdb_cli", _fake_tapdb)
    monkeypatch.setattr("dewey_service.cli.export_database_url_for_target", _fake_db_url)
    monkeypatch.setattr("dewey_service.cli.subprocess.run", _fake_run)

    result = runner.invoke(cli, ["db", "build", "--target", "local"])
    assert result.exit_code == 0
    assert calls["tapdb"] == 1
    assert calls["dburl"] == 1
    assert calls["seed"] == 1
