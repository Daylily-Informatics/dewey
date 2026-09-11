# Dewey Phase 2 deferred ledger

Phase 1 deployment and its60-minute observation completed successfully at2026-09-11T12:07:45Z.
No Phase 2 implementation or PR disposition has started. This ledger is separate
from Phase 1 completion counts. Planned owner G: gpt-5.6-sol, effort high;
start after Phase 1 acceptance and within the user's feature scope and credit budget.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| P200 | Release display | Show packaged build provenance in the Dewey footer | OPEN | bugfix | Phase 2 | G | Actual9.0.0 GUI shows correct package version but unavailable branch/commit and unreleased tag; public health and OCI release identity are correct | dewey_service/ui_metadata.py attempts Git discovery in the installed package and supplies display defaults when Git metadata is unavailable | Cosmetic; do not mutate immutable9.0.0 or overlay source in production |
| P201 | PR review | Refresh Dewey PRs1–5 against the new exact lock and record superseded or remaining changes | OPEN | review | Phase 1 acceptance | G | Prior PR inventory only; current PR state has not been refreshed in this release turn | Deferred by migration release scope and user's credit constraint | |
| P202 | Minor features | Record and implement subsequently specified minor feature requests | OPEN | feature_implementation | Explicit feature requirements | G | No new minor features specified | Requirements pending | Undeployed Labcore and other branch work remain separately preserved |

All rows terminal: no. Phase 2 objective complete: no.
