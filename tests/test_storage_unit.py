from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import dewey_service.storage as storage_mod


class FakeClientError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


class _Body:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload


class _Paginator:
    def __init__(self, pages: list[dict[str, object]], error: Exception | None = None) -> None:
        self.pages = pages
        self.error = error
        self.calls: list[dict[str, str]] = []

    def paginate(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return list(self.pages)


class _FakeS3Backend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.paginator = _Paginator([])
        self.head_response = {
            "VersionId": "v1",
            "ContentLength": 42,
            "ContentType": "application/pdf",
            "StorageClass": "STANDARD",
            "ETag": '"etag-1"',
        }
        self.get_response = {"Body": _Body(b"payload")}
        self.tagging_response = {"TagSet": [{"Key": "existing", "Value": "keep"}]}
        self.presigned_url = "https://signed.example.com/object"
        self.errors: dict[str, Exception] = {}

    def _raise(self, name: str) -> None:
        if name in self.errors:
            raise self.errors[name]

    def head_object(self, **kwargs):
        self.calls.append(("head_object", kwargs))
        self._raise("head_object")
        return dict(self.head_response)

    def get_paginator(self, name: str):
        self.calls.append(("get_paginator", name))
        if "get_paginator" in self.errors:
            raise self.errors["get_paginator"]
        return self.paginator

    def get_object(self, **kwargs):
        self.calls.append(("get_object", kwargs))
        self._raise("get_object")
        return self.get_response

    def copy_object(self, **kwargs):
        self.calls.append(("copy_object", kwargs))
        self._raise("copy_object")

    def put_object(self, **kwargs):
        self.calls.append(("put_object", kwargs))
        self._raise("put_object")

    def put_object_tagging(self, **kwargs):
        self.calls.append(("put_object_tagging", kwargs))
        self._raise("put_object_tagging")

    def get_object_tagging(self, **kwargs):
        self.calls.append(("get_object_tagging", kwargs))
        self._raise("get_object_tagging")
        return self.tagging_response

    def put_object_retention(self, **kwargs):
        self.calls.append(("put_object_retention", kwargs))
        self._raise("put_object_retention")

    def generate_presigned_url(self, operation: str, *, Params: dict, ExpiresIn: int):
        self.calls.append(("generate_presigned_url", (operation, Params, ExpiresIn)))
        self._raise("generate_presigned_url")
        return self.presigned_url


def _client(backend: _FakeS3Backend) -> storage_mod.S3StorageClient:
    client = object.__new__(storage_mod.S3StorageClient)
    client._client = backend
    client._client_error = FakeClientError
    return client


def test_s3_storage_client_init_builds_session_from_profile_and_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    class FakeSession:
        def __init__(self, **kwargs) -> None:
            seen["kwargs"] = kwargs

        def client(self, service_name: str) -> str:
            seen["service_name"] = service_name
            return "fake-s3-client"

    fake_boto3 = types.SimpleNamespace(session=types.SimpleNamespace(Session=FakeSession))
    fake_exceptions = types.SimpleNamespace(ClientError=FakeClientError)

    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", fake_exceptions)

    client = storage_mod.S3StorageClient(profile="  team ", region=" us-west-2 ")

    assert client._client == "fake-s3-client"
    assert client._client_error is FakeClientError
    assert seen == {
        "kwargs": {"profile_name": "team", "region_name": "us-west-2"},
        "service_name": "s3",
    }


def test_s3_storage_client_object_operations_cover_success_paths() -> None:
    backend = _FakeS3Backend()
    backend.paginator = _Paginator(
        [
            {
                "Contents": [
                    {"Key": "docs/a.pdf", "Size": 11, "StorageClass": "STANDARD", "ETag": '"etag-a"'},
                    {"Key": "docs/b.pdf", "Size": 12, "StorageClass": "GLACIER", "ETag": ""},
                ]
            }
        ]
    )
    client = _client(backend)

    head = client.head_object(bucket="bucket-1", key="docs/a.pdf", version_id="ver-1")
    payload = client.get_object_bytes(bucket="bucket-1", key="docs/a.pdf", version_id="ver-1")
    listed = client.list_objects(bucket="bucket-1", prefix="docs/", limit=1)

    expected_obj = storage_mod.StorageObject(
        bucket="bucket-1",
        key="docs/a.pdf",
        version_id="v1",
        size=42,
        content_type="application/pdf",
        storage_class="STANDARD",
        etag="etag-1",
    )
    assert head == expected_obj
    assert payload == b"payload"
    assert listed == [
        storage_mod.StorageObject(
            bucket="bucket-1",
            key="docs/a.pdf",
            version_id=None,
            size=11,
            content_type=None,
            storage_class="STANDARD",
            etag="etag-a",
        )
    ]
    assert backend.paginator.calls == [{"Bucket": "bucket-1", "Prefix": "docs/"}]


def test_s3_storage_client_write_tag_retention_and_presign_paths() -> None:
    backend = _FakeS3Backend()
    backend.tagging_response = {
        "TagSet": [
            {"Key": "zeta", "Value": "keep"},
            {"Key": "", "Value": "ignored"},
        ]
    }
    client = _client(backend)
    head_calls: list[tuple[str, str]] = []

    def fake_head_object(*, bucket: str, key: str, version_id: str | None = None):
        head_calls.append((bucket, key))
        return storage_mod.StorageObject(bucket=bucket, key=key, etag="copied")

    client.head_object = fake_head_object  # type: ignore[method-assign]

    copied = client.copy_object(
        source_bucket="source-bucket",
        source_key="source-key",
        dest_bucket="dest-bucket",
        dest_key="dest-key",
    )
    uploaded = client.put_bytes(
        bucket="dest-bucket",
        key="dest-key",
        body=b"hello",
        content_type="text/plain",
    )
    tags = client.get_object_tags(bucket="dest-bucket", key="dest-key")
    client.put_object_tags(
        bucket="dest-bucket",
        key="dest-key",
        tags={"alpha": "one", "blank": "   ", "beta": 2},
    )
    retain_until = datetime(2026, 4, 5, 18, 0, tzinfo=timezone.utc)
    client.set_retention(
        bucket="dest-bucket",
        key="dest-key",
        mode=" governance ",
        retain_until=retain_until,
    )
    get_url = client.generate_presigned_get_url(
        bucket="dest-bucket",
        key="dest-key",
        expires_in=30,
        version_id="ver-2",
    )
    upload = client.generate_presigned_upload(
        bucket="dest-bucket",
        key="upload-key",
        expires_in=45,
        content_type="application/pdf",
    )

    assert copied == storage_mod.StorageObject(bucket="dest-bucket", key="dest-key", etag="copied")
    assert uploaded == storage_mod.StorageObject(bucket="dest-bucket", key="dest-key", etag="copied")
    assert head_calls == [("dest-bucket", "dest-key"), ("dest-bucket", "dest-key")]
    assert tags == {"zeta": "keep"}
    assert get_url == "https://signed.example.com/object"
    assert upload == {
        "method": "PUT",
        "url": "https://signed.example.com/object",
        "headers": {"Content-Type": "application/pdf"},
    }
    assert ("copy_object", {"Bucket": "dest-bucket", "Key": "dest-key", "CopySource": {
        "Bucket": "source-bucket",
        "Key": "source-key",
    }}) in backend.calls
    assert ("put_object", {
        "Bucket": "dest-bucket",
        "Key": "dest-key",
        "Body": b"hello",
        "ContentType": "text/plain",
    }) in backend.calls
    assert ("put_object_retention", {
        "Bucket": "dest-bucket",
        "Key": "dest-key",
        "Retention": {"Mode": "GOVERNANCE", "RetainUntilDate": retain_until},
    }) in backend.calls

    tag_call = next(kwargs for name, kwargs in backend.calls if name == "put_object_tagging")
    assert tag_call == {
        "Bucket": "dest-bucket",
        "Key": "dest-key",
        "Tagging": {
            "TagSet": [
                {"Key": "alpha", "Value": "one"},
                {"Key": "beta", "Value": "2"},
                {"Key": "zeta", "Value": "keep"},
            ]
        },
    }
    presigned_calls = [payload for name, payload in backend.calls if name == "generate_presigned_url"]
    assert presigned_calls == [
        ("get_object", {"Bucket": "dest-bucket", "Key": "dest-key", "VersionId": "ver-2"}, 60),
        (
            "put_object",
            {"Bucket": "dest-bucket", "Key": "upload-key", "ContentType": "application/pdf"},
            60,
        ),
    ]


@pytest.mark.parametrize(
    ("method_name", "invoke", "code", "expected_exception"),
    [
        (
            "head_object",
            lambda client: client.head_object(bucket="b", key="k"),
            "NotFound",
            storage_mod.StorageObjectNotFoundError,
        ),
        (
            "get_object",
            lambda client: client.get_object_bytes(bucket="b", key="k"),
            "AccessDenied",
            storage_mod.StoragePermissionError,
        ),
        (
            "copy_object",
            lambda client: client.copy_object(
                source_bucket="sb",
                source_key="sk",
                dest_bucket="db",
                dest_key="dk",
            ),
            "500",
            storage_mod.StorageError,
        ),
        (
            "put_object",
            lambda client: client.put_bytes(bucket="b", key="k", body=b"x"),
            "500",
            storage_mod.StorageError,
        ),
        (
            "get_object_tagging",
            lambda client: client.get_object_tags(bucket="b", key="k"),
            "AccessDenied",
            storage_mod.StoragePermissionError,
        ),
        (
            "put_object_tagging",
            lambda client: client.put_object_tags(bucket="b", key="k", tags={"a": "b"}),
            "NotFound",
            storage_mod.StorageObjectNotFoundError,
        ),
        (
            "put_object_retention",
            lambda client: client.set_retention(
                bucket="b",
                key="k",
                mode="governance",
                retain_until=datetime(2026, 4, 5, tzinfo=timezone.utc),
            ),
            "AccessDenied",
            storage_mod.StoragePermissionError,
        ),
        (
            "generate_presigned_url",
            lambda client: client.generate_presigned_get_url(bucket="b", key="k", expires_in=61),
            "500",
            storage_mod.StorageError,
        ),
    ],
)
def test_s3_storage_client_translates_method_errors(
    method_name: str,
    invoke,
    code: str,
    expected_exception: type[Exception],
) -> None:
    backend = _FakeS3Backend()
    backend.errors[method_name] = FakeClientError(code, f"{method_name} failed")
    client = _client(backend)

    with pytest.raises(expected_exception, match=f"{method_name} failed"):
        invoke(client)


def test_s3_storage_client_translate_error_classifies_common_cases() -> None:
    client = _client(_FakeS3Backend())

    not_found = client._translate_error(
        FakeClientError("404", "missing object"),
        bucket="bucket-1",
        key="key-1",
    )
    denied = client._translate_error(
        FakeClientError("403", "denied object"),
        bucket="bucket-1",
        key="key-1",
    )
    generic = client._translate_error(
        SimpleNamespace(response={"Error": {"Code": "500", "Message": ""}}),
        bucket="bucket-1",
        key="key-1",
    )

    assert isinstance(not_found, storage_mod.StorageObjectNotFoundError)
    assert isinstance(denied, storage_mod.StoragePermissionError)
    assert isinstance(generic, storage_mod.StorageError)
    assert str(generic) == "bucket-1/key-1"
