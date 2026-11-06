"""S3 browser contracts using local provider/authorization fixtures only."""

from contextlib import nullcontext
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from dewey_service.deletion_policy import DeletionProhibitionMiddleware
from dewey_service.registry_access import Principal, principal_context
from dewey_service.services.registry_storage import RegistryStorageServiceMixin
from dewey_service.storage import StorageObject, StoragePrefix
from tests.test_storage_unit import _client, _FakeS3Backend


def test_listing_preserves_dates_and_only_exact_markers_without_extra_s3_calls():
    backend = _FakeS3Backend()
    stamp = datetime(2026, 7, 11, 4, 36, 36, tzinfo=timezone.utc)
    backend.list_objects_v2_response = {
        "CommonPrefixes": [{"Prefix": "docs/known/"}, {"Prefix": "docs/unknown/"}],
        "Contents": [
            {"Key": "docs/", "Size": 0, "LastModified": stamp},
            {"Key": "docs/known/", "Size": 0, "LastModified": stamp},
            {"Key": "docs/report.tsv", "Size": 12, "LastModified": stamp,
             "StorageClass": "GLACIER", "ETag": '"multipart-2"'},
        ],
        "IsTruncated": True,
        "NextContinuationToken": "another-page",
    }
    result = _client(backend).browse_prefix(bucket="fixture", prefix="docs/", limit=25, cache_ttl=0)
    assert result["prefixes"] == [
        StoragePrefix("fixture", "docs/known/", stamp.isoformat()),
        StoragePrefix("fixture", "docs/unknown/"),
    ]
    assert result["objects"] == [StorageObject(
        bucket="fixture", key="docs/report.tsv", size=12, storage_class="GLACIER",
        etag="multipart-2", last_modified=stamp.isoformat(),
    )]
    assert result["next_continuation_token"] == "another-page"
    assert backend.calls == [("list_objects_v2", {
        "Bucket": "fixture", "Prefix": "docs/", "Delimiter": "/", "MaxKeys": 25,
    })]


def test_browser_response_preserves_metadata_and_filters_unauthorized_rows():
    service = RegistryStorageServiceMixin()
    calls = []
    stamp = "2026-07-11T04:36:36+00:00"
    def browse(**kwargs):
        calls.append(kwargs)
        return {
            "prefixes": [StoragePrefix("fixture", "docs/folder/", stamp)],
            "objects": [
                StorageObject("fixture", "docs/report.tsv", size=12, etag="multi-2",
                              storage_class="STANDARD", last_modified=stamp),
                StorageObject("fixture", "docs/private.tsv", size=99, last_modified=stamp),
            ],
            "next_continuation_token": "next", "is_truncated": True,
        }
    service._require_storage = lambda: SimpleNamespace(browse_prefix=browse)
    service.backend = SimpleNamespace(session_scope=lambda **kwargs: nullcontext(object()))
    service.registry_defaults = lambda: {"listing_cache_ttl_seconds": 30}
    service._storage_access_batch = lambda session, bucket, keys, indicators=None: (
        {key: key != "docs/private.tsv" for key in keys}, {},
    )
    result = service.registry_browse("s3://fixture/docs/", limit=25)
    assert len(calls) == 1
    assert [row["key"] for row in result["items"]] == ["docs/folder/", "docs/report.tsv"]
    folder, file = result["items"]
    assert folder["marker_last_modified"] == stamp
    assert "last_modified" not in folder and "size" not in folder
    assert {key: file[key] for key in ("last_modified", "size", "storage_class", "etag")} == {
        "last_modified": stamp, "size": 12, "storage_class": "STANDARD", "etag": "multi-2",
    }
    assert result["next_continuation_token"] == "next"


@pytest.mark.parametrize("method,path", [
    ("DELETE", "/api/v1/storage/object"),
    ("POST", "/api/v1/storage/deletions/preview"),
    ("POST", "/api/v1/storage/deletions/Z-operation/execute"),
])
def test_browser_destructive_routes_reject_before_handler(method, path):
    app = FastAPI()
    @app.api_route(path, methods=[method])
    def unreachable():
        raise AssertionError("Deletion reached a backend handler")
    app.add_middleware(DeletionProhibitionMiddleware)
    response = TestClient(app).request(method, path)
    assert response.status_code == 403
    assert "including administrators" in response.json()["detail"]


def test_admin_cannot_delete_replace_or_upload_over_an_existing_key():
    service = RegistryStorageServiceMixin()
    admin = Principal(subject="Z-admin", roles=("ADMIN",), internal=True)
    with principal_context(admin):
        with pytest.raises(HTTPException) as deleted:
            service.require_storage_access("fixture", "existing", action="delete")
        assert deleted.value.status_code == 403
        with pytest.raises(HTTPException) as replacement:
            service.begin_registry_upload(uri="s3://fixture/existing", size=1,
                                          content_type="text/plain", replace_etag="known")
        assert replacement.value.status_code == 403
        service._require_storage = lambda: SimpleNamespace(
            head_object=lambda **kwargs: StorageObject("fixture", "existing", etag="known"),
        )
        with pytest.raises(HTTPException) as existing:
            service.begin_registry_upload(uri="s3://fixture/existing", size=1, content_type="text/plain")
        assert existing.value.status_code == 409


def test_new_key_completion_is_atomic_create_only():
    backend = _FakeS3Backend()
    _client(backend).complete_multipart(bucket="fixture", key="new", upload_id="Z-upload",
                                      parts=[{"ETag": "part", "PartNumber": 1}])
    assert backend.calls == [("complete_multipart_upload", {
        "Bucket": "fixture", "Key": "new", "UploadId": "Z-upload",
        "MultipartUpload": {"Parts": [{"ETag": "part", "PartNumber": 1}]},
        "IfNoneMatch": "*",
    })]
