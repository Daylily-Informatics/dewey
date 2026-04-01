"""TapDB runtime helpers for Dewey."""

from __future__ import annotations

import importlib.metadata
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from dewey_service.defaults import DEFAULT_DB_PORT

DEFAULT_AWS_PROFILE = "lsmc"
DEFAULT_AWS_REGION = "us-west-2"
DEFAULT_TAPDB_CLIENT_ID = "dewey"
DEFAULT_TAPDB_DATABASE_NAME = "dewey"

_TARGET_TO_TAPDB_ENV = {
    "local": "dev",
    "aurora": "prod",
    "prod": "prod",
}


class TapDBRuntimeError(RuntimeError):
    """Raised for TapDB runtime configuration/invocation errors."""


def _sanitize_deployment_code(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-]+", "-", (value or "").strip())
    cleaned = cleaned.strip("-")
    return cleaned or "local"


def _resolve_deployment_code() -> str:
    return _sanitize_deployment_code(
        os.environ.get("DEWEY_DEPLOYMENT_CODE")
        or os.environ.get("DEPLOYMENT_CODE")
        or os.environ.get("LSMC_DEPLOYMENT_CODE")
        or "local"
    )


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_semver_tuple(version: str) -> tuple[int, int, int] | None:
    match = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)", version or "")
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def ensure_tapdb_version() -> str:
    try:
        return importlib.metadata.version("daylily-tapdb")
    except importlib.metadata.PackageNotFoundError as exc:
        raise TapDBRuntimeError("daylily-tapdb is required but not installed") from exc


def tapdb_env_for_target(target: str) -> str:
    normalized = (target or "").strip().lower()
    if normalized not in _TARGET_TO_TAPDB_ENV:
        raise TapDBRuntimeError(f"Unsupported database target '{target}'. Use local or aurora.")
    return _TARGET_TO_TAPDB_ENV[normalized]


def _resolve_tapdb_config_path(*, namespace: str, client_id: str, config_path: str = "") -> str | None:
    explicit = str(config_path or "").strip()
    if explicit:
        return explicit
    normalized_namespace = (
        namespace or DEFAULT_TAPDB_DATABASE_NAME
    ).strip() or DEFAULT_TAPDB_DATABASE_NAME
    normalized_client_id = (client_id or DEFAULT_TAPDB_CLIENT_ID).strip() or DEFAULT_TAPDB_CLIENT_ID
    deployment_code = _resolve_deployment_code()

    deployment_scoped = (
        Path.home()
        / ".config"
        / "tapdb"
        / normalized_client_id
        / f"{normalized_namespace}-{deployment_code}"
        / "tapdb-config.yaml"
    )
    if deployment_scoped.exists():
        return str(deployment_scoped)

    user_scoped = (
        Path.home()
        / ".config"
        / "tapdb"
        / normalized_client_id
        / normalized_namespace
        / "tapdb-config.yaml"
    )
    if user_scoped.exists():
        return str(user_scoped)

    repo_root = Path(__file__).resolve().parents[2]
    repo_scoped = repo_root / "config" / f"tapdb-config-{normalized_namespace}.yaml"
    if repo_scoped.exists():
        return str(repo_scoped)

    return None


def _resolve_runtime_env(
    *,
    target: str,
    client_id: str = DEFAULT_TAPDB_CLIENT_ID,
    profile: str = DEFAULT_AWS_PROFILE,
    region: str = DEFAULT_AWS_REGION,
    namespace: str = DEFAULT_TAPDB_DATABASE_NAME,
    tapdb_env: str | None = None,
    config_path: str = "",
) -> dict[str, str]:
    resolved_env = (tapdb_env or tapdb_env_for_target(target)).strip().lower()
    resolved_client_id = (client_id or DEFAULT_TAPDB_CLIENT_ID).strip() or DEFAULT_TAPDB_CLIENT_ID
    resolved_namespace = (namespace or DEFAULT_TAPDB_DATABASE_NAME).strip() or DEFAULT_TAPDB_DATABASE_NAME
    resolved_cfg_path = _resolve_tapdb_config_path(
        namespace=resolved_namespace,
        client_id=resolved_client_id,
        config_path=config_path,
    )
    return {
        "aws_profile": (profile or DEFAULT_AWS_PROFILE).strip() or DEFAULT_AWS_PROFILE,
        "aws_region": (region or DEFAULT_AWS_REGION).strip() or DEFAULT_AWS_REGION,
        "client_id": resolved_client_id,
        "database_name": resolved_namespace,
        "tapdb_env": resolved_env,
        "config_path": resolved_cfg_path or "",
    }


def _require_config_path(runtime_env: Mapping[str, str]) -> str:
    config_path = str(runtime_env.get("config_path") or "").strip()
    if not config_path:
        raise TapDBRuntimeError(
            "TapDB config path is required. Resolve it via Dewey settings and pass it explicitly "
            "to TapDB with --config."
        )
    return config_path


