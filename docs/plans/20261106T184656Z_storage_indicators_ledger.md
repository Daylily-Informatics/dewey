# Compact S3 relationship indicators

CREATED: 2026-11-06 18:46:56 UTC
Updated: 2026-11-06 19:05:58 UTC

## Current state

Implementation and focused privacy/UI checks are complete. Source publication is authorized. A release/deployment is blocked by the user's retained effectively-unchanged-cost and <=4% load-time condition. The measured cached-service path does not establish that bound, so no new tag, image build, hot patch or deployment is made. The prior immutable12.0.27 deployment is unchanged.

| Work unit | Status | Evidence |
|---|---|---|
| Inventory | SUCCESS | Current source starts at12.0.27; two previous local operational receipt changes are excluded from publication and preserved |
| Compact column | SUCCESS | One Status column immediately after Copy S3 URI; 12px inline SVGs in a34px button; mobile44px controls side by side |
| Native authority | SUCCESS | Exact registered record; typed artifact_set_member, current share_revision_target and current share_grant_target lineage |
| Privacy | SUCCESS | Visible set policy; active/unexpired current share/grants; share audience only for owners/admins with verified managed-sharing context |
| Requests | SUCCESS | Same browser request;0 extra S3 requests; SQL statements unchanged at15/admin and16/internal-reader including runtime/session statements |
| Functional validation | SUCCESS |7 browser/backend contracts,5 JavaScript behavior tests, native PostgreSQL privacy contract |
| Performance condition | BLOCKED |50 paired samples per role/size,5 warmups; confidence interval does not establish <=4% |
| Release/deploy | BLOCKED | No new tag/build/deploy until the condition is satisfied or explicitly changed |

## Semantics

The combined glyphs show explicit registration, membership of a visible set, an active share target the viewer manages, and exact lsmc.com-only versus broader recipients. Named external recipients, lsmc.bio, subdomains and public-with-registration count as broader than exact lsmc.com. Broader does not mean anonymous/public access. Expired/revoked grants and historical target revisions do not count. Private membership/share IDs, addresses, counts and audience details are not returned. The compact payload contains only authorized flags; missing icons do not establish absence of private relationships. Duplicate exact registrations combine only their authorized indicators.

The current SQL-expression cache is bounded and keyed by the full immutable principal, managed-sharing capability and maintenance mode. It caches query construction only, never authorization results, relationships or expiry decisions. Every request reads live native data and uses database time. Existing backend no-delete and atomic create-only protections are preserved.

## Comparison

Alternating paired native PostgreSQL service calls with a cached-listing stand-in; no artificial network delay. Each fixture has250 explicitly registered page objects,750 background objects,2 sets and3 active shares, with current/historical/revoked/expired grants. Earlier isolated trial fixtures are retained, so these are fixture counts rather than the total final database population. Sizes25,100,250 cover the browser page and larger API pages. Five warmups then50 measured pairs per role/size; paired bootstrap95% intervals use2000 resamples.

| Role | Rows | Median before/after ms | Mean before/after ms | P95 before/after ms | Mean increase | Paired95% interval |
|---|---:|---:|---:|---:|---:|---|
| admin | 25 | 6.98 / 10.56 | 7.28 / 10.75 | 8.64 / 11.94 | 47.7% | [45.1%, 50.2%] |
| admin | 100 | 10.36 / 13.26 | 10.55 / 14.14 | 12.23 / 16.82 | 34.1% | [28.3%, 44.2%] |
| admin | 250 | 18.13 / 18.37 | 18.17 / 21.25 | 18.71 / 47.06 | 17.0% | [4.7%, 30.0%] |
| internal_reader | 25 | 34.11 / 39.11 | 34.66 / 47.24 | 38.42 / 83.29 | 36.3% | [23.7%, 50.1%] |
| internal_reader | 100 | 96.10 / 103.07 | 98.34 / 113.31 | 103.50 / 150.40 | 15.2% | [8.7%, 21.8%] |
| internal_reader | 250 | 205.61 / 215.28 | 219.16 / 222.22 | 259.31 / 266.05 | 1.4% | [-2.6%, 5.6%] |

These are local cached-service measurements, not production HTTP/page paint or every workload. They demonstrate measurable extra database work; no end-to-end <=4% claim or billing equivalence is made. Two prior designs were also measured and were slower. The final expression-cached design reduces the admin25-row mean overhead to about3.47ms but still exceeds the strict relative bound. Full timing distributions remain local; the adjacent JSON contains safe aggregate evidence only.

## Checks and remaining work

- PASS: `node --test tests/ui/storage_browser.test.cjs` —5 tests,0 failures; local sorting/TSV/copy preserved and no extra fetch for icons/details.
- PASS: seven focused storage-browser metadata/no-delete/create-only tests. Native PostgreSQL checks cover explicit lineage, historical and inactive grants, exact-domain semantics, private set/share suppression, missing managed context and unregistered paths. Initial native setup accidentally duplicated automatically initialized fixture policies; it was corrected to update the fixture's existing policy, then the native contract passed.
- Native comparison collection completed for all six final workloads. The performance gate itself is NOT satisfied; collection completion is not a performance pass. No full suite/lint/coverage or CI campaign was run. CI configuration routes the native contract to its existing isolated PostgreSQL job and excludes the explicitly requested timing experiment from routine CI.
- Chrome synthetic preview checked desktop1381px and actual CSS mobile320px. At320px document width=scroll width320, table290.9px; copy and indicator controls both44px and share the same row. Desktop indicator footprint34x34px versus copy33x29px. Accessible details dialog works without a fetch. Temporary viewport reset and preview server stopped. No live acceptance is claimed for this undeployed candidate.
- Remaining release gate: further optimization and representative timing evidence establishing the bound, or explicit user relaxation of that condition. Operational receipts and full artifacts are not uploaded to the public repository or Library.
