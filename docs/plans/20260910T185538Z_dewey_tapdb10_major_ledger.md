# Dewey 9: production-preserving upgrade to TapDB 10.1.1rc1

Controlling plan and execution ledger. Approved by the user in the implementation request on 2026-09-11. Execution began 2026-09-11T03:47:50Z.

**Execution resumed by explicit user instruction on 2026-09-11; amendment recorded at 2026-09-11T05:17:31Z.** The user authorized `python -m pip install 'daylily-tapdb==10.1.1rc1'`. This exact prerelease supersedes the former 10.1.0 target. Its public wheel and annotated tag were independently verified, and the isolated EC2 operator environment now runs it. Production remains Dewey 8.0.2 / TapDB 9.0.9. The earlier pause at 2026-09-11T04:23:30Z and [release handoff](20260911T042330Z_tapdb_release_handoff.md) remain historical evidence; new source capture and Dewey acceptance must qualify the fix before the capacity blocker is closed.

**Actual RC capture and mapped recapture succeeded.** Native capture retained 79,918 rows across nine tables and all 20 generators. The mapped recapture completed at 05:48:23Z in 65.926 seconds; all four dormant mappings are source-backed and independently accepted, no generators remain unmapped, and the identity digest is unchanged. An earlier claim that missing automatic source quarantine required another TapDB release is withdrawn. AM03/AM04 record the supported maintenance/copy SOP with native target fences; no production writer has been stopped and no database has been changed.

**AM04 supersedes backup/restore execution with a direct database copy.** The user explicitly said the Aurora cluster is already backed up and instructed this task not to back it up again. No new logical backup, Aurora snapshot, checkpoint backup or backup-as-export is permitted. Use the existing Aurora recovery protection and preserve the original database. A documented one-time `CREATE DATABASE ... TEMPLATE ...` operation copies the quiescent Dewey database within the same ordinary Aurora cluster; native TapDB inventory, identity comparison, migration, advancement, binding and reconciliation remain the acceptance interfaces. PostgreSQL client download preparation has stopped; no backup was created and no client package was installed into the host.

**AM06 waives inbox/outbox message retention.** The user explicitly permits loss of any inbox/outbox messages and will resend from the owning systems if needed. Queue preservation, acknowledgement reconciliation and message replay are no longer migration/cutover gates. No intentional purge is requested. Existing messages may copy naturally; all other data/identity preservation and every generator's strict floor requirements remain in force. This direction supersedes earlier queue-retention language in the plan and agent preparation notes.

## Objective and approved decisions

Replace production `https://dewey.day.lsmc.bio` with Dewey **9.0.0**, released through **main**, pinned to **daylily-tapdb[aurora,gui]==10.1.1rc1**. Use the verified live Dewey implementation as the controlling source boundary. Preserve all production data, UID/EUIDs, prefixes, domain/tenant/issuer identities, lineage, creation identity and strictly increasing sequence allocation. No runtime backward compatibility, shims, fallback paths, silent target discovery or reminting.

Use a **replacement Dewey database**, **planned outage sized by rehearsal**, and separate migration and independent acceptance agents. Preserve undeployed branch work for Phase 2. No upstream TapDB development or release is in scope for this task; a missing or failing required capability in immutable 10.1.1rc1 is a blocker, not permission to patch the package or change versions. Do not automatically select a stable or newer release.

Prefer safe, reviewable operator SOPs for infrequent migration/setup requirements, as explicitly directed by the user. Missing automation is not itself a blocker. Preserve all data/identity/floor guarantees and use released native validators; seek another TapDB release only if no safe released-tool/SOP path can satisfy a required guarantee.

| Release field | Approved value |
|---|---|
| Dewey release | 9.0.0 on main |
| TapDB package | daylily-tapdb[aurora,gui]==10.1.1rc1 |
| TapDB commit | 02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c |
| TapDB annotated tag object | 1ac2f09a1787b9e747eda582c45a628ca60b7020 |
| Published wheel SHA-256 | 26de691dd5f9c8fac596a18119c9220f4ea78826094753b47f9eb936b0677ce7 |
| Published sdist SHA-256 | abf2e5b18184db736c8e54fb77cbc96e78c77921f0f65b7c8f026ebb20a8a5fb |
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

