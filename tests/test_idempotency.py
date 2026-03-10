from __future__ import annotations


def test_register_artifact_idempotent_replay(client) -> None:
    headers = {"Authorization": "Bearer token-123", "Idempotency-Key": "idem-replay-1"}
    payload = {
        "artifact_type": "fastq",
        "storage_backend": "s3",
        "bucket": "bucket-1",
        "key": "reads/r1.fastq.gz",
    }
    first = client.post("/api/v1/artifacts", headers=headers, json=payload)
    second = client.post("/api/v1/artifacts", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["artifact_euid"] == second.json()["artifact_euid"]


def test_register_artifact_idempotency_conflict(client) -> None:
    headers = {"Authorization": "Bearer token-123", "Idempotency-Key": "idem-conflict-1"}
    payload_a = {
        "artifact_type": "fastq",
        "storage_backend": "s3",
        "bucket": "bucket-1",
        "key": "reads/a.fastq.gz",
    }
    payload_b = {
        "artifact_type": "fastq",
        "storage_backend": "s3",
        "bucket": "bucket-1",
        "key": "reads/b.fastq.gz",
    }
    first = client.post("/api/v1/artifacts", headers=headers, json=payload_a)
    second = client.post("/api/v1/artifacts", headers=headers, json=payload_b)
    assert first.status_code == 200
    assert second.status_code == 409
    assert "Idempotency-Key reuse" in second.json()["detail"]


def test_mutation_requires_idempotency_key(client) -> None:
    response = client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123"},
        json={"artifact_set_type": "bundle"},
    )
    assert response.status_code == 400
    assert "Idempotency-Key" in response.json()["detail"]
