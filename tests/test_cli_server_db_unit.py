from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

import dewey_service.cli.db as db_cli
import dewey_service.cli.server as server_cli
from dewey_service.settings import Settings


def _settings() -> Settings:
    return Settings(
        cognito_domain="auth.example.com",
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
    assert server_cli._runtime_meta_file() == tmp_path / "server-meta.json"

    server_cli._ensure_runtime_dirs()
    assert (tmp_path / "logs").exists()


def test_server_load_settings_and_uri_validation(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    clear_calls: list[str] = []
    monkeypatch.setattr(server_cli, "clear_settings_cache", lambda: clear_calls.append("clear"))
    monkeypatch.setattr(server_cli, "get_settings", lambda: _settings())
    assert server_cli._load_settings().cognito_app_client_id == "client-1"
    assert clear_calls == ["clear"]

    monkeypatch.setattr(
        server_cli, "_load_settings", lambda: (_ for _ in ()).throw(ValueError("bad config"))
    )
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

    monkeypatch.setattr(
        server_cli, "_load_settings", lambda: (_ for _ in ()).throw(ValueError("invalid"))
    )
    assert server_cli._status_bind() == ("unknown", "unknown")


def test_optional_ncbi_api_key_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    key_file = tmp_path / "ncbi-key.txt"

    monkeypatch.setattr(server_cli, "NCBI_API_KEY_FILE", key_file)
    monkeypatch.delenv("NCBI_API_KEY", raising=False)

    server_cli._maybe_set_ncbi_api_key()
    assert "NCBI_API_KEY" not in os.environ

    key_file.write_text("file-key\n", encoding="utf-8")
    server_cli._maybe_set_ncbi_api_key()
    assert os.environ["NCBI_API_KEY"] == "file-key"

    monkeypatch.setenv("NCBI_API_KEY", "already-set")
    key_file.write_text("replacement-key\n", encoding="utf-8")
    server_cli._maybe_set_ncbi_api_key()
    assert os.environ["NCBI_API_KEY"] == "already-set"


def test_tls_resolution_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    shared_dir = tmp_path / "shared"
    repo_dir = tmp_path / "repo"
    explicit_cert = tmp_path / "explicit-cert.pem"
    explicit_key = tmp_path / "explicit-key.pem"
    generic_cert = tmp_path / "generic-cert.pem"
    generic_key = tmp_path / "generic-key.pem"
    shared_cert = shared_dir / "cert.pem"
    shared_key = shared_dir / "key.pem"
    repo_cert = repo_dir / "cert.pem"
    repo_key = repo_dir / "key.pem"

    for path in (
        explicit_cert,
        explicit_key,
        generic_cert,
        generic_key,
        shared_cert,
        shared_key,
        repo_cert,
        repo_key,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    monkeypatch.setattr(server_cli, "CERT_FILE", repo_cert)
    monkeypatch.setattr(server_cli, "KEY_FILE", repo_key)
    monkeypatch.setattr(server_cli, "_shared_cert_dir", lambda: shared_dir)
    monkeypatch.setattr(
        server_cli, "ensure_certs", lambda path: (path / "cert.pem", path / "key.pem")
    )

    assert server_cli._resolve_tls_material(
        ssl_enabled=True,
        cert_path=explicit_cert,
        key_path=explicit_key,
    ) == (explicit_cert, explicit_key)

    monkeypatch.setenv(server_cli.GENERIC_CERT_ENV, str(generic_cert))
    monkeypatch.setenv(server_cli.GENERIC_KEY_ENV, str(generic_key))
    assert server_cli._resolve_tls_material(
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    ) == (generic_cert, generic_key)

    monkeypatch.delenv(server_cli.GENERIC_CERT_ENV, raising=False)
    monkeypatch.delenv(server_cli.GENERIC_KEY_ENV, raising=False)
    assert server_cli._resolve_tls_material(
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    ) == (shared_cert, shared_key)

    shared_cert.unlink()
    shared_key.unlink()
    assert server_cli._resolve_tls_material(
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    ) == (repo_cert, repo_key)


def test_tls_resolution_validation_and_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    shared_dir = tmp_path / "shared"
    repo_dir = tmp_path / "repo"
    repo_cert = repo_dir / "cert.pem"
    repo_key = repo_dir / "key.pem"
    repo_cert.parent.mkdir(parents=True, exist_ok=True)
    repo_key.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(server_cli, "CERT_FILE", repo_cert)
    monkeypatch.setattr(server_cli, "KEY_FILE", repo_key)
    monkeypatch.setattr(server_cli, "_shared_cert_dir", lambda: shared_dir)

    with pytest.raises(typer.BadParameter, match="CLI flags requires both"):
        server_cli._resolve_tls_material(
            ssl_enabled=True,
            cert_path=tmp_path / "cert-only.pem",
            key_path=None,
        )

    monkeypatch.setenv(server_cli.GENERIC_CERT_ENV, str(tmp_path / "generic-cert.pem"))
    monkeypatch.delenv(server_cli.GENERIC_KEY_ENV, raising=False)
    with pytest.raises(
        typer.BadParameter,
        match="environment variables SSL_CERT_FILE/SSL_KEY_FILE requires both",
    ):
        server_cli._resolve_tls_material(
            ssl_enabled=True,
            cert_path=None,
            key_path=None,
        )

    monkeypatch.delenv(server_cli.GENERIC_CERT_ENV, raising=False)
    generated_cert = shared_dir / "cert.pem"
    generated_key = shared_dir / "key.pem"
    calls: list[Path] = []

    def fake_ensure_certs(path: Path) -> tuple[Path, Path]:
        calls.append(path)
        path.mkdir(parents=True, exist_ok=True)
        generated_cert.write_text("cert", encoding="utf-8")
        generated_key.write_text("key", encoding="utf-8")
        return generated_cert, generated_key

    monkeypatch.setattr(server_cli, "ensure_certs", fake_ensure_certs)
    assert server_cli._resolve_tls_material(
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    ) == (generated_cert, generated_key)
    assert calls == [shared_dir]

    monkeypatch.setattr(
        server_cli, "ensure_certs", lambda path: (_ for _ in ()).throw(SystemExit("mkcert missing"))
    )
    generated_cert.unlink()
    generated_key.unlink()
    with pytest.raises(typer.BadParameter, match="mkcert missing"):
        server_cli._resolve_tls_material(
            ssl_enabled=True,
            cert_path=None,
            key_path=None,
        )

    assert server_cli._resolve_tls_material(
        ssl_enabled=False,
        cert_path=None,
        key_path=None,
    ) == (None, None)


def test_start_server_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(server_cli, "_ensure_runtime_dirs", lambda: None)
    monkeypatch.setattr(server_cli, "_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(server_cli, "_log_dir", lambda: tmp_path)
    monkeypatch.setattr(server_cli, "_runtime_meta_file", lambda: tmp_path / "server-meta.json")
    monkeypatch.setattr(server_cli, "NCBI_API_KEY_FILE", tmp_path / "ncbi-key.txt")
    monkeypatch.delenv("NCBI_API_KEY", raising=False)

    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("cert", encoding="utf-8")
    key.write_text("key", encoding="utf-8")
    monkeypatch.setattr(
        server_cli,
        "_resolve_tls_material",
        lambda **kwargs: (cert, key) if kwargs["ssl_enabled"] else (None, None),
    )

    monkeypatch.setattr(server_cli, "read_pid", lambda path: 321)
    server_cli._start_server(
        host="0.0.0.0",
        port=8914,
        reload=False,
        background=True,
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    )

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
        server_cli._start_server(
            host="0.0.0.0",
            port=8914,
            reload=True,
            background=True,
            ssl_enabled=True,
            cert_path=None,
            key_path=None,
        )
    assert exc.value.exit_code == 1

    writes: list[int] = []
    commands: list[list[str]] = []

    class RunningProc:
        pid = 555

        @staticmethod
        def poll():
            return None

    def fake_popen(cmd, *args, **kwargs):
        commands.append(cmd)
        assert kwargs["env"]["NCBI_API_KEY"] == "bg-key"
        return RunningProc()

    (tmp_path / "ncbi-key.txt").write_text("bg-key\n", encoding="utf-8")
    monkeypatch.setattr(server_cli.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(server_cli, "write_pid", lambda path, pid: writes.append(pid))
    server_cli._start_server(
        host="0.0.0.0",
        port=8914,
        reload=False,
        background=True,
        ssl_enabled=True,
        cert_path=None,
        key_path=None,
    )
    assert writes == [555]
    assert os.environ["NCBI_API_KEY"] == "bg-key"
    assert "--ssl-certfile" in commands[0]
    assert "--ssl-keyfile" in commands[0]

    uvicorn_calls: list[dict[str, object]] = []
    monkeypatch.setattr(server_cli.uvicorn, "run", lambda **kwargs: uvicorn_calls.append(kwargs))
    server_cli._start_server(
        host="127.0.0.1",
        port=8915,
        reload=True,
        background=False,
        ssl_enabled=False,
        cert_path=None,
        key_path=None,
    )
    assert uvicorn_calls[0]["host"] == "127.0.0.1"
    assert uvicorn_calls[0]["port"] == 8915
    assert "ssl_certfile" not in uvicorn_calls[0]
    assert "ssl_keyfile" not in uvicorn_calls[0]


def test_status_scheme_meta(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(server_cli, "_runtime_meta_file", lambda: tmp_path / "server-meta.json")
    assert server_cli._status_scheme() == "https"

    server_cli._write_runtime_meta(ssl_enabled=False)
    assert server_cli._status_scheme() == "http"

    server_cli._write_runtime_meta(ssl_enabled=True)
    assert server_cli._status_scheme() == "https"


def test_stop_server_and_logs_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(server_cli, "_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(server_cli, "_runtime_meta_file", lambda: tmp_path / "server-meta.json")
    (tmp_path / "server-meta.json").write_text('{"ssl_enabled": true}', encoding="utf-8")
    monkeypatch.setattr(server_cli, "stop_pid", lambda path: (True, "Server stopped"))
    server_cli._stop_server()
    assert "Server stopped" in capsys.readouterr().out
    assert not (tmp_path / "server-meta.json").exists()

    monkeypatch.setattr(
        server_cli, "stop_pid", lambda path: (False, "Permission denied stopping PID 1")
    )
    with pytest.raises(typer.Exit) as exc:
        server_cli._stop_server()
    assert exc.value.exit_code == 1

    monkeypatch.setattr(server_cli, "stop_pid", lambda path: (False, "No server running"))
    server_cli._stop_server()
    assert "No server running" in capsys.readouterr().err

    monkeypatch.setattr(server_cli, "_ensure_runtime_dirs", lambda: None)
    monkeypatch.setattr(server_cli, "_log_dir", lambda: tmp_path)
    monkeypatch.setattr(server_cli, "list_logs", lambda path: [])
    server_cli.logs(all_logs=True)
    assert "No log files found" in capsys.readouterr().err

    log_file = tmp_path / "server_1.log"
    log_file.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(server_cli, "list_logs", lambda path: [log_file])
    server_cli.logs(all_logs=True)
    assert "server_1.log" in capsys.readouterr().out

    monkeypatch.setattr(server_cli, "latest_log", lambda path: None)
    server_cli.logs(all_logs=False)
    assert "No log file found" in capsys.readouterr().err

    monkeypatch.setattr(server_cli, "latest_log", lambda path: log_file)
    followed: list[tuple[Path, int]] = []
    monkeypatch.setattr(
        server_cli, "tail_follow", lambda path, lines=50: followed.append((path, lines))
    )
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
    monkeypatch.setattr(
        server_cli,
        "_validate_cognito_uris_for_port",
        lambda **kwargs: start_calls.append({"validated": kwargs}),
    )
    monkeypatch.setattr(server_cli, "_start_server", lambda **kwargs: start_calls.append(kwargs))

    server_cli.start(reload=True, background=False)
    assert start_calls[0]["validated"] == {"port": 9002, "host": "127.0.0.1"}
    assert start_calls[1] == {
        "host": "127.0.0.1",
        "port": 9002,
        "reload": True,
        "background": False,
        "ssl_enabled": True,
        "cert_path": None,
        "key_path": None,
    }

    stop_calls: list[str] = []
    monkeypatch.setattr(server_cli, "_stop_server", lambda: stop_calls.append("stop"))
    server_cli.stop()
    assert stop_calls == ["stop"]


def test_db_cli_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_cli, "ensure_tapdb_version", lambda: "3.0.6")

    with pytest.raises(typer.Exit) as exc:
        db_cli.build(
            target="aurora", cluster="", profile="team-profile", region="us-west-2", namespace="dewey"
        )
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
        db_cli.build(
            target="local", cluster="", profile="team-profile", region="us-west-2", namespace="dewey"
        )
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
            profile="team-profile",
            region="us-west-2",
            namespace="dewey",
        )
    assert exc.value.exit_code == 1


def test_db_cli_resolves_profile_from_config_when_flag_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    monkeypatch.setattr(db_cli, "ensure_tapdb_version", lambda: "3.0.6")
    monkeypatch.setattr(db_cli, "load_config_aws_profile", lambda: "config-profile")
    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda args, **kwargs: (calls.append(("run", kwargs)) or _proc(returncode=0, stdout="ok")),
    )
    monkeypatch.setattr(
        db_cli,
        "export_database_url_for_target",
        lambda **kwargs: (calls.append(("export", kwargs)) or "postgresql+psycopg2://dewey@localhost:5432/dewey"),
    )
    monkeypatch.setattr(db_cli.subprocess, "run", lambda *args, **kwargs: None)

    db_cli.build(target="local", cluster="", profile="", region="us-west-2", namespace="dewey")

    assert calls == [
        (
            "run",
            {
                "target": "local",
                "client_id": db_cli.DEFAULT_TAPDB_CLIENT_ID,
                "profile": "config-profile",
                "region": "us-west-2",
                "namespace": "dewey",
                "cwd": db_cli.PROJECT_ROOT,
            },
        ),
        (
            "export",
            {
                "target": "local",
                "client_id": db_cli.DEFAULT_TAPDB_CLIENT_ID,
                "profile": "config-profile",
                "region": "us-west-2",
                "namespace": "dewey",
            },
        ),
    ]


def test_db_cli_requires_profile_source(monkeypatch: pytest.MonkeyPatch) -> None:
    errors: list[str] = []

    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(db_cli, "ensure_tapdb_version", lambda: "3.0.6")
    monkeypatch.setattr(db_cli, "load_config_aws_profile", lambda: "")
    monkeypatch.setattr(db_cli.ccyo_out, "error", lambda message: errors.append(message))

    with pytest.raises(typer.Exit) as exc:
        db_cli.build(target="local", cluster="", profile="", region="us-west-2", namespace="dewey")

    assert exc.value.exit_code == 1
    assert errors == [
        "DB build failed: AWS profile is required; set --profile, DEWEY_AWS_PROFILE, aws.profile, or AWS_PROFILE."
    ]


def test_db_cli_reset_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        db_cli,
        "run_tapdb_cli",
        lambda args, **kwargs: (
            calls.append(("delete", args)) or _proc(returncode=0, stdout="deleted")
        ),
    )
    monkeypatch.setattr(
        db_cli,
        "build",
        lambda **kwargs: calls.append(("build", kwargs)),
    )

    db_cli.reset(
        force=True,
        target="local",
        cluster="cluster-1",
        profile="team-profile",
        region="us-west-2",
        namespace="dewey",
    )

    assert calls == [
        ("delete", ["db", "delete", "dev", "--force"]),
        (
            "build",
            {
                "target": "local",
                "cluster": "cluster-1",
                "profile": "team-profile",
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
        lambda args, **kwargs: (
            calls.append(("delete", args)) or _proc(returncode=0, stdout="deleted")
        ),
    )
    monkeypatch.setattr(
        db_cli,
        "build",
        lambda **kwargs: calls.append(("build", kwargs)),
    )

    db_cli.nuke(
        force=True,
        target="aurora",
        profile="team-profile",
        region="us-west-2",
        namespace="dewey",
    )

    assert calls == [("delete", ["db", "delete", "prod", "--force"])]
