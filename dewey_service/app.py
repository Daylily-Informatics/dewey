"""FastAPI app for Dewey canonical artifact service."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from dewey_service.auth import (
    AuthError,
    build_cognito_login_url,
    build_cognito_logout_url,
    decode_jwt_claims_noverify,
    exchange_code,
    generate_state,
    require_api_auth,
    require_ui_session,
)
from dewey_service.domain_access import (
    build_allowed_origin_regex,
    build_trusted_hosts,
    is_allowed_origin,
)
from dewey_service.storage import S3StorageClient
from dewey_service.service import DeweyConflictError, DeweyNotFoundError, DeweyService
from dewey_service.settings import Settings, get_settings
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
    transport: str = Field(default="presigned_s3", pattern="^(presigned_s3)$")
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
        service = DeweyService(
            backend,
            default_share_ttl_seconds=settings.default_share_reference_ttl_seconds,
            storage_client=storage_client,
            managed_storage_bucket=settings.managed_storage_bucket,
            managed_storage_prefix=settings.managed_storage_prefix,
            upload_session_ttl_seconds=settings.upload_session_ttl_seconds,
            upload_token_secret=settings.session_secret_key,
            search_export_max_rows=settings.search_export_max_rows,
        )
        service.bootstrap()

    app = FastAPI(
        title="Dewey Artifact Service",
        version="1.0.0",
        description="Canonical artifact registry and resolver for LSMC",
    )
    app.state.settings = settings
    app.state.service = service
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
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

    templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    api_auth_dep = require_api_auth(settings)

    def _template_context(**kwargs: Any) -> dict[str, Any]:
        context = {
            "deployment": settings.deployment,
        }
        context.update(kwargs)
        return context

    def _with_search_alias_headers(response: Response, successor: str) -> None:
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Wed, 30 Sep 2026 00:00:00 GMT"
        response.headers["Link"] = f"<{successor}>; rel=\"successor-version\""

    def _search_payload_to_tsv(items: list[dict[str, Any]]) -> str:
        fields = [
            "record_type",
            "source_kind",
            "euid",
            "name",
            "created_at",
            "modified_at",
            "artifact_type",
            "producer_system",
            "storage_backend",
            "storage_uri",
            "availability_status",
            "import_mode",
            "target_type",
            "target_euid",
            "transport",
            "status",
            "expires_at",
            "metadata",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for item in items:
            row = dict(item)
            row["metadata"] = json.dumps(item.get("metadata") or {}, sort_keys=True, default=str)
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

    @app.middleware("http")
    async def _enforce_origin_allowlist(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and not is_allowed_origin(origin, allow_local=allow_local_domain_access):
            return HTMLResponse(status_code=403, content="Origin not allowed")
        return await call_next(request)

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

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        """Redirect unauthenticated browser requests to the login page."""
        if exc.status_code == 401:
            accept = request.headers.get("accept", "")
            if "text/html" in accept and not request.url.path.startswith("/api/"):
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail or ""})
        return HTMLResponse(status_code=exc.status_code, content=exc.detail or "")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/ui", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> RedirectResponse:
        return RedirectResponse(url="/static/favicon.svg", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/auth/login", include_in_schema=False)
    async def auth_login(request: Request) -> RedirectResponse:
        state = generate_state()
        request.session["oauth_state"] = state
        url = build_cognito_login_url(settings=settings, state=state)
        return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/auth/callback", include_in_schema=False)
    async def auth_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
        expected_state = str(request.session.get("oauth_state") or "").strip()
        if not code.strip():
            raise HTTPException(status_code=400, detail="Missing authorization code")
        if not state.strip() or expected_state != state.strip():
            raise HTTPException(status_code=400, detail="Invalid oauth state")

        try:
            token_payload = exchange_code(settings=settings, code=code.strip())
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        id_token = str(token_payload.get("id_token") or "").strip()
        claims = decode_jwt_claims_noverify(id_token)
        email = str(claims.get("email") or claims.get("preferred_username") or "").strip()
        sub = str(claims.get("sub") or "").strip()
        groups = claims.get("cognito:groups") or []
        if not email:
            raise HTTPException(status_code=401, detail="Cognito response missing email claim")

        request.session["operator_profile"] = {
            "email": email,
            "sub": sub,
            "groups": groups if isinstance(groups, list) else [],
        }
        request.session.pop("oauth_state", None)
        return RedirectResponse(url="/ui", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/login", include_in_schema=False)
    async def login_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "login.html",
            _template_context(
                cognito_login_url="/auth/login",
                title="Dewey Operator Login",
            ),
        )

    @app.post("/logout", include_in_schema=False)
    async def logout(request: Request) -> RedirectResponse:
        request.session.clear()
        # Generate a fresh OAuth state so the callback can validate CSRF
        # after the user re-authenticates through Cognito managed login.
        state = generate_state()
        request.session["oauth_state"] = state
        logout_url = build_cognito_logout_url(settings=settings, state=state)
        return RedirectResponse(url=logout_url, status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/ui", include_in_schema=False)
    async def ui_home(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
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
            ),
        )

    @app.get("/search", include_in_schema=False)
    async def search_page(
        request: Request, profile: dict[str, Any] = Depends(require_ui_session)
    ) -> HTMLResponse:
        form = _search_form_payload(request)
        result = service.query_search_v2(form)
        return templates.TemplateResponse(
            request,
            "search.html",
            _template_context(
                profile=profile,
                form=form,
                result=result,
                export_payload_json=json.dumps(form),
            ),
        )

    @app.get("/search/export", include_in_schema=False)
    async def search_export_page(
        request: Request, _profile: dict[str, Any] = Depends(require_ui_session)
    ) -> Response:
        payload = _search_form_payload(request)
        export_format = str(request.query_params.get("format") or "json").strip().lower() or "json"
        payload["format"] = export_format
        if request.query_params.get("max_rows"):
            payload["max_rows"] = int(request.query_params["max_rows"])
        items, timing_ms, truncated = service.collect_search_export_rows(payload)
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

    @app.get(
        "/api/v1/artifacts/{artifact_euid}",
        dependencies=[Depends(api_auth_dep)],
    )
    async def get_artifact(artifact_euid: str) -> dict[str, Any]:
        try:
            return service.get_artifact(artifact_euid)
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
