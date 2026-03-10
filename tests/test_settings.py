from __future__ import annotations

from pathlib import Path

import pytest

from dewey_service.settings import Settings, load_settings


def test_settings_requires_https_cognito_domain() -> None:
    with pytest.raises(ValueError):
        Settings(
            cognito_domain="http://bad.example.com",
            cognito_app_client_id="x",
            cognito_redirect_uri="https://localhost:8913/auth/callback",
        )


def test_settings_loads_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "dewey"
    cfg_dir.mkdir(parents=True)
    cfg = cfg_dir / "config.yaml"
    cfg.write_text(
        """
application:
  api_bearer_token: yaml-token
auth:
  cognito:
    domain: https://auth.example.com
    app_client_id: client-1
    redirect_uri: https://localhost:8913/auth/callback
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DEWEY_API_BEARER_TOKEN", raising=False)
    loaded = load_settings()
    assert loaded.api_bearer_token == "yaml-token"
    assert loaded.cognito_domain == "https://auth.example.com"
