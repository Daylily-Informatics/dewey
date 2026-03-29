"""Runtime settings for Dewey."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dewey_service.rbac import DEFAULT_COGNITO_GROUP_ROLE_MAP, normalize_group_role_map


def _require_https_url(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if not normalized.startswith("https://"):
        raise ValueError(f"{field_name} must use an absolute https:// URL")
    return normalized


def _validate_optional_https_url(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    if not normalized:
        return ""
    if not normalized.startswith("https://"):
        raise ValueError(f"{field_name} must use an absolute https:// URL")
    return normalized


def _default_config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "dewey" / "config.yaml"


def _flatten_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}

    out: dict[str, Any] = {}

    def _write(prefix: str, payload: dict[str, Any]) -> None:
        for key, value in payload.items():
            merged = f"{prefix}_{key}" if prefix else str(key)
            if merged == "auth_cognito_group_role_map" and isinstance(value, dict):
                out[merged] = value
            elif isinstance(value, dict):
                _write(merged, value)
            else:
                out[merged] = value

    _write("", config)

    remap = {
        "application_api_bearer_token": "api_bearer_token",
        "application_api_bearer_tokens": "api_bearer_tokens",
        "application_session_secret_key": "session_secret_key",
        "application_host": "host",
        "application_port": "port",
        "application_verify_ssl": "verify_ssl",
        "application_search_export_max_rows": "search_export_max_rows",
        "database_backend": "database_backend",
        "database_target": "database_target",
        "database_namespace": "tapdb_database_name",
        "database_client_id": "tapdb_client_id",
        "database_env": "tapdb_env",
        "database_config_path": "tapdb_config_path",
        "aws_profile": "aws_profile",
        "aws_region": "aws_region",
        "storage_managed_bucket": "managed_storage_bucket",
        "storage_managed_prefix": "managed_storage_prefix",
        "storage_upload_session_ttl_seconds": "upload_session_ttl_seconds",
        "auth_cognito_domain": "cognito_domain",
        "auth_cognito_app_client_id": "cognito_app_client_id",
        "auth_cognito_app_client_secret": "cognito_app_client_secret",
        "auth_cognito_redirect_uri": "cognito_redirect_uri",
        "auth_cognito_logout_url": "cognito_logout_url",
        "auth_cognito_user_pool_id": "cognito_user_pool_id",
        "auth_cognito_region": "cognito_region",
        "auth_cognito_group_role_map": "cognito_group_role_map",
        "deployment_name": "deployment_name",
        "deployment_color": "deployment_color",
        "deployment_is_production": "deployment_is_production",
    }
    normalized: dict[str, Any] = {}
    for key, value in out.items():
        normalized[remap.get(key, key)] = value
    return normalized


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEWEY_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    api_bearer_token: str = "dewey-dev-token"
    api_bearer_tokens: str = ""
    session_secret_key: str = "dewey-session-secret-change-me"
    host: str = "127.0.0.1"
    port: int = 8914
    verify_ssl: bool = True

    # Cognito-backed browser UI auth
    cognito_domain: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str = ""
    cognito_redirect_uri: str = "https://localhost:8914/auth/callback"
    cognito_logout_url: str = "https://localhost:8914/login"
    cognito_user_pool_id: str = ""
    cognito_region: str = "us-west-2"
    cognito_group_role_map: dict[str, str] = Field(
        default_factory=lambda: dict(DEFAULT_COGNITO_GROUP_ROLE_MAP)
    )

    deployment_name: str = ""
    deployment_color: str = "#0f766e"
    deployment_is_production: bool = False

    # TapDB runtime
    database_backend: str = "tapdb"
    database_target: str = "local"
    tapdb_client_id: str = "dewey"
    tapdb_database_name: str = "dewey"
    tapdb_env: str = "dev"
    tapdb_config_path: str = ""
    tapdb_strict_namespace: int = 1

    # AWS defaults for TapDB wrappers
    aws_profile: str = "lsmc"
    aws_region: str = "us-west-2"

    # Dewey-managed storage
    managed_storage_bucket: str = ""
    managed_storage_prefix: str = "artifacts"
    upload_session_ttl_seconds: int = 900

    # Literature integration
    literature_managed_copy_allowed_domains: str = "europepmc.org,ncbi.nlm.nih.gov"
    literature_metapub_cache_dir: str = ""
    literature_request_timeout_seconds: int = 10
    literature_max_redirects: int = 3

    # Share reference defaults
    default_share_reference_ttl_seconds: int = 3600
    search_export_max_rows: int = 1000

    @field_validator("cognito_redirect_uri", "cognito_logout_url")
    @classmethod
    def validate_cognito_urls(cls, value: str, info):
        return _validate_optional_https_url(value, field_name=str(info.field_name))

    @field_validator("database_backend")
    @classmethod
    def validate_db_backend(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized != "tapdb":
            raise ValueError("database_backend must be tapdb")
        return normalized

    @field_validator("database_target")
    @classmethod
    def validate_db_target(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"local", "aurora"}:
            raise ValueError("database_target must be one of: local, aurora")
        return normalized

    @field_validator("api_bearer_token")
    @classmethod
    def validate_api_bearer_token(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("api_bearer_token is required")
        return normalized

    @field_validator("cognito_group_role_map", mode="before")
    @classmethod
    def validate_cognito_group_role_map(cls, value: Any) -> dict[str, str]:
        return normalize_group_role_map(value)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"development", "staging", "production", "testing"}:
            raise ValueError(
                "environment must be one of: development, staging, production, testing"
            )
        return normalized

    @model_validator(mode="after")
    def validate_cognito_contract(self) -> "Settings":
        missing: list[str] = []
        if not str(self.cognito_domain or "").strip():
            missing.append("cognito_domain")
        if not str(self.cognito_app_client_id or "").strip():
            missing.append("cognito_app_client_id")
        if not str(self.cognito_redirect_uri or "").strip():
            missing.append("cognito_redirect_uri")
        if not str(self.cognito_logout_url or "").strip():
            missing.append("cognito_logout_url")
        if missing:
            raise ValueError("Cognito UI auth is required; missing settings: " + ", ".join(missing))
        self.cognito_domain = _require_https_url(
            self.cognito_domain,
            field_name="cognito_domain",
        )
        return self

    def api_tokens(self) -> set[str]:
        tokens = {str(self.api_bearer_token or "").strip()}
        for item in str(self.api_bearer_tokens or "").split(","):
            cleaned = str(item).strip()
            if cleaned:
                tokens.add(cleaned)
        return {item for item in tokens if item}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def deployment(self) -> dict[str, Any]:
        return {
            "name": self.deployment_name,
            "color": self.deployment_color,
            "is_production": self.deployment_is_production,
        }

    @property
    def literature_allowed_domains(self) -> set[str]:
        return {
            str(item or "").strip().lower()
            for item in str(self.literature_managed_copy_allowed_domains or "").split(",")
            if str(item or "").strip()
        }

def get_config_file_path() -> Path:
    return _default_config_path()


def load_settings(config_path: Path | None = None) -> Settings:
    cfg_path = config_path or get_config_file_path()
    seed: dict[str, Any] = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if isinstance(raw, dict):
            seed = _flatten_config(raw)

    yaml_only_defaults = {
        "cognito_domain": "",
        "cognito_app_client_id": "",
        "cognito_app_client_secret": "",
        "cognito_redirect_uri": "https://localhost:8914/auth/callback",
        "cognito_logout_url": "https://localhost:8914/login",
        "cognito_user_pool_id": "",
        "cognito_region": "us-west-2",
        "cognito_group_role_map": dict(DEFAULT_COGNITO_GROUP_ROLE_MAP),
        "deployment_name": "",
        "deployment_color": "#0f766e",
        "deployment_is_production": False,
    }
    env_override = {
        key[len("DEWEY_") :].lower(): value
        for key, value in os.environ.items()
        if key.startswith("DEWEY_") and key[len("DEWEY_") :].lower() not in yaml_only_defaults
    }
    merged = {**seed, **env_override}
    for key, default in yaml_only_defaults.items():
        merged[key] = seed.get(key, default)
    return Settings(**merged)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
