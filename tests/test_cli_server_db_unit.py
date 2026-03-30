from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

import dewey_service.cli.db as db_cli
import dewey_service.cli.server as server_cli
from dewey_service.settings import Settings


def _settings() -> Settings:
    return Settings(
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client-1",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_server_state_and_path_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ctx = SimpleNamespace(xdg_paths=SimpleNamespace(state=tmp_path))
    monkeypatch.setattr("cli_core_yo.runtime.get_context", lambda: ctx)

    assert server_cli._state_dir() == tmp_path
    assert server_cli._log_dir() == tmp_path / "logs"
    assert server_cli._pid_file() == tmp_path / "server.pid"

    server_cli._ensure_runtime_dirs()
    assert (tmp_path / "logs").exists()


def test_server_load_settings_and_uri_validation(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    clear_calls: list[str] = []
    monkeypatch.setattr(server_cli, "clear_settings_cache", lambda: clear_calls.append("clear"))
    monkeypatch.setattr(server_cli, "get_settings", lambda: _settings())
    assert server_cli._load_settings().cognito_app_client_id == "client-1"
    assert clear_calls == ["clear"]

    monkeypatch.setattr(server_cli, "_load_settings", lambda: (_ for _ in ()).throw(ValueError("bad config")))
    with pytest.raises(typer.Exit) as exc:
        server_cli._validate_cognito_uris_for_port(port=8914, host="localhost")
    assert exc.value.exit_code == 1

    monkeypatch.setattr(server_cli, "_load_settings", _settings)
    monkeypatch.setattr(server_cli, "validate_uri_list_ports", lambda **kwargs: ["port mismatch"])
    server_cli._validate_cognito_uris_for_port(port=8914, host="localhost")
    assert "port mismatch" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "validate_uri_list_ports", lambda **kwargs: [])
    server_cli._validate_cognito_uris_for_port(port=8914, host="localhost")


def test_server_port_host_and_status_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEWEY_PORT", raising=False)
    assert server_cli._resolve_port(8914) == 8914

    monkeypatch.setenv("DEWEY_PORT", "9000")
    assert server_cli._resolve_port(8914) == 9000

    monkeypatch.setenv("DEWEY_PORT", "bad")
    with pytest.raises(typer.BadParameter):
        server_cli._resolve_port(8914)

    monkeypatch.setenv("DEWEY_HOST", "0.0.0.0")
    monkeypatch.setenv("DEWEY_PORT", "9001")
    assert server_cli._resolve_host("127.0.0.1") == "0.0.0.0"
    assert server_cli._status_bind() == ("localhost", "9001")

    monkeypatch.delenv("DEWEY_HOST", raising=False)
    monkeypatch.delenv("DEWEY_PORT", raising=False)
    monkeypatch.setattr(server_cli, "_load_settings", _settings)
    assert server_cli._status_bind() == ("localhost", "8914")

    monkeypatch.setattr(server_cli, "_load_settings", lambda: (_ for _ in ()).throw(ValueError("invalid")))
    assert server_cli._status_bind() == ("unknown", "unknown")


def test_start_server_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(server_cli, "_ensure_runtime_dirs", lambda: None)
    monkeypatch.setattr(server_cli, "_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(server_cli, "_log_dir", lambda: tmp_path)

    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    monkeypatch.setattr(server_cli, "CERT_FILE", cert)
    monkeypatch.setattr(server_cli, "KEY_FILE", key)

    with pytest.raises(typer.BadParameter, match="HTTPS certs are missing"):
        server_cli._start_server(host="0.0.0.0", port=8914, reload=False, background=True)

    cert.write_text("cert", encoding="utf-8")
    key.write_text("key", encoding="utf-8")

    monkeypatch.setattr(server_cli, "read_pid", lambda path: 321)
    server_cli._start_server(host="0.0.0.0", port=8914, reload=False, background=True)

    monkeypatch.setattr(server_cli, "read_pid", lambda path: None)
    monkeypatch.setattr(server_cli, "new_log_path", lambda path: tmp_path / "server.log")
    monkeypatch.setattr(server_cli.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(server_cli.shutil, "which", lambda name: "/usr/bin/python")

    class FailedProc:
        pid = 999

        @staticmethod
        def poll():
            return 1

    monkeypatch.setattr(server_cli.subprocess, "Popen", lambda *args, **kwargs: FailedProc())
    with pytest.raises(typer.Exit) as exc:
        server_cli._start_server(host="0.0.0.0", port=8914, reload=True, background=True)
    assert exc.value.exit_code == 1

    writes: list[int] = []

    class RunningProc:
        pid = 555

        @staticmethod
        def poll():
            return None

    monkeypatch.setattr(server_cli.subprocess, "Popen", lambda *args, **kwargs: RunningProc())
    monkeypatch.setattr(server_cli, "write_pid", lambda path, pid: writes.append(pid))
    server_cli._start_server(host="0.0.0.0", port=8914, reload=False, background=True)
    assert writes == [555]

    uvicorn_calls: list[dict[str, object]] = []
    monkeypatch.setattr(server_cli.uvicorn, "run", lambda **kwargs: uvicorn_calls.append(kwargs))
    server_cli._start_server(host="127.0.0.1", port=8915, reload=True, background=False)
    assert uvicorn_calls[0]["host"] == "127.0.0.1"
    assert uvicorn_calls[0]["port"] == 8915


def test_stop_server_and_logs_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(server_cli, "_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(server_cli, "stop_pid", lambda path: (True, "Server stopped"))
    server_cli._stop_server()
    assert "Server stopped" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "stop_pid", lambda path: (False, "Permission denied stopping PID 1"))
    with pytest.raises(typer.Exit) as exc:
        server_cli._stop_server()
    assert exc.value.exit_code == 1

    monkeypatch.setattr(server_cli, "stop_pid", lambda path: (False, "No server running"))
    server_cli._stop_server()
    assert "No server running" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "_ensure_runtime_dirs", lambda: None)
    monkeypatch.setattr(server_cli, "_log_dir", lambda: tmp_path)
    monkeypatch.setattr(server_cli, "list_logs", lambda path: [])
    server_cli.logs(all_logs=True)
    assert "No log files found" in capsys.readouterr().out

    log_file = tmp_path / "server_1.log"
    log_file.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(server_cli, "list_logs", lambda path: [log_file])
    server_cli.logs(all_logs=True)
    assert "server_1.log" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "latest_log", lambda path: None)
    server_cli.logs(all_logs=False)
    assert "No log file found" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "latest_log", lambda path: log_file)
    followed: list[tuple[Path, int]] = []
    monkeypatch.setattr(server_cli, "tail_follow", lambda path, lines=50: followed.append((path, lines)))
    server_cli.logs(lines=25, all_logs=False)
    assert followed == [(log_file, 25)]

    def raise_keyboard(path, lines=50):
        raise KeyboardInterrupt

    monkeypatch.setattr(server_cli, "tail_follow", raise_keyboard)
    server_cli.logs(lines=10, all_logs=False)


