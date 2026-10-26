# Dewey released TapDB execution inputs and operator acceptance checklist

Reviewed 2026-09-11 against immutable `daylily-tapdb==10.1.1rc1`, commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. This is independent E contract
review. O owns configuration preparation, exact command execution and live
receipts; C owns migration manifests/tooling. No command below was executed
against Aurora by E. No additional backup or snapshot is part of this procedure.

The controlling ledger and O's explicit variable/input record decide when each
step is authorized. Root confirms the user authorized the bounded setup SOP,
including the documented public-API operator overlay and the one production GUI
config field that has no CLI flag. These are explicit setup steps, not changes
to the published package. Preserve the original source config and all previous
receipts. Do not print either passwords or full application inventories.

Latest user steering permits Dewey to remain offline throughout rehearsal and
final cutover, and waives inbox/outbox message preservation and replay gates.
The source remains closed after its initial reviewed cutoff/copy. Retain that
cutoff and continuous freeze evidence for the later final provider copy; do not
try a new native source connection while admission is closed. The
[revised copy review](20260911T063007Z_dewey_rehearsal_copy_review.md) records
this disposition. All other identity and allocator preservation remains required.

## 1. Bind exact inputs before any operation

| Input | Required value or source |
|---|---|
| `TAPDB` | `/home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/tapdb`, verified exact RC |
| `SOURCE_CONFIG` | `/home/ubuntu/dewey_ops/tapdb101-20260911/source-operator.yaml` |
| Source database/schema | `dewey_prod` / `tapdb_dewey_lsmcok1_local` |
| Rehearsal database | `dewey_tapdb10_rehearsal_20260911`, only after O's explicit unused-target check and provider copy |
| Final replacement database | `dewey_prod_tapdb10`, only after a fresh final source outage/copy |
| Target host | `dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com` |
| Cluster/region/profile | `dayhoff-lsmcok1-tapdb` / `us-west-2` / `lsmc` |
| Scope | Domain `M`, owner repo `dewey`; explicit tenant/global policy from accepted source and application scope |
| Operator | Existing `dayhoff`, using its separate existing protected secret reference |
| `COPY_RUNTIME_USER` | `dewey_rehearsal_9` for rehearsal; `dewey_runtime_9` for final, each with its own matching credential |
| `COPY_CONFIG` | Fixed absolute operator config for this particular copy; never rename it within its family |
| `RUNTIME_CONFIG` | Explicit final resolved absolute pathname used inside the runtime container; choose before binding |
| `CONTROL_CONFIG` | Explicit config for the authenticated existing `postgres` control database (OID 5), on the same exact server transport |
| `PROVIDER_CONTRACT` | New protected JSON input with the exact ten fields in section 4 |
| `MAPPINGS` | Independently accepted four dormant mappings, SHA-256 `5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8`; native capture checks the actual copy |
| `FAMILY_ID`, `FAMILY`, journal roots | New explicit canonical UUID and existing canonical absolute directories for this copy only; no prior history discarded |
| All input/output paths | Explicit absolute paths; output receipts/logs are new files; protected directory, `umask 077`, no overwrite or concurrent writer |

The source operator config's future runtime username paired with the old
`dayhoff` secret was an inventory-only placeholder. It is not valid runtime
credential preparation and must never be used for runtime bootstrap/binding.

Selected native inventory policy is identical in source, copy and all later
identity comparisons:

```bash
"$TAPDB" --config "$COPY_CONFIG" db-config update \
  --inventory-max-rows 1000000 \
  --inventory-max-row-bytes 8388608 \
  --inventory-max-receipt-bytes 536870912
```

This edits only the selected config. The three limits are sealed in identity
receipts. Verification refuses different policies, recomputes recorded usage,
and migration imports the policy from its supplied historical contract
(`identity_inventory.py:806`, `migration_identity.py:513`). These are evidence
limits, not the JSON file's raw byte size. Never truncate, partition or omit
original rows to fit a limit.

