"""Authentication helpers for Dewey API and operator UI."""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any

from daylily_cognito import build_authorization_url, exchange_authorization_code
from daylily_cognito import build_logout_url as daycog_build_logout_url
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dewey_service.settings import Settings


class AuthError(RuntimeError):
    """Raised when authentication flow fails."""


def decode_jwt_claims_noverify(token: str) -> dict[str, Any]:
    if not token or "." not in token:
        return {}
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        payload += "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8")
        parsed = json.loads(decoded)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def generate_state() -> str:
    return secrets.token_urlsafe(24)


def build_cognito_login_url(*, settings: Settings, state: str) -> str:
    domain = str(settings.cognito_domain or "").strip().rstrip("/")
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
    if domain.startswith("http://"):
        domain = domain[len("http://") :]
    return build_authorization_url(
        domain=domain,
        client_id=settings.cognito_app_client_id,
        redirect_uri=settings.cognito_redirect_uri,
        state=state,
    )


def build_cognito_logout_url(*, settings: Settings) -> str:
    domain = str(settings.cognito_domain or "").strip().rstrip("/")
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
    if domain.startswith("http://"):
        domain = domain[len("http://") :]
    target = settings.cognito_logout_url or settings.cognito_redirect_uri.replace(
        "/auth/callback", ""
    )
    return daycog_build_logout_url(
        domain=domain,
        client_id=settings.cognito_app_client_id,
        logout_uri=target,
    )


def exchange_code(*, settings: Settings, code: str) -> dict[str, Any]:
    domain = str(settings.cognito_domain or "").strip().rstrip("/")
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
    if domain.startswith("http://"):
        domain = domain[len("http://") :]
    try:
        return exchange_authorization_code(
            domain=domain,
            client_id=settings.cognito_app_client_id,
            code=code,
            redirect_uri=settings.cognito_redirect_uri,
            client_secret=settings.cognito_app_client_secret or None,
        )
    except RuntimeError as exc:
        raise AuthError(str(exc)) from exc


def require_api_auth(settings: Settings):
    bearer = HTTPBearer(auto_error=False)

    def _require_api_auth(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> str:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = str(credentials.credentials or "").strip()
        if token not in settings.api_tokens():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

    return _require_api_auth


def require_ui_session(request: Request) -> dict[str, Any]:
    profile = request.session.get("operator_profile")
    if not isinstance(profile, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return profile
