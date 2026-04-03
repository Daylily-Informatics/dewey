from __future__ import annotations

from pathlib import Path


def test_activate_uses_editable_metadata_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    activate_script = (repo_root / "activate").read_text(encoding="utf-8")

    assert "Editable project location" in activate_script
    assert "dewey-service" in activate_script
    assert "is not installed editable from" in activate_script
    assert "_dewey_module_is_from_repo" not in activate_script
    assert 'pip install --no-deps -e "${DEWEY_ROOT}" -q' in activate_script
