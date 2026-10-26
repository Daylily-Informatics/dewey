from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dewey_service.labcore_owner_contracts import (
    CONTRACT_TYPE,
    CONTRACT_VERSION,
    HASH_DOMAIN,
    LabcoreSequencingRunOwnerContractV1,
    bind_request_hash,
    canonical_request_bytes,
    canonical_request_sha256,
)
from dewey_service.sequencer_run_contracts import SequencerRunRegistrationRequest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts/dynamic_workflow/labcore_sequencing_run_owner.v1.schema.json"
GOLDEN_PATH = ROOT / "contracts/dynamic_workflow/labcore_sequencing_run_owner.v1.golden.json"


def _golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _raw() -> dict:
    return copy.deepcopy(_golden()["raw"])


def test_committed_schema_and_cross_language_golden_match_model() -> None:
    golden = _golden()
    bound = bind_request_hash(golden["raw"])
    model = LabcoreSequencingRunOwnerContractV1.model_validate(bound)

    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) == model.model_json_schema()
    assert golden["contract_type"] == CONTRACT_TYPE
    assert golden["version"] == CONTRACT_VERSION
    assert golden["hash_domain"] == HASH_DOMAIN
    assert model.model_dump(mode="json") == golden["normalized"]
    assert (
        base64.b64encode(canonical_request_bytes(model)).decode("ascii")
        == golden["canonical_utf8_base64"]
    )
    assert canonical_request_sha256(model) == golden["sha256"]
    assert model.request_sha256 == model.idempotency_key == golden["sha256"]


def test_canonical_hash_is_stable_across_mapping_order() -> None:
    raw = _raw()
    reversed_raw = dict(reversed(list(raw.items())))
    assert canonical_request_bytes(raw) == canonical_request_bytes(reversed_raw)
    assert canonical_request_sha256(raw) == canonical_request_sha256(reversed_raw)


def test_validated_contract_is_deeply_immutable() -> None:
    model = LabcoreSequencingRunOwnerContractV1.model_validate(bind_request_hash(_raw()))

    with pytest.raises(ValidationError, match="Instance is frozen"):
        model.tenant_euid = "TENANT-DIFFERENT"
    with pytest.raises(ValidationError, match="Instance is frozen"):
        model.expected_files[0].relative_path = "different.fastq.gz"
    with pytest.raises(AttributeError):
        model.expected_files.append(model.expected_files[0])
    with pytest.raises(ValidationError, match="Instance is frozen"):
        model.expected_files = ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("external_system", "bloom"),
        ("external_system", "atlas"),
        ("external_object_type", "run"),
        ("relation_type", "sequencing_run"),
        ("target_type", "artifact_set"),
        ("platform", "illumina"),
    ],
)
def test_closed_literals_fail_without_aliases(field: str, value: str) -> None:
    raw = _raw()
    raw[field] = value
    with pytest.raises(ValidationError):
        bind_request_hash(raw)


def test_owner_identity_and_hash_identities_must_match() -> None:
    raw = _raw()
    raw["external_object_id"] = "M-SRUN-DIFFERENT"
    with pytest.raises(ValidationError, match="external_object_id must equal"):
        bind_request_hash(raw)

    bound = bind_request_hash(_raw())
    bound["request_sha256"] = "f" * 64
    with pytest.raises(ValidationError, match="canonical request hash"):
        LabcoreSequencingRunOwnerContractV1.model_validate(bound)

    bound = bind_request_hash(_raw())
    bound["idempotency_key"] = "e" * 64
    with pytest.raises(ValidationError, match="must equal request_sha256"):
        LabcoreSequencingRunOwnerContractV1.model_validate(bound)


def test_contract_forbids_unknown_phi_or_mutable_authority_fields() -> None:
    for forbidden in (
        "patient_name",
        "sample_name",
        "bloom_run_euid",
        "atlas_order_euid",
        "lifecycle_state",
        "metadata",
    ):
        raw = _raw()
        raw[forbidden] = "not-allowed"
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            bind_request_hash(raw)

    raw = _raw()
    raw["expected_files"][0]["patient_id"] = "not-allowed"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        bind_request_hash(raw)


def test_required_tenant_site_and_evidence_are_strict() -> None:
    for field in (
        "tenant_euid",
        "processing_site_euid",
        "dataset_revision",
        "inventory_sha256",
        "labcore_binding_receipt_id",
        "labcore_binding_receipt_sha256",
    ):
        raw = _raw()
        raw.pop(field)
        with pytest.raises(ValidationError, match="Field required"):
            bind_request_hash(raw)

    raw = _raw()
    raw["expected_files"] = []
    with pytest.raises(ValidationError):
        bind_request_hash(raw)

    raw = _raw()
    raw["expected_files"][0]["size_bytes"] = "512"
    with pytest.raises(ValidationError):
        bind_request_hash(raw)

    raw = _raw()
    raw["expected_files"].append(copy.deepcopy(raw["expected_files"][0]))
    with pytest.raises(ValidationError, match="relative_path values must be unique"):
        bind_request_hash(raw)


def test_dataset_root_and_file_paths_have_one_normal_form() -> None:
    raw = _raw()
    raw["dataset_root_uri"] = "  s3://lsmc-internal-test/runs/M-SRUN-0001  "
    bound = bind_request_hash(raw)
    assert bound["dataset_root_uri"] == "s3://lsmc-internal-test/runs/M-SRUN-0001/"

    for invalid in (
        "https://example.test/run/",
        "s3://bucket/run/?version=1",
        "s3://user@bucket/run/",
        "s3://bucket:443/run/",
        "s3://bucket/run/./current/",
        "s3://bucket/run/../other/",
    ):
        raw = _raw()
        raw["dataset_root_uri"] = invalid
        with pytest.raises(ValidationError):
            bind_request_hash(raw)

    raw = _raw()
    raw["expected_files"][0]["relative_path"] = "../secret.txt"
    with pytest.raises(ValidationError):
        bind_request_hash(raw)


def test_existing_bloom_registration_contract_remains_accepted() -> None:
    legacy = SequencerRunRegistrationRequest(
        run_root_uri="s3://legacy-bucket/runs/RUN-1/",
        platform="ILMN",
        trigger_policy="register_only",
        bloom_run_euid="BLM-RUN-1",
    )
    assert legacy.bloom_run_euid == "BLM-RUN-1"
