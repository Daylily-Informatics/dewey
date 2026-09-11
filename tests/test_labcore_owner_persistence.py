from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dewey_service.labcore_owner_command import (
    COMMAND_TYPE,
    COMMAND_VERSION,
    HASH_DOMAIN,
    LabcoreSequencingRunRegistrationCommandV2,
    bind_registration_command,
)
from dewey_service.labcore_owner_contracts import (
    LabcoreSequencingRunOwnerContractV1,
    bind_request_hash,
)
from dewey_service.service import DeweyConflictError, DeweyService
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
)
from tests.labcore_owner_support import LocalTransactionalBackend


@pytest.fixture(autouse=True)
def unit_external_attachment(monkeypatch):
    monkeypatch.setattr(
        "dewey_service.services.labcore_owner.attach_external_relation",
        lambda session, relation: None,
    )


GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "contracts/dynamic_workflow/labcore_sequencing_run_owner.v1.golden.json"
)


def _command(
    target_euid: str = "AT-000001",
    *,
    tenant_euid: str = "TENANT-INTERNAL-TEST",
    test_euid: str = "TEST-A",
) -> LabcoreSequencingRunRegistrationCommandV2:
    raw = json.loads(GOLDEN.read_text(encoding="utf-8"))["raw"]
    raw.update({"target_euid": target_euid, "tenant_euid": tenant_euid})
    frozen = LabcoreSequencingRunOwnerContractV1.model_validate(bind_request_hash(raw))
    return LabcoreSequencingRunRegistrationCommandV2.model_validate(
        bind_registration_command(
            {
                "command_type": COMMAND_TYPE,
                "command_version": COMMAND_VERSION,
                "hash_domain": HASH_DOMAIN,
                "test_euid": test_euid,
                "owner_request": frozen.model_dump(mode="json"),
            }
        )
    )


def _seed_artifact(
    backend: LocalTransactionalBackend, command: LabcoreSequencingRunRegistrationCommandV2
) -> None:
    request = command.owner_request
    payload = request.model_dump(mode="json")
    owner = {
        field: payload[field]
        for field in (
            "tenant_euid",
            "processing_site_euid",
            "platform",
            "dataset_root_uri",
            "dataset_revision",
            "inventory_sha256",
            "labcore_binding_receipt_id",
            "labcore_binding_receipt_sha256",
            "labcore_sequencing_run_euid",
        )
    }
    owner.update({"test_euid": command.test_euid, "expected_files": payload["expected_files"]})
    artifact = backend.create_instance(
        None,
        template_code=ARTIFACT_TEMPLATE,
        name=request.target_euid,
        json_addl={
            "artifact_type": "sequencing_run",
            "storage_kind": "prefix",
            "storage_backend": "s3",
            "storage_uri": request.dataset_root_uri,
            "producer_system": "labcore",
            "producer_object_euid": request.labcore_sequencing_run_euid,
            "metadata": {"labcore_owner": owner},
        },
    )
    assert artifact.euid == request.target_euid


def _service(command: LabcoreSequencingRunRegistrationCommandV2):
    backend = LocalTransactionalBackend()
    _seed_artifact(backend, command)
    return DeweyService(backend), backend


def test_service_validates_artifact_and_testeuid_binding() -> None:
    command = _command()
    service, backend = _service(command)
    code, receipt = service.register_labcore_sequencing_run_owner(
        request_body=command, principal_id="unit-caller"
    )
    assert code == 201
    assert receipt["command_sha256"] == command.command_sha256
    assert backend.count(EXTERNAL_OBJECT_TEMPLATE) == 1

    service, backend = _service(command)
    wrong_test = _command(test_euid="TEST-B")
    assert wrong_test.owner_request == command.owner_request
    assert wrong_test.command_sha256 != command.command_sha256
    with pytest.raises(DeweyConflictError):
        service.register_labcore_sequencing_run_owner(
            request_body=wrong_test, principal_id="unit-caller"
        )
    assert backend.count(EXTERNAL_OBJECT_TEMPLATE) == 0

    invalid = command.model_dump(mode="json")
    invalid["command_sha256"] = "0" * 64
    invalid["idempotency_key"] = "0" * 64
    with pytest.raises(ValidationError):
        LabcoreSequencingRunRegistrationCommandV2.model_validate(invalid)


def test_v2_command_identity_fields_are_required_literals() -> None:
    command = _command()
    payload = command.model_dump(mode="json")
    for field in ("command_type", "command_version", "hash_domain"):
        missing = dict(payload)
        missing.pop(field)
        with pytest.raises(ValidationError):
            LabcoreSequencingRunRegistrationCommandV2.model_validate(missing)
        wildcard = dict(payload)
        wildcard[field] = "X" if field != "command_version" else 3
        with pytest.raises(ValidationError):
            LabcoreSequencingRunRegistrationCommandV2.model_validate(wildcard)
    schema = LabcoreSequencingRunRegistrationCommandV2.model_json_schema()
    assert {"command_type", "command_version", "hash_domain"} <= set(schema["required"])
    assert schema["properties"]["command_type"]["const"] == COMMAND_TYPE
    assert schema["properties"]["command_version"]["const"] == COMMAND_VERSION
    assert schema["properties"]["hash_domain"]["const"] == HASH_DOMAIN


def test_service_rolls_back_only_its_staged_authority() -> None:
    command = _command()
    service, backend = _service(command)
    backend.fail_template = REGISTRATION_RECEIPT_TEMPLATE
    with pytest.raises(RuntimeError, match="forced persistence failure"):
        service.register_labcore_sequencing_run_owner(
            request_body=command, principal_id="unit-caller"
        )
    for template in (
        EXTERNAL_OBJECT_TEMPLATE,
        EXTERNAL_OBJECT_RELATION_TEMPLATE,
        REGISTRATION_RECEIPT_TEMPLATE,
        IDEMPOTENCY_TEMPLATE,
    ):
        assert backend.count(template) == 0
