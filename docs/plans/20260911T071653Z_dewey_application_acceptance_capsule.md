# Dewey isolated application acceptance commands

D preparation, 2026-09-11. O runs these only after the native copy/migration/
floor and [principal stages](20260911T070836Z_dewey_principal_capsule.md) pass.
Source stays stopped/closed throughout rehearsal and final. No additional backup
or inbox/outbox replay/retention gate is introduced. These commands were not
executed by D. This recipe now targets the complete rebuilt context-fix candidate;
O/F's new published image receipt owns its final digest:

- Manifest digest: required explicitly from the new O/F publication receipt.
- Image source revision: `c6406b8ffb40e58feaba31e2163d77448d47698c`.
- Dewey `9.0.0`, TapDB `10.1.1rc1`, Meridian `0.4.8`.

## 1. Prepare exact mounted capsule files and inputs

In an existing private operator directory, prepare an `application-acceptance-c6406b8ffb40`
subdirectory containing these exact reviewed, nonsecret repo files:

| Host basename | Repository file |
| --- | --- |
| `dewey_runtime_principal_prepare.py` | `scripts/dewey_runtime_principal_prepare.py` |
| `application_acceptance.py` | `docs/plans/20260911T070000Z_dewey_application_acceptance.py` |
| `fixture-inputs.json` | `docs/plans/20260911T061000Z_dewey_900_acceptance_inputs.json` |

Record file hashes. This capsule directory must contain no configs, operator
references or credentials. Prepare distinct new private existing state/output
directories, one per lane. Retain the resolver token at its existing protected
file; it is mounted separately and is never printed/copied into a receipt.

Retain the failed candidate container, old capsule directories and their receipts.
The new container/capsule/state/output/environment paths below must be absent before
O creates them with private permissions. Keep the original principal helper SHA256
`9921210bd5b3ee4fcc52f06184dd88a6efa986e23e608f3672ccffcd529372f2` for its prior
bootstrap/bind operations; only the new acceptance capsule uses the reviewed runtime
verification helper SHA256
`ed71f502750e4041c7b6cabe6b03e1c4e5134eb92f9cc06a8f017849d8961680`.

Use O's already preserved host manifest directly:
`/home/ubuntu/dewey_ops/tapdb101-20260911/fixtures/qeo-complete-multiqc-package-20260910.json`.
O verified SHA256 `4ed7e3e6938edb309a277042a42125d2ac58e99579809973e369054e1a67f4e9`
against the retained fixture after copying it from the stopped source container.
The separate read-only mount below needs no second manifest copy.

```bash
set -euo pipefail
umask 077
D_CONTAINER=dewey-tapdb10-rehearsal-c6406b8ffb40
D_LANE=rehearsal
D_RUNTIME_DIR=/opt/dewey/day/releases/tapdb10-rehearsal-20260911
D_CAPSULE_DIR=/home/ubuntu/dewey_ops/tapdb101-20260911/application-acceptance-c6406b8ffb40
D_IMAGE_SHA=c6406b8ffb40e58feaba31e2163d77448d47698c
: "${D_DIGEST:?Exact new published c6406b8ffb40 manifest digest from O/F receipt}"
: "${D_IMAGE_REPOSITORY:?Exact published repository from O/F image receipt}"
D_STATE_DIR=/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-application-state-c6406b8ffb40
D_OUTPUT_DIR=/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-application-c6406b8ffb40
D_LAUNCH_DIR=/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-launch-c6406b8ffb40
D_IMAGE="${D_IMAGE_REPOSITORY}@${D_DIGEST}"
test -z "$(ss -H -ltn 'sport = :18914')"
test -z "$(docker ps -aq --filter 'name=^/dewey-tapdb10-rehearsal-c6406b8ffb40$')"
```

The owning image inspection must match digest, source labels and package receipt
before launch. `--image-digest` below records the manifest digest, not Docker's
different image config ID. The capsule compares the running health build SHA
and package versions; it does not have Docker socket access to verify the
externally supplied manifest digest itself.

### Preserve the exact owning Compose environment before launch

The original recipe omitted deployed auth/product variables and `extra_hosts`.
This correction is mandatory. O prepares the reviewed host-only helper
`scripts/dewey_launch_environment_prepare.py` at the exact path below. Keep it
and its private output directory outside the mounted application capsule.

