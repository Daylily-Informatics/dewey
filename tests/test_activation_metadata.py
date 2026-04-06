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
    assert "_dewey_reconcile_packaged_dependencies" in activate_script
    assert "dewey-service" in activate_script
    assert "is not installed editable from" in activate_script
    assert "_dewey_module_is_from_repo" not in activate_script
    assert 'pip install --no-deps -e "${DEWEY_ROOT}" -q' in activate_script
    assert 'export MERIDIAN_DOMAIN_CODE="${MERIDIAN_DOMAIN_CODE:-D}"' in activate_script
    assert 'export TAPDB_APP_CODE="${TAPDB_APP_CODE:-D}"' in activate_script
    assert "MERIDIAN_DOMAIN_CODE=D" in template_text
    assert "TAPDB_APP_CODE=D" in template_text
    assert "MERIDIAN_DOMAIN_CODE=D" in tapdb_template_text
    assert "TAPDB_APP_CODE=D" in tapdb_template_text
    assert "unset MERIDIAN_DOMAIN_CODE" in deactivate_script
    assert "unset TAPDB_APP_CODE" in deactivate_script
