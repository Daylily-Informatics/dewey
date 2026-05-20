# Dewey CloudFront Sharing Execution Ledger

Date: 2026-05-20

## Control Ledger

Controlling plan: extracted Dewey CloudFront requirements from `/Users/jmajor/projects/mega_dayhoff/dayhoff/mega_dy.md` and `/Users/jmajor/projects/mega_dayhoff/codex_plan_prompt/source_inputs/dewey_cloudfront_reqs.md`

Ledger path: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-cloudfront-main-20260520/docs/plans/20260520T192209Z_dewey_cloudfront_ledger.md`

## Gate 0 Baseline

- Dewey implementation checkout: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-cloudfront-main-20260520`
- Dewey repo state: `git status --short --branch` -> `## main...origin/main`
- Dewey HEAD: `152580aceeabe493ee2d74273e67acc51df80ce5` (`origin/main`, `152580a Merge pull request #59 from Daylily-Informatics/codex/aws-lsmcok1-release-20260520`)
- Existing Dewey checkout left untouched: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey` on `codex/dewey-external-euid-links-20260520`
- Dayhoff plan repo state: `git -C /Users/jmajor/projects/mega_dayhoff/dayhoff status --short --branch` -> `## main...origin/main [ahead 5, behind 13]`
- Dayhoff plan file status: `/Users/jmajor/projects/mega_dayhoff/dayhoff/mega_dy.md` is untracked in the dirty Dayhoff checkout.
- Sweep evidence: current Dewey code has current transports `presigned_s3`, `rclone_http`, and `rclone_sftp`; CloudFront share implementation is not present.
- AWS read-only inventory from planning: no Dewey-specific CloudFront distribution was found; existing distributions are unrelated DayOA/MultiQC shares.
- Live limits: no destructive AWS action, production S3/OAC/bucket-policy mutation, CloudFront distribution mutation, or external public share issuance is performed without separate explicit approval.
- Implementation assumption: public CloudFront share creation requires exact verified creator domain `lsmc.com` and explicit `lsmc:dewey:share-writer` capability; admins can inspect/revoke but do not implicitly bypass this public-share creation rule.

## Rows

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| LEDGER-001 | Dewey | Create execution ledger and record Gate 0 baseline before runtime edits | SUCCESS | plan_amendment | Gate 0 | orchestrator | This ledger. |  | Ledger created before code edits. |
| PLAN-001 | Dayhoff | Remove extracted Dewey CloudFront items from `dayhoff/mega_dy.md` and leave non-Dewey plan content intact | SUCCESS | plan_amendment | Gate 1 | orchestrator | `/Users/jmajor/projects/mega_dayhoff/dayhoff/mega_dy.md` summary changed to 18 workstreams and Dewey CloudFront bullets removed. |  | Extraction applied without touching unrelated Dayhoff dirty files. |
| SHARE-001 | Dewey | Extend share-reference transport/model for CloudFront targets, visibility, recipients, permissions, mode, revocation, and audit data | SUCCESS | feature_implementation | Gate 3 | Agent 1 | `dewey_service/services/sharing.py`; `dewey_service/services/base.py`; `tests/test_cloudfront_shares.py`. |  | CloudFront share metadata is persisted in the existing share-reference JSON payload. |
| SHARE-002 | Dewey | Enforce authenticated recipient rules, exact-domain matching, pending-external denial, expiration, revocation, and public-share creator policy | SUCCESS | feature_implementation | Gate 3 | Agent 1 | `test_cloudfront_authenticated_share_authorizes_exact_domain`; `test_cloudfront_public_share_requires_lsmc_share_writer`. |  | Public share creation requires exact verified `lsmc.com` plus `lsmc:dewey:share-writer`. |
| CF-001 | Dewey | Add explicit CloudFront signer/config abstraction with no inferred defaults and scoped URL/cookie package generation | SUCCESS | config_or_startup_contract | Gate 2 | Agent 2 | `dewey_service/cloudfront.py`; `dewey_service/settings.py`; config templates; `test_settings_loads_explicit_cloudfront_config`. |  | CloudFront signing config is explicit and disabled unless configured. |
| UI-001 | Dewey | Add dedicated CloudFront share create/detail/browse/denied/programmatic templates and routes | SUCCESS | feature_implementation | Gate 3 | Agent 3 | Dedicated templates under `dewey_service/templates/`; route coverage test passed. |  | Create/detail/browse/denied/programmatic surfaces are registered and covered. |
| ADMIN-001 | Dewey | Add `/admin/external-shares` report with required filters and columns | SUCCESS | feature_implementation | Gate 3 | Agent 3 | `dewey_service/app.py`; `admin_external_shares_report.html`; `test_cloudfront_routes_and_admin_report`. |  | Admin external-share report renders CloudFront share rows and filters. |
| TEST-001 | Dewey | Add focused tests for CloudFront share creation, policy, scoping, audit, templates, and report rendering | SUCCESS | contract_test | Gate 5 | Agent 4 | `pytest tests/test_cloudfront_shares.py ... -> 65 passed`; `DAYHOFF_PROJECT_ROOT=/Users/jmajor/projects/mega_dayhoff/dayhoff pytest -q -> passed, 2 skipped`. |  | Focused and full local suites pass. |
| AWS-001 | AWS/Dewey | Verify live us-west-2 Dayhoff Dewey target identity, config path, S3 privacy, and CloudFront readiness via read-only checks | SUCCESS | config_or_startup_contract | Gate 4 | orchestrator | SSM read-only inventory found live Dewey on `i-09126000eb19643b0`, cwd `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey`, config `/home/ubuntu/.config/dewey-lsmcok1/dewey-config-lsmcok1.yaml`, port `8914`; CloudFront list found no Dewey distribution. |  | Live target identified; no non-Dewey service restart performed. |
| AWS-002 | AWS/Dewey | Deploy local Dewey changes to the AWS Dayhoff deployed Dewey and restart Dewey only | OPEN | config_or_startup_contract | Gate 4 | orchestrator | Pending. |  |  |
| AWS-003 | AWS/Dewey | Create/update real CloudFront distribution/OAC/bucket policy if required | BLOCKED | config_or_startup_contract | Gate 4 | orchestrator | Planning found no Dewey distribution. | Separate explicit approval is required before live CloudFront/S3 policy mutation. | Blocked until the user approves the exact live AWS mutation. |

## Progress Log

- 2026-05-20T19:22:09Z: Gate 0 recorded from clean main checkout and dirty Dayhoff plan checkout; implementation not started.
- 2026-05-20T19:35:00Z: Local focused suite passed: `pytest tests/test_cloudfront_shares.py tests/test_share_references.py tests/test_service_relationships.py tests/test_artifacts_ui.py tests/test_route_coverage_gaps.py tests/test_route_surface_coverage.py tests/test_settings.py tests/test_storage_unit.py tests/test_run_prefix_ingest.py -q` -> 65 passed, 1 known TapDB duplicate operation-id warning.
- 2026-05-20T19:36:00Z: Full local suite passed with explicit schema root: `DAYHOFF_PROJECT_ROOT=/Users/jmajor/projects/mega_dayhoff/dayhoff pytest -q` -> passed, 2 skipped, 1 known TapDB duplicate operation-id warning.
- 2026-05-20T19:36:00Z: AWS read-only inventory identified deployed Dewey on `i-09126000eb19643b0` / `lsmcok1`.
