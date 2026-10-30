"""Extra config subcommands for Dewey."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

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
    Settings,
    _flatten_config,
    build_effective_config_rows,
    clear_settings_cache,
    get_config_file_path,
    get_settings,
    persist_managed_storage_bucket,
)


class _FileSettings(Settings):
    """Release preparation validates the file itself, without ambient overrides."""

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        return (init_settings,)


_RECIPIENT_ENDPOINTS = {
    "share_login_url": "/auth/share",
    "identity_url": "/api/v1/dewey/identity/introspect",
    "identity_mint_url": "/api/v1/dewey/identity/credentials",
    "identity_revoke_url": "/api/v1/dewey/identity/revoke",
}


def _endpoint_authority(value, path):
    if not isinstance(value, str) or value != value.strip():
        raise ValueError("An exact HTTPS endpoint is required")
    parsed = urlsplit(value)
    query_allowed = not parsed.query or (path == "/auth/logout" and parsed.query == "service=dewey")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or not query_allowed
        or parsed.fragment
        or parsed.path != path
        or parsed.netloc != parsed.netloc.lower()
        or any(c.isspace() for c in value)
    ):
        raise ValueError("An exact HTTPS endpoint is required")
    if parsed.port not in {None, 443}:
        raise ValueError("Broker endpoints must use HTTPS port 443")
    return parsed.netloc


def _prepare_sharing_v12(
    destination: Path = typer.Option(..., help="Absolute new private Dewey 12 configuration path."),
    recipient_contract: Path = typer.Option(
        ...,
        exists=True,
        dir_okay=False,
        help="Absolute private JSON containing the public assertion and four explicit broker endpoints.",
    ),
) -> None:
    """Write a new validated sharing configuration, preserving every existing authority."""
    from dewey_service.share_routing import validate_sharing_configuration

    source = Path(get_config_file_path())
    if not all(path.is_absolute() for path in (source, destination, recipient_contract)):
        raise typer.BadParameter(
            "Source, destination and recipient contract must use absolute paths"
        )
    if destination.exists() or destination.is_symlink() or destination == source:
        raise typer.BadParameter(
            "Destination must be a new file; existing configurations are never overwritten"
        )
    metadata = recipient_contract.stat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise typer.BadParameter(
            "Recipient contract must be a private regular file with no group or other permissions"
        )
    try:
        original = source.read_bytes()
        payload = yaml.safe_load(original)
        contract = json.loads(recipient_contract.read_bytes())
        if (
            not isinstance(payload, dict)
            or not isinstance(contract, dict)
            or set(contract) != {"public_ingress_assertion", "auth"}
        ):
            raise ValueError()
        if not isinstance(contract["auth"], dict) or set(contract["auth"]) != {"external_broker"}:
            raise ValueError()
        additions = contract["auth"]["external_broker"]
        if not isinstance(additions, dict) or set(additions) != set(_RECIPIENT_ENDPOINTS):
            raise ValueError()
        current_auth, current_share = payload["auth"], payload["share"]
        if current_auth["mode"] != "external_broker" or not isinstance(current_share, dict):
            raise ValueError()
        current_broker = current_auth["external_broker"]
        if current_broker["service_id"] != "dewey" or not current_broker["service_token"]:
            raise ValueError()
        authority = _endpoint_authority(current_broker["login_url"], "/auth/login")
        if (
            _endpoint_authority(current_broker["handoff_exchange_url"], "/auth/handoff/consume")
            != authority
        ):
            raise ValueError()
        if _endpoint_authority(current_broker["logout_url"], "/auth/logout") != authority:
            raise ValueError()
        origin = urlsplit(current_share["application_origin"])
        callback_authority = _endpoint_authority(
            current_broker["callback_url"], "/auth/lsmc/callback"
        )
        if (
            origin.scheme != "https"
            or origin.netloc != callback_authority
            or origin.path
            or origin.query
            or origin.fragment
        ):
            raise ValueError()
        for field, path in _RECIPIENT_ENDPOINTS.items():
            if _endpoint_authority(additions[field], path) != authority:
                raise ValueError()
            if current_broker.get(field) and current_broker[field] != additions[field]:
                raise ValueError()
        if (
            current_share.get("public_ingress_assertion")
            and current_share["public_ingress_assertion"] != contract["public_ingress_assertion"]
        ):
            raise ValueError()
        if (
            current_share.get("public_ingress_assertion_header", "X-Dewey-Recipient-Assertion")
            != "X-Dewey-Recipient-Assertion"
        ):
            raise ValueError()
        candidate = {
            **payload,
            "auth": {**current_auth, "external_broker": {**current_broker, **additions}},
            "share": {
                **current_share,
                "public_ingress_assertion": contract["public_ingress_assertion"],
                "public_ingress_assertion_header": "X-Dewey-Recipient-Assertion",
            },
        }
        # Required private/session/origin fields must exist in the source file.
        if any(
            not current_share.get(field)
            for field in (
                "ingress_assertion",
                "ingress_assertion_header",
                "trusted_proxy_peer",
                "application_origin",
                "content_host_suffix",
                "session_generation",
            )
        ):
            raise ValueError()
        if not payload["application"]["session_secret_key"]:
            raise ValueError()
        prepared = _FileSettings(**_flatten_config(candidate))
        validate_sharing_configuration(prepared)
        content = yaml.safe_dump(candidate, sort_keys=False).encode()
    except Exception:
        # Pydantic/parser exceptions can echo supplied credential values.
        raise typer.BadParameter(
            "Invalid recipient contract or source configuration: exact endpoint authority, retained private/session settings and complete sharing configuration are required"
        ) from None
    if source.read_bytes() != original:
        raise typer.BadParameter(
            "Source configuration changed during preparation; review the current source"
        )
    with os.fdopen(
        os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    ccyo_out.emit_json(
        {
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "destination_sha256": hashlib.sha256(content).hexdigest(),
        }
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
    principals: Path = typer.Option(
        ..., exists=True, dir_okay=False, help="Explicit SHA256-to-subject/roles JSON mapping."
    ),
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
        if (
            not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            or not isinstance(identity, dict)
            or not str(identity.get("subject", "")).strip()
        ):
            raise typer.BadParameter(
                "Each service credential needs a SHA256 fingerprint and explicit subject"
            )
        roles = identity.get("roles")
        if (
            not isinstance(roles, list)
            or not roles
            or set(roles) - {"ADMIN", "READ_WRITE", "READ_ONLY"}
        ):
            raise typer.BadParameter("Each service principal needs explicit valid roles")
    required = {hashlib.sha256(token.encode()).hexdigest() for token in settings.api_tokens()}
    if set(identities) != required:
        raise typer.BadParameter(
            "Principal manifest must exactly cover the configured general API credentials"
        )
    payload = yaml.safe_load(source.read_text())
    payload["registry"] = {
        **payload.get("registry", {}),
        "internal_domains": ["lsmc.com"],
        "service_principals": identities,
        "default_share_lifetime_days": None,
    }
    payload["share"] = {**payload.get("share", {}), "default_signed_ttl_seconds": 900}
    content = yaml.safe_dump(payload, sort_keys=False).encode()
    with os.fdopen(
        os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    ccyo_out.emit_json(
        {
            "status": "prepared",
            "source": str(source),
            "destination": str(destination),
            "sha256": hashlib.sha256(content).hexdigest(),
            "service_principal_count": len(identities),
            "active_configuration_changed": False,
        }
    )


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
    registry.add_command(
        "config",
        "prepare-registry-release",
        _prepare_registry_release,
        help_text="Prepare the explicit Dewey 10 configuration and service principal mappings.",
        policy=REQUIRED_MUTATING,
    )
    registry.add_command(
        "config",
        "prepare-sharing-v12",
        _prepare_sharing_v12,
        help_text="Prepare a new private Dewey 12 recipient configuration without changing the active file.",
        policy=REQUIRED_MUTATING,
    )
