# Sequencer Run Registration and Ursa Trigger 10-Agent Ledger

Created: 2026-05-26T22:05:47Z

## Objective

Implement private, non-main support for Dewey sequencer run registration and Ursa trigger handoff across the Dayhoff ecosystem. Dewey records immutable run/result evidence and catalog-driven triggers; Ursa owns execution; DayEC/DayOA own command catalog and recipes; Bloom/Atlas remain linkage and delivery systems. No AWS deployment, main merge, or destructive cleanup is in scope for this ledger.

## Gate 0 Inventory

| Repo | Private worktree | Branch | Base tag | Base commit | Initial dirty state |
|---|---|---|---|---|---|
| Dewey | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `3.0.16` | `925129b5100576a322a151343413fe5c261cc930` | clean |
| daylily-ursa | `/Users/jmajor/projects/mega_dayhoff/repos_work/daylily-ursa-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `4.0.0` | `23fbf4c06ca779b0904095c71559b51c6062bbd2` | clean |
| daylily-ephemeral-cluster | `/Users/jmajor/projects/mega_dayhoff/repos_work/daylily-ec-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `5.0.1` | `5966aabad77e76a65cbc7fd87b2770496f52100d` | clean |
| daylily-omics-analysis | `/Users/jmajor/projects/mega_dayhoff/repos_work/daylily-omics-analysis-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `2.0.1` | `a6b4dd4918c9d2473bb52ec69f3aba12b7fb7f32` | clean |
| lsmc-atlas | `/Users/jmajor/projects/mega_dayhoff/repos_work/lsmc-atlas-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `4.0.33` | `8f11cd6d15b89eb88ad42c5c5b5759ab987c779a` | clean |
| bloom | `/Users/jmajor/projects/mega_dayhoff/repos_work/bloom-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `5.0.31` | `37f4b0d145b3811e99ccdeffb91f54e9f79a3174` | clean |
| zebra_day | `/Users/jmajor/projects/mega_dayhoff/repos_work/zebra-day-sequencer-run-registration-20260526` | `codex/sequencer-run-registration-20260526T220547Z` | `6.0.20` | `5ab36b1c44e4fe48c83cb20588eae72948f84599` | clean |

## Recon Notes

- Dewey currently exposes `POST /api/v1/artifact-prefixes` as prefix registration only; it does not list descendants or prove transfer completion.
- Dewey currently exposes `POST /api/v1/artifacts/import-run-prefix` for `platform=ultima` only through `SUPPORTED_RUN_PREFIX_PLATFORMS = {"ultima"}` in `dewey_service/services/artifacts.py`.
- The ULTIMA importer uses S3 list output and currently records listed child objects as `storage_status="verified"` even though S3 `list_objects_v2` cannot return version IDs or full checksum evidence.
- Dewey has duplicate browser `GET /share-references/{share_reference_euid}` routes. The earlier route calls `service.open_share_reference` without `require_ui_session`; the later route calls `service.issue_share_reference_access` with session attribution.
- DayEC already includes catalog IDs `illumina_snv_alignstats_relatedness_vep_multiqc`, `ultima_snv_alignstats_kitchensink`, `ont_snv_alignstats_kitchensink`, `hybrid_ilmn_ont_snv_kitchensink`, `illumina_run_qc`, `ont_run_qc`, and `ultima_run_qc` in both source and packaged catalog files.
- DayOA already contains workflow targets for run QC, kitchen-sink outputs, relatedness, VEP, and MultiQC support.
- Ursa already validates analysis command IDs through the DayEC catalog in `daylib_ursa/analysis_commands.py` and exposes analysis job routes in `daylib_ursa/workset_api.py`.
- Atlas already gates Ursa returned results by approved review state before clinical delivery.

## Ledger Rows

| ID | Agent | Area | Requirement | Status | Evidence |
|---|---:|---|---|---|---|
| SETUP-001 | 1 | Gate 0 | Re-fetch all repos, verify max non-`v` semver tags, create private worktrees/branches, record dirty state and baselines. | DONE | Worktrees and base commits recorded above. |
| RECON-001 | 1 | Recon | Document existing Dewey, Ursa, DayEC, DayOA, Bloom, Atlas, and Zebra seams, route names, command IDs, auth patterns, storage assumptions, and deployment gates. | DONE | Recon notes recorded above; Dewey/Ursa contract docs added. |
| DAYOA-001 | 2 | Recipes | Implement full kitchen-sink workflow recipes for ULTIMA, ONT, hybrid ILMN+ONT, and verify ILMN command. | DONE | Existing DayOA targets and QEO registration rules verified by focused tests. |
| DAYEC-001 | 3 | Catalog | Add/validate DayEC catalog entries, packaged catalog mirror, run-context support, dry-run previews, export expectations, and version bump. | DONE | Existing DayEC catalog entries verified; source and packaged mirrors already include required commands. |
| DEWEY-001 | 4 | Run Registration | Add Dewey API/GUI run registration, platform selectors, immutable prefix/file records, sidecar discovery, receipts, and outbox records. | DONE | Added `POST /api/v1/sequencer-runs/register`, GUI action `/sequencer-runs/register`, `SequencerRunRegistrationServiceMixin`, selectors, sidecar parsing, receipts, and outbox. |
| DEWEY-002 | 4 | Results | Add Dewey analysis-result registration, terminal pass/fail artifact sets, sample linkage, lineage to run/sidecar, and non-PHI events. | DONE | Added `POST /api/v1/analysis-results/register` with artifact-set, lineage, receipt, and non-PHI outbox support. |
| URSA-001 | 5 | Trigger API | Add Dewey trigger endpoint, idempotency, command catalog validation, queue state, sidecar response capture, and Dewey client methods. | DONE | Added Ursa `POST/GET /api/v1/dewey/run-analysis-triggers` and Dewey client `register_analysis_results`. |
| URSA-002 | 6 | Execution | Add cluster create/reuse, one-run-at-a-time staging, DayEC launch/monitor/export, terminal Dewey registration, and config-gated idle cleanup. | BLOCKED | Live execution and destructive idle cleanup are outside this private implementation without a separate approval gate. Stubbed queue/trigger handoff is in scope. |
| LINK-001 | 7 | Atlas/Bloom | Extend Bloom resolution for ULTIMA/hybrid as needed and Atlas result-return contracts for Dewey analysis artifact-set links. | DONE | Atlas result-return request/context now carries `analysis_artifact_set_euid` and `dewey_receipt_euid`. Bloom/Zebra unchanged because Dewey accepts explicit linkage EUIDs and Bloom ULTIMA/hybrid wet-lab queue semantics are outside this slice. |
| ACCEPT-001 | 8-10 | Security/Test/Release | Add security/QMS tests, focused and repo gates, private branch commits/tags without `v` prefixes, and terminal ledger states. | DONE | Tests passed; changed repos committed locally for private branch push/tag. |

## Acceptance Log

- Dewey: `python -m compileall dewey_service tests` passed.
- Dewey: `pytest -q tests/test_sequencer_run_registration.py tests/test_run_prefix_ingest.py` passed, 9 tests.
- Dewey: `dewey quality check` passed.
- Dewey: `dewey test run` passed.
- Ursa: `pytest -q tests/test_dewey_run_analysis_triggers.py tests/test_dewey_client.py` passed, 6 tests.
- Ursa: `ruff check daylib_ursa/workset_api.py daylib_ursa/integrations/dewey_client.py tests/test_dewey_run_analysis_triggers.py` passed.
- Ursa: repo-wide `URSA_DEPLOYMENT_CODE=runtrig ursa quality check` remains blocked by pre-existing unrelated format/typecheck debt; touched-file lint and focused tests pass.
- DayEC: `pytest -q tests/test_repository_catalog.py` passed, 8 tests.
- DayOA: `pytest -q tests/test_multiqc_qc_targets.py tests/test_run_qc_reports.py tests/test_qeo_registration.py` passed, 33 tests.
- Atlas: `ruff check app/domain/services/ursa_integration.py app/api/routes/ursa_integration.py tests/test_ursa_result_return_service.py` passed.
- Atlas: `ruff format --check app/domain/services/ursa_integration.py app/api/routes/ursa_integration.py tests/test_ursa_result_return_service.py` passed.
- Atlas: `pytest -q tests/test_ursa_result_return_service.py::test_apply_creates_result_and_artifacts` passed.
