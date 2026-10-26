"""Deploy the final readiness correction to Dewey only, without DB conversion."""
import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import time

import yaml

ROOT = Path("/home/ubuntu/dewey-sharing-20261004T000136Z")
spec = importlib.util.spec_from_file_location("recorded_cutover", ROOT / "20261004T000136Z_dewey_sharing_cutover.py")
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
PREDECESSOR = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:31ed96826facacfa6230793a5e77e2f742185c058837f9960797c9133981bc30"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-receipt", type=Path, required=True)
    args = parser.parse_args()
    ops.require(pwd.getpwuid(os.getuid()).pw_name == "ubuntu", "Run as ubuntu")
    ops.require(subprocess.check_output(["sudo", "tailscale", "ip", "-4"], text=True).strip() == "100.71.233.11", "Unexpected host")
    ops.require(args.image_receipt.is_absolute(), "Absolute image receipt required")
    image = json.loads(args.image_receipt.read_text())

    def image_guard():
        ops.require(image["service"] == "dewey" and image["source_tag"] == "11.0.2"
            and image["builder_instance"] == ops.INSTANCE and re.fullmatch(r"[a-f0-9]{40}", image["source_commit"]), "Unexpected corrected release")
        ops.require(re.fullmatch(r"108782052779\.dkr\.ecr\.us-west-2\.amazonaws\.com/dayhoff/day/dewey@sha256:[a-f0-9]{64}", image["image"]), "Wrong image namespace")
        observed = json.loads(subprocess.check_output(["sudo", "docker", "image", "inspect", image["image"]]))[0]
        ops.require(image["image"] in observed["RepoDigests"]
            and observed["Config"]["Labels"].get("org.opencontainers.image.revision") == image["source_commit"]
            and observed["Config"]["Labels"].get("org.opencontainers.image.version") == image["source_tag"], "Image provenance mismatch")

    image_guard()
    prior = json.loads((ROOT / "deployment-receipt.json").read_text())
    ops.require(prior["image"] == PREDECESSOR and prior["native_conversion"]["readiness"] == "ready", "Native conversion deployment receipt differs")
    before = ops.containers()
    ops.require(before[ops.NAME] == prior["container"], "Predecessor runtime changed")
    raw_compose, raw_manifest = ops.read(ops.COMPOSE), ops.read(ops.MANIFEST)
    compose, manifest = yaml.safe_load(raw_compose), json.loads(raw_manifest)
    service = compose["services"]["dewey"]
    ops.require(service["image"] == PREDECESSOR and manifest["images"]["dewey"]["image"] == PREDECESSOR, "Configured predecessor differs")
    configs = {}
    for field in ("DEWEY_CONFIG", "TAPDB_CONFIG_PATH"):
        mounts = [v for v in service["volumes"] if isinstance(v, dict) and v.get("target") == service["environment"][field]]
        ops.require(len(mounts) == 1, "Ambiguous configuration mount: " + field)
        configs[mounts[0]["source"]] = ops.digest(ops.read(mounts[0]["source"]))
    service["image"] = image["image"]
    service["environment"].update(DEWEY_BUILD_SHA=image["source_commit"], LSMC_RELEASE_SHA=image["source_commit"], DEWEY_BUILD_BRANCH=image["source_branch"])
    manifest["images"]["dewey"].update(image=image["image"], source_commit=image["source_commit"], source_tag=image["source_tag"])
    root = ROOT / "readiness-release-11.0.2"
    root.mkdir(mode=0o700)
    ops.private(root / "previous-compose.yml", raw_compose)
    ops.private(root / "previous-manifest.json", raw_manifest)
    ops.private(root / "compose.yml", yaml.safe_dump(compose, sort_keys=False))
    ops.private(root / "manifest.json", manifest)
    candidate = {name: ops.digest((root / name).read_bytes()) for name in ("compose.yml", "manifest.json")}
    script_sha256 = ops.digest(Path(__file__).read_bytes())
    ops.private(root / "preparation.json", {"prepared_at": ops.now(), "image": image, "containers_before": before,
        "candidate_sha256": candidate, "live_config_sha256": configs, "script_sha256": script_sha256, "native_conversion_repeated": False})

    def guard(*, installed=False):
        image_guard()
        ops.require(ops.digest(Path(__file__).read_bytes()) == script_sha256, "Execution helper changed")
        for name, expected in candidate.items():
            ops.require(ops.digest((root / name).read_bytes()) == expected, "Candidate changed: " + name)
        for path, expected in configs.items():
            ops.require(ops.digest(ops.read(path)) == expected, "Live configuration changed: " + path)
        ops.require(ops.digest(ops.read(ops.COMPOSE)) == (candidate["compose.yml"] if installed else ops.digest(raw_compose)), "Compose changed")
        ops.require(ops.digest(ops.read(ops.MANIFEST)) == (candidate["manifest.json"] if installed else ops.digest(raw_manifest)), "Manifest changed")

    guard()
    ops.require(ops.containers() == before, "Runtime changed before drain")
    started = ops.now()
    stop = subprocess.Popen(["sudo", "docker", "stop", "--signal", "SIGTERM", "--timeout", "-1", before[ops.NAME]["id"]], stdout=subprocess.DEVNULL)
    deadline = time.monotonic() + 120
    while True:
        state = json.loads(subprocess.check_output(["sudo", "docker", "inspect", before[ops.NAME]["id"]]))[0]["State"]
        if not state["Running"]:
            break
        ops.require(time.monotonic() < deadline, "Graceful drain exceeded120seconds; no force or automatic rollback")
        time.sleep(2)
    ops.require(state["Status"] == "exited" and state["ExitCode"] in (0, 143) and not state["OOMKilled"] and stop.wait(timeout=10) == 0,
        "Worker did not drain normally")
    guard()
    drained = deepcopy(before)
    drained[ops.NAME]["running"] = False
    ops.require(ops.containers() == drained, "Sibling or predecessor changed during drain")
    for name, path in (("compose.yml", ops.COMPOSE), ("manifest.json", ops.MANIFEST)):
        subprocess.run(["sudo", "install", "-m", "0600", str(root / name), str(path)], check=True)
    guard(installed=True)
    ops.logged("readiness-service-start", ["sudo", "docker", "compose", "-p", "dayhoff-day", "-f", str(ops.COMPOSE),
        "up", "-d", "--no-deps", "--pull", "never", "dewey"], timeout=180)
    after = ops.containers()
    ops.require(after[ops.NAME]["image"] == image["image"] and after[ops.NAME]["running"], "New worker not running")
    ops.require({k: v for k, v in after.items() if k != ops.NAME} == {k: v for k, v in before.items() if k != ops.NAME}, "Sibling runtime changed")
    receipt = {"phase": "deployed", "started_at": started, "deployed_at": ops.now(), "tag": image["source_tag"],
        "commit": image["source_commit"], "image": image["image"], "container": after[ops.NAME],
        "native_conversion_repeated": False, "prior_verified_inventory": prior["inventory_sha256"], "force_used": False,
        "sibling_containers_unchanged": True, "tests_run": False, "user_acceptance": "pending"}
    ops.private(root / "deployment-receipt.json", receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
