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

TAPDB_REQUIRED_VERSION = "3.0.9"
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
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip())
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


def ensure_tapdb_version(required_version: str = TAPDB_REQUIRED_VERSION) -> str:
    try:
        installed_version = importlib.metadata.version("daylily-tapdb")
    except importlib.metadata.PackageNotFoundError as exc:
        raise TapDBRuntimeError(
            f"daylily-tapdb=={required_version} is required but not installed"
        ) from exc

    if installed_version != required_version:
        required_tuple = _parse_semver_tuple(required_version)
        installed_tuple = _parse_semver_tuple(installed_version)
        if required_tuple is None or installed_tuple is None or installed_tuple < required_tuple:
            raise TapDBRuntimeError(
                "daylily-tapdb version mismatch. "
                f"Required baseline: {required_version}, installed: {installed_version}."
            )
    return installed_version


def tapdb_env_for_target(target: str) -> str:
    normalized = (target or "").strip().lower()
    if normalized not in _TARGET_TO_TAPDB_ENV:
        raise TapDBRuntimeError(f"Unsupported database target '{target}'. Use local or aurora.")
    return _TARGET_TO_TAPDB_ENV[normalized]


def _resolve_tapdb_config_path(*, namespace: str, client_id: str) -> str | None:
    explicit = (os.environ.get("TAPDB_CONFIG_PATH") or "").strip()
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
) -> dict[str, str]:
    resolved_env = (tapdb_env or tapdb_env_for_target(target)).strip().lower()
    env = os.environ.copy()
    env["AWS_PROFILE"] = (profile or DEFAULT_AWS_PROFILE).strip() or DEFAULT_AWS_PROFILE
    env["AWS_REGION"] = (region or DEFAULT_AWS_REGION).strip() or DEFAULT_AWS_REGION
    env["TAPDB_CLIENT_ID"] = (
        client_id or DEFAULT_TAPDB_CLIENT_ID
    ).strip() or DEFAULT_TAPDB_CLIENT_ID
    env["TAPDB_DATABASE_NAME"] = (
        namespace or DEFAULT_TAPDB_DATABASE_NAME
    ).strip() or DEFAULT_TAPDB_DATABASE_NAME
    env["TAPDB_ENV"] = resolved_env
    env["TAPDB_STRICT_NAMESPACE"] = "1"

    resolved_cfg_path = _resolve_tapdb_config_path(
        namespace=env["TAPDB_DATABASE_NAME"],
        client_id=env["TAPDB_CLIENT_ID"],
    )
    if resolved_cfg_path and not (env.get("TAPDB_CONFIG_PATH") or "").strip():
        env["TAPDB_CONFIG_PATH"] = resolved_cfg_path
    return env


def _get_tapdb_db_config_for_env(tapdb_env: str) -> dict[str, str]:
    from daylily_tapdb.cli.db_config import get_db_config_for_env

    cfg = get_db_config_for_env(tapdb_env)
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
) -> str:
    ensure_tapdb_version()
    runtime_env = _resolve_runtime_env(
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        tapdb_env=tapdb_env,
    )

    os.environ.update(runtime_env)
    cfg = _get_tapdb_db_config_for_env(runtime_env["TAPDB_ENV"])
    db_url = _build_sqlalchemy_url(cfg)
    os.environ["DATABASE_URL"] = db_url
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
    )
    cmd = [
        sys.executable,
        "-m",
        "daylily_tapdb.cli",
        "--client-id",
        runtime_env["TAPDB_CLIENT_ID"],
        "--database-name",
        runtime_env["TAPDB_DATABASE_NAME"],
    ]
    cmd.extend(args)

    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=runtime_env,
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
