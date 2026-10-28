"""Current-viewer report sessions on isolated, authenticated content hosts."""

from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import mimetypes
import re
import secrets
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote

from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import Body, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from dewey_service.audit import authenticated_user_email_context
from dewey_service.preview_sessions import (
    binding_principal,
    current_session_binding,
    live_session_binding,
    operation_row,
    require_preview_configuration,
)
from dewey_service.registry_access import OPERATION_TEMPLATE, principal, principal_context
from dewey_service.share_context import require_share_context, require_share_ingress
from dewey_service.share_gateway import exact_relative_key, object_delivery, reserve_report_delivery
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso

_COOKIE = "__Host-dewey_preview"


def redacted_path(path):
    return re.sub(r"(/previews/[^/]+/)[^/]+", r"\1[retired]", path)


class PreviewLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(redacted_path(v) if isinstance(v, str) else v for v in record.args)
        if isinstance(record.msg, str):
            record.msg = redacted_path(record.msg)
        return True


def _hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _live_context(service, settings, session, row):
    data = normalize_instance_payload(row)
    if (
        data.get("operation") != "isolated_report_context"
        or data.get("status") == "revoked"
        or datetime.fromisoformat(data["expires_at"]) <= datetime.now(timezone.utc)
    ):
        raise HTTPException(410, "Preview expired; reopen it from Dewey")
    # Resolve authoritative session binding through native lineage, never a
    # copied object-reference string in metadata.
    bindings = (
        session.query(generic_instance)
        .join(
            generic_instance_lineage,
            generic_instance_lineage.parent_instance_uid == generic_instance.uid,
        )
        .filter(
            generic_instance_lineage.child_instance_uid == row.uid,
            generic_instance_lineage.relationship_type == "has_report_context",
            generic_instance_lineage.is_deleted.is_(False),
            generic_instance.is_deleted.is_(False),
        )
        .all()
    )
    if len(bindings) != 1:
        raise HTTPException(409, "Preview session relationship unavailable")
    binding = live_session_binding(service, settings, session, bindings[0].euid)
    if data.get("actor") != binding.get("actor"):
        raise HTTPException(409, "Preview viewer binding is invalid")
    targets = (
        session.query(generic_instance)
        .join(
            generic_instance_lineage,
            generic_instance_lineage.parent_instance_uid == generic_instance.uid,
        )
        .filter(
            generic_instance_lineage.child_instance_uid == row.uid,
            generic_instance_lineage.relationship_type == "preview_target",
            generic_instance_lineage.is_deleted.is_(False),
            generic_instance.is_deleted.is_(False),
        )
        .all()
    )
    shares = (
        session.query(generic_instance)
        .join(
            generic_instance_lineage,
            generic_instance_lineage.parent_instance_uid == generic_instance.uid,
        )
        .filter(
            generic_instance_lineage.child_instance_uid == row.uid,
            generic_instance_lineage.relationship_type == "has_storage_operation",
            generic_instance_lineage.is_deleted.is_(False),
            generic_instance.is_deleted.is_(False),
        )
        .all()
    )
    if len(targets) != 1 or len(shares) != 1:
        raise HTTPException(409, "Preview source relationship unavailable")
    from dewey_service.services.share_expiry import validate_activation_generation
    validate_activation_generation(data, normalize_instance_payload(shares[0]))
    return data, binding, bindings[0].euid, shares[0].euid, targets[0].euid


