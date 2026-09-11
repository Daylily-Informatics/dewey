"""Reference contract for Labcore-owned sequencing-run artifact relations."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal, Mapping
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONTRACT_TYPE = "dewey.labcore-sequencing-run-owner/v1"
CONTRACT_VERSION = 1
HASH_DOMAIN = "dewey.labcore-sequencing-run-owner.request/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_PATTERN = r"^[0-9a-f]{64}$"


def _required_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    clean = value.strip()
    if not clean:
        raise ValueError(f"{field_name} is required")
    return clean


def _sha256(value: Any, *, field_name: str) -> str:
    clean = _required_text(value, field_name=field_name)
    if not SHA256_RE.fullmatch(clean):
        raise ValueError(f"{field_name} must be a 64-character lowercase hex digest")
    return clean


class StrictContractModel(BaseModel):
    """Reject undeclared or type-coerced input at every contract level."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ExpectedDatasetFileV1(StrictContractModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64, pattern=SHA256_PATTERN)
    size_bytes: int = Field(ge=0)
    object_version_id: str = Field(min_length=1)

    @field_validator("relative_path", mode="before")
    @classmethod
    def _relative_path(cls, value: Any) -> str:
        clean = _required_text(value, field_name="relative_path")
        segments = clean.split("/")
        if clean.startswith("/") or any(segment in {"", ".", ".."} for segment in segments):
            raise ValueError("relative_path must be a normalized relative path")
        if "\\" in clean or clean.endswith("/"):
            raise ValueError("relative_path must be a normalized relative file path")
        return clean

    @field_validator("sha256", mode="before")
    @classmethod
    def _file_sha256(cls, value: Any) -> str:
        return _sha256(value, field_name="sha256")

    @field_validator("object_version_id", mode="before")
    @classmethod
    def _version_id(cls, value: Any) -> str:
        return _required_text(value, field_name="object_version_id")


class _LabcoreSequencingRunOwnerHashInputV1(StrictContractModel):
    contract_type: Literal["dewey.labcore-sequencing-run-owner/v1"]
    contract_version: Literal[1]
    hash_domain: Literal["dewey.labcore-sequencing-run-owner.request/v1"]
    external_system: Literal["labcore"]
    external_object_type: Literal["sequencing_run"]
    external_object_id: str = Field(min_length=1)
    labcore_sequencing_run_euid: str = Field(min_length=1)
    tenant_euid: str = Field(min_length=1)
    processing_site_euid: str = Field(min_length=1)
    platform: Literal["ILMN", "ONT"]
    dataset_root_uri: str = Field(min_length=1)
    dataset_revision: str = Field(min_length=64, max_length=64, pattern=SHA256_PATTERN)
    inventory_sha256: str = Field(min_length=64, max_length=64, pattern=SHA256_PATTERN)
    labcore_binding_receipt_id: str = Field(min_length=1)
    labcore_binding_receipt_sha256: str = Field(
        min_length=64,
        max_length=64,
        pattern=SHA256_PATTERN,
    )
    target_type: Literal["artifact"]
    target_euid: str = Field(min_length=1)
    relation_type: Literal["labcore_sequencing_run"]
    expected_files: tuple[ExpectedDatasetFileV1, ...] = Field(min_length=1)

    @field_validator(
        "external_object_id",
        "labcore_sequencing_run_euid",
        "tenant_euid",
        "processing_site_euid",
        "labcore_binding_receipt_id",
        "target_euid",
        mode="before",
    )
    @classmethod
    def _identities(cls, value: Any, info) -> str:
        return _required_text(value, field_name=info.field_name)

    @field_validator(
        "dataset_revision",
        "inventory_sha256",
        "labcore_binding_receipt_sha256",
        mode="before",
    )
    @classmethod
    def _hashes(cls, value: Any, info) -> str:
        return _sha256(value, field_name=info.field_name)

    @field_validator("expected_files", mode="before")
    @classmethod
    def _immutable_expected_files(cls, value: Any) -> tuple[Any, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("expected_files must be an array")
        return tuple(value)

    @field_validator("dataset_root_uri", mode="before")
    @classmethod
    def _dataset_root(cls, value: Any) -> str:
        clean = _required_text(value, field_name="dataset_root_uri")
        parsed = urlsplit(clean)
        if parsed.scheme != "s3" or not parsed.netloc:
            raise ValueError("dataset_root_uri must use s3:// with a bucket")
        if (
            parsed.query
            or parsed.fragment
            or "\\" in parsed.path
            or "@" in parsed.netloc
            or ":" in parsed.netloc
        ):
            raise ValueError(
                "dataset_root_uri must not contain credentials, port, query, fragment, or backslash"
            )
        segments = parsed.path.split("/")
        if any(segment in {".", ".."} for segment in segments) or "//" in parsed.path:
            raise ValueError("dataset_root_uri must be normalized")
        normalized_path = parsed.path.rstrip("/")
        return f"s3://{parsed.netloc}{normalized_path}/"

    @model_validator(mode="after")
    def _owner_identity_matches(self) -> "_LabcoreSequencingRunOwnerHashInputV1":
        if self.external_object_id != self.labcore_sequencing_run_euid:
            raise ValueError("external_object_id must equal labcore_sequencing_run_euid")
        paths = [item.relative_path for item in self.expected_files]
        if len(paths) != len(set(paths)):
            raise ValueError("expected_files relative_path values must be unique")
        return self


def _normalized_hash_payload(value: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        payload = value.model_dump(
            mode="json",
            exclude={"request_sha256", "idempotency_key"},
        )
    else:
        payload = dict(value)
        payload.pop("request_sha256", None)
        payload.pop("idempotency_key", None)
    return _LabcoreSequencingRunOwnerHashInputV1.model_validate(payload).model_dump(mode="json")


def canonical_request_bytes(value: BaseModel | Mapping[str, Any]) -> bytes:
    """Return Dewey-domain canonical bytes, excluding self-referential hash fields."""

    payload = _normalized_hash_payload(value)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def canonical_request_sha256(value: BaseModel | Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_request_bytes(value)).hexdigest()


def bind_request_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an unhashed request and bind its required hash/idempotency identity."""

    normalized = _normalized_hash_payload(value)
    digest = canonical_request_sha256(normalized)
    return {**normalized, "request_sha256": digest, "idempotency_key": digest}


class LabcoreSequencingRunOwnerContractV1(_LabcoreSequencingRunOwnerHashInputV1):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "x-dewey-equality-constraints": [
                "external_object_id == labcore_sequencing_run_euid",
                "idempotency_key == request_sha256 == sha256(canonical_request_bytes)",
            ],
        },
    )

    request_sha256: str = Field(min_length=64, max_length=64, pattern=SHA256_PATTERN)
    idempotency_key: str = Field(min_length=64, max_length=64, pattern=SHA256_PATTERN)

    @field_validator("request_sha256", "idempotency_key", mode="before")
    @classmethod
    def _request_hashes(cls, value: Any, info) -> str:
        return _sha256(value, field_name=info.field_name)

    @model_validator(mode="after")
    def _request_identity_matches(self) -> "LabcoreSequencingRunOwnerContractV1":
        expected = canonical_request_sha256(self)
        if self.request_sha256 != expected:
            raise ValueError("request_sha256 must equal the canonical request hash")
        if self.idempotency_key != self.request_sha256:
            raise ValueError("idempotency_key must equal request_sha256")
        return self