def _get_tapdb_db_config_for_env(
    tapdb_env: str,
    *,
    config_path: str,
    client_id: str,
    database_name: str,
) -> dict[str, str]:
    from daylily_tapdb.cli.db_config import get_db_config_for_env

    cfg = get_db_config_for_env(
        tapdb_env,
        config_path=config_path or None,
        client_id=client_id,
        database_name=database_name,
    )
    if not cfg:
        raise TapDBRuntimeError(f"No TapDB database config resolved for TAPDB_ENV={tapdb_env}.")
    return cfg


def _build_sqlalchemy_url(cfg: Mapping[str, str]) -> str:
    user = quote((cfg.get("user") or "").strip(), safe="") or "postgres"
    password = quote((cfg.get("password") or "").strip(), safe="")
    host = (cfg.get("host") or "localhost").strip()
    port = (cfg.get("port") or str(DEFAULT_DB_PORT)).strip()
    database = (cfg.get("database") or "").strip()
    if not database:
        raise TapDBRuntimeError("TapDB DB config is missing database name")
    auth = f"{user}:{password}@" if password else f"{user}@"
    return f"postgresql+psycopg2://{auth}{host}:{port}/{database}"


def export_database_url_for_target(
    *,
    target: str,
    client_id: str = DEFAULT_TAPDB_CLIENT_ID,
    profile: str = DEFAULT_AWS_PROFILE,
    region: str = DEFAULT_AWS_REGION,
    namespace: str = DEFAULT_TAPDB_DATABASE_NAME,
    tapdb_env: str | None = None,
    config_path: str = "",
) -> str:
    ensure_tapdb_version()
    runtime_env = _resolve_runtime_env(
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        tapdb_env=tapdb_env,
        config_path=config_path,
    )
    resolved_config_path = _require_config_path(runtime_env)
    cfg = _get_tapdb_db_config_for_env(
        runtime_env["tapdb_env"],
        config_path=resolved_config_path,
        client_id=runtime_env["client_id"],
        database_name=runtime_env["database_name"],
    )
    db_url = _build_sqlalchemy_url(cfg)
    return db_url


def run_tapdb_cli(
    args: Sequence[str],
    *,
    target: str,
    client_id: str = DEFAULT_TAPDB_CLIENT_ID,
    profile: str = DEFAULT_AWS_PROFILE,
    region: str = DEFAULT_AWS_REGION,
    namespace: str = DEFAULT_TAPDB_DATABASE_NAME,
    tapdb_env: str | None = None,
    config_path: str = "",
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    ensure_tapdb_version()
    runtime_env = _resolve_runtime_env(
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        tapdb_env=tapdb_env,
        config_path=config_path,
    )
    cmd = [
        sys.executable,
        "-m",
        "daylily_tapdb.cli",
        "--config", _require_config_path(runtime_env),
        "--env", runtime_env["tapdb_env"],
    ]
    cmd.extend(args)
    child_env = os.environ.copy()
    child_env["AWS_PROFILE"] = runtime_env["aws_profile"]
    child_env["AWS_REGION"] = runtime_env["aws_region"]
    child_env["AWS_DEFAULT_REGION"] = runtime_env["aws_region"]

    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=child_env,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise TapDBRuntimeError(
            f"tapdb command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc


def run_schema_drift_check(
    *,
    target: str,
    client_id: str = DEFAULT_TAPDB_CLIENT_ID,
    profile: str = DEFAULT_AWS_PROFILE,
    region: str = DEFAULT_AWS_REGION,
    namespace: str = DEFAULT_TAPDB_DATABASE_NAME,
    tapdb_env: str | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    env_name = (tapdb_env or tapdb_env_for_target(target)).strip().lower()
    tool_version = ensure_tapdb_version()
    result = run_tapdb_cli(
        ["db", "schema", "drift-check", env_name, "--json", "--no-strict"],
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        tapdb_env=env_name,
        cwd=cwd,
        check=False,
    )

    payload: dict[str, object] = {}
    raw_stdout = (result.stdout or "").strip()
    if raw_stdout:
        try:
            parsed = json.loads(raw_stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": raw_stdout}
        if isinstance(parsed, dict):
            payload = parsed

    status = "check_failed"
    if result.returncode == 0:
        status = "clean"
    elif result.returncode == 1:
        status = "drift"

    counts = payload.get("counts")
    summary = "schema drift report unavailable"
    if isinstance(counts, dict):
        expected = counts.get("expected")
        live = counts.get("live")
        summary = f"expected={expected} live={live}"
    elif status == "clean":
        summary = "no schema drift reported"
    elif status == "drift":
        summary = "schema drift detected"

    normalized: dict[str, object] = {
        "status": status,
        "checked_at": _utcnow(),
        "environment": env_name,
        "tool_version": tool_version,
        "summary": summary,
        "report": payload,
        "strict": False,
    }
    stderr = (result.stderr or "").strip()
    if stderr and status == "check_failed":
        normalized["stderr"] = stderr
    return normalized
