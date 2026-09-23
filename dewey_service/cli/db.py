"""Read-only Dewey verification and explicit TapDB lifecycle delegation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

import typer
from cli_core_yo import ccyo_out

from dewey_service.cli._registry_v2 import EXEMPT, REQUIRED, REQUIRED_MUTATING, register_group_commands

if TYPE_CHECKING:
    from cli_core_yo.registry import CommandRegistry
    from cli_core_yo.spec import CliSpec


db_app = typer.Typer(help="Verify existing Dewey data and review native TapDB lifecycle ownership")


@db_app.command("verify-templates")
def verify_templates() -> None:
    """Verify existing Dewey templates using SELECT-only runtime operations."""
    from dewey_service.tapdb_backend import TapDBBackend

    try:
        backend = TapDBBackend(app_username="dewey")
        with backend.session_scope(commit=False) as session:
            backend.ensure_templates(session)
        ccyo_out.success("Dewey required templates are present; no data changed")
    except RuntimeError as exc:
        ccyo_out.error(str(exc))
        raise typer.Exit(1) from exc


@db_app.command("lifecycle")
def lifecycle() -> None:
    """Show the external native lifecycle required before starting Dewey."""
    ccyo_out.print_text(
        "Dewey startup only verifies existing templates and runtime access. "
        "It never creates databases, migrates schemas, seeds templates or prepares principals.\n"
        "Use the reviewed migration ledger with an explicit absolute operator config: "
        "tapdb --config /absolute/operator-config.yaml --help.\n"
        "TapDB 10.1.1rc1 owns backup plan/create/verify/restore-plan/restore, "
        "db schema migrate, db identity inventory/verify, db sequences advance/verify/reconcile, "
        "and db runtime-principal bootstrap/bind.\n"
        "Application data preparation belongs in an explicitly reviewed native lifecycle, "
        "never a startup overlay. Preserve existing identities, domain/prefix bindings and "
        "allocator floors. Do not seed or overwrite historical Dewey templates.\n"
        "After preservation and runtime-principal binding, close old sessions and start "
        "Dewey with the exact bound runtime config."
    )


def registry_conversion(
    mode: str = typer.Argument(..., help="plan, apply, or reverse; never runs at startup."),
    actor: str = typer.Option(...),
    manifest: Path = typer.Option(...),
    receipt: Path | None = typer.Option(None),
    expected_sha256: str | None = typer.Option(None),
) -> None:
    """Plan or execute the explicit Dewey 10 data conversion with private receipts."""
    from dewey_service.registry_conversion import main
    import os
    config = os.environ.get("DEWEY_CONFIG", "")
    if not config or not Path(config).is_absolute():
        raise typer.BadParameter("Set DEWEY_CONFIG to the explicit absolute service configuration")
    if mode not in {"plan", "apply", "reverse"} or not manifest.is_absolute() or receipt is not None and not receipt.is_absolute():
        raise typer.BadParameter("Choose plan/apply/reverse and absolute manifest/receipt paths")
    args = [mode, "--actor", actor, "--manifest", str(manifest)]
    if receipt is not None:
        args += ["--receipt", str(receipt)]
    if expected_sha256:
        args += ["--expected-sha256", expected_sha256]
    main(args)


def registry_templates(
    operator_config: Path = typer.Option(..., exists=True, dir_okay=False),
    repository_pack: Path = typer.Option(..., exists=True, dir_okay=False),
    receipt_pack: Path = typer.Option(...),
    actor: str = typer.Option(...),
) -> None:
    """Create only the three new Dewey templates through TapDB's governed loader."""
    from dataclasses import asdict
    from daylily_tapdb import TAPDBConnection, generic_template
    from daylily_tapdb.cli.db_config import get_db_config
    from daylily_tapdb.templates.loader import find_tapdb_core_config_dir, seed_templates
    from daylily_tapdb.templates.repository import read_repository_pack, export_repository_pack, serialize_template, template_key
    from dewey_service.settings import get_settings
    from dewey_service.integrations.tapdb_runtime import load_runtime_config
    import json
    if any(not p.is_absolute() for p in (operator_config, repository_pack, receipt_pack)) or receipt_pack.exists():
        raise typer.BadParameter("Use absolute paths and a new export receipt pack")
    runtime = load_runtime_config(get_settings())
    cfg = get_db_config(config_path=str(operator_config))
    for key in ("database", "host", "port", "schema_name", "domain_code", "owner_repo_name"):
        if cfg[key] != runtime[key]:
            raise typer.BadParameter("Operator and running service targets differ: " + key)
    if not cfg.get("operator_configured") or not cfg.get("operator_user") or cfg["operator_user"] == cfg["user"]:
        raise typer.BadParameter("Explicit separately authenticated operator credentials are required")
    _, pack, _ = read_repository_pack(repository_pack)
    expected = {("access", "registry_policy", "generic", "1.0"),
        ("access", "api_client", "generic", "1.0"), ("operational", "storage_operation", "generic", "1.0")}
    if {template_key(t) for t in pack["templates"]} != expected or len(pack["templates"]) != 3:
        raise typer.BadParameter("This operation accepts only the three Dewey 10 templates")
    with TAPDBConnection(db_hostname=f"{cfg['host']}:{cfg['port']}", db_hostaddr=cfg.get("hostaddr"),
        db_user=cfg["operator_user"], db_pass=cfg.get("operator_password"),
        secret_arn=cfg.get("operator_secret_arn"), db_name=cfg["database"], engine_type=cfg["engine_type"],
        region=cfg["region"], iam_auth=cfg.get("operator_iam_auth", False), app_username=actor,
        domain_code=cfg["domain_code"], owner_repo_name=cfg["owner_repo_name"], schema_name=cfg["schema_name"],
        config_identity=str(operator_config), connection_role="operator", aws_profile=cfg.get("aws_profile"),
        sslrootcert=cfg.get("sslrootcert"), echo_sql=False) as connection:
        connection.engine.update_execution_options(isolation_level="REPEATABLE READ")
        with connection.session_scope(commit=True) as session:
            existing = {template_key(serialize_template(t)): serialize_template(t) for t in session.query(generic_template).filter(
                generic_template.domain_code == cfg["domain_code"], generic_template.issuer_app_code == cfg["owner_repo_name"]).all()}
            for item in pack["templates"]:
                if template_key(item) in existing and existing[template_key(item)] != item:
                    raise ValueError("An existing template conflicts with the release pack")
            result = seed_templates(session, pack["templates"], overwrite=False,
                core_config_dir=find_tapdb_core_config_dir(), domain_code=cfg["domain_code"],
                owner_repo_name=cfg["owner_repo_name"], domain_registry_path=Path(cfg["domain_registry_path"]),
                prefix_registry_path=Path(cfg["prefix_ownership_registry_path"]))
        with connection.session_scope(commit=False) as session:
            receipt = export_repository_pack(session, receipt_pack, domain_code=cfg["domain_code"],
                issuer_app_code=cfg["owner_repo_name"], prefix_registry_path=cfg["prefix_ownership_registry_path"], actor=actor)
    ccyo_out.print_text(json.dumps({"status": "created", "summary": asdict(result),
        "export_sha256": receipt["content_sha256"], "export_pack": str(receipt_pack)}))


