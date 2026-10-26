#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly SOURCE_URL="https://github.com/lsmc-bio/dewey.git"
readonly RELEASE_VERSION="9.0.0"
readonly IMAGE_REPOSITORY="108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey"
readonly BUILD_TEMPLATE_SHA256="49338d9a6a349b2877c284f81930f330f0a2c617146d631afcf60fdce5249430"
readonly RELEASE_DOCKERFILE_SHA256="16b4ec188bde0070ce47610a1364d92942f9a2f8dc51a22b5bf0b93fd22ed93e"
readonly SOURCE_DOCKERFILE_SHA256="221fe0a763e07973c6b7b02f099ce96de7ab49d826bd0c84ec2fe5e5df1d3318"
readonly PYPROJECT_SHA256="a2a67b3f5c47b9de0271c47527c0fa52514f4bd91b961f1dcb78a53d7cdb3d98"
readonly UV_LOCK_SHA256="43c88b3d5ab9950bcdba2c7f0b3158900584424fbc21192dd0e695ffe899c094"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BUILD_TEMPLATE="${SCRIPT_DIR}/build-smoke-push-linux-amd64.template.sh"
readonly RELEASE_DOCKERFILE_TEMPLATE="${SCRIPT_DIR}/Dockerfile.release"

usage() {
    printf '%s\n' \
        "Usage: $0 --repo /absolute/clean/repo --source-commit <40 hex>" \
        "          --output-dir /absolute/absent/path" >&2
}

if [[ $# -ne 6 || "$1" != "--repo" || "$3" != "--source-commit" || \
    "$5" != "--output-dir" ]]; then
    usage
    exit 64
fi
readonly REPO="$2"
readonly SOURCE_COMMIT="$4"
readonly OUTPUT_DIR="$6"

