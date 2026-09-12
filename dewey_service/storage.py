"""Storage helpers for Dewey artifact lifecycle operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class StorageError(RuntimeError):
    """Base storage operation failure."""


class StorageObjectNotFoundError(StorageError):
    """Raised when a referenced storage object does not exist."""


class StoragePermissionError(StorageError):
    """Raised when Dewey lacks permission for a storage operation."""


@dataclass(frozen=True)
class StorageObject:
    bucket: str
    key: str
    version_id: str | None = None
    size: int | None = None
    content_type: str | None = None
    storage_class: str | None = None
    etag: str | None = None
    sha256: str | None = None
    metadata: dict[str, str] | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class StoragePrefix:
    bucket: str
    prefix: str


class S3StorageClient:
    """Small S3 adapter kept intentionally narrow for Dewey flows."""

    def _check(self, bucket: str, key: str, action: str) -> None:
        authorization = getattr(self, "authorization", None)
        if authorization is None:
            raise RuntimeError("Storage requires an explicit Dewey authorization provider")
        authorization(bucket, key, action=action)

    def __init__(self, *, profile: str | None = None, region: str | None = None) -> None:
        try:
            import boto3
            from botocore.config import Config
            from botocore.exceptions import ClientError
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError("boto3 is required for Dewey storage operations") from exc

        session_kwargs: dict[str, Any] = {}
        if str(profile or "").strip():
            session_kwargs["profile_name"] = str(profile).strip()
        if str(region or "").strip():
            session_kwargs["region_name"] = str(region).strip()

        session = boto3.session.Session(**session_kwargs)
        self._client = session.client(
            "s3",
            config=Config(s3={"use_accelerate_endpoint": False}),
        )
        self._client_error = ClientError

    def head_object(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str | None = None,
        request_payer: str | None = None,
        permission: str = "metadata",
    ) -> StorageObject:
        if permission not in {"metadata", "download", "upload"}:
            raise ValueError("Invalid object inspection permission")
        self._check(bucket, key, permission)
        params: dict[str, Any] = {"Bucket": bucket, "Key": key}
        if version_id:
            params["VersionId"] = version_id
        if str(request_payer or "").strip():
            params["RequestPayer"] = str(request_payer).strip()
        try:
            response = self._client.head_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return self._to_storage_object(bucket=bucket, key=key, response=response)

    def list_buckets(self, *, continuation_token: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"MaxBuckets": 100}
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        response = self._client.list_buckets(**params)
        return {"items": [{"name": item["Name"], "region": item.get("BucketRegion"),
                           "created_at": item["CreationDate"].isoformat()} for item in response.get("Buckets", [])],
                "next_continuation_token": response.get("ContinuationToken")}

    def open_object(self, *, bucket: str, key: str, version_id: str | None = None):
        self._check(bucket, key, "download")
        params = {"Bucket": bucket, "Key": key}
        if version_id:
            params["VersionId"] = version_id
        try:
            result = self._client.get_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return result["Body"], result.get("ContentType")

    def begin_multipart(self, *, bucket: str, key: str, content_type: str, metadata: dict | None = None) -> str:
        self._check(bucket, key, "upload")
        return self._client.create_multipart_upload(Bucket=bucket, Key=key, ContentType=content_type, Metadata=metadata or {})["UploadId"]

    def upload_part(self, *, bucket: str, key: str, upload_id: str, part_number: int, body: bytes) -> str:
        self._check(bucket, key, "upload")
        return self._client.upload_part(Bucket=bucket, Key=key, UploadId=upload_id,
            PartNumber=part_number, Body=body)["ETag"]

    def complete_multipart(self, *, bucket: str, key: str, upload_id: str, parts: list[dict], replace_etag: str | None = None):
        self._check(bucket, key, "upload")
        condition = {"IfMatch": replace_etag} if replace_etag else {"IfNoneMatch": "*"}
        return self._client.complete_multipart_upload(Bucket=bucket, Key=key,
            UploadId=upload_id, MultipartUpload={"Parts": parts}, **condition)

    def abort_multipart(self, *, bucket: str, key: str, upload_id: str):
        self._check(bucket, key, "upload")
        return self._client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)

    def delete_reviewed_objects(self, *, bucket: str, objects: list[dict]):
        for item in objects:
            self._check(bucket, item["Key"], "delete")
        if not objects or len(objects) > 1000 or any(not o.get("Key") or not o.get("ETag") for o in objects):
            raise ValueError("Deletion requires 1..1000 exact keys with reviewed ETags")
        return self._client.delete_objects(Bucket=bucket, Delete={"Objects": objects, "Quiet": False})

    def bucket_versioning(self, bucket: str) -> str:
        return self._client.get_bucket_versioning(Bucket=bucket).get("Status", "Unversioned")

    def list_objects(
        self,
        *,
        bucket: str,
        prefix: str,
        limit: int = 1000,
        request_payer: str | None = None,
    ) -> list[StorageObject]:
        self._check(bucket, prefix, "metadata")
        paginator = self._client.get_paginator("list_objects_v2")
        rows: list[StorageObject] = []
        try:
            params: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
            if str(request_payer or "").strip():
                params["RequestPayer"] = str(request_payer).strip()
            pages = paginator.paginate(**params)
            for page in pages:
                for item in page.get("Contents", []):
                    from fastapi import HTTPException
                    try:
                        self._check(bucket, str(item.get("Key") or ""), "metadata")
                    except HTTPException as exc:
                        if exc.status_code == 403:
                            continue
                        raise
                    rows.append(
                        StorageObject(
                            bucket=bucket,
                            key=str(item.get("Key") or ""),
                            version_id=None,
                            size=item.get("Size"),
                            content_type=None,
                            storage_class=item.get("StorageClass"),
                            etag=str(item.get("ETag") or "").strip('"') or None,
                        )
                    )
                    if len(rows) >= max(1, int(limit)):
                        return rows
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=prefix) from exc
        return rows

    def browse_prefix(
        self,
        *,
        bucket: str,
        prefix: str = "",
        limit: int = 200,
        continuation_token: str | None = None,
        request_payer: str | None = None,
    ) -> dict[str, Any]:
        self._check(bucket, prefix, "metadata")
        params: dict[str, Any] = {
            "Bucket": bucket,
            "Prefix": str(prefix or ""),
            "Delimiter": "/",
            "MaxKeys": max(1, min(int(limit), 1000)),
        }
        if str(continuation_token or "").strip():
            params["ContinuationToken"] = str(continuation_token).strip()
        if str(request_payer or "").strip():
            params["RequestPayer"] = str(request_payer).strip()
        try:
            response = self._client.list_objects_v2(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=prefix) from exc
        prefixes = [
            StoragePrefix(
                bucket=bucket,
                prefix=str(item.get("Prefix") or ""),
            )
            for item in response.get("CommonPrefixes", [])
            if item.get("Prefix") is not None
        ]
        objects = [
            StorageObject(
                bucket=bucket,
                key=str(item.get("Key") or ""),
                version_id=None,
                size=item.get("Size"),
                content_type=None,
                storage_class=item.get("StorageClass"),
                etag=str(item.get("ETag") or "").strip('"') or None,
            )
            for item in response.get("Contents", [])
            if item.get("Key") is not None
            and str(item["Key"]) != prefix
        ]
        return {
            "prefixes": prefixes,
            "objects": objects,
            "is_truncated": bool(response.get("IsTruncated")),
            "next_continuation_token": (
                str(response.get("NextContinuationToken") or "").strip() or None
            ),
        }

    def get_object_bytes(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str | None = None,
        request_payer: str | None = None,
    ) -> bytes:
        self._check(bucket, key, "download")
        params: dict[str, Any] = {"Bucket": bucket, "Key": key}
        if version_id:
            params["VersionId"] = version_id
        if str(request_payer or "").strip():
            params["RequestPayer"] = str(request_payer).strip()
        try:
            response = self._client.get_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return bytes(response["Body"].read())

    def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageObject:
        self._check(source_bucket, source_key, "download")
        self._check(dest_bucket, dest_key, "upload")
        source = self.head_object(bucket=source_bucket, key=source_key)
        if source.size == 0:
            return self.put_bytes(bucket=dest_bucket, key=dest_key, body=b"", content_type=source.content_type)
        if source.size is None or not source.etag:
            raise StorageError("Copy requires an observed source size and ETag")
        copy_source = {"Bucket": source_bucket, "Key": source_key}
        if source.version_id:
            copy_source["VersionId"] = source.version_id
        upload_id = self.begin_multipart(bucket=dest_bucket, key=dest_key, content_type=source.content_type or "application/octet-stream", metadata=source.metadata)
        parts = []
        try:
            chunk_size = max(512 * 1024**2, (source.size + 9999) // 10000)
            for number, offset in enumerate(range(0, source.size, chunk_size), 1):
                response = self._client.upload_part_copy(Bucket=dest_bucket, Key=dest_key,
                    UploadId=upload_id, PartNumber=number, CopySource=copy_source,
                    CopySourceIfMatch=source.etag,
                    **({"CopySourceRange": f"bytes={offset}-{min(offset + chunk_size, source.size) - 1}"} if source.size > chunk_size else {}))
                parts.append({"PartNumber": number, "ETag": response["CopyPartResult"]["ETag"]})
            self.complete_multipart(bucket=dest_bucket, key=dest_key, upload_id=upload_id, parts=parts)
        except self._client_error as exc:
            # Abort only this operation's incomplete upload; never retry an overwrite.
            self.abort_multipart(bucket=dest_bucket, key=dest_key, upload_id=upload_id)
            raise self._translate_error(exc, bucket=dest_bucket, key=dest_key) from exc
        return self.head_object(bucket=dest_bucket, key=dest_key)

    def put_bytes(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> StorageObject:
        self._check(bucket, key, "upload")
        params: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
            "IfNoneMatch": "*",
        }
        if content_type:
            params["ContentType"] = content_type
        try:
            self._client.put_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return self.head_object(bucket=bucket, key=key)

    def put_object_tags(self, *, bucket: str, key: str, tags: dict[str, str]) -> None:
        self._check(bucket, key, "upload")
        merged = dict(self.get_object_tags(bucket=bucket, key=key))
        merged.update({str(k): str(v) for k, v in tags.items() if str(v).strip()})
        try:
            self._client.put_object_tagging(
                Bucket=bucket,
                Key=key,
                Tagging={
                    "TagSet": [
                        {"Key": tag_key, "Value": tag_value}
                        for tag_key, tag_value in sorted(merged.items())
                    ]
                },
            )
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc

    def get_object_tags(self, *, bucket: str, key: str) -> dict[str, str]:
        self._check(bucket, key, "metadata")
        try:
            response = self._client.get_object_tagging(Bucket=bucket, Key=key)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        tags: dict[str, str] = {}
        for item in response.get("TagSet", []):
            tag_key = str(item.get("Key") or "").strip()
            if tag_key:
                tags[tag_key] = str(item.get("Value") or "")
        return tags

    def set_retention(
        self,
        *,
        bucket: str,
        key: str,
        mode: str,
        retain_until: datetime,
    ) -> None:
        self._check(bucket, key, "delete")
        try:
            self._client.put_object_retention(
                Bucket=bucket,
                Key=key,
                Retention={
                    "Mode": str(mode or "GOVERNANCE").strip().upper(),
                    "RetainUntilDate": retain_until,
                },
            )
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc

    def generate_presigned_get_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        version_id: str | None = None,
        request_payer: str | None = None,
    ) -> str:
        self._check(bucket, key, "download")
        params: dict[str, Any] = {"Bucket": bucket, "Key": key, "ResponseContentDisposition": "attachment"}
        if version_id:
            params["VersionId"] = version_id
        if str(request_payer or "").strip():
            params["RequestPayer"] = str(request_payer).strip()
        try:
            return str(
                self._client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=max(1, int(expires_in)),
                )
            )
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc

    def generate_presigned_upload(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        self._check(bucket, key, "upload")
        params: dict[str, Any] = {"Bucket": bucket, "Key": key, "IfNoneMatch": "*"}
        headers: dict[str, str] = {"If-None-Match": "*"}
        if content_type:
            params["ContentType"] = content_type
            headers["Content-Type"] = content_type
        try:
            url = self._client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=max(1, int(expires_in)),
            )
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return {
            "method": "PUT",
            "url": str(url),
            "headers": headers,
        }

    def _to_storage_object(
        self,
        *,
        bucket: str,
        key: str,
        response: dict[str, Any],
    ) -> StorageObject:
        return StorageObject(
            bucket=bucket,
            key=key,
            version_id=response.get("VersionId"),
            size=response.get("ContentLength"),
            content_type=response.get("ContentType"),
            storage_class=response.get("StorageClass"),
            etag=str(response.get("ETag") or "").strip('"') or None,
            sha256=str(response.get("ChecksumSHA256") or "").strip() or None,
            metadata=dict(response.get("Metadata") or {}),
            last_modified=response["LastModified"].isoformat() if response.get("LastModified") else None,
        )

    def _translate_error(self, exc: Exception, *, bucket: str, key: str) -> StorageError:
        error = getattr(exc, "response", {}).get("Error", {})
        code = str(error.get("Code") or "").strip()
        message = str(error.get("Message") or f"{bucket}/{key}").strip()
        if code in {"404", "NoSuchKey", "NotFound"}:
            return StorageObjectNotFoundError(message)
        if code in {"403", "AccessDenied"}:
            return StoragePermissionError(message)
        return StorageError(message)
