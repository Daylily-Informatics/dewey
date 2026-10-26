# Dewey 12.0.0 sharing release — execution ledger

## Current continuation state

- Objective: implement SHR-01–SHR-20 and release Dewey 12.0.0 plus additive Login 4.1.0 to `dewey.day.lsmc.bio`, with the dedicated public recipient ALB. Stop only when required functionality, running provenance, bounded acceptance, and unchanged sibling-service evidence are established; terminal blocked rows do not establish success.
- Authority: user explicitly said “PLEASE IMPLEMENT THIS PLAN” and supplied the complete plan on 2026-10-26 UTC. This authorizes the scoped source changes, dedicated ingress, preserving schema-3 conversion, final EC2 builds, selected-service deployment and bounded acceptance. Prior planning answers confirmed bounded changed-code tests twice and permitted additive Login changes. No PR, branch merge, full main CI, unrelated service/shared-library changes, physical S3 move/delete, or destructive cleanup is authorized.
- Repositories: Dewey `/Users/jmajor/projects/dewey-sharing-docs-20261025`, branch `codex/dewey-sharing-review-20261025`, remote `Daylily-Informatics/dewey`, baseline HEAD `34b0e5697d9c1920909dd54a24ed96ac72d71034` (clean); Dayhoff `/Users/jmajor/projects/lsmc/dayhoff`, initially clean main; Login valid checkout to be created from deployed 4.0.5. Old/broken worktrees remain untouched.
- Baseline from planning: Dewey 11.0.10 / `7f6fde5429741780517cf461a615e5b3e5f102f2`; Login 4.0.5 / `d3d76d9f1eb91a8e8f7ede73c37ca93b172ec258`. Fresh execution inventory pending. Target EC2 `i-07df3a933e4839f52`, region `us-west-2`; all EC2 operations through interactive SSM as ubuntu. No laptop container builds.
- Constraints: preserve every unselected image/config; Dewey auth 2.1.5, Login auth 2.1.9, TapDB 11.0.9 unchanged. Existing Cognito pool/client/provider/confirmation/recovery settings unchanged. Only explicit share invitations use new SES delivery. No automatic domain tenant admission.
- Completed: accepted plan and source baseline recorded; documentation packet from prior task remains historical baseline. No implementation or runtime change yet.
- Next: commit this ledger, refresh source/runtime Gate 0, assign disjoint worker write scopes, implement approved contracts. Evidence root: `docs/plans/evidence/20261026_dewey12/`. Tests use controlled fixtures and explicit nonproduction database only; missing credentials/fixtures become explicit blockers, not substituted production targets.

## Accepted design and boundaries

1. **Authority and lifecycle:** creator delegation checks; recipient share grant sufficient without underlying recipient ACL. File/fixed-set/live-prefix scopes; pending/mixed emails; named recipients or Public with registration; never anonymous. Thirty-day default, explicit null expiry, finite credentials. Atomic revisioned target/recipient/filter/expiry edits; stable EUIDs/history; no object deletion for unsharing. Native schema 3 and typed lineage.
2. **Identifiers:** `/fetch/<share-euid>[/<relative-path>]`; single file at root, single prefix preserves paths, multiple roots namespace by persisted target EUID. Slugs: global atomic claims, lowercase ASCII letters/digits/hyphens, 3–63 characters, reserved control/EUID namespace, explicit conflict, native alias lineage, no reassignment and permanent tombstones.
3. **Delivery:** authenticated GET/HEAD/Range/conditions; browser deep-login return and machine 401. Complete paginated manifest (`?format=manifest`), recursive resumable CLI, streaming uncompressed TAR (`?format=tar`) after complete inventory. Version/conditional source reads; abort changed/missing content; TAR restarts. Every request and archive member checks current policy. An admitted individual-file response may finish. Stop raw S3 presign issuance; retain existing durable share pages as authenticated entrypoints; removed payloads/modes fail explicitly.
4. **WWW:** exact bundle/entrypoint; durable fetch page starts existing isolated per-context content-host viewer. Every sidecar authorized; no report script execution in application origin.
5. **Identity:** additive Login `/auth/share`, verified share-only guests, no automatic organization access. Private Dewey introspection checks provider revocation plus current enabled/verified email. Login stores encrypted provider grants; opaque binding to Dewey, positive cache at most 60 seconds. Personal credentials finite and individually revocable. SES for explicit invitations with accepted/failed/uncertain receipts. Existing Cognito default-email quota remains, failures retain pending grants and return path without resend loops.
6. **Audit/rebind/interfaces:** native lifecycle/access history, authorized aggregate reports with coverage/watermarks and precise server-versus-client metrics. Audited destination-equivalent storage-reference revision preserves identities/paths; collision/mismatch fails; no physical storage move/delete. Management API/GUI and CLI parity, README/schema/help updated.
7. **Ingress:** dedicated ALB HTTPS 443, certificate for exact Dewey/Login and isolated content wildcard; selected origin private listeners 8443 recipient and 8444 trusted management. Preserve shared 443, existing SGs, tailnet and container backchannels. Exact private DNS zones for Dewey/Login and public aliases to ALB. Exact route/method/host allowlist, verified public_recipient role, strip incoming assertion headers; port conflict fails. No broad sibling exposure.

## Gate 0 and ownership

Required inventory: repository status/HEAD/remotes; runtime image digests and container identities/restarts; selected live config hashes and source labels; complete same-deployment release manifest; current schema/share/grant/history inventory; current ingress/DNS/SG/Cognito identities; explicit test DSN and controlled acceptance identities. Never put secrets, personal addresses, production data payloads or OAuth tokens in evidence.

