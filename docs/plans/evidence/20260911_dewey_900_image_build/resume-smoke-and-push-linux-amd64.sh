#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly SOURCE_COMMIT="c484c95768a4147acdcabd12a2da0332c4c750dc"
readonly SOURCE_URL="https://github.com/lsmc-bio/dewey.git"
readonly IMAGE_REPOSITORY="108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
readonly IMAGE_TAG="9.0.0-c484c95768a4"
readonly IMAGE_REF="${IMAGE_REPOSITORY}:${IMAGE_TAG}"
readonly EXPECTED_IMAGE_ID="sha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f"
readonly AWS_REGION="us-west-2"
readonly TARGET_PLATFORM="linux/amd64"
readonly SMOKE_DEPLOYMENT_CODE="dewey900-image-smoke"

usage() {
    printf 'Usage: %s --receipt-dir /absolute/new/path\n' "$0" >&2
}

if [[ $# -ne 2 || "$1" != "--receipt-dir" ]]; then
    usage
    exit 64
fi
readonly RECEIPT_DIR="$2"
if [[ "$RECEIPT_DIR" != /* || "$RECEIPT_DIR" == "/" || "$RECEIPT_DIR" == "${HOME}" ]]; then
    printf 'Receipt directory must be a safe absolute path: %s\n' "$RECEIPT_DIR" >&2
    exit 64
fi

for command_name in aws date docker grep mktemp tee uname; do
    command -v "$command_name" >/dev/null || {
        printf 'Required command is unavailable: %s\n' "$command_name" >&2
        exit 69
    }
done
[[ "$(uname -m)" == "x86_64" ]] || {
    printf 'Native x86_64 host required; observed %s\n' "$(uname -m)" >&2
    exit 65
}
docker version >/dev/null
[[ "$(docker info --format '{{.OSType}}/{{.Architecture}}')" == "linux/x86_64" ]] || {
    printf 'Native linux/x86_64 Docker engine required; observed %s\n' \
        "$(docker info --format '{{.OSType}}/{{.Architecture}}')" >&2
    exit 65
}
if [[ -e "$RECEIPT_DIR" || -L "$RECEIPT_DIR" ]]; then
    printf 'Receipt directory must be absent: %s\n' "$RECEIPT_DIR" >&2
    exit 67
fi
mkdir -- "$RECEIPT_DIR"

readonly OBSERVED_IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE_REF")"
[[ "$OBSERVED_IMAGE_ID" == "$EXPECTED_IMAGE_ID" ]] || {
    printf 'Built image ID mismatch: expected %s; observed %s\n' \
        "$EXPECTED_IMAGE_ID" "$OBSERVED_IMAGE_ID" >&2
    exit 68
}
[[ "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE_REF")" == "$TARGET_PLATFORM" ]] || {
    printf 'Built image platform mismatch\n' >&2
    exit 68
}
[[ "$(docker image inspect --format '{{.Config.User}}' "$IMAGE_REF")" == "lsmc" ]] || {
    printf 'Built image default user mismatch\n' >&2
    exit 68
}
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.version"}}' "$IMAGE_REF")" == "9.0.0" ]] || {
    printf 'Built image version label mismatch\n' >&2
    exit 68
}
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$IMAGE_REF")" == "$SOURCE_COMMIT" ]] || {
    printf 'Built image revision label mismatch\n' >&2
    exit 68
}
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.source"}}' "$IMAGE_REF")" == "$SOURCE_URL" ]] || {
    printf 'Built image source label mismatch\n' >&2
    exit 68
}

{
    printf 'resume_mode=smoke-and-push-existing-image\n'
    printf 'expected_image_id=%s\n' "$EXPECTED_IMAGE_ID"
    printf 'observed_image_id=%s\n' "$OBSERVED_IMAGE_ID"
    printf 'source_commit=%s\n' "$SOURCE_COMMIT"
    printf 'source_url=%s\n' "$SOURCE_URL"
    printf 'target_platform=%s\n' "$TARGET_PLATFORM"
    printf 'image_ref=%s\n' "$IMAGE_REF"
    printf 'smoke_deployment_code=%s\n' "$SMOKE_DEPLOYMENT_CODE"
    printf 'started_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/resume-inputs.txt"
docker image inspect "$IMAGE_REF" > "$RECEIPT_DIR/local-image-inspect.json"

docker run --rm --env "DEWEY_DEPLOYMENT_CODE=${SMOKE_DEPLOYMENT_CODE}" \
    --entrypoint /app/.venv/bin/python "$IMAGE_REF" -c \
    'import importlib.metadata as m, json, os, sys; from dewey_service.integrations.tapdb_runtime import ensure_tapdb_version; ensure_tapdb_version(); observed={"dewey-service":m.version("dewey-service"),"daylily-tapdb":m.version("daylily-tapdb"),"meridian-euid":m.version("meridian-euid"),"python":sys.version.split()[0],"executable":sys.executable,"deployment_code":os.environ["DEWEY_DEPLOYMENT_CODE"]}; expected={"dewey-service":"9.0.0","daylily-tapdb":"10.1.1rc1","meridian-euid":"0.4.8","deployment_code":"dewey900-image-smoke"}; assert all(observed[k] == v for k,v in expected.items()), observed; assert observed["python"].startswith("3.12."), observed; assert observed["executable"] == "/app/.venv/bin/python", observed; print(json.dumps(observed,sort_keys=True))' \
    | tee "$RECEIPT_DIR/package-versions.json"
docker run --rm --env "DEWEY_DEPLOYMENT_CODE=${SMOKE_DEPLOYMENT_CODE}" \
    --entrypoint /app/.venv/bin/dewey "$IMAGE_REF" --help \
    > "$RECEIPT_DIR/dewey-help.txt"
docker run --rm --entrypoint /bin/sh "$IMAGE_REF" -c \
    'set -eu; test "$(id -un)" = lsmc; test -x /app/.venv/bin/python; test ! -e /usr/bin/git; printf "runtime_user=%s\n" "$(id)"' \
    | tee "$RECEIPT_DIR/runtime-filesystem.txt"

{
    printf 'local_image_id=%s\n' "$OBSERVED_IMAGE_ID"
    printf 'local_image_size_bytes=%s\n' "$(docker image inspect --format '{{.Size}}' "$IMAGE_REF")"
    printf 'local_platform=%s\n' "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE_REF")"
    printf 'local_default_user=%s\n' "$(docker image inspect --format '{{.Config.User}}' "$IMAGE_REF")"
    printf 'local_validation=passed\n'
    printf 'validated_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/resume-smoke-receipt.txt"

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

readonly PRIVATE_DOCKER_CONFIG="$(mktemp -d)"
trap 'rm -rf -- "$PRIVATE_DOCKER_CONFIG"' EXIT
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
    printf 'pushed_image_id=%s\n' "$OBSERVED_IMAGE_ID"
    printf 'pushed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$RECEIPT_DIR/push-receipt.txt"
