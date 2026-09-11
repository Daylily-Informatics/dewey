# Dewey 9 data-preservation and recovery preparation

**Status:** L08/L09 preparation is implemented; execution is blocked. The
coordinator's native 10.1.0 capture of `dewey_prod` failed with
`Identity receipt exceeds the declared size bound`; no source receipt was
written. No migration, restore, or production acceptance is claimed.
Author: role C, `gpt-6-astra` / `max`.
Independent acceptance belongs to role E, `gpt-6-astra` / `max`.

**Execution hold:** Role B is determining whether the immutable release has a
supported public configuration for this bound. Do not retry capture, partition
the source, omit rows/tables, alter package constants, or patch the installed
release. The commands below remain preparation until the coordinator resolves
this exact gate. No newer target version is implicitly approved.

**Controlling record:**
[Dewey major-upgrade ledger](20260910T185538Z_dewey_tapdb10_major_ledger.md).
Only the coordinator changes that ledger or operates AWS, databases, fences,
restores, runtime binding, or deployment. The steps below are reviewable command
templates, not a script to execute as a batch. Destructive restoration/reset/deletion
still requires the later exact-effect second approval.

| Binding | Required value or evidence |
|---|---|
| Service release | Dewey `9.0.0`, replacing the controlling `dewey.day.lsmc.bio` deployment |
| Source substrate | Actual installed TapDB `9.0.9`, reverified by the coordinator before capture |
| Target substrate | Published immutable TapDB `10.1.0`, commit `9db1abb4525f2594ebdbf2a307eb8b49aa51883d` |
| Target wheel SHA256 | `f46cb2abfccb3000b9f9443ea00045e83fb96f6b320d2aeac0ad800ea47e8801` |
| Original database | `dewey_prod` |
| Production replacement | Exactly `dewey_prod_tapdb10`; an existing destination is a refusal |
| Preserved schema/domain | `tapdb_dewey_lsmcok1_local` / `M` |
| Historical template binding | Preserve the observed `DGX` binding and every stored prefix; no substitution with `TPX` |
| Rehearsal destination | Separately approved explicit database/config/journal; never inferred from production names |

The controlling ledger supplies these baseline facts. Fresh native source and
provider receipts must establish the actual physical identity before operation.
The published release is accepted at the release level; its historical candidate
documentation does not reopen the waived CI/formal-review gates. Dewey adoption
evidence remains required.

## 1. Required evidence before L08 can be completed

Retain sensitive native inventories and recovery artifacts in the coordinator's
restricted evidence storage. Commit only sanitized references/checksums and
review conclusions. Native inventories can contain real persisted identities;
do not copy their full contents into Git or chat.

| Evidence | Required contents / owner |
|---|---|
| Source provenance | Running image digest, reconciled source commit, installed package versions, mounted/runtime-file references; O/A |
| Native source contract | Every physical table and sequence, physical/config identity, original rows including deleted rows, catalog dependencies, exact declared source version; O/B |
| External recovery set | Exact source/control/target configs and checksums, registry versions, TLS paths, IAM identity/policies, secret references and recovery method, runtime files; O |
| Original principal state | Login attributes, memberships, ownership, ACLs, effective database `TEMP`, runtime/operator scope and IAM mapping; owning-system evidence, not inferred from bootstrap/bind; O/B |
| Writer inventory | Web/service pools, background workers, integrations, maintenance clients, other allocator sessions; O/B |
| Immutable recovery family | Source and every planned replacement/rehearsal journal root, origin physical identity, canonical family UUID, retained journal heads; O/B |
| Preservation crosswalk | Every original table/row/column, lineage, audit, share/membership/idempotency and integration state; source-derived, never the former nine-table/twenty-sequence counts as a whitelist; C |
| Allocator crosswalk | All native generator names, prefix or owned-column proof, `last_value`, `is_called`, assigned/allocated floors, increment/start/bounds/cache/cycle/owner/dependencies and native plan next values; B/C |

Unknown/missing mappings, unreadable rows, unsupported generators, changed source
contracts, missing journals, or a required operation unavailable in immutable
10.1.0 block the relevant row. Do not patch TapDB, switch versions, add a shim,
or use raw SQL/dump tools to get past the failure.

## 2. Operator bindings and native source capture

