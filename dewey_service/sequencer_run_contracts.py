"""Sequencer run and analysis-result registration contracts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SequencerPlatform = Literal["ILMN", "ONT", "ULTIMA", "HYBRID_ILMN_ONT"]
TriggerPolicy = Literal["register_only", "trigger_ursa"]
TerminalResultStatus = Literal["succeeded", "failed", "canceled"]


class FileEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logical_name: str
    relative_path: str
    artifact_role: str
    sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    version_id: str | None = None
    mime_type: str | None = None
    required: bool = True
    parser_hint: str | None = None

    @field_validator("logical_name", "relative_path", "artifact_role")
    @classmethod
    def _required_text(cls, value: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError("value is required")
        return clean.lstrip("/")

    @field_validator("sha256")
    @classmethod
    def _sha256(cls, value: str | None) -> str | None:
        clean = str(value or "").strip().lower()
        if not clean:
            return None
        if len(clean) != 64 or any(char not in "0123456789abcdef" for char in clean):
            raise ValueError("sha256 must be a 64-character lowercase hex digest")
        return clean


class SequencerRunRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    run_root_uri: str
    platform: SequencerPlatform
    trigger_policy: TriggerPolicy
    run_euid: str | None = None
    run_xid: str | None = None
    bloom_run_euid: str | None = None
    atlas_order_euid: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    expected_files: list[FileEvidence] = Field(default_factory=list)
    expected_manifest_sha256: str | None = None
    sidecar_required: bool = False

    @field_validator("run_root_uri")
    @classmethod
    def _root_uri(cls, value: str) -> str:
        clean = str(value or "").strip()
        if not clean.startswith("s3://"):
            raise ValueError("run_root_uri must use s3://")
        return clean.rstrip("/") + "/"

    @field_validator("platform")
    @classmethod
    def _platform(cls, value: str) -> str:
        return str(value or "").strip().upper()

    @field_validator("expected_manifest_sha256")
    @classmethod
    def _manifest_sha(cls, value: str | None) -> str | None:
        clean = str(value or "").strip().lower()
        if not clean:
            return None
        if len(clean) != 64 or any(char not in "0123456789abcdef" for char in clean):
            raise ValueError("expected_manifest_sha256 must be a 64-character hex digest")
        return clean


class SampleIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_euid: str | None = None
    sample_xid: str | None = None
    library_euid: str | None = None
    library_xid: str | None = None
    read_group_id: str | None = None

    @model_validator(mode="after")
    def _has_identifier(self) -> "SampleIdentifier":
        if not any(
            str(value or "").strip()
            for value in (
                self.sample_euid,
                self.sample_xid,
                self.library_euid,
                self.library_xid,
                self.read_group_id,
            )
        ):
            raise ValueError("at least one sample/library/read-group identifier is required")
        return self


class AnalysisResultArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logical_name: str
    artifact_role: str
    relative_path: str | None = None
    storage_uri: str | None = None
    sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    version_id: str | None = None
    mime_type: str | None = None
    required: bool = True
    parser_hint: str | None = None
    sample_identifiers: list[SampleIdentifier] = Field(default_factory=list)

    @field_validator("logical_name", "artifact_role")
    @classmethod
    def _required_text(cls, value: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError("value is required")
        return clean

    @field_validator("sha256")
    @classmethod
    def _sha256(cls, value: str | None) -> str | None:
        clean = str(value or "").strip().lower()
        if not clean:
            return None
        if len(clean) != 64 or any(char not in "0123456789abcdef" for char in clean):
            raise ValueError("sha256 must be a 64-character lowercase hex digest")
        return clean

    @model_validator(mode="after")
    def _has_path(self) -> "AnalysisResultArtifact":
        if not str(self.relative_path or "").strip() and not str(self.storage_uri or "").strip():
            raise ValueError("relative_path or storage_uri is required")
        if self.storage_uri and not self.storage_uri.startswith("s3://"):
            raise ValueError("storage_uri must use s3://")
        if self.relative_path:
            self.relative_path = str(self.relative_path).strip().lstrip("/")
        return self


class AnalysisResultsRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    analysis_euid: str
    command_id: str
    result_status: TerminalResultStatus
    result_root_uri: str
    run_artifact_set_euid: str | None = None
    run_euid: str | None = None
    sidecar_artifact_euid: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    sample_identifiers: list[SampleIdentifier] = Field(default_factory=list)
    artifacts: list[AnalysisResultArtifact]

    @field_validator("analysis_euid", "command_id")
    @classmethod
    def _required_text(cls, value: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError("value is required")
        return clean

    @field_validator("result_root_uri")
    @classmethod
    def _result_root_uri(cls, value: str) -> str:
        clean = str(value or "").strip()
        if not clean.startswith("s3://"):
            raise ValueError("result_root_uri must use s3://")
        return clean.rstrip("/") + "/"

    @model_validator(mode="after")
    def _has_artifacts(self) -> "AnalysisResultsRegistrationRequest":
        if not self.artifacts:
            raise ValueError("at least one result artifact is required")
        return self


class RegistrationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    request_id: str
    idempotency_key: str
    registration_kind: str
    artifact_set_euid: str
    registered_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    skipped_existing: list[dict[str, Any]] = Field(default_factory=list)
    failed: list[dict[str, Any]] = Field(default_factory=list)
    registered_at: str
    status: str
    local_only: bool = False
    outbox_event_euid: str | None = None


class OutboxEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    occurred_at: str
    producer: str = "dewey"
    schema_version: str = "1.0"
    payload: dict[str, Any]
    correlation_id: str
    causation_id: str | None = None


class PipelineOrderEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline_code: str
    params: dict[str, Any]
    dewey_status: str
    dewey_date: str
    pipeline_attempts: list[dict[str, str]]


def canonical_json_bytes(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    else:
        payload = value
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def deterministic_idempotency_key(operation: str, value: Any) -> str:
    return f"{operation}:{canonical_sha256(value)}"


def parse_pipeline_order_tsv(text: str) -> list[PipelineOrderEntry]:
    rows: list[PipelineOrderEntry] = []
    for line_number, raw_line in enumerate(str(text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            raise ValueError(f"sidecar line {line_number} must have at least 6 TSV columns")
        if (len(parts) - 4) % 2 != 0:
            raise ValueError(
                f"sidecar line {line_number} must repeat pipeline_status/pipeline_date pairs"
            )
        pipeline_code = parts[0].strip()
        if not pipeline_code:
            raise ValueError(f"sidecar line {line_number} has empty pipeline_code")
        try:
            params = json.loads(parts[1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"sidecar line {line_number} params_json is invalid JSON") from exc
        if not isinstance(params, dict):
            raise ValueError(f"sidecar line {line_number} params_json must be a JSON object")
        attempts: list[dict[str, str]] = []
        for index in range(4, len(parts), 2):
            status = parts[index].strip()
            date = parts[index + 1].strip()
            if not status or not date:
                raise ValueError(
                    f"sidecar line {line_number} pipeline status/date columns are required"
                )
            attempts.append({"pipeline_status": status, "pipeline_date": date})
        rows.append(
            PipelineOrderEntry(
                pipeline_code=pipeline_code,
                params=params,
                dewey_status=parts[2].strip(),
                dewey_date=parts[3].strip(),
                pipeline_attempts=attempts,
            )
        )
    return rows
