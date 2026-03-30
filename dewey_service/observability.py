"""Local observability helpers for Dewey."""

from __future__ import annotations

import hashlib
import os
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import ceil
from statistics import median
from time import monotonic
from typing import Any

from fastapi import Request
from sqlalchemy import text

from dewey_service.schema_drift import load_schema_drift_payload
from dewey_service.settings import Settings

CONTRACT_VERSION = "v3"
SERVICE_NAME = "dewey"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(len(ordered) * quantile) - 1))
    return round(float(ordered[index]), 3)


def hash_identifier(value: str) -> str:
    payload = str(value or "").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _status_for_projection(projection: "ProjectionMetadata", ready_status: str) -> str:
    return ready_status if projection.state == "ready" else "unknown"


def _build_sha() -> str:
    return (
        os.environ.get("DEWEY_BUILD_SHA")
        or os.environ.get("BUILD_SHA")
        or os.environ.get("GIT_SHA")
        or ""
    )


@dataclass
class ProjectionMetadata:
    state: str = "ready"
    stale: bool = False
    observed_at: str | None = None
    last_synced_at: str | None = None
    detail: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "stale": self.stale,
            "observed_at": self.observed_at,
            "last_synced_at": self.last_synced_at,
            "detail": self.detail,
        }


@dataclass
class EndpointRollup:
    method: str
    route_template: str
    request_count: int = 0
    error_count: int = 0
    status_class_counts: Counter[str] = field(default_factory=Counter)
    durations_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    fingerprints: set[str] = field(default_factory=set)
    observed_at: str = field(default_factory=_utcnow_iso)

    def record(self, *, status_code: int, duration_ms: float, fingerprint: str) -> None:
        self.request_count += 1
        if status_code >= 500:
            self.error_count += 1
        self.status_class_counts[f"{status_code // 100}xx"] += 1
        self.durations_ms.append(float(duration_ms))
        if fingerprint:
            self.fingerprints.add(fingerprint)
        self.observed_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        durations = list(self.durations_ms)
        return {
            "method": self.method,
            "route_template": self.route_template,
            "request_count": self.request_count,
            "status_class_counts": dict(self.status_class_counts),
            "p50_ms": round(median(durations), 3) if durations else 0.0,
            "p95_ms": _percentile(durations, 0.95),
            "p99_ms": _percentile(durations, 0.99),
            "fingerprint_count": len(self.fingerprints),
            "error_count": self.error_count,
            "observed_at": self.observed_at,
        }


@dataclass
class FamilyRollup:
    family: str
    request_count: int = 0
    error_count: int = 0
    durations_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    observed_at: str = field(default_factory=_utcnow_iso)

    def record(self, *, status_code: int, duration_ms: float) -> None:
        self.request_count += 1
        if status_code >= 500:
            self.error_count += 1
        self.durations_ms.append(float(duration_ms))
        self.observed_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        durations = list(self.durations_ms)
        return {
            "family": self.family,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "p50_ms": round(median(durations), 3) if durations else 0.0,
            "p95_ms": _percentile(durations, 0.95),
            "p99_ms": _percentile(durations, 0.99),
            "observed_at": self.observed_at,
        }


@dataclass
class DbOperationRollup:
    fingerprint: str
    label: str
    request_count: int = 0
    error_count: int = 0
    durations_ms: deque[float] = field(default_factory=lambda: deque(maxlen=256))
    observed_at: str = field(default_factory=_utcnow_iso)

    def record(self, *, duration_ms: float, success: bool) -> None:
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.durations_ms.append(float(duration_ms))
        self.observed_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        durations = list(self.durations_ms)
        return {
            "fingerprint": self.fingerprint,
            "label": self.label,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "p50_ms": round(median(durations), 3) if durations else 0.0,
            "p95_ms": _percentile(durations, 0.95),
            "p99_ms": _percentile(durations, 0.99),
            "observed_at": self.observed_at,
        }


