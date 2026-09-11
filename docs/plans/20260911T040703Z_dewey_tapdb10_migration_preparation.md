# Dewey 9 data-preservation and recovery preparation

**Status:** Preparation is amended for the explicitly approved published
`10.1.1rc1` candidate. The earlier 10.1.0 capture failed with
`Identity receipt exceeds the declared size bound` and wrote no receipt. The
coordinator's RC capture succeeded. The four dormant generators now have a
source-backed mapping input independently reviewed by B; native recapture remains.
The user selected an explicit source shutdown SOP for this migration; a new
TapDB source-isolation feature is not required. The actual conversion crosswalk,
target rehearsal, and recovery proof remain pending. No migration, copy,
or production acceptance is claimed.
Author: role C, `gpt-6-astra` / `max`.
Independent acceptance belongs to role E, `gpt-6-astra` / `max`.

**Backup boundary:** The user explicitly prohibited another backup. No new
logical backup, snapshot, checkpoint backup, or renamed export is part of this
runbook. Existing Aurora automated backups remain the recovery protection.
The reviewed transfer design is a one-time database copy followed by native
identity verification and migration; O alone owns its exact setup/approval.

**Version boundary:** The user authorized exact `10.1.1rc1`; this is not stable
10.1.1 or a merge to TapDB main. Role B owns artifact/provenance qualification.
The coordinator alone configures the explicit native budget and performs live
capture. Do not partition source evidence, omit rows/tables, alter package
constants, patch the installed release, or infer approval for another version.

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
| Target substrate | Exact published TapDB `10.1.1rc1`, tagged commit `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c` |
| Target wheel SHA256 | `26de691dd5f9c8fac596a18119c9220f4ea78826094753b47f9eb936b0677ce7`, verified by O/B; isolated EC2 installation and `pip check` passed |
| Annotated tag object | `1ac2f09a1787b9e747eda582c45a628ca60b7020`, peeling to the target commit above |
| Original database | `dewey_prod` |
| Production replacement | Exactly `dewey_prod_tapdb10`; an existing destination is a refusal |
| Preserved schema/domain | `tapdb_dewey_lsmcok1_local` / `M` |
| Historical template binding | Preserve all 11 original `DGX` and all 11 original `TPX` template identities and their exact bindings; no substitution between them |
| Rehearsal destination | Exact isolated copy/config/journal chosen by O for rehearsal before promotion; any separate database needs explicit approval and native family continuity |

The controlling ledger supplies these baseline facts. Fresh native source and
provider receipts must establish the actual physical identity before operation.
The prior stable release's accepted/waived gates remain historical evidence.
The RC's focused qualification and exact publication are separate receipts;
neither is a claim of stable promotion or completed Dewey adoption.

**Received census summary from O:** the native census authenticated to
`dewey_prod` (database OID `16749`, server `10.0.2.148:5432`, PostgreSQL `16.13`)
as owner/operator `dayhoff`; it reported 25 roles, 153 objects, and complete
activity visibility. Two connections were observed, including the census and
one idle `dayhoff` connection. `dewey_prod_tapdb10` was absent. Historical scope
binding structure was explicitly unavailable with no stored binding rows. These
are census observations, not proof of writer exclusion; the private sealed
receipt remains with O/B.

**Received source-inventory evidence from O:** native RC capture completed in
65.735 seconds, producing a 225,211,759-byte historical source-contract receipt
for source version `9.0.9`. It contains 79,918 identity rows across 9 tables,
173,423,825 row-evidence bytes, a largest serialized source row of 1,706,924 bytes,
and 20 sequences. The selected policy was 1,000,000 rows / 8 MiB per row /
512 MiB row evidence. `missing_generators` is empty, but four mappings remain
`unmapped`; successful capture is not successful mapping or transfer validation.

