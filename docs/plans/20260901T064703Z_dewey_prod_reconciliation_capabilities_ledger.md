# Dewey Production Reconciliation And Capabilities Ledger

Opened: 2026-09-01T06:47:03Z

## Objective

Reconcile the source and release provenance of the Dewey service running at
`dewey.day.lsmc.bio`, inventory all localhost-only Dewey work for explicit user
approval, align the production commits with the authoritative `lsmc-bio/dewey`
`main` branch, and publish a comprehensive derived feature/capability reference
without adding new product behavior.

## Authority And Constraints

- Deployment source authority: `git@github.com:lsmc-bio/dewey.git`.
- Production inspection is read-only. No restart, deployment, record write,
  Dayhoff pin change, or production configuration change is authorized.
- No pre-existing localhost-only change may be staged, committed, merged, or
  tagged until the user approves its stable candidate ID.
- Generated output, credentials, runtime state, and operational residue do not
  become Dewey source by default.
- No fallback, compatibility shim, speculative feature, or Plan 2 feature is in
  scope.
- A new Dewey tag is created only if the user approves source changes. A
  documentation-only merge receives no package tag.

## Gate 0 Baseline

| Fact | Evidence | State |
| --- | --- | --- |
| Production health | `GET https://dewey.day.lsmc.bio/healthz` returned `200`, service `dewey`, environment `day`, version `8.0.2` | VERIFIED |
| Production readiness | `GET https://dewey.day.lsmc.bio/readyz` returned `200`, `ready=true`, database check `ok` | VERIFIED |
| Running image | `dayhoff-day-dewey-1`, image digest `sha256:0780a42dd2b3d5620de2c538cada32acd661f5be5a0f0b60a08c9f941ea3af42` | VERIFIED |
| Released source | Annotated tag `8.0.2` peels to `dea0009b743ad5b627177acdf21c87dd5c1d67c1` | VERIFIED |
| Application/config parity | 72 files under `dewey_service` and `config`; normalized SHA-256 `312bef19beb57dd973d94cf456bf5e1d38002749eb16bdbd499156b90c72e6c7` in both container and tag checkout | VERIFIED |
| Source overlay | No `/app` bind mount and no `/app` writable-layer entry in `docker diff` | VERIFIED |
| Container residue | Added `/tmp` publication/integrity artifacts and deployment/AWS bind mounts; no application-source mutation observed | VERIFIED_OPERATIONAL_ONLY |
| Remote main | `lsmc-bio/dewey@main` is `818bf15c7cfd65a351acf6816293057ee2ba8bf6` (`8.0.0`) | VERIFIED |
| Production commits beyond main | `8.0.1` and `8.0.2` are descendants of `main` but not contained by it | VERIFIED |
| Remote default branch | GitHub default is `jemdev10` at `61173c27ed08dab9e193bef518d7127bdbebe75a`; it contains production plus three later Labcore-owner commits that are not deployed | VERIFIED_WITH_FINDING |
| Clean execution branch | `codex/dewey-prod-reconciliation-capabilities-20260901` from `origin/main` in this isolated clone | VERIFIED |

## Audit Roles

- Lead/synthesis: `gpt-5.6-sol`, `ultra`; sole editor of this clean branch.
- Production/Git provenance: `gpt-5.6-sol`, `xhigh`; read-only evidence return.
- Capability/API/data model: `gpt-5.6-sol`, `xhigh`; read-only evidence return.
- GUI/docs/defects: `gpt-5.6-terra`, `high`; read-only evidence return.

No audit agent edited the clean branch or any pre-existing candidate.

## Execution Ledger

