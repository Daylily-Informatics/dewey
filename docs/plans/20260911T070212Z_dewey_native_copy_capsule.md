# Dewey native copy execution capsule

Controlling ledger: `20260910T185538Z_dewey_tapdb10_major_ledger.md` in O's
worktree. Implements the public interfaces reviewed in
`20260911T060545Z_dewey_native_execution_inputs.md`, exact TapDB `10.1.1rc1`
commit `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. C authors this capsule; E
independently reviews it and its actual results. O alone executes live commands.

O reports source freeze/copy success at `2026-09-11T06:57:52Z`: source OID
`16749` stays closed, old container stopped with exit 0; rehearsal database
`dewey_tapdb10_rehearsal_20260911`, OID **645854**, owner `dayhoff`, open to the
operator only. Keep that outage through rehearsal and final cutover. No source
reconnection, extra backup, queue preservation/replay gate, runtime bootstrap,
runtime binding, or service start is performed by this capsule. Messages may
copy naturally under AM06's explicit waiver.

## 1. Prepare one immutable operator input file

Script: `scripts/dewey_copy_native_lifecycle.py`. Use the already installed
operator Python and native CLI under
`/home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/`. Every invocation must run
via targeted sudo from the existing interactive `ubuntu` session, retaining O's
existing explicit AWS environment. Native stdout/stderr remain protected files.

O prepares the following **operator input**, not a native receipt. Fields are
required exactly as listed; `extra_next_plans` is an explicit array. Do not use
unfilled placeholders. The actual copy OID and source freeze are already known;
only O's selected family UUID, new journal directory, exact local manifest path
and actual file hashes remain to fill.

| Field | Rehearsal value |
|---|---|
| `schema_version` | `dewey-native-copy-capsule/v1` |
| `database` | `dewey_tapdb10_rehearsal_20260911` |
| `target_oid` | `645854` (JSON integer) |
| `copy_config` | `ROOT/rehearsal-operator.yaml` |
| `copy_config_sha256` | SHA-256 of that existing file |
| `copy_receipt` | `ROOT/receipts/rehearsal-copy-sop-result.json` |
| `copy_receipt_sha256` | `2e477de116715b8c42c127618188d9607ac26826fb97453059b7921dd6c6ba7c` |
| `source_contract` | `ROOT/receipts/rehearsal-source-cutoff.json` |
| `source_next_plan` | `ROOT/receipts/rehearsal-source-next-plan.json` |
| `source_next_plan_sha256` | SHA-256 of the actual native next-plan file |
| `migration_manifest` | Absolute protected copy of the accepted manifest, file SHA `af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8` |
| `family_id` | O's explicit new canonical UUID |
| `journal_dir` | `ROOT/receipts/rehearsal-native-journal` (create once, empty, private) |
| `output_dir` | `ROOT/receipts/rehearsal-native` (already holds O's initial capture) |
| `extra_next_plans` | `[]` for rehearsal |
| `control_config_sha256` | SHA-256 of existing `ROOT/control-operator.yaml` |
| `provider_contract_sha256` | SHA-256 of existing `ROOT/receipts/aurora-provider-contract-20260911.json` |

Here `ROOT` means the complete absolute operator path above; expand it in every
JSON string. Put `capsule.json` under `output_dir`, write exclusively with mode
0600, and retain its SHA. Use the entire same immutable file for this copy's
stages. Native family identity also retains the operator config's pathname.
Changing an input or evidence file requires an explicit new reviewed operation;
there is no automatic rewrite, resume, reconciliation, or overwrite behavior.

The accepted manifest source is
`docs/plans/evidence/20260911T055609Z_dewey_native_migration_manifest.json`.
The accepted dormant mapping input is already at
`ROOT/receipts/source-sequence-mappings-20260911T053316Z.json`; its exact
`5b69e68d...` file hash is checked by the script. Neither file is inferred from
the database or edited in place.

## 2. Execute individual stages

For each row, invoke the same absolute script and capsule paths:

```bash
"$OPERATOR_PYTHON" "$LIFECYCLE_SCRIPT" verify-copy --capsule "$CAPSULE"
```

Use the row's stage instead of `verify-copy`. Paths in the following table are
relative to the explicit `output_dir` only. Every output is exclusive and
private. A failure leaves its evidence and any native journal intact; stop and
inspect the real state. Do not rerun a failed apply or reopen a native gate.

| Stage | Native operation / gate |
|---|---|
| `capture-copy` | Native historical `identity inventory --source-version 9.0.9`. **Already executed separately by O with RC 0; skip this invocation.** Retain `copy-untouched.json`, `capture-copy.stdout`, `.stderr`, `.rc`. |
| `verify-copy` | Bind actual OID/config/server to O's copy receipt; require every original generator definition/mapping/state/boundary equal; create the exact target-only conversion input; native `identity verify` from frozen source to copy. |
| `create-family` | After copy verification, native historical inventory with new family UUID, one explicit empty journal root and distinct family/source output files. |
| `migration-plan` | Require family capture unchanged from untouched copy; native `schema migrate --dry-run`, using the actual copy's `copy-historical.json`, family and journal. **Stop for independent plan review.** |
| `migration-apply` | Requires the reviewed plan's file SHA and explicit review reference; native `schema migrate --apply` with unchanged source/plan/family and native target/control/provider fence. |
| `capture-migrated` | Require complete native migration/recovery/release result; native inventory with `--source-version 10.1.1rc1` and the existing family. |
| `verify-migrated` | Native identity verification against `copy-historical.json` with the exact accepted same-target migration manifest. **E reviews the actual narrow difference before allocator apply/runtime bind.** |
| `prepare-floors` | Offline public native validators check source-next/family history; require source-next inventory equals the frozen cutoff; retain all assigned/allocated, already retained, and native planned-next integers unchanged. Writes `external-floors.json`, never a native receipt. |
| `sequence-plan` | Native read-only `sequences advance` using that floor input and complete copy family. **Stop for independent plan/floor review.** |
| `sequence-apply` | Requires the reviewed sequence-plan file SHA/reference; native fenced advance with unchanged floors, family, control and provider. |
| `sequence-verify` | Native strict floor verification; require actual RC 0, `ok: true`, empty `violations`. Runtime bootstrap/bind is a subsequent O operation. |
| `exposure-plan` | Only after rehearsal testing has stopped and its sessions/journals are terminal: native read-only advance with the same family/floors, to retain every rehearsal exposure for the final copy. It does not itself stop writers. |

Both applies use this additional exact form:

```bash
"$OPERATOR_PYTHON" "$LIFECYCLE_SCRIPT" migration-apply --capsule "$CAPSULE" \
  --reviewed-plan-sha256 "$REVIEWED_PLAN_FILE_SHA256" \
  --review-reference "$INDEPENDENT_REVIEW_REFERENCE"
