"""TapDB runtime helpers for Dewey."""

from __future__ import annotations

import importlib.metadata
import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from dewey_service.defaults import (
    AWS_PROFILE_REQUIRED_MESSAGE,
)


class TapDBRuntimeError(RuntimeError):
    """Raised for TapDB runtime configuration/invocation errors."""


def _sanitize_deployment_code(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in (value or "").strip())
    cleaned = cleaned.strip("-")
    if not cleaned:
        raise TapDBRuntimeError("Dewey deployment code is required")
    return cleaned


def _resolve_deployment_code() -> str:
    return _sanitize_deployment_code(
        os.environ.get("DEPLOYMENT_CODE")
        or os.environ.get("DEWEY_DEPLOYMENT_CODE")
        or os.environ.get("LSMC_DEPLOYMENT_CODE")
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


def validate_database_target(target: str) -> str:
    normalized = (target or "").strip().lower()
    if normalized not in {"local", "aurora"}:
        raise TapDBRuntimeError(f"Unsupported database target '{target}'. Use local or aurora.")
    return normalized


def _resolve_tapdb_config_path(
    *, namespace: str, client_id: str, config_path: str = ""
) -> str | None:
    del namespace, client_id
    explicit = str(config_path or "").strip()
    if explicit:
        resolved = Path(explicit)
        if not resolved.is_absolute():
            raise TapDBRuntimeError(
                f"TapDB config path must be an absolute file path, got: {explicit}"
            )
        return str(resolved.resolve())
    env_override = str(os.environ.get("TAPDB_CONFIG_PATH") or "").strip()
    if env_override:
        resolved = Path(env_override)
        if not resolved.is_absolute():
            raise TapDBRuntimeError(
                f"TAPDB_CONFIG_PATH must be an absolute file path, got: {env_override}"
            )
        return str(resolved.resolve())
    return None


def _resolve_runtime_env(
    *,
    target: str,
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
    config_path: str = "",
) -> dict[str, str]:
    validate_database_target(target)
    resolved_client_id = (client_id or "").strip()
    if not resolved_client_id:
        raise TapDBRuntimeError("Dewey TapDB client_id is required")
    resolved_namespace = (namespace or "").strip()
    if not resolved_namespace:
        raise TapDBRuntimeError("Dewey TapDB database_name/namespace is required")
    resolved_cfg_path = _resolve_tapdb_config_path(
        namespace=resolved_namespace,
        client_id=resolved_client_id,
        config_path=config_path,
    )
    resolved_profile = (profile or "").strip()
    if not resolved_profile:
        raise TapDBRuntimeError(AWS_PROFILE_REQUIRED_MESSAGE)
    resolved_region = (region or "").strip()
    if not resolved_region:
        raise TapDBRuntimeError("Dewey AWS region is required")
    return {
        "aws_profile": resolved_profile,
        "aws_region": resolved_region,
        "client_id": resolved_client_id,
        "database_name": resolved_namespace,
        "config_path": resolved_cfg_path or "",
    }


def _require_config_path(runtime_env: Mapping[str, str]) -> str:
    config_path = str(runtime_env.get("config_path") or "").strip()
    if not config_path:
        raise TapDBRuntimeError(
            "TapDB config path is required. Pass an explicit absolute path via Dewey settings, "
            "--config, or TAPDB_CONFIG_PATH, then run TapDB as "
            "'tapdb --config <path> ...'."
        )
    return config_path


def _resolve_tapdb_cli_executable() -> str:
    tapdb_executable = shutil.which("tapdb")
    if tapdb_executable:
        return tapdb_executable
    raise TapDBRuntimeError(
        "tapdb CLI is not available on PATH. Install daylily-tapdb in the active Dewey "
        "environment so 'tapdb --config <path> ...' is available."
    )


def _get_tapdb_db_config(
    *,
    config_path: str,
    client_id: str,
    database_name: str,
) -> dict[str, str]:
    from daylily_tapdb.cli.db_config import get_db_config

    cfg = get_db_config(
        config_path=config_path or None,
        client_id=client_id,
        database_name=database_name,
    )
    if not cfg:
        raise TapDBRuntimeError("No TapDB database config resolved for the explicit target.")
    return cfg


def _build_sqlalchemy_url(cfg: Mapping[str, str]) -> str:
    user = quote((cfg.get("user") or "").strip(), safe="")
    if not user:
        raise TapDBRuntimeError("TapDB DB config is missing user")
    password = quote((cfg.get("password") or "").strip(), safe="")
    host = (cfg.get("host") or "").strip()
    if not host:
        raise TapDBRuntimeError("TapDB DB config is missing host")
    port = (cfg.get("port") or "").strip()
    if not port:
        raise TapDBRuntimeError("TapDB DB config is missing port")
    database = (cfg.get("database") or "").strip()
    if not database:
        raise TapDBRuntimeError("TapDB DB config is missing database name")
    schema_name = (cfg.get("schema_name") or "").strip()
    if not schema_name:
        raise TapDBRuntimeError("TapDB DB config is missing schema_name")
    auth = f"{user}:{password}@" if password else f"{user}@"
    return (
        f"postgresql+psycopg2://{auth}{host}:{port}/{database}"
        f"?options={quote(f'-csearch_path={schema_name}', safe='')}"
    )


def export_database_url_for_target(
    *,
    target: str,
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
    config_path: str = "",
) -> str:
    ensure_tapdb_version()
    runtime_env = _resolve_runtime_env(
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        config_path=config_path,
    )
    resolved_config_path = _require_config_path(runtime_env)
    cfg = _get_tapdb_db_config(
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
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
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
        config_path=config_path,
    )
    tapdb_executable = _resolve_tapdb_cli_executable()
    cmd = [
        tapdb_executable,
        "--config",
        _require_config_path(runtime_env),
    ]
    cmd.extend(args)
    child_env = os.environ.copy()
    if runtime_env["aws_profile"]:
        child_env["AWS_PROFILE"] = runtime_env["aws_profile"]
    else:
        child_env.pop("AWS_PROFILE", None)
    child_env["AWS_REGION"] = runtime_env["aws_region"]
    child_env["AWS_DEFAULT_REGION"] = runtime_env["aws_region"]
    domain_code = str(os.environ.get("MERIDIAN_DOMAIN_CODE") or "").strip()
    owner_repo_name = str(os.environ.get("TAPDB_OWNER_REPO") or "").strip()
    if not domain_code:
        raise TapDBRuntimeError("MERIDIAN_DOMAIN_CODE is required for TapDB runtime commands")
    if not owner_repo_name:
        raise TapDBRuntimeError("TAPDB_OWNER_REPO is required for TapDB runtime commands")
    child_env["MERIDIAN_DOMAIN_CODE"] = domain_code
    child_env["TAPDB_OWNER_REPO"] = owner_repo_name

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
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
    cwd: Path | None = None,
) -> dict[str, object]:
    target_label = validate_database_target(target)
    tool_version = ensure_tapdb_version()
    result = run_tapdb_cli(
        ["db", "schema", "drift-check", "--json", "--no-strict"],
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
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
        "target": target_label,
        "tool_version": tool_version,
        "summary": summary,
        "report": payload,
        "strict": False,
    }
    stderr = (result.stderr or "").strip()
    if stderr and status == "check_failed":
        normalized["stderr"] = stderr
    return normalized
