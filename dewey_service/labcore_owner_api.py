"""Strict, conditionally mounted Labcore service-principal API."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from dewey_service.labcore_owner_command import LabcoreSequencingRunRegistrationCommandV2
from dewey_service.labcore_owner_config import (
    LABCORE_OWNER_WRITE_SCOPE,
    LabcoreOwnerApiConfig,
    load_labcore_owner_config,
)
from dewey_service.service import DeweyConflictError, DeweyNotFoundError


@dataclass(frozen=True)
class LabcoreOwnerPrincipal:
    tenant_euid: str
    principal_id: str


class LabcoreOwnerRegistrationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    registration_receipt_euid: str
    request_sha256: str
    command_sha256: str
    tenant_euid: str
    external_object_euid: str
    external_object_relation_euid: str


class LabcoreOwnerErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    detail: str


class LabcoreOwnerRoute(APIRoute):
    """Prevent FastAPI validation payloads from reflecting body evidence."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def redacted(request: Request) -> Response:
            # Bound the actual stream before JSON parsing, including chunked requests.
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 16 * 1024 * 1024:
                    return JSONResponse(status_code=413, content={"detail": "Request too large"})
                body.extend(chunk)
            request._body = bytes(body)
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Invalid Labcore owner registration"},
                )

        return redacted


def _auth_dependency(config: LabcoreOwnerApiConfig):
    bearer = HTTPBearer(auto_error=False)

    def authenticate(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> LabcoreOwnerPrincipal:
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = str(credentials.credentials or "").strip()
        for principal in config.service_principals:
            if not secrets.compare_digest(token, principal.bearer_token):
                continue
            if LABCORE_OWNER_WRITE_SCOPE not in principal.scopes:
                raise HTTPException(
                    status_code=403, detail="Service principal lacks required scope"
                )
            return LabcoreOwnerPrincipal(
                tenant_euid=principal.tenant_euid, principal_id=principal.principal_id
            )
        raise HTTPException(
            status_code=401,
            detail="Invalid service principal",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return authenticate


def attach_labcore_owner_api(app, *, settings) -> None:
    """Attach no route unless the complete explicit configuration is enabled."""

    config = load_labcore_owner_config()
    general_tokens = settings.api_tokens()
    if any(item.bearer_token in general_tokens for item in config.service_principals):
        raise ValueError("Labcore credentials must be distinct from general Dewey API tokens")
    app.state.labcore_owner_effective_config = {
        "api_enabled": config.is_enabled,
        "service_principals": tuple(item.principal_id for item in config.service_principals),
    }
    if not config.is_enabled:
        return
    authorize = _auth_dependency(config)

    def register(
        body: LabcoreSequencingRunRegistrationCommandV2,
        principal: LabcoreOwnerPrincipal = Depends(authorize),
        idempotency_key: str = Header(..., alias="Idempotency-Key"),
    ) -> JSONResponse:
        if principal.tenant_euid != body.owner_request.tenant_euid:
            raise HTTPException(status_code=403, detail="Service principal tenant mismatch")
        if idempotency_key != body.command_sha256:
            raise HTTPException(status_code=409, detail="Idempotency-Key must equal command_sha256")
        try:
            code, payload = app.state.service.register_labcore_sequencing_run_owner(
                request_body=body, principal_id=principal.principal_id
            )
            response = LabcoreOwnerRegistrationResponse.model_validate(payload)
            return JSONResponse(status_code=code, content=response.model_dump(mode="json"))
        except DeweyNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target artifact not authorized") from exc
        except DeweyConflictError as exc:
            raise HTTPException(
                status_code=409, detail="Labcore owner registration conflicts"
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid Labcore owner registration"
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503, detail="Labcore owner authority unavailable"
            ) from exc

    responses = {
        200: {"model": LabcoreOwnerRegistrationResponse},
        201: {"model": LabcoreOwnerRegistrationResponse},
        400: {"model": LabcoreOwnerErrorResponse},
        401: {"model": LabcoreOwnerErrorResponse},
        403: {"model": LabcoreOwnerErrorResponse},
        404: {"model": LabcoreOwnerErrorResponse},
        409: {"model": LabcoreOwnerErrorResponse},
        413: {"model": LabcoreOwnerErrorResponse},
        422: {"model": LabcoreOwnerErrorResponse},
        503: {"model": LabcoreOwnerErrorResponse},
    }
    router = APIRouter(route_class=LabcoreOwnerRoute)
    router.add_api_route(
        "/api/v2/sequencer-runs/register",
        register,
        methods=["POST"],
        response_model=LabcoreOwnerRegistrationResponse,
        status_code=status.HTTP_201_CREATED,
        responses=responses,
    )
    app.include_router(router)
