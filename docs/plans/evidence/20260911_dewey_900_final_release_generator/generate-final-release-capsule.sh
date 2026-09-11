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
readonly POSTFIX_GENERATOR_DIR="${SCRIPT_DIR}/../20260911_dewey_900_postfix_image_generator"
readonly BUILD_TEMPLATE="${POSTFIX_GENERATOR_DIR}/build-smoke-push-linux-amd64.template.sh"
readonly RELEASE_DOCKERFILE_TEMPLATE="${POSTFIX_GENERATOR_DIR}/Dockerfile.release"

usage() {
    printf '%s\n' \
        "Usage: $0 --repo /absolute/clean/main --release-commit <40 hex>" \
        "          --qualified-source-commit <40 hex> --qualified-source-tree <40 hex>" \
        "          --qualified-build-inputs-sha256 <64 hex>" \
        "          --image-tag <9.0.0 or exact release commit>" \
        "          --output-dir /absolute/absent/path" >&2
}

if [[ $# -ne 14 || "$1" != "--repo" || "$3" != "--release-commit" || \
    "$5" != "--qualified-source-commit" || "$7" != "--qualified-source-tree" || \
    "$9" != "--qualified-build-inputs-sha256" || "${11}" != "--image-tag" || \
    "${13}" != "--output-dir" ]]; then
    usage
    exit 64
fi
readonly REPO="$2"
readonly RELEASE_COMMIT="$4"
readonly QUALIFIED_SOURCE_COMMIT="$6"
readonly QUALIFIED_SOURCE_TREE="$8"
readonly QUALIFIED_BUILD_INPUTS_SHA256="${10}"
readonly IMAGE_TAG="${12}"
readonly OUTPUT_DIR="${14}"