All commands use `tapdb --config ABS`; global `--json` precedes command groups unless the owning command explicitly requires command-local JSON. Use the immutable 10.1.1rc1 `docs/service-readiness.md` and owning CLI help for exact arguments. Stale candidate-publication prose in tagged docs is superseded by release receipts.

| Purpose | Released CLI |
|---|---|
| Historical source/identity inventory | db identity inventory |
| Read-only database, principal and session census | db census |
| Preservation comparison | db identity verify |
| Receipt-bound advancement | db sequences advance |
| Strict floor verification | db sequences verify |
| Ambiguous or stalled intent recovery | db sequences reconcile |
| Offline/CONNECT-only preparation | db runtime-principal bootstrap |
| Final privilege and scope binding | db runtime-principal bind |
| Existing backup/recovery qualification | Historical evidence only under AM04; no new backup/create/restore workflow is planned |
| Schema migration | db schema migrate |

- Source contracts declare the observed installed source version and verified catalog allocator mappings; no implicit initialization or allocation during inventory.
- No family or journal has yet been created in this execution. Under AM04, preserve the final original-source contract/floors independently; prove untouched-copy equality before using native identity inventory to establish a new immutable family rooted at the copy's actual physical identity and all explicitly planned journals. Do not claim that an external copy joined an existing source-origin family. Preserve every root and head anchor; never hand-edit a receipt or infer related directories.
- Native fencing requires a different explicit control database, verified provider identity, reviewed writer/fence/quarantine evidence and durable external journals.
- AM03 established that an isolated restoration would be supported; AM04 replaces that unexecuted path with a direct copy. The owning service SOP proves source writer exclusion. Native target gates/fences, binding and acceptance precede production activation. If a native recovery path is later used, its actual receipt requirements remain mandatory; never fabricate a source fence or use a misleading recovery purpose.
- The direct-copy exception is limited to reviewed database administration: copying the exact quiescent source into an absent named database and establishing the new database's connection policy. It does not authorize raw schema-conversion SQL, manual allocator changes, package patches, or skipping native comparison. Database-level grants/settings are not inherited by `CREATE DATABASE ... TEMPLATE`; record and deliberately prepare them. Run the copy from an explicit different control database, outside a transaction, with no source sessions. Standard Aurora is required; Aurora Limitless does not support this operation.
- Source maintenance stops all Dewey HTTP execution, external CLI/operator writers, consumers, dispatchers, schedules and connection pools. A GET external-object-relations endpoint persists changes, so HTTP-verb filtering is insufficient. Drain QEO dispatch acknowledgements before shutdown and preserve any unresolved outcomes. Census corroborates database sessions but cannot substitute for a complete service writer inventory. Keep the source offline through final capture, floor collection and final cutover; no synthetic stalled epoch or fabricated native fence receipt is permitted. For the separate rehearsal copy, old-source service can resume after the short copy window while the copy remains isolated; final cutover requires a fresh source capture/copy.
- Retain identical reviewed plan fingerprint, source/fence/control/provider evidence and physical destination for apply. Every restoration requires explicit runtime rebinding.
- Rely on existing Aurora backups; retain external configs, domain/prefix registries, TLS/IAM references, principal-state inventory, secret recovery mechanisms, images/runtime files, journal roots and acceptance evidence. Never put secrets, PII/PHI or unredacted data in Git or output.
- Do not use partial legacy backup commands, direct dump/restore/SQL shortcuts, private APIs, old Dewey bootstrap or automatic template overwrites.

Preserve every original UID/EUID, stored prefix/domain, machine UUID, tenant/issuer/creation identity and lineage endpoint. Include soft-deleted records, dormant prefixes, audit, outbox/inbox, idempotency, shares, memberships and all application tables. Preserve existing DGX business objects and historical DGX template bindings; do not substitute TPX. Native typed external references plus lineage own relationships; incidental metadata must not become authority. A reviewed conversion manifest lists only permitted non-identity transformations. Refuse undeclared differences and reminting.

