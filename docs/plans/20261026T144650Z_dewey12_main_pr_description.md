Main is behind the application running at **dewey.day.lsmc.bio**. This PR integrates the complete existing release branch through **Dewey 12.0.7**, current operating/API/GUI/CLI documentation, and main-CI repairs. It includes all deployed Dewey code and retains its published release ancestry.

The branch also contains prior registry/TapDB, external-reference, LabCore-owner, annotation, search/graph and deletion-policy work. At the documentation-phase baseline it was 181 commits ahead of main. Four pre-existing 17 MiB synthetic multipart fixtures account for most of the large textual diff; historical evidence is preserved.

## Sharing behavior

- Native schema-3 revisions support creator-authorized delegation, mixed internal/external and pending email recipients, named or registration-open audiences,30-day defaults, explicit indefinite expiry, atomic edits and revocation.
- Stable `/fetch/<share-euid>` URLs and globally claimed permanent slugs deliver authenticated files, complete manifests, resumable recursive CLI retrieval and streaming uncompressed TAR. Current policy governs subsequent requests and archive members.
- WWW links establish isolated content hosts and authorize sidecars. MultiQC client-generated plot downloads work while network form submission remains blocked.
- Finite personal credentials use current verified identity through Login 4.1.1. Explicit SES invitations retain accepted/failed/uncertain receipts. Registration grants share access without automatic organization membership.
- Native audit history, lifecycle/aggregate reports and qualified-equivalence rebind preserve identities, URLs and location history. Rebind does not physically move/delete storage.

## Breaking contract

Managed shares no longer issue raw S3/CloudFront presigns or accept obsolete owner/group/TTL/transport payloads. Consumption requires verified authentication and schema-3 policy; WWW delivery uses isolated hosts. Durable share entrypoints remain supported. Migration preserves inactive identities/history; an 11.x image-only rollback is invalid after schema-3 conversion or new writes.

## Deployed source and PR-only corrections

| Item | Verified deployment |
| --- | --- |
| Immutable annotated tag | [`12.0.7`](https://github.com/Daylily-Informatics/dewey/tree/12.0.7) |
| Source | `3adc81c622d3a8e81fa31b91a2d3ce43690c8202` |
| Image | `sha256:fdf49285e8884894c6f0ee5ce72b6bda61bfd9f6e7ead31990c6e52bc2d64e41` |
| Installed source binding | 113/113 tagged package files/assets match running bytes; no source override mounts |
| Shared libraries | TapDB 11.0.9; Dewey auth 2.1.5; Login auth 2.1.9 retained |

The [running-source receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/running-source-pr-binding-12.0.7.json) binds the complete installed package to the tag. Source/build/config inputs matched it at documentation checkpoint 44ad680. The PR keeps that full ancestry, followed by reviewed format/import normalization and two source corrections **not yet deployed**:

- Explicit empty search scopes are rejected rather than silently selecting default artifact scopes. Omitted/null scopes retain the declared default.
- Readiness sharing-schema status moves to `checks.database.details.sharing_schema`, within the pinned canonical Dayhoff schema. Readiness/status semantics and canonical fixture/provenance bytes remain intact.

The scoped production deployment preserved Login and all 11 other sibling containers. All 42 inactive historical shares were preserved. Dedicated recipient ALB/8443 and trusted-management 8444 ingress are documented in the [ledger](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/20261026T010947Z_dewey_12_sharing_release_ledger.md). Login and Dayhoff changes have their own repositories and published release inputs.

Final read-only inspection confirms that same 12.0.7 container/source/image remains running with zero restarts. The report entry returns the expected login redirect with its exact deep link preserved. [Fresh runtime receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-final-runtime-binding.json).

## Validation

- Main CI uses frozen dependencies and a supported Ubuntu 24.04 browser runner. Ruff/import cleanup has [AST and review evidence](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-quality-cleanup-review.json). No dependency upgrade, production rebuild or tag movement occurred.
- Full run [40359932597](https://github.com/Daylily-Informatics/dewey/actions/runs/40359932597) is green at code/test head `220f02b`: **1,296 Python passes, 5 native PostgreSQL passes, 45 browser-script passes**, Ruff/Bandit and the package build. Two Cognito E2E cases require a separately configured pool and are skipped. The tested merge-candidate tree exactly equals the feature-head tree. [Full CI receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-full-ci-success.json).
- Added 62 direct HTTP denial/retirement cases, 3 canonical readiness-state cases and 99 current-feature failure-path cases. Fresh Python coverage passes **83.63% changed lines/82.43% branches**; browser coverage passes **100%/88.79%**, with zero unmeasured files. Both 80% gates, baseline 11.0.10 and exclusions are unchanged. [Coverage closure receipt](https://github.com/Daylily-Informatics/dewey/blob/codex/dewey-sharing-review-20261025/docs/plans/evidence/20261026_dewey12/pr64-branch-coverage-closure.json).
- Retained deployed-tag measurements remain separate: Python 95.96% lines/89.67% branches, browser 100%/88.79%. Deployed acceptance covers external login, report/sidecars, all 7 selected MultiQC PNGs, HTTP/ranges, curl/wget/recursive CLI, manifests/TAR, lifecycle edits, aliases, rebind and native audit reconciliation.
- Documentation whitespace, local links and exact canonical schema hashes pass. Failure inventories and bounded retries are retained in the ledger/evidence.

## Remaining acceptance

The internal identity is enabled, confirmed and email-verified; registration must not be repeated. Its exact internal first-use return/admission and denied management access remain unverified. Earlier missing denial events were not reconstructed. This PR does not assert complete production acceptance or user acceptance.

Use a **merge commit** to preserve released-tag ancestry. Main integration is separate from deploying another image or moving a release tag.
