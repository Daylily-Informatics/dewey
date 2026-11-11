"""Request-local read budgets and bounded, payload-free performance evidence."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from threading import Lock
from time import monotonic
from uuid import uuid4

from fastapi import HTTPException

_current = ContextVar("dewey_performance", default=None)
_lock = Lock()
_instrument_lock = Lock()
_active = {}
_recent = deque(maxlen=200)
_started = 0
_completed = 0
_REGISTRATION_ROUTES = {
    "/api/v1/records",
    "/api/v1/analysis-results/register",
    "/api/v1/artifact-sets/analysis/register",
    "/api/v1/artifact-sets/multiqc/register",
}
_SQL_KINDS = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "SET", "SAVEPOINT", "RELEASE", "ROLLBACK"}


def instrument_engine(engine):
    """Use the public Session bind; TapDB's runtime wrapper is not an Engine."""
    from sqlalchemy import event

    with _instrument_lock:
        if not event.contains(engine, "before_cursor_execute", before_query):
            event.listen(engine, "before_cursor_execute", before_query)
            event.listen(engine, "after_cursor_execute", after_query)
            event.listen(engine, "handle_error", query_error)


def remaining_seconds():
    state = _current.get()
    if state is None or not state["interactive_read"]:
        return 15.0
    remaining = 15.0 - (monotonic() - state["started"])
    if remaining <= 0:
        raise HTTPException(504, "Dewey read deadline exceeded; retry or narrow the query")
    return remaining


def metric(name, value):
    state = _current.get()
    if state is not None:
        state[name] = state.get(name, 0) + value


@contextmanager
def measure(name):
    started = monotonic()
    try:
        yield
    finally:
        metric(name, (monotonic() - started) * 1000)


def before_query(conn, cursor, statement, parameters, context, executemany):
    state = _current.get()
    if state is None:
        return
    context._dewey_query_started = monotonic()
    if state["registration"]:
        words = statement.split(maxsplit=1)
        kind = words[0].upper() if words else ""
        context._dewey_sql_kind = kind if kind in _SQL_KINDS else "OTHER"
    if state["interactive_read"]:
        milliseconds = max(1, min(10000, int(remaining_seconds() * 1000)))
        cursor.execute(
            "SELECT set_config('statement_timeout', %s, true), set_config('lock_timeout', '1000', true)",
            (str(milliseconds),),
        )
    metric("query_count", 1)


def _record_sql(context):
    started = getattr(context, "_dewey_query_started", None)
    state = _current.get()
    if started is None or state is None:
        return
    elapsed = (monotonic() - started) * 1000
    metric("sql_ms", elapsed)
    if state["registration"]:
        kind = context._dewey_sql_kind
        by_kind = state["sql_by_kind"].setdefault(kind, {"count": 0, "duration_ms": 0.0})
        by_kind["count"] += 1
        by_kind["duration_ms"] += elapsed
        if elapsed > state["slowest_sql_ms"]:
            state["slowest_sql_ms"] = elapsed
            state["slowest_sql_kind"] = kind
            compiled = getattr(context, "compiled", None)
            state["slowest_sql_fingerprint"] = (
                sha256(compiled.string.encode()).hexdigest() if compiled is not None else None
            )


def after_query(conn, cursor, statement, parameters, context, executemany):
    _record_sql(context)


def query_error(exception_context):
    _record_sql(exception_context.execution_context)
    metric("query_failures", 1)


def snapshot():
    with _lock:
        return {
            "started": _started,
            "completed": _completed,
            "active_count": _started - _completed,
            "active": [
                {
                    "request_id": key,
                    "route": value["route"],
                    "elapsed_ms": round((monotonic() - value["started"]) * 1000, 2),
                }
                for key, value in _active.items()
            ],
            "recent": list(_recent),
        }


class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        global _started, _completed
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        from dewey_service.report_preview import redacted_path

        path = redacted_path(scope["path"])
        read = (
            scope["method"] == "GET"
            and path.startswith(("/api/v1/storage/", "/api/v1/records/", "/api/v1/registry/"))
        ) or (
            scope["method"] == "POST"
            and path in {"/api/v1/registry/search", "/api/v1/registry/search/counts"}
        )
        request_id = uuid4().hex
        # Before routing, redact object identities; query strings are never stored.
        route = "/api/v1/records/:euid" if path.startswith("/api/v1/records/") else path
        if path.startswith(("/records/", "/shares/")):
            route = path.split("/")[1] + "/:euid"
        state = {
            "started": monotonic(),
            "route": route,
            "method": scope["method"],
            "interactive_read": read,
            "registration": scope["method"] == "POST" and path in _REGISTRATION_ROUTES,
            "query_count": 0,
            "sql_ms": 0,
            "s3_ms": 0,
            "db_session_ms": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "response_bytes": 0,
            "status": 500,
            "response_complete": False,
        }
        if state["registration"]:
            state.update(sql_by_kind={}, slowest_sql_ms=0.0, slowest_sql_kind=None,
                         slowest_sql_fingerprint=None, storage_authorization_ms=0.0)
        token = _current.set(state)
        with _lock:
            _started += 1
            if len(_active) < 256:
                _active[request_id] = state

        async def observed_send(message):
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-dewey-request-id", request_id.encode()),
                ]
            elif message["type"] == "http.response.body":
                metric("response_bytes", len(message.get("body", b"")))
                if not message.get("more_body", False):
                    state["response_complete"] = True
            await send(message)

        try:
            await self.app(scope, receive, observed_send)
        finally:
            record = {
                key: value
                for key, value in state.items()
                if key not in {"started", "interactive_read", "registration"}
            }
            record.update(
                request_id=request_id,
                duration_ms=round((monotonic() - state["started"]) * 1000, 2),
                route=redacted_path(getattr(scope.get("route"), "path", route)),
                observed_at=datetime.now(timezone.utc).isoformat(),
            )
            with _lock:
                _active.pop(request_id, None)
                _recent.appendleft(record)
                _completed += 1
            _current.reset(token)
            if state["registration"]:
                logging.getLogger("uvicorn.error").info(
                    json.dumps({"event": "dewey_registration_performance", **record},
                               separators=(",", ":"))
                )
