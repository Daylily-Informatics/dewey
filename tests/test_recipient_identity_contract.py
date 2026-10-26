from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from dewey_service import auth, recipient_identity


def settings():
    return SimpleNamespace(
        external_broker_service_id="dewey", external_broker_service_token="fixture-service-credential",
        external_broker_ca_bundle="", external_broker_identity_url="https://login.example.test/api/v1/dewey/identity/introspect",
        external_broker_identity_mint_url="https://login.example.test/api/v1/dewey/identity/credentials",
        external_broker_identity_revoke_url="https://login.example.test/api/v1/dewey/identity/revoke",
        external_broker_share_login_url="https://login.example.test/auth/share",
        external_broker_login_url="https://login.example.test/auth/login",
        external_broker_callback_url="https://dewey.example.test/auth/lsmc/callback",
        cognito_group_role_map={},
    )


def binding(**changes):
    result = {"grant_id": "fixture-recipient-grant", "revision": 1,
              "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
              "kind": "browser", "audience": "dewey", "active": True,
              "canonical_user_id": "fixture-canonical", "provider_subject": "fixture-provider-subject",
              "email": "recipient@example.test", "email_verified": True, "recipient_only": True}
    result.update(changes)
    return result


def test_deep_fetch_login_uses_explicit_recipient_entry_and_keeps_destination():
    config = settings()
    request = Request({"type": "http", "method": "GET", "path": "/auth/login", "headers": [], "session": {}})
    target = "/fetch/fixture-share/report.html?view=detail"
    response = auth.start_external_broker_login(request, settings=config, next_path=target)
    parsed = urlparse(response.headers["location"])
    assert parsed.path == "/auth/share"
    assert parse_qs(parsed.query)["next"] == [target]
    assert request.session[auth._EXTERNAL_BROKER_NEXT_KEY] == target
    account = auth.start_external_broker_login(request, settings=config, next_path="/recipient/account")
    assert urlparse(account.headers["location"]).path == "/auth/share"
    response = auth.start_external_broker_login(request, settings=config, next_path="/ui")
    assert urlparse(response.headers["location"]).path == "/auth/login"


def test_recipient_projection_cannot_inherit_administrator_groups():
    config = settings()
    request = Request({"type": "http", "method": "GET", "path": "/auth/lsmc/callback", "headers": [],
                       "app": SimpleNamespace(state=SimpleNamespace(settings=config))})
    user = {"canonical_user_id": "fixture-canonical", "email": "recipient@example.test",
            "email_verified": True, "verification_state": "verified", "groups": ["lsmc:global-admin"],
            "recipient_identity": binding()}
    principal = auth.resolve_external_broker_principal(user, request)
    assert principal.roles == ["READ_ONLY"]
    assert principal.app_context["recipient_only"] is True


@pytest.mark.parametrize("change", [
    {"email_verified": False}, {"active": False}, {"audience": "another-service"},
    {"expires_at": "2020-01-01T00:00:00+00:00"}, {"recipient_only": None},
])
def test_invalid_broker_identity_is_denied(monkeypatch, change):
    monkeypatch.setattr(recipient_identity, "_request", lambda *args: binding(**change))
    with pytest.raises(HTTPException) as failure:
        recipient_identity.verify_recipient_binding(settings(), grant_id="fixture-recipient-grant", revision=1)
    assert failure.value.status_code == 401


def test_identity_grant_and_revision_must_match_exactly(monkeypatch):
    monkeypatch.setattr(recipient_identity, "_request", lambda *args: binding(revision=2))
    with pytest.raises(HTTPException) as failure:
        recipient_identity.verify_recipient_binding(settings(), grant_id="fixture-recipient-grant", revision=1)
    assert failure.value.status_code == 401
