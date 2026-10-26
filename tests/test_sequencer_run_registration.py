from __future__ import annotations

import json
from copy import deepcopy

import pytest
from fastapi import HTTPException

from dewey_service.sequencer_run_contracts import (
    AnalysisResultArtifact,
    AnalysisResultsRegistrationRequest,
    FileEvidence,
    SequencerRunRegistrationRequest,
    deterministic_idempotency_key,
)
from dewey_service.service import DeweyService
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
)
from tests.support.service_fakes import _FakeStorageClient, _InMemoryBackend
from tests.support.sharing_v12_fakes import READER, actor, row
from tests.test_service_relationships import _managed_share_harness


def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Authorization": "Bearer token-123"}
    headers.update(extra or {})
    return headers


def _seed_illumina_run(storage: _FakeStorageClient) -> str:
    root = "runs/RUN-DIR-9901-RT4/"
    for key, size in [
        (f"{root}RunInfo.xml", 11),
        (f"{root}RunParameters.xml", 12),
        (f"{root}SampleSheet.csv", 13),
        (f"{root}InterOp/IndexMetricsOut.bin", 14),
        (f"{root}Reports/Demultiplex_Stats.csv", 15),
        (f"{root}Data/Intensities/BaseCalls/L001/C1.1/s_1_1101.bcl", 16),
        (f"{root}fastq/S1_R1_001.fastq.gz", 17),
        (f"{root}fastq/S1_R2_001.fastq.gz", 18),
    ]:
        storage.seed_object(bucket="seq-bucket", key=key, size=size)
    storage.put_bytes(
        bucket="seq-bucket",
        key=f"{root}RUN-DIR-9901-RT4.analysis_pipeline_order.tsv",
        body=(
            "illumina_snv_alignstats_relatedness_vep_multiqc\t{}\tnew\t"
            "2026-05-26T00:00:00Z\tqueued\t2026-05-26T00:00:00Z\n"
        ).encode("utf-8"),
        content_type="text/tab-separated-values",
    )
    return "s3://seq-bucket/runs/RUN-DIR-9901-RT4/"


def test_register_sequencer_run_selects_needed_files_and_records_outbox(
    service: DeweyService,
    storage: _FakeStorageClient,
    backend: _InMemoryBackend,
) -> None:
    root_uri = _seed_illumina_run(storage)
    body = SequencerRunRegistrationRequest(
        run_root_uri=root_uri,
        platform="ILMN",
        trigger_policy="trigger_ursa",
        run_euid="RUN-EUID-1",
        expected_files=[
            FileEvidence(
                logical_name="sample sheet",
                relative_path="SampleSheet.csv",
                artifact_role="sample_sheet",
                size_bytes=13,
            )
        ],
    )

    status_code, payload = service.register_sequencer_run(
        request_body=body,
        idempotency_key=None,
        request_id="req-1",
        correlation_id="corr-1",
    )

    assert status_code == 201
    assert payload["artifact_set"]["artifact_set_type"] == "sequencer_run"
    assert payload["manifest_sha256"]
    manifest_paths = {row["relative_path"] for row in payload["manifest"]}
    assert "SampleSheet.csv" in manifest_paths
    assert "fastq/S1_R1_001.fastq.gz" in manifest_paths
    assert "Data/Intensities/BaseCalls/L001/C1.1/s_1_1101.bcl" not in manifest_paths
    assert {item["pipeline_code"] for item in payload["pipeline_plan"]} == {
        "illumina_run_qc",
        "illumina_snv_alignstats_relatedness_vep_multiqc",
    }
    file_rows = [row for row in payload["manifest"] if row["storage_kind"] == "object"]
    assert {row["storage_status"] for row in file_rows} == {"observed"}
    event_payload = payload["outbox_event"]["payload"]
    assert "run_root_uri" not in event_payload
    assert "sample_name" not in event_payload

    receipt_rows = backend.instances[REGISTRATION_RECEIPT_TEMPLATE]
    outbox_rows = backend.instances[OUTBOX_EVENT_TEMPLATE]
    assert len(receipt_rows) == 1
    assert len(outbox_rows) == 1

    replay_code, replay_payload = service.register_sequencer_run(
        request_body=body,
        idempotency_key=deterministic_idempotency_key("sequencer_run.register", body),
        request_id="req-2",
        correlation_id="corr-2",
    )
    assert replay_code == 201
    assert replay_payload["receipt_euid"] == payload["receipt_euid"]


