# Dewey one-time runtime principal stages

Prepared by D at 2026-09-11 07:08:36Z. O executes after the controlling native
migration/floor gates. Source remains stopped/closed through rehearsal and final
acceptance. No additional backup, inbox/outbox replay or retention gate is added.

Launcher: [`scripts/dewey_runtime_principal_prepare.py`](../../scripts/dewey_runtime_principal_prepare.py).
It uses the five-field public operator overlay accepted in B/E's
`20260911T060545Z_dewey_native_execution_inputs.md`, preserves the actual runtime
config identity and never writes operator credentials to runtime YAML. It pins
the installed public TapDB `10.1.1rc1` and Meridian `0.4.8`.

## Inputs

Copy this exact launcher to the protected operator directory and record its hash.
Select one lane; all paths below must already exist. Receipt parents must be
canonical, private, existing directories; outputs must be new.

| Input | Rehearsal | Final |
| --- | --- | --- |
| Lane | `rehearsal` | `production` |
| Runtime directory | `/opt/dewey/day/releases/tapdb10-rehearsal-20260911` | `/opt/dewey/day/releases/9.0.0` |
| Operator YAML | `/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-operator.yaml` | `/home/ubuntu/dewey_ops/tapdb101-20260911/replacement-operator.yaml` |
| Runtime user | `dewey_rehearsal_9` | `dewey_runtime_9` |
| Existing safe secret record | `rehearsal-runtime-secret.json` | `production-runtime-secret.json` |
| Runtime secret version | `092f355d-e532-4efb-b7af-d8dcb475f0ab` | `4d5f13a0-9691-40ef-91de-453543c9c05e` |

Supply actual absolute copies of the coordinator's safe secret-reference records,
plus the exact existing `dayhoff` secret ARN and accepted current version ID from
O's credential receipt. The wrapper seals these references and config/registry/
CA/launcher hashes into review inputs. It does not refresh secret metadata or
claim that a supplied version label proves AWSCURRENT. O retains the owning
current-version/role-pairing receipt and prevents rotation during these stages.

Example rehearsal binding in O's interactive shell:

```bash
umask 077
D_PY=/home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/python
D_LAUNCHER=/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_runtime_principal_prepare.py
D_LANE=rehearsal
D_RUNTIME=/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml
D_OPERATOR=/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-operator.yaml
: "${D_RUNTIME_SECRET_RECORD:?Absolute existing rehearsal secret-reference receipt}"
: "${D_OPERATOR_SECRET_ARN:?Exact accepted dayhoff secret ARN, never its value}"
: "${D_OPERATOR_SECRET_VERSION:?Accepted operator secret version ID}"
: "${D_BOOT_PLAN:?New absolute bootstrap plan in private existing directory}"
: "${D_BIND_PLAN:?New absolute binding plan in private existing directory}"
D_COMMON=(--lane "$D_LANE" --runtime-config "$D_RUNTIME" --operator-config "$D_OPERATOR" --runtime-secret-record "$D_RUNTIME_SECRET_RECORD" --operator-secret-arn "$D_OPERATOR_SECRET_ARN" --operator-secret-version "$D_OPERATOR_SECRET_VERSION")
```

For final, select production and corresponding exact paths/record before
generating new final plans. Do not rename a bound runtime file or reuse rehearsal
receipts against final.

## Separate execution/review steps

Run one command per reviewed stage; this is not a combined batch.

```bash
"$D_PY" "$D_LAUNCHER" bootstrap-plan "${D_COMMON[@]}" --receipt "$D_BOOT_PLAN"
```

Review native offline plan, runtime role, exact database, CONNECT-only bootstrap
effects and wrapper inputs. The offline plan neither inspects role existence nor
generates a password. Then:

```bash
"$D_PY" "$D_LAUNCHER" bootstrap-apply "${D_COMMON[@]}" --receipt "$D_BOOT_PLAN"
```

Require new `<bootstrap-plan-stem>.result.json` with native `status=applied`.
Existing roles are validated without password reset. Unexpected state requires
review, never an automatic rotate/retry. Next:

```bash
"$D_PY" "$D_LAUNCHER" bind-plan "${D_COMMON[@]}" --receipt "$D_BIND_PLAN"
```

Review the native sealed plan and `<bind-plan-stem>.inputs.json`: exact runtime
scope, CONNECT/schema/sequence grants, PUBLIC TEMP revocation, operator TEMP
preservation and fresh-session requirement. After that review:

```bash
"$D_PY" "$D_LAUNCHER" bind-apply "${D_COMMON[@]}" --receipt "$D_BIND_PLAN"
```

Native bind applies the same canonical receipt and writes its own `.result.json`;
require `status=applied`, `runtime_temp_denied=true`, `privileges_verified=true`.
The helper refuses changed input hashes and existing results. It does not change
the copy recovery-family identity. Unexpected errors are printed by class only.

## Fresh runtime verification in the isolated image

After binding, start only the fresh isolated candidate with runtime-only mounts.
Mount this launcher read-only at
`/run/dewey-acceptance/dewey_runtime_principal_prepare.py` and an existing private
writable receipt directory at `/run/dewey-acceptance-output`. Run a new process:

```bash
docker exec "$D_CONTAINER" /app/.venv/bin/python /run/dewey-acceptance/dewey_runtime_principal_prepare.py runtime-verify --lane "$D_LANE" --runtime-config "$D_RUNTIME" --receipt /run/dewey-acceptance-output/runtime-verified.json
```

No operator file, secret record or operator argument is permitted in this phase.
Checks cover exact package versions, authenticated runtime role/database/context,
CONNECT true, effective TEMP/database CREATE/schema CREATE false, forbidden role
attributes false, and all 11 existing M/DGX templates through public APIs. Public
cached engines are disposed before each probe to obtain fresh sessions. Fixed
TEMP-table and managed-schema table probes must fail with SQLSTATE `42501` after
session initialization succeeds. The integer-only definitions contain no
allocators/defaults; an unexpectedly permitted table is rolled back and fails
acceptance. No seed or principal mutation occurs in this verification phase.

Keep all old source/runtime pools closed; binding alone does not revoke an old
session's existing TEMP capability. O retains fresh process/container evidence
alongside the new `status=verified` receipt.

## Local validation

New focused wrapper tests: **16 passed**, no database/credentials/AWS. Coverage:
restricted overlay, wrong target/scope/secret/operator rejection, stale review
refusal before apply, unchanged-plan apply, no overwrite, private receipt parent
and digest tampering. Ruff check/format and script `--help` passed. Existing
application/native suites were not rerun. No live principal stage or DDL probe
was executed by D.
