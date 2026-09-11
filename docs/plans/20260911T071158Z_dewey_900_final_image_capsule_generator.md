# Dewey 9.0.0 post-fix candidate and final image capsules

Updated 2026-09-11 for the E-accepted native-reference application source. The
old images, stopped candidates, capsules, tags and receipts remain retained.
This workflow prepares a new complete image from the accepted source; it does
not use a package overlay or overwrite any old artifact.

Neither generator runs Docker, pushes ECR, tags Git, merges, deploys or changes
production. O owns the native build/publication and all final release actions.

## Exact accepted source capsule

`evidence/20260911_dewey_900_postfix_image_generator/generate-accepted-source-capsule.sh`
accepts an explicit clean source revision and generates a complete Docker build
context, selected-build-input manifest, pinned release Dockerfile, corrected
build/smoke/push script, provenance manifest and `SHA256SUMS`. It derives the
candidate tag as `9.0.0-<12-character-source-prefix>` and refuses reuse through
the build script's existing ECR tag check.

The generator does not compare application source with the obsolete candidate.
It pins the accepted commit and tree directly while retaining exact hashes for
the unchanged Dockerfile, `pyproject.toml` and frozen `uv.lock`. The release
Dockerfile retains exact builder/runtime manifest digests. Its build script
retains the corrected `DEWEY_DEPLOYMENT_CODE=dewey900-image-smoke` package and
CLI checks.

O supplied this clean accepted source:

| Field | Exact value |
| --- | --- |
| Source commit | `5f51f8137d7bd2d4e2668593df5cc492b390a4b8` |
| Source tree | `87bcaef591365182adc757ec12fc682dd5a15a9a` |
| Accepted app source | D `0f3509cefe4df4a326403af9d2268ca8f2c6cda6`, merged normally before the controlling source revision |
| Native adapter | `dewey_service/integrations/tapdb_external_references.py`; SHA256 `f433e4a3382ba5738cf4d75de00c1d5e254e8f3420db2387b73357825503d298` |
| Accepted-source generator | SHA256 `d51e8bec0a25b2ec986cd71b2ff4735cb8f787a05f119ea57b8ca9b4a50414dd` |
| Generic build template | SHA256 `49338d9a6a349b2877c284f81930f330f0a2c617146d631afcf60fdce5249430` |
| Build-input manifest | SHA256 `99ff4efc3992f6826adf865b3e2184b304b60a8d3fe35cf6aae0a05dd4101665`; 80 files |
| Source context | `dewey-9.0.0-5f51f8137d7b-source-context.tar.gz`; SHA256 `5a738e33b049d1f408e3890b7b4382ed7bc084142fe615365349d1d8fa58a280`; 316,742 bytes |
| Candidate build script | SHA256 `d8939f5995aea230ec1f299220fc6ff464ba44412b203ec2badd41760dd188c6` |
| Candidate image tag | `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey:9.0.0-5f51f8137d7b` |

The generated capsule is
`evidence/20260911_dewey_900_postfix_image_generator/candidate-5f51f8137d7b/`.
On the native `linux/amd64` builder, verify its `SHA256SUMS`, then run:

```bash
./build-smoke-push-linux-amd64.sh \
  --receipt-dir /absolute/absent/private/path/dewey-9.0.0-5f51f8137d7b-receipt \
  --push
```

The complete build must precede the new isolated application acceptance. A
successful build or package smoke does not close that application gate.

O stages the generated directory and the updated environment helper into the
existing private root. In the retained interactive SSM 30715 session and its
`image-build` tmux pane, use these exact remote paths and require every staged
hash before running the build:

```bash
set -euo pipefail
umask 077
ROOT=/home/ubuntu/dewey_ops/tapdb101-20260911
IMAGE_CAPSULE="$ROOT/image-candidate-5f51f8137d7b"
IMAGE_RECEIPT="$ROOT/receipts/image-candidate-5f51f8137d7b"
LAUNCH_HELPER="$ROOT/dewey_launch_environment_prepare_5f51f8137d7b.py"
test -d "$ROOT"
test -d "$ROOT/venv"
test -d "$IMAGE_CAPSULE"
test ! -e "$IMAGE_RECEIPT"
test -f "$LAUNCH_HELPER"
cd "$IMAGE_CAPSULE"
sha256sum --check SHA256SUMS
test "$(sha256sum "$LAUNCH_HELPER" | cut -d ' ' -f 1)" = "528d963b9da6a4c56688be48248f29c837d2723d34dc34c6475ba630993600dc"
test "$(stat -c '%a' "$IMAGE_CAPSULE/build-smoke-push-linux-amd64.sh")" = 755
./build-smoke-push-linux-amd64.sh --receipt-dir "$IMAGE_RECEIPT" --push
```

