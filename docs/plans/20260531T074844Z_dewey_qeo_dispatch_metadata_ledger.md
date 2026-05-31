# Dewey/QEO Dispatch Filter And Metadata Ledger

Control ledger path: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey/docs/plans/20260531T074844Z_dewey_qeo_dispatch_metadata_ledger.md`

## Gate 0 Baseline

- Dewey repo: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey`
- Dewey branch: `codex/inf6-deploy-formalization-20260528`
- Dewey HEAD: `0c76c431c94e386f102710b7d19cef2460dd6f7a`
- Dewey status: `## codex/inf6-deploy-formalization-20260528...origin/codex/inf6-deploy-formalization-20260528`
- QEO repo: `/Users/jmajor/projects/lsmc/qeo`
- QEO branch: `codex/inf6-deploy-formalization-20260528`
- QEO HEAD: `53198cf1fd01e96f501bc9fa033a6c048eba7524`
- QEO status: `## codex/inf6-deploy-formalization-20260528...origin/codex/inf6-deploy-formalization-20260528`
- Instructions read: `/Users/jmajor/.agents/AGENTS.md`, `/Users/jmajor/.codex/AGENTS.md`, Dewey `AGENTS.md`, QEO `AGENTS.md`, `/Users/jmajor/projects/lsmc/AGENTS.md`, `/Users/jmajor/projects/daylily/daylily-omics-analysis/AGENTS.md`, `/Users/jmajor/.codex/docs/plan-ledger-workflow.md`.
- Sweep evidence:
  - Dewey contracts: `dewey_service/registration_contracts.py`, `dewey_service/services/artifact_set_registration.py`, `dewey_service/services/outbox.py`, `dewey_service/cli/qeo.py`.
  - Dewey currently emits `lsmc.dewey.artifact_set.registered.v1` and `lsmc.dewey.multiqc_artifact_set.registered.v1`.
  - Dewey registration requests persist request-derived artifact-set metadata, but strict request models do not expose explicit freeform registration metadata fields.
  - Dewey QEO dispatch currently filters by dispatch status and Dewey event prefix only; it cannot target one event id or artifact-set EUID.
  - QEO accepts only `/api/v1/ingest/dewey-events` and `/api/v1/ingest/dewey-receipts`; focused boundary tests reject Dewey registration routes and filesystem/S3 prefix crawling in `app/domain/dewey.py`.
- Assumptions: no live Dewey/QEO dispatch will be run in this implementation pass; missing live config remains a hard local error.

## Control Rows

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| DQ-001 | Dewey contracts | Add explicit metadata fields to strict registration request/receipt contracts and persist them without changing outbox payload privacy. | SUCCESS | feature_implementation | 1 | Dewey agent | `dewey_service/registration_contracts.py`, `dewey_service/services/artifact_set_registration.py`, `dewey_service/services/artifact_sets.py`, `tests/test_qeo_artifact_set_registration.py`, `tests/test_qeo_multiqc_registration.py`; outbox event payload test still omits paths/artifact refs. |  | Request metadata is persisted on artifact sets and receipts; artifact metadata is persisted on artifacts and receipt refs; QEO resolver responses include receipt metadata. |
| DQ-002 | Dewey dispatch | Add QEO dispatch filtering by event ID and artifact-set EUID so trial dispatch cannot send unrelated pending events. | SUCCESS | feature_implementation | 1 | Dewey agent | `dewey_service/services/outbox.py`, `tests/test_qeo_registration_events.py`; focused tests cover event-id filter, artifact-set filter, and empty-filter hard failure. |  | Scoped dispatch filters candidates before HTTP POST and leaves unrelated pending rows untouched. |
| DQ-003 | Dewey CLI | Expose dispatch filters through `dewey qeo dispatch` as explicit operator arguments. | SUCCESS | feature_implementation | 1 | Dewey agent | `dewey_service/cli/qeo.py`; options `--event-id` and `--artifact-set-euid` pass explicit sets into `dispatch_qeo_outbox`. |  | Operators can target trial outbox rows without sending unrelated pending events. |
| DQ-004 | QEO contracts | Confirm QEO consumes Dewey only through existing ingest endpoints and accepts Dewey receipt metadata if Dewey receipts carry it. | SUCCESS | contract_test | 1 | QEO agent | QEO `app/contracts.py`, `app/domain/dewey.py`, `tests/qeo_contracts/test_dewey_boundary.py`, `tests/qeo_dewey/test_dewey_consumer.py`; docs updated in `docs/qeo/QEO_DEWEY_CONSUMER_CONTRACT.md`. |  | QEO endpoints remain `/api/v1/ingest/dewey-events` and `/api/v1/ingest/dewey-receipts`; metadata is accepted and preserved in artifact-set projection. |
| DQ-005 | Verification | Run focused Dewey/QEO tests and record terminal status. | SUCCESS | contract_test | 5 | Orchestrator | Dewey: `python -m pytest -q tests/test_qeo_artifact_set_registration.py tests/test_qeo_multiqc_registration.py tests/test_qeo_registration_events.py` -> 23 passed. QEO: `.venv/bin/python -m pytest -q tests/qeo_contracts/test_dewey_boundary.py tests/qeo_dewey/test_dewey_consumer.py` -> 16 passed. `git diff --check` clean in both repos. |  | All rows are terminal; no live dispatch was run. |

## Final Status

- Terminal rows: 5 `SUCCESS`, 0 `BLOCKED`, 0 `FAIL`.
- Objective status for this Dewey/QEO implementation slice: complete locally.
- Live Dewey/QEO dispatch was not performed; the trial remains a later live operation requiring explicit runtime config and event/artifact-set filters.
