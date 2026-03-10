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
