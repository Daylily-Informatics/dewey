"""Authentication helpers for Dewey API and browser UI."""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
from daylily_auth_cognito.browser import session as browser_session
from daylily_auth_cognito.browser.oauth import build_authorization_url
from daylily_auth_cognito.browser.session import (
    CognitoWebAuthError,
    CognitoWebSessionConfig,
    SessionPrincipal,
    clear_session_principal,
    complete_cognito_callback,
    load_session_principal,
    start_cognito_login,
    store_session_principal,
    validate_web_auth_contract,
)
from daylily_auth_cognito.browser.session import (
    configure_session_middleware as _configure_session_middleware,
)
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dewey_service.rbac import Role, normalize_session_profile, profile_has_role
from dewey_service.settings import Settings

configure_session_middleware = _configure_session_middleware

_EXTERNAL_BROKER_STATE_KEY = "dewey_external_broker_state"
_EXTERNAL_BROKER_NEXT_KEY = "dewey_external_broker_next"


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


def _bare_host(value: str) -> str:
    cleaned = str(value or "").strip().rstrip("/")
    if not cleaned:
        raise ValueError("cognito_domain must be a bare host, not a URL")
    parsed = urlsplit(cleaned)
    if parsed.scheme or parsed.netloc or any(char in cleaned for char in "/?#"):
        raise ValueError("cognito_domain must be a bare host, not a URL")
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
        domain=_bare_host(settings.cognito_domain),
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


def build_web_session_config(
    *,
    settings: Settings,
    server_instance_id: str | None = None,
) -> CognitoWebSessionConfig:
    if settings.auth_mode != "external_broker":
        return build_cognito_web_session_config(
            settings=settings,
            server_instance_id=server_instance_id,
        )

    public_base_url = _origin(settings.external_broker_callback_url)
    return CognitoWebSessionConfig(
        domain=urlsplit(settings.external_broker_login_url).netloc,
        client_id=settings.external_broker_service_id,
        redirect_uri=settings.external_broker_callback_url,
        logout_uri=public_base_url,
        session_secret_key=settings.session_secret_key,
        session_cookie_name="dewey_session",
        public_base_url=public_base_url,
        allow_insecure_http=public_base_url.startswith("http://"),
        server_instance_id=server_instance_id or secrets.token_urlsafe(16),
        auth_mode="external_broker",
    )


def build_cognito_login_url(*, settings: Settings, state: str) -> str:
    domain = _bare_host(settings.cognito_domain)
    return build_authorization_url(
        domain=domain,
        client_id=settings.cognito_app_client_id,
        redirect_uri=settings.cognito_redirect_uri,
        state=state,
    )


def build_cognito_logout_url(*, settings: Settings, state: str | None = None) -> str:
    import urllib.parse

    domain = _bare_host(settings.cognito_domain)
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
    domain = _bare_host(settings.cognito_domain)
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
    settings: Settings = request.app.state.settings
    if settings.auth_mode == "external_broker":
        return start_external_broker_login(request, settings=settings, next_path=next_path)
    return start_cognito_login(request, config, next_path)


def _safe_next_path(value: str | None) -> str:
    cleaned = str(value or "").strip()
    return cleaned if cleaned.startswith("/") else "/ui"


