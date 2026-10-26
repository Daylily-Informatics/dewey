"""Private Login responses cannot silently authorize a changed or unavailable identity."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from dewey_service import auth, recipient_identity as identity
from tests.test_auth_unit import _settings
from tests.test_storage_unit import _client, _FakeS3Backend


def settings(**changes):
    return SimpleNamespace(**{
        "external_broker_identity_url": "https://login.example.test/api/identity",
        "external_broker_identity_mint_url": "https://login.example.test/api/mint",
        "external_broker_identity_revoke_url": "https://login.example.test/api/revoke",
        "external_broker_service_token": "fixture-service-credential",
        "external_broker_service_id": "dewey", "external_broker_ca_bundle": "", **changes})


def binding(**changes):
    return {"expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "email_verified": True, "active": True, "audience": "dewey", "kind": "browser",
        "recipient_only": True, "revision": 2, "grant_id": "fixture-binding", "canonical_user_id": "fixture-user",
        "provider_subject": "fixture-provider-user", "email": "recipient@example.test", **changes}


def transport(monkeypatch, status=200, result=None, error=None):
    calls = []
    class Client:
        def __init__(self, **kwargs):
            assert kwargs == {"timeout": 10, "follow_redirects": False, "verify": True}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, endpoint, **kwargs):
            calls.append((endpoint, kwargs))
            if error:
                raise error
            def read():
                if isinstance(result, Exception):
                    raise result
                return result
            return SimpleNamespace(status_code=status, json=read)
    monkeypatch.setattr(identity.httpx, "Client", Client)
    return calls


@pytest.mark.parametrize("status,expected", [(400,401),(401,401),(403,401),(404,401),(409,401),(422,401),(302,503),(429,503),(500,503)])
def test_provider_rejection_is_distinct_from_outage_and_redirect_is_not_followed(monkeypatch, status, expected):
    calls = transport(monkeypatch, status)
    with pytest.raises(HTTPException) as failure:
        identity.verify_recipient_binding(settings(), grant_id="fixture-binding", revision=2)
    assert failure.value.status_code == expected and len(calls) == 1


@pytest.mark.parametrize("result,error", [(None,None),([],None),(ValueError("bad JSON"),None),(None,httpx.ConnectError("offline"))])
def test_invalid_provider_response_fails_closed(monkeypatch, result, error):
    transport(monkeypatch, result=result, error=error)
    with pytest.raises(HTTPException) as failure:
        identity.verify_recipient_binding(settings(), grant_id="fixture-binding", revision=2)
    assert failure.value.status_code == 503


@pytest.mark.parametrize("changes", [
    {"external_broker_identity_url": "http://login.example.test/api/identity"},
    {"external_broker_identity_url": "https://user@login.example.test/api/identity"},
    {"external_broker_service_token": ""}, {"external_broker_service_id": "other"},
])
def test_missing_or_untrusted_endpoint_is_rejected_before_transport(monkeypatch, changes):
    calls = transport(monkeypatch, result=binding())
    with pytest.raises(HTTPException) as failure:
        identity.verify_recipient_binding(settings(**changes), grant_id="fixture-binding", revision=2)
    assert failure.value.status_code == 503 and calls == []


@pytest.mark.parametrize("changes", [{"email_verified":False},{"active":False},{"audience":"other"},
    {"kind":"service"},{"recipient_only":"true"},{"revision":0},{"grant_id":""},
    {"canonical_user_id":""},{"provider_subject":""},{"email":"UPPER@example.test"},
    {"email":"invalid"},{"expires_at":"bad"},{"expires_at":"2099-01-01T00:00:00"},
    {"expires_at":"2000-01-01T00:00:00+00:00"}])
def test_unverified_inactive_or_malformed_identity_never_authorizes(changes):
    with pytest.raises(HTTPException) as failure:
        identity._binding(binding(**changes))
    assert failure.value.status_code == 401


def test_binding_exact_match_mint_kind_and_confirmed_revocation(monkeypatch):
    result = binding()
    calls = transport(monkeypatch, result=result)
    assert identity.verify_recipient_binding(settings(), grant_id="fixture-binding", revision=2) == result
    assert calls[0][1]["json"] == {"grant_id":"fixture-binding", "revision":2}
    assert calls[0][1]["headers"]["X-LSMC-Service-ID"] == "dewey"
    for grant_id, revision in [("",2),("fixture-binding",0),("other",2),("fixture-binding",3)]:
        with pytest.raises(HTTPException) as failure:
            identity.verify_recipient_binding(settings(), grant_id=grant_id, revision=revision)
        assert failure.value.status_code == 401
    with pytest.raises(HTTPException) as wrong_kind:
        identity.mint_personal_identity(settings(), grant_id="fixture-binding", revision=2, lifetime_days=1)
    assert wrong_kind.value.status_code == 503
    result["kind"] = "personal"
    assert identity.mint_personal_identity(settings(), grant_id="fixture-binding", revision=2, lifetime_days=1)["kind"] == "personal"
    assert calls[-1][1]["json"]["lifetime_days"] == 1
    with pytest.raises(HTTPException) as unconfirmed:
        identity.revoke_recipient_identity(settings(), grant_id="fixture-binding", revision=2)
    assert unconfirmed.value.status_code == 503
    result.update(status="revoked")
    assert identity.revoke_recipient_identity(settings(), grant_id="fixture-binding", revision=2)["status"] == "revoked"


@pytest.mark.parametrize("method,path,allowed", [("GET","/api/v1/records",True), ("HEAD","/fetch/fixture",True),
    ("POST","/api/v1/resolve/artifact",True), ("POST","/api/v1/records/fixture/shares",False),
    ("PATCH","/api/v1/records/fixture",False)])
def test_read_only_personal_credential_cannot_gain_write_access(method, path, allowed):
    actor = SimpleNamespace(writable=False, email="recipient@example.test")
    request = SimpleNamespace(state=SimpleNamespace(registry_principal=actor), method=method, url=SimpleNamespace(path=path))
    credential = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dewey_user_fixture_only")
    dependency = auth.require_api_auth(_settings())
    if allowed:
        assert dependency(request, credential) == credential.credentials
    else:
        with pytest.raises(HTTPException) as failure:
            dependency(request, credential)
        assert failure.value.status_code == 403


@pytest.mark.parametrize("checksum_mode", [False, True])
def test_storage_rebind_inspection_preserves_full_object_checksum_kind(checksum_mode):
    backend = _FakeS3Backend()
    backend.head_response.update(ChecksumSHA256="fixture-base64-digest", ChecksumType="FULL_OBJECT")
    client = _client(backend)
    result = client.head_object(bucket="fixture-bucket", key="file.txt", version_id="version-1",
        request_payer="requester", permission="download", checksum_mode=checksum_mode)
    assert result.sha256 == "fixture-base64-digest" and result.checksum_type == "FULL_OBJECT"
    assert client.authorizations == [("fixture-bucket","file.txt","download")]
    assert backend.calls == [("head_object", {"Bucket":"fixture-bucket", "Key":"file.txt",
        "VersionId":"version-1", "RequestPayer":"requester", **({"ChecksumMode":"ENABLED"} if checksum_mode else {})})]
