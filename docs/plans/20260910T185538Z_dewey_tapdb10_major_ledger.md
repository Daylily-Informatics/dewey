# Dewey 9: production-preserving upgrade to TapDB 10.1.0

Controlling plan and execution ledger. Approved by the user in the implementation request on 2026-09-11. Execution began 2026-09-11T03:47:50Z.

**Execution paused by the user at 2026-09-11T04:23:30Z.** Actual source capture is blocked by the immutable 10.1.0 identity-receipt limit. The user will have a separate agent make and publish TapDB changes; this task performs no upstream work or automatic resumption. See the [release handoff](20260911T042330Z_tapdb_release_handoff.md). The exact Dewey dependency remains 10.1.0 in the saved work until a published replacement is explicitly verified and recorded on resumption. Active role D was interrupted; its unfinished local edits are preserved.

## Objective and approved decisions

Replace production `https://dewey.day.lsmc.bio` with Dewey **9.0.0**, released through **main**, pinned to **daylily-tapdb[aurora,gui]==10.1.0**. Use the verified live Dewey implementation as the controlling source boundary. Preserve all production data, UID/EUIDs, prefixes, domain/tenant/issuer identities, lineage, creation identity and strictly increasing sequence allocation. No runtime backward compatibility, shims, fallback paths, silent target discovery or reminting.

Use a **replacement Dewey database**, **planned outage sized by rehearsal**, and separate migration and independent acceptance agents. Preserve undeployed branch work for Phase 2. No new TapDB release is in scope; a missing or failing required capability in immutable 10.1.0 is a blocker, not permission to patch the package or change versions.

| Release field | Approved value |
|---|---|
| Dewey release | 9.0.0 on main |
| TapDB package | daylily-tapdb[aurora,gui]==10.1.0 |
| TapDB commit | 9db1abb4525f2594ebdbf2a307eb8b49aa51883d |
| TapDB annotated tag object | d8d36584a5338d7256aba0300d299d53a5c12217 |
| Published wheel SHA-256 | f46cb2abfccb3000b9f9443ea00045e83fb96f6b320d2aeac0ad800ea47e8801 |
| Python | >=3.12 |
| Meridian EUID | 0.4.8 |
| Source database | dewey_prod |
| Replacement database | dewey_prod_tapdb10; fail if it already exists |
| Preserved schema | tapdb_dewey_lsmcok1_local |
| Preserved production domain | M |
| Aurora | dayhoff-lsmcok1-tapdb, us-west-2 |
| Production host | i-07df3a933e4839f52; SSM interactive ubuntu only |

TapDB 10.1.0 publication was verified during planning. Its CI/formal review were waived, not passed; independent acceptance was user-attested. Do not reopen those accepted upstream release gates or misstate them as witnessed tests. Dewey-specific adoption, data migration and production acceptance remain required. Released tools now own former prerequisite development rows.

## Agent ownership and operating rules

| Agent | Model | Effort | Exclusive responsibility |
|---|---|---|---|
| O | gpt-6-astra | max | Coordinator, ledger, integration, production operator and final acceptance |
| A | gpt-6-astra | xhigh | Source reconciliation, main merge boundary, undeployed work preservation |
| B | gpt-6-astra | max | Published TapDB qualification, native inventory/allocator/principal/recovery contracts |
| C | gpt-6-astra | max | Data manifests, replacement migration and recovery rehearsal |
| D | gpt-6-astra | xhigh | Dewey API/config adaptation, exact pin, compatibility removal |
| E | gpt-6-astra | max | Independent PostgreSQL, authorization, identity and application acceptance |
| F | gpt-5.6-sol | high | Full image build/provenance and Dewey-only deployment |
| G | gpt-5.6-sol | high | Separate Phase 2 PR and feature work |

At most three subagents plus O run concurrently. Use separate worktrees and disjoint write scopes. O alone updates this ledger and integrates changes; agents report owned-row changes, files, commands, results, blockers and risks. E must not author the migration it qualifies. O is the only live operator. Do not create scheduled tasks/automations. Preserve all existing user worktrees and dirty changes.

## Gate 0 baseline

