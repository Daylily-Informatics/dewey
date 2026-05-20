# AWS Dewey Artifact Refs And Revokable Shares Ledger

## Summary

Implement the AWS `lsmcok1` Dewey artifact-detail page layout repair, artifact-page external reference creation, Dewey-gated revokable share references with float-day lifetimes up to 365.0 days, and a shared-data report view. CloudFront is explicitly out of scope.

## Status Protocol

Working: `OPEN`, `IN_PROGRESS`, `ATTEMPTING_BUGFIX`.
Terminal: `SUCCESS`, `DUPLICATE`, `NO_LONGER_NEEDED`, `FAIL`, `BLOCKED`.
`FAIL` requires a prior `ATTEMPTING_BUGFIX` state with bugfix evidence and root cause.

## Gate 0 Inventory

- Repo path: `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey`.
- Runtime config: `/home/ubuntu/.config/dewey-lsmcok1/dewey-config-lsmcok1.yaml`.
- Public URL: `https://dewey.dev.lsmc.life` via ngrok to `https://localhost:8914`.
- Runtime process observed before edits: `/home/ubuntu/miniconda3/envs/DEWEY-lsmcok1/bin/python -m uvicorn dewey_service.app:create_app --factory --host 0.0.0.0 --port 8914 ...`.
- Repo state before edits: detached `HEAD`, commit `5e8f566a6b77a916dcab28f166cb6c90de586350`, tag describe `3.0.12`.
- Activation contract: `source ./activate lsmcok1`; `python` resolves to `/home/ubuntu/miniconda3/envs/DEWEY-lsmcok1/bin/python`; `dewey` resolves to `/home/ubuntu/miniconda3/envs/DEWEY-lsmcok1/bin/dewey`.
- CloudFront inventory: current Dewey source contains no `cloudfront` or `CloudFront` implementation hits; current share transports are `presigned_s3`, `rclone_http`, and `rclone_sftp`.
- Current artifact detail layout evidence: `dewey_service/templates/artifact_detail.html` uses inline two-column `content-grid` and `kv-table`; `dewey_service/static/console.css` has generic table wrapping but no artifact-detail long-value containment class.
- Current share evidence: `dewey_service/services/sharing.py` creates immediate S3 presigned URLs in `create_share_reference`; `dewey_service/app.py` artifact detail download route reads `share_ttl_hours` as an integer.
- Current external-object evidence: API routes and service methods exist for external objects and relations, but artifact detail UI only lists relations and has no validate/create form.
- Live limits: no CloudFront work, no bucket policy changes, no destructive AWS changes, no restart of non-Dewey services.

## Tracking Table

