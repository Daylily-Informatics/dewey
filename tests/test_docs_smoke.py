from __future__ import annotations

import ast
import re
from pathlib import Path

from cli_core_yo import output
from cli_core_yo.app import run as run_cli

import dewey_service.cli as cli_module

DOC_FILES = [
    Path("README.md"),
    Path("docs/README.md"),
    Path("docs/architecture.md"),
    Path("docs/how-tos.md"),
    Path("docs/apis.md"),
    Path("docs/gui.md"),
    Path("docs/becoming_a_discoverable_service.md"),
]


def _invoke(argv: list[str]) -> tuple[int, str]:
    output._reset_console()
    import sys
    from io import StringIO

    captured = StringIO()
    stdout = sys.stdout
    stderr = sys.stderr
    try:
        sys.stdout = captured
        sys.stderr = captured
        exit_code = run_cli(cli_module._build_spec(), argv)
    finally:
        sys.stdout = stdout
        sys.stderr = stderr
    return exit_code, captured.getvalue()


def _iter_routes(module_path: str) -> set[tuple[str, str]]:
    tree = ast.parse(Path(module_path).read_text(encoding="utf-8"))
    routes: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            if not isinstance(decorator.args[0].value, str):
                continue
            routes.add((method, decorator.args[0].value))
    return routes


def test_docs_files_exist() -> None:
    for path in DOC_FILES:
        assert path.exists(), f"Missing documentation file: {path}"


def test_readme_and_how_tos_reference_current_cli_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    how_tos = Path("docs/how-tos.md").read_text(encoding="utf-8")

    expected_commands = [
        "source ./activate <deploy-name>",
        "dewey --json version",
        "dewey runtime check",
        "dewey config init",
        "dewey db build --target local",
        "dewey server start --port 8914",
        "pytest --collect-only -q",
        "pytest --cov=dewey_service --cov-report=term-missing:skip-covered",
    ]

    for command in expected_commands:
        assert command in readme or command in how_tos


def test_shipped_docs_and_templates_do_not_teach_guessed_tapdb_paths() -> None:
    files = {
        Path("config/dewey-config.example.yaml"): "/absolute/path/to/tapdb-config.yaml",
        Path("config/tapdb-config-dewey.yaml"): "/absolute/path/to/domain_code_registry.json",
        Path("dewey_service/etc/dewey-config-template.yaml"): "/absolute/path/to/tapdb-config.yaml",
        Path("docs/how-tos.md"): "/absolute/path/to/tapdb-config.yaml",
    }

    for path, expected_snippet in files.items():
        content = path.read_text(encoding="utf-8")
        assert "~/.config/tapdb" not in content
        assert expected_snippet in content


def test_documented_cli_groups_match_live_help_surface() -> None:
    root_code, root_help = _invoke(["--help"])
    server_code, server_help = _invoke(["server", "--help"])
    db_code, db_help = _invoke(["db", "--help"])
    test_code, test_help = _invoke(["test", "--help"])
    quality_code, quality_help = _invoke(["quality", "--help"])

    assert root_code == 0
    assert server_code == 0
    assert db_code == 0
    assert test_code == 0
    assert quality_code == 0

    for snippet in (
        "config",
        "env",
        "runtime",
        "server",
        "db",
        "tapdb",
        "cognito",
        "test",
        "quality",
    ):
        assert snippet in root_help
    for snippet in ("start", "stop", "status", "logs", "restart"):
        assert snippet in server_help
    for snippet in ("build", "seed", "reset", "nuke"):
        assert snippet in db_help
    for snippet in ("run", "cov"):
        assert snippet in test_help
    for snippet in ("lint", "format", "check"):
        assert snippet in quality_help


def test_primary_documented_routes_exist_in_app_surface() -> None:
    api_docs = Path("docs/apis.md").read_text(encoding="utf-8")
    gui_docs = Path("docs/gui.md").read_text(encoding="utf-8")
    routes = _iter_routes("dewey_service/app.py")

    documented_routes = {
        ("GET", "/healthz"),
        ("GET", "/readyz"),
        ("GET", "/health"),
        ("GET", "/obs_services"),
        ("GET", "/api_health"),
        ("GET", "/endpoint_health"),
        ("GET", "/db_health"),
        ("GET", "/my_health"),
        ("GET", "/auth_health"),
        ("GET", "/login"),
        ("GET", "/auth/login"),
        ("GET", "/auth/callback"),
        ("GET", "/ui"),
        ("GET", "/artifacts"),
        ("GET", "/literature"),
        ("GET", "/search"),
        ("GET", "/ui/anomalies"),
        ("GET", "/ui/observability"),
        ("GET", "/admin"),
        ("POST", "/api/v1/literature/search"),
        ("POST", "/api/v1/literature/save"),
        ("PATCH", "/api/v1/literature/saves/{literature_save_euid}"),
        ("GET", "/api/v1/literature/saves/mine"),
        ("GET", "/api/v1/artifacts"),
        ("POST", "/api/v1/artifacts"),
        ("POST", "/api/v1/artifacts/import"),
        ("POST", "/api/v1/artifact-prefixes"),
        ("POST", "/api/v1/artifacts/upload-sessions"),
        ("POST", "/api/v1/artifacts/upload-sessions/{upload_token}/complete"),
        ("GET", "/api/v1/artifacts/{artifact_euid}"),
        ("POST", "/api/v1/artifacts/{artifact_euid}/storage/verify"),
        ("POST", "/api/v1/artifacts/{artifact_euid}/storage/lock"),
        ("GET", "/api/v1/artifact-sets"),
        ("POST", "/api/v1/artifact-sets"),
        ("GET", "/api/v1/artifact-sets/{artifact_set_euid}"),
        ("POST", "/api/v1/artifact-sets/{artifact_set_euid}/members"),
        ("DELETE", "/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}"),
        ("POST", "/api/v1/resolve/artifact"),
        ("POST", "/api/v1/resolve/artifact-set"),
        ("POST", "/api/v1/share-references"),
        ("GET", "/api/v1/share-references/{share_reference_euid}"),
        ("GET", "/api/v1/artifacts/{artifact_euid}/share-references"),
        ("POST", "/api/search/v2/query"),
        ("POST", "/api/search/v2/export"),
        ("POST", "/api/v1/external-objects"),
        ("POST", "/api/v1/external-object-relations"),
        ("GET", "/api/v1/{target_type}/{target_euid}/external-object-relations"),
    }

    for method, path in documented_routes:
        assert (method, path) in routes
        assert path in api_docs or path in gui_docs


def test_gui_doc_references_four_committed_screenshots() -> None:
    gui_doc = Path("docs/gui.md").read_text(encoding="utf-8")
    screenshot_paths = [
        "assets/dashboard.png",
        "assets/artifacts-workflow.png",
        "assets/literature-search-save.png",
        "assets/unified-search-results.png",
    ]

    for path in screenshot_paths:
        assert path in gui_doc
        assert (Path("docs") / path).exists()


def test_readme_contains_exactly_one_mermaid_diagram_and_architecture_contains_one() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    architecture = Path("docs/architecture.md").read_text(encoding="utf-8")

    assert len(re.findall(r"```mermaid", readme)) == 1
    assert len(re.findall(r"```mermaid", architecture)) == 1