if [[ "$REPO" != /* || ! -d "$REPO" ]]; then
    printf 'Repository must be an existing absolute directory: %s\n' "$REPO" >&2
    exit 64
fi
if [[ ! "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Source commit must be 40 lowercase hexadecimal characters\n' >&2
    exit 64
fi
if [[ "$OUTPUT_DIR" != /* || "$OUTPUT_DIR" == "/" || \
    ( -n "${HOME:-}" && "$OUTPUT_DIR" == "$HOME" ) ]]; then
    printf 'Output directory must be a safe absolute path: %s\n' "$OUTPUT_DIR" >&2
    exit 64
fi
if [[ -e "$OUTPUT_DIR" || -L "$OUTPUT_DIR" ]]; then
    printf 'Output directory must be absent: %s\n' "$OUTPUT_DIR" >&2
    exit 67
fi

for command_name in chmod cp date git grep gzip mkdir sed sha256sum wc; do
    command -v "$command_name" >/dev/null || {
        printf 'Required command is unavailable: %s\n' "$command_name" >&2
        exit 69
    }
done

[[ "$(sha256sum "$BUILD_TEMPLATE" | sed 's/[[:space:]].*$//')" == \
    "$BUILD_TEMPLATE_SHA256" ]] || {
    printf 'Build template SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(sha256sum "$RELEASE_DOCKERFILE_TEMPLATE" | sed 's/[[:space:]].*$//')" == \
    "$RELEASE_DOCKERFILE_SHA256" ]] || {
    printf 'Release Dockerfile SHA256 mismatch\n' >&2
    exit 66
}

readonly REPO_ROOT="$(git -C "$REPO" rev-parse --show-toplevel)"
[[ "$REPO_ROOT" == "$REPO" ]] || {
    printf 'Pass the exact repository root; expected %s, received %s\n' \
        "$REPO_ROOT" "$REPO" >&2
    exit 65
}
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || {
    printf 'Source repository is not clean\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$SOURCE_COMMIT" ]] || {
    printf 'HEAD does not equal the explicit accepted source commit\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" cat-file -t "$SOURCE_COMMIT")" == "commit" ]] || {
    printf 'Accepted source must identify a commit object\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" remote get-url origin)" == "$SOURCE_URL" ]] || {
    printf 'origin URL does not equal %s\n' "$SOURCE_URL" >&2
    exit 65
}

readonly -a BUILD_PATHS=(
    .dockerignore
    Dockerfile
    README.md
    config
    dewey_service
    docker/entrypoint.sh
    pyproject.toml
    uv.lock
)

git_blob_sha256() {
    local path="$1"
    git -C "$REPO" show "${SOURCE_COMMIT}:${path}" | sha256sum | sed 's/[[:space:]].*$//'
}
[[ "$(git_blob_sha256 Dockerfile)" == "$SOURCE_DOCKERFILE_SHA256" ]] || {
    printf 'Source Dockerfile SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(git_blob_sha256 pyproject.toml)" == "$PYPROJECT_SHA256" ]] || {
    printf 'pyproject.toml SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(git_blob_sha256 uv.lock)" == "$UV_LOCK_SHA256" ]] || {
    printf 'uv.lock SHA256 mismatch\n' >&2
    exit 66
}

readonly SOURCE_TREE="$(git -C "$REPO" rev-parse "${SOURCE_COMMIT}^{tree}")"
readonly SOURCE_SHORT="${SOURCE_COMMIT:0:12}"
readonly IMAGE_TAG="${RELEASE_VERSION}-${SOURCE_SHORT}"
readonly CONTEXT_NAME="dewey-${RELEASE_VERSION}-${SOURCE_SHORT}-source-context.tar.gz"
mkdir -- "$OUTPUT_DIR"

git -C "$REPO" ls-tree -r --full-tree "$SOURCE_COMMIT" -- "${BUILD_PATHS[@]}" \
    > "${OUTPUT_DIR}/build-inputs.git-ls-tree"
readonly BUILD_INPUTS_SHA256="$(sha256sum \
    "${OUTPUT_DIR}/build-inputs.git-ls-tree" | sed 's/[[:space:]].*$//')"
readonly BUILD_INPUT_COUNT="$(wc -l < \
    "${OUTPUT_DIR}/build-inputs.git-ls-tree" | sed 's/[[:space:]]//g')"

git -C "$REPO" archive --format=tar "$SOURCE_COMMIT" "${BUILD_PATHS[@]}" \
    | gzip -n > "${OUTPUT_DIR}/${CONTEXT_NAME}"
readonly CONTEXT_SHA256="$(sha256sum \
    "${OUTPUT_DIR}/${CONTEXT_NAME}" | sed 's/[[:space:]].*$//')"
readonly CONTEXT_BYTES="$(wc -c < \
    "${OUTPUT_DIR}/${CONTEXT_NAME}" | sed 's/[[:space:]]//g')"

cp -- "$RELEASE_DOCKERFILE_TEMPLATE" "${OUTPUT_DIR}/Dockerfile.release"
sed \
    -e "s|@@SOURCE_COMMIT@@|${SOURCE_COMMIT}|g" \
    -e "s|@@SOURCE_TREE@@|${SOURCE_TREE}|g" \
    -e "s|@@CONTEXT_NAME@@|${CONTEXT_NAME}|g" \
    -e "s|@@CONTEXT_SHA256@@|${CONTEXT_SHA256}|g" \
    -e "s|@@IMAGE_TAG@@|${IMAGE_TAG}|g" \
    "$BUILD_TEMPLATE" > "${OUTPUT_DIR}/build-smoke-push-linux-amd64.sh"
chmod 0755 "${OUTPUT_DIR}/build-smoke-push-linux-amd64.sh"
if grep -Eq '@@[A-Z_]+@@' "${OUTPUT_DIR}/build-smoke-push-linux-amd64.sh"; then
    printf 'Generated build script retained a template placeholder\n' >&2
    exit 66
fi

readonly GENERATED_SCRIPT_SHA256="$(sha256sum \
    "${OUTPUT_DIR}/build-smoke-push-linux-amd64.sh" | sed 's/[[:space:]].*$//')"
readonly GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
    printf '{\n'
    printf '  "generated_at": "%s",\n' "$GENERATED_AT"
    printf '  "capsule_role": "accepted-source-candidate",\n'
    printf '  "release_version": "%s",\n' "$RELEASE_VERSION"
    printf '  "source_commit": "%s",\n' "$SOURCE_COMMIT"
    printf '  "source_tree": "%s",\n' "$SOURCE_TREE"
    printf '  "source_url": "%s",\n' "$SOURCE_URL"
    printf '  "build_inputs_manifest": "build-inputs.git-ls-tree",\n'
    printf '  "build_inputs_sha256": "%s",\n' "$BUILD_INPUTS_SHA256"
    printf '  "build_input_count": %s,\n' "$BUILD_INPUT_COUNT"
    printf '  "context_archive": "%s",\n' "$CONTEXT_NAME"
    printf '  "context_sha256": "%s",\n' "$CONTEXT_SHA256"
    printf '  "context_bytes": %s,\n' "$CONTEXT_BYTES"
    printf '  "source_dockerfile_sha256": "%s",\n' "$SOURCE_DOCKERFILE_SHA256"
    printf '  "pyproject_sha256": "%s",\n' "$PYPROJECT_SHA256"
    printf '  "uv_lock_sha256": "%s",\n' "$UV_LOCK_SHA256"
    printf '  "release_dockerfile_sha256": "%s",\n' "$RELEASE_DOCKERFILE_SHA256"
    printf '  "build_template_sha256": "%s",\n' "$BUILD_TEMPLATE_SHA256"
    printf '  "build_script_sha256": "%s",\n' "$GENERATED_SCRIPT_SHA256"
    printf '  "target_platform": "linux/amd64",\n'
    printf '  "image_repository": "%s",\n' "$IMAGE_REPOSITORY"
    printf '  "image_tag": "%s",\n' "$IMAGE_TAG"
    printf '  "image_ref": "%s:%s",\n' "$IMAGE_REPOSITORY" "$IMAGE_TAG"
    printf '  "oci_version": "%s",\n' "$RELEASE_VERSION"
    printf '  "oci_revision": "%s",\n' "$SOURCE_COMMIT"
    printf '  "oci_source": "%s"\n' "$SOURCE_URL"
    printf '}\n'
} > "${OUTPUT_DIR}/capsule-inputs.json"

(
    cd "$OUTPUT_DIR"
    sha256sum \
        "$CONTEXT_NAME" \
        build-inputs.git-ls-tree \
        Dockerfile.release \
        build-smoke-push-linux-amd64.sh \
        capsule-inputs.json \
        > SHA256SUMS
)

printf 'capsule_status=prepared\n'
printf 'output_dir=%s\n' "$OUTPUT_DIR"
printf 'qualified_source_commit=%s\n' "$SOURCE_COMMIT"
printf 'qualified_source_tree=%s\n' "$SOURCE_TREE"
printf 'qualified_build_inputs_sha256=%s\n' "$BUILD_INPUTS_SHA256"
printf 'context_sha256=%s\n' "$CONTEXT_SHA256"
printf 'build_script_sha256=%s\n' "$GENERATED_SCRIPT_SHA256"
printf 'image_ref=%s:%s\n' "$IMAGE_REPOSITORY" "$IMAGE_TAG"
printf 'next=%s/build-smoke-push-linux-amd64.sh --receipt-dir /absolute/absent/receipt --push\n' \
    "$OUTPUT_DIR"
