"""TapDB web + DAG integration helpers for Dewey."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request

from daylily_tapdb.web import (
    TapdbHostBridge,
    TapdbHostNavLink,
    build_dag_capability_advertisement,
    create_tapdb_dag_router,
    create_tapdb_web_app,
)
from dewey_service.auth import build_browser_login_href, require_session_or_api_auth, require_ui_session
from dewey_service.integrations.tapdb_runtime import _resolve_tapdb_config_path
from dewey_service.rbac import Role, profile_has_role
from dewey_service.settings import Settings


def _request_next_path(request: Request) -> str:
    next_path = request.url.path
    if request.url.query:
        next_path = f"{next_path}?{request.url.query}"
    return next_path


def _resolve_host_user(request: Request) -> dict[str, Any] | None:
    try:
        profile = require_ui_session(request)
    except HTTPException:
        return None

    email = str(profile.get("email") or "").strip().lower()
    return {
        "uid": str(profile.get("sub") or email).strip() or email,
        "username": email,
        "email": email,
        "display_name": str(profile.get("name") or email).strip() or email,
        "role": "admin" if profile_has_role(profile, Role.ADMIN) else "user",
        "is_active": True,
        "require_password_change": False,
    }


def resolve_tapdb_config_path(settings: Settings) -> str:
    return str(
        _resolve_tapdb_config_path(
            namespace=settings.tapdb_database_name,
            client_id=settings.tapdb_client_id,
            config_path=settings.tapdb_config_path,
        )
        or ""
    ).strip()


def build_tapdb_host_bridge(settings: Settings) -> TapdbHostBridge:
    return TapdbHostBridge(
        auth_mode="host_session",
        service_name="dewey",
        app_name="Dewey",
        shell_title="Dewey Console",
        shell_subtitle="TapDB substrate",
        home_url="/ui",
        login_url=lambda request: build_browser_login_href(next_path=_request_next_path(request)),
        logout_url="/auth/logout",
        change_password_url=None,
        resolve_user=_resolve_host_user,
        nav_links=(
            TapdbHostNavLink(label="Dashboard", href="/ui"),
            TapdbHostNavLink(label="Artifacts", href="/artifacts"),
            TapdbHostNavLink(label="Search", href="/search"),
            TapdbHostNavLink(label="Observability", href="/ui/observability"),
        ),
        extra_stylesheets=("/static/console.css",),
        extra_context=lambda _request: {"dewey_embedded": True, "deployment": settings.deployment},
    )


def mount_tapdb_surfaces(app, *, settings: Settings) -> bool:
    """Mount the TapDB UI and canonical DAG API into Dewey when configured."""

    config_path = resolve_tapdb_config_path(settings)
    if not config_path:
        app.state.tapdb_embedded = False
        app.state.tapdb_configured = False
        return False

    bridge = build_tapdb_host_bridge(settings)
    app.state.tapdb_host_bridge = bridge
    app.state.tapdb_embedded = True
    app.state.tapdb_configured = True
    app.state.tapdb_config_path = config_path

    app.mount(
        "/tapdb",
        create_tapdb_web_app(
            config_path=config_path,
            env_name=settings.tapdb_env,
            host_bridge=bridge,
        ),
    )
    app.include_router(
        create_tapdb_dag_router(
            config_path=config_path,
            env_name=settings.tapdb_env,
            service_name="dewey",
        ),
        dependencies=[Depends(require_session_or_api_auth(settings))],
    )
    return True


def dewey_tapdb_obs_services_fragment() -> dict[str, Any]:
    """Return Dewey-facing obs_services metadata for the embedded TapDB contract."""

    return build_dag_capability_advertisement(
        base_path="/api/dag",
        auth="session_or_bearer",
    )
