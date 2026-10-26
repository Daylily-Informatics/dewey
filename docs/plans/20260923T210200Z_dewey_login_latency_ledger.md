# Dewey signed-in latency investigation — 2026-09-23

## Current continuation state

Updated: 2026-09-23T22:06Z. Objective: implement the approved combined Dewey performance release and deploy only Dewey; distinguish source/release/deployment, stability, human acceptance, and quantitative performance evidence. The user explicitly said “PLEASE IMPLEMENT THIS PLAN”; the historical diagnosis-only stop is superseded.

Authority: source/API/UI changes, native audited cache initialization, one final tagged EC2 build, selected-service cutover, and normal availability observations approved. Tests/controlled performance campaigns remain unauthorized without two explicit scoped approvals. No PR, merge, local image build, sibling deployment, cleanup, or monitor.

Identities: /Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-gui-performance-20260919; codex/dewey-gui-performance-20260919; clean starting commit 3b52ba3. Service https://dewey.day.lsmc.bio; profile lsmc; us-west-2; designated EC2 i-07df3a933e4839f52; dayhoff-day-dewey-1. Fresh live health at 21:42:53Z: 10.0.7 / 8d04719a6ad82a6808bf38933b39cadb210b43d0; image sha256:50ef1ba6922be663e7c88839849b4a1649590ae8674c819dc8862e695055b7ac; 64 GiB available, 94% disk used. Human identity/role mapping remains unavailable. No inference made.

Completed source: blocking browse moved to worker pool; request-batched storage authorization/registration/breadcrumbs/buckets; typed visibility queries; optional Library counts and shared counts route; summary records plus lazy metadata/activity/member pages; 25-entry Load more; stale-read cancellation; bounded raw listing cache with single-flight/generation invalidation; durable Admin TTL; owning idempotent initialization CLI; query/S3/cache/response/unfinished telemetry and read timeouts. Syntax-only Python/JS parsing passed; no tests, lint, benchmark, or application test execution. Local installed dewey CLI points at older dewey-runtime-context-fix-20260911 worktree; its new-command help failed. No runtime operation attempted there and no CLI bypass. Final image packages this source and owns initialization.

Release: 10.0.8 and 10.0.9 were published and EC2-built but both failed native initialization before cutover. Exact source, tag and image identities are retained in the evidence. 10.0.8 used an unsupported runtime engine attribute, corrected through public Session.get_bind. 10.0.9 used the pre-existing invalid defaults identity key; TapDB requires a lowercase namespace followed by a colon. Corrected to dewey:registry-service-defaults. Native source and explicit production configuration confirm the existing tenant-null principal can own this global object without changing runtime permissions. Production 10.0.7 and durable settings remain unchanged; both failed one-off containers and receipts are preserved. Next unused tag 10.0.10 is absent remotely and will carry the corrected final candidate. Native initialization remains before service replacement.

Next: publish the corrected immutable 10.0.10 candidate, build on designated EC2, then run native initialization and selected cutover helper docs/plans/20260923T215000Z_dewey108_selected_cutover.py. Observe actual runtime and GUI login. Preserve previous compose/manifest/image; never force-stop or automatically roll back. P9 human acceptance and P10 50%/p95 claims require real comparable evidence. Combined release cannot isolate an incremental 50% beyond repair-only. Tests remain off.

Evidence: evidence/20260923T210200Z_dewey_login_latency/ includes original incident and implementation_baseline.json; implementation_notes.md records contracts, static review, limitations and deferred scenarios. P1–P10 remain independent of historical D1–D3.

## Gate 0

- Initial OWY checkout is unrelated and dirty; no edits there.
- Owning Dewey checkout baseline: `git status --short --branch` showed clean branch; older audit checkout is not the running revision. Existing completed September 19 ledger read once as historical context.
- Initial inspection: live /healthz, EC2 describe, host uptime/memory/disk, container status. No tests run per user policy.
- Symptoms: user confirmed "all of them" when asked which pages were unusable. Exact login time and browser timing not yet available.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Runtime | Confirm live deployment and resource baseline | SUCCESS | historical_docs_only | Read-only investigation | root | Live health, EC2/host observation above | | Exact runtime identified; machine not CPU/memory saturated at snapshot |
| D2 | Requests | Identify shared failing or slow path | SUCCESS | historical_docs_only | Read-only investigation | root | request_correlation.json; live_telemetry.json; live-matching app.py:3411 and registry_storage.py:92 | Blocking per-item browse work executes on shared event loop | Cross-client queuing and native slow browse confirmed; two separate search timeouts recorded |
| D3 | Diagnosis | Document cause, limits, and concrete next step | SUCCESS | historical_docs_only | Read-only investigation | root | Findings and remediation below; runtime_and_source.json | | Investigation complete with explicit query-level and browser-role limits; production unchanged |

