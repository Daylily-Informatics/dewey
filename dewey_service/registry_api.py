"""Public EUID registry and storage operations; every client calls these services."""
from __future__ import annotations

from typing import Any, Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from dewey_service.registry_access import principal
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError


class Registration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["object", "prefix", "set"]
    uri: str | None = None
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    member_euids: list[str] = Field(default_factory=list)
    producer_system: str | None = None
    artifact_type: str | None = None
    version_id: str | None = None


class MetadataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class AccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relative_key: str = ""
    ttl_seconds: int | None = Field(default=None, ge=1, le=3600)


class ShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    purpose: str | None = None
    audience: Literal["private", "internal", "recipients", "authenticated"] = "private"
    allowed_users: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    expires_at: str | None = None
    lifetime_days: int | None = Field(default=None, ge=1)


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uri: str
    size: int = Field(ge=0, le=5 * 1024**4)
    content_type: str = "application/octet-stream"
    replace_etag: str | None = None


class DeletePreview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uri: str
    kind: Literal["object", "prefix"]


class DeleteExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifest_sha256: str
    confirmation: Literal["DELETE"]


def attach_registry_api(app, *, templates):
    service = app.state.service
    router = APIRouter(prefix="/api/v1", tags=["EUID registry"], dependencies=[Depends(principal)])
    from dewey_service.report_preview import attach_report_preview
    attach_report_preview(app, router, service)

    @app.middleware("http")
    async def private_registry_responses(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        # Native same-origin forms need their Origin for the allowlist check.
        # Preserve the stricter policy set by isolated preview responses.
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @router.patch("/records/{euid}/owner")
    def owner(euid: str, data: dict[str, str] = Body(...)):
        if set(data) != {"email"}:
            raise ValueError("Supply only the new owner's email")
        return service.transfer_registry_owner(euid, data["email"])

    from botocore.exceptions import ClientError
    from dewey_service.storage import StorageError, StorageObjectNotFoundError, StoragePermissionError

    @app.exception_handler(ClientError)
    async def provider_error(request, exc):
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        status = 403 if code in {"403", "AccessDenied"} else 404 if code in {"404", "NoSuchKey", "NoSuchBucket", "NotFound"} else 409 if code in {"PreconditionFailed", "ConditionalRequestConflict", "412"} else 502
        detail = "The object changed or already exists; review the target again" if status == 409 else f"S3 returned {code}; check the selected location and server permissions"
        return JSONResponse({"detail": detail}, status_code=status)

    @app.exception_handler(StorageError)
    async def storage_error(request, exc):
        status = 403 if isinstance(exc, StoragePermissionError) else 404 if isinstance(exc, StorageObjectNotFoundError) else 502
        return JSONResponse({"detail": str(exc)}, status_code=status)

    @app.exception_handler(PermissionError)
    async def permission_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=403)

    # Existing exception handling remains available to the established contracts.
    @app.exception_handler(DeweyNotFoundError)
    async def missing(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(DeweyConflictError)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @router.post("/records", status_code=201)
    def register(data: Registration, idempotency_key: str = Header(alias="Idempotency-Key")):
        code, result = service.register_registry(data.model_dump(exclude_none=True), idempotency_key=idempotency_key)
        return JSONResponse(result, status_code=code)

    @router.get("/records/{euid}")
    def resolve(euid: str):
        return service.resolve_registry(euid)

    @router.patch("/records/{euid}")
    def edit(euid: str, data: MetadataUpdate):
        return service.update_registry(euid, data.model_dump(exclude_unset=True))

    @router.post("/records/{euid}/archive")
    def archive(euid: str):
        return service.archive_registry(euid)

    @router.patch("/records/{euid}/permissions")
    def permissions(euid: str, data: dict[str, Any] = Body(...)):
        return service.update_registry_permissions(euid, data)

    @router.get("/records/{euid}/contents")
    def contents(euid: str, relative_prefix: str = "", continuation_token: str | None = None):
        return service.registry_contents(euid, relative_prefix=relative_prefix, continuation_token=continuation_token)

    @router.post("/records/{euid}/members")
    def add_member(euid: str, data: dict[str, str] = Body(...), idempotency_key: str = Header(alias="Idempotency-Key")):
        code, result = service.add_artifact_set_member(artifact_set_euid=euid, artifact_euid=data["artifact_euid"], idempotency_key=idempotency_key)
        return JSONResponse(result, status_code=code)

    @router.delete("/records/{euid}/members/{member_euid}")
    def remove_member(euid: str, member_euid: str, idempotency_key: str = Header(alias="Idempotency-Key")):
        code, result = service.remove_artifact_set_member(artifact_set_euid=euid, artifact_euid=member_euid, idempotency_key=idempotency_key)
        return JSONResponse(result, status_code=code)

    @router.post("/records/{euid}/access")
    def access(euid: str, data: AccessRequest = Body(default=AccessRequest())):
        return service.registry_download(euid=euid, **data.model_dump())

    @router.post("/records/{euid}/shares", status_code=201)
    def share(euid: str, data: ShareRequest, idempotency_key: str = Header(alias="Idempotency-Key")):
        code, result = service.share_registry(euid, data.model_dump(exclude_none=True), idempotency_key=idempotency_key)
        return JSONResponse(result, status_code=code)

    @router.post("/registry/search")
    def search(data: dict[str, Any] = Body(default={})):
        return service.search_registry(data)

    @router.get("/registry/shares/{euid}")
    def share_detail(euid: str):
        return service.registry_share_detail(euid)

    @router.patch("/registry/shares/{euid}")
    def share_edit(euid: str, data: dict[str, Any] = Body(...)):
        return service.modify_registry_share(euid, data)

    @router.post("/registry/shares/{euid}/revoke")
    def share_revoke(euid: str, data: dict[str, Any] = Body(default={})):
        return service.revoke_share(euid, revoked_by=principal().subject, reason=data.get("reason"))

    @router.post("/registry/shares/{euid}/invite")
    def invite(euid: str, data: dict[str, str] = Body(...)):
        if set(data) != {"email"}:
            raise ValueError("Supply only the recipient email")
        return service.invite_registry_recipient(euid, data["email"])

    @router.get("/storage/buckets", tags=["S3 storage"])
    def buckets(continuation_token: str | None = None, locations_page: int = Query(default=1, ge=1)):
        return service.registry_buckets(continuation_token, locations_page=locations_page)

    @router.get("/storage/object", tags=["S3 storage"])
    def object_detail(uri: str):
        return service.registry_object(uri)

    @router.post("/storage/access", tags=["S3 storage"])
    def storage_access(data: dict[str, Any] = Body(...)):
        return service.registry_download(uri=data["uri"], ttl_seconds=data.get("ttl_seconds"))

    @router.post("/storage/uploads", tags=["S3 storage"])
    def upload(data: UploadRequest):
        return service.begin_registry_upload(**data.model_dump())

    @router.put("/storage/uploads/{euid}/parts/{number}", tags=["S3 storage"])
    async def part(euid: str, number: int, request: Request):
        from starlette.concurrency import run_in_threadpool
        # Reject an oversized part before buffering it; never accept an unbounded body.
        with service.backend.session_scope(commit=False) as session:
            _, operation = service._storage_operation(session, euid)
        maximum = operation["part_size"]
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > maximum:
                raise HTTPException(413, "Part exceeds the declared upload part size")
            body.extend(chunk)
        return await run_in_threadpool(service.upload_registry_part, euid, number, bytes(body))

    @router.post("/storage/uploads/{euid}/complete", tags=["S3 storage"])
    def complete(euid: str):
        return service.complete_registry_upload(euid)

    @router.post("/storage/uploads/{euid}/abort", tags=["S3 storage"])
    def abort(euid: str):
        return service.complete_registry_upload(euid, abort=True)

    @router.post("/storage/deletions/preview", tags=["S3 storage"])
    def deletion_preview(data: DeletePreview):
        return service.preview_registry_delete(**data.model_dump())

    @router.post("/storage/deletions/{euid}/execute", tags=["S3 storage"])
    def deletion_execute(euid: str, data: DeleteExecution):
        return service.execute_registry_delete(euid, **data.model_dump())

    @router.get("/storage/operations/{euid}", tags=["S3 storage"])
    def operation(euid: str):
        with service.backend.session_scope(commit=False) as session:
            _, data = service._storage_operation(session, euid)
            return {"operation_euid": euid, **{k: v for k, v in data.items() if k not in {"upload_id", "properties", "principal", "token_sha256"}}}

    @router.get("/account/tokens")
    def tokens():
        return service.registry_tokens()

    @router.get("/registry/admin")
    def administration():
        if not principal().admin:
            raise HTTPException(403, "Admin access required")
        from dewey_service.settings import build_effective_config_rows, get_config_file_path
        return {"version": app.version, "git": app.state.git_metadata,
            "config": build_effective_config_rows(app.state.settings, config_path=get_config_file_path()),
            **service.registry_defaults(),
            "tokens": service.registry_tokens()}

    @router.get("/registry/defaults")
    def defaults():
        return service.registry_defaults()

    @router.patch("/registry/defaults")
    def change_defaults(data: dict[str, int] = Body(...)):
        return service.update_registry_defaults(data)

    @router.post("/account/tokens", status_code=201)
    def token_create(data: dict[str, Any] = Body(...)):
        return service.issue_registry_token(name=data["name"], lifetime_days=int(data.get("lifetime_days", 30)), role=data.get("role"))

    @router.post("/account/tokens/{euid}/revoke")
    def token_revoke(euid: str):
        return service.revoke_registry_token(euid)

    app.include_router(router)

    def page(request: Request, section: str, *, euid=""):
        actor = getattr(request.state, "registry_principal", None)
        if actor is None:
            next_path = request.url.path
            if request.url.query:
                next_path += "?" + request.url.query
            return RedirectResponse("/login?" + urlencode({"next": next_path}), status_code=303)
        return templates.TemplateResponse(request=request, name="registry.html", context={
            "section": section, "euid": euid, "actor": actor, "version": app.version})

    @app.get("/ui", include_in_schema=False)
    @app.get("/search", include_in_schema=False)
    def library_page(request: Request):
        return page(request, "Library")

    @app.get("/sets", include_in_schema=False)
    def sets_page(request: Request):
        return page(request, "Sets")

    @app.get("/storage", include_in_schema=False)
    @app.get("/artifacts/dag", include_in_schema=False)
    def storage_page(request: Request):
        return page(request, "S3 Browser")

    @app.get("/records/{euid}", include_in_schema=False)
    @app.get("/artifacts/euid/{euid}", include_in_schema=False)
    def record_page(request: Request, euid: str):
        return page(request, "Record", euid=euid)

    @app.get("/artifacts", include_in_schema=False)
    @app.get("/add", include_in_schema=False)
    def add_page(request: Request):
        return page(request, "Add")

    @app.get("/shares", include_in_schema=False)
    def shares_page(request: Request):
        return page(request, "Sharing")

    @app.get("/shares/{euid}", include_in_schema=False)
    def recipient_page(request: Request, euid: str):
        return page(request, "Share", euid=euid)

    @app.get("/account", include_in_schema=False)
    def account_page(request: Request):
        return page(request, "Account")

    @app.get("/literature", include_in_schema=False)
    def literature_page(request: Request):
        return page(request, "Literature")

    @app.get("/admin", include_in_schema=False)
    def admin_page(request: Request):
        return page(request, "Admin")
