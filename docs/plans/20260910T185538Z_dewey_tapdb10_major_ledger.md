# Dewey 9: production-preserving upgrade to TapDB 10.1.1rc1

Controlling plan and execution ledger. Approved by the user in the implementation request on 2026-09-11. Execution began 2026-09-11T03:47:50Z.

**Execution resumed by explicit user instruction on 2026-09-11; amendment recorded at 2026-09-11T05:17:31Z.** The user authorized `python -m pip install 'daylily-tapdb==10.1.1rc1'`. This exact prerelease supersedes the former 10.1.0 target. Its public wheel and annotated tag were independently verified, and the isolated EC2 operator environment runs it. The earlier pause at 2026-09-11T04:23:30Z and [release handoff](20260911T042330Z_tapdb_release_handoff.md) remain historical evidence. Actual mapped source capture qualified the capacity fix. Dewey 8 is now stopped; Dewey 9 has not yet been deployed.

**Actual RC capture, migration, strict allocator advancement and runtime binding succeeded.** Native capture retained 79,918 rows across nine tables and all 20 generators. The mapped source contract, original preservation and all generator mappings are independently accepted. Under AM03/AM04/AM07, Dewey stopped at06:56:35Z and source database `dewey_prod`/OID16749 remains closed. Rehearsal copy/OID645854 completed native schema migration at07:33:01Z and strict advancement at08:02:31Z; completed-transition verification passed at08:18:13Z against all130 applicable prior floors, retaining all150 committed floors for future exposure/recovery. The c6406b8 complete image starts and its fresh runtime sessions pass principal, TEMP and DDL denial checks. HTTP acceptance found historical metadata incompatible with the native DAG contract. AM10 tracks explicit Dewey metadata conversion and native-reference adoption; final release and deployment remain open.

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