The mapped discovery capture reported by O completed at
`2026-09-11T05:48:23.633925+00:00`, RC 0, 65.926 seconds. Its safe summary records
79,918 rows, 173,423,825 evidence bytes and a 225,223,602-byte raw file. File
SHA-256 is `c8d8d02e4ee93a6e615b960a20fa761e0456ba2a4d2a6318107f1441583b79f3`;
source-contract SHA-256 is
`b4fa8198d2c8082e551011f227497b4d17b379d79d4350ff15635e1c9a9f6e75`.
This is discovery evidence, not the future final outage capture. E read only
O's sanitized `mapped-source-summary.json`, not the private row file.

## 2. Source outage, untouched copy and target-only identity verification

1. For rehearsal, stop every source writer/pool, prevent automatic restart,
   review source sessions, capture the complete source and its next values,
   close source connections, and perform O's separately reviewed database copy.
   Keep the copy's HTTP, workers and outbound integrations isolated. Leave old
   source admission closed and its original container stopped throughout
   rehearsal, as authorized by the latest user instruction.
2. For final replacement, verify the continuous source freeze and copy that
   unchanged closed source into the fixed final destination using new provider
   receipt paths. Native capture of the new copy must compare to the retained
   original cutoff. Do not reconnect to or reopen the old source merely to
   capture it again. Any breach of the source freeze stops this reviewed
   capsule. Census observes sessions; it is not a fence or evidence that
   disconnected clients cannot reconnect.
3. Capture source and untouched copy using identical mapping and limit policy:

```bash
"$TAPDB" --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$MAPPINGS" \
  --receipt "$SOURCE_FINAL"

"$TAPDB" --config "$SOURCE_CONFIG" --json db sequences advance \
  --floors "$EMPTY_OBSERVATION_FLOORS" --receipt "$SOURCE_NEXT_PLAN" \
  --sequence-mappings "$MAPPINGS"

"$TAPDB" --config "$COPY_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$MAPPINGS" \
  --receipt "$COPY_UNTOUCHED"
```

`EMPTY_OBSERVATION_FLOORS` is exactly `{"floors":[]}`. The advance command above
is read-only because it lacks `--apply`. Require its `inventory.sha256` to equal
`SOURCE_FINAL.sequence_inventory.sha256`. It is an observation, not the final
floor input. Store large stdout/stderr in protected new files rather than the
terminal; the canonical receipt is the file written by `--receipt`.

4. C/O generates the copy conversion input using the **entire actual**
   `COPY_UNTOUCHED.identity_inventory.target` object. Its minimal shape is:

```text
{
  "schema_version": "tapdb-identity-conversion/v1",
  "target": COPY_UNTOUCHED.identity_inventory.target,
  "tables": {},
  "added_tables": []
}
```

This notation specifies an object projection; replace the projection with the
actual JSON object before invoking the CLI. Do not add `sha256`,
`physical_target` or other keys. The operator config's resolved path is part of
the target. The target-only declaration allows the copied physical target to
change while preserving every original table, column, cell, identity, metadata
and schema name (`identity_inventory.py:848–880`). No row or column conversion
is allowed by this input.

```bash
"$TAPDB" --config "$COPY_CONFIG" --json db identity verify \
  --before "$SOURCE_FINAL" --after "$COPY_UNTOUCHED" \
  --conversion-manifest "$COPY_TARGET_ONLY_MANIFEST"
```

There is no `--receipt` flag on identity verify. Persist its native JSON stdout
and RC as a new protected result. The CLI independently requires the after
receipt's target to equal the explicit config target. The verifier allows
physical substitution when a target is declared, so also match the copy's
actual database/OID/server to O's owning copy receipt. Separately compare all
twenty original generator names, definitions, mappings, states and assigned/
allocated boundaries; identity verify does not perform that sequence comparison.

## 3. Create this copy's native family, then migrate it

No prior family/journal exists for the initial task entry, as confirmed by O/C.
A rehearsal family and a fresh final-copy family are separate immutable
lineages. Retain both histories; a provider copy does not assert a native join.

```bash
"$TAPDB" --config "$COPY_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$MAPPINGS" \
  --new-recovery-family-id "$FAMILY_ID" \
  --family-receipts-dir "$MIGRATION_JOURNAL" \
  --family-receipts-dir "$SEQUENCE_JOURNAL" \
  --family-receipt "$FAMILY" --receipt "$COPY_HISTORICAL"
```

