"""Closed configuration for the default-off Labcore owner API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from dewey_service.settings import get_config_file_path

LABCORE_OWNER_WRITE_SCOPE = "dewey.labcore-owner.write/v1"


class LabcoreOwnerServicePrincipal(BaseModel):
    """One service bearer, scope, and tenant binding."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    principal_id: str = Field(min_length=1)
    bearer_token: str = Field(min_length=1, repr=False)
    tenant_euid: str = Field(min_length=1)
    scopes: tuple[str, ...] = Field(min_length=1)

    @field_validator("principal_id", "bearer_token", "tenant_euid")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("service principal fields must be non-empty")
        return cleaned

    @field_validator("scopes", mode="before")
    @classmethod
    def _scopes(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("scopes must be a YAML list")
        scopes = tuple(str(item).strip() for item in value)
        if not scopes or any(not scope for scope in scopes) or len(set(scopes)) != len(scopes):
            raise ValueError("scopes must contain unique non-empty strings")
        return scopes


class LabcoreOwnerApiConfig(BaseModel):
    """Configuration parsed separately so the core Settings schema stays stable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    api_enabled: bool = False
    service_principals: tuple[LabcoreOwnerServicePrincipal, ...] = ()

    @field_validator("service_principals", mode="before")
    @classmethod
    def _principals(cls, value: object) -> tuple[object, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("service_principals must be a YAML list")
        return tuple(value)

    @model_validator(mode="after")
    def _unique_bindings(self) -> "LabcoreOwnerApiConfig":
        ids = [item.principal_id for item in self.service_principals]
        tokens = [item.bearer_token for item in self.service_principals]
        if len(ids) != len(set(ids)) or len(tokens) != len(set(tokens)):
            raise ValueError("service principal IDs and bearer tokens must be unique")
        if self.api_enabled and not self.service_principals:
            raise ValueError("Enabled Labcore API requires service principals")
        return self

    @property
    def is_enabled(self) -> bool:
        return self.api_enabled and bool(self.service_principals)


def _config_payload(path: Path) -> object:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("Dewey configuration root must be a mapping")
    return loaded.get("labcore_owner", {})


def load_labcore_owner_config() -> LabcoreOwnerApiConfig:
    """Load explicit YAML configuration, with opt-in environment overrides."""

    payload = _config_payload(get_config_file_path())
    if not isinstance(payload, dict):
        raise ValueError("labcore_owner must be a mapping")
    merged = dict(payload)
    enabled = os.environ.get("DEWEY_LABCORE_OWNER_API_ENABLED")
    principals = os.environ.get("DEWEY_LABCORE_OWNER_SERVICE_PRINCIPALS")
    if enabled is not None:
        if enabled not in {"true", "false"}:
            raise ValueError("DEWEY_LABCORE_OWNER_API_ENABLED must be true or false")
        merged["api_enabled"] = enabled == "true"
    if principals is not None:
        merged["service_principals"] = json.loads(principals)
    try:
        return LabcoreOwnerApiConfig.model_validate(merged)
    except ValidationError:
        raise ValueError("Invalid Labcore owner configuration") from None


def redacted_effective_config(config: LabcoreOwnerApiConfig) -> dict[str, object]:
    """Expose only non-secret effective configuration for diagnostics/tests."""

    return {
        "api_enabled": config.api_enabled,
        "service_principals": tuple(
            {
                "principal_id": item.principal_id,
                "tenant_euid": item.tenant_euid,
                "scopes": item.scopes,
            }
            for item in config.service_principals
        ),
    }
