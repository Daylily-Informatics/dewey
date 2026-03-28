"""Dewey CLI, built on cli-core-yo."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from cli_core_yo.app import create_app, run
from cli_core_yo.spec import CliSpec, ConfigSpec, EnvSpec, PluginSpec, XdgSpec

from dewey_service.settings import Settings, _flatten_config, clear_settings_cache, get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVATE_SCRIPT = PROJECT_ROOT / "activate"
DEACTIVATE_SCRIPT = PROJECT_ROOT / "dewey_deactivate"

_YAML_ONLY_DEFAULTS = {
    "cognito_domain": "",
    "cognito_app_client_id": "",
    "cognito_app_client_secret": "",
    "cognito_redirect_uri": "https://localhost:8914/auth/callback",
    "cognito_logout_url": "https://localhost:8914/login",
    "cognito_user_pool_id": "",
    "cognito_region": "us-west-2",
    "deployment_name": "",
    "deployment_color": "#0f766e",
    "deployment_is_production": False,
}


def _validate_dewey_config(content: str) -> list[str]:
    """Validate Dewey configuration YAML."""
    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(config, dict):
        return ["Root YAML object must be a mapping"]

    errors: list[str] = []

    for section in ("application", "auth", "database"):
        payload = config.get(section)
        if not isinstance(payload, dict) or not payload:
            errors.append(f"Missing or empty required section: '{section}'")

    auth = config.get("auth") or {}
    if isinstance(auth, dict):
        cognito = auth.get("cognito")
        if not isinstance(cognito, dict) or not cognito:
            errors.append("auth.cognito is required and must be a mapping")

    database = config.get("database") or {}
    if isinstance(database, dict):
        backend = str(database.get("backend", "tapdb")).strip().lower()
        if backend != "tapdb":
            errors.append("database.backend must be 'tapdb'")
        target = str(database.get("target", "local")).strip().lower()
        if target not in {"local", "aurora"}:
            errors.append("database.target must be one of: local, aurora")

    if errors:
        return errors

    seed = _flatten_config(config)
    merged = dict(seed)
    for key, default in _YAML_ONLY_DEFAULTS.items():
        merged[key] = seed.get(key, default)

    try:
        Settings(**merged)
    except Exception as exc:
        errors.append(f"settings validation failed: {exc}")

    return errors


def _dewey_info_hook() -> list[tuple[str, str]]:
    """Return Dewey-specific rows for the built-in info command."""
    rows: list[tuple[str, str]] = [("Project Root", str(PROJECT_ROOT))]

    try:
        clear_settings_cache()
        settings = get_settings()
    except Exception as exc:
        rows.append(("Config Status", f"invalid ({exc})"))
        settings = None
    else:
        rows.extend(
            [
                ("Database Backend", settings.database_backend),
                ("Database Target", settings.database_target),
                ("TapDB Client", settings.tapdb_client_id),
                ("TapDB Namespace", settings.tapdb_database_name),
                ("TapDB Env", settings.tapdb_env),
                ("Host", settings.host),
                ("Port", str(settings.port)),
            ]
        )

    rows.extend(
        [
            ("AWS Profile", os.environ.get("AWS_PROFILE", "")),
            ("AWS Region", os.environ.get("AWS_REGION", "")),
        ]
    )

    try:
        from cli_core_yo.runtime import get_context

        pid_file = get_context().xdg_paths.state / "server.pid"
        if pid_file.exists():
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            rows.append(("Dev Server", f"Running (PID {pid})"))
        else:
            rows.append(("Dev Server", "Stopped"))
    except Exception:
        rows.append(("Dev Server", "Unknown"))

    return rows


spec = CliSpec(
    prog_name="dewey",
    app_display_name="Dewey",
    dist_name="dewey-service",
    root_help="Dewey — Development CLI for the canonical artifact registry service.",
    xdg=XdgSpec(app_dir_name="dewey"),
    config=ConfigSpec(
        primary_filename="config.yaml",
        template_resource=("dewey_service", "etc/dewey-config-template.yaml"),
        validator=_validate_dewey_config,
    ),
    env=EnvSpec(
        active_env_var="DEWEY_ACTIVE",
        project_root_env_var="DEWEY_PROJECT_ROOT",
        activate_script_name=str(ACTIVATE_SCRIPT),
        deactivate_script_name=str(DEACTIVATE_SCRIPT),
    ),
    plugins=PluginSpec(
        explicit=[
            "dewey_service.cli.server.register",
            "dewey_service.cli.db.register",
            "dewey_service.cli.test.register",
            "dewey_service.cli.quality.register",
            "dewey_service.cli.config_extra.register",
        ]
    ),
    info_hooks=[_dewey_info_hook],
)

app = create_app(spec)
cli = app


def main() -> None:
    """Main CLI entry point."""
    raise SystemExit(run(spec))
