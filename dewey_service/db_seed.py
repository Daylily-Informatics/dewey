"""Seed the Dewey TapDB JSON template pack through TapDB's loader."""

from __future__ import annotations

from pathlib import Path

from daylily_tapdb import (
    find_tapdb_core_config_dir,
    resolve_seed_config_dirs,
    seed_templates,
    validate_template_configs,
)

from dewey_service.tapdb_backend import TapDBBackend
from dewey_service.settings import get_settings


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
    with backend.session_scope(commit=True) as session:
        seed_templates(
            session,
            templates,
            overwrite=True,
            core_config_dir=find_tapdb_core_config_dir(),
            domain_code=settings.tapdb_domain_code,
            owner_repo_name=settings.tapdb_owner_repo_name,
            domain_registry_path=Path(settings.tapdb_domain_registry_path),
            prefix_registry_path=Path(settings.tapdb_prefix_ownership_registry_path),
        )


if __name__ == "__main__":
    main()
