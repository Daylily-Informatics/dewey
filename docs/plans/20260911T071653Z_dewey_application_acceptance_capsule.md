# Dewey isolated application acceptance commands

D preparation, 2026-09-11. O runs these only after the native copy/migration/
floor and [principal stages](20260911T070836Z_dewey_principal_capsule.md) pass.
Source stays stopped/closed throughout rehearsal and final. No additional backup
or inbox/outbox replay/retention gate is introduced. These commands were not
executed by D. O's published candidate receipt owns image provenance:

- Manifest digest: `sha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f`.
- Image source revision: `c484c95768a4147acdcabd12a2da0332c4c750dc`.
- Dewey `9.0.0`, TapDB `10.1.1rc1`, Meridian `0.4.8`.

## 1. Prepare exact mounted capsule files and inputs

In an existing private operator directory, prepare an `application-acceptance`
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

Use O's already preserved host manifest directly:
`/home/ubuntu/dewey_ops/tapdb101-20260911/fixtures/qeo-complete-multiqc-package-20260910.json`.
O verified SHA256 `4ed7e3e6938edb309a277042a42125d2ac58e99579809973e369054e1a67f4e9`
against the retained fixture after copying it from the stopped source container.
The separate read-only mount below needs no second manifest copy.

```bash
umask 077
D_CONTAINER=dewey-tapdb10-rehearsal-20260911
D_LANE=rehearsal
D_RUNTIME_DIR=/opt/dewey/day/releases/tapdb10-rehearsal-20260911
D_CAPSULE_DIR=/home/ubuntu/dewey_ops/tapdb101-20260911/application-acceptance
D_DIGEST=sha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f
D_IMAGE_SHA=c484c95768a4147acdcabd12a2da0332c4c750dc
: "${D_IMAGE_REPOSITORY:?Exact published repository from O/F image receipt}"
: "${D_STATE_DIR:?New existing absolute private rehearsal state directory}"
: "${D_OUTPUT_DIR:?New existing absolute private rehearsal receipt directory}"
D_IMAGE="${D_IMAGE_REPOSITORY}@${D_DIGEST}"
test -z "$(ss -H -ltn 'sport = :18914')"
test -z "$(docker ps -aq --filter 'name=^/dewey-tapdb10-rehearsal-20260911$')"
```

The owning image inspection must match digest, source labels and package receipt
before launch. `--image-digest` below records the manifest digest, not Docker's
different image config ID. The capsule compares the running health build SHA
and package versions; it does not have Docker socket access to verify the
externally supplied manifest digest itself.

## 2. Start only the isolated fresh runtime

O confirmed the original `network_mode=host` and approved this exact rehearsal
shape: host network, `HOST=127.0.0.1`, `PORT=18914`, restart disabled, no 8914
listener. This preserves localhost OTEL and existing AWS transport. No background
dispatch command runs. UID `0:0` **does not imply HOME=/root**: the actual existing
HOME is `/home/ubuntu`, preserved below. All source/operator configuration
directories and the broad Dayhoff deployment mount are omitted.

```bash
docker run --detach --name "$D_CONTAINER" --restart=no --network=host --user=0:0 \
  --env HOME=/home/ubuntu \
  --env LSMC_SERVICE_NAME=dewey --env LSMC_ENV=prod --env LSMC_RUNTIME_CLASS=aws-compose \
  --env HOST=127.0.0.1 --env PORT=18914 \
  --env OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
  --env DEWEY_EXECUTION_BACKEND=dewey-container --env DEWEY_DEPLOYMENT_CODE=day \
  --env DEWEY_ENVIRONMENT=production \
  --env "DEWEY_CONFIG=$D_RUNTIME_DIR/dewey-config.yaml" \
  --env "TAPDB_CONFIG_PATH=$D_RUNTIME_DIR/tapdb-runtime.yaml" \
  --env DEWEY_DATABASE_TARGET=aurora --env DEWEY_TAPDB_CLIENT_ID=dewey \
  --env DEWEY_TAPDB_DATABASE_NAME=dewey-day --env DEWEY_TAPDB_DOMAIN_CODE=M \
  --env DEWEY_TAPDB_OWNER_REPO_NAME=dewey \
  --env "DEWEY_BUILD_SHA=$D_IMAGE_SHA" --env "LSMC_RELEASE_SHA=$D_IMAGE_SHA" \
  --env AWS_PROFILE=lsmc --env AWS_REGION=us-west-2 --env AWS_DEFAULT_REGION=us-west-2 \
  --env AWS_CONFIG_FILE=/home/ubuntu/.aws/config \
  --env AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
  --env DEWEY_NCBI_API_KEY_FILE=/home/ubuntu/.config/ncbi/key.txt \
  --env LSMC_AI_AGENT_GRANTS_PATH=/opt/dayhoff/deployments/day/state/kahlo/ai-agent-grants.json \
  --env XDG_STATE_HOME=/run/dewey-acceptance-state/state \
  --env XDG_CACHE_HOME=/run/dewey-acceptance-state/cache \
  --env DEWEY_LITERATURE_METAPUB_CACHE_DIR=/run/dewey-acceptance-state/metapub \
  --env DEWEY_QEO_INGEST_URL= --env DEWEY_QEO_API_TOKEN= --env DEWEY_QEO_CONSUMER_GROUP= \
  --mount "type=bind,src=$D_RUNTIME_DIR/dewey-config.yaml,dst=$D_RUNTIME_DIR/dewey-config.yaml,readonly" \
  --mount "type=bind,src=$D_RUNTIME_DIR/tapdb-runtime.yaml,dst=$D_RUNTIME_DIR/tapdb-runtime.yaml,readonly" \
  --mount type=bind,src=/home/ubuntu/.aws,dst=/home/ubuntu/.aws,readonly \
  --mount type=bind,src=/home/ubuntu/.config/tapdb/rds-ca-bundle.pem,dst=/home/ubuntu/.config/tapdb/rds-ca-bundle.pem,readonly \
  --mount type=bind,src=/home/ubuntu/.config/dewey-day/cloudfront-private-key.pem,dst=/home/ubuntu/.config/dewey-day/cloudfront-private-key.pem,readonly \
  --mount type=bind,src=/home/ubuntu/.config/ncbi/key.txt,dst=/home/ubuntu/.config/ncbi/key.txt,readonly \
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
the new private Dewey YAML. The NCBI and CloudFront files remain read-only.

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
exact search. The primary `application.api_bearer_token` is selected internally;
two additional tokens are not selected by set order. The resolver token is
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
exposure evidence, repeat with new private state/output directories, unused
18914, `D_CONTAINER=dewey-tapdb10-final-20260911`, `D_LANE=production`,
`D_RUNTIME_DIR=/opt/dewey/day/releases/9.0.0`, and the final native principal
results. Keep both copies' receipts; source remains stopped/closed. Only O's
final promotion changes service publication to the approved production listener.
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
