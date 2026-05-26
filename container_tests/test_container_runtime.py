from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dewey_service import container_entry


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docker_runtime_files_use_foreground_uv_and_no_legacy_runtime() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (PROJECT_ROOT / "docker" / "entrypoint.sh").read_text(encoding="utf-8")

    assert "uv sync --frozen --no-dev --no-install-project" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert "USER lsmc" in dockerfile
    assert "python\", \"-m\", \"dewey_service.container_entry" in dockerfile
    assert ":latest" not in dockerfile
    assert "conda" not in dockerfile.lower()
    assert "tmux" not in entrypoint
    assert "background" not in entrypoint
    assert "${DEWEY_CONFIG:?DEWEY_CONFIG is required}" in entrypoint
    assert "${TAPDB_CONFIG_PATH:?TAPDB_CONFIG_PATH is required}" in entrypoint


def test_container_entry_requires_absolute_config_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEWEY_CONFIG", "relative.yaml")

    with pytest.raises(RuntimeError, match="must be an absolute path"):
        container_entry._required_absolute_file("DEWEY_CONFIG")


def test_container_entry_runs_foreground_http_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "dewey.yaml"
    tapdb_path = tmp_path / "tapdb.yaml"
    config_path.write_text("auth: {}\n", encoding="utf-8")
    tapdb_path.write_text("target: {}\n", encoding="utf-8")
    monkeypatch.setenv("DEWEY_CONFIG", str(config_path))
    monkeypatch.setenv("TAPDB_CONFIG_PATH", str(tapdb_path))
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8914")

    with patch("dewey_service.container_entry._start_server") as start:
        container_entry.main()

    assert start.call_args.kwargs == {
        "host": "127.0.0.1",
        "port": 8914,
        "reload": False,
        "ssl_enabled": False,
        "cert": None,
        "key": None,
        "background": False,
        "check_cognito_uris": False,
    }
