"""Own-account credential operations; public ingress never exposes admin token lists."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from dewey_service.registry_access import principal
from dewey_service.share_context import require_share_context, require_share_ingress


class RecipientTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    lifetime_days: int = Field(default=30, ge=1, le=30)


def attach_recipient_account(app, service, templates):
    router = APIRouter(
        prefix="/api/v2/recipient/tokens",
        tags=["Recipient credentials"],
        dependencies=[Depends(principal), Depends(require_share_context)],
    )

    @router.get("")
    def tokens():
        return service.registry_tokens(own_only=True)

    @router.post("", status_code=201)
    def create_token(data: RecipientTokenRequest):
        return service.issue_registry_token(
            name=data.name, lifetime_days=data.lifetime_days, role="READ_ONLY", recipient_only=True
        )

    @router.post("/{token_euid}/revoke")
    def revoke_token(token_euid: str):
        return service.revoke_registry_token(token_euid, own_only=True)

    app.include_router(router)

    @app.get("/recipient/account", include_in_schema=False)
    def account(request: Request):
        require_share_ingress(request)
        actor = getattr(request.state, "registry_principal", None)
        if actor is None or not actor.email_verified:
            return RedirectResponse("/auth/login?next=%2Frecipient%2Faccount", status_code=303)
        if actor.service:
            raise HTTPException(403, "A registered recipient is required")
        return templates.TemplateResponse(
            request=request, name="recipient_account.html", context={"email": actor.email}
        )
