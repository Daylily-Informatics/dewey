"""Dedicated reader admission shared by Dewey's middleware and native DAG auth."""
from __future__ import annotations

import hashlib
import re
import secrets
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

if TYPE_CHECKING:
    from dewey_service.settings import Settings


def is_canonical_dag_get(request: Request) -> bool:
    path = request.url.path
    return request.method == "GET" and (
        path in {"/api/dag/manifest", "/api/dag/v2/data", "/api/dag/v2/search"}
        or re.fullmatch(r"/api/dag/v2/object/[^/]+", path) is not None
    )


def dedicated_dag_actor(request: Request, settings: Settings, token: str) -> dict[str, str] | None:
    """Verify only the dedicated reader; never create a registry/admin principal."""
    if not token.startswith("dewey_dag_"):
        return None
    if not is_canonical_dag_get(request):
        raise HTTPException(status_code=403, detail="DAG read credential has no route scope")
    expected = settings.dag_read_token_sha256
    fingerprint = hashlib.sha256(token.encode()).hexdigest()
    if not expected or not secrets.compare_digest(fingerprint, expected):
        raise HTTPException(status_code=401, detail="Invalid DAG read credential")
    return {"username": settings.dag_read_actor}
