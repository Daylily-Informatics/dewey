"""TapDB runtime helpers for Dewey."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from dewey_service.defaults import (
    AWS_PROFILE_REQUIRED_MESSAGE,
)


class TapDBRuntimeError(RuntimeError):
    """Raised for TapDB runtime configuration/invocation errors."""


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


TAPDB_VERSION = "11.0.1"
MERIDIAN_VERSION = "0.4.8"


def ensure_tapdb_version() -> str:
    for package, expected in (
        ("daylily-tapdb", TAPDB_VERSION),
        ("meridian-euid", MERIDIAN_VERSION),
    ):
        try:
            installed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            raise TapDBRuntimeError(f"{package} is required but not installed") from exc
        if installed != expected:
            raise TapDBRuntimeError(f"{package} must be exactly {expected}; installed {installed}")
    return TAPDB_VERSION


def load_runtime_config(settings) -> dict[str, object]:
    """Validate and bind the single TapDB target for this Dewey process."""
    from daylily_tapdb.cli.context import set_cli_context
    from daylily_tapdb.cli.db_config import get_db_config

    path = Path(str(settings.tapdb_config_path))
    if not path.is_absolute() or not path.is_file():
        raise TapDBRuntimeError("TapDB config must be an existing absolute file path")
    cfg = get_db_config(
        config_path=str(path),
        client_id=settings.tapdb_client_id,
        database_name=settings.tapdb_database_name,
    )
    for field, expected in (
        ("domain_code", settings.tapdb_domain_code),
        ("owner_repo_name", settings.tapdb_owner_repo_name),
        ("engine_type", settings.database_target),
    ):
        if cfg[field] != expected:
            raise TapDBRuntimeError(f"TapDB {field} disagrees with the explicit Dewey setting")
    # Embedded metrics and GUI code also resolve TapDB settings without a path.
    # Keep their process context explicit without replacing Dewey's CLI context.
    set_cli_context(
        config_path=path,
        client_id=settings.tapdb_client_id,
        database_name=settings.tapdb_database_name,
    )
    return cfg


def validate_database_target(target: str) -> str:
    normalized = (target or "").strip().lower()
    if normalized not in {"local", "aurora"}:
        raise TapDBRuntimeError(f"Unsupported database target '{target}'. Use local or aurora.")
    return normalized


def _resolve_tapdb_config_path(*, namespace: str, client_id: str, config_path: str) -> str:
    del namespace, client_id
    explicit = str(config_path or "").strip()
    path = Path(explicit)
    if not explicit or not path.is_absolute():
        raise TapDBRuntimeError("TapDB config path must be an explicit absolute file path")
    if not path.is_file():
        raise TapDBRuntimeError(f"TapDB config file does not exist: {path}")
    return str(path)


def _resolve_runtime_env(
    *,
    target: str,
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
    config_path: str = "",
) -> dict[str, str]:
    target = validate_database_target(target)
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
    from daylily_tapdb.cli.db_config import get_db_config

    cfg = get_db_config(
        config_path=resolved_cfg_path,
        client_id=resolved_client_id,
        database_name=resolved_namespace,
    )
    if cfg["engine_type"] != target:
        raise TapDBRuntimeError("TapDB target disagrees with the explicit Dewey setting")
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
    # Runtime scope is owned by the explicit native config, never shell aliases.
    child_env.pop("MERIDIAN_DOMAIN_CODE", None)
    child_env.pop("TAPDB_OWNER_REPO", None)

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
    config_path: str,
    cwd: Path | None = None,
) -> dict[str, object]:
    target_label = validate_database_target(target)
    tool_version = ensure_tapdb_version()
    result = run_tapdb_cli(
        ["db", "schema", "drift-check", "--json", "--strict"],
        target=target,
        client_id=client_id,
        profile=profile,
        region=region,
        namespace=namespace,
        config_path=config_path,
        cwd=cwd,
        check=False,
    )

    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise TapDBRuntimeError("TapDB drift-check returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise TapDBRuntimeError("TapDB drift-check must return a JSON object")

    status = "check_failed"
    if result.returncode == 0:
        status = "clean"
    elif result.returncode == 1:
        status = "drift"

    counts = payload.get("counts")
    if status in {"clean", "drift"}:
        if (
            payload.get("status") != status
            or payload.get("strict") is not True
            or not isinstance(counts, dict)
            or not isinstance(counts.get("expected"), dict)
            or not isinstance(counts.get("live"), dict)
        ):
            raise TapDBRuntimeError(
                "TapDB drift-check returned an incomplete or inconsistent receipt"
            )
        summary = f"expected={counts['expected']} live={counts['live']}"
    else:
        summary = str(payload.get("error") or "schema drift check failed")

    normalized: dict[str, object] = {
        "status": status,
        "checked_at": _utcnow(),
        "target": target_label,
        "tool_version": tool_version,
        "summary": summary,
        "report": payload,
        "strict": True,
    }
    stderr = (result.stderr or "").strip()
    if stderr and status == "check_failed":
        normalized["stderr"] = stderr
    return normalized
