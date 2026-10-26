"""Prepare a reviewed recipient configuration without exposing or replacing authority."""

import hashlib
import json
import stat
from copy import deepcopy

import pytest
import typer
import yaml

from dewey_service.cli import config_extra


def fixtures(tmp_path, monkeypatch):
    source = tmp_path / "current.yaml"
    payload = {
        "application": {"session_secret_key": "retained-session-secret"},
        "auth": {
            "mode": "external_broker",
            "cognito": {"domain": "retained.example.test"},
            "external_broker": {
                "service_id": "dewey",
                "service_token": "retained-service-token",
                "login_url": "https://login.example.test/auth/login",
                "handoff_exchange_url": "https://login.example.test/auth/handoff/consume",
                "callback_url": "https://dewey.example.test/auth/lsmc/callback",
                "logout_url": "https://login.example.test/auth/logout",
                "ca_bundle": "",
            },
        },
        "share": {
            "ingress_assertion": "retained-private-assertion-" * 2,
            "ingress_assertion_header": "X-Dewey-Tailnet-Assertion",
            "trusted_proxy_peer": "127.0.0.1",
            "application_origin": "https://dewey.example.test",
            "content_host_suffix": "content.example.test",
            "session_generation": "retained-session-generation",
        },
        "unrelated": {"retained": True},
    }
    source.write_text(yaml.safe_dump(payload))
    source.chmod(0o600)
    contract = {
        "public_ingress_assertion": "new-public-assertion-" * 3,
        "auth": {
            "external_broker": {
                field: "https://login.example.test" + path
                for field, path in config_extra._RECIPIENT_ENDPOINTS.items()
            }
        },
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract))
    path.chmod(0o600)
    monkeypatch.setattr(config_extra, "get_config_file_path", lambda: source)
    output = []
    monkeypatch.setattr(config_extra.ccyo_out, "emit_json", lambda value: output.append(value))
    return source, payload, path, contract, output


def test_prepare_preserves_source_and_authority_and_emits_only_hashes(tmp_path, monkeypatch):
    source, payload, path, contract, output = fixtures(tmp_path, monkeypatch)
    original = source.read_bytes()
    destination = tmp_path / "release.yaml"
    monkeypatch.setenv("DEWEY_SHARE_INGRESS_ASSERTION", "ambient-value-must-not-change-source")
    config_extra._prepare_sharing_v12(destination, path)
    assert source.read_bytes() == original
    prepared = yaml.safe_load(destination.read_bytes())
    expected = deepcopy(payload)
    expected["auth"]["external_broker"].update(contract["auth"]["external_broker"])
    expected["share"].update(
        public_ingress_assertion=contract["public_ingress_assertion"],
        public_ingress_assertion_header="X-Dewey-Recipient-Assertion",
    )
    assert prepared == expected
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert output == [
        {
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "destination_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        }
    ]
    with pytest.raises(typer.BadParameter, match="new file"):
        config_extra._prepare_sharing_v12(destination, path)


def test_prepare_preserves_existing_dewey_logout_service_query(tmp_path, monkeypatch):
    source, payload, path, contract, output = fixtures(tmp_path, monkeypatch)
    logout = "https://login.example.test/auth/logout?service=dewey"
    payload["auth"]["external_broker"]["logout_url"] = logout
    source.write_text(yaml.safe_dump(payload))
    original = source.read_bytes()
    destination = tmp_path / "release.yaml"
    config_extra._prepare_sharing_v12(destination, path)
    assert source.read_bytes() == original
    prepared = yaml.safe_load(destination.read_bytes())
    assert prepared["auth"]["external_broker"]["logout_url"] == logout
    assert (
        prepared["auth"]["external_broker"]["service_token"]
        == payload["auth"]["external_broker"]["service_token"]
    )
    assert set(output[0]) == {"source_sha256", "destination_sha256"}


@pytest.mark.parametrize(
    "logout",
    [
        "https://login.example.test/auth/logout?service=other",
        "https://login.example.test/auth/logout?service=dewey&service=dewey",
        "https://login.example.test/auth/logout?service=dewey&next=%2Fui",
        "https://login.example.test/auth/logout?service=%64ewey",
        "https://login.example.test/auth/logout?service=dewey#fragment",
        "https://other.example.test/auth/logout?service=dewey",
        "https://user@login.example.test/auth/logout?service=dewey",
    ],
)
def test_prepare_rejects_other_logout_query_or_authority(tmp_path, monkeypatch, logout):
    source, payload, path, contract, output = fixtures(tmp_path, monkeypatch)
    payload["auth"]["external_broker"]["logout_url"] = logout
    source.write_text(yaml.safe_dump(payload))
    destination = tmp_path / "release.yaml"
    with pytest.raises(typer.BadParameter):
        config_extra._prepare_sharing_v12(destination, path)
    assert not destination.exists() and not output


@pytest.mark.parametrize("field", list(config_extra._RECIPIENT_ENDPOINTS))
def test_new_recipient_endpoints_still_reject_logout_service_query(tmp_path, monkeypatch, field):
    source, payload, path, contract, output = fixtures(tmp_path, monkeypatch)
    contract["auth"]["external_broker"][field] += "?service=dewey"
    path.write_text(json.dumps(contract))
    destination = tmp_path / "release.yaml"
    with pytest.raises(typer.BadParameter):
        config_extra._prepare_sharing_v12(destination, path)
    assert not destination.exists() and not output


@pytest.mark.parametrize(
    "bad",
    [
        "authority",
        "missing",
        "public_private_equal",
        "contract_mode",
        "endpoint_query",
        "source_authority",
    ],
)
def test_invalid_contract_fails_without_destination_or_secret_output(tmp_path, monkeypatch, bad):
    source, payload, path, contract, output = fixtures(tmp_path, monkeypatch)
    if bad == "authority":
        contract["auth"]["external_broker"]["identity_url"] = (
            "https://other.example.test/api/v1/dewey/identity/introspect"
        )
    if bad == "missing":
        del contract["auth"]["external_broker"]["identity_mint_url"]
    if bad == "public_private_equal":
        contract["public_ingress_assertion"] = payload["share"]["ingress_assertion"]
    if bad == "endpoint_query":
        contract["auth"]["external_broker"]["identity_url"] += "?secret=value"
    if bad == "source_authority":
        payload["auth"]["external_broker"]["handoff_exchange_url"] = (
            "https://other.example.test/auth/handoff/consume"
        )
        source.write_text(yaml.safe_dump(payload))
    path.write_text(json.dumps(contract))
    if bad == "contract_mode":
        path.chmod(0o644)
    destination = tmp_path / "release.yaml"
    with pytest.raises(typer.BadParameter) as rejected:
        config_extra._prepare_sharing_v12(destination, path)
    assert not destination.exists() and not output
    assert "retained-service-token" not in str(rejected.value) and "?secret=value" not in str(
        rejected.value
    )
