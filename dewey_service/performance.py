"""Request-local read budgets and bounded, payload-free performance evidence."""
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from time import monotonic
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException

_current = ContextVar("dewey_performance", default=None)
_lock = Lock()
_active = {}
_recent = deque(maxlen=200)
_started = 0
_completed = 0


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
    if state["interactive_read"]:
        milliseconds = max(1, min(10000, int(remaining_seconds() * 1000)))
        cursor.execute("SELECT set_config('statement_timeout', %s, true), set_config('lock_timeout', '1000', true)", (str(milliseconds),))
    metric("query_count", 1)


def after_query(conn, cursor, statement, parameters, context, executemany):
    started = getattr(context, "_dewey_query_started", None)
    if started is not None:
        metric("sql_ms", (monotonic() - started) * 1000)


def query_error(exception_context):
    context = exception_context.execution_context
    started = getattr(context, "_dewey_query_started", None)
    if started is not None:
        metric("sql_ms", (monotonic() - started) * 1000)
    metric("query_failures", 1)


def snapshot():
    with _lock:
        return {"started": _started, "completed": _completed,
                "active_count": _started - _completed,
                "active": [{"request_id": key, "route": value["route"],
                            "elapsed_ms": round((monotonic() - value["started"]) * 1000, 2)}
                           for key, value in _active.items()],
                "recent": list(_recent)}


class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        global _started, _completed
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        from dewey_service.report_preview import redacted_path
        path = redacted_path(scope["path"])
        read = (scope["method"] == "GET" and path.startswith(("/api/v1/storage/", "/api/v1/records/", "/api/v1/registry/"))) or (
            scope["method"] == "POST" and path in {"/api/v1/registry/search", "/api/v1/registry/search/counts"})
        request_id = uuid4().hex
        # Before routing, redact object identities; query strings are never stored.
        route = "/api/v1/records/:euid" if path.startswith("/api/v1/records/") else path
        if path.startswith(("/records/", "/shares/")):
            route = path.split("/")[1] + "/:euid"
        state = {"started": monotonic(), "route": route, "method": scope["method"],
                 "interactive_read": read, "query_count": 0, "sql_ms": 0,
                 "s3_ms": 0, "cache_hits": 0, "cache_misses": 0, "response_bytes": 0,
                 "status": 500, "response_complete": False}
        token = _current.set(state)
        with _lock:
            _started += 1
            if len(_active) < 256:
                _active[request_id] = state

        async def observed_send(message):
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                message["headers"] = [*message.get("headers", []), (b"x-dewey-request-id", request_id.encode())]
            elif message["type"] == "http.response.body":
                metric("response_bytes", len(message.get("body", b"")))
                if not message.get("more_body", False):
                    state["response_complete"] = True
            await send(message)

        try:
            await self.app(scope, receive, observed_send)
        finally:
            record = {key: value for key, value in state.items() if key not in {"started", "interactive_read"}}
            record.update(request_id=request_id, duration_ms=round((monotonic() - state["started"]) * 1000, 2),
                          route=redacted_path(getattr(scope.get("route"), "path", route)),
                          observed_at=datetime.now(timezone.utc).isoformat())
            with _lock:
                _active.pop(request_id, None)
                _recent.appendleft(record)
                _completed += 1
            _current.reset(token)
