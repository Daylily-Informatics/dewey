"""New launch projection tests use synthetic credentials and no Docker/AWS calls."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/dewey_launch_environment_prepare.py"
SPEC = importlib.util.spec_from_file_location("dewey_launch_environment", SCRIPT)
assert SPEC and SPEC.loader
launch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launch)


def owning_service():
    environment = dict.fromkeys(launch.REQUIRED_PRESERVED, "synthetic-value")
    environment.update(
        DEWEY_API_BEARER_TOKEN="test-only-selected-primary",
        LSMC_AUTH_BROKER_SERVICE_TOKEN="test-only-service-credential",
        HOST="0.0.0.0",
        PORT="8914",
        DEWEY_CONFIG="/old/application.yaml",
        TAPDB_CONFIG_PATH="/old/runtime.yaml",
        UNLISTED_PRODUCT_SETTING='literal spaces = and "quotes"',
    )
    return {"environment": environment, "extra_hosts": list(launch.EXTRA_HOSTS)}


@pytest.mark.parametrize("matches", [True, False])
def test_complete_deployed_environment_preserved_with_explicit_primary_even_if_yaml_differs(
    matches,
):
    service = owning_service()
    config = {
        "application": {
            "api_bearer_token": (
                "test-only-selected-primary" if matches else "different-test-only-primary"
            )
        }
    }
    env, hosts, receipt = launch.prepare_payloads(
        yaml.safe_dump({"services": {"dewey": service}}).encode(),
        yaml.safe_dump(config).encode(),
        "rehearsal",
        launch.REHEARSAL_IMAGE_SHA,
    )
    result = dict(line.split("=", 1) for line in env.decode().splitlines())
    for key in (
        service["environment"].keys()
        - launch.isolated_overrides("rehearsal", launch.REHEARSAL_IMAGE_SHA).keys()
    ):
        assert result[key] == service["environment"][key]
    assert result["HOST"] == result["DEWEY_HOST"] == "127.0.0.1"
    assert result["PORT"] == result["DEWEY_PORT"] == "18914"
    assert result["TAPDB_CONFIG_PATH"].endswith("tapdb10-rehearsal-20260911/tapdb-runtime.yaml")
    assert result["DEWEY_QEO_INGEST_URL"] == ""
    assert hosts.decode().splitlines() == [f"--add-host={host}" for host in launch.EXTRA_HOSTS]
    assert receipt["yaml_primary_matches_deployed_environment"] is matches
    serialized = json.dumps(receipt)
    assert "test-only-selected-primary" not in serialized
    assert "test-only-service-credential" not in serialized


@pytest.mark.parametrize("value", [None, 123, "${AMBIENT_VALUE}", "escaped$$value", "line\nbreak"])
def test_unresolved_or_env_file_unsafe_values_fail_without_exposing_values(value):
    service = owning_service()
    service["environment"]["UNLISTED_PRODUCT_SETTING"] = value
    with pytest.raises(launch.PreparationError) as error:
        launch.extract_dewey(yaml.safe_dump({"services": {"dewey": service}}).encode())
    assert "AMBIENT_VALUE" not in str(error.value)


@pytest.mark.parametrize("field", ["env_file", "extends"])
def test_indirect_environment_cannot_be_silently_omitted(field):
    service = owning_service()
    service[field] = "unreviewed-reference"
    with pytest.raises(launch.PreparationError, match="Indirect"):
        launch.extract_dewey(yaml.safe_dump({"services": {"dewey": service}}).encode())


def test_missing_host_or_preserved_product_setting_fails():
    service = owning_service()
    service["extra_hosts"].pop()
    with pytest.raises(launch.PreparationError, match="extra_hosts"):
        launch.extract_dewey(yaml.safe_dump({"services": {"dewey": service}}).encode())
    service = owning_service()
    del service["environment"]["LSMC_AUTH_BROKER_SERVICE_TOKEN"]
    with pytest.raises(launch.PreparationError, match="environment key missing"):
        launch.extract_dewey(yaml.safe_dump({"services": {"dewey": service}}).encode())


def test_duplicate_yaml_key_fails_without_secret_value():
    with pytest.raises(launch.PreparationError, match="Duplicate") as error:
        launch.extract_dewey(b"services: {}\nservices: test-only-secret\n")
    assert "test-only-secret" not in str(error.value)


def test_private_output_is_exclusive_and_not_overwritten(tmp_path):
    path = tmp_path / "runtime.env"
    launch.write_new(path, b"TOKEN=test-only-original\n")
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        launch.write_new(path, b"TOKEN=test-only-replacement\n")
    assert path.read_bytes() == b"TOKEN=test-only-original\n"


def test_unique_loader_retains_safe_loader_object_tag_rejection():
    with pytest.raises(yaml.constructor.ConstructorError):
        launch.extract_dewey(b"!!python/object/apply:builtins.str ['must not construct']")


@pytest.mark.parametrize("image_sha", [None, "", "a" * 39, "g" * 40, "A" * 40])
def test_image_sha_validation_rejects_missing_or_noncanonical_revision(image_sha):
    with pytest.raises(launch.PreparationError, match="40-character"):
        launch.validate_image_sha("production", image_sha)


def test_image_sha_validation_pins_rehearsal_candidate():
    launch.validate_image_sha("rehearsal", launch.REHEARSAL_IMAGE_SHA)
    with pytest.raises(launch.PreparationError, match="Rehearsal image source SHA changed"):
        launch.validate_image_sha("rehearsal", "a" * 40)


def test_image_sha_validation_requires_cli_argument(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            str(SCRIPT),
            "--compose",
            str(launch.COMPOSE_PATH),
            "--dewey-config",
            launch.DIRECTORIES["production"] + "/dewey-config.yaml",
            "--lane",
            "production",
            "--output-dir",
            "/explicit/private/output",
        ],
    )
    with pytest.raises(SystemExit) as error:
        launch.main()
    assert error.value.code == 2
    assert "--image-sha" in capsys.readouterr().err


def test_image_sha_production_input_propagates_to_environment_and_receipt():
    final_test_sha = "a" * 40
    config = {"application": {"api_bearer_token": "test-only-selected-primary"}}
    env, _, receipt = launch.prepare_payloads(
        yaml.safe_dump({"services": {"dewey": owning_service()}}).encode(),
        yaml.safe_dump(config).encode(),
        "production",
        final_test_sha,
    )
    result = dict(line.split("=", 1) for line in env.decode().splitlines())
    assert result["DEWEY_BUILD_SHA"] == result["LSMC_RELEASE_SHA"] == final_test_sha
    assert receipt["image_sha"] == final_test_sha
    assert result["DEWEY_API_BEARER_TOKEN"] == "test-only-selected-primary"
    assert result["TAPDB_CONFIG_PATH"] == launch.DIRECTORIES["production"] + "/tapdb-runtime.yaml"
