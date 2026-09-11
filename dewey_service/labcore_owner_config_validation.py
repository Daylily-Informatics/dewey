"""Config-init validation adapter for the isolated Labcore owner settings."""

from __future__ import annotations

import yaml
from pydantic import ValidationError

from dewey_service.labcore_owner_config import LabcoreOwnerApiConfig


def validate_labcore_owner_config(content: str) -> list[str]:
    """Return closed configuration errors without rendering bearer values."""

    try:
        root = yaml.safe_load(content)
    except yaml.YAMLError:
        return ["labcore_owner configuration contains invalid YAML"]
    if not isinstance(root, dict):
        return []
    section = root.get("labcore_owner", {})
    try:
        LabcoreOwnerApiConfig.model_validate(section)
    except (ValidationError, ValueError):
        return ["labcore_owner configuration is invalid"]
    return []


def install_config_validator(spec) -> None:
    """Compose the lane validator into the normal cli-core config validator."""

    validator = spec.config.validator
    if getattr(validator, "_labcore_owner_validator", False):
        return

    def combined(content: str) -> list[str]:
        errors = validator(content)
        return errors or validate_labcore_owner_config(content)

    setattr(combined, "_labcore_owner_validator", True)
    object.__setattr__(spec.config, "validator", combined)
