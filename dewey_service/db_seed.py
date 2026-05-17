"""Seed the Dewey TapDB JSON template pack through TapDB's loader."""

from __future__ import annotations

import json
from pathlib import Path

from daylily_tapdb.euid import AUDIT_LOG_PREFIX, GENERIC_INSTANCE_LINEAGE_PREFIX
from daylily_tapdb.governance import assert_registered_domain, normalize_owner_repo_name
from daylily_tapdb.templates.loader import (
    find_tapdb_core_config_dir,
    resolve_seed_config_dirs,
    seed_templates,
    validate_template_configs,
)
from sqlalchemy import text

from dewey_service.settings import get_settings
from dewey_service.tapdb_backend import TapDBBackend

_PREFIX_OWNERSHIP_REGISTRY_VERSION = "0.4.0"
_TAPDB_CORE_PREFIXES = {"SYS", "MSG"}


def _is_source_under_dir(source_file: str | None, directory: Path) -> bool:
    if not source_file:
        return False
    try:
        Path(source_file).resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _client_template_prefixes(
    templates: list[dict[str, object]], *, core_config_dir: Path
) -> list[str]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for template in templates:
        source_file = str(template.get("_source_file") or "") or None
        if _is_source_under_dir(source_file, core_config_dir):
            continue
        prefix = str(template.get("instance_prefix") or "").strip().upper()
        if not prefix:
            raise ValueError(f"Template {template.get('name')!r} is missing an instance_prefix")
        if prefix in _TAPDB_CORE_PREFIXES:
            continue
        if prefix not in seen:
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def _filter_client_templates(templates: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        template
        for template in templates
        if str(template.get("instance_prefix") or "").strip().upper() not in _TAPDB_CORE_PREFIXES
    ]


def _load_or_init_prefix_registry(path: Path) -> dict[str, object]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {"version": _PREFIX_OWNERSHIP_REGISTRY_VERSION, "ownership": {}}
    if not isinstance(payload, dict):
        raise ValueError(f"Prefix registry must contain a JSON object: {path}")
    if payload.get("version") != _PREFIX_OWNERSHIP_REGISTRY_VERSION:
        raise ValueError(
            f"Prefix registry version must be {_PREFIX_OWNERSHIP_REGISTRY_VERSION!r}: {path}"
        )
    ownership = payload.get("ownership")
    if not isinstance(ownership, dict):
        raise ValueError(f"Prefix registry must define an object 'ownership': {path}")
    return payload


def _claim_client_template_prefix_ownership(
    templates: list[dict[str, object]],
    *,
    domain_code: str,
    owner_repo_name: str,
    domain_registry_path: Path,
    prefix_registry_path: Path,
    core_config_dir: Path,
) -> list[str]:
    normalized_owner_repo_name = normalize_owner_repo_name(owner_repo_name)
    assert_registered_domain(domain_code, path=domain_registry_path)

    prefixes = _client_template_prefixes(
        templates,
        core_config_dir=core_config_dir,
    )
    if not prefixes:
        return []

    payload = _load_or_init_prefix_registry(prefix_registry_path)
    ownership = payload["ownership"]
    if not isinstance(ownership, dict):
        raise ValueError("Prefix registry ownership table must be an object")
    domain_claims = ownership.get(domain_code)
    if domain_claims is None:
        domain_claims = {}
        ownership[domain_code] = domain_claims
    if not isinstance(domain_claims, dict):
        raise ValueError(f"Prefix registry claims for domain {domain_code!r} must be an object")

    changed = False
    for prefix in prefixes:
        claim = domain_claims.get(prefix)
        if claim is None:
            domain_claims[prefix] = {"issuer_app_code": normalized_owner_repo_name}
            changed = True
            continue
        if not isinstance(claim, dict):
            raise ValueError(f"Prefix {prefix!r} in domain {domain_code!r} must be an object")
        registered_owner = str(
            claim.get("issuer_app_code")
            or claim.get("owner_repo_name")
            or claim.get("repo_name")
            or ""
        ).strip()
        if not registered_owner:
            raise ValueError(f"Prefix {prefix!r} in domain {domain_code!r} is missing an owner")
        if registered_owner != normalized_owner_repo_name:
            raise ValueError(
                f"Prefix {prefix!r} in domain {domain_code!r} is owned by "
                f"{registered_owner!r}, not {normalized_owner_repo_name!r}"
            )

    if changed:
        prefix_registry_path.parent.mkdir(parents=True, exist_ok=True)
        prefix_registry_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return prefixes


