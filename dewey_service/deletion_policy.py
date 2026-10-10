"""Non-configurable prohibition of deletion through Dewey web surfaces."""
from __future__ import annotations

from fastapi import HTTPException
from starlette.responses import JSONResponse

DELETION_DISABLED = "Deletion is disabled in Dewey for all users, including administrators."


def reject_deletion() -> None:
    raise HTTPException(status_code=403, detail=DELETION_DISABLED)


class DeletionProhibitionMiddleware:
    """Reject before authentication, body parsing, or any database/storage operation."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            method = scope["method"]
            path = scope["path"].rstrip("/")
            segments = path.split("/")
            destructive = (
                method == "DELETE"
                or (method not in {"GET", "HEAD", "OPTIONS"} and (
                    # Generic object edits and backup restoration can erase data.
                    path == "/tapdb" or path.startswith("/tapdb/")
                    or path == "/api/v1/storage/deletions"
                    or path.startswith("/api/v1/storage/deletions/")
                    or (path.startswith("/api/v1/records/") and segments[-1] == "archive")
                    or (path.startswith("/api/v1/storage/uploads/") and segments[-1] == "abort")
                ))
            )
            if destructive:
                response = JSONResponse(
                    {"detail": DELETION_DISABLED}, status_code=403,
                    headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