```bash
sudo /home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/python /home/ubuntu/dewey_ops/tapdb101-20260911/dewey_launch_environment_prepare_c6406b8ffb40.py --compose /opt/dayhoff/deployments/day/compose/docker-compose.yml --dewey-config "$D_RUNTIME_DIR/dewey-config.yaml" --lane "$D_LANE" --image-sha "$D_IMAGE_SHA" --output-dir "$D_LAUNCH_DIR"
```

Review the new `receipt.json` before proceeding. The helper pins owning Compose
SHA256 `35a37f2c5df1cc84ebfd57ad19a9d56b14f88b3e6bc322aebadd3db081da8509`,
requires the observed literal string environment mapping (no `env_file`,
`extends`, dollar interpolation, merged/duplicate keys or multiline values),
and writes exclusive mode-0600 `runtime.env`, `extra-hosts.args`, `receipt.json`.
All existing environment values are preserved except the fixed runtime identity,
private state/cache paths, disabled QEO dispatch and loopback overrides. No
credential value enters a command argument, receipt or terminal. Do not source
the env-file: Docker reads its literal `KEY=value` records directly.
`--image-sha` is required and must be exactly 40 lowercase hexadecimal characters.
Rehearsal requires the candidate SHA above. Production uses the exact final
source SHA supplied by O/F consistently in both environment labels and receipt;
the helper does not select a revision or independently prove image provenance.

Preserved fields include all `LSMC_AUTH_*` broker credentials/URLs,
`LSMC_AI_AGENT_*`, primary API/QEO resolver credentials, Atlas/Bloom URLs,
managed storage and AWS/OTEL settings. The source-backed credential selector is
explicitly the owning Compose **`DEWEY_API_BEARER_TOKEN`**. The helper privately
compares it to the new YAML `application.api_bearer_token` and records only
`yaml_primary_matches_deployed_environment`. A false result is retained for O's
review; it does not substitute the YAML value or add an approval gate. The
deployed nonempty environment primary remains unchanged. Dewey's
`load_settings()` applies `DEWEY_*` over YAML and nonempty `LSMC_AUTH_*` over auth.

```bash
mapfile -t D_HOST_ARGS < <(sudo cat "$D_LAUNCH_DIR/extra-hosts.args")
test "${#D_HOST_ARGS[@]}" -eq 8
```

These are the exact `login`, `atlas`, `bloom`, `ursa`, `dewey`, `qeo`, `zebra-day`
and `kahlo` `.day.lsmc.bio` hosts mapped to `127.0.0.1`. Preserve them for the
existing authentication/product transport. No sibling mutation route is called
by this HTTP capsule. There is no blanket outbound-network disable claim.

## 2. Start only the isolated fresh runtime

O confirmed the original `network_mode=host` and approved this exact rehearsal
shape: host network, `HOST=127.0.0.1`, `PORT=18914`, restart disabled, no 8914
listener. This preserves localhost OTEL and existing AWS transport. No background
dispatch command runs. UID `0:0` **does not imply HOME=/root**: the actual existing
HOME is `/home/ubuntu`, preserved below. All source/operator configuration
directories and the broad Dayhoff deployment mount are omitted.

```bash
sudo docker run --detach --name "$D_CONTAINER" --restart=no --network=host --user=0:0 \
  --env-file "$D_LAUNCH_DIR/runtime.env" "${D_HOST_ARGS[@]}" \
  --mount "type=bind,src=$D_RUNTIME_DIR/dewey-config.yaml,dst=$D_RUNTIME_DIR/dewey-config.yaml,readonly" \
  --mount "type=bind,src=$D_RUNTIME_DIR/tapdb-runtime.yaml,dst=$D_RUNTIME_DIR/tapdb-runtime.yaml,readonly" \
  --mount type=bind,src=/home/ubuntu/.aws,dst=/home/ubuntu/.aws,readonly \
  --mount type=bind,src=/home/ubuntu/.config/tapdb/rds-ca-bundle.pem,dst=/home/ubuntu/.config/tapdb/rds-ca-bundle.pem,readonly \
  --mount type=bind,src=/home/ubuntu/.config/dewey-day/cloudfront-private-key.pem,dst=/home/ubuntu/.config/dewey-day/cloudfront-private-key.pem,readonly \
  --mount type=bind,src=/opt/dayhoff/deployments/day/state/kahlo/ai-agent-grants.json,dst=/opt/dayhoff/deployments/day/state/kahlo/ai-agent-grants.json,readonly \
  --mount type=bind,src=/opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json,dst=/opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json,readonly \
  --mount type=bind,src=/opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json,dst=/opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json,readonly \
  --mount "type=bind,src=$D_CAPSULE_DIR,dst=/run/dewey-acceptance,readonly" \
  --mount type=bind,src=/home/ubuntu/dewey_ops/tapdb101-20260911/fixtures/qeo-complete-multiqc-package-20260910.json,dst=/run/dewey-acceptance-manifest.json,readonly \
  --mount type=bind,src=/opt/dewey/day/releases/qeo-resolver-7782aef47b86/resolver.token,dst=/run/dewey-acceptance-resolver.token,readonly \
  --mount "type=bind,src=$D_STATE_DIR,dst=/run/dewey-acceptance-state" \
  --mount "type=bind,src=$D_OUTPUT_DIR,dst=/run/dewey-acceptance-output" \
  "$D_IMAGE"
```

