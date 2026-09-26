"""Canonical TapDB 10 GUI and authenticated DAG v2 integration for Dewey."""

from __future__ import annotations

import hashlib
import re
import secrets
from typing import Any

from daylily_tapdb.web import (
    DagV2Limits,
    TapdbHostBridge,
    TapdbHostNavLink,
    create_tapdb_gui_app,
    mount_tapdb_dag_surfaces,
)
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dewey_service.auth import (
    build_browser_login_href,
    require_session_or_api_auth,
    require_ui_session,
)
from dewey_service.integrations.tapdb_runtime import (
    _resolve_tapdb_config_path,
    ensure_tapdb_version,
)
from dewey_service.rbac import Role, profile_has_role
from dewey_service.settings import Settings


def _request_next_path(request: Request) -> str:
    path = request.url.path
    return f"{path}?{request.url.query}" if request.url.query else path


def _resolve_host_user(request: Request) -> dict[str, Any] | None:
    try:
        profile = require_ui_session(request)
    except HTTPException:
        return None
    subject = str(profile.get("sub") or "").strip()
    email = str(profile.get("email") or "").strip().lower()
    if not subject or not email:
        raise HTTPException(status_code=401, detail="Authenticated subject and email are required")
    return {
        "uid": subject,
        "username": email,
        "email": email,
        "display_name": str(profile.get("name") or email).strip(),
        "role": "admin" if profile_has_role(profile, Role.ADMIN) else "user",
        "is_active": True,
        "require_password_change": False,
    }


def resolve_tapdb_config_path(settings: Settings) -> str:
    return _resolve_tapdb_config_path(
        namespace=settings.tapdb_database_name,
        client_id=settings.tapdb_client_id,
        config_path=settings.tapdb_config_path,
    )


def build_tapdb_host_bridge(settings: Settings) -> TapdbHostBridge:
    return TapdbHostBridge(
        auth_mode="host_session",
        service_name="dewey",
        app_name="Dewey",
        shell_title="Dewey Admin",
        shell_subtitle="Advanced data and service administration",
        home_url="/ui",
        login_url=lambda request: build_browser_login_href(next_path=_request_next_path(request)),
        logout_url="/auth/logout",
        change_password_url=None,
        resolve_user=_resolve_host_user,
        nav_links=(
            TapdbHostNavLink(label="Library", href="/ui"),
            TapdbHostNavLink(label="S3 Browser", href="/storage"),
            TapdbHostNavLink(label="Sets", href="/sets"),
            TapdbHostNavLink(label="Sharing", href="/shares"),
            TapdbHostNavLink(label="Admin", href="/admin"),
        ),
        extra_stylesheets=("/static/tapdb-embedded.css",),
        extra_context=lambda _request: {"dewey_embedded": True, "deployment": settings.deployment},
    )


def build_dag_auth_dependency(settings: Settings):
    """Project verified host auth into the stable actor contract required by DAG v2."""

    regular_auth = require_session_or_api_auth(settings)
    bearer = HTTPBearer(auto_error=False)

    async def require_dag_actor(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> dict[str, str]:
        token = str(credentials.credentials or "") if credentials else ""
        if token.startswith("dewey_dag_"):
            path = request.url.path
            allowed = path in {
                "/api/dag/manifest", "/api/dag/v2/data", "/api/dag/v2/search",
            } or re.fullmatch(r"/api/dag/v2/object/[^/]+", path) is not None
            if request.method != "GET" or not allowed:
                raise HTTPException(status_code=403, detail="DAG read credential has no route scope")
            expected = settings.dag_read_token_sha256
            fingerprint = hashlib.sha256(token.encode()).hexdigest()
            if not expected or not secrets.compare_digest(fingerprint, expected):
                raise HTTPException(status_code=401, detail="Invalid DAG read credential")
            return {"username": settings.dag_read_actor}

        authenticated = regular_auth(request, credentials)
        if authenticated.get("service_principal") is True:
            # Dewey's configured bearer tokens authorize this one service principal.
            return {"username": "dewey-service-token"}
        profile = authenticated.get("profile")
        if not isinstance(profile, dict) or not str(profile.get("sub") or "").strip():
            raise HTTPException(
                status_code=401, detail="DAG access requires an authenticated subject"
            )
        return {"sub": str(profile["sub"]).strip()}

    return require_dag_actor


def mount_tapdb_surfaces(app, *, settings: Settings) -> bool:
    """Mount both required surfaces or fail startup without a partial-capability fallback."""
    ensure_tapdb_version()
    config_path = resolve_tapdb_config_path(settings)
    bridge = build_tapdb_host_bridge(settings)
    gui_app = create_tapdb_gui_app(config_path=config_path, host_bridge=bridge)
    mount = mount_tapdb_dag_surfaces(
        app,
        config_path=config_path,
        service_id="dewey",
        display_name="Dewey",
        auth_dependency=build_dag_auth_dependency(settings),
        limits=DagV2Limits(max_depth=6, max_nodes=500, max_search_page_size=100),
    )
    if not mount.mounted:
        raise RuntimeError(f"Dewey DAG v2 unavailable: {mount.reason}: {mount.diagnostic}")
    app.mount("/tapdb", gui_app)
    app.state.tapdb_host_bridge = bridge
    app.state.tapdb_embedded = True
    app.state.tapdb_configured = True
    app.state.tapdb_config_path = config_path
    return True


def dewey_tapdb_obs_services_fragment(app) -> dict[str, Any]:
    """Advertise only the manifest from the successful canonical DAG v2 mount."""
    mount = app.state.tapdb_dag_v2_mount
    manifest = mount.manifest.to_dict()
    return {
        "extensions": list(mount.advertisement["extensions"]),
        "endpoints": [dict(item, auth="session_or_bearer") for item in manifest["endpoints"]],
        "capabilities": [key for key, enabled in manifest["features"].items() if enabled],
        "external_ref_models": ["typed_external_reference"],
        "contract_version": manifest["contract"],
        "dag_v2": manifest,
    }
