Main is behind the application source deployed at `dewey.day.lsmc.bio`. This PR integrates the complete existing release branch through Dewey **12.0.7**, with current operating, API, GUI and CLI documentation.

The branch retains earlier deployed registry/TapDB, external-reference, LabCore-owner, annotation, search/graph and deletion-policy work, followed by the Dewey 12 sharing release. At the documentation-phase baseline it contained 181 commits beyond `main`. Historical evidence includes four pre-existing 17 MiB synthetic multipart fixtures; these account for most of the large textual diff.

## Delivered sharing behavior

- Native schema-3 share revisions support creator-authorized delegation, mixed internal/external and pending email recipients, named or registration-open audiences, 30-day defaults, explicit indefinite expiry, atomic scope/recipient edits and revocation.
- Stable `/fetch/<share-euid>` URLs and globally claimed, permanently owned slugs provide authenticated files, complete manifests, recursive resumable CLI retrieval and uncompressed streaming TAR. Current policy governs subsequent requests and archive members.
- WWW links establish isolated content hosts and authorize report sidecars. MultiQC form-driven plot exports work with generated downloads while network form submissions remain blocked.
- Finite personal credentials use current verified identity through Login 4.1.1. Explicit SES invitations have accepted, failed and uncertain receipts. New recipients gain share access without automatic organization membership.
- Native audit history, lifecycle inventory, aggregate reports and qualified-equivalence storage rebind preserve durable identities, links and location history. Physical S3 movement/deletion is separate from rebind.

## Breaking contract

Managed shares no longer issue raw S3/CloudFront presigns or accept obsolete owner/group/TTL/transport payloads. They require verified authenticated consumption, explicit schema-3 lifecycle revisions and isolated WWW delivery. Existing durable share links remain authenticated entrypoints. Migration preserves identities and inactive history; an 11.x image-only rollback is invalid after schema-3 conversion or new writes.

## Running source and deployment evidence

| Item | Recorded value |
|---|---|
| Release tag | [`12.0.7`](https://github.com/Daylily-Informatics/dewey/tree/12.0.7), immutable annotated tag |
| Deployed source | `3adc81c622d3a8e81fa31b91a2d3ce43690c8202` |
| Deployed image | `sha256:fdf49285e8884894c6f0ee5ce72b6bda61bfd9f6e7ead31990c6e52bc2d64e41` |
| Complete installed application binding | 113/113 tagged package files/assets match running bytes; no source override mounts |
| Shared libraries | TapDB 11.0.9; Dewey auth 2.1.5; Login auth 2.1.9 retained |

The [running-source receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/running-source-pr-binding-12.0.7.json) binds the complete installed application package to the tag. At documentation checkpoint `44ad680`, runtime code, configuration sources, Dockerfile, dependency locks and operator scripts also matched that release. The PR retains that full release ancestry. The subsequent CI-only normalization below is additional to the deployed source; it does not move the tag or deploy another image.

The scoped EC2 deployment preserved Login and all 11 other sibling containers. The 42 inactive historical shares were preserved without retirement/deletion. Dedicated recipient ALB/8443 and trusted-source management/8444 ingress are recorded in the [release ledger](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/20261026T010947Z_dewey_12_sharing_release_ledger.md). Login and Dayhoff changes belong to their own repositories and published release inputs.

## Validation

- Expanded release selection: 771 passing cases at 12.0.5; audit correction: 81 affected cases; export correction: 17 Python and 45 browser-script cases. These selections overlap.
- Retained 12.0.7 changed executable line/branch gates: Dewey Python **95.96%/89.67%**, browser JavaScript **100%/88.79%**. Login and scoped Dayhoff tooling also exceed their independent 80% gates.
- Original isolated PostgreSQL claims/revisions/lineage/migration group retained. No production database was used for contract tests.
- Controlled deployed evidence covers external login, report/sidecar rendering, all seven selected MultiQC PNG downloads, HTTP/ranges/conditions, curl/wget/recursive CLI, manifests/TAR, recipient/target edits, aliases, revocation, rebind and native audit reconciliation.
- Documentation synchronization passed whitespace and local file-link review. Main-target CI is tracked on this PR separately from those retained release receipts.

## Main CI integration cleanup

The first main-target run failed Ruff with 308 style/import diagnostics; Bandit passed, and dependent test jobs were skipped. The formatter changed 89 files while strict AST hashes remained identical across all 194 Python files. Import ordering and narrow unused-name cleanup preserve intentional public exports and imported pytest fixtures. Two assigned canonicalization lambdas became same-scope return-only functions, and an unused test assignment retains its original call.

Local `ruff check` and `ruff format --check` now pass. After the documented import/helper normalizations, all 194 files retain equivalent non-import ASTs. Import initialization remains subject to full PR CI. The retained production-tag coverage percentages above are separate from the normalized PR head's forthcoming CI measurements. See [cleanup review](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-quality-cleanup-review.json).

Run [40346672128](https://github.com/Daylily-Informatics/dewey/actions/runs/40346672128) passed Ruff, Bandit and isolated PostgreSQL contracts. Tests stopped during browser installation, before pytest: `ubuntu-latest` supplied Ubuntu 26.04, which locked Playwright 1.60.0 rejects. The browser test job is now pinned to supported Ubuntu 24.04, with dependency locks unchanged; fresh full-test, coverage and package-build results remain pending. The [versioned Playwright dependency table](https://github.com/microsoft/playwright/blob/v1.60.0/packages/playwright-core/src/server/registry/nativeDeps.ts) includes Ubuntu 24.04.

Run [40347942901](https://github.com/Daylily-Informatics/dewey/actions/runs/40347942901) confirms that runner correction: Ruff, Bandit, native PostgreSQL and browser installation pass. The full unit suite then reports **948 passed, 89 failed, 93 setup errors and 2 skipped**. That historical failure inventory is retained in the [integration receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-full-suite-integration.json); coverage gates, browser-script tests and the package build were not reached.

Repairs now have passing evidence for **383 distinct affected cases**, using original affected runs and failure-only retries rather than another local full-suite campaign. They include 62 new direct HTTP denial/retirement checks and three canonical readiness-state cases. Explicit app/native/backend/identity fixtures, current API expectations and context cleanup retain authorization and deletion denials. All 35 changed Python files pass Ruff check/format and the canonical observability fixture hashes are unchanged. Fresh full CI, 80% changed-line/branch gates and the package build remain pending. See [focused repair validation](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-focused-repair-validation.json).

Two source corrections are additional to the deployed release. `search_registry` preserves an explicit empty `scopes` list for existing rejection, rather than silently broadening it to default artifact scopes; omitted/null scopes retain their declared default. `/readyz` places sharing-schema status in `checks.database.details.sharing_schema`, inside the pinned Dayhoff schema, rather than adding an unsupported top-level property. Ready/status behavior is preserved, and the canonical fixture/provenance bytes remain intact. Both corrections are PR-only and require fresh CI coverage; neither is deployed or represented as part of tag 12.0.7.

## Remaining acceptance boundary

The internal acceptance identity is enabled, confirmed and email-verified; registration must not be repeated. Its exact first-use return, internal share admission and denied management access remain unverified. Earlier missing denial events before 12.0.6 were not reconstructed. These limits remain explicit in the ledger; this PR does not manufacture that missing live acceptance or assert full release-objective completion.

Use a merge commit to retain the published release ancestry. Main integration is separate from deploying another image or moving any release tag.
