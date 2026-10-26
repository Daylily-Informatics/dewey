"""Finite isolated report contexts require current verified recipient identity."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.preview_sessions import binding_principal
from dewey_service.registry_access import Principal
from dewey_service.report_preview import _context_expiry


def test_indefinite_share_still_has_finite_report_context():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert _context_expiry(now, None) == now + timedelta(minutes=15)
    session_end = now + timedelta(minutes=4)
    assert _context_expiry(now, None, session_end.isoformat()) == session_end
    share_end = now + timedelta(minutes=2)
    assert _context_expiry(now, share_end.isoformat(), session_end.isoformat()) == share_end


def test_report_asset_refreshes_external_guest_identity(monkeypatch):
    from dewey_service import recipient_identity
    actor = Principal(subject="recipient-fixture", email="recipient@example.test", roles=("READ_ONLY",),
        email_verified=True, recipient_only=True, identity_grant_id="binding-fixture", identity_revision=2,
        identity_expires_at="2099-01-01T00:00:00+00:00")
    calls = []
    def verify(settings, **kwargs):
        calls.append(kwargs)
        return {"canonical_user_id": actor.subject, "email": actor.email, "email_verified": True,
            "grant_id": actor.identity_grant_id, "revision": actor.identity_revision,
            "expires_at": actor.identity_expires_at, "kind": "browser"}
    monkeypatch.setattr(recipient_identity, "verify_recipient_binding", verify)
    settings = SimpleNamespace(cognito_group_role_map={}, registry_internal_domains={"lsmc.bio"})
    current = binding_principal({"principal": asdict(actor)}, settings)
    assert current.email_verified and current.recipient_only and not current.internal
    assert current.roles == ("READ_ONLY",)
    assert calls == [{"grant_id": "binding-fixture", "revision": 2}]

    def disabled(settings, **kwargs):
        raise HTTPException(401, "Provider disabled identity")
    monkeypatch.setattr(recipient_identity, "verify_recipient_binding", disabled)
    with pytest.raises(HTTPException) as failure:
        binding_principal({"principal": asdict(actor)}, settings)
    assert failure.value.status_code == 401


def test_report_asset_rejects_changed_verified_email(monkeypatch):
    from dewey_service import recipient_identity
    actor = Principal(subject="recipient-fixture", email="recipient@example.test", recipient_only=True,
        email_verified=True, identity_grant_id="binding-fixture", identity_revision=2)
    monkeypatch.setattr(recipient_identity, "verify_recipient_binding", lambda *args, **kwargs: {
        "canonical_user_id": actor.subject, "email": "other@example.test", "email_verified": True})
    with pytest.raises(HTTPException) as failure:
        binding_principal({"principal": asdict(actor)}, SimpleNamespace())
    assert failure.value.status_code == 401