Activate the coordinator's reviewed Dewey environment with
`source ./activate <explicit-deploy-name>`. Role B must first prove that its
`tapdb` executable is the published `10.1.0` artifact. This runbook explicitly
delegates substrate operations to the public TapDB CLI.

Before each command, bind every variable to an explicit reviewed value. Configs,
mapping files, family descriptors, journals, and all input/output files must use
full absolute paths. Do not infer one deployment's settings from another.

| Variables | Meaning |
|---|---|
| `SOURCE_CONFIG`, `CONTROL_CONFIG` | Source config and a different existing control database on the same verified server |
| `DESTINATION_CONFIG`, `DESTINATION_DATABASE` | The exact approved destination for this attempt; production uses `dewey_prod_tapdb10` |
| `SOURCE_MAPPINGS`, `DESTINATION_MAPPINGS` | Explicit verified mapping files from catalog/owning-registry evidence; no copied guesses |
| `SOURCE_JOURNAL`, `REHEARSAL_JOURNAL`, `REPLACEMENT_JOURNAL` | Existing canonical absolute roots, all included before sealing the family |
| `FAMILY_ID`, `RECOVERY_FAMILY` | Operator-selected canonical UUID and new native family receipt file |
| `SOURCE_INITIAL`, `SOURCE_FINAL`, `TARGET_HISTORICAL` | Distinct new native source-contract receipt files |
| `PROVIDER_CONTRACT` | Qualified Aurora provider evidence for the exact operation |
| Other output variables | Distinct new files in the restricted evidence store; never reused or overwritten |

Shell variables below are operator inputs, not defaults. Use an unset-variable
error policy in the operator shell, and stop after any failed command. Record
UTC start/end, command arguments with secret values excluded, exit status, and
owning receipt/reference for every step.

Create the family and initial historical source contract through the native CLI:

```bash
tapdb --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$SOURCE_MAPPINGS" \
  --new-recovery-family-id "$FAMILY_ID" \
  --family-receipts-dir "$SOURCE_JOURNAL" \
  --family-receipts-dir "$REHEARSAL_JOURNAL" \
  --family-receipts-dir "$REPLACEMENT_JOURNAL" \
  --family-receipt "$RECOVERY_FAMILY" --receipt "$SOURCE_INITIAL"
```

Repeat `--family-receipts-dir` for every additional explicitly planned root.
Never edit the sealed descriptor to add or omit a replacement. Retain each
root's head anchor and all aborted or ambiguous intents throughout recovery.

When the coordinator has stopped writers and established the qualified source
fence, capture a new final source contract. A source still changing is not ready
for the final backup:

```bash
tapdb --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$SOURCE_MAPPINGS" \
  --recovery-family "$RECOVERY_FAMILY" --receipt "$SOURCE_FINAL"
```

The original and final contracts are both retained. Planned maintenance does not
waive final source capture or sequence-session closure.

## 3. Backup and explicit isolated restore

Use the same source contract and family for plan/create; a changed source forces
a new capture and review:

```bash
tapdb --config "$SOURCE_CONFIG" --json backup plan --class full \
  --source-contract "$SOURCE_FINAL" --recovery-family "$RECOVERY_FAMILY"

tapdb --config "$SOURCE_CONFIG" --json backup create --class full \
  --source-contract "$SOURCE_FINAL" --recovery-family "$RECOVERY_FAMILY"

tapdb --config "$SOURCE_CONFIG" --json backup verify \
  --backup-id "$BACKUP_ID" --level deep
```

`BACKUP_ID` must come from the successful native creation receipt. Preserve the
manifest, verification result, source identity asset and immutable backup
location, plus the external recovery set from section 1.

Compose `RECOVERY_SOURCE` only from actual native outputs. Its exact purpose is:

| Attempt | Required recovery-source content |
|---|---|
| Isolated rehearsal | `purpose: isolated_rehearsal` and unchanged `recovery_family` from the backup contract |
| Production/source recovery | `purpose: fenced_source_recovery`, fresh sealed `source_contract`, verified source `writer_fence` or separately qualified quarantine evidence, canonical `source_receipts_dir`, unchanged `recovery_family` |

`fenced_migration` belongs to native migration receipts; it is not a restore
purpose. Do not handwrite or alter sealed native receipts.

Stage the exact destination and preserve the resulting plan fingerprint:

