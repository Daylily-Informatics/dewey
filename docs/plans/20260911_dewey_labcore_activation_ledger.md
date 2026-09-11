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
rollback; enable only with verified tenant/principal and persisted canary inputs. The user subsequently
authorized explicitly synthetic acceptance data when no Labcore record is available;
never invent Meridian-shaped IDs or substitute nulls for required contract fields.
Rollback disables the feature and retains accepted writes and receipts.

## Ledger

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| J00 | Baseline | Source, deployment, config and ownership inventory | SUCCESS | active_product_contract | Gate 0 | O | Gate 0; source/live inventory |  | Main baseline, clean isolated worktree, zero existing Labcore ownership |
| J01 | Port | Selectively integrate #6–#8 | SUCCESS | feature_implementation | Approved plan | O | PR #15; 87fd7cf3c56e |  | Selective port complete; current GUI/Search v2 retained |
| J02 | Ownership/API | Atomic claims, lineage, auth and limits | SUCCESS | feature_implementation | Approved plan | O | services/labcore_owner.py; docs/labcore_owner_api.md |  | Native atomic ownership and bounded scoped API complete |
| J03 | Verification | Focused tests and PostgreSQL concurrency | SUCCESS | contract_test | Acceptance | O | CI 34616603871; evidence/20260911_dewey_labcore_910/postgres-acceptance.json |  | 573 passed; nine Aurora case groups passed |
| J04 | Release | Main, annotated 9.1.0 tag and final image | SUCCESS | feature_implementation | Approved release | O | Tag 9.1.0; final-image/capsule-inputs.json; package-versions.json |  | One final image built and published |
| J05 | Production | Scoped configuration and controlled registration | SUCCESS | config_or_startup_contract | Verified identity required | O | candidate-acceptance.json; live-acceptance.json; promotion-result.json |  | Enabled with user-authorized synthetic principal; real identities and live checks passed |
| J06 | Closeout | Terminal evidence and caller handoff | SUCCESS | historical_docs_only | Acceptance | O | docs/labcore_owner_api.md; this closeout |  | Evidence retained; Labcore caller and Dependabot remain separate |

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

+- GitHub default branch was `jemdev10`; user requested `main`. Updated with
+  `gh repo edit --default-branch main`; verified returned `main`.
+- Live original container `55bce3940b4c`, image `382bc96a15e7`, unchanged during
+  implementation. Read-only source inventory found zero active Labcore-produced
+  artifacts or Labcore external objects. No legacy Labcore identity adoption needed.
+- Port preserves current TapDB GUI/DAG and Search v2. Removed the obsolete
+  registry introduced by #7; mounted the feature independently in app startup.
+- Labcore is a Go/PostgreSQL owner, not a TapDB object service: its run is a
+  native opaque XRF (`labcore`, `sequencing_run`, global identity), with local
+  typed DGX policy objects and authoritative lineage. Global identity scope is
+  not public access permission; API authorization remains tenant scoped.
+- Focused verification: 30 tests passed, then 5 API tests passed after adding
+  request-boundary/alias/credential-isolation coverage. First collection lacked
+  the required deployment environment; corrected it without a broad rerun.
+- Aurora acceptance: `/home/ubuntu/dewey_ops/labcore-910/postgres-acceptance.json`.
+  Nine case groups passed against `dewey_tapdb10_rehearsal_20260911`, as runtime
+  `dewey_rehearsal_9`, TEMP=false. Distinct PostgreSQL sessions and observed lock
+  waits proved 201/200 replay, 201/409 conflicts, cross-tenant global uniqueness,
+  commit/rollback waiters, independent keys, receipt failure rollback, native XRF
+  plus three receipt lineages, and soft-deletion reservation.
+- Test harness fixes: used the complete existing image's dependencies and corrected
+  the XRF type assertion to native `external_identifier`. Metrics background writes
+  were denied by the rehearsal's read-only mount; ownership checks completed.
+  No intermediate image build and no production data writes.
+- CI concurrency cancels duplicate push/PR runs for the same branch. The final
+  broad suite runs in the PR; a skip-CI merge message will reuse that result.

