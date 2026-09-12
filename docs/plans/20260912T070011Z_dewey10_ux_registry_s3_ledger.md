# Dewey 10 registry, sharing and S3 browser execution ledger

Approved implementation: 2026-09-12, current task. Owner: primary agent.
Controlling record: this file. Target release: 10.0.0, subject to tag inventory.

## Contract and release boundaries

- Retain Artifact and Set templates. `storage_kind` is object or prefix; one registration has one existing service-issued EUID. Browsing never registers children. Sets contain artifact EUIDs through lineage; no nested sets.
- Preserve OWY, Ursa and Labcore active APIs, identity, coordinates, lineage, idempotency and historical receipts. Explicitly initialize existing access policies and correct evidenced kind errors; ambiguous records require individual resolution. No database replacement.
- Default metadata visibility and download access independently to internal LSMC. Owners/admins and explicit delegates manage records and sharing. Every share requires shared login and approved-network ingress. External email/domain Dewey sharing is included; native external AWS grants and user-mapped AWS identities are deferred.
- Explicit release defaults: share lifetime 30 days, delivery credentials 900 seconds. Revocation stops new delivery, not previously issued credentials. Prefix shares include future permitted descendants.
- S3 Browser uses server credentials through one provider boundary. Honor registered path restrictions in every view/action. Permit internal uploads and admin deletion/replacement with exact reviewed effects; no silent overwrite. No bucket administration, version-history purge, recursive navigation scans, or credential exposure.
- GUI and CLI use public authorized service operations. Search covers all registered metadata and PubMed, without file-content indexing.
- User amendment: EUID-only transactions are a core contract. Other Dayhoff systems may persist only a Dewey EUID; Dewey GUI/API/CLI resolve kind, metadata, permissions, contents and access actions without requiring persisted S3 coordinates or delivery URLs. Existing resolve contracts remain supported.
- Stage the user-provided NCBI key securely at `/home/ubuntu/.config/ncbi/key.txt`, read-only inside Dewey, with explicit `DEWEY_NCBI_API_KEY_FILE`. Do not print or commit its content.
- Tests/lint/coverage/CI campaigns are OFF. No PR or merge. Commit intended changes on the current working branch, immutable annotated numeric tag, one final scoped image and Dewey production deployment. User acceptance precedes Ursa/Kahlo browser-link cutovers. Preserve unrelated dirty work.
- Live destructive AWS actions, live share issuance and recipient invitations are not part of implementation validation. No recurring agent automation.

## Gate 0 baseline

- Worktree: `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-labcore-910`.
- Branch `codex/dewey-labcore-910`; HEAD `6c965d7`; only initial dirty file `AGENTS.md` (user release policy; preserve).
- Production observation 2026-09-12T07:00:11Z: Dewey 9.1.0, SHA `87fd7cf3c56e8dc283ed1dedea1232984825137d`, health `ok`.
- Ursa reported 13.0.0; Kahlo reported 8.0.1. Neither is changed before Dewey acceptance.
- `git ls-remote --tags origin '10.*'` returned no tags at implementation start.
- Planning assessment: 39 browser states, 61 published API operations. Admin session only; no live write acceptance. TapDB readiness blocked by Chrome. Actual command/response behavior remains distinct from inspected source.
- Prior 9.1.0 Labcore receipts: `docs/plans/evidence/20260911_dewey_labcore_910/`; reuse unchanged contract evidence, no rerun.
- Local NCBI key exists; contents not read in planning. No key staging or production mutation occurred during planning.

## Page disposition inventory

