from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from dewey_service.integrations import tapdb_runtime


def test_ensure_tapdb_version_requires_exact_released_pair(monkeypatch):
    versions = {"daylily-tapdb": "10.1.1rc1", "meridian-euid": "0.4.8"}
    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", versions.__getitem__)
    assert tapdb_runtime.ensure_tapdb_version() == "10.1.1rc1"
    for package, wrong in (("daylily-tapdb", "10.1.1"), ("meridian-euid", "0.4.7")):
        expected = versions[package]
        versions[package] = wrong
        with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="must be exactly"):
            tapdb_runtime.ensure_tapdb_version()
        versions[package] = expected


def test_ensure_tapdb_version_requires_install(monkeypatch):
    def missing(name):
        raise tapdb_runtime.importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(tapdb_runtime.importlib.metadata, "version", missing)
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="required but not installed"):
        tapdb_runtime.ensure_tapdb_version()


@pytest.mark.parametrize("path", ["", "relative.yaml", "/missing/config.yaml"])
def test_tapdb_path_has_no_environment_or_discovery_fallback(path):
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="config"):
        tapdb_runtime._resolve_tapdb_config_path(
            namespace="dewey", client_id="dewey", config_path=path
        )


def test_runtime_config_resolves_declared_scope(test_settings):
    cfg = tapdb_runtime.load_runtime_config(test_settings)
    assert cfg["domain_code"] == "Z"
    assert cfg["owner_repo_name"] == "dewey"
    assert cfg["database"] == "dewey_test"


@pytest.mark.parametrize(
    "field,value",
    [
        ("tapdb_domain_code", "M"),
        ("tapdb_owner_repo_name", "another"),
        ("database_target", "aurora"),
    ],
)
def test_runtime_config_rejects_scope_disagreement(test_settings, field, value):
    setattr(test_settings, field, value)
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="disagrees"):
        tapdb_runtime.load_runtime_config(test_settings)


def test_run_tapdb_cli_preserves_exact_config_and_argv(monkeypatch, explicit_tapdb_test_config):
    seen = {}
    monkeypatch.setattr(tapdb_runtime, "_resolve_tapdb_cli_executable", lambda: "/test/bin/tapdb")
    monkeypatch.setenv("MERIDIAN_DOMAIN_CODE", "Z")
    monkeypatch.setenv("TAPDB_OWNER_REPO", "dewey")

    def run(argv, **kwargs):
        seen.update(argv=argv, **kwargs)
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    monkeypatch.setattr(tapdb_runtime.subprocess, "run", run)
    tapdb_runtime.run_tapdb_cli(
        ["db", "schema", "drift-check", "--json", "--strict"],
        target="local",
        client_id="dewey",
        profile="test-profile",
        region="us-west-2",
        namespace="dewey",
        config_path=str(explicit_tapdb_test_config),
    )
    assert seen["argv"] == [
        "/test/bin/tapdb",
        "--config",
        str(explicit_tapdb_test_config),
        "db",
        "schema",
        "drift-check",
        "--json",
        "--strict",
    ]
    assert seen["env"]["AWS_PROFILE"] == "test-profile"
    assert "MERIDIAN_DOMAIN_CODE" not in seen["env"]
    assert "TAPDB_OWNER_REPO" not in seen["env"]
    assert "shell" not in seen


@pytest.mark.parametrize("stdout", ["", "not-json", "[]"])
def test_drift_check_rejects_invalid_success_receipts(
    monkeypatch, explicit_tapdb_test_config, stdout
):
    monkeypatch.setattr(
        tapdb_runtime,
        "run_tapdb_cli",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=stdout, stderr=""),
    )
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="JSON"):
        tapdb_runtime.run_schema_drift_check(
            target="local",
            client_id="dewey",
            profile="test",
            region="us-west-2",
            namespace="dewey",
            config_path=str(explicit_tapdb_test_config),
        )


@pytest.mark.parametrize("returncode,status", [(0, "clean"), (1, "drift"), (2, "error")])
def test_drift_receipt_preserves_native_status_and_command_local_json(
    monkeypatch, explicit_tapdb_test_config, returncode, status
):
    payload = {
        "status": status,
        "strict": True,
        "counts": {"expected": {"tables": 2}, "live": {"tables": 2}},
    }
    seen = []

    def run(args, **kwargs):
        seen.append(args)
        assert kwargs["config_path"] == str(explicit_tapdb_test_config)
        assert kwargs["check"] is False
        return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(tapdb_runtime, "run_tapdb_cli", run)
    result = tapdb_runtime.run_schema_drift_check(
        target="local",
        client_id="dewey",
        profile="test",
        region="us-west-2",
        namespace="dewey",
        config_path=str(explicit_tapdb_test_config),
    )
    assert seen == [["db", "schema", "drift-check", "--json", "--strict"]]
    assert result["status"] == (status if returncode < 2 else "check_failed")
    assert result["report"] == payload


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "error"},
        {"status": "clean", "strict": False},
        {"status": "clean", "strict": True, "counts": {"expected": 1, "live": 1}},
    ],
)
def test_drift_does_not_treat_incomplete_success_as_clean(
    monkeypatch, explicit_tapdb_test_config, payload
):
    monkeypatch.setattr(
        tapdb_runtime,
        "run_tapdb_cli",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="incomplete or inconsistent"):
        tapdb_runtime.run_schema_drift_check(
            target="local",
            client_id="dewey",
            profile="test",
            region="us-west-2",
            namespace="dewey",
            config_path=str(explicit_tapdb_test_config),
        )


def test_cli_target_mismatch_fails_before_subprocess(monkeypatch, explicit_tapdb_test_config):
    monkeypatch.setattr(
        tapdb_runtime.subprocess,
        "run",
        lambda *a, **k: pytest.fail("must not invoke mismatched target"),
    )
    with pytest.raises(tapdb_runtime.TapDBRuntimeError, match="target disagrees"):
        tapdb_runtime.run_tapdb_cli(
            ["db", "status"],
            target="aurora",
            client_id="dewey",
            profile="test",
            region="us-west-2",
            namespace="dewey",
            config_path=str(explicit_tapdb_test_config),
        )
