from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest

from dewey_service.service import DeweyService
from tests.support.service_fakes import _FakeStorageClient


def _login_user(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "johnm@lsmc.com",
            "sub": "sub-johnm",
            "name": "John Major",
            "cognito:groups": ["dewey-readwrite"],
        },
    )
    login = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302


def test_service_import_run_prefix_creates_hierarchy_and_freeze_behavior(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    root_uri = "s3://bucket-9/basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/"
    sample_a = "504352-UGAv3-1527-CAACGATATGTGAT"
    sample_b = "504352-UGAv3-1528-CGATACGATATGTGAT"
    for key in [
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_a}/{sample_a}.cram",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_a}/{sample_a}.cram.crai",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_a}/{sample_a}.json",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_a}/{sample_a}.csv",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_a}/{sample_a}.h5",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_b}/{sample_b}_unmatched.cram",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_b}/{sample_b}_unmatched.cram.crai",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_b}/{sample_b}_unmatched.json",
        f"basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/{sample_b}/{sample_b}_unmatched.csv",
    ]:
        storage.seed_object(bucket="bucket-9", key=key, size=1024)

    status_code, payload = service.import_run_prefix(
        root_uri=root_uri,
        platform="ultima",
        owner_email="johnm@lsmc.com",
        idempotency_key="idem-run-prefix-live",
    )

    assert status_code == 201
    run_artifact = payload["run_artifact"]
    assert run_artifact["storage_kind"] == "prefix"
    assert run_artifact["node_kind"] == "run_folder"
    assert run_artifact["metadata"]["run_id"] == "RUN504352"
    assert run_artifact["metadata"]["owner_email"] == "johnm@lsmc.com"

    run_children = service.list_artifact_children(artifact_euid=run_artifact["artifact_euid"])
    assert {item["original_filename"] for item in run_children} == {sample_a, sample_b}
    sample_a_node = next(item for item in run_children if item["original_filename"] == sample_a)
    assert sample_a_node["node_kind"] == "sample_folder"
    assert sample_a_node["is_terminal"] is False
    assert sample_a_node["metadata"]["seq_index"] == "CAACGATATGTGAT"

    sample_a_children = service.list_artifact_children(artifact_euid=sample_a_node["artifact_euid"])
    assert {item["artifact_type"] for item in sample_a_children} == {"cram", "crai", "json", "csv"}
    assert {item["storage_status"] for item in sample_a_children} == {"observed"}
    cram_artifact = next(item for item in sample_a_children if item["artifact_type"] == "cram")
    cram_parents = service.list_artifact_parents(artifact_euid=cram_artifact["artifact_euid"])
    assert [item["artifact_euid"] for item in cram_parents] == [sample_a_node["artifact_euid"]]

    with pytest.raises(ValueError, match="object-backed artifact"):
        service.verify_artifact_storage(
            artifact_euid=run_artifact["artifact_euid"],
            idempotency_key="idem-run-prefix-verify",
        )
    with pytest.raises(ValueError, match="object-backed artifact"):
        service.lock_artifact_storage(
            artifact_euid=run_artifact["artifact_euid"],
            mode="GOVERNANCE",
            retain_until="2028-01-01T00:00:00Z",
            idempotency_key="idem-run-prefix-lock",
        )
    with pytest.raises(ValueError, match="object-backed artifact"):
        service.create_share(
            target_kind="artifact_object",
            target_euid=run_artifact["artifact_euid"],
            targets=[],
            name=None,
            purpose="download",
            owner_email="johnm@lsmc.com",
            allowed_users=[],
            allowed_domains=[],
            allowed_groups=[],
            delivery_modes=["presigned_s3"],
            expires_at=None,
            ttl_seconds=None,
            idempotency_key="idem-run-prefix-share",
        )

    freeze_code, freeze_payload = service.import_run_prefix(
        root_uri=root_uri,
        platform="ultima",
        owner_email="johnm@lsmc.com",
        finalize=True,
        idempotency_key="idem-run-prefix-freeze",
    )
    assert freeze_code in {200, 201}
    assert freeze_payload["run_state"] == "frozen"

    storage.seed_object(
        bucket="bucket-9",
        key=(
            "basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/"
            "504352-UGAv3-1529-ATGCATGCATGCATGC/"
            "504352-UGAv3-1529-ATGCATGCATGCATGC.cram"
        ),
        size=1024,
    )
    frozen_code, frozen_payload = service.import_run_prefix(
        root_uri=root_uri,
        platform="ultima",
        owner_email="johnm@lsmc.com",
        idempotency_key="idem-run-prefix-frozen-rerun",
    )
    assert frozen_code == 200
    assert frozen_payload["run_state"] == "frozen"
    assert frozen_payload["folder_nodes"] == {"created": 0, "updated": 0}