class DeweyObservabilityStore:
    """Dewey-local in-memory rollups shared by API and UI surfaces."""

    def __init__(self, settings: Settings, *, version: str) -> None:
        self.settings = settings
        self.version = version
        self.instance_id = uuid.uuid4().hex
        self._started_at = _utcnow_iso()
        self._endpoint_rollups: dict[tuple[str, str], EndpointRollup] = {}
        self._family_rollups: dict[str, FamilyRollup] = {}
        self._db_rollups: dict[str, DbOperationRollup] = {}
        self._db_probes: deque[dict[str, Any]] = deque(maxlen=25)
        self._auth_recent: deque[dict[str, Any]] = deque(maxlen=25)
        self._auth_status_counts: Counter[str] = Counter()
        self._configured_dependencies: tuple[str, ...] = tuple()
        self._observed_dependencies: set[str] = set()
        self._schema_drift = load_schema_drift_payload(settings)
        self._obs_services_snapshot = self._build_obs_services_snapshot()

    def _build_obs_services_snapshot(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "endpoints": [
                {"path": "/healthz", "auth": "none", "kind": "liveness"},
                {"path": "/readyz", "auth": "none", "kind": "readiness"},
                {"path": "/health", "auth": "operator_or_service_token", "kind": "summary"},
                {"path": "/obs_services", "auth": "operator_or_service_token", "kind": "discovery"},
                {"path": "/api_health", "auth": "operator_or_service_token", "kind": "api_rollup"},
                {"path": "/endpoint_health", "auth": "operator_or_service_token", "kind": "endpoint_rollup"},
                {"path": "/db_health", "auth": "operator_or_service_token", "kind": "database"},
                {"path": "/my_health", "auth": "authenticated_self", "kind": "self"},
                {"path": "/auth_health", "auth": "operator_or_service_token", "kind": "auth"},
                {"path": "/api/anomalies", "auth": "operator_or_service_token", "kind": "anomaly_list"},
                {
                    "path": "/api/anomalies/{anomaly_id}",
                    "auth": "operator_or_service_token",
                    "kind": "anomaly_detail",
                },
            ],
            "extensions": ["dewey.operator_ui", "dewey.anomalies_v1"],
            "dependencies": {
                "configured_services": list(self._configured_dependencies),
                "observed_services": sorted(self._observed_dependencies),
            },
            "observed_at": self._started_at,
        }

    def projection(self, *, observed_at: str | None = None, detail: str | None = None) -> ProjectionMetadata:
        seen_at = observed_at or self._started_at
        return ProjectionMetadata(
            state="ready",
            stale=False,
            observed_at=seen_at,
            last_synced_at=seen_at,
            detail=detail,
        )

    def record_http_request(
        self,
        *,
        method: str,
        route_template: str,
        status_code: int,
        duration_ms: float,
        path: str,
    ) -> None:
        fingerprint = hash_identifier(path) if status_code >= 500 else ""
        family = classify_family(route_template)
        key = (method.upper(), route_template)
        endpoint_rollup = self._endpoint_rollups.setdefault(
            key,
            EndpointRollup(method=method.upper(), route_template=route_template),
        )
        endpoint_rollup.record(
            status_code=status_code,
            duration_ms=duration_ms,
            fingerprint=fingerprint,
        )
        family_rollup = self._family_rollups.setdefault(family, FamilyRollup(family=family))
        family_rollup.record(status_code=status_code, duration_ms=duration_ms)

    def record_db_operation(self, *, label: str, duration_ms: float, success: bool) -> None:
        fingerprint = hash_identifier(label)
        rollup = self._db_rollups.setdefault(
            fingerprint,
            DbOperationRollup(fingerprint=fingerprint, label=label),
        )
        rollup.record(duration_ms=duration_ms, success=success)

    def record_db_probe(self, *, status: str, latency_ms: float, detail: str) -> None:
        self._db_probes.appendleft(
            {
                "status": status,
                "latency_ms": round(float(latency_ms), 3),
                "detail": detail,
                "fingerprint": hash_identifier(detail),
                "observed_at": _utcnow_iso(),
            }
        )

    def record_auth_event(
        self,
        *,
        status: str,
        mode: str,
        detail: str,
        service_principal: bool = False,
    ) -> None:
        event = {
            "status": status,
            "mode": mode,
            "detail": detail,
            "service_principal": service_principal,
            "fingerprint": hash_identifier(detail),
            "observed_at": _utcnow_iso(),
        }
        self._auth_recent.appendleft(event)
        self._auth_status_counts[status] += 1

    def health_snapshot(self) -> dict[str, Any]:
        latest_db = self.latest_db_probe()
        latest_auth = self._auth_recent[0] if self._auth_recent else None
        database_status = str((latest_db or {}).get("status") or "unknown")
        overall_status = "ok" if database_status in {"ok", "unknown"} else "degraded"
        return {
            "status": overall_status,
            "checks": {
                "process": {"status": "ok", "observed_at": _utcnow_iso()},
                "database": latest_db
                or {
                    "status": "unknown",
                    "latency_ms": None,
                    "detail": None,
                    "observed_at": None,
                },
                "auth": {
                    "status": str((latest_auth or {}).get("status") or "unknown"),
                    "mode": str((latest_auth or {}).get("mode") or ""),
                    "cognito_configured": bool(
                        self.settings.cognito_domain and self.settings.cognito_app_client_id
                    ),
                    "observed_at": (latest_auth or {}).get("observed_at"),
                },
            },
        }

    def obs_services_snapshot(self) -> tuple[ProjectionMetadata, dict[str, Any]]:
        snapshot = dict(self._obs_services_snapshot)
        observed_at = str(snapshot.get("observed_at") or self._started_at)
        return self.projection(observed_at=observed_at), snapshot

    def api_health(self) -> tuple[ProjectionMetadata, list[dict[str, Any]]]:
        families = [rollup.to_dict() for rollup in self._family_rollups.values()]
        families.sort(key=lambda item: (-int(item["request_count"]), item["family"]))
        observed_at = families[0]["observed_at"] if families else self._started_at
        return self.projection(observed_at=observed_at), families

    def endpoint_health(self, *, offset: int, limit: int) -> tuple[ProjectionMetadata, dict[str, Any]]:
        items = [rollup.to_dict() for rollup in self._endpoint_rollups.values()]
        items.sort(key=lambda item: (-int(item["request_count"]), item["route_template"], item["method"]))
        total = len(items)
        sliced = items[offset : offset + limit]
        observed_at = sliced[0]["observed_at"] if sliced else (items[0]["observed_at"] if items else self._started_at)
        return self.projection(observed_at=observed_at), {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": sliced,
        }

    def latest_db_probe(self) -> dict[str, Any] | None:
        return dict(self._db_probes[0]) if self._db_probes else None

    def db_health(self) -> tuple[ProjectionMetadata, dict[str, Any]]:
        latest = dict(self._db_probes[0]) if self._db_probes else None
        recent = [rollup.to_dict() for rollup in self._db_rollups.values()]
        recent.sort(key=lambda item: (-float(item["p95_ms"]), -int(item["request_count"]), item["label"]))
        hottest = sorted(recent, key=lambda item: (-int(item["request_count"]), item["label"]))[:5]
        slowest = sorted(recent, key=lambda item: (-float(item["p95_ms"]), item["label"]))[:5]
        observed_at = (latest or {}).get("observed_at") or (recent[0]["observed_at"] if recent else self._started_at)
        return self.projection(observed_at=observed_at), {
            "status": str((latest or {}).get("status") or "unknown"),
            "latest": latest,
            "recent": recent[:25],
            "slowest": slowest,
            "hottest": hottest,
            "schema_drift": dict(self._schema_drift),
            "observed_at": observed_at,
        }

    def auth_health(self) -> tuple[ProjectionMetadata, dict[str, Any]]:
        recent = list(self._auth_recent)
        status_counts = dict(self._auth_status_counts)
        latest = recent[0] if recent else None
        observed_at = str((latest or {}).get("observed_at") or self._started_at)
        return self.projection(observed_at=observed_at), {
            "status": str((latest or {}).get("status") or "unknown"),
            "mode": str((latest or {}).get("mode") or "unknown"),
            "cognito_configured": bool(
                self.settings.cognito_domain and self.settings.cognito_app_client_id
            ),
            "cognito_domain": self.settings.cognito_domain or "",
            "user_pool_id": self.settings.cognito_user_pool_id or "",
            "app_client_id_present": bool(self.settings.cognito_app_client_id),
            "recent": recent,
            "status_counts": status_counts,
            "sessions": {
                "supported": False,
                "active_session_count": None,
                "recent_user_count": None,
                "observed_at": observed_at,
            },
            "observed_at": observed_at,
        }