def _host_context(request, service, session, *, lock=False):
    settings = request.app.state.settings
    require_preview_configuration(settings)
    require_share_ingress(request)
    # Host selects a persisted context only; transport attestation authorizes
    # network access. App APIs are separately excluded from this subtree.
    host = request.url.hostname
    if not host or not re.fullmatch(
        r"pv-[0-9a-f]{32}\." + re.escape(settings.share_content_host_suffix), host
    ):
        raise HTTPException(404, "Preview context unavailable")
    if request.headers.get("host") != host:
        raise HTTPException(404, "Preview host authority is not canonical")
    template = service.backend.templates.get_template(
        session, OPERATION_TEMPLATE, domain_code=service.backend.domain_code
    )
    if template is None:
        raise RuntimeError("Missing native storage_operation template")
    query = session.query(generic_instance).filter(
        generic_instance.template_uid == template.uid,
        generic_instance.is_deleted.is_(False),
        generic_instance.json_addl["context_host"].astext == host,
        generic_instance.json_addl["operation"].astext == "isolated_report_context",
    )
    if lock:
        query = query.with_for_update()
    row = query.first()
    if row is None:
        raise HTTPException(404, "Preview context unavailable")
    return row, _live_context(service, settings, session, row)


@contextmanager
def _attributed_host_write(request, service):
    # Isolated hosts deliberately have no application session cookie. Resolve
    # their native session lineage read-only, then restore its current verified
    # viewer before opening a transaction that requires write attribution.
    with service.backend.session_scope(commit=False) as session:
        row, context = _host_context(request, service, session)
        expected = deepcopy((row.euid, context[1:]))
    actor = binding_principal(context[1], request.app.state.settings)
    with principal_context(actor), authenticated_user_email_context(actor.email):
        with service.backend.session_scope(commit=True) as session:
            row, context = _host_context(request, service, session, lock=True)
            # Recheck the live context/session under its native row lock. The
            # verified identity must still describe the exact same binding and
            # source relationships observed before the provider check.
            if (row.euid, context[1:]) != expected:
                raise HTTPException(409, "Preview session changed; reopen it from Dewey")
            yield session, row, context


def _cookie_matches(request, data):
    cookie = request.cookies.get(_COOKIE, "")
    if not cookie or not hmac.compare_digest(_hash(cookie), str(data.get("cookie_sha256", ""))):
        raise HTTPException(401, "Preview host challenge is required")


def _report_csp(settings, *, nonce=None):
    if nonce:
        return (
            f"default-src 'none'; script-src 'nonce-{nonce}'; "
            f"frame-ancestors {settings.share_application_origin}; base-uri 'none'; form-action 'none'; "
            "object-src 'none'; worker-src 'none'"
        )
    # Report export handlers need submit events and blob downloads. Actual form
    # navigation remains blocked by form-action below.
    return (
        "sandbox allow-scripts allow-same-origin allow-forms allow-downloads; default-src 'none'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
        "worker-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'; "
        "navigate-to 'self'; "
        f"frame-ancestors {settings.share_application_origin}"
    )


def _headers(settings, *, nonce=None):
    return {
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": _report_csp(settings, nonce=nonce),
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    }


def _context_expiry(now, share_expiry, session_expiry=None):
    deadlines = [now + timedelta(seconds=900)]
    for value in (share_expiry, session_expiry):
        if value is not None:
            deadlines.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
    return min(deadlines)


