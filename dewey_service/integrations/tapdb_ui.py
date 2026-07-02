"""TapDB web + DAG integration helpers for Dewey."""

from __future__ import annotations

from typing import Any

from daylily_tapdb.models.instance import generic_instance
from daylily_tapdb.models.lineage import generic_instance_lineage
from daylily_tapdb.models.template import generic_template
from daylily_tapdb.web import (
    TapdbHostBridge,
    TapdbHostNavLink,
    build_dag_capability_advertisement,
    create_tapdb_dag_router,
    create_tapdb_gui_app,
)
from daylily_tapdb.web import runtime as tapdb_dag_runtime
from fastapi import Depends, HTTPException, Query, Request

from dewey_service.auth import (
    build_browser_login_href,
    require_session_or_api_auth,
    require_ui_session,
)
from dewey_service.integrations.tapdb_runtime import _resolve_tapdb_config_path
from dewey_service.rbac import Role, profile_has_role
from dewey_service.settings import Settings

_DAG_SEARCH_RECORD_TYPES = {"all", "template", "instance", "lineage"}
_DAG_SEARCH_MODELS = {
    "template": generic_template,
    "instance": generic_instance,
    "lineage": generic_instance_lineage,
}


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


def _dag_search_clean(value: Any) -> str:
    return str(value or "").strip()


def _dag_search_lower(value: Any) -> str:
    return _dag_search_clean(value).lower()


def _dag_search_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return value.isoformat()
    except Exception:
        return _dag_search_clean(value) or None


def _dag_search_record_type(value: Any) -> str:
    normalized = _dag_search_lower(value) or "all"
    return normalized if normalized in _DAG_SEARCH_RECORD_TYPES else "all"


def _dag_row_matches_text(row: Any, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        _dag_search_lower(getattr(row, name, None))
        for name in (
            "euid",
            "name",
            "category",
            "type",
            "subtype",
            "version",
            "bstatus",
            "relationship_type",
        )
    )
    return query in haystack


def _dag_row_matches_filters(
    row: Any,
    *,
    query: str,
    euid: str,
    category: str,
    type_name: str,
    subtype: str,
    tenant_id: str,
    relationship_type: str,
) -> bool:
    if query and not _dag_row_matches_text(row, query):
        return False
    if euid and _dag_search_lower(getattr(row, "euid", None)) != euid:
        return False
    if category and _dag_search_lower(getattr(row, "category", None)) != category:
        return False
    if type_name and _dag_search_lower(getattr(row, "type", None)) != type_name:
        return False
    if subtype and _dag_search_lower(getattr(row, "subtype", None)) != subtype:
        return False
    if tenant_id and _dag_search_lower(getattr(row, "tenant_id", None)) != tenant_id:
        return False
    if (
        relationship_type
        and _dag_search_lower(getattr(row, "relationship_type", None)) != relationship_type
    ):
        return False
    return True


def _dag_search_result(row: Any, *, record_type: str, service_name: str) -> dict[str, Any]:
    euid = getattr(row, "euid", None)
    name = getattr(row, "name", None)
    return {
        "system": service_name,
        "service": service_name,
        "record_type": record_type,
        "kind": record_type,
        "uid": getattr(row, "uid", None),
        "euid": euid,
        "name": name,
        "display_label": name or euid,
        "category": getattr(row, "category", None),
        "type": getattr(row, "type", None),
        "subtype": getattr(row, "subtype", None),
        "version": getattr(row, "version", None),
        "bstatus": getattr(row, "bstatus", None),
        "tenant_id": _dag_search_clean(getattr(row, "tenant_id", None)) or None,
        "relationship_type": getattr(row, "relationship_type", None),
        "href": f"/object/{euid or ''}",
        "graph_href": f"/api/dag/data?start_euid={euid or ''}",
        "created_dt": _dag_search_iso(getattr(row, "created_dt", None)),
        "modified_dt": _dag_search_iso(getattr(row, "modified_dt", None)),
    }