| Surface | Disposition | Destination or requirement |
|---|---|---|
| `/ui` dashboard | Hide | Library landing; remove capped counters/duplicate shortcuts |
| `/artifacts` registration | Refactor | Single Add flow; advanced bulk import |
| Artifact Sets section | Refactor | Sets list and new detail page |
| Recent Artifacts section | Hide | Library sort/view |
| `/search` | Refactor | Complete, permission-filtered Library |
| Artifact details (object, OWY run, Ursa prefix) | Refactor | Kind-aware overview, contents, metadata, access, activity |
| `/artifacts/dag` | Replace | S3 Browser and contextual relationships |
| `/shares` | Refactor | First-class Sharing center |
| `/shares/{euid}` | Refactor | Dedicated owner/recipient view |
| `/admin/shares` | Hide duplicate | Sharing admin view |
| Literature/search results | Refactor | Preserve specialty; repair runtime and graceful errors |
| Anomalies and detail | Refactor | Admin; distinguish demo records |
| Observability | Refactor | Admin |
| Admin | Refactor | Access, clients/tokens, safe config, health, audit |
| `/graph` wrapper | Hide | Canonical admin/contextual graph |
| Login | Keep | Shared login, compact chrome, real build identity |
| Authentication error | Refactor | Clear recovery |
| TapDB root and overview | Refactor | Consolidate and repair embedding style |
| TapDB graphs, search, object repair | Keep under Admin | Enforced authorization, not just hidden links |
| TapDB templates/create/builder | Keep under Admin | Advanced tooling |
| TapDB audit/help/inventory/Meridian/backups | Keep | Accurate capability labels and admin access |
| TapDB metrics/runtime | Refactor | Embedded status semantics |
| TapDB readiness | Investigate | Browser inspection gap remains explicit |
| TapDB password | Hide | Broker owns credentials |
| S3 Browser | New | Buckets, URI, exact-key navigation, registration, upload/download/delete |
| Set detail | New | Membership, metadata, permissions, sharing/activity |
| Recipient share view | New | Authenticated file/prefix/set access |

## Control ledger

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| D00 | Baseline | Freeze source, runtime, dirty work, caller contracts | IN_PROGRESS | active_product_contract | G0 | primary | Baseline above | | |
| D01 | Plan | Persist approved scope and every page disposition | SUCCESS | historical_docs_only | G1 | primary | This ledger | | Approved assessment and boundaries recorded |
| D02 | Registry | Enforce object/prefix kind and preserve active registration contracts | IN_PROGRESS | feature_implementation | G2 | primary | | | |
| D03 | Registry | Metadata edits, archive, sets and lineage membership | IN_PROGRESS | feature_implementation | G2 | primary | | | |
| D04 | Access | Shared principal context and object/path authorization | IN_PROGRESS | feature_implementation | G2 | primary | | | |
| D05 | Conversion | Explicit audited policy/kind initialization and reversal manifest | IN_PROGRESS | feature_implementation | G2 | primary | | | |
| D06 | Search | Database filtering, permissions, sorting, counts, pagination/export | IN_PROGRESS | feature_implementation | G2 | primary | | | |
| D07 | Sharing | Recipient policies, delegated grants, separate lifetimes/revocation/audit | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D08 | Sharing | Authenticated stable recipient URLs and live folder navigation | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D09 | Storage | Bucket/explicit-location listing, exact-key navigation and inspection | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D10 | Storage | Authorized downloads, uploads, multipart progress and collision handling | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D11 | Storage | Admin reviewed deletion/replacement and partial-operation receipts | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D12 | GUI | Unified Library/Add/S3/Sets/Sharing/Literature shell and page dispositions | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D13 | CLI/API | Public API and authenticated artifacts/sets/shares/storage CLI parity | IN_PROGRESS | feature_implementation | G3 | primary | | | |
| D24 | EUID | First-class EUID-only resolution, browse, download and share in GUI/API/CLI | IN_PROGRESS | active_product_contract | G3 | primary | User amendment 2026-09-12 | | |
| D14 | Admin | Recursive redaction, enforced embedded admin, shared-login ownership | IN_PROGRESS | feature_implementation | G4 | primary | | | |
| D15 | Admin | Access/client management and truthful runtime/provenance | IN_PROGRESS | feature_implementation | G4 | primary | | | |
| D16 | PubMed | Stage key, initialize before adapter, graceful usable search errors | IN_PROGRESS | config_or_startup_contract | G4 | primary | | | |
| D17 | Integrations | Preserve OWY/Ursa/Labcore receipts and correct display semantics | IN_PROGRESS | active_product_contract | G4 | primary | | | |
| D18 | Release | Intended commit, annotated tag, one final image | OPEN | feature_implementation | G5 | primary | | | |
| D19 | Production | Scoped Dewey deployment and runtime/GUI observations | OPEN | config_or_startup_contract | G6 | primary | | | |
| D20 | Acceptance | User accepts deployed Dewey experience | OPEN | active_product_contract | G6 | user | | | |
| D21 | Ursa | Replace browser controls with configured Dewey links; retain mounts/exports | OPEN | feature_implementation | G7 after D20 | primary | | | |
| D22 | Kahlo | Replace navigation with Dewey links; retain inventory/observability | OPEN | feature_implementation | G7 after D20 | primary | | | |
| D23 | Closeout | Evidence, limitations, all-terminal audit and actual completion | OPEN | historical_docs_only | G8 | primary | | | |