| Private native evidence | Retained reference / SHA256 |
|---|---|
| Remote source contract | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/source-inventory-10.1.1rc1.json` on the controlling Dewey EC2 host |
| Source contract SHA256 | `645315ea89b62edf78f30bdb83d282ea2bf782d4a98912f23662baeef2eba1b3` |
| Identity inventory SHA256 | `4a4d2df17d60f3caacd0b6decd3cee8ebc6263a9ad46b8908fb168b79cd2164f` |
| Sequence inventory SHA256 | `7dc63a2ae200cb19aa027994ee9a354be8108fe40c1ea9d478216f287ab4e1fc` |

The four dormant names are `ay_instance_seq`, `wsx_instance_seq`,
`wx_instance_seq`, and `xx_instance_seq`. The
[source-backed mapping review](20260911T053316Z_dewey_source_sequence_mapping_review.md)
binds explicit TapDB 9.0.9 declarations to their sealed native catalog evidence.
The [four-entry mapping input](evidence/20260911T053316Z_dewey_source_sequence_mappings.json)
does not change counters, create generators, or grant prefix ownership.
B independently reviewed this input; a fresh native capture with it remains
required before transfer, source-next planning, or advancement.

O's sanitized discovery index records the following original row counts. These
are a discovery baseline, not final cutoff values or a table whitelist:

| Original table | Rows | Observed identity prefixes |
|---|---:|---|
| `audit_log` | 66,666 | `ADT` |
| `generic_instance` | 12,204 | 12,200 `DGX`, 4 `GVR` |
| `generic_instance_lineage` | 1,015 | `EDG` |
| `generic_template` | 22 | 11 `DGX`, 11 `TPX` |
| `tapdb_identity_prefix_config` | 6 | Preserve every original keyed `prefix` value |
| `_tapdb_migrations` | 5 | Preserve original migration records |
| `inbox_message` | 0 | Empty at this capture |
| `outbox_event` | 0 | Empty at this capture |
| `outbox_event_attempt` | 0 | Empty at this capture |

All observed identity-domain rows were `M`. No original `is_deleted` value was
true in this discovery receipt; retain the ability to preserve deleted rows in
later capture and verification. The 11 Dewey templates bind `DGX`; the 11 native
templates have `TPX` identities and bind `MSG`, `SYS`, `GSE`, `XRF`, or `GVR`.
Empty native messaging tables do not prove the absence of service-owned typed
outbox objects, pending external requests, or an accepted remote outcome.

## 1. Required evidence before L08 can be completed

Retain sensitive native inventories and recovery artifacts in the coordinator's
restricted evidence storage. Commit only sanitized references/checksums and
review conclusions. Native inventories can contain real persisted identities;
do not copy their full contents into Git or chat.

| Evidence | Required contents / owner |
|---|---|
| Source provenance | Running image digest, reconciled source commit, installed package versions, mounted/runtime-file references; O/A |
| Native source contract | Every physical table and sequence, physical/config identity, original rows including deleted rows, catalog dependencies, exact declared source version, sealed `limits`/`usage`; O/B |
| External recovery set | Exact source/control/target configs and checksums, registry versions, TLS paths, IAM identity/policies, secret references and recovery method, runtime files; O |
| Original principal state | Native `db census` receipt: login attributes, memberships, ownership, ACLs, effective database `TEMP`, available runtime/operator scope and IAM mapping; no substitution with bootstrap/bind; O/B |
| Writer inventory | Web/service pools, background workers, integrations, maintenance clients, other allocator sessions; O/B |
| Immutable recovery family | After the copy is verified, create the family on its actual physical identity only if no earlier family or mutation history exists; include every planned journal root and retain original-source floors separately; O/B |
| Preservation crosswalk | Every original table/row/column, lineage, audit, share/membership/idempotency and integration state; source-derived, never the former nine-table/twenty-sequence counts as a whitelist; C |
| Allocator crosswalk | All native generator names, prefix or owned-column proof, `last_value`, `is_called`, assigned/allocated floors, increment/start/bounds/cache/cycle/owner/dependencies and native plan next values; B/C |

Unknown/missing mappings, unreadable rows, unsupported generators, changed source
contracts, missing journals, or a required operation unavailable in immutable
10.1.1rc1 block the relevant row. Do not patch TapDB, switch versions, add a shim,
or use raw SQL/dump tools to get past the failure.

## 2. Operator bindings and native source capture

Activate the coordinator's reviewed Dewey environment with
`source ./activate <explicit-deploy-name>`. Role B must first prove that its
`tapdb` executable is the published `10.1.1rc1` artifact. This runbook explicitly
delegates substrate operations to the public TapDB CLI.

Before each command, bind every variable to an explicit reviewed value. Configs,
mapping files, family descriptors, journals, and all input/output files must use
full absolute paths. Do not infer one deployment's settings from another.

| Variables | Meaning |
|---|---|
| `SOURCE_CONFIG`, `CONTROL_CONFIG` | Source config and a different existing control database on the same verified server |
| `CONTROL_DATABASE`, `REHEARSAL_DATABASE` | Exact reviewed names; presence/absence comes from authenticated native census, control login is independently proved |
| `DESTINATION_CONFIG`, `DESTINATION_DATABASE` | The exact approved destination for this attempt; production uses `dewey_prod_tapdb10` |
| `SOURCE_MAPPINGS`, `DESTINATION_MAPPINGS` | Independently reviewed explicit mapping files from exact source declarations and native catalog/registry evidence; the destination must preserve the same source evidence and prove its own matching catalog |
| `REHEARSAL_JOURNAL`, `REPLACEMENT_JOURNAL`, `RECOVERY_JOURNAL` | Explicit existing canonical absolute roots for every planned family operation, all included before sealing |
| `FAMILY_ID`, `RECOVERY_FAMILY` | Operator-selected canonical UUID and new native family receipt file |
| `SOURCE_INITIAL`, `SOURCE_FINAL`, `TARGET_COPY`, `TARGET_HISTORICAL` | Distinct new native contracts; the first untouched-copy contract precedes the copy-origin family contract |
| `PROVIDER_CONTRACT` | Qualified Aurora provider evidence for the exact operation |
| `INVENTORY_MAX_ROWS`, `INVENTORY_MAX_ROW_BYTES`, `INVENTORY_MAX_RECEIPT_BYTES` | Coordinator-selected positive finite native budgets; all three are recorded, with process memory/storage assessed separately |
| Planned native budget for the resumed capture | O selected 1,000,000 rows, 8,388,608 bytes per source row, 536,870,912 row-evidence bytes; conservative operating policy, not measured source size |
| Other output variables | Distinct new files in the restricted evidence store; never reused or overwritten |

Shell variables below are operator inputs, not defaults. Use an unset-variable
error policy in the operator shell, and stop after any failed command. Record
UTC start/end, command arguments with secret values excluded, exit status, and
owning receipt/reference for every step.

Set the selected capacity through the candidate's public config command before
capturing a new contract. This is an independent operator config change, not
an edit of the running Dewey application's config:

```bash
tapdb --config "$SOURCE_CONFIG" db-config update \
  --inventory-max-rows "$INVENTORY_MAX_ROWS" \
  --inventory-max-row-bytes "$INVENTORY_MAX_ROW_BYTES" \
  --inventory-max-receipt-bytes "$INVENTORY_MAX_RECEIPT_BYTES"
