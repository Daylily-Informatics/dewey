"""One new native contract: explicit RC limits across the old 9.0.9 roundtrip.

Run only in a copy of the exact release's tests/schema/config directories,
using the separately installed public wheel and existing disposable PG fixture.
This file adds no TapDB implementation and contains no migration statements.
"""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from daylily_tapdb.cli.db_config import get_db_config
from tests.test_backup_historical_pg import released_source  # noqa: F401
from tests.test_backup_historical_pg import (
    test_released_restore_and_separate_migration_preserve_all_original_rows as run_existing_historical_contract,
)

POLICY = {
    "max_rows": 1000000,
    "max_row_bytes": 8388608,
    "max_receipt_bytes": 536870912,
}


@pytest.fixture(autouse=True)
def rc1_limits_via_native_config(pg_instance):
    assert importlib.metadata.version("daylily-tapdb") == "10.1.1rc1"
    config = str(pg_instance["config_path"])
    # The old fixture intentionally omits admin/backup sections. Prepare it
    # through native init, exactly as required for operator config update.
    root = yaml.safe_load(Path(config).read_text())
    meta, target, safety = root["meta"], root["target"], root["safety"]
    init = [
        str(Path(sys.executable).with_name("tapdb")),
        "--config",
        config,
        "db-config",
        "init",
    ]
    for flag, value in {
        "client-id": meta["client_id"],
        "database-name": meta["database_name"],
        "owner-repo-name": meta["owner_repo_name"],
        "domain-registry-path": meta["domain_registry_path"],
        "prefix-ownership-registry-path": meta["prefix_ownership_registry_path"],
        "engine-type": target["engine_type"],
        "host": target["host"],
        "port": target["port"],
        "ui-port": target["ui_port"],
        "domain-code": target["domain_code"],
        "user": target["user"],
        "password": target["password"],
        "operator-user": target["operator"]["user"],
        "operator-password": target["operator"]["password"],
        "database": target["database"],
        "schema-name": target["schema_name"],
        "tenant-id": target["tenant_id"],
        "safety-tier": safety["safety_tier"],
        "destructive-operations": safety["destructive_operations"],
    }.items():
        init.extend(["--" + flag, str(value)])
    assert target["allow_global_claims"] is True
    assert target["operator"]["iam_auth"] is False
    init.extend(["--allow-global-claims", "--no-operator-iam-auth"])
    initialized = subprocess.run(init, capture_output=True, text=True, check=False)
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    command = [
        str(Path(sys.executable).with_name("tapdb")),
        "--config",
        config,
        "db-config",
        "update",
        "--inventory-max-rows",
        str(POLICY["max_rows"]),
        "--inventory-max-row-bytes",
        str(POLICY["max_row_bytes"]),
        "--inventory-max-receipt-bytes",
        str(POLICY["max_receipt_bytes"]),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert get_db_config(config_path=config)["inventory_limits"] == POLICY


@pytest.mark.parametrize("released_source", ["9.0.9"], indirect=True)
def test_rc1_explicit_limits_survive_historical_native_roundtrip(released_source):  # noqa: F811
    cfg, _settings, contract = released_source
    assert cfg["inventory_limits"] == POLICY
    assert contract["identity_inventory"]["limits"] == POLICY
    assert contract["identity_inventory"]["usage"]["rows"] > 0

    # The unchanged release test creates a full historical backup, restores it,
    # requires rebinding, migrates behind its native fence, verifies postcommit
    # evidence and every original cell hash, and checks no pending recovery.
    # RC receipt comparison rejects differing policies, so success covers the
    # newly added policy propagation across those native stages.
    run_existing_historical_contract(released_source)