## Acceptance coverage (not test authorization)

One-EUID prefix/object registration; unchanged existing identities/receipts; set membership and access boundaries; uncapped registry search; consistent internal/external/owner/delegate/admin authorization; separate share and delivery expiration; live-prefix exceptions; exact S3 keys/pagination/denials; uploads without implicit overwrite; reviewed deletion and partial failures; PubMed success and graceful failure; secret-free configuration; real build identity; readable desktop layouts; later Ursa/Kahlo deep links.

## Execution log

- Implementation started. No tests, tag, build, production write, or sibling changes yet.

## Implementation progress — user status request

Local work remains uncommitted and unaccepted. No tests, lint, coverage, CI,
release build, tag or deployment have run. Production data/configuration has not
been changed by this implementation.

- Added EUID registry APIs and remote authenticated CLI commands; compact GUI
  views consume those APIs.
- Added registry policy predicates, database-side search, metadata lifecycle,
  stable shares, S3 navigation, multipart uploads, reviewed conditional deletion,
  and configuration redaction. Source review and remaining integration work continue.
- Added explicit conversion/reversal tooling and a native pack containing only
  the three new policy/client/operation templates. No conversion has been applied.
- Live host inspection confirmed container `fee0f8d0076eb3af774e61d04ae05a116f98d5b25be957281723c36870afb943`,
  running with zero restarts since 2026-09-11T15:37:51Z, image
  `sha256:7982b35d67ae54f12103d7bec8cf0e4f84de1eb730b0a1138041de1572b2b0a3`.
  Its configured NCBI file path lacks a corresponding container mount.
- SSM inventory command `df9b034d-b20f-4566-8621-c159d7fa8b2b` obtained the
  container evidence, then failed to read the root-owned compose file as ubuntu.
  The remaining compose/config capture requires targeted sudo; this is not a
  service failure and did not change production.
- Local dependency metadata reports boto3 1.43.92 with conditional multipart
  completion and per-object DeleteObjects ETag fields. This is an SDK capability
  inspection, not a test run.
- Remote `10.*` tag inventory remains empty at this refresh.

Remaining: close authorization and legacy-operation gaps; finish administration,
report isolation and GUI details; stage key and complete deployment identity/config;
review actual conversion manifest; publish final tagged image; deploy Dewey only;
observe availability; obtain user acceptance; then perform separate Ursa/Kahlo
cutovers. All release and acceptance rows remain open.

## Accelerated completion plan — 2026-09-12T08:42:05Z

This section controls the remaining execution order. It refines D00–D24 without
replacing their requirements or declaring local implementation accepted. The user
reports stopping a competing agent in this worktree. Primary is the sole assigned
writer; no additional agents are being started. Preserve existing changes rather
than attributing or reverting them based on incomplete agent history.

### Reconciled position

- Fresh source inventory: branch `codex/dewey-labcore-910`, HEAD
  `6c965d7f3681ee19abf801f6786530759400d7d2`; 21 modified tracked files (including
  the pre-existing AGENTS.md change) and 13 untracked implementation/document files.
  Tracked diff statistics omit untracked implementation and are not a completion measure.
- Fresh `git ls-remote --tags origin '10.*'` returned no matches. Target remains
  10.0.0, subject to the final publication check. No release commit/tag/image exists
  for this implementation yet.
- Production remains **last observed**, not freshly reconfirmed here, at 9.1.0 and
  the image recorded above. Refresh its exact identity immediately before deployment.
- Private rollback inputs were successfully captured on the host under
  `/home/ubuntu/dewey_ops/registry10-20260912/` (directory 0700; files 0600).
  SSM receipt `153a97e2-9fd4-47b5-af13-d683b1d70c4d` supersedes the earlier
  compose-read failure. Restore only Dewey fields; other services may have changed.
- The NCBI key was successfully staged at `/home/ubuntu/.config/ncbi/key.txt`,
  mode 0600, through an encrypted SSM tunnel. Receipt
  `96039809-d30a-4efe-8c90-dd20eeaa7718`; receiver and tunnel terminated.
  Container mount and actual PubMed availability remain pending. This corrects
  the earlier “stage key” remaining item; do not copy it again.
- Runtime source inspection confirms EUID operations and major GUI/API/CLI
  implementations exist, but finds remaining interface wiring: CLI access still
  defaults to 900 seconds, GUI share lifetime is hard-coded, registered-location
  pagination is not wired through the GUI, and isolated report preview is absent.
  Presence of source is not proof of correct runtime behavior.
