"""Verified callback bindings retain finite native authority and reject drift."""

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from daylily_auth_cognito.browser.session import SessionPrincipal, load_session_principal
from fastapi import HTTPException, Request

from dewey_service.preview_sessions import binding_principal, establish_session_binding
from tests.test_report_preview_attribution import ACTOR
from tests.test_report_preview_attribution import preview as preview


def callback_request(p, context):
    p.app.state.service = p.service
    user = SessionPrincipal(
        user_sub=ACTOR.subject, email=ACTOR.email, roles=list(ACTOR.roles), app_context=context
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/auth/lsmc/callback",
            "headers": [],
            "app": p.app,
            "session": user.to_session_dict(),
        }
    )
    config = SimpleNamespace(
        session_max_age=3600, server_instance_id=None, auth_mode="external_broker"
    )
    return request, config


def identity_context():
    return {
        "recipient_identity": {
            "grant_id": ACTOR.identity_grant_id,
            "revision": ACTOR.identity_revision,
        },
        "recipient_only": True,
    }


def test_verified_callback_caps_native_session_at_identity_expiry_and_revokes_previous(
    preview, monkeypatch
):
    p = preview
    deadline = datetime.now(timezone.utc) + timedelta(seconds=90)
    monkeypatch.setattr(
        "dewey_service.recipient_identity.verify_recipient_binding",
        lambda *args, **kwargs: {
            "grant_id": ACTOR.identity_grant_id,
            "revision": 1,
            "canonical_user_id": ACTOR.subject,
            "email": ACTOR.email,
            "email_verified": True,
            "expires_at": deadline.isoformat(),
        },
    )
    request, config = callback_request(p, identity_context())
    previous = SessionPrincipal(
        user_sub=ACTOR.subject,
        email=ACTOR.email,
        roles=list(ACTOR.roles),
        app_context={"dewey_session_binding_euid": p.binding.euid},
    )
    establish_session_binding(request, config, previous_user=previous)
    current = load_session_principal(request)
    persisted = next(
        row
        for row in p.database.rows
        if row.euid == current.app_context["dewey_session_binding_euid"]
    )
    assert persisted.euid != p.binding.euid and p.binding.json_addl["status"] == "revoked"
    assert datetime.fromisoformat(persisted.json_addl["expires_at"]) == deadline
    assert persisted.json_addl["principal"]["email_verified"] is True
    assert persisted.json_addl["principal"]["recipient_only"] is True
    assert persisted.json_addl["principal"]["identity_grant_id"] == ACTOR.identity_grant_id


@pytest.mark.parametrize(
    "context",
    [
        {"recipient_identity": "invalid", "recipient_only": True},
        {"recipient_identity": {}, "recipient_only": True},
        {"recipient_identity": {"grant_id": "fixture", "revision": 1}},
    ],
)
def test_invalid_callback_identity_is_rejected_before_native_binding_creation(preview, context):
    request, config = callback_request(preview, context)
    before = len(preview.database.rows)
    with pytest.raises(HTTPException) as failure:
        establish_session_binding(request, config)
    assert failure.value.status_code == 401 and len(preview.database.rows) == before


@pytest.mark.parametrize(
    "change", [{"canonical_user_id": "other-fixture-user"}, {"email": "other@example.test"}]
)
def test_callback_identity_mismatch_cannot_rebind_browser_session(preview, monkeypatch, change):
    request, config = callback_request(preview, identity_context())
    monkeypatch.setattr(
        "dewey_service.recipient_identity.verify_recipient_binding",
        lambda *args, **kwargs: {
            "canonical_user_id": ACTOR.subject,
            "email": ACTOR.email,
            **change,
        },
    )
    before = len(preview.database.rows)
    with pytest.raises(HTTPException) as failure:
        establish_session_binding(request, config)
    assert failure.value.status_code == 401 and len(preview.database.rows) == before


def test_ordinary_browser_binding_keeps_console_session_without_share_identity(preview):
    request, config = callback_request(preview, {})
    establish_session_binding(request, config)
    user = load_session_principal(request)
    row = next(
        row
        for row in preview.database.rows
        if row.euid == user.app_context["dewey_session_binding_euid"]
    )
    assert row.json_addl["principal"]["identity_grant_id"] == ""
    assert row.json_addl["principal"]["email_verified"] is False
    with pytest.raises(HTTPException) as failure:
        binding_principal(row.json_addl, preview.settings)
    assert failure.value.status_code == 401


def test_verified_binding_without_current_dewey_role_is_forbidden(preview):
    stored = {"principal": {**asdict(ACTOR), "recipient_only": False, "groups": []}}
    with pytest.raises(HTTPException) as failure:
        binding_principal(stored, preview.settings)
    assert failure.value.status_code == 403
