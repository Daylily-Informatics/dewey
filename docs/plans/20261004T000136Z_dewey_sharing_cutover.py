"""Reviewed Dewey-only sharing cutover, run as ubuntu on the confirmed EC2 host.

Phases are explicit. No automatic rollback, tests, sibling deployment or cleanup.
All configuration, native conversion outputs and credentials stay private on host.
"""
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import subprocess
import time
from uuid import uuid4

import yaml

ROOT = Path("/home/ubuntu/dewey-sharing-20261004T000136Z")
COMPOSE = Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
MANIFEST = Path("/opt/dayhoff/deployments/day/container-release-manifest.json")
APACHE = Path("/etc/apache2/sites-available/dewey-day.conf")
CONTENT = Path("/etc/apache2/sites-available/dewey-content-day.conf")
DNS = Path("/etc/dnsmasq.d/dayhoff-day-lsmc-bio.conf")
CERT = "/etc/letsencrypt/live/dewey-content-day"
INSTANCE = "i-07df3a933e4839f52"
NAME = "dayhoff-day-dewey-1"
OLD_IMAGE = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:30b155ab0a3555cd03a8ccbe59c340f8b801331bbe4ea0b64f56e3c473ab7d5a"
ACTOR = "codex:dewey-sharing-20261004"
CREATED_SINCE = "2026-09-27T04:43:55Z"


def now():
    return datetime.now(timezone.utc).isoformat()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return subprocess.check_output(["sudo", "cat", str(path)])


def protected_path_exists(path):
    return json.loads(subprocess.check_output(["sudo", "python3", "-c",
        "import json, os, sys; print(json.dumps(os.path.lexists(sys.argv[1])))", str(path)]))


def private(path, value):
    data = value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else json.dumps(value, indent=2).encode()
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def digest(value):
    return hashlib.sha256(value).hexdigest()


def logged(name, command, *, timeout=None):
    path = ROOT / (name + ".log")
    with path.open("x") as log:
        path.chmod(0o600)
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0, f"{name} failed; inspect private log {path}; no automatic rollback")


def containers():
    ids = subprocess.check_output(["sudo", "docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=dayhoff-day"], text=True).split()
    require(ids, "No deployment containers found")
    return {row["Name"].lstrip("/"): {"id": row["Id"], "image": row["Config"]["Image"],
        "running": row["State"]["Running"]} for row in json.loads(subprocess.check_output(["sudo", "docker", "inspect", *ids]))}


def native(name, args):
    verify_prepared()
    logged(name, ["sudo", "docker", "compose", "-p", "dewey-sharing-native", "-f", str(ROOT / "native-compose.yml"),
        "run", "-T", "--no-deps", "--pull", "never", "--rm", "--entrypoint", "/app/.venv/bin/dewey", "dewey", "db", *args])


def verify_prepared():
    prepared = json.loads((ROOT / "final-preparation.json").read_text())
    for name, expected in prepared["candidate_sha256"].items():
        require(digest((ROOT / name).read_bytes()) == expected, "Prepared candidate changed: " + name)
    for path, expected in prepared["live_config_sha256"].items():
        require(digest(read(path)) == expected, "Live configuration changed after preparation: " + path)
    require(digest(Path(__file__).read_bytes()) == prepared["execution_script_sha256"], "Cutover script changed after preparation")
    image = prepared["image"]
    observed = json.loads(subprocess.check_output(["sudo", "docker", "image", "inspect", image["image"]]))[0]
    require(image["image"] in observed["RepoDigests"], "Final digest is not present in the local image store")
    labels = observed["Config"]["Labels"]
    require(labels.get("org.opencontainers.image.revision") == image["source_commit"]
        and labels.get("org.opencontainers.image.version") == image["source_tag"], "Final image identity changed")
    return prepared


