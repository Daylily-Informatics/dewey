# Dewey 9.0.0 final image capsule generator

Prepared 2026-09-11T07:11:58Z after the qualified candidate image completed
its corrected smoke and ECR publication. This generator performs no build,
publish, tag, merge, deployment or production action. O remains responsible for
the final clean `main` merge, annotated numeric tag, capsule generation, native
image build/publication and controlling-ledger evidence.

## Purpose and boundary

`evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh`
accepts the future exact release commit instead of embedding an unknown SHA now.
Its SHA256 is
`76c970aa4fb8d1e94d8bc122d94c66383cfc8ea41d7fac82941b37b60c71f31f`.
It will generate a self-contained final source context, digest-pinned release
Dockerfile, corrected build/smoke/publish script, input manifest and checksum
file. It neither resolves nor selects a current/latest release.

The generator requires all of these before creating output:

1. An explicit absolute Dewey repository root with a clean worktree on `main`.
2. Exact agreement among `HEAD`, `origin/main`, the supplied 40-character
   release commit and the peeled commit of annotated tag `9.0.0`.
3. Exact origin URL `https://github.com/lsmc-bio/dewey.git`.
4. Qualified source commit `c484c95768a4147acdcabd12a2da0332c4c750dc`
   as an ancestor.
5. No content or mode difference from that qualified commit across every build
   input: `.dockerignore`, `Dockerfile`, `README.md`, `config/`,
   `dewey_service/`, `docker/entrypoint.sh`, `pyproject.toml`, and `uv.lock`.
6. Exact known Dockerfile, project and frozen-lock hashes plus qualified build
   template and pinned-Dockerfile hashes.
7. One explicit ECR tag: numeric `9.0.0` or the exact 40-character release SHA.
   Any other tag, including `latest`, fails.
8. An absent absolute output directory.

Because the application, complete build context and frozen lock must remain
identical to the qualified candidate, the final native build may reuse Docker's
existing cached layers. The generated context and image still bind the final
release commit: the context is archived from that exact commit, the build script
records its context SHA256, and `org.opencontainers.image.revision` uses the
final SHA. A final image build is therefore still required even when every
application layer is cached.

## Exact generation invocation

After O merges the accepted release to clean local `main`, synchronizes
`origin/main`, and creates annotated tag `9.0.0` on that same commit:

```bash
./docs/plans/evidence/20260911_dewey_900_final_release_generator/generate-final-release-capsule.sh \
  --repo /absolute/path/to/clean/dewey \
  --release-commit <exact-40-character-main-release-commit> \
  --image-tag 9.0.0 \
  --output-dir /absolute/absent/path/dewey-9.0.0-final-image-capsule
```

To use the release SHA as the ECR tag instead, supply that same exact
40-character value to both `--release-commit` and `--image-tag`. The generator
does not create multiple tags or aliases.

The successful generator output prints the exact capsule path, release commit,
context SHA256, generated-script SHA256, image reference and next command. On a
native `x86_64` Linux builder, O then verifies `SHA256SUMS` and runs the printed
command with a new absolute receipt directory and `--push`.

## Generated build behavior

The emitted script reuses the qualified complete-image recipe with:

- Python 3.12 and `SETUPTOOLS_SCM_PRETEND_VERSION=9.0.0`;
- frozen `daylily-tapdb[aurora,gui]==10.1.1rc1` and
  `meridian-euid==0.4.8`;
- exact `linux/amd64` builder and runtime manifest pins;
- OCI version `9.0.0`, exact final revision SHA and verified source URL;
- explicit `DEWEY_DEPLOYMENT_CODE=dewey900-image-smoke` for package and CLI
  smoke imports;
- package, interpreter, platform, label, image-user, CLI and runtime-file checks;
- an absent receipt-directory requirement;
- a fail-closed ECR tag-existence check before publication; and
- immutable pushed-digest receipts with no `latest` tag or fallback tag.

`DEWEY_BUILD_SHA` and `LSMC_RELEASE_SHA` remain deployment inputs. O must set
both to the exact final release commit in the reviewed runtime definition.

## Current evidence and remaining gate

O reported the qualified candidate resume completed at 2026-09-11T07:03:13Z
with package and CLI checks passing. PR 13 CI reported 427 passed, 2 skipped and
all jobs green. Application source, `uv.lock` and Dockerfile remain unchanged
from `c484c95768a4147acdcabd12a2da0332c4c750dc`. Those are coordinator inputs;
this local preparation did not requery GitHub, run a test suite, or run Docker.

The actual final commit does not exist yet. Final source context SHA, generated
script SHA, image ID and immutable ECR digest intentionally remain future
receipts produced only after accepted `main` and tag `9.0.0` exist.
