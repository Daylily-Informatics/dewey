"""Runtime settings for Dewey."""

from __future__ import annotations

import colorsys
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dewey_service.defaults import (
    DEFAULT_APP_PORT,
    DEFAULT_COGNITO_ALLOWED_EMAIL_DOMAINS,
    DEFAULT_TAPDB_CONFIG_DIR,
    DEFAULT_TAPDB_DOMAIN_REGISTRY_PATH,
    DEFAULT_TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH,
    build_default_config_template,
    default_cognito_logout_url,
    default_cognito_redirect_uri,
)
from dewey_service.rbac import DEFAULT_COGNITO_GROUP_ROLE_MAP, normalize_group_role_map

DEFAULT_COGNITO_DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_COGNITO_AUTO_PROVISION_ALLOWED_DOMAINS = ("lsmc.com",)

DEFAULT_DEPLOYMENT_BANNER_COLOR = "#AFEEEE"
PRODUCTION_DEPLOYMENT_NAMES = {"prod", "production"}
SENSITIVE_CONFIG_KEY_PARTS = {
    "secret",
    "token",
    "password",
    "passwd",
    "key",
    "credential",
    "private",
    "signing",
    "session",
    "cookie",
    "authorization",
    "client_secret",
    "api_key",
    "access_key",
    "secret_key",
}


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


def _read_first_env(*names: str) -> str:
    for name in names:
        value = str(os.environ.get(name) or "").strip()
        if value:
            return value
    return ""


def _require_bare_host(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    if not normalized:
        raise ValueError(f"{field_name} is required")
    parsed = urlsplit(normalized)
    if parsed.scheme or parsed.netloc or any(char in normalized for char in "/?#"):
        raise ValueError(f"{field_name} must be a bare host, not a URL")
    return normalized


def _normalize_email_domains(value: Any, *, default: tuple[str, ...] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, str):
        raw_items = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raise ValueError("email domains must be a string or list of strings")
    cleaned = [str(item or "").strip().lower() for item in raw_items if str(item or "").strip()]
    return cleaned if cleaned else list(default or [])


def _normalize_managed_storage_bucket(value: str, *, allow_empty: bool = True) -> str:
    normalized = str(value or "").strip()
    if normalized.startswith("s3://"):
        normalized = normalized[5:]
    normalized = normalized.strip().strip("/")
    if not normalized:
        if allow_empty:
            return ""
        raise ValueError("managed_storage_bucket is required")
    if "/" in normalized:
        raise ValueError(
            "managed_storage_bucket must be a bucket name, not an s3://bucket/key path"
        )
    if any(char.isspace() for char in normalized):
        raise ValueError("managed_storage_bucket must not contain whitespace")
    return normalized


def _default_config_path() -> Path:
    raw_config = str(os.environ.get("DEWEY_CONFIG") or "").strip()
    if raw_config:
        config_path = Path(raw_config).expanduser()
        if not config_path.is_absolute():
            raise RuntimeError(f"DEWEY_CONFIG must be an absolute path: {raw_config}")
        return config_path
    raw_root = str(os.environ.get("XDG_CONFIG_HOME") or "").strip()
    if not raw_root:
        raise RuntimeError("Dewey requires explicit XDG_CONFIG_HOME or DEWEY_CONFIG")
    root = Path(raw_root)
    if not root.is_absolute():
        raise RuntimeError(f"XDG_CONFIG_HOME must be an absolute path: {raw_root}")
    return root / _config_dir_name() / _config_filename()


def _sanitize_deployment_code(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-]+", "-", str(value or "").strip()).strip("-")
    if not cleaned:
        raise RuntimeError("Dewey deployment code is required")
    return cleaned


def _resolve_deployment_code() -> str:
    raw = (
        os.environ.get("DEWEY_DEPLOYMENT_CODE")
        or os.environ.get("DEPLOYMENT_CODE")
        or os.environ.get("LSMC_DEPLOYMENT_CODE")
    )
    return _sanitize_deployment_code(raw)


def _config_dir_name() -> str:
    return f"dewey-{_resolve_deployment_code()}"


def _config_filename() -> str:
    deployment = _resolve_deployment_code()
    return f"dewey-config-{deployment}.yaml"


def _stable_deployment_color_hex(name: str) -> str:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:8], "big") % 360
    red, green, blue = colorsys.hls_to_rgb(hue / 360.0, 0.46, 0.72)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )


def _stable_region_color_hex(name: str) -> str:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    hue = (int.from_bytes(digest[:8], "big") % 360 + 180) % 360
    red, green, blue = colorsys.hls_to_rgb(hue / 360.0, 0.62, 0.45)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )


def _resolve_deployment_chrome(
    *,
    name: str | None,
    color: str | None,
    deployment_code: str | None = None,
) -> dict[str, Any]:
    resolved_name = str(name or "").strip() or str(deployment_code or "").strip()
    if not resolved_name:
        raise ValueError("deployment.name is required")
    resolved_color = str(color or "").strip() or _stable_deployment_color_hex(resolved_name)
    return {
        "name": resolved_name,
        "color": resolved_color,
        "is_production": resolved_name.lower() in PRODUCTION_DEPLOYMENT_NAMES,
    }


def _resolve_region_chrome(name: str | None) -> dict[str, Any]:
    resolved_name = str(name or "").strip()
    if not resolved_name:
        raise ValueError("aws.region is required")
    return {
        "name": resolved_name,
        "color": _stable_region_color_hex(resolved_name),
    }


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
        "database_owner_repo_name": "tapdb_owner_repo_name",
        "database_domain_code": "tapdb_domain_code",
        "database_domain_registry_path": "tapdb_domain_registry_path",
        "database_prefix_ownership_registry_path": "tapdb_prefix_ownership_registry_path",
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
        "auth_cognito_allowed_email_domains": "cognito_allowed_email_domains",
        "auth_cognito_default_tenant_id": "cognito_default_tenant_id",
        "auth_cognito_auto_provision_allowed_domains": "cognito_auto_provision_allowed_domains",
        "auth_cognito_group_role_map": "cognito_group_role_map",
        "auth_mode": "auth_mode",
        "auth_external_broker_service_id": "external_broker_service_id",
        "auth_external_broker_login_url": "external_broker_login_url",
        "auth_external_broker_handoff_exchange_url": "external_broker_handoff_exchange_url",
        "auth_external_broker_service_token": "external_broker_service_token",
        "auth_external_broker_callback_url": "external_broker_callback_url",
        "auth_external_broker_logout_url": "external_broker_logout_url",
        "auth_external_broker_share_recipient_prepare_url": "external_broker_share_recipient_prepare_url",
        "auth_external_broker_ca_bundle": "external_broker_ca_bundle",
        "deployment_name": "deployment_name",
        "deployment_color": "deployment_color",
        "deployment_is_production": "deployment_is_production",
        "ui_show_environment_chrome": "show_environment_chrome",
        "show_environment_chrome": "show_environment_chrome",
    }
    normalized: dict[str, Any] = {}
    for key, value in out.items():
        normalized[remap.get(key, key)] = value
    return normalized


def _is_sensitive_config_path(path: str) -> bool:
    lowered = str(path or "").lower()
    return any(part in lowered for part in SENSITIVE_CONFIG_KEY_PARTS)


def _display_config_value(value: Any) -> str:
    if value is None:
        return "<unset>"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items) if items else "<unset>"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    text = str(value).strip()
    return text or "<unset>"