def test_server_command_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    start_calls: list[dict[str, object]] = []
    monkeypatch.setenv("DEWEY_HOST", "127.0.0.1")
    monkeypatch.setenv("DEWEY_PORT", "9002")
    monkeypatch.setattr(server_cli, "_validate_cognito_uris_for_port", lambda **kwargs: start_calls.append({"validated": kwargs}))
    monkeypatch.setattr(server_cli, "_start_server", lambda **kwargs: start_calls.append(kwargs))

    server_cli.start(reload=True, background=False)
    assert start_calls[0]["validated"] == {"port": 9002, "host": "127.0.0.1"}
    assert start_calls[1] == {"host": "127.0.0.1", "port": 9002, "reload": True, "background": False}

    stop_calls: list[str] = []
    monkeypatch.setattr(server_cli, "_stop_server", lambda: stop_calls.append("stop"))
    server_cli.stop()
    assert stop_calls == ["stop"]


def test_db_cli_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_cli, "ensure_tapdb_version", lambda: "3.0.6")

    with pytest.raises(typer.Exit) as exc:
        db_cli.build(target="aurora", cluster="", profile="lsmc", region="us-west-2", namespace="dewey")
    assert exc.value.exit_code == 1

    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda *args, **kwargs: _proc(returncode=0, stdout="ok"),
    )
    monkeypatch.setattr(
        db_cli,
        "export_database_url_for_target",
        lambda **kwargs: "postgresql+psycopg2://dewey@localhost:5432/dewey",
    )

    def fail_seed(cmd, cwd=None, check=False):
        raise db_cli.subprocess.CalledProcessError(returncode=7, cmd=cmd)

    monkeypatch.setattr(db_cli.subprocess, "run", fail_seed)
    with pytest.raises(typer.Exit) as exc:
        db_cli.build(target="local", cluster="", profile="lsmc", region="us-west-2", namespace="dewey")
    assert exc.value.exit_code == 1

    with pytest.raises(typer.Exit) as exc:
        db_cli.seed()
    assert exc.value.exit_code == 7

    monkeypatch.setattr(db_cli.typer, "confirm", lambda message: False)
    with pytest.raises(typer.Exit) as exc:
        db_cli.reset(force=False)
    assert exc.value.exit_code == 0

    with pytest.raises(typer.Exit) as exc:
        db_cli.nuke(force=False)
    assert exc.value.exit_code == 0

    monkeypatch.setattr(db_cli.typer, "confirm", lambda message: True)
    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda *args, **kwargs: (_ for _ in ()).throw(db_cli.TapDBRuntimeError("delete failed")),
    )
    with pytest.raises(typer.Exit) as exc:
        db_cli.reset(
            force=True,
            target="local",
            cluster="",
            profile="lsmc",
            region="us-west-2",
            namespace="dewey",
        )
    assert exc.value.exit_code == 1


def test_db_cli_reset_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda args, **kwargs: calls.append(("delete", args)) or _proc(returncode=0, stdout="deleted"),
    )
    monkeypatch.setattr(
        db_cli,
        "build",
        lambda **kwargs: calls.append(("build", kwargs)),
    )

    db_cli.reset(force=True, target="local", cluster="cluster-1", profile="lsmc", region="us-west-2", namespace="dewey")

    assert calls == [
        ("delete", ["db", "delete", "dev", "--force"]),
        (
            "build",
            {
                "target": "local",
                "cluster": "cluster-1",
                "profile": "lsmc",
                "region": "us-west-2",
                "namespace": "dewey",
            },
        ),
    ]


def test_db_cli_nuke_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda args, **kwargs: calls.append(("delete", args)) or _proc(returncode=0, stdout="deleted"),
    )
    monkeypatch.setattr(
        db_cli,
        "build",
        lambda **kwargs: calls.append(("build", kwargs)),
    )

    db_cli.nuke(force=True, target="aurora", profile="lsmc", region="us-west-2", namespace="dewey")

    assert calls == [("delete", ["db", "delete", "prod", "--force"])]
