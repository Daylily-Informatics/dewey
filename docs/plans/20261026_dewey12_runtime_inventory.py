#!/usr/bin/env python3
"""Read-only selected-release inventory. Never print environment secrets/config contents."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


def run(*args):
    return subprocess.check_output(args, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compose", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.compose, args.manifest):
        if not path.is_absolute() or not path.is_file():
            parser.error("Explicit existing absolute paths required")
    ids = run("docker", "ps", "--filter", "label=com.docker.compose.project=dayhoff-day", "-q").split()
    containers = []
    for item in json.loads(run("docker", "inspect", *ids)):
        image = json.loads(run("docker", "image", "inspect", item["Image"]))[0]
        labels = image["Config"].get("Labels") or {}
        containers.append({"name": item["Name"].lstrip("/"), "id": item["Id"], "image_id": item["Image"],
            "configured_image": item["Config"]["Image"], "repo_digests": image.get("RepoDigests", []),
            "started_at": item["State"]["StartedAt"], "restart_count": item["RestartCount"],
            "version": labels.get("org.opencontainers.image.version"),
            "source_revision": labels.get("org.opencontainers.image.revision")})
    compose = yaml.safe_load(args.compose.read_text())
    selected = {}
    hashes = {}
    for name in ("dewey", "login"):
        service = compose["services"][name]
        volumes = service.get("volumes", [])
        selected[name] = {"image": service["image"], "volumes": volumes,
            "extra_hosts": service.get("extra_hosts"), "network_mode": service.get("network_mode")}
        for volume in volumes:
            source = volume.split(":", 1)[0] if isinstance(volume, str) else volume.get("source", "")
            path = Path(source)
            if path.is_file() and path.suffix in {".yaml", ".yml"}:
                hashes[source] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps({"observed_at": datetime.now(timezone.utc).isoformat(), "containers": containers,
        "selected_compose": selected, "config_sha256": hashes,
        "manifest": json.loads(args.manifest.read_text()),
        "compose_sha256": hashlib.sha256(args.compose.read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
