"""Prepare a private native-CLI inventory capsule on the confirmed EC2 host.

No database mutation, service cutover, image build, or credential output.
The existing published image supplies dependencies for the staged CLI inventory.
Final conversion must use the eventual exact tagged final image.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
from uuid import uuid4

import yaml

ROOT = Path("/home/ubuntu/dewey-sharing-20261004T000136Z")
COMPOSE = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
OLD_IMAGE = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:30b155ab0a3555cd03a8ccbe59c340f8b801331bbe4ea0b64f56e3c473ab7d5a"


def read(path):
    return subprocess.check_output(["sudo", "cat", str(path)])


def private(path, data):
    raw = data if isinstance(data, bytes) else data.encode()
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as handle:
        handle.write(raw)


def main():
    if pwd.getpwuid(os.getuid()).pw_name != "ubuntu":
        raise RuntimeError("Run as ubuntu on the confirmed Dayhoff EC2 host")
    tailnet = subprocess.check_output(["sudo", "tailscale", "ip", "-4"], text=True).strip()
    if tailnet != "100.71.233.11":
        raise RuntimeError("Unexpected host identity")
    if not (ROOT / "source/dewey_service/share_upgrade.py").is_file():
        raise RuntimeError("Explicit staged inventory source is missing")
    original = yaml.safe_load(read(COMPOSE))
    service = deepcopy(original["services"]["dewey"])
    if service["image"] != OLD_IMAGE:
        raise RuntimeError("Reviewed predecessor image changed")
    mounts = service["volumes"]
    env = service["environment"]
    for field, name in (("DEWEY_CONFIG", "dewey-config.yaml"), ("TAPDB_CONFIG_PATH", "tapdb-runtime.yaml")):
        target = env[field]
        matches = [m for m in mounts if isinstance(m, dict) and m.get("target") == target]
        if len(matches) != 1:
            raise RuntimeError("Native configuration mount is ambiguous: " + field)
        private(ROOT / name, read(matches[0]["source"]))
        if field == "TAPDB_CONFIG_PATH":
            # Config identity is part of TapDB's immutable runtime binding.
            matches[0]["source"] = str(ROOT / name)
        else:
            env[field] = "/opt/dewey-sharing/" + name
    operator = Path("/home/ubuntu/dewey_ops/tapdb101-20260911/replacement-operator.yaml")
    private(ROOT / "operator.yaml", read(operator))
    env.update(PYTHONPATH="/opt/dewey-sharing/source", XDG_CONFIG_HOME="/opt/dewey-sharing/config", XDG_STATE_HOME="/opt/dewey-sharing/state",
        XDG_CACHE_HOME="/opt/dewey-sharing/cache", XDG_DATA_HOME="/opt/dewey-sharing/data")
    service["user"] = "1000:1000"
    service["restart"] = "no"
    service["volumes"].append({"type": "bind", "source": str(ROOT), "target": "/opt/dewey-sharing"})
    private(ROOT / "inventory-compose.yml", yaml.safe_dump({"services": {"dewey": service}}, sort_keys=False))
    private(ROOT / "attribution.json", json.dumps({"actor_kind": "service", "actor_issuer": "codex",
        "actor_subject": "codex:dewey-sharing-20261004", "service_identity": "dewey",
        "request_id": str(uuid4()), "operation_id": "sharing-upgrade-20261004",
        "correction_reason": "User-approved Tailscale plus shared Login implementation and native conversion"}, indent=2))
    receipt = {"status": "prepared", "existing_image": OLD_IMAGE,
        "source_manifest_sha256": hashlib.sha256((ROOT / "source-manifest.json").read_bytes()).hexdigest(),
        "production_changed": False, "database_changed": False, "tests_run": False,
        "created_at": datetime.now(timezone.utc).isoformat()}
    private(ROOT / "preparation-receipt.json", json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
