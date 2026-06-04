from __future__ import annotations

from hashlib import sha256

import httpx

from dewey_service.registration_contracts import (
    AnalysisArtifactSetRegistrationRequest,
    FileArtifact,
    canonical_json,
    manifest_sha256_for_request,
)


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _request_with_sensitive_metadata(
    *,
    analysis_euid: str = "AN-000002",
    run_euid: str = "RUN-000002",
    key: str = "analysis/AN-2/qc-summary.json",
) -> AnalysisArtifactSetRegistrationRequest:
    artifact = FileArtifact(
        logical_name="qc-summary",
        relative_path="qeo/qc-summary.json",
        storage_uri=f"s3://qeo-bucket/{key}",
        sha256=_digest(key),
        size_bytes=64,
        mime_type="application/json",
        artifact_role="analysis_json",
        parser_hint="alignstats",
        required=True,
        produced_by="daylily-snakemake",
        parent_artifact_euids=[],
    )
    request = AnalysisArtifactSetRegistrationRequest(
        schema_version="1.0",
        analysis_euid=analysis_euid,
        run_euid=run_euid,
        workset_euid=None,
        project_euid=None,
        assay_id="NO-PHI-HERE",
        pipeline_name="daylily-omics-analysis",
        pipeline_version="1.2.3",
        workflow_engine="snakemake",
        workflow_engine_version="8.20.1",
        snakemake_version="8.20.1",
        workflow_git_sha="8205223c47f568211a301d11aa384615f1bdc395",
        workflow_config_sha256=_digest("config"),
        workflow_profile="slurm",
        generated_at="2026-05-26T18:10:00Z",
        manifest_sha256="0" * 64,
        parent_analysis_artifact_set_euid=None,
        rerun_of=None,
        status="registered",
        artifacts=[artifact],
        lineage_refs=[],
        parser_family_hint="alignstats",
    )
    return request.model_copy(update={"manifest_sha256": manifest_sha256_for_request(request)})


def test_analysis_registration_outbox_event(service, storage) -> None:
    request = _request_with_sensitive_metadata()
    artifact = request.artifacts[0]
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-2/qc-summary.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )

    _, receipt = service.register_analysis_artifact_set(request)
    events = service.list_outbox_events()

    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "lsmc.dewey.artifact_set.registered.v1"
    assert event["correlation_id"] == receipt["request_id"]
    assert event["payload"] == {
        "artifact_set_euid": receipt["artifact_set_euid"],
        "analysis_euid": request.analysis_euid,
        "manifest_sha256": request.manifest_sha256,
        "parser_family_hint": "alignstats",
    }
    assert event["dispatch_status"] == "pending"
    assert event["dispatch_attempt_count"] == 0


def test_qeo_outbox_dispatch_marks_parsed_success(service, storage, monkeypatch) -> None:
    request = _request_with_sensitive_metadata()
    artifact = request.artifacts[0]
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-2/qc-summary.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    service.register_analysis_artifact_set(request)
    sent: dict[str, object] = {}

    def fake_post(url, *, headers, json, timeout, verify):
        sent.update(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
                "verify": verify,
            }
        )
        return httpx.Response(
            200,
            json={
                "request_id": "qeo-request-1",
                "payload": {
                    "status": "PARSED",
                    "ingest_id": "qeo-ingest-1",
                    "qeo_ingestion_id": "qeo-parser-ingestion-1",
                    "artifact_set_euid": json["event"]["payload"]["artifact_set_euid"],
                },
            },
        )

    monkeypatch.setattr("dewey_service.services.outbox.httpx.post", fake_post)

    result = service.dispatch_qeo_outbox()

    assert result["attempted"] == 1
    assert result["counts"] == {"dispatched": 1}
    updated = result["results"][0]
    assert updated["dispatch_status"] == "dispatched"
    assert updated["dispatch_attempt_count"] == 1
    assert updated["last_dispatch_http_status"] == 200
    assert updated["qeo_request_id"] == "qeo-request-1"
    assert updated["qeo_ingest_id"] == "qeo-ingest-1"
    assert updated["qeo_parser_ingestion_id"] == "qeo-parser-ingestion-1"
    assert sent["url"] == "https://qeo.test/api/v1/ingest/dewey-events"
    assert sent["headers"] == {
        "Authorization": "Bearer qeo-token",
        "Content-Type": "application/json",
    }
    assert sent["json"]["consumer_group"] == "qeo.test"
    assert sent["json"]["event"]["event_type"] == "lsmc.dewey.artifact_set.registered.v1"


def test_qeo_outbox_dispatch_missing_explicit_config_fails_hard(service) -> None:
    service.qeo_ingest_url = ""

    try:
        service.dispatch_qeo_outbox()
    except RuntimeError as exc:
        assert "qeo.ingest_url is required" in str(exc)
    else:
        raise AssertionError("dispatch without qeo.ingest_url should fail")


