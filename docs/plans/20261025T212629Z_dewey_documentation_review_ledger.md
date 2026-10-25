# Dewey capabilities and sharing documentation review

## Current continuation state

Updated: 2026-10-25; documentation-only task.

- Objective: inspect the complete deployed Dewey surface and matching source; write capabilities, sharing requirements, and gap analysis under `docs/dev-docs/`; add README sharing guidance; commit and push for review.
- Stop condition: all requested documents and README changes are pushed with inspectable evidence. No feature implementation or multi-agent implementation plan is authorized by this task.
- Working identity: `/Users/jmajor/projects/dewey-sharing-docs-20261025`, branch `codex/dewey-sharing-review-20261025`, based on annotated tag `11.0.10`, commit `7f6fde5429741780517cf461a615e5b3e5f102f2`, remote `git@github.com:Daylily-Informatics/dewey.git`.
- Authority: user's 2026-10-25 request explicitly authorizes investigation, README/document writing, commit, and push. Review precedes any later multi-agent ledgered implementation plan. No shares, users, invitations, tokens, storage objects, network rules, release tags, deployments, tests, CI campaigns, or scheduled work are being created/changed.
- Completed: live health/readiness and OpenAPI inspected; 105 paths / 114 operations captured; release tag matches live build; two deployed GUI JavaScript assets match the tag byte-for-byte. Static source route inventory contains 176 decorators (not 176 live routes).
- Limits: browser tool returned “The browser access host is unavailable”; no preconfigured Dewey user token was available in the shell. Authenticated UI, real recipient delivery, Login provisioning, and global-network reachability are not functionally verified. Read-only HTTP inspection is available.
- Next: finish and publish the capabilities baseline, then requirements, then gap analysis and README cross-links. Use `[skip ci]` on documentation commits because tests are off by explicit policy.
- Evidence: `docs/dev-docs/evidence/20261025_dewey_sharing_review/` contains sanitized live observations and source/API inventory; documents cite immutable release source.

## Gate 0 inventory and scope

- Existing `/Users/jmajor/projects/dewey` was on old release branch `codex/release-dewey-3.0.3`, commit `520bf71`, with unrelated modified `AGENTS.md`; preserved unchanged.
- The previously recorded `mega_dayhoff` checkout no longer exists. The recent `dewey-graph-legacy-boundaries-20261015/dewey` worktree has an invalid Git common-directory pointer to that absent checkout; preserved unchanged.
- A new isolated documentation worktree was required because neither was suitable for current-release edits. Initial worktree status was clean.
- Remote `main` observed at `818bf15c7cfd65a351acf6816293057ee2ba8bf6`; documentation is deliberately based on deployed source, not an unverified main checkout. Remote annotated tag object `a38416b0d4837937852fda95dbed467be7d9cbf0` peels to the live SHA above.
- Inventory: bounded unauthenticated GETs, live OpenAPI extraction, static AST decorator inventory, and focused reads of registration, sharing, gateway, report, identity, storage, deletion, CLI and UI source. No application imports, environment installation, tests, or live mutations.
- Validation authorized for documentation: source/claim review, link/file checks, `git diff --check`, and remote commit verification. Application functional acceptance remains outside this documentation task.

## Documentation delivery ledger

This ledger tracks document delivery only. It is not the later feature implementation plan.

| ID | Requirement | Status | Category | Gate | Owner | Evidence | Terminal note |
|---|---|---|---|---|---|---|---|
| DOC-01 | Current capability baseline and source/live inventory | IN_PROGRESS | historical_docs_only | Documentation | Primary agent | Live evidence directory | Pending publication |
| DOC-02 | Sharing requirements and consequential design decisions | OPEN | historical_docs_only | Documentation | Primary agent | User request; DOC-01 | Pending |
| DOC-03 | Traceable gap analysis | OPEN | historical_docs_only | Documentation | Primary agent | DOC-01 and DOC-02 | Pending |
| DOC-04 | Accurate README sharing section and pushed documentation | OPEN | historical_docs_only | Documentation | Primary agent | README; Git receipts | Pending |
