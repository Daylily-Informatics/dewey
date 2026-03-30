from __future__ import annotations

from pathlib import Path

import pytest

from dewey_service.settings import Settings, load_settings


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


def test_settings_ignore_dewey_cognito_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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

    assert loaded.cognito_domain == "https://yaml.example.com"
    assert loaded.cognito_app_client_id == "yaml-client"
