#!/usr/bin/env python3
"""One-time, explicit Dewey 9 principal SOP using released TapDB public APIs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Any

OPERATOR_FIELDS = (
    "operator_user",
    "operator_password",
    "operator_secret_arn",
    "operator_iam_auth",
    "operator_configured",
)
MATCH_FIELDS = (
    "engine_type",
    "host",
    "hostaddr",
    "port",
    "server_port",
    "database",
    "schema_name",
    "client_id",
    "database_name",
    "domain_code",
    "owner_repo_name",
    "user",
    "tenant_id",
    "allow_global_claims",
    "iam_auth",
    "secret_arn",
    "password",
    "region",
    "cluster_identifier",
    "aws_profile",
    "ssl",
    "domain_registry_path",
    "prefix_ownership_registry_path",
)
LANES = {
    "rehearsal": {
        "directory": "/opt/dewey/day/releases/tapdb10-rehearsal-20260911",
        "operator": "/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-operator.yaml",
        "database": "dewey_tapdb10_rehearsal_20260911",
        "user": "dewey_rehearsal_9",
    },
    "production": {
        "directory": "/opt/dewey/day/releases/9.0.0",
        "operator": "/home/ubuntu/dewey_ops/tapdb101-20260911/replacement-operator.yaml",
        "database": "dewey_prod_tapdb10",
        "user": "dewey_runtime_9",
    },
}
EXPECTED = {
    "engine_type": "aurora",
    "host": "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com",
    "port": "5432",
    "schema_name": "tapdb_dewey_lsmcok1_local",
    "client_id": "dewey",
    "database_name": "dewey-day",
    "domain_code": "M",
    "owner_repo_name": "dewey",
    "region": "us-west-2",
    "cluster_identifier": "dayhoff-lsmcok1-tapdb",
    "aws_profile": "lsmc",
}


class PreparationError(RuntimeError):
    """A safe, credential-free operator input failure."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise PreparationError(reason)


