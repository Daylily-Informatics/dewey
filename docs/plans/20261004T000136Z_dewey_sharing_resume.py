"""Resume the recorded drained cutover with a corrected, final tagged image.

Verify the existing applied epoch; never rerun retirement or template population.
All prior evidence remains immutable. Run interactively as ubuntu on the same EC2.
"""
from copy import deepcopy
import argparse
import importlib.util
import json
from pathlib import Path
import pwd
import os
import re
import subprocess

import yaml

ROOT = Path("/home/ubuntu/dewey-sharing-20261004T000136Z")
spec = importlib.util.spec_from_file_location("recorded_cutover", ROOT / "20261004T000136Z_dewey_sharing_cutover.py")
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)


def image_identity(image):
    original.require(image["service"] == "dewey" and image["builder_instance"] == original.INSTANCE,
        "Unexpected corrected image builder")
    original.require(image["source_tag"] == "11.0.1" and re.fullmatch(r"[a-f0-9]{40}", image["source_commit"]),
        "Expected the immutable corrected 11.0.1 release")
    original.require(re.fullmatch(r"108782052779\.dkr\.ecr\.us-west-2\.amazonaws\.com/dayhoff/day/dewey@sha256:[a-f0-9]{64}", image["image"]),
        "Unexpected corrected image namespace")
    observed = json.loads(subprocess.check_output(["sudo", "docker", "image", "inspect", image["image"]]))[0]
    original.require(image["image"] in observed["RepoDigests"], "Corrected digest not present locally")
    labels = observed["Config"]["Labels"]
    original.require(labels.get("org.opencontainers.image.revision") == image["source_commit"]
        and labels.get("org.opencontainers.image.version") == image["source_tag"], "Corrected image label mismatch")