def start_external_broker_login(
    request: Request,
    *,
    settings: Settings,
    next_path: str | None = None,
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    target = _safe_next_path(next_path or "/ui")
    request.session[_EXTERNAL_BROKER_STATE_KEY] = state
    request.session[_EXTERNAL_BROKER_NEXT_KEY] = target
    query = urlencode(
        {
            "service": settings.external_broker_service_id,
            "next": target,
            "callback_url": settings.external_broker_callback_url,
            "state": state,
        }
    )
    return RedirectResponse(
        url=f"{settings.external_broker_login_url.rstrip('/')}?{query}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


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


async def exchange_external_broker_handoff(*, settings: Settings, code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.external_broker_handoff_exchange_url, json={"code": code})
    if response.status_code >= 400:
        raise CognitoWebAuthError(
            "auth_error",
            f"External broker handoff exchange failed with status {response.status_code}",
            status_code=status.HTTP_401_UNAUTHORIZED,
            redirect_to_error=True,
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise CognitoWebAuthError(
            "auth_error",
            "External broker handoff response must be an object",
            status_code=status.HTTP_401_UNAUTHORIZED,
            redirect_to_error=True,
        )
    return payload


def _service_entitlement_roles(user: dict[str, Any], *, service_id: str) -> list[str]:
    entitlements = user.get("service_entitlements") or []
    out: list[str] = []
    if isinstance(entitlements, dict):
        entitlement = entitlements.get(service_id)
        entitlements = [entitlement] if isinstance(entitlement, dict) else []
    for entitlement in entitlements:
        if not isinstance(entitlement, dict):
            continue
        if str(entitlement.get("service") or service_id).strip() != service_id:
            continue
        for role in entitlement.get("roles") or []:
            normalized = str(role or "").strip().lower().replace("-", "_")
            if normalized in {"admin", "administrator"}:
                out.append("dewey-admin")
            elif normalized in {"read_write", "readwrite", "write", "operator", "internal_user"}:
                out.append("dewey-readwrite")
            elif normalized in {"read_only", "readonly", "read", "viewer", "auditor"}:
                out.append("dewey-readonly")
    return out


def resolve_external_broker_principal(user: dict[str, Any], request: Request) -> SessionPrincipal:
    settings: Settings = request.app.state.settings
    email = str(user.get("email") or "").strip().lower()
    subject = str(
        user.get("canonical_user_id") or user.get("sub") or user.get("user_id") or email
    ).strip()
    name = str(user.get("display_name") or user.get("name") or "").strip() or None
    if not email or not subject:
        raise CognitoWebAuthError(
            "auth_error",
            "External broker handoff missing required user identity",
            status_code=status.HTTP_401_UNAUTHORIZED,
            redirect_to_error=True,
        )
    _require_allowed_cognito_email_domain(settings, email)
    groups = [str(item).strip() for item in user.get("groups") or [] if str(item).strip()]
    groups.extend(
        _service_entitlement_roles(user, service_id=settings.external_broker_service_id)
    )
    profile = normalize_session_profile(
        email=email,
        sub=subject,
        groups=list(dict.fromkeys(groups)),
        group_role_map=settings.cognito_group_role_map,
    )
    if not profile["roles"]:
        raise CognitoWebAuthError(
            "not_authorized",
            "External broker user has no Dewey roles",
            status_code=status.HTTP_403_FORBIDDEN,
            redirect_to_error=True,
        )
    return SessionPrincipal(
        user_sub=profile["sub"],
        email=profile["email"],
        name=name,
        roles=list(profile["roles"]),
        cognito_groups=list(profile["groups"]),
        auth_mode="external_broker",
        app_context={"canonical_user": dict(user)},
    )


async def complete_external_broker_login(
    request: Request,
    config: CognitoWebSessionConfig,
    *,
    code: str | None,
    state: str | None,
) -> RedirectResponse:
    if not code:
        return RedirectResponse(
            url="/auth/error?reason=missing_code",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    expected_state = str(request.session.get(_EXTERNAL_BROKER_STATE_KEY) or "")
    if not expected_state or state != expected_state:
        clear_ui_session(request)
        return RedirectResponse(
            url="/auth/error?reason=invalid_state",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    settings: Settings = request.app.state.settings
    try:
        payload = await exchange_external_broker_handoff(settings=settings, code=code)
        user = payload.get("user")
        if not isinstance(user, dict):
            raise CognitoWebAuthError(
                "auth_error",
                "External broker handoff response omitted user",
                status_code=status.HTTP_401_UNAUTHORIZED,
                redirect_to_error=True,
            )
        principal = resolve_external_broker_principal(user, request)
        store_session_principal(request, config, principal)
    except CognitoWebAuthError as exc:
        clear_ui_session(request)
        return RedirectResponse(
            url=f"/auth/error?reason={exc.reason}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    request.session.pop(_EXTERNAL_BROKER_STATE_KEY, None)
    redirect_to = _safe_next_path(str(request.session.pop(_EXTERNAL_BROKER_NEXT_KEY, "/ui") or "/ui"))
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


def clear_ui_session(request: Request) -> None:
    clear_session_principal(request)
    config = getattr(getattr(request.app, "state", None), "web_session_config", None)
    if config is not None:
        request.session.pop(config.state_session_key, None)
        request.session.pop(config.next_path_session_key, None)
    request.session.pop(_EXTERNAL_BROKER_STATE_KEY, None)
    request.session.pop(_EXTERNAL_BROKER_NEXT_KEY, None)


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
            mode=str(getattr(request.state, "auth_mode", "cognito") or "cognito"),
            detail="ui_session",
            service_principal=False,
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
        profile = _load_ui_profile(request)
        if isinstance(profile, dict):
            auth_mode = str(getattr(request.state, "auth_mode", "cognito") or "cognito")
            store = getattr(request.app.state, "observability", None)
            if store is not None:
                store.record_auth_event(
                    status="ok",
                    mode=auth_mode,
                    detail="session",
                    service_principal=False,
                )
            return {"auth_mode": auth_mode, "service_principal": False, "profile": profile}

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
            auth_mode = str(getattr(request.state, "auth_mode", "cognito") or "cognito")
            store = getattr(request.app.state, "observability", None)
            if store is not None:
                store.record_auth_event(
                    status="ok",
                    mode=auth_mode,
                    detail="session_or_bearer",
                    service_principal=False,
                )
            return {"auth_mode": auth_mode, "service_principal": False, "profile": profile}

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