List every existing, explicit future operation journal root. If one root serves
both operations, pass that root once. Roots must be canonical absolute existing
directories, sorted/unique in the native descriptor and permanently readable.
`--family-receipt` and `--receipt` must be different new paths. The native CLI
seals the actual copy's sequence inventory as origin and reseals its source
contract (`cli/identity.py:128–205`, `backup/recovery.py:81–145`). Verify identity
and sequence content still equal the accepted untouched copy.

Family member identity contains both the complete normalized target,
**including `config_identity`**, and physical database/OID/server
(`identity_inventory.py:213`, `backup/recovery.py:54`, line 393). Keep this
copy's operator pathname and target transport fixed throughout family inventory,
migration and sequence operations. Runtime principal binding is a separate
scope and may use the chosen runtime pathname; it does not accept a family.

```bash
"$TAPDB" --config "$COPY_CONFIG" db schema migrate --dry-run \
  --receipt "$MIGRATION_PLAN" --source-contract "$COPY_HISTORICAL" \
  --sequence-mappings "$MAPPINGS" --receipts-dir "$MIGRATION_JOURNAL" \
  --recovery-family "$FAMILY"
```

Review pending files/digests, original source-contract equality, all identities,
generator definitions/floors, explicit family and terminal journal state. This
must use the actual copy's historical contract, not the old source's different
physical target. If a preparatory operation legitimately changed copy sequence
state, recapture its historical contract with the **same existing family**;
the previous contract is stale. No backup ID/archive/restore-purpose input is
required (`migration_identity.py:469–594`, `cli/db.py:1536`).

After O's existing mutation gates and unchanged preflight review:

```bash
"$TAPDB" --config "$COPY_CONFIG" db schema migrate --apply \
  --preflight-receipt "$MIGRATION_PLAN" --receipt "$MIGRATION_RESULT" \
  --source-contract "$COPY_HISTORICAL" --sequence-mappings "$MAPPINGS" \
  --receipts-dir "$MIGRATION_JOURNAL" --recovery-family "$FAMILY" \
  --establish-writer-fence --control-config "$CONTROL_CONFIG" \
  --provider-contract "$PROVIDER_CONTRACT"
```

Migration has no `--conversion-manifest` option. Its own native preservation
checks run during migration. C's narrowly reviewed post-migration conversion
manifest belongs to the separate final `db identity verify` command, never to
the untouched-copy comparison. Review the written result's `migration_result`,
`recovery_completion`, `writer_fence_release` and
`principal_binding_required: true`; CLI success text or global JSON mode alone
is not that result. Native apply retains target and control sessions through
fence, commit, postcommit verification and release (`cli/db.py:1743–1840`).

## 4. Exact provider and control requirements

The provider input has **exactly ten nonempty string values**, no seal or
additional fields (`sequence_fence.py:137–215`):

| Key | Exact value/source |
|---|---|
| `schema_version` | `tapdb-fence-provider/v1` |
| `engine` | `aurora-postgresql` |
| `engine_version` | `16.13` |
| `aws_profile` | `lsmc` |
| `region` | `us-west-2` |
| `cluster_identifier` | `dayhoff-lsmcok1-tapdb` |
| `cluster_arn` | Exact retained AWS `DBClusters[0].DBClusterArn` |
| `cluster_resource_id` | Exact retained AWS `DBClusters[0].DbClusterResourceId` |
| `writer_endpoint` | Exact retained AWS `DBClusters[0].Endpoint`, equal to target host |
| `sslmode` | `verify-full` |

There is no separate native CLI provider-file generator. O serializes this
reviewed public input from its existing owning-system response and records the
file hash separately. Do not invent ARN/resource ID or repeat an already
accepted provider lookup just to populate the file. At apply, native TapDB
itself performs its required authenticated exact-cluster lookup and compares
these fields, server version, Aurora version and provider/operator role
attributes. The executing process therefore needs its explicit existing profile
and read permission for the exact RDS metadata and selected credential secret.

The control database must already exist, differ from the copy, and be reachable
by the exact operator at identical host/port. Its config is a complete native
explicit target, with distinct operator/runtime fields, valid governance paths,
explicit TLS/IAM choices and explicit schema text; no control schema creation
or seeding is required. Do not bootstrap or bind the runtime to control.

