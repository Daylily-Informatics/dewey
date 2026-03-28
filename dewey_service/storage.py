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


class S3StorageClient:
    """Small S3 adapter kept intentionally narrow for Dewey flows."""

    def __init__(self, *, profile: str | None = None, region: str | None = None) -> None:
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError("boto3 is required for Dewey storage operations") from exc

        session_kwargs: dict[str, Any] = {}
        if str(profile or "").strip():
            session_kwargs["profile_name"] = str(profile).strip()
        if str(region or "").strip():
            session_kwargs["region_name"] = str(region).strip()

        session = boto3.session.Session(**session_kwargs)
        self._client = session.client("s3")
        self._client_error = ClientError

    def head_object(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str | None = None,
    ) -> StorageObject:
        params: dict[str, Any] = {"Bucket": bucket, "Key": key}
        if version_id:
            params["VersionId"] = version_id
        try:
            response = self._client.head_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return self._to_storage_object(bucket=bucket, key=key, response=response)

    def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> StorageObject:
        try:
            self._client.copy_object(
                Bucket=dest_bucket,
                Key=dest_key,
                CopySource={"Bucket": source_bucket, "Key": source_key},
            )
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=source_bucket, key=source_key) from exc
        return self.head_object(bucket=dest_bucket, key=dest_key)

    def put_bytes(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> StorageObject:
        params: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
        }
        if content_type:
            params["ContentType"] = content_type
        try:
            self._client.put_object(**params)
        except self._client_error as exc:
            raise self._translate_error(exc, bucket=bucket, key=key) from exc
        return self.head_object(bucket=bucket, key=key)

    def put_object_tags(self, *, bucket: str, key: str, tags: dict[str, str]) -> None:
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
    ) -> str:
        params: dict[str, Any] = {"Bucket": bucket, "Key": key}
        if version_id:
            params["VersionId"] = version_id
        try:
            return str(
                self._client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=max(60, int(expires_in)),
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
        params: dict[str, Any] = {"Bucket": bucket, "Key": key}
        headers: dict[str, str] = {}
        if content_type:
            params["ContentType"] = content_type
            headers["Content-Type"] = content_type
        try:
            url = self._client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=max(60, int(expires_in)),
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