| ID | Requirement | Status | Evidence / Terminal Note |
| --- | --- | --- | --- |
| PROV-001 | Complete container/image/build-context parity, including entrypoint, package metadata, lock/dependencies, history, mounts, Compose image, and active manifest | COMPLETE | Every Dockerfile-copied source/build-input file matches annotated `8.0.2`; the live manifest binds commit and digest. No production source overlay exists. |
| GIT-001 | Verify tag types, peeled commits, remote containment, and authoritative branch topology | COMPLETE_WITH_FINDINGS | Baseline `main` was `8.0.0`; PRs `#9/#10` advanced the reconciled pre-documentation baseline to `656f8ba` while preserving annotated production tags. Remote default `jemdev10` contains the additional undeployed Labcore-owner lane. |
| LOCAL-001 | Inventory every same-origin checkout/worktree and local-only candidate | COMPLETE | Same-origin clones/worktrees and the known `datasave` residue were classified read-only. No pre-existing candidate was staged. |
| APPROVAL-001 | Present stable localhost candidate table and receive explicit include/exclude/archive decisions | COMPLETE | At `2026-09-01T07:24:27Z` the user approved every recommended disposition. |
| LABCORE-001 | Review the post-`8.0.2` Labcore contract/API architecture, including PostgreSQL locking, TapDB ownership, idempotency, and competing patterns | COMPLETE | Architecture review passed the lock/transaction design and found two narrow blockers. Commit `ae2ff79` fixed both; green PR `lsmc-bio/dewey#8` merged normally into `jemdev10` as `6a0e86a` at `2026-09-01T07:51:17Z`. Issue-only work is recorded below. |
| MAIN-001 | Merge the existing production `8.0.1`/`8.0.2` commits into authoritative `main` normally | COMPLETE | PR `lsmc-bio/dewey#9` merged normally at `2026-09-01T07:52:45Z` as `482570d`; original commits `c139fdc` and `dea0009` are ancestors of main and annotated tags `8.0.1`/`8.0.2` remain on their original commits. |
| SOURCE-001 | Reapply only approved localhost source onto a fresh branch from reconciled `main` | COMPLETE | The only approved include, evidence candidate `LOC-INV-01`, was reapplied byte-identically as `3c27428` and merged through PR `#10` at `2026-09-01T07:54:16Z` as `656f8ba`. No product source candidate was approved. |
| RELEASE-001 | Validate, merge, and create the next unused annotated numeric patch tag only if approved source changed | COMPLETE_NO_TAG | `LOC-INV-01` is evidence-only and changes no package source or behavior. Per approved rule, no new Dewey package tag is created. |
| DOC-001 | Produce `docs/derived_features_and_capabilities.md` with complete evidence-backed surface inventory | COMPLETE | The reference distinguishes live production, released source, repository-only Labcore, and local-only candidates; it inventories API, browser, CLI, objects, lineage, storage, integrations, auth, configuration, findings, and exclusions. |
| PLAN2-001 | Add a decision-ready Plan 2 intake register without implementing features | COMPLETE | The reference ends with evidence, impact, dependency/contract, risk, and acceptance proof for release blockers, misleading/redundant surfaces, hidden capabilities, and product opportunities. No Plan 2 feature was implemented. |
| QA-001 | Reconcile route inventories; run bounded source/release checks and document validation | COMPLETE | Exact 55 OpenAPI and 50 non-schema first-party operations reconcile with the runtime app; five mounted TapDB DAG operations and eight Dewey CLI groups are separately inventoried. Validation evidence is recorded below. |
| PR-001 | Open normal PRs and merge when green | READY | Documentation and ledger are locally complete and validated. No administrative bypass or force push is authorized. |

## Required Approval Table Columns

Each localhost candidate will be presented with: stable ID, checkout/path,
branch/HEAD/upstream, exact changed files and diffstat, tracked/untracked status,
remote reachability, production byte match, inferred purpose, overlap/conflict,
existing validation, risk, and recommendation (`include`, `exclude`, `archive`,
or `needs owner`).

## Localhost Candidate Approval Table

`archive` below means retain the isolated branch/files as historical evidence
without merging them; it does not authorize deletion or modification.