def prepare(image_receipt):
    image = json.loads(image_receipt.read_text())
    require(image["service"] == "dewey" and image["builder_instance"] == INSTANCE, "Unreviewed build receipt")
    require(re.fullmatch(r"108782052779\.dkr\.ecr\.us-west-2\.amazonaws\.com/dayhoff/day/dewey@sha256:[a-f0-9]{64}", image["image"]), "Wrong service image")
    require(re.fullmatch(r"\d+\.\d+\.\d+", image["source_tag"]) and re.fullmatch(r"[a-f0-9]{40}", image["source_commit"]), "Invalid release identity")
    raw_compose, raw_manifest, raw_proxy, raw_dns = read(COMPOSE), read(MANIFEST), read(APACHE), read(DNS)
    compose, manifest = yaml.safe_load(raw_compose), json.loads(raw_manifest)
    require(compose["services"]["dewey"]["image"] == OLD_IMAGE and manifest["images"]["dewey"]["image"] == OLD_IMAGE, "Predecessor changed")
    require(containers()[NAME]["image"] == OLD_IMAGE, "Actual predecessor changed")
    labels = json.loads(subprocess.check_output(["sudo", "docker", "image", "inspect", image["image"]]))[0]["Config"]["Labels"]
    require(labels.get("org.opencontainers.image.revision") == image["source_commit"] and labels.get("org.opencontainers.image.version") == image["source_tag"], "Image labels differ from tagged release")
    current_service = compose["services"]["dewey"]
    live_config_sha256 = {}
    for field, saved in (("DEWEY_CONFIG", "dewey-config.yaml"), ("TAPDB_CONFIG_PATH", "tapdb-runtime.yaml")):
        sources = [v for v in current_service["volumes"] if isinstance(v, dict)
            and v.get("target") == current_service["environment"][field]]
        require(len(sources) == 1, "Ambiguous live configuration identity: " + field)
        source = sources[0]["source"]
        source_sha256 = digest(read(source))
        require(source_sha256 == digest((ROOT / saved).read_bytes()),
            "Private inventory configuration differs from live configuration: " + field)
        live_config_sha256[source] = source_sha256
    for name, raw in (("previous-compose.yml", raw_compose), ("previous-manifest.json", raw_manifest),
                      ("previous-proxy.conf", raw_proxy), ("previous-dns.conf", raw_dns)):
        private(ROOT / name, raw)
    private(ROOT / "containers-before.json", containers())
    token = secrets.token_urlsafe(48)
    config = yaml.safe_load((ROOT / "dewey-config.yaml").read_bytes())
    config.setdefault("share", {}).update(trusted_proxy_peer="127.0.0.1", ingress_assertion_header="X-Dewey-Tailnet-Assertion",
        ingress_assertion=token, application_origin="https://dewey.day.lsmc.bio",
        content_host_suffix="dewey-content.day.lsmc.bio", session_generation=str(uuid4()))
    private(ROOT / "final-config.yaml", yaml.safe_dump(config, sort_keys=False))
    candidate = compose["services"]["dewey"]
    old_config = candidate["environment"]["DEWEY_CONFIG"]
    target = f"/opt/dewey/day/releases/{image['source_tag']}/dewey-config.yaml"
    selected = [v for v in candidate["volumes"] if isinstance(v, dict) and v.get("target") == old_config]
    require(len(selected) == 1, "Ambiguous Dewey config mount")
    selected[0].update(source=str(ROOT / "final-config.yaml"), target=target)
    candidate["image"] = image["image"]
    candidate["environment"].update(DEWEY_CONFIG=target, HOST="127.0.0.1", DEWEY_HOST="127.0.0.1",
        DEWEY_BUILD_SHA=image["source_commit"], LSMC_RELEASE_SHA=image["source_commit"], DEWEY_BUILD_BRANCH=image["source_branch"])
    manifest["images"]["dewey"].update(image=image["image"], source_commit=image["source_commit"], source_tag=image["source_tag"])
    private(ROOT / "final-compose.yml", yaml.safe_dump(compose, sort_keys=False))
    private(ROOT / "final-manifest.json", manifest)
    cli = deepcopy(candidate)
    cli.update(user="1000:1000", restart="no")
    cli_runtime = [v for v in cli["volumes"] if isinstance(v, dict) and v.get("target") == cli["environment"]["TAPDB_CONFIG_PATH"]]
    require(len(cli_runtime) == 1, "Ambiguous immutable TapDB runtime mount")
    cli_runtime[0]["source"] = str(ROOT / "tapdb-runtime.yaml")
    cli["environment"].update(XDG_CONFIG_HOME="/opt/dewey-sharing/config", XDG_STATE_HOME="/opt/dewey-sharing/state",
        XDG_CACHE_HOME="/opt/dewey-sharing/cache", XDG_DATA_HOME="/opt/dewey-sharing/data")
    cli["volumes"].append({"type": "bind", "source": str(ROOT), "target": "/opt/dewey-sharing"})
    private(ROOT / "native-compose.yml", yaml.safe_dump({"services": {"dewey": cli}}, sort_keys=False))
    attestation = f'''    RequestHeader unset X-Dewey-Tailnet-Assertion early
    RewriteEngine On
    RewriteRule ^ - [E=!DEWEY_TRUSTED_TAILNET]
    RewriteCond %{{SERVER_ADDR}} =100.71.233.11
    RewriteCond expr "%{{CONN_REMOTE_ADDR}} -ipmatch '100.64.0.0/10'"
    RewriteRule ^ - [E=DEWEY_TRUSTED_TAILNET:1]
    RequestHeader set X-Dewey-Tailnet-Assertion "{token}" env=DEWEY_TRUSTED_TAILNET
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"
    ProxyPreserveHost On
    AllowEncodedSlashes NoDecode
    MergeSlashes Off
'''
    main_proxy = f'''<VirtualHost *:443>
    ServerName dewey.day.lsmc.bio
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/dayhoff-day-primary/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/dayhoff-day-primary/privkey.pem
{attestation}    ProxyPass / http://127.0.0.1:8914/ nocanon
    ProxyPassReverse / http://127.0.0.1:8914/
    ErrorLog ${{APACHE_LOG_DIR}}/dewey-error.log
    CustomLog ${{APACHE_LOG_DIR}}/dewey-access.log combined
</VirtualHost>
'''
    content_proxy = f'''<VirtualHost *:443>
    ServerName dewey-content.day.lsmc.bio
    ServerAlias *.dewey-content.day.lsmc.bio
    SSLEngine on
    SSLCertificateFile {CERT}/fullchain.pem
    SSLCertificateKeyFile {CERT}/privkey.pem
{attestation}    RewriteCond %{{ENV:DEWEY_TRUSTED_TAILNET}} !=1
    RewriteRule ^ - [F]
    RewriteCond %{{REQUEST_URI}} !^/__dewey_preview/
    RewriteRule ^ - [F]
    ProxyPass /__dewey_preview/ http://127.0.0.1:8914/__dewey_preview/ nocanon
    ProxyPassReverse /__dewey_preview/ http://127.0.0.1:8914/__dewey_preview/
    ErrorLog ${{APACHE_LOG_DIR}}/dewey-content-error.log
    CustomLog ${{APACHE_LOG_DIR}}/dewey-content-access.log combined
</VirtualHost>
'''
    private(ROOT / "final-proxy.conf", main_proxy)
    private(ROOT / "content-proxy.conf", content_proxy)
    rule = "address=/dewey-content.day.lsmc.bio/100.71.233.11\n"
    require("dewey-content.day.lsmc.bio" not in raw_dns.decode(), "Content DNS already configured; review exact existing state")
    private(ROOT / "final-dns.conf", raw_dns + (b"" if raw_dns.endswith(b"\n") else b"\n") + rule.encode())
    candidate_files = ("final-compose.yml", "final-manifest.json", "final-config.yaml", "native-compose.yml",
        "final-proxy.conf", "content-proxy.conf", "final-dns.conf", "tapdb-runtime.yaml", "operator.yaml", "attribution.json")
    private(ROOT / "final-preparation.json", {"phase": "prepared", "image": image, "prepared_at": now(),
        "candidate_sha256": {name: digest((ROOT / name).read_bytes()) for name in candidate_files},
        "live_config_sha256": live_config_sha256,
        "execution_script_sha256": digest(Path(__file__).read_bytes()),
        "compose_before_sha256": digest(raw_compose), "manifest_before_sha256": digest(raw_manifest),
        "proxy_before_sha256": digest(raw_proxy), "dns_before_sha256": digest(raw_dns), "tests_run": False})
    print(json.dumps({"phase": "prepared", "tag": image["source_tag"], "commit": image["source_commit"], "production_changed": False}))


