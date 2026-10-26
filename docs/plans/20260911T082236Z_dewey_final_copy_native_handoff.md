# Final frozen-source copy and native execution handoff

C preparation for O/E; exact TapDB `10.1.1rc1`. No live command or additional
test was run for this handoff. The accepted scripts remain unchanged. O reports
the rehearsal completed-transition verification passed at
`2026-09-11T08:18:13.995753+00:00`, RC 0, native seal
`84c97198683d71494277cf05ccfb6df058481560d8c53a064b8855bb439c8eab`.
That actual completion is retained under the controlling ledger's evidence.

## 1. Accepted script paths and final exposure

Run each command separately through O's existing targeted-sudo interactive
`ubuntu` invocation, preserving its explicit AWS environment. These assignments
name the already staged scripts; they do not execute a stage:

```bash
OPERATOR_PYTHON=/home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/python
FINAL_COPY_SCRIPT=/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_final_copy.py
LIFECYCLE_SCRIPT=/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_copy_native_lifecycle_cli_fix.py
TRANSITION_SCRIPT=/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_sequence_transition_sop.py
REHEARSAL_CAPSULE=/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-native/capsule.json
REHEARSAL_EXPOSURE=/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-native/exposure-after-completed-transition-plan.json
FINAL_CAPSULE=/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-native/capsule.json
```

| Script | Accepted SHA-256 |
|---|---|
| Final copy | `a85dabc1a04e021b0afa6c7e781b9d6a7bd70637e259a40be9b59c609829501b` |
| Imported `dewey_rehearsal_copy.py`, in the same directory | `d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733` |
| Lifecycle with schema CLI-mode correction | `e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407` |
| Completed-transition SOP | `0e2765067beb776dfe914a553d02ef8d2710723ff2582cc5fa56e43b2b6378a1` |

After accepted rehearsal testing, stop every rehearsal writer/process and drain
its sessions. Keep rehearsal unchanged after exposure through final floor
preparation. The original `dewey_prod` OID 16749 remains closed and its original
container remains stopped throughout. Neither exposure nor final copy performs
rehearsal shutdown. No queue preservation/replay gate is added.

```bash
"$OPERATOR_PYTHON" "$TRANSITION_SCRIPT" exposure-plan \
  --capsule "$REHEARSAL_CAPSULE" --review-reference "$EXPOSURE_REVIEW"
```

Require new `exposure-after-completed-transition.completed.json`, actual RC 0,
and the exact native plan at `REHEARSAL_EXPOSURE`. E reviews the native plan,
complete terminal rehearsal family and stopped-writer evidence. Retain every
original/future floor and planned next. The final-copy script hashes this file;
it does **not** independently validate its native contents or stop writers.
Its acceptance reference must therefore identify this accepted terminal
rehearsal/exposure evidence, not only the earlier sequence apply.

## 2. Plan, review and create the fixed final database

```bash
"$OPERATOR_PYTHON" "$FINAL_COPY_SCRIPT" plan \
  --rehearsal-exposure-plan "$REHEARSAL_EXPOSURE" \
  --acceptance-reference "$REHEARSAL_ACCEPTANCE"
```

Review `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-copy-sop-plan.json`.
Then invoke `apply` with the **identical** exposure path and acceptance reference:

```bash
"$OPERATOR_PYTHON" "$FINAL_COPY_SCRIPT" apply \
  --rehearsal-exposure-plan "$REHEARSAL_EXPOSURE" \
  --acceptance-reference "$REHEARSAL_ACCEPTANCE"
```

This is the already reviewed three-action setup SOP: create the absent
`dewey_prod_tapdb10` closed using frozen `dewey_prod` as TEMPLATE, revoke PUBLIC
CONNECT/TEMP, open and verify owner-only access. It records
`receipts/final-copy-sop-result.json` and `receipts/final-copy-sop-events.jsonl`.
Accept only `copy_created_source_remains_fenced`, exact owner `dayhoff`, the
actual distinct final OID and unchanged source/control identities. Existing
target, outputs, changed fingerprint or partial execution stops the SOP; inspect
the retained evidence. Do not delete/recreate, change the destination name,
reopen source or create a backup.

## 3. Immutable final operator capsule

After successful copy, O creates private, separate, unused `final-native` and
`final-native-journal` directories under the existing receipts directory and
writes `FINAL_CAPSULE` exclusively. This is an operator input, not a native
receipt. Use exactly the following fields; fill actual facts before execution.

