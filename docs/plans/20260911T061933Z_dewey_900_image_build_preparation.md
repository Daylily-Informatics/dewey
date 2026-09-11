# Dewey 9.0.0 complete-image build preparation

Prepared 2026-09-11T06:19:33Z from the coordinator integration commit
`c484c95768a4147acdcabd12a2da0332c4c750dc`. This is the packaging lane for
the Dewey 9.0.0 release candidate. It does not replace the coordinator's
controlling ledger and does not authorize or record deployment, database work,
cutover, acceptance, a release tag, or a merge to `main`.

## Status

| Item | Status | Evidence |
| --- | --- | --- |
| Clean isolated source | Prepared | Worktree branch `codex/dewey-packaging-20260911`; source tree `b765812bcd8d41222e373d8a16b028a4cbba6f06` |
| Exact source context | Prepared | `evidence/20260911_dewey_900_image_build/dewey-9.0.0-c484c95768a4-source-context.tar.gz`; SHA256 `78b70410759ab4abc08e17da962f77fbcda638a920a4b80b4fc88c1caf0cbefe`; 314,972 bytes; 79 tracked files |
| Complete Dockerfile | Prepared | Source Dockerfile plus a release-only copy whose only changes are the two platform-specific base-image digest pins |
| Local image build | Not run | Local Docker client `29.5.2` found; default and Colima engines were unavailable. No engine was started. |
| Native build capsule | Prepared | `evidence/20260911_dewey_900_image_build/build-and-push-linux-amd64.sh`; SHA256 `254dda2cd40b915c3919dc4123b19d877307055b375514e82741afff5bd08b50` |
| Candidate image publish | Pending O | Exact candidate tag below; build capsule refuses an existing tag and records the immutable ECR digest after push |
| Production deployment/DB | Unchanged | No EC2, ECR, database, runtime config, Compose, release tag, or production operation was performed here |

## Exact build inputs

| Field | Value |
| --- | --- |
| Source repository | `https://github.com/lsmc-bio/dewey.git` |
| Source commit | `c484c95768a4147acdcabd12a2da0332c4c750dc` |
| Target | Native `linux/amd64` |
| Version argument | `SETUPTOOLS_SCM_PRETEND_VERSION=9.0.0` |
| Python argument | `PYTHON_VERSION=3.12` |
| Locked dependencies | `daylily-tapdb[aurora,gui]==10.1.1rc1`; `meridian-euid==0.4.8` |
| Builder base index | `ghcr.io/astral-sh/uv:0.5.30-python3.12-bookworm-slim@sha256:31c96c071fe7d89af0f35a174582d4b9ffbdec99e0f1eada7e692d8c7000f6ee` |
| Builder base `linux/amd64` | `sha256:dae7f9060850980a52f1c629f2e94024c7d267f506dbc465c170553200e19d9f` |
| Runtime base index | `python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254` |
| Runtime base `linux/amd64` | `sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef` |
| Candidate tag | `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey:9.0.0-c484c95768a4` |

The release Dockerfile pins the two `linux/amd64` manifest digests. A direct
diff against the source Dockerfile contains only those two `FROM` replacements.
The source context is produced by `git archive` from the exact integration
commit and contains only the files copied or evaluated by the complete image
build. It has no `.git`, test, plan, output, overlay, credential or runtime
configuration material.

The build supplies these exact OCI labels:

- `org.opencontainers.image.version=9.0.0`
- `org.opencontainers.image.revision=c484c95768a4147acdcabd12a2da0332c4c750dc`
- `org.opencontainers.image.source=https://github.com/lsmc-bio/dewey.git`

`DEWEY_BUILD_SHA` and `LSMC_RELEASE_SHA` are runtime deployment inputs and are
not baked into the image. O must set both to the same full source commit in the
candidate service definition.

## Native build and push capsule

Run the capsule only on O's designated non-service `x86_64` Linux build host
with a running native Docker engine and authorized ECR identity. Copy the entire
`evidence/20260911_dewey_900_image_build/` directory intact, verify
`SHA256SUMS`, and run:

```bash
sha256sum -c SHA256SUMS
./build-and-push-linux-amd64.sh \
  --receipt-dir /absolute/private/path/dewey-9.0.0-c484c95768a4-receipt \
  --push
```

The capsule fails before building unless the host and Docker engine are native
`x86_64`/`linux/x86_64`, the context/Dockerfile/source lock hashes match, and
the two base digest pins are intact. The receipt directory must be absent and
must not be a symlink; the capsule creates it once and refuses reuse. It performs
the complete frozen build,
checks `linux/amd64`, OCI labels, default image user, `/app/.venv` interpreter,
Dewey/TapDB/Meridian/Python versions, TapDB runtime version guard, CLI help and
absence of runtime Git. It then fails closed if the candidate ECR tag already
exists, pushes, reads the immutable ECR digest, and writes nonsecret receipts.

Required completion evidence for O:

1. `docker-build.log` terminates successfully.
2. `package-versions.json` reports Dewey `9.0.0`, TapDB `10.1.1rc1`, Meridian
   `0.4.8`, Python `3.12.x`, executable `/app/.venv/bin/python`.
3. `local-image-inspect.json` reports `linux/amd64`, user `lsmc`, and all three
   exact OCI labels.
4. `push-receipt.txt` reports `push_status=succeeded` and the immutable
   `IMAGE_REPOSITORY@sha256:...` reference.
5. `ecr-image.json` names the candidate tag and the same digest.

Only after those checks should O place the immutable digest reference into
`DEWEY_RELEASE_IMAGE` and set both runtime SHA variables in the reviewed
Dewey-only override. Deployment and populated-data acceptance remain separate
controlling-ledger gates.

## Validation performed here

- `bash -n build-and-push-linux-amd64.sh` passed.
- Source and release Dockerfiles differ only at the two digest-pinned `FROM`
  lines.
- `docker buildx imagetools inspect` resolved and recorded both base indexes and
  their `linux/amd64` manifests.
- A repeated `git archive ... | gzip -n` produces the recorded source-context
  SHA256.
- Existing affected test, Ruff, Bandit and frozen-install receipts were reused;
  no suite was rerun because this lane changes packaging evidence only.
- No complete image was built locally because no local engine was running.