def initialize_performance_settings(
    actor: str = typer.Option(..., help="Explicit operator audit identity"),
    listing_cache_ttl_seconds: int = typer.Option(..., min=0, max=300),
) -> None:
    """Explicitly initialize the required global listing TTL without overwriting existing settings."""
    import json
    import os
    from dewey_service.registry_access import POLICY_TEMPLATE, Principal, principal_context
    from dewey_service.tapdb_backend import TapDBBackend, normalize_instance_payload
    from dewey_service.settings import get_settings
    if not actor.strip() or not Path(os.environ.get("DEWEY_CONFIG", "")).is_absolute():
        raise typer.BadParameter("An operator audit identity and explicit absolute DEWEY_CONFIG are required")
    settings = get_settings()
    backend = TapDBBackend(app_username=actor)
    with principal_context(Principal(subject=actor, roles=("ADMIN",), service=True), maintenance=True):
        with backend.session_scope(commit=True) as session:
            backend.lock_external_key(session, operation="registry.defaults", key="service_defaults")
            row = backend.find_by_json_field(session, template_code=POLICY_TEMPLATE,
                field="policy_kind", value="service_defaults", for_update=True)
            created = False
            if row is None:
                row, created = backend.claim_global_instance(session, template_code=POLICY_TEMPLATE,
                    identity_key="dewey:registry-service-defaults", name="Dewey registry defaults",
                    json_addl={"policy_kind": "service_defaults",
                        "share_lifetime_days": settings.registry_default_share_lifetime_days,
                        "delivery_lifetime_seconds": settings.share_default_signed_ttl_seconds,
                        "listing_cache_ttl_seconds": listing_cache_ttl_seconds},
                    command_evidence={"actor": actor, "operation": "registry.defaults.initialize-performance"})
            data = normalize_instance_payload(row)
            if "listing_cache_ttl_seconds" not in data:
                backend.update_instance_json(session, row, {"listing_cache_ttl_seconds": listing_cache_ttl_seconds})
                status = "initialized"
            elif data["listing_cache_ttl_seconds"] != listing_cache_ttl_seconds:
                raise ValueError("Existing TTL differs; use the authenticated Admin settings to change it")
            else:
                status = "created" if created else "already_initialized"
            result = {"status": status, "settings_euid": row.euid, "listing_cache_ttl_seconds": listing_cache_ttl_seconds}
    ccyo_out.print_text(json.dumps(result))


def register(registry: CommandRegistry, spec: CliSpec) -> None:
    """Register verification and lifecycle guidance, with no bootstrap aliases."""
    _ = spec
    register_group_commands(
        registry,
        "db",
        "Verify existing Dewey data and review native TapDB lifecycle ownership",
        [("initialize-performance-settings", initialize_performance_settings, REQUIRED_MUTATING),
         ("verify-templates", verify_templates, REQUIRED), ("lifecycle", lifecycle, EXEMPT),
         ("registry-conversion", registry_conversion, REQUIRED_MUTATING),
         ("registry-templates", registry_templates, REQUIRED_MUTATING)],
    )
