from __future__ import annotations

from pathlib import Path

import pytest

from dewey_service.settings import (
    DEFAULT_DEPLOYMENT_BANNER_COLOR,
    Settings,
    _resolve_region_chrome,
    _resolve_deployment_chrome,
    _stable_region_color_hex,
    _stable_deployment_color_hex,
    build_effective_config_rows,
    load_settings,
    persist_managed_storage_bucket,
)


def test_settings_requires_https_cognito_domain() -> None:
    with pytest.raises(ValueError):
        Settings(
            cognito_domain="http://bad.example.com",
            cognito_app_client_id="x",
            cognito_redirect_uri="https://localhost:8914/auth/callback",
            cognito_logout_url="https://localhost:8914/login",
        )


def test_settings_loads_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")
    cfg_dir = tmp_path / "dewey-local"
    cfg_dir.mkdir(parents=True)
    cfg = cfg_dir / "dewey-config-local.yaml"
    cfg.write_text(
        """
application:
  api_bearer_token: yaml-token
auth:
  cognito:
    domain: https://auth.example.com
    app_client_id: client-1
    redirect_uri: https://localhost:8914/auth/callback
    logout_url: https://localhost:8914/login
    allowed_email_domains:
      - lsmc.com
      - lsmc.bio
      - lsmc.life
      - daylilyinformatics.com
    default_tenant_id: 00000000-0000-0000-0000-000000000000
    auto_provision_allowed_domains:
      - lsmc.com
    group_role_map:
      platform-admin: ADMIN
      dewey-admin: ADMIN
      dewey-readwrite: READ_WRITE
      dewey-readonly: READ_ONLY
deployment:
  name: staging
  color: "#124e78"
  is_production: false
storage:
  managed_bucket: dewey-artifacts-staging
  managed_prefix: managed
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DEWEY_API_BEARER_TOKEN", raising=False)
    loaded = load_settings()
    assert loaded.api_bearer_token == "yaml-token"
    assert loaded.cognito_domain == "https://auth.example.com"
    assert loaded.cognito_redirect_uri == "https://localhost:8914/auth/callback"
    assert loaded.cognito_logout_url == "https://localhost:8914/login"
    assert loaded.cognito_allowed_email_domains == [
        "lsmc.com",
        "lsmc.bio",
        "lsmc.life",
        "daylilyinformatics.com",
    ]
    assert loaded.cognito_default_tenant_id == "00000000-0000-0000-0000-000000000000"
    assert loaded.cognito_auto_provision_allowed_domains == ["lsmc.com"]
    assert loaded.cognito_group_role_map == {
        "platform-admin": "ADMIN",
        "dewey-admin": "ADMIN",
        "dewey-readwrite": "READ_WRITE",
        "dewey-readonly": "READ_ONLY",
    }
    assert loaded.deployment == {
        "name": "staging",
        "color": _stable_deployment_color_hex("staging"),
        "is_production": False,
    }
    assert loaded.managed_storage_bucket == "dewey-artifacts-staging"
    assert loaded.managed_storage_prefix == "managed"
    assert loaded.show_environment_chrome is True


def test_load_settings_aws_profile_prefers_dewey_env_over_config_and_shell_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DEWEY_AWS_PROFILE", "dewey-env-profile")
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    cfg_dir = tmp_path / "dewey-local"
    cfg_dir.mkdir(parents=True)
    cfg = cfg_dir / "dewey-config-local.yaml"
    cfg.write_text(
        """
application:
  api_bearer_token: yaml-token
auth:
  cognito:
    domain: https://auth.example.com
    app_client_id: client-1
    redirect_uri: https://localhost:8914/auth/callback
    logout_url: https://localhost:8914/login
database:
  backend: tapdb
aws:
  profile: config-profile
""",
        encoding="utf-8",
    )

    loaded = load_settings()

    assert loaded.aws_profile == "dewey-env-profile"


def test_settings_defaults_include_cognito_domain_policy() -> None:
    settings = Settings(
        api_bearer_token="token",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )

    assert settings.cognito_allowed_email_domains == [
        "lsmc.com",
        "lsmc.bio",
        "lsmc.life",
        "daylilyinformatics.com",
    ]
    assert settings.cognito_default_tenant_id == "00000000-0000-0000-0000-000000000000"
    assert settings.cognito_auto_provision_allowed_domains == ["lsmc.com"]


def test_settings_aws_profile_uses_config_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_PROFILE", "env-profile")
    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        aws_profile="config-profile",
    )
    assert loaded.aws_profile == "config-profile"


def test_settings_aws_profile_blank_does_not_use_shell_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_PROFILE", "env-profile")
    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        aws_profile="",
    )
    assert loaded.aws_profile == ""


def test_settings_aws_profile_blank_does_not_use_dewey_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEWEY_AWS_PROFILE", "dewey-env-profile")
    monkeypatch.setenv("AWS_PROFILE", "shell-profile")
    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        aws_profile="",
    )
    assert loaded.aws_profile == ""


def test_settings_aws_profile_missing_is_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEWEY_AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )
    assert loaded.aws_profile == ""


def test_settings_fall_back_to_deployment_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "stage-g")

    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        deployment_name="",
        deployment_color="#124e78",
        deployment_is_production=True,
    )

    assert loaded.deployment == {
        "name": "stage-g",
        "color": _stable_deployment_color_hex("stage-g"),
        "is_production": False,
    }


def test_prod_deployment_name_uses_derived_color() -> None:
    loaded = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        deployment_name="production",
        deployment_color="#124e78",
    )

    assert loaded.deployment == {
        "name": "production",
        "color": _stable_deployment_color_hex("production"),
        "is_production": True,
    }


def test_light_aqua_is_used_without_any_deployment_name() -> None:
    assert _resolve_deployment_chrome(name="", color="", fallback_name="") == {
        "name": "",
        "color": DEFAULT_DEPLOYMENT_BANNER_COLOR,
        "is_production": False,
    }


def test_deployment_color_is_derived_from_name_even_when_configured() -> None:
    assert _resolve_deployment_chrome(
        name="510x2",
        color="#124e78",
        fallback_name="local",
    ) == {
        "name": "510x2",
        "color": "#4321ca",
        "is_production": False,
    }


def test_region_color_is_derived_from_region_name() -> None:
    assert _stable_region_color_hex("us-east-1") == "#8aca72"
    assert _stable_region_color_hex("us-west-2") == "#a5ca72"
    assert _resolve_region_chrome("us-east-1") == {
        "name": "us-east-1",
        "color": "#8aca72",
    }


def test_effective_config_rows_redact_secret_values(tmp_path: Path) -> None:
    settings = Settings(
        api_bearer_token="token",
        session_secret_key="secret",
        cognito_domain="https://auth.example.com",
        cognito_app_client_id="client",
        cognito_app_client_secret="secret-client",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
        show_environment_chrome=False,
        aws_region="us-east-1",
    )

    rows = build_effective_config_rows(settings, config_path=tmp_path / "dewey.yaml")
    row_map = {row["path"]: row["value"] for row in rows}

    assert row_map["ui.show_environment_chrome"] == "false"
    assert row_map["auth.cognito.app_client_secret"] == "<redacted>"
    assert row_map["application.session_secret_key"] == "<redacted>"
    assert row_map["application.api_bearer_token"] == "<redacted>"
    assert row_map["aws.region"] == "us-east-1"
    assert row_map["auth.cognito.group_role_map.platform-admin"] == "ADMIN"
    assert row_map["config.file_path"] == str(tmp_path / "dewey.yaml")


def test_settings_allow_dewey_cognito_env_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")
    cfg_dir = tmp_path / "dewey-local"
    cfg_dir.mkdir(parents=True)
    cfg = cfg_dir / "dewey-config-local.yaml"
    cfg.write_text(
        """
application:
  api_bearer_token: yaml-token
auth:
  cognito:
    domain: https://yaml.example.com
    app_client_id: yaml-client
    redirect_uri: https://localhost:8914/auth/callback
    logout_url: https://localhost:8914/login
    group_role_map:
      platform-admin: ADMIN
      dewey-admin: ADMIN
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DEWEY_COGNITO_DOMAIN", "https://env.example.com")
    monkeypatch.setenv("DEWEY_COGNITO_APP_CLIENT_ID", "env-client")

    loaded = load_settings()

    assert loaded.cognito_domain == "https://env.example.com"
    assert loaded.cognito_app_client_id == "env-client"


def test_persist_managed_storage_bucket_creates_or_updates_storage_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "local")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path, normalized = persist_managed_storage_bucket("s3://dewey-artifacts-local")
    raw = config_path.read_text(encoding="utf-8")

    assert normalized == "dewey-artifacts-local"
    assert "storage:" in raw
    assert "managed_bucket: dewey-artifacts-local" in raw

    loaded = load_settings(config_path)
    assert loaded.managed_storage_bucket == "dewey-artifacts-local"
