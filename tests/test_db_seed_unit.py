from __future__ import annotations

import importlib
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer


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
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            calls["exited"] = True

    class FakeSession:
        def execute(self, statement, params=None):  # noqa: ANN001 - test double
            rows = calls.setdefault("identity_rows", [])
            rows.append(dict(params or {}))
            return SimpleNamespace(scalar_one_or_none=lambda: None)

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

    def fake_validate_template_configs(config_dirs, strict):  # noqa: ANN001 - test double
        if config_dirs == [core_config_dir]:
            return (
                [
                    {
                        "_source_file": str(core_config_dir / "system" / "system.json"),
                        "name": "TapDB System User",
                        "polymorphic_discriminator": "actor_template",
                        "category": "actor",
                        "type": "user",
                        "subtype": "system",
                        "version": "1.0",
                        "instance_prefix": "SYS",
                    },
                    {
                        "_source_file": str(
                            core_config_dir / "external_refs" / "external_ref.json"
                        ),
                        "name": "TapDB External Reference",
                        "polymorphic_discriminator": "external_reference_template",
                        "category": "reference",
                        "type": "external_identifier",
                        "subtype": "tapdb_object",
                        "version": "1.0",
                        "instance_prefix": "XRF",
                    },
                ],
                [],
            )
        return (
            [
                {
                    "_source_file": str(
                        tmp_path / "config" / "tapdb_templates" / "dewey" / "templates.json"
                    ),
                    "name": "Dewey Artifact",
                    "polymorphic_discriminator": "data_template",
                    "category": "data",
                    "type": "artifact",
                    "subtype": "generic",
                    "version": "1.0",
                    "instance_prefix": "DGX",
                },
                {
                    "_source_file": str(
                        tmp_path / "config" / "external_refs" / "external_ref.json"
                    ),
                    "name": "TapDB External Reference",
                    "polymorphic_discriminator": "external_reference_template",
                    "category": "reference",
                    "type": "external_identifier",
                    "subtype": "tapdb_object",
                    "version": "1.0",
                    "instance_prefix": "XRF",
                },
                {
                    "_source_file": str(tmp_path / "config" / "generic_viewer" / "viewer.json"),
                    "name": "TapDB Generic Viewer",
                    "polymorphic_discriminator": "generic_viewer_template",
                    "category": "GVR",
                    "type": "viewer",
                    "subtype": "generic",
                    "version": "1.0",
                    "instance_prefix": "GVR",
                },
            ],
            [],
        )

    monkeypatch.setattr(db_seed, "validate_template_configs", fake_validate_template_configs)
    monkeypatch.setattr(
        db_seed,
        "seed_templates",
        lambda session, templates, overwrite, **kwargs: calls.setdefault("seed_calls", []).append(
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
    assert len(calls["seed_calls"]) == 2
    assert all(
        call["seed_session"].__class__.__name__ == "FakeSession" for call in calls["seed_calls"]
    )
    assert calls["seed_calls"][0]["overwrite"] is True
    assert len(calls["seed_calls"][0]["templates"]) == 2
    assert calls["seed_calls"][0]["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_calls"][0]["seed_kwargs"]["owner_repo_name"] == "daylily-tapdb"
    assert calls["seed_calls"][1]["overwrite"] is True
    assert len(calls["seed_calls"][1]["templates"]) == 1
    assert calls["seed_calls"][1]["templates"][0]["instance_prefix"] == "DGX"
    assert calls["seed_calls"][1]["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_calls"][1]["seed_kwargs"]["owner_repo_name"] == "dewey"
    assert str(calls["seed_calls"][1]["seed_kwargs"]["domain_registry_path"]).endswith(
        "domain_code_registry.json"
    )
    assert str(calls["seed_calls"][1]["seed_kwargs"]["prefix_registry_path"]).endswith(
        "prefix_ownership_registry.json"
    )
    assert all(call["claim_exists"] is True for call in calls["seed_calls"])
    assert calls["identity_rows"] == [
        {
            "entity": "generic_template",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "DGX",
        },
        {
            "entity": "generic_template",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "DGX",
        },
        {
            "entity": "generic_instance_lineage",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "EDG",
        },
        {
            "entity": "generic_instance_lineage",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "EDG",
        },
        {
            "entity": "audit_log",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "ADT",
        },
        {
            "entity": "audit_log",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "ADT",
        },
    ]
    registry = json.loads(prefix_registry.read_text(encoding="utf-8"))
    assert registry["ownership"]["Z"]["DGX"]["issuer_app_code"] == "dewey"
    assert "SYS" not in registry["ownership"]["Z"]
    assert "XRF" not in registry["ownership"]["Z"]
    assert "GVR" not in registry["ownership"]["Z"]


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
            "_source_file": str(
                tmp_path / "config" / "tapdb_templates" / "dewey" / "templates.json"
            ),
            "name": "Dewey Artifact",
            "polymorphic_discriminator": "data_template",
            "category": "data",
            "type": "artifact",
            "subtype": "generic",
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
            "category": "actor",
            "type": "user",
            "subtype": "system",
            "version": "1.0",
            "instance_prefix": "SYS",
        },
        {
            "_source_file": str(tmp_path / "core_config" / "message" / "webhook_event.json"),
            "name": "TapDB Message",
            "polymorphic_discriminator": "message_template",
            "category": "message",
            "type": "webhook",
            "subtype": "event",
            "version": "1.0",
            "instance_prefix": "MSG",
        },
        {
            "_source_file": str(tmp_path / "client_config" / "external_refs" / "external_ref.json"),
            "name": "TapDB External Reference",
            "polymorphic_discriminator": "external_reference_template",
            "category": "reference",
            "type": "external_identifier",
            "subtype": "tapdb_object",
            "version": "1.0",
            "instance_prefix": "XRF",
        },
        {
            "_source_file": str(tmp_path / "client_config" / "generic_viewer" / "viewer.json"),
            "name": "TapDB Generic Viewer",
            "polymorphic_discriminator": "generic_viewer_template",
            "category": "GVR",
            "type": "viewer",
            "subtype": "generic",
            "version": "1.0",
            "instance_prefix": "GVR",
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
    monkeypatch.setattr(
        db_seed,
        "get_settings",
        lambda: SimpleNamespace(
            tapdb_domain_code="Z",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_registry_path="/tmp/domain_code_registry.json",
            tapdb_prefix_ownership_registry_path="/tmp/prefix_ownership_registry.json",
        ),
    )
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
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def execute(self, statement, params=None):  # noqa: ANN001 - tiny test double
            rows = calls.setdefault("identity_rows", [])
            rows.append(dict(params or {}))
            return SimpleNamespace(scalar_one_or_none=lambda: None)

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
                    "_source_file": str(
                        tmp_root / "config" / "tapdb_templates" / "dewey" / "templates.json"
                    ),
                    "name": "Dewey Artifact",
                    "polymorphic_discriminator": "data_template",
                    "category": "data",
                    "type": "artifact",
                    "subtype": "generic",
                    "version": "1.0",
                    "instance_prefix": "DGX",
                }
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        "daylily_tapdb.templates.loader.seed_templates",
        lambda session, templates, overwrite, **kwargs: calls.setdefault("seed_calls", []).append(
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
    assert len(calls["seed_calls"]) == 2
    assert all(
        call["seed_session"].__class__.__name__ == "FakeSession" for call in calls["seed_calls"]
    )
    assert calls["seed_calls"][0]["overwrite"] is True
    assert calls["seed_calls"][0]["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_calls"][0]["seed_kwargs"]["owner_repo_name"] == "daylily-tapdb"
    assert calls["seed_calls"][1]["overwrite"] is True
    assert calls["seed_calls"][1]["seed_kwargs"]["domain_code"] == "Z"
    assert calls["seed_calls"][1]["seed_kwargs"]["owner_repo_name"] == "dewey"
    assert str(calls["seed_calls"][1]["seed_kwargs"]["domain_registry_path"]).endswith(
        "domain_code_registry.json"
    )
    assert str(calls["seed_calls"][1]["seed_kwargs"]["prefix_registry_path"]).endswith(
        "prefix_ownership_registry.json"
    )
    assert calls["identity_rows"] == [
        {
            "entity": "generic_template",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "DGX",
        },
        {
            "entity": "generic_template",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "DGX",
        },
        {
            "entity": "generic_instance_lineage",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "EDG",
        },
        {
            "entity": "generic_instance_lineage",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "EDG",
        },
        {
            "entity": "audit_log",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "ADT",
        },
        {
            "entity": "audit_log",
            "domain_code": "Z",
            "owner_repo_name": "dewey",
            "prefix": "ADT",
        },
    ]


def test_db_seed_identity_prefix_helper_registers_lineage_prefix() -> None:
    db_seed = importlib.import_module("dewey_service.db_seed")
    calls: list[dict[str, object]] = []

    class FakeSession:
        def execute(self, statement, params=None):  # noqa: ANN001 - tiny test double
            calls.append(
                {
                    "sql": getattr(statement, "text", str(statement)),
                    "params": dict(params or {}),
                }
            )
            return SimpleNamespace(scalar_one_or_none=lambda: None)

    db_seed._ensure_identity_prefix_config(
        FakeSession(),
        entity="generic_instance_lineage",
        domain_code="Z",
        owner_repo_name="dewey",
        prefix="EDG",
    )

    assert len(calls) == 2
    assert "SELECT prefix" in calls[0]["sql"]
    assert calls[0]["params"] == {
        "entity": "generic_instance_lineage",
        "domain_code": "Z",
        "owner_repo_name": "dewey",
        "prefix": "EDG",
    }
    assert "INSERT INTO tapdb_identity_prefix_config" in calls[1]["sql"]
    assert calls[1]["params"] == {
        "entity": "generic_instance_lineage",
        "domain_code": "Z",
        "owner_repo_name": "dewey",
        "prefix": "EDG",
    }


def test_db_repair_templates_requires_explicit_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "unit")
    db_commands = importlib.import_module("dewey_service.cli.db")
    calls: list[str] = []
    monkeypatch.setattr(db_commands, "_verify_dewey_templates", lambda: calls.append("verify"))
    monkeypatch.setattr(db_commands, "_seed_dewey_template_overlay", lambda: calls.append("seed"))

    with pytest.raises(typer.Exit) as exc_info:
        db_commands.repair_templates(confirm_dewey_template_repair="")

    assert exc_info.value.exit_code == 1
    assert calls == []


def test_db_repair_templates_seeds_only_when_verification_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEWEY_DEPLOYMENT_CODE", "unit")
    db_commands = importlib.import_module("dewey_service.cli.db")
    calls: list[str] = []

    def fake_verify() -> None:
        calls.append("verify")
        if calls == ["verify"]:
            raise RuntimeError("Missing Dewey templates: system/registration_receipt/generic/1.0/")

    monkeypatch.setattr(db_commands, "_verify_dewey_templates", fake_verify)
    monkeypatch.setattr(db_commands, "_seed_dewey_template_overlay", lambda: calls.append("seed"))

    db_commands.repair_templates(
        confirm_dewey_template_repair=db_commands.DEWEY_PROD_TEMPLATE_SEED_APPROVAL
    )

    assert calls == ["verify", "seed", "verify"]
