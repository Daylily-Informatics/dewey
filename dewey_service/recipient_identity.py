"""Private Login recipient credential contract. No OAuth credentials leave Login."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException


def close_recipient_client(settings):
    with settings._recipient_http_lock:
        if settings._recipient_http_client is not None:
            settings._recipient_http_client.close()
            settings._recipient_http_client = None


def _client(settings):
    with settings._recipient_http_lock:
        if settings._recipient_http_client is None:
            settings._recipient_http_client = httpx.Client(
                timeout=10, follow_redirects=False,
                verify=settings.external_broker_ca_bundle or True,
            )
        return settings._recipient_http_client


def _request(settings, field, body):
    endpoint = str(getattr(settings, field, "") or "").strip()
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or not settings.external_broker_service_token
        or settings.external_broker_service_id != "dewey"
    ):
        raise HTTPException(503, "Registered Dewey recipient identity endpoint is not configured")
    try:
        client = _client(settings)
        request = client.build_request(
            "POST", endpoint, json=body,
            headers={
                "Authorization": "Bearer " + settings.external_broker_service_token,
                "X-LSMC-Service-ID": "dewey",
            },
        )
        # These are independent service-authenticated identity checks. Never
        # carry a previous recipient's broker cookie into another request.
        request.headers.pop("cookie", None)
        response = client.send(request)
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Current recipient identity is unavailable") from exc
    if response.status_code in (400, 401, 403, 404, 409, 422):
        raise HTTPException(401, "Recipient identity is revoked, changed or expired; sign in again")
    if response.status_code != 200:
        raise HTTPException(503, "Current recipient identity is unavailable")
    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(503, "Recipient identity response is invalid") from exc
    if not isinstance(result, dict):
        raise HTTPException(503, "Recipient identity response is invalid")
    return result


def _binding(result):
    try:
        expiry = datetime.fromisoformat(result["expires_at"])
        valid = (
            result["email_verified"] is True
            and result["active"] is True
            and result["audience"] == "dewey"
            and result["kind"] in {"browser", "personal"}
            and isinstance(result["recipient_only"], bool)
            and isinstance(result["revision"], int)
            and result["revision"] > 0
            and bool(result["grant_id"])
            and bool(result["canonical_user_id"])
            and bool(result["provider_subject"])
            and "@" in result["email"]
            and result["email"] == result["email"].strip().lower()
            and expiry.tzinfo is not None
            and expiry > datetime.now(timezone.utc)
        )
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise HTTPException(401, "Verified active recipient identity is required")
    return result


def verify_recipient_binding(settings, *, grant_id: str, revision: int) -> dict:
    if not grant_id or not isinstance(revision, int) or revision < 1:
        raise HTTPException(401, "Verified recipient identity is required; sign in again")
    result = _binding(
        _request(
            settings, "external_broker_identity_url", {"grant_id": grant_id, "revision": revision}
        )
    )
    if result["grant_id"] != grant_id or result["revision"] != revision:
        raise HTTPException(401, "Recipient identity binding changed; sign in again")
    return result


def mint_personal_identity(settings, *, grant_id: str, revision: int, lifetime_days: int) -> dict:
    result = _binding(
        _request(
            settings,
            "external_broker_identity_mint_url",
            {"grant_id": grant_id, "revision": revision, "lifetime_days": lifetime_days},
        )
    )
    if result["kind"] != "personal":
        raise HTTPException(503, "Login did not issue a personal recipient credential")
    return result


def revoke_recipient_identity(settings, *, grant_id: str, revision: int) -> dict:
    result = _request(
        settings,
        "external_broker_identity_revoke_url",
        {"grant_id": grant_id, "revision": revision},
    )
    if result.get("grant_id") != grant_id or result.get("status") != "revoked":
        raise HTTPException(503, "Recipient credential revocation is unconfirmed")
    return result
