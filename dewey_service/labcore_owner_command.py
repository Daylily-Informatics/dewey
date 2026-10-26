"""Additive TestEUID-bound command around the frozen DW-01 owner contract."""

from __future__ import annotations

import hashlib
import json
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from dewey_service.labcore_owner_contracts import LabcoreSequencingRunOwnerContractV1

COMMAND_TYPE = "dewey.labcore-sequencing-run-registration/v2"
COMMAND_VERSION = 2
HASH_DOMAIN = "dewey.labcore-sequencing-run-registration.command/v2"


class _CommandHashInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    command_type: str
    command_version: int
    hash_domain: str
    test_euid: str = Field(min_length=1)
    owner_request: LabcoreSequencingRunOwnerContractV1


def canonical_command_bytes(value: BaseModel | Mapping[str, object]) -> bytes:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude={"command_sha256", "idempotency_key"})
    else:
        payload = dict(value)
        payload.pop("command_sha256", None)
        payload.pop("idempotency_key", None)
    normalized = _CommandHashInput.model_validate(payload).model_dump(mode="json")
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def canonical_command_sha256(value: BaseModel | Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_command_bytes(value)).hexdigest()


def bind_registration_command(value: Mapping[str, object]) -> dict[str, object]:
    payload = dict(value)
    digest = canonical_command_sha256(payload)
    return {**payload, "command_sha256": digest, "idempotency_key": digest}


class LabcoreSequencingRunRegistrationCommandV2(_CommandHashInput):
    """A strict command that adds TestEUID without changing the DW-01 bytes."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    command_type: Literal[COMMAND_TYPE]
    command_version: Literal[COMMAND_VERSION]
    hash_domain: Literal[HASH_DOMAIN]
    command_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")

    @field_validator("test_euid", mode="before")
    @classmethod
    def _test_euid(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("test_euid is required")
        return value.strip()

    @model_validator(mode="after")
    def _bounded_inventory(self):
        if len(self.owner_request.expected_files) > 50_000:
            raise ValueError("At most 50,000 expected files are accepted")
        if any(
            len(item.relative_path.encode("utf-8")) > 1024
            for item in self.owner_request.expected_files
        ):
            raise ValueError("Relative paths must not exceed 1,024 UTF-8 bytes")
        return self

    @model_validator(mode="after")
    def _hashes_match(self) -> "LabcoreSequencingRunRegistrationCommandV2":
        expected = canonical_command_sha256(self)
        if self.command_sha256 != expected or self.idempotency_key != expected:
            raise ValueError(
                "command_sha256 and idempotency_key must match canonical command bytes"
            )
        return self
