"""Transport and origin boundaries around the managed-share surfaces."""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse


def validate_sharing_configuration(settings):
    from dewey_service.preview_sessions import require_preview_configuration
    require_preview_configuration(settings)
    if not settings.share_ingress_assertion or len(settings.share_ingress_assertion) < 32:
        raise RuntimeError("Sharing requires a private proxy assertion of at least 32 characters")
    if not settings.share_ingress_assertion.isascii() or any(c.isspace() for c in settings.share_ingress_assertion):
        raise RuntimeError("The private proxy assertion must be an ASCII token")
    try:
        peer = ipaddress.ip_address(settings.share_trusted_proxy_peer)
    except ValueError as exc:
        raise RuntimeError("Sharing requires an explicit loopback proxy peer") from exc
    if not peer.is_loopback:
        raise RuntimeError("The sharing backend must accept its private proxy on loopback")


class ShareHostBoundaryMiddleware:
    def __init__(self, app, *, settings):
        self.app, self.settings = app, settings
        self.application_host = urlsplit(settings.share_application_origin).netloc
        self.content_pattern = re.compile(r"pv-[0-9a-f]{32}\." + re.escape(settings.share_content_host_suffix))

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        authority = headers.get("host", "")
        host = authority.split(":", 1)[0].rstrip(".").lower()
        suffix = self.settings.share_content_host_suffix
        content_host = host == suffix or host.endswith("." + suffix)
        path = scope.get("path", "")
        content_path = path.startswith("/__dewey_preview/")
        managed = (path == "/shares" or path.startswith("/shares/")
            or path.startswith("/api/v1/shares") or path.startswith("/api/v1/registry/shares")
            or path.startswith("/api/v1/share-roots") or path.startswith("/share-roots")
            or re.fullmatch(r"/api/v1/records/[^/]+/shares(?:/preview)?", path) is not None)

        async def deny(status, detail):
            await JSONResponse({"detail": detail}, status_code=status,
                headers={"Cache-Control": "no-store"})(scope, receive, send)

        if content_host:
            if authority != host or not self.content_pattern.fullmatch(host) or not content_path:
                return await deny(404, "Preview context unavailable")
            if not scope.get("state", {}).get("trusted_tailnet"):
                return await deny(403, "Trusted Tailscale ingress is required")
            # Same-origin report fetches and the exact application handoff are
            # the only origins allowed on the isolated content surface.
            origin = headers.get("origin")
            if origin and origin not in {"https://" + host, self.settings.share_application_origin}:
                return await deny(403, "Preview origin not allowed")
        elif content_path:
            return await deny(404, "Preview context unavailable")
        elif managed:
            if authority != self.application_host:
                return await deny(404, "Managed shares require the configured Dewey host")
            if not scope.get("state", {}).get("trusted_tailnet"):
                return await deny(403, "Trusted Tailscale ingress is required")
            if (scope["method"] not in {"GET", "HEAD", "OPTIONS"}
                    and headers.get("origin") not in {None, self.settings.share_application_origin}):
                return await deny(403, "Share changes must originate from Dewey")
        await self.app(scope, receive, send)