| ID | Location / source state | Exact candidate delta | Evidence, overlap, and risk | Recommendation | User disposition |
| --- | --- | --- | --- | --- | --- |
| LOC-INV-01 | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey`; branch `jem-dev`, local-only commit `e0a517c6d688`, one commit ahead of `origin/jem-dev` | Two evidence files, `+715`: snapshot README and 700-line `generic_templates.json` | JSON parses; SHA-256 `30a7b3dc…de6e` exactly matches production `/tmp/dewey_generic_templates.json` and the retained transfer snapshot. Evidence only; it must never seed production. Parent is old `7.0.2`, so reapply the two files only after reconciliation. | `include` | APPROVED_INCLUDE |
| LOC-LINEAGE-01 | Same checkout/ref, dirty working tree | Seven source/template files, `+70/-18`: `app.py`, four service modules, and two artifact templates | Python changes are TODO comments describing the copied-`producer_object_euid` antipattern; templates are whitespace/tab churn. No behavior or test change; based below production and overlaps heavily changed files. Preserve the design finding in Plan 2. | `exclude` | APPROVED_EXCLUDE |
| LOC-SHARE-01 | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-share-html-view-20260713`; branch `codex/dewey-share-html-view-20260713`, `HEAD=818bf15`, no upstream | Four tracked files, `+120`: `app.py`, `templates/shares.html`, `docs/apis.md`, `tests/test_share_management.py` | Adds a stateful `GET /shares/{euid}/view` redirect. Historical ledger records focused 7 pass, full 381 pass/2 skip, Ruff/Bandit/build/diff pass, but the WIP is based on `8.0.0`, inherits current share-auth P0/P1 flaws, and is not deployed. | `needs owner` | APPROVED_DEFER |
| LOC-SHARE-LEDGER-01 | Same share-view worktree | Untracked `docs/plans/20260713T215243Z_dewey_authenticated_html_view_ledger.md`; 51 lines/4,747 bytes | Accurate historical WIP/test evidence with no live-success proof. Include only if the share-view source is later deliberately recovered; otherwise retain with its worktree. | `archive` | APPROVED_ARCHIVE |
| LOC-SHARE-HELPERS-01 | Same share-view worktree | Six untracked deployment helpers: four SSM JSON payloads, a 129-line proof script, and a 99-line WIP-patch script | Generated/ad-hoc deployment proof glue, not product source or production overlay. | `exclude` | APPROVED_EXCLUDE |
| LOC-SHARE-ACCEPT-01 | Same share-view worktree | Untracked `scripts/prod_share_delivery_acceptance.py`; 539 lines/19,610 bytes | No literal secret found and token is read from the environment, but the script performs production prefix/share mutations and predates the authorization findings. | `needs owner` | APPROVED_DEFER |
| LOC-COMMIT-01 | Local branch `codex/deployment-banner-release-dewey`; commit `19b315020673`; upstream gone | Eight files, `+126/-11` | Not remote/tag-contained. Deployment-color behavior is already implemented by later `8.0.2` code. | `archive` | APPROVED_ARCHIVE |
| LOC-COMMIT-02 | Local branch `codex/lsmc5-dewey-standalone`; commit `a5a16bf8429a`; upstream gone | Two files, `+2/-1`; adds `euid_client_code: D` | Not remote/tag-contained and conflicts with the released `domain_code: Z`/registry contract. | `archive` | APPROVED_ARCHIVE |
| LOC-COMMIT-03 | Local branch `codex/dewey-tapdb-hard-cut-v3`; commit `e81331b098c9`; upstream gone | Seven files, `+68/-39` | Not remote/tag-contained. Explicit-config semantics already exist in `8.0.2`; activation/dependency details are obsolete. | `archive` | APPROVED_ARCHIVE |
| LOC-COMMIT-04 | `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-share-prefix-hardening-20260526`; local-only commit `025e8b550eaf` | 16 files, `+272/-76`, including source, tests, fakes, docs, and a ledger | Old share/prefix hardening line; not patch-equivalent to released source and unreachable from remote refs. Reapplication would mix superseded semantics into the current release. | `archive` | APPROVED_ARCHIVE |
| LOC-COMMIT-05 | `/Users/jmajor/.codex/worktrees/cbc5/daylily/dewey`; branch `codex/archive-dewey-pre-main-merge`; local-only commit `b0cad40fb024` | 24 files, `+829/-70`, including runtime/config, CLI, schema-drift/observability, and E2E support | Explicitly an old pre-main-merge archive snapshot; not production-equivalent or remote-contained. | `archive` | APPROVED_ARCHIVE |
| LOC-STALE-01 | `/Users/jmajor/projects/cli_refactor/dayhoff/.dayhoff/local/lsmc5/repos/dewey`; detached `a029abb` (`0.5.0`) | `AGENTS.md` `+7` and `config/tapdb-config-dewey.yaml` `+1` (`euid_client_code: D`) | Stale generated clone; duplicates LOC-COMMIT-02 and contradicts production's `Z` domain. | `archive` | APPROVED_ARCHIVE |
| LOC-STALE-02 | `/Users/jmajor/projects/cli_refactor/dayhoff/.dayhoff/local/xxyyzz/repos/dewey`; detached `eb667b7` (`0.9.7`) | `AGENTS.md` `+7` and deletion of a one-line `environment.yml` symlink | Stale generated clone with no production match or validation. | `archive` | APPROVED_ARCHIVE |
| LOC-AGENTS-01 | 38 historical Dewey checkouts/worktrees, grouped after exhaustive scan | 30 copies add shell defaults (`+7`); five add shell defaults plus budget policy (`+11`); three add budget policy only (`+4`) | Runtime-neutral duplicates. Shell defaults already exist in released `8.0.2`; the budget stanza does not. Do not merge 38 copies. If wanted, the budget policy should be applied once to canonical authority in a separately explicit decision. | `exclude` | APPROVED_EXCLUDE |
| LOC-DATASAVE-SCRIPTS-01 | `/Users/jmajor/projects/lsmc/datasave`, local `lsmc` checkout branch `codex/recent-seqrun-runqc-solo-hybrid`, `HEAD=d4e9f5874cba` | Three untracked helpers: two at 236 lines (`2308e7cc…403c`, `76f1d851…dcb6`) and one at 214 lines (`57c1447e…a169`) | First two exactly match production `/tmp`; all are one-off mutating Bjuice/MultiQC/CloudFront publication helpers. No literal token was found; operational identities/paths are fixed. Not Dewey source. | `archive` | APPROVED_ARCHIVE |
| LOC-DATASAVE-JSON-01 | Same `datasave` directory | Four untracked JSON receipts/inspection files, including `dewey_day_share_publish_inspect_20260717.json` (`2db7f5…23b`) | Operational evidence includes real persisted EUIDs and expired signed-URL fields. Leave in place; never reproduce those values in Dewey Git. | `exclude` | APPROVED_EXCLUDE |
| LOC-TEMPLATE-COPY-01 | `/Users/jmajor/projects/mega_dayhoff/.template-snapshots-transfer/dayhoff-production-template-snapshots-20260719T044748Z/dewey_generic_templates.json` | One untracked transfer copy, SHA-256 `30a7b3dc…de6e` | Exact duplicate of LOC-INV-01 and production `/tmp`; transfer residue, not a second source candidate. | `exclude` | APPROVED_EXCLUDE |

