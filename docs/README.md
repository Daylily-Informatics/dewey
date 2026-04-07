# Dewey Docs

This directory is the current, code-grounded documentation set for Dewey.

For Cognito integration, the live 2.0 split is `daylily-auth-cognito.browser.session` for browser sessions, `browser.oauth` and `browser.google` for Hosted UI helpers, `runtime.verifier` and `runtime.m2m` for bearer verification, and `daycog` plus `admin.*` for lifecycle changes. Keep service runtime code out of `daylily_auth_cognito.cli`.

## Start Here

- [../README.md](../README.md): GUI-first repo overview, ecology framing, current-state caveats, and glossary
- [architecture.md](architecture.md): domain model, runtime boundaries, ownership split, and request/data flow
- [how-tos.md](how-tos.md): operator and developer workflows using the current CLI, GUI, and APIs
- [apis.md](apis.md): current HTTP contract, auth modes, idempotency rules, and deprecated aliases
- [gui.md](gui.md): screen-by-screen guide with current screenshots and role notes
- [becoming_a_discoverable_service.md](becoming_a_discoverable_service.md): how Dewey fits the Dayhoff-managed service contract

## Best Historical References

Inside this repo:

- [old_docs/bloom_dewey_vs_solo_dewey_gap_report.md](old_docs/bloom_dewey_vs_solo_dewey_gap_report.md)
- [old_docs/dewey_cutover_execution_plan.md](old_docs/dewey_cutover_execution_plan.md)
- [old_docs/branch_triage_2026-04-02.md](old_docs/branch_triage_2026-04-02.md)

In the adjacent Dayhoff repo:

- `../dayhoff/DESIGN_PHILOSOPHY.md`
- `../dayhoff/docs/becoming_a_discoverable_service.md`
- `../dayhoff/docs/old_docs/governance/OBJECT-OWNERSHIP-GOVERNANCE.md`

Use those files for context and history. When they disagree with Dewey's live code or the current docs in this repo, the current code wins.
