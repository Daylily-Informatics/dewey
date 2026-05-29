from __future__ import annotations

from hashlib import sha256

import pytest

from dewey_service.registration_contracts import (
    AnalysisArtifactSetRegistrationRequest,
    FileArtifact,
    canonical_sha256,
    computed_registration_idempotency_key,
    manifest_sha256_for_request,
)
from dewey_service.service import DeweyConflictError, DeweyNotFoundError


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _file_artifact(
    *,
    logical_name: str = "alignstats-json",
    key: str = "analysis/AN-1/alignstats.json",
    size_bytes: int = 128,
    digest: str | None = None,
    artifact_role: str = "analysis_json",
    parser_hint: str | None = "alignstats",
) -> FileArtifact:
    checksum = digest or _digest(key)
    return FileArtifact(
        logical_name=logical_name,
        relative_path=f"manifest/{logical_name}.json",
        storage_uri=f"s3://qeo-bucket/{key}",
        sha256=checksum,
        size_bytes=size_bytes,
        mime_type="application/json",
        artifact_role=artifact_role,
        parser_hint=parser_hint,
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )


def _analysis_request(
    artifact: FileArtifact,
    *,
    analysis_euid: str = "AN-000001",
    parent_analysis_artifact_set_euid: str | None = None,
    rerun_of: str | None = None,
    local_only: bool = False,
) -> AnalysisArtifactSetRegistrationRequest:
    request = AnalysisArtifactSetRegistrationRequest(
        schema_version="1.0",
        analysis_euid=analysis_euid,
        run_euid="RUN-000001",
        workset_euid="WS-000001",
        project_euid="PRJ-000001",
        assay_id="assay-1",
        pipeline_name="daylily-omics-analysis",
        pipeline_version="1.2.3",
        workflow_engine="snakemake",
        workflow_engine_version="8.20.1",
        snakemake_version="8.20.1",
        workflow_git_sha="8205223c47f568211a301d11aa384615f1bdc395",
        workflow_config_sha256=_digest("workflow-config"),
        workflow_profile="slurm",
        generated_at="2026-05-26T18:00:00Z",
        manifest_sha256="0" * 64,
        parent_analysis_artifact_set_euid=parent_analysis_artifact_set_euid,
        rerun_of=rerun_of,
        status="registered",
        artifacts=[artifact],
        lineage_refs=[],
        local_only=local_only,
        parser_family_hint="alignstats",
    )
    return request.model_copy(update={"manifest_sha256": manifest_sha256_for_request(request)})


def test_deterministic_manifest_hashing() -> None:
    artifact = _file_artifact()
    request = _analysis_request(artifact)
    shuffled = {
        "status": request.status,
        "artifacts": [artifact.model_dump(mode="json")],
        "schema_version": request.schema_version,
        "analysis_euid": request.analysis_euid,
        "run_euid": request.run_euid,
        "workset_euid": request.workset_euid,
        "project_euid": request.project_euid,
        "assay_id": request.assay_id,
        "pipeline_name": request.pipeline_name,
        "pipeline_version": request.pipeline_version,
        "workflow_engine": request.workflow_engine,
        "workflow_engine_version": request.workflow_engine_version,
        "snakemake_version": request.snakemake_version,
        "workflow_git_sha": request.workflow_git_sha,
        "workflow_config_sha256": request.workflow_config_sha256,
        "workflow_profile": request.workflow_profile,
        "generated_at": request.generated_at,
        "manifest_sha256": "0" * 64,
        "parent_analysis_artifact_set_euid": None,
        "rerun_of": None,
        "lineage_refs": [],
        "local_only": False,
        "parser_family_hint": "alignstats",
    }
    assert manifest_sha256_for_request(request) == request.manifest_sha256
    assert canonical_sha256(shuffled) == canonical_sha256(
        AnalysisArtifactSetRegistrationRequest.model_validate(shuffled)
    )


