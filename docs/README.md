# Dewey Docs

This directory contains the maintained Dewey 12.0.8 guides and explicitly dated
historical references. Deployment, software validation and live/user acceptance
are separate states in the release ledger.

For authentication, the 2.x split is `daylily-auth-cognito.browser.session` for
browser sessions, `browser.oauth` and `browser.google` for Hosted UI helpers,
`runtime.verifier` and `runtime.m2m` for bearer verification, and `daycog` plus
`admin.*` for Cognito lifecycle. The day deployment uses shared Login as its
external broker. Keep service runtime code out of `daylily_auth_cognito.cli`.

## Start Here

- [../README.md](../README.md): GUI-first repo overview, ecology framing, current-state caveats, and glossary
- [architecture.md](architecture.md): domain model, runtime boundaries, ownership split, and request/data flow
- [how-tos.md](how-tos.md): operator and developer workflows using the current CLI, GUI, and APIs
- [apis.md](apis.md): current HTTP contract, recipient/management boundaries, revision fields and removed delivery modes
- [gui.md](gui.md): current Library, Sharing, recipient, report-export and account controls
- [sharing.md](sharing.md): authenticated internal/external sharing, EUID/slug URLs, recursive delivery, isolated reports, lifecycle audit and rebind
- [dev-docs/20261026_sharing_test_coverage.md](dev-docs/20261026_sharing_test_coverage.md): changed-code line/branch coverage contract and recorded results
- [plans/20261026T010947Z_dewey_12_sharing_release_ledger.md](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md): deployed provenance and exact remaining acceptance; internal signup is confirmed, while internal scoped-access proof and user acceptance remain open
- [becoming_a_discoverable_service.md](becoming_a_discoverable_service.md): how Dewey fits the Dayhoff-managed service contract

## Best Historical References

Inside this repo:

- [derived_features_and_capabilities.md](derived_features_and_capabilities.md): September 1 capability/evidence snapshot; not the current sharing contract
- [plans/20260911T035319Z_dewey_source_reconciliation.md](plans/20260911T035319Z_dewey_source_reconciliation.md): retained Dewey 9 source boundary and Git ancestry
- [qeo/QEO_DEWEY_RECON.md](qeo/QEO_DEWEY_RECON.md): May QEO/KEO reconnaissance; its older sharing observations remain historical
- [old_docs/bloom_dewey_vs_solo_dewey_gap_report.md](old_docs/bloom_dewey_vs_solo_dewey_gap_report.md)
- [old_docs/dewey_cutover_execution_plan.md](old_docs/dewey_cutover_execution_plan.md)
- [old_docs/branch_triage_2026-04-02.md](old_docs/branch_triage_2026-04-02.md)

In the adjacent Dayhoff repo:

- `../dayhoff/DESIGN_PHILOSOPHY.md`
- `../dayhoff/docs/becoming_a_discoverable_service.md`
- `../dayhoff/docs/old_docs/governance/OBJECT-OWNERSHIP-GOVERNANCE.md`

Use those files for context and history. When they disagree with Dewey's live code or the current docs in this repo, the current code wins.
