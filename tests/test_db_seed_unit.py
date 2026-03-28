from __future__ import annotations

import importlib
import runpy
import sys


def test_db_seed_main_uses_env_ttl(monkeypatch) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: dict[str, object] = {}

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

    class FakeService:
        def __init__(self, backend, *, default_share_ttl_seconds: int) -> None:
            calls["backend"] = backend
            calls["ttl"] = default_share_ttl_seconds

        def bootstrap(self) -> None:
            calls["bootstrapped"] = True

    monkeypatch.setenv("DEWEY_DEFAULT_SHARE_REFERENCE_TTL_SECONDS", "120")
    monkeypatch.setattr(db_seed, "TapDBBackend", FakeBackend)
    monkeypatch.setattr(db_seed, "DeweyService", FakeService)

    db_seed.main()

    assert calls["app_username"] == "dewey"
    assert calls["ttl"] == 120
    assert calls["bootstrapped"] is True


def test_db_seed_main_invalid_ttl_defaults(monkeypatch) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: dict[str, object] = {}

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

    class FakeService:
        def __init__(self, backend, *, default_share_ttl_seconds: int) -> None:
            calls["ttl"] = default_share_ttl_seconds

        def bootstrap(self) -> None:
            calls["bootstrapped"] = True

    monkeypatch.setenv("DEWEY_DEFAULT_SHARE_REFERENCE_TTL_SECONDS", "not-an-int")
    monkeypatch.setattr(db_seed, "TapDBBackend", FakeBackend)
    monkeypatch.setattr(db_seed, "DeweyService", FakeService)

    db_seed.main()

    assert calls["app_username"] == "dewey"
    assert calls["ttl"] == 3600
    assert calls["bootstrapped"] is True


def test_db_seed_module_runs_main_when_invoked_as_script(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeBackend:
        def __init__(self, app_username: str) -> None:
            calls["app_username"] = app_username

    class FakeService:
        def __init__(self, backend, *, default_share_ttl_seconds: int) -> None:
            calls["ttl"] = default_share_ttl_seconds

        def bootstrap(self) -> None:
            calls["bootstrapped"] = True

    monkeypatch.setenv("DEWEY_DEFAULT_SHARE_REFERENCE_TTL_SECONDS", "75")
    monkeypatch.setattr("dewey_service.tapdb_backend.TapDBBackend", FakeBackend)
    monkeypatch.setattr("dewey_service.service.DeweyService", FakeService)
    sys.modules.pop("dewey_service.db_seed", None)

    runpy.run_module("dewey_service.db_seed", run_name="__main__")

    assert calls["app_username"] == "dewey"
    assert calls["ttl"] == 75
    assert calls["bootstrapped"] is True