No candidate above matches missing production application bytes, because there
are no missing production application bytes. Nothing in this table has been
staged, copied into the clean branch, committed, pushed, or deleted.

`/Users/jmajor/projects/mega_dayhoff/dayhoff/scripts/export_service_template_snapshot.py`
is already tracked Dayhoff source and exactly matches production
`/tmp/export_service_template_snapshot.py`; it is not a Dewey localhost
candidate.

## Production Parity Evidence

- Live container: `dayhoff-day-dewey-1`, continuously running since
  `2026-07-14T23:05:01Z`.
- Immutable image:
  `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:0780a42dd2b3d5620de2c538cada32acd661f5be5a0f0b60a08c9f941ea3af42`,
  tagged `8.0.2-dea0009` in ECR.
- Annotated Git tag `8.0.2` peels to
  `dea0009b743ad5b627177acdf21c87dd5c1d67c1`.
- `/app/dewey_service`, `/app/config`, `/entrypoint.sh`, `/app/pyproject.toml`,
  `/app/uv.lock`, and `/app/README.md` are byte-identical to tag `8.0.2`.
- The active Compose file and container configuration agree on the image;
  `container-release-manifest.json` binds source tag `8.0.2`, the peeled commit,
  and the exact image digest.
- No `/app` mount or writable-layer source change exists. Added `/tmp` files are
  classified as one-off publication/integrity helpers, exported evidence, or
  disposable runtime residue, not application source.
- Runtime dependencies report Dewey `8.0.2`, Python `3.12.13`, TapDB `9.0.9`,
  auth-cognito `2.1.5`, cli-core-yo `2.1.1`, FastAPI `0.136.3`, Uvicorn
  `0.48.0`, and boto3 `1.43.15`.