```

Apply the identical reviewed values through this same command to each explicit
destination config used for identity/copy/migration captures. The RC's
published example of a 512 MiB budget is not a measured Dewey requirement.
`max_receipt_bytes` counts cumulative row-evidence bytes, not database size,
indented JSON file size, or process memory. Complete evidence remains in memory.

Configured captures retain the existing `tapdb-identity-inventory/v1` format and
seal top-level `limits` and `usage`. Limits are resource policy, not physical
target identity. Native verification rejects conflicting policies or recorded
usage that violates them. Once captured, carry the same policy through copy
verification, migration, fence recovery and final verification. A policy
change requires deliberately reviewed fresh capture; never edit sealed receipts.

On another limit failure, retain the native `identity_inventory_limit` error and
its sanitized phase/table/processed_rows/accumulated_bytes/attempted_bytes/
limit_name/configured_value/attempted_value. Diagnostics do not constitute a
partial successful source contract. A new budget/retry is a separate coordinator
decision; never automatically raise capacity or narrow the evidence scope.

Capture the original principals and explicitly named database existence with
the new read-only native command:

```bash
tapdb --config "$SOURCE_CONFIG" --json db census \
  --database "$DESTINATION_DATABASE" --database "$CONTROL_DATABASE" \
  --database "$REHEARSAL_DATABASE" --receipt "$SOURCE_CENSUS"