```bash
tapdb --config "$DESTINATION_CONFIG" --json backup restore-plan \
  --backup-id "$BACKUP_ID" --mode isolated \
  --target-database "$DESTINATION_DATABASE" \
  --target-schema tapdb_dewey_lsmcok1_local \
  --recovery-source "$RECOVERY_SOURCE" \
  --control-config "$CONTROL_CONFIG" --provider-contract "$PROVIDER_CONTRACT"
```

If the qualified native lifecycle requires explicit writer-fence or quarantine
input, add its exact `--writer-fence` or `--quarantine-receipt` argument to both
plan and apply. Missing required evidence is a blocker; omitting it is not an
alternate restore path. The plan must prove the actual database/OID/server/port,
unchanged schema/domain/owner, absent destination, and complete family history.

After the separate exact-target approval gate, the coordinator uses the unchanged
arguments plus the reviewed fingerprint:

```bash
tapdb --config "$DESTINATION_CONFIG" --json backup restore \
  --backup-id "$BACKUP_ID" --mode isolated \
  --target-database "$DESTINATION_DATABASE" \
  --target-schema tapdb_dewey_lsmcok1_local \
  --plan-fingerprint "$RESTORE_PLAN_FINGERPRINT" \
  --recovery-source "$RECOVERY_SOURCE" \
  --control-config "$CONTROL_CONFIG" --provider-contract "$PROVIDER_CONTRACT"
```

No schema initialization, `db setup`, `db schema apply`, old Dewey bootstrap,
overwrite seeding, `--allow-identity-mismatch`, `--allow-unknown-migrations`, or
`--allow-unclaimable-prefixes` is part of this migration. Successful restore
must still report `principal_binding_required: true`.

Use the explicit isolated restore flow for the service rehearsal. The convenience
`backup rehearse` command owns a disposable generated name and cleanup behavior;
it does not replace this ledger's reviewed destination, retained journals,
separate migration, failure exercises, or service acceptance.

## 4. Target-local historical contract and migration

The restored database still has historical schema/assets. Capture its own
physical/config identity with the historical source version:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$DESTINATION_MAPPINGS" \
  --recovery-family "$RECOVERY_FAMILY" --receipt "$TARGET_HISTORICAL"
```

Use this new target-local contract for migration preflight/apply. Native migration
compares `--source-contract` against the current configured and physical database.
The original `dewey_prod` contract cannot be passed unchanged as that target-local
contract, and its sealed fields must never be edited to make it match.

First verify original-to-restored preservation using a reviewed target-only
conversion manifest: its `target` is copied exactly from the restored inventory,
`tables` is empty, and `added_tables` is empty. Native restore also records its
own exhaustive preservation check. Both checks must pass before migration.

After the database exists, the coordinator can plan and apply CONNECT-only
`db runtime-principal bootstrap`. Retain its JSON plan/result. It does not
initialize schema or grant runtime schema access. Binding remains later.

```bash
tapdb --config "$DESTINATION_CONFIG" --json db schema migrate --dry-run \
  --receipt "$MIGRATION_PREFLIGHT" --source-contract "$TARGET_HISTORICAL" \
  --sequence-mappings "$DESTINATION_MAPPINGS" \
  --receipts-dir "$DESTINATION_JOURNAL" --recovery-family "$RECOVERY_FAMILY"
```

Review exact pending migration filenames/checksums, transformation contracts,
permitted new tables/rows, scope changes, prefix preservation, and generators.
Then the coordinator applies that preflight under the qualified writer fence:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db schema migrate --apply \
  --preflight-receipt "$MIGRATION_PREFLIGHT" --receipt "$MIGRATION_RESULT" \
  --source-contract "$TARGET_HISTORICAL" \
  --sequence-mappings "$DESTINATION_MAPPINGS" \
  --receipts-dir "$DESTINATION_JOURNAL" --recovery-family "$RECOVERY_FAMILY" \
  --establish-writer-fence --control-config "$CONTROL_CONFIG" \
  --provider-contract "$PROVIDER_CONTRACT"
```

A reviewed existing fence can use `--writer-fence` instead of the
`--establish-writer-fence` / control-config pair. Do not combine the two.
Preserve migration result, allocator intent/completion, and gate-release evidence
separately. Source and destination application writers stay stopped after a
native operation releases its temporary database gate.

## 5. Conversion-manifest review