The image build receives no runtime credentials or database config. The updated
helper is invoked later through the existing operator venv by the isolated
application recipe. Its digest remains an unset required input until the
build/push receipt returns an immutable ECR manifest digest.

## Final image generator

`evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh`
still requires clean synchronized `main`, an annotated numeric `9.0.0` tag and
an exact final release commit. It now also requires three explicit values from
the accepted post-fix candidate capsule: source commit, source tree and selected
build-input manifest SHA256. The updated generator SHA256 is
`5aae4715013437824543c7005650d0a5f52be19410b9ef1e9eaf19c7f4708491`.

The generator requires all of these before creating output:

1. An explicit absolute Dewey repository root with a clean worktree on `main`.
2. Exact agreement among `HEAD`, `origin/main`, the supplied 40-character final
   commit and the peeled commit of annotated tag `9.0.0`.
3. Exact origin URL `https://github.com/lsmc-bio/dewey.git`.
4. The explicit qualified source commit as an ancestor of the final commit and
   its Git tree equal to the explicit qualified tree.
5. The qualified commit's selected build-input manifest equal to the supplied
   SHA256, and the final commit's selected build-input manifest equal to it.
6. Exact known Dockerfile, project, frozen-lock, build-template and release-
   Dockerfile hashes.
7. One explicit ECR tag: numeric `9.0.0` or the exact final 40-character SHA.
   Any other tag, including `latest`, fails.
8. An absent absolute output directory.

This permits release-only docs and operational records after candidate
acceptance while preventing any unqualified application, config, Dockerfile,
entrypoint or dependency input from entering the final image. Docker may reuse
layers, but the generated context and OCI revision always bind to the exact
final release commit and a new complete image build remains required.

After accepted application evidence, clean-main merge and annotated tag:

```bash
./docs/plans/evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh \
  --repo /absolute/path/to/clean/dewey \
  --release-commit <exact-40-character-main-release-commit> \
  --qualified-source-commit 5f51f8137d7bd2d4e2668593df5cc492b390a4b8 \
  --qualified-source-tree 87bcaef591365182adc757ec12fc682dd5a15a9a \
  --qualified-build-inputs-sha256 99ff4efc3992f6826adf865b3e2184b304b60a8d3fe35cf6aae0a05dd4101665 \
  --image-tag 9.0.0 \
  --output-dir /absolute/absent/path/dewey-9.0.0-final-image-capsule
```

To use the final SHA as the ECR tag, supply the same exact 40-character value to
`--release-commit` and `--image-tag`. The generator never selects a current,
latest or alternate tag and never creates multiple tags.

## Rehearsal identity pins

The following source-specific rehearsal inputs now use the new candidate SHA.
The pushed digest remains unset until O has a verified publication receipt:

| Input | Prepared value | Required disposition |
| --- | --- | --- |
| `scripts/dewey_launch_environment_prepare.py` `REHEARSAL_IMAGE_SHA` | `5f51f8137d7bd2d4e2668593df5cc492b390a4b8` | Prepared; exact accepted source |
| `docs/plans/20260911T071653Z_dewey_application_acceptance_capsule.md` candidate source/SHA | `5f51f8137d7bd2d4e2668593df5cc492b390a4b8` | Prepared; exact accepted source |
| Same acceptance recipe candidate digest and container/capsule paths | digest remains a required unset operator input; paths use `5f51f8137d7b` | O substitutes only the verified immutable digest after publication |

`docs/plans/evidence/20260911_dewey_rc_inventory/rehearsal-launch-environment.json`
is a historical receipt and remains unchanged. The HTTP acceptance program
already accepts explicit `--image-sha` and `--image-digest`; it has no embedded
candidate identity.

## Remaining gates

The new candidate is prepared, not built or published. O must retain native
build, package/CLI smoke, pushed immutable digest and isolated application
acceptance receipts. The accepted source CI result remains a separate gate. Only
after those pass may the accepted build-input identity feed the clean-main/tag
final generator. Production remains unchanged by these generators.