tapdb --config "$SOURCE_CONFIG" --json db schema drift-check
```

The sealed `tapdb-principal-census/v1` receipt supplies role/ACL and observed
activity evidence. Explicitly unavailable visibility or historical scope
bindings stay unavailable. Source-server catalog proof of control existence
does not prove login to that control database; source authentication failure
does not prove destination absence. Activity is not a complete HTTP/service/
worker census or a writer fence. Census supports bounded
`--statement-timeout-ms` and `--max-catalog-rows`; record selected values if the
coordinator changes the published defaults. Overflow is failure, never truncation.
Drift-check exit 0 means clean, 1 means reported drift, and 2 means missing
database/inspection failure; expected historical drift is evidence for migration.

Capture the initial historical source without creating a family on the database
that will remain offline. Before selecting this path, O must confirm that no
prior source-origin family or mutating journal history already exists; preserve
and reconcile any such history instead of discarding it:

O confirmed during this amendment that no family or mutating journal had been
created. Recheck that fact before initial family creation if execution intervenes.

```bash
tapdb --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$SOURCE_MAPPINGS" \
  --receipt "$SOURCE_INITIAL"
```

The copy receives its own native family only after exhaustive preservation is
proved in section 4. Original source observations and native planned-next floors
remain immutable evidence and are supplied explicitly to destination advancement.

After the coordinator has stopped every source writer and established a
qualified exclusion posture that permits the required read-only operator
sessions, capture a new final source contract. A source still changing is not
ready for the final transfer:

```bash
tapdb --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$SOURCE_MAPPINGS" \
  --receipt "$SOURCE_FINAL"
```

The original and final contracts are both retained. The user approved the
following operator-owned source exclusion SOP, which O must make concrete with
the actual deployment and session-control commands before the maintenance gate:

1. Inventory every Dewey HTTP process, worker, scheduler, integration dispatcher,
   administrative CLI, and other holder of the source credentials. Bind the
   reviewed stop/disable commands and exact service/container identities to the
   evidence packet. Prevent automatic restarts or another operator starting a
   source client throughout the window.
2. Stop admission of **all** Dewey HTTP execution and new CLI/worker work. HTTP
   method filtering is insufficient: the external-object-relations GET route
   persists graph-reference synchronization. Drain the admitted requests and
   allocator work before stopping the whole source container and external
   workers. Retain container/process stop results and restarted-client refusal
   evidence; the independent TapDB operator environment remains available.
3. Drain the outbox dispatch acknowledgement window. A QEO request can be
   accepted remotely before Dewey commits its local outcome. Record every
   unresolved accepted/ambiguous outcome with existing request/idempotency
   evidence and its recovery disposition before final capture. Do not invent a
   successful local acknowledgement or blindly replay it. An earlier empty
   native outbox table does not waive this drain.
4. Close every previous non-operator database session and allocator pool,
   including idle sessions. Establish exclusive operator access using the
   reviewed deployment/network/credential controls, account for administrative
   and provider access, and retain the exact effective controls and session
   evidence. Census visibility supports this proof; a momentary census alone
   is insufficient. No source write or `nextval` probe is permitted after the
   cutoff. If O cannot prove exclusion, remain in maintenance and resolve that
   specific control before capture.
5. Keep those controls in place through final native identity/sequence capture,
   source-next observation, database copy, target preparation, final advancement,
   and cutover. After final capture, close the operator source sessions as well
   before copying from the separate control database. The source application
   and all other source writers remain stopped.
6. Record the cutoff UTC, complete writer/session inventory, stop/drain results,
   effective exclusive-access controls, observed native identities, and every
   artifact reference/digest in a clearly labelled **operator SOP receipt**.
   Keep it separate from sealed TapDB receipts. Any source write, new writer,
   connection-control loss, or ambiguous outcome invalidates the cutoff and
   requires O to review the change and obtain fresh controlling evidence.

For the reviewed database copy, this SOP owns source exclusion. Do not invent a
native `writer_fence` or quarantine receipt, use takeover on a healthy source,
or require a new TapDB release solely to automate this infrequent procedure.
Native migration, advancement, and reconciliation retain their connection gates
and evidence requirements. The copy itself is explicitly operator-owned setup;
it does not produce a native restore or family-join receipt. A native
`--establish-writer-fence` holds its own sessions while `ALLOW_CONNECTIONS` is
false; it is not a standalone
source maintenance command into which subsequent CLI processes can reconnect.
The source remains offline after cutover until a separately reviewed recovery
or retention decision; no source restart is part of normal cutover.

## 3. One-time Aurora database copy, without a new backup

The user stopped all new backup creation. Preserve the existing Aurora recovery
configuration and evidence; do not invoke logical backup creation, take a new
snapshot, or rename a backup operation as an export. O records the actual
cluster identity, existing retention and earliest/latest restorable times, plus
external config/registry/TLS/IAM and secret recovery references. Aurora manages
continuous backups; the latest restorable point is separate evidence from the
application cutoff. [AWS Aurora backup and recovery documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Managing.Backups.html)

AWS documents same-cluster database copying with `CREATE DATABASE ... TEMPLATE`
for Aurora PostgreSQL. This is the replacement database itself, not an extra
backup artifact. Confirm the actual cluster is ordinary Aurora PostgreSQL;
Aurora Limitless explicitly does not support this option.
[AWS Aurora database copy guidance](https://docs.aws.amazon.com/dms/latest/oracle-to-aurora-postgresql-migration-playbook/chap-oracle-aurora-pg.special.multitenant.html),
[AWS Limitless restriction](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/limitless-reference.DDL-limitations.html)

Exact RC source exposes fresh database creation and native archive restoration,
not a source-template copy option. The one-time copy therefore requires an
explicitly reviewed operator SQL capsule, rather than a fabricated TapDB command
or receipt. Its exact effect is to create absent `dewey_prod_tapdb10` from the
unchanged `dewey_prod`, preserving schema `tapdb_dewey_lsmcok1_local` and owner
`dayhoff`. O alone prepares and operates that capsule. Candidate statement for
review, not a command executed by this author:

```sql
CREATE DATABASE "dewey_prod_tapdb10"
  WITH TEMPLATE "dewey_prod" OWNER "dayhoff" ALLOW_CONNECTIONS false;