- No tests, lint, coverage, CI campaign, database conversion, new image build or
  deployment has been performed by this implementation. This planning refresh
  performs read-only source/Git inspection and documentation edits only.

### Shortest execution path

Use one focused source-completion pass, one release reconciliation, one final
tagged build, and one bounded Dewey deployment/conversion interval. Do not repeat
the full page survey, redesign the chosen model, create staging deployments, or
run intermediate image builds. Read independent inputs together; keep writes,
conversion and release promotion sequential. Do not remove requirements to make
the ledger appear complete.

The following C rows schedule the parent D rows. A C row becomes SUCCESS only
when its stated evidence exists; parent rows retain their own completion status.

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| C01 | Reconciliation | Record current worktree/tag state and single assigned writer; retain all existing changes | SUCCESS | plan_amendment | G0; D00 | primary | Fresh Git inventory and user report recorded above | Competing agent reported by user; file authorship is not assumed | Source baseline refreshed; no reset, merge or competing agent started |
| C02 | Access and EUID contracts | Finish authorization, identity, ownership, sharing and receipt consistency across new and retained routes | SUCCESS | active_product_contract | G2–G3; D02–D08,D13,D17,D24 | primary | Contract crosswalk; registry_access.py, services/registry.py, auth.py and retained caller entry points | Inconsistent identity and object/path access | Source implementation complete; runtime acceptance remains D19–D20; tests intentionally off |
| C03 | Product completion | Finish the existing GUI/CLI, isolated report access, administration and PubMed wiring | SUCCESS | feature_implementation | G3–G4; D09–D16,D24 | primary | Contract crosswalk; registry_api.py, cli/registry.py, static/registry.js, report_preview.py, ncbi_config.py | Incomplete UI controls, defaults wiring and report preview | Source implementation complete; production observations remain D19; tests intentionally off |
| C04 | Operator readiness | Expose conversion through the owned Dewey CLI; prepare explicit config, reviewed conversion inventory and rollback inputs | IN_PROGRESS | config_or_startup_contract | G2,G4; D00,D05,D15,D16 | primary | Required: native CLI command paths, redacted config delta, manifest digest, ambiguity disposition and reversal procedure | Conversion not yet inspected against actual records; service principals/mount/build identity pending | |
| C05 | Release | Review final source against requirements, commit intended files, publish immutable annotated numeric tag, build/publish exact tagged Dewey image | IN_PROGRESS | feature_implementation | G5; D18; after C02–C04 | primary | Required: intended file manifest, clean release tree, commit, annotated tag target, image digest and build identity | Final implementation and release capsule not ready | |
| C06 | Production | Refresh live identity, quiesce only Dewey, apply exact conversion, promote only its tagged image/config, observe runtime and GUI | OPEN | config_or_startup_contract | G6; D19; after C05 | primary | Required: conversion commit receipt, exact running tag/SHA/digest, restart/availability observations and authenticated GUI evidence | Depends on completed release and reviewed conversion | |
| C07 | Acceptance | Present working Dewey and concrete remaining limitations for user acceptance | OPEN | active_product_contract | G6; D20; after C06 | user | Required: explicit user acceptance of deployed Dewey | Acceptance requires the deployed result | |
| C08 | Integration cutover | Replace only Ursa/Kahlo S3 browser controls with configured URI-preserving Dewey links | OPEN | feature_implementation | G7; D21–D22; after C07 | primary | Required: separately scoped numeric tags, deployed images and observed correct deep links; retained non-browser functions | Explicitly sequenced after Dewey acceptance | |
| C09 | Closeout | Reconcile every parent and completion row, record limitations and actual objective outcome | OPEN | historical_docs_only | G8; D23; after C08 | primary | Required: all rows terminal with evidence; distinguish failed/blocked from achieved | Release, acceptance and peer cutovers remain unfinished | |

### C02 — resolve the release-critical contract gaps first

1. Follow principal/authorization through existing external-reference, relation,
   graph, export, idempotency replay and storage-listing routes. Close any path
   that exposes restricted records or descendant names, or permits an unauthorized
   mutation. Keep OWY/Ursa/Labcore identity and historical receipt contracts intact.
2. Complete explicit owner/admin ownership management; keep metadata and download
   rights independent. Ensure download-only access works without an incidental
   metadata permission requirement. Align set manifests and sharing with each
   member's rights; do not silently share hidden members or grant future set members.