Native `control_state` validates current database, session/current login, target
database existence/OID, server address/port and PostgreSQL version. Census
existence is not a successful authenticated control session. The copy database
owner must be the exact fence operator; its ACL must be safely restorable.
Native gates reject unsupported concurrent sessions, prepared transactions,
subscription/extension/preload states and unsupported privilege relationships.
Target/control config paths and CA files must resolve in the executing process.

Only mutation commands use `--establish-writer-fence --control-config`. Do not
pass a fabricated writer fence, takeover/quarantine receipt or stalled epoch.
If native apply fails after closing connections, retain its full result/journal
and inspect its actual native reconciliation state before further operations;
the database may correctly remain closed. No automatic replay, raw reopen or
receipt editing is authorized by this checklist.

### O's completed setup observations

O reports a successful public operator connection to `postgres` (OID 5) as
`dayhoff`, source OID 16749, PostgreSQL 16.13, both proposed destinations absent,
and operator CREATEDB/CREATEROLE true with SUPERUSER false. The observed idle
source connection from `10.0.0.222` still belongs in the outage/session review.
These observations precede copying and do not authorize ignoring later state.
O reports provider-file SHA-256
`0700678f55acd55a39f2563b4ec73c4dbfba9876611644279ab3ad1d04abaa84`.

The instance role initially could not perform the required provider metadata
lookup or read new runtime secrets. O reports applying the following precise
grants and creating two runtime secrets with generated passwords retained only
in memory and Secrets Manager. E checked the local safe policy/secret-reference
files, not credentials or AWS. All four files are in the controlling worktree's
`docs/plans/evidence/20260911_dewey_rc_inventory/`:

| Safe record | Scope / SHA-256 |
|---|---|
| `ec2-migration-read-policy.json` | Only `rds:DescribeDBClusters` on the exact cluster ARN; `c299d22a457176d686c4f58d65522afcbf2ecac1bceb980e1d7f868711bf54cf` |
| `ec2-runtime-secret-read-policy.json` | Only `secretsmanager:GetSecretValue` and `DescribeSecret` on the two exact newly created secret ARNs; `69751957e5f241fec5878288dc9f022ec39c00b99a3a4a63ac5bc17cc8410802` |
| `production-runtime-secret.json` | `dewey_runtime_9`; version `4d5f13a0-9691-40ef-91de-453543c9c05e`; `68b1107ffee7be03e16ba45e6c720b8b6080d01227c76e46fc095a75aaac0e8d` |
| `rehearsal-runtime-secret.json` | `dewey_rehearsal_9`; version `092f355d-e532-4efb-b7af-d8dcb475f0ab`; `8bc774bd8ea78181a9deacf6a26189debcaa43615a3b8e584134b2f7e9e8721e` |

At that update, O reports no database role/copy/grant/container changes. Database
IAM auth remains false. No additional KMS grant or wildcard permission was
reported; actual secret resolution by the selected execution identity remains
required before claiming runtime authentication works.

## 5. Original-source and rehearsal floors into the final copy

The released CLI accepts `--floors`, not `--floor-inventory`. Its file has
exactly one top-level key, `floors`; each entry has exactly `name`, `value`,
`source`. Name must be a generator present in the current inventory; value is a
nonnegative integer, not bool; source is a nonempty provenance string
(`cli/sequences.py:103`, `sequences.py:454–486`).

The operator input can retain evidence from a different physical target or
family. Native validation does not assert that input provenance is a family
membership receipt. Independently match allocator names and meanings; preserve
original receipts and hashes. Retaining external floor records does not join
families or recover rows written elsewhere.

1. Keep every original-source initial/final assigned/allocated/reserved floor.
   Preserve each observed native `advances[].next_value` as an additional floor
   with its exact integer and source plan/inventory hashes. Do not subtract one:
   the accepted policy requires final next values strictly above those prior
   native next boundaries. Native arithmetic alone computes the next value.
2. After rehearsal acceptance, stop its writers/pools and outbound operations.
   Resolve actual interrupted operations through native reconciliation before
   claiming complete terminal exposure evidence. With the entire rehearsal
   family retained, capture a final native read-only advance plan using the
   rehearsal config and all prior explicit rehearsal floors. Preserve its
   complete `floors`, `advances`, inventory, family and receipt digests.