- Controlling worktree: `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-tapdb10-major-20260910`.
- Branch: `codex/dewey-tapdb101-major-20260910`, created from deployed `556dfcf936ea11e25f6126931fe1f655482d00a6`.
- Source worktree `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-qeo-resolver-20260909` is clean at `598be4d5f31525e982de01b36a284704fa603042`. Its application matches deployed commit `556dfcf`; the later commit also changes a deployment helper, so it is not receipt-only. A preserves its documentation separately and excludes that later helper change from the live-source baseline.
- Live remote main: `ef7f5412b5c7a4d3a8c47fb55500fa66f165b0ca`; live resolver ref `598be4d5f31525e982de01b36a284704fa603042`; no remote `9.0.0` tag on execution start.
- Fresh HTTPS health 2026-09-11T03:47:17Z: Dewey 8.0.2, process started 2026-09-10T00:41:05Z, status ok, build SHA blank. SSM Online for the expected host.
- Prior planning inspection (to refresh): image `sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f`, OCI revision `556dfcf936ea11e25f6126931fe1f655482d00a6`; all 73 application/lock blobs matched Git; no application writable-layer changes; TapDB9.0.9/Meridian0.4.7; strict schema drift clean with9 tables/20 sequences.
- Baseline checks pending: fresh runtime manifest, complete source identities and prefix/sequence states, principal inventory, writer inventory, source tests, published package installation and target absence.
- Gate 0 remains incomplete until L00/L02/L03 evidence is captured. Twenty prior sequences is not a hardcoded scope limit.

## Native interfaces and data contracts

All commands use `tapdb --config ABS`; global `--json` precedes command groups. Use the immutable10.1.0 `docs/service-readiness.md` and owning CLI help for exact arguments. Stale candidate-publication prose in tagged docs is superseded by release receipts.

| Purpose | Released CLI |
|---|---|
| Historical source/identity inventory | db identity inventory |
| Preservation comparison | db identity verify |
| Receipt-bound advancement | db sequences advance |
| Strict floor verification | db sequences verify |
| Ambiguous or stalled intent recovery | db sequences reconcile |
| Offline/CONNECT-only preparation | db runtime-principal bootstrap |
| Final privilege and scope binding | db runtime-principal bind |
| Backup/recovery | backup plan/create/verify/restore-plan/restore |
| Schema migration | db schema migrate |

- Source contracts declare the observed installed source version and verified catalog allocator mappings; no implicit initialization or allocation during inventory.
- One sealed immutable recovery family covers source and every planned replacement journal. Preserve every root and head anchor; never hand-edit a receipt or infer related directories.
- Native fencing requires a different explicit control database, verified provider identity, reviewed writer/fence/quarantine evidence and durable external journals.
- Restore purposes are `isolated_rehearsal` for rehearsal and `fenced_source_recovery` for production recovery; `fenced_migration` is not a restore purpose.
- Retain identical reviewed plan fingerprint, source/fence/control/provider evidence and physical destination for apply. Every restoration requires explicit runtime rebinding.
- Protect database backups and external recovery artifacts: configs, domain/prefix registries, TLS/IAM references, principal-state inventory, secret recovery mechanisms, images/runtime files, journal roots and acceptance evidence. Never put secrets, PII/PHI or unredacted data in Git or output.
- Do not use partial legacy backup commands, direct dump/restore/SQL shortcuts, private APIs, old Dewey bootstrap or automatic template overwrites.

Preserve every original UID/EUID, stored prefix/domain, machine UUID, tenant/issuer/creation identity and lineage endpoint. Include soft-deleted records, dormant prefixes, audit, outbox/inbox, idempotency, shares, memberships and all application tables. Preserve existing DGX business objects and historical DGX template bindings; do not substitute TPX. Native typed external references plus lineage own relationships; incidental metadata must not become authority. A reviewed conversion manifest lists only permitted non-identity transformations. Refuse undeclared differences and reminting.

For every generator freeze initial source, final fenced source, assigned/reserved values, target state immediately before advancement and previously exposed recovery floors. The first resumed allocation must be strictly greater than every applicable floor, including the previously available source next value. Preserve increment alignment, ownership, dependencies, bounds and cache semantics. Unknown mappings, unsupported cache state, cycling, nonpositive increments or exhaustion block migration. Capture new migration generators too. Close old allocator sessions/pools. Retain aborted/probe/migration allocations conservatively; no identifier reuse during recovery.

## Dewey/runtime implementation

- Pin and lock exact10.1.0; validate installed version. Port removed DAG interfaces to supported DAGv2 and current GUI APIs.
- Preserve live QEO resolver, complete package registration and container CLI.
- Keep schema migration, seeding and principal preparation outside application startup. Deploy with `verify_existing` and a complete newly built image, not an overlay on TapDB9.
- Bootstrap grants only the configured constrained runtime login and CONNECT. Final bind follows restoration, schema migration, service conversion and identity/floor verification.
- Review database-wide PUBLIC/runtime TEMP revocations and any explicit operator-preservation grants; no unreviewed sibling-role effects or cascading grants.
- Close and recreate every runtime session after binding. Fresh sessions must use the intended role, have effective TEMP=false and reject forbidden DDL.