def classify_family(route_template: str) -> str:
    path = route_template or "/"
    if path.startswith("/api/"):
        parts = [part for part in path.split("/") if part]
        if len(parts) > 2 and parts[1].startswith("v") and parts[1][1:].isdigit():
            return parts[2]
        return parts[1] if len(parts) > 1 else "api"
    if path.startswith("/auth"):
        return "auth"
    if path.startswith("/ui"):
        return "ui"
    if path in {
        "/health",
        "/healthz",
        "/readyz",
        "/obs_services",
        "/api_health",
        "/endpoint_health",
        "/db_health",
        "/my_health",
        "/auth_health",
    }:
        return "observability"
    return "web"


def route_template_from_request(request: Request) -> str:
    route = request.scope.get("route")
    return str(
        getattr(route, "path", None)
        or getattr(route, "path_format", None)
        or request.url.path
    )


def base_frame(request: Request, *, status: str) -> dict[str, Any]:
    store: DeweyObservabilityStore = request.app.state.observability
    settings: Settings = request.app.state.settings
    environment = settings.deployment_name or settings.environment
    return {
        "contract_version": CONTRACT_VERSION,
        "service": SERVICE_NAME,
        "environment": environment,
        "instance_id": store.instance_id,
        "observed_at": _utcnow_iso(),
        "status": status,
        "request_id": getattr(request.state, "request_id", ""),
        "correlation_id": getattr(request.state, "correlation_id", ""),
        "build": {
            "version": request.app.version,
            "sha": _build_sha(),
        },
    }


