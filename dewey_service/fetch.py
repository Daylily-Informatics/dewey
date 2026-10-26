"""Stable, authenticated recipient URLs independent of object storage locations."""
from __future__ import annotations

import html
from urllib.parse import urlencode

from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from dewey_service.registry_access import current_principal
from dewey_service.share_context import require_share_context, require_share_ingress
from dewey_service.share_exports import archive_delivery, fetch_path, manifest_page
from dewey_service.share_gateway import exact_relative_key, object_delivery


def _browser(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "").lower() and not request.headers.get("authorization")


def _recipient(request: Request):
    require_share_ingress(request)
    actor = current_principal()
    if actor is None or not actor.email_verified:
        if _browser(request) and request.method == "GET" and request.url.path.startswith("/fetch/"):
            destination = request.url.path + ("?" + request.url.query if request.url.query else "")
            return RedirectResponse("/auth/login?" + urlencode({"next": destination}), status_code=303,
                headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
        raise HTTPException(401, "Sign in or supply a verified personal access token",
            headers={"WWW-Authenticate": "Bearer"})
    require_share_context()
    return None


def _json_response(payload: dict, *, head=False):
    response = JSONResponse(payload, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff"})
    if head:
        response.body = b""
    return response


def _listing_page(request, resolved, page, *, path=""):
    root = fetch_path(resolved["share_euid"], path)
    esc = html.escape
    rows = "".join(f'<tr><td><a href="{esc(item["fetch_path"], quote=True)}">{esc(item["path"])}</a></td>'
        f'<td>{item["size"]:,} B</td></tr>' for item in page["items"])
    more = ""
    if page["continuation_token"]:
        more = '<p><a href="' + esc(root + "?" + urlencode({"continuation_token": page["continuation_token"]}), quote=True) + '">Next page</a></p>'
    text = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Shared files · Dewey</title><body><main><h1>' + esc(resolved.get("name") or "Shared files") + '</h1>'
        '<p>Access is checked for your verified account on every request.</p><nav><a href="' + esc(root + '?format=manifest', quote=True)
        + '">Download manifest</a> · <a href="' + esc(root + '?format=tar', quote=True) + '">Download all as TAR</a>'
        ' · <a href="/recipient/account">Account and command-line access</a></nav>'
        '<p>' + str(len(page["items"])) + (' files on this page; more pages follow.' if page["incomplete"] else ' files on this final page.')
        + '</p><table><thead><tr><th>File</th><th>Size</th></tr></thead><tbody>' + (rows or '<tr><td colspan="2">No permitted files on this page.</td></tr>')
        + '</tbody></table>' + more + '</main></body></html>')
    response = HTMLResponse(text, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        "X-Content-Type-Options": "nosniff"})
    if request.method == "HEAD":
        response.body = b""
    return response


def attach_fetch_routes(app, service):
    @app.api_route("/fetch/{identifier}", methods=["GET", "HEAD"], tags=["Recipient sharing"])
    @app.api_route("/fetch/{identifier}/{relative_path:path}", methods=["GET", "HEAD"], tags=["Recipient sharing"])
    def fetch(identifier: str, request: Request, relative_path: str = "", format: str | None = None,
              limit: int = Query(default=200, ge=1, le=200), continuation_token: str | None = None,
              download: bool = False):
        redirect = _recipient(request)
        if redirect is not None:
            return redirect
        exact_relative_key(relative_path)
        if format not in {None, "manifest", "tar"}:
            raise HTTPException(400, "format must be manifest or tar")
        resolved = service.resolve_share_identifier(identifier)
        if format == "tar":
            if continuation_token:
                raise HTTPException(400, "A TAR archive always begins with a complete inventory")
            return archive_delivery(request, service, resolved, path=relative_path)
        if format == "manifest":
            return _json_response(manifest_page(service, resolved, path=relative_path, limit=limit,
                continuation_token=continuation_token), head=request.method == "HEAD")
        report_path = resolved.get("report_entrypoint")
        if resolved.get("content_mode") == "www" and _browser(request) and not download:
            selected = relative_path or report_path
            if selected and selected == report_path:
                from dewey_service.report_preview import report_entry_page
                receipt = service.resolve_share_fetch(identifier, selected)
                return report_entry_page(request, resolved, receipt)
        is_single_object = (not resolved["namespaced"] and len(resolved["members"]) == 1
            and resolved["members"][0]["target_kind"] == "artifact_object")
        if (relative_path and (not relative_path.endswith("/") or download)) or is_single_object:
            if continuation_token:
                raise HTTPException(400, "Continuation tokens apply only to a directory inventory")
            receipt = service.resolve_share_fetch(identifier, relative_path)
            return object_delivery(request, service, receipt)
        page = manifest_page(service, resolved, path=relative_path, limit=limit, continuation_token=continuation_token)
        if _browser(request):
            return _listing_page(request, resolved, page, path=relative_path)
        return _json_response(page, head=request.method == "HEAD")

    @app.get("/api/v2/recipient/shares/{identifier}", tags=["Recipient sharing"])
    def recipient_share(identifier: str, request: Request):
        _recipient(request)
        resolved = service.resolve_share_identifier(identifier)
        # Storage locations and management-only details do not cross this API.
        return {key: resolved[key] for key in ("share_euid", "fetch_path", "name", "policy_revision",
            "content_mode", "expires_at", "namespaced", "report_entrypoint", "report_bundle_root") if key in resolved}

    @app.get("/api/v2/recipient/shares/{identifier}/contents", tags=["Recipient sharing"])
    def recipient_contents(identifier: str, request: Request, path: str = "",
                           limit: int = Query(default=200, ge=1, le=200), continuation_token: str | None = None):
        _recipient(request)
        resolved = service.resolve_share_identifier(identifier)
        return _json_response(manifest_page(service, resolved, path=path, limit=limit, continuation_token=continuation_token))