def _require_absolute_path(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    resolved = Path(normalized)
    if not resolved.is_absolute():
        raise ValueError(f"{field_name} must be an absolute file path")
    return str(resolved.resolve())


def _display_config_path(path: str) -> str:
    mapping = {
        "show_environment_chrome": "ui.show_environment_chrome",
        "deployment_name": "deployment.name",
        "deployment_color": "deployment.color",
        "deployment_is_production": "deployment.is_production",
        "environment": "application.environment",
        "api_bearer_token": "application.api_bearer_token",
        "api_bearer_tokens": "application.api_bearer_tokens",
        "session_secret_key": "application.session_secret_key",
        "host": "application.host",
        "port": "application.port",
        "verify_ssl": "application.verify_ssl",
        "cognito_domain": "auth.cognito.domain",
        "cognito_app_client_id": "auth.cognito.app_client_id",
        "cognito_app_client_secret": "auth.cognito.app_client_secret",
        "cognito_redirect_uri": "auth.cognito.redirect_uri",
        "cognito_logout_url": "auth.cognito.logout_url",
        "cognito_user_pool_id": "auth.cognito.user_pool_id",
        "cognito_region": "auth.cognito.region",
        "cognito_allowed_email_domains": "auth.cognito.allowed_email_domains",
        "cognito_default_tenant_id": "auth.cognito.default_tenant_id",
        "cognito_auto_provision_allowed_domains": "auth.cognito.auto_provision_allowed_domains",
        "cognito_group_role_map": "auth.cognito.group_role_map",
        "auth_mode": "auth.mode",
        "external_broker_service_id": "auth.external_broker.service_id",
        "external_broker_login_url": "auth.external_broker.login_url",
        "external_broker_handoff_exchange_url": "auth.external_broker.handoff_exchange_url",
        "external_broker_service_token": "auth.external_broker.service_token",
        "external_broker_callback_url": "auth.external_broker.callback_url",
        "external_broker_logout_url": "auth.external_broker.logout_url",
        "external_broker_share_recipient_prepare_url": "auth.external_broker.share_recipient_prepare_url",
        "external_broker_ca_bundle": "auth.external_broker.ca_bundle",
        "database_backend": "database.backend",
        "database_target": "database.target",
        "tapdb_client_id": "database.client_id",
        "tapdb_database_name": "database.namespace",
        "tapdb_owner_repo_name": "database.owner_repo_name",
        "tapdb_domain_code": "database.domain_code",
        "tapdb_domain_registry_path": "database.domain_registry_path",
        "tapdb_prefix_ownership_registry_path": "database.prefix_ownership_registry_path",
        "tapdb_config_path": "database.config_path",
        "tapdb_strict_namespace": "database.strict_namespace",
        "aws_profile": "aws.profile",
        "aws_region": "aws.region",
        "managed_storage_bucket": "storage.managed_bucket",
        "managed_storage_prefix": "storage.managed_prefix",
        "upload_session_ttl_seconds": "storage.upload_session_ttl_seconds",
        "literature_managed_copy_allowed_domains": "literature.managed_copy_allowed_domains",
        "literature_metapub_cache_dir": "literature.metapub_cache_dir",
        "literature_request_timeout_seconds": "literature.request_timeout_seconds",
        "literature_max_redirects": "literature.max_redirects",
        "default_share_reference_ttl_seconds": "share_reference.default_ttl_seconds",
        "external_reference_targets": "external_references.targets",
        "search_export_max_rows": "search.export_max_rows",
        "config_path": "config.file_path",
    }
    if path in mapping:
        return mapping[path]
    prefix_mapping = {
        "cognito_group_role_map.": "auth.cognito.group_role_map.",
    }
    for prefix, replacement in prefix_mapping.items():
        if path.startswith(prefix):
            return replacement + path[len(prefix) :]
    return path.replace("_", ".")


def build_effective_config_rows(settings: "Settings", *, config_path: Path) -> list[dict[str, str]]:
    payload = settings.model_dump(mode="python")
    payload["show_environment_chrome"] = settings.show_environment_chrome
    payload["config_path"] = str(config_path)

    rows: list[dict[str, str]] = []

    def _visit(path: str, value: Any) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                next_path = f"{path}.{key}" if path else str(key)
                _visit(next_path, value[key])
            return
        display_path = _display_config_path(path)
        rows.append(
            {
                "path": display_path,
                "value": "<redacted>"
                if _is_sensitive_config_path(display_path)
                else _display_config_value(value),
            }
        )

    for key in sorted(payload):
        _visit(str(key), payload[key])

    rows.sort(key=lambda item: item["path"])
    return rows


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
    port: int = DEFAULT_APP_PORT
    verify_ssl: bool = True

    auth_mode: str = "cognito"

    # Cognito-backed browser UI auth
    cognito_domain: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str = ""
    cognito_redirect_uri: str = default_cognito_redirect_uri()
    cognito_logout_url: str = default_cognito_logout_url()
    cognito_user_pool_id: str = ""
    cognito_region: str = "us-west-2"
    cognito_allowed_email_domains: list[str] = Field(
        default_factory=lambda: list(DEFAULT_COGNITO_ALLOWED_EMAIL_DOMAINS)
    )
    cognito_default_tenant_id: str = DEFAULT_COGNITO_DEFAULT_TENANT_ID
    cognito_auto_provision_allowed_domains: list[str] = Field(
        default_factory=lambda: list(DEFAULT_COGNITO_AUTO_PROVISION_ALLOWED_DOMAINS)
    )
    cognito_group_role_map: dict[str, str] = Field(
        default_factory=lambda: dict(DEFAULT_COGNITO_GROUP_ROLE_MAP)
    )
    external_broker_service_id: str = "dewey"
    external_broker_login_url: str = ""
    external_broker_handoff_exchange_url: str = ""
    external_broker_service_token: str = ""
    external_broker_callback_url: str = ""
    external_broker_logout_url: str = ""
    external_broker_share_recipient_prepare_url: str = ""
    external_broker_ca_bundle: str = ""

    deployment_name: str = ""
    deployment_color: str = ""
    deployment_is_production: bool = False
    network_allowed_hosts: list[str] = Field(default_factory=list)
    show_environment_chrome: bool = True

    # TapDB runtime
    database_backend: str = "tapdb"
    database_target: str = "local"
    tapdb_client_id: str = "dewey"
    tapdb_database_name: str = "dewey"
    tapdb_owner_repo_name: str = "dewey"
    tapdb_domain_code: str = "Z"
    tapdb_domain_registry_path: str = str(DEFAULT_TAPDB_DOMAIN_REGISTRY_PATH)
    tapdb_prefix_ownership_registry_path: str = str(DEFAULT_TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH)
    tapdb_config_path: str = str(DEFAULT_TAPDB_CONFIG_DIR / "dewey" / "dewey" / "tapdb-config.yaml")
    tapdb_strict_namespace: int = 1

    # AWS defaults for TapDB wrappers
    aws_profile: str = ""
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
    external_reference_targets: list[dict[str, Any]] = Field(default_factory=list)
    search_export_max_rows: int = 1000

    @field_validator("cognito_redirect_uri", "cognito_logout_url")
    @classmethod
    def validate_cognito_urls(cls, value: str, info):
        return _validate_optional_https_url(value, field_name=str(info.field_name))

    @field_validator(
        "external_broker_login_url",
        "external_broker_handoff_exchange_url",
        "external_broker_callback_url",
        "external_broker_logout_url",
        "external_broker_share_recipient_prepare_url",
    )
    @classmethod
    def validate_external_broker_urls(cls, value: str, info):
        return _validate_optional_https_url(value, field_name=str(info.field_name))

    @field_validator("auth_mode")
    @classmethod
    def validate_auth_mode(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"cognito", "external_broker"}:
            raise ValueError("auth_mode must be one of: cognito, external_broker")
        return normalized

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

    @field_validator("tapdb_owner_repo_name")
    @classmethod
    def validate_tapdb_owner_repo_name(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("tapdb_owner_repo_name is required")
        return normalized

    @field_validator("tapdb_domain_code")
    @classmethod
    def validate_tapdb_domain_code(cls, value: str) -> str:
        normalized = str(value or "").strip().upper()
        if not normalized:
            raise ValueError("tapdb_domain_code is required")
        return normalized

    @field_validator("tapdb_domain_registry_path", "tapdb_prefix_ownership_registry_path")
    @classmethod
    def validate_tapdb_registry_path(cls, value: str) -> str:
        return _require_absolute_path(value, field_name="TapDB registry path")

    @field_validator("api_bearer_token")
    @classmethod
    def validate_api_bearer_token(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("api_bearer_token is required")
        return normalized

    @field_validator("managed_storage_bucket")
    @classmethod
    def validate_managed_storage_bucket(cls, value: str) -> str:
        return _normalize_managed_storage_bucket(value, allow_empty=True)

    @field_validator("managed_storage_prefix")
    @classmethod
    def validate_managed_storage_prefix(cls, value: str) -> str:
        normalized = str(value or "").strip().strip("/")
        return normalized or "artifacts"

    @field_validator("cognito_group_role_map", mode="before")
    @classmethod
    def validate_cognito_group_role_map(cls, value: Any) -> dict[str, str]:
        return normalize_group_role_map(value)

    @field_validator(
        "cognito_allowed_email_domains", "cognito_auto_provision_allowed_domains", mode="before"
    )
    @classmethod
    def validate_cognito_email_domains(cls, value: Any) -> list[str]:
        return _normalize_email_domains(value)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"development", "staging", "production", "testing"}:
            raise ValueError(
                "environment must be one of: development, staging, production, testing"
            )
        return normalized

    @field_validator("cognito_default_tenant_id")
    @classmethod
    def validate_cognito_default_tenant_id(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return DEFAULT_COGNITO_DEFAULT_TENANT_ID
        return normalized

    @model_validator(mode="after")
    def validate_cognito_contract(self) -> "Settings":
        if self.auth_mode == "external_broker":
            missing = [
                field_name
                for field_name in (
                    "external_broker_service_id",
                    "external_broker_login_url",
                    "external_broker_handoff_exchange_url",
                    "external_broker_service_token",
                    "external_broker_callback_url",
                    "external_broker_logout_url",
                )
                if not str(getattr(self, field_name) or "").strip()
            ]
            if missing:
                raise ValueError(
                    "external_broker auth requires explicit settings: " + ", ".join(sorted(missing))
                )
            self.external_broker_service_id = str(self.external_broker_service_id).strip()
            self.external_broker_login_url = _require_https_url(
                self.external_broker_login_url,
                field_name="external_broker_login_url",
            )
            self.external_broker_handoff_exchange_url = _require_https_url(
                self.external_broker_handoff_exchange_url,
                field_name="external_broker_handoff_exchange_url",
            )
            self.external_broker_callback_url = _require_https_url(
                self.external_broker_callback_url,
                field_name="external_broker_callback_url",
            )
            self.external_broker_logout_url = _require_https_url(
                self.external_broker_logout_url,
                field_name="external_broker_logout_url",
            )
            self.external_broker_share_recipient_prepare_url = _validate_optional_https_url(
                self.external_broker_share_recipient_prepare_url,
                field_name="external_broker_share_recipient_prepare_url",
            )
            ca_bundle = str(self.external_broker_ca_bundle or "").strip()
            if ca_bundle and not Path(ca_bundle).is_file():
                raise ValueError("external_broker_ca_bundle does not exist")
        if str(self.cognito_domain or "").strip():
            self.cognito_domain = _require_bare_host(
                self.cognito_domain,
                field_name="cognito_domain",
            )
        if str(self.cognito_redirect_uri or "").strip():
            self.cognito_redirect_uri = _require_https_url(
                self.cognito_redirect_uri,
                field_name="cognito_redirect_uri",
            )
        if str(self.cognito_logout_url or "").strip():
            self.cognito_logout_url = _require_https_url(
                self.cognito_logout_url,
                field_name="cognito_logout_url",
            )
        self.cognito_allowed_email_domains = _normalize_email_domains(
            self.cognito_allowed_email_domains,
            default=DEFAULT_COGNITO_ALLOWED_EMAIL_DOMAINS,
        )
        self.cognito_auto_provision_allowed_domains = _normalize_email_domains(
            self.cognito_auto_provision_allowed_domains,
            default=DEFAULT_COGNITO_AUTO_PROVISION_ALLOWED_DOMAINS,
        )
        deployment = _resolve_deployment_chrome(
            name=self.deployment_name,
            color=self.deployment_color,
            deployment_code=_resolve_deployment_code(),
        )
        self.deployment_name = str(deployment["name"])
        self.deployment_color = str(deployment["color"])
        self.deployment_is_production = bool(deployment["is_production"])
        tapdb_config_path = str(os.environ.get("TAPDB_CONFIG_PATH") or "").strip()
        if tapdb_config_path:
            self.tapdb_config_path = tapdb_config_path
        else:
            self.tapdb_config_path = str(self.tapdb_config_path or "").strip()
        self.tapdb_config_path = _require_absolute_path(
            self.tapdb_config_path,
            field_name="tapdb_config_path",
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

    def validate_cognito_email_domain(self, email: str) -> tuple[bool, str]:
        if not email:
            return False, "Email address is required"
        if "@" not in email:
            return False, "Invalid email address format"
        domain = email.split("@")[-1].strip().lower()
        if not domain:
            return False, "Invalid email address: missing domain"
        allowed = {
            str(item or "").strip().lower()
            for item in self.cognito_allowed_email_domains
            if str(item or "").strip()
        }
        if domain not in allowed:
            return False, (
                f"Email domain '{domain}' is not allowed. "
                f"Registration is restricted to: {', '.join(sorted(allowed))}"
            )
        return True, ""


def get_config_file_path() -> Path:
    return _default_config_path()


def _template_config_payload() -> dict[str, Any]:
    raw = yaml.safe_load(build_default_config_template().decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Default Dewey config template must parse to a mapping")
    return raw


def _load_config_payload(config_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    cfg_path = config_path or get_config_file_path()
    if not cfg_path.exists():
        raise ValueError(f"Dewey config file is required: {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root YAML object must be a mapping")
    return cfg_path, raw


def load_config_aws_profile(config_path: Path | None = None) -> str:
    _cfg_path, raw = _load_config_payload(config_path)
    aws_config = raw.get("aws")
    if not isinstance(aws_config, dict):
        return ""
    return str(aws_config.get("profile") or "").strip()


def persist_managed_storage_bucket(
    bucket: str,
    *,
    config_path: Path | None = None,
) -> tuple[Path, str]:
    cfg_path, raw = _load_config_payload(config_path)
    normalized = _normalize_managed_storage_bucket(bucket, allow_empty=False)
    storage = raw.get("storage")
    if not isinstance(storage, dict):
        storage = {}
    storage["managed_bucket"] = normalized
    storage["managed_prefix"] = (
        str(storage.get("managed_prefix") or "").strip().strip("/") or "artifacts"
    )
    storage["upload_session_ttl_seconds"] = int(storage.get("upload_session_ttl_seconds") or 900)
    raw["storage"] = storage
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    clear_settings_cache()
    return cfg_path, normalized


def load_settings(config_path: Path | None = None) -> Settings:
    cfg_path = config_path or get_config_file_path()
    if not cfg_path.exists():
        raise ValueError(f"Dewey config file is required: {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root YAML object must be a mapping")
    seed: dict[str, Any] = _flatten_config(raw)

    yaml_only_defaults = {
        "cognito_domain": "",
        "cognito_app_client_id": "",
        "cognito_app_client_secret": "",
        "cognito_redirect_uri": default_cognito_redirect_uri(),
        "cognito_logout_url": default_cognito_logout_url(),
        "cognito_user_pool_id": "",
        "cognito_region": "us-west-2",
        "cognito_allowed_email_domains": list(DEFAULT_COGNITO_ALLOWED_EMAIL_DOMAINS),
        "cognito_default_tenant_id": DEFAULT_COGNITO_DEFAULT_TENANT_ID,
        "cognito_auto_provision_allowed_domains": list(
            DEFAULT_COGNITO_AUTO_PROVISION_ALLOWED_DOMAINS
        ),
        "cognito_group_role_map": dict(DEFAULT_COGNITO_GROUP_ROLE_MAP),
        "auth_mode": "cognito",
        "external_broker_service_id": "dewey",
        "external_broker_login_url": "",
        "external_broker_handoff_exchange_url": "",
        "external_broker_callback_url": "",
        "external_broker_logout_url": "",
        "external_broker_share_recipient_prepare_url": "",
        "external_broker_ca_bundle": "",
        "deployment_name": "",
        "deployment_color": "",
        "deployment_is_production": False,
        "show_environment_chrome": True,
    }
    env_override = {
        key[len("DEWEY_") :].lower(): value
        for key, value in os.environ.items()
        if key.startswith("DEWEY_")
    }
    shared_auth_env = {
        "auth_mode": _read_first_env("LSMC_AUTH_MODE"),
        "external_broker_service_id": _read_first_env(
            "LSMC_AUTH_BROKER_SERVICE_ID",
            "LSMC_AUTH_SERVICE_ID",
        ),
        "external_broker_login_url": _read_first_env("LSMC_AUTH_BROKER_LOGIN_URL"),
        "external_broker_handoff_exchange_url": _read_first_env(
            "LSMC_AUTH_BROKER_HANDOFF_EXCHANGE_URL"
        ),
        "external_broker_service_token": _read_first_env("LSMC_AUTH_BROKER_SERVICE_TOKEN"),
        "external_broker_callback_url": _read_first_env("LSMC_AUTH_BROKER_CALLBACK_URL"),
        "external_broker_logout_url": _read_first_env("LSMC_AUTH_BROKER_LOGOUT_URL"),
        "external_broker_share_recipient_prepare_url": _read_first_env(
            "LSMC_AUTH_BROKER_SHARE_RECIPIENT_PREPARE_URL",
            "DEWEY_EXTERNAL_SHARE_RECIPIENT_PREPARE_URL",
        ),
        "external_broker_ca_bundle": _read_first_env("LSMC_AUTH_BROKER_CA_BUNDLE"),
    }
    merged = {**seed}
    for key, default in yaml_only_defaults.items():
        merged[key] = seed.get(key, default)
    merged.update(env_override)
    merged.update({key: value for key, value in shared_auth_env.items() if value})
    return Settings(**merged)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
