"""A separate, read-only credential accepted by exactly one resolver route."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


def issue_resolver_credential(path: Path, *, lifetime_days: int) -> dict:
    if not path.is_absolute() or not 1 <= lifetime_days <= 366:
        raise ValueError("An absolute output path and 1..366 day lifetime are required")
    token = "dewey_qeo_resolver_" + secrets.token_urlsafe(48)
    # Never overwrite or print a secret. An existing path (including a symlink) fails.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token + "\n")
    return {
        "principal": "qeo",
        "scope": "multiqc-package:resolve",
        "token_file": str(path),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=lifetime_days)).isoformat(),
    }


def require_qeo_resolver_auth(settings):
    bearer = HTTPBearer(auto_error=False)

    def authenticate(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        configured = settings.qeo_resolver_token_sha256
        try:
            expires = datetime.fromisoformat(settings.qeo_resolver_token_expires_at)
            valid_time = expires.tzinfo is not None and expires > datetime.now(timezone.utc)
        except (ValueError, TypeError):
            valid_time = False
        if not configured or not valid_time:
            raise HTTPException(503, "QEO resolver credential is not configured or has expired")
        supplied = credentials.credentials if credentials else ""
        if not supplied.startswith("dewey_qeo_resolver_") or not secrets.compare_digest(
            hashlib.sha256(supplied.encode()).hexdigest(), configured
        ):
            raise HTTPException(401, "Invalid QEO resolver credential")
        return "qeo"

    return authenticate
