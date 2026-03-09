from __future__ import annotations

from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import Settings
from dewey_service.store import InMemoryArtifactStore


def _app():
    settings = Settings(
        api_bearer_token="token-123",
        operator_username="operator",
        operator_password="pw-123",
        session_secret_key="session-secret",
    )
    return create_app(settings=settings, store=InMemoryArtifactStore())


def test_api_requires_bearer_token() -> None:
    with TestClient(_app()) as client:
        response = client.post(
            "/api/v1/artifacts",
            json={"artifact_type": "vcf", "storage_uri": "s3://bucket/a.vcf.gz"},
        )
    assert response.status_code == 401


def test_artifact_and_set_flow() -> None:
    headers = {"Authorization": "Bearer token-123"}
    with TestClient(_app()) as client:
        create_artifact = client.post(
            "/api/v1/artifacts",
            headers=headers,
            json={"artifact_type": "vcf", "storage_uri": "s3://bucket/a.vcf.gz"},
        )
        assert create_artifact.status_code == 200, create_artifact.text
        artifact_euid = create_artifact.json()["artifact_euid"]
        assert artifact_euid.startswith("AT-")

        create_set = client.post(
            "/api/v1/artifact-sets",
            headers=headers,
            json={"artifact_set_type": "analysis_output"},
        )
        assert create_set.status_code == 200, create_set.text
        artifact_set_euid = create_set.json()["artifact_set_euid"]
        assert artifact_set_euid.startswith("AS-")

        add_member = client.post(
            f"/api/v1/artifact-sets/{artifact_set_euid}/members",
            headers=headers,
            json={"artifact_euid": artifact_euid},
        )
        assert add_member.status_code == 200, add_member.text
        assert add_member.json()["artifact_euids"] == [artifact_euid]

        resolve_artifact = client.post(
            "/api/v1/resolve/artifact",
            headers=headers,
            json={"artifact_euid": artifact_euid},
        )
        assert resolve_artifact.status_code == 200, resolve_artifact.text
        assert resolve_artifact.json()["storage_uri"] == "s3://bucket/a.vcf.gz"

        resolve_set = client.post(
            "/api/v1/resolve/artifact-set",
            headers=headers,
            json={"artifact_set_euid": artifact_set_euid},
        )
        assert resolve_set.status_code == 200, resolve_set.text
        assert resolve_set.json()["artifact_euids"] == [artifact_euid]

        share_reference = client.post(
            "/api/v1/share-references",
            headers=headers,
            json={"target_type": "artifact", "target_euid": artifact_euid},
        )
        assert share_reference.status_code == 200, share_reference.text
        assert share_reference.json()["share_reference_euid"].startswith("SH-")
