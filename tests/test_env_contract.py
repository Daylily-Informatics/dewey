from __future__ import annotations

from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_metapub_runtime_dependency() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = pyproject["project"]["dependencies"]

    assert any(dep.startswith("metapub") for dep in dependencies)


def test_root_environment_contract_uses_environment_yaml() -> None:
    assert (PROJECT_ROOT / "environment.yaml").is_file()
    assert not (PROJECT_ROOT / "environment").with_suffix(".yml").exists()


def test_environment_yaml_does_not_install_local_repo_directly() -> None:
    environment = (PROJECT_ROOT / "environment.yaml").read_text(encoding="utf-8")

    assert "-e ." not in environment


def test_environment_yaml_only_contains_bootstrap_and_system_packages() -> None:
    environment = (PROJECT_ROOT / "environment.yaml").read_text(encoding="utf-8")
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert "pip:" not in environment
    assert "ipython" not in environment
    assert "djlint" not in environment
    assert "psycopg2" not in environment
    assert "python=3.12.0" in environment
    assert "pip=23.3.1" in environment
    assert "postgresql=16.1" in environment
    assert "parallel=20230922" in environment
    assert "jq" in environment
    assert "fd-find" in environment
    assert "rclone" in environment
    assert "setuptools<81" in environment
    assert "optional-dependencies" not in pyproject["project"]
    assert "pytest-cov>=4.1.0" in dependencies
    assert "ruff>=0.9.0" in dependencies


def test_agents_ban_secondary_install_sets() -> None:
    agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "secondary install set" in agents
    assert "`.[dev]`" in agents
    assert "`[project.optional-dependencies]`" in agents


def test_user_facing_files_do_not_reference_dev_extras_or_optional_groups() -> None:
    for relative_path in ("README.md", "docs/how-tos.md", "activate"):
        text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert ".[dev]" not in text, relative_path
        assert "optional-dependencies.dev" not in text, relative_path