```

Use `sequence-apply` and its own reviewed native plan for the other apply. The
SHA is of the entire actual plan file, not its embedded native `sha256` field.
Supplying a hash records the existing operational gate; it is not independent
acceptance by the author. No command automatically follows a successful plan.

## 3. Result acceptance and final-copy reuse

1. Native copy comparison permits only physical/config relocation. The
   additional operator sequence comparison excludes exactly `target`,
   `physical_target`, and the native seal; every other inventory field stays
   exact. No EUID, relationship, row, or allocator is reconstructed.
2. E constrains the accepted migration manifest's schema allowances to the
   eight reviewed assets, eight new migration tracking rows, original
   `identity_key` values NULL, and two empty new tables before binding. Original
   cells may not change. Use C's existing hash-only diff helper for that distinct
   catalog review; do not treat native RC 0 as the full application acceptance.
3. The source remains frozen. A separately approved final provider copy can be
   verified against the **same retained source cutoff**, without reconnecting
   to source. Use actual final copy identity, fixed final operator config,
   separate output/journal directories, and a new native family. Do not join or
   rename the rehearsal family.
4. Final `extra_next_plans` must explicitly include the stopped rehearsal's
   terminal exposure plan as `{"path": ABSOLUTE_PATH, "file_sha256": ACTUAL_SHA}`
   and every additional required exposure input. The helper retains all of
   each plan's floors and next values, including lower duplicate evidence; it
   never subtracts one, increments, deduplicates, or computes allocator values.
   The owning native APIs require complete current family history and reject
   missing generators. E owns completeness and cross-copy allocator meaning.
5. Existing Aurora recovery protection and current-member repair forward remain
   the recovery plan. This capsule does not create recovery artifacts, abandon
   family journals, reactivate stale source, or authorize an unreviewed changed
   physical recovery target after production accepts writes.

Source qualification: tagged `cli/identity.py:89–260`, `cli/sequences.py:38–277`,
`cli/db.py:1536–1840`, `backup/recovery.py:81–156,404–425`, and
`sequences.py:454–571`. Local execution is limited to new helper guard tests,
syntax/lint and diff checks; actual migration/allocator acceptance remains O/E.