## Approved implementation ledger

Gate 0 implementation baseline: clean 3b52ba3; instructed owning environment activated; no unrelated work changed. Source inventory: app.py, registry API/services/access, storage, backend, observability, client UI, owning CLI, and existing EC2 release/cutover helpers. Tests intentionally not run under user policy.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Baseline | Refresh source, production, resources and auth evidence | SUCCESS | historical_docs_only | Approved implementation plan; tests separately gated | root | implementation_baseline.json; fresh EC2/health/source inspection | | Baseline captured; human-role limitations explicit |
| P2 | Backend | Worker-pool browse and batched authorized storage lookup | SUCCESS | feature_implementation | Approved implementation plan; tests separately gated | root | registry_storage.py; app.py; registry_access.py; source review | | Implemented; runtime acceptance remains P9/P10; tests off |
| P3 | Results | Optional totals, lazy record sections, 25-entry pagination | SUCCESS | active_product_contract | Approved implementation plan; tests separately gated | root | registry.py; registry_api.py; static/registry.js; syntax parsing | | Additive contracts and lazy UI implemented; tests off |
| P4 | Cache | Bounded raw listing cache, refresh, single-flight and invalidation | SUCCESS | feature_implementation | Approved implementation plan; tests separately gated | root | listing_cache.py; storage.py; source race review | | Raw cache bounded and fenced; authorization runs outside it; tests off |
| P5 | Settings | Native audited global admin TTL and explicit initialization | ATTEMPTING_BUGFIX | config_or_startup_contract | Approved implementation plan; tests separately gated | root | cli/db.py; registry defaults; Admin UI | | Native initialization pending |
| P6 | Telemetry | Query/S3/cache/unfinished timing and bounded reads | SUCCESS | legitimate_safety_handling | Approved implementation plan; tests separately gated | root | performance.py; tapdb_backend.py; observability.py | | Bounded evidence and read failures implemented; runtime observation pending |
| P7 | Release | One immutable annotated numeric tagged release | SUCCESS | feature_implementation | Approved implementation plan; tests separately gated | root | 10.0.8 / ed74f512e499433d13e948ec2299b4cd30475646; annotated tag 9c5b5b72d61c20c4b720dbd538a8a442d8b2da0c | | Published exact source; CI skipped |
| P8 | Deployment | Final EC2 image and selected Dewey cutover | ATTEMPTING_BUGFIX | feature_implementation | Approved implementation plan; tests separately gated | root | Pending | | |
| P9 | Acceptance | Production stability and signed-in human acceptance | OPEN | active_product_contract | Approved implementation plan; tests separately gated | root | Pending | | |
| P10 | Performance | Comparable latency evidence and honest target disposition | OPEN | active_product_contract | Approved implementation plan; tests separately gated | root | Pending | | |

## Findings

At 16:56:34–16:57:49 EDT (20:56:34–20:57:49 UTC), `/api/v1/storage/browse` occupied approximately 75.6 seconds by proxy/application correlation. The native service duration is 75.429 seconds. Five requests from the other client for `/`, `/ui`, `/records/:id`, and `/storage` started during that interval and all returned at 20:57:49.644–20:57:49.649Z, immediately after browse returned at 20:57:49.640Z. Earlier, another browse took approximately 47 seconds and object requests queued behind it.

`dewey_service/app.py:3411` declares browse as `async def`, but line 3419 directly calls the synchronous service without awaiting a threadpool. `services/artifacts.py:608` enters `registry_browse`; `services/registry_storage.py:97` loops through every entry and performs authorization followed by registration lookup. `require_storage_access` constructs correlated permission predicates and loads policy children; `registry_access.py:162` includes inherited-prefix and denied-ancestor predicates. The GUI requests up to 100 entries. This creates repeated database work while preventing the event loop from serving unrelated users.

Live native telemetry at 21:05:28Z:

| Surface | Recorded evidence | Interpretation |
|---|---|---|
| S3 browse | 13 completed requests; p95 75.429 s | Severe backend browse latency |
| registry_browse database-session scope | 14 scopes; p95 73.759 s | Almost all slow-browse time is inside the per-entry session block; includes SQL and Python within that scope |
| Bucket list | 2 requests; p95 13.830 s | Another expensive authorized storage path |
| Shared login callback | 2 requests; p95 0.168 s | Login exchange itself was fast in the incident |
| Library search | Proxy 502 at 20:59:55Z and 21:00:51Z, about 300 s after arrival | Completed-app metrics omit the hung requests; query-level cause remains to be profiled |
| Database connectivity | Native probe 63.254 ms | Connectivity was responsive when sampled; does not clear expensive permission queries |

The role-dependent code is confirmed: admins bypass `require_storage_access` at lines 39–40 and `visibility_clause` at lines 215–217. The two clients are anonymized and not attributed to either named user or role. Previous September 19 performance acceptance measured an OWY service principal and compact Library/Set responses, not human-role S3 browsing. It cannot clear this incident.

## Concrete remediation scope

1. Make the synchronous browse handler a standard synchronous FastAPI route, or explicitly use the existing framework threadpool. This removes the event-loop stall without changing authorization.
2. Replace entry-by-entry storage policy and registration lookups with bounded batch reads and request-local reuse, preserving exact path, ancestor restrictions, visibility, counts, and pagination. Profile the Library visibility/count query under the affected verified role before choosing SQL/index changes.
3. Keep queued/unfinished and proxy timeout evidence visible in observability. The current HTML timing starts only once the event loop can run, and the app records completed requests; both can look healthy while users wait or the proxy times out.

No source implementation is included in this investigation. No performance-recovery claim is made. The isolated browser reached normal authentication but had no signed-in session; no credentials were entered and no synthetic principals or traffic were used.

## Historical investigation closeout

- All rows terminal: yes — 3 SUCCESS.
- Investigation objective complete: yes; main all-page stall has live and source evidence.
- Remediation/deployment/acceptance complete: no; not part of this investigation request.
- Production service, database, S3, permissions, and sibling services unchanged.
- No tests or load campaign run. Documentation/evidence review and scoped whitespace check only.

## Initialization attempt 1

The final-image native CLI invocation returned nonzero. The selected cutover failed closed before stopping 10.0.7 or replacing compose/manifest. Private failure receipt: /home/ubuntu/dewey-10.0.8-20260923T215039Z/deployment/deployment-receipt.json; initialization stderr retained beside it. Diagnosing the native command; no raw database fallback.

## Runtime integration correction

Native initialization failed with `'RuntimeDBConnection' object has no attribute 'engine'` before any configuration initialization or cutover. Cause: the new telemetry setup assumed the low-level TapDB connection API instead of Dewey's actual web.runtime wrapper. Source inspection confirmed the wrapper exposes scoped SQLAlchemy Sessions; correction installs listeners once on `session.get_bind()` under a lock. No raw SQL/data workaround or wrapper internals used. 10.0.8 remains immutable and undeployed; 10.0.9 is the replacement final deployment candidate and requires another EC2 build. No rebuild occurred on the laptop, no tests ran, and no sibling/production replacement occurred. Actual first final build completed 21:50:39–21:52:08 UTC (~89 seconds); billing/token amounts unavailable.

## Initialization attempt 2 and identity correction

10.0.9 completed its EC2 build at 21:56:46Z (started 21:55:17Z; ~89 seconds). Native initialization failed at 21:57:59Z with `identity_key must start with a lowercase ASCII namespace followed by ':'`. The invalid key was inherited from the previous defaults-update path. The native factory source establishes the exact namespace contract. Corrected the owning CLI to `dewey:registry-service-defaults`; no fabricated EUID, alternate data path, configuration change, or privilege expansion. Production has no configured tenant ID; the native write policy explicitly allows tenant-null rows for its tenant-null principal, so its existing `allow_global_claims=false` remains untouched. Both failures are saved in `initialization_failures.json`; the 10.0.9 build receipt is `image_10.0.9.json`. Both tags remain immutable. 10.0.10 supersedes the undeployed 10.0.9 candidate; another final EC2 build is necessary. Costs and token billing unavailable.
