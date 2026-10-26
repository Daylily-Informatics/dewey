"""Operator release commands preserve configuration and require reviewed migration inputs."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
import yaml

from dewey_service.cli import config_extra, db
from tests.test_config_sharing_v12 import fixtures


@pytest.mark.parametrize(
    "mutation",
    [
        "source_list",
        "contract_list",
        "extra_auth",
        "wrong_mode",
        "wrong_service",
        "missing_service_token",
        "bad_callback",
        "changed_endpoint",
        "changed_assertion",
        "changed_header",
        "missing_session_generation",
        "missing_session_secret",
    ],
)
def test_release_configuration_rejects_missing_or_changed_existing_authority(
    tmp_path, monkeypatch, mutation
):
    source, payload, contract_path, contract, output = fixtures(tmp_path, monkeypatch)
    if mutation == "source_list":
        payload = []
    elif mutation == "contract_list":
        contract = []
    elif mutation == "extra_auth":
        contract["auth"]["unexpected"] = {}
    elif mutation == "wrong_mode":
        payload["auth"]["mode"] = "local"
    elif mutation == "wrong_service":
        payload["auth"]["external_broker"]["service_id"] = "other"
    elif mutation == "missing_service_token":
        payload["auth"]["external_broker"]["service_token"] = ""
    elif mutation == "bad_callback":
        payload["auth"]["external_broker"]["callback_url"] = (
            "https://other.example.test/auth/lsmc/callback"
        )
    elif mutation == "changed_endpoint":
        payload["auth"]["external_broker"]["identity_url"] = "https://login.example.test/changed"
    elif mutation == "changed_assertion":
        payload["share"]["public_ingress_assertion"] = "other-existing-assertion"
    elif mutation == "changed_header":
        payload["share"]["public_ingress_assertion_header"] = "X-Other"
    elif mutation == "missing_session_generation":
        payload["share"].pop("session_generation")
    elif mutation == "missing_session_secret":
        payload["application"]["session_secret_key"] = ""
    source.write_text(yaml.safe_dump(payload))
    contract_path.write_text(json.dumps(contract))
    original = source.read_bytes()
    destination = tmp_path / "candidate.yaml"
    with pytest.raises(typer.BadParameter, match="Invalid recipient contract"):
        config_extra._prepare_sharing_v12(destination, contract_path)
    assert source.read_bytes() == original and not destination.exists() and output == []


def test_release_configuration_refuses_relative_paths_symlinks_and_source_drift(
    tmp_path, monkeypatch
):
    source, payload, contract_path, contract, output = fixtures(tmp_path, monkeypatch)
    with pytest.raises(typer.BadParameter, match="absolute"):
        config_extra._prepare_sharing_v12(Path("relative.yaml"), contract_path)
    linked = tmp_path / "linked.yaml"
    linked.symlink_to(source)
    with pytest.raises(typer.BadParameter, match="new file"):
        config_extra._prepare_sharing_v12(linked, contract_path)
    real_settings = config_extra._FileSettings

    def source_drift(**kwargs):
        result = real_settings(**kwargs)
        source.write_bytes(source.read_bytes() + b"\n# concurrent operator edit\n")
        return result

    monkeypatch.setattr(config_extra, "_FileSettings", source_drift)
    destination = tmp_path / "candidate.yaml"
    with pytest.raises(typer.BadParameter, match="changed during preparation"):
        config_extra._prepare_sharing_v12(destination, contract_path)
    assert not destination.exists() and not output


@pytest.mark.parametrize("phase", ["inventory", "apply", "verify"])
def test_preserving_migration_cli_uses_explicit_operator_and_private_receipts(
    tmp_path, monkeypatch, phase
):
    from dewey_service import audit, registry_access, service, share_upgrade_v3, tapdb_backend

    attribution = tmp_path / "attribution.json"
    attribution.write_text(
        json.dumps(
            {
                "actor_kind": "service",
                "actor_issuer": "fixture-operator",
                "actor_subject": "fixture-operator",
                "service_identity": "dewey",
                "request_id": "fixture-request",
                "operation_id": "fixture-operation",
            }
        )
    )
    attribution.chmod(0o600)
    inventory = tmp_path / "inventory.json"
    if phase != "inventory":
        inventory.write_text(json.dumps({"inventory_sha256": "reviewed-fixture-digest"}))
        inventory.chmod(0o600)
    receipt = tmp_path / "receipt.json"
    monkeypatch.setenv("DEWEY_CONFIG", str(tmp_path / "private-config.yaml"))
    backend = SimpleNamespace()
    seen, printed = [], []

    def build_backend(**kwargs):
        assert kwargs == {"app_username": "fixture-operator"}
        return backend

    monkeypatch.setattr(tapdb_backend, "TapDBBackend", build_backend)
    monkeypatch.setattr(service, "DeweyService", lambda value: value)

    def invoke(value, *args):
        assert value is backend
        actor = registry_access.current_principal()
        assert actor.subject == "fixture-operator" and actor.service and actor.admin
        assert registry_access.maintenance_mode()
        assert audit.current_explicit_attribution().actor_subject == "fixture-operator"
        seen.append(args)
        return {
            "phase": phase,
            "status": "complete",
            "schema_version": 3,
            "share_count": 4,
            "inventory_sha256": "reviewed-fixture-digest",
            "private_recipient": "recipient@example.test",
        }

    monkeypatch.setattr(share_upgrade_v3, phase, invoke)
    monkeypatch.setattr(db.ccyo_out, "print_text", printed.append)
    db.upgrade_sharing_v3(
        phase,
        inventory,
        "fixture-operator",
        attribution,
        "reviewed-fixture-digest" if phase != "inventory" else None,
        receipt if phase != "inventory" else None,
    )
    destination = inventory if phase == "inventory" else receipt
    assert destination.stat().st_mode & 0o777 == 0o600
    assert json.loads(destination.read_text())["private_recipient"] == "recipient@example.test"
    assert len(seen) == 1 and len(printed) == 1 and "recipient@example.test" not in printed[0]
    if phase != "inventory":
        assert seen[0] == (
            {"inventory_sha256": "reviewed-fixture-digest"},
            "reviewed-fixture-digest",
        )
    assert audit.current_explicit_attribution() is None


@pytest.mark.parametrize(
    "phase,actor,config,receipt,digest",
    [
        ("retire", "operator", "/fixture/config", "/fixture/receipt", "digest"),
        ("apply", "", "/fixture/config", "/fixture/receipt", "digest"),
        ("apply", "operator", "relative", "/fixture/receipt", "digest"),
        ("apply", "operator", "/fixture/config", None, "digest"),
        ("verify", "operator", "/fixture/config", "relative", "digest"),
        ("apply", "operator", "/fixture/config", "/fixture/receipt", None),
    ],
)
def test_migration_cli_rejects_unreviewed_inputs_before_database_access(
    monkeypatch, phase, actor, config, receipt, digest
):
    from dewey_service import tapdb_backend

    monkeypatch.setenv("DEWEY_CONFIG", config)

    def forbidden(**kwargs):
        pytest.fail("Invalid migration input reached the database constructor")

    monkeypatch.setattr(tapdb_backend, "TapDBBackend", forbidden)
    with pytest.raises(typer.BadParameter):
        db.upgrade_sharing_v3(
            phase,
            Path("/fixture/inventory"),
            actor,
            Path("/fixture/attribution"),
            digest,
            Path(receipt) if receipt else None,
        )