## Control ledger

Working states: OPEN, IN_PROGRESS, ATTEMPTING_BUGFIX. Terminal: SUCCESS, DUPLICATE, NO_LONGER_NEEDED, FAIL, BLOCKED. FAIL requires a documented bugfix attempt; BLOCKED requires exact cause/unblock condition. All rows terminal is distinct from objective completion. Phase2 is a separate ledger.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| AM01 | Plan | Fix10.1.0 target; qualify released capabilities rather than develop/release TapDB | SUCCESS | plan_amendment | User implementation approval | O | Approved plan committed as 5c75e7b | | Exact target and released-capability qualification recorded; no upstream development/release authorized |
| L00 | Inventory | Refresh source/image/config/database identity and release artifacts | IN_PROGRESS | legitimate_safety_handling | Gate0 | O/A | Fresh health, refs and SSM container inspection match the approved baseline | | |
| L01 | Source | Reconcile verified live source onto release branch targeting main, exclude undeployed features | IN_PROGRESS | feature_implementation | L00 | A | A confirms main contributes five documentation/evidence files; normal merge preserves live application | | |
| L02 | Native inventory | Capture old Dewey schema and mappings using published10.1.0 | BLOCKED | contract_test | L00 | B/O | [Actual-source failure](20260911T041429Z_dewey_native_inventory_blocker.md); native exit 2, no receipt produced | Immutable 128 MiB cumulative identity evidence limit; no supported override | Requires a separately released qualified capability and explicit target amendment; user paused while another agent handles TapDB |
| L03 | Source evidence | Complete identities/prefixes/roles/writers/all generators; finish Gate0 | BLOCKED | legitimate_safety_handling | L02 | C/O | Native source capture stopped before sequence capture; no complete census exists | L02 capacity failure; separate native principal/writer census gap | Resume after upstream release and explicit plan amendment; no claimed floors or source manifest |
| L04 | Native lifecycle | Qualify strict advancement, fencing, bootstrap/bind and journal recovery | IN_PROGRESS | contract_test | L02 | B/E | B reports 301 focused tests passed on PostgreSQL 16.13 against the installed public package; actual Dewey qualification pending | | |
| L05 | Historical recovery | Qualify published package and historical backup/restore/migration for Dewey | BLOCKED | contract_test | L04 | B/E | Existing 301 native tests include historical 9.0.9 fixtures; actual Dewey recovery reuses the failing capture | L02 capacity failure | Fixtures do not qualify actual Dewey capacity; preserve existing passing receipts |
| L06 | Dewey runtime | Exact10.1.0 lock/public API adoption and mutation-free startup | IN_PROGRESS | feature_implementation | L01/L05 | D | Partial edits in dewey-implementation-20260911, exact package installed/lock updated; interrupted on user pause | Acceptance depends on L05; local work not yet integrated or independently accepted | |
| L07 | Compatibility | Remove owned compatibility/fallbacks; prove explicit failures | IN_PROGRESS | removable_compatibility_debt | L06 | D/E | Partial removals and affected-test updates preserved in D's worktree; no additional tests on pause | User pause; L06 not closed | |
| L08 | Data conversion | Reviewed non-identity transformations and complete preservation manifest | BLOCKED | feature_implementation | L03/L05 | C | Preparation commit 7ff8bc7; offline review helper and native runbook; 16 focused tests passed | Complete actual source contract unavailable from L02 | No conversion manifest or source identities fabricated; preparation branch retained |
| L09 | Rehearsal | Timed isolated full restoration, migration, floors and recovery | BLOCKED | contract_test | L08 | C/E | Runbook prepared; no restoration performed | L02/L08 capacity and source-evidence gate | Rehearsal and its exact-effect approval remain future work |
| L10 | Independent acceptance | PostgreSQL/auth/concurrency/application/restored-data acceptance | OPEN | contract_test | L06-L09 | E | Pending | | |
| L11 | Release | Merge main normally, annotated9.0.0 tag, full immutable image | OPEN | feature_implementation | L10 | F/O | Pending | | |
| L12 | Production gate | Exact targets/control/config/image, timed outage, required destructive confirmation | OPEN | legitimate_safety_handling | Production | O/C/F | Pending | | |
| L13 | Cutover | Fence, fresh backup/restore, migrate, verify identities and strict floors | OPEN | feature_implementation | L12 | C/F/O | Pending | | |
| L14 | Deployment acceptance | Bind, recreate sessions, authenticated reads and controlled writes | OPEN | contract_test | L13 | E/O | Pending | | |
| L15 | Closeout | Terminal counts,60minute observation, recovery evidence and objective disposition | OPEN | legitimate_safety_handling | L14 | O | Pending | | |