All commands use `tapdb --config ABS`. Identity and sequence commands support global `--json`; `db schema migrate` rejects it and must use native `--receipt` files without that flag. Use the immutable 10.1.1rc1 `docs/service-readiness.md` and owning CLI help for exact arguments. Stale candidate-publication prose in tagged docs is superseded by release receipts.

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
- The rehearsal native family `bfb30029-5dd1-42ec-8bf8-3094e78ae2f6` is rooted at actual copy OID645854 and its explicit journal. Under AM04, preserve the final original-source contract/floors independently; prove untouched-copy equality before establishing each copy's immutable native family. Do not claim that an external copy joined an existing source-origin family. Preserve every root and head anchor; never hand-edit a receipt or infer related directories.
- Native fencing requires a different explicit control database, verified provider identity, reviewed writer/fence/quarantine evidence and durable external journals.
- AM03 established that an isolated restoration would be supported; AM04 replaces that unexecuted path with a direct copy. The owning service SOP proves source writer exclusion. Native target gates/fences, binding and acceptance precede production activation. If a native recovery path is later used, its actual receipt requirements remain mandatory; never fabricate a source fence or use a misleading recovery purpose.
- The direct-copy exception is limited to reviewed database administration: copying the exact quiescent source into an absent named database and establishing the new database's connection policy. It does not authorize raw schema-conversion SQL, manual allocator changes, package patches, or skipping native comparison. Database-level grants/settings are not inherited by `CREATE DATABASE ... TEMPLATE`; record and deliberately prepare them. Run the copy from an explicit different control database, outside a transaction, with no source sessions. Standard Aurora is required; Aurora Limitless does not support this operation.
- Source maintenance stops all Dewey HTTP execution, external CLI/operator writers, consumers, dispatchers, schedules and connection pools. A GET external-object-relations endpoint persists changes, so HTTP-verb filtering is insufficient. AM06 waives queue acknowledgement preservation; no queue drain/replay gate remains. Census corroborates database sessions but cannot substitute for the service writer inventory. AM07 keeps the original source continuously closed from final cutoff through both copies and cutover. Do not restart Dewey 8 between rehearsal and final copy. No synthetic stalled epoch or fabricated native source fence receipt is permitted.
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
| AM08 | Operator CLI | Use supported schema-migration receipt mode without global JSON | SUCCESS | plan_amendment | User explicitly requests workaround; existing migration/setup SOP authorization | O/E | Corrected wrapper SHA e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407; native dry run and reviewed apply both RC0 | First dry run exited2 because db schema migrate rejects global --json before its callback | Failed generic command evidence retained under failed-migration-plan-json-mode; no native history moved, package patch or version change; migration completed07:33:01Z |
| AM09 | Allocator verification | Verify completed transition against every prior applicable floor while retaining new reservations for future recovery | SUCCESS | plan_amendment | Existing explicit safe migration/setup SOP authorization | C/E/O | [Independent actual outcome review](20260911T081124Z_dewey_sequence_outcome_scope_review.md); helper0e276506; fresh native RC0 at08:18:13Z, verification84c97198, inventory584a01f8, exact130-floor file d4d90271 | Original family-aware follow-up included this operation's own20 newly reserved next values; E's earlier generic post-check requirement was too broad | Original RC1 preserved. No second advancement, manual SQL, package patch or journal edit. All150 committed result floors and full family remain mandatory for future exposure/final-copy/recovery |
| AM10 | Dewey data/API adoption | Convert historical envelopes, retire graph projections and use canonical references without identity or scope changes | IN_PROGRESS | plan_amendment | Existing explicit migration, safe SOP and no-compatibility authorization | C/D/E/O | [Metadata census](evidence/20260911_dewey_rc_inventory/rehearsal-c6406b8ffb40-metadata-shapes.json); [authoritative relation census](evidence/20260911_dewey_rc_inventory/rehearsal-c6406b8ffb40-external-relation-census.json) | Dewey overwrites native factory properties and writes obsolete properties.external_payload.tapdb_graph; DAG v2 rejects both | Exact conversion and independent review underway; no metadata conversion applied. Internal un-tenanted path/trigger identifiers remain typed DGX non-federated relationships, never relabeled public or assigned invented tenants |
| L00 | Inventory | Refresh source/image/config/database identity and release artifacts | SUCCESS | legitimate_safety_handling | Gate0 | O/A | Fresh source parity/runtime inspection, exact RC artifact receipts, native census and control/provider preflight | | Source, image, config, physical database and immutable package provenance recorded; later cutoff drift remains a live gate |
| L01 | Source | Reconcile verified live source onto release branch targeting main, exclude undeployed features | SUCCESS | feature_implementation | L00 | A | Reconciliation 84e93852; normal root merge ca77fae; 181 non-doc paths and 73 application/lock blobs match deployed source | | Main ancestry retained; undeployed Labcore and later deployment-helper changes excluded; source parity receipt committed |
| L02 | Native inventory | Capture old Dewey schema and mappings using published 10.1.1rc1 | SUCCESS | contract_test | L00 | B/O | [Mapped native index](evidence/20260911_dewey_rc_inventory/mapped-source-summary.json); contract b4fa8198d2c8082e551011f227497b4d17b379d79d4350ff15635e1c9a9f6e75; E-accepted mappings | | Complete actual source contract and all20 mapped generators captured; former immutable capacity failure resolved by authorized RC |
| L03 | Source evidence | Complete identities/prefixes/roles/writers/all generators; finish Gate0 | SUCCESS | legitimate_safety_handling | L02 | C/O | Native census, complete mapped source, host/cron/timer census and native control plan; eight upload sessions all expired by2026-07-17; only source writer is exact Dewey container | | Gate0 inventory complete; matching Ursa process uses its own database and stays untouched; actual source fence is separately applied and evidenced in L09 |
| L04 | Native lifecycle | Qualify strict advancement, fencing, bootstrap/bind and journal recovery | IN_PROGRESS | contract_test | L02 | B/E | Reused native release evidence; changed-limit historical roundtrip passed; AM03 supports source SOP plus native target fencing | Fresh source orchestration is SOP-owned, not an automatic release blocker; actual Dewey target and recovery acceptance pending | |
| L05 | Historical migration | Qualify released native migration of an exact historical database copy and existing recovery path | IN_PROGRESS | contract_test | L04 | B/E | Reuse prior301/RC123 receipts and passing changed-limit historical roundtrip; native migration accepts copy-local contract/family without archive | Actual copy/migration and accepted-state recovery acceptance pending; no new backup required | |
| L06 | Dewey runtime | Exact 10.1.1rc1 lock/public API adoption and mutation-free startup | SUCCESS | feature_implementation | L01/L05 | D/E | D0f3509ce normal merge; E accepted exact adapter f433e4a3/backend9fa41b2a/external_objects0af66ea5; focused affected checks in 20260911T091833Z_dewey_native_reference_adoption.md | Historical factory-envelope and native reference adoption corrected | New full image and actual converted-data acceptance remain L09/L10 |
| L07 | Compatibility | Remove owned compatibility/fallbacks; prove explicit failures | SUCCESS | removable_compatibility_debt | L06 | D/E | D0f3509ce and E final review remove obsolete metadata graph writer and response; relation GET is read-only; strict malformed envelope/scope/endpoint negatives pass | Existing relation replay previously could reconstruct endpoints from copied IDs; now rejected | Prior bootstrap/search/literature/overlay removals retained; no runtime shape migration or installed-package patch |
| L08 | Data conversion | Reviewed non-identity transformations and complete preservation manifest | IN_PROGRESS | feature_implementation | L03/L05 | C/E | Native schema-only preservation accepted for all79918 original rows/cells under manifestaf99535d; AM10 actual census identifies required additional metadata transformations | Native schema migration does not convert Dewey-owned flat metadata or graph projections | Reopened for explicit per-cell metadata/audit/additive-reference manifest; original identity, audit and lineage preservation remain mandatory |
| L09 | Rehearsal | Timed isolated production-data copy, migration, floors and recovery procedure | IN_PROGRESS | contract_test | L08 | C/E | Copy78.358s; native migration442.684s; preservation and strict20-generator advancement accepted; bootstrap/bind and fresh runtime privileges verified | Metadata conversion, application write/replay/GUI acceptance and final exposure/recovery proof remain pending | |
| L10 | Independent acceptance | PostgreSQL/auth/concurrency/application/restored-data acceptance | ATTEMPTING_BUGFIX | contract_test | L06-L09 | E | Native preservation/floors and fresh principal/config/DDL denial accepted; c6406b8 read capsule passed10checks before DAG409 | Startup context fix is accepted. DAG rejects missing properties on12091 objects and obsolete graph projections on109 objects; C/D preparing conversion and native API port | Failed HTTP receipt700af89b retained; no controlled application write accepted yet |
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
4. Use the final source contract/allocators captured before closure under the reviewed writer-exclusion SOP. The same cutoff serves both exact copies while the source remains continuously closed under AM07. Create no new backup.
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
| 2026-09-11T06:56:35Z | Stopped exact Dewey8 container and closed source under approved SOP | Graceful exit0/no OOM; source dewey_prod/OID16749 ALLOW_CONNECTIONS=false |
| 2026-09-11T06:57:52Z | Created owner-only rehearsal copy | OID645854;78.358s; source remained closed; copy result2e477de116715b8c42c127618188d9607ac26826fb97453059b7921dd6c6ba7c |
| 2026-09-11T07:03:13Z | Published complete candidate image after correcting smoke-only missing deployment code | Sourcec484c95768a4147acdcabd12a2da0332c4c750dc; digestsha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f; no application rebuild/retest required for wrapper correction |
| 2026-09-11 | Verified all copied data and all20 generators; established copy-native family | Native parity ok/zero violations; familybfb30029-5dd1-42ec-8bf8-3094e78ae2f6; protected receipts retained |
| 2026-09-11 | ATTEMPTING_BUGFIX for schema command JSON flag | Original native preflight rejected global --json before database callback; omitted flag only for db schema migrate; retained all failed generic evidence |
| 2026-09-11T07:33:01Z | Corrected reviewed native migration apply completed | RC0; principal_binding_required=true; recovery committed; fence released; external source-next floor and application acceptance still required |
| 2026-09-11T07:41:20Z | Native post-migration identity verification completed | RC0/ok true/zero violations; verificationae181fed06cbf7eb10c630cf166437e4d9b867d661084d13ada87f1105855b3b; original rows/cells unchanged |
| 2026-09-11 | Prepared and independently accepted exact strict allocator plan | Plan file3fcdef0f0d8a6965fadc4e22c5117535d0635b30719a966823f7675d5e4d3aef; native seal83f86ca0aae608b2de42147c68280534848029d057c7b60cec72eabeda7f2791; all38 external records retained, all20 planned next values exceed source next boundaries |
| 2026-09-11 | Preserved deployed authentication/product environment for isolated launch | Exact canonical Compose35a37f2c...; safe receipt rehearsal-launch-environment.json; effective primary matches preserved YAML;8 host mappings retained; private env file never printed/committed |
| 2026-09-11 | Prepared final main worktree and Dewey-only deployment renderer | Clean main worktree dewey-main-release-20260911 starts at origin/main ef7f541; canonical service-only replacement retains shared boot unit/proxy/siblings and restores original production dispatch settings after isolated acceptance |

