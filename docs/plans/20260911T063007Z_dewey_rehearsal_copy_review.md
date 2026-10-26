# Independent review of Dewey rehearsal-copy SOP

**Current disposition:** Exact apply capsule accepted. Revised source SHA-256
`d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`
matches O's actual plan SHA-256
`30524c4f5438712dd60c0af87402ea805835817c1fb4ca2b2f63be20932ac1a5`.
All three initial findings below are closed. The latest
user instruction authorizes keeping Dewey offline through rehearsal and final
cutover; revised success retains source admission closed and container stopped.

Reviewed 2026-09-11. Scope: O's
`scripts/dewey_rehearsal_copy.py` in the controlling Dewey worktree, initial
SHA-256 `9beee9bab6e7d0935c03c7d4ef41285c371be16c75f9eafa169dc66d16fb0d9d`.
E read source and official PostgreSQL documentation only. No script invocation,
test suite, database call, live action or change to O's script was performed.

The user waived preserving inbox/outbox messages and acknowledgment/replay
acceptance: other systems can resend if needed. This review adds no queue-drain
or queue-preservation gate and requests no intentional deletion. All other
identity, row, relationship and allocator requirements remain in force.

## Route and native interface acceptance

- Source and target names are fixed: source `dewey_prod` OID 16749; rehearsal
  `dewey_tapdb10_rehearsal_20260911`; final `dewey_prod_tapdb10` must remain
  absent; control is authenticated `postgres` OID 5 as `dayhoff`.
- The exact original container ID/image/restart policy and all three operator
  config file hashes are part of the plan/apply fingerprint. Mapping input is
  independently pinned to its accepted SHA-256. Exact published RC is required.
- The plan path executes database reads and records a plan only. Apply refuses
  a different fingerprint or an already used operation output. It stops the
  selected container with a 300-second graceful shutdown allowance and rejects
  running/OOM/unexpected-exit state. It does not terminate unknown source
  sessions.
- Source capture uses the public native full `db identity inventory
  --source-version 9.0.9 --sequence-mappings ... --receipt ...`. The source-next
  command is the public read-only `db sequences advance --floors ... --receipt
  ... --sequence-mappings ...`, with exactly `{"floors":[]}` and no `--apply`.
  The comparison at lines 163–164 uses the correct native fields:
  `planned.inventory.sha256 == source.sequence_inventory.sha256`.
- The source gate is closed only after both separate native captures finish,
  with no source session left. The copy is created with admission already
  closed, then PUBLIC CONNECT/TEMP is revoked before opening copy admission.
  Source admission is restored and the same original container is started.
  This is O's explicit database-copy SOP, not a native TapDB fence receipt.
- Native `operator_session(control, isolation_level="AUTOCOMMIT")` passes the
  isolation setting to the engine and closes its verification transaction before
  yielding (`runtime_principal.py:240–327`). Therefore the PostgreSQL CREATE
  DATABASE statement is outside a database transaction block.

The remaining writer-exclusion premise belongs to O's accepted service/host
inventory: all non-container clients must also be stopped or excluded during
source capture. Session census is an observation and does not prove a dormant
client cannot reconnect. Reopening the old source after this short rehearsal
copy is intentional; final cutover later requires a fresh source cutoff/copy.

## PostgreSQL copy semantics checked