```

The complete capsule must establish and record:

1. Exact source/control/target physical identities, sufficient database-creation
   and source-owner authority, and target absence. Do not broaden source
   `IS_TEMPLATE` permissions merely to allow copying.
2. Final source contract and planned-next floors captured under section 2's
   persistent outage, then **all** source sessions closed. Execute the copy
   from the explicit different control database outside a transaction block.
3. Destination admission closed on creation. Database-level privileges and
   `ALTER DATABASE` settings are not copied: explicitly review their required
   values and establish operator-only target access before opening its gate.
   The inherited schema/data ACLs and ownership also require verification.
   `CONNECTION LIMIT` alone does not prove exclusion. Reopening the target for
   native operator commands must preserve exclusion of every runtime client.
4. Copy result plus independent destination existence/identity evidence. A lost
   acknowledgement requires inspection of this exact destination before any
   retry; no automatic drop, overwrite, or recreated alternate name.
5. Original source remains offline. Capture and verify the untouched destination
   through section 4 before any migration, issuance, seeding, or runtime binding.

The session, permission, and database-setting requirements follow
[PostgreSQL 16 CREATE DATABASE](https://www.postgresql.org/docs/16/sql-createdatabase.html).
The operator controls and resulting evidence must be reviewed independently;
this author has not executed the copy or certified live Aurora behavior.

No schema initialization, `db setup`, `db schema apply`, old Dewey bootstrap,
overwrite seeding, identity-mismatch allowance, or unclaimable-prefix waiver is
part of this transfer. Any destructive action, overwrite, cleanup, or provider
restore retains the separate exact-effect second-approval gate. A successful
copy is not migration, runtime-principal, or production acceptance.

## 4. Target-local historical contract and migration

The untouched copied database still has historical schema/assets. Capture its own
physical/config identity with the historical source version:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$DESTINATION_MAPPINGS" \
  --receipt "$TARGET_COPY"
```

First verify original-to-copy preservation. The target-only native conversion
manifest has the exact copied inventory `target`, empty `tables`, and empty
`added_tables`. No row or column conversion is allowed at this stage. Preserve
its reviewed file digest and the native verification output:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity verify \
  --before "$SOURCE_FINAL" --after "$TARGET_COPY" \
  --conversion-manifest "$COPY_TARGET_MANIFEST" \
  --sequence-mappings "$DESTINATION_MAPPINGS"
