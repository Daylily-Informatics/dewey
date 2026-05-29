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
