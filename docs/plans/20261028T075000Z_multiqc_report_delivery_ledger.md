# Current continuation state
Updated: 2026-10-28T07:09:52.415585+00:00.
Objective: repair the slow navigation and missing plots experienced in https://dewey.day.lsmc.bio/fetch/M-DGX-1801M, then observe the requested report in Chrome. User explicitly requests browser exploration and improvement. Existing share identity, audience, no-expiry policy and S3 analysis outputs remain authoritative.

Gate0: Dewey active worktree /Users/jmajor/projects/dewey-sharing-docs-20261025 was clean on codex/dewey-share-mail-20261027/e55e2c7; now scoped branch codex/dewey-multiqc-delivery-12.0.15-20261028. Live release12.0.14/818ea7e; exact deployment i-07df3a933e4839f52/us-west-2 from owning release ledger. Canonical /Users/jmajor/projects/dewey has unrelated dirty AGENTS and old3.0.3 branch, preserved. Latest remote numeric patch14,15unused at source preparation. No tests, PR, merge, local container builds, new controls/limits, or extra post-success checks.

Reproduction: native Chrome (browser access host unavailable), original share/isolated preview. Navigated Raw Reads→Coverage and Mosdepth Cumulative coverage plot. Tables eventually populate but plotted area remains blank. Console19errors includes required Plotly/jQuery/pako/multiqc/data/bundle-index scripts rejected429; subsequent Plotly/jQuery/pako undefined. Source share_gateway._reserve rejects over2active per subject/8global. Normal browser parallel asset burst exceeds2. Existing no-store also retransfers all libraries each navigation. No CSS/CSP bypass indicated.

Correction: preserve2/8 limits and normal download admission; queue isolated report asset requests asynchronously on the existing capacity so they do not consume worker threads waiting, restore actor/context across async/threadpool boundary, preserve authorization/audit. Report assets private,no-cache require authorization and conditional revalidation everyrequest, allowing native S3conditional304. Handshake/challenge/application responses remain no-store. No auth/grant/source-data edits. Publish annotated15 on scoped branch and deploy selected Dewey finalimage only on confirmedEC2, no tests/CI/PR/merge. Requested browser observation covers Raw Reads/Coverage/another section, visible plots and repeat navigation; not a broad testcampaign.

Next: implement minimal owning gateway/preview changes; record native build/deploy results; browse same share to confirm requested behavior. Use existing Dayhoff deployment controls. No new runtime cutoffs, duplication of controls or fallback.

# Execution ledger
|ID|Requirement|Status|Evidence|
|---|---|---|---|
|P1|Reproduce report navigation/blank plots|SUCCESS|Chrome rawreads/coverage,429 dependency failures and Plotly undefined|
|P2|Repair report asset delivery under existing limits|SUCCESS|Async report capacity wait, same2/8limits, mandatory conditional revalidation; source reviewed, no tests|
|P3|Publish tagged source and deploy selected Dewey image|IN_PROGRESS|Final EC2 image only; no tests/PR/merge|
|P4|Observe requested report navigation/plots after deployment|OPEN|Scoped user-requested Chrome observation|