```

Identity verification does not substitute for allocator-copy equality. Compare
the complete sealed source/copy sequence payloads: every generator name,
definition, mapping/evidence, owner, dependency, `last_value`, `is_called`, and
assigned/allocated floor must match, with no missing or extra generator. Their
whole receipt hashes differ because physical/config identities differ; preserve
both receipts and record exact field-level equality excluding only those
expected relocation fields. No counter reduction or ignored unknown mapping is
permitted.

After that check passes, and only if O has established that there is no prior
family or mutating journal to reconcile, create the immutable native family from
the actual untouched copy. Do not pretend its new database OID belongs to a
source-origin family or synthesize a native restore/join receipt:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$DESTINATION_MAPPINGS" \
  --new-recovery-family-id "$FAMILY_ID" \
  --family-receipts-dir "$REHEARSAL_JOURNAL" \
  --family-receipts-dir "$REPLACEMENT_JOURNAL" \
  --family-receipts-dir "$RECOVERY_JOURNAL" \
  --family-receipt "$RECOVERY_FAMILY" --receipt "$TARGET_HISTORICAL"
```

Repeat `--family-receipts-dir` for every additional explicitly planned existing
root. Include the current destination journal. Retain all roots, head anchors,
aborted values, and ambiguous intents; never replace or narrow this descriptor.
Require the untouched-copy identity and sequence inventories to remain unchanged
across family creation. Preserve original-source initial/final/native-next
provenance separately and include those values in final retained floors.

Use `TARGET_HISTORICAL` for native migration preflight/apply: its historical
schema version is `9.0.9`, while physical/config identity belongs to this actual
copy and its native family. The original `dewey_prod` contract cannot be passed
unchanged as that target-local contract. Never edit sealed target fields.

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
files. It checks versioned JSON and checksum integrity, then lists catalog,
recorded `limits`/`usage`, and exact row/column hash differences. It has no
database imports, does not compute allocator positions, does not print row
identity values, and writes only a new mode-0600 review file.

The CLI requires `--max-input-bytes`: a separately reviewed finite limit for
each complete input JSON file. Choose it using actual native artifact sizes and
available review-host memory; native row-evidence budgets do not determine
indented JSON file sizes. The helper streams file hashing, canonical checksum
encoding, and review output, avoiding extra full serialized copies. Both parsed
inventories and the review still occupy memory; this is not a constant-memory
comparison. Exceeding the selected file limit is a refusal, never truncation.
No local file budget can substitute for a complete successful native capture.

```bash
python "$DEWEY_MIGRATION_REPO/scripts/tapdb10_inventory_diff.py" \
  --before "$SOURCE_FINAL" --after "$TARGET_AFTER" --report "$DIFFERENCE_REVIEW" \
  --max-input-bytes "$REVIEW_MAX_INPUT_BYTES"
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
| `target` | Exact destination inventory target; physical copy is separately bound by source/copy/config/provider evidence |
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
source, final isolated source, every destination, assigned/reserved/aborted/probe/
migration values, and the entire recovery family. Include the previous source
**next value**, not only its `last_value` or largest persisted row.

Use native sequence plans to calculate next values. Do not implement sequence
arithmetic in Dewey. A separately labelled observation input containing only
`{"floors": []}` is permitted for a read-only native observation plan; it is
never the final/apply floor document and never claims migration readiness:

```bash
tapdb --config "$SOURCE_CONFIG" --json db sequences advance \
  --floors "$OBSERVATION_INPUT" --receipt "$SOURCE_NEXT_PLAN" \
  --sequence-mappings "$SOURCE_MAPPINGS"