def test_register_sequencer_run_rejects_required_file_and_manifest_mismatch(
    service: DeweyService,
    storage: _FakeStorageClient,
    backend: _InMemoryBackend,
) -> None:
    root_uri = _seed_illumina_run(storage)
    with pytest.raises(ValueError, match="size mismatch"):
        service.register_sequencer_run(
            request_body=SequencerRunRegistrationRequest(
                run_root_uri=root_uri,
                platform="ILMN",
                trigger_policy="register_only",
                expected_files=[
                    FileEvidence(
                        logical_name="sample sheet",
                        relative_path="SampleSheet.csv",
                        artifact_role="sample_sheet",
                        size_bytes=999,
                    )
                ],
            ),
            idempotency_key=None,
            request_id="req-3",
            correlation_id="corr-3",
        )
    assert backend.instances.get(ARTIFACT_TEMPLATE) is None

    with pytest.raises(Exception, match="required run artifact missing"):
        service.register_sequencer_run(
            request_body=SequencerRunRegistrationRequest(
                run_root_uri=root_uri,
                platform="ILMN",
                trigger_policy="register_only",
                expected_files=[
                    FileEvidence(
                        logical_name="missing",
                        relative_path="missing.fastq.gz",
                        artifact_role="fastq",
                    )
                ],
            ),
            idempotency_key=None,
            request_id="req-4",
            correlation_id="corr-4",
        )

    with pytest.raises(ValueError, match="manifest_sha256 mismatch"):
        service.register_sequencer_run(
            request_body=SequencerRunRegistrationRequest(
                run_root_uri=root_uri,
                platform="ILMN",
                trigger_policy="register_only",
                expected_manifest_sha256="f" * 64,
            ),
            idempotency_key=None,
            request_id="req-5",
            correlation_id="corr-5",
        )