## Qualification and production procedure

Required tests: actual populated observed9.0.9 to10.1.0 on matching PostgreSQL/Aurora; full identity/prefix/relationship preservation; is_called true/false, nonunit increments, reserved/cache allocations, stale receipts, exhaustion/restart/concurrency; separate-session tenant/replay/conflict/privilege/TEMP denial; artifact/run/search/share/download/manifest/QEO workflows; authenticated Dewey and embedded TapDB GUI/DAG; explicit config/version/malformed/unavailable failures; complete project tests/lint/security/locked-install/build/image smoke; lost acknowledgement and recovery without reuse or loss of accepted writes. Native tests are prerequisites, not Dewey acceptance.

1. Restore isolated production data with outbound mutations and dispatch disabled; measure migration and recovery time.
2. Retain original database/image and complete protected recovery set; record maintenance window and exact commands.
3. Stop/fence every Dewey writer, worker, consumer, dispatcher, scheduler, operator and pool; preserve pending and acknowledged work.
4. Capture fresh final source contract/allocators/backup after fencing; rehearsal data is not final capture.
5. Restore the exact fresh replacement, migrate/convert, advance and verify all identities/floors.
6. Bind replacement runtime principal, recreate sessions and verify role/TEMP/DDL confinement.
7. Switch only Dewey image and explicit database/runtime config; preserve sibling services, cluster identity, DNS and existing data-object locations.
8. Accept authenticated reads and controlled write allocations before normal writers resume; observe60minutes including registration/replay/QEO package checks.
9. Record exact versions/image/receipts/floors; retain source database without automatic deletion.

Before new writes, recovery to old source requires its allocators to exceed all cutover allocations. After accepted writes, prefer repair forward; any return to Dewey8 requires preserving/reconciling those writes. Image-only rollback is insufficient. Ambiguous operations retain journals/fences and require native reconciliation before retry; observed-only is not proof of commit.

Destructive restore/reset/delete retains a second explicit confirmation after exact effects/targets are presented. Initial implementation approval is not that second confirmation. Old database deletion and unrelated service changes are excluded.

Phase2 starts only after Phase1 acceptance: refresh prior Dewey PRs1-5 against the new lock, document supersession, and use a separate ledger for remaining PRs/new minor-feature requirements. Undeployed Labcore/branch features remain outside this migration.

## Execution log

| UTC | Action | Evidence/result |
|---|---|---|
| 2026-09-11T03:47:50Z | Created isolated worktree and exact-source branch | git worktree add from556dfcf; existing clean resolver checkout preserved |
| 2026-09-11 | Committed controlling plan and dispatched A/B/C | Commit 5c75e7b; disjoint source, native qualification, and migration preparation scopes; O owns production and ledger |
| 2026-09-11 | Refreshed live container identity over interactive SSM as ubuntu | Container 872434f05303; image sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f; OCI revision 556dfcf; three expected mounts; no production mutation |
| 2026-09-11 | Received B's focused native qualification result | 301 passed, zero failures/errors/skips, PostgreSQL 16.13; actual source and Aurora acceptance remain open |
| 2026-09-11 | Integrated A's source reconciliation | Normal merge ca77fae preserves main ancestry and deployed source; undeployed branch work retained |
| 2026-09-11 | Installed separate EC2 operator tools and generated native operator config | Exact public wheel/hash verified; original live container/config unchanged; setup failures retained |
| 2026-09-11 | Ran actual-source inventory once; retained terminal result | Native identity_inventory_error: Identity receipt exceeds the declared size bound; exit 2 recovered from the unchanged tmux shell status; no source/allocator receipt |
| 2026-09-11T04:23:30Z | User paused and assigned TapDB release to another agent | D interrupted; B/C completed; no further implementation, tests, migration, release or automatic continuation; handoff prepared |

## Final disposition

All rows terminal: no. Objective complete: no. Execution: paused by user. Production data, allocators, privileges, running application and deployment configuration changed: none. A separate protected operator environment/config was created on EC2. D's partial local edits and C's committed preparation branch are preserved for resumption. No Dewey 9 tag/image/release/cutover or Phase 2 work has occurred.
