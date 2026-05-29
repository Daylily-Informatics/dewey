from __future__ import annotations

from hashlib import sha256

from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.registration_contracts import (
    FileArtifact,
    MultiQCArtifactSetRegistrationRequest,
    manifest_sha256_for_request,
)


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _object_artifact(
    *,
    logical_name: str,
    key: str,
    role: str,
    mime_type: str,
    parser_hint: str | None = "multiqc",
    size_bytes: int = 256,
) -> FileArtifact:
    return FileArtifact(
        logical_name=logical_name,
        relative_path=f"multiqc/{logical_name}",
        storage_uri=f"s3://qeo-bucket/{key}",
        sha256=_digest(key),
        size_bytes=size_bytes,
        mime_type=mime_type,
        artifact_role=role,
        parser_hint=parser_hint,
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )


def _directory_artifact() -> FileArtifact:
    return FileArtifact(
        logical_name="multiqc-data-dir",
        relative_path="multiqc/multiqc_data/",
        storage_uri="s3://qeo-bucket/analysis/AN-1/multiqc/multiqc_data/",
        sha256=_digest("multiqc-data-dir"),
        size_bytes=0,
        mime_type="inode/directory",
        artifact_role="directory",
        parser_hint="multiqc_data",
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )


def _multiqc_request(*, local_only: bool = False) -> MultiQCArtifactSetRegistrationRequest:
    request = MultiQCArtifactSetRegistrationRequest(
        schema_version="1.0",
        analysis_euid="AN-000001",
        report_kind="multiqc_general",
        multiqc_version="1.25.1",
        html_artifact=_object_artifact(
            logical_name="multiqc-report-html",
            key="analysis/AN-1/multiqc/multiqc_report.html",
            role="multiqc_html",
            mime_type="text/html",
        ),
        data_dir_artifact=_directory_artifact(),
        key_files=[
            _object_artifact(
                logical_name="multiqc-data-json",
                key="analysis/AN-1/multiqc/multiqc_data/multiqc_data.json",
                role="multiqc_key_file",
                mime_type="application/json",
            )
        ],
        parser_relevant_files=[
            _object_artifact(
                logical_name="fastqc-section-tsv",
                key="analysis/AN-1/multiqc/multiqc_data/fastqc.tsv",
                role="parser_relevant_file",
                mime_type="text/tab-separated-values",
                parser_hint="fastqc",
            )
        ],
        generated_at="2026-05-26T18:05:00Z",
        manifest_sha256="0" * 64,
        local_only=local_only,
        parser_family_hint="multiqc",
    )
    return request.model_copy(update={"manifest_sha256": manifest_sha256_for_request(request)})


def _seed_multiqc_storage(storage, request: MultiQCArtifactSetRegistrationRequest) -> None:
    for artifact in [
        request.html_artifact,
        *request.key_files,
        *request.parser_relevant_files,
    ]:
        _, path = artifact.storage_uri.removeprefix("s3://").split("/", 1)
        storage.seed_object(
            bucket="qeo-bucket",
            key=path,
            size=artifact.size_bytes,
            content_type=artifact.mime_type,
            sha256=artifact.sha256,
        )


def test_multiqc_directory_and_key_file_registration(service, storage) -> None:
    request = _multiqc_request()
    _seed_multiqc_storage(storage, request)

    code, receipt = service.register_multiqc_artifact_set(request)
    artifact_set = service.get_artifact_set(receipt["artifact_set_euid"])

    assert code == 201
    assert receipt["status"] == "registered"
    assert receipt["artifact_set_kind"] == "multiqc_artifact_set"
    assert receipt["report_kind"] == "multiqc_general"
    assert receipt["manifest_sha256"] == request.manifest_sha256
    assert receipt["source_service"] == "dewey"
    assert receipt["parser_hint"] == "multiqc"
    assert artifact_set["artifact_set_type"] == "multiqc_artifact_set"
    assert artifact_set["member_count"] == 4
    roles = {item["artifact_role"] for item in receipt["registered_artifacts"]}
    assert roles == {
        "multiqc_html",
        "directory",
        "multiqc_key_file",
        "parser_relevant_file",
    }

    resolved = service.resolve_artifact_set(receipt["artifact_set_euid"])
    assert resolved["artifact_set_kind"] == "multiqc_artifact_set"
    assert resolved["report_kind"] == "multiqc_general"
    assert resolved["manifest_sha256"] == request.manifest_sha256
    assert "artifact_euids" not in resolved


def test_multiqc_local_only_receipt_and_outbox(service, storage) -> None:
    request = _multiqc_request(local_only=True)
    _seed_multiqc_storage(storage, request)

    _, receipt = service.register_multiqc_artifact_set(request)
    outbox = service.list_outbox_events()

    assert receipt["status"] == "local_only"
    assert outbox[0]["dispatch_status"] == "local_only"
    assert outbox[0]["local_only"] is True


def test_multiqc_registration_route_auth_and_computed_idempotency(
    test_settings,
    service,
    storage,
) -> None:
    request = _multiqc_request()
    _seed_multiqc_storage(storage, request)
    app = create_app(settings=test_settings, service=service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        unauthenticated = client.post(
            "/api/v1/artifact-sets/multiqc/register",
            json=request.model_dump(mode="json"),
        )
        authenticated = client.post(
            "/api/v1/artifact-sets/multiqc/register",
            headers={"Authorization": "Bearer token-123"},
            json=request.model_dump(mode="json"),
        )
        resolved = client.post(
            "/api/v1/resolve/artifact-set",
            headers={"Authorization": "Bearer token-123"},
            json={"artifact_set_euid": authenticated.json()["artifact_set_euid"]},
        )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["status_code"] == 201
    assert authenticated.json()["artifact_set_euid"].startswith("AS-")
    assert resolved.status_code == 200
    assert resolved.json()["artifact_set_kind"] == "multiqc_artifact_set"
    assert resolved.json()["manifest_sha256"] == request.manifest_sha256
