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
| AWS-002 | AWS/Dewey | Deploy local Dewey changes to the AWS Dayhoff deployed Dewey and restart Dewey only | SUCCESS | config_or_startup_contract | Gate 4 | orchestrator | Remote `i-09126000eb19643b0` fetched branch `codex/dewey-cloudfront-sharing-20260520`, focused remote tests passed, Dewey restarted on PID `325010`, `https://localhost:8914/healthz` and `https://dewey.dev.lsmc.life/healthz` returned `status=ok`. |  | Dewey-only code deployment and restart completed; ngrok and non-Dewey services left running. |
| AWS-003 | AWS/Dewey | Create/update real CloudFront distribution/OAC/bucket policy if required | SUCCESS | config_or_startup_contract | Gate 4 | orchestrator | Created public key `K2V6BK2G0P9S1Q`, key group `5bb4dbc2-14fc-45da-95db-19eff915ca78`, OAC `ELN2H45KSPZ3D`, distribution `E3V6LY7GVFQDQ3` / `d213df1ma80hb0.cloudfront.net`; `lsmc-dewey-0` bucket policy status `IsPublic=false`; Dewey PID `326168`; public health OK; CloudFront smoke `unsigned=403`, `signed=200`. |  | Live Dewey CloudFront delivery is enabled with private S3 origin access and Dewey signing config. |

## Progress Log

- 2026-05-20T19:22:09Z: Gate 0 recorded from clean main checkout and dirty Dayhoff plan checkout; implementation not started.
- 2026-05-20T19:35:00Z: Local focused suite passed: `pytest tests/test_cloudfront_shares.py tests/test_share_references.py tests/test_service_relationships.py tests/test_artifacts_ui.py tests/test_route_coverage_gaps.py tests/test_route_surface_coverage.py tests/test_settings.py tests/test_storage_unit.py tests/test_run_prefix_ingest.py -q` -> 65 passed, 1 known TapDB duplicate operation-id warning.
- 2026-05-20T19:36:00Z: Full local suite passed with explicit schema root: `DAYHOFF_PROJECT_ROOT=/Users/jmajor/projects/mega_dayhoff/dayhoff pytest -q` -> passed, 2 skipped, 1 known TapDB duplicate operation-id warning.
- 2026-05-20T19:36:00Z: AWS read-only inventory identified deployed Dewey on `i-09126000eb19643b0` / `lsmcok1`.
- 2026-05-20T19:38:00Z: Pushed branch `codex/dewey-cloudfront-sharing-20260520` to GitHub for remote fetch-based deployment.
- 2026-05-20T19:39:00Z: Remote branch fetch/switch succeeded on `i-09126000eb19643b0`; remote focused tests passed: `pytest tests/test_cloudfront_shares.py tests/test_settings.py tests/test_share_references.py -q`.
- 2026-05-20T19:41:00Z: Restarted Dewey only with Dayhoff runtime env; live PID `325010` listens on `0.0.0.0:8914`; local and public health checks return `status=ok`; CloudFront route smoke checks return expected unauthenticated `401`.
- 2026-05-20T20:49:29Z: User gave second explicit approval to create live Dewey CloudFront distribution, OAC, private S3 bucket policy, signing key material, Dewey config, and Dewey-only restart. Fresh baseline recorded before live mutation.
- 2026-05-20T20:51:34Z: Generated RSA private key on EC2 at `/home/ubuntu/.config/dewey-lsmcok1/cloudfront-private-key.pem` with mode `0600`; registered CloudFront public key `K2V6BK2G0P9S1Q`.
- 2026-05-20T20:54:00Z: Created CloudFront key group `5bb4dbc2-14fc-45da-95db-19eff915ca78`, OAC `ELN2H45KSPZ3D`, and distribution `E3V6LY7GVFQDQ3` (`d213df1ma80hb0.cloudfront.net`) for origin `lsmc-dewey-0.s3.us-west-2.amazonaws.com`.
- 2026-05-20T20:54:20Z: Applied non-public `lsmc-dewey-0` bucket policy granting `s3:GetObject` only to CloudFront distribution ARN `arn:aws:cloudfront::108782052779:distribution/E3V6LY7GVFQDQ3`; `get-bucket-policy-status` returned `IsPublic=false`.
- 2026-05-20T20:54:41Z: Updated `/home/ubuntu/.config/dewey-lsmcok1/dewey-config-lsmcok1.yaml` with `storage.cloudfront.enabled=true`, distribution domain/id, public key id, private key path, and 900-second TTLs; backup saved beside the config.
- 2026-05-20T20:55:58Z: Restarted Dewey only with deployment conda/env markers after an initial CLI validation miss; new PID `326168`; local and public `/healthz` returned `status=ok`; `/shares/cloudfront/new` returned unauthenticated `401`.
- 2026-05-20T20:56:30Z: Distribution status `Deployed`; default behavior trusts key group `5bb4dbc2-14fc-45da-95db-19eff915ca78`; OAC signing is `always`; CloudFront smoke against an existing small object returned `unsigned=403` and Dewey-signed `HEAD=200`.