def absolute_file(value: str | Path, *, private: bool = False) -> Path:
    path = Path(value)
    require(path.is_absolute() and path.is_file(), "Existing absolute file required")
    require(path.resolve() == path, "Canonical file path required; no symlink path")
    if private:
        require(path.stat().st_mode & 0o077 == 0, "Configuration must remain private")
    return path


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sealed(payload: dict[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in payload.items() if key != "sha256"}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {**body, "sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def require_new_output(path: Path) -> None:
    require(path.is_absolute() and path.parent.is_dir(), "Absolute receipt parent required")
    require(path.parent.resolve() == path.parent, "Canonical receipt directory required")
    require(path.parent.stat().st_mode & 0o077 == 0, "Receipt directory must be private")
    require(not path.exists() and not path.is_symlink(), "Output already exists")


def write_new(path: Path, payload: dict[str, Any]) -> None:
    require_new_output(path)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_sealed(path: Path) -> dict[str, Any]:
    payload = json.loads(absolute_file(path).read_text())
    require(isinstance(payload, dict) and payload == sealed(payload), "Invalid review receipt")
    return payload


def check_versions() -> None:
    for package, expected in (("daylily-tapdb", "10.1.1rc1"), ("meridian-euid", "0.4.8")):
        require(importlib.metadata.version(package) == expected, f"Wrong installed {package}")


def validate_runtime(cfg: dict[str, Any], lane: str, path: Path) -> None:
    expected = {**EXPECTED, "database": LANES[lane]["database"], "user": LANES[lane]["user"]}
    require(str(path) == LANES[lane]["directory"] + "/tapdb-runtime.yaml", "Wrong runtime path")
    require(cfg["config_path"] == str(path), "Resolved runtime path changed")
    for key, value in expected.items():
        require(str(cfg.get(key)) == value, f"Unexpected runtime field: {key}")
    require(cfg.get("operator_configured") is False, "Runtime contains operator configuration")
    require(not any(cfg.get(key) for key in OPERATOR_FIELDS), "Runtime contains operator fields")
    require(cfg.get("iam_auth") in (False, "false"), "Runtime IAM must be explicitly false")
    require(cfg.get("password") == "" and bool(cfg.get("secret_arn")), "Runtime secret required")


def reviewed_overlay(
    runtime: dict[str, Any], operator: dict[str, Any], *, expected_operator_secret: str
) -> dict[str, Any]:
    for key in MATCH_FIELDS:
        require(runtime.get(key) == operator.get(key), f"Runtime/operator disagree: {key}")
    require(operator.get("operator_user") == "dayhoff", "Unexpected operator role")
    require(operator.get("operator_configured") is True, "Operator mapping required")
    require(operator.get("operator_iam_auth") is False, "Operator IAM must be false")
    require(operator.get("operator_password") == "", "Plaintext operator password forbidden")
    require(bool(expected_operator_secret), "Expected operator secret ARN required")
    require(
        operator.get("operator_secret_arn") == expected_operator_secret,
        "Operator secret reference changed",
    )
    return {**runtime, **{key: operator[key] for key in OPERATOR_FIELDS}}


def resolve_inputs(args) -> tuple[dict[str, Any], dict[str, Any]]:
    from daylily_tapdb.cli.db_config import get_db_config

    runtime_path = absolute_file(args.runtime_config, private=True)
    runtime_hash = file_sha(runtime_path)
    runtime = get_db_config(config_path=runtime_path, client_id="dewey", database_name="dewey-day")
    validate_runtime(runtime, args.lane, runtime_path)
    operator_path = absolute_file(args.operator_config, private=True)
    operator_hash = file_sha(operator_path)
    require(str(operator_path) == LANES[args.lane]["operator"], "Wrong operator path")
    operator = get_db_config(
        config_path=operator_path, client_id="dewey", database_name="dewey-day"
    )
    require(operator["config_path"] == str(operator_path), "Resolved operator path changed")
    reference_path = absolute_file(args.runtime_secret_record)
    reference = json.loads(reference_path.read_text())
    require(reference["role"] == runtime["user"], "Secret record role mismatch")
    require(reference["target"] == args.lane, "Secret record lane mismatch")
    require(reference["secret_arn"] == runtime["secret_arn"], "Runtime secret reference changed")
    require(bool(reference["version_id"]), "Runtime secret version required")
    require(bool(args.operator_secret_version), "Operator secret version required")
    overlay = reviewed_overlay(runtime, operator, expected_operator_secret=args.operator_secret_arn)
    require(file_sha(runtime_path) == runtime_hash, "Runtime config changed during resolution")
    require(file_sha(operator_path) == operator_hash, "Operator config changed during resolution")
    inputs = {
        "launcher_sha256": file_sha(Path(__file__).resolve()),
        "lane": args.lane,
        "runtime_config": str(runtime_path),
        "runtime_config_sha256": runtime_hash,
        "operator_config": str(operator_path),
        "operator_config_sha256": operator_hash,
        "runtime_secret_record_sha256": file_sha(reference_path),
        "runtime_secret_arn": reference["secret_arn"],
        "runtime_secret_version": reference["version_id"],
        "operator_secret_arn": args.operator_secret_arn,
        "operator_secret_version": args.operator_secret_version,
        "registry_sha256": {
            key: file_sha(absolute_file(runtime[key]))
            for key in ("domain_registry_path", "prefix_ownership_registry_path")
        },
        "operator_tls_ca_sha256": file_sha(absolute_file(runtime["sslrootcert"])),
    }
    return overlay, inputs


def prepare(args) -> Path:
    from daylily_tapdb.runtime_principal import bind_runtime_principal, bootstrap_runtime_principal

    cfg, inputs = resolve_inputs(args)
    receipt = Path(args.receipt)
    result_path = receipt.with_name(receipt.stem + ".result.json")
    context_path = receipt.with_name(receipt.stem + ".inputs.json")
    require(receipt.is_absolute(), "Absolute receipt path required")
    require(not result_path.exists(), "Result exists; review before any new operation")
    require_new_output(result_path)
    if args.phase.endswith("-plan"):
        require_new_output(receipt)
    if args.phase == "bootstrap-plan":
        plan = bootstrap_runtime_principal(cfg, apply=False)
        write_new(receipt, sealed({"operation": "bootstrap", "inputs": inputs, "native": plan}))
        return receipt
    if args.phase == "bootstrap-apply":
        reviewed = read_sealed(receipt)
        require(reviewed["operation"] == "bootstrap", "Wrong reviewed operation")
        require(reviewed["inputs"] == inputs, "Reviewed bootstrap inputs changed")
        require(
            reviewed["native"] == bootstrap_runtime_principal(cfg, apply=False),
            "Reviewed bootstrap plan changed",
        )
        result = bootstrap_runtime_principal(cfg, apply=True)
        write_new(result_path, sealed({"inputs": inputs, "native": result}))
        require(result["status"] == "applied", "Bootstrap result is not applied")
        return result_path
    if args.phase == "bind-plan":
        require_new_output(context_path)
        # Native bind owns its exact canonical plan and later .result.json.
        bind_runtime_principal(cfg, apply=False, receipt_path=receipt)
        write_new(context_path, sealed({"operation": "bind", "inputs": inputs}))
        return receipt
    reviewed = read_sealed(context_path)
    require(reviewed["operation"] == "bind", "Wrong reviewed operation")
    require(reviewed["inputs"] == inputs, "Reviewed binding inputs changed")
    result = bind_runtime_principal(cfg, apply=True, receipt_path=receipt)
    require(result["status"] == "applied", "Binding result is not applied")
    require(result["runtime_temp_denied"] is True, "Binding did not deny runtime TEMP")
    require(result["privileges_verified"] is True, "Binding privileges not verified")
    return result_path


def verify_runtime(args) -> Path:
    from daylily_tapdb import TemplateManager
    from daylily_tapdb.cli.db_config import get_db_config
    from daylily_tapdb.web.runtime import dispose_all_runtime_engines, get_db
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from dewey_service.tapdb_backend import BOOT_TEMPLATE_DEFINITIONS

    path = absolute_file(args.runtime_config, private=True)
    cfg = get_db_config(config_path=path, client_id="dewey", database_name="dewey-day")
    validate_runtime(cfg, args.lane, path)
    require(importlib.metadata.version("dewey-service") == "9.0.0", "Wrong Dewey image version")
    receipt = Path(args.receipt)
    require_new_output(receipt)
    result: dict[str, Any] = {"lane": args.lane, "runtime_config_sha256": file_sha(path)}
    try:
        dispose_all_runtime_engines()
        db = get_db(str(path))
        db.app_username = "dewey-migration-acceptance"
        with db.session_scope(commit=False) as session:
            row = dict(
                session.execute(
                    text("""
                SELECT current_database() AS database, current_user AS role,
                  session_user AS login, pg_backend_pid() AS backend_pid,
                  has_database_privilege(current_user,current_database(),'CONNECT') AS connect,
                  has_database_privilege(current_user,current_database(),'TEMP') AS temp,
                  has_database_privilege(current_user,current_database(),'CREATE') AS db_create,
                  has_schema_privilege(current_user,:schema,'CREATE') AS schema_create,
                  current_setting('session.current_config_identity') AS config_identity,
                  current_setting('session.current_domain_code') AS domain,
                  current_setting('session.current_owner_repo_name') AS owner,
                  current_setting('session.current_tenant_id') AS tenant,
                  current_setting('session.allow_global_rows') AS allow_global,
                  rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolreplication, rolinherit
                FROM pg_catalog.pg_roles WHERE rolname=current_user
            """),
                    {"schema": cfg["schema_name"]},
                )
                .mappings()
                .one()
            )
            for key in (
                "temp",
                "db_create",
                "schema_create",
                "rolsuper",
                "rolbypassrls",
                "rolcreatedb",
                "rolcreaterole",
                "rolreplication",
                "rolinherit",
            ):
                require(row[key] is False, f"Runtime retains forbidden privilege: {key}")
            require(row["connect"] is True, "Runtime CONNECT missing")
            require(row["database"] == cfg["database"], "Runtime database mismatch")
            require(row["role"] == row["login"] == cfg["user"], "Runtime login mismatch")
            require(row["config_identity"] == str(path), "Runtime config scope mismatch")
            require(row["domain"] == "M" and row["owner"] == "dewey", "Runtime scope mismatch")
            require(row["tenant"] == (cfg["tenant_id"] or ""), "Runtime tenant mismatch")
            require(
                row["allow_global"] == ("true" if cfg["allow_global_claims"] else "false"),
                "Runtime global policy mismatch",
            )
            manager = TemplateManager()
            bindings = []
            for code in BOOT_TEMPLATE_DEFINITIONS:
                template = manager.get_template(session, code, domain_code="M")
                require(template is not None, "Required historical template missing")
                require(template.instance_prefix == "DGX", "Historical template prefix changed")
                bindings.append({"code": code, "euid": template.euid, "instance_prefix": "DGX"})
            require(len(bindings) == 11, "Unexpected Dewey template set")
            result.update(session=row, templates=bindings)
        result["ddl_denial"] = []
        statements = (
            (
                "temporary_table",
                "CREATE TEMP TABLE dewey_acceptance_temp_probe_20260911 (n integer)",
            ),
            (
                "managed_schema_table",
                'CREATE TABLE "tapdb_dewey_lsmcok1_local".'
                '"dewey_acceptance_ddl_probe_20260911" (n integer)',
            ),
        )
        for label, statement in statements:
            dispose_all_runtime_engines()
            db = get_db(str(path))
            db.app_username = "dewey-migration-acceptance"
            attempted = False
            denied = False
            try:
                with db.session_scope(commit=False) as session:
                    attempted = True
                    session.execute(text(statement))
            except DBAPIError as exc:
                # A context/setup failure is not evidence that this DDL was denied.
                denied = attempted and getattr(exc.orig, "pgcode", None) == "42501"
                if not denied:
                    raise
            require(denied, f"Runtime DDL was not denied: {label}")
            result["ddl_denial"].append({"probe": label, "sqlstate": "42501"})
        result["status"] = "verified"
        write_new(receipt, sealed(result))
        return receipt
    finally:
        dispose_all_runtime_engines()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "phase",
        choices=("bootstrap-plan", "bootstrap-apply", "bind-plan", "bind-apply", "runtime-verify"),
    )
    result.add_argument("--lane", choices=tuple(LANES), required=True)
    result.add_argument("--runtime-config", required=True)
    result.add_argument("--receipt", required=True)
    result.add_argument("--operator-config")
    result.add_argument("--runtime-secret-record")
    result.add_argument("--operator-secret-arn")
    result.add_argument("--operator-secret-version")
    return result


def main() -> int:
    os.umask(0o077)
    args = parser().parse_args()
    try:
        check_versions()
        operator_args = (
            args.operator_config,
            args.runtime_secret_record,
            args.operator_secret_arn,
            args.operator_secret_version,
        )
        if args.phase == "runtime-verify":
            require(not any(operator_args), "Runtime verification forbids operator inputs")
            output = verify_runtime(args)
        else:
            require(all(operator_args), "All explicit operator/reference inputs are required")
            output = prepare(args)
        print(json.dumps({"status": "completed", "phase": args.phase, "receipt": str(output)}))
        return 0
    except Exception as exc:
        payload = {"status": "failed", "phase": args.phase, "error_class": type(exc).__name__}
        if isinstance(exc, PreparationError):
            payload["reason"] = str(exc)
        print(json.dumps(payload))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