## Provenance And Runtime Findings

1. `origin/main` stops at `8.0.0`; production commits `c139fdc` (`8.0.1`) and
   `dea0009` (`8.0.2`) must be merged into it without moving either tag.
2. GitHub's default branch is `jemdev10`, not `main`. It contains production
   plus three later Labcore sequencing-owner commits (`0944115`, `3f1ccf1`,
   `61173c2`) that are Git-only and absent from production OpenAPI/source.
3. The image declares user `lsmc`, but Compose overrides it with `0:0`; the
   live Python process runs as root and the root filesystem is writable.
4. Live health and OpenAPI expose version `8.0.2`, but `LSMC_RELEASE_SHA` and
   OCI source/revision labels are absent; `/version` is not implemented.
5. Tag `8.0.2` is annotated, but it has no GitHub Release.
6. Reconciliation completed without moving tags: authoritative `main` is now
   `656f8ba15847917c4ddd8781a6a2fc2a781a041b`, containing the original
   production commits plus the approved evidence-only inventory snapshot.

## Post-8.0.2 Labcore Architecture Gate

Audit target: `origin/jemdev10` commit
`61173c27ed08dab9e193bef518d7127bdbebe75a`, containing Labcore commits
`09441150e3febfeab6b6be8d66cb6160f267886c` and
`3f1ccf1e9bf173fb99f6b16ee0530dcd74df0ba2`. This source is not deployed in
production.

### Accepted design

- `pg_advisory_xact_lock(bigint)` is acquired inside TapDB `9.0.9`'s explicit
  SQLAlchemy transaction before Labcore idempotency or authority reads.
- The deterministic signed 64-bit key binds the exact global
  `labcore:sequencing_run:<run-euid>` identity and intentionally excludes
  tenant, so competing tenants serialize on the same run.
- PostgreSQL releases the transaction lock on commit or rollback. The held
  transaction performs TapDB work only; it makes no S3, network, or provider
  call.
- Identical concurrent commands serialize to one `201` creation and one `200`
  replay. A divergent command for the same run serializes and then conflicts.
  Artifact, external object, relation, two lineage edges, receipt, and
  idempotency record commit or roll back together.
- The Labcore identity, global-owner policy, and lock-key derivation remain
  Dewey domain responsibilities. The current native PostgreSQL call is correct
  and does not block this default-off package. The stronger end state is TapDB
  issue `#93`: a database-enforced optional typed-instance identity key and
  atomic created/existing claim. Dewey tracking issue `#202` will adopt that
  released primitive, remove the direct lock, and add database-backed
  concurrency proof. TapDB `#92` is retained only for rowless coordination
  problems, not as the preferred Labcore dependency.
- Dewey's existing two-object external-object/reified-relation representation
  is retained for Labcore in this release. Future ordinary cross-service
  references should converge on TapDB's typed XRF object plus direct lineage;
  a reified relation should remain only where the relation has independent
  metadata, authority, audit, receipt, or lifecycle.

### Narrow release blockers and fixes

1. Origin used an `async def` FastAPI handler that directly called synchronous
   SQL and could wait on the advisory lock on the event loop. Commit `ae2ff79`
   makes the handler synchronous so FastAPI runs it in a worker thread.
2. Generic v1 writers could pre-create the reserved Labcore identity or attach
   the reserved relation without the Labcore lock/tenant command. Commit
   `ae2ff79` rejects `labcore` + `sequencing_run`, rejects
   `labcore_sequencing_run`, and rejects any generic relation to a reserved
   Labcore object across public and internal generic helper paths.

Focused proof on the fix branch: 31 Labcore/external-object/service tests pass;
Ruff check and format, Bandit, `compileall`, and `git diff --check` pass. The
known duplicate `/api/dag/search` operation-ID warning is unchanged. CodeQL's
Python and JavaScript/TypeScript analyses passed, and PR `#8` merged normally
into `jemdev10` as `6a0e86a14798997f22daa2aa381ba2946fd15766`.

### Activation-only gates and issue disposition

