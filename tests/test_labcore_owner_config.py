from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from dewey_service.cli import spec
from dewey_service.defaults import build_default_config_template
from dewey_service.labcore_owner_config import (
    LABCORE_OWNER_WRITE_SCOPE,
    LabcoreOwnerApiConfig,
    load_labcore_owner_config,
    redacted_effective_config,
)


def _principal(*, principal_id="owy-v4", token="test-token", tenant="TENANT-1") -> dict:
    return {
        "principal_id": principal_id,
        "bearer_token": token,
        "tenant_euid": tenant,
        "scopes": [LABCORE_OWNER_WRITE_SCOPE],
    }


def test_yaml_scope_lists_are_strict_and_effective_view_never_exposes_bearers(
    tmp_path, monkeypatch
) -> None:
    config_path = tmp_path / "dewey.yaml"
    config_path.write_text(
        "labcore_owner:\n  api_enabled: true\n  service_principals:\n"
        "    - principal_id: owy-v4\n      bearer_token: test-token\n"
        "      tenant_euid: TENANT-1\n      scopes:\n"
        f"        - {LABCORE_OWNER_WRITE_SCOPE}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "dewey_service.labcore_owner_config.get_config_file_path", lambda: config_path
    )
    config = load_labcore_owner_config()
    assert config.is_enabled
    assert config.service_principals[0].scopes == (LABCORE_OWNER_WRITE_SCOPE,)
    rendered = str(redacted_effective_config(config))
    assert "test-token" not in rendered
    assert "bearer_token" not in rendered


def test_duplicate_principal_or_cross_tenant_bearer_bindings_fail_closed() -> None:
    with pytest.raises(ValidationError):
        LabcoreOwnerApiConfig.model_validate(
            {
                "api_enabled": True,
                "service_principals": [_principal(), _principal(tenant="TENANT-2")],
            }
        )
    with pytest.raises(ValidationError):
        LabcoreOwnerApiConfig.model_validate(
            {
                "api_enabled": True,
                "service_principals": [
                    _principal(principal_id="owy-a"),
                    _principal(principal_id="owy-b", token="test-token", tenant="TENANT-2"),
                ],
            }
        )


def test_generated_config_keeps_the_owner_api_default_off(monkeypatch) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "test")
    template = build_default_config_template(session_secret_key="test-session").decode("utf-8")
    assert "labcore_owner:" in template
    assert "api_enabled: false" in template
    assert "service_principals: []" in template


def test_missing_config_is_fail_closed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "dewey_service.labcore_owner_config.get_config_file_path", lambda: tmp_path / "absent.yaml"
    )
    with pytest.raises(FileNotFoundError):
        load_labcore_owner_config()


def test_normal_dewey_config_validator_rejects_invalid_lane(monkeypatch) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "test")
    config = yaml.safe_load(build_default_config_template(session_secret_key="test-session"))
    config["labcore_owner"] = {
        "api_enabled": True,
        "service_principals": [_principal(), _principal(principal_id="other")],
    }
    assert spec.config.validator(yaml.safe_dump(config)) == [
        "labcore_owner configuration is invalid"
    ]


def test_enabled_requires_principal_and_malformed_override_fails(monkeypatch, explicit_config_file):
    with pytest.raises(ValidationError):
        LabcoreOwnerApiConfig(api_enabled=True)
    monkeypatch.setenv("DEWEY_LABCORE_OWNER_API_ENABLED", "tru")
    with pytest.raises(ValueError, match="must be true or false"):
        load_labcore_owner_config()
