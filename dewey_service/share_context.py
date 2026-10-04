"""Request-local, verified ingress and identity for managed sharing."""
from __future__ import annotations

import hmac
import re
from urllib.parse import urlsplit
from uuid import uuid4
from contextlib import contextmanager
from contextvars import ContextVar
from fastapi import HTTPException

_CONTEXT: ContextVar[dict | None] = ContextVar("dewey_share_context", default=None)


def current_share_audit_context() -> dict:
    value = _CONTEXT.get() or {}
    return {key: value[key] for key in ("request_id", "trusted_tailnet", "managed_origin") if key in value}


def share_context_available() -> bool:
    value = _CONTEXT.get()
    from dewey_service.registry_access import current_principal
    actor = current_principal()
    return bool(value and value.get("trusted_tailnet") is True and value.get("managed_origin") is True and actor
                and actor.subject and actor.email and not actor.service)


def require_share_context() -> dict:
    if not share_context_available():
        raise HTTPException(403, "Managed sharing requires trusted Tailscale ingress and a verified current identity")
    from dewey_service.registry_access import principal
    actor = principal()
    return {**dict(_CONTEXT.get()), "identity_verified": True,
            "subject": actor.subject, "email": actor.email}


@contextmanager
def share_context_context(value: dict):
    token = _CONTEXT.set(dict(value))
    try:
        yield
    finally:
        _CONTEXT.reset(token)


def require_trusted_tailnet(request) -> None:
    """Accept only an assertion from the configured private proxy transport.

    The proxy MUST remove the client-supplied assertion and set its configured
    secret only on its Tailscale-bound listener. Uvicorn must not rewrite the
    transport peer using forwarded headers. No IP/Host header proves ingress.
    """
    settings = request.app.state.settings
    peer = request.scope.get("client")
    configured_peer = settings.share_trusted_proxy_peer
    expected = settings.share_ingress_assertion
    values = request.headers.getlist(settings.share_ingress_assertion_header)
    if (not configured_peer or not expected or not peer or peer[0] != configured_peer
            or len(values) != 1 or not hmac.compare_digest(values[0].encode("latin-1"), expected.encode("utf-8"))):
        raise HTTPException(403, "Trusted Tailscale ingress is required")


class ManagedShareIngressMiddleware:
    """Pure ASGI context; principal resolution can safely run inside it."""
    def __init__(self, app, *, settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        peer = scope.get("client")
        header = self.settings.share_ingress_assertion_header.lower().encode("ascii")
        values = [value for name, value in scope.get("headers", ()) if name.lower() == header]
        expected = self.settings.share_ingress_assertion
        trusted = bool(self.settings.share_trusted_proxy_peer and expected and peer
                       and peer[0] == self.settings.share_trusted_proxy_peer and len(values) == 1
                       and hmac.compare_digest(values[0], expected.encode("utf-8")))
        from starlette.datastructures import Headers
        headers = Headers(scope=scope)
        authority, origin = headers.get("host", ""), headers.get("origin")
        application = self.settings.share_application_origin
        content = bool(re.fullmatch(r"pv-[0-9a-f]{32}\." + re.escape(self.settings.share_content_host_suffix), authority)
                       and scope.get("path", "").startswith("/__dewey_preview/"))
        managed_origin = (authority == urlsplit(application).netloc and origin in {None, application}) or (
            content and origin in {None, application, "https://" + authority})
        scope.setdefault("state", {})["trusted_tailnet"] = trusted
        with share_context_context({"trusted_tailnet": trusted, "managed_origin": managed_origin,
                                    "request_id": str(uuid4())}):
            await self.app(scope, receive, send)
