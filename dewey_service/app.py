"""FastAPI app for Dewey canonical artifact service."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic, time_ns
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.middleware.trustedhost import TrustedHostMiddleware

from dewey_service.artifact_ui import (
    ARTIFACT_SET_TYPES,
    ARTIFACT_TYPES,
    NA_ARTIFACT_TYPE,
    bulk_template_tsv,
    collect_metadata,
    collect_metadata_search_filters,
    metadata_fields,
    parse_json_object,
    resolve_artifact_type,
    split_csv,
    split_lines,
)
from dewey_service.auth import (
    build_browser_login_href,
    build_cognito_logout_url,
    build_cognito_web_session_config,
    clear_ui_session,
    complete_browser_login,
    configure_session_middleware,
    generate_state,
    require_api_auth,
    require_observability_access,
    require_session_or_api_auth,
    require_ui_admin_session,
    require_ui_session,
    start_browser_login,
)
from dewey_service.domain_access import (
    build_allowed_origin_regex,
    build_trusted_hosts,
    is_allowed_origin,
)
from dewey_service.integrations.tapdb_ui import (
    dewey_tapdb_obs_services_fragment,
    mount_tapdb_surfaces,
)
from dewey_service.literature import LiteratureUnavailableError, MetapubAdapter, ViewerContext
from dewey_service.observability import (
    DeweyObservabilityStore,
    build_api_health_payload,
    build_auth_health_payload,
    build_db_health_payload,
    build_endpoint_health_payload,
    build_health_payload,
    build_healthz_payload,
    build_my_health_payload,
    build_obs_services_payload,
    build_readyz_payload,
    hash_identifier,
    probe_database,
    route_template_from_request,
)
from dewey_service.rbac import Role, profile_has_role
from dewey_service.service import DeweyConflictError, DeweyNotFoundError, DeweyService
from dewey_service.settings import (
    Settings,
    get_config_file_path,
    get_settings,
    persist_managed_storage_bucket,
)
from dewey_service.storage import S3StorageClient
from dewey_service.tapdb_backend import TapDBBackend


class ArtifactRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    storage_backend: str = "s3"
    bucket: str
    key: str
    version_id: str | None = None
    size: int | None = None
    checksums: dict[str, Any] = Field(default_factory=dict)
    content_type: str | None = None
    original_filename: str | None = None
    producer_system: str | None = None
    producer_object_euid: str | None = None
    storage_class: str | None = None
    availability_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    storage_uri: str | None = None
    source_uri: str | None = None
    import_mode: str = Field(default="reference", pattern="^(copy|reference)$")
    lock_after_import: bool = False
    producer_system: str | None = None
    producer_object_euid: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactRunPrefixImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_uri: str
    platform: str = Field(default="ultima", pattern="^(ultima)$")
    owner_email: str
    run_id: str | None = None
    finalize: bool = False


class UploadSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    original_filename: str
    content_type: str | None = None
    producer_system: str | None = None
    producer_object_euid: str | None = None
    lock_after_import: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadSessionCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upload_token: str | None = None
    checksums: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactSetCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_set_type: str
    label: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactSetMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_euid: str


class ResolveArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_euid: str


class ResolveArtifactSetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_set_euid: str


class ShareReferenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: str = Field(pattern="^(artifact|artifact_set)$")
    target_euid: str
    purpose: str | None = None
    scope: str | None = None
    expires_at: str | None = None
    issued_by: str | None = None
    transport: str = Field(
        default="presigned_s3",
        pattern="^(presigned_s3|rclone_http|rclone_sftp)$",
    )
    transport_config: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int | None = None


class ArtifactStorageLockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = "GOVERNANCE"
    retain_until: str


class ExternalObjectCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_system: str
    external_object_type: str
    external_object_id: str
    external_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalObjectRelationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: str = Field(pattern="^(artifact|artifact_set)$")
    target_euid: str
    external_object_euid: str
    relation_type: str = "linked"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchPropertyFilterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    op: str = "eq"
    value: Any = None


class SearchQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str | None = None
    scopes: list[str] | None = None
    page: int = 1
    page_size: int = 25
    sort_field: str = "created_at"
    sort_dir: str = "desc"
    property_filters: list[SearchPropertyFilterRequest] = Field(default_factory=list)
    created_at_start: str | None = None
    created_at_end: str | None = None


class SearchExportRequest(SearchQueryRequest):
    format: str = Field(default="json", pattern="^(json|tsv)$")
    max_rows: int | None = None


class LiteratureSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    page: int = 1
    page_size: int = 20


class LiteratureSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pmid: str
    save_mode: str = Field(
        default="auto",
        pattern="^(auto|managed_artifact|external_reference)$",
    )
    visibility_scope: str = Field(
        default="private",
        pattern="^(private|restricted|all_users)$",
    )
    allowed_users: list[str] = Field(default_factory=list)
    allowed_groups: list[str] = Field(default_factory=list)


class LiteratureSaveVisibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visibility_scope: str = Field(
        default="private",
        pattern="^(private|restricted|all_users)$",
    )
    allowed_users: list[str] = Field(default_factory=list)
    allowed_groups: list[str] = Field(default_factory=list)


def create_app(
    settings: Settings | None = None,
    service: DeweyService | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    allow_local_domain_access = not settings.is_production

    if service is None:
        backend = TapDBBackend(app_username="dewey")
        storage_client = S3StorageClient(
            profile=settings.aws_profile,
            region=settings.aws_region,
        )
        literature_adapter = None
        try:
            literature_adapter = MetapubAdapter(
                cache_dir=settings.literature_metapub_cache_dir,
                request_timeout_seconds=settings.literature_request_timeout_seconds,
                max_redirects=settings.literature_max_redirects,
            )
        except LiteratureUnavailableError:
            literature_adapter = None
        service = DeweyService(
            backend,
            default_share_ttl_seconds=settings.default_share_reference_ttl_seconds,
            storage_client=storage_client,
            managed_storage_bucket=settings.managed_storage_bucket,
            managed_storage_prefix=settings.managed_storage_prefix,
            upload_session_ttl_seconds=settings.upload_session_ttl_seconds,
            upload_token_secret=settings.session_secret_key,
            search_export_max_rows=settings.search_export_max_rows,
            literature_adapter=literature_adapter,
            literature_allowed_domains=settings.literature_allowed_domains,
            literature_request_timeout_seconds=settings.literature_request_timeout_seconds,
        )
        service.bootstrap()

    app = FastAPI(
        title="Dewey Artifact Service",
        version="1.0.0",
        description="Canonical artifact registry and resolver for LSMC",
    )
    app.state.settings = settings
    app.state.service = service
    app.state.observability = DeweyObservabilityStore(settings, version=app.version)
    backend = getattr(service, "backend", None)
    if backend is not None and hasattr(backend, "observability"):
        backend.observability = app.state.observability
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=build_trusted_hosts(allow_local=allow_local_domain_access),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=build_allowed_origin_regex(allow_local=allow_local_domain_access),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    web_session_config = build_cognito_web_session_config(settings=settings)
    app.state.web_session_config = web_session_config
    app.state.server_instance_id = web_session_config.server_instance_id
    configure_session_middleware(app, web_session_config)

    templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

    def _static_url(path: str) -> str:
        clean = str(path or "").lstrip("/")
        separator = "&" if "?" in clean else "?"
        return f"/static/{clean}{separator}v={time_ns()}"

    templates.env.globals["static_url"] = _static_url
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    tapdb_embedded = mount_tapdb_surfaces(app, settings=settings)
    if tapdb_embedded:
        fragment = dewey_tapdb_obs_services_fragment()
        app.state.observability.add_obs_services_fragment(
            endpoints=list(fragment.get("endpoints") or []),
            extensions=list(fragment.get("extensions") or []),
        )

    api_auth_dep = require_api_auth(settings)
    observability_auth_dep = require_observability_access(settings)
    session_or_api_auth_dep = require_session_or_api_auth(settings)

    def _template_context(**kwargs: Any) -> dict[str, Any]:
        context = {
            "deployment": settings.deployment,
            "tapdb_embedded": bool(getattr(app.state, "tapdb_embedded", False)),
        }
        context.update(kwargs)
        return context

    def _auth_template_context(
        *,
        cognito_login_url: str = "/auth/login",
        badge: str = "Authentication Required",
        eyebrow: str = "Dewey",
        title: str = "Dewey Access Login",
        description: str = "Canonical artifact intake, lifecycle, sharing, and search for Dewey users and admins.",
        card_title: str = "Sign In",
        card_copy: str = "Continue through Cognito Hosted UI to access the Dewey console.",
        primary_href: str = "/auth/login",
        primary_label: str = "Sign In with Cognito",
        error_message: str = "",
        status_code: int = 200,
    ) -> tuple[dict[str, Any], int]:
        context = _template_context(
            cognito_login_url=cognito_login_url,
            title=title,
            auth_badge=badge,
            auth_eyebrow=eyebrow,
            auth_title=title,
            auth_description=description,
            auth_card_title=card_title,
            auth_card_copy=card_copy,
            auth_primary_href=primary_href,
            auth_primary_label=primary_label,
            auth_error=error_message,
            auth_status_code=status_code,
        )
        return context, status_code

    def _request_next_path(request: Request) -> str:
        next_path = request.url.path
        if request.url.query:
            next_path = f"{next_path}?{request.url.query}"
        return next_path

    def _login_url_for_request(request: Request) -> str:
        return f"/login?{urlencode({'next': _request_next_path(request)})}"

    def _viewer_context(profile: dict[str, Any]) -> ViewerContext:
        return ViewerContext.from_operator_profile(profile)

    def _is_admin(profile: dict[str, Any]) -> bool:
        return profile_has_role(profile, Role.ADMIN)

    def _with_search_alias_headers(response: Response, successor: str) -> None:
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Wed, 30 Sep 2026 00:00:00 GMT"
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'

    def _search_payload_to_tsv(items: list[dict[str, Any]]) -> str:
        fields = [
            "record_type",
            "source_kind",
            "euid",
            "name",
            "created_at",
            "modified_at",
            "artifact_type",
            "artifact_set_type",
            "label",
            "description",
            "title",
            "pmid",
            "doi",
            "producer_system",
            "storage_backend",
            "storage_uri",
            "availability_status",
            "import_mode",
            "storage_mode",
            "member_count",
            "saved_by_me",
            "saved_by_others_count",
            "visible_owner_labels",
            "target_type",
            "target_euid",
            "transport",
            "status",
            "expires_at",
            "connection",
            "manifest",
            "metadata",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for item in items:
            row = dict(item)
            row["metadata"] = json.dumps(item.get("metadata") or {}, sort_keys=True, default=str)
            row["visible_owner_labels"] = json.dumps(
                item.get("visible_owner_labels") or [],
                sort_keys=True,
                default=str,
            )
            row["connection"] = json.dumps(
                item.get("connection") or {}, sort_keys=True, default=str
            )
            row["manifest"] = json.dumps(item.get("manifest") or [], sort_keys=True, default=str)
            writer.writerow(row)
        return buffer.getvalue()

    def _search_form_payload(request: Request) -> dict[str, Any]:
        params = request.query_params
        property_filters: list[dict[str, Any]] = []
        for field_name in [
            "artifact_type",
            "producer_system",
            "availability_status",
            "import_mode",
            "transport",
            "status",
        ]:
            value = str(params.get(field_name) or "").strip()
            if value:
                property_filters.append({"path": field_name, "op": "eq", "value": value})

        external_object_id = str(params.get("external_object_id") or "").strip()
        if external_object_id:
            property_filters.append(
                {
                    "path": "external_objects.external_object_id",
                    "op": "eq",
                    "value": external_object_id,
                }
            )

        raw_scopes = params.getlist("scope")
        scopes = [item for item in raw_scopes if item]
        return {
            "q": str(params.get("q") or "").strip() or None,
            "scopes": scopes or ["artifact", "share_reference"],
            "page": int(params.get("page") or 1),
            "page_size": int(params.get("page_size") or 25),
            "sort_field": str(params.get("sort_field") or "created_at"),
            "sort_dir": str(params.get("sort_dir") or "desc"),
            "property_filters": property_filters,
            "created_at_start": str(params.get("created_at_start") or "").strip() or None,
            "created_at_end": str(params.get("created_at_end") or "").strip() or None,
        }

    def _new_idempotency_key(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex}"

    def _artifact_metadata_fields() -> list[dict[str, str]]:
        return metadata_fields("artifact")

    def _artifact_set_metadata_fields() -> list[dict[str, str]]:
        return metadata_fields("artifact_set")

    def _parse_state_json(raw: Any) -> dict[str, Any]:
        text = str(raw or "").strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _artifact_search_payload(values: dict[str, Any]) -> dict[str, Any]:
        greedy = str(values.get("artifact_match_mode") or "greedy").strip().lower() != "exact"
        property_filters: list[dict[str, Any]] = []
        for field_name in [
            "artifact_type",
            "producer_system",
            "availability_status",
            "import_mode",
        ]:
            value = str(values.get(field_name) or "").strip()
            if value:
                property_filters.append({"path": field_name, "op": "eq", "value": value})
        artifact_euids = split_lines(values.get("artifact_euids"))
        if artifact_euids:
            property_filters.append({"path": "artifact_euid", "op": "in", "value": artifact_euids})
        external_object_id = str(values.get("external_object_id") or "").strip()
        if external_object_id:
            property_filters.append(
                {
                    "path": "external_objects.external_object_id",
                    "op": "eq",
                    "value": external_object_id,
                }
            )
        property_filters.extend(
            collect_metadata_search_filters(
                values,
                fields=_artifact_metadata_fields(),
                prefix="artifact_filter",
                greedy=greedy,
            )
        )
        return {
            "q": str(values.get("artifact_q") or "").strip() or None,
            "scopes": ["artifact"],
            "page": int(values.get("artifact_page") or 1),
            "page_size": int(values.get("artifact_page_size") or 25),
            "sort_field": str(values.get("artifact_sort_field") or "created_at"),
            "sort_dir": str(values.get("artifact_sort_dir") or "desc"),
            "property_filters": property_filters,
            "created_at_start": str(values.get("artifact_created_at_start") or "").strip() or None,
            "created_at_end": str(values.get("artifact_created_at_end") or "").strip() or None,
        }

    def _artifact_set_search_payload(values: dict[str, Any]) -> dict[str, Any]:
        greedy = str(values.get("artifact_set_match_mode") or "greedy").strip().lower() != "exact"
        property_filters: list[dict[str, Any]] = []
        artifact_set_type = str(values.get("artifact_set_type") or "").strip()
        if artifact_set_type:
            property_filters.append(
                {"path": "artifact_set_type", "op": "eq", "value": artifact_set_type}
            )
        for field_name in ["label", "description"]:
            value = str(values.get(f"artifact_set_{field_name}") or "").strip()
            if value:
                property_filters.append(
                    {
                        "path": field_name,
                        "op": "contains" if greedy else "eq",
                        "value": value,
                    }
                )
        artifact_set_euids = split_lines(values.get("artifact_set_euids"))
        if artifact_set_euids:
            property_filters.append(
                {"path": "artifact_set_euid", "op": "in", "value": artifact_set_euids}
            )
        property_filters.extend(
            collect_metadata_search_filters(
                values,
                fields=_artifact_set_metadata_fields(),
                prefix="artifact_set_filter",
                greedy=greedy,
            )
        )
        return {
            "q": str(values.get("artifact_set_q") or "").strip() or None,
            "scopes": ["artifact_set"],
            "page": int(values.get("artifact_set_page") or 1),
            "page_size": int(values.get("artifact_set_page_size") or 25),
            "sort_field": str(values.get("artifact_set_sort_field") or "created_at"),
            "sort_dir": str(values.get("artifact_set_sort_dir") or "desc"),
            "property_filters": property_filters,
            "created_at_start": str(values.get("artifact_set_created_at_start") or "").strip()
            or None,
            "created_at_end": str(values.get("artifact_set_created_at_end") or "").strip() or None,
        }

    def _empty_artifact_search_result() -> dict[str, Any]:
        return {
            "items": [],
            "facets": {"artifact": 0, "artifact_set": 0, "share_reference": 0},
            "total": 0,
            "page": 1,
            "page_size": 25,
            "has_more": False,
            "timing_ms": 0,
        }

    def _empty_artifact_set_search_result() -> dict[str, Any]:
        return {
            "items": [],
            "facets": {"artifact": 0, "artifact_set": 0, "share_reference": 0},
            "total": 0,
            "page": 1,
            "page_size": 25,
            "has_more": False,
            "timing_ms": 0,
        }

    def _normalize_artifact_section(value: Any) -> str:
        allowed = {"register", "search", "artifact_sets", "recent_artifacts"}
        candidate = str(value or "").strip().lower() or "register"
        return candidate if candidate in allowed else "register"

    def _admin_page_response(
        request: Request,
        *,
        profile: dict[str, Any],
        artifact_bucket_form: dict[str, Any] | None = None,
        artifact_bucket_status: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        anomalies = service.list_anomalies(limit=100)
        return templates.TemplateResponse(
            request,
            "admin.html",
            _template_context(
                profile=profile,
                anomalies=anomalies,
                is_admin=True,
                managed_storage_bucket=str(settings.managed_storage_bucket or "").strip(),
                managed_storage_prefix=str(settings.managed_storage_prefix or "").strip(),
                config_path=str(get_config_file_path()),
                artifact_bucket_form=artifact_bucket_form
                or {"managed_storage_bucket": str(settings.managed_storage_bucket or "").strip()},
                artifact_bucket_status=artifact_bucket_status,
            ),
            status_code=status_code,
        )

    def _default_artifact_page_context(profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "profile": profile,
            "is_admin": _is_admin(profile),
            "artifact_types": ARTIFACT_TYPES,
            "artifact_set_types": ARTIFACT_SET_TYPES,
            "artifact_metadata_fields": _artifact_metadata_fields(),
            "artifact_set_metadata_fields": _artifact_set_metadata_fields(),
            "artifact_form": {},
            "artifact_search_form": {},
            "artifact_set_form": {},
            "artifact_set_search_form": {},
            "artifact_search_result": _empty_artifact_search_result(),
            "artifact_set_search_result": _empty_artifact_set_search_result(),
            "artifact_search_form_json": "{}",
            "artifact_set_search_form_json": "{}",
            "register_report": [],
            "bulk_report": [],
            "run_prefix_form": {
                "root_uri": "",
                "platform": "ultima",
                "owner_email": str(profile.get("email") or "").strip().lower(),
                "run_id": "",
                "finalize": "no",
            },
            "run_prefix_result": None,
            "recent_artifacts": service.list_artifacts(limit=20),
            "artifact_share_results": [],
            "artifact_set_share_result": None,
            "artifact_set_create_result": None,
            "bulk_template_url": "/artifacts/bulk-template.tsv",
            "active_section": "register",
        }

    def _ui_home_response(
        request: Request,
        *,
        profile: dict[str, Any],
        quick_register_form: dict[str, Any] | None = None,
        quick_register_result: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        artifacts = service.list_artifacts(limit=100)
        share_references = service.list_share_references(limit=100)
        active_share_count = sum(1 for item in share_references if item.get("status") == "active")
        verification_failures = sum(
            1 for item in artifacts if item.get("storage_status") in {"missing", "error"}
        )
        recent_imports = sum(
            1 for item in artifacts if item.get("import_mode") in {"copy", "reference", "upload"}
        )
        return templates.TemplateResponse(
            request,
            "ui_home.html",
            _template_context(
                profile=profile,
                artifacts=artifacts,
                share_references=share_references[:12],
                metrics={
                    "artifact_count": len(artifacts),
                    "active_share_count": active_share_count,
                    "recent_import_count": recent_imports,
                    "verification_failures": verification_failures,
                },
                artifact_types=ARTIFACT_TYPES,
                quick_register_form=quick_register_form
                or {
                    "source_url": "",
                    "source_s3_uri": "",
                    "artifact_tags": "",
                },
                quick_register_result=quick_register_result,
                is_admin=_is_admin(profile),
            ),
            status_code=status_code,
        )

    def _default_browse_root_uri() -> str:
        bucket = str(settings.managed_storage_bucket or "").strip()
        prefix = str(settings.managed_storage_prefix or "").strip().strip("/")
        if not bucket:
            return ""
        if prefix:
            return f"s3://{bucket}/{prefix}/"
        return f"s3://{bucket}/"

    def _browse_root_for_artifact(artifact: dict[str, Any]) -> str:
        if str(artifact.get("storage_backend") or "").strip().lower() != "s3":
            return ""
        bucket = str(artifact.get("bucket") or "").strip()
        key = str(artifact.get("key") or "").strip()
        if not bucket:
            return ""
        if str(artifact.get("storage_kind") or "").strip().lower() == "prefix":
            return str(artifact.get("storage_uri") or "").strip() or f"s3://{bucket}/{key}"
        parent_parts = [item for item in key.split("/") if item][:-1]
        if not parent_parts:
            return f"s3://{bucket}/"
        return f"s3://{bucket}/{'/'.join(parent_parts)}/"

    def _artifact_page_response(
        request: Request,
        *,
        profile: dict[str, Any],
        **overrides: Any,
    ) -> HTMLResponse:
        context = _default_artifact_page_context(profile)
        context.update(overrides)
        if isinstance(context.get("artifact_search_form"), dict):
            context["artifact_search_form_json"] = json.dumps(context["artifact_search_form"])
        if isinstance(context.get("artifact_set_search_form"), dict):
            context["artifact_set_search_form_json"] = json.dumps(
                context["artifact_set_search_form"]
            )
        return templates.TemplateResponse(
            request,
            "artifacts.html",
            _template_context(**context),
        )

    def _artifact_dag_response(
        request: Request,
        *,
        profile: dict[str, Any],
        browse_root_uri: str = "",
        browse_limit: int = 200,
        browse_result: dict[str, Any] | None = None,
        graph_result: dict[str, Any] | None = None,
        selected_artifact: dict[str, Any] | None = None,
        dag_message: dict[str, Any] | None = None,
        continuation_token: str | None = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "artifact_dag.html",
            _template_context(
                profile=profile,
                browse_root_uri=browse_root_uri or _default_browse_root_uri(),
                browse_limit=browse_limit,
                browse_result=browse_result,
                browse_result_json=json.dumps(browse_result or {}),
                graph_result=graph_result,
                graph_result_json=json.dumps(graph_result or {}),
                selected_artifact=selected_artifact,
                continuation_token=continuation_token or "",
                dag_message=dag_message,
                is_admin=_is_admin(profile),
            ),
            status_code=status_code,
        )

    def _artifact_detail_response(
        request: Request,
        *,
        profile: dict[str, Any],
        artifact: dict[str, Any],
        detail_message: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "artifact_detail.html",
            _template_context(
                profile=profile,
                artifact=artifact,
                artifact_share_references=service.list_share_references(
                    target_type="artifact",
                    target_euid=artifact["artifact_euid"],
                    limit=20,
                ),
                artifact_external_relations=service.list_external_object_relations(
                    target_type="artifact",
                    target_euid=artifact["artifact_euid"],
                    limit=20,
                ),
                artifact_parents=service.list_artifact_parents(
                    artifact_euid=artifact["artifact_euid"],
                    limit=50,
                ),
                artifact_children=service.list_artifact_children(
                    artifact_euid=artifact["artifact_euid"],
                    limit=200,
                ),
                detail_message=detail_message,
                is_admin=_is_admin(profile),
            ),
            status_code=status_code,
        )

    def _string_form_values(form) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key in form.keys():
            value = form.get(key)
            if isinstance(value, StarletteUploadFile):
                continue
            values[key] = value
        return values

    def _rerun_artifact_search(
        form_state: dict[str, Any],
        *,
        profile: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not form_state:
            return {}, _empty_artifact_search_result()
        payload = _artifact_search_payload(form_state)
        result = service.query_search_v2(payload, viewer_context=_viewer_context(profile))
        return form_state, result

    def _rerun_artifact_set_search(
        form_state: dict[str, Any],
        *,
        profile: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not form_state:
            return {}, _empty_artifact_set_search_result()
        payload = _artifact_set_search_payload(form_state)
        result = service.query_search_v2(payload, viewer_context=_viewer_context(profile))
        return form_state, result

    @app.middleware("http")
    async def _enforce_origin_allowlist(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and not is_allowed_origin(origin, allow_local=allow_local_domain_access):
            return HTMLResponse(status_code=403, content="Origin not allowed")
        return await call_next(request)

    @app.middleware("http")
    async def _capture_observability(request: Request, call_next):
        request_id = str(request.headers.get("x-request-id") or "").strip() or generate_state()
        correlation_source = (
            str(request.headers.get("x-correlation-id") or "").strip()
            or str(request.headers.get("traceparent") or "").strip()
            or request_id
        )
        request.state.request_id = request_id
        request.state.correlation_id = hash_identifier(correlation_source)
        started = monotonic()
        response = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Correlation-Id"] = request.state.correlation_id
            return response
        finally:
            app.state.observability.record_http_request(
                method=request.method,
                route_template=route_template_from_request(request),
                status_code=status_code,
                duration_ms=(monotonic() - started) * 1000,
                path=request.url.path,
            )

    def _require_idempotency_key(value: str | None) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
        return normalized

    @app.exception_handler(DeweyNotFoundError)
    async def _not_found_handler(_request: Request, exc: DeweyNotFoundError):
        if _request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        return HTMLResponse(status_code=404, content=str(exc))

    @app.exception_handler(LiteratureUnavailableError)
    async def _literature_unavailable_handler(_request: Request, exc: LiteratureUnavailableError):
        if _request.url.path.startswith("/api/"):
            return JSONResponse(status_code=503, content={"detail": str(exc)})
        return HTMLResponse(status_code=503, content=str(exc))

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        """Redirect unauthenticated browser requests to the login page."""
        if exc.status_code == 401:
            accept = request.headers.get("accept", "")
            if "text/html" in accept and not request.url.path.startswith("/api/"):
                if getattr(request.state, "cognito_auth_reason", None) == "session_expired":
                    return RedirectResponse(
                        url="/auth/error?reason=session_expired",
                        status_code=status.HTTP_302_FOUND,
                    )
                return RedirectResponse(
                    url=_login_url_for_request(request),
                    status_code=status.HTTP_302_FOUND,
                )
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail or ""})
        return HTMLResponse(status_code=exc.status_code, content=exc.detail or "")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/ui", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> RedirectResponse:
        return RedirectResponse(
            url="/static/favicon.svg", status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    @app.get("/auth/login", include_in_schema=False)
    async def auth_login(
        request: Request,
        next_path: str = Query("/ui", alias="next"),
    ) -> RedirectResponse:
        try:
            return start_browser_login(request, web_session_config, next_path=next_path)
        except ValueError:
            return RedirectResponse(
                url="/auth/error?reason=cognito_sign_in_misconfigured",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    @app.get("/auth/callback", include_in_schema=False)
    async def auth_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
        return await complete_browser_login(
            request,
            web_session_config,
            code=code,
            state=state,
        )

    @app.get("/login", include_in_schema=False)
    async def login_page(
        request: Request,
        error: str = "",
        next_path: str = Query("", alias="next"),
    ) -> HTMLResponse:
        cognito_login_url = build_browser_login_href(next_path=next_path)
        context, status_code = _auth_template_context(
            cognito_login_url=cognito_login_url,
            primary_href=cognito_login_url,
            error_message=str(error or "").strip(),
        )
        return templates.TemplateResponse(request, "login.html", context, status_code=status_code)

    @app.get("/auth/error", include_in_schema=False)
    async def auth_error(request: Request, reason: str = "auth_error") -> HTMLResponse:
        reasons = {
            "auth_error": "An authentication error prevented sign-in from completing.",
            "invalid_state": "The sign-in flow could not be validated.",
            "missing_code": "The sign-in flow did not return an authorization code.",
            "token_exchange_failed": "Dewey could not finish exchanging the authorization code.",
            "session_expired": "Your session ended before the requested page loaded.",
            "not_authorized": "This account is not provisioned for Dewey access.",
            "cognito_sign_in_misconfigured": (
                "Dewey Cognito sign-in is misconfigured. The shared app client callback/logout "
                "URLs or redirect URI do not match this Dewey deployment."
            ),
            "cognito_logout_misconfigured": (
                "Dewey cleared your local session, but the shared Cognito logout contract is "
                "misconfigured. Update the shared app client redirect URLs for this Dewey deployment."
            ),
        }
        message = reasons.get(reason, reasons["auth_error"])
        context, status_code = _auth_template_context(
            badge="Access Review",
            title="This account could not complete sign-in.",
            description="Dewey access is provisioned per user role and deployment policy.",
            card_title="Sign-in was blocked",
            card_copy=message,
            primary_href="/auth/login",
            primary_label="Return to Sign In",
            error_message=message,
            status_code=403,
        )
        return templates.TemplateResponse(request, "login.html", context, status_code=status_code)

    async def _logout_response(request: Request) -> RedirectResponse:
        clear_ui_session(request)
        request.session.clear()
        state = generate_state()
        request.session["oauth_state"] = state
        try:
            logout_url = build_cognito_logout_url(settings=settings, state=state)
        except ValueError:
            return RedirectResponse(
                url="/auth/error?reason=cognito_logout_misconfigured",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        return RedirectResponse(url=logout_url, status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/auth/logout", include_in_schema=False)
    async def auth_logout_get(request: Request) -> RedirectResponse:
        return await _logout_response(request)

    @app.post("/auth/logout", include_in_schema=False)
    async def auth_logout_post(request: Request) -> RedirectResponse:
        return await _logout_response(request)

    @app.post("/logout", include_in_schema=False)
    async def logout(request: Request) -> RedirectResponse:
        return await _logout_response(request)

    @app.get("/healthz")
    async def healthz(request: Request) -> dict[str, Any]:
        return build_healthz_payload(
            request,
            started_at=app.state.observability.started_at,
        )

    @app.get("/readyz")
    async def readyz(request: Request) -> JSONResponse:
        probe = probe_database(service)
        app.state.observability.record_db_probe(
            status=str(probe["status"]),
            latency_ms=float(probe["latency_ms"]),
            detail=str(probe["detail"]),
        )
        ready = str(probe.get("status") or "") == "ok"
        payload = build_readyz_payload(
            request,
            started_at=app.state.observability.started_at,
            database_check=probe,
            ready=ready,
        )
        return JSONResponse(status_code=200 if ready else 503, content=payload)

    @app.get("/health")
    async def health(
        request: Request,
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        latest_db = app.state.observability.latest_db_probe()
        projection = app.state.observability.projection(
            observed_at=(latest_db or {}).get("observed_at")
        )
        return build_health_payload(
            request,
            projection=projection,
            health_snapshot=app.state.observability.health_snapshot(),
        )

    @app.get("/obs_services")
    async def obs_services(
        request: Request,
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        projection, snapshot = app.state.observability.obs_services_snapshot()
        return build_obs_services_payload(request, projection=projection, snapshot=snapshot)

    @app.get("/api_health")
    async def api_health(
        request: Request,
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        projection, families = app.state.observability.api_health()
        return build_api_health_payload(request, projection=projection, families=families)

    @app.get("/endpoint_health")
    async def endpoint_health(
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(25, ge=1, le=200),
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        projection, payload = app.state.observability.endpoint_health(offset=offset, limit=limit)
        return build_endpoint_health_payload(
            request,
            projection=projection,
            total=int(payload["total"]),
            offset=int(payload["offset"]),
            limit=int(payload["limit"]),
            items=list(payload["items"]),
        )

    @app.get("/db_health")
    async def db_health(
        request: Request,
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        probe = probe_database(service)
        app.state.observability.record_db_probe(
            status=str(probe["status"]),
            latency_ms=float(probe["latency_ms"]),
            detail=str(probe["detail"]),
        )
        projection, payload = app.state.observability.db_health()
        return build_db_health_payload(request, projection=projection, db_health=payload)

    @app.get("/my_health")
    async def my_health(
        request: Request,
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> dict[str, Any]:
        return build_my_health_payload(request, profile)

    @app.get("/auth_health")
    async def auth_health(
        request: Request,
        _auth: dict[str, Any] = Depends(observability_auth_dep),
    ) -> dict[str, Any]:
        projection, payload = app.state.observability.auth_health()
        return build_auth_health_payload(request, projection=projection, auth_rollup=payload)

    @app.get(
        "/api/anomalies",
        dependencies=[Depends(api_auth_dep)],
    )
    async def list_anomalies(
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        rows = service.list_anomalies(limit=limit)
        return {"items": rows, "total": len(rows)}

    @app.get(
        "/api/anomalies/{anomaly_id}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_anomaly(anomaly_id: str) -> dict[str, Any]:
        try:
            return service.get_anomaly(anomaly_id)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/ui", include_in_schema=False)
    async def ui_home(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        return _ui_home_response(request, profile=profile)

    @app.post("/ui/register", include_in_schema=False)
    async def ui_quick_register(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form(max_files=8)
        requested_artifact_type = str(form.get("artifact_type") or NA_ARTIFACT_TYPE).strip().lower()
        source_url = str(form.get("source_url") or "").strip()
        source_s3_uri = str(form.get("source_s3_uri") or "").strip()
        tag_text = str(form.get("artifact_tags") or "").strip()
        tag_values = split_csv(tag_text)
        metadata = {"tags": tag_values} if tag_values else {}
        quick_form = {
            "source_url": source_url,
            "source_s3_uri": source_s3_uri,
            "artifact_tags": tag_text,
        }
        upload = form.get("file_data")
        has_file = isinstance(upload, StarletteUploadFile) and bool(
            str(upload.filename or "").strip()
        )
        selected_sources = int(has_file) + int(bool(source_url)) + int(bool(source_s3_uri))
        if selected_sources != 1:
            return _ui_home_response(
                request,
                profile=profile,
                quick_register_form=quick_form,
                quick_register_result={
                    "state": "error",
                    "detail": "Specify exactly one source: local file, public URL, or S3 URI.",
                },
                status_code=400,
            )
        try:
            if has_file:
                file_name = Path(str(upload.filename or "").strip() or "upload.bin").name
                artifact_type = resolve_artifact_type(requested_artifact_type, file_name)
                _, payload = service.upload_artifact_bytes(
                    artifact_type=artifact_type,
                    original_filename=file_name,
                    body=await upload.read(),
                    content_type=str(upload.content_type or "").strip() or None,
                    producer_system=None,
                    producer_object_euid=None,
                    metadata=metadata,
                    lock_after_import=False,
                    idempotency_key=_new_idempotency_key("ui-home-upload"),
                )
                result_detail = f"Registered {file_name} as {payload['artifact_type']}."
                quick_form = {
                    "source_url": "",
                    "source_s3_uri": "",
                    "artifact_tags": tag_text,
                }
            elif source_url:
                artifact_type = resolve_artifact_type(requested_artifact_type, source_url)
                _, payload = service.import_artifact_from_uri(
                    artifact_type=artifact_type,
                    source_uri=source_url,
                    import_mode="copy",
                    lock_after_import=False,
                    producer_system=None,
                    producer_object_euid=None,
                    metadata=metadata,
                    idempotency_key=_new_idempotency_key("ui-home-url"),
                )
                result_detail = f"Imported {source_url} as {payload['artifact_type']}."
            else:
                artifact_type = resolve_artifact_type(requested_artifact_type, source_s3_uri)
                _, payload = service.import_artifact_from_uri(
                    artifact_type=artifact_type,
                    source_uri=source_s3_uri,
                    import_mode="reference",
                    lock_after_import=False,
                    producer_system=None,
                    producer_object_euid=None,
                    metadata=metadata,
                    idempotency_key=_new_idempotency_key("ui-home-s3"),
                )
                result_detail = f"Registered {source_s3_uri} as {payload['artifact_type']}."
        except Exception as exc:
            return _ui_home_response(
                request,
                profile=profile,
                quick_register_form=quick_form,
                quick_register_result={"state": "error", "detail": str(exc)},
                status_code=400,
            )
        return _ui_home_response(
            request,
            profile=profile,
            quick_register_form=quick_form,
            quick_register_result={
                "state": "ok",
                "detail": result_detail,
                "artifact_euid": payload["artifact_euid"],
            },
        )

    @app.get("/ui/anomalies", include_in_schema=False)
    async def anomalies_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        anomalies = service.list_anomalies(limit=100)
        return templates.TemplateResponse(
            request,
            "anomalies.html",
            _template_context(
                profile=profile,
                anomalies=anomalies,
                is_admin=_is_admin(profile),
            ),
        )

    @app.get("/ui/anomalies/{anomaly_id}", include_in_schema=False)
    async def anomaly_detail_page(
        request: Request,
        anomaly_id: str,
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> HTMLResponse:
        try:
            anomaly = service.get_anomaly(anomaly_id)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request,
            "anomaly_detail.html",
            _template_context(
                profile=profile,
                anomaly=anomaly,
                is_admin=_is_admin(profile),
            ),
        )

    @app.get("/admin", include_in_schema=False)
    async def admin_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_admin_session)
    ) -> HTMLResponse:
        return _admin_page_response(request, profile=profile)

    @app.post("/admin/artifact-storage", include_in_schema=False)
    async def admin_update_artifact_storage(
        request: Request, profile: dict[str, Any] = Depends(require_ui_admin_session)
    ) -> HTMLResponse:
        form = await request.form()
        bucket_value = str(form.get("managed_storage_bucket") or "").strip()
        bucket_form = {"managed_storage_bucket": bucket_value}
        try:
            config_path, normalized_bucket = persist_managed_storage_bucket(bucket_value)
        except Exception as exc:
            return _admin_page_response(
                request,
                profile=profile,
                artifact_bucket_form=bucket_form,
                artifact_bucket_status={"state": "error", "detail": str(exc)},
                status_code=400,
            )

        settings.managed_storage_bucket = normalized_bucket
        app.state.settings = settings
        setattr(service, "managed_storage_bucket", normalized_bucket)
        return _admin_page_response(
            request,
            profile=profile,
            artifact_bucket_form={"managed_storage_bucket": normalized_bucket},
            artifact_bucket_status={
                "state": "ok",
                "detail": f"Managed artifact bucket updated in {config_path}.",
            },
        )

    @app.get("/ui/observability", include_in_schema=False)
    async def observability_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        obs_projection, obs_snapshot = app.state.observability.obs_services_snapshot()
        api_projection, api_families = app.state.observability.api_health()
        endpoint_projection, endpoint_page = app.state.observability.endpoint_health(
            offset=0,
            limit=25,
        )
        db_projection, db_payload = app.state.observability.db_health()
        auth_projection, auth_payload = app.state.observability.auth_health()
        return templates.TemplateResponse(
            request,
            "observability.html",
            _template_context(
                profile=profile,
                obs_services_payload=build_obs_services_payload(
                    request,
                    projection=obs_projection,
                    snapshot=obs_snapshot,
                ),
                api_health_payload=build_api_health_payload(
                    request,
                    projection=api_projection,
                    families=api_families,
                ),
                anomalies=service.list_anomalies(limit=25),
                endpoint_health_payload=build_endpoint_health_payload(
                    request,
                    projection=endpoint_projection,
                    total=int(endpoint_page["total"]),
                    offset=int(endpoint_page["offset"]),
                    limit=int(endpoint_page["limit"]),
                    items=list(endpoint_page["items"]),
                ),
                db_health_payload=build_db_health_payload(
                    request,
                    projection=db_projection,
                    db_health=db_payload,
                ),
                auth_health_payload=build_auth_health_payload(
                    request,
                    projection=auth_projection,
                    auth_rollup=auth_payload,
                ),
            ),
        )

    @app.get("/literature", include_in_schema=False)
    async def literature_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        viewer = _viewer_context(profile)
        query = str(request.query_params.get("q") or "").strip()
        page = int(request.query_params.get("page") or 1)
        page_size = int(request.query_params.get("page_size") or 20)
        result = {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "has_more": False,
            "timing_ms": 0,
        }
        if query:
            result = service.search_literature(
                viewer=viewer,
                query=query,
                page=page,
                page_size=page_size,
            )
        elif service.literature is None:
            raise LiteratureUnavailableError(
                "Literature endpoints require metapub to be installed in the Dewey environment."
            )
        return templates.TemplateResponse(
            request,
            "literature.html",
            _template_context(
                profile=profile,
                query=query,
                result=result,
                page_size=page_size,
                is_admin=_is_admin(profile),
            ),
        )

    @app.get("/search", include_in_schema=False)
    async def search_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = _search_form_payload(request)
        result = service.query_search_v2(form, viewer_context=_viewer_context(profile))
        return templates.TemplateResponse(
            request,
            "search.html",
            _template_context(
                profile=profile,
                form=form,
                result=result,
                export_payload_json=json.dumps(form),
                is_admin=_is_admin(profile),
            ),
        )

    @app.get("/search/export", include_in_schema=False)
    async def search_export_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> Response:
        payload = _search_form_payload(request)
        export_format = str(request.query_params.get("format") or "json").strip().lower() or "json"
        payload["format"] = export_format
        if request.query_params.get("max_rows"):
            payload["max_rows"] = int(request.query_params["max_rows"])
        items, timing_ms, truncated = service.collect_search_export_rows(
            payload,
            viewer_context=_viewer_context(profile),
        )
        if export_format == "json":
            return JSONResponse(
                content={
                    "items": items,
                    "row_count": len(items),
                    "timing_ms": timing_ms,
                    "truncated": truncated,
                }
            )
        return Response(
            content=_search_payload_to_tsv(items),
            media_type="text/tab-separated-values",
            headers={
                "Content-Disposition": 'attachment; filename="dewey_search_v2.tsv"',
                "X-Row-Count": str(len(items)),
                "X-Truncated": str(truncated).lower(),
                "X-Timing-Ms": str(timing_ms),
            },
        )

    @app.get("/artifacts", include_in_schema=False)
    async def artifacts_page(
        request: Request,
        section: str | None = Query(default=None),
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> HTMLResponse:
        return _artifact_page_response(
            request,
            profile=profile,
            active_section=_normalize_artifact_section(section),
        )

    @app.get("/artifacts/dag", include_in_schema=False)
    async def artifact_dag_page(
        request: Request,
        artifact_euid: str | None = Query(default=None),
        root_uri: str | None = Query(default=None),
        browse_limit: int = Query(default=200, ge=1, le=1000),
        continuation_token: str | None = Query(default=None),
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> HTMLResponse:
        browse_root_uri = str(root_uri or "").strip()
        browse_result: dict[str, Any] | None = None
        graph_result: dict[str, Any] | None = None
        selected_artifact: dict[str, Any] | None = None
        dag_message: dict[str, Any] | None = None
        response_status = 200

        try:
            if artifact_euid:
                selected_artifact = service.get_artifact(artifact_euid)
                if not browse_root_uri:
                    browse_root_uri = _browse_root_for_artifact(selected_artifact)
                graph_result = service.get_artifact_graph(artifact_euid=artifact_euid, depth=4)

            browse_root_uri = browse_root_uri or _default_browse_root_uri()
            if browse_root_uri:
                browse_result = service.browse_storage_prefix(
                    root_uri=browse_root_uri,
                    limit=browse_limit,
                    continuation_token=continuation_token,
                )
                if graph_result is None and browse_result.get("current_artifact"):
                    selected_artifact = browse_result["current_artifact"]
                    graph_result = service.get_artifact_graph(
                        artifact_euid=selected_artifact["artifact_euid"],
                        depth=4,
                    )
        except Exception as exc:
            dag_message = {"state": "error", "detail": str(exc)}
            response_status = 400

        return _artifact_dag_response(
            request,
            profile=profile,
            browse_root_uri=browse_root_uri,
            browse_limit=browse_limit,
            browse_result=browse_result,
            graph_result=graph_result,
            selected_artifact=selected_artifact,
            dag_message=dag_message,
            continuation_token=continuation_token,
            status_code=response_status,
        )

    @app.get("/artifacts/euid/{artifact_euid}", include_in_schema=False)
    async def artifact_detail_page(
        request: Request,
        artifact_euid: str,
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> HTMLResponse:
        artifact = service.get_artifact(artifact_euid)
        return _artifact_detail_response(request, profile=profile, artifact=artifact)

    @app.get("/artifacts/bulk-template.tsv", include_in_schema=False)
    async def artifacts_bulk_template(
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> Response:
        _ = profile
        return Response(
            content=bulk_template_tsv(),
            media_type="text/tab-separated-values",
            headers={
                "Content-Disposition": 'attachment; filename="dewey_artifacts_bulk_template.tsv"'
            },
        )

    @app.post("/artifacts/register", include_in_schema=False)
    async def artifacts_register(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form(max_files=1105)
        values = _string_form_values(form)
        requested_artifact_type = str(values.get("artifact_type") or "").strip().lower()

        metadata = collect_metadata(
            values,
            fields=_artifact_metadata_fields(),
            prefix="artifact_meta",
            extra_json_field="artifact_additional_metadata_json",
        )
        producer_system = str(values.get("producer_system") or "").strip() or None
        producer_object_euid = str(values.get("producer_object_euid") or "").strip() or None
        lock_after_import = str(values.get("lock_after_import") or "").strip().lower() == "yes"

        artifact_set_payload: dict[str, Any] | None = None
        artifact_set_euid = ""
        grouping_mode = str(values.get("grouping_mode") or "none").strip().lower() or "none"
        if grouping_mode == "use_existing":
            artifact_set_euid = str(values.get("existing_artifact_set_euid") or "").strip()
            if not artifact_set_euid:
                return _artifact_page_response(
                    request,
                    profile=profile,
                    artifact_form=values,
                    register_report=[
                        {
                            "status": "error",
                            "detail": "existing_artifact_set_euid is required when using an existing set",
                        }
                    ],
                    active_section="register",
                )
            artifact_set_payload = service.get_artifact_set(artifact_set_euid)
        elif grouping_mode == "create":
            artifact_set_metadata = collect_metadata(
                values,
                fields=_artifact_set_metadata_fields(),
                prefix="artifact_set_meta",
                extra_json_field="artifact_set_additional_metadata_json",
            )
            _, artifact_set_payload = service.create_artifact_set(
                artifact_set_type=str(values.get("artifact_set_type") or "batch").strip().lower()
                or "batch",
                label=str(values.get("artifact_set_label") or "").strip() or None,
                description=str(values.get("artifact_set_description") or "").strip() or None,
                metadata=artifact_set_metadata,
                idempotency_key=_new_idempotency_key("ui-artifact-set"),
            )
            artifact_set_euid = artifact_set_payload["artifact_set_euid"]

        results: list[dict[str, Any]] = []

        def _remember_result(source: str, payload: dict[str, Any]) -> None:
            results.append(
                {
                    "status": "success",
                    "source": source,
                    "artifact_euid": payload["artifact_euid"],
                    "storage_uri": payload.get("storage_uri"),
                    "artifact_set_euid": artifact_set_euid or None,
                    "detail": payload.get("import_mode") or "register",
                }
            )

        async def _upload_local_file(source_label: str, upload: UploadFile) -> None:
            nonlocal artifact_set_payload
            file_name = Path(str(upload.filename or "").strip() or "upload.bin").name
            payload_code, payload = service.upload_artifact_bytes(
                artifact_type=resolve_artifact_type(requested_artifact_type, file_name),
                original_filename=file_name,
                body=await upload.read(),
                content_type=str(upload.content_type or "").strip() or None,
                producer_system=producer_system,
                producer_object_euid=producer_object_euid,
                metadata=metadata,
                lock_after_import=lock_after_import,
                idempotency_key=_new_idempotency_key("ui-upload"),
            )
            _ = payload_code
            if artifact_set_euid:
                _, artifact_set_payload = service.add_artifact_set_member(
                    artifact_set_euid=artifact_set_euid,
                    artifact_euid=payload["artifact_euid"],
                    idempotency_key=_new_idempotency_key("ui-artifact-set-member"),
                )
            _remember_result(source_label, payload)

        try:
            local_files = [
                item for item in form.getlist("file_data") if isinstance(item, StarletteUploadFile)
            ]
            for item in local_files:
                if str(item.filename or "").strip():
                    await _upload_local_file(str(item.filename), item)

            directory_files = [
                item
                for item in form.getlist("directory_data")
                if isinstance(item, StarletteUploadFile)
            ]
            directory_files = [
                item
                for item in directory_files
                if not Path(str(item.filename or "")).name.startswith(".")
            ]
            if len(directory_files) > 1000:
                return _artifact_page_response(
                    request,
                    profile=profile,
                    artifact_form=values,
                    register_report=[
                        {
                            "status": "error",
                            "detail": "Too many directory files. Maximum is 1000.",
                        }
                    ],
                    active_section="register",
                )
            for item in directory_files:
                if str(item.filename or "").strip():
                    await _upload_local_file(str(item.filename), item)

            for source_uri in split_lines(values.get("url_sources")):
                _, payload = service.import_artifact_from_uri(
                    artifact_type=resolve_artifact_type(requested_artifact_type, source_uri),
                    source_uri=source_uri,
                    import_mode="copy",
                    lock_after_import=lock_after_import,
                    producer_system=producer_system,
                    producer_object_euid=producer_object_euid,
                    metadata=metadata,
                    idempotency_key=_new_idempotency_key("ui-url-import"),
                )
                if artifact_set_euid:
                    _, artifact_set_payload = service.add_artifact_set_member(
                        artifact_set_euid=artifact_set_euid,
                        artifact_euid=payload["artifact_euid"],
                        idempotency_key=_new_idempotency_key("ui-artifact-set-member"),
                    )
                _remember_result(source_uri, payload)

            s3_mode = str(values.get("s3_mode") or "reference").strip().lower() or "reference"
            for source_uri in split_lines(values.get("s3_sources")):
                expanded_sources = service.expand_s3_sources(source_uri)
                for expanded_source in expanded_sources:
                    if s3_mode == "register":
                        parsed = expanded_source.removeprefix("s3://")
                        bucket, key = parsed.split("/", 1)
                        _, payload = service.register_artifact(
                            artifact_type=resolve_artifact_type(
                                requested_artifact_type,
                                key,
                                expanded_source,
                            ),
                            storage_backend="s3",
                            bucket=bucket,
                            key=key,
                            version_id=None,
                            size=None,
                            checksums={},
                            content_type=None,
                            original_filename=Path(key).name,
                            producer_system=producer_system,
                            producer_object_euid=producer_object_euid,
                            storage_class=None,
                            availability_status="available",
                            metadata=metadata,
                            idempotency_key=_new_idempotency_key("ui-s3-register"),
                        )
                    else:
                        _, payload = service.import_artifact_from_uri(
                            artifact_type=resolve_artifact_type(
                                requested_artifact_type,
                                expanded_source,
                            ),
                            source_uri=expanded_source,
                            import_mode=s3_mode,
                            lock_after_import=lock_after_import,
                            producer_system=producer_system,
                            producer_object_euid=producer_object_euid,
                            metadata=metadata,
                            idempotency_key=_new_idempotency_key("ui-s3-import"),
                        )
                    if artifact_set_euid:
                        _, artifact_set_payload = service.add_artifact_set_member(
                            artifact_set_euid=artifact_set_euid,
                            artifact_euid=payload["artifact_euid"],
                            idempotency_key=_new_idempotency_key("ui-artifact-set-member"),
                        )
                    _remember_result(expanded_source, payload)
        except Exception as exc:
            results.append({"status": "error", "detail": str(exc), "source": "register"})

        return _artifact_page_response(
            request,
            profile=profile,
            artifact_form=values,
            register_report=results,
            artifact_set_create_result=artifact_set_payload,
            active_section="register",
        )

    @app.post("/artifacts/bulk-upload", include_in_schema=False)
    async def artifacts_bulk_upload(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form(max_files=32)
        file = form.get("bulk_tsv")
        if not isinstance(file, StarletteUploadFile) or not str(file.filename or "").strip():
            return _artifact_page_response(
                request,
                profile=profile,
                bulk_report=[
                    {"row_number": 0, "status": "error", "detail": "bulk_tsv is required"}
                ],
                active_section="register",
            )
        text = (await file.read()).decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
        results: list[dict[str, Any]] = []
        artifact_set_cache: dict[tuple[str, str, str, str], str] = {}
        for index, row in enumerate(reader, start=2):
            metadata: dict[str, Any] = {}
            for field in _artifact_metadata_fields():
                key = field["name"]
                value = row.get(key)
                if value:
                    parsed_value = (
                        parse_json_object(value, label=key)
                        if key == "additional_metadata_json"
                        else None
                    )
                    if parsed_value is not None:
                        metadata.update(parsed_value)
                    else:
                        metadata.update(
                            collect_metadata(
                                {f"bulk_{key}": value},
                                fields=[field],
                                prefix="bulk",
                                extra_json_field="unused_bulk_json",
                            )
                        )
            try:
                source_mode = str(row.get("source_mode") or "").strip().lower()
                artifact_type = str(row.get("artifact_type") or "").strip().lower()
                source_uri = str(row.get("source_uri") or "").strip()
                if source_mode == "register":
                    bucket = str(row.get("bucket") or "").strip()
                    key = str(row.get("key") or "").strip()
                    if not bucket or not key:
                        if source_uri.startswith("s3://"):
                            trimmed = source_uri.removeprefix("s3://")
                            bucket, key = trimmed.split("/", 1)
                        else:
                            raise ValueError("register rows require bucket/key or s3 source_uri")
                    _, payload = service.register_artifact(
                        artifact_type=resolve_artifact_type(
                            artifact_type,
                            str(row.get("original_filename") or "").strip() or None,
                            key,
                            source_uri,
                        ),
                        storage_backend="s3",
                        bucket=bucket,
                        key=key,
                        version_id=None,
                        size=None,
                        checksums={},
                        content_type=None,
                        original_filename=str(row.get("original_filename") or "").strip()
                        or Path(key).name,
                        producer_system=str(row.get("producer_system") or "").strip() or None,
                        producer_object_euid=str(row.get("producer_object_euid") or "").strip()
                        or None,
                        storage_class=None,
                        availability_status="available",
                        metadata=metadata,
                        idempotency_key=_new_idempotency_key("ui-bulk-register"),
                    )
                elif source_mode in {"reference", "copy"}:
                    if not source_uri:
                        raise ValueError("reference/copy rows require source_uri")
                    _, payload = service.import_artifact_from_uri(
                        artifact_type=resolve_artifact_type(
                            artifact_type,
                            str(row.get("original_filename") or "").strip() or None,
                            source_uri,
                        ),
                        source_uri=source_uri,
                        import_mode=source_mode,
                        lock_after_import=False,
                        producer_system=str(row.get("producer_system") or "").strip() or None,
                        producer_object_euid=str(row.get("producer_object_euid") or "").strip()
                        or None,
                        metadata=metadata,
                        idempotency_key=_new_idempotency_key("ui-bulk-import"),
                    )
                else:
                    raise ValueError("source_mode must be register, reference, or copy")

                set_label = str(row.get("artifact_set_label") or "").strip()
                if set_label:
                    set_type = (
                        str(row.get("artifact_set_type") or "batch").strip().lower() or "batch"
                    )
                    set_description = str(row.get("artifact_set_description") or "").strip()
                    cache_key = (
                        set_type,
                        set_label,
                        set_description,
                        json.dumps({}, sort_keys=True),
                    )
                    artifact_set_euid = artifact_set_cache.get(cache_key)
                    if not artifact_set_euid:
                        _, artifact_set = service.create_artifact_set(
                            artifact_set_type=set_type,
                            label=set_label,
                            description=set_description or None,
                            metadata={},
                            idempotency_key=_new_idempotency_key("ui-bulk-set"),
                        )
                        artifact_set_euid = artifact_set["artifact_set_euid"]
                        artifact_set_cache[cache_key] = artifact_set_euid
                    service.add_artifact_set_member(
                        artifact_set_euid=artifact_set_euid,
                        artifact_euid=payload["artifact_euid"],
                        idempotency_key=_new_idempotency_key("ui-bulk-set-member"),
                    )
                results.append(
                    {
                        "row_number": index,
                        "status": "success",
                        "artifact_euid": payload["artifact_euid"],
                        "storage_uri": payload.get("storage_uri"),
                    }
                )
            except Exception as exc:
                results.append({"row_number": index, "status": "error", "detail": str(exc)})
        return _artifact_page_response(
            request,
            profile=profile,
            bulk_report=results,
            active_section="register",
        )

    @app.post("/artifacts/import-run-prefix", include_in_schema=False)
    async def artifacts_import_run_prefix(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        values = _string_form_values(form)
        run_prefix_form = {
            "root_uri": str(values.get("root_uri") or "").strip(),
            "platform": str(values.get("platform") or "ultima").strip().lower() or "ultima",
            "owner_email": str(values.get("owner_email") or "").strip().lower(),
            "run_id": str(values.get("run_id") or "").strip(),
            "finalize": (
                "yes"
                if str(values.get("finalize") or "").strip().lower() in {"yes", "on", "true", "1"}
                else "no"
            ),
        }
        try:
            _, payload = service.import_run_prefix(
                root_uri=run_prefix_form["root_uri"],
                platform=run_prefix_form["platform"],
                owner_email=run_prefix_form["owner_email"],
                run_id=run_prefix_form["run_id"] or None,
                finalize=run_prefix_form["finalize"] == "yes",
                idempotency_key=_new_idempotency_key("ui-run-prefix-import"),
            )
            return _artifact_page_response(
                request,
                profile=profile,
                run_prefix_form=run_prefix_form,
                run_prefix_result=payload,
                active_section="register",
            )
        except Exception as exc:
            return _artifact_page_response(
                request,
                profile=profile,
                run_prefix_form=run_prefix_form,
                run_prefix_result={"state": "error", "detail": str(exc)},
                active_section="register",
            )

    @app.post("/artifacts/search", include_in_schema=False)
    async def artifacts_search(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        values = _string_form_values(form)
        result = service.query_search_v2(
            _artifact_search_payload(values),
            viewer_context=_viewer_context(profile),
        )
        return _artifact_page_response(
            request,
            profile=profile,
            artifact_search_form=values,
            artifact_search_result=result,
            active_section="search",
        )

    @app.post("/artifacts/search/export", include_in_schema=False)
    async def artifacts_search_export(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> Response:
        form = await request.form()
        values = _string_form_values(form)
        payload = _artifact_search_payload(values)
        export_format = str(values.get("format") or "tsv").strip().lower() or "tsv"
        payload["format"] = export_format
        payload["max_rows"] = int(values.get("max_rows") or 1000)
        items, timing_ms, truncated = service.collect_search_export_rows(
            payload,
            viewer_context=_viewer_context(profile),
        )
        if export_format == "json":
            return JSONResponse(
                {
                    "items": items,
                    "row_count": len(items),
                    "timing_ms": timing_ms,
                    "truncated": truncated,
                }
            )
        return Response(
            content=_search_payload_to_tsv(items),
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": 'attachment; filename="dewey_artifact_search.tsv"'},
        )

    @app.post("/artifacts/download", include_in_schema=False)
    async def artifacts_download(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> Response:
        _ = profile
        form = await request.form()
        artifact_euids = [
            str(item).strip() for item in form.getlist("artifact_euids") if str(item).strip()
        ]
        archive_name, archive_bytes = service.build_artifact_download_archive(
            artifact_euids=artifact_euids,
            naming_mode=str(form.get("download_naming_mode") or "hybrid"),
            include_metadata=str(form.get("download_include_metadata") or "yes").strip().lower()
            == "yes",
        )
        return Response(
            content=archive_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
        )

    @app.post("/artifacts/euid/{artifact_euid}/download", include_in_schema=False)
    async def artifact_download_redirect(
        request: Request,
        artifact_euid: str,
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> Response:
        artifact = service.get_artifact(artifact_euid)
        form = await request.form()
        ttl_hours = max(1, int(form.get("share_ttl_hours") or 24))
        try:
            _, payload = service.create_share_reference(
                target_type="artifact",
                target_euid=artifact_euid,
                purpose="download",
                scope="external",
                expires_at=None,
                issued_by=str(profile.get("email") or "").strip() or None,
                transport="presigned_s3",
                transport_config={},
                ttl_seconds=ttl_hours * 3600,
                idempotency_key=_new_idempotency_key("ui-artifact-direct-download"),
            )
        except Exception as exc:
            return _artifact_detail_response(
                request,
                profile=profile,
                artifact=artifact,
                detail_message={"state": "error", "detail": str(exc)},
                status_code=400,
            )
        access_url = str(payload.get("access_url") or "").strip()
        if not access_url:
            return _artifact_detail_response(
                request,
                profile=profile,
                artifact=artifact,
                detail_message={
                    "state": "error",
                    "detail": "Could not generate a presigned download URL for this artifact.",
                },
                status_code=400,
            )
        return RedirectResponse(url=access_url, status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/artifacts/share", include_in_schema=False)
    async def artifacts_share(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        artifact_euids = [
            str(item).strip() for item in form.getlist("artifact_euids") if str(item).strip()
        ]
        ttl_hours = max(1, int(form.get("share_ttl_hours") or 24))
        share_rows: list[dict[str, Any]] = []
        for artifact_euid in artifact_euids:
            _, payload = service.create_share_reference(
                target_type="artifact",
                target_euid=artifact_euid,
                purpose="download",
                scope="external",
                expires_at=None,
                issued_by=str(profile.get("email") or "").strip() or None,
                transport="presigned_s3",
                transport_config={},
                ttl_seconds=ttl_hours * 3600,
                idempotency_key=_new_idempotency_key("ui-artifact-share"),
            )
            share_rows.append(payload)
        search_form, search_result = _rerun_artifact_search(
            _parse_state_json(form.get("artifact_search_form_state")),
            profile=profile,
        )
        return _artifact_page_response(
            request,
            profile=profile,
            artifact_search_form=search_form,
            artifact_search_result=search_result,
            artifact_share_results=share_rows,
            active_section="search",
        )

    @app.post("/artifacts/sets/create", include_in_schema=False)
    async def artifacts_set_create(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        values = _string_form_values(form)
        metadata = collect_metadata(
            values,
            fields=_artifact_set_metadata_fields(),
            prefix="artifact_set_meta",
            extra_json_field="artifact_set_additional_metadata_json",
        )
        _, artifact_set = service.create_artifact_set(
            artifact_set_type=str(values.get("artifact_set_type") or "collection").strip().lower()
            or "collection",
            label=str(values.get("artifact_set_label") or "").strip() or None,
            description=str(values.get("artifact_set_description") or "").strip() or None,
            metadata=metadata,
            idempotency_key=_new_idempotency_key("ui-set-create"),
        )
        artifact_set_euid = artifact_set["artifact_set_euid"]
        for artifact_euid in [
            str(item).strip() for item in form.getlist("artifact_euids") if str(item).strip()
        ]:
            _, artifact_set = service.add_artifact_set_member(
                artifact_set_euid=artifact_set_euid,
                artifact_euid=artifact_euid,
                idempotency_key=_new_idempotency_key("ui-set-member"),
            )
        artifact_search_form, artifact_search_result = _rerun_artifact_search(
            _parse_state_json(form.get("artifact_search_form_state")),
            profile=profile,
        )
        artifact_set_search_form, artifact_set_search_result = _rerun_artifact_set_search(
            _parse_state_json(form.get("artifact_set_search_form_state")),
            profile=profile,
        )
        return _artifact_page_response(
            request,
            profile=profile,
            artifact_search_form=artifact_search_form,
            artifact_search_result=artifact_search_result,
            artifact_set_search_form=artifact_set_search_form,
            artifact_set_search_result=artifact_set_search_result,
            artifact_set_create_result=artifact_set,
            artifact_set_form=values,
            active_section="artifact_sets",
        )

    @app.post("/artifacts/sets/search", include_in_schema=False)
    async def artifacts_set_search(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        values = _string_form_values(form)
        result = service.query_search_v2(
            _artifact_set_search_payload(values),
            viewer_context=_viewer_context(profile),
        )
        return _artifact_page_response(
            request,
            profile=profile,
            artifact_set_search_form=values,
            artifact_set_search_result=result,
            active_section="artifact_sets",
        )

    @app.post("/artifacts/sets/export", include_in_schema=False)
    async def artifacts_set_export(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> Response:
        form = await request.form()
        values = _string_form_values(form)
        payload = _artifact_set_search_payload(values)
        export_format = str(values.get("format") or "tsv").strip().lower() or "tsv"
        payload["format"] = export_format
        payload["max_rows"] = int(values.get("max_rows") or 1000)
        items, timing_ms, truncated = service.collect_search_export_rows(
            payload,
            viewer_context=_viewer_context(profile),
        )
        if export_format == "json":
            return JSONResponse(
                {
                    "items": items,
                    "row_count": len(items),
                    "timing_ms": timing_ms,
                    "truncated": truncated,
                }
            )
        return Response(
            content=_search_payload_to_tsv(items),
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": 'attachment; filename="dewey_artifact_sets.tsv"'},
        )

    @app.post("/artifacts/sets/share", include_in_schema=False)
    async def artifacts_set_share(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = await request.form()
        artifact_set_euid = str(form.get("selected_artifact_set_euid") or "").strip()
        if not artifact_set_euid:
            return _artifact_page_response(
                request,
                profile=profile,
                artifact_set_share_result={"status": "error", "detail": "No artifact set selected"},
                active_section="artifact_sets",
            )
        duration_days = max(1.0, float(form.get("share_duration_days") or 1))
        expires_at = (
            (datetime.now(timezone.utc) + timedelta(days=duration_days))
            .isoformat()
            .replace("+00:00", "Z")
        )
        transport = str(form.get("share_transport") or "presigned_s3").strip().lower()
        _, payload = service.create_share_reference(
            target_type="artifact_set",
            target_euid=artifact_set_euid,
            purpose="artifact-set-share",
            scope="external",
            expires_at=expires_at,
            issued_by=str(profile.get("email") or "").strip() or None,
            transport=transport,
            transport_config={
                "bucket": str(form.get("share_bucket") or "").strip() or None,
                "host": str(form.get("share_host") or "").strip() or None,
                "port": int(form.get("share_port") or 0) or None,
                "user": str(form.get("share_user") or "").strip() or None,
                "passwd": str(form.get("share_password") or "").strip() or None,
            },
            ttl_seconds=None,
            idempotency_key=_new_idempotency_key("ui-set-share"),
        )
        artifact_set_search_form, artifact_set_search_result = _rerun_artifact_set_search(
            _parse_state_json(form.get("artifact_set_search_form_state")),
            profile=profile,
        )
        return _artifact_page_response(
            request,
            profile=profile,
            artifact_set_search_form=artifact_set_search_form,
            artifact_set_search_result=artifact_set_search_result,
            artifact_set_share_result=payload,
            active_section="artifact_sets",
        )

    @app.post("/api/v1/literature/search")
    async def literature_search(
        body: LiteratureSearchRequest,
        profile: dict[str, Any] = Depends(require_ui_session),
    ) -> dict[str, Any]:
        try:
            return service.search_literature(
                viewer=_viewer_context(profile),
                query=body.query,
                page=body.page,
                page_size=body.page_size,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/literature/save")
    async def literature_save(
        body: LiteratureSaveRequest,
        profile: dict[str, Any] = Depends(require_ui_session),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.save_literature(
                viewer=_viewer_context(profile),
                pmid=body.pmid,
                save_mode=body.save_mode,
                visibility_scope=body.visibility_scope,
                allowed_users=body.allowed_users,
                allowed_groups=body.allowed_groups,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/v1/literature/saves/{literature_save_euid}")
    async def literature_save_visibility(
        literature_save_euid: str,
        body: LiteratureSaveVisibilityRequest,
        profile: dict[str, Any] = Depends(require_ui_session),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.update_literature_save_visibility(
                viewer=_viewer_context(profile),
                literature_save_euid=literature_save_euid,
                visibility_scope=body.visibility_scope,
                allowed_users=body.allowed_users,
                allowed_groups=body.allowed_groups,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/literature/saves/mine")
    async def my_literature_saves(
        profile: dict[str, Any] = Depends(require_ui_session),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        rows = service.list_my_literature_saves(
            viewer=_viewer_context(profile),
            limit=limit,
        )
        return {"items": rows, "total": len(rows)}

    @app.get(
        "/api/v1/artifacts/{artifact_euid}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_artifact(artifact_euid: str) -> dict[str, Any]:
        try:
            return service.get_artifact(artifact_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifacts/{artifact_euid}/children",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_artifact_children(
        artifact_euid: str,
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        try:
            rows = service.list_artifact_children(artifact_euid=artifact_euid, limit=limit)
            return {"items": rows, "total": len(rows)}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifacts/{artifact_euid}/parents",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_artifact_parents(
        artifact_euid: str,
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        try:
            rows = service.list_artifact_parents(artifact_euid=artifact_euid, limit=limit)
            return {"items": rows, "total": len(rows)}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/artifacts/{artifact_euid}/graph")
    async def get_artifact_graph(
        artifact_euid: str,
        depth: int = Query(default=3, ge=0, le=6),
        limit: int = Query(default=200, ge=1, le=500),
        _auth: dict[str, Any] = Depends(session_or_api_auth_dep),
    ) -> dict[str, Any]:
        _ = _auth
        try:
            return service.get_artifact_graph(
                artifact_euid=artifact_euid,
                depth=depth,
                limit=limit,
            )
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/storage/browse")
    async def browse_storage_prefix(
        root_uri: str = Query(...),
        limit: int = Query(default=200, ge=1, le=1000),
        continuation_token: str | None = Query(default=None),
        _auth: dict[str, Any] = Depends(session_or_api_auth_dep),
    ) -> dict[str, Any]:
        _ = _auth
        try:
            return service.browse_storage_prefix(
                root_uri=root_uri,
                limit=limit,
                continuation_token=continuation_token,
            )
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifacts/{artifact_euid}/storage/verify",
        dependencies=[Depends(api_auth_dep)],
    )
    async def verify_artifact_storage(
        artifact_euid: str,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.verify_artifact_storage(
                artifact_euid=artifact_euid,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifacts/{artifact_euid}/storage/lock",
        dependencies=[Depends(api_auth_dep)],
    )
    async def lock_artifact_storage(
        artifact_euid: str,
        body: ArtifactStorageLockRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.lock_artifact_storage(
                artifact_euid=artifact_euid,
                mode=body.mode,
                retain_until=body.retain_until,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifacts",
        dependencies=[Depends(api_auth_dep)],
    )
    async def list_artifacts(
        artifact_type: str | None = Query(default=None),
        producer_system: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        rows = service.list_artifacts(
            artifact_type=artifact_type,
            producer_system=producer_system,
            limit=limit,
        )
        return {"items": rows, "total": len(rows)}

    @app.post(
        "/api/v1/artifacts",
        dependencies=[Depends(api_auth_dep)],
    )
    async def register_artifact(
        body: ArtifactRegisterRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.register_artifact(
                artifact_type=body.artifact_type,
                storage_backend=body.storage_backend,
                bucket=body.bucket,
                key=body.key,
                version_id=body.version_id,
                size=body.size,
                checksums=body.checksums,
                content_type=body.content_type,
                original_filename=body.original_filename,
                producer_system=body.producer_system,
                producer_object_euid=body.producer_object_euid,
                storage_class=body.storage_class,
                availability_status=body.availability_status,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifacts/import",
        dependencies=[Depends(api_auth_dep)],
    )
    async def import_artifact(
        body: ArtifactImportRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.import_artifact_from_uri(
                artifact_type=body.artifact_type,
                storage_uri=body.storage_uri,
                source_uri=body.source_uri,
                import_mode=body.import_mode,
                lock_after_import=body.lock_after_import,
                producer_system=body.producer_system,
                producer_object_euid=body.producer_object_euid,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/v1/artifacts/import-run-prefix")
    async def import_run_prefix(
        body: ArtifactRunPrefixImportRequest,
        _auth: dict[str, Any] = Depends(session_or_api_auth_dep),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        _ = _auth
        try:
            status_code, payload = service.import_run_prefix(
                root_uri=body.root_uri,
                platform=body.platform,
                owner_email=body.owner_email,
                run_id=body.run_id,
                finalize=body.finalize,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifacts/upload-sessions",
        dependencies=[Depends(api_auth_dep)],
    )
    async def create_upload_session(
        body: UploadSessionCreateRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.create_upload_session(
                artifact_type=body.artifact_type,
                original_filename=body.original_filename,
                content_type=body.content_type,
                producer_system=body.producer_system,
                producer_object_euid=body.producer_object_euid,
                metadata=body.metadata,
                lock_after_import=body.lock_after_import,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifacts/upload-sessions/{upload_token}/complete",
        dependencies=[Depends(api_auth_dep)],
    )
    async def complete_upload_session(
        upload_token: str,
        body: UploadSessionCompleteRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.complete_upload_session(
                upload_token=upload_token or body.upload_token,
                checksums=body.checksums,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifact-sets/{artifact_set_euid}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_artifact_set(artifact_set_euid: str) -> dict[str, Any]:
        try:
            return service.get_artifact_set(artifact_set_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifact-sets",
        dependencies=[Depends(api_auth_dep)],
    )
    async def list_artifact_sets(
        artifact_set_type: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        rows = service.list_artifact_sets(
            artifact_set_type=artifact_set_type,
            limit=limit,
        )
        return {"items": rows, "total": len(rows)}

    @app.post(
        "/api/v1/artifact-sets",
        dependencies=[Depends(api_auth_dep)],
    )
    async def create_artifact_set(
        body: ArtifactSetCreateRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.create_artifact_set(
                artifact_set_type=body.artifact_set_type,
                label=body.label,
                description=body.description,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/artifact-sets/{artifact_set_euid}/members",
        dependencies=[Depends(api_auth_dep)],
    )
    async def add_artifact_set_member(
        artifact_set_euid: str,
        body: ArtifactSetMemberRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.add_artifact_set_member(
                artifact_set_euid=artifact_set_euid,
                artifact_euid=body.artifact_euid,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete(
        "/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def remove_artifact_set_member(
        artifact_set_euid: str,
        artifact_euid: str,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.remove_artifact_set_member(
                artifact_set_euid=artifact_set_euid,
                artifact_euid=artifact_euid,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/resolve/artifact",
        dependencies=[Depends(api_auth_dep)],
    )
    async def resolve_artifact(body: ResolveArtifactRequest) -> dict[str, Any]:
        try:
            return service.resolve_artifact(body.artifact_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/api/v1/resolve/artifact-set",
        dependencies=[Depends(api_auth_dep)],
    )
    async def resolve_artifact_set(body: ResolveArtifactSetRequest) -> dict[str, Any]:
        try:
            return service.resolve_artifact_set(body.artifact_set_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/api/v1/share-references",
        dependencies=[Depends(api_auth_dep)],
    )
    async def create_share_reference(
        body: ShareReferenceCreateRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.create_share_reference(
                target_type=body.target_type,
                target_euid=body.target_euid,
                purpose=body.purpose,
                scope=body.scope,
                expires_at=body.expires_at,
                issued_by=body.issued_by,
                transport=body.transport,
                transport_config=body.transport_config,
                ttl_seconds=body.ttl_seconds,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(
        "/api/v1/share-references/{share_reference_euid}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_share_reference(share_reference_euid: str) -> dict[str, Any]:
        try:
            return service.get_share_reference(share_reference_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(
        "/api/v1/artifacts/{artifact_euid}/share-references",
        dependencies=[Depends(api_auth_dep)],
    )
    async def list_artifact_share_references(
        artifact_euid: str,
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        try:
            rows = service.list_share_references(
                target_type="artifact",
                target_euid=artifact_euid,
                limit=limit,
            )
            return {"items": rows, "total": len(rows)}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/search/v2/query",
        dependencies=[Depends(api_auth_dep)],
    )
    async def search_v2_query(body: SearchQueryRequest) -> dict[str, Any]:
        try:
            return service.query_search_v2(body.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/search/v2/query",
        dependencies=[Depends(api_auth_dep)],
    )
    async def search_v2_query_alias(body: SearchQueryRequest) -> Response:
        try:
            response = JSONResponse(content=service.query_search_v2(body.model_dump()))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        _with_search_alias_headers(response, "/api/search/v2/query")
        return response

    @app.post(
        "/api/search/v2/export",
        dependencies=[Depends(api_auth_dep)],
    )
    async def search_v2_export(body: SearchExportRequest) -> Response:
        try:
            items, timing_ms, truncated = service.collect_search_export_rows(body.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.format == "json":
            return JSONResponse(
                content={
                    "items": items,
                    "row_count": len(items),
                    "timing_ms": timing_ms,
                    "truncated": truncated,
                }
            )
        return Response(
            content=_search_payload_to_tsv(items),
            media_type="text/tab-separated-values",
            headers={
                "Content-Disposition": 'attachment; filename="dewey_search_v2.tsv"',
                "X-Row-Count": str(len(items)),
                "X-Truncated": str(truncated).lower(),
                "X-Timing-Ms": str(timing_ms),
            },
        )

    @app.post(
        "/api/v1/search/v2/export",
        dependencies=[Depends(api_auth_dep)],
    )
    async def search_v2_export_alias(body: SearchExportRequest) -> Response:
        response = await search_v2_export(body)
        _with_search_alias_headers(response, "/api/search/v2/export")
        return response

    @app.post(
        "/api/v1/external-objects",
        dependencies=[Depends(api_auth_dep)],
    )
    async def create_external_object(
        body: ExternalObjectCreateRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.create_external_object(
                external_system=body.external_system,
                external_object_type=body.external_object_type,
                external_object_id=body.external_object_id,
                external_uri=body.external_uri,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/external-object-relations",
        dependencies=[Depends(api_auth_dep)],
    )
    async def attach_external_object_relation(
        body: ExternalObjectRelationCreateRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            status_code, payload = service.attach_external_object_relation(
                target_type=body.target_type,
                target_euid=body.target_euid,
                external_object_euid=body.external_object_euid,
                relation_type=body.relation_type,
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/api/v1/{target_type}/{target_euid}/external-object-relations",
        dependencies=[Depends(api_auth_dep)],
    )
    async def list_external_object_relations(
        target_type: str,
        target_euid: str,
        limit: int = Query(default=200, ge=1, le=2000),
    ) -> dict[str, Any]:
        try:
            rows = service.list_external_object_relations(
                target_type=target_type,
                target_euid=target_euid,
                limit=limit,
            )
            return {"items": rows, "total": len(rows)}
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app