Capture a new destination inventory after each completed conversion stage:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity inventory \
  --sequence-mappings "$DESTINATION_MAPPINGS" --receipt "$TARGET_AFTER"
```

The offline helper consumes only existing native inventory/source-contract
files. It checks versioned JSON and checksum integrity, then lists catalog
changes and exact row/column hashes. It has no database imports, does not compute
allocator positions, does not print row identity values, and writes only a new
mode-0600 review file. Its 192 MiB input limit is explicit; exceeding it blocks
this helper and must be reviewed, not silently truncated.

That local file limit does not change native capture capacity. Immutable 10.1.0
sets `MAX_RECEIPT_BYTES` to 128 MiB of accumulated row-receipt content and refused
the actual source capture at that bound. This helper needs a complete existing
native receipt and cannot provide one when native capture fails.

```bash
python "$DEWEY_MIGRATION_REPO/scripts/tapdb10_inventory_diff.py" \
  --before "$SOURCE_FINAL" --after "$TARGET_AFTER" --report "$DIFFERENCE_REVIEW"
```

This is an offline evidence-review tool, not a Dewey/TapDB operational bypass.
Exit zero means a review file was produced. Every report is `review_required`.
It checks file integrity, not source authenticity, complete native semantics,
preservation acceptance, or permissions. No conversion manifest is generated
automatically, even when the comparison contains no differences.

Construct the native `tapdb-identity-conversion/v1` manifest from the actual
source/destination receipts and reviewed native migration contracts:

| Native field | Dewey review rule |
|---|---|
| `schema_version` | Exactly `tapdb-identity-conversion/v1` |
| `target` | Exact destination inventory target; physical relocation is separately bound by restore/config/provider evidence |
| `added_tables` | Only individually justified native/service tables; record each table's content hash and added-row keys in the review |
| `tables.<name>.added_columns` | Exact newly introduced column names, tied to reviewed migration/conversion behavior |
| `tables.<name>.schema_changes` | Enable only for individually reviewed tables; enumerate every catalog difference, including owner, RLS, policies, triggers, constraints, indexes and dependencies |
| `tables.<name>.added_rows` | Enable only for individually reviewed tables; bind the exact observed added keys/counts/hashes to this attempt's review |
| `tables.<name>.changed_columns` | Exact permitted non-identity cell transitions with a documented reason; prefer `exact_value_hashes` tied to actual row keys and before/after hashes |

Native `schema_changes: true` and `added_rows: true` are table-level permissions;
they do not independently establish that every particular catalog change or
added row is intended. Role E must compare the exact reviewed differences with
the final native evidence. A hash match is not proof of intended semantics.

Retain UID/EUID, original prefixes and bindings, domain/tenant/issuer/machine
identity, creation identities, original rows including deleted rows, lineage,
audit, deduplication, shares, memberships, and integration state. No identity
conversion is permitted. In particular, `DGX` business objects and historical
template bindings must remain unchanged even if a prefix-config column is not
classified as immutable by native inventory metadata.

The native historical outbox migration has a narrowly defined
`null_reference_from_mapping/v1` contract. If actual source data requires it,
review its exact source NULL cell, newly persisted target and mapping row keys,
mapping-row digest, and validated FK dependencies. This fills an originally NULL
reference; it must not rewrite an existing reference or intrinsic identity.
Use only persisted native migration outputs, never manufactured EUIDs or guessed
mapping rows. The crosswalk must name every such actual row.

Dewey's typed external-reference objects and `generic_instance_lineage` remain
authoritative. Existing copied metadata or graph blobs do not establish new
relationships. No service-owned rewrite is approved merely because the new
substrate can represent data differently. If a necessary Dewey conversion emerges,
record the actual requirement and implement/review its supported service command
before execution; no ad hoc post-migration writes or bootstrap seeding.

Run native verification against the original source, then preserve its output
and exit status in the evidence store:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity verify \
  --before "$SOURCE_FINAL" --after "$TARGET_AFTER" \
  --conversion-manifest "$CONVERSION_MANIFEST" \
  --sequence-mappings "$DESTINATION_MAPPINGS"
```

`--after` makes this comparison consume the explicit recorded destination
inventory; omitting it performs a fresh read-only capture. The native command
has no `--receipt` flag. Capture stdout without overwriting any earlier evidence.
After any subsequent data/catalog mutation, capture again and renew the review.

## 6. Floors strictly beyond the prior next values

