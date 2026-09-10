"""Approved one-shot Dewey-only deployment. Run as targeted sudo from Ubuntu.

Default is read-only preflight. --apply replaces only Dewey, then promotes only
services.dewey after health succeeds. No builds, shared-unit calls or DB commands.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

BASE = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
BASE_SHA = "b2a9c0977e125c628c970a294235ee2fc590acc0a4af6e9b7022177aea58ea8a"
OLD_CONTAINER = "4b66bc39c7ef63980c6d7a164c15298524992dcfa4421f988ac7ea5f91d12dc2"
REPOSITORY = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
OLD_IMAGE = REPOSITORY + "@sha256:0780a42dd2b3d5620de2c538cada32acd661f5be5a0f0b60a08c9f941ea3af42"


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, text=True, capture_output=True, **kwargs).stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def private_write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def replace_dewey(base, service):
    text = base.decode()
    before = yaml.safe_load(text)
    tree = yaml.compose(text)
    mappings = [v for k, v in tree.value if k.value == "services"]
    if len(mappings) != 1 or mappings[0].flow_style:
        raise ValueError("Expected exactly one block services mapping")
    pairs = [(k, v) for k, v in mappings[0].value if k.value == "dewey"]
    if len(pairs) != 1:
        raise ValueError("Expected exactly one Dewey entry")
    key, value = pairs[0]
    if key.start_mark.column != 2 or value.flow_style:
        raise ValueError("Unexpected generated Compose layout")
    start = text.rfind("\n", 0, key.start_mark.index) + 1
    end = value.end_mark.index
    line_start = text.rfind("\n", 0, end) + 1
    if not text[line_start:end].strip():
        end = line_start
    block = yaml.safe_dump({"dewey": service}, sort_keys=False)
    replacement = "".join("  " + line if line.strip() else line for line in block.splitlines(True))
    result = (text[:start] + replacement + text[end:]).encode()
    expected = copy.deepcopy(before)
    expected["services"]["dewey"] = service
    if yaml.safe_load(result) != expected:
        raise ValueError("Generated change touched another service or global setting")
    return result


def siblings():
    ids = run(
        ["docker", "ps", "-q", "--filter", "label=com.docker.compose.project=dayhoff-day"]
    ).split()
    rows = json.loads(run(["docker", "inspect", *ids]))
    return {
        d["Config"]["Labels"]["com.docker.compose.service"]: {
            "id": d["Id"],
            "image": d["Image"],
            "started": d["State"]["StartedAt"],
        }
        for d in rows
        if d["Config"]["Labels"]["com.docker.compose.service"] != "dewey"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--release-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(re.escape(REPOSITORY) + r"@sha256:[0-9a-f]{64}", args.image):
        raise ValueError("Exact Dewey repository digest required")
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise ValueError("Exact source commit required")
    expected_dir = Path("/opt/dewey/day/releases/qeo-resolver-" + args.source_commit[:12])
    if args.release_dir != expected_dir or args.release_dir.exists():
        raise ValueError("Expected a new exact Dewey release directory")
    if BASE.is_symlink():
        raise ValueError("Compose symlink is forbidden")
    base = BASE.read_bytes()
    base_stat = BASE.stat()
    if digest(base) != BASE_SHA:
        raise ValueError("Reviewed base Compose changed; no mutation")
    old = json.loads(run(["docker", "inspect", "dayhoff-day-dewey-1"]))[0]
    if (
        old["Id"] != OLD_CONTAINER
        or old["Config"]["Image"] != OLD_IMAGE
        or not old["State"]["Running"]
    ):
        raise ValueError("Reviewed Dewey container changed; no mutation")
    before_siblings = siblings()
    if len(before_siblings) != 11:
        raise ValueError("Expected 11 running sibling services")
    print(
        json.dumps(
            {
                "preflight": "success",
                "apply": args.apply,
                "source": args.source_commit,
                "image": args.image,
                "base_sha256": BASE_SHA,
                "siblings": len(before_siblings),
            }
        ),
        flush=True,
    )
    if not args.apply:
        return

    # Pull only; no docker build can be executed by this helper.
    password = run(
        [
            "sudo",
            "-u",
            "ubuntu",
            "-H",
            "/usr/local/bin/aws",
            "ecr",
            "get-login-password",
            "--region",
            "us-west-2",
            "--profile",
            "lsmc",
            "--no-cli-pager",
        ]
    )
    run(
        ["docker", "login", "--username", "AWS", "--password-stdin", REPOSITORY.split("/")[0]],
        input=password,
    )
    del password
    run(["docker", "pull", args.image])
    image = json.loads(run(["docker", "image", "inspect", args.image]))[0]
    if (
        image["Architecture"] != "amd64"
        or image["Config"]["Labels"].get("org.opencontainers.image.revision") != args.source_commit
    ):
        raise ValueError("Pulled image does not match reviewed source/platform")
    args.release_dir.mkdir(parents=True, mode=0o700)
    private_write(args.release_dir / "boot-before.yml", base)
    private_write(args.release_dir / "siblings-before.json", json.dumps(before_siblings).encode())
    # Preserve existing writable-layer temporary artifacts before Compose replaces Dewey.
    run(["docker", "cp", OLD_CONTAINER + ":/tmp", str(args.release_dir / "old-container-tmp")])

    credential = json.loads(
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--user",
                "0:0",
                "--entrypoint",
                "dewey",
                "--tmpfs",
                "/tmp:rw,mode=1777",
                "-e",
                "DEWEY_DEPLOYMENT_CODE=day",
                "-e",
                "XDG_CONFIG_HOME=/tmp/dewey/config",
                "-e",
                "XDG_DATA_HOME=/tmp/dewey/data",
                "-e",
                "XDG_STATE_HOME=/tmp/dewey/state",
                "-e",
                "XDG_CACHE_HOME=/tmp/dewey/cache",
                "-v",
                str(args.release_dir) + ":/operator-output:rw",
                args.image,
                "--json",
                "qeo",
                "resolver-credential-create",
                "--token-output-file",
                "/operator-output/resolver.token",
                "--lifetime-days",
                "90",
            ]
        )
    )
    private_write(args.release_dir / "credential-receipt.json", json.dumps(credential).encode())
    service = copy.deepcopy(yaml.safe_load(base)["services"]["dewey"])
    if service["image"] != OLD_IMAGE:
        raise ValueError("Boot image differs from reviewed live image")
    service["image"] = args.image
    service["environment"].update(
        {
            "DEWEY_QEO_RESOLVER_TOKEN_SHA256": credential["token_sha256"],
            "DEWEY_QEO_RESOLVER_TOKEN_EXPIRES_AT": credential["expires_at"],
            "LSMC_RELEASE_SHA": args.source_commit,
        }
    )
    candidate = replace_dewey(base, service)
    candidate_file = args.release_dir / "docker-compose.yml"
    private_write(candidate_file, candidate)
    run(["docker", "compose", "-p", "dayhoff-day", "-f", str(candidate_file), "config", "--quiet"])
    if BASE.read_bytes() != base or siblings() != before_siblings:
        raise ValueError("Host state changed before deployment; no container replacement")
    print(
        json.dumps({"phase": "replace_dewey", "backup": str(args.release_dir / "boot-before.yml")}),
        flush=True,
    )
    run(
        [
            "docker",
            "compose",
            "-p",
            "dayhoff-day",
            "-f",
            str(candidate_file),
            "up",
            "-d",
            "--no-deps",
            "--no-build",
            "--pull",
            "never",
            "dewey",
        ]
    )

    # Poll only Dewey's read-only health endpoint. Do not run any bootstrap command.
    health = None
    for _ in range(30):
        try:
            request = urllib.request.Request(
                "http://127.0.0.1:8914/healthz", headers={"Host": "dewey.day.lsmc.bio"}
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.status == 200:
                    health = json.loads(response.read())
                    break
        except (OSError, ValueError):
            pass
        time.sleep(2)
    if health is None:
        raise RuntimeError(
            "Dewey health did not pass; boot base unmodified, backup retained. Inspect before rollback."
        )
    new = json.loads(run(["docker", "inspect", "dayhoff-day-dewey-1"]))[0]
    if new["Config"]["Image"] != args.image or not new["State"]["Running"]:
        raise ValueError("Running Dewey is not the reviewed candidate")
    if (
        siblings() != before_siblings
        or BASE.read_bytes() != base
        or BASE.stat().st_ino != base_stat.st_ino
    ):
        raise ValueError("Sibling/base state changed; boot file not promoted")
    temp = BASE.with_name(".dewey-qeo-resolver-" + args.source_commit[:12] + ".tmp")
    private_write(temp, candidate)
    os.chown(temp, base_stat.st_uid, base_stat.st_gid)
    os.chmod(temp, stat.S_IMODE(base_stat.st_mode))
    os.replace(temp, BASE)
    directory = os.open(BASE.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    if BASE.read_bytes() != candidate:
        raise ValueError("Boot file post-write verification failed; retain backups")
    receipt = {
        "status": "success",
        "source_commit": args.source_commit,
        "image": args.image,
        "container_id": new["Id"],
        "changed_path": "services.dewey",
        "base_before_sha256": BASE_SHA,
        "base_after_sha256": digest(BASE.read_bytes()),
        "siblings_unchanged": siblings() == before_siblings,
        "health": health,
        "release_dir": str(args.release_dir),
        "resolver_token_reference": str(args.release_dir / "resolver.token"),
        "resolver_expires_at": credential["expires_at"],
        "shared_unit_invoked": False,
        "aurora_configuration_changed": False,
    }
    private_write(
        args.release_dir / "deployment-receipt.json", json.dumps(receipt, indent=2).encode()
    )
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