def _ensure_identity_prefix_config(
    session,
    *,
    entity: str,
    domain_code: str,
    owner_repo_name: str,
    prefix: str,
) -> None:
    normalized_entity = str(entity or "").strip()
    normalized_domain = str(domain_code or "").strip().upper()
    normalized_owner = normalize_owner_repo_name(owner_repo_name)
    normalized_prefix = str(prefix or "").strip().upper()
    if not normalized_entity:
        raise ValueError("Dewey TapDB identity entity is required")
    if not normalized_prefix:
        raise ValueError(f"Dewey TapDB identity prefix is required for {normalized_entity!r}")

    params = {
        "entity": normalized_entity,
        "domain_code": normalized_domain,
        "owner_repo_name": normalized_owner,
        "prefix": normalized_prefix,
    }
    existing = session.execute(
        text(
            """
            SELECT prefix
            FROM tapdb_identity_prefix_config
            WHERE entity = :entity
              AND domain_code = :domain_code
              AND issuer_app_code = :owner_repo_name
            """
        ),
        params,
    ).scalar_one_or_none()
    if existing is not None:
        existing_prefix = str(existing or "").strip().upper()
        if existing_prefix != normalized_prefix:
            raise RuntimeError(
                f"Dewey identity prefix config for entity {normalized_entity!r} in domain "
                f"{normalized_domain!r} is already seeded with prefix {existing_prefix!r}, "
                f"not {normalized_prefix!r}"
            )
        return

    session.execute(
        text(
            """
            INSERT INTO tapdb_identity_prefix_config(
              entity, domain_code, issuer_app_code, prefix
            )
            VALUES (:entity, :domain_code, :owner_repo_name, :prefix)
            """
        ),
        params,
    )


def main() -> None:
    backend = TapDBBackend(app_username="dewey")
    settings = get_settings()
    config_root = Path(__file__).resolve().parents[1] / "config" / "tapdb_templates"
    core_config_dir = find_tapdb_core_config_dir()
    core_templates, core_issues = validate_template_configs([core_config_dir], strict=True)
    raw_client_templates, client_issues = validate_template_configs(
        resolve_seed_config_dirs(config_root),
        strict=True,
    )
    client_templates = _filter_client_templates(raw_client_templates)
    errors = [issue for issue in [*core_issues, *client_issues] if issue.level == "error"]
    if errors:
        joined = "; ".join(issue.message for issue in errors)
        raise RuntimeError(f"Dewey template pack validation failed: {joined}")

    domain_registry_path = Path(settings.tapdb_domain_registry_path)
    prefix_registry_path = Path(settings.tapdb_prefix_ownership_registry_path)
    _claim_client_template_prefix_ownership(
        client_templates,
        domain_code=settings.tapdb_domain_code,
        owner_repo_name=settings.tapdb_owner_repo_name,
        domain_registry_path=domain_registry_path,
        prefix_registry_path=prefix_registry_path,
        core_config_dir=core_config_dir,
    )
    with backend.session_scope(commit=True) as session:
        seed_templates(
            session,
            core_templates,
            overwrite=True,
            core_config_dir=core_config_dir,
            domain_code=settings.tapdb_domain_code,
            owner_repo_name="daylily-tapdb",
            domain_registry_path=domain_registry_path,
            prefix_registry_path=prefix_registry_path,
        )
        _ensure_identity_prefix_config(
            session,
            entity="generic_template",
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            prefix="DGX",
        )
        _ensure_identity_prefix_config(
            session,
            entity="generic_instance_lineage",
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            prefix=GENERIC_INSTANCE_LINEAGE_PREFIX,
        )
        _ensure_identity_prefix_config(
            session,
            entity="audit_log",
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            prefix=AUDIT_LOG_PREFIX,
        )
        seed_templates(
            session,
            client_templates,
            overwrite=True,
            core_config_dir=core_config_dir,
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            domain_registry_path=domain_registry_path,
            prefix_registry_path=prefix_registry_path,
        )


if __name__ == "__main__":
    main()