if [[ "$REPO" != /* || ! -d "$REPO" ]]; then
    printf 'Repository must be an existing absolute directory: %s\n' "$REPO" >&2
    exit 64
fi
if [[ ! "$RELEASE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Release commit must be 40 lowercase hexadecimal characters\n' >&2
    exit 64
fi
if [[ ! "$QUALIFIED_SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Qualified source commit must be 40 lowercase hexadecimal characters\n' >&2
    exit 64
fi
if [[ ! "$QUALIFIED_SOURCE_TREE" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Qualified source tree must be 40 lowercase hexadecimal characters\n' >&2
    exit 64
fi
if [[ ! "$QUALIFIED_BUILD_INPUTS_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
    printf 'Qualified build-input SHA256 must be 64 lowercase hexadecimal characters\n' >&2
    exit 64
fi
if [[ "$IMAGE_TAG" != "$RELEASE_VERSION" && "$IMAGE_TAG" != "$RELEASE_COMMIT" ]]; then
    printf 'Image tag must be exactly %s or the exact release commit %s\n' \
        "$RELEASE_VERSION" "$RELEASE_COMMIT" >&2
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
    printf 'Qualified build template SHA256 mismatch\n' >&2
    exit 66
}
[[ "$(sha256sum "$RELEASE_DOCKERFILE_TEMPLATE" | sed 's/[[:space:]].*$//')" == \
    "$RELEASE_DOCKERFILE_SHA256" ]] || {
    printf 'Qualified release Dockerfile SHA256 mismatch\n' >&2
    exit 66
}

readonly REPO_ROOT="$(git -C "$REPO" rev-parse --show-toplevel)"
[[ "$REPO_ROOT" == "$REPO" ]] || {
    printf 'Pass the exact repository root; expected %s, received %s\n' "$REPO_ROOT" "$REPO" >&2
    exit 65
}
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || {
    printf 'Release repository is not clean\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" branch --show-current)" == "main" ]] || {
    printf 'Release repository must be on branch main\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$RELEASE_COMMIT" ]] || {
    printf 'HEAD does not equal the explicit release commit\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" rev-parse refs/remotes/origin/main)" == "$RELEASE_COMMIT" ]] || {
    printf 'origin/main does not equal the explicit release commit\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" remote get-url origin)" == "$SOURCE_URL" ]] || {
    printf 'origin URL does not equal %s\n' "$SOURCE_URL" >&2
    exit 65
}
[[ "$(git -C "$REPO" cat-file -t "$RELEASE_VERSION")" == "tag" ]] || {
    printf 'Release tag %s must be annotated\n' "$RELEASE_VERSION" >&2
    exit 65
}
[[ "$(git -C "$REPO" rev-parse "${RELEASE_VERSION}^{commit}")" == "$RELEASE_COMMIT" ]] || {
    printf 'Release tag %s does not peel to the explicit release commit\n' "$RELEASE_VERSION" >&2
    exit 65
}
git -C "$REPO" merge-base --is-ancestor "$QUALIFIED_SOURCE_COMMIT" "$RELEASE_COMMIT" || {
    printf 'Qualified source commit is not an ancestor of the release commit\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" cat-file -t "$QUALIFIED_SOURCE_COMMIT")" == "commit" ]] || {
    printf 'Qualified source must identify a commit object\n' >&2
    exit 65
}
[[ "$(git -C "$REPO" rev-parse "${QUALIFIED_SOURCE_COMMIT}^{tree}")" == \
    "$QUALIFIED_SOURCE_TREE" ]] || {
    printf 'Qualified source tree does not match its explicit commit\n' >&2
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
readonly QUALIFIED_BUILD_INPUTS_ACTUAL="$(git -C "$REPO" ls-tree -r --full-tree \
    "$QUALIFIED_SOURCE_COMMIT" -- "${BUILD_PATHS[@]}" | sha256sum | \
    sed 's/[[:space:]].*$//')"
[[ "$QUALIFIED_BUILD_INPUTS_ACTUAL" == "$QUALIFIED_BUILD_INPUTS_SHA256" ]] || {
    printf 'Qualified source build-input manifest does not match explicit SHA256\n' >&2
    exit 66
}
readonly RELEASE_BUILD_INPUTS_SHA256="$(git -C "$REPO" ls-tree -r --full-tree \
    "$RELEASE_COMMIT" -- "${BUILD_PATHS[@]}" | sha256sum | \
    sed 's/[[:space:]].*$//')"
[[ "$RELEASE_BUILD_INPUTS_SHA256" == "$QUALIFIED_BUILD_INPUTS_SHA256" ]] || {
    printf 'Release build inputs differ from the accepted source capsule\n' >&2
    exit 66
}

git_blob_sha256() {
    local path="$1"
    git -C "$REPO" show "${RELEASE_COMMIT}:${path}" | sha256sum | sed 's/[[:space:]].*$//'
}
[[ "$(git_blob_sha256 Dockerfile)" == "$SOURCE_DOCKERFILE_SHA256" ]]
[[ "$(git_blob_sha256 pyproject.toml)" == "$PYPROJECT_SHA256" ]]
[[ "$(git_blob_sha256 uv.lock)" == "$UV_LOCK_SHA256" ]]

readonly RELEASE_TREE="$(git -C "$REPO" rev-parse "${RELEASE_COMMIT}^{tree}")"
readonly RELEASE_SHORT="${RELEASE_COMMIT:0:12}"
readonly CONTEXT_NAME="dewey-${RELEASE_VERSION}-${RELEASE_SHORT}-source-context.tar.gz"
mkdir -- "$OUTPUT_DIR"
git -C "$REPO" ls-tree -r --full-tree "$RELEASE_COMMIT" -- "${BUILD_PATHS[@]}" \
    > "${OUTPUT_DIR}/build-inputs.git-ls-tree"
git -C "$REPO" archive --format=tar "$RELEASE_COMMIT" "${BUILD_PATHS[@]}" \
    | gzip -n > "${OUTPUT_DIR}/${CONTEXT_NAME}"
readonly CONTEXT_SHA256="$(sha256sum "${OUTPUT_DIR}/${CONTEXT_NAME}" | sed 's/[[:space:]].*$//')"
readonly CONTEXT_BYTES="$(wc -c < "${OUTPUT_DIR}/${CONTEXT_NAME}" | sed 's/[[:space:]]//g')"
readonly CONTEXT_FILE_COUNT="$(git -C "$REPO" ls-tree -r --name-only "$RELEASE_COMMIT" -- \
    "${BUILD_PATHS[@]}" | wc -l | sed 's/[[:space:]]//g')"

cp -- "$RELEASE_DOCKERFILE_TEMPLATE" "${OUTPUT_DIR}/Dockerfile.release"
sed \
    -e "s|@@SOURCE_COMMIT@@|${RELEASE_COMMIT}|g" \
    -e "s|@@SOURCE_TREE@@|${RELEASE_TREE}|g" \
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
    printf '  "release_version": "%s",\n' "$RELEASE_VERSION"
    printf '  "release_commit": "%s",\n' "$RELEASE_COMMIT"
    printf '  "release_tree": "%s",\n' "$RELEASE_TREE"
    printf '  "annotated_tag": "%s",\n' "$RELEASE_VERSION"
    printf '  "source_url": "%s",\n' "$SOURCE_URL"
    printf '  "qualified_source_commit": "%s",\n' "$QUALIFIED_SOURCE_COMMIT"
    printf '  "qualified_source_tree": "%s",\n' "$QUALIFIED_SOURCE_TREE"
    printf '  "qualified_build_inputs_sha256": "%s",\n' \
        "$QUALIFIED_BUILD_INPUTS_SHA256"
    printf '  "qualified_build_inputs_identical": true,\n'
    printf '  "build_inputs_manifest": "build-inputs.git-ls-tree",\n'
    printf '  "build_inputs_sha256": "%s",\n' "$RELEASE_BUILD_INPUTS_SHA256"
    printf '  "context_archive": "%s",\n' "$CONTEXT_NAME"
    printf '  "context_sha256": "%s",\n' "$CONTEXT_SHA256"
    printf '  "context_bytes": %s,\n' "$CONTEXT_BYTES"
    printf '  "context_file_count": %s,\n' "$CONTEXT_FILE_COUNT"
    printf '  "release_dockerfile_sha256": "%s",\n' "$RELEASE_DOCKERFILE_SHA256"
    printf '  "build_script_sha256": "%s",\n' "$GENERATED_SCRIPT_SHA256"
    printf '  "target_platform": "linux/amd64",\n'
    printf '  "image_repository": "%s",\n' "$IMAGE_REPOSITORY"
    printf '  "image_tag": "%s",\n' "$IMAGE_TAG"
    printf '  "image_ref": "%s:%s",\n' "$IMAGE_REPOSITORY" "$IMAGE_TAG"
    printf '  "oci_version": "%s",\n' "$RELEASE_VERSION"
    printf '  "oci_revision": "%s",\n' "$RELEASE_COMMIT"
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
printf 'release_commit=%s\n' "$RELEASE_COMMIT"
printf 'context_sha256=%s\n' "$CONTEXT_SHA256"
printf 'build_script_sha256=%s\n' "$GENERATED_SCRIPT_SHA256"
printf 'image_ref=%s:%s\n' "$IMAGE_REPOSITORY" "$IMAGE_TAG"
printf 'next=%s/build-smoke-push-linux-amd64.sh --receipt-dir /absolute/absent/receipt --push\n' \
    "$OUTPUT_DIR"
