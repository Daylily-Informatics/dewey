"""Strict contracts for QEO/KEO artifact-set registration."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_SCHEMA_VERSION = "1.0"
OUTBOX_SCHEMA_VERSION = "1.0"


def _clean_text(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_iso8601(value: str, *, field_name: str) -> str:
    raw = _clean_text(value)
    if not raw:
        raise ValueError(f"{field_name} is required")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for registration hashing and receipts."""

    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def manifest_sha256_for_request(request: BaseModel) -> str:
    return canonical_sha256(request.model_dump(mode="json", exclude={"manifest_sha256"}))


def computed_registration_idempotency_key(request: BaseModel) -> str:
    return canonical_sha256(request)


def deterministic_request_id(idempotency_key: str) -> str:
    return sha256(f"dewey-registration-request:{idempotency_key}".encode("utf-8")).hexdigest()


class StrictContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FileArtifact(StrictContractModel):
    logical_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    storage_uri: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    mime_type: str = Field(min_length=1)
    artifact_role: str = Field(min_length=1)
    parser_hint: str | None = None
    required: bool = True
    produced_by: str = Field(min_length=1)
    parent_artifact_euids: list[str] = Field(default_factory=list)

    @field_validator(
        "logical_name",
        "relative_path",
        "storage_uri",
        "mime_type",
        "artifact_role",
        "produced_by",
        mode="before",
    )
    @classmethod
    def _strip_required_text(cls, value: Any) -> str:
        return _clean_text(value)

    @field_validator("parser_hint", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: Any) -> str | None:
        clean = _clean_text(value)
        return clean or None

    @field_validator("parent_artifact_euids", mode="before")
    @classmethod
    def _strip_parent_euids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("parent_artifact_euids must be a list")
        cleaned = [_clean_text(item) for item in value]
        return [item for item in cleaned if item]

    @field_validator("relative_path")
    @classmethod
    def _relative_path_is_manifest_path(cls, value: str) -> str:
        if value.startswith("/"):
            raise ValueError("relative_path must be relative")
        parts = PurePosixPath(value).parts
        if ".." in parts:
            raise ValueError("relative_path must not contain '..'")
        if not parts:
            raise ValueError("relative_path is required")
        return value

    @field_validator("storage_uri")
    @classmethod
    def _storage_uri_is_s3(cls, value: str) -> str:
        if not value.startswith("s3://"):
            raise ValueError("storage_uri must use s3://")
        return value

    @field_validator("sha256", mode="before")
    @classmethod
    def _normalize_sha256(cls, value: Any) -> str:
        clean = _clean_text(value).lower()
        if not SHA256_RE.fullmatch(clean):
            raise ValueError("sha256 must be a 64-character lowercase hex digest")
        return clean


class LineageRef(StrictContractModel):
    kind: str = Field(min_length=1)
    euid: str = Field(min_length=1)
    role: str | None = None

    @field_validator("kind", "euid", mode="before")
    @classmethod
    def _strip_required_text(cls, value: Any) -> str:
        return _clean_text(value)

    @field_validator("role", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: Any) -> str | None:
        clean = _clean_text(value)
        return clean or None


class AnalysisArtifactSetRegistrationRequest(StrictContractModel):
    schema_version: str = Field(default=RECEIPT_SCHEMA_VERSION)
    analysis_euid: str = Field(min_length=1)
    run_euid: str = Field(min_length=1)
    workset_euid: str | None = None
    project_euid: str | None = None
    assay_id: str | None = None
    pipeline_name: str = Field(min_length=1)
    pipeline_version: str = Field(min_length=1)
    workflow_engine: str = Field(min_length=1)
    workflow_engine_version: str = Field(min_length=1)
    snakemake_version: str = Field(min_length=1)
    workflow_git_sha: str = Field(min_length=1)
    workflow_config_sha256: str = Field(min_length=64, max_length=64)
    workflow_profile: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    parent_analysis_artifact_set_euid: str | None = None
    rerun_of: str | None = None
    status: str = Field(min_length=1)
    artifacts: list[FileArtifact] = Field(min_length=1)
    lineage_refs: list[LineageRef] = Field(default_factory=list)
    local_only: bool = False
    parser_family_hint: str | None = None

    @field_validator(
        "schema_version",
        "analysis_euid",
        "run_euid",
        "pipeline_name",
        "pipeline_version",
        "workflow_engine",
        "workflow_engine_version",
        "snakemake_version",
        "workflow_git_sha",
        "workflow_profile",
        "status",
        mode="before",
    )
    @classmethod
    def _strip_required_text(cls, value: Any) -> str:
        return _clean_text(value)

    @field_validator(
        "workset_euid",
        "project_euid",
        "assay_id",
        "parent_analysis_artifact_set_euid",
        "rerun_of",
        "parser_family_hint",
        mode="before",
    )
    @classmethod
    def _strip_optional_text(cls, value: Any) -> str | None:
        clean = _clean_text(value)
        return clean or None

    @field_validator("manifest_sha256", "workflow_config_sha256", mode="before")
    @classmethod
    def _normalize_sha256(cls, value: Any) -> str:
        clean = _clean_text(value).lower()
        if not SHA256_RE.fullmatch(clean):
            raise ValueError("sha256 fields must be 64-character lowercase hex digests")
        return clean

    @field_validator("generated_at")
    @classmethod
    def _generated_at_iso8601(cls, value: str) -> str:
        return _normalize_iso8601(value, field_name="generated_at")