Docker `--mount` fails when a source is absent. No chown/chmod of existing files
is needed. O retains the actual container ID, exact mounts/env and loopback-only
listener receipt before proceeding. No source or TapDB package overlay is mounted.
The production-like GUI settings remain true with approved Host `dewey.day.lsmc.bio`;
do not weaken auth/Host checks to reach loopback. Auth/session values come from
the new private Dewey YAML. The CloudFront file remains read-only. The reviewed
host and stopped old runtime have no NCBI key file or parent directory; Dewey's
optional loader continues without `NCBI_API_KEY` when the configured path is
absent. Preserve the existing `DEWEY_NCBI_API_KEY_FILE` environment value, but
do not mount or create an empty credential.

## 3. Fresh principal verification, then HTTP reads

```bash
docker exec "$D_CONTAINER" /app/.venv/bin/python /run/dewey-acceptance/dewey_runtime_principal_prepare.py runtime-verify --lane "$D_LANE" --runtime-config "$D_RUNTIME_DIR/tapdb-runtime.yaml" --receipt /run/dewey-acceptance-output/runtime-verified.json
```

After reviewing that new successful receipt, bind the HTTP capsule arguments:

```bash
D_APP=(docker exec "$D_CONTAINER" /app/.venv/bin/python /run/dewey-acceptance/application_acceptance.py)
D_HTTP=(--lane "$D_LANE" --base-url http://127.0.0.1:18914 --dewey-config "$D_RUNTIME_DIR/dewey-config.yaml" --resolver-token-file /run/dewey-acceptance-resolver.token --fixture-inputs /run/dewey-acceptance/fixture-inputs.json --fixture-manifest /run/dewey-acceptance-manifest.json --image-digest "$D_DIGEST" --image-sha "$D_IMAGE_SHA")
"${D_APP[@]}" read "${D_HTTP[@]}" --receipt /run/dewey-acceptance-output/app-read.json
```

This checks readiness/version/SHA, actual persisted report `M-DGX-NKDM`, package
`M-DGX-NNSS` and its 20 members, both QEO resolver inputs, resolver-only bearer
rejection on general API, anonymous DAG rejection, native manifest/object/graph/
exact search. The effective primary `DEWEY_API_BEARER_TOKEN` is selected internally
and checked against the explicit preserved environment; two additional tokens
are not selected by set order. The resolver token is
checked against the retained hash and expiry. HTTP proxies and redirects are
disabled; every connection goes only to the explicit loopback port. Each invocation
also resolves the runtime YAML through released `get_db_config` and reuses the
companion principal launcher's strict lane/database/role/scope and operator-free
checks before any HTTP request. Both Python files must be in the mounted capsule
directory under the exact basenames above.

## 4. Reviewed controlled DB-only write, then replay

Run only after the read receipt and native gates have been reviewed:

```bash
"${D_APP[@]}" write "${D_HTTP[@]}" --prior-receipt /run/dewey-acceptance-output/app-read.json --receipt /run/dewey-acceptance-output/app-write.json
```

Review the returned/persisted artifact-set EUID before replay:

```bash
"${D_APP[@]}" replay "${D_HTTP[@]}" --prior-receipt /run/dewey-acceptance-output/app-write.json --receipt /run/dewey-acceptance-output/app-replay.json
```

The write creates one explicitly labeled `migration_acceptance` artifact set and
one typed membership to the already persisted report; it also creates required
idempotency records. Keys include the explicit lane/date. Replay requires the
same returned EUID and exact original response digests, and a changed body with
the same key must return 409. No EUID is supplied for creation. Receipts persist
returned identifiers before another request, including unexpected HTTP status
and partial failure; there is no automatic retry or cleanup. Keep any failed or
reserved allocation evidence for C's final floors. No S3 operation, share,
literature mutation, sibling grant-file edit or QEO dispatch is invoked.

