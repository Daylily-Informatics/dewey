from __future__ import annotations

import tomllib
from pathlib import Path


def _tapdb_dependency_spec() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    for dependency in dependencies:
        if dependency.startswith("daylily-tapdb"):
            return dependency
    raise AssertionError("daylily-tapdb dependency missing from pyproject.toml")


def test_pyproject_declares_shared_library_versions() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = pyproject["project"]["dependencies"]
    tapdb_dependency = next(dep for dep in dependencies if dep.startswith("daylily-tapdb"))

    assert "cli-core-yo==2.0.0" in dependencies
    assert "daylily-auth-cognito==2.0.3" in dependencies
    assert tapdb_dependency == _tapdb_dependency_spec()
    assert tapdb_dependency.startswith("daylily-tapdb==")


def test_pyproject_declares_pytest_cov_in_dev_dependencies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]

    assert any(dep.startswith("pytest-cov") for dep in dev_dependencies)


def test_pyproject_declares_python_multipart_for_browser_forms() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert any(dep.startswith("python-multipart") for dep in dependencies)


def test_pyproject_packages_dewey_config_template() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["dewey_service"] == ["etc/*.yaml", "templates/*.html", "static/*"]


def test_pyproject_uses_dynamic_version_from_git_tags() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert "version" not in project
    assert project["dynamic"] == ["version"]


def test_build_system_declares_setuptools_scm() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    requires = pyproject["build-system"]["requires"]

    assert any(requirement.startswith("setuptools_scm") for requirement in requires)


def test_setuptools_scm_tracks_numeric_release_tags() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    scm_config = pyproject["tool"]["setuptools_scm"]

    assert scm_config["version_scheme"] == "guess-next-dev"
    assert scm_config["local_scheme"] == "no-local-version"
    assert scm_config["tag_regex"] == r"^(?P<version>\d+\.\d+\.\d+)$"
    assert scm_config["scm"]["git"]["describe_command"] == (
        "git describe --dirty --tags --long --match '[0-9]*'"
    )


def test_pyproject_declares_coverage_assessment_defaults() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    coverage_run = pyproject["tool"]["coverage"]["run"]
    coverage_report = pyproject["tool"]["coverage"]["report"]

    assert coverage_run["source"] == ["dewey_service"]
    assert coverage_run["branch"] is True
    assert "*/tests/*" in coverage_run["omit"]
    assert coverage_report["show_missing"] is True
    assert "if TYPE_CHECKING:" in coverage_report["exclude_lines"]
