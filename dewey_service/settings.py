"""Runtime settings for Dewey."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
            if isinstance(value, dict):
                _write(merged, value)
            else:
                out[merged] = value

    _write("", config)

    remap = {
        "runtime_api_bearer_token": "api_bearer_token",
        "runtime_api_bearer_tokens": "api_bearer_tokens",
        "runtime_session_secret_key": "session_secret_key",
        "runtime_host": "host",
        "runtime_port": "port",
        "runtime_verify_ssl": "verify_ssl",
        "database_backend": "database_backend",
        "database_target": "database_target",
        "database_namespace": "tapdb_database_name",
        "database_client_id": "tapdb_client_id",
        "database_env": "tapdb_env",
        "database_config_path": "tapdb_config_path",
        "aws_profile": "aws_profile",
        "aws_region": "aws_region",
        "auth_cognito_domain": "cognito_domain",
        "auth_cognito_app_client_id": "cognito_app_client_id",
        "auth_cognito_app_client_secret": "cognito_app_client_secret",
        "auth_cognito_redirect_uri": "cognito_redirect_uri",
        "auth_cognito_logout_url": "cognito_logout_url",
        "auth_cognito_user_pool_id": "cognito_user_pool_id",
        "auth_cognito_region": "cognito_region",
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
    port: int = 8913
    verify_ssl: bool = True

    # Cognito-backed operator UI auth
    cognito_domain: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str = ""
    cognito_redirect_uri: str = "https://localhost:8913/auth/callback"
    cognito_logout_url: str = "https://localhost:8913/login"
    cognito_user_pool_id: str = ""
    cognito_region: str = "us-west-2"

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

    # Share reference defaults
    default_share_reference_ttl_seconds: int = 3600

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


def get_config_file_path() -> Path:
    return _default_config_path()


def load_settings(config_path: Path | None = None) -> Settings:
    cfg_path = config_path or get_config_file_path()
    seed: dict[str, Any] = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if isinstance(raw, dict):
            seed = _flatten_config(raw)

    env_override: dict[str, Any] = {}
    env_key_remap = {
        "runtime__host": "host",
        "runtime__port": "port",
        "runtime__verify_ssl": "verify_ssl",
        "runtime__api_bearer_token": "api_bearer_token",
        "runtime__api_bearer_tokens": "api_bearer_tokens",
        "runtime__session_secret_key": "session_secret_key",
        "auth__cognito__domain": "cognito_domain",
        "auth__cognito__app_client_id": "cognito_app_client_id",
        "auth__cognito__app_client_secret": "cognito_app_client_secret",
        "auth__cognito__redirect_uri": "cognito_redirect_uri",
        "auth__cognito__logout_url": "cognito_logout_url",
        "auth__cognito__user_pool_id": "cognito_user_pool_id",
        "auth__cognito__region": "cognito_region",
        "tapdb__client_id": "tapdb_client_id",
        "tapdb__database_name": "tapdb_database_name",
        "tapdb__env": "tapdb_env",
        "tapdb__config_path": "tapdb_config_path",
        "aws__profile": "aws_profile",
        "aws__region": "aws_region",
        "application__environment": "environment",
        "features__default_share_reference_ttl_seconds": "default_share_reference_ttl_seconds",
    }
    for key, value in os.environ.items():
        if not key.startswith("DEWEY_"):
            continue
        raw_key = key[len("DEWEY_") :].lower()
        mapped_key = env_key_remap.get(raw_key)
        if mapped_key:
            env_override[mapped_key] = value
    merged = {**seed, **env_override}
    return Settings(**merged)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
