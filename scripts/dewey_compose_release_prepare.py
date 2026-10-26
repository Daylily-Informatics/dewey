#!/usr/bin/env python3
"""Prepare a private, reviewable Dewey-only production Compose replacement."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

import yaml


IMAGE_REPOSITORY = (
    "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
)
SOURCE_URL = "https://github.com/lsmc-bio/dewey.git"
RELEASE_VERSION = "9.0.0"
COMPOSE_PATH = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
MANIFEST_PATH = Path("/opt/dayhoff/deployments/day/container-release-manifest.json")
EXPECTED_COMPOSE_SHA256 = (
    "35a37f2c5df1cc84ebfd57ad19a9d56b14f88b3e6bc322aebadd3db081da8509"
)
EXPECTED_MANIFEST_SHA256 = (
    "b958136a7b15492042cb6b7e06023b63cb164daf5ff8532950b3ebe8c6bc3cd2"
)
EXPECTED_NON_DEWEY_MANIFEST_SHA256 = (
    "c788b60baa92c05b2daa99ce7abd3303017e63c0434c70f6eaadd88bd200d31e"
)
EXPECTED_TEMPLATE_SHA256 = (
    "131aaf7747aa976ea5db103c81e060f4a2c8ab3f1bed7c24be9b12bbd57406ed"
)
EXPECTED_ENVIRONMENT_PREPARER_SHA256 = (
    "528d963b9da6a4c56688be48248f29c837d2723d34dc34c6475ba630993600dc"
)
EXPECTED_EXTRA_HOSTS = [
    "login.day.lsmc.bio:127.0.0.1",
    "atlas.day.lsmc.bio:127.0.0.1",
    "bloom.day.lsmc.bio:127.0.0.1",
    "ursa.day.lsmc.bio:127.0.0.1",
    "dewey.day.lsmc.bio:127.0.0.1",
    "qeo.day.lsmc.bio:127.0.0.1",
    "zebra-day.day.lsmc.bio:127.0.0.1",
    "kahlo.day.lsmc.bio:127.0.0.1",
]
DISPATCH_KEYS = (
    "DEWEY_QEO_INGEST_URL",
    "DEWEY_QEO_API_TOKEN",
    "DEWEY_QEO_CONSUMER_GROUP",
)
FINAL_ENVIRONMENT = {
    "HOST": "0.0.0.0",
    "DEWEY_HOST": "0.0.0.0",
    "PORT": "8914",
    "DEWEY_PORT": "8914",
    "DEWEY_CONFIG": "/opt/dewey/day/releases/9.0.0/dewey-config.yaml",
    "TAPDB_CONFIG_PATH": "/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml",
    "DEWEY_EXECUTION_BACKEND": "dewey-container",
    "DEWEY_DEPLOYMENT_CODE": "day",
    "DEWEY_ENVIRONMENT": "production",
    "DEWEY_DATABASE_TARGET": "aurora",
    "DEWEY_TAPDB_CLIENT_ID": "dewey",
    "DEWEY_TAPDB_DATABASE_NAME": "dewey-day",
    "DEWEY_TAPDB_DOMAIN_CODE": "M",
    "DEWEY_TAPDB_OWNER_REPO_NAME": "dewey",
    "XDG_STATE_HOME": "/run/dewey-production-state/state",
    "XDG_CACHE_HOME": "/run/dewey-production-state/cache",
    "DEWEY_LITERATURE_METAPUB_CACHE_DIR": "/run/dewey-production-state/metapub",
}
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
ENV_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
SAFE_PATH_RE = re.compile(r"/[A-Za-z0-9._/-]+\Z")


class PreparationError(RuntimeError):
    pass


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate and merged mappings in deployment YAML."""


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise PreparationError("YAML merge keys are unsupported")
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in result:
            raise PreparationError("duplicate or nonstring YAML mapping key")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def require_regular_private_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise PreparationError(f"{label} must be an existing regular file: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise PreparationError(f"{label} must not grant group/other permissions: {path}")


def require_private_directory(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise PreparationError(f"{label} must be an existing directory: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise PreparationError(f"{label} must not grant group/other permissions: {path}")
    if path.resolve() != path:
        raise PreparationError(f"{label} must use its canonical path: {path}")


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreparationError(f"Cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreparationError(f"{label} root must be an object")
    return value


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.load(  # nosec B506
            path.read_text(encoding="utf-8"), Loader=UniqueLoader
        )
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PreparationError(f"Cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreparationError(f"{label} root must be a mapping")
    return value


def parse_runtime_environment(path: Path) -> dict[str, str]:
    require_regular_private_file(path, "runtime environment")
    environment: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or "=" not in line:
            raise PreparationError(
                f"runtime environment line {line_number} must be KEY=value"
            )
        key, value = line.split("=", 1)
        if not ENV_KEY_RE.fullmatch(key):
            raise PreparationError(
                f"runtime environment line {line_number} has invalid key"
            )
        if key in environment:
            raise PreparationError(f"runtime environment repeats key: {key}")
        if "\x00" in value or "\r" in value:
            raise PreparationError(f"runtime environment has invalid value for: {key}")
        environment[key] = value
    if not environment:
        raise PreparationError("runtime environment must not be empty")
    return environment


def parse_extra_hosts(path: Path) -> list[str]:
    require_regular_private_file(path, "extra-hosts file")
    prefix = "--add-host="
    lines = path.read_text(encoding="utf-8").splitlines()
    if any(not line.startswith(prefix) for line in lines):
        raise PreparationError("extra-hosts file contains a non --add-host line")
    return [line.removeprefix(prefix) for line in lines]


def restore_deployed_dispatch(
    isolated_environment: dict[str, str], deployed_environment: dict[str, Any]
) -> tuple[dict[str, str], dict[str, str]]:
    """Remove isolated blanks or restore exact deployed dispatch values."""
    result = dict(isolated_environment)
    projection: dict[str, str] = {}
    for key in DISPATCH_KEYS:
        if key in deployed_environment:
            value = deployed_environment[key]
            if not isinstance(value, str):
                raise PreparationError(f"deployed dispatch value must be a string: {key}")
            result[key] = value
            projection[key] = "restored_from_owning_compose"
        else:
            result.pop(key, None)
            projection[key] = "removed_isolated_override"
    return result, projection


def validate_path(value: str, label: str) -> Path:
    if (
        not SAFE_PATH_RE.fullmatch(value)
        or value == "/"
        or "//" in value
        or any(part in {".", ".."} for part in Path(value).parts)
    ):
        raise PreparationError(f"{label} must be a safe absolute path")
    return Path(value)


def write_private(path: Path, payload: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--runtime-environment", required=True)
    parser.add_argument("--runtime-environment-receipt", required=True)
    parser.add_argument("--extra-hosts", required=True)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compose_path = Path(args.compose)
    manifest_path = Path(args.manifest)
    environment_path = Path(args.runtime_environment)
    environment_receipt_path = Path(args.runtime_environment_receipt)
    extra_hosts_path = Path(args.extra_hosts)
    state_dir = validate_path(args.state_dir, "state directory")
    output_dir = validate_path(args.output_dir, "output directory")

    if not SHA_RE.fullmatch(args.release_sha):
        raise PreparationError("release SHA must be 40 lowercase hexadecimal characters")
    if not DIGEST_RE.fullmatch(args.image_digest):
        raise PreparationError("image digest must be sha256:<64 lowercase hex>")
    if output_dir.exists() or output_dir.is_symlink():
        raise PreparationError(f"output directory must be absent: {output_dir}")
    require_private_directory(state_dir, "state directory")
    require_private_directory(output_dir.parent, "output parent directory")
    if compose_path != COMPOSE_PATH:
        raise PreparationError(f"Compose input must be {COMPOSE_PATH}")
    if manifest_path != MANIFEST_PATH:
        raise PreparationError(f"manifest input must be {MANIFEST_PATH}")
    if compose_path.is_symlink() or not compose_path.is_file():
        raise PreparationError(f"Compose input must be a regular file: {compose_path}")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PreparationError(f"manifest input must be a regular file: {manifest_path}")
    if sha256_file(compose_path) != EXPECTED_COMPOSE_SHA256:
        raise PreparationError("canonical Compose checksum differs from reviewed input")
    if sha256_file(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise PreparationError("release manifest checksum differs from reviewed input")

    environment = parse_runtime_environment(environment_path)
    extra_hosts = parse_extra_hosts(extra_hosts_path)
    require_regular_private_file(environment_receipt_path, "environment receipt")
    environment_receipt = read_json(environment_receipt_path, "environment receipt")
    if environment_receipt.get("status") != "prepared":
        raise PreparationError("environment receipt status must be prepared")
    if environment_receipt.get("lane") != "production":
        raise PreparationError("environment receipt lane must be production")
    if environment_receipt.get("compose_sha256") != EXPECTED_COMPOSE_SHA256:
        raise PreparationError("environment receipt Compose checksum mismatch")
    if environment_receipt.get("environment_file_sha256") != sha256_file(
        environment_path
    ):
        raise PreparationError("runtime environment checksum mismatch")
    if environment_receipt.get("extra_hosts_file_sha256") != sha256_file(
        extra_hosts_path
    ):
        raise PreparationError("extra-hosts checksum mismatch")
    receipt_environment_keys = environment_receipt.get("environment_keys")
    if (
        not isinstance(receipt_environment_keys, list)
        or not all(isinstance(key, str) for key in receipt_environment_keys)
        or sorted(receipt_environment_keys) != sorted(environment)
    ):
        raise PreparationError("environment receipt key inventory mismatch")
    if extra_hosts != EXPECTED_EXTRA_HOSTS:
        raise PreparationError("extra-hosts file differs from reviewed eight-host list")
    if environment_receipt.get("extra_hosts") != EXPECTED_EXTRA_HOSTS:
        raise PreparationError("environment receipt extra-host inventory mismatch")
    if (
        environment_receipt.get("preparation_script_sha256")
        != EXPECTED_ENVIRONMENT_PREPARER_SHA256
    ):
        raise PreparationError("environment preparer checksum mismatch")
    if environment_receipt.get("image_sha") != args.release_sha:
        raise PreparationError("environment receipt image SHA mismatch")
    if environment_receipt.get("general_bearer_selector") != (
        "DEWEY_API_BEARER_TOKEN (effective primary)"
    ):
        raise PreparationError("environment receipt bearer selector mismatch")
    if not isinstance(
        environment_receipt.get("yaml_primary_matches_deployed_environment"), bool
    ):
        raise PreparationError("environment receipt YAML comparison must be boolean")

    template_path = (
        Path(__file__).resolve().parents[1]
        / "docs/plans/evidence/20260911_dewey_900_deployment_capsule"
        / "dewey-service.yaml.template"
    )
    if sha256_file(template_path) != EXPECTED_TEMPLATE_SHA256:
        raise PreparationError("service template checksum differs from reviewed input")
    service = read_yaml(template_path, "service template")
    if service.get("image") != "@@IMAGE_REFERENCE@@":
        raise PreparationError("service template image marker mismatch")
    volumes = service.get("volumes")
    if not isinstance(volumes, list) or not volumes:
        raise PreparationError("service template volumes must be a nonempty list")
    state_volume = volumes[-1]
    if not isinstance(state_volume, dict) or state_volume.get("source") != "@@STATE_DIRECTORY@@":
        raise PreparationError("service template state-directory marker mismatch")

    environment.update(FINAL_ENVIRONMENT)
    environment["DEWEY_BUILD_SHA"] = args.release_sha
    environment["LSMC_RELEASE_SHA"] = args.release_sha
    service["image"] = f"{IMAGE_REPOSITORY}@{args.image_digest}"
    service["extra_hosts"] = extra_hosts
    state_volume["source"] = str(state_dir)

    compose = read_yaml(compose_path, "canonical Compose")
    if compose.get("name") != "dayhoff-day":
        raise PreparationError("canonical Compose project name must be dayhoff-day")
    services = compose.get("services")
    if not isinstance(services, dict) or "dewey" not in services:
        raise PreparationError("canonical Compose must contain services.dewey")
    deployed_service = services["dewey"]
    if not isinstance(deployed_service, dict):
        raise PreparationError("canonical services.dewey must be a mapping")
    deployed_environment = deployed_service.get("environment")
    if not isinstance(deployed_environment, dict):
        raise PreparationError("canonical Dewey environment must be a mapping")
    environment, dispatch_projection = restore_deployed_dispatch(
        environment, deployed_environment
    )
    service["environment"] = environment
    non_dewey_services_sha256 = canonical_sha256(
        {key: value for key, value in services.items() if key != "dewey"}
    )
    services["dewey"] = service
    if canonical_sha256(
        {key: value for key, value in services.items() if key != "dewey"}
    ) != non_dewey_services_sha256:
        raise PreparationError("non-Dewey Compose services changed during preparation")

    manifest = read_json(manifest_path, "release manifest")
    images = manifest.get("images")
    if not isinstance(images, dict) or "dewey" not in images:
        raise PreparationError("release manifest must contain images.dewey")
    non_dewey_images = {key: value for key, value in images.items() if key != "dewey"}
    if canonical_sha256(non_dewey_images) != EXPECTED_NON_DEWEY_MANIFEST_SHA256:
        raise PreparationError("non-Dewey manifest image inventory checksum mismatch")
    images["dewey"] = {
        "image": f"{IMAGE_REPOSITORY}@{args.image_digest}",
        "repository": "dayhoff/day/dewey",
        "source_commit": args.release_sha,
        "source_tag": RELEASE_VERSION,
    }
    if canonical_sha256(
        {key: value for key, value in images.items() if key != "dewey"}
    ) != EXPECTED_NON_DEWEY_MANIFEST_SHA256:
        raise PreparationError("non-Dewey manifest entries changed during preparation")

    service_payload = yaml.safe_dump(service, sort_keys=False).encode()
    compose_payload = yaml.safe_dump(compose, sort_keys=False).encode()
    manifest_payload = (json.dumps(manifest, indent=2) + "\n").encode()
    receipt = {
        "status": "prepared",
        "release_version": RELEASE_VERSION,
        "release_sha": args.release_sha,
        "source_url": SOURCE_URL,
        "image_repository": IMAGE_REPOSITORY,
        "image_digest": args.image_digest,
        "image_reference": f"{IMAGE_REPOSITORY}@{args.image_digest}",
        "source_compose_sha256": EXPECTED_COMPOSE_SHA256,
        "source_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "non_dewey_compose_services_sha256": non_dewey_services_sha256,
        "non_dewey_manifest_images_sha256": EXPECTED_NON_DEWEY_MANIFEST_SHA256,
        "environment_file_sha256": sha256_file(environment_path),
        "environment_preparation_script_sha256": environment_receipt.get(
            "preparation_script_sha256"
        ),
        "environment_yaml_primary_matches_deployed_environment": (
            environment_receipt.get("yaml_primary_matches_deployed_environment")
        ),
        "general_bearer_selector": environment_receipt.get(
            "general_bearer_selector"
        ),
        "environment_keys": sorted(environment),
        "dispatch_isolation_projection": dispatch_projection,
        "state_dir": str(state_dir),
        "restart_policy": "unless-stopped",
        "proxy_change_required": False,
        "boot_unit_change_required": False,
        "promotion_command": (
            "/usr/bin/docker compose -f "
            "/opt/dayhoff/deployments/day/compose/docker-compose.yml "
            "up -d --no-deps --pull never dewey"
        ),
        "rendered_service_sha256": sha256_bytes(service_payload),
        "rendered_compose_sha256": sha256_bytes(compose_payload),
        "rendered_manifest_sha256": sha256_bytes(manifest_payload),
        "service_template_sha256": EXPECTED_TEMPLATE_SHA256,
        "preparation_script_sha256": sha256_file(Path(__file__).resolve()),
    }
    receipt_payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()

    old_umask = os.umask(0o077)
    try:
        output_dir.mkdir(mode=0o700)
        write_private(output_dir / "dewey-service.yaml", service_payload)
        write_private(output_dir / "docker-compose.yml", compose_payload)
        write_private(output_dir / "container-release-manifest.json", manifest_payload)
        write_private(output_dir / "deployment-inputs.json", receipt_payload)
        sums = "".join(
            f"{sha256_file(output_dir / name)}  {name}\n"
            for name in (
                "dewey-service.yaml",
                "docker-compose.yml",
                "container-release-manifest.json",
                "deployment-inputs.json",
            )
        ).encode()
        write_private(output_dir / "SHA256SUMS", sums)
    finally:
        os.umask(old_umask)

    print("prepare_status=prepared")
    print(f"output_dir={output_dir}")
    print(f"image_reference={IMAGE_REPOSITORY}@{args.image_digest}")
    print(f"rendered_compose_sha256={sha256_bytes(compose_payload)}")
    print(f"rendered_manifest_sha256={sha256_bytes(manifest_payload)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreparationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
