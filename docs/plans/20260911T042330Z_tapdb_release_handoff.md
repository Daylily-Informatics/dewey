# TapDB release handoff for the paused Dewey migration

Recorded 2026-09-11T04:23:30Z. The user paused Dewey work and assigned TapDB
changes/publication to a separate agent. No upstream changes or release will be
made by this paused task. The proposed next patch version is 10.1.1, subject to
verifying the next unused tag. Dewey is not yet repinned.

Use `gpt-6-astra` with `max` effort for the TapDB change and a separate reviewer
for preservation/recovery acceptance. Keep the scope below bounded.

## Required to unblock Dewey

### T01: Complete inventory at actual Dewey scale

Actual published 10.1.0 fails on the existing Dewey database with
`Identity receipt exceeds the declared size bound`. Its fixed cumulative
identity-evidence ceiling is 134,217,728 bytes (128 MiB). This is evidence size,
not a measured database size. The failure occurs before the source contract or
sequence inventory is written. Full backup, schema migration and restored-data
verification reuse the same capture implementation.

Provide a documented public way to set validated inventory limits, propagated
consistently through standalone inventory, historical source contracts, backup
plan/create/verify/restore, migration preflight/apply/post-verification, and
identity comparison. Inventory, emitted evidence and later readers/verifiers
must agree on the selected limits. Retain bounded resource use and complete
table/row evidence; use streaming or chunked evidence if needed for the supported
capacity. Existing UID/EUIDs, domain/prefix bindings, deleted records, lineage,
audit and integration state must remain covered.

Review all three current ceilings together:

| Current 10.1.0 limit | Value | Evidence |
|---|---:|---|
| Cumulative identity row evidence | 128 MiB | Actual Dewey failure |
| Total captured rows | 250,000 | Source-defined; not the observed failure |
| Individual serialized source row | 8 MiB | Source-defined; not the observed failure |

Add structured failure diagnostics: operation phase, table, processed row count,
attempted/accumulated byte count, limit name and configured value. Keep row
contents, credentials and other sensitive values out of diagnostics. An
incomplete capture must never publish a usable successful source/family receipt.

Acceptance should include a complete capture over the old 128 MiB threshold,
selected-limit refusal, affected backup/migration/recovery paths, and one actual
Dewey read-only inventory with the newly published package. Existing successful
test evidence should be reused where unchanged; rerun affected paths and new
capacity tests, not recent tests without an expected informative result.

### T02: Native read-only principal, access and writer census

Expose a supported read-only CLI census that works against historical 9.0.9
without schema initialization or principal bootstrap/bind. The current
service-readiness contract requires original principal-state evidence, but
10.1.0 has no complete public census command. Its internal fence helpers and
new-schema bind plan are not an equivalent historical inspection interface.

Capture the exact authenticated operator and physical database identity;
relevant role attributes and memberships; database/schema/object ownership and
ACLs; effective CONNECT/CREATE/TEMP privileges; existing domain/owner/tenant
scope bindings where supported; IAM-to-database-role membership; and relevant
active connections. Preserve enough original ACL evidence for recovery. Report
unavailable historical binding structures explicitly. Omit SQL query text,
secrets and application row contents.

Also provide an authoritative read-only check of explicitly named destination
and control databases, including existence and physical identity. Connection or
authorization failure must remain an error, not an absence claim. Production's
fixed destination is `dewey_prod_tapdb10`; no existing destination may be
overwritten. No control database has been selected or created by this task.

Use a read-only transaction, exact target guards and bounded timeouts. The
census must not create roles/schemas, change grants, bind scope, allocate
identities, fence writers or terminate sessions. Current activity is only part
of writer evidence; Dewey still owns its HTTP/worker/scheduler/client inventory.

## Small additional fix already identified

### T03: Consistent JSON output from schema drift-check

In the released package/pinned CLI framework, root `--json` suppresses the
`print_text` output used by `db schema drift-check`. The present documented
invocation requires the command-local flag:

```text
tapdb --config ABS db schema drift-check --json --strict
```

Make the command use the canonical structured-output emitter so the global
JSON contract returns a parseable payload. Test the affected CLI output/exit
behavior locally; this issue does not require another live database scan.

## Existing behavior to retain; no extra feature work requested

- Strict sequence advancement and recovery floors, including conservative
  preservation after failed/ambiguous operations. The first resumed allocation
  must remain greater than the source's previously available next value and
  every other applicable frozen floor.
- Historical DGX template/prefix bindings, domain M and existing identities.
- Separate control-database fencing, immutable recovery-family journals,
  receipt-bound planning/application and explicit restoration purposes.
- CONNECT-only principal bootstrap, explicit post-restore binding, reviewed
  database TEMP revocation and fresh runtime sessions after binding.
- Existing published interfaces or any explicitly documented replacements;
  no service-side compatibility code is requested.

The missing `root.admin` section in Dewey's old v4 operator-config copy was
already handled by the supported **native `db-config init`** path, generating
a separate complete operator config. That does not require automatic legacy
configuration repair or backward-compatibility behavior. Clearer validation
guidance is optional, not a new blocker.

## Production and release boundary

Current service: Dewey 8.0.2 / TapDB 9.0.9 / Meridian 0.4.7 at
`https://dewey.day.lsmc.bio`, EC2 `i-07df3a933e4839f52`, Aurora
`dayhoff-lsmcok1-tapdb`, `us-west-2`, PostgreSQL 16.13. Database `dewey_prod`,
schema `tapdb_dewey_lsmcok1_local`, domain M. No source data, sequence values,
grants, runtime configuration or running image changed in this task.

The protected operator installation and native config remain on EC2 under
`/home/ubuntu/dewey_ops/tapdb101-20260911/`. The source operator config is
`source-operator.yaml`; it is inventory-only and must not be used to bind a
runtime principal. All EC2 access is interactive SSM as ubuntu, with targeted
sudo. No live operation is requested by this handoff document itself.

Publish a new immutable non-v annotated tag through the repository's release
workflow. Return exact version, source commit, annotated tag object, wheel and
sdist SHA-256, PyPI installation proof, package/Python/Meridian requirements,
changed CLI/config contracts, and accurate test/review dispositions. Preserve
10.1.0 unchanged. No automatic movement to a later release is authorized.

The Dewey task will resume only on user instruction, verify the released
artifact, record an explicit target amendment, update its exact lock and
integration as required, and repeat the previously failed source inventory.
Production restoration, migration, runtime binding and Dewey 9 release/cutover
remain separate uncompleted gates. Phase 2 remains deferred.

## Evidence available to the receiving agent

- [Actual-source failure, command and baseline](20260911T041429Z_dewey_native_inventory_blocker.md).
- [Native failure JSON](evidence/20260911_dewey_native_inventory/source-inventory-error.json).
- [Recent 301-test published-package qualification and receipts](20260911T035703Z_tapdb101_dewey_qualification.md).
- Independent diagnosis: `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/tapdb101-dewey-qualification-20260911/docs/plans/20260911T041728Z_dewey_source_identity_bound_blocker.md`, committed as `740e30e6912834c61b71670909e5b8d2f915bafd`.
- Migration preparation: `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-data-migration-20260911/docs/plans/20260911T040703Z_dewey_tapdb10_migration_preparation.md`, committed as `7ff8bc7e6d7d667238d21acb3a69e6afbfde0ce1`; its initial “B is determining” wording is superseded by the confirmed blocker above.