def _search_tapdb_objects(
    session: Any,
    *,
    service_name: str,
    q: str = "",
    euid: str = "",
    record_type: str = "all",
    category: str = "",
    type_name: str = "",
    subtype: str = "",
    tenant_id: str = "",
    relationship_type: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    normalized_record_type = _dag_search_record_type(record_type)
    selected_types = (
        ["template", "instance", "lineage"]
        if normalized_record_type == "all"
        else [normalized_record_type]
    )
    normalized_limit = max(1, min(100, int(limit or 25)))
    filters = {
        "q": _dag_search_lower(q),
        "euid": _dag_search_lower(euid),
        "record_type": normalized_record_type,
        "category": _dag_search_lower(category),
        "type": _dag_search_lower(type_name),
        "subtype": _dag_search_lower(subtype),
        "tenant_id": _dag_search_lower(tenant_id),
        "relationship_type": _dag_search_lower(relationship_type),
        "limit": normalized_limit,
    }

    results: list[dict[str, Any]] = []
    for kind in selected_types:
        rows = session.query(_DAG_SEARCH_MODELS[kind]).filter_by(is_deleted=False).all()
        for row in rows:
            if _dag_row_matches_filters(
                row,
                query=filters["q"],
                euid=filters["euid"],
                category=filters["category"],
                type_name=filters["type"],
                subtype=filters["subtype"],
                tenant_id=filters["tenant_id"],
                relationship_type=filters["relationship_type"],
            ):
                results.append(_dag_search_result(row, record_type=kind, service_name=service_name))

    results.sort(
        key=lambda item: (
            str(item.get("created_dt") or ""),
            str(item.get("record_type") or ""),
            str(item.get("euid") or ""),
        ),
        reverse=True,
    )
    return {
        "items": results[:normalized_limit],
        "page": {
            "limit": normalized_limit,
            "total": len(results),
            "next_cursor": None,
        },
        "filters": filters,
    }


def _dewey_dag_contract_version() -> str:
    return str(build_dag_capability_advertisement().get("contract_version") or "dag:v1")


def _build_dewey_dag_router(*, config_path: str) -> Any:
    router = create_tapdb_dag_router(
        config_path=config_path,
        service_name="dewey",
    )

    @router.get("/api/dag/search")
    async def dag_search(
        q: str = "",
        euid: str = "",
        record_type: str = "all",
        category: str = "",
        type: str = "",
        subtype: str = "",
        tenant_id: str = "",
        relationship_type: str = "",
        limit: int = Query(25, ge=1, le=100),
    ) -> dict[str, Any]:
        with tapdb_dag_runtime.get_db(config_path) as conn:
            with conn.session_scope() as session:
                payload = _search_tapdb_objects(
                    session,
                    service_name="dewey",
                    q=q,
                    euid=euid,
                    record_type=record_type,
                    category=category,
                    type_name=type,
                    subtype=subtype,
                    tenant_id=tenant_id,
                    relationship_type=relationship_type,
                    limit=limit,
                )
                payload["meta"] = {
                    "owner_service": "dewey",
                    "contract_version": _dewey_dag_contract_version(),
                }
                return payload

    return router


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
        create_tapdb_gui_app(
            config_path=config_path,
            host_bridge=bridge,
        ),
    )
    app.include_router(
        _build_dewey_dag_router(
            config_path=config_path,
        ),
        dependencies=[Depends(require_session_or_api_auth(settings))],
    )
    return True


def dewey_tapdb_obs_services_fragment() -> dict[str, Any]:
    """Return Dewey-facing obs_services metadata for the embedded TapDB contract."""

    fragment = build_dag_capability_advertisement(
        base_path="/api/dag",
        auth="session_or_bearer",
    )
    endpoints = list(fragment.get("endpoints") or [])
    if not any(item.get("path") == "/api/dag/search" for item in endpoints):
        endpoints.insert(
            2,
            {
                "path": "/api/dag/search",
                "auth": "session_or_bearer",
                "kind": "dag_object_search",
            },
        )
    fragment["endpoints"] = endpoints

    capabilities = list(fragment.get("capabilities") or [])
    if "object_search" not in capabilities:
        capabilities.append("object_search")
    fragment["capabilities"] = capabilities

    external_ref_models = list(fragment.get("external_ref_models") or [])
    for model_name in ("external_payload.tapdb_graph", "typed_external_identifier"):
        if model_name not in external_ref_models:
            external_ref_models.append(model_name)
    fragment["external_ref_models"] = external_ref_models
    return fragment
