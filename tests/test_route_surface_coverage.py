from __future__ import annotations

import ast
import re
from pathlib import Path


def _iter_routes(module_path: str) -> set[tuple[str, str]]:
    tree = ast.parse(Path(module_path).read_text())
    routes: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(
                decorator.func, ast.Attribute
            ):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            if not isinstance(decorator.args[0].value, str):
                continue
            routes.add((method, decorator.args[0].value))
    return routes


def _sample_path(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value.split("?", 1)[0]
    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append("SEGMENT")
            else:
                return None
        return "".join(parts).split("?", 1)[0]
    return None


def _iter_direct_request_samples() -> set[tuple[str, str]]:
    samples: set[tuple[str, str]] = set()
    for path in Path("tests").glob("test_*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                continue
            if not node.args:
                continue
            sample = _sample_path(node.args[0])
            if sample is None:
                continue
            samples.add((method, sample))
    return samples


def _route_matches(route: str, sample: str) -> bool:
    pattern = re.escape(route)
    pattern = re.sub(r"\\\{[^{}]+\\\}", r"[^/]+", pattern)
    return re.fullmatch(pattern, sample) is not None


def test_all_decorated_routes_have_direct_request_coverage() -> None:
    decorated_routes = _iter_routes("dewey_service/app.py")
    request_samples = _iter_direct_request_samples()
    missing = sorted(
        (method, route)
        for method, route in decorated_routes
        if not any(
            method == sample_method and _route_matches(route, sample_route)
            for sample_method, sample_route in request_samples
        )
    )

    assert missing == []
