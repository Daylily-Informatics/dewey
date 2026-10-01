"""Request-scoped audit principal helpers for Dewey TapDB writes."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_CURRENT_AUTHENTICATED_USER_EMAIL: ContextVar[str | None] = ContextVar(
    "dewey_authenticated_user_email",
    default=None,
)


def normalize_authenticated_user_email(email: object) -> str | None:
    cleaned = str(email or "").strip().lower()
    return cleaned or None


def current_authenticated_user_email() -> str | None:
    return _CURRENT_AUTHENTICATED_USER_EMAIL.get()


def set_current_authenticated_user_email(email: object) -> Token[str | None]:
    return _CURRENT_AUTHENTICATED_USER_EMAIL.set(normalize_authenticated_user_email(email))


def reset_current_authenticated_user_email(token: Token[str | None]) -> None:
    _CURRENT_AUTHENTICATED_USER_EMAIL.reset(token)


@contextmanager
def authenticated_user_email_context(email: object) -> Iterator[str | None]:
    token = set_current_authenticated_user_email(email)
    try:
        yield current_authenticated_user_email()
    finally:
        reset_current_authenticated_user_email(token)


def creation_audit_fields() -> dict[str, str]:
    email = current_authenticated_user_email()
    if not email:
        return {}
    return {"created_by_email": email, "updated_by_email": email}


def update_audit_fields() -> dict[str, str]:
    email = current_authenticated_user_email()
    if not email:
        return {}
    return {"updated_by_email": email}


def human_issuer(settings) -> str:
    """The configured verifier owns the subject namespace; email is display only."""
    if settings.auth_mode == "external_broker":
        issuer = settings.external_broker_handoff_exchange_url
    elif settings.auth_mode == "cognito":
        if not settings.cognito_user_pool_id or not settings.cognito_region:
            raise ValueError("Cognito attribution requires its configured region and user pool")
        issuer = f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    else:
        raise ValueError("Human attribution requires an explicit supported identity verifier")
    if not issuer:
        raise ValueError("Human attribution issuer is not configured")
    return issuer


_EXPLICIT_ATTRIBUTION = ContextVar("dewey_explicit_attribution", default=None)


_REQUEST_ID: ContextVar[str | None] = ContextVar("dewey_audit_request_id", default=None)


@contextmanager
def request_audit_context():
    from uuid import uuid4
    token = _REQUEST_ID.set(str(uuid4()))
    try:
        yield
    finally:
        _REQUEST_ID.reset(token)


@contextmanager
def explicit_attribution_context(path):
    import json
    from daylily_tapdb.security_context import Attribution, set_invocation_attribution, reset_invocation_attribution
    envelope = Attribution(**json.loads(path.read_text()))
    local_token = _EXPLICIT_ATTRIBUTION.set(envelope)
    token = set_invocation_attribution(envelope)
    try:
        yield envelope
    finally:
        reset_invocation_attribution(token)
        _EXPLICIT_ATTRIBUTION.reset(local_token)


def transaction_attribution(settings, operation: str, *, commit: bool):
    from uuid import uuid4
    from dataclasses import replace
    from daylily_tapdb.security_context import Attribution
    from dewey_service.registry_access import current_principal

    explicit = _EXPLICIT_ATTRIBUTION.get()
    if explicit is not None:
        return replace(explicit, operation_id=f"{operation}:{uuid4()}")
    actor = current_principal()
    invocation = _REQUEST_ID.get() or str(uuid4())
    if actor is None:
        if commit:
            raise ValueError("Dewey writes require a verified actor or explicit attribution envelope")
        return None
    else:
        kind = "service" if actor.service else "human"
        issuer = "dewey" if actor.service else human_issuer(settings)
        subject = actor.subject
    return Attribution(actor_kind=kind, actor_issuer=issuer, actor_subject=subject,
        service_identity="dewey", request_id=invocation,
        operation_id=f"{operation}:{uuid4()}")


@contextmanager
def qeo_dispatch_attribution_context():
    """The unattended outbox dispatch entrypoint explicitly acts as Dewey."""
    from uuid import uuid4
    from daylily_tapdb.security_context import Attribution
    envelope = Attribution(actor_kind="service", actor_issuer="dewey",
        actor_subject="dewey:qeo-dispatch", service_identity="dewey",
        request_id=str(uuid4()), operation_id=str(uuid4()))
    token = _EXPLICIT_ATTRIBUTION.set(envelope)
    try:
        yield envelope
    finally:
        _EXPLICIT_ATTRIBUTION.reset(token)
