from __future__ import annotations

from pathlib import Path


def test_activate_uses_editable_metadata_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    activate_script = (repo_root / "activate").read_text(encoding="utf-8")
    deactivate_script = (repo_root / "dewey_deactivate").read_text(encoding="utf-8")
    template_text = (repo_root / "dewey_service" / "etc" / "dewey-config-template.yaml").read_text(
        encoding="utf-8"
    )
    tapdb_template_text = (repo_root / "config" / "tapdb-config-dewey.yaml").read_text(
        encoding="utf-8"
    )

    assert "Editable project location" in activate_script
    assert "_dewey_reconcile_packaged_dependencies" not in activate_script
    assert 'pip install -e "${DEWEY_ROOT}[dev]" -q' in activate_script
    assert "_dewey_validate_main_repo_install" in activate_script
    assert 'export AWS_PROFILE="${AWS_PROFILE:-lsmc}"' not in activate_script
    assert 'AWS_PROFILE=${AWS_PROFILE:-<unset>}' in activate_script
    assert "_DEWEY_DAYLILY_TAPDB_ROOT" not in activate_script
    assert "Installing local daylily-tapdb checkout" not in activate_script
    assert "TAPDB_APP_CODE" not in activate_script
    assert 'config/tapdb-config-${client_id}.yaml' in activate_script
    assert 'export MERIDIAN_DOMAIN_CODE="D"' in activate_script
    assert 'export TAPDB_OWNER_REPO="dewey"' in activate_script
    assert "MERIDIAN_DOMAIN_CODE=D" in template_text
    assert "TAPDB_OWNER_REPO=dewey" in template_text
    assert "owner_repo_name: dewey" in template_text
    assert "domain_code: D" in template_text
    assert "domain_registry_path: ~/.config/tapdb/domain_code_registry.json" in template_text
    assert "prefix_ownership_registry_path: ~/.config/tapdb/prefix_ownership_registry.json" in template_text
    assert "MERIDIAN_DOMAIN_CODE=D" in tapdb_template_text
    assert "TAPDB_OWNER_REPO=dewey" in tapdb_template_text
    assert "owner_repo_name: dewey" in tapdb_template_text
    assert "domain_code: D" in tapdb_template_text
    assert "euid_client_code" not in tapdb_template_text
    assert "unset MERIDIAN_DOMAIN_CODE" in deactivate_script
    assert "unset TAPDB_OWNER_REPO" in deactivate_script
    assert "unset TAPDB_DOMAIN_CODE" in deactivate_script
    assert "unset TAPDB_DOMAIN_REGISTRY_PATH" in deactivate_script
    assert "unset TAPDB_PREFIX_OWNERSHIP_REGISTRY_PATH" in deactivate_script