def report_entry_page(request, resolved, receipt):
    """The durable application URL contains only the trusted viewer shell."""
    settings = request.app.state.settings
    require_preview_configuration(settings)
    nonce = secrets.token_urlsafe(24)
    endpoint = "/api/v2/recipient/shares/" + quote(resolved["share_euid"], safe="") + "/preview"
    config = json.dumps(
        {
            "endpoint": endpoint,
            "content_suffix": settings.share_content_host_suffix,
            "body": {
                "target_euid": receipt["target_euid"],
                "relative_key": receipt["relative_key"],
                "bundle_root": resolved.get("report_bundle_root", ""),
            },
        },
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    script = (Path(__file__).parent / "static" / "report-section-host.js").read_text() + "\n" + """
const config = CONFIG;
const frame = document.getElementById('report');
const status = document.getElementById('status');
const banner = document.getElementById('report-notice');
const dismiss = document.getElementById('dismiss-notice');
let noticeTimer, noticeError=false;
function hideNotice() { if (!noticeError) banner.hidden=true; }
function reportError(error) {
  noticeError=true; clearTimeout(noticeTimer); banner.hidden=false; dismiss.hidden=true;
  status.setAttribute('role','alert'); status.textContent=error.message;
}
dismiss.addEventListener('click', hideNotice);
window.addEventListener('load', () => { noticeTimer=setTimeout(hideNotice, 10000); }, {once:true});
async function post(path, body) {
  const response = await fetch(path, {method:'POST', credentials:'same-origin',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if (!response.ok) { let detail='Report access failed ('+response.status+')';
    try { detail=(await response.json()).detail || detail; } catch (_) {}
    throw new Error(typeof detail==='string'?detail:'Report access failed'); }
  return response.json();
}
(async () => {
  const view = await post(config.endpoint, config.body);
  const origin = new URL(view.preview_origin), challenge = new URL(view.challenge_url);
  const handoffEndpoint = new URL(view.handoff_endpoint, location.origin);
  if (origin.protocol!=='https:' || origin.hostname.split('.').slice(1).join('.')!==config.content_suffix ||
      !/^pv-[0-9a-f]{32}$/.test(origin.hostname.split('.')[0]) || origin.port || origin.username || origin.password ||
      origin.href!==origin.origin+'/' || challenge.origin!==origin.origin || challenge.pathname!=='/__dewey_preview/challenge' ||
      handoffEndpoint.origin!==location.origin || !handoffEndpoint.pathname.startsWith(config.endpoint+'/'))
    throw new Error('Invalid report host configuration');
  retainReportSections(origin.origin, frame, reportError, hideNotice, status);
  let used=false;
  window.addEventListener('message', async event => {
    if (used || event.origin!==origin.origin || event.source!==frame.contentWindow ||
        event.data?.type!=='dewey-preview-challenge' || event.data.context_euid!==view.context_euid ||
        !/^[0-9a-f]{64}$/.test(event.data.challenge || '')) return;
    used=true;
    try {
      const handoff=await post(handoffEndpoint.pathname, {challenge:event.data.challenge});
      if (!handoff.token || handoff.handoff_url!==origin.origin+'/__dewey_preview/handoff')
        throw new Error('Invalid report handoff');
      const form=document.createElement('form'), token=document.createElement('input');
      form.method='POST'; form.action=handoff.handoff_url; form.target=frame.name; form.hidden=true;
      token.name='token'; token.value=handoff.token; form.append(token); document.body.append(form);
      form.submit(); form.remove(); status.textContent='Report session expires '+view.expires_at+'. Reopen this URL to renew.';
    } catch (error) { reportError(error); }
  });
  frame.src=challenge.href;
})().catch(reportError);
""".replace("CONFIG", config, 1)
    title = html.escape(resolved.get("name") or "Shared report")
    content = (
        f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{title} · Dewey</title><style nonce="{nonce}">'
        "html{height:100%}body{margin:0;height:100dvh;display:flex;flex-direction:column;overflow:hidden;font:15px system-ui}"
        "header{flex:0 0 auto;display:flex;align-items:flex-start;gap:12px;padding:8px 12px;border-bottom:1px solid #dfe6e0}"
        "header[hidden]{display:none}.notice-text{flex:1;min-width:0}h1{font-size:14px;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
        "#status{font-size:12px;margin:3px 0 0;overflow-wrap:anywhere}#dismiss-notice{flex:0 0 auto;border:0;background:transparent;padding:0 4px;font:22px system-ui;cursor:pointer}"
        "iframe{display:block;width:100%;flex:1 1 0;min-height:0;border:0}iframe[hidden]{display:none}</style>"
        f'<header id="report-notice"><div class="notice-text"><h1 title="{title}">{title}</h1><p id="status" role="status">Opening your authorized report…</p></div>'
        '<button id="dismiss-notice" type="button" aria-label="Dismiss report notice">×</button></header>'
        '<iframe id="report" name="dewey-isolated-report" title="Shared report" sandbox="allow-scripts allow-same-origin allow-forms allow-downloads" '
        f'referrerpolicy="no-referrer"></iframe><script nonce="{nonce}">{script}</script></html>'
    )
    content_origin = "https://*." + settings.share_content_host_suffix
    # A native cross-origin POST form needs the real application Origin for
    # the one-use handoff. no-referrer would serialize that Origin as null.
    headers = {
        "Cache-Control": "no-store",
        "Referrer-Policy": "strict-origin",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
        f"connect-src 'self'; frame-src {content_origin}; form-action {content_origin}; frame-ancestors 'none'; base-uri 'none'",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    }
    response = HTMLResponse(content, headers=headers)
    if request.method == "HEAD":
        response.body = b""
    return response


def attach_report_preview(app, router, service):
    logging.getLogger("uvicorn.access").addFilter(PreviewLogFilter())

    @router.post("/records/{euid}/preview", tags=["EUID registry"])
    def retired_record_preview(euid: str):
        raise HTTPException(
            409, "Select an authorized managed share and an explicit report bundle root for preview"
        )

    @app.api_route("/previews/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def retired_bearer_preview(path: str):
        raise HTTPException(
            410, "Stored-issuer bearer report previews are retired; reopen through a managed share"
        )

    @app.post("/api/v2/recipient/shares/{share_euid}/preview", tags=["Recipient sharing"])
    @router.post("/registry/shares/{share_euid}/preview", tags=["Managed sharing"])
    def create_preview(share_euid: str, request: Request, body: dict = Body(...)):
        require_share_context()
        share_euid = service.resolve_share_identifier(share_euid)["share_euid"]
        settings = request.app.state.settings
        require_preview_configuration(settings)
        if set(body) != {"target_euid", "relative_key", "bundle_root"}:
            raise HTTPException(
                400, "Supply target_euid, exact relative_key and explicit bundle_root"
            )
        target = body["target_euid"]
        if not isinstance(target, str) or not target:
            raise HTTPException(400, "A persisted target EUID is required")
        relative = exact_relative_key(body["relative_key"])
        root = exact_relative_key(body["bundle_root"])
        if root and not root.endswith("/"):
            raise HTTPException(400, "bundle_root must be empty or end in a slash")
        if not relative.startswith(root):
            raise HTTPException(400, "Report must be inside its explicit bundle root")
        receipt = service.authorize_share_object(share_euid, target, relative, action="report")
        if not receipt["key"].lower().endswith((".html", ".htm")):
            raise HTTPException(400, "Preview requires an HTML report")
        binding_euid = current_session_binding(request, service)
        context_host = "pv-" + secrets.token_hex(16) + "." + settings.share_content_host_suffix
        now = datetime.now(timezone.utc)
        expires = _context_expiry(now, receipt["expires_at"])
        with service.backend.session_scope(commit=True) as session:
            binding = operation_row(service, session, binding_euid)
            session_data = live_session_binding(service, settings, session, binding_euid)
            expires = _context_expiry(now, receipt["expires_at"], session_data["expires_at"])
            share = service._canonical_share(session, share_euid)
            if normalize_instance_payload(share)["policy_revision"] != receipt["policy_revision"]:
                raise HTTPException(409, "Share policy changed before preview creation; reopen from Dewey")
            target_row = next(
                (v for v in service._share_members(session, share) if v.euid == target), None
            )
            if target_row is None:
                raise HTTPException(403, "Preview target is unavailable")
            row = service.backend.create_instance(
                session,
                template_code=OPERATION_TEMPLATE,
                name="Isolated report context",
                json_addl={
                    "operation": "isolated_report_context",
                    "status": "pending",
                    "actor": principal().subject,
                    "context_host": context_host,
                    "bundle_root": root,
                    "report_relative_key": relative,
                    "object_only": not relative,
                    "share_activation_generation": normalize_instance_payload(share).get("activation_generation", 0),
                    "created_at": utc_now_iso(),
                    "expires_at": expires.isoformat(),
                },
            )
            service.backend.create_lineage(
                session, parent=binding, child=row, relationship_type="has_report_context"
            )
            service.backend.create_lineage(
                session, parent=share, child=row, relationship_type="has_storage_operation"
            )
            service.backend.create_lineage(
                session, parent=target_row, child=row, relationship_type="preview_target"
            )
            context_euid = row.euid
        service.append_share_event(
            share_euid,
            event_type="report_context_created",
            decision="allow",
            grant_euid=receipt["grant_euid"],
            target_euid=target,
            details={
                "context_euid": context_euid,
                "bundle_root": root,
                "policy_revision": receipt["policy_revision"],
                "expires_at": expires.isoformat(),
            },
        )
        origin = "https://" + context_host
        recipient = request.url.path.startswith("/api/v2/recipient/")
        endpoint_root = "/api/v2/recipient/shares/" if recipient else "/api/v1/registry/shares/"
        return {
            "context_euid": context_euid,
            "preview_origin": origin,
            "challenge_url": origin + "/__dewey_preview/challenge",
            "handoff_endpoint": f"{endpoint_root}{quote(share_euid, safe='')}/preview/{quote(context_euid, safe='')}/handoff",
            "expires_at": expires.isoformat(),
        }

    @app.get("/__dewey_preview/challenge", include_in_schema=False)
    def preview_challenge(request: Request):
        settings = request.app.state.settings
        cookie, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        with _attributed_host_write(request, service) as (session, row, context):
            data, _, _, _, _ = context
            if data["status"] != "pending":
                raise HTTPException(409, "Preview challenge already issued; reopen from Dewey")
            service.backend.update_instance_json(
                session, row, {"status": "challenged", "cookie_sha256": _hash(cookie)}
            )
            euid = row.euid
        # Challenge is proof of a pending host cookie, not an asset capability.
        payload = json.dumps(
            {"type": "dewey-preview-challenge", "context_euid": euid, "challenge": _hash(cookie)}
        ).replace("<", "\\u003c")
        app_origin = json.dumps(settings.share_application_origin).replace("<", "\\u003c")
        response = HTMLResponse(
            f'<!doctype html><meta charset="utf-8"><script nonce="{nonce}">parent.postMessage({payload},{app_origin});</script>',
            headers=_headers(settings, nonce=nonce),
        )
        response.set_cookie(
            _COOKIE, cookie, secure=True, httponly=True, samesite="strict", path="/", max_age=900
        )
        return response

    @app.post(
        "/api/v2/recipient/shares/{share_euid}/preview/{context_euid}/handoff",
        tags=["Recipient sharing"],
    )
    @router.post(
        "/registry/shares/{share_euid}/preview/{context_euid}/handoff", tags=["Managed sharing"]
    )
    def issue_handoff(share_euid: str, context_euid: str, request: Request, body: dict = Body(...)):
        require_share_context()
        share_euid = service.resolve_share_identifier(share_euid)["share_euid"]
        if (
            set(body) != {"challenge"}
            or not isinstance(body["challenge"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", body["challenge"])
        ):
            raise HTTPException(400, "A preview host challenge is required")
        binding_euid = current_session_binding(request, service)
        token = secrets.token_urlsafe(32)
        with service.backend.session_scope(commit=True) as session:
            row = operation_row(service, session, context_euid, lock=True)
            data, binding, linked_binding, linked_share, target = _live_context(
                service, request.app.state.settings, session, row
            )
            if (
                linked_binding != binding_euid
                or linked_share != share_euid
                or data["status"] != "challenged"
                or not hmac.compare_digest(str(data.get("cookie_sha256", "")), body["challenge"])
            ):
                raise HTTPException(403, "Preview handoff binding mismatch")
            service.authorize_share_object(
                share_euid, target, data["report_relative_key"], action="report"
            )
            deadline = min(
                datetime.now(timezone.utc) + timedelta(seconds=60),
                datetime.fromisoformat(data["expires_at"]),
            )
            service.backend.update_instance_json(
                session,
                row,
                {
                    "status": "handoff_issued",
                    "handoff_sha256": _hash(token),
                    "handoff_expires_at": deadline.isoformat(),
                },
            )
        return {
            "token": token,
            "handoff_url": "https://" + data["context_host"] + "/__dewey_preview/handoff",
        }

    @app.post("/__dewey_preview/handoff", include_in_schema=False)
    async def consume_handoff(request: Request):
        settings = request.app.state.settings
        if request.headers.get("origin") != settings.share_application_origin:
            raise HTTPException(403, "Preview handoff must originate from Dewey")
        if (
            request.headers.get("content-type", "").split(";", 1)[0]
            != "application/x-www-form-urlencoded"
        ):
            raise HTTPException(415, "Preview handoff requires a form body")
        # Reject before and during body consumption; never buffer report bytes.
        content_length = request.headers.get("content-length")
        if content_length and (not content_length.isdigit() or int(content_length) > 4096):
            raise HTTPException(413, "Handoff body is too large")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 4096:
                raise HTTPException(413, "Handoff body is too large")
        try:
            form = parse_qs(raw.decode("ascii"), strict_parsing=True)
        except (UnicodeError, ValueError):
            raise HTTPException(400, "Invalid handoff form")
        if set(form) != {"token"} or len(form["token"]) != 1:
            raise HTTPException(400, "A single handoff token is required")
        token = form["token"][0]
        with _attributed_host_write(request, service) as (session, row, context):
            data, _, _, share, target = context
            _cookie_matches(request, data)
            if (
                data["status"] != "handoff_issued"
                or not hmac.compare_digest(_hash(token), data.get("handoff_sha256", ""))
                or datetime.fromisoformat(data["handoff_expires_at"]) <= datetime.now(timezone.utc)
            ):
                raise HTTPException(403, "Preview handoff is invalid, expired or already used")
            receipt = service.authorize_share_object(
                share, target, data["report_relative_key"], action="report"
            )
            service.backend.update_instance_json(
                session,
                row,
                {"status": "active", "handoff_sha256": "", "activated_at": utc_now_iso()},
            )
        report = (
            receipt["key"].rsplit("/", 1)[-1]
            if data["object_only"]
            else data["report_relative_key"][len(data["bundle_root"]) :]
        )
        return RedirectResponse(
            "/__dewey_preview/assets/" + quote(report, safe="/"),
            status_code=303,
            headers=_headers(settings),
        )

    @app.api_route(
        "/__dewey_preview/assets/{asset_path:path}",
        methods=["GET", "HEAD"],
        include_in_schema=False,
    )
    async def preview_asset(asset_path: str, request: Request):
        exact_relative_key(asset_path, allow_empty=False)

        def authorize_asset():
            with service.backend.session_scope(commit=False) as session:
                row, (data, binding, _, share, target) = _host_context(request, service, session)
                _cookie_matches(request, data)
                if data["status"] != "active":
                    raise HTTPException(401, "Preview handoff has not completed")
            relative = data["bundle_root"] + asset_path
            actor = binding_principal(binding, request.app.state.settings)
            with principal_context(actor), authenticated_user_email_context(actor.email):
                if data["object_only"]:
                    receipt = service.authorize_share_object(share, target, "", action="report")
                    if asset_path != receipt["key"].rsplit("/", 1)[-1]:
                        raise HTTPException(403, "Object-only report has no authorized bundle assets")
                else:
                    receipt = service.authorize_share_object(share, target, relative, action="report")
            return actor, receipt

        actor, receipt = await run_in_threadpool(authorize_asset)
        with principal_context(actor), authenticated_user_email_context(actor.email):
            reservation = await reserve_report_delivery(actor.subject)
            try:
                # Every conditional request retains live authorization. Only
                # unchanged body transfer is avoided by the provider's 304.
                headers = {**_headers(request.app.state.settings), "Cache-Control": "private, no-cache"}
                media = mimetypes.guess_type(receipt["key"])[0]
                if media:
                    headers["Content-Type"] = media
                return await run_in_threadpool(
                    object_delivery, request, service, receipt,
                    inline=True, extra_headers=headers, reservation=reservation,
                    preview=True,
                )
            except BaseException:
                reservation()
                raise