Preserve all generator definitions and mappings. At reopening, every supported
generator's next value must exceed the maximum retained floor from initial
source, final fenced source, every destination, assigned/reserved/aborted/probe/
migration values, and the entire recovery family. Include the previous source
**next value**, not only its `last_value` or largest persisted row.

Use native sequence plans to calculate next values. Do not implement sequence
arithmetic in Dewey. A separately labelled observation input containing only
`{"floors": []}` is permitted for a read-only native observation plan; it is
never the final/apply floor document and never claims migration readiness:

```bash
tapdb --config "$SOURCE_CONFIG" --json db sequences advance \
  --floors "$OBSERVATION_INPUT" --receipt "$SOURCE_NEXT_PLAN" \
  --sequence-mappings "$SOURCE_MAPPINGS" --recovery-family "$RECOVERY_FAMILY"
```

Retain native plans for the controlling initial and final fenced source states
and the destination before final advancement. Native `advances[].next_value`
is at least the observed next value; family history can raise it conservatively.
Copy those native values into the retained floor input with exact sequence names
and plan-digest provenance. Do not derive a next value from the sequence name,
assume increment one, or discard an uncalled sequence's current next value.

The apply floor document has exactly one top-level key, `floors`, whose entries
have exactly `name` (native generator name), `value` (native observed/planned
integer), and nonempty `source` (receipt path/reference and digest). Retain
distinct provenances. Role B/C must reconcile full generator coverage, including
new native generators, without reducing scope to the former twenty sequences.

```bash
tapdb --config "$DESTINATION_CONFIG" --json db sequences advance \
  --floors "$RETAINED_FLOORS" --receipt "$ADVANCE_PREFLIGHT" \
  --sequence-mappings "$DESTINATION_MAPPINGS" --recovery-family "$RECOVERY_FAMILY"

tapdb --config "$DESTINATION_CONFIG" --json db sequences advance --apply \
  --floors "$RETAINED_FLOORS" --preflight-receipt "$ADVANCE_PREFLIGHT" \
  --receipt "$ADVANCE_RESULT" --sequence-mappings "$DESTINATION_MAPPINGS" \
  --recovery-family "$RECOVERY_FAMILY" --receipts-dir "$DESTINATION_JOURNAL" \
  --establish-writer-fence --control-config "$CONTROL_CONFIG" \
  --provider-contract "$PROVIDER_CONTRACT"

tapdb --config "$DESTINATION_CONFIG" --json db sequences verify \
  --floors "$RETAINED_FLOORS" --sequence-mappings "$DESTINATION_MAPPINGS" \
  --recovery-family "$RECOVERY_FAMILY"
```

Close old allocator sessions and pools before reopening. Cached/reserved values,
sequence exhaustion, nonpositive/cycling generators, changed ownership/mappings,
missing generators, unknown outcomes, or a stale preflight prevent resumption.
A successful command return does not replace the sealed apply/completion,
strict-floor verification, or gate-release receipts.

## 7. Rebinding, rehearsal evidence, and recovery decisions

After conversion/identity/floor checks pass, the coordinator plans
`db runtime-principal bind --receipt <new-absolute-plan>` and applies that exact
plan with `--apply`. Record the separate applied result. Review database-wide
PUBLIC/runtime `TEMP` revokes and explicit operator maintenance grants. Close
pre-binding runtime sessions; recreate them after bind and prove effective
`TEMP=false`, correct runtime principal/scope, and rejected startup DDL. Binding
does not close sessions or remove pre-existing temporary objects.

| L09 exercise | Required completion evidence |
|---|---|
| Historical restore | Exact backup ID/manifest, destination identity, deep verification, exhaustive original-row preservation, no runtime binding yet |
| Native migration and conversion | Reviewed preflight/result, pending-migration checksums, exact difference crosswalk, native identity verification, preserved DGX/lineage/audit/integration state |
| Allocator rehearsal | Initial/final/native-next floor provenance, all family roots/head anchors, exact advancement result, independent strict-floor and session/cache evidence |
| Failed migration | Native aborted or authoritative ambiguous outcome; all consumed/reserved values retained; target stays operator-only |
| Lost acknowledgement | Exact original journal root and intent ID; reconciliation evidence that distinguishes committed, rolled back, and observed-only outcomes |
| Repeated recovery | No lost/rewritten journal root, no reused allocation, no undeclared table/row changes, destination/principal explicitly rebound |
| Service acceptance | Independent role E API/GUI/auth and application-data tests using actual persisted objects, fresh sessions and exact new image/config |
| Timing | UTC duration of backup, restore, migration, conversion, verification, bind and acceptance; measured maintenance window proposed from this run |

