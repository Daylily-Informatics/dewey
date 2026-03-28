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


def test_get_artifact_and_artifact_set_routes_return_registered_state(client) -> None:
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-get-art-1"},
        json={
            "artifact_type": "report",
            "storage_backend": "s3",
            "bucket": "bucket-2",
            "key": "reports/case-report.pdf",
            "original_filename": "case-report.pdf",
            "producer_system": "atlas",
            "metadata": {"case_id": "CASE-22"},
        },
    ).json()

    artifact_set = client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-get-set-1"},
        json={
            "artifact_set_type": "report_bundle",
            "label": "Case 22",
            "description": "Primary case outputs",
        },
    ).json()

    client.post(
        f"/api/v1/artifact-sets/{artifact_set['artifact_set_euid']}/members",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-get-member-1"},
        json={"artifact_euid": artifact["artifact_euid"]},
    )

    fetched_artifact = client.get(
        f"/api/v1/artifacts/{artifact['artifact_euid']}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched_artifact.status_code == 200
    artifact_payload = fetched_artifact.json()
    assert "status_code" not in artifact_payload
    assert artifact_payload["artifact_euid"] == artifact["artifact_euid"]
    assert artifact_payload["storage_uri"] == artifact["storage_uri"]
    assert artifact_payload["metadata"] == {"case_id": "CASE-22"}

    fetched_set = client.get(
        f"/api/v1/artifact-sets/{artifact_set['artifact_set_euid']}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched_set.status_code == 200
    assert fetched_set.json()["artifact_euids"] == [artifact["artifact_euid"]]
    assert fetched_set.json()["members"][0]["original_filename"] == "case-report.pdf"


def test_list_artifact_sets_route_filters_by_type(client) -> None:
    client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-list-set-1"},
        json={"artifact_set_type": "report_bundle", "label": "Bundle A"},
    )
    client.post(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-list-set-2"},
        json={"artifact_set_type": "delivery_package", "label": "Bundle B"},
    )

    listed = client.get(
        "/api/v1/artifact-sets",
        headers={"Authorization": "Bearer token-123"},
        params={"artifact_set_type": "report_bundle", "limit": 10},
    )
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 1
    assert payload["items"][0]["artifact_set_type"] == "report_bundle"
    assert payload["items"][0]["label"] == "Bundle A"
