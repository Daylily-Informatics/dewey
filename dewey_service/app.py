"""FastAPI app for Dewey v1 canonical artifact service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.sessions import SessionMiddleware

from dewey_service.settings import Settings, get_settings
from dewey_service.store import InMemoryArtifactStore


class ArtifactCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_type: str
    storage_uri: str
    metadata: dict[str, str] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    artifact_euid: str
    artifact_type: str
    storage_uri: str
    metadata: dict[str, str]


class ArtifactSetCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_set_type: str


class ArtifactSetAddMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_euid: str


class ArtifactSetResponse(BaseModel):
    artifact_set_euid: str
    artifact_set_type: str
    artifact_euids: list[str]


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


class ShareReferenceResponse(BaseModel):
    share_reference_euid: str
    target_type: str
    target_euid: str


def create_app(
    settings: Settings | None = None,
    store: InMemoryArtifactStore | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    store = store or InMemoryArtifactStore()

    app = FastAPI(title="Dewey Artifact Service", version="0.1.0")
    app.state.settings = settings
    app.state.store = store
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
    bearer = HTTPBearer(auto_error=False)

    def require_api_auth(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> None:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = str(credentials.credentials or "").strip()
        if token != settings.api_bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def require_ui_session(request: Request) -> str:
        user = str(request.session.get("operator_user") or "").strip()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
        return user

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/artifacts", response_model=ArtifactResponse, dependencies=[Depends(require_api_auth)])
    async def create_artifact(request: ArtifactCreateRequest) -> ArtifactResponse:
        rec = store.create_artifact(
            artifact_type=request.artifact_type,
            storage_uri=request.storage_uri,
            metadata=request.metadata,
        )
        return ArtifactResponse(**rec.__dict__)

    @app.get(
        "/api/v1/artifacts/{artifact_euid}",
        response_model=ArtifactResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def get_artifact(artifact_euid: str) -> ArtifactResponse:
        rec = store.get_artifact(artifact_euid)
        if rec is None:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return ArtifactResponse(**rec.__dict__)

    @app.post(
        "/api/v1/artifact-sets",
        response_model=ArtifactSetResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def create_artifact_set(request: ArtifactSetCreateRequest) -> ArtifactSetResponse:
        rec = store.create_artifact_set(artifact_set_type=request.artifact_set_type)
        return ArtifactSetResponse(**rec.__dict__)

    @app.post(
        "/api/v1/artifact-sets/{artifact_set_euid}/members",
        response_model=ArtifactSetResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def add_artifact_set_member(
        artifact_set_euid: str,
        request: ArtifactSetAddMemberRequest,
    ) -> ArtifactSetResponse:
        try:
            rec = store.add_artifact_to_set(
                artifact_set_euid=artifact_set_euid,
                artifact_euid=request.artifact_euid,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ArtifactSetResponse(**rec.__dict__)

    @app.post(
        "/api/v1/resolve/artifact",
        response_model=ArtifactResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def resolve_artifact(request: ResolveArtifactRequest) -> ArtifactResponse:
        rec = store.get_artifact(request.artifact_euid)
        if rec is None:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return ArtifactResponse(**rec.__dict__)

    @app.post(
        "/api/v1/resolve/artifact-set",
        response_model=ArtifactSetResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def resolve_artifact_set(request: ResolveArtifactSetRequest) -> ArtifactSetResponse:
        rec = store.get_artifact_set(request.artifact_set_euid)
        if rec is None:
            raise HTTPException(status_code=404, detail="Artifact set not found")
        return ArtifactSetResponse(**rec.__dict__)

    @app.post(
        "/api/v1/share-references",
        response_model=ShareReferenceResponse,
        dependencies=[Depends(require_api_auth)],
    )
    async def create_share_reference(request: ShareReferenceCreateRequest) -> ShareReferenceResponse:
        try:
            rec = store.create_share_reference(
                target_type=request.target_type,
                target_euid=request.target_euid,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ShareReferenceResponse(**rec.__dict__)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/ui", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/login", include_in_schema=False, response_class=HTMLResponse)
    async def login_page() -> HTMLResponse:
        return HTMLResponse(
            """
            <html><body>
            <h1>Dewey Operator Login</h1>
            <form method="post" action="/login">
              <label>Username <input name="username" /></label><br/>
              <label>Password <input type="password" name="password" /></label><br/>
              <button type="submit">Login</button>
            </form>
            </body></html>
            """
        )

    @app.post("/login", include_in_schema=False)
    async def login(request: Request, username: str = Form(...), password: str = Form(...)) -> RedirectResponse:
        if username != settings.operator_username or password != settings.operator_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        request.session["operator_user"] = username
        return RedirectResponse(url="/ui", status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/logout", include_in_schema=False)
    async def logout(request: Request) -> RedirectResponse:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/ui", include_in_schema=False, response_class=HTMLResponse)
    async def ui_home(request: Request, _user: str = Depends(require_ui_session)) -> HTMLResponse:
        rows = "".join(
            f"<tr><td>{a.artifact_euid}</td><td>{a.artifact_type}</td><td>{a.storage_uri}</td></tr>"
            for a in sorted(store._artifacts.values(), key=lambda item: item.artifact_euid)
        )
        return HTMLResponse(
            f"""
            <html><body>
            <h1>Dewey Artifacts</h1>
            <form method="post" action="/logout"><button type="submit">Logout</button></form>
            <table border="1">
              <tr><th>EUID</th><th>Type</th><th>Storage URI</th></tr>
              {rows}
            </table>
            </body></html>
            """
        )

    return app
