"""Dewey QEO registration keeps enforced validation in its real runtime."""

import pytest

from dewey_service.cli import _build_spec


def test_container_backend_is_explicit_and_enforced(monkeypatch):
    monkeypatch.setenv("DEWEY_EXECUTION_BACKEND", "dewey-container")
    spec = _build_spec()
    assert spec.runtime.default_backend == "dewey-container"
    assert spec.runtime.guard_mode == "enforced"
    assert not spec.runtime.allow_skip_check
    backend = next(b for b in spec.runtime.supported_backends if b.name == "dewey-container")
    assert backend.kind == "docker"
    assert backend.validation.files == ("/.dockerenv", "/app/dewey_service/cli/__init__.py")
    assert backend.validation.command_probe
    checks = {p.key: p for p in spec.runtime.prereqs}
    for key in ("dewey-daylily-tapdb", "dewey-daylily-auth-cognito"):
        assert "dewey-container" in checks[key].applies_to_backends
    for key in ("dewey-conda-active-env", "dewey-conda-env-name"):
        assert "dewey-container" not in checks[key].applies_to_backends


def test_conda_backend_remains_required_locally(monkeypatch):
    monkeypatch.delenv("DEWEY_EXECUTION_BACKEND", raising=False)
    assert _build_spec().runtime.default_backend == "dewey-conda"


def test_unknown_explicit_backend_is_rejected(monkeypatch):
    monkeypatch.setenv("DEWEY_EXECUTION_BACKEND", "not-a-backend")
    with pytest.raises(ValueError):
        _build_spec()
