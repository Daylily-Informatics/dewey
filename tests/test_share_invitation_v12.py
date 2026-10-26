"""Durable invitation outcomes distinguish provider rejection from uncertainty."""
from types import SimpleNamespace
import pytest
import requests
from fastapi import HTTPException
from dewey_service.registry_access import principal_context
from dewey_service.services.registry import RegistryServiceMixin
from tests.test_recipient_tokens_v12 import ACTOR, Backend


@pytest.mark.parametrize("http_status,delivery,expected", [
    (200,"accepted","accepted"),(502,"failed","failed"),
    (502,"uncertain","uncertain"),(400,None,"failed"),(None,None,"uncertain"),
])
def test_invitation_receipt_preserves_provider_outcome(monkeypatch,http_status,delivery,expected):
    service=RegistryServiceMixin();service.backend=Backend()
    service._require_sharing=lambda:None
    service.backend.create_lineage=lambda *args,**kwargs:None
    share=service.backend.create_instance(None,template_code="access/share/generic/1.0/",name="Invitation fixture",json_addl={"properties":{},"status":"active",
        "expires_at":None,"denied_emails":[],"audience":"public_registered"})
    share.euid="share-fixture"
    service._storage_operation=lambda session,euid,lock: (service.backend.rows[-1],None)
    config=SimpleNamespace(external_broker_service_token="fixture-private-broker-token",external_broker_ca_bundle="",
        external_broker_callback_url="https://dewey.example.test/auth/lsmc/callback")
    monkeypatch.setattr("dewey_service.settings.get_settings",lambda:config)
    monkeypatch.setenv("LSMC_AUTH_BROKER_SHARE_RECIPIENT_PREPARE_URL","https://login.example.test/api/v1/dewey/share-recipient/prepare")
    calls=[]
    def send(endpoint,**kwargs):
        calls.append(kwargs)
        if http_status is None:raise requests.ReadTimeout("private details must not appear in receipt")
        def body():
            if delivery is None:raise ValueError("invalid JSON")
            return {"invite_email":{"status":delivery}}
        return SimpleNamespace(status_code=http_status,json=body)
    monkeypatch.setattr(requests,"post",send)
    with principal_context(ACTOR):
        if expected=="accepted":
            assert service.invite_registry_recipient(share.euid,"recipient@example.test")["status"]==expected
        else:
            with pytest.raises(HTTPException) as failure:
                service.invite_registry_recipient(share.euid,"recipient@example.test")
            assert failure.value.status_code==502
    assert service.backend.rows[-1].json_addl["status"]==expected
    assert calls[0]["json"]["share_url"]=="https://dewey.example.test/fetch/share-fixture"
    assert share.json_addl["status"]=="active" and share.json_addl["expires_at"] is None
