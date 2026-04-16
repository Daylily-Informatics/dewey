"""Seed the Dewey TapDB JSON template pack through TapDB's loader."""

from __future__ import annotations

import json
from pathlib import Path

from daylily_tapdb.templates.loader import (
    find_tapdb_core_config_dir,
    resolve_seed_config_dirs,
    seed_templates,
    validate_template_configs,
)
from daylily_tapdb.governance import assert_registered_domain, normalize_owner_repo_name

from dewey_service.tapdb_backend import TapDBBackend
from dewey_service.settings import get_settings


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
            raise ValueError(
                f"Template {template.get('name')!r} is missing an instance_prefix"
            )
        if prefix in _TAPDB_CORE_PREFIXES:
            continue
        if prefix not in seen:
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def _load_or_init_prefix_registry(path: Path) -> dict[str, object]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError(f"Prefix registry must contain a JSON object: {path}")
    payload.setdefault("version", _PREFIX_OWNERSHIP_REGISTRY_VERSION)
    ownership = payload.setdefault("ownership", {})
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
    assert isinstance(ownership, dict)
    domain_claims = ownership.setdefault(domain_code, {})
    if not isinstance(domain_claims, dict):
        raise ValueError(
            f"Prefix registry claims for domain {domain_code!r} must be an object"
        )

    changed = False
    for prefix in prefixes:
        claim = domain_claims.get(prefix)
        if claim is None:
            domain_claims[prefix] = {"issuer_app_code": normalized_owner_repo_name}
            changed = True
            continue
        if not isinstance(claim, dict):
            raise ValueError(
                f"Prefix {prefix!r} in domain {domain_code!r} must be an object"
            )
        registered_owner = str(
            claim.get("issuer_app_code")
            or claim.get("owner_repo_name")
            or claim.get("repo_name")
            or ""
        ).strip()
        if not registered_owner:
            raise ValueError(
                f"Prefix {prefix!r} in domain {domain_code!r} is missing an owner"
            )
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


def main() -> None:
    backend = TapDBBackend(app_username="dewey")
    settings = get_settings()
    config_root = Path(__file__).resolve().parents[1] / "config" / "tapdb_templates"
    config_dirs = resolve_seed_config_dirs(config_root)
    templates, issues = validate_template_configs(config_dirs, strict=True)
    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        joined = "; ".join(issue.message for issue in errors)
        raise RuntimeError(f"Dewey template pack validation failed: {joined}")
    core_config_dir = find_tapdb_core_config_dir()
    domain_registry_path = Path(settings.tapdb_domain_registry_path)
    prefix_registry_path = Path(settings.tapdb_prefix_ownership_registry_path)
    _claim_client_template_prefix_ownership(
        templates,
        domain_code=settings.tapdb_domain_code,
        owner_repo_name=settings.tapdb_owner_repo_name,
        domain_registry_path=domain_registry_path,
        prefix_registry_path=prefix_registry_path,
        core_config_dir=core_config_dir,
    )
    with backend.session_scope(commit=True) as session:
        seed_templates(
            session,
            templates,
            overwrite=True,
            core_config_dir=core_config_dir,
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            domain_registry_path=domain_registry_path,
            prefix_registry_path=prefix_registry_path,
        )


if __name__ == "__main__":
    main()