def test_run_prefix_api_routes_support_bearer_and_session_auth(monkeypatch, client) -> None:
    bearer_response = client.post(
        "/api/v1/artifacts/import-run-prefix",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-api-run-prefix-bearer",
        },
        json={
            "root_uri": "s3://bucket-1/basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/",
            "platform": "ultima",
            "owner_email": "johnm@lsmc.com",
            "run_id": "RUN504352",
        },
    )
    assert bearer_response.status_code == 200
    run_artifact = bearer_response.json()["run_artifact"]
    assert run_artifact["storage_kind"] == "prefix"
    assert run_artifact["node_kind"] == "run_folder"

    children = client.get(
        f"/api/v1/artifacts/{run_artifact['artifact_euid']}/children",
        headers={"Authorization": "Bearer token-123"},
    )
    assert children.status_code == 200
    assert children.json()["total"] == 2
    folder_artifact = children.json()["items"][0]

    parents = client.get(
        f"/api/v1/artifacts/{folder_artifact['artifact_euid']}/parents",
        headers={"Authorization": "Bearer token-123"},
    )
    assert parents.status_code == 200
    assert parents.json()["items"][0]["artifact_euid"] == run_artifact["artifact_euid"]

    verify = client.post(
        f"/api/v1/artifacts/{run_artifact['artifact_euid']}/storage/verify",
        headers={
            "Authorization": "Bearer token-123",
            "Idempotency-Key": "idem-api-run-prefix-verify",
        },
    )
    assert verify.status_code == 400

    _login_user(monkeypatch, client)
    session_response = client.post(
        "/api/v1/artifacts/import-run-prefix",
        headers={"Idempotency-Key": "idem-api-run-prefix-session"},
        json={
            "root_uri": "s3://bucket-2/basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/",
            "platform": "ultima",
            "owner_email": "johnm@lsmc.com",
            "run_id": "RUN504352",
            "finalize": True,
        },
    )
    assert session_response.status_code == 200
    assert session_response.json()["run_state"] == "frozen"


def test_run_prefix_ui_flow_renders_hierarchy_detail(monkeypatch, client, fake_service) -> None:
    _login_user(monkeypatch, client)

    intake = client.post(
        "/artifacts/import-run-prefix",
        data={
            "root_uri": "s3://bucket-3/basecalls/lsmc/ssf-hq/RUN504352/2026/504352-20260404_1215/",
            "platform": "ultima",
            "owner_email": "johnm@lsmc.com",
            "run_id": "RUN504352",
            "finalize": "no",
        },
    )
    assert intake.status_code == 200
    assert "Sequencing Run Intake" in intake.text
    assert "Run Artifact" in intake.text

    run_artifact = next(
        item for item in fake_service.artifacts.values() if item["node_kind"] == "run_folder"
    )
    detail = client.get(f"/artifacts/euid/{run_artifact['artifact_euid']}")
    assert detail.status_code == 200
    assert "Hierarchy" in detail.text
    assert "Open In Console" in detail.text
    assert "Prefix nodes use prefix or mixed-set shares from the Shares page." in detail.text
    assert f'action="/artifacts/euid/{run_artifact["artifact_euid"]}/download"' not in detail.text
