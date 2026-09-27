"""One request principal and SQL authorization contract for the Dewey registry.

Policies are typed TapDB objects attached by lineage. Policy subjects are verified
identity predicates, never client-supplied EUID relationships.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import DateTime, and_, cast, exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from dewey_service.dag_auth import dedicated_dag_actor, is_canonical_dag_get

POLICY_TEMPLATE = "access/registry_policy/generic/1.0/"
TOKEN_TEMPLATE = "access/api_client/generic/1.0/"
OPERATION_TEMPLATE = "operational/storage_operation/generic/1.0/"
REGISTRY_TYPES = {"artifact", "artifact_set"}


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str = ""
    roles: tuple[str, ...] = ()
    groups: tuple[str, ...] = ()
    internal: bool = False
    service: bool = False

    @property
    def admin(self) -> bool:
        return "ADMIN" in self.roles

    @property
    def writable(self) -> bool:
        return self.admin or "READ_WRITE" in self.roles


_PRINCIPAL: ContextVar[Principal | None] = ContextVar("dewey_registry_principal", default=None)
_MAINTENANCE: ContextVar[bool] = ContextVar("dewey_registry_maintenance", default=False)


def principal() -> Principal:
    actor = _PRINCIPAL.get()
    if actor is None:
        raise HTTPException(401, "A verified Dewey principal is required")
    return actor


@contextmanager
def principal_context(actor: Principal, *, maintenance: bool = False):
    token = _PRINCIPAL.set(actor)
    mode = _MAINTENANCE.set(maintenance)
    try:
        yield actor
    finally:
        _MAINTENANCE.reset(mode)
        _PRINCIPAL.reset(token)


def maintenance_mode() -> bool:
    return _MAINTENANCE.get()


def domain_suffixes(email: str) -> list[str]:
    domain = email.rpartition("@")[2].lower()
    parts = domain.split(".")
    return [".".join(parts[i:]) for i in range(max(0, len(parts) - 1))]


def audience_clause(data, actor: Principal):
    scope = data["scope"].astext
    choices = [scope == "authenticated"]
    if actor.internal:
        choices.append(scope == "internal")
    if actor.email:
        choices.append(data["users"].contains([actor.email]))
        choices.extend(data["domains"].contains([d]) for d in domain_suffixes(actor.email))
    choices.extend(data["groups"].contains([g]) for g in actor.groups)
    return or_(*choices)


def owner_clause(data, actor: Principal):
    choices = [data["owner_subject"].astext == actor.subject]
    if actor.email:
        choices.append(data["owner_email"].astext == actor.email)
    return or_(*choices)


def share_clause(data, actor: Principal, *, active_only: bool = True):
    allowed = owner_clause(data, actor)
    criteria = []
    if actor.email:
        criteria.append(data["allowed_users"].contains([actor.email]))
        criteria.extend(data["allowed_domains"].contains([d]) for d in domain_suffixes(actor.email))
    criteria.extend(data["allowed_groups"].contains([g]) for g in actor.groups)
    criteria.append(data["audience"].astext == "authenticated")
    if actor.internal:
        criteria.append(data["audience"].astext == "internal")
    recipients = or_(*criteria)
    if active_only:
        now = datetime.now(timezone.utc)
        recipients = and_(data["status"].astext == "active", cast(data["expires_at"].astext, DateTime(timezone=True)) > now, recipients)
    return or_(allowed, recipients)


def direct_record_clause(session, model, action: str = "metadata"):
    """Correlated SQL predicate; permission filtering precedes pagination/counts."""
    from daylily_tapdb import generic_instance, generic_instance_lineage

    actor = _PRINCIPAL.get()
    if maintenance_mode():
        return true()
    if actor is None:
        return false()
    if actor.admin:
        return true()
    if action in {"edit", "share"} and not actor.writable:
        return false()
    policy = aliased(generic_instance)
    edge = aliased(generic_instance_lineage)
    data = policy.json_addl
    allowed = owner_clause(data, actor)
    if action in {"metadata", "download"}:
        allowed = or_(allowed, audience_clause(data[action], actor))
        if action == "metadata" and actor.email:
            allowed = or_(allowed, data["edit_users"].contains([actor.email]), data["share_users"].contains([actor.email]))
    elif actor.email:
        allowed = or_(allowed, data[f"{action}_users"].contains([actor.email]))
    policy_grant = exists(select(literal(1)).select_from(edge).join(
        policy, policy.uid == edge.child_instance_uid
    ).where(
        edge.parent_instance_uid == model.uid,
        edge.relationship_type == "registry_policy",
        edge.is_deleted.is_(False), policy.is_deleted.is_(False),
        policy.type == "registry_policy", allowed,
    )).correlate(model)
    if action in {"metadata", "download"}:
        share = aliased(generic_instance)
        share_edge = aliased(generic_instance_lineage)
        now = datetime.now(timezone.utc)
        share_grant = exists(select(literal(1)).select_from(share_edge).join(
            share, share.uid == share_edge.child_instance_uid
        ).where(
            share_edge.parent_instance_uid == model.uid,
            share_edge.relationship_type == "has_share",
            share_edge.is_deleted.is_(False), share.is_deleted.is_(False),
            share.type == "share", share.json_addl["status"].astext == "active",
            cast(share.json_addl["expires_at"].astext, DateTime(timezone=True)) > now,
            share_clause(share.json_addl, actor),
        )).correlate(model)
        policy_grant = or_(policy_grant, share_grant)
    return and_(model.bstatus != "archived", policy_grant)


def record_clause(session, model, action: str = "metadata"):
    """A child cannot bypass a protected ancestor through another registration."""
    from daylily_tapdb import generic_instance, generic_instance_lineage
    actor = _PRINCIPAL.get()
    direct = direct_record_clause(session, model, action)
    if maintenance_mode() or (actor is not None and actor.admin):
        return direct
    if action in {"metadata", "download"} and actor is not None:
        grant_parent = aliased(generic_instance)
        own_policy = aliased(generic_instance)
        own_edge = aliased(generic_instance_lineage)
        explicitly_restricted = exists(select(literal(1)).select_from(own_edge).join(
            own_policy, own_policy.uid == own_edge.child_instance_uid).where(
            own_edge.parent_instance_uid == model.uid, own_edge.relationship_type == "registry_policy",
            own_edge.is_deleted.is_(False), own_policy.is_deleted.is_(False),
            own_policy.json_addl["explicit_restriction"].astext == "true",
        )).correlate(model)
        inherited = exists(select(literal(1)).select_from(grant_parent).where(
            grant_parent.uid != model.uid, grant_parent.type == "artifact", grant_parent.is_deleted.is_(False),
            grant_parent.domain_code == model.domain_code, grant_parent.issuer_app_code == model.issuer_app_code,
            grant_parent.json_addl["storage_kind"].astext == "prefix",
            grant_parent.json_addl["storage_backend"].astext == "s3", model.json_addl["storage_backend"].astext == "s3",
            grant_parent.json_addl["bucket"].astext == model.json_addl["bucket"].astext,
            func.left(model.json_addl["key"].astext, func.length(grant_parent.json_addl["key"].astext)) == grant_parent.json_addl["key"].astext,
            direct_record_clause(session, grant_parent, action),
        )).correlate(model)
        direct = or_(direct, and_(model.bstatus != "archived", ~explicitly_restricted, inherited))
    parent = aliased(generic_instance)
    policy = aliased(generic_instance)
    edge = aliased(generic_instance_lineage)
    restricted = exists(select(literal(1)).select_from(edge).join(policy, policy.uid == edge.child_instance_uid).where(
        edge.parent_instance_uid == parent.uid, edge.relationship_type == "registry_policy",
        edge.is_deleted.is_(False), policy.is_deleted.is_(False),
        policy.json_addl["explicit_restriction"].astext == "true",
    )).correlate(parent)
    ancestor_denied = exists(select(literal(1)).select_from(parent).where(
        parent.type == "artifact", parent.uid != model.uid,
        parent.domain_code == model.domain_code, parent.issuer_app_code == model.issuer_app_code,
        parent.is_deleted.is_(False),
        or_(parent.bstatus == "archived", restricted),
        parent.json_addl["storage_backend"].astext == "s3",
        model.json_addl["storage_backend"].astext == "s3",
        parent.json_addl["bucket"].astext == model.json_addl["bucket"].astext,
        or_(parent.json_addl["key"].astext == model.json_addl["key"].astext,
            and_(parent.json_addl["storage_kind"].astext == "prefix",
                func.left(model.json_addl["key"].astext, func.length(parent.json_addl["key"].astext)) == parent.json_addl["key"].astext)),
        ~direct_record_clause(session, parent, "download" if action == "download" else "metadata"),
    )).correlate(model)
    return and_(direct, ~ancestor_denied)


def visibility_clause(session, model, *, types=None):
    actor = _PRINCIPAL.get()
    if maintenance_mode() or (actor is not None and actor.admin):
        return true()
    if actor is None:
        return false()
    if types and set(types) <= REGISTRY_TYPES:
        return record_clause(session, model)
    if types and not set(types) & {*REGISTRY_TYPES, "share", "external_object", "external_object_relation"}:
        return true()
    from daylily_tapdb import generic_instance, generic_instance_lineage
    target = aliased(generic_instance)
    edge = aliased(generic_instance_lineage)
    can_manage_share = exists(select(literal(1)).select_from(edge).join(target,
        target.uid == edge.parent_instance_uid).where(edge.child_instance_uid == model.uid,
        edge.relationship_type == "has_share", edge.is_deleted.is_(False), target.is_deleted.is_(False),
        record_clause(session, target, "share"))).correlate(model)
    source = aliased(generic_instance)
    source_edge = aliased(generic_instance_lineage)
    external_edge = aliased(generic_instance_lineage)
    readable_relation = exists(select(literal(1)).select_from(source_edge).join(source,
        source.uid == source_edge.parent_instance_uid).where(
        source_edge.child_instance_uid == model.uid,
        source_edge.relationship_type == "has_external_relation",
        source_edge.is_deleted.is_(False), source.is_deleted.is_(False),
        source.type.in_(REGISTRY_TYPES), record_clause(session, source))).correlate(model)
    readable_external = exists(select(literal(1)).select_from(external_edge).join(source_edge,
        source_edge.child_instance_uid == external_edge.child_instance_uid).join(source,
        source.uid == source_edge.parent_instance_uid).where(
        external_edge.parent_instance_uid == model.uid,
        external_edge.relationship_type == "is_external_relation_for",
        source_edge.relationship_type == "has_external_relation",
        external_edge.is_deleted.is_(False), source_edge.is_deleted.is_(False),
        source.is_deleted.is_(False), source.type.in_(REGISTRY_TYPES),
        record_clause(session, source))).correlate(model)
    any_external_link = exists(select(literal(1)).select_from(external_edge).where(
        external_edge.parent_instance_uid == model.uid,
        external_edge.relationship_type == "is_external_relation_for",
        external_edge.is_deleted.is_(False))).correlate(model)
    return or_(
        and_(model.type.in_(REGISTRY_TYPES), record_clause(session, model)),
        and_(model.type == "share", or_(share_clause(model.json_addl, actor), can_manage_share)),
        and_(model.type == "external_object_relation", readable_relation),
        and_(model.type == "external_object", or_(readable_external, and_(~any_external_link, literal(actor.internal)))),
        ~model.type.in_([*REGISTRY_TYPES, "share", "external_object", "external_object_relation"]),
    )


def require_record(backend, session, record, action: str):
    from daylily_tapdb import generic_instance
    if record.bstatus == "archived" and not maintenance_mode():
        raise HTTPException(410, "This Dewey registration is archived")
    allowed = session.query(generic_instance.uid).filter(
        generic_instance.uid == record.uid,
        record_clause(session, generic_instance, action),
    ).first()
    if not allowed:
        raise HTTPException(403, f"Dewey {action} permission is required")


def default_policy(actor: Principal) -> dict[str, Any]:
    audience = {"scope": "internal", "users": [], "domains": [], "groups": []}
    return {
        "owner_subject": actor.subject, "owner_email": actor.email,
        "metadata": dict(audience), "download": dict(audience),
        "edit_users": [], "share_users": [], "explicit_restriction": False,
    }


def validate_policy(value: dict[str, Any]) -> dict[str, Any]:
    unknown = set(value) - {"metadata", "download", "edit_users", "share_users"}
    if unknown:
        raise ValueError("Unsupported policy fields: " + ", ".join(sorted(unknown)))
    out: dict[str, Any] = {}
    for field, rule in value.items():
        if field in {"edit_users", "share_users"}:
            if not isinstance(rule, list) or any(not isinstance(v, str) or "@" not in v for v in rule):
                raise ValueError(f"{field} must contain email addresses")
            out[field] = sorted({v.strip().lower() for v in rule})
            continue
        if not isinstance(rule, dict) or set(rule) - {"scope", "users", "domains", "groups"}:
            raise ValueError(f"Invalid {field} audience")
        if rule.get("scope") not in {"private", "internal", "recipients", "authenticated"}:
            raise ValueError(f"{field}.scope is required")
        normalized = {"scope": rule["scope"]}
        for key in ("users", "domains", "groups"):
            items = rule.get(key, [])
            if not isinstance(items, list) or any(not isinstance(v, str) or not v.strip() for v in items):
                raise ValueError(f"{field}.{key} must be a list of nonempty strings")
            normalized[key] = sorted({v.strip().lower() if key != "groups" else v.strip() for v in items})
        if any("@" not in v for v in normalized["users"]):
            raise ValueError("Audience users must be email addresses")
        if any("." not in v or any(c in v for c in "/*@ ") for v in normalized["domains"]):
            raise ValueError("Audience domains must be explicit DNS suffixes")
        if normalized["scope"] == "private" and any(normalized[key] for key in ("users", "domains", "groups")):
            raise ValueError("A private audience cannot include additional recipients")
        out[field] = normalized
    return out


class RegistryPrincipalMiddleware(BaseHTTPMiddleware):
    """Runs inside SessionMiddleware, before route dependencies and worker threads."""
    async def dispatch(self, request: Request, call_next):
        from dewey_service.auth import _load_ui_profile
        settings = request.app.state.settings
        actor = None
        try:
            profile = _load_ui_profile(request)
            if profile:
                email = profile["email"].lower()
                actor = Principal(
                    subject=profile["sub"], email=email,
                    roles=tuple(profile["roles"]), groups=tuple(profile["groups"]),
                    internal=("lsmc:internal-user" in profile["groups"] or
                              email.rpartition("@")[2] in settings.registry_internal_domains),
                )
            authorization = request.headers.get("authorization", "")
            if actor is None and authorization.startswith("Bearer "):
                token = authorization[7:].strip()
                if token in settings.api_tokens():
                    identity = settings.registry_service_principals.get(sha256(token.encode()).hexdigest())
                    if not identity or not identity.get("subject"):
                        return JSONResponse({"detail": "Service credential has no configured registry identity"}, status_code=503)
                    actor = Principal(subject=identity["subject"], roles=tuple(identity["roles"]), internal=True, service=True)
                elif token.startswith("dewey_user_"):
                    from starlette.concurrency import run_in_threadpool
                    actor = await run_in_threadpool(request.app.state.service.authenticate_registry_token, token)
            path = request.url.path
            dag_reader = None
            if is_canonical_dag_get(request):
                scheme, token = get_authorization_scheme_param(authorization)
                if scheme.lower() == "bearer":
                    dag_reader = dedicated_dag_actor(request, settings, token)
            admin_path = path.startswith(("/tapdb", "/api/dag", "/admin", "/ui/anomalies", "/ui/observability")) or path == "/graph"
            if path.startswith("/tapdb/change-password"):
                return JSONResponse({"detail": "Credentials are managed by shared LSMC login"}, status_code=410)
            if admin_path and dag_reader is None and (actor is None or not actor.admin):
                if actor is None and not path.startswith("/api/"):
                    return RedirectResponse("/login", status_code=303)
                return JSONResponse({"detail": "Dewey admin access required"}, status_code=403)
            # Token and cookie are never forwarded to another host or logged.
            context = _PRINCIPAL.set(actor)
            request.state.registry_principal = actor
            from dewey_service.audit import authenticated_user_email_context
            try:
                with authenticated_user_email_context(actor.email if actor else None):
                    return await call_next(request)
            finally:
                _PRINCIPAL.reset(context)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
