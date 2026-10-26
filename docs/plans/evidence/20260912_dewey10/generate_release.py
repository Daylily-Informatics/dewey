"""Generate the Dewey-only build capsule from its final annotated release tag.

Derived from the retained 9.1 release capsule; no main-branch, CI or smoke stages.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--tag", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if not args.repo.is_absolute() or not args.output.is_absolute() or args.output.exists() or not re.fullmatch(r"\d+\.\d+\.\d+", args.tag):
    raise SystemExit("Use an absolute repository, an absent absolute output directory and a numeric release tag")
def git(*argv):
    return subprocess.check_output(["git", "-C", str(args.repo), *argv])
if git("cat-file", "-t", args.tag).strip() != b"tag":
    raise SystemExit("The release tag must be annotated")
commit = git("rev-parse", args.tag + "^{commit}").decode().strip()
if commit != git("rev-parse", "HEAD").decode().strip():
    raise SystemExit("Tag must identify the current intended release commit")
inputs = ["dewey_service", "config", "pyproject.toml", "uv.lock", "README.md", "docker/entrypoint.sh"]
if git("diff", args.tag, "--", *inputs):
    raise SystemExit("Release source differs from the tag")
args.output.mkdir(parents=True, mode=0o700)
archive = gzip.compress(git("archive", "--format=tar", args.tag, *inputs), mtime=0)
(args.output / "source.tar.gz").write_bytes(archive)
reference = "docs/plans/evidence/20260911_dewey_900_final_release_generator/release-1f634ef66082/Dockerfile.release"
dockerfile = git("show", args.tag + ":" + reference).decode()
dockerfile = "\n".join(line for line in dockerfile.splitlines() if not line.startswith('RUN /app/.venv/bin/python -c')) + "\n"
(args.output / "Dockerfile.release").write_text(dockerfile)
repository = "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
manifest = {"tag": args.tag, "commit": commit, "tree": git("rev-parse", args.tag + "^{tree}").decode().strip(),
    "source_sha256": hashlib.sha256(archive).hexdigest(), "dockerfile_sha256": hashlib.sha256(dockerfile.encode()).hexdigest(),
    "repository": repository, "image": repository + ":" + args.tag, "platform": "linux/amd64", "tests_run": False}
(args.output / "release.json").write_text(json.dumps(manifest, indent=2) + "\n")
script = f'''#!/usr/bin/env bash
set -euo pipefail
umask 077
cd -- "$(dirname -- "$0")"
printf '%s  %s\\n' '{manifest["source_sha256"]}' source.tar.gz '{manifest["dockerfile_sha256"]}' Dockerfile.release | sha256sum -c -
if aws ecr describe-images --region us-west-2 --repository-name dayhoff/day/dewey --image-ids imageTag={args.tag} > existing-image.json 2> existing-image-error.txt; then
  echo 'Release image tag already exists; refusing to overwrite it' >&2
  exit 1
fi
grep -q ImageNotFoundException existing-image-error.txt
mkdir context
tar -xzf source.tar.gz -C context
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --file Dockerfile.release --build-arg SETUPTOOLS_SCM_PRETEND_VERSION={args.tag} --label org.opencontainers.image.version={args.tag} --label org.opencontainers.image.revision={commit} --label org.opencontainers.image.source=https://github.com/lsmc-bio/dewey.git --tag {manifest["image"]} context 2>&1 | tee build.log
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 108782052779.dkr.ecr.us-west-2.amazonaws.com >/dev/null
docker push {manifest["image"]} 2>&1 | tee push.log
aws ecr describe-images --region us-west-2 --repository-name dayhoff/day/dewey --image-ids imageTag={args.tag} --query 'imageDetails[0].{{digest:imageDigest,tags:imageTags,pushedAt:imagePushedAt}}' --output json > image-receipt.json
cat image-receipt.json
'''
(args.output / "build-publish.sh").write_text(script)
(args.output / "build-publish.sh").chmod(0o700)
print(json.dumps(manifest))
