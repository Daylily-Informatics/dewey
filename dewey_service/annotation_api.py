"""Dewey-owned managed annotations submitted by a broker-delegated human."""
from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request
from itsdangerous import BadSignature
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from dewey_service.artifact_ui import resolve_artifact_type
from dewey_service.storage import StorageObjectNotFoundError, storage_authorization_context
from dewey_service.auth import resolve_external_broker_principal
from dewey_service.audit import authenticated_user_email_context
from dewey_service.registry_access import Principal, principal_context

MAX_BYTES = 50 * 1024 * 1024


class CreateAnnotationUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=1, le=MAX_BYTES)
    content_type: str = Field(default="application/octet-stream", max_length=128)
    target: dict[str, str]


class CompleteAnnotationUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upload_token: str = Field(min_length=1, max_length=16000)


@asynccontextmanager
async def delegated(request, operation, resource):
    settings = request.app.state.settings
    token = request.headers.get("X-LSMC-Delegation")
    if not token or request.headers.get("authorization"):
        raise HTTPException(401, "A single human delegation credential is required")
    if not settings.external_broker_service_token or not settings.external_broker_handoff_exchange_url:
        raise HTTPException(503, "Dewey registered broker configuration is required")
    async with httpx.AsyncClient(timeout=10, verify=settings.external_broker_ca_bundle or True) as client:
        response = await client.post(settings.external_broker_handoff_exchange_url,
            headers={"Authorization": f"Bearer {settings.external_broker_service_token}", "X-LSMC-Service-ID": settings.external_broker_service_id},
            json={"delegation": {"action": "introspect", "credential": token, "operation": operation, "resource": resource}})
    if response.status_code != 200:
        raise HTTPException(response.status_code if response.status_code in {401, 403} else 503, "Human delegation was rejected or is unavailable")
    claims = response.json()
    user = resolve_external_broker_principal(claims["user"], request)
    if claims.get("calling_service") != "kahlo" or "lsmc:internal-user" not in user.cognito_groups:
        raise HTTPException(403, "Internal human delegation from Kahlo is required")
    actor = Principal(subject=user.user_sub, email=user.email, roles=tuple(user.roles),
        groups=tuple(user.cognito_groups), internal=True, service=False,
        annotation_upload=operation in {"dewey.annotation.create", "dewey.annotation.complete"})
    with principal_context(actor), authenticated_user_email_context(actor.email):
        yield actor, claims


def managed_payload(service, actor, resource, body):
    metadata = {"annotation_operation_id": resource, "annotation_owner_subject": actor.subject,
                "calling_service": "kahlo", "declared_size": body.size, "target": body.target}
    return {"artifact_type": resolve_artifact_type("other", body.filename),
            "original_filename": service._safe_filename(body.filename),
            "content_type": body.content_type.strip() or None, "producer_system": "kahlo",
            "producer_object_euid": None, "metadata": metadata, "lock_after_import": False}


def managed_key(service, actor, resource, payload):
    spec = {k: payload[k] for k in ("artifact_type", "original_filename", "content_type", "producer_system", "producer_object_euid", "metadata", "lock_after_import")}
    return service._managed_key(namespace="uploads",
        seed=f"annotation:{actor.subject}:{resource}:create:{service._fingerprint(spec)}",
        filename=payload["original_filename"])


