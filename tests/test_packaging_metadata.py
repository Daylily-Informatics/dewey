from __future__ import annotations

import tomllib
from pathlib import Path


def test_pyproject_declares_cli_core_yo_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert any(dep.startswith("cli-core-yo") for dep in dependencies)


def test_pyproject_packages_dewey_config_template() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["dewey_service"] == ["etc/*.yaml"]