| ID | Repo | Requirement | Status | Category | Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| LEDGER-001 | Dewey | Create ledger, record AWS checkout state, live config, tmux/process state, route inventory, and no-CloudFront scope | SUCCESS | plan_amendment | Gate 0 | Agent 1 | This ledger Gate 0 inventory. |  | Ledger created before runtime code edits. |
| UI-001 | Dewey | Fix artifact EUID page overflow for Source URI, Key, Storage URI, hierarchy, metadata, share references, and external relations | SUCCESS | feature_implementation | Gate 1 | Agent 2 | `dewey_service/static/console.css`; `dewey_service/templates/artifact_detail.html`; focused Dewey tests passed. |  | Artifact detail cards now use contained grid cells and long-value wrapping. |
| UI-002 | Dewey | Add at least 8px more spacing between property labels and values throughout the artifact detail page | SUCCESS | feature_implementation | Gate 1 | Agent 2 | `.artifact-detail-grid .kv-table th` and `td` spacing in `dewey_service/static/console.css`; focused Dewey tests passed. |  | Key/value labels and values have additional spacing and wrap. |
| REF-001 | Dewey | Add artifact-page external reference form: enter EUID, validate against explicit configured peer service endpoints, show hit/error | SUCCESS | feature_implementation | Gate 2 | Agent 3 | `dewey_service/app.py` validate route; `artifact_detail.html` form; live config `external_reference_targets`; `tests/test_artifacts_ui.py`. |  | Validation scans only configured peer targets. |
| REF-002 | Dewey | Create external relation only after exactly one peer hit validates; no service discovery or guessed endpoints | SUCCESS | feature_implementation | Gate 2 | Agent 3 | `dewey_service/app.py` create route requires submitted validation token fields; `tests/test_artifacts_ui.py` covers success and missing target error. |  | Zero/multiple/missing target cases fail clearly; one hit can create relation. |
| SHARE-001 | Dewey | Replace TTL-hours artifact share UI with days float input, >0 and <=365.0 | SUCCESS | feature_implementation | Gate 3 | Agent 4 | `artifact_detail.html`; `_artifact_links.html`; `_parse_share_duration_days`; `tests/test_artifacts_ui.py` invalid days cases. | Legacy tests expected old direct S3 URL contract during first focused run. | Bugfix pass updated tests; float days now accepted within range and invalid values fail. |
| SHARE-002 | Dewey | Add Dewey-gated share references that can be revoked and mint short-lived S3 presigned URLs at access time | SUCCESS | feature_implementation | Gate 3 | Agent 4 | `dewey_service/services/sharing.py` `open_share_reference` and `revoke_share_reference`; `/share-references/{id}` route; focused tests 20 passed. | First test pass still expected immediate direct presigned S3 URL. | Share creation returns Dewey route; access route validates active/expiry/revoke before minting short S3 URL and increments access count. |
| SHARE-003 | Dewey | List existing artifact share references on the artifact page with status, recipient if known, created/expires, access count if known, and revoke action | SUCCESS | feature_implementation | Gate 3 | Agent 4 | `artifact_detail.html`; `_share_reference_response`; `tests/conftest.py`; focused tests 20 passed. |  | Artifact page lists share state and revocation action for active Dewey-managed shares. |
| REPORT-001 | Dewey | Add shared-data report view showing shared artifact/data, recipient if known, status, expiry, revoke state, and access count if known | SUCCESS | feature_implementation | Gate 4 | Agent 5 | `/shares` route in `dewey_service/app.py`; `dewey_service/templates/shares.html`; smoke route returns auth-required 401 when unauthenticated. |  | Admin/operator report page is present and protected. |
| DH-001 | Dayhoff | If peer service URLs or share settings are generated by Dayhoff, update only Dewey-related config generation so rebuilds preserve explicit settings | SUCCESS | config_or_startup_contract | Gate 5 | Agent 6 | `/home/ubuntu/projects/dayhoff/app/dayhoff/runtime_core.py`; `tests/test_runtime_core.py`; targeted Dayhoff tests 2 passed. |  | Dayhoff now builds Dewey external-reference targets from explicit Kahlo fleet targets after the Bloom token is available. |
| LIVE-001 | Dewey | Restart only Dewey on AWS via existing tmux/start-script pattern; do not interrupt other services | SUCCESS | contract_test | Gate 6 | Agent 7 | Restarted Dewey only with `start_dewey.sh`; process PID 248915 on port 8914; `/healthz` returned status ok. | SSM wrapper reported nonzero once despite successful health output, so a follow-up smoke verified runtime state. | No Atlas, Bloom, Ursa, Kahlo, Zebra Day, login broker, or Dayhoff restart was performed. |
| TEST-001 | Dewey | Run focused tests and live smoke for artifact page, external refs, share creation/revoke, and report view | SUCCESS | contract_test | Gate 7 | Agent 8 | Dewey: `python -m py_compile ...`; `python -m pytest tests/test_artifacts_ui.py tests/test_external_object_links.py tests/test_service_relationships.py tests/test_share_references.py tests/test_route_coverage_gaps.py -q` -> 20 passed. Dayhoff: two targeted runtime tests passed. Live smoke: `/artifacts/euid/Z-DGX-1HR` 401 protected, `/shares` 401 protected, fake share 404. |  | Focused tests and protected route smoke completed. |

## Terminal Report

All ledger rows are terminal: 12 `SUCCESS`, 0 open.

Implemented only the AWS `lsmcok1` Dewey checkout plus Dewey-related Dayhoff config generation. CloudFront remains out of scope and untouched. Dewey is running on `https://localhost:8914` behind the existing `https://dewey.dev.lsmc.life` ngrok tunnel. The artifact and shares pages are protected for unauthenticated requests, and the fake share route returns 404 rather than minting anything.

Changed Dewey files:

- `dewey_service/app.py`
- `dewey_service/services/base.py`
- `dewey_service/services/sharing.py`
- `dewey_service/settings.py`
- `dewey_service/static/console.css`
- `dewey_service/templates/_artifact_links.html`
- `dewey_service/templates/artifact_detail.html`
- `dewey_service/templates/shares.html`
- `tests/conftest.py`
- `tests/test_artifacts_ui.py`
- `tests/test_service_relationships.py`
- `tests/test_share_references.py`
- this ledger under `docs/plans/`

Changed Dayhoff files for Dewey-only config preservation:

- `/home/ubuntu/projects/dayhoff/app/dayhoff/runtime_core.py`
- `/home/ubuntu/projects/dayhoff/tests/test_runtime_core.py`

Tests and smoke:

- Dewey focused compile and pytest: 20 passed.
- Dayhoff focused compile and two runtime config tests: 2 passed.
- Live Dewey health: `status=ok`, `service=dewey`.
- Live route smoke: artifact and shared-data pages require auth; invalid share route returns 404.

No CloudFront work, bucket policy mutation, destructive AWS action, release/tag work, or non-Dewey service restart was performed.