def build_health_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    health_snapshot: dict[str, Any],
) -> dict[str, Any]:
    payload = base_frame(
        request,
        status=_status_for_projection(projection, str(health_snapshot.get("status") or "unknown")),
    )
    payload["checks"] = dict(health_snapshot.get("checks") or {})
    payload["projection"] = projection.model_dump()
    return payload


def build_obs_services_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    payload = base_frame(
        request,
        status=_status_for_projection(projection, str(snapshot.get("status") or "ok")),
    )
    payload["endpoints"] = list(snapshot.get("endpoints") or [])
    payload["extensions"] = list(snapshot.get("extensions") or [])
    payload["dependencies"] = dict(snapshot.get("dependencies") or {})
    payload["projection"] = projection.model_dump()
    return payload


def build_api_health_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    families: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = base_frame(request, status=_status_for_projection(projection, "ok"))
    payload["families"] = families
    payload["projection"] = projection.model_dump()
    return payload


def build_endpoint_health_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    total: int,
    offset: int,
    limit: int,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = base_frame(request, status=_status_for_projection(projection, "ok"))
    payload["page"] = {"total": total, "offset": offset, "limit": limit}
    payload["items"] = items
    payload["projection"] = projection.model_dump()
    return payload


def build_db_health_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    db_health: dict[str, Any],
) -> dict[str, Any]:
    payload = base_frame(
        request,
        status=_status_for_projection(projection, str(db_health.get("status") or "unknown")),
    )
    payload["database"] = db_health
    payload["projection"] = projection.model_dump()
    return payload


def build_auth_health_payload(
    request: Request,
    *,
    projection: ProjectionMetadata,
    auth_rollup: dict[str, Any],
) -> dict[str, Any]:
    payload = base_frame(
        request,
        status=_status_for_projection(projection, str(auth_rollup.get("status") or "unknown")),
    )
    payload["auth"] = {
        "mode": str(auth_rollup.get("mode") or ""),
        "cognito_configured": bool(auth_rollup.get("cognito_configured", False)),
        "cognito_domain": str(auth_rollup.get("cognito_domain") or ""),
        "user_pool_id": str(auth_rollup.get("user_pool_id") or ""),
        "app_client_id_present": bool(auth_rollup.get("app_client_id_present", False)),
        "recent": list(auth_rollup.get("recent") or []),
        "status_counts": dict(auth_rollup.get("status_counts") or {}),
        "sessions": dict(auth_rollup.get("sessions") or {}),
    }
    payload["projection"] = projection.model_dump()
    return payload


def build_my_health_payload(request: Request, profile: dict[str, Any]) -> dict[str, Any]:
    groups = profile.get("groups")
    roles = [str(item) for item in groups] if isinstance(groups, list) else []
    payload = base_frame(request, status="ok")
    payload["principal"] = {
        "subject": str(profile.get("sub") or ""),
        "email": str(profile.get("email") or ""),
        "name": str(profile.get("email") or "") or None,
        "roles": roles or ["OPERATOR"],
        "auth_mode": "cognito",
        "expires_at": None,
        "service_principal": False,
    }
    return payload


def probe_database(service: Any) -> dict[str, Any]:
    started = monotonic()
    backend = getattr(service, "backend", None)
    if backend is None or not hasattr(backend, "session_scope"):
        return {
            "status": "unknown",
            "latency_ms": round((monotonic() - started) * 1000, 3),
            "detail": "backend unavailable",
        }
    try:
        with backend.session_scope(commit=False) as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "latency_ms": round((monotonic() - started) * 1000, 3),
            "detail": "ok",
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency_ms": round((monotonic() - started) * 1000, 3),
            "detail": str(exc),
        }
