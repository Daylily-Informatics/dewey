# Dewey 9.0.0 single final image handoff

This handoff replaces another intermediate candidate build. The accepted
application source is fixed below; the final release commit remains pending the
current CI result and clean `main` merge/tag. O builds and publishes exactly one
new image from that final commit.

## Qualified application source

| Field | Exact value |
| --- | --- |
| Source commit | `2eb8615be1afdfde3f423d540e1585baaca67962` |
| Source tree | `aad8b23625474462836f673f6299ab001c6b365d` |
| Selected build-input manifest SHA256 | `3a82a20469bfa0a0a5dff91160347f4f550e4b64a597702d228a08f47bf17193` |
| Selected build inputs | `.dockerignore`, `Dockerfile`, `README.md`, `config`, `dewey_service`, `docker/entrypoint.sh`, `pyproject.toml`, `uv.lock` |
| Generator | `docs/plans/evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh`; SHA256 `5aae4715013437824543c7005650d0a5f52be19410b9ef1e9eaf19c7f4708491` |

The selected-build manifest differs from the earlier accepted source because
`dewey_service/services/search.py` received the accepted formatting-only
change. The final generator must therefore use the manifest above. It requires
that the qualified source is an ancestor of the final release and that the
final selected-build manifest remains exactly identical.

## Generate the only new image capsule

After CI passes, merge to clean `main`, push, and create the annotated numeric
tag `9.0.0` on that exact commit. Set `FINAL_MAIN_SHA` to the resulting full
40-character SHA. Then run:

```bash
set -euo pipefail
FINAL_MAIN_SHA=<FINAL_MAIN_SHA>
FINAL_OUTPUT=/absolute/absent/path/dewey-9.0.0-final-image-capsule
./docs/plans/evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh \
  --repo /absolute/path/to/clean/dewey-main \
  --release-commit "$FINAL_MAIN_SHA" \
  --qualified-source-commit 2eb8615be1afdfde3f423d540e1585baaca67962 \
  --qualified-source-tree aad8b23625474462836f673f6299ab001c6b365d \
  --qualified-build-inputs-sha256 3a82a20469bfa0a0a5dff91160347f4f550e4b64a597702d228a08f47bf17193 \
  --image-tag 9.0.0 \
  --output-dir "$FINAL_OUTPUT"
```

The generator fails unless `HEAD`, `origin/main`, and the peeled annotated tag
all equal `FINAL_MAIN_SHA`. Any selected application, config, Dockerfile,
entrypoint, project, or lock-file difference after the qualified source also
fails. Release-only documentation, test, and operator-helper changes do not
alter the selected build-input manifest.

## Native build and publication

O stages the generated final directory under the existing private root, then
uses the retained interactive SSM 30715 session and `image-build` tmux pane:

```bash
set -euo pipefail
umask 077
ROOT=/home/ubuntu/dewey_ops/tapdb101-20260911
FINAL_MAIN_SHA=<FINAL_MAIN_SHA>
FINAL_SHORT="${FINAL_MAIN_SHA:0:12}"
IMAGE_CAPSULE="$ROOT/image-final-9.0.0-$FINAL_SHORT"
IMAGE_RECEIPT="$ROOT/receipts/image-final-9.0.0-$FINAL_SHORT"
test -d "$ROOT/venv"
test -d "$IMAGE_CAPSULE"
test ! -e "$IMAGE_RECEIPT"
cd "$IMAGE_CAPSULE"
sha256sum --check SHA256SUMS
./build-smoke-push-linux-amd64.sh --receipt-dir "$IMAGE_RECEIPT" --push
```

The generated script builds `linux/amd64`, checks Dewey `9.0.0`, exact
`daylily-tapdb[aurora,gui]==10.1.1rc1`, Meridian `0.4.8`, Python 3.12, CLI
startup, runtime user/filesystem, and OCI source/version/revision before push.
It refuses to overwrite an existing `9.0.0` ECR tag.

## Final isolated-launch pin

After `FINAL_MAIN_SHA` is known, update the rehearsal source pin in
`scripts/dewey_launch_environment_prepare.py` and the source/container/capsule/
state/output/helper paths in
`docs/plans/20260911T071653Z_dewey_application_acceptance_capsule.md` to that
exact SHA and its 12-character prefix. Do not use `2eb8615...` as an image pin
and do not build an intermediate image from it.

Keep the image digest unset until the final build/push receipt returns the
immutable ECR manifest digest. O then supplies that exact digest to the isolated
launch without embedding it in the helper. The existing owning authentication
environment, eight host mappings, read-only Dewey/TapDB runtime config mounts,
and absent NCBI mount remain unchanged.

## Current boundary

Prepared only. No image was built or published, no release tag was created, no
launch helper was repinned, and no production or database state changed.