## Final disposition

All rows terminal: no. Objective complete: no. Dewey8 is stopped and the original source database is retained closed. The isolated rehearsal passed complete copy parity, native schema migration, original-data preservation, strict allocator advancement and bound-runtime privilege checks. Its full image starts, but DAG acceptance requires the explicit Dewey metadata/API conversion tracked by AM10. Normal main merge, annotated9.0.0 tag, final image, replacement copy and production deployment remain open. No additional backup, original-database deletion or Phase2 work has occurred.

### 2026-09-11T08:29Z actual runtime binding and image startup

- Native rehearsal bootstrap created only constrained role `dewey_rehearsal_9`/OID646337; exact binding plan `e65fdff7d846d58730696f5e54cb34936d470d8073d25f0c04ac2606cc360f86` independently accepted and applied. Result file `27515410a7f3d1167d0f0722d88b951b96d01bb88447a2266e36daf31c3690ea`, native result `87c5999fe15c27ccd6af5b06038b18085ad441dfc34b6e73b7ffb5120d4cd83b`, `runtime_temp_denied=true`, `privileges_verified=true`. Fresh runtime sessions remain a separate gate.
- First Docker launch returned125 before container creation because the new mount list required absent `/home/ubuntu/.config/ncbi/key.txt`. Both this host file and its parent are absent; the stopped source used the identical read-only host config directory. Existing `cli/server.py:155-168` treats that API key as optional. F removed only the unsupported new bind from the recipe/final template; existing environment behavior is preserved, no credential file was generated. Failed launch receipt remains intact.
- Corrected full candidate launch created container `6f67f639bf2512de2525e91703bf41b40f79f131891f025c9fd5842f6a783da2` at08:26:25Z; it exited1 at08:26:30Z, without OOM or an HTTP listener. Native `web.runtime` metrics initialization resolved the shared `cli_core_yo` Dewey configuration instead of the explicit TapDB runtime configuration. L10 enters ATTEMPTING_BUGFIX. D owns explicit released `set_cli_context` integration in Dewey; E reviews the interface and new regression. F prepares a complete new source image after acceptance. No TapDB package edits, compatibility layer, new native migration, or repeated allocator advancement are indicated.
- Original Dewey8 remains stopped and original database closed. No application acceptance writes occurred. Full private startup log remains on EC2; only nonsecret failure metadata and launch commands enter Git.

