"""Authentication helpers for Dewey API and browser UI."""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any

from daylily_cognito import build_authorization_url, exchange_authorization_code
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dewey_service.rbac import Role, normalize_session_profile, profile_has_role
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
    return build_authorization_url(
        domain=domain,
        client_id=settings.cognito_app_client_id,
        redirect_uri=settings.cognito_redirect_uri,
        state=state,
    )


def build_cognito_logout_url(*, settings: Settings, state: str | None = None) -> str:
    import urllib.parse
    domain = str(settings.cognito_domain or "").strip().rstrip("/")
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
    logout_target = settings.cognito_logout_url
    query: dict[str, str] = {
        "client_id": settings.cognito_app_client_id,
        "redirect_uri": logout_target.rstrip("/"),
        "response_type": "code",
    }
    if state:
        query["state"] = state
    params = urllib.parse.urlencode(query)
    return f"https://{domain}/logout?{params}"


def exchange_code(*, settings: Settings, code: str) -> dict[str, Any]:
    domain = str(settings.cognito_domain or "").strip().rstrip("/")
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
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
        store = getattr(request.app.state, "observability", None)
        if store is not None:
            store.record_auth_event(
                status="denied",
                mode="anonymous",
                detail="ui_session",
                service_principal=False,
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    store = getattr(request.app.state, "observability", None)
    if store is not None:
        store.record_auth_event(
            status="ok",
            mode="cognito",
            detail="ui_session",
            service_principal=False,
        )
    request.state.auth_mode = "cognito"
    if "roles" not in profile:
        return normalize_session_profile(
            email=profile.get("email"),
            sub=profile.get("sub"),
            groups=profile.get("groups"),
        )
    return profile


def require_ui_admin_session(request: Request) -> dict[str, Any]:
    profile = require_ui_session(request)
    if not profile_has_role(profile, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return profile


def build_session_profile(
    *,
    settings: Settings,
    email: str,
    sub: str,
    groups: list[str] | tuple[str, ...] | None,
) -> dict[str, Any]:
    return normalize_session_profile(
        email=email,
        sub=sub,
        groups=groups,
        group_role_map=settings.cognito_group_role_map,
    )


def require_observability_access(settings: Settings):
    bearer = HTTPBearer(auto_error=False)

    def _require_observability_access(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> dict[str, Any]:
        profile = request.session.get("operator_profile")
        if isinstance(profile, dict):
            store = getattr(request.app.state, "observability", None)
            if store is not None:
                store.record_auth_event(
                    status="ok",
                    mode="cognito",
                    detail="session",
                    service_principal=False,
                )
            request.state.auth_mode = "cognito"
            return {"auth_mode": "cognito", "service_principal": False, "profile": profile}

        if credentials is not None:
            token = str(credentials.credentials or "").strip()
            if token in settings.api_tokens():
                store = getattr(request.app.state, "observability", None)
                if store is not None:
                    store.record_auth_event(
                        status="ok",
                        mode="service_token",
                        detail="bearer",
                        service_principal=True,
                    )
                request.state.auth_mode = "service_token"
                return {"auth_mode": "service_token", "service_principal": True}

        store = getattr(request.app.state, "observability", None)
        if store is not None:
            store.record_auth_event(
                status="denied",
                mode="anonymous",
                detail="observability",
                service_principal=False,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _require_observability_access
