from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_metapub_dependency_is_available() -> None:
    from dewey_service import literature

    assert literature.PubMedFetcher is not None
    assert literature.FindIt is not None


def test_root_environment_contract_uses_environment_yaml() -> None:
    assert (PROJECT_ROOT / "environment.yaml").is_file()
    assert not (PROJECT_ROOT / "dewey_env.yaml").exists()


def test_environment_yaml_does_not_install_local_repo_directly() -> None:
    environment = (PROJECT_ROOT / "environment.yaml").read_text(encoding="utf-8")

    assert "-e ." not in environment
