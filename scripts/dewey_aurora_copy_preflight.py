"""Prepare explicit operator inputs and inspect the Dewey copy prerequisites.

Run using targeted sudo from interactive ubuntu. No backup, database creation,
role/grant change, session termination, container stop or migration occurs here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess

import boto3
from daylily_tapdb.cli.db_config import get_db_config
from daylily_tapdb.runtime_principal import operator_connection
from sqlalchemy import text
import yaml

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
SOURCE = ROOT / "source-operator.yaml"
CONTROL = ROOT / "control-operator.yaml"
REHEARSAL = "dewey_tapdb10_rehearsal_20260911"
FINAL = "dewey_prod_tapdb10"


def write(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def prepare_control():
    if CONTROL.exists() or CONTROL.is_symlink():
        raise RuntimeError("Control configuration already exists; inspect it")
    doc = yaml.safe_load(SOURCE.read_text())
    target, meta = doc["target"], doc["meta"]
    expected = {"engine_type": "aurora", "database": "dewey_prod", "domain_code": "M",
                "schema_name": "tapdb_dewey_lsmcok1_local", "cluster_identifier": "dayhoff-lsmcok1-tapdb"}
    if any(target.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Unexpected source configuration")
    if target["operator"]["user"] != "dayhoff":
        raise RuntimeError("Unexpected source operator")
    args = [str(ROOT / "venv/bin/tapdb"), "--config", str(CONTROL), "db-config", "init"]
    for key in ("client_id", "database_name", "owner_repo_name", "domain_registry_path", "prefix_ownership_registry_path"):
        args.extend(["--" + key.replace("_", "-"), str(meta[key])])
    for key in ("engine_type", "host", "port", "ui_port", "schema_name", "domain_code", "cluster_identifier", "region", "sslrootcert"):
        args.extend(["--" + key.replace("_", "-"), str(target[key])])
    args.extend(["--database", "postgres", "--user", "dewey_runtime_9",
                 "--operator-user", "dayhoff", "--operator-secret-arn", target["operator"]["secret_arn"],
                 "--no-operator-iam-auth", "--tenant-id", "", "--no-allow-global-claims",
                 "--no-iam-auth", "--secret-arn", target["operator"]["secret_arn"],
                 "--ssl", "verify-full", "--aws-profile", "lsmc",
                 "--safety-tier", "production", "--destructive-operations", "blocked"])
    subprocess.run(args, check=True)
    print(json.dumps({"control_config": str(CONTROL), "runtime_use_forbidden": True}))


def inspect_control():
    destination = ROOT / "receipts/copy-control-preflight-20260911.json"
    provider_path = ROOT / "receipts/aurora-provider-contract-20260911.json"
    if destination.exists() or provider_path.exists():
        raise RuntimeError("Preflight evidence already exists; inspect before repeating")
    cfg = get_db_config(config_path=CONTROL)
    expected_config = {"engine_type": "aurora", "database": "postgres", "schema_name": "tapdb_dewey_lsmcok1_local",
                       "domain_code": "M", "operator_user": "dayhoff", "cluster_identifier": "dayhoff-lsmcok1-tapdb",
                       "host": "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com"}
    if any(cfg.get(key) != value for key, value in expected_config.items()):
        raise RuntimeError("Control configuration differs from the approved Aurora identity")
    cluster = boto3.Session(profile_name="lsmc").client("rds", region_name="us-west-2").describe_db_clusters(
        DBClusterIdentifier="dayhoff-lsmcok1-tapdb"
    )["DBClusters"]
    if len(cluster) != 1:
        raise RuntimeError("Expected exactly one named Aurora cluster")
    cluster = cluster[0]
    expected = {"Engine": "aurora-postgresql", "EngineVersion": "16.13",
                "DBClusterArn": "arn:aws:rds:us-west-2:108782052779:cluster:dayhoff-lsmcok1-tapdb",
                "DbClusterResourceId": "cluster-AA24MJP2WJNSFOFGXGHAXWHVKU",
                "Endpoint": "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com"}
    if any(cluster.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Aurora provider differs from the reviewed cluster")
    if cluster.get("ClusterScalabilityType") == "limitless":
        raise RuntimeError("Aurora Limitless does not support the reviewed copy")
    with operator_connection(cfg, read_only=True) as connection:
        identity = dict(connection.execute(text("SELECT current_database() AS database, current_user AS operator, current_setting('server_version') AS server_version, inet_server_addr()::text AS server_address, pg_backend_pid() AS backend_pid")).mappings().one())
        databases = [dict(row) for row in connection.execute(text("SELECT d.datname, d.oid::bigint AS oid, pg_get_userbyid(d.datdba) AS owner, d.datallowconn, d.datistemplate, d.datconnlimit, d.datacl::text FROM pg_catalog.pg_database d WHERE d.datname IN (:source, :control, :rehearsal, :target) ORDER BY d.datname"), {"source": "dewey_prod", "control": "postgres", "rehearsal": REHEARSAL, "target": FINAL}).mappings()]
        operator = dict(connection.execute(text("SELECT rolname, rolcanlogin, rolcreatedb, rolsuper, rolcreaterole FROM pg_catalog.pg_roles WHERE rolname=current_user")).mappings().one())
        source_sessions = [dict(row) for row in connection.execute(text("SELECT pid, usename, application_name, client_addr::text, backend_start, state FROM pg_catalog.pg_stat_activity WHERE datname='dewey_prod' ORDER BY pid")).mappings()]
    names = {row["datname"] for row in databases}
    if names != {"postgres", "dewey_prod"}:
        raise RuntimeError("Expected source/control present and BOTH exact destinations absent")
    source_database = next(row for row in databases if row["datname"] == "dewey_prod")
    if source_database["oid"] != 16749 or source_database["owner"] != "dayhoff":
        raise RuntimeError("Source physical identity differs from the approved native census")
    if identity["database"] != "postgres" or identity["operator"] != "dayhoff":
        raise RuntimeError("Actual control connection differs from the approved operator/database")
    if not operator["rolcreatedb"]:
        raise RuntimeError("Explicit operator cannot create the replacement database")
    provider = {"schema_version": "tapdb-fence-provider/v1", "engine": expected["Engine"],
                "engine_version": expected["EngineVersion"], "aws_profile": "lsmc", "region": "us-west-2",
                "cluster_identifier": "dayhoff-lsmcok1-tapdb", "cluster_arn": expected["DBClusterArn"],
                "cluster_resource_id": expected["DbClusterResourceId"], "writer_endpoint": expected["Endpoint"], "sslmode": "verify-full"}
    write(provider_path, provider)
    receipt = {"purpose": "Operator-owned read-only copy prerequisite census; no writer fence",
               "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(), "control_config": str(CONTROL),
               "control_identity": identity, "databases": databases, "operator": operator,
               "source_sessions": source_sessions, "cluster_scalability_type": cluster.get("ClusterScalabilityType"),
               "engine_mode": cluster["EngineMode"], "provider_contract": str(provider_path),
               "provider_file_sha256": hashlib.sha256(provider_path.read_bytes()).hexdigest(),
               "backup_operation_performed": False, "database_mutation_performed": False}
    write(destination, receipt)
    print(json.dumps(receipt, sort_keys=True, default=str))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare-control", "inspect-control"))
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from the approved interactive ubuntu session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Require the exact released RC")
    {"prepare-control": prepare_control, "inspect-control": inspect_control}[args.operation]()


if __name__ == "__main__":
    main()
