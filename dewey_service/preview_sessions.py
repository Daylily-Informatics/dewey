"""Native typed, revocable browser session bindings for report contexts."""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from daylily_tapdb import generic_instance
from daylily_auth_cognito.browser.session import load_session_principal, store_session_principal
from dewey_service.registry_access import OPERATION_TEMPLATE, Principal, principal_context
from dewey_service.audit import authenticated_user_email_context
from dewey_service.rbac import normalize_session_profile
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso


def operation_row(service, session, euid, *, lock=False):
    template = service.backend.templates.get_template(session, OPERATION_TEMPLATE, domain_code=service.backend.domain_code)
    if template is None:
        raise RuntimeError("Missing native storage_operation template")
    query = session.query(generic_instance).filter(generic_instance.template_uid == template.uid,
        generic_instance.euid == euid, generic_instance.is_deleted.is_(False))
    if lock:
        query = query.with_for_update()
    row = query.first()
    if row is None:
        raise HTTPException(401, "Session context unavailable; sign in again")
    return row


def require_preview_configuration(settings):
    names = ("share_application_origin", "share_content_host_suffix", "share_session_generation")
    if any(not getattr(settings, name) for name in names):
        raise HTTPException(503, "Isolated report session configuration is incomplete")
    from urllib.parse import urlsplit
    apphost = urlsplit(settings.share_application_origin).hostname
    if apphost == settings.share_content_host_suffix or apphost.endswith("." + settings.share_content_host_suffix):
        raise HTTPException(503, "Report content must have a distinct origin subtree")


def establish_session_binding(request, config, *, previous_user=None):
    """Called only after a successful verified browser callback."""
    settings = request.app.state.settings
    if not settings.share_session_generation:
        raise HTTPException(503, "Browser session generation is not configured")
    user = load_session_principal(request)
    if user is None:
        raise HTTPException(401, "Verified callback did not establish a session")
    service = request.app.state.service
    expires = datetime.now(timezone.utc) + timedelta(seconds=config.session_max_age)
    actor = Principal(subject=user.user_sub, email=user.email, roles=tuple(user.roles),
        groups=tuple(user.cognito_groups), internal=("lsmc:internal-user" in user.cognito_groups
            or user.email.rpartition("@")[2] in settings.registry_internal_domains))
    if previous_user is not None:
        revoke_session_binding(request, user=previous_user)
    with principal_context(actor), authenticated_user_email_context(actor.email), service.backend.session_scope(commit=True) as session:
        row = service.backend.create_instance(session, template_code=OPERATION_TEMPLATE, name="Browser session binding",
            json_addl={"operation": "browser_session_binding", "status": "active", "actor": user.user_sub,
                "principal": asdict(actor), "generation": settings.share_session_generation,
                "created_at": utc_now_iso(), "expires_at": expires.isoformat()})
        binding_euid = row.euid
    store_session_principal(request, config, replace(user,
        app_context={**user.app_context, "dewey_session_binding_euid": binding_euid}))


def revoke_session_binding(request, *, user=None):
    user = user if user is not None else load_session_principal(request)
    binding = user.app_context.get("dewey_session_binding_euid") if user else None
    if not binding:
        return
    service = request.app.state.service
    actor = Principal(subject=user.user_sub, email=user.email, roles=tuple(user.roles), groups=tuple(user.cognito_groups))
    with principal_context(actor), authenticated_user_email_context(actor.email), service.backend.session_scope(commit=True) as session:
        row = operation_row(service, session, binding, lock=True)
        data = normalize_instance_payload(row)
        if data.get("operation") != "browser_session_binding" or data.get("actor") != user.user_sub:
            raise HTTPException(401, "Session binding is invalid")
        if data.get("status") == "active":
            service.backend.update_instance_json(session, row, {"status": "revoked", "revoked_at": utc_now_iso()})


def live_session_binding(service, settings, session, euid):
    data = normalize_instance_payload(operation_row(service, session, euid))
    if (data.get("operation") != "browser_session_binding" or data.get("status") != "active"
            or not settings.share_session_generation or data.get("generation") != settings.share_session_generation
            or datetime.fromisoformat(data["expires_at"]) <= datetime.now(timezone.utc)):
        raise HTTPException(401, "Report session ended; sign in again")
    return data


def current_session_binding(request, service):
    user = load_session_principal(request)
    euid = user.app_context.get("dewey_session_binding_euid") if user else None
    if not euid:
        raise HTTPException(401, "Report preview requires a new browser sign-in")
    with service.backend.session_scope(commit=False) as session:
        binding = live_session_binding(service, request.app.state.settings, session, euid)
    if binding.get("actor") != user.user_sub or binding["principal"]["email"] != user.email:
        raise HTTPException(401, "Report session identity mismatch")
    return euid


def binding_principal(binding, settings):
    identity = binding["principal"]
    profile = normalize_session_profile(email=identity["email"], sub=identity["subject"],
        groups=identity["groups"], group_role_map=settings.cognito_group_role_map)
    if not profile["roles"]:
        raise HTTPException(403, "Current report session has no Dewey role")
    return Principal(subject=profile["sub"], email=profile["email"], roles=tuple(profile["roles"]),
        groups=tuple(profile["groups"]), internal=("lsmc:internal-user" in profile["groups"]
            or profile["email"].rpartition("@")[2] in settings.registry_internal_domains))
