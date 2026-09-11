# Dewey 9.0.0 post-fix candidate and final image capsules

Updated 2026-09-11 after the first published candidate reached Dewey startup
and exposed an application integration error before HTTP service or writes. The
old image, stopped failed container, capsule, tag and receipts remain retained.
This workflow prepares a new complete image from the E-accepted source fix; it
does not use a package overlay or overwrite any old artifact.

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
| Source commit | `c6406b8ffb40e58feaba31e2163d77448d47698c` |
| Source tree | `d234131c0943ead5d17c5fbc097620c976782d78` |
| Accepted app fix | D `5251d1e6a42452284b36dc511c73b1446ff21ee0`, merged normally before the controlling source revision |
| Changed image input | `dewey_service/integrations/tapdb_runtime.py`; SHA256 `91fa5122a22cfa5cb00f83055a26d099324ca77e258f6c3bdd665f62e6a76fa4` |
| Accepted-source generator | SHA256 `d51e8bec0a25b2ec986cd71b2ff4735cb8f787a05f119ea57b8ca9b4a50414dd` |
| Generic build template | SHA256 `49338d9a6a349b2877c284f81930f330f0a2c617146d631afcf60fdce5249430` |
| Build-input manifest | SHA256 `c6424e0062c08aedbe26315d0037a7b8c48d86d340ca0cca6416f52c03f6a771`; 79 files |
| Source context | `dewey-9.0.0-c6406b8ffb40-source-context.tar.gz`; SHA256 `8cd3cea268632e8a6c173d60fca88319b1c444dc3a241e5a0d53367a9ac4fc9a`; 315,059 bytes |
| Candidate build script | SHA256 `a4bda13ef1dae9709da2c2d48ae34e311f12ee935b529d6f35c1bc077b211a2f` |
| Candidate image tag | `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey:9.0.0-c6406b8ffb40` |

The generated capsule is
`evidence/20260911_dewey_900_postfix_image_generator/candidate-c6406b8ffb40/`.
On the native `linux/amd64` builder, verify its `SHA256SUMS`, then run:

```bash
./build-smoke-push-linux-amd64.sh \
  --receipt-dir /absolute/absent/private/path/dewey-9.0.0-c6406b8ffb40-receipt \
  --push
```

The complete build must precede the new isolated application acceptance. A
successful build or package smoke does not close that application gate.

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
  --qualified-source-commit c6406b8ffb40e58feaba31e2163d77448d47698c \
  --qualified-source-tree d234131c0943ead5d17c5fbc097620c976782d78 \
  --qualified-build-inputs-sha256 c6424e0062c08aedbe26315d0037a7b8c48d86d340ca0cca6416f52c03f6a771 \
  --image-tag 9.0.0 \
  --output-dir /absolute/absent/path/dewey-9.0.0-final-image-capsule
```

To use the final SHA as the ECR tag, supply the same exact 40-character value to
`--release-commit` and `--image-tag`. The generator never selects a current,
latest or alternate tag and never creates multiple tags.

## Rehearsal identity pins owned by D/O

The following source-specific rehearsal inputs must use the new candidate SHA
and eventual pushed digest before the new acceptance launch. Packaging does not
edit these D-owned inputs:

| Input | Current obsolete identity | Required disposition |
| --- | --- | --- |
| `scripts/dewey_launch_environment_prepare.py` `REHEARSAL_IMAGE_SHA` | `c484c95768a4147acdcabd12a2da0332c4c750dc` | Pin `c6406b8ffb40e58feaba31e2163d77448d47698c` |
| `docs/plans/20260911T071653Z_dewey_application_acceptance_capsule.md` candidate source/SHA | `c484c95768a4147acdcabd12a2da0332c4c750dc` | Pin the new source SHA |
| Same acceptance recipe candidate digest and container/capsule paths | old published digest and old names | Pin the new immutable digest and fresh `dewey-tapdb10-rehearsal-c6406b8ffb40` lane paths |

`docs/plans/evidence/20260911_dewey_rc_inventory/rehearsal-launch-environment.json`
is a historical receipt and remains unchanged. The HTTP acceptance program
already accepts explicit `--image-sha` and `--image-digest`; it has no embedded
candidate identity.

## Remaining gates

The new candidate is prepared, not built or published. O must retain native
build, package/CLI smoke, pushed immutable digest and isolated application
acceptance receipts. CI run `34579850198` is a separate source-change gate. Only
after those pass may the accepted build-input identity feed the clean-main/tag
final generator. Production remains unchanged by these generators.
