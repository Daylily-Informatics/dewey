"""FastAPI app for Dewey canonical artifact service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
    storage_uri: str
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


def create_app(
    settings: Settings | None = None,
    service: DeweyService | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    allow_local_domain_access = not settings.is_production

    if service is None:
        backend = TapDBBackend(app_username="dewey")
        service = DeweyService(
            backend,
            default_share_ttl_seconds=settings.default_share_reference_ttl_seconds,
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
        artifact_sets = service.list_artifact_sets(limit=100)
        return templates.TemplateResponse(
            request,
            "ui_home.html",
            _template_context(
                profile=profile,
                artifacts=artifacts,
                artifact_sets=artifact_sets,
            ),
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
                metadata=body.metadata,
                idempotency_key=_require_idempotency_key(idempotency_key),
            )
            return {"status_code": status_code, **payload}
        except DeweyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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