Closing source admission does **not** make it ineligible as the template for
CREATE DATABASE. PostgreSQL documents `template0` as normally closed, permits
the owner to clone another database, and requires other source sessions to be
absent. [PostgreSQL 16 template database documentation](https://www.postgresql.org/docs/16/manage-ag-templatedbs.html)

The command permits an initially closed destination, requires execution outside
a transaction block, and does not inherit source database grants or database
settings. O's owner/revoke steps and the source database-settings refusal match
those semantics. [PostgreSQL 16 CREATE DATABASE documentation](https://www.postgresql.org/docs/16/sql-createdatabase.html)

The exact upstream 16.13 implementation takes a source database lock, checks
owner permission and other backends/prepared transactions, and initializes a
default destination database ACL. It has no requirement that source
`datallowconn` be true. Aurora-specific support remains O's separately reviewed
owning-provider qualification. [PostgreSQL REL_16_13 implementation](https://github.com/postgres/postgres/blob/REL_16_13/src/backend/commands/dbcommands.c#L903)

## Bounded corrections sent to O before apply

1. **Preflight both native log paths before stopping production.** Initial
   lines 144–146 check receipt/event outputs but omit
   `logs/rehearsal-source-cutoff.log` and
   `logs/rehearsal-source-next-plan.log`. Each is opened with mode `x` only after
   the container has stopped. An existing log can therefore leave production
   stopped without starting the intended native capture. Include both log paths
   and their existing parent directories in the early collision/path check.
2. **Record final admission/ACL state, not the earlier closed snapshot.**
   Initial lines 173–176 capture `copied.datallowconn=false`, then lines
   178–180 open target and source gates. The success result at line 189 still
   includes that closed `copied` record. Retain it explicitly as creation state,
   then read/assert and record the final source/copy gates and copy ACL from the
   retained control session before claiming restored source and restricted
   copy admission. Do not report unconditional `copy_operator_only` without
   evidence for the asserted database admission policy.
3. **Join native cutoff physical identity to control identity explicitly.**
   Before closing source admission, require
   `source.sequence_inventory.physical_target` (and the identical identity
   inventory physical target) to match source database/OID/server observed by
   the control connection. The initial script checks fixed OIDs only through
   control; its floor evidence should also be tied directly to that source.

These are bounded SOP preflight/receipt corrections; no new TapDB release,
backup, raw schema conversion or repeated test suite is needed. A changed script
requires a new reviewed script fingerprint and preserved prior plan record.
O owns changes and the new read-only plan. This initial script revision is not
yet independently accepted for apply.

Any failure preserves its actual stage and evidence. The script correctly has
no automatic cleanup, retry or rollback. PostgreSQL AUTOCOMMIT means earlier
successful gate/copy/grant operations remain effective after a later exception;
context exit is not rollback of those operations. Native target migration,
family, sequence fences and binding have not begun. Source restart is a process
claim; O's normal original-service health confirmation follows separately.

## Revised script review

E re-read the exact revised script and independently recomputed its SHA-256
`d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`.
No script, plan, test or live operation was executed by E.

| Original finding | Revised evidence | Disposition |
|---|---|---|
| Log path checks after outage | Lines 157–161 check both `NATIVE_LOGS`, all output paths and parent directories before line 165 stops the container | Closed |
| Stale closed target snapshot in successful result | Lines 191–203 retain creation state, then inspect final gates and require source false, copy true, same copy OID, no source sessions, nonempty owner-only database ACL | Closed |
| Cutoff physical evidence not directly bound to control | Lines 135/139 seal source physical state in the fingerprint; lines 182–184 require unchanged control observation plus exact native identity, sequence and next-plan physical objects | Closed |

Lines 143–146 contain only four explicit SQL actions: close the source, create
the closed rehearsal copy, revoke PUBLIC CONNECT/TEMP on that copy and open its
restricted admission. There is no source reopen statement or `docker start`.
Lines 204–207 verify the exact original container remains stopped. The result
separates `copied_database_at_creation`, final `copied_database`,
`final_database_gates`, `copy_acl` and `source_container` under status
`copy_created_source_remains_fenced`.

This final state supersedes the initial short-outage/restart behavior described
above. Keep the pre-gate native cutoff/next receipts and continuous source-freeze
evidence. Separate native commands cannot reconnect after source admission is
closed. The later final provider copy can clone that closed frozen source, then
native verification compares the final copy to the retained cutoff. Do not
reopen the source merely to obtain another capture or call the SOP evidence a
native TapDB fence receipt.

No further must-fix findings remain in this revision. Apply acceptance is
limited to the exact reviewed script/config/mapping/physical fingerprint in O's
new actual read-only plan, with all other original user gates preserved. This
is not a claim that the copy, native target lifecycle or deployment succeeded.

## Actual read-only plan and exact apply signoff

O reports plan RC 0, with `planned_at` equal to
`2026-09-11T06:53:22.708943+00:00`. E read the actual safe plan at the controlling
worktree's
`docs/plans/evidence/20260911_dewey_rc_inventory/rehearsal-copy-sop-plan.json`
and independently recomputed SHA-256
`30524c4f5438712dd60c0af87402ea805835817c1fb4ca2b2f63be20932ac1a5`.
E also rehashed the unchanged script as
`d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`.

| Reviewed plan field | Actual value |
|---|---|
| Source | `dewey_prod`, OID 16749 |
| Control | `postgres`, OID 5 |
| Physical source via control | `10.0.2.148/32:5432`, database/OID exactly as above |
| Target | `dewey_tapdb10_rehearsal_20260911` |
| Original container | `872434f0530335fd5a985a920f498fe39a36fd5eab40b9cb3934b185ceddeb36` |
| Original image | `sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f` |
| Source config SHA-256 | `d22c5ebd3a5fc83032ff5946a57545f49dd8e448b8a4f6c99580d8a926c2a617` |
| Control config SHA-256 | `42491d0bf321d4d8027ef52918a1396e4e4c7f2c7bdecdabd82449b86b87686a` |
| Rehearsal config SHA-256 | `9208dde2d25577ff06679e2bd19a37870ddc1c5d3039edc11dd31f3da8f53520` |
| Planned final state | `source_closed_container_stopped_copy_operator_only` |
| Pre-stop session | One idle `dayhoff` session, PID 27027, client `10.0.0.222/32`; apply requires zero after shutdown |

The plan contains exactly the reviewed seven steps and four SQL statements,
with `apply_performed: false` and `backup_created: false`. O reports output/log
paths unused. The revised script rechecks config/script/physical fingerprints
and paths before stopping production, then enforces the capture and admission
conditions during apply.

**Independent E acceptance:** This unchanged capsule is accepted to apply under
the user's renewed explicit stop/freeze/copy/rehearsal authorization. Scope is
the exact source freeze and one rehearsal copy, not native target migration,
runtime binding, additional backup, message retention or automatic restart.
Actual execution success still requires its new result/events/native receipts.
No additional tests, live reads or mutations were performed by E for signoff.