```

This source-local observation omits the family flag because it records the old
source's allocators only; replacement journals may contain new generators that
do not exist in the historical schema. It makes no family-completeness or
recovery claim. The complete unchanged family is still mandatory for destination
advancement/verification and any source recovery.

The final source-next capture procedure is:

1. O/B prove writer exclusion, closure of cached allocator sessions, and the
   operator connection posture described in section 2. Stop new family operations
   during the controlling cutoff. Census alone is insufficient.
2. Capture `SOURCE_FINAL` once through the section-2 native historical-contract
   command, then immediately capture a **new** source-local `SOURCE_NEXT_PLAN`
   using the observation command above. Keep both immutable output files; do not
   overwrite an earlier initial-source or rehearsal observation.
3. Require `SOURCE_NEXT_PLAN.inventory.sha256` to equal
   `SOURCE_FINAL.sequence_inventory.sha256`, with the same configured/physical
   source identity and complete generator-name set. No allocator may change
   between these captures. Mismatch blocks this cutoff; O investigates the writer
   or state change and reviews any new capture instead of editing either receipt.
4. Copy every native planned safe `advances[].next_value` into the retained floor
   document as that generator's `value`; bind each entry's `source` to the exact source-next
   plan path, plan SHA256, and sequence-inventory SHA256. This uses native
   calculated values, including an uncalled sequence's next value. Retain initial
   source and all other observed/reserved provenance separately.
5. Obtain the corresponding native destination observation immediately before
   final advancement, add its proven values, and present the reviewed complete
   retained floor document plus unchanged family to the destination advance plan.
   Its native plan must cover every current generator and every applicable family
   floor. Reject unknown/missing mappings, omitted generators or a stale family
   head. After apply, require strict native verification and session/gate evidence
   before allowing any service allocation.

Native `advances[].next_value` is a planned safe next, at least the observed
unreserved next value; assigned/allocated floors can raise the plan. A higher
native candidate is a conservative floor. Do not derive a next value from a
sequence name, assume increment one, or discard an uncalled sequence's current
next value. Complete family reconciliation belongs to the native
destination/recovery operations.

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
| Historical copy | Exact operator copy capsule/result, source/target physical identities, target-only native exhaustive preservation verification, no runtime binding yet |
| Native migration and conversion | Reviewed preflight/result, pending-migration checksums, exact difference crosswalk, native identity verification, preserved DGX/lineage/audit/integration state |
| Allocator rehearsal | Initial/final/native-next floor provenance, all family roots/head anchors, exact advancement result, independent strict-floor and session/cache evidence |
| Failed migration | Native aborted or authoritative ambiguous outcome; all consumed/reserved values retained; target stays operator-only |
| Lost acknowledgement | Exact original journal root and intent ID; reconciliation evidence that distinguishes committed, rolled back, and observed-only outcomes |
| Repeated recovery | No lost/rewritten journal root, no reused allocation, no undeclared table/row changes, destination/principal explicitly rebound |
| Service acceptance | Independent role E API/GUI/auth and application-data tests using actual persisted objects, fresh sessions and exact new image/config |
| Timing | UTC duration of source isolation, copy, migration, conversion, verification, bind and acceptance; measured maintenance window proposed from this run |

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
| Before accepted new production writes | Keep the original source offline. A possible return requires separately qualified native family continuity, every retained generator, advancement beyond **all** exposed values, and fresh sessions; the old source is not a member of the copy-origin family |
| Any family-retained generator is absent from the historical source/recovery point | Keep the old source offline; repair the current family member forward or use an existing Aurora recovery point that contains current schema and accepted state, with separately qualified family continuity |
| After accepted writes on the replacement | Recover the current accepted-write state or repair forward with all family evidence; image-only or old-archive rollback would lose accepted state and is prohibited |
| Cleanup | Retain old source, backups, failed targets and journals; no automatic deletion or cleanup command is authorized here |

The generator condition can arise before the first new business write. Evaluate
the actual before/after native inventories and journal heads; do not assume the
RC creates a new generator merely because a migration name refers to prefixes.
Native restore refuses an archive that omits a retained family generator, and
native advance likewise refuses a retained floor whose generator is absent.
Never remove those floors, omit a family root, or fabricate a generator to make
an older archive pass. This is a recovery phase boundary for the SOP.

The user prohibited additional checkpoint backups. Record post-migration and
post-cutover native evidence and the existing Aurora earliest/latest restorable
times instead. Confirm that the actual chosen recovery point includes the
required schema, every retained generator, and the accepted application state.
Do not call an older restore point current, or silently accept loss of writes
between that point and the observed application cutoff.

Repair-forward within the current family member preserves its physical
membership. If existing Aurora backups are needed, the coordinator must prepare
the exact provider restore, destination, accepted-state boundary, and native
family-continuity procedure before the separate restore approval. A new database
OID/server is not automatically a member of the old family. Do not fabricate a
native join, discard existing family history, or create a new backup to avoid
this review. The source remains offline; all original/current native receipts,
source floors, family journals, and remote acknowledgement evidence remain
retained. If accepted state or a native outcome is unresolved, remain in
maintenance and resolve that exact issue before reopening.

## 8. Preparation evidence and handoff

RC delta checks for the offline helper:

```bash
pytest --noconftest -q tests/test_tapdb10_inventory_diff.py \
  -k 'test_rc_ or historical_contract_retains_exact_input_file_references or report_is_exclusive_private_and_cannot_overwrite_an_input'
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

