"""Build one exact, annotated service release on the designated EC2 host only.

Run as ubuntu from an interactive bash login session. This script never deploys,
runs a test campaign, changes sibling images, or replaces an existing image tag.
GitHub credentials remain in process memory and the BuildKit secret channel.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import urllib.request

INSTANCE = "i-07df3a933e4839f52"
REGION = "us-west-2"
PROFILE = "lsmc"
REGISTRY = "108782052779.dkr.ecr.us-west-2.amazonaws.com"
SECRET = "arn:aws:secretsmanager:us-east-1:108782052779:secret:dayhoff/container-build/github/token/iamh2o-gh-repo-awtQQ9"
REPOSITORIES = {"dewey": "dewey"}


def checked_output(argv, *, env=None):
    return subprocess.check_output(argv, text=True, env=env).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=sorted(REPOSITORIES))
    parser.add_argument("tag")
    parser.add_argument("commit")
    parser.add_argument("branch")
    args = parser.parse_args()
    if pwd.getpwuid(os.getuid()).pw_name != "ubuntu":
        raise RuntimeError("Build must run as ubuntu on the designated EC2 host")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.tag):
        raise ValueError("An exact numeric release tag is required")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise ValueError("An exact source commit is required")
    if not re.fullmatch(r"codex/[A-Za-z0-9._/-]+", args.branch):
        raise ValueError("The exact working branch is required for provenance")
    token_request = urllib.request.Request(
        "http://169.254.169.254/latest/api/token", method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(token_request, timeout=3) as response:
        metadata_token = response.read().decode()
    identity_request = urllib.request.Request(
        "http://169.254.169.254/latest/dynamic/instance-identity/document",
        headers={"X-aws-ec2-metadata-token": metadata_token},
    )
    with opener.open(identity_request, timeout=3) as response:
        identity = json.load(response)
    if identity["instanceId"] != INSTANCE or identity["region"] != REGION:
        raise RuntimeError("Unexpected EC2 builder identity; no build started")

    env = {**os.environ, "AWS_PROFILE": PROFILE, "AWS_DEFAULT_REGION": REGION,
           "AWS_PAGER": "", "GIT_TERMINAL_PROMPT": "0"}
    repository = f"dayhoff/day/{args.service}"
    image_tag = args.tag
    existing = subprocess.run(
        ["aws", "ecr", "describe-images", "--repository-name", repository,
         "--image-ids", f"imageTag={image_tag}", "--region", REGION],
        env=env, capture_output=True, text=True,
    )
    if existing.returncode == 0:
        raise RuntimeError("Final ECR release tag already exists; refusing replacement")
    if "ImageNotFoundException" not in existing.stderr:
        raise RuntimeError("Unable to establish exact ECR tag absence: " + existing.stderr)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(f"/home/ubuntu/{args.service}-{args.tag}-{stamp}")
    root.mkdir(mode=0o700)
    source = root / "source"
    log_path = root / "build.log"
    url = f"https://github.com/lsmc-bio/{REPOSITORIES[args.service]}.git"
    secret = json.loads(checked_output(
        ["aws", "secretsmanager", "get-secret-value", "--region", "us-east-1",
         "--secret-id", SECRET, "--query", "SecretString", "--output", "text"], env=env))
    if not isinstance(secret.get("token"), str) or not secret["token"].strip():
        raise RuntimeError("Configured GitHub build credential is empty")
    env["DEWEY_RELEASE_GITHUB_TOKEN"] = secret["token"]
    askpass = root / "git-askpass.py"
    askpass.write_text(
        "#!/usr/bin/env python3\nimport os,sys\n"
        "prompt=sys.argv[1]\n"
        "if 'Username' in prompt: print('x-access-token')\n"
        "elif 'Password' in prompt: print(os.environ['DEWEY_RELEASE_GITHUB_TOKEN'])\n"
        "else: raise SystemExit(1)\n"
    )
    askpass.chmod(0o700)
    env["GIT_ASKPASS"] = str(askpass)
    image = f"{REGISTRY}/{repository}:{image_tag}"
    logged_in = False
    try:
        with log_path.open("x") as log:
            subprocess.run(["git", "clone", "--branch", args.tag, "--single-branch",
                            "--depth", "1", url, str(source)], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
            if checked_output(["git", "-C", str(source), "cat-file", "-t", args.tag]) != "tag":
                raise RuntimeError("Source release tag is not annotated")
            if checked_output(["git", "-C", str(source), "rev-parse", "HEAD"]) != args.commit:
                raise RuntimeError("Source tag commit differs from reviewed release")
            if checked_output(["git", "-C", str(source), "status", "--porcelain"]):
                raise RuntimeError("Exact source checkout is dirty")
            password = checked_output(["aws", "ecr", "get-login-password", "--region", REGION], env=env)
            subprocess.run(["sudo", "docker", "login", "--username", "AWS", "--password-stdin", REGISTRY],
                           input=password, text=True, stdout=log, stderr=subprocess.STDOUT, check=True)
            logged_in = True
            command = ["sudo", "--preserve-env=DEWEY_RELEASE_GITHUB_TOKEN", "docker", "build",
                       "--platform", "linux/amd64", "--progress", "plain",
                       "--label", f"org.opencontainers.image.version={args.tag}",
                       "--label", f"org.opencontainers.image.revision={args.commit}"]
            build_args = {"SETUPTOOLS_SCM_PRETEND_VERSION": args.tag,
                          "DEWEY_BUILD_BRANCH": args.branch, "DEWEY_BUILD_SHA": args.commit}
            for key, value in build_args.items():
                command += ["--build-arg", f"{key}={value}"]
            release_dockerfile = source / "docs/plans/evidence/20260911_dewey_900_final_release_generator/release-1f634ef66082/Dockerfile.release"
            # The existing scoped Dewey release generator uses this exact pinned
            # Dockerfile and excludes its standalone predeployment version probe.
            dockerfile = "\n".join(line for line in release_dockerfile.read_text().splitlines()
                if not line.startswith("RUN /app/.venv/bin/python -c")) + "\n"
            selected_dockerfile = root / "Dockerfile.release"
            selected_dockerfile.write_text(dockerfile)
            command += ["--file", str(selected_dockerfile), "--label", "org.opencontainers.image.source=" + url,
                        "--tag", image, str(source)]
            subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run(["sudo", "docker", "push", image], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        published = json.loads(checked_output(
            ["aws", "ecr", "describe-images", "--repository-name", repository,
             "--image-ids", f"imageTag={image_tag}", "--region", REGION], env=env))["imageDetails"]
        if len(published) != 1 or not re.fullmatch(r"sha256:[0-9a-f]{64}", published[0]["imageDigest"]):
            raise RuntimeError("Final ECR digest is not exact")
        receipt = {
            "schema": "ursa-owy-kahlo.final-image/v1", "service": args.service,
            "source_tag": args.tag, "source_commit": args.commit, "source_branch": args.branch,
            "source_tag_object": checked_output(["git", "-C", str(source), "rev-parse", args.tag + "^{tag}"]),
            "source_url": url, "dockerfile_sha256": hashlib.sha256(selected_dockerfile.read_bytes()).hexdigest(), "builder_instance": INSTANCE, "builder_region": REGION,
            "builder_aws_profile": PROFILE,
            "image": f"{REGISTRY}/{repository}@{published[0]['imageDigest']}",
            "image_tag": image, "build_root": str(root), "build_log": str(log_path),
            "build_log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
            "completed_at": datetime.now(timezone.utc).isoformat(), "tests_run": False,
            "deployed": False,
        }
        receipt_path = root / "image-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({"receipt": str(receipt_path), **receipt}, indent=2))
    finally:
        env.pop("DEWEY_RELEASE_GITHUB_TOKEN", None)
        secret.clear()
        askpass.unlink(missing_ok=True)
        if logged_in:
            subprocess.run(["sudo", "docker", "logout", REGISTRY],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


if __name__ == "__main__":
    main()
