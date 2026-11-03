# Dewey report share viewing debug

## Current continuation state
Updated: 2026-11-03T09:09:00Z. Objective now includes Dewey-only production deployment of the durable UI fix. New user authority: "deploy the durable fix to the global bug please"; deployment-only restriction below is superseded for this fix. Separate exact test-scope question received user "second approval"; only four report-view behavior groups (five parameterized cases) are authorized. No broad tests, lint, coverage, CI campaign, artifact upload, live share target/permission edits, credential/security/network changes, or Ultima work.

The first focused run failed all five before assertions because the existing synthetic DOM lacks appendChild used by notification rendering. Added the standard method to the fixture; the same-scope rerun passed5/5 (74.49175ms). No other tests/lint/coverage ran. No production change yet. Current live manifest explicitly identifies Dewey12.0.18/image1a10f323d96e9b7c5d19cd6bc523ed2844bbe93a0e2a83600fcacb70ff440156. Published12.0.19 has an identical source tree to this branch HEAD; no merge is needed. New immutable release planned12.0.20. Interactive SSM session as ubuntu is open to designatedi-07df3a933e4839f52/us-west-2. Supported release route: native selected-service registry-cache builder, then existing targeted Compose update, preserving current unselected service entries and existing runtime/DB configuration.

Next: complete focused rerun, commit intended source/docs/fixture/release helper on current branch, annotate/push12.0.20, build final image once onEC2, deploy onlyDewey, one post-deployment behavior check and R60 opening.

Historical debug-only scope and unexecuted-test statements below describe the earlier checkpoint and are superseded by this explicit deployment/test amendment.

Source: /Users/jmajor/projects/dewey-sharing-docs-20261025, codex/dewey-token-governance-20261029, f0487369d4efd45ded6caef80de8cb43c98fd013; deployed browser footer Dewey12.0.18. This worktree was clean before edits. Default /Users/jmajor/projects/dewey is older520bf71 and has unrelated dirty AGENTS.md; it is untouched.

Findings: M-DGX-1GR61 is active WWW, policy revision1, targetM-DGX-1GR37 (single DAY_final_multiqc.html object), saved entrypointDAY_final_multiqc.html, bundle root empty, exactlsmc.com domain grant. Its saved configuration is present. sharing.js used an unconditional HTML preview action that prompted for another bundle root and independently created a preview. fetch.py already opens the stored entrypoint with report_preview.report_entry_page and the persisted bundle root. The local fix routes the matching configured entrypoint to that durable fetch URL and removes the duplicate interactive preview path; other HTML stays download-only. Preview isolation and authorization remain in the canonical viewer unchanged.

The148128-byte downloaded DAY_final_multiqc.html has title Final LSMC MultiQC Report: MultiQC Report and links presentation.js, CSS, jquery, pako, data JS and bundle-index.js under DAY_final_multiqc_files/. The share browser exposes only one authorized object. report_preview.py explicitly returns403 Object-only report has no authorized bundle assets for its sidecars. Repairing the live report publication requires selecting/uploading the complete bundle and reviewing the exact share target; this task does not authorize that live change. No assets or permissions were synthesized.

Latest matrix: live Sharing search Product Capabilities sorted Newest first returned23 entries in one page; R60 M-DGX-1CBMT is first, followed byR59 M-DGX-1C327. Native publication receipt product-definitions/matrix/v2/evidence/R60_www_share.json records created2026-10-30T04:40:32.698611Z, target prefixM-DGX-17Z97 (s3://lsmc-dewey-0/artifacts/lsmc-matrix/v2/R38/), entrypointR60/Matrix_V2_Interactive_R60.html, bundle root empty. URL https://dewey.day.lsmc.bio/fetch/M-DGX-1CBMT. Normal Chrome navigation visibly rendered HG002 matrix, PublicationR60, 74/74configuration rows, ROI heatmaps, coverage columns and PDF/TSV controls. Screenshot /Users/jmajor/Documents/Codex/2026-11-03/task-2/matrix-r60-rendered.png. Initial claimed automated tabs remained blank; CDP reported paused document response. Normal Chrome rendering establishes the matrix works; those intermediate blanks are not evidence of service failure.

## Control ledger
Gate0: read repo/global policies, README/docs/sharing.md and supported dewey/shares CLI help; activate day environment. No configured shell DEWEY_API_TOKEN_FILE; no credential created and no raw API/DB fallback attempted. Existing signed-in Chrome LSMC session used. dayhoff-services skill absent from exposed catalogs and searched local skill directories. No deployment operations require it here.

|ID|Requirement|Status|Evidence / limitation|
|---|---|---|---|
|DBG1|Identify saved share configuration and UI root cause|SUCCESS|Signed-in share editor inspected without saving; sharing.js browse/handle; fetch.py WWW route; report_preview.py persisted root|
|DBG2|Local prompt-free link correction|SUCCESS|sharing.js uses the configured WWW entrypoint, encoded target namespace and canonical fetch route; existing manager-preview tests replaced with focused link behavior cases; tests not run under user policy|
|DBG3|Identify/open latest published product matrix|SUCCESS|Live23-result newest-first list, R60 publication receipt and visible74-row report; screenshot above|
|DBG4|Make existing MultiQC publication fully render with its sidecars|BLOCKED|Single-object share cannot authorize linked DAY_final_multiqc_files assets. Requires separately approved complete-bundle publication/target change; no live alteration performed|
|DBG5|Deploy local UI correction|BLOCKED|Explicit task excludes deployment; separate applicable approval required|

All rows terminal: yes. Debug/local-source objective complete; live MultiQC repair not complete. No test, lint, coverage or build commands run. Regression cases added but unexecuted. No push, PR, merge, deployment, service restart, live share change or security/network work performed.

## Final artifact evidence

The actual Download link on M-DGX-1GR61 saved `/Users/jmajor/Downloads/DAY_final_multiqc (1).html`; inspection confirmed148128bytes, the same six linked script/style dependencies and the MultiQC title. Live `/records/M-DGX-1GR37` explicitly shows OBJECT and this exact location: `s3://lsmc-ssf-sequencing-data/derived/ultima-solo/20261015/pclu-2100/ultima-solo-602218-20261015t144000z/daylily-omics-analysis/results/day/hg38_broad/reports/DAY_final_multiqc.html`. Thus the file content and single-object target are independently grounded in this share rather than inferred from a similarly named local file. Structured evidence: `/Users/jmajor/Documents/Codex/2026-11-03/task-2/dewey-report-share-evidence.json`. Deliverable patch: `/Users/jmajor/Documents/Codex/2026-11-03/task-2/dewey-report-share-local-fix.patch`. Local diff inspected; no tests run.

## Deployment amendment

|ID|Requirement|Status|Evidence / limitation|
|---|---|---|---|
|REL1|Four approved focused behavior groups|SUCCESS|First run:5failed at missing fixture appendChild before feature assertions; fixture repaired; same focused rerun5passed/0failed|
|REL2|Immutable12.0.20 publication and EC2 final image|IN_PROGRESS|User-authorized Dewey-only deployment; exact published tags inspected; no existing tag overwritten|
|REL3|Selected Dewey Compose update and browser acceptance|IN_PROGRESS|Supported helper/docs identified; live mutations not yet performed|

Approved focused command: `source ./activate day`, then `node --test --test-name-pattern='configured WWW report|single object WWW report|multi-target WWW reports|HTML without a matching configured WWW entrypoint' tests/ui/sharing_v12.test.cjs`. Result5passed/0failed; no broad suite. Native current Compose reports runningDewey12.0.18 at source14f63f2d982ac4b479de2a81a88f225283357c7c.
