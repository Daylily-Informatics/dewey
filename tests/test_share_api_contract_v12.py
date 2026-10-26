"""Breaking share schemas preserve omission and reject retired authority/delivery fields."""
import pytest
from pydantic import ValidationError
from dewey_service.app import ShareCreateRequest, ShareRootSubsetCreateRequest, ShareAccessPackageRequest
from dewey_service.registry_api import ShareRequest, LocationRebindRequest


@pytest.mark.parametrize("model,payload", [
    (ShareCreateRequest, {"target_kind":"artifact_object","target_euid":"artifact-fixture"}),
    (ShareRootSubsetCreateRequest, {"targets":[{"target_kind":"artifact_prefix","target_euid":"prefix-fixture"}]}),
    (ShareRequest, {}),
])
def test_omitted_expiry_survives_api_serialization(model, payload):
    assert "expires_at" not in model.model_validate(payload).model_dump(exclude_unset=True)
    assert model.model_validate({**payload,"expires_at":None}).model_dump(exclude_unset=True)["expires_at"] is None


@pytest.mark.parametrize("field,value", [("ttl_seconds",60),("allowed_groups",["admins"]),("owner_email","another@example.test")])
def test_obsolete_create_authority_and_ttl_payloads_fail(field,value):
    with pytest.raises(ValidationError):
        ShareCreateRequest.model_validate({"target_kind":"artifact_object","target_euid":"artifact-fixture",field:value})


def test_removed_presign_contract_and_invalid_revision_fail():
    with pytest.raises(ValidationError):
        ShareAccessPackageRequest.model_validate({"delivery_mode":"presigned"})
    with pytest.raises(ValidationError):
        ShareAccessPackageRequest.model_validate({"signed_ttl_seconds":900})
    with pytest.raises(ValidationError):
        LocationRebindRequest.model_validate({"storage_uri":"s3://fixture/target","expected_location_revision":0,"reason":"relocation"})