3. Final external floor input includes every retained rehearsal plan floor and
   every rehearsal `advances[].next_value`, plus the new final-source evidence.
   Include failed/reserved/probe evidence; do not delete a lower record because
   a higher one exists. Copy integers unchanged with explicit receipt/family
   provenance. Independent review owns completeness of this projection.
4. The final target plan/apply/verify uses its own full final-copy family and
   that identical external floor file. A generator absent from the final target
   fails natively; do not omit it, shorten a family or invent a recreation.
   Require all necessary generators before accepting final runtime writes.

```bash
"$TAPDB" --config "$COPY_CONFIG" --json db sequences advance \
  --floors "$FINAL_FLOORS" --receipt "$SEQUENCE_PLAN" \
  --sequence-mappings "$MAPPINGS" --recovery-family "$FAMILY"

"$TAPDB" --config "$COPY_CONFIG" --json db sequences advance --apply \
  --floors "$FINAL_FLOORS" --preflight-receipt "$SEQUENCE_PLAN" \
  --receipt "$SEQUENCE_RESULT" --sequence-mappings "$MAPPINGS" \
  --recovery-family "$FAMILY" --receipts-dir "$SEQUENCE_JOURNAL" \
  --establish-writer-fence --control-config "$CONTROL_CONFIG" \
  --provider-contract "$PROVIDER_CONTRACT"

"$TAPDB" --config "$COPY_CONFIG" --json db sequences verify \
  --floors "$FINAL_FLOORS" --sequence-mappings "$MAPPINGS" \
  --recovery-family "$FAMILY"
```

Sequence verify has no `--receipt`; retain native stdout and RC. Require `ok`
true, empty `violations`, complete expected generators and all retained
boundaries. Native plan/apply rejects changed state, mappings, floors or family
history. New native journal observations belong to the same retained family.

These floors protect allocation boundaries. Rehearsal test rows are isolated
test data, not accepted production writes. Existing Aurora recovery protection
and current-member repair forward remain the data recovery plan; neither floor
projection nor a stale source recovers accepted production rows.

## 6. Runtime credentials and configuration before binding

Use native `db-config init` for a new runtime-only file with all observed
metadata, target, governance paths, region/profile/TLS fields, selected runtime
role and its **new matching** runtime secret reference. O records every argument
and keeps no default target inference. Do not supply any `--operator-*` options
to this fresh runtime-only file. Init creates config only, including a private
random `admin.session.secret`; it does not create a database, role or registry
claim. Do not use `--force`, which replaces admin defaults and its session
secret (`cli/__init__.py:971`, line 1113). Apply the same selected limits.

For an existing dedicated operator config whose runtime role reference must be
corrected, native options are:

```bash
"$TAPDB" --config "$COPY_CONFIG" db-config update \
  --user "$COPY_RUNTIME_USER" --no-iam-auth \
  --secret-arn "$NEW_RUNTIME_SECRET_ARN" --password '' \
  --operator-user dayhoff --no-operator-iam-auth \
  --operator-secret-arn "$EXISTING_DAYHOFF_SECRET_ARN" --operator-password ''
```

This is preparation on the explicit new copy config, not an edit to the active
old source config. Native config update prints target update values; therefore
never pass the real password via `--password` or other secret-valued arguments.
Secret reference ARNs may be recorded in protected operator inputs; secret
values stay in the owning secret store. Password authentication does not use
database IAM auth, but reading a new secret and native provider metadata still
requires explicit IAM permissions. O found the existing instance role lacked
both, and added only the exact cluster metadata read and the two new secret read
grants recorded below; no wildcard access is implied by this procedure.

Native runtime bootstrap **does not generate a password or a Secrets Manager
secret**. O's authorized credential setup supplied fresh matching role secrets
and the required narrowly scoped read access. Native expects JSON with a
`password` key; retaining the exact `username` alongside it allows O to verify
the intended pairing, although TapDB reads only `password`. Never repoint an
existing role to an unrelated password by assumption.

