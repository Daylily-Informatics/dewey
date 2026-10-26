"""Approved combined Dewey performance cutover; run as ubuntu on designated EC2.

No builds, schema migrations, credential changes or sibling deployment.
Explicit native initialization of the listing-cache setting precedes cutover.
Keep previous files private for deliberate rollback; no automatic rollback occurs.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import time
from urllib.request import ProxyHandler, Request, build_opener

import yaml

INSTANCE = "i-07df3a933e4839f52"
REGION = "us-west-2"
COMPOSE = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
MANIFEST = Path("/opt/dayhoff/deployments/day/container-release-manifest.json")
NAME = "dayhoff-day-dewey-1"
REGISTRY = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
OLD_IMAGE = REGISTRY + "@sha256:50ef1ba6922be663e7c88839849b4a1649590ae8674c819dc8862e695055b7ac"
OLD_COMMIT = "8d04719a6ad82a6808bf38933b39cadb210b43d0"
SERVICE_SHA = "125765623414b9f26e3527454c2bf6c07f2da83e5722c759a4b117d7c975b17d"
MANIFEST_ROW_SHA = "0e5c9471dda8682f2bc61928e3c2d898618ccfedb120e5bae14cb09dcd379649"
TAG = "10.0.10"
BRANCH = "codex/dewey-gui-performance-20260919"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read(path):
    return subprocess.check_output(["sudo", "cat", str(path)])


def save(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def containers():
    ids = subprocess.check_output(["sudo", "docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=dayhoff-day"], text=True).split()
    require(bool(ids), "Native compose containers are missing")
    values = json.loads(subprocess.check_output(["sudo", "docker", "inspect", *ids]))
    return {row["Name"].lstrip("/"): {"id": row["Id"], "image": row["Image"],
        "configured_image": row["Config"]["Image"], "status": row["State"]["Status"],
        "started_at": row["State"]["StartedAt"], "restarts": row["RestartCount"],
        "source_commit": row["Config"].get("Labels", {}).get("org.opencontainers.image.revision"),
        "source_tag": row["Config"].get("Labels", {}).get("org.opencontainers.image.version")}
        for row in values if row["Name"].lstrip("/") != "dewey-performance-settings-10010"}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--image-receipt", type=Path, required=True)
parser.add_argument("--image-receipt-sha256", required=True)
parser.add_argument("--receipt-dir", type=Path, required=True)
parser.add_argument("--commit", required=True)
parser.add_argument("--tag-object", required=True)
args = parser.parse_args()
COMMIT, TAG_OBJECT = args.commit, args.tag_object
require(re.fullmatch(r"[a-f0-9]{40}", COMMIT) and re.fullmatch(r"[a-f0-9]{40}", TAG_OBJECT), "Exact reviewed commit and annotated tag object required")
require(pwd.getpwuid(os.getuid()).pw_name == "ubuntu", "Interactive ubuntu operator required")
require(args.image_receipt.is_absolute() and args.receipt_dir.is_absolute() and not args.receipt_dir.exists(),
        "Explicit existing image receipt and new private receipt directory required")
opener = build_opener(ProxyHandler({}))
with opener.open(Request("http://169.254.169.254/latest/api/token", method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"}), timeout=3) as response:
    token = response.read().decode()
with opener.open(Request("http://169.254.169.254/latest/dynamic/instance-identity/document",
        headers={"X-aws-ec2-metadata-token": token}), timeout=3) as response:
    identity = json.load(response)
require(identity["instanceId"] == INSTANCE and identity["region"] == REGION, "Unexpected deployment instance")
del token
raw_build = args.image_receipt.read_bytes()
require(sha(raw_build) == args.image_receipt_sha256, "Final build receipt changed")
build = json.loads(raw_build)
require(build.get("schema") == "ursa-owy-kahlo.final-image/v1" and build.get("service") == "dewey"
        and build.get("source_tag") == TAG and build.get("source_commit") == COMMIT
        and build.get("source_tag_object") == TAG_OBJECT and build.get("source_branch") == BRANCH
        and build.get("builder_instance") == INSTANCE and build.get("builder_region") == REGION
        and build.get("tests_run") is False and build.get("deployed") is False,
        "Exact reviewed final Dewey release/build required")
image = build["image"]
require(re.fullmatch(re.escape(REGISTRY) + r"@sha256:[a-f0-9]{64}", image), "Immutable Dewey image required")
image_data = json.loads(subprocess.check_output(["sudo", "docker", "image", "inspect", image]))[0]
labels = image_data["Config"]["Labels"]
require(labels.get("org.opencontainers.image.revision") == COMMIT
        and labels.get("org.opencontainers.image.version") == TAG, "Local final image provenance differs")
raw_compose, raw_manifest = read(COMPOSE), read(MANIFEST)
compose, manifest = yaml.safe_load(raw_compose), json.loads(raw_manifest)
old = compose["services"]["dewey"]
require(sha(canonical(old)) == SERVICE_SHA and old["image"] == OLD_IMAGE,
        "Selected Dewey service changed since review")
require(sha(canonical(manifest["images"]["dewey"])) == MANIFEST_ROW_SHA,
        "Selected Dewey recorded release changed since review")
before = containers()
require(before[NAME]["configured_image"] == OLD_IMAGE and before[NAME]["source_commit"] == OLD_COMMIT,
        "Actual current Dewey container differs from the reviewed predecessor")
updated = deepcopy(compose)
candidate = updated["services"]["dewey"]
candidate["image"] = image
candidate["environment"].update(DEWEY_BUILD_SHA=COMMIT, LSMC_RELEASE_SHA=COMMIT, DEWEY_BUILD_BRANCH=BRANCH)
updated_manifest = deepcopy(manifest)
updated_manifest["images"]["dewey"].update(image=image, source_commit=COMMIT, source_tag=TAG)
require({k: v for k, v in updated["services"].items() if k != "dewey"}
        == {k: v for k, v in compose["services"].items() if k != "dewey"}, "Sibling compose change refused")
args.receipt_dir.mkdir(mode=0o700)
save(args.receipt_dir / "previous-compose.yml", raw_compose)
save(args.receipt_dir / "previous-manifest.json", raw_manifest)
save(args.receipt_dir / "containers-before.json", before)
receipt = {"schema": "ursa-owy-kahlo.deployment/v1", "service": "dewey",
    "source_tag": TAG, "source_commit": COMMIT, "source_tag_object": TAG_OBJECT, "source_branch": BRANCH,
    "image": image, "previous_image": OLD_IMAGE, "started_at": now(),
    "builder_receipt": {"path": str(args.image_receipt), "sha256": args.image_receipt_sha256},
    "instance_id": INSTANCE, "phase": "PREPARED", "tests_run": False,
    "database_operations": [], "credential_changes": False, "service_configuration_preserved": True}
save(args.receipt_dir / "start-receipt.json", receipt)
try:
    # Run the owning CLI from the final image, against the preserved service config.
    initialization_compose = args.receipt_dir / "initialization-compose.yml"
    save(initialization_compose, yaml.safe_dump(updated, sort_keys=False).encode())
    init_command = ["sudo", "docker", "compose", "-p", "dayhoff-day", "-f", str(initialization_compose),
        "run", "-T", "--no-deps", "--pull", "never", "--name", "dewey-performance-settings-10010",
        "--entrypoint", "/app/.venv/bin/dewey", "dewey", "db", "initialize-performance-settings",
        "--actor", "codex:dewey-performance-20260923", "--listing-cache-ttl-seconds", "15"]
    initialization = subprocess.run(init_command, capture_output=True, text=True)
    save(args.receipt_dir / "initialization-output.txt", initialization.stdout.encode())
    # stderr is private on-host; never copy environment/config diagnostics to public evidence.
    save(args.receipt_dir / "initialization-stderr.txt", initialization.stderr.encode())
    require(initialization.returncode == 0, "Native settings initialization failed; prior Dewey remains running; inspect private initialization logs")
    receipt["database_operations"] = [{"operation": "dewey db initialize-performance-settings",
        "listing_cache_ttl_seconds": 15, "exit_code": initialization.returncode,
        "receipt": str(args.receipt_dir / "initialization-output.txt")}]
    # Compare complete current files immediately before writing so another
    # selected-service cutover cannot be lost through a stale compose snapshot.
    require(read(COMPOSE) == raw_compose and read(MANIFEST) == raw_manifest, "Concurrent deployment changed native files")
    receipt["phase"] = "GRACEFUL_STOPPING"
    subprocess.run(["sudo", "docker", "stop", "--signal", "SIGTERM", "--timeout", "-1", before[NAME]["id"]], check=True)
    stopped = json.loads(subprocess.check_output(["sudo", "docker", "inspect", before[NAME]["id"]]))[0]
    stopped_state = stopped["State"]
    receipt["predecessor_shutdown"] = {
        "container_id": stopped["Id"], "status": stopped_state["Status"],
        "exit_code": stopped_state["ExitCode"], "oom_killed": stopped_state["OOMKilled"],
        "finished_at": stopped_state["FinishedAt"], "signal": "SIGTERM", "timeout_seconds": -1,
        "force_used": False,
    }
    save(args.receipt_dir / "predecessor-shutdown.json", receipt["predecessor_shutdown"])
    require(stopped_state["Status"] == "exited" and stopped_state["ExitCode"] in (0, 143)
            and stopped_state["OOMKilled"] is False, "Predecessor did not exit normally after SIGTERM")
    require(read(COMPOSE) == raw_compose and read(MANIFEST) == raw_manifest, "Native files changed during graceful shutdown")
    for label, target, value in (
        ("compose", COMPOSE, yaml.safe_dump(updated, sort_keys=False).encode()),
        ("manifest", MANIFEST, (json.dumps(updated_manifest, indent=2) + "\n").encode()),
    ):
        staged = args.receipt_dir / ("selected-" + label)
        save(staged, value)
        temporary = str(target) + ".dewey10010-new"
        subprocess.run(["sudo", "install", "-m", "600", str(staged), temporary], check=True)
        subprocess.run(["sudo", "mv", temporary, str(target)], check=True)
    receipt["phase"] = "CONFIGURATION_SELECTED"
    subprocess.run(["sudo", "docker", "compose", "-p", "dayhoff-day", "-f", str(COMPOSE), "up", "-d", "--no-deps",
                    "--no-build", "--pull", "never", "dewey"], check=True)
    receipt["phase"] = "CONTAINER_REPLACED"
    availability = []
    for attempt in range(12):
        observation = {"observed_at": now()}
        try:
            with opener.open("https://dewey.day.lsmc.bio/healthz", timeout=5) as response:
                body = response.read(65536)
                observation.update(status=response.status, body_sha256=sha(body))
            if observation["status"] == 200:
                availability.append(observation)
                break
        except Exception as error:
            observation["error_type"] = type(error).__name__
        availability.append(observation)
        time.sleep(2)
    receipt["availability"] = availability
    require(availability[-1].get("status") == 200, "Deployed Dewey health did not become available")
    after = containers()
    require(after[NAME]["configured_image"] == image and after[NAME]["source_commit"] == COMMIT
            and after[NAME]["source_tag"] == TAG and after[NAME]["status"] == "running", "Actual deployed source/image differs")
    require({k: v for k, v in before.items() if k != NAME} == {k: v for k, v in after.items() if k != NAME},
            "Sibling runtime changed during selected cutover")
    package = subprocess.check_output(["sudo", "docker", "exec", NAME, "/app/.venv/bin/python", "-c",
        "from importlib.metadata import version;print(version('dewey-service'))"], text=True).strip()
    require(package == TAG, "Installed package version differs from the release")
    runtime = json.loads(subprocess.check_output(["sudo", "docker", "exec", NAME, "/app/.venv/bin/python", "-c",
        "import os,json;print(json.dumps({k:os.environ.get(k) for k in ['DEWEY_BUILD_SHA','LSMC_RELEASE_SHA','DEWEY_BUILD_BRANCH']}))"]))
    require(runtime == {"DEWEY_BUILD_SHA": COMMIT, "LSMC_RELEASE_SHA": COMMIT, "DEWEY_BUILD_BRANCH": BRANCH},
            "Deployed provenance environment differs")
    receipt.update(phase="SUCCESS", observed_at=now(), completed_at=now(), installed_package_version=package,
        runtime_provenance=runtime, containers_before=before, containers_after=after, siblings_unchanged=True,
        compose_sha256=sha(read(COMPOSE)), manifest_sha256=sha(read(MANIFEST)), performance_acceptance=False)
except Exception as error:
    receipt.update(phase="FAIL", failed_at=now(), error_type=type(error).__name__, error=str(error))
    save(args.receipt_dir / "deployment-receipt.json", receipt)
    raise
save(args.receipt_dir / "deployment-receipt.json", receipt)
print(json.dumps({"receipt_path": str(args.receipt_dir / "deployment-receipt.json"),
                  "receipt_sha256": sha((args.receipt_dir / "deployment-receipt.json").read_bytes()), **receipt}, sort_keys=True))
