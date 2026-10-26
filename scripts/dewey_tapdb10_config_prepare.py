"""Prepare new explicit Dewey/TapDB configurations using the approved setup SOP.

Native config init/update owns the schema. One reviewed production_like field
has no native CLI flag. Existing active configurations remain untouched; no
database connection, principal binding, backup or application start occurs.
"""

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess

from daylily_tapdb.cli.db_config import get_admin_settings, get_db_config
import yaml

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
SOURCE_TAPDB = Path("/home/ubuntu/.config/tapdb/dewey/dewey-day/tapdb-config.yaml")
SOURCE_DEWEY = Path("/home/ubuntu/.config/dewey-day/dewey-config-day.yaml")
TARGETS = {
    "rehearsal": {
        "database": "dewey_tapdb10_rehearsal_20260911", "role": "dewey_rehearsal_9",
        "secret": "arn:aws:secretsmanager:us-west-2:108782052779:secret:/dayhoff/day/dewey/9.0.0/rehearsal-runtime-20260911-uwqxtM",
        "directory": "/opt/dewey/day/releases/tapdb10-rehearsal-20260911", "operator": "rehearsal-operator.yaml",
    },
    "production": {
        "database": "dewey_prod_tapdb10", "role": "dewey_runtime_9",
        "secret": "arn:aws:secretsmanager:us-west-2:108782052779:secret:/dayhoff/day/dewey/9.0.0/runtime-TiiOqx",
        "directory": "/opt/dewey/day/releases/9.0.0", "operator": "replacement-operator.yaml",
    },
}


def run(arguments):
    subprocess.run(arguments, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=tuple(TARGETS))
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from interactive ubuntu")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Exact RC required")
    binding = TARGETS[args.target]
    directory = Path(binding["directory"])
    runtime = directory / "tapdb-runtime.yaml"
    dewey_path = directory / "dewey-config.yaml"
    operator = ROOT / binding["operator"]
    receipt = ROOT / "receipts" / f"{args.target}-config-preparation.json"
    if directory.exists() or operator.exists() or receipt.exists():
        raise RuntimeError("A prepared destination already exists; inspect instead of overwriting")
    original = yaml.safe_load(SOURCE_TAPDB.read_text())
    target, meta = original["target"], original["meta"]
    if target["database"] != "dewey_prod" or target["domain_code"] != "M" or target["user"] != "dayhoff":
        raise RuntimeError("Unexpected original TapDB identity")
    if target["host"] != "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com":
        raise RuntimeError("Unexpected original Aurora endpoint")
    source_dewey = yaml.safe_load(SOURCE_DEWEY.read_text())
    if source_dewey["database"]["config_path"] != str(SOURCE_TAPDB):
        raise RuntimeError("Dewey source wiring differs from the verified deployment")
    directory.mkdir(mode=0o700)
    for path, is_operator in ((operator, True), (runtime, False)):
        command = [str(ROOT / "venv/bin/tapdb"), "--config", str(path), "db-config", "init"]
        for key in ("client_id", "database_name", "owner_repo_name", "domain_registry_path", "prefix_ownership_registry_path"):
            command.extend(["--" + key.replace("_", "-"), str(meta[key])])
        for key in ("engine_type", "host", "port", "ui_port", "schema_name", "domain_code", "cluster_identifier", "region", "sslrootcert"):
            command.extend(["--" + key.replace("_", "-"), str(target[key])])
        command.extend(["--database", binding["database"], "--user", binding["role"],
                        "--tenant-id", "", "--no-allow-global-claims", "--no-iam-auth",
                        "--secret-arn", binding["secret"], "--ssl", "verify-full", "--aws-profile", "lsmc",
                        "--safety-tier", "production", "--destructive-operations", "blocked"])
        if is_operator:
            command.extend(["--operator-user", "dayhoff", "--operator-secret-arn", target["secret_arn"], "--no-operator-iam-auth"])
        run(command)
        run([str(ROOT / "venv/bin/tapdb"), "--config", str(path), "db-config", "update",
             "--inventory-max-rows", "1000000", "--inventory-max-row-bytes", "8388608",
             "--inventory-max-receipt-bytes", "536870912", "--admin-auth-mode", "tapdb",
             "--admin-allowed-origin", "https://dewey.day.lsmc.bio"])
        doc = yaml.safe_load(path.read_text())
        if not isinstance(doc, dict) or not isinstance(doc.get("admin"), dict):
            raise RuntimeError("Native-generated admin shape differs")
        before = copy.deepcopy(doc)
        if "security" not in doc["admin"]:
            doc["admin"]["security"] = {}
        security = doc["admin"]["security"]
        if not isinstance(security, dict) or ("production_like" in security and not isinstance(security["production_like"], bool)):
            raise RuntimeError("Unexpected production_like configuration shape")
        security["production_like"] = True
        stripped = copy.deepcopy(doc)
        if "security" in before["admin"]:
            stripped["admin"]["security"] = before["admin"]["security"]
        else:
            del stripped["admin"]["security"]
        if stripped != before:
            raise RuntimeError("Unexpected non-security configuration change")
        path.write_text(yaml.safe_dump(doc, sort_keys=False))
        os.chmod(path, 0o600)
        cfg = get_db_config(config_path=path, client_id="dewey", database_name="dewey-day")
        admin = get_admin_settings(config_path=path)
        if cfg["database"] != binding["database"] or cfg["user"] != binding["role"] or cfg["secret_arn"] != binding["secret"]:
            raise RuntimeError("Native target validation differs")
        if bool(cfg["operator_configured"]) != is_operator:
            raise RuntimeError("Runtime/operator separation validation failed")
        if not admin["session_secret"] or admin["auth_mode"] != "tapdb" or admin["production_like"] is not True or admin["allowed_origins"] != ["https://dewey.day.lsmc.bio"]:
            raise RuntimeError("Native admin configuration validation failed")
    dewey = copy.deepcopy(source_dewey)
    dewey["database"]["config_path"] = str(runtime)
    dewey["aws"] = {"profile": "lsmc", "region": "us-west-2"}
    with dewey_path.open("x") as handle:
        yaml.safe_dump(dewey, handle, sort_keys=False)
    result = {"target": args.target, "database": binding["database"], "role": binding["role"],
              "operator_config": str(operator), "runtime_config": str(runtime), "dewey_config": str(dewey_path),
              "source_dewey_sha256": hashlib.sha256(SOURCE_DEWEY.read_bytes()).hexdigest(),
              "config_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (operator, runtime, dewey_path)},
              "runtime_has_operator_credentials": False, "production_like": True,
              "dewey_changed_fields": ["database.config_path", "aws.profile", "aws.region"],
              "database_connection_performed": False, "original_config_changed": False}
    with receipt.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
