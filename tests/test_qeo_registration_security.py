from __future__ import annotations

from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.registration_contracts import (
    AnalysisArtifactSetRegistrationRequest,
    FileArtifact,
    manifest_sha256_for_request,
)
from dewey_service.service import DeweyConflictError


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _artifact(*, digest: str | None = None, role: str = "analysis_json") -> FileArtifact:
    key = "analysis/AN-3/result.json"
    return FileArtifact(
        logical_name="result-json",
        relative_path="qeo/result.json",
        storage_uri=f"s3://qeo-bucket/{key}",
        sha256=digest or _digest(key),
        size_bytes=100,
        mime_type="application/json",
        artifact_role=role,
        parser_hint="alignstats",
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )


def _request(artifact: FileArtifact) -> AnalysisArtifactSetRegistrationRequest:
    request = AnalysisArtifactSetRegistrationRequest(
        schema_version="1.0",
        analysis_euid="AN-000003",
        run_euid="RUN-000003",
        pipeline_name="daylily-omics-analysis",
        pipeline_version="1.2.3",
        workflow_engine="snakemake",
        workflow_engine_version="8.20.1",
        snakemake_version="8.20.1",
        workflow_git_sha="8205223c47f568211a301d11aa384615f1bdc395",
        workflow_config_sha256=_digest("config"),
        workflow_profile="slurm",
        generated_at="2026-05-26T18:15:00Z",
        manifest_sha256="0" * 64,
        status="registered",
        artifacts=[artifact],
        lineage_refs=[],
    )
    return request.model_copy(update={"manifest_sha256": manifest_sha256_for_request(request)})


def test_analysis_registration_route_requires_bearer(test_settings, service, storage) -> None:
    artifact = _artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-3/result.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    request = _request(artifact)
    app = create_app(settings=test_settings, service=service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        unauthenticated = client.post(
            "/api/v1/artifact-sets/analysis/register",
            json=request.model_dump(mode="json"),
        )
        authenticated = client.post(
            "/api/v1/artifact-sets/analysis/register",
            headers={"Authorization": "Bearer token-123"},
            json=request.model_dump(mode="json"),
        )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["status_code"] == 201


def test_no_mutable_artifact_rewrite_on_existing_storage_uri(service, storage) -> None:
    artifact = _artifact()
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-3/result.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    service.register_analysis_artifact_set(_request(artifact))

    conflicting = _artifact(digest=_digest("different"))
    storage.objects[("qeo-bucket", "analysis/AN-3/result.json")] = storage.objects[
        ("qeo-bucket", "analysis/AN-3/result.json")
    ].__class__(
        bucket="qeo-bucket",
        key="analysis/AN-3/result.json",
        size=conflicting.size_bytes,
        content_type=conflicting.mime_type,
        storage_class="STANDARD",
        etag="etag-2",
        sha256=conflicting.sha256,
    )

    with pytest.raises(DeweyConflictError, match="immutable registration manifest"):
        service.register_analysis_artifact_set(_request(conflicting))


def test_directory_artifact_requires_explicit_directory_shape(service) -> None:
    malformed = FileArtifact(
        logical_name="not-a-directory",
        relative_path="qeo/not-a-directory",
        storage_uri="s3://qeo-bucket/analysis/AN-3/not-a-directory",
        sha256=_digest("not-a-directory"),
        size_bytes=0,
        mime_type="inode/directory",
        artifact_role="directory",
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )

    with pytest.raises(ValueError, match="ending in '/'"):
        service.register_analysis_artifact_set(_request(malformed))