3. Resolve canonical registration identity, including meaningful URL query strings,
   same-location duplicates, concurrency and exact S3 keys. Do not infer prefix
   kind from a slash or change existing EUIDs/identity keys during repair.
4. Use configured share/delivery defaults consistently in all interfaces and
   retained operations. Bound issuance by effective grants, redact recipient
   information for non-managers, and record issuance/access decisions accurately.
5. Review upload/deletion transaction boundaries and uncertain AWS outcomes.
   Preserve collision protection, admin-only replacement/deletion, reviewed
   contents and per-item receipts. Never retry an uncertain mutation blindly.

### C03 — complete the product using the existing shell

1. Wire defaults, ownership, activity, share listing, storage name filtering,
   registered-location pagination, selected-storage-item set registration and
   explicit upload abort/replacement controls. Make EUID entry, resolution,
   contents and access work coherently across GUI/API/CLI.
2. Implement isolated S3 report previews with authorized relative assets. Keep
   untrusted report code outside Dewey's authenticated application context and
   retain authorization on asset delivery; do not solve this by serving active
   HTML in the ordinary application origin.
3. Finish the compact Admin surface and common navigation/recovery links, enforce
   native TapDB admin access and distinguish embedded health from standalone
   probe failures. Preserve the readiness inspection gap until directly observed.
4. Retain the repaired PubMed error surface; complete key mount and initialization
   wiring. Actual returned results, or a precise unresolved upstream failure,
   are required before claiming the search issue resolved.

### C04–C06 — one prepared release and conversion

1. Add the explicit conversion plan/apply/reverse commands to the owned `dewey`
   CLI. Use native `tapdb` template import only through documented delegation.
   Correct the older crosswalk's direct-module operator example before execution;
   no raw database/config fallback is authorized by urgency.
2. Prepare the Dewey-only deployment capsule with explicit existing bearer
   principal mappings, production DB/template bindings, 30-day/900-second defaults,
   `DEWEY_BUILD_BRANCH`, actual tag/SHA, and the read-only NCBI mount. Keep secrets
   and full private configuration off Git and out of tool output.
3. Obtain a read-only conversion inventory now to identify ambiguities before an
   outage. Resolve evidenced rows individually. Capture existing recovery evidence
   and a precise data-conversion reversal, without inventing new backup campaigns.
4. Reconcile source and the crosswalk once; record evidence without running tests,
   lint, coverage or CI. Inspect publication triggers so branch/tag publication
   does not accidentally initiate the prohibited campaign. Preserve unrelated
   AGENTS.md in the working tree; build from the exact committed release tree.
5. Commit only intended release changes and durable ledgers, publish the immutable
   annotated numeric tag, then build/publish that exact revision once. If a final
   build fails, record and fix the concrete cause; never move a published tag.
6. Before promotion, refresh the live compose/image/config identity and preserve
   any sibling changes. Quiesce only the Dewey writer, import only missing new
   templates, generate/reconcile the final manifest while writes are stopped,
   apply the reviewed digest and preserve its committed receipt. Fail on changed
   inventory or new ambiguity rather than silently converting additional records.
7. Start only the final tagged Dewey image with its prepared configuration. Observe
   version/SHA/digest, startup, restarts, normal GUI/login navigation and existing
   read flows. These observations are not a synthetic write/test campaign. Record
   missing role-specific or write acceptance honestly rather than claiming it ran.
8. On failure, distinguish configuration/runtime repair from a conversion reversal.
   An image rollback alone is insufficient after data changes. Preserve accepted
   new records and sibling services; do not restore an old whole-database snapshot.

### Stop conditions and completion reporting

- No fresh user approval is needed for the already authorized implementation and
  Dewey release. Ask only for a concrete unresolved data/product choice or an
  action beyond that authorization. Do not ask for approval of this plan again.
- C07 is the intentional human gate. Ursa/Kahlo changes cannot pass it based on
  elapsed time or a successful health response.
- Report completed row IDs, the current row, the next concrete action and any
  actual blocker. Do not assign a completion percentage from file counts.
- There is no defensible wall-clock ETA until C02–C04 identify the actual remaining
  fixes and conversion ambiguities. The speed commitment is the bounded sequence
  above, immediate execution, and no duplicate surveys or intermediate builds.
- At this refresh: parent ledger **1 SUCCESS, 18 IN_PROGRESS, 6 OPEN**; completion
  sequence **1 SUCCESS, 8 OPEN**. Product objective and production release are
  **not complete**. These counts describe tracking state, not verified feature coverage.