For every generator freeze initial source, final fenced source, assigned/reserved values, target state immediately before advancement and previously exposed recovery floors. The first resumed allocation must be strictly greater than every applicable floor, including the previously available source next value. Preserve increment alignment, ownership, dependencies, bounds and cache semantics. Unknown mappings, unsupported cache state, cycling, nonpositive increments or exhaustion block migration. Capture new migration generators too. Close old allocator sessions/pools. Retain aborted/probe/migration allocations conservatively; no identifier reuse during recovery.

## Dewey/runtime implementation

- Pin and lock exact10.1.1rc1; validate installed version. Port removed DAG interfaces to supported DAGv2 and current GUI APIs.
- Preserve live QEO resolver, complete package registration and container CLI.
- Keep schema migration, seeding and principal preparation outside application startup. Deploy with `verify_existing` and a complete newly built image, not an overlay on TapDB9.
- Bootstrap grants only the configured constrained runtime login and CONNECT. Final bind follows restoration, schema migration, service conversion and identity/floor verification.
- Review database-wide PUBLIC/runtime TEMP revocations and any explicit operator-preservation grants; no unreviewed sibling-role effects or cascading grants.
- Close and recreate every runtime session after binding. Fresh sessions must use the intended role, have effective TEMP=false and reject forbidden DDL.

## Control ledger

Execution update, 2026-09-11T07:10Z: the approved frozen-source copy completed
at06:57:52Z in78.358seconds. Source dewey_prod/OID16749 remains closed; the exact
old Dewey container is stopped with exit0. Rehearsal copy OID645854 is open only
to owner dayhoff. Native copy preservation returned ok=true/no violations and
all20 generators match the frozen source except declared physical/config
relocation. The initial and final source receipt files are byte-identical.
No new backup, schema migration, principal binding, or final deployment has yet
been performed. Native rehearsal family preparation is underway.

Candidate complete image c484c95768a4 was published at07:03:13Z as
`108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f`.
Its package/CLI smoke proves9.0.0/10.1.1rc1/0.4.8. L11's first smoke failed
because the operator helper omitted required DEWEY_DEPLOYMENT_CODE; bugfix
d826870 supplied an explicit smoke deployment and resumed against the same
built image with fresh receipts. No image rebuild was necessary. The original
failure remains retained. [Image evidence](evidence/20260911_dewey_rc_inventory/candidate-image-publish.json).

