from __future__ import annotations

from pathlib import Path


def test_activate_uses_bare_environment_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    activate_script = (repo_root / "activate").read_text(encoding="utf-8")
    deactivate_script = (repo_root / "dewey_deactivate").read_text(encoding="utf-8")

    assert ' "${CONDA_PREFIX}/bin/python" -m pip install -e "$DEWEY_ROOT" -q' in activate_script
    assert "_dewey_ensure_published_dependency" not in activate_script
    assert "_dewey_prepare_tapdb_config_path" not in activate_script
    assert 'export PATH="${CONDA_PREFIX}/bin:$PATH"' not in activate_script
    assert "export TAPDB_CONFIG_PATH=" not in activate_script
    assert "export TAPDB_OWNER_REPO=" not in activate_script
    assert "export MERIDIAN_DOMAIN_CODE=" not in activate_script
    assert "export AWS_REGION=" not in activate_script
    assert "export DATABASE_BACKEND=" not in activate_script
    assert "export DATABASE_TARGET=" not in activate_script
    assert 'export DEWEY_DEPLOYMENT_CODE="' in activate_script
    assert 'export DEPLOYMENT_CODE="' in activate_script
    assert 'export LSMC_DEPLOYMENT_CODE="' in activate_script
    assert "export DEWEY_ACTIVE=1" in activate_script
    assert 'export DEWEY_PROJECT_ROOT="$DEWEY_ROOT"' in activate_script
    assert "unset MERIDIAN_DOMAIN_CODE" in deactivate_script
    assert "unset TAPDB_OWNER_REPO" in deactivate_script
    assert "unset TAPDB_DOMAIN_CODE" in deactivate_script
    assert "unset TAPDB_DOMAIN_REGISTRY_PATH" in deactivate_script
    assert "unset TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH" in deactivate_script