The lane remains default-off. Before enabling it, an operator must inventory
pre-existing reserved identities/relations, prove Labcore tokens do not overlap
ordinary Dewey bearer tokens, identify the trusted producer of the target
artifact's Labcore evidence, confirm the intended application-level tenant
model, and exercise identical/divergent requests against real PostgreSQL
sessions.

The production path does not use a Python lock. It invokes
`pg_advisory_xact_lock(bigint)` in the TapDB transaction. Python
`threading.Lock` appears only in the local transactional test backend, where it
provides fast deterministic service coverage but cannot prove PostgreSQL
session isolation, rollback release, independent keys, or bounded waits. This
is a proof/API-ownership gap rather than a flaw in the deployed lock algorithm.
Tenant row locking or row-level security is not a substitute: the contested
identity is global, there is no owner row on the first insert, and two
cross-tenant claimants would not contend on the same tenant-scoped row.

- `lsmc-bio/scaffold#199`: principal attribution, token separation, request
  bounds, real PostgreSQL proof, target provenance, closed error mapping, and
  activation preflight.
- `lsmc-bio/scaffold#200`: canonical alias, tenant/provenance documentation,
  receipt lineage decision, and non-EUID test identities.
- `lsmc-bio/scaffold#201`: Dewey-wide convergence with TapDB typed XRF objects.
- `Daylily-Informatics/daylily-tapdb#93`: database-enforced typed-instance
  natural identity and atomic claim with cross-tenant uniqueness; implement
  first.
- `lsmc-bio/scaffold#202`: adopt the released TapDB identity claim in Dewey,
  remove the direct advisory-lock path, and prove Labcore `201/200` replay and
  `201/409` conflict behavior against PostgreSQL; implement second. Dewey
  issues are disabled, so scaffold is its tracker.
- `Daylily-Informatics/daylily-tapdb#92`: retain only as an optional primitive
  for coordination that genuinely cannot be represented by a unique row.
- Existing TapDB issue `#42` now records the preferred XRF/direct-lineage versus
  reified-relation decision rule.

## Release-Critical Capability Findings

- **P0:** Released share UI mutations use any authenticated UI session instead
  of a write/admin guard. A `READ_ONLY` principal can revoke a known share and
  can create a self-owned share/access package for a known artifact or set.
- **P1:** Share list/detail expose policy, ownership, and audit data without
  row-level authorization; owner identity can be supplied during creation;
  share-root allowed delivery modes are stored but not enforced for subsets.
- **P1:** API bearer tokens are unscoped operator authority, not attributable
  principals with role/owner boundaries.
- **Misleading/redundant:** `dewey_html_browser` follows the CloudFront-cookie
  package branch but no response establishes browser cookies; `/shares` and
  `/admin/shares` render the same manager.
- **Documentation drift:** README examples advertise unregistered `dewey
  artifacts` and `dewey shares` CLI families and describe QEO as an HTTP API
  family although QEO is CLI/outbox behavior. `docs/gui.md` retains stale
  April verification language.
- These are Plan 2 findings only in this execution. No live exploit, write, or
  repair was attempted.

## Capability Audit Baseline

- Released source declares 105 first-party method/path operations: 55 OpenAPI
  schema operations and 50 browser/session or internal operations. Mounted
  TapDB adds five DAG API operations and the `/tapdb` GUI.
- Dewey registers eleven active TapDB object families: artifact, artifact set,
  share, share root, external object, external-object relation, literature save,
  anomaly, idempotency request, registration receipt, and outbox event.
- Durable lineage types observed are `artifact_hierarchy`,
  `artifact_set_member`, `has_share`, `has_literature_save`,
  `has_external_relation`, `is_external_relation_for`,
  `analysis_artifact_set_parent`, and `analysis_artifact_set_rerun_of`.
- Implemented capability families include artifact/reference/copy/import and
  upload sessions; storage browse/verify/lock/download; artifact sets and
  analysis/MultiQC registration; sequencer-run and terminal-result
  registration; search/export; shares/roots/subsets; external relations;
  literature saves; preferences; anomaly/health views; QEO outbox dispatch;
  Cognito/broker browser auth; static bearer API auth; and TapDB DAG/UI access.
- Actual Dewey CLI plugins are `config`, `server`, `db`, `test`, `quality`,
  `tapdb`, `cognito`, and `qeo`. Business artifact/share/search/literature CLI
  families are not implemented.
