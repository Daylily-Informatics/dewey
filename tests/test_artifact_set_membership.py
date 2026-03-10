from __future__ import annotations


def _register_artifact(client, idem: str) -> str:
    response = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": idem},
        json={
            "artifact_type": "bam",
            "storage_backend": "s3",
            "bucket": "bucket-1",
            "key": f"reads/{idem}.bam",
        },
    )
    return response.json()["artifact_euid"]


def test_create_artifact_set_and_add_member(client) -> None:
    artifact_euid = _register_artifact(client, "idem-artifact-set-member")

    create_set = client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-set-1"},
        json={"artifact_set_type": "analysis_output", "label": "Set 1"},
    )
    assert create_set.status_code == 200
    set_payload = create_set.json()
    artifact_set_euid = set_payload["artifact_set_euid"]

    add_member = client.post(
        f"/api/v1/artifact-sets/{artifact_set_euid}/members",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-set-member-1"},
        json={"artifact_euid": artifact_euid},
    )
    assert add_member.status_code == 200
    add_payload = add_member.json()
    assert artifact_euid in add_payload["artifact_euids"]


def test_remove_artifact_set_member(client) -> None:
    artifact_euid = _register_artifact(client, "idem-artifact-set-member-rm")
    create_set = client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-set-rm-1"},
        json={"artifact_set_type": "analysis_output"},
    )
    artifact_set_euid = create_set.json()["artifact_set_euid"]

    client.post(
        f"/api/v1/artifact-sets/{artifact_set_euid}/members",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-set-rm-2"},
        json={"artifact_euid": artifact_euid},
    )

    remove = client.delete(
        f"/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-set-rm-3"},
    )
    assert remove.status_code == 200
    assert artifact_euid not in remove.json()["artifact_euids"]
