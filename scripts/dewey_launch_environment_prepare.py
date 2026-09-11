#!/usr/bin/env python3
"""Project the reviewed owning Dewey Compose environment into private launch inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

COMPOSE_PATH = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
COMPOSE_SHA256 = "35a37f2c5df1cc84ebfd57ad19a9d56b14f88b3e6bc322aebadd3db081da8509"
REHEARSAL_IMAGE_SHA = "5f51f8137d7bd2d4e2668593df5cc492b390a4b8"
DIRECTORIES = {
    "rehearsal": "/opt/dewey/day/releases/tapdb10-rehearsal-20260911",
    "production": "/opt/dewey/day/releases/9.0.0",
}
EXTRA_HOSTS = [
    f"{name}.day.lsmc.bio:127.0.0.1"
    for name in ("login", "atlas", "bloom", "ursa", "dewey", "qeo", "zebra-day", "kahlo")
]
REQUIRED_PRESERVED = {
    "LSMC_AUTH_MODE",
    "LSMC_AUTH_BROKER_CALLBACK_URL",
    "LSMC_AUTH_BROKER_HANDOFF_EXCHANGE_URL",
    "LSMC_AUTH_BROKER_LOGIN_URL",
    "LSMC_AUTH_BROKER_LOGOUT_URL",
    "LSMC_AUTH_BROKER_SERVICE_ID",
    "LSMC_AUTH_BROKER_SERVICE_TOKEN",
    "LSMC_AUTH_BROKER_SHARE_RECIPIENT_PREPARE_URL",
    "LSMC_AUTH_BROKER_USER_PREFERENCES_URL",
    "LSMC_AI_AGENT_ACCESS_ENABLED",
    "LSMC_AI_AGENT_SERVICE_ID",
    "DEWEY_API_BEARER_TOKEN",
    "DEWEY_QEO_RESOLVER_TOKEN_SHA256",
    "DEWEY_QEO_RESOLVER_TOKEN_EXPIRES_AT",
    "ATLAS_BASE_URL",
    "BLOOM_BASE_URL",
    "DEWEY_MANAGED_STORAGE_BUCKET",
    "DEWEY_MANAGED_STORAGE_PREFIX",
    "DEWEY_AWS_REGION",
    "OTEL_SERVICE_NAME",
    "AWS_SDK_LOAD_CONFIG",
}


class PreparationError(RuntimeError):
    """Only credential-free messages may be raised with this type."""


def require(condition, reason):
    if not condition:
        raise PreparationError(reason)


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate/merged mappings instead of accepting an ambiguous source."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        require(key_node.tag != "tag:yaml.org,2002:merge", "YAML merge keys are unsupported")
        key = loader.construct_object(key_node, deep=True)
        require(isinstance(key, str) and key not in result, "Duplicate or nonstring YAML key")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def exact_file(path, *, private=False):
    require(path.is_absolute() and path.is_file(), "Explicit existing absolute file required")
    require(path.resolve() == path, "Canonical file path required")
    if private:
        require(path.stat().st_mode & 0o077 == 0, "Private file permissions required")
    return path.read_bytes()


def extract_dewey(compose_bytes):
    """Pure projection; caller must verify the owning file hash first."""
    # UniqueLoader subclasses SafeLoader; only duplicate-key rejection is added.
    raw = yaml.load(compose_bytes, Loader=UniqueLoader)  # nosec B506
    require(isinstance(raw, dict), "Compose root must be a mapping")
    services = raw.get("services")
    require(isinstance(services, dict), "Compose services must be a mapping")
    service = services.get("dewey")
    require(isinstance(service, dict), "Owning Dewey service is required")
    require(
        "env_file" not in service and "extends" not in service, "Indirect environment forbidden"
    )
    environment = service.get("environment")
    require(isinstance(environment, dict), "Literal environment mapping required")
    for key, value in environment.items():
        require(re.fullmatch(r"[A-Z_][A-Z0-9_]*", key), "Invalid environment key")
        require(isinstance(value, str), "Environment values must be explicit strings")
        require(
            not any(c in value for c in ("$", "\n", "\r", "\0")), "Nonliteral environment value"
        )
    require(REQUIRED_PRESERVED <= environment.keys(), "Required deployed environment key missing")
    require(service.get("extra_hosts") == EXTRA_HOSTS, "Owning extra_hosts mapping changed")
    return dict(environment), list(EXTRA_HOSTS)


def validate_image_sha(lane, image_sha):
    require(
        isinstance(image_sha, str) and re.fullmatch(r"[0-9a-f]{40}", image_sha),
        "Explicit 40-character lowercase hexadecimal image source SHA required",
    )
    if lane == "rehearsal":
        require(image_sha == REHEARSAL_IMAGE_SHA, "Rehearsal image source SHA changed")


def isolated_overrides(lane, image_sha):
    """Only the approved runtime identity, mounts and loopback isolation change."""
    validate_image_sha(lane, image_sha)
    directory = DIRECTORIES[lane]
    overrides = {
        "HOME": "/home/ubuntu",
        "LSMC_SERVICE_NAME": "dewey",
        "LSMC_ENV": "prod",
        "LSMC_RUNTIME_CLASS": "aws-compose",
        "HOST": "127.0.0.1",
        "PORT": "18914",
        "DEWEY_HOST": "127.0.0.1",
        "DEWEY_PORT": "18914",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
        "DEWEY_EXECUTION_BACKEND": "dewey-container",
        "DEWEY_DEPLOYMENT_CODE": "day",
        "DEWEY_ENVIRONMENT": "production",
        "DEWEY_CONFIG": directory + "/dewey-config.yaml",
        "TAPDB_CONFIG_PATH": directory + "/tapdb-runtime.yaml",
        "DEWEY_DATABASE_TARGET": "aurora",
        "DEWEY_TAPDB_CLIENT_ID": "dewey",
        "DEWEY_TAPDB_DATABASE_NAME": "dewey-day",
        "DEWEY_TAPDB_DOMAIN_CODE": "M",
        "DEWEY_TAPDB_OWNER_REPO_NAME": "dewey",
        "DEWEY_BUILD_SHA": image_sha,
        "LSMC_RELEASE_SHA": image_sha,
        "AWS_PROFILE": "lsmc",
        "AWS_REGION": "us-west-2",
        "AWS_DEFAULT_REGION": "us-west-2",
        "AWS_CONFIG_FILE": "/home/ubuntu/.aws/config",
        "AWS_SHARED_CREDENTIALS_FILE": "/home/ubuntu/.aws/credentials",
        "DEWEY_NCBI_API_KEY_FILE": "/home/ubuntu/.config/ncbi/key.txt",
        "LSMC_AI_AGENT_GRANTS_PATH": "/opt/dayhoff/deployments/day/state/kahlo/ai-agent-grants.json",
        "XDG_STATE_HOME": "/run/dewey-acceptance-state/state",
        "XDG_CACHE_HOME": "/run/dewey-acceptance-state/cache",
        "DEWEY_LITERATURE_METAPUB_CACHE_DIR": "/run/dewey-acceptance-state/metapub",
    }
    # Empty dispatch configuration is the explicit application disable contract.
    overrides["DEWEY_QEO_INGEST_URL"] = ""
    overrides["DEWEY_QEO_API_TOKEN"] = ""  # nosec B105
    overrides["DEWEY_QEO_CONSUMER_GROUP"] = ""
    return overrides


def prepare_payloads(compose_bytes, config_bytes, lane, image_sha):
    environment, hosts = extract_dewey(compose_bytes)
    # UniqueLoader retains SafeLoader's prohibition on Python object construction.
    config = yaml.load(config_bytes, Loader=UniqueLoader)  # nosec B506
    require(isinstance(config, dict), "Dewey YAML root must be a mapping")
    application = config.get("application")
    require(isinstance(application, dict), "Dewey application mapping required")
    primary = application.get("api_bearer_token")
    require(isinstance(primary, str) and primary.strip(), "Explicit YAML primary token required")
    deployed_primary = environment["DEWEY_API_BEARER_TOKEN"]
    require(deployed_primary.strip(), "Explicit deployed environment primary token required")
    require(deployed_primary != "dewey-dev-token", "Development primary token forbidden")
    overrides = isolated_overrides(lane, image_sha)
    require(not (REQUIRED_PRESERVED & overrides.keys()), "Preserved environment override forbidden")
    result = {**environment, **overrides}
    env_bytes = "".join(f"{key}={value}\n" for key, value in sorted(result.items())).encode()
    host_bytes = "".join(f"--add-host={item}\n" for item in hosts).encode()
    receipt = {
        "status": "prepared",
        "lane": lane,
        "prepared_at": datetime.now(UTC).isoformat(),
        "compose_sha256": sha256(compose_bytes),
        "dewey_config_sha256": sha256(config_bytes),
        "image_sha": image_sha,
        "environment_file_sha256": sha256(env_bytes),
        "extra_hosts_file_sha256": sha256(host_bytes),
        "environment_keys": sorted(result),
        "preserved_keys": sorted(environment.keys() - overrides.keys()),
        "overridden_keys": sorted(environment.keys() & overrides.keys()),
        "added_keys": sorted(overrides.keys() - environment.keys()),
        "yaml_primary_matches_deployed_environment": deployed_primary == primary,
        "general_bearer_selector": "DEWEY_API_BEARER_TOKEN (effective primary)",
        "extra_hosts": hosts,
    }
    return env_bytes, host_bytes, receipt


def write_new(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose", type=Path, required=True)
    parser.add_argument("--dewey-config", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(DIRECTORIES), required=True)
    parser.add_argument("--image-sha", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_image_sha(args.lane, args.image_sha)
        require(args.compose == COMPOSE_PATH, "Wrong owning Compose path")
        require(
            str(args.dewey_config) == DIRECTORIES[args.lane] + "/dewey-config.yaml",
            "Wrong lane application config",
        )
        compose_bytes = exact_file(args.compose)
        require(sha256(compose_bytes) == COMPOSE_SHA256, "Owning Compose hash changed")
        config_bytes = exact_file(args.dewey_config, private=True)
        env_bytes, host_bytes, receipt = prepare_payloads(
            compose_bytes, config_bytes, args.lane, args.image_sha
        )
        directory = args.output_dir
        require(
            directory.is_absolute() and directory.is_dir(), "Existing output directory required"
        )
        require(directory.resolve() == directory, "Canonical output directory required")
        require(directory.stat().st_mode & 0o077 == 0, "Private output directory required")
        paths = [directory / name for name in ("runtime.env", "extra-hosts.args", "receipt.json")]
        require(
            not any(path.exists() or path.is_symlink() for path in paths), "Output already exists"
        )
        require(
            args.compose.read_bytes() == compose_bytes, "Owning Compose changed while preparing"
        )
        require(
            args.dewey_config.read_bytes() == config_bytes, "Dewey YAML changed while preparing"
        )
        receipt["preparation_script_sha256"] = sha256(Path(__file__).read_bytes())
        for path, content in zip(
            paths,
            (
                env_bytes,
                host_bytes,
                (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode(),
            ),
            strict=True,
        ):
            write_new(path, content)
        print(json.dumps({"status": "prepared", "receipt": str(paths[-1])}))
        return 0
    except Exception as exc:
        payload = {"status": "failed", "error_class": type(exc).__name__}
        if isinstance(exc, PreparationError):
            payload["reason"] = str(exc)
        print(json.dumps(payload))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
