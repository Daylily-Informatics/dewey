"""Read-only TapDB schema drift checks for Dewey monitoring."""

from __future__ import annotations

from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from dewey_service.integrations.tapdb_runtime import run_schema_drift_check as run_tapdb_schema_drift_check
from dewey_service.settings import Settings


def default_schema_drift_payload(environment: str = "") -> dict[str, Any]:
    return {
        "status": "not_run",
        "checked_at": None,
        "environment": environment,
        "tool_version": _tool_version(),
        "summary": "Schema drift check has not been run.",
        "report": {},
        "strict": False,
    }


def load_schema_drift_payload(settings: Settings) -> dict[str, Any]:
    return dict(
        _cached_schema_drift_payload(
            settings.database_target,
            settings.tapdb_client_id,
            settings.aws_profile,
            settings.aws_region,
            settings.tapdb_database_name,
            settings.tapdb_env or "",
        )
    )


@lru_cache(maxsize=16)
def _cached_schema_drift_payload(
    target: str,
    client_id: str,
    profile: str,
    region: str,
    namespace: str,
    tapdb_env: str,
) -> dict[str, Any]:
    try:
        return run_tapdb_schema_drift_check(
            target=target,
            client_id=client_id,
            profile=profile,
            region=region,
            namespace=namespace,
            tapdb_env=tapdb_env or None,
        )
    except Exception as exc:
        return {
            **default_schema_drift_payload(tapdb_env),
            "status": "check_failed",
            "summary": f"Unable to execute tapdb drift-check: {exc}",
        }


def _tool_version() -> str:
    try:
        return version("daylily-tapdb")
    except PackageNotFoundError:
        return ""
