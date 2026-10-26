from __future__ import annotations

import pytest
from fastapi import HTTPException

from dewey_service.literature import ViewerContext
from dewey_service.registry_access import Principal, principal_context
from dewey_service.service import DeweyService
from tests.support.service_fakes import _FakeStorageClient


def test_artifact_set_search_scope_and_retired_share_transport_rejection(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    storage.seed_object(
        bucket="bucket-8",
        key="release/one.txt",
        size=12,
        content_type="text/plain",
    )
    storage.seed_object(
        bucket="bucket-8",
        key="release/two.txt",
        size=12,
        content_type="text/plain",
    )
    _, first = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-8",
        key="release/one.txt",
        version_id=None,
        size=12,
        checksums=None,
        content_type="text/plain",
        original_filename="one.txt",
        producer_system="atlas",
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata={"study_id": "ST-8"},
        idempotency_key="idem-set-share-artifact-1",
    )
    _, second = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket="bucket-8",
        key="release/two.txt",
        version_id=None,
        size=12,
        checksums=None,
        content_type="text/plain",
        original_filename="two.txt",
        producer_system="atlas",
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata={"study_id": "ST-8"},
        idempotency_key="idem-set-share-artifact-2",
    )
    _, artifact_set = service.create_artifact_set(
        artifact_set_type="release",
        label="March Release",
        description="Artifact delivery bundle.",
        metadata={"program": "oncology", "cohort": "A"},
        idempotency_key="idem-set-share-create",
    )
    service.add_artifact_set_member(
        artifact_set_euid=artifact_set["artifact_set_euid"],
        artifact_euid=first["artifact_euid"],
        idempotency_key="idem-set-share-member-1",
    )
    service.add_artifact_set_member(
        artifact_set_euid=artifact_set["artifact_set_euid"],
        artifact_euid=second["artifact_euid"],
        idempotency_key="idem-set-share-member-2",
    )

    search = service.query_search_v2(
        {
            "scopes": ["artifact_set"],
            "page_size": 25,
            "property_filters": [{"path": "metadata.program", "op": "eq", "value": "oncology"}],
        }
    )
    assert search["total"] == 1
    assert search["items"][0]["artifact_set_euid"] == artifact_set["artifact_set_euid"]

    before = len(service.backend.instances.get("access/share/generic/1.0/", []))
    with pytest.raises(HTTPException) as removed:
        service.create_share_access_package(
            "fixture-retired-share", delivery_mode="presigned_s3_manifest"
        )
    assert removed.value.status_code == 410
    assert "authenticated /fetch" in removed.value.detail
    assert len(service.backend.instances.get("access/share/generic/1.0/", [])) == before


def test_upload_complete_verify_lock_and_search(
    service: DeweyService,
    storage: _FakeStorageClient,
) -> None:
    session_code, upload_session = service.create_upload_session(
        artifact_type="report",
        original_filename="case-report.pdf",
        content_type="application/pdf",
        producer_system="atlas",
        producer_object_euid="REL-1",
        metadata={"case_id": "CASE-1"},
        lock_after_import=False,
        idempotency_key="idem-upload-create",
    )
    assert session_code == 201

    storage.seed_object(
        bucket=upload_session["bucket"],
        key=upload_session["key"],
        size=2048,
        content_type="application/pdf",
    )
    complete_code, artifact = service.complete_upload_session(
        upload_token=upload_session["upload_token"],
        checksums={"sha256": "abc123"},
        metadata={"case_id": "CASE-1"},
        idempotency_key="idem-upload-complete",
    )
    assert complete_code == 201
    assert artifact["import_mode"] == "upload"
    assert artifact["storage_status"] == "verified"

    verify_code, verified = service.verify_artifact_storage(
        artifact_euid=artifact["artifact_euid"],
        idempotency_key="idem-verify-1",
    )
    assert verify_code == 200
    assert verified["storage_status"] == "verified"

    lock_code, locked = service.lock_artifact_storage(
        artifact_euid=artifact["artifact_euid"],
        mode="GOVERNANCE",
        retain_until="2027-01-01T00:00:00Z",
        idempotency_key="idem-lock-1",
    )
    assert lock_code == 200
    assert locked["retention_mode"] == "GOVERNANCE"

    query = service.query_search_v2(
        {
            "scopes": ["artifact"],
            "page": 1,
            "page_size": 25,
            "property_filters": [
                {"path": "import_mode", "op": "eq", "value": "upload"},
                {"path": "metadata.case_id", "op": "eq", "value": "CASE-1"},
            ],
        }
    )
    assert query["total"] == 1
    assert query["items"][0]["artifact_euid"] == artifact["artifact_euid"]

    export_rows, timing_ms, truncated = service.collect_search_export_rows(
        {
            "scopes": ["artifact"],
            "page_size": 25,
            "max_rows": 25,
        }
    )
    assert timing_ms >= 0
    assert truncated is False
    assert export_rows[0]["record_type"] == "artifact"