def test_analysis_artifact_set_registration_replay(service, storage) -> None:
    artifact = _file_artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-1/alignstats.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    request = _analysis_request(artifact)

    first_code, first = service.register_analysis_artifact_set(request)
    second_code, second = service.register_analysis_artifact_set(request)

    assert first_code == second_code == 201
    assert first == second
    assert first["artifact_set_euid"].startswith("AS-")
    assert first["registered_artifacts"][0]["artifact_role"] == "analysis_json"
    assert service.get_artifact_set(first["artifact_set_euid"])["member_count"] == 1
    assert len(service.list_outbox_events()) == 1


def test_idempotency_key_mismatch_rejected(service, storage) -> None:
    artifact = _file_artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-1/alignstats.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    request = _analysis_request(artifact)

    with pytest.raises(DeweyConflictError, match="Idempotency-Key does not match"):
        service.register_analysis_artifact_set(request, idempotency_key="wrong-key")


def test_checksum_mismatch_rejection(service, storage) -> None:
    artifact = _file_artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-1/alignstats.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=_digest("different"),
    )
    request = _analysis_request(artifact)

    with pytest.raises(ValueError, match="sha256 mismatch"):
        service.register_analysis_artifact_set(request)


def test_required_artifact_missing_rejected_before_mutation(service, backend) -> None:
    artifact = _file_artifact()
    request = _analysis_request(artifact)

    with pytest.raises(DeweyNotFoundError, match="Required artifact missing"):
        service.register_analysis_artifact_set(request)

    assert service.list_artifact_sets() == []
    assert backend.lineages == []


def test_artifact_set_rerun_linkage(service, storage, backend) -> None:
    parent_artifact = _file_artifact(
        logical_name="parent-report",
        key="analysis/parent/report.json",
    )
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/parent/report.json",
        size=parent_artifact.size_bytes,
        content_type=parent_artifact.mime_type,
        sha256=parent_artifact.sha256,
    )
    _, parent_receipt = service.register_analysis_artifact_set(
        _analysis_request(parent_artifact, analysis_euid="AN-PARENT")
    )

    child_artifact = _file_artifact(
        logical_name="child-report",
        key="analysis/child/report.json",
    )
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/child/report.json",
        size=child_artifact.size_bytes,
        content_type=child_artifact.mime_type,
        sha256=child_artifact.sha256,
    )
    parent_set = parent_receipt["artifact_set_euid"]
    service.register_analysis_artifact_set(
        _analysis_request(
            child_artifact,
            analysis_euid="AN-CHILD",
            parent_analysis_artifact_set_euid=parent_set,
            rerun_of=parent_set,
        )
    )

    relationship_types = {lineage.relationship_type for lineage in backend.lineages}
    assert "analysis_artifact_set_parent" in relationship_types
    assert "analysis_artifact_set_rerun_of" in relationship_types


def test_reprocessing_creates_new_set_and_skips_existing_artifact(service, storage) -> None:
    artifact = _file_artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-1/alignstats.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    first_request = _analysis_request(artifact, analysis_euid="AN-000001")
    second_request = _analysis_request(artifact, analysis_euid="AN-000002")

    _, first = service.register_analysis_artifact_set(first_request)
    _, second = service.register_analysis_artifact_set(second_request)

    assert first["artifact_set_euid"] != second["artifact_set_euid"]
    assert second["registered_artifacts"] == []
    assert second["skipped_existing"][0]["artifact_euid"] == first["registered_artifacts"][0][
        "artifact_euid"
    ]


def test_supplied_matching_idempotency_key_is_accepted(service, storage) -> None:
    artifact = _file_artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-1/alignstats.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    request = _analysis_request(artifact)
    key = computed_registration_idempotency_key(request)

    code, receipt = service.register_analysis_artifact_set(request, idempotency_key=key)

    assert code == 201
    assert receipt["idempotency_key"] == key