- The released tree contains 371 test functions. This is a source count, not a
  fresh collection or pass claim.

### Plan 2 Release-Blocker Intake

1. Browser `READ_ONLY` principals can reach share and other mutation handlers;
   bearer share packages trust body-supplied actor identity and groups.
2. Sequencer-run and analysis-result events write `status: pending`, while the
   dispatcher selects `dispatch_status`; `trigger_ursa` events are therefore
   not dispatchable by the released selector.
3. Generic membership endpoints can mutate a receipt-backed artifact set after
   its immutable registration manifest/receipt was issued.
4. The advertised AI-agent token path is effectively unreachable and names an
   obsolete search endpoint.
5. Explicit managed-literature mode can silently degrade to an external
   reference, contrary to fail-closed workspace policy.
6. Remote HTTP artifact import follows redirects without final-host controls
   and buffers the response in memory.
7. An external-relation `GET` can commit derived graph metadata, making a read
   route mutate durable state without an idempotency contract.
8. Invalid search scope/operator values can silently fall back instead of
   failing validation.
9. Static demo anomalies are seeded into every database and presented beside
   operational anomalies.

### Additional Suspect Or Misleading Contracts

- Share delivery TTL is not capped to remaining share lifetime; revocation is
  prospective and cannot invalidate an already issued S3 URL or CloudFront
  cookie.
- Share-set membership is expanded at access time rather than snapshotted;
  recorded member count and delivered membership may diverge.
- Upload completion persists caller-supplied checksums without comparing them
  with S3 content; storage verification establishes presence/version metadata,
  not content integrity.
- ZIP downloads and HTTP imports use process memory without explicit byte caps.
- Share-root subsets have prefix containment checks but no durable root/subset
  lineage, and root delivery-mode restrictions are not enforced.
- QEO documentation says there is no broker dispatch although HTTPS dispatch is
  implemented; the shipped example configuration omits several newer gates.
- `/api/dag/search` appears to be registered twice, producing a duplicate
  operation-ID warning in existing evidence.

## Documentation And Validation Evidence

- Labcore source branch focused validation: 31 owner/API/external-object/service
  tests passed; Ruff check and format check, Bandit, `compileall`, and
  `git diff --check` passed. PR `#8` CodeQL Python and JavaScript/TypeScript
  analyses passed.
- Exactly one full Labcore-branch suite was run after the narrow fixes: 409
  tests collected, 405 passed, two skipped, and two observability-contract
  checks failed only because `DAYHOFF_PROJECT_ROOT` was unset. Per the bounded
  rerun rule, only those two checks were rerun with the canonical
  `/Users/jmajor/projects/mega_dayhoff/dayhoff` root; both passed. Terminal
  functional result: 407 passed, two skipped, no source-attributed failure.
- Documentation smoke and runtime-route coverage: 10 tests passed. The known
  duplicate TapDB DAG search operation-ID warning remains recorded as
  `DAG-01`.
- An independent runtime/document parser reconciled all 55 released OpenAPI
  operations and all 50 released non-schema browser/session operations with no
  missing or extra entry. The five embedded TapDB DAG operations and eight
  registered Dewey CLI groups are separately enumerated.
- Mermaid CLI rendered all three diagrams successfully. All ten local links in
  `docs/README.md` resolve, including the new capability reference.
- The approved template evidence JSON parses and retains SHA-256
  `30a7b3dc9628cc2a68559f242cd60b746d9501ba27130012927572d95b07de6e`.
- `git diff --check` passes for the documentation branch, and the new documents
  contain no invented Meridian-style EUID examples.

## Terminal Acceptance

- Production source/build provenance is either fully reconciled or every gap is
  explicit and evidence-backed.
- Every localhost candidate has a user-approved terminal disposition.
- Existing production commits are contained by authoritative `main`.
- Any approved source is merged, validated, and tagged exactly once; otherwise
  no new tag exists.
- The derived capability reference accounts for all API, GUI, CLI, durable
  object/template, configuration, integration, and observability surfaces.
- Broken, suspect, redundant, deprecated, misleading, hidden, and explicitly
  unimplemented behavior is cataloged for Plan 2.
