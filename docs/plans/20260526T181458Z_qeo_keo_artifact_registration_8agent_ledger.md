# Dewey QEO/KEO Artifact Registration 8-Agent Ledger

Created: 2026-05-26T18:14:58Z

## Summary

Implement narrow Data Plane support for QEO/KEO artifact-set registration in Dewey. Dewey records artifact existence, pointers, checksums, lineage references, deterministic receipts, and local transactional outbox events. Dewey must not parse QC metrics, crawl workflow directories, make QC decisions, become R2, or orchestrate Daylily workflows.

## Gate 0 Inventory

Controlling plan: user-provided "Dewey QEO/KEO Artifact Registration 8-Agent Ledger Plan"
Ledger path: `docs/plans/20260526T181458Z_qeo_keo_artifact_registration_8agent_ledger.md`

Repo state:

| Repo | Path | Branch | State |
|---|---|---|---|
| Dewey source | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey` | `codex/security-dewey-share-auth-20260526` | `HEAD`, `origin/main`, and `origin/HEAD` all `8205223c47f568211a301d11aa384615f1bdc395`; clean |
| Dewey worktree | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-qeo-keo-artifacts-20260526` | `codex/qeo-keo-artifact-registration-20260526` | Created from `origin/main` at `8205223c47f568211a301d11aa384615f1bdc395`; clean after activation and baseline tests |

Instructions read:

- `/Users/jmajor/.agents/AGENTS.md`
- `/Users/jmajor/.codex/AGENTS.md`
- `/Users/jmajor/.codex/docs/plan-ledger-workflow.md`
- `/Users/jmajor/.augment/AGENTS.md`
- `/Users/jmajor/.augment/rules/*.md`
- `AGENTS.md`

Baseline commands:

- `git status --short --branch` -> `## codex/qeo-keo-artifact-registration-20260526...origin/main`
- `rg --files | wc -l` -> `155`
- `rg -n "artifact-set|artifact_set|Idempotency-Key|outbox|event|receipt|share reference|external object|TapDB|api_bearer|Bearer" README.md docs dewey_service tests config | wc -l` -> `1007`
- `source ./activate qeoart` -> created and activated `DEWEY-qeoart`, installed editable Dewey checkout
- `source ./activate qeoart && pytest -q tests/test_artifact_registration.py tests/test_artifact_set_membership.py tests/test_idempotency.py` -> `8 passed`

Live-system limits:

- No live AWS, production S3/OAC, CloudFront, TapDB reset/delete, Daylily producer change, QEO repo change, broker deployment, or destructive action is in scope.
- Event dispatch beyond local TapDB outbox storage is a stub.

## Ledger Rows

