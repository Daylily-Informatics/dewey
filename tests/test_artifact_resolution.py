from __future__ import annotations


def test_resolve_artifact_and_set(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-res-art-1"},
        json={
            "artifact_type": "vcf",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": "out/var.vcf.gz",
        },
    ).json()

    artifact_set = client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-res-set-1"},
        json={"artifact_set_type": "result_bundle"},
    ).json()

    client.post(
        f"/api/v1/artifact-sets/{artifact_set['artifact_set_euid']}/members",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-res-member-1"},
        json={"artifact_euid": artifact["artifact_euid"]},
    )

    resolved_artifact = client.post(
        "/api/v1/resolve/artifact",
        headers={"Authorization": "Bearer token-123"},
        json={"artifact_euid": artifact["artifact_euid"]},
    )
    assert resolved_artifact.status_code == 200
    assert resolved_artifact.json()["storage_uri"] == "s3://bucket-1/out/var.vcf.gz"

    resolved_set = client.post(
        "/api/v1/resolve/artifact-set",
        headers={"Authorization": "Bearer token-123"},
        json={"artifact_set_euid": artifact_set["artifact_set_euid"]},
    )
    assert resolved_set.status_code == 200
    assert resolved_set.json()["artifact_euids"] == [artifact["artifact_euid"]]
