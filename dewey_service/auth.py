"""Authentication helpers for Dewey API and browser UI."""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any
from urllib.parse import urlencode, urlsplit

from daylily_auth_cognito.browser.oauth import build_authorization_url
from daylily_auth_cognito.browser import session as browser_session
from daylily_auth_cognito.browser.session import (
    CognitoWebAuthError,
    CognitoWebSessionConfig,
    SessionPrincipal,
    clear_session_principal,
    complete_cognito_callback,
    configure_session_middleware as _configure_session_middleware,
    load_session_principal,
    start_cognito_login,
    validate_web_auth_contract,
)
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dewey_service.rbac import Role, normalize_session_profile, profile_has_role
from dewey_service.settings import Settings

configure_session_middleware = _configure_session_middleware


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


def _strip_scheme(value: str) -> str:
    cleaned = str(value or "").strip().rstrip("/")
    if cleaned.startswith("https://"):
        return cleaned[len("https://") :]
    if cleaned.startswith("http://"):
        return cleaned[len("http://") :]
    return cleaned


def _origin(value: str) -> str:
    parsed = urlsplit(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("cognito_redirect_uri must be an absolute http(s) URL")
    return f"{parsed.scheme}://{parsed.netloc}"


def _require_allowed_cognito_email_domain(settings: Settings, email: str) -> None:
    valid, message = settings.validate_cognito_email_domain(email)
    if not valid:
        raise CognitoWebAuthError(
            "not_authorized",
            message or "This account is not provisioned for Dewey access.",
            status_code=status.HTTP_403_FORBIDDEN,
            redirect_to_error=True,
        )


def build_cognito_web_session_config(
    *,
    settings: Settings,
    server_instance_id: str | None = None,
) -> CognitoWebSessionConfig:
    config = CognitoWebSessionConfig(
        domain=_strip_scheme(settings.cognito_domain),
        client_id=settings.cognito_app_client_id,
        redirect_uri=settings.cognito_redirect_uri,
        logout_uri=settings.cognito_logout_url,
        session_secret_key=settings.session_secret_key,
        session_cookie_name="dewey_session",
        public_base_url=_origin(settings.cognito_redirect_uri),
        client_secret=settings.cognito_app_client_secret or None,
        allow_insecure_http=_origin(settings.cognito_redirect_uri).startswith("http://"),
        server_instance_id=server_instance_id or secrets.token_urlsafe(16),
    )
    validate_web_auth_contract(config, config.public_base_url)
    return config


def build_cognito_login_url(*, settings: Settings, state: str) -> str:
    domain = _strip_scheme(settings.cognito_domain)
    return build_authorization_url(
        domain=domain,
        client_id=settings.cognito_app_client_id,
        redirect_uri=settings.cognito_redirect_uri,
        state=state,
    )


def build_cognito_logout_url(*, settings: Settings, state: str | None = None) -> str:
    import urllib.parse

    domain = _strip_scheme(settings.cognito_domain)
    logout_target = settings.cognito_redirect_uri
    query: dict[str, str] = {
        "client_id": settings.cognito_app_client_id,
        "redirect_uri": logout_target.rstrip("/"),
        "response_type": "code",
    }
    if state:
        query["state"] = state
    params = urllib.parse.urlencode(query)
    return f"https://{domain}/logout?{params}"


async def exchange_code(*, settings: Settings, code: str) -> dict[str, Any]:
    domain = _strip_scheme(settings.cognito_domain)
    try:
        return await browser_session.exchange_authorization_code_async(
            domain=domain,
            client_id=settings.cognito_app_client_id,
            code=code,
            redirect_uri=settings.cognito_redirect_uri,
            client_secret=settings.cognito_app_client_secret or None,
        )
    except RuntimeError as exc:
        raise AuthError(str(exc)) from exc


def build_browser_login_href(*, next_path: str | None = None) -> str:
    href = "/auth/login"
    cleaned = str(next_path or "").strip()
    if cleaned:
        href = f"{href}?{urlencode({'next': cleaned})}"
    return href


def start_browser_login(
    request: Request,
    config: CognitoWebSessionConfig,
    next_path: str | None = None,
):
    return start_cognito_login(request, config, next_path)


async def complete_browser_login(
    request: Request,
    config: CognitoWebSessionConfig,
    *,
    code: str | None,
    state: str | None,
) -> RedirectResponse:
    try:
        response = await complete_cognito_callback(
            request,
            config,
            code,
            state,
            resolve_operator_principal,
        )
    except CognitoWebAuthError as exc:
        clear_ui_session(request)
        return RedirectResponse(
            url=f"/auth/error?reason={exc.reason}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return response


def clear_ui_session(request: Request) -> None:
    clear_session_principal(request)
    config = getattr(getattr(request.app, "state", None), "web_session_config", None)
    if config is not None:
        request.session.pop(config.state_session_key, None)
        request.session.pop(config.next_path_session_key, None)


def resolve_operator_principal(
    tokens: dict[str, Any],
    request: Request,
) -> SessionPrincipal:
    id_token = str(tokens.get("id_token") or "").strip()
    claims = decode_jwt_claims_noverify(id_token)
    email = str(claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    sub = str(claims.get("sub") or "").strip()
    name = str(claims.get("name") or claims.get("given_name") or "").strip() or None
    if not email or not sub:
        raise CognitoWebAuthError(
            "auth_error",
            "Cognito response missing required claims",
            status_code=401,
        )

    groups = claims.get("cognito:groups") or []
    if not isinstance(groups, list):
        groups = []

    settings: Settings = request.app.state.settings
    _require_allowed_cognito_email_domain(settings, email)
    profile = normalize_session_profile(
        email=email,
        sub=sub,
        groups=groups,
        group_role_map=settings.cognito_group_role_map,
    )
    return SessionPrincipal(
        user_sub=profile["sub"],
        email=profile["email"],
        name=name,
        roles=list(profile["roles"]),
        cognito_groups=list(profile["groups"]),
        auth_mode="cognito",
        app_context={},
    )


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


def _load_ui_profile(request: Request) -> dict[str, Any] | None:
    principal = load_session_principal(request)
    if principal is not None:
        settings: Settings = request.app.state.settings
        request.state.auth_mode = principal.auth_mode
        return normalize_session_profile(
            email=principal.email,
            sub=principal.user_sub,
            groups=principal.cognito_groups,
            group_role_map=settings.cognito_group_role_map,
        )

    return None


def require_ui_session(request: Request) -> dict[str, Any]:
    profile = _load_ui_profile(request)
    if profile is None:
        store = getattr(request.app.state, "observability", None)
        if store is not None:
            store.record_auth_event(
                status="denied",
                mode="anonymous",
                detail="ui_session",
                service_principal=False,
            )
        detail = (
            "Session expired"
            if getattr(request.state, "cognito_auth_reason", None) == "session_expired"
            else "Login required"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    store = getattr(request.app.state, "observability", None)
    if store is not None:
        store.record_auth_event(
            status="ok",
            mode="cognito",
            detail="ui_session",
            service_principal=False,
        )
    request.state.auth_mode = "cognito"
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
        profile = _load_ui_profile(request)
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


def require_session_or_api_auth(settings: Settings):
    bearer = HTTPBearer(auto_error=False)

    def _require_session_or_api_auth(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> dict[str, Any]:
        profile = _load_ui_profile(request)
        if isinstance(profile, dict):
            store = getattr(request.app.state, "observability", None)
            if store is not None:
                store.record_auth_event(
                    status="ok",
                    mode="cognito",
                    detail="session_or_bearer",
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
                        detail="session_or_bearer",
                        service_principal=True,
                    )
                request.state.auth_mode = "service_token"
                return {"auth_mode": "service_token", "service_principal": True}

        store = getattr(request.app.state, "observability", None)
        if store is not None:
            store.record_auth_event(
                status="denied",
                mode="anonymous",
                detail="session_or_bearer",
                service_principal=False,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login or bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _require_session_or_api_auth