def test_register_analysis_results_links_samples_and_non_phi_event(
    service: DeweyService,
    storage: _FakeStorageClient,
    backend: _InMemoryBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_assertions = []

    def record_owner_assertion(session, *, source, **assertion):
        # The owner service is outside this unit fixture; preserve its exact contract.
        assert session is backend
        assert source in backend.instances[ARTIFACT_TEMPLATE]
        owner_assertions.append({"source_euid": source.euid, **assertion})

    monkeypatch.setattr(
        "dewey_service.services.sequencer_runs.attach_analysis_result_owner_reference",
        record_owner_assertion,
    )
    storage.seed_object(
        bucket="analysis-bucket",
        key="results/A1/multiqc_report.html",
        size=200,
        version_id="vid-1",
        content_type="text/html",
    )
    body = AnalysisResultsRegistrationRequest(
        analysis_euid="AN-EUID-1",
        command_id="illumina_snv_alignstats_relatedness_vep_multiqc",
        result_status="succeeded",
        result_root_uri="s3://analysis-bucket/results/A1/",
        run_artifact_set_euid="AS-RUN-1",
        sample_identifiers=[{"sample_euid": "fixture-sample"}],
        metadata={
            "registration_contract": "analysis_results.v1",
            "artifact_manifest_rows": [
                {
                    "relative_path": "multiqc_report.html",
                    "importable": True,
                    "result_s3_uri": "s3://analysis-bucket/results/A1/multiqc_report.html",
                    "artifact_role": "multiqc_html",
                    "size_bytes": 200,
                    "version_id": "vid-1",
                    "mime_type": "text/html",
                }
            ],
            "artifact_lineage": [
                {
                    "path": "multiqc_report.html",
                    "entity_type": "sample",
                    "entity_euid": "fixture-sample",
                    "relationship": "results_for_sample",
                    "source": "fixture-manifest",
                }
            ],
            "entity_owner_systems": {"sample": "bloom"},
        },
        artifacts=[
            AnalysisResultArtifact(
                logical_name="multiqc_report.html",
                artifact_role="multiqc_html",
                relative_path="multiqc_report.html",
                storage_uri="s3://analysis-bucket/results/A1/multiqc_report.html",
                size_bytes=200,
                version_id="vid-1",
                mime_type="text/html",
                sample_identifiers=[{"sample_euid": "fixture-sample"}],
            )
        ],
    )

    status_code, payload = service.register_analysis_results(
        request_body=body,
        idempotency_key=None,
        request_id="req-6",
        correlation_id="corr-6",
    )

    assert status_code == 201
    assert payload["artifact_set"]["artifact_set_type"] == "analysis_results"
    sample_assertions = [
        assertion
        for assertion in owner_assertions
        if assertion["relationship_type"] == "results_for_sample"
    ]
    assert len(sample_assertions) == 1
    assert sample_assertions[0]["owner_system"] == "bloom"
    assert sample_assertions[0]["owner_object_euid"] == "fixture-sample"
    assert sample_assertions[0]["owner_object_type"] == "sample"
    assert json.loads(sample_assertions[0]["assertion_provenance"]) == {
        "contract": "analysis_results.v1",
        "path": "multiqc_report.html",
        "source": "fixture-manifest",
    }
    execution_assertions = [
        assertion
        for assertion in owner_assertions
        if assertion["relationship_type"] == "produced_by_analysis_execution"
    ]
    assert len(execution_assertions) == 2
    assert {item["owner_object_euid"] for item in execution_assertions} == {body.analysis_euid}
    event_payload = payload["outbox_event"]["payload"]
    assert event_payload == {
        "artifact_set_euid": payload["artifact_set"]["artifact_set_euid"],
        "analysis_euid": "AN-EUID-1",
        "manifest_sha256": payload["manifest_sha256"],
        "command_id": "illumina_snv_alignstats_relatedness_vep_multiqc",
        "result_status": "succeeded",
    }
    assert "patient" not in str(event_payload).lower()
    assert "sample_name" not in str(event_payload).lower()


def test_route_requires_deterministic_idempotency_key(client) -> None:
    body = {
        "run_root_uri": "s3://seq-bucket/runs/RUN-DIR-9901-RT4/",
        "platform": "ILMN",
        "trigger_policy": "register_only",
    }
    response = client.post(
        "/api/v1/sequencer-runs/register",
        headers=_auth_headers({"Idempotency-Key": "wrong-key"}),
        json=body,
    )
    assert response.status_code == 409

    response = client.post(
        "/api/v1/sequencer-runs/register",
        headers=_auth_headers(),
        json=body,
    )
    assert response.status_code == 200
    assert response.json()["receipt"]["registration_kind"] == "sequencer_run"

    analysis_response = client.post(
        "/api/v1/analysis-results/register",
        headers=_auth_headers(),
        json={
            "analysis_euid": "AN-EUID-ROUTE",
            "command_id": "illumina_snv_alignstats_relatedness_vep_multiqc",
            "result_status": "succeeded",
            "result_root_uri": "s3://analysis-bucket/results/route/",
            "artifacts": [
                {
                    "logical_name": "multiqc",
                    "artifact_role": "multiqc_html",
                    "relative_path": "multiqc_report.html",
                }
            ],
        },
    )
    assert analysis_response.status_code == 200
    assert analysis_response.json()["receipt"]["registration_kind"] == "analysis_results"


def test_browser_sequencer_run_registration_requires_session(client) -> None:
    response = client.post(
        "/sequencer-runs/register",
        data={
            "run_root_uri": "s3://seq-bucket/runs/RUN-DIR-9901-RT4/",
            "platform": "ILMN",
            "trigger_policy": "register_only",
            "metadata_json": "{}",
        },
        follow_redirects=False,
    )
    assert response.status_code in {303, 401, 403}


def test_browser_share_reference_route_is_removed(client) -> None:
    routes = [
        route
        for route in client.app.routes
        if getattr(route, "path", None) == "/share-references/{share_reference_euid}"
        and "GET" in getattr(route, "methods", set())
    ]
    assert routes == []
    response = client.get("/share-references/SH-000001", follow_redirects=False)
    assert response.status_code == 404


def test_create_share_does_not_persist_presigned_urls() -> None:
    harness = _managed_share_harness()
    service = harness.service
    artifact_a = harness.artifact(
        "fixture-artifact-a", key="a.txt", storage_uri="s3://fixture-source/a.txt", size=1
    )
    artifact_b = harness.artifact(
        "fixture-artifact-b", key="b.txt", storage_uri="s3://fixture-source/b.txt", size=1
    )
    artifact_set = harness.add(row("artifact_set", "fixture-artifact-set"))
    for artifact in (artifact_a, artifact_b):
        harness.link(
            harness.session,
            parent=artifact_set,
            child=artifact,
            relationship_type="artifact_set_member",
        )
    harness.query_rows = [artifact_a, artifact_b]
    with actor():
        _, share = service.create_share(
            target_kind="artifact_set",
            target_euid=artifact_set.euid,
            name="artifact set share",
            purpose="download",
            allowed_users=[READER.email],
            delivery_modes=["gateway"],
            expires_at=None,
            idempotency_key="share-create",
        )

    assert "manifest" not in share
    assert {item["artifact_euid"] for item in share["members"]} == {
        artifact_a.euid,
        artifact_b.euid,
    }
    persisted_before = [deepcopy(instance.json_addl) for instance in harness.rows]
    with actor(READER):
        issued = service.create_share_access_package(share["share_euid"])
        assert issued["browser_path"] == f"/fetch/{share['share_euid']}"
        assert issued["manifest_path"] == f"/fetch/{share['share_euid']}?format=manifest"
        assert issued["archive_path"] == f"/fetch/{share['share_euid']}?format=tar"
        with pytest.raises(HTTPException) as removed:
            service.create_share_access_package(
                share["share_euid"], delivery_mode="presigned_s3_manifest"
            )
        assert removed.value.status_code == 410

    assert "signed_url" not in repr(issued)
    assert "signed_url" not in repr(share)
    assert "X-Amz-Signature" not in repr(persisted_before)
    assert [instance.json_addl for instance in harness.rows] == persisted_before
