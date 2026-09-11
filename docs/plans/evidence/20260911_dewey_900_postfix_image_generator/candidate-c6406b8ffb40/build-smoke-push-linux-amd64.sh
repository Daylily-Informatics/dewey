#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly SOURCE_COMMIT="c6406b8ffb40e58feaba31e2163d77448d47698c"
readonly SOURCE_TREE="d234131c0943ead5d17c5fbc097620c976782d78"
readonly SOURCE_URL="https://github.com/lsmc-bio/dewey.git"
readonly CONTEXT_NAME="dewey-9.0.0-c6406b8ffb40-source-context.tar.gz"
readonly CONTEXT_SHA256="8cd3cea268632e8a6c173d60fca88319b1c444dc3a241e5a0d53367a9ac4fc9a"
readonly RELEASE_DOCKERFILE_SHA256="16b4ec188bde0070ce47610a1364d92942f9a2f8dc51a22b5bf0b93fd22ed93e"
readonly IMAGE_REPOSITORY="108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
readonly IMAGE_TAG="9.0.0-c6406b8ffb40"
readonly IMAGE_REF="${IMAGE_REPOSITORY}:${IMAGE_TAG}"
readonly AWS_REGION="us-west-2"
readonly TARGET_PLATFORM="linux/amd64"
readonly SMOKE_DEPLOYMENT_CODE="dewey900-image-smoke"
readonly BUILDER_BASE="ghcr.io/astral-sh/uv:0.5.30-python3.12-bookworm-slim@sha256:dae7f9060850980a52f1c629f2e94024c7d267f506dbc465c170553200e19d9f"
readonly RUNTIME_BASE="python:3.12-slim-bookworm@sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly CONTEXT_ARCHIVE="${SCRIPT_DIR}/${CONTEXT_NAME}"
readonly RELEASE_DOCKERFILE="${SCRIPT_DIR}/Dockerfile.release"

usage() {
    printf 'Usage: %s --receipt-dir /absolute/path [--push]\n' "$0" >&2
}