def test_literature_query_search_v2_enrichment(service: DeweyService) -> None:
    viewer = ViewerContext(
        subject="sub-1",
        email="owner@example.com",
        groups=("dewey-readwrite",),
    )

    service.save_literature(
        viewer=viewer,
        pmid="789012",
        save_mode="external_reference",
        visibility_scope="all_users",
        allowed_users=[],
        allowed_groups=[],
        idempotency_key="lit-search-1",
    )

    # The verified principal owns visibility; a caller-supplied ViewerContext
    # cannot impersonate another user's save summary.
    with principal_context(
        Principal(
            subject=viewer.subject,
            email=viewer.email,
            groups=viewer.groups,
            roles=("ADMIN",),
            internal=True,
            email_verified=True,
        )
    ):
        result = service.query_search_v2(
            {
                "scopes": ["artifact"],
                "page": 1,
                "page_size": 25,
                "property_filters": [{"path": "pmid", "op": "eq", "value": "789012"}],
            },
            viewer_context=ViewerContext(
                subject="different-viewer", email="different@example.test", groups=()
            ),
        )

    assert result["total"] == 1
    item = result["items"][0]
    assert item["artifact_type"] == "literature"
    assert item["pmid"] == "789012"
    assert item["storage_mode"] == "external_reference"
    assert item["saved_by_me"] is True


@pytest.mark.parametrize(
    "query",
    [
        {"scopes": ["unknown"]},
        {"scopes": ["", "artifact"]},
        {"scopes": []},
        {"property_filters": [{"path": "metadata.type", "op": "typo"}]},
        {"property_filters": [{"path": ""}]},
        {"property_filters": [{"path": "metadata..type"}]},
        {"property_filters": ["not-an-object"]},
        {"property_filters": {}},
        {"sort_field": "unknown"},
        {"sort_dir": "typo"},
        {"sort_dir": ""},
        {"sort_field": ""},
        {"property_filters": [{"path": "metadata.type", "op": ""}]},
    ],
)
def test_invalid_search_has_no_match_all_fallback_on_empty_database(service, query):
    with pytest.raises(ValueError):
        service.query_search_v2(query)


def test_search_wrapper_preserves_text_query_and_export_bound(service, monkeypatch):
    calls = []
    response = {"items": [{"euid": "fixture-visible-result"}], "total": 2}
    monkeypatch.setattr(
        service, "search_registry", lambda request: calls.append(dict(request)) or response
    )
    query = {"q": "CASE-1", "scopes": ["artifact"], "page": 4, "max_rows": 1}
    assert service.query_search_v2(query) is response
    rows, timing, truncated = service.collect_search_export_rows(query)
    assert rows == response["items"] and truncated is True and timing >= 0
    assert calls == [query, {**query, "page": 1, "page_size": 1}]
    assert query["page"] == 4