## Final source completion and release preparation — 2026-09-12

- Implemented source crosswalk: authoritative object/prefix kind, EUID-only record
  transactions, policy and path authorization, metadata/archive/ownership, flat sets,
  database-side search and external-reference filters, share modification/revocation,
  independent lifetime defaults, explicit login invitations, personal role-scoped tokens,
  multipart uploads/conditional completion, reviewed conditional deletion, isolated HTML
  report previews with authorized relative assets, compact shared GUI and authenticated CLI.
- Added owned operator commands: `dewey config prepare-registry-release` and
  `dewey db registry-conversion plan|apply|reverse`. Added scoped final-tag release
  generator and Dewey-only prepare/promote operator under
  `docs/plans/evidence/20260912_dewey10/`. These adapt the retained release capsule;
  no intermediate app start or pre-deployment verification stage is included.
- Refreshed production: 9.1.0, recorded immutable image/SHA unchanged, zero restarts.
  Native TapDB operator `replacement-operator.yaml` targets `dewey_prod_tapdb10`,
  namespace `dewey-day`, domain M. Existing container user 0:0 is preserved; host
  commands run as ubuntu with targeted sudo for protected configuration.
- Read-only API inventory reached the existing 2,000-artifact cap and returned 10
  sets. This is not a registry total or a conversion manifest. Receipt
  `4f6ac0fb-28a0-4853-89ac-26b7e7ab7581`; full native inventory remains required.
- Operator inspections `c7dfded5-d700-4c87-97c6-e6d7d0c3d458` (script syntax) and
  `0ef78276-4904-4d67-9c47-10f683dfe8df` (protected-file permission) failed without
  production mutation. Corrected read-only receipts:
  `f91d3aac-146a-4897-bfb3-2f84e24ab838` and
  `e71962b3-53a3-4f2d-9e53-e804963b5750`. No test campaign or billing claim.
- Dependency lock pins boto3/botocore 1.43.93 for conditional multipart completion
  and per-object deletion ETags. No tests, lint, coverage or syntax checks run.
- Remote 10.* tag inventory is still empty. Intended release excludes the unrelated
  AGENTS.md change. Commit uses `[skip ci]`; no PR, merge or broad Dayhoff rollout.
- Sequence clarification: C04 source/operator preparation is complete before tagging;
  its actual conversion inventory uses the final tagged image after C05 build, before
  production promotion. This avoids an intermediate build. Individual ambiguous
  records still require source-backed resolution; image rollback alone is insufficient.
- No real invitations, shares, uploads, replacements or deletions have been invoked
  for validation. User acceptance and Ursa/Kahlo cutovers remain open.


### Release 10.0.0 operator finding and immutable patch

- Published annotated tag 10.0.0 at `a69da97d8eafd78734815d7dc73a5daa2c793c3c`;
  image `sha256:e5a54e5452d2303490f936371377cd1bfeabf501e9b1e75754bb912f8cc53e38`,
  pushed 2026-09-12T09:32:45Z. Exact-tag build succeeded; no tests or CI ran.
- Owned config preparation succeeded: three explicit service principals, new private
  config SHA256 `6cb6f6efa2cccca14e05b4eddc666a137be020bd2bdd7b5df0d42a187f4cd6f3`.
- Actual conversion inventory failed with SQLAlchemy DetachedInstanceError when
  calculating inventory EUIDs after closing its read-only session. No manifest,
  database write or production promotion occurred. Fixed by collecting the inventory
  count/hash inside the transaction. Published tag 10.0.0 remains immutable;
  final release target advances to 10.0.1.
- Native template import requires a real prior export receipt; the new three-template
  definitions cannot legitimately have one before creation. Added owned
  `dewey db registry-templates`, delegating to TapDB's governed loader for exactly
  those three keys, with separately authenticated operator credentials, matching
  runtime target, no overwrite and a native persisted-template export receipt.
  This avoids broad core seeding and fabricated import receipts.
- Prior native export succeeded using the actual bound runtime configuration:
  13 Dewey-owned templates, SHA256
  `12497b41c2074e7bd058013fc78ceea9851ea724fadcf7bc4397f134348a4baa`,
  private `10.0.0/prior-templates.json` and native receipt. Earlier export attempts
  failed because sudo did not retain the explicit AWS files, then because the old
  replacement operator config's runtime role is not bound to this target. No writes.
  Operator authentication remains separate; no role binding is changed.