class MultiQCArtifactSetRegistrationRequest(StrictContractModel):
    schema_version: str = Field(default=RECEIPT_SCHEMA_VERSION)
    analysis_euid: str = Field(min_length=1)
    report_kind: str = Field(min_length=1)
    multiqc_version: str = Field(min_length=1)
    html_artifact: FileArtifact
    data_dir_artifact: FileArtifact
    key_files: list[FileArtifact] = Field(default_factory=list)
    parser_relevant_files: list[FileArtifact] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    local_only: bool = False
    parser_family_hint: str | None = None

    @field_validator(
        "schema_version",
        "analysis_euid",
        "report_kind",
        "multiqc_version",
        mode="before",
    )
    @classmethod
    def _strip_required_text(cls, value: Any) -> str:
        return _clean_text(value)

    @field_validator("parser_family_hint", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: Any) -> str | None:
        clean = _clean_text(value)
        return clean or None

    @field_validator("manifest_sha256", mode="before")
    @classmethod
    def _normalize_sha256(cls, value: Any) -> str:
        clean = _clean_text(value).lower()
        if not SHA256_RE.fullmatch(clean):
            raise ValueError("manifest_sha256 must be a 64-character lowercase hex digest")
        return clean

    @field_validator("generated_at")
    @classmethod
    def _generated_at_iso8601(cls, value: str) -> str:
        return _normalize_iso8601(value, field_name="generated_at")

    @model_validator(mode="after")
    def _multiqc_roles_are_explicit(self) -> "MultiQCArtifactSetRegistrationRequest":
        if self.html_artifact.artifact_role != "multiqc_html":
            raise ValueError("html_artifact.artifact_role must be multiqc_html")
        if self.data_dir_artifact.artifact_role != "directory":
            raise ValueError("data_dir_artifact.artifact_role must be directory")
        return self


class ReceiptArtifact(StrictContractModel):
    artifact_euid: str
    logical_name: str
    relative_path: str
    storage_uri: str
    sha256: str
    size_bytes: int
    artifact_role: str
    parser_hint: str | None = None
    required: bool


class ReceiptFailure(StrictContractModel):
    logical_name: str | None = None
    storage_uri: str | None = None
    error: str


class RegistrationReceipt(StrictContractModel):
    schema_version: str = RECEIPT_SCHEMA_VERSION
    request_id: str
    idempotency_key: str
    artifact_set_euid: str
    artifact_set_kind: str
    report_kind: str | None = None
    manifest_sha256: str
    registered_artifacts: list[ReceiptArtifact] = Field(default_factory=list)
    skipped_existing: list[ReceiptArtifact] = Field(default_factory=list)
    failed: list[ReceiptFailure] = Field(default_factory=list)
    registered_at: str
    status: Literal["registered", "replayed", "local_only"]
    source_service: str = "dewey"
    source_version: str | None = None
    parser_hint: str | None = None


class OutboxEventEnvelope(StrictContractModel):
    event_id: str
    event_type: Literal[
        "lsmc.dewey.artifact_set.registered.v1",
        "lsmc.dewey.multiqc_artifact_set.registered.v1",
    ]
    occurred_at: str
    producer: str = "dewey"
    schema_version: str = OUTBOX_SCHEMA_VERSION
    payload: dict[str, Any]
    correlation_id: str
    causation_id: str | None = None


__all__ = [
    "AnalysisArtifactSetRegistrationRequest",
    "FileArtifact",
    "LineageRef",
    "MultiQCArtifactSetRegistrationRequest",
    "OutboxEventEnvelope",
    "ReceiptArtifact",
    "ReceiptFailure",
    "RegistrationReceipt",
    "canonical_json",
    "canonical_sha256",
    "computed_registration_idempotency_key",
    "deterministic_request_id",
    "manifest_sha256_for_request",
]