def drained_predecessor(prepared):
    for path, key in ((original.COMPOSE, "compose"), (original.MANIFEST, "manifest"),
                      (original.APACHE, "proxy"), (original.DNS, "dns")):
        original.require(original.digest(original.read(path)) == prepared[key + "_before_sha256"],
            "Live configuration changed during stopped maintenance: " + key)
    before = json.loads((ROOT / "containers-before.json").read_text())
    expected = deepcopy(before)
    expected[original.NAME]["running"] = False
    original.require(original.containers() == expected, "Drained predecessor or sibling containers changed")
    drain = json.loads((ROOT / "predecessor-drain.json").read_text())
    state = json.loads(subprocess.check_output(["sudo", "docker", "inspect", before[original.NAME]["id"]]))[0]["State"]
    original.require(not state["Running"] and state["Status"] == "exited" and not state["OOMKilled"]
        and state["ExitCode"] == drain["exit_code"] and state["FinishedAt"] == drain["finished_at"]
        and not drain["force_used"], "Exact graceful drain receipt no longer matches")
    return before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-receipt", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    original.require(pwd.getpwuid(os.getuid()).pw_name == "ubuntu", "Run as ubuntu")
    original.require(subprocess.check_output(["sudo", "tailscale", "ip", "-4"], text=True).strip() == "100.71.233.11",
        "Unexpected Tailscale host")
    original.require(args.image_receipt.is_absolute(), "Explicit absolute image receipt required")
    prepared = original.verify_prepared()
    before = drained_predecessor(prepared)
    inventory = json.loads((ROOT / "final-inventory.json").read_text())
    applied = json.loads((ROOT / "upgrade-apply.json").read_text())
    original.require(applied["status"] == "applied" and applied["inventory_sha256"] == args.expected_sha256
        and inventory["inventory_sha256"] == args.expected_sha256 and not inventory["ambiguous"], "Original applied inventory differs")
    original.require(applied["created_since"] == inventory["created_since"], "Applied cutoff differs")
    original.require(original.protected_path_exists(original.CERT), "Content certificate missing")
    image = json.loads(args.image_receipt.read_text())
    image_identity(image)
    original.require(image["image"] != prepared["image"]["image"], "Resume requires the corrected image")

    compose = yaml.safe_load((ROOT / "final-compose.yml").read_text())
    native = yaml.safe_load((ROOT / "native-compose.yml").read_text())
    for service in (compose["services"]["dewey"], native["services"]["dewey"]):
        old_target = service["environment"]["DEWEY_CONFIG"]
        mounts = [v for v in service["volumes"] if isinstance(v, dict) and v.get("target") == old_target]
        original.require(len(mounts) == 1, "Ambiguous corrected configuration mount")
        target = "/opt/dewey/day/releases/11.0.1/dewey-config.yaml"
        mounts[0]["target"] = target
        service["image"] = image["image"]
        service["environment"].update(DEWEY_CONFIG=target, DEWEY_BUILD_SHA=image["source_commit"],
            LSMC_RELEASE_SHA=image["source_commit"], DEWEY_BUILD_BRANCH=image["source_branch"])
    manifest = json.loads((ROOT / "final-manifest.json").read_text())
    manifest["images"]["dewey"].update(image=image["image"], source_commit=image["source_commit"], source_tag=image["source_tag"])
    original.private(ROOT / "resume-compose.yml", yaml.safe_dump(compose, sort_keys=False))
    original.private(ROOT / "resume-native-compose.yml", yaml.safe_dump(native, sort_keys=False))
    original.private(ROOT / "resume-manifest.json", manifest)
    candidates = ("resume-compose.yml", "resume-native-compose.yml", "resume-manifest.json")
    resume = {"prepared_at": original.now(), "image": image, "inventory_sha256": args.expected_sha256,
        "original_preparation_sha256": original.digest((ROOT / "final-preparation.json").read_bytes()),
        "script_sha256": original.digest(Path(__file__).read_bytes()),
        "candidate_sha256": {name: original.digest((ROOT / name).read_bytes()) for name in candidates}}
    original.private(ROOT / "resume-preparation.json", resume)

    def guard():
        original.verify_prepared()
        original.require(original.digest((ROOT / "final-preparation.json").read_bytes()) == resume["original_preparation_sha256"],
            "Original prepared receipt changed")
        original.require(original.digest(Path(__file__).read_bytes()) == resume["script_sha256"], "Resume helper changed")
        for name, expected in resume["candidate_sha256"].items():
            original.require(original.digest((ROOT / name).read_bytes()) == expected, "Resume candidate changed: " + name)
        image_identity(image)

    guard()
    original.logged("resume-upgrade-verify", ["sudo", "docker", "compose", "-p", "dewey-sharing-native",
        "-f", str(ROOT / "resume-native-compose.yml"), "run", "-T", "--no-deps", "--pull", "never", "--rm",
        "--entrypoint", "/app/.venv/bin/dewey", "dewey", "db", "upgrade-sharing", "--phase", "verify",
        "--inventory", "/opt/dewey-sharing/final-inventory.json", "--created-since", original.CREATED_SINCE,
        "--expected-sha256", args.expected_sha256, "--receipt", "/opt/dewey-sharing/upgrade-verify-11.0.1.json",
        "--actor", original.ACTOR, "--attribution", "/opt/dewey-sharing/attribution.json"], timeout=180)
    verified = json.loads((ROOT / "upgrade-verify-11.0.1.json").read_text())
    original.require(verified["status"] == "verified" and verified["readiness"] == "ready"
        and verified["inventory_sha256"] == args.expected_sha256, "Native verification is not complete")
    for key in ("share_count", "eligible_share_count", "retire_before_cutoff_count"):
        original.require(verified[key] == applied[key], "Native disposition changed: " + key)
    guard()
    drained_predecessor(prepared)
    for source, target in (("resume-compose.yml", original.COMPOSE), ("resume-manifest.json", original.MANIFEST),
                          ("final-proxy.conf", original.APACHE), ("content-proxy.conf", original.CONTENT), ("final-dns.conf", original.DNS)):
        subprocess.run(["sudo", "install", "-m", "0600", str(ROOT / source), str(target)], check=True)
    subprocess.run(["sudo", "ln", "-s", str(original.CONTENT), "/etc/apache2/sites-enabled/dewey-content-day.conf"], check=True)
    original.logged("resume-apache-configuration", ["sudo", "apache2ctl", "configtest"])
    original.logged("resume-dns-configuration", ["sudo", "dnsmasq", "--test", "--conf-file=" + str(original.DNS)])
    guard()
    original.logged("resume-service-start", ["sudo", "docker", "compose", "-p", "dayhoff-day", "-f", str(original.COMPOSE),
        "up", "-d", "--no-deps", "--pull", "never", "dewey"], timeout=180)
    original.logged("resume-proxy-reload", ["sudo", "systemctl", "reload", "apache2"], timeout=60)
    original.logged("resume-dns-reload", ["sudo", "systemctl", "restart", "dayhoff-day-lsmc-bio-dnsmasq"], timeout=60)
    after = original.containers()
    original.require(after[original.NAME]["image"] == image["image"] and after[original.NAME]["running"], "New worker identity mismatch")
    original.require({k: v for k, v in after.items() if k != original.NAME}
        == {k: v for k, v in before.items() if k != original.NAME}, "Sibling runtime changed")
    receipt = {"phase": "deployed", "deployed_at": original.now(), "tag": image["source_tag"], "commit": image["source_commit"],
        "image": image["image"], "container": after[original.NAME], "inventory_sha256": args.expected_sha256,
        "native_conversion": verified, "retirement_reapplied": False, "sibling_containers_unchanged": True,
        "superseded_image": prepared["image"]["image"], "tests_run": False, "user_acceptance": "pending"}
    original.private(ROOT / "deployment-receipt.json", receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