Optional separately reviewed **existing-package CLI replay**, when that acceptance
row is selected by O; this is not inbox/outbox replay:

```bash
docker exec "$D_CONTAINER" dewey --config "$D_RUNTIME_DIR/dewey-config.yaml" qeo package-register --manifest /run/dewey-acceptance-manifest.json --idempotency-key qeo-multiqc-illumina-20260815-full-package-v1
```

Retain its public receipt and require original `M-DGX-NNSS`; never retry against
another config. Real authenticated embedded GUI/OAuth/browser acceptance remains
a separate O/E evidence step; HTTP probes do not replace it.

## 5. Final copied target

After O stops this rehearsal container and preserves its terminal allocator
exposure evidence, repeat with new private state/output/environment directories, unused
18914, `D_CONTAINER=dewey-tapdb10-final-20260911`, `D_LANE=production`,
`D_RUNTIME_DIR=/opt/dewey/day/releases/9.0.0`, and the final native principal
results. Set `D_IMAGE_SHA` and `D_DIGEST` from the final main/tag image's accepted
source and manifest receipts, then rebuild `D_IMAGE` from that exact digest;
do not retain the rehearsal candidate SHA/digest for the final image. Pass that
same final SHA to both environment preparation and HTTP acceptance. Keep both
copies' receipts; source remains stopped/closed. Only O's
final promotion changes service publication to the approved production listener.
F's final service renderer consumes the same reviewed environment projection and
explicitly changes `HOST`/`DEWEY_HOST` to `0.0.0.0`, `PORT`/`DEWEY_PORT` to `8914`,
and binds its selected final private state paths. The helper itself keeps both
lanes isolated until that separately owned promotion.
This capsule does not switch boot Compose, expose 8914, publish another image,
restart source or execute an image-only rollback.

## Local validation

New capsule orchestration tests: **14 passed** (12 initial cases plus 2 added URL
boundary cases), without network/database access; only the 2 new cases were run
after the URL boundary was tightened.
Coverage includes strict loopback URLs, primary-token selection, no credential
serialization, returned-ID persistence on partial failure/unexpected status,
exact replay, changed-image rejection, no overwrite and no redirect following.
Ruff, Bandit and script `--help` passed. The coordinator's 427-pass/2-skip app CI
and prior native receipts are reused; no broad tests or image rebuild was run.

The 2026-09-11 07:45Z environment correction adds **15 new passing cases**:
12 launch projection cases plus 2 effective-primary cases in one focused run,
then one new SafeLoader Python-tag rejection case. All use synthetic local
inputs; no Docker/AWS/app endpoint was called. Existing tests were deselected.
Ruff/format, helper `--help` and all 9 Bash block syntax checks passed.
Bandit initially flagged the custom `yaml.SafeLoader` subclass and an explicitly
empty dispatch setting. SafeLoader rejection is now tested; the two safe-loader
call sites have documented `B506` annotations and the explicit empty dispatch
setting has one `B105` annotation. No unsafe YAML constructor was enabled. The
final scan passed with Bandit's redundant assignment-node annotation warning.
Principal script and all
application/image build inputs are unchanged; deployed behavior still requires
O's actual environment preparation, launch and acceptance receipts.

The subsequent final-image provenance correction makes `--image-sha` mandatory.
**8 new cases passed** for malformed/missing arguments, the exact rehearsal pin,
and propagation of a distinct explicit production SHA to both environment labels
and receipt. The prior cases were not rerun. Ruff and the 9 Bash syntax checks
passed; authentication selection and all application/image build inputs remain
unchanged. O/F owns verification that the supplied production SHA belongs to
the actual final image.

The 08:38Z runtime-context correction pins rehearsal to O's new source
`c6406b8ffb40e58feaba31e2163d77448d47698c` and assigns new container, capsule,
state, output and environment paths. The previous candidate is now explicitly
rejected by the pin test. The HTTP acceptance script, stored fixture identities,
idempotency keys, resolved TapDB runtime path and principal binding are unchanged.
Use targeted `sudo` to create/read the protected launch environment and start Docker;
do not relax the existing credentials' permissions. The rebuilt image digest remains
an explicit required O/F receipt input until publication succeeds.