Bootstrap plan is offline. Bootstrap apply creates a missing constrained LOGIN
using the configured secret password and grants only target `CONNECT`; an
existing role is validated but its password is not reset/rotated
(`runtime_principal.py:175`, line 201, line 454). An unexpected existing role or
credential mismatch requires explicit review, not an automatic retry/rotation.

For production GUI config, the exact public field is:

```yaml
admin:
  security:
    production_like: true
```

O adds only this field to the native-generated mapping, preserving every other
field and recording the credential-free structural diff. There is no native
init/update option for it. `--safety-tier production` does not set it, and
`get_db_config` reports target name `target`, so physical database naming cannot
replace it (`cli/db_config.py:597`, line 918–943). Keep config auth mode `tapdb`
before D's authenticated host bridge; `host_session` is not an accepted YAML
auth mode. Require nonempty existing `admin.session.secret` without printing it.
The GUI validates these settings before applying its host bridge
(`gui/router.py:3420`).

Aurora runtime uses `Path.home()/.config/tapdb/rds-ca-bundle.pem`, independently
of `cfg.sslrootcert`. O must confirm the actual container HOME/UID and mount the
verified CA read-only at that exact cache path; UID 0 is not itself evidence of
HOME. The pinned CA SHA-256 in this release is
`e5bb2084ccf45087bda1c9bffdea0eb15ee67f0b91646106e466714f9de3c7e3`.
An existing cache file is used without another native hash check; retain O's
hash evidence. Operator cfg.sslrootcert separately remains an existing absolute
readable path (`aurora/connection.py:27`, line 164; `web/runtime.py:253`).

Runtime Secret Manager refresh calls use the process boto3 credential chain;
unlike operator credential resolution, that call does not pass
`cfg.aws_profile` (`web/runtime.py:225`, `runtime_principal.py:225`). Confirm the
intended explicit container AWS environment can read/decrypt the exact runtime
secret using existing access. Do not expose the operator secret store/profile
to runtime merely because operator preparation worked.

## 7. Public bootstrap/bind with runtime-only file and separate operator config

The final runtime file must not contain operator credential references. The
CLI cannot remove its operator mapping: empty `--operator-user` leaves a
nonempty mapping rejected by `get_db_config`, `--clear operator` is unsupported,
and init merges a previous mapping (`cli/__init__.py:1690`, line 1841;
`cli/db_config.py:448–489`). Do not use those as cleanup operations.

O's explicitly authorized bounded public-API setup procedure is:

1. Resolve `RUNTIME_CONFIG` through documented
   `daylily_tapdb.cli.db_config.get_db_config(config_path=...)` and resolve the
   separate `COPY_CONFIG` through the same public function.
2. Require the resolved runtime config path to be the exact chosen runtime
   path. Require its operator mapping absent/empty (`operator_configured` false
   and all operator credentials empty). Require the two configs to match exact
   engine, host, port, optional server port/hostaddr, physical database, schema,
   client/database namespace, domain, owner, runtime role, tenant/global policy,
   IAM mode, runtime secret reference, region and cluster. The runtime and
   operator config paths are intentionally different; do not rewrite either.
3. Copy the resolved runtime mapping in memory. Overlay **only**
   `operator_user`, `operator_password`, `operator_secret_arn`,
   `operator_iam_auth`, and `operator_configured` from the separately resolved
   operator mapping. Require exact `dayhoff`, distinct from runtime, explicit
   false operator IAM, the expected existing operator secret and empty plaintext
   password. Keep `config_path` and all runtime/scope values from the actual
   final runtime file. Do not dump this mapping or write it into runtime YAML.
4. Invoke only the documented public functions below; no private helper or SQL:

```python
from daylily_tapdb.runtime_principal import (
    bootstrap_runtime_principal,
    bind_runtime_principal,
)

bootstrap_plan = bootstrap_runtime_principal(reviewed_cfg, apply=False)
# After the exact bootstrap plan review:
bootstrap_result = bootstrap_runtime_principal(reviewed_cfg, apply=True)

bind_plan = bind_runtime_principal(
    reviewed_cfg, receipt_path=absolute_new_bind_plan, apply=False,
)
# After unchanged plan review, use the SAME receipt path:
bind_result = bind_runtime_principal(
    reviewed_cfg, receipt_path=absolute_new_bind_plan, apply=True,
)
```

