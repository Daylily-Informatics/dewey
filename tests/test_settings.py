from __future__ import annotations

from pathlib import Path

import pytest

from dewey_service.settings import Settings, load_settings, persist_managed_storage_bucket


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
    assert loaded.cognito_group_role_map == {
        "platform-admin": "ADMIN",
        "dewey-admin": "ADMIN",
        "dewey-readwrite": "READ_WRITE",
        "dewey-readonly": "READ_ONLY",
    }
    assert loaded.deployment == {
        "name": "staging",
        "color": "#124e78",
        "is_production": False,
    }
    assert loaded.managed_storage_bucket == "dewey-artifacts-staging"
    assert loaded.managed_storage_prefix == "managed"


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
