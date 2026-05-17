"""Dewey CLI, built on cli-core-yo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from cli_core_yo.app import create_app, run
from cli_core_yo.spec import (
    BackendDetectSpec,
    BackendValidationSpec,
    CliSpec,
    ConfigSpec,
    EnvSpec,
    ExecutionBackendSpec,
    PluginSpec,
    PolicySpec,
    PrereqSpec,
    RuntimeSpec,
    XdgSpec,
)

from dewey_service.cli._registry_v2 import DEWEY_RUNTIME_TAG
from dewey_service.defaults import (
    build_default_config_template,
    default_cognito_logout_url,
    default_cognito_redirect_uri,
    resolve_aws_profile,
)
from dewey_service.settings import (
    Settings,
    _config_dir_name,
    _config_filename,
    _flatten_config,
    clear_settings_cache,
    get_settings,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVATE_SCRIPT = PROJECT_ROOT / "activate"
DEACTIVATE_SCRIPT = PROJECT_ROOT / "dewey_deactivate"

_YAML_ONLY_DEFAULTS = {
    "cognito_domain": "",
    "cognito_app_client_id": "",
    "cognito_app_client_secret": "",
    "cognito_redirect_uri": default_cognito_redirect_uri(),
    "cognito_logout_url": default_cognito_logout_url(),
    "cognito_user_pool_id": "",
    "cognito_region": "us-west-2",
    "deployment_name": "",
    "deployment_color": "",
    "deployment_is_production": False,
}


def _build_spec() -> CliSpec:
    return CliSpec(
        prog_name="dewey",
        app_display_name="Dewey",
        dist_name="dewey-service",
        root_help="Dewey — Development CLI for the canonical artifact registry service.",
        xdg=XdgSpec(app_dir_name=_config_dir_name()),
        policy=PolicySpec(),
        config=ConfigSpec(
            xdg_relative_path=_config_filename(),
            template_bytes=build_default_config_template(),
            validator=_validate_dewey_config,
        ),
        env=EnvSpec(
            active_env_var="DEWEY_ACTIVE",
            project_root_env_var="DEWEY_PROJECT_ROOT",
            activate_script_name=f"{ACTIVATE_SCRIPT} <deploy-name>",
            deactivate_script_name=str(DEACTIVATE_SCRIPT),
            preferred_backend="dewey-conda",
        ),
        runtime=RuntimeSpec(
            supported_backends=[
                ExecutionBackendSpec(
                    name="dewey-conda",
                    kind="conda",
                    entry_guidance="source ./activate <deploy-name>",
                    detect=BackendDetectSpec(env_vars=("CONDA_PREFIX",)),
                    validation=BackendValidationSpec(env_vars=("CONDA_PREFIX",)),
                )
            ],
            default_backend="dewey-conda",
            guard_mode="enforced",
            prereqs=[
                PrereqSpec(
                    key="dewey-conda-active-env",
                    kind="env_var",
                    value="CONDA_DEFAULT_ENV",
                    help="Activate Dewey with source ./activate <deploy-name>.",
                    applies_to_backends={"dewey-conda"},
                    tags={DEWEY_RUNTIME_TAG},
                    success_message="Deployment-scoped conda environment is active.",
                    failure_message=(
                        "Dewey CLI requires an active deployment-scoped conda environment. "
                        "Run `source ./activate <deploy-name>`."
                    ),
                ),
                PrereqSpec(
                    key="dewey-conda-env-name",
                    kind="command_probe",
                    value=(
                        sys.executable,
                        "-c",
                        "import os, sys; env = os.environ.get('CONDA_DEFAULT_ENV', '').strip(); "
                        "sys.exit(0 if env and '-' in env else 1)",
                    ),
                    help="Use a deployment-scoped conda environment such as DEWEY-local2.",
                    applies_to_backends={"dewey-conda"},
                    tags={DEWEY_RUNTIME_TAG},
                    success_message="Deployment-scoped conda environment name is valid.",
                    failure_message=(
                        "Dewey CLI requires a deployment-scoped conda environment name with '-'. "
                        "Run `source ./activate <deploy-name>`."
                    ),
                ),
                PrereqSpec(
                    key="dewey-daylily-tapdb",
                    kind="python_import",
                    value="daylily_tapdb",
                    help="Install daylily-tapdb into the active Dewey environment.",
                    applies_to_backends={"dewey-conda"},
                    tags={DEWEY_RUNTIME_TAG},
                    success_message="Dependency available: daylily-tapdb",
                    failure_message=(
                        "Missing dependency: daylily-tapdb. "
                        "Re-run `source ./activate <deploy-name>`."
                    ),
                ),
                PrereqSpec(
                    key="dewey-daylily-auth-cognito",
                    kind="python_import",
                    value="daylily_auth_cognito",
                    help="Install daylily-auth-cognito into the active Dewey environment.",
                    applies_to_backends={"dewey-conda"},
                    tags={DEWEY_RUNTIME_TAG},
                    success_message="Dependency available: daylily-auth-cognito",
                    failure_message=(
                        "Missing dependency: daylily-auth-cognito. "
                        "Re-run `source ./activate <deploy-name>`."
                    ),
                ),
            ],
        ),
        plugins=PluginSpec(
            explicit=[
                "dewey_service.cli.server.register",
                "dewey_service.cli.db.register",
                "dewey_service.cli.test.register",
                "dewey_service.cli.quality.register",
                "dewey_service.cli.tapdb.register",
                "dewey_service.cli.cognito.register",
                "dewey_service.cli.config_extra.register",
            ]
        ),
        info_hooks=[_dewey_info_hook],
    )


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
    aws_profile = resolve_aws_profile()

    try:
        clear_settings_cache()
        settings = get_settings()
    except Exception as exc:
        rows.append(("Config Status", f"invalid ({exc})"))
        settings = None
    else:
        aws_profile = resolve_aws_profile(config_profile=settings.aws_profile)
        rows.extend(
            [
                ("Database Backend", settings.database_backend),
                ("Database Target", settings.database_target),
                ("TapDB Namespace", settings.tapdb_database_name),
                ("TapDB Owner Repo", settings.tapdb_owner_repo_name),
                ("TapDB Domain", settings.tapdb_domain_code),
                ("TapDB Target", settings.database_target),
                ("Host", settings.host),
                ("Port", str(settings.port)),
            ]
        )

    rows.extend(
        [
            ("AWS Profile", aws_profile),
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


spec = _build_spec()

app = create_app(spec)
cli = app


def main() -> None:
    """Main CLI entry point."""
    raise SystemExit(run(spec))