def managed_receipt(service, actor, resource, receipt):
    try:
        payload = service._upload_serializer.loads(receipt)
        meta = payload["metadata"]
        if (meta["annotation_operation_id"] != resource or meta["annotation_owner_subject"] != actor.subject
                or meta["calling_service"] != "kahlo" or payload["bucket"] != service.managed_storage_bucket
                or payload["key"] != managed_key(service, actor, resource, payload)):
            raise HTTPException(403, "Managed upload receipt does not belong to this human, operation and location")
        return payload
    except (BadSignature, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(401, "Invalid managed upload receipt") from exc


@contextmanager
def managed_access(service, actor, key):
    # Explicit Dewey policy for internal-human annotations: only this operation's
    # managed object, with no download, listing, deletion or overwrite capability.
    # Existing record/ancestor restrictions continue to be evaluated.
    def authorize(bucket, requested_key, *, action):
        if (not actor.annotation_upload or not actor.internal or actor.service
                or bucket != service.managed_storage_bucket or requested_key != key
                or action not in {"metadata", "upload"}):
            raise HTTPException(403, "Operation is outside the managed annotation scope")
        service.require_storage_access(bucket, key, action="metadata")
    with storage_authorization_context(authorize):
        yield


def attach_annotation_api(app):
    router = APIRouter(prefix="/api/v1/annotations", tags=["annotations"])
    service = app.state.service

    @router.post("/uploads/{operation_id}")
    async def create(request: Request, operation_id: UUID, body: CreateAnnotationUpload):
        resource = str(operation_id)
        async with delegated(request, "dewey.annotation.create", resource) as (actor, claims):
            spec = managed_payload(service, actor, resource, body)
            with managed_access(service, actor, managed_key(service, actor, resource, spec)):
                _, payload = await run_in_threadpool(service.create_upload_session,
                    **spec, idempotency_key=f"annotation:{actor.subject}:{resource}:create")
                return payload

    @router.post("/uploads/{operation_id}/resume")
    async def resume(request: Request, operation_id: UUID, body: CompleteAnnotationUpload):
        resource = str(operation_id)
        async with delegated(request, "dewey.annotation.create", resource) as (actor, claims):
            token = managed_receipt(service, actor, resource, body.upload_token)
            with managed_access(service, actor, token["key"]):
                storage = service._require_storage()
                try:
                    await run_in_threadpool(storage.head_object, bucket=token["bucket"], key=token["key"])
                except StorageObjectNotFoundError:
                    upload = await run_in_threadpool(storage.generate_presigned_upload,
                        bucket=token["bucket"], key=token["key"], expires_in=service.upload_session_ttl_seconds,
                        content_type=token["content_type"])
                    # Keep the original signed registration token and idempotency fingerprint.
                    return {"status": "ready", "upload_token": body.upload_token,
                            "upload_method": upload["method"], "upload_url": upload["url"],
                            "upload_headers": upload["headers"], "expires_in": service.upload_session_ttl_seconds}
                return {"status": "stored"}

    @router.post("/uploads/{operation_id}/complete")
    async def complete(request: Request, operation_id: UUID, body: CompleteAnnotationUpload):
        resource = str(operation_id)
        async with delegated(request, "dewey.annotation.complete", resource) as (actor, claims):
            # A fresh human credential can recover already-stored bytes after PUT expiry.
            token = managed_receipt(service, actor, resource, body.upload_token)
            with managed_access(service, actor, token["key"]):
                try:
                    obj = await run_in_threadpool(service._require_storage().head_object, bucket=token["bucket"], key=token["key"])
                except StorageObjectNotFoundError as exc:
                    raise HTTPException(409, "File bytes are not present; resume this upload operation") from exc
                size = token["metadata"].get("declared_size")
                if type(size) is not int or obj.size != size or not 0 < size <= MAX_BYTES:
                    raise HTTPException(409, "Stored file size differs from the declared annotation size")
                _, result = await run_in_threadpool(service.complete_upload_session,
                    upload_token=body.upload_token, checksums={}, metadata={},
                    idempotency_key=f"annotation:{actor.subject}:{resource}:complete", annotation_recovery=True)

            resolved = await run_in_threadpool(service.resolve_registry, result["artifact_euid"])
            if resolved.get("owner") not in {actor.email, actor.subject}:
                raise HTTPException(409, "Dewey artifact owner differs from the authenticated human")
            return resolved

    @router.get("/artifacts/{euid}")
    async def resolve(request: Request, euid: str):
        async with delegated(request, "dewey.artifact.resolve", euid):
            return await run_in_threadpool(service.resolve_registry, euid)

    @router.post("/artifacts/{euid}/access")
    async def access(request: Request, euid: str):
        async with delegated(request, "dewey.artifact.access", euid):
            return await run_in_threadpool(service.registry_download, euid=euid, ttl_seconds=300)

    app.include_router(router)