if [[ $# -ne 2 && $# -ne 3 ]]; then
    usage
    exit 64
fi
if [[ "$1" != "--receipt-dir" || "$2" != /* ]]; then
    usage
    exit 64
fi
readonly RECEIPT_DIR="$2"
if [[ "$RECEIPT_DIR" == "/" || "$RECEIPT_DIR" == "${HOME}" ]]; then
    printf 'Refusing unsafe receipt directory: %s\n' "$RECEIPT_DIR" >&2
    exit 64
fi
readonly PUSH_MODE="${3:-}"
if [[ -n "$PUSH_MODE" && "$PUSH_MODE" != "--push" ]]; then
    usage
    exit 64
fi

for command_name in date docker grep mktemp sed sha256sum tar tee uname; do
    command -v "$command_name" >/dev/null || {
        printf 'Required command is unavailable: %s\n' "$command_name" >&2
        exit 69
    }
done
if [[ "$PUSH_MODE" == "--push" ]]; then
    command -v aws >/dev/null || {
        printf 'Required command is unavailable: aws\n' >&2
        exit 69
    }
fi

[[ "$(uname -m)" == "x86_64" ]] || {
    printf 'Native x86_64 builder required; observed %s\n' "$(uname -m)" >&2
    exit 65
}

docker version >/dev/null
[[ "$(docker info --format '{{.OSType}}/{{.Architecture}}')" == "linux/x86_64" ]] || {
    printf 'Native linux/x86_64 Docker engine required; observed %s\n' \
        "$(docker info --format '{{.OSType}}/{{.Architecture}}')" >&2
    exit 65
}

[[ "$(sha256sum "$CONTEXT_ARCHIVE" | sed 's/[[:space:]].*$//')" == "$CONTEXT_SHA256" ]] || {
    printf 'Source context SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(sha256sum "$RELEASE_DOCKERFILE" | sed 's/[[:space:]].*$//')" == "$RELEASE_DOCKERFILE_SHA256" ]] || {
    printf 'Release Dockerfile SHA256 mismatch\n' >&2
    exit 66
}
grep -Fqx "FROM ${BUILDER_BASE} AS builder" "$RELEASE_DOCKERFILE" || {
    printf 'Builder base pin mismatch\n' >&2
    exit 66
}
grep -Fqx "FROM ${RUNTIME_BASE} AS runtime" "$RELEASE_DOCKERFILE" || {
    printf 'Runtime base pin mismatch\n' >&2
    exit 66
}

if [[ -e "$RECEIPT_DIR" || -L "$RECEIPT_DIR" ]]; then
    printf 'Receipt directory must be absent: %s\n' "$RECEIPT_DIR" >&2
    exit 67
fi
mkdir -- "$RECEIPT_DIR"
readonly BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_ROOT"' EXIT
tar -xzf "$CONTEXT_ARCHIVE" -C "$BUILD_ROOT"

[[ "$(sha256sum "$BUILD_ROOT/Dockerfile" | sed 's/[[:space:]].*$//')" == \
    "221fe0a763e07973c6b7b02f099ce96de7ab49d826bd0c84ec2fe5e5df1d3318" ]] || {
    printf 'Source Dockerfile SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(sha256sum "$BUILD_ROOT/pyproject.toml" | sed 's/[[:space:]].*$//')" == \
    "a2a67b3f5c47b9de0271c47527c0fa52514f4bd91b961f1dcb78a53d7cdb3d98" ]] || {
    printf 'pyproject.toml SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(sha256sum "$BUILD_ROOT/uv.lock" | sed 's/[[:space:]].*$//')" == \
    "43c88b3d5ab9950bcdba2c7f0b3158900584424fbc21192dd0e695ffe899c094" ]] || {
    printf 'uv.lock SHA256 mismatch\n' >&2
    exit 66
}

{
    printf 'source_commit=%s\n' "$SOURCE_COMMIT"
    printf 'source_tree=%s\n' "$SOURCE_TREE"
    printf 'source_url=%s\n' "$SOURCE_URL"
    printf 'context_sha256=%s\n' "$CONTEXT_SHA256"
    printf 'release_dockerfile_sha256=%s\n' "$RELEASE_DOCKERFILE_SHA256"
    printf 'target_platform=%s\n' "$TARGET_PLATFORM"
    printf 'builder_base=%s\n' "$BUILDER_BASE"
    printf 'runtime_base=%s\n' "$RUNTIME_BASE"
    printf 'image_ref=%s\n' "$IMAGE_REF"
    printf 'push_requested=%s\n' "$([[ "$PUSH_MODE" == "--push" ]] && printf true || printf false)"
    printf 'started_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/build-inputs.txt"

DOCKER_BUILDKIT=1 docker build \
    --pull \
    --platform "$TARGET_PLATFORM" \
    --file "$RELEASE_DOCKERFILE" \
    --build-arg PYTHON_VERSION=3.12 \
    --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=9.0.0 \
    --label org.opencontainers.image.version=9.0.0 \
    --label "org.opencontainers.image.revision=${SOURCE_COMMIT}" \
    --label "org.opencontainers.image.source=${SOURCE_URL}" \
    --tag "$IMAGE_REF" \
    "$BUILD_ROOT" 2>&1 | tee "$RECEIPT_DIR/docker-build.log"

[[ "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE_REF")" == "$TARGET_PLATFORM" ]]
[[ "$(docker image inspect --format '{{.Config.User}}' "$IMAGE_REF")" == "lsmc" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.version"}}' "$IMAGE_REF")" == "9.0.0" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$IMAGE_REF")" == "$SOURCE_COMMIT" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$IMAGE_REF")" == "$SOURCE_URL" ]]
docker image inspect "$IMAGE_REF" > "$RECEIPT_DIR/local-image-inspect.json"

docker run --rm --env "DEWEY_DEPLOYMENT_CODE=${SMOKE_DEPLOYMENT_CODE}" \
    --entrypoint /app/.venv/bin/python "$IMAGE_REF" -c \
    'import importlib.metadata as m, json, sys; from dewey_service.integrations.tapdb_runtime import ensure_tapdb_version; ensure_tapdb_version(); observed={"dewey-service":m.version("dewey-service"),"daylily-tapdb":m.version("daylily-tapdb"),"meridian-euid":m.version("meridian-euid"),"python":sys.version.split()[0],"executable":sys.executable}; expected={"dewey-service":"9.0.0","daylily-tapdb":"10.1.1rc1","meridian-euid":"0.4.8"}; assert all(observed[k] == v for k,v in expected.items()), observed; assert observed["python"].startswith("3.12."), observed; assert observed["executable"] == "/app/.venv/bin/python", observed; print(json.dumps(observed,sort_keys=True))' \
    | tee "$RECEIPT_DIR/package-versions.json"
docker run --rm --env "DEWEY_DEPLOYMENT_CODE=${SMOKE_DEPLOYMENT_CODE}" \
    --entrypoint /app/.venv/bin/dewey "$IMAGE_REF" --help \
    > "$RECEIPT_DIR/dewey-help.txt"
docker run --rm --entrypoint /bin/sh "$IMAGE_REF" -c \
    'set -eu; test "$(id -un)" = lsmc; test -x /app/.venv/bin/python; test ! -e /usr/bin/git; printf "runtime_user=%s\n" "$(id)"' \
    | tee "$RECEIPT_DIR/runtime-filesystem.txt"

{
    printf 'local_image_id=%s\n' "$(docker image inspect --format '{{.Id}}' "$IMAGE_REF")"
    printf 'local_image_size_bytes=%s\n' "$(docker image inspect --format '{{.Size}}' "$IMAGE_REF")"
    printf 'local_platform=%s\n' "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE_REF")"
    printf 'local_default_user=%s\n' "$(docker image inspect --format '{{.Config.User}}' "$IMAGE_REF")"
    printf 'local_validation=passed\n'
    printf 'built_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/local-build-receipt.txt"

if [[ "$PUSH_MODE" != "--push" ]]; then
    printf 'push_status=not_requested\n' | tee "$RECEIPT_DIR/push-receipt.txt"
    exit 0
fi

readonly ECR_REGISTRY="${IMAGE_REPOSITORY%%/*}"
readonly ECR_REPOSITORY="${IMAGE_REPOSITORY#*/}"
if aws ecr describe-images \
    --region "$AWS_REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids "imageTag=${IMAGE_TAG}" \
    > "$RECEIPT_DIR/ecr-existing-tag.json" \
    2> "$RECEIPT_DIR/ecr-tag-preflight.stderr.txt"; then
    printf 'Refusing to overwrite existing ECR tag: %s\n' "$IMAGE_REF" >&2
    exit 73
fi
grep -Fq 'ImageNotFoundException' "$RECEIPT_DIR/ecr-tag-preflight.stderr.txt" || {
    printf 'ECR tag preflight failed for a reason other than ImageNotFoundException\n' >&2
    exit 74
}

readonly PRIVATE_DOCKER_CONFIG="${BUILD_ROOT}/docker-auth"
mkdir -p -- "$PRIVATE_DOCKER_CONFIG"
export DOCKER_CONFIG="$PRIVATE_DOCKER_CONFIG"
aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null
docker push "$IMAGE_REF" 2>&1 | tee "$RECEIPT_DIR/docker-push.log"
readonly IMAGE_DIGEST="$(aws ecr describe-images \
    --region "$AWS_REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids "imageTag=${IMAGE_TAG}" \
    --query 'imageDetails[0].imageDigest' \
    --output text)"
[[ "$IMAGE_DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]] || {
    printf 'Invalid pushed image digest: %s\n' "$IMAGE_DIGEST" >&2
    exit 75
}
aws ecr describe-images \
    --region "$AWS_REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids "imageDigest=${IMAGE_DIGEST}" \
    > "$RECEIPT_DIR/ecr-image.json"

{
    printf 'push_status=succeeded\n'
    printf 'image_tag=%s\n' "$IMAGE_REF"
    printf 'image_digest=%s@%s\n' "$IMAGE_REPOSITORY" "$IMAGE_DIGEST"
    printf 'pushed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/push-receipt.txt"
