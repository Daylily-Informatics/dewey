# Dewey 9.1.0 Labcore activation

Approved 2026-09-11. Selectively port PRs #6, #7 and #8 onto main; preserve
Search v2 and exact TapDB 10.1.1rc1. Release and enable the canonical
`POST /api/v2/sequencer-runs/register` API. Automatic Labcore calling and
Dependabot PRs #1–#5 are separate. No Labcore deployment or database replacement.

Use native global identity claims in one transaction with typed external
references, lineage, receipts and idempotency. Preserve canonical v1/v2 hashes;
retain reserved namespace controls; attribute principal IDs; enforce tenant,
scope and credential separation. Limits: 16 MiB body, 50,000 files, 1,024 UTF-8
bytes per relative path. Default disabled; incomplete enabled config fails.
Template preparation stays offline. No advisory fallback or compatibility aliases.

One focused verification pass, one broad CI run (repeat only after informative
fixes), one final image. Verify real separate-session PostgreSQL concurrency and
rollback; enable only with verified tenant/principal and persisted canary inputs.
Rollback disables the feature and retains accepted writes and receipts.

## Ledger

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| J00 | Baseline | Source, deployment, config and ownership inventory | OPEN | active_product_contract | Gate 0 | O | | | |
| J01 | Port | Selectively integrate #6–#8 | OPEN | feature_implementation | Approved plan | O | | | |
| J02 | Ownership/API | Atomic claims, lineage, auth and limits | OPEN | feature_implementation | Approved plan | O | | | |
| J03 | Verification | Focused tests and PostgreSQL concurrency | OPEN | contract_test | Acceptance | O | | | |
| J04 | Release | Main, annotated 9.1.0 tag and final image | OPEN | feature_implementation | Approved release | O | | | |
| J05 | Production | Scoped configuration and controlled registration | OPEN | config_or_startup_contract | Verified identity required | O | | | |
| J06 | Closeout | Terminal evidence and caller handoff | OPEN | historical_docs_only | Acceptance | O | | | |

## Gate 0

- Worktree: `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-labcore-910`.
- Branch: `codex/dewey-labcore-910`; clean origin/main baseline
  `200e67c2c949ab9a0b968e77e3acbb4c38554025` (9.0.1), refreshed by git fetch.
- Prior search worktree remains unchanged. No unrelated files in new worktree.
- Expected production image: `sha256:382bc96a15e70b06d2e4c865b4922f27ce67229a4f3e8522b6246e3c9a706234`;
  refresh live before mutation. Database `dewey_prod_tapdb10`, domain M.
- Planning inventory found no Labcore principal in Dewey and no Dewey credentials
  in Labcore ECS task definition 338. Verify tenant/canary before activation.
- Prior broad checks: 544 passed, 2 skipped for 9.0.1; reuse unchanged GUI/search
  evidence and run only informative new tests before one final CI pass.

## Execution evidence

Implementation started; production unchanged.