- First broad CI: 569 passed, 2 skipped, four fixture failures. The new explicit
  default fixture masked config paths intentionally selected by four CLI/settings
  tests. ATTEMPTING_BUGFIX: those tests now explicitly select their own files;
  no runtime behavior changed. Second CI pass is informative and authorized.

- Second CI `34616603871` passed: **573 passed, 2 skipped**, package build,
  Ruff, Bandit and CodeQL. Four targeted fixture regressions passed before push.
  No further broad runs are needed for unchanged application code.
- PR #15 merged normally; annotated tag `9.1.0`, release `main` and origin/main
  identify `87fd7cf3c56e8dc283ed1dedea1232984825137d`. GitHub default and local
  origin/HEAD point to main. The merge reused green PR CI with `[skip ci]`.
- Final image capsule generated from that exact clean main/tag and qualified
  source `2784c70b51cf75c8be6e83af680f7c11e3bf56a0`. Context SHA256
  `70ee78b6f65fea678d323eba4a9f3972ff2111d2db4f54a15e28c94b67a33c70`.
- New private config prepared at `/opt/dewey/day/releases/9.1.0/dewey-config.yaml`
  through the supported `dewey --config ABS config edit` command. Only Labcore
  owner settings change; DB config, broker auth, storage and sibling services do not.
  The dedicated principal `labcore-synthetic-acceptance-910` is bound solely to
  `synthetic-labcore-tenant-910`; its bearer remains in protected host config.
  User explicitly authorized synthetic acceptance in lieu of a real Labcore record.

## Production closeout

All seven rows are SUCCESS; no working or blocked rows remain. The API is
released and enabled. Actual Labcore automation is explicitly outside this phase.

- Published image `sha256:7982b35d67ae54f12103d7bec8cf0e4f84de1eb730b0a1138041de1572b2b0a3`;
  Dewey 9.1.0, TapDB 10.1.1rc1, Meridian 0.4.8, Python 3.12.14.
- Live container `fee0f8d0076eb3af774e61d04ae05a116f98d5b25be957281723c36870afb943`,
  started 2026-09-11T15:37:51.37338201Z, running with zero restarts at closeout.
- HTTPS health/readiness on `dewey.day.lsmc.bio` return 9.1.0 / release SHA;
  database ready. Unauthenticated canonical registration returns 401.
- Synthetic fixture artifact `M-DGX-NP43`, external identity `M-DGX-NP6Z`,
  relation `M-DGX-NP7X`, receipt `M-DGX-NP8V` were genuinely persisted by Dewey/TapDB.
  Labcore tenant/run/test are labelled synthetic, not asserted real Labcore records.
  No S3 objects were created or copied; prefix availability is marked unavailable.
- Candidate: 201 creation, 200 identical replay, 409 mismatched header and
  correctly hashed conflicting command. Live: 200 replay with identical receipt,
  409 conflict, scoped token denied general API access, alternate routes absent,
  three receipt lineages, native external reference and fresh-session TEMP=false.
- Search v2 HTTP measured 0.761s candidate / 0.801s live. Existing GUI/login and
  search implementation retained; recent GUI evidence reused because auth and
  static configuration are value-equivalent aside from the explicit new API section.
- Promotion verified all sibling container identities/start times unchanged.
  Database configuration and original migration recovery database remain untouched.
- Reproducible helper sources and nonsecret receipts are checked in under
  `docs/plans/evidence/20260911_dewey_labcore_910/`. Protected credentials and
  compose/config copies remain only on the host under the existing private paths.
- Rollback: disable `labcore_owner.api_enabled` through `dewey config edit` on
  the explicit 9.1.0 config and recreate only Dewey, or restore the captured
  previous Dewey image/config. Retain accepted objects and receipts in either case.
- Cost controls: one coordinating agent, two broad CI passes (second fixed four
  configuration-fixture failures), focused informative checks, one final image,
  no additional TapDB release or migration campaign. No background monitor created.
