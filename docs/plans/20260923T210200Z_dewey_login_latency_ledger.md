# Dewey signed-in latency investigation — 2026-09-23

## Current continuation state

Updated: 2026-09-23T21:08Z. Objective: investigate the user-reported immediate degradation across all Dewey pages after two human users signed in; identify the cause and concrete remediation. Investigation complete; stop at diagnosis. Remediation is recommended and has not been performed.

Authority: current user request authorizes investigation. Read-only production observations and local evidence records are in scope. No tests, load campaign, service mutation, restart, build, release, deployment, data changes, or scheduled monitor requested. Preserve unrelated work.

Identities: service https://dewey.day.lsmc.bio; AWS profile lsmc, us-west-2, instance i-07df3a933e4839f52 (live verified running t3.2xlarge, Dayhoff-day-Compute/Hostprimary); container dayhoff-day-dewey-1. Live health identifies 10.0.7 / 8d04719a6ad82a6808bf38933b39cadb210b43d0. Owning checkout /Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-gui-performance-20260919, branch codex/dewey-gui-performance-20260919, clean baseline eaf9754. Tag 10.0.7 is annotated and peels to live SHA.

Completed: health request at 21:00:20Z returned 200 in 0.321 seconds. Host at 21:00:56Z load 0.23/0.65/0.93; available memory 23,015 MiB of 31,719; root filesystem 94% used, 63 GiB available. These do not establish signed-in GUI health. Prior 20260919 performance evidence used the OWY service principal and explicitly did not establish human-role/browser performance.

Confirmed: S3 browse performs synchronous S3/database work directly in an async route on one running Python server process. Native endpoint telemetry records browse p95 75,429.446 ms; its per-entry database-session work records p95 73,759.059 ms. Existing proxy/app logs show another client's five page requests delayed 51.6–56.6 seconds and completing within 9 ms after that browse completes. This establishes the shared event-loop stall. Per-item authorization and registration queries explain the expensive browse path; admin short-circuits part of this work. No human identity/role was inferred from client labels.

Also confirmed: two Library searches started 20:54:55Z and 20:55:51Z and received proxy 502 after approximately 300 seconds. They are absent from completed application rollups. Their exact SQL plans remain unprofiled. Successful health/login/HTML timings do not establish availability during a stalled browse.

Next action if remediation is requested: move browse's blocking work off the event loop, batch its authorized storage/registration lookups, and inspect the non-admin Library visibility query path. Preserve all permission semantics. No tests, builds, release, deployment, restart, or data changes performed.

Evidence: `evidence/20260923T210200Z_dewey_login_latency/` contains sanitized request correlation, live native telemetry, runtime/source-hash receipt, and the read-only correlation script. Six live source hashes match the local 10.0.7 implementation. All investigation rows are terminal SUCCESS. This does not mean service remediation or acceptance is complete.

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

## Closeout

- All rows terminal: yes — 3 SUCCESS.
- Investigation objective complete: yes; main all-page stall has live and source evidence.
- Remediation/deployment/acceptance complete: no; not part of this investigation request.
- Production service, database, S3, permissions, and sibling services unchanged.
- No tests or load campaign run. Documentation/evidence review and scoped whitespace check only.