def certificate():
    require(not protected_path_exists(CERT), "Content certificate already exists; inspect instead of reissuing")
    logged("certificate", ["sudo", "env", "AWS_PROFILE=lsmc", "AWS_CONFIG_FILE=/home/ubuntu/.aws/config",
        "AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials", "certbot", "certonly", "--dns-route53",
        "--non-interactive", "--cert-name", "dewey-content-day", "-d", "*.dewey-content.day.lsmc.bio"], timeout=180)
    sans = subprocess.check_output(["sudo", "openssl", "x509", "-in", CERT + "/fullchain.pem", "-noout", "-ext", "subjectAltName"], text=True)
    require("DNS:*.dewey-content.day.lsmc.bio" in sans, "Content certificate SAN missing")
    private(ROOT / "certificate-receipt.json", {"issued_at": now(), "sans": sans.strip(), "public_application_ingress": False})
    print(json.dumps({"phase": "certificate", "content_subtree_only": True}))


def inventory():
    native("final-inventory", ["upgrade-sharing", "--phase", "inventory", "--inventory", "/opt/dewey-sharing/final-inventory.json",
        "--created-since", CREATED_SINCE, "--actor", ACTOR, "--attribution", "/opt/dewey-sharing/attribution.json"])
    data = json.loads((ROOT / "final-inventory.json").read_text())
    print(json.dumps({"phase": "inventory", "sha256": data["inventory_sha256"], "created_since": data["created_since"],
        "shares": len(data["shares"]), "eligible_share_count": data["eligible_share_count"],
        "retire_before_cutoff_count": data["retire_before_cutoff_count"], "ambiguous": data["ambiguous"]}))


