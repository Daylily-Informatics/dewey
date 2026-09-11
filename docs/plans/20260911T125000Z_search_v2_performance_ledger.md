# Dewey Search v2 consolidation and page performance

Gate 0: clean controlling checkout at 33cbd13, live image still Dewey 9.0.0 digest bce8846d42320467824ce9473dd2315922ea7575c92633e04ca0a159c25c613b. Source inspection finds per-artifact relationship queries before pagination and duplicate artifact/set search forms. No unrelated changes. User authorizes GUI consolidation and performance fixes on Dewey. Target: >=2x reduction in measured affected-page latency with same data and equivalent authenticated requests; do not claim every page improves without measurement.

One agent; no intermediate image; focused tests then one required final CI run. No data migration or allocator changes. Existing TapDB pin remains 10.1.1rc1. This ledger is separate from completed migration Phase 1.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| S01 | GUI | One Search v2 interface; preserve intake/share workflows | SUCCESS | feature_implementation | User request | O | /search and artifacts.html | Duplicate forms | |
| P01 | Performance | Measure baseline and remove repeated DB work | SUCCESS | feature_implementation | User request | O | services/search.py | Per-row external lineage queries | |
| V01 | Acceptance | Equivalent results, focused regression and >=2x live comparison | OPEN | contract_test | User request | O | Pending | | |
| R01 | Release | Release and promote one complete image, Dewey only | OPEN | feature_implementation | Existing deployment authorization and current fix request | O | Pending | | |

## Baseline and implementation

- Production API POST `/api/search/v2/query`, scopes artifact/share, page_size 25: 8.608 / 8.894 / 8.885 seconds, median 8.885; total 5038. All three normalized result hashes: `800cb1df4afcd48bdbab1e1e5ea70bc8c2a7d84381a7990dce6e9d89a4d6852a`.
- Batch active lineage children, endpoint validation, set membership and literature saves. No response cache or skipped permission checks. Run synchronous search work in FastAPI worker threads to avoid blocking other page requests.
- Duplicate artifact/set query forms replaced with scoped Search v2 entry points. Existing mutation result panels and API contracts retained; PubMed search is a distinct external literature workflow.
- Focused validation: 76 tests passed covering search, artifact GUI, embedded integration, UI chrome and external references. After extending batching to sets/literature, the 46 affected search/reference tests passed. Initial focused attempt found an unsupported class relationship loader and missing local test deployment environment; corrected to explicit parent-UID batching and explicit ci environment. No broad local suite was run.
- Authenticated browser acceptance reached Google password entry; user asked to finish sign-in. No credentials read or session bypass attempted.

## Actual-data performance proof

Read-only diagnostic subprocess inside the existing image, separate from the server: old installed application compared with revised application modules loaded only into the diagnostic process; no installed files/package or running server changed. Exact same runtime config/database, source and request. Remote evidence `/home/ubuntu/dewey_ops/search-v2-20260911/profile.log`.

| Phase | Seconds | SQL statements | Total | Result hash |
|---|---:|---:|---:|---|
| Old service | 8.974 | 5289 | 5038 | 800cb1df4afcd48bdbab1e1e5ea70bc8c2a7d84381a7990dce6e9d89a4d6852a |
| Batched 1 | 0.774 | 16 | 5038 | same |
| Batched 2 | 0.657 | 16 | 5038 | same |
| Batched 3 | 0.653 | 16 | 5038 | same |

Median revised service 0.657s; 13.66x against old service measurement. This proves the affected search computation; final image HTTP and GUI acceptance remain separate. No claim that every standalone page is 13x faster.
