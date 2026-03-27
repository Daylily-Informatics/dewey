"""TapDB runtime helpers for Dewey."""

from __future__ import annotations

import importlib.metadata
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import quote

TAPDB_REQUIRED_VERSION = "0.2.7"
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
    port = (cfg.get("port") or "5432").strip()
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