Worker ownership is disjoint and phase-specific. Lead alone commits/tags/pushes, runs integrated tests, mutates production, and maintains this ledger. Workers report exact files, contracts, focused test commands and evidence; they do not edit the ledger concurrently.

- **A / core:** `services/sharing.py`, `services/share_policy.py`, native claim/model helpers, new schema/migration/rebind/report modules and their focused tests. Do not edit shared registry API, auth, UI, CLI or release files.
- **B / delivery:** gateway/fetch/manifest/archive/report modules and focused tests; GUI and CLI in wave 2 after explicit handoff. Do not edit core sharing policy, auth or shared registry API without lead coordination.
- **C / identity/ingress:** Login repo and Dewey identity integration files agreed with lead; scoped Dayhoff ingress module in wave 2. No AWS/runtime mutation, images or commits; lead operates deployment.
- **Lead:** shared API/schema routing, configuration integration, locks/version/CI, release tooling, documentation, ledger, Gate 0 and production operations.

## Tracking table

| ID | Area / requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|
| G0 | Source/runtime/config/fixture/migration baseline | IN_PROGRESS | config_or_startup_contract | 0 inventory | Lead | Initial clean Dewey HEAD recorded above | — | — |
| CORE | SHR-01–06,19: policy/revisions/lifetime/targets | OPEN | feature_implementation | 1 contracts | A | — | — | — |
| ALIAS | SHR-08: atomic slug claim/lineage/tombstone | OPEN | feature_implementation | 1 contracts | A | — | — | — |
| IDENTITY | SHR-03,06,12–13: onboarding/introspection/SES | OPEN | feature_implementation | 1 contracts | C | — | — | — |
| FETCH | SHR-07,09,18–19: stable authenticated HTTP | OPEN | feature_implementation | 1 contracts | B | — | — | — |
| TREE | SHR-10,19: complete manifests/TAR/recursive client | OPEN | feature_implementation | 1 contracts | B | — | — | — |
| WWW | SHR-11: deep report entry/isolated sidecars | OPEN | feature_implementation | 1 contracts | B | — | — | — |
| REBIND | SHR-17: audited equivalent storage-reference change | OPEN | feature_implementation | 1 contracts | A | — | — | — |
| AUDIT | SHR-15–16: precise events/aggregate/export | OPEN | feature_implementation | 1 contracts | A | — | — | — |
| INTERFACES | SHR-18,20: API/GUI/CLI/docs parity | OPEN | feature_implementation | 2 integration | Lead/B | — | — | — |
| INGRESS | SHR-14: dedicated restricted public ALB/TLS/DNS | OPEN | config_or_startup_contract | 3 cutover | C/Lead | — | — | — |
| MIGRATE | Preserve EUIDs/grants/scope/lifecycle/history | OPEN | active_product_contract | 3 cutover | A/Lead | — | — | — |
| VERIFY | Changed-code + isolated PostgreSQL integrated pass | OPEN | contract_test | 2 integration | Lead | Approved bounded scope in user implementation request | — | — |
| RELEASE | Immutable tags/final EC2 images/scoped deployment | OPEN | config_or_startup_contract | 3 cutover | Lead | — | — | — |
| ACCEPT | Bounded live journeys/provenance/sibling invariance | OPEN | contract_test | 4 acceptance | Lead | — | — | — |

Allowed working states: OPEN, IN_PROGRESS, ATTEMPTING_BUGFIX. Terminal states: SUCCESS, DUPLICATE, NO_LONGER_NEEDED, FAIL, BLOCKED. FAIL requires a documented bugfix attempt; BLOCKED/FAIL require root cause and next action. Every required requirement must actually be satisfied before claiming objective complete.

## Validation and release gates

- One integrated explicit changed-code test selection, plus one isolated PostgreSQL contract group for claims/revisions/lineage/migration. No production DSN. Focus on verified identity, concurrent edits/claims, null/finite expiry, HTTP/path handling, pagination/source change, report isolation, rebind equivalence, preservation and audit totals. Only affected/failing cases repeat after new changes.
- Narrow Dewey full-suite CI to main pushes and PR-main; no unrelated suites/lint/coverage, no full main CI before later PR. Login has no checked-in Actions trigger at baseline.
- Commit/push and annotate tags 12.0.0 and 4.1.0; verify remote peeled commits. Build only final intended tagged images on target EC2 using complete base manifest. Selected pins/provenance helper only; retain all sibling digests. No intermediate/local/all-service build.
- Deploy additive Login first. Fence sharing writes, drain delivery, digest-recheck/apply/reconcile migration, then selected Dewey compose update with verify_existing. Never rerun historical retirement migration or force-kill streams. Public DNS activation follows route-boundary verification.
- One bounded live acceptance on controlled non-sensitive identities/data, including external network, registration/deep return, private and public-registered access, curl/wget, recursion, MultiQC assets, edits/revoke/rebind/report reconciliation; read-only compare sibling identities/digests/restarts.
- Record expiry window for already issued raw presigns; do not claim recall. Before incompatible conversion, old image/config rollback is valid. After schema 3/new writes, fence and repair forward or separately review restoration preserving intervening data/history. Never image-only rollback to an incompatible schema.
- Finish with committed/pushed sanitized receipts and terminal counts, distinguishing source, running deployment, functional acceptance and user acceptance. Later PR/merge/full-main-CI are outside this release authority.

## Evidence and chronology

- 2026-10-26: User explicitly approved execution of the complete plan. Initial Dewey and Dayhoff statuses clean. Applicable exposure restrictions are superseded only for the exact approved recipient ingress; broad sibling exposure remains prohibited. Existing general no-tests policy is superseded only by the twice-confirmed bounded scope and this explicit implementation request.
