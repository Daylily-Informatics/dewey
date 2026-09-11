"""Exercise the released TapDB context with a real Dewey CLI context present."""

from pathlib import Path

import pytest
from cli_core_yo import runtime as cli_runtime
from cli_core_yo.xdg import resolve_paths
from daylily_tapdb.cli.context import (
    active_config_path,
    active_context_overrides,
    clear_cli_context,
)
from daylily_tapdb.cli.db_config import get_admin_settings
from daylily_tapdb.web.runtime import dispose_all_runtime_engines

from dewey_service import container_entry
from dewey_service.cli import spec
from dewey_service.integrations import tapdb_runtime
from dewey_service.tapdb_backend import TapDBBackend


@pytest.fixture(autouse=True)
def isolated_process_context():
    cli_runtime._reset()
    clear_cli_context()
    yield
    dispose_all_runtime_engines()
    clear_cli_context()
    cli_runtime._reset()


@pytest.mark.parametrize("entrypoint", ["container", "qeo-package-cli"])
def test_backend_keeps_dewey_context_and_binds_released_tapdb_metrics(
    entrypoint, monkeypatch, test_settings, explicit_config_file
):
    if entrypoint == "container":
        container_entry._initialize_runtime_context(explicit_config_file)
    else:
        cli_runtime.initialize(
            spec,
            resolve_paths(spec.xdg),
            config_path=explicit_config_file,
            invocation={"command": "qeo package register"},
        )
    dewey_context = cli_runtime.get_context()
    assert active_config_path() == explicit_config_file
    # Reproduce the actual no-path settings failure before Dewey binds TapDB.
    with pytest.raises(RuntimeError, match="TapDB config metadata is required"):
        get_admin_settings()

    monkeypatch.setattr("dewey_service.tapdb_backend.get_settings", lambda: test_settings)
    backend = TapDBBackend()
    tapdb_path = Path(test_settings.tapdb_config_path)
    assert backend.domain_code == test_settings.tapdb_domain_code
    assert active_context_overrides() == {
        "client_id": test_settings.tapdb_client_id,
        "database_name": test_settings.tapdb_database_name,
        "config_path": tapdb_path,
    }
    assert get_admin_settings() == get_admin_settings(config_path=tapdb_path)
    assert cli_runtime.get_context() is dewey_context
    assert dewey_context.config_path == explicit_config_file


@pytest.mark.parametrize(
    "field,value",
    [
        ("tapdb_domain_code", "M"),
        ("tapdb_owner_repo_name", "another"),
        ("database_target", "aurora"),
    ],
)
def test_invalid_target_does_not_bind_tapdb_context(
    field, value, test_settings, explicit_config_file
):
    container_entry._initialize_runtime_context(explicit_config_file)
    before = active_context_overrides()
    setattr(test_settings, field, value)
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="disagrees"):
        tapdb_runtime.load_runtime_config(test_settings)
    assert active_context_overrides() == before
    assert cli_runtime.get_context().config_path == explicit_config_file
