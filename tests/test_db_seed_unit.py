from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path

import pytest


def test_db_seed_main_validates_and_seeds(monkeypatch: pytest.MonkeyPatch) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: dict[str, object] = {}

    class _Scope:
        def __enter__(self):
            calls["entered"] = True
            return "session"

        def __exit__(self, exc_type, exc, tb):
            calls["exited"] = True

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

        def session_scope(self, commit: bool = False):
            calls["commit"] = commit
            return _Scope()

    def fake_resolve(config_root: Path):
        calls["config_root"] = config_root
        return [config_root]

    monkeypatch.setattr(db_seed, "TapDBBackend", FakeBackend)
    monkeypatch.setattr(db_seed, "resolve_seed_config_dirs", fake_resolve)
    monkeypatch.setattr(
        db_seed,
        "validate_template_configs",
        lambda config_dirs, strict: ([{"template_code": "generic/data/artifact/1.0/"}], []),
    )
    monkeypatch.setattr(
        db_seed,
        "seed_templates",
        lambda session, templates, overwrite: calls.update(
            {"seed_session": session, "templates": templates, "overwrite": overwrite}
        ),
    )

    db_seed.main()

    assert calls["app_username"] == "dewey"
    assert calls["commit"] is True
    assert calls["entered"] is True
    assert calls["exited"] is True
    assert str(calls["config_root"]).endswith("config/tapdb_templates")
    assert calls["seed_session"] == "session"
    assert calls["templates"] == [{"template_code": "generic/data/artifact/1.0/"}]
    assert calls["overwrite"] is True


def test_db_seed_main_raises_on_validation_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: dict[str, object] = {}

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

        def session_scope(self, commit: bool = False):
            raise AssertionError("session_scope should not be entered on validation failure")

    class Issue:
        def __init__(self, message: str, level: str = "error") -> None:
            self.message = message
            self.level = level

    monkeypatch.setattr(db_seed, "TapDBBackend", FakeBackend)
    monkeypatch.setattr(db_seed, "resolve_seed_config_dirs", lambda config_root: [config_root])
    monkeypatch.setattr(
        db_seed,
        "validate_template_configs",
        lambda config_dirs, strict: ([], [Issue("bad template shape")]),
    )

    with pytest.raises(
        RuntimeError, match="Dewey template pack validation failed: bad template shape"
    ):
        db_seed.main()

    assert calls["app_username"] == "dewey"


def test_db_seed_module_runs_main_when_invoked_as_script(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class _Scope:
        def __enter__(self):
            return "session"

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

        def session_scope(self, commit: bool = False):
            calls["commit"] = commit
            return _Scope()

    monkeypatch.setattr("dewey_service.tapdb_backend.TapDBBackend", FakeBackend)
    monkeypatch.setattr("daylily_tapdb.resolve_seed_config_dirs", lambda config_root: [config_root])
    monkeypatch.setattr(
        "daylily_tapdb.validate_template_configs",
        lambda config_dirs, strict: ([{"template_code": "generic/data/artifact/1.0/"}], []),
    )
    monkeypatch.setattr(
        "daylily_tapdb.seed_templates",
        lambda session, templates, overwrite: calls.update(
            {"seed_session": session, "templates": templates, "overwrite": overwrite}
        ),
    )

    sys.modules.pop("dewey_service.db_seed", None)
    runpy.run_module("dewey_service.db_seed", run_name="__main__")

    assert calls["app_username"] == "dewey"
    assert calls["commit"] is True
    assert calls["seed_session"] == "session"
    assert calls["overwrite"] is True
