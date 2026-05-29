from __future__ import annotations


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer token-123",
        "Idempotency-Key": "idem-artifact-1",
    }


def test_register_artifact(client) -> None:
    response = client.post(
        "/api/v1/artifacts",
        headers=_auth_headers(),
        json={
            "artifact_type": "fastq",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "runs/RUN-1/read1.fastq.gz",
            "producer_system": "bloom",
            "producer_object_euid": "RUN-1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_code"] == 201
    assert payload["artifact_euid"].startswith("AT-")
    assert payload["artifact_type"] == "fastq"


def test_import_artifact_from_s3_uri(client) -> None:
    response = client.post(
        "/api/v1/artifacts/import",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-import-1"},
        json={
            "artifact_type": "vcf",
            "storage_uri": "s3://bucket-2/path/sample.vcf.gz",
            "metadata": {"producer_system": "ursa", "producer_object_euid": "AN-1"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_code"] == 201
    assert payload["bucket"] == "bucket-2"
    assert payload["key"] == "path/sample.vcf.gz"
    assert payload["import_mode"] == "reference"


def test_register_artifact_prefix_api(client) -> None:
    response = client.post(
        "/api/v1/artifact-prefixes",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-prefix-api"},
        json={
            "artifact_type": "folder",
            "root_uri": "s3://bucket-2/path/prefix",
            "producer_system": "atlas",
            "producer_object_euid": "RUN-2",
            "metadata": {"tags": ["prefix"], "title": "Prefix Only"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_code"] == 201
    assert payload["storage_kind"] == "prefix"
    assert payload["node_kind"] == "prefix"
    assert payload["is_terminal"] is False
    assert payload["bucket"] == "bucket-2"
    assert payload["key"] == "path/prefix/"
    assert payload["storage_uri"] == "s3://bucket-2/path/prefix/"
    assert payload["source_uri"] == "s3://bucket-2/path/prefix/"
    assert payload["metadata"]["title"] == "Prefix Only"


def test_upload_session_round_trip(client) -> None:
    create = client.post(
        "/api/v1/artifacts/upload-sessions",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-upload-create"},
        json={
            "artifact_type": "report",
            "original_filename": "case-report.pdf",
            "content_type": "application/pdf",
            "producer_system": "atlas",
            "producer_object_euid": "REL-1",
        },
    )
    assert create.status_code == 200
    created = create.json()
    assert created["status_code"] == 201
    assert created["upload_token"].startswith("upload-")

    complete = client.post(
        f"/api/v1/artifacts/upload-sessions/{created['upload_token']}/complete",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-upload-complete"},
        json={"checksums": {"sha256": "abc123"}},
    )
    assert complete.status_code == 200
    payload = complete.json()
    assert payload["status_code"] == 201
    assert payload["import_mode"] == "upload"
