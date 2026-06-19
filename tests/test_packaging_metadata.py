from __future__ import annotations

import json
import tomllib
from pathlib import Path

from dewey_service import tapdb_backend


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

    assert "cli-core-yo==2.1.1" in dependencies
    assert "daylily-auth-cognito==2.1.5" in dependencies
    assert "daylily-tapdb @ git+https://github.com/Daylily-Informatics/daylily-tapdb.git@9.0.6" in dependencies
    assert "psycopg2-binary>=2.9.9" in dependencies
    assert tapdb_dependency == _tapdb_dependency_spec()
    assert tapdb_dependency == "daylily-tapdb @ git+https://github.com/Daylily-Informatics/daylily-tapdb.git@9.0.6"


def test_pyproject_uses_a_single_dependency_set() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert "optional-dependencies" not in pyproject["project"]
    assert "pytest-cov>=4.1.0" in dependencies
    assert "pytest>=8.0.0" in dependencies
    assert "pytest-playwright>=0.4.4" in dependencies
    assert "playwright>=1.42.0" in dependencies
    assert "ruff>=0.9.0" in dependencies
    assert "bandit[toml]>=1.8.0" in dependencies
    assert "build>=1.2.0" in dependencies
    assert "djlint" in dependencies
    assert "ipython==8.18.1" in dependencies
    assert "pre-commit>=3.8.0" in dependencies


def test_pyproject_declares_python_multipart_for_browser_forms() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert any(dep.startswith("python-multipart") for dep in dependencies)


def test_pyproject_packages_dewey_config_template() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["dewey_service"] == [
        "etc/*.yaml",
        "etc/*.json",
        "templates/*.html",
        "static/*",
    ]


def test_dockerfile_copies_tapdb_template_config() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY config ./config" in dockerfile


def test_dockerfile_installs_git_before_git_pinned_dependencies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")

    first_uv_sync = dockerfile.index("uv sync")
    git_install = dockerfile.index("git")
    assert git_install < first_uv_sync


def test_dockerfile_uses_package_specific_scm_version() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")

    assert "ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}" not in dockerfile
    assert (
        "ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DEWEY_SERVICE=${SETUPTOOLS_SCM_PRETEND_VERSION}"
        in dockerfile
    )
    assert dockerfile.count("unset SETUPTOOLS_SCM_PRETEND_VERSION && uv sync") == 2


def test_dockerfile_installs_postgresql_client_for_tapdb_bootstrap() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")

    assert "postgresql-client" in dockerfile


def test_packaged_tapdb_registry_fixtures_match_owned_prefixes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    templates = json.loads(
        (repo_root / "config" / "tapdb_templates" / "dewey" / "templates.json").read_text(
            encoding="utf-8"
        )
    )["templates"]
    domain_registry = json.loads(
        (repo_root / "dewey_service" / "etc" / "domain_code_registry.json").read_text(
            encoding="utf-8"
        )
    )
    prefix_registry = json.loads(
        (repo_root / "dewey_service" / "etc" / "prefix_ownership_registry.json").read_text(
            encoding="utf-8"
        )
    )

    assert domain_registry["domains"] == {"Z": {"name": "dewey"}}
    assert set(prefix_registry["ownership"]) == {"Z"}
    assert set(prefix_registry["ownership"]["Z"]) == {
        template["instance_prefix"] for template in templates
    }
    assert {claim["issuer_app_code"] for claim in prefix_registry["ownership"]["Z"].values()} == {
        "dewey"
    }


def test_required_template_definitions_exist_in_source_pack() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    templates = json.loads(
        (repo_root / "config" / "tapdb_templates" / "dewey" / "templates.json").read_text(
            encoding="utf-8"
        )
    )["templates"]
    source_codes = {
        "/".join(
            [
                str(template["category"]).strip(),
                str(template["type"]).strip(),
                str(template["subtype"]).strip(),
                str(template["version"]).strip(),
                "",
            ]
        )
        for template in templates
    }

    assert set(tapdb_backend.TEMPLATE_DEFINITIONS) <= source_codes
    assert tapdb_backend.REGISTRATION_RECEIPT_TEMPLATE in source_codes
    assert tapdb_backend.OUTBOX_EVENT_TEMPLATE in source_codes


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