def test_qeo_outbox_dispatch_filters_by_event_id(service, storage, monkeypatch) -> None:
    first = _request_with_sensitive_metadata()
    second = _request_with_sensitive_metadata(
        analysis_euid="AN-000003",
        run_euid="RUN-000003",
        key="analysis/AN-3/qc-summary.json",
    )
    for request in (first, second):
        artifact = request.artifacts[0]
        _, key = artifact.storage_uri.removeprefix("s3://").split("/", 1)
        storage.seed_object(
            bucket="qeo-bucket",
            key=key,
            size=artifact.size_bytes,
            content_type=artifact.mime_type,
            sha256=artifact.sha256,
        )
        service.register_analysis_artifact_set(request)

    target = next(
        event
        for event in service.list_outbox_events()
        if event["payload"]["analysis_euid"] == "AN-000003"
    )
    sent_event_ids: list[str] = []

    def fake_post(url, *, headers, json, timeout, verify):
        _ = url, headers, timeout, verify
        assert headers["Authorization"] == "Bearer qeo-token"
        sent_event_ids.append(json["event"]["event_id"])
        return httpx.Response(
            200,
            json={
                "payload": {
                    "status": "PARSED",
                    "artifact_set_euid": json["event"]["payload"]["artifact_set_euid"],
                }
            },
        )

    monkeypatch.setattr("dewey_service.services.outbox.httpx.post", fake_post)

    result = service.dispatch_qeo_outbox(event_ids={target["event_id"]})

    assert result["attempted"] == 1
    assert result["filters"] == {
        "event_ids": [target["event_id"]],
        "artifact_set_euids": [],
    }
    assert sent_event_ids == [target["event_id"]]
    statuses = {
        row["event_id"]: row["dispatch_status"] for row in service.list_outbox_events()
    }
    assert statuses[target["event_id"]] == "dispatched"
    other_event_id = next(
        row["event_id"]
        for row in service.list_outbox_events()
        if row["event_id"] != target["event_id"]
    )
    assert statuses[other_event_id] == "pending"


def test_qeo_outbox_dispatch_filters_by_artifact_set_euid(
    service, storage, monkeypatch
) -> None:
    first = _request_with_sensitive_metadata()
    second = _request_with_sensitive_metadata(
        analysis_euid="AN-000004",
        run_euid="RUN-000004",
        key="analysis/AN-4/qc-summary.json",
    )
    receipts = []
    for request in (first, second):
        artifact = request.artifacts[0]
        _, key = artifact.storage_uri.removeprefix("s3://").split("/", 1)
        storage.seed_object(
            bucket="qeo-bucket",
            key=key,
            size=artifact.size_bytes,
            content_type=artifact.mime_type,
            sha256=artifact.sha256,
        )
        _, receipt = service.register_analysis_artifact_set(request)
        receipts.append(receipt)
    target_artifact_set_euid = receipts[1]["artifact_set_euid"]
    sent_artifact_sets: list[str] = []

    def fake_post(url, *, headers, json, timeout, verify):
        _ = url, headers, timeout, verify
        sent_artifact_sets.append(json["event"]["payload"]["artifact_set_euid"])
        return httpx.Response(200, json={"payload": {"status": "PARSED"}})

    monkeypatch.setattr("dewey_service.services.outbox.httpx.post", fake_post)

    result = service.dispatch_qeo_outbox(
        artifact_set_euids={target_artifact_set_euid},
    )

    assert result["attempted"] == 1
    assert result["filters"] == {
        "event_ids": [],
        "artifact_set_euids": [target_artifact_set_euid],
    }
    assert sent_artifact_sets == [target_artifact_set_euid]
    pending = [
        row
        for row in service.list_outbox_events()
        if row["payload"]["artifact_set_euid"] != target_artifact_set_euid
    ]
    assert len(pending) == 1
    assert pending[0]["dispatch_status"] == "pending"


def test_qeo_outbox_dispatch_empty_filter_fails_hard(service) -> None:
    try:
        service.dispatch_qeo_outbox(event_ids={""})
    except ValueError as exc:
        assert "event_ids must include at least one non-empty value" in str(exc)
    else:
        raise AssertionError("empty event_id filter should fail")


def test_qeo_outbox_dispatch_records_dead_letter_error(service, storage, monkeypatch) -> None:
    request = _request_with_sensitive_metadata()
    artifact = request.artifacts[0]
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-2/qc-summary.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )
    service.register_analysis_artifact_set(request)

    def fake_post(url, *, headers, json, timeout, verify):
        _ = url, headers, json, timeout, verify
        return httpx.Response(
            200,
            json={
                "request_id": "qeo-request-2",
                "payload": {
                    "status": "DEAD_LETTERED",
                    "ingest_id": "qeo-ingest-2",
                    "dead_letter_id": "qeo-dead-letter-1",
                    "message": "parser-readable files missing",
                },
            },
        )

    monkeypatch.setattr("dewey_service.services.outbox.httpx.post", fake_post)

    result = service.dispatch_qeo_outbox()

    assert result["counts"] == {"error": 1}
    updated = result["results"][0]
    assert updated["dispatch_status"] == "error"
    assert updated["qeo_request_id"] == "qeo-request-2"
    assert updated["qeo_ingest_id"] == "qeo-ingest-2"
    assert updated["qeo_dead_letter_id"] == "qeo-dead-letter-1"
    assert updated["last_dispatch_error_class"] == "QeoIngestRejected"


def test_receipt_and_outbox_persist_once_on_replay(service, storage) -> None:
    request = _request_with_sensitive_metadata()
    artifact = request.artifacts[0]
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-2/qc-summary.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )

    service.register_analysis_artifact_set(request)
    service.register_analysis_artifact_set(request)

    assert len(service.list_registration_receipts()) == 1
    assert len(service.list_outbox_events()) == 1


def test_event_payload_omits_phi_paths_and_artifact_refs(service, storage) -> None:
    request = _request_with_sensitive_metadata()
    artifact = request.artifacts[0]
    storage.seed_object(
        bucket="qeo-bucket",
        key="analysis/AN-2/qc-summary.json",
        size=artifact.size_bytes,
        content_type=artifact.mime_type,
        sha256=artifact.sha256,
    )

    service.register_analysis_artifact_set(request)
    event_json = canonical_json(service.list_outbox_events()[0])

    denied_tokens = [
        "Patient",
        "sample",
        "storage_uri",
        "relative_path",
        "s3://",
        artifact.logical_name,
        artifact.storage_uri,
        artifact.relative_path,
    ]
    for token in denied_tokens:
        assert token not in event_json
