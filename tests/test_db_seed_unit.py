from __future__ import annotations

import importlib
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_db_seed_main_claims_prefixes_before_seeding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: dict[str, object] = {}
    core_config_dir = db_seed.find_tapdb_core_config_dir()
    domain_registry = tmp_path / "domain_code_registry.json"
    prefix_registry = tmp_path / "prefix_ownership_registry.json"
    domain_registry.write_text(
        '{"version":"0.4.0","domains":{"Z":{"name":"test-localhost"}}}\n',
        encoding="utf-8",
    )

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

    def fake_get_settings() -> SimpleNamespace:
        return SimpleNamespace(
            tapdb_domain_code="Z",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_registry_path=str(domain_registry),
            tapdb_prefix_ownership_registry_path=str(prefix_registry),
        )

    monkeypatch.setattr(db_seed, "TapDBBackend", FakeBackend)
    monkeypatch.setattr(db_seed, "resolve_seed_config_dirs", fake_resolve)
    monkeypatch.setattr(db_seed, "get_settings", fake_get_settings)
    monkeypatch.setattr(
        db_seed,
        "validate_template_configs",
        lambda config_dirs, strict: (
            [
                {
                    "_source_file": str(
                        tmp_path / "config" / "tapdb_templates" / "dewey" / "templates.json"
                    ),
                    "name": "Dewey Artifact",
                    "polymorphic_discriminator": "data_template",
                    "category": "DGX",
                    "type": "data",
                    "subtype": "artifact",
                    "version": "1.0",
                    "instance_prefix": "DGX",
                },
                {
                    "_source_file": str(
                        core_config_dir / "system" / "system.json"
                    ),
                    "name": "TapDB System User",
                    "polymorphic_discriminator": "actor_template",
                    "category": "SYS",
                    "type": "actor",
                    "subtype": "system_user",
                    "version": "1.0",
                    "instance_prefix": "SYS",
                },
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        db_seed,
        "seed_templates",
        lambda session, templates, overwrite, **kwargs: calls.update(
            {
                "seed_session": session,
                "templates": templates,
                "overwrite": overwrite,
                "seed_kwargs": kwargs,
                "claim_exists": json.loads(prefix_registry.read_text(encoding="utf-8"))[
                    "ownership"
                ]["Z"]["DGX"]["issuer_app_code"]
                == "dewey",
            }
        ),
    )

    db_seed.main()

    assert calls["app_username"] == "dewey"
    assert calls["commit"] is True
    assert calls["entered"] is True
    assert calls["exited"] is True
    assert str(calls["config_root"]).endswith("config/tapdb_templates")
    assert calls["seed_session"] == "session"
    assert len(calls["templates"]) == 2
    assert calls["overwrite"] is True
    assert calls["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_kwargs"]["owner_repo_name"] == "dewey"
    assert str(calls["seed_kwargs"]["domain_registry_path"]).endswith(
        "domain_code_registry.json"
    )
    assert str(calls["seed_kwargs"]["prefix_registry_path"]).endswith(
        "prefix_ownership_registry.json"
    )
    assert calls["claim_exists"] is True
    registry = json.loads(prefix_registry.read_text(encoding="utf-8"))
    assert registry["ownership"]["Z"]["DGX"]["issuer_app_code"] == "dewey"
    assert "SYS" not in registry["ownership"]["Z"]


def test_db_seed_claim_helper_rejects_collisions(tmp_path: Path) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    repo_root = Path(__file__).resolve().parents[1]
    domain_registry = tmp_path / "domain_code_registry.json"
    prefix_registry = tmp_path / "prefix_ownership_registry.json"
    domain_registry.write_text(
        '{"version":"0.4.0","domains":{"Z":{"name":"test-localhost"}}}\n',
        encoding="utf-8",
    )
    prefix_registry.write_text(
        (repo_root / "dewey_service" / "etc" / "prefix_ownership_registry.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    payload = json.loads(prefix_registry.read_text(encoding="utf-8"))
    payload["ownership"]["Z"]["DGX"]["issuer_app_code"] = "other-repo"
    prefix_registry.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    templates = [
        {
            "_source_file": str(tmp_path / "config" / "tapdb_templates" / "dewey" / "templates.json"),
            "name": "Dewey Artifact",
            "polymorphic_discriminator": "data_template",
            "category": "DGX",
            "type": "data",
            "subtype": "artifact",
            "version": "1.0",
            "instance_prefix": "DGX",
        }
    ]

    with pytest.raises(ValueError, match="owned by 'other-repo'"):
        db_seed._claim_client_template_prefix_ownership(
            templates,
            domain_code="Z",
            owner_repo_name="dewey",
            domain_registry_path=domain_registry,
            prefix_registry_path=prefix_registry,
            core_config_dir=tmp_path / "core_config",
        )


def test_db_seed_claim_helper_skips_core_prefixes(tmp_path: Path) -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    domain_registry = tmp_path / "domain_code_registry.json"
    prefix_registry = tmp_path / "prefix_ownership_registry.json"
    domain_registry.write_text(
        '{"version":"0.4.0","domains":{"Z":{"name":"test-localhost"}}}\n',
        encoding="utf-8",
    )

    templates = [
        {
            "_source_file": str(tmp_path / "core_config" / "system" / "system.json"),
            "name": "TapDB System User",
            "polymorphic_discriminator": "actor_template",
            "category": "SYS",
            "type": "actor",
            "subtype": "system_user",
            "version": "1.0",
            "instance_prefix": "SYS",
        },
        {
            "_source_file": str(tmp_path / "core_config" / "message" / "webhook_event.json"),
            "name": "TapDB Message",
            "polymorphic_discriminator": "message_template",
            "category": "MSG",
            "type": "message",
            "subtype": "webhook_event",
            "version": "1.0",
            "instance_prefix": "MSG",
        },
    ]

    prefixes = db_seed._claim_client_template_prefix_ownership(
        templates,
        domain_code="Z",
        owner_repo_name="dewey",
        domain_registry_path=domain_registry,
        prefix_registry_path=prefix_registry,
        core_config_dir=tmp_path / "core_config",
    )

    assert prefixes == []
    assert not prefix_registry.exists()


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
    tmp_root = Path("/tmp/dewey-db-seed-script-test")
    domain_registry = tmp_root / "domain_code_registry.json"
    prefix_registry = tmp_root / "prefix_ownership_registry.json"
    tmp_root.mkdir(parents=True, exist_ok=True)
    domain_registry.write_text(
        '{"version":"0.4.0","domains":{"Z":{"name":"test-localhost"}}}\n',
        encoding="utf-8",
    )

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
    monkeypatch.setattr(
        "dewey_service.settings.get_settings",
        lambda: SimpleNamespace(
            tapdb_domain_code="Z",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_registry_path=str(domain_registry),
            tapdb_prefix_ownership_registry_path=str(prefix_registry),
        ),
    )
    monkeypatch.setattr(
        "daylily_tapdb.templates.loader.resolve_seed_config_dirs",
        lambda config_root: [config_root],
    )
    monkeypatch.setattr(
        "daylily_tapdb.templates.loader.validate_template_configs",
        lambda config_dirs, strict: (
            [
                {
                    "_source_file": str(tmp_root / "config" / "tapdb_templates" / "dewey" / "templates.json"),
                    "name": "Dewey Artifact",
                    "polymorphic_discriminator": "data_template",
                    "category": "DGX",
                    "type": "data",
                    "subtype": "artifact",
                    "version": "1.0",
                    "instance_prefix": "DGX",
                }
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        "daylily_tapdb.templates.loader.seed_templates",
        lambda session, templates, overwrite, **kwargs: calls.update(
            {
                "seed_session": session,
                "templates": templates,
                "overwrite": overwrite,
                "seed_kwargs": kwargs,
            }
        ),
    )

    sys.modules.pop("dewey_service.db_seed", None)
    runpy.run_module("dewey_service.db_seed", run_name="__main__")

    assert calls["app_username"] == "dewey"
    assert calls["commit"] is True
    assert calls["seed_session"] == "session"
    assert calls["overwrite"] is True
    assert calls["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_kwargs"]["owner_repo_name"] == "dewey"
    assert str(calls["seed_kwargs"]["domain_registry_path"]).endswith(
        "domain_code_registry.json"
    )
    assert str(calls["seed_kwargs"]["prefix_registry_path"]).endswith(
        "prefix_ownership_registry.json"
    )
