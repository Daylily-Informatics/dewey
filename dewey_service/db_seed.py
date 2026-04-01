"""Seed the Dewey TapDB JSON template pack through TapDB's loader."""

from __future__ import annotations

from pathlib import Path

from daylily_tapdb import (
    find_tapdb_core_config_dir,
    resolve_seed_config_dirs,
    seed_templates,
    validate_template_configs,
)
from daylily_tapdb.euid import resolve_client_scoped_core_prefix

from dewey_service.tapdb_backend import TapDBBackend


def main() -> None:
    backend = TapDBBackend(app_username="dewey")
    core_prefix = resolve_client_scoped_core_prefix("D")
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
            core_instance_prefix=core_prefix,
        )


if __name__ == "__main__":
    main()