| Field | Final value / required evidence |
|---|---|
| `schema_version` | `dewey-native-copy-capsule/v1` |
| `database` | `dewey_prod_tapdb10` |
| `target_oid` | Actual JSON integer from final copy result; pending copy |
| `copy_config` | `/home/ubuntu/dewey_ops/tapdb101-20260911/replacement-operator.yaml` |
| `copy_config_sha256` | Actual hash of that fixed final operator config |
| `copy_receipt` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-copy-sop-result.json` |
| `copy_receipt_sha256` | Actual final result file hash; pending copy |
| `source_contract` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-source-cutoff.json` |
| `source_next_plan` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-source-next-plan.json` |
| `source_next_plan_sha256` | `019284408c20d71c415550ed081c893549e6f407966dd9f4991cc2e6d62c495f` |
| `migration_manifest` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/native-migration-manifest-20260911.json` |
| `family_id` | O's new canonical UUID, distinct from rehearsal; pending selection |
| `journal_dir` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-native-journal` |
| `output_dir` | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-native` |
| `extra_next_plans` | Array containing `{"path": REHEARSAL_EXPOSURE, "file_sha256": ACTUAL_EXPOSURE_FILE_SHA}` with the full absolute path substituted; retain any additional applicable exposure inputs |
| `control_config_sha256` | Existing accepted value `42491d0bf321d4d8027ef52918a1396e4e4c7f2c7bdecdabd82449b86b87686a`, conditional on unchanged `/home/ubuntu/dewey_ops/tapdb101-20260911/control-operator.yaml` |
| `provider_contract_sha256` | Existing accepted value `0700678f55acd55a39f2563b4ec73c4dbfba9876611644279ab3ad1d04abaa84` for `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/aurora-provider-contract-20260911.json` |

Keep operator config paths, capsule, all rehearsal/final journal roots and
input files unchanged. Final gets its own copy-rooted native family; do not
rename/join the rehearsal family. No source connection is needed: source/copy
verification uses the retained cutoff. The helper requires every historical
generator field except explicit physical/config target relocation to match.

## 4. Individual native stages and inspection gates

For ordinary stages, invoke the following form once with the selected stage:

```bash
"$OPERATOR_PYTHON" "$LIFECYCLE_SCRIPT" capture-copy --capsule "$FINAL_CAPSULE"
```

| Order | Stage / acceptance |
|---|---|
| 1 | `capture-copy` — final is a new target: perform its first native 9.0.9 inventory. Do not carry over rehearsal's instruction to skip an already completed capture. |
| 2 | `verify-copy` — exact frozen source to untouched final identity verification and complete generator equality; creates target-only manifest from actual final target. |
| 3 | `create-family` — native inventory creates final family and `copy-historical.json` before any schema/allocator mutation. |
| 4 | `migration-plan` — dry native migration using final historical source contract/family. Stop for E's actual plan review. |
| 5 | `migration-apply` — exact reviewed plan file hash/reference; native target/control/provider fence. |
| 6 | `capture-migrated`, then `verify-migrated` — independent invocations. Require native identity success and E's actual catalog delta acceptance before allocator apply. |
| 7 | `prepare-floors` — retain original frozen-source evidence plus every floor/planned-next from accepted rehearsal exposure, with full family validation. Review this new final external floor file. |
| 8 | `sequence-plan` — native final plan with final family and unchanged external floor input. E accepts all 20 next values strictly beyond every applicable source/rehearsal boundary. |
| 9 | `sequence-apply` — exact reviewed final plan and native fence. |
| 10 | Accepted transition SOP `prepare`, inspect its actual complete prior-floor projection, then `verify-completed`. Require fresh RC 0 and whole native verification equal to final apply's successful verification. |

The two applies require their own **file** SHA-256, not the embedded native
seal. For example:

```bash
"$OPERATOR_PYTHON" "$LIFECYCLE_SCRIPT" migration-apply --capsule "$FINAL_CAPSULE" \
  --reviewed-plan-sha256 "$FINAL_MIGRATION_PLAN_FILE_SHA" \
  --review-reference "$FINAL_MIGRATION_REVIEW"
```

Use `sequence-apply` with that plan's own hash/review for order 9. For order 10:

```bash
"$OPERATOR_PYTHON" "$TRANSITION_SCRIPT" prepare \
  --capsule "$FINAL_CAPSULE" --review-reference "$FINAL_SEQUENCE_REVIEW"
```

After inspection, invoke `verify-completed` with identical final capsule/review
arguments. Final floor counts and hashes come from its actual receipts; do not
reuse rehearsal's 130-floor file or its successful verification hash. This
explicitly supersedes lifecycle `sequence-verify` for the completed-operation
claim. That older full-family invocation would include the operation's own
newly retained future reservations. Preserve the entire family for future
plans/recovery; no narrowing applies to the final plan or advance.

The accepted migration manifest remains SHA
`af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8`.
With the unchanged cutoff, expect 11 tables/79,926 rows before runtime binding,
exactly eight added tracking rows, original `identity_key` NULL, both new tables
empty and every original cell preserved. E compares actual metadata with the
eight native migration assets; original DGX bindings, EUIDs, lineage and audit
remain exact. There is no per-row Dewey conversion step.

Then hand the actual accepted final identity/floor evidence to the existing
production principal workflow: `replacement-operator.yaml`, runtime role
`dewey_runtime_9`, and runtime config
`/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml`. Bootstrap/bind, fresh runtime
sessions, major release deployment and application acceptance remain O/D/E
stages. Existing Aurora protection and current-member repair forward remain the
recovery boundary after accepted production writes; no stale-source restart is
part of this handoff.

Source review: current final-copy lines 54–166; corrected lifecycle lines
145–191, 262–370; accepted transition SOP lines 124–200. Earlier capsule stage
names are superseded only as stated here. No accepted helper, ledger or live
state was changed by C. Documentation validation: `git diff --check` only.
