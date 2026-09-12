"""Extra config subcommands for Dewey."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
import hashlib
import json
import os
import re
import yaml

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import REQUIRED, REQUIRED_MUTATING
from dewey_service.labcore_owner_config import (
    load_labcore_owner_config,
    redacted_effective_config,
)
from dewey_service.labcore_owner_config_validation import install_config_validator
from dewey_service.settings import (
    build_effective_config_rows,
    clear_settings_cache,
    get_config_file_path,
    get_settings,
    persist_managed_storage_bucket,
)


def _status() -> None:
    """Show merged Dewey runtime settings."""
    clear_settings_cache()
    try:
        settings = get_settings()
    except Exception as exc:
        ccyo_out.error(f"Configuration invalid: {exc}")
        raise typer.Exit(1) from exc

    ccyo_out.print_text(f"Config path: [cyan]{get_config_file_path()}[/cyan]")
    for row in build_effective_config_rows(settings, config_path=get_config_file_path()):
        ccyo_out.print_text(f"{row['path']}={row['value']}")
    owner_config = redacted_effective_config(load_labcore_owner_config())
    if owner_config["api_enabled"] or owner_config["service_principals"]:
        ccyo_out.print_text(f"labcore_owner.api_enabled={owner_config['api_enabled']}")
        for principal in owner_config["service_principals"]:
            ccyo_out.print_text(
                "labcore_owner.service_principal="
                f"{principal['principal_id']}:{principal['tenant_euid']}:{','.join(principal['scopes'])}"
            )


def _set_artifact_bucket(
    bucket: str = typer.Argument(
        ..., help="S3 bucket name for Dewey-managed artifact copies and uploads."
    ),
) -> None:
    """Persist the managed artifact bucket in the Dewey config file."""
    try:
        config_path, normalized = persist_managed_storage_bucket(bucket)
        settings = get_settings()
    except Exception as exc:
        ccyo_out.error(f"Could not update artifact bucket: {exc}")
        raise typer.Exit(1) from exc

    ccyo_out.success(f"Updated artifact bucket in {config_path}")
    ccyo_out.print_text(f"managed_storage_bucket={settings.managed_storage_bucket or normalized}")


def _prepare_registry_release(
    destination: Path = typer.Option(..., help="Absolute new private service configuration path."),
    principals: Path = typer.Option(..., exists=True, dir_okay=False, help="Explicit SHA256-to-subject/roles JSON mapping."),
) -> None:
    """Prepare a new Dewey 10 configuration without modifying the active file."""
    source = get_config_file_path()
    if not destination.is_absolute() or not principals.is_absolute():
        raise typer.BadParameter("Configuration and principal manifest paths must be absolute")
    settings = get_settings()
    identities = json.loads(principals.read_text())
    if not isinstance(identities, dict):
        raise typer.BadParameter("Principal manifest must be an object")
    for fingerprint, identity in identities.items():
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint) or not isinstance(identity, dict) or not str(identity.get("subject", "")).strip():
            raise typer.BadParameter("Each service credential needs a SHA256 fingerprint and explicit subject")
        roles = identity.get("roles")
        if not isinstance(roles, list) or not roles or set(roles) - {"ADMIN", "READ_WRITE", "READ_ONLY"}:
            raise typer.BadParameter("Each service principal needs explicit valid roles")
    required = {hashlib.sha256(token.encode()).hexdigest() for token in settings.api_tokens()}
    if set(identities) != required:
        raise typer.BadParameter("Principal manifest must exactly cover the configured general API credentials")
    payload = yaml.safe_load(source.read_text())
    payload["registry"] = {**payload.get("registry", {}), "internal_domains": ["lsmc.com"],
        "service_principals": identities, "default_share_lifetime_days": 30}
    payload["share"] = {**payload.get("share", {}), "default_signed_ttl_seconds": 900}
    content = yaml.safe_dump(payload, sort_keys=False).encode()
    with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    ccyo_out.emit_json({"status": "prepared", "source": str(source), "destination": str(destination),
        "sha256": hashlib.sha256(content).hexdigest(), "service_principal_count": len(identities),
        "active_configuration_changed": False})


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register Dewey-specific config subcommands."""
    if hasattr(spec, "config"):
        install_config_validator(spec)
    registry.add_command(
        "config",
        "status",
        _status,
        help_text="Show merged Dewey runtime settings",
        policy=REQUIRED,
    )
    registry.add_command(
        "config",
        "set-artifact-bucket",
        _set_artifact_bucket,
        help_text="Set the S3 bucket Dewey uses for managed artifact storage.",
        policy=REQUIRED_MUTATING,
    )
    registry.add_command("config", "prepare-registry-release", _prepare_registry_release,
        help_text="Prepare the explicit Dewey 10 configuration and service principal mappings.", policy=REQUIRED_MUTATING)