For a stalled native fence, plan reconciliation with the exact root and intent:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db sequences reconcile \
  --control-config "$CONTROL_CONFIG" --receipts-dir "$STALLED_JOURNAL" \
  --fence-intent-receipt-id "$STALLED_FENCE_INTENT_ID" \
  --receipt "$RECONCILIATION_PREFLIGHT" --provider-contract "$PROVIDER_CONTRACT" \
  --sequence-mappings "$DESTINATION_MAPPINGS" --recovery-family "$RECOVERY_FAMILY"
```

For a lost gate-release acknowledgement, use the exact
`--release-intent-receipt-id` instead; the two intent options are mutually
exclusive. Apply only the reviewed reconciliation using `--apply`,
`--preflight-receipt`, and a new result `--receipt`. The target remains
operator-only until a new review authorizes further work. Observed-only means
the physical state was measured; it does not mean the previous operation
committed. Never retry past an unresolved intent or replace an existing journal.

| Recovery point | Required action |
|---|---|
| Before accepted new production writes | Coordinator may review returning to the retained source only after native advancement beyond **all** exposed replacement/family values and new session verification |
| A retained generator cannot be represented safely on the old source through the native path | Keep the source fenced; rollback is blocked pending a supported recovery decision |
| After accepted writes on the replacement | Repair forward with all family evidence; image-only rollback would lose accepted state and is prohibited |
| Cleanup | Retain old source, backups, failed targets and journals; no automatic deletion or cleanup command is authorized here |

## 8. Preparation evidence and handoff

Local checks for the offline helper:

```bash
pytest --noconftest -q tests/test_tapdb10_inventory_diff.py
ruff check scripts/tapdb10_inventory_diff.py tests/test_tapdb10_inventory_diff.py
ruff format --check scripts/tapdb10_inventory_diff.py tests/test_tapdb10_inventory_diff.py
git diff --check
```

`--noconftest` keeps this bounded offline test from importing the application or
its database-related test fixtures. The structural test fixtures contain no real
Dewey records or Meridian-style EUIDs. They exercise deleted/lineage/integration
row retention visibility, prefix changes, catalog/physical changes, corruption,
ambiguous JSON, input-path refusal, private new output, and overwrite prevention.
They are not migration/allocator/restore acceptance.

**Recorded local validation, 2026-09-11:** All 16 focused tests passed in the
existing `DEWEY-d9impl` environment (Python 3.12.0). Ruff lint passed; the initial
format check requested layout changes, which were applied, and the final format
check passed for both Python files. The test receipt is reused after formatting;
no behavior changed and no full-suite or repeated database test was run. These
are author checks, not independent acceptance.

**Open blockers:** Native source capture exceeded the declared receipt-size
bound and wrote no receipt; actual source/final contracts are therefore absent.
Also outstanding: reviewed physical destination,
principal/writer and external recovery inventories; immutable family/journal
anchors; actual migration/conversion differences; exact retained floors;
separate restore approval; timed isolated run; independent role E acceptance.

**Next actions:** O/B capture and qualify the native evidence, C derives the
actual per-attempt conversion crosswalk, O executes the approved isolated
rehearsal, and E independently validates the results. L08/L09 remain open until
their actual ledger completion evidence exists. Phase-two features and outstanding
PRs begin only after the major replacement and its acceptance/closeout gates.

## Immutable upstream references

- [Native service lifecycle and receipt shapes](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/docs/service-readiness.md)
- [Identity capture/verify CLI](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/cli/identity.py)
- [Manifest contract and immutable-column checks](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/identity_inventory.py)
- [Target-local migration contract and native historical transformations](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/migration_identity.py)
- [Sequence CLI and reconciliation flags](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/cli/sequences.py)
- [Native allocator state and strict floor semantics](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/sequences.py)
- [Backup/restore CLI](https://github.com/Daylily-Informatics/daylily-tapdb/blob/9db1abb4525f2594ebdbf2a307eb8b49aa51883d/daylily_tapdb/cli/backup.py)