| ID | Agent | Area | Requirement | Status | Category | Gate | Evidence | Root Cause | Terminal Note |
|---|---:|---|---|---|---|---|---|---|---|
| SETUP-001 | 1 | Worktree/Gate 0 | Create isolated worktree, activate with `source ./activate qeoart`, record git state, baseline tests, instructions, and source inventory in the ledger. | SUCCESS | feature_implementation | Gate 0 | Gate 0 inventory above; focused baseline tests `8 passed`. |  | Isolated worktree and baseline are recorded. |
| RECON-001 | 1 | Recon | Create `docs/qeo/QEO_DEWEY_RECON.md` with exact current routes, symbols, storage/auth/TapDB/share assumptions, risks, and integration seams. | SUCCESS | feature_implementation | Gate 1 | `docs/qeo/QEO_DEWEY_RECON.md` |  | Recon doc created with paths, symbols, assumptions, risks, and integration seams. |
| CONTRACT-001 | 2 | Models | Add strict registration, file artifact, receipt, and event envelope models plus deterministic canonical JSON/hash helpers. | SUCCESS | feature_implementation | Gate 1 | `dewey_service/registration_contracts.py`; focused tests `17 passed`. |  | Strict Pydantic contracts and canonical hash helpers implemented. |
| PERSIST-001 | 3 | TapDB | Add receipt and outbox templates/constants, fake backend support, and receipt/outbox persistence helpers. | SUCCESS | feature_implementation | Gate 2 | `dewey_service/tapdb_backend.py`; `config/tapdb_templates/dewey/templates.json`; `tests/support/service_fakes.py`; focused tests `17 passed`. |  | Receipt and outbox templates plus fake support are implemented. |
| SERVICE-001 | 4 | Registration | Implement analysis artifact-set registration with preflight validation, immutable semantics, lineage refs, rerun links, receipts, and outbox event. | SUCCESS | feature_implementation | Gate 2 | `dewey_service/services/artifact_set_registration.py`; `tests/test_qeo_artifact_set_registration.py`; `tests/test_qeo_registration_events.py`. |  | Analysis artifact-set registration implemented and covered. |
| SERVICE-002 | 4 | Registration | Implement MultiQC artifact-set registration with report HTML, data-dir artifact, key files, parser-relevant files, receipts, and MultiQC event. | SUCCESS | feature_implementation | Gate 2 | `dewey_service/services/artifact_set_registration.py`; `tests/test_qeo_multiqc_registration.py`. |  | MultiQC registration implemented and covered. |
| API-001 | 5 | Routes/Auth | Wire the two new POST routes through existing bearer auth and Dewey error handling; do not expose broad enumeration or share expansion. | SUCCESS | feature_implementation | Gate 3 | `dewey_service/app.py`; route auth tests in QEO test suite. |  | New POST routes use existing bearer dependency and error mapping. |
| HANDOFF-001 | 6 | QEO handoff | Ensure receipt and outbox event contain QEO-consumable manifest/artifact refs and parser hints, not filesystem paths. | SUCCESS | feature_implementation | Gate 3 | Receipt/event contract tests in `tests/test_qeo_registration_events.py`; docs in `docs/qeo/`. |  | QEO handoff is receipt plus local outbox; event payloads omit paths and artifact lists. |
| SECURITY-001 | 7 | Security | Add PHI denylist/event scanner tests, service-auth preservation tests, replay/idempotency tests, and immutable rewrite rejection tests. | SUCCESS | contract_test | Gate 4 | `tests/test_qeo_registration_security.py`; `tests/test_qeo_registration_events.py`; focused tests `17 passed`. |  | PHI/event, auth, replay, and immutable rewrite tests added. |
| TEST-001 | 7 | Tests | Cover manifest hashing, duplicate replay, checksum/size mismatch, required missing, rerun linkage, directory plus key files, outbox, events, and local-only. | SUCCESS | contract_test | Gate 4 | `pytest -q tests/test_qeo_artifact_set_registration.py tests/test_qeo_multiqc_registration.py tests/test_qeo_registration_events.py tests/test_qeo_registration_security.py` -> `17 passed`. |  | Focused QEO registration coverage added. |
| DOCS-001 | 8 | Docs | Add `docs/qeo/QEO_DEWEY_REGISTRATION_CONTRACT.md`, `QEO_DEWEY_EVENT_CONTRACTS.md`, and `QEO_DEWEY_RUNBOOK.md`. | SUCCESS | feature_implementation | Gate 4 | `docs/qeo/QEO_DEWEY_REGISTRATION_CONTRACT.md`; `docs/qeo/QEO_DEWEY_EVENT_CONTRACTS.md`; `docs/qeo/QEO_DEWEY_RUNBOOK.md`; `docs/apis.md`; `docs/architecture.md`. |  | Required docs and API/architecture references updated. |
| ACCEPT-001 | 1 | Acceptance | Run focused tests, full `dewey test run`, `dewey quality check`, and final ledger terminal-state report. | SUCCESS | contract_test | Gate 5 | Focused QEO tests `17 passed`; exact `dewey test run` passed; exact `dewey quality check` passed. Both full commands emitted the pre-existing FastAPI duplicate operation-id warning for `dag_search_api_dag_search_get`. |  | All ledger rows are terminal and the objective is complete in the isolated worktree. |

## Acceptance Evidence

- `source ./activate qeoart && pytest -q tests/test_qeo_artifact_set_registration.py tests/test_qeo_multiqc_registration.py tests/test_qeo_registration_events.py tests/test_qeo_registration_security.py` -> `17 passed`
- `source ./activate qeoart && dewey test run` -> passed with `2 skipped`; warning: duplicate FastAPI operation ID `dag_search_api_dag_search_get`
- `source ./activate qeoart && dewey quality check` -> Ruff passed, tests passed with `2 skipped`; warning: duplicate FastAPI operation ID `dag_search_api_dag_search_get`