This fragment states public invocation contracts, not an installed migration
tool. O's launcher accepts explicit phase/path arguments so review and apply
are separate invocations. `reviewed_cfg` is freshly resolved and validated in
each invocation by steps 1–3, never an arbitrary persisted input. Bootstrap
results must be serialized to new protected files without printing credentials.
Before bootstrap apply, compare its freshly generated offline plan with the
retained reviewed plan, and bind O's external config-file hashes and secret
ARN/version references to the invocation. The native bootstrap plan does not
seal password contents or replace that credential-input review.
Unexpected exceptions are reported by class only; native CLI deliberately
avoids serializing driver errors that could contain statement values.

Bind writes its own sealed plan and, on apply, a separate
`<plan-stem>.result.json` beside it. It rejects an existing output, invalid
digest, changed target or stale role/scope/catalog/privileges. The immutable
runtime scope records the real final resolved config pathname, schema, domain,
issuer, tenant and global policy (`runtime_principal.py:879`, line 1083).
There is no family or control-config argument to principal bind. Nothing in
this procedure changes the copy family's operator config identity.

Require native bind result `status: applied`, `runtime_temp_denied: true`,
`privileges_verified: true`, runtime `CONNECT` true, effective runtime TEMP
false and the exact accepted scope. Review database-wide PUBLIC TEMP revocation
and any operator TEMP preservation grant. Bind does not migrate, seed, close
old runtime sessions or certify removal of existing temporary objects. Its
`runtime_session_requirement` explicitly remains unverified by bind. Recreate
all runtime processes/pools before application acceptance and observe successful
fresh authenticated runtime sessions using only the runtime file.

## 8. Completion evidence and current limits

- Native source/copy identity equality with no cell/identity waivers; all
  twenty historical generators and four verified dormant mappings retained.
- Copy-rooted family, complete immutable journal roots, native migration plan,
  apply/postcommit/fence release, explicit final identity conversion acceptance.
- Native final floor plan/apply/verification retaining original-source,
  rehearsal, failed/probe/reserved and complete current-family evidence.
- Separate role/secret pairing, exact final runtime path/scope, native bootstrap
  and binding results, operator-free runtime file, read-only CA mount and fresh
  runtime session/application acceptance.
- Existing Aurora recovery protection retained; after accepted target writes,
  use current-member repair forward or a separately reviewed provider recovery
  that preserves those writes and complete allocator history. No image-only or
  stale-source rollback claim.

This revision adds source-backed operator preparation and argument review only.
It reuses the accepted 123 release tests, prior 301 native suite and one already
completed nondefault-limit historical roundtrip. No suites, database queries,
source copy, secret creation, binding or deployment were performed by E for this
checklist. Actual Aurora fence, copy preservation and fresh runtime/application
outcomes remain O/E acceptance gates. Final acceptance is not yet claimed.

Related durable reports: [immutable release qualification](20260911T052037Z_tapdb1011rc1_dewey_qualification.md),
[source outage contract](20260911T052037Z_dewey_source_outage_sop_contract.md),
[D and sequence-mapping independent review](20260911T060000Z_dewey_independent_adoption_review.md).

E independently accepted C's no-original-cell-conversion migration manifest
SHA-256 `af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8`
as an execution input. Fifteen SQL/include asset hashes and native declarations
match this exact release; five candidate filename/row-key hash pairs and the
eight remaining filenames match C's retained tracking evidence and O's safe
summary counts/digests. This does not claim E read the private original tracking
rows. Native actual preflight must corroborate the exact applied/pending set.
The [independent static review receipt](20260911T051700Z_tapdb1011rc1_evidence/20260911T060545Z_migration_manifest_review.json)
has SHA-256 `dd257678e27895734ca80d8e97beb8eeb11f275128b51bf23b293d2d24472a16`.
Conditional on unchanged source cutoff, expect 11 tables and 79,926 rows before
binding/probes, only eight new tracking records, `identity_key` NULL on original
instances, and both new native tables empty. Review all actual catalog deltas
against tagged assets because native per-table schema permissions are broader
than those exact intended changes. NULL/empty-string source hashes do not prove
absence of trimmed whitespace; the no-cell-change verifier remains mandatory.