**RC delta validation, 2026-09-11:** 12 selected cases passed: ten new cases for
the sealed limits/usage fields, explicit finite file budget, streamed canonical
hash equivalence/output, and required CLI budget; plus two existing source-file
reference/output-protection cases affected by the I/O changes. Ruff lint and
formatting passed. The other fourteen original cases were not rerun. No native
database tests, live operations, fabricated identities, or acceptance claims
were added by this author.

**Currently missing before execution:**

| Area | Exact required evidence / owner |
|---|---|
| Source inventory | RC capture succeeded and B independently accepted the four-entry mapping input. A new native contract with all 20 observed mappings resolved remains required; O/B/E |
| Source next floors | Initial native safe-next plan; later final contract/plan inventory-hash equality under qualified exclusion, every generator and retained provenance; O/B/C |
| Original principals | Native census summarized above; retain its private sealed reference/digest and address explicitly unavailable historical scope evidence. Control/rehearsal observations must be bound to their exact selected names; O/B |
| Control | Explicit existing absolute config, different existing database on the exact server, successful authenticated control connection, operator/provider/TLS/IAM identity and required authority; O/B |
| Source maintenance SOP | User-approved operator exclusion: bind actual stop/drain/restart-prevention/access-control commands to complete writer inventory, close cached sessions, retain exclusive operator access and maintenance through cutoff/cutover. No new TapDB source-isolation feature is required; O/B |
| Service writers | Stop all HTTP execution, including the GET synchronization writer; drain QEO dispatch acknowledgement windows and record unresolved accepted outcomes; include all CLI/background/scheduler clients, stopped source container and closed database pools/sessions; O/D |
| Rehearsal destination | Exact approved isolated copy, absent-destination proof, explicit config with preserved schema/domain/owner/registries and matching inventory limits; any additional database requires explicit family continuity; O |
| Recovery family | Prove no prior discarded family/journals; create the initial family on the verified untouched copy, with every planned existing root/head anchor and retained original-source floors; O/B |
| Existing Aurora recovery and external set | Actual retained backup/recovery window and chosen restore-point coverage, configs, registries, TLS/IAM, secret recovery references, image/runtime files and original principal evidence; no new backup creation; O/B |
| Conversion and acceptance | Actual per-attempt differences and manifest, reviewed copy/access-control capsule, timed isolated migration/floor/recovery receipts, and independent role E acceptance; C/O/E |
| Current-schema recovery | Repair-forward on the current family member or separately reviewed use of existing Aurora recovery with proven accepted-state coverage and native family continuity; no new checkpoint backup or unconditional old-source restart; O/B/E |

The old 128 MiB failure remains historical evidence; actual RC capture succeeded.
The fixed candidate plus supported native commands and the reviewed operator SOP
remain the implementation platform. Mapping qualification, exact conversion
review, complete source isolation, and measured rehearsal/recovery are remaining
execution and acceptance evidence, not automatic requests for another release.

**Next actions:** O/B capture and qualify the native evidence, C derives the
actual per-attempt conversion crosswalk, O executes the reviewed copy and isolated
rehearsal, and E independently validates the results. L08/L09 remain open until
their actual ledger completion evidence exists. Phase-two features and outstanding
PRs begin only after the major replacement and its acceptance/closeout gates.

## Immutable upstream references

- [RC publication scope, capacity policy, census, and drift contract](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/docs/plans/20260911_tapdb_dewey_prerelease_handoff.md)
- [Native service lifecycle and receipt shapes](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/docs/service-readiness.md)
- [Identity capture/verify CLI](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/cli/identity.py)
- [Manifest contract, limits policy, and immutable-column checks](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/identity_inventory.py)
- [Target-local migration contract and native historical transformations](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/migration_identity.py)
- [Sequence CLI and reconciliation flags](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/cli/sequences.py)
- [Native allocator state and strict floor semantics](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/sequences.py)
- [Fence session lifecycle and journal-bound takeover](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/sequence_fence.py)
- [Backup/restore CLI](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/cli/backup.py)