### 2026-09-11T09:05Z runtime acceptance and metadata conversion scope

- Complete candidate `c6406b8ffb40e58feaba31e2163d77448d47698c` published at08:41:38Z, digest `sha256:cdf64e75f23c2ee6cd9327e3a52432000b7aa08073f02b9237e125f5df9f54c1`. Isolated container `039f7ac3d6a3f3ccc289b7a379b1370df2b4b1339a37b3ff66e5b5ea333a666d` runs only on127.0.0.1:18914. Full image source/lock/base parity and package smoke receipts retained.
- Fresh actual runtime verification file `197cd09c7a2ea876316d80fc33f1e0b0620751a4a348ecc2e3ed288cc59e8d86` is independently accepted: exact role/config/domainM/dewey, effective TEMP=false, forbidden TEMP/schema DDL denied42501, all11 historical DGX template bindings unchanged. This does not establish application write or GUI acceptance.
- CI run [34580376918](https://github.com/lsmc-bio/dewey/actions/runs/34580376918) completed successfully on head5e8761b: Ruff/security/build passed;502tests passed,2skipped,5warnings in39.59s. The previous run failed only formatting of an operator-helper test and is retained. Reuse current passing evidence until informative source changes.
- Authenticated HTTP read receipt `700af89b99f7b30171094f63b44fadd12caaa20509d2886475487ae518333b82` passed health/ready/artifact/package20members/QEO resolver/auth-negative/manifest/object-detail checks, then failed DAG409: `invalid_local_graph_contract: json_addl.properties must be an object`. No controlled application writes or metadata conversion followed.
- Read-only census file `617389a02b41075809f4157c89f4114ca2e52c870b4dfaf715a390f98e89986e` found12091 Dewey instances and1014 lineages missing properties, plus109 instance projections containing the retired graph key. All observed properties values that exist are objects.
- Expanded census file `71946640e8e194665a1c93878b1c2588b9cdb718cd238972943d6b7fbb004e95` found396 external objects,440 relation objects and880 authoritative endpoint lineages. All440 graph entries match those relationships exactly; no unknown projections, endpoint mismatches or duplicate native-assertion groups. Native reference templates are not visible to the current runtime.
- C prepares reviewed per-cell conversion and protected archival evidence; D ports writers to the released API and removes mutating GET behavior; E independently reviews identity, archive, native template provisioning and runtime scope. All three agents resumed successfully after a temporary account usage error. No credit redemption, model change or new TapDB release is requested or performed.
- Scope decision: un-tenanted internal DYEC directory identifiers and Ursa logical trigger identifiers retain their existing typed DGX objects and authoritative local lineage as non-federated identifiers. They must not be falsely labeled public, assigned invented tenants or classified by EUID-shaped syntax. Proven persisted external object kinds use native TapDBObjectTarget links. Historical graph projections are retained verbatim as explicitly non-authoritative migration evidence and removed from the active graph contract.

### 2026-09-11T09:22Z accepted application port and template-plan correction

- D application commit `0f3509cefe4df4a326403af9d2268ca8f2c6cda6` merged normally. E accepted the final files and focused tests. New instance envelopes are retained, canonical external references use stable persisted assertion evidence, relation reads no longer write, and corrupt existing endpoints cannot be reconstructed from copied IDs. No dependency, lock, Dockerfile or entrypoint pin changed. L06/L07 return to SUCCESS for source implementation; actual converted-data acceptance remains open.
- Original template setup helper `df765690de43da83c02938a74956123a0620c1c04a77ec4301dae544cdcdb49a` stopped in its read-only plan with RC1 at native physical-target comparison. Configuration supplied port as text. No plan, apply intent or mutation occurred. Safe diagnostic file `319cb9d0c27791100fd4d6459b29e5121350e5bee49752d6551f6bd006918bae` is retained.
- C correction53b7a32 calls public `validate_target` before `physical_target`. E accepted exact corrected helper `a59c18d74d3ebf251e418c79beb5597fcac42fba706a0f54512578e6ed14cdd9` for the read-only retry. The original remote file remains intact; corrected file is `/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_xrf_template_setup_port_fix.py`. A staging length assertion initially used11425 instead of the actual11399bytes; the existing complete file was then verified as11399bytes with the exact accepted SHA, without re-uploading or editing its content.

### 2026-09-11T09:38Z template setup and CI correction

- E accepted the actual template plan `9be5da6144d9f37889fd5c01c00ab2f670a7a09b55344a4ed914c67d58484301`. Its exact apply committed at09:36:38Z: two canonical M/dewey XRF templates inserted, zero updated, all22 original whole-row hashes unchanged;24 templates now exist. Result file `c7f4e392fb949299ce2f565458fdc81910cf58a4d6acaf13b3949bb2979ccdf1` is retained in the protected operator root and sanitized evidence directory. Original source remains closed and candidate stopped.
- A fresh native runtime binding plan was produced for the newly available templates, file `5888e3d33d36884e996222c004926d3d728918092da5043e5ffb67b03c2dcf4c`; E's actual grant review precedes apply. This step does not establish metadata, reference or application acceptance.
- Required CI34583948418 on5f51f81 failed only the Ruff formatter on `dewey_service/services/search.py`; lint and Bandit passed, dependent tests/build did not run. O applied the exact three-line formatting correction. The newly integrated C metadata test also required formatting; its eight focused guard-test results are reused. Both changed files now pass the frozen formatter. No behavioral test was repeated for formatting.
- C metadata helper78a0608/script `d99d763572d7fbc350a8f296051232539c1caca0136fcee0f9a36b53e36b9579` is integrated and E accepted it for read-only planning against a fresh post-template/bind native baseline. Exact-cell apply and native post-comparison remain open.
- F prepared full image capsule5f51f81 without live publication. Because the formatting correction changes an application source input, it will be regenerated from the next clean source commit before publication; the unused capsule remains retained.

### AM11: user-directed expedited deployment

- User requested immediate deployment, sufficient existing rehearsal/test reuse, and reduced agent work because of remaining credits. Release merge/tag and the single final image build may now proceed concurrently with the remaining fixed data conversion. No further intermediate candidate image or broad optional test run is planned. Production switch still requires preserved data and strict allocator floors;60-minute observation follows the live switch.
- Native XRF binding applied successfully: result `df9776e25ea7c97fe72423781644dfc12923c1a32a519757947b0be711479e33`, TEMP denied and privileges verified. E accepted the exact plan and sole added XRF sequence grant. C/E completed bounded reference helper `006cc4ec8b7ac18363568273784a8ff00f644d02e6ebe6f82839ca4310484f1b` and are idle.
- CI34585283379 passed lint/format/security and538 tests, with2 skips; one anomaly response test supplied the obsolete missing-properties fixture. O added only the required empty properties object to that fixture; the single failed test now passes. Application behavior and qualified build-input manifest remain unchanged.
- Metadata helper staging initially started before the foreground bind command had returned, so the first transfer command was not executed. Exact inspection established that the bind result committed and the helper destination did not exist; the helper was then staged with exclusive creation and verified at21308bytes/SHA d99d7635. No database apply was repeated.
- All original-database, prefix, identity, source-freeze and recovery-floor requirements remain active. No new backup, original-database deletion, credit redemption or Phase2 work is authorized or performed.

### 2026-09-11T09:59Z final release and replacement database

- PR13 merged normally at09:46:27Z to `main` commit `1f634ef66082eee32c788e0d8c386a20c2b8563e`. Annotated numeric tag9.0.0 is published and peels to that exact clean main commit. Required CI34585653293 passed Ruff, Bandit,543 tests with2 skips and package build. No optional suite was repeated.
- The one complete final image was built from the exact tag/main source and qualified build-input manifest `3a82a20469bfa0a0a5dff91160347f4f550e4b64a597702d228a08f47bf17193`. Published09:53:16Z as Dewey9.0.0, digest `sha256:bce8846d42320467824ce9473dd2315922ea7575c92633e04ca0a159c25c613b`; push receipt99d747d2 is retained. TapDB10.1.1rc1, Meridian0.4.8 and frozen Python3.12 image checks passed.
- AM11 now executes the remaining reviewed metadata/reference conversion only on final, with actual native preservation required before runtime activation. The read-only rehearsal metadata plan `fef63f3a40c78caca94cadbb63e392187cae75d3fac680659e807ecaa51dd66c` confirmed13214 exact changes/26428 expected audit rows; no rehearsal metadata/reference apply occurred. Protected disposition `expedited-cutover-decision.json` records the user's expedited boundary accurately.
- Terminal rehearsal exposure plan `a80108644cb181038f798143a95e66a6ed2847982789e124ebb6122d71da03b9` passed native validation:20 generators and221 retained/projected floor records; no pending family operation. All source and rehearsal writers remain stopped.
- Exact final copy `dewey_prod_tapdb10`/OID646741 was created owner-only from continuously frozen source. Copy result `6cdc21cc0fd23fee47e4684a419d32518b80526c27e39686989e7770259d0904`; no backup or source reopen. Full native copy capture and original-data/generator comparison passed. New family `24e51781-01a0-424e-8ab7-445267f76530`, capsule8433b36a, has a separate final journal and includes full rehearsal exposure. Native migration planning is in progress.
- Final Dewey-only deployment is rendered but not installed. It binds exact final image/config, restores original production dispatch configuration, and preserves sibling service/manifest content. Renderer now pins the actual accepted environment helper528d963b (operator-only constant change; no image change). Rendered Compose9f1c4c3b, manifest6d459793, safe deployment planb6d51838. Original Dewey8 is still stopped; new Dewey is not live yet.

### Final schema and strict allocator acceptance

- Native final migration plan12a66c21 matched all eight independently accepted rehearsal migration assets, applied-migration state, prefix configuration and template bindings. Its apply, migrated capture and full native preservation verification returned0. GitHub release9.0.0 is published at https://github.com/lsmc-bio/dewey/releases/tag/9.0.0.
- Final allocator plan `3ad19d300cfd59c21dea1052722e8da0cce4e1b129f5697e1e3fce80e4613be0` covers all20 generators and complete frozen source/rehearsal floors. Native apply returned0 with every planned next strictly above its floor; DGX next22207, XRF next4, generic instance UID12208, generic template UID27, lineage UID1019 and audit UID66695. These are sequence values, not fabricated EUIDs.
- The follow-up operator SOP stopped before writing preparation evidence because it compared duplicate multiplicities: native family retained333 distinct exact(name,value,source) records, while the successful result retained371 records including38 duplicates. Independent native result seals, commit/fence release and every distinct floor matched; no unknown floor, pending operation or new allocation was found. O corrected only the SOP's equality comparison to exact distinct records, retaining every original record/file and all plan floors. Corrected helper `7a214cc6ab6feeb84016aa5802a4dbb724f46025ace861527b2c9d3c99b52939` is staged separately; old helper retained. The fresh native completed-transition verification then returned0. No allocator apply was repeated, no TapDB package changed and no test suite rerun.
- Final constrained runtime bootstrap completed using the same E-accepted plan54f17f91; only login attributes and CONNECT were prepared. Exact final template planf52160e8 matches all22 unchanged original rows and both E-accepted canonical definitions; two-template apply and final bind plan are in progress. Metadata/native reference conversion and live activation remain open.

### 2026-09-11T10:49Z final metadata audit correction

- Final template apply committed two canonical additions with zero overwritten templates. Final runtime binding plan6574f408 matches the independently accepted rehearsal grants and routine definitions after excluding physical routine OIDs; native bind apply completed. Runtime sessions have not yet started.
- L13 entered ATTEMPTING_BUGFIX after the first metadata transaction failed its audit assertion. The failed intent and outputs remain retained. A single public-API update with deliberate rollback confirmed the native trigger emits exactly three records: json_addl, modified_dt, and created_dt. The creation timestamp represents the same original instant; the extra audit is caused by SQL versus JSON timestamp text formatting. Protected diagnostic is copied as final-metadata-audit-probe.json, SHA940cbd25b64687464fd31c3e87ccbb5073eca37f2e4cd6057d3e5f6e35195cfb.
- O corrected only the one-time metadata helper audit proof, staged separately as dewey_metadata_conversion_audit_fix.py, SHA2624db7c69f80d1826c4e39cc55a8e58f00c9622ef162261d353b9c99375f19f. It requires timezone-aware creation instants and the exact original native cell hash; the conversion manifest still permits only json_addl and modified_dt changes. The installed TapDB package and image are unchanged.
- Fresh read-only plan64c1264308d1ea75035b2ad30fb6ae6370df05a560ad5132efe3654e71edc9b1 proved all13214 reviewed cells and every other plan field unchanged except helper hash and39642 expected native audit rows. It also proved no post-baseline audit rows persisted from the failed transaction. Nontransactional sequence consumption from failed/probe work is retained, never reset. The corrected apply and native preservation chain are running in the original operator pane, using a new private evidence directory. No test suite rerun or additional agents were used.