def cutover(expected_sha256):
    inventory = json.loads((ROOT / "final-inventory.json").read_text())
    require(expected_sha256 and inventory["inventory_sha256"] == expected_sha256 and not inventory["ambiguous"], "Review exact unambiguous inventory before cutover")
    require(datetime.fromisoformat(inventory["created_since"]) == datetime.fromisoformat(CREATED_SINCE.replace("Z", "+00:00")), "Reviewed creation cutoff changed")
    prepared = verify_prepared()
    image = prepared["image"]
    for path, key in ((COMPOSE, "compose"), (MANIFEST, "manifest"), (APACHE, "proxy"), (DNS, "dns")):
        require(digest(read(path)) == prepared[key + "_before_sha256"], "Concurrent configuration change: " + key)
    before = containers()
    require(before == json.loads((ROOT / "containers-before.json").read_text()), "Runtime containers changed since preparation")
    require(protected_path_exists(CERT), "Content certificate must be prepared before maintenance")
    native("templates", ["registry-templates", "--operator-config", "/opt/dewey-sharing/operator.yaml",
        "--repository-pack", "/app/config/tapdb_templates/dewey/sharing2.repository-pack.json",
        "--receipt-pack", "/opt/dewey-sharing/template-receipt.json", "--actor", ACTOR,
        "--attribution", "/opt/dewey-sharing/attribution.json"])
    private(ROOT / "maintenance-start.json", {"started_at": now(), "predecessor": before[NAME], "drain_limit_seconds": 120})
    # SIGTERM asks Uvicorn to drain. No timeout-induced SIGKILL is authorized.
    drain = subprocess.Popen(["sudo", "docker", "stop", "--signal", "SIGTERM", "--timeout", "-1", before[NAME]["id"]], stdout=subprocess.DEVNULL)
    deadline = time.monotonic() + 120
    while True:
        state = json.loads(subprocess.check_output(["sudo", "docker", "inspect", before[NAME]["id"]]))[0]["State"]
        if not state["Running"]:
            break
        require(time.monotonic() < deadline, "Drain exceeded maintenance bound; no force used and conversion has not started")
        time.sleep(2)
    require(state["Status"] == "exited" and state["ExitCode"] in (0, 143) and not state["OOMKilled"], "Predecessor did not drain normally")
    require(drain.wait(timeout=10) == 0, "Native graceful stop did not complete")
    private(ROOT / "predecessor-drain.json", {"finished_at": state["FinishedAt"], "exit_code": state["ExitCode"], "force_used": False})
    for phase in ("apply", "verify"):
        native("upgrade-" + phase, ["upgrade-sharing", "--phase", phase, "--inventory", "/opt/dewey-sharing/final-inventory.json",
            "--created-since", CREATED_SINCE,
            "--expected-sha256", expected_sha256, "--receipt", "/opt/dewey-sharing/upgrade-" + phase + ".json",
            "--actor", ACTOR, "--attribution", "/opt/dewey-sharing/attribution.json"])
    for path, key in ((COMPOSE, "compose"), (MANIFEST, "manifest"), (APACHE, "proxy"), (DNS, "dns")):
        require(digest(read(path)) == prepared[key + "_before_sha256"], "Configuration changed during maintenance: " + key)
    verify_prepared()
    for source, target in (("final-compose.yml", COMPOSE), ("final-manifest.json", MANIFEST),
                           ("final-proxy.conf", APACHE), ("content-proxy.conf", CONTENT), ("final-dns.conf", DNS)):
        subprocess.run(["sudo", "install", "-m", "0600", str(ROOT / source), str(target)], check=True)
    subprocess.run(["sudo", "ln", "-s", str(CONTENT), "/etc/apache2/sites-enabled/dewey-content-day.conf"], check=True)
    logged("apache-configuration", ["sudo", "apache2ctl", "configtest"])
    logged("dns-configuration", ["sudo", "dnsmasq", "--test", "--conf-file=" + str(DNS)])
    verify_prepared()
    logged("service-start", ["sudo", "docker", "compose", "-p", "dayhoff-day", "-f", str(COMPOSE), "up", "-d", "--no-deps", "--pull", "never", "dewey"])
    logged("proxy-reload", ["sudo", "systemctl", "reload", "apache2"])
    logged("dns-reload", ["sudo", "systemctl", "restart", "dayhoff-day-lsmc-bio-dnsmasq"])
    after = containers()
    require(after[NAME]["image"] == image["image"] and after[NAME]["running"], "Final Dewey container identity mismatch")
    require({k: v for k, v in after.items() if k != NAME} == {k: v for k, v in before.items() if k != NAME}, "Sibling runtime changed; investigate")
    private(ROOT / "deployment-receipt.json", {"phase": "deployed", "deployed_at": now(), "tag": image["source_tag"],
        "commit": image["source_commit"], "image": image["image"], "container": after[NAME], "inventory_sha256": expected_sha256,
        "native_conversion": "verified", "sibling_containers_unchanged": True, "tests_run": False, "user_acceptance": "pending"})
    print(json.dumps({"phase": "deployed", "image": image["image"], "availability_observation": "pending", "user_acceptance": "pending"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "certificate", "inventory", "cutover"))
    parser.add_argument("--image-receipt", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    require(pwd.getpwuid(os.getuid()).pw_name == "ubuntu", "Run from the authorized ubuntu login shell")
    require(subprocess.check_output(["sudo", "tailscale", "ip", "-4"], text=True).strip() == "100.71.233.11", "Unexpected EC2 Tailscale identity")
    if args.phase == "prepare":
        require(args.image_receipt and args.image_receipt.is_absolute(), "Explicit absolute final image receipt required")
        prepare(args.image_receipt)
    elif args.phase == "certificate":
        certificate()
    elif args.phase == "inventory":
        inventory()
    else:
        cutover(args.expected_sha256)


if __name__ == "__main__":
    main()