[Draft release PR13](https://github.com/lsmc-bio/dewey/pull/13) has one completed
CI run at head89255d2: lint/security/build pass,427tests passed,2skipped in34.79s.
App, lock, Dockerfile and entrypoint inputs remain unchanged since that head;
later operator scripts/docs are tracked separately. Reuse that evidence unless
an informative application change warrants another run.
[CI receipt](evidence/20260911_dewey_rc_inventory/pr13-ci-run.json).

Working states: OPEN, IN_PROGRESS, ATTEMPTING_BUGFIX. Terminal: SUCCESS, DUPLICATE, NO_LONGER_NEEDED, FAIL, BLOCKED. FAIL requires a documented bugfix attempt; BLOCKED requires exact cause/unblock condition. All rows terminal is distinct from objective completion. Phase2 is a separate ledger.

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| AM01 | Plan | Fix10.1.0 target; qualify released capabilities rather than develop/release TapDB | SUCCESS | plan_amendment | User implementation approval | O | Approved plan committed as 5c75e7b | | Exact target and released-capability qualification recorded; no upstream development/release authorized |
| AM02 | Plan | Resume with exact 10.1.1rc1 after user-directed upstream release | SUCCESS | plan_amendment | Explicit user install/resume instruction | O | Public wheel hash, tag object and peeled commit independently match; isolated EC2 pip report matches approved wheel; pip check and CLI version pass | Former immutable 10.1.0 capacity failure | Exact prerelease authorized; no automatic newer release; original release evidence remains historical |
| AM03 | Operations | Use a documented maintenance SOP for healthy-source writer exclusion and native isolated target lifecycle | SUCCESS | plan_amendment | User explicitly requests safe SOP instead of a new TapDB release for infrequent source isolation | O/B/C | B inspected RC backup/verify.py isolated branch and native target finalization; existing historical roundtrip exercises unfenced-source backup, isolated restoration and natively fenced target migration | Missing fresh source quarantine CLI was incorrectly treated as mandatory for all replacement restores | Automatic new-release blocker withdrawn; SOP evidence is service-owned, never forged into a native fence receipt; exact-effect destructive approvals remain |
| AM04 | Operations | Use existing Aurora backups and direct database copy; create no additional backups | SUCCESS | plan_amendment | Explicit user no-new-backup instruction | O/B/C | AWS Aurora migration playbooks and PostgreSQL16 CREATE DATABASE contract; B confirms native migration needs copy-local historical contract/family, not a backup archive | Original artifact-based workflow required an unnecessary new backup | New backup and client-download work stopped; no backup/database mutation occurred; one-time copy SOP replaces restore preparation |
| AM05 | Setup | Prepare exact runtime credentials/configs and public separate-operator binding SOP | IN_PROGRESS | plan_amendment | Existing explicit safe setup SOP and release/deployment authorization | O/B/D | Two new matching runtime secrets; exact-secret read policy and one-cluster metadata read policy; reviewed native-init plus production_like field and public operator overlay | EC2 role initially lacked required RDS metadata and new-secret reads; native CLI has no split runtime/operator config flag | |
| AM06 | Data scope | Waive inbox/outbox message preservation and replay gates | SUCCESS | plan_amendment | Explicit user instruction that any inbox/outbox messages may be lost and resent | O | User waiver received after source census found seven pending, zero-attempt messages | Earlier plan required message preservation and acknowledgement drain | Message loss accepted; no purge required, no queue-retention/replay delay; other identities/data and every generator floor remain protected |
| AM07 | Outage | Keep Dewey stopped and original source closed through rehearsal and cutover | SUCCESS | plan_amendment | User states Dewey may remain off for hours and explicitly approves all four remaining execution stages | O/E | Reviewed copy script d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733; native-control plan30524c4f5438712dd60c0af87402ea805835817c1fb4ca2b2f63be20932ac1a5 | Short outage and intermediate Dewey8 restart are no longer required | Single frozen source may serve both exact copies while continuously closed; final identity and floor evidence remains required; no old-source restart is in the copy capsule |
| L00 | Inventory | Refresh source/image/config/database identity and release artifacts | SUCCESS | legitimate_safety_handling | Gate0 | O/A | Fresh source parity/runtime inspection, exact RC artifact receipts, native census and control/provider preflight | | Source, image, config, physical database and immutable package provenance recorded; later cutoff drift remains a live gate |
| L01 | Source | Reconcile verified live source onto release branch targeting main, exclude undeployed features | SUCCESS | feature_implementation | L00 | A | Reconciliation 84e93852; normal root merge ca77fae; 181 non-doc paths and 73 application/lock blobs match deployed source | | Main ancestry retained; undeployed Labcore and later deployment-helper changes excluded; source parity receipt committed |
| L02 | Native inventory | Capture old Dewey schema and mappings using published 10.1.1rc1 | SUCCESS | contract_test | L00 | B/O | [Mapped native index](evidence/20260911_dewey_rc_inventory/mapped-source-summary.json); contract b4fa8198d2c8082e551011f227497b4d17b379d79d4350ff15635e1c9a9f6e75; E-accepted mappings | | Complete actual source contract and all20 mapped generators captured; former immutable capacity failure resolved by authorized RC |
| L03 | Source evidence | Complete identities/prefixes/roles/writers/all generators; finish Gate0 | SUCCESS | legitimate_safety_handling | L02 | C/O | Native census, complete mapped source, host/cron/timer census and native control plan; eight upload sessions all expired by2026-07-17; only source writer is exact Dewey container | | Gate0 inventory complete; matching Ursa process uses its own database and stays untouched; actual source fence is separately applied and evidenced in L09 |
| L04 | Native lifecycle | Qualify strict advancement, fencing, bootstrap/bind and journal recovery | IN_PROGRESS | contract_test | L02 | B/E | Reused native release evidence; changed-limit historical roundtrip passed; AM03 supports source SOP plus native target fencing | Fresh source orchestration is SOP-owned, not an automatic release blocker; actual Dewey target and recovery acceptance pending | |
| L05 | Historical migration | Qualify released native migration of an exact historical database copy and existing recovery path | IN_PROGRESS | contract_test | L04 | B/E | Reuse prior301/RC123 receipts and passing changed-limit historical roundtrip; native migration accepts copy-local contract/family without archive | Actual copy/migration and accepted-state recovery acceptance pending; no new backup required | |
| L06 | Dewey runtime | Exact 10.1.1rc1 lock/public API adoption and mutation-free startup | SUCCESS | feature_implementation | L01/L05 | D/E | D492c0ffd normal merge ee4edfe; exact lock/public APIs and120 latest affected passes; independent adoption review84812dd | | Implementation and independent source acceptance complete; populated runtime/image acceptance remains L09/L10/L14 |
| L07 | Compatibility | Remove owned compatibility/fallbacks; prove explicit failures | SUCCESS | removable_compatibility_debt | L06 | D/E | Removed old bootstrap, fallback search/literature and TapDB9 overlay paths; E reviewed negatives and120 distinct latest passing outcomes | | Owned compatibility paths removed with explicit failures; no repeated test suites |
| L08 | Data conversion | Reviewed non-identity transformations and complete preservation manifest | IN_PROGRESS | feature_implementation | L03/L05 | C/E | Cc47e4a7; exact five original migration filenames, eight pending native assets; manifest af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8 independently accepted | Actual copy target/final cutoff remain to bind; manifest permits no original-cell changes | |
| L09 | Rehearsal | Timed isolated production-data copy, migration, floors and recovery procedure | IN_PROGRESS | contract_test | L08 | C/E | Direct-copy SOP under AM04/AM07; exact read-only plan RC0 and independently reviewed script; native copy migration capsule in preparation | Copy/migration apply and actual target acceptance remain pending | |
| L10 | Independent acceptance | PostgreSQL/auth/concurrency/application/restored-data acceptance | OPEN | contract_test | L06-L09 | E | Pending | | |
| L11 | Release | Merge main normally, annotated9.0.0 tag, full immutable image | IN_PROGRESS | feature_implementation | L10 | F/O | F gpt-5.6-sol/high preparing complete clean-source image; D release/runtime/acceptance inputs integrated | Publication and main/tag gate remains after actual-data acceptance | |
| L12 | Production gate | Exact targets/control/config/image, timed outage, required destructive confirmation | OPEN | legitimate_safety_handling | Production | O/C/F | Pending | | |
| L13 | Cutover | Stop writers, capture final evidence, copy database, migrate and verify identities/strict floors | OPEN | feature_implementation | L12 | C/F/O | Pending under AM04; no new backup | | |
| L14 | Deployment acceptance | Bind, recreate sessions, authenticated reads and controlled writes | OPEN | contract_test | L13 | E/O | Pending | | |
| L15 | Closeout | Terminal counts,60minute observation, recovery evidence and objective disposition | OPEN | legitimate_safety_handling | L14 | O | Pending | | |

## Qualification and production procedure

Required qualification: actual populated observed 9.0.9 to 10.1.1rc1 on matching PostgreSQL/Aurora; full identity/prefix/relationship preservation; is_called true/false, nonunit increments, reserved/cache allocations, stale receipts, exhaustion/restart/concurrency; separate-session tenant/replay/conflict/privilege/TEMP denial; artifact/run/search/share/download/manifest/QEO workflows; authenticated Dewey and embedded TapDB GUI/DAG; explicit config/version/malformed/unavailable failures; project tests/lint/security/locked-install/build/image smoke; lost acknowledgement and recovery without reuse or loss of accepted writes. Native tests are prerequisites, not Dewey acceptance. Reuse recent passing results for unchanged surfaces; rerun only when changes, failures or unresolved concerns make the result informative, as explicitly directed by the user.

1. Rehearse on an isolated exact copy of production data with outbound mutations and dispatch disabled; measure migration and recovery procedure time. Use an explicit separately planned destination and source copy window; do not improvise a new database name on collision.
2. Retain original database/image, existing Aurora recovery protection and external journals/configuration evidence; record maintenance window and exact commands.
3. Stop/fence every Dewey writer, worker, consumer, dispatcher, scheduler, operator and pool; preserve pending and acknowledged work.
4. Capture fresh final source contract/allocators under the documented writer-exclusion SOP; rehearsal data is not final capture. Create no new backup.
5. Copy into the exact absent replacement; verify untouched-copy identity and generator equality, establish its native recovery family, then migrate/convert, advance and verify all identities/floors.
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
| 2026-09-11T05:17:31Z | AM02: verified and installed user-authorized exact10.1.1rc1 | Operator pip report hash matches published wheel; pip check and CLI version pass; live Dewey8.0.2 unchanged |
| 2026-09-11T05:21:06Z | Native read-only Aurora census completed | Source OID16749 on16.13,25roles,153objects; exact replacement absent; full activity visibility, no native source fence claimed |
| 2026-09-11T05:22:40Z | Native actual-source inventory completed | Exit0 in65.735s;225211759bytes,173423825evidencebytes,79918rows,20generators; protected source receipt and sanitized index retained |
| 2026-09-11 | Integrated D's exact RC implementation | Normal merge ee4edfe;120 distinct latest affected tests pass; no full-suite rerun or production change |
| 2026-09-11 | AM03: user requested safe occasional-operation SOP; independent reassessment withdrew new-release blocker | Native isolated replacement restore and target fencing are supported; service-owned source shutdown remains mandatory; preflight gap review underway |
| 2026-09-11 | User renewed authorization to proceed through released Dewey on dewey.day.lsmc.bio | Exact10.1.1rc1 remains fixed; safe operator SOPs preferred over upstream feature/release work |
| 2026-09-11 | AM04: user prohibited another backup because Aurora is already protected | No backup created; client preparation stopped after stale package URL failure; supported in-cluster database-copy SOP replaces new-backup/restore path |
| 2026-09-11T05:48:23Z | Native mapped source capture completed | Exit0/65.926s;225223602bytes;79918rows/20mappedgenerators; original identity digest unchanged |
| 2026-09-11 | Integrated C manifests, B/E qualification and D runtime preparation | Separate reviewed commits retained; original audit changed_by and validator_ref contain no NULL/empty values, so no source-cell transformation permitted |
| 2026-09-11T06:10:15Z | Created two matching constrained-runtime credential secrets | Passwords generated only in memory and sent to Secrets Manager; safe ARN/version receipts retained; no DB role/password changes |
| 2026-09-11T06:11:04Z | Fixed exact provider-read prerequisite and proved control connection | First DescribeDBClusters attempt denied; added only named-cluster read and exact two new-secret read policies. Control postgresOID5/dayhoff on16.13; sourceOID16749; both exact destinations absent |
| 2026-09-11T06:16:11Z | Completed reviewed read-only typed writer/upload census | Eight upload creations, all expired (latest2026-07-17); seven pending messages, all dispatch_attempt_count0; no matching cron/timers; only Dewey container is a source process, other match is the excluded Ursa workset API with its own DB config |
| 2026-09-11 | AM06 user waiver removes inbox/outbox preservation/replay work | Messages may be lost and resent upstream; no further queue-specific acceptance required |

## Final disposition

All rows terminal: no. Objective complete: no. Production data, allocators, database privileges and running application remain unchanged. Setup created two Secrets Manager runtime credentials and narrowly scoped EC2 metadata/new-secret read policies; exact artifacts are retained. Native source capture/mappings, local Dewey implementation and independent source acceptance are complete. Actual copy/migration/runtime/image acceptance and main/tag release remain open. No additional backup, Dewey9 release/cutover or Phase2 work has occurred.
