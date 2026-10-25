# Dewey capabilities and feature analysis — 2026-10-25

Status: current-release baseline for review. This document describes existing behavior; it is not a feature implementation plan.

## 1. Executive finding

Dewey already provides an EUID-based artifact registry, S3 browser, sets, managed sharing, authenticated file delivery, isolated HTML-report viewing, identity integration, audit events, literature references, sequencing/result registration, external-object lineage, and operational inspection.

**Internal and external email sharing exists, with material conditions.** A share can contain individual S3 objects, prefixes and their descendants, or multiple object/prefix targets. Email and domain grants can mix internal and external recipients. Managers can change recipient policies, filters and expiration and revoke grants or the share. Creating a grant does not require a recipient lookup or an existing Dewey account. However, access currently requires trusted Tailscale ingress, a verified identity accepted by shared Login, a matching current share grant, and satisfaction of explicit protected-artifact/ancestor restrictions. This is not arbitrary global access based solely on the share grant.

The requested stable `/fetch/<share-euid>/<path>` entrypoint, human slug registration, registration-open audience, indefinite expiration, editing the persisted target membership of an existing share, storage relocation under an unchanged artifact identifier, recursive bulk-download workflow, and aggregate sharing report are not complete existing features. The sections below distinguish these gaps from functionality already present.

## 2. Evidence and verification boundary

| Observation | Result | Evidence |
|---|---|---|
| Live service | `https://dewey.day.lsmc.bio`, deployment `day` | [HTTP observations](evidence/20261025_dewey_sharing_review/http_observations.json) |
| Health at 2026-10-25 21:26:29 UTC / 17:26:29 America/Toronto | HTTP 200, process `ok`, build **11.0.10**, SHA `7f6fde5429741780517cf461a615e5b3e5f102f2` | [Health receipt](evidence/20261025_dewey_sharing_review/health.json) |
| Readiness at 21:26:39 UTC | HTTP 200, process/database `ok` | [Readiness receipt](evidence/20261025_dewey_sharing_review/ready.json) |
| Git release identity | Remote annotated tag `11.0.10` peels to the same build SHA; tag object `a38416b0d4837937852fda95dbed467be7d9cbf0` | [Release source](https://github.com/Daylily-Informatics/dewey/tree/11.0.10) |
| Live API catalog | **105 paths, 114 method/path operations**; title `Dewey Artifact Service`, version `11.0.10` | [Extracted operation inventory](evidence/20261025_dewey_sharing_review/openapi_operations.json), [live OpenAPI](https://dewey.day.lsmc.bio/openapi.json) |
| GUI implementation provenance | Live `registry.js` and `sharing.js` SHA256 values match the release files byte-for-byte | HTTP observations above |
| Browser inspection | Tool returned “The browser access host is unavailable” | Documentation ledger |
| Anonymous access | Main product pages redirect to login; shared Login redirect observed; share/storage API reads return 401; `/fetch` returns 404 | HTTP observations above |
| Static route sweep | 176 route decorators, including duplicate/older handlers and hidden browser/content routes | [Source inventory](evidence/20261025_dewey_sharing_review/source_routes.json) |

**Evidence vocabulary:** “observed” means the read-only live result above; “implemented” means inspected in source matching the live build; “advertised” means present in the live OpenAPI catalog. None means a successful authenticated recipient workflow was exercised. No existing private files, recipient lists, tenant data, or live usage counts were exported. No shares, users, invitations, downloads, tokens, uploads, deletions, tests, release tags, or deployments were created by this review.

This is a comprehensive inventory of Dewey's advertised and source-defined product surface, not a claim of exhaustive authenticated acceptance. Login provisioning, Cognito configuration, content-host deployment, real report rendering, and reachability from a network outside LSMC/Tailscale remain unverified. Embedded TapDB contributes its own mounted routes; the 114-operation count is the main Dewey OpenAPI document, not every route of every mounted application.

## 3. Product-surface inventory

The registry routes are attached before older browser routes in `create_app`; for overlapping paths, the earlier registry handlers define the current GUI. Historical templates and route declarations alone are not evidence of additional usable pages. [Application setup][app], [registry routes][registry-api], [GUI template][ui-template]

| Surface | Existing functionality | Access / limits |
|---|---|---|
| Library: `/ui`, `/search` | Authorized object/prefix registry, search, metadata filters, sorting, pagination, summary projections, EUID lookup | Results are filtered for the current principal before pagination; metadata and download rights are separate |
| Record: `/records/<euid>` | Metadata, storage/reference information, contents, activity, capabilities, owner/permission editing, sharing and authorized access | Source permissions determine available actions; basic record edits accept name, description, metadata, not storage relocation |
| S3 Browser: `/storage` | Configured/authorized buckets and registered locations, bounded prefix/object browsing, object details, downloads, registration, selected-location sets, upload | Browsing does not recursively register descendants; S3 write operations require internal write authority |
| Sets: `/sets` | Named selections of persisted object/prefix EUIDs; create, inspect, add members, share | No nested sets in the registry contract; removal is blocked by deletion policy |
| Sharing: `/shares` | Search and page accessible/managed shares; create through a record, edit, revoke, inspect activity | Share owner/admin management; recipients see a sanitized view. Share page visibility does not grant all file access |
| Recipient page: `/shares/<share-euid>` | Filtered files, downloads, explicit raw presign issuance, report viewing | Current grants and per-path checks; no anonymous browsing |
| Add: `/add` | Explicit object, prefix, URL-reference, set registration and new-key uploads | Writable principals; idempotent registry creation |
| Literature: `/literature` | PubMed search, reference saves, authorized saved-literature discovery | Shared literature service also supports managed full-text acquisition where configured/available; provider failures are explicit |
| Account: `/account` | Personal tokens, expiry, revocation, CLI setup | Token displayed once; 1–90-day lifetime, role cannot exceed issuer; token scope is role-based, not a new per-share credential type |
| Admin: `/admin` | Effective redacted configuration, release identity, persisted sharing/cache defaults, links to operational tools | Admin only; displayed legacy repair/backup wording does not override read-only TapDB policy |
| Operational pages: `/ui/observability`, `/ui/anomalies` | Service/runtime diagnostics and anomaly inspection | Admin/session gates; no share analytics dashboard established |
| Embedded substrate: `/tapdb/`, `/graph` | TapDB object, lineage, audit and graph inspection | Admin-facing; embedded web mutations are blocked |
| API documentation: `/docs`, `/redoc`, `/openapi.json` | Current operation/schema descriptions | Observed anonymously accessible; an advertised operation can still be disabled by middleware |

## 4. Capability catalog and interface crosswalk

`GUI` refers to the source-defined interface above, not an authenticated browser validation. CLI families below are inspected command registrations; they were not executed.

| ID | Capability | API / GUI / CLI | Current behavior and boundary |
|---|---|---|---|
| CAP-01 | Durable artifact identity | `/api/v1/records`; Library/Add; `dewey artifacts register/get` | One persisted EUID for an explicit object/prefix; optional S3 version ID. HTTP(S) references are registrable objects. EUIDs are assigned by the owning substrate, not synthesized by clients. [Registry][registry] |
| CAP-02 | Sets | `/records/.../members`, `/artifact-sets`; Sets; `dewey sets` | Explicit object/prefix relationships; no implicit descendant registration or nested registry sets. Add supported, remove prohibited. [Registry][registry], [deletion policy][deletion] |
| CAP-03 | Metadata and policy | Record PATCH, permissions and owner routes; Record editor; artifact/set update/permissions/owner | Independent metadata/download audiences; owner/delegated edit/share rules; owner transfer and native activity. Record metadata edit does not change bucket/key/version. [Access policy][access], [registry][registry] |
| CAP-04 | Search and export | Registry search/counts, search v2 query/export; Library/Sets; CLI search | Authorized filters, pagination, summary/full projections, facets/counts, bounded export with truncation reporting. Not an unlimited S3 content scan. [Registry][registry], [search][search] |
| CAP-05 | Storage navigation | Storage buckets/object/browse routes; S3 Browser; `dewey storage buckets/browse/object` | Bounded metadata listing, continuation, explicit refresh/cache controls; storage visibility follows current authorization. [Storage service][storage] |
| CAP-06 | Direct record delivery | Record/storage access; Download/open; `artifacts access` | Lazy access issuance, including S3 signed delivery and external URL references under record policy. This is distinct from managed-share gateway authorization. [Storage service][storage] |
| CAP-07 | Upload/import | Storage multipart operations, artifact import/upload sessions; Add/S3 Browser; storage upload | Upload new objects and register references; multipart state/receipts. Existing-object replacement and abort are currently prohibited. [Storage service][storage], [artifact service][artifacts] |
| CAP-08 | Managed sharing targets | Record shares and `/api/v1/shares`; Share editor; `shares create` | S3 object, prefix, artifact set, mixed targets. Managed share members must be S3-backed; arbitrary HTTP reference registration does not make external content a governed share. [Sharing][sharing] |
| CAP-09 | Recipients | Explicit email/domain grants; Share editor; policy JSON | Mix internal/external recipients; exact domain match by default, optional subdomains; recipient-specific filters, targets and expiry. Group grants and unrestricted authenticated audiences are rejected by canonical share logic. [Share policy][policy] |
| CAP-10 | New-recipient invitation | Registry share invite; explicit invitation action; `shares invite` | Grant creation does not require account existence. Separate invitation POST calls registered shared Login and records sending/sent/uncertain-failure state. Actual provisioning/verification is owned by Login and was not exercised. [Invitation implementation][invite] |
| CAP-11 | Recursive selection | Share contents and preview; filtered browse; `shares contents/preview` | Prefixes include matching descendants at any depth. Share and grant includes/excludes are combined. Listing is paginated; selection preview is not a completed download manifest. [Sharing][sharing] |
| CAP-12 | Share editing | PATCH registry share; Edit share; `shares update` | Name, purpose, audience grants, filters, delivery modes, denies and deadline can change with current `policy_revision`. Persisted member targets cannot be added/replaced/removed by this PATCH. [Share editing][edit] |
| CAP-13 | Expiry and revocation | Share/grant revoke routes; GUI controls; CLI revoke/revoke-grant | Finite deadlines; grant expiry no later than share expiry. Expired/revoked shares cannot be reactivated. Concurrent stale revisions reject with 409. No indefinite share representation. [Share editing][edit], [policy][policy] |
| CAP-14 | Authenticated file gateway | GET/HEAD `/shares/<share-euid>/files/<target-euid>?relative_key=...`; Download; `shares download` | Streams S3 bytes through Dewey, single Range and HTTP conditional support, current authorization per request. Limits in source: eight concurrent streams per process, two per subject. [Gateway][gateway] |
| CAP-15 | Presigned delivery | Registry share presign/access-package; optional GUI presign; `shares presign` | Explicitly enabled per share. Default 900s, maximum 3600s, capped by share/grant expiry. Anyone holding an issued S3 URL can consume it until expiry without Dewey login. [Sharing][sharing] |
| CAP-16 | HTML reports and assets | Share preview/handoff/content routes; View report; `shares report` | Explicit entry HTML plus bundle root; per-context isolated origin, one-use handoff, host cookie and per-asset reauthorization. CLI report returns the share browser URL, not rendered content or a portable fetch deep link. [Report source][report] |
| CAP-17 | Share events | Share activity/audit; Load activity/export loaded JSON; `shares activity` | Append-only native event records and lineage for policy/access/issuance/server transfer outcomes. Paginated manager view; no aggregate lifecycle report. [Sharing][sharing], [gateway][gateway] |
| CAP-18 | Share roots/subsets | `/api/v1/share-roots` and subsets | Explicit root URI and bounded-target subset admission; root does not auto-register children. Resulting shares retain the same managed-share restrictions. [Sharing][sharing] |
| CAP-19 | Personal API access | Account token create/list/revoke; Account GUI; CLI consumes private token file | Current personal token identity can use share gateway with required ingress. Generic configured service credentials have no human email and are rejected by the managed-share context. Personal-token authentication reads the local token record, including the identity/roles captured at issuance; live broker account/email revalidation is not shown in that path. [Tokens][tokens], [share context][context] |
| CAP-20 | Literature reference workflow | Literature search/save/visibility/mine; Literature GUI | PubMed/PMID/DOI/PMCID enrichment, existing-artifact/reference reuse, user save overlays and visibility; managed full text depends on permitted upstream availability. [Literature service][literature] |
| CAP-21 | Sequencing-run/result registration | v1 sequencer-runs and analysis-results registration | Prefix/evidence pointers, selected downstream files, deterministic registration, terminal result sets and native outbox events; registration is not proof of transfer completion or scientific QC. [Registration contract][runs] |
| CAP-22 | Labcore owner integration | `/api/v2/sequencer-runs/register` advertised live | Separately configured service credentials and canonical owner registration; mounted only with explicit configuration. No live registration was submitted. [Owner API][owner-api] |
| CAP-23 | Analysis/MultiQC sets and resolvers | Analysis/MultiQC set registration; resolve artifact/set/multiqc | Existing registration/resolution contracts support consumers locating artifacts by durable identity. Resolver success is not evidence of report rendering or share entitlement. [Set registration][sets-source], live API inventory |
| CAP-24 | External-object lineage and DAG | External objects/relations, artifact graph/parents/children, DAG v2 | Typed external references and native lineage; DAG publication/read access has its own authenticated contract. EUID strings in metadata are not authoritative relationships. [External objects][external], [TapDB integration][tapdb] |
| CAP-25 | Kahlo annotations | `/api/v1/annotations/...` | Operation-bound human authorization, managed new-object upload/resume/complete, artifact resolution/access; up to 50 MiB in the documented annotation contract. No general upload permission or object replacement implied. [Annotation contract][annotations] |
| CAP-26 | Operational observability | Health/readiness, service/API/endpoint/DB/auth health, anomalies | Availability, identity, database and operational diagnostics. Health success does not prove delivery, recipient policy, analytics completeness, or acceptance. [Application][app] |
| CAP-27 | Configuration and lifecycle tools | `dewey config`, `db`, `server`, `tapdb`, `cognito`, `qeo`, quality/test command families | Explicit configs; DB/template/conversion controls; process lifecycle; delegated substrate/identity operations and QEO outbox/resolver utilities. Presence of a tool is not authority to execute it. [CLI source][cli] |
| CAP-28 | Preferences | `/api/v1/me/preferences` GET/PUT | Shared-broker preference contract; separate from artifact or share policy. [Application][app] |
| CAP-29 | Deletion prohibition | Middleware plus service rejection | All DELETE requests, record archive, S3 deletion review/execute, upload abort/replacement, and embedded TapDB mutations are prohibited for all roles. Share/token revocation remains allowed and retains records. [Deletion source][deletion] |

## 5. Sharing semantics that matter to users

### Authorization and new users

1. The creator must be writable and have the right to share each target. Creating an email grant validates its shape; it does not look up a recipient's pre-existing ACL or require their account to exist.
2. A recipient must subsequently establish a shared Login identity. The external-share entitlement allows a non-internal email through Dewey's domain gate with read-only service access. This does not confer general S3 rights. [Broker principal][auth]
3. Every managed request also requires trusted Tailscale ingress, the configured host/origin and a non-service principal with subject/email. Thus sharing an email does not itself admit an arbitrary internet user to the network. [Context][context], [host boundary][routing]
4. Current `_protected_share_path` checks independently restricted records and registered ancestors. Those can deny a valid share recipient who lacks direct metadata/download permission. This is a substantive mismatch with the requested share-grant-as-authority model. [Protected path implementation][protected]
5. Owners/admins can manage a share but do not bypass recipient grants when reading its files. Revoking one grant does not revoke another independently applicable grant or access through another share.

### Scope, membership and expiration

- Prefix selection is **live**: future matching keys are included. A share made from a set freezes the reviewed member target EUIDs; later set additions do not join that existing share. A prefix among those fixed members remains live. Neither behavior freezes S3 bytes.
- Filters can add/remove eligible paths inside existing prefix targets. They cannot add a new persisted target to the share. Share-wide excludes constrain every grant; one grant's exclusions do not cancel another grant's independent allowance. `denied_emails` denies that email across this share.
- Matching is case-sensitive, root-relative and literal apart from documented globs: `*` stays within a segment, `**` crosses segments, `?` matches one non-separator. Preserve exact S3 key spelling; do not normalize repeated separators or spaces.
- All shares have finite timezone-bearing deadlines. Omission selects the persisted service default, not infinity. Source settings provide a 30-day initialization default and 3650-day ceiling; the effective persisted production values were not read in this unauthenticated review.
- Contents return at most 200 visible items per page with a bounded candidate scan and continuation token. An empty filtered page can still have more data. An access package fails when contents exceed its single bounded page; it is not a complete recursive export of an arbitrary prefix. [Sharing][sharing], [settings][settings]

### Downloads and WWW reports

A current gateway URL stays on Dewey and accepts session or personal-token authorization, so authenticated curl/wget use is possible in principle. The CLI implements single-file streaming, refuses overwrite and reports length mismatches. It has no recursive tree downloader or archive endpoint. A bare URL without credentials is not equivalent to an authorized machine request.

Raw presigns are intentionally different: Dewey audits their issuance, then S3 serves the holder. Revocation prevents new issuance but cannot retract a previously issued link before its effective expiry. This conflicts with a strict requirement that every consumer must be a registered identity; the new specification must explicitly resolve that conflict.

Report viewing supports a selected HTML file and permitted relative sidecar files within an explicit bundle root. A single-object share does not silently include siblings. The report runs on a separate per-context content origin; a short-lived handoff and Secure HttpOnly cookie authorize assets. Contexts expire within 900 seconds or the earlier grant/session deadline. Current CSP excludes workers, nested frames and form submission. Arbitrary report compatibility, cross-origin resources and absolute-root URLs are not guaranteed. The stable recipient URL is the share page, not `/fetch/<share-euid>/multiqc.html`. [Report][report], [preview sessions][sessions]

### Audit precision

Share history includes creation, policy revision, recipient/share revocation, contents/access decisions, report context events, raw presign issuance, gateway authorization, server bytes, response completion and disconnect/failure. Events link to native share/grant/target objects where known. Activity retrieval is manager-only and paginated.

`response_completion_observed` means the server sent the response; it does **not** prove a recipient persisted the file. The gateway explicitly records `download_completion_observed: false`. Presign issuance does not prove S3 consumption. Separate HEAD, conditional, Range, HTML-asset and file requests when designing download statistics. No existing aggregate “how many shares by type/duration/age/access/download” product report was found. [Gateway][gateway], [event implementation][sharing]

## 6. Important limits and documentation drift

| Finding | Consequence |
|---|---|
| `ShareRequest.audience` schema still lists `internal` and `authenticated`, while `share_registry` and canonical policy reject them | The live schema enum is not proof of registration-open sharing |
| OpenAPI retains deletion and archive operations; CLI registrations retain related command names | Those operations are denied, even to admins; do not document them as usable features |
| CloudFront signer helpers/configuration remain in source | Canonical managed shares accept only `gateway` and `presigned`; helper existence does not establish a usable CloudFront sharing mode |
| README at the baseline still describes an older TapDB dependency | Actual release `pyproject.toml` pins TapDB Git tag `11.0.9`; source wins over old descriptive text |
| Older GUI guides/handlers coexist with the current registry interface | Use current registration order and UI source for the active page description |
| Immutable EUID resolution exists, but record edit only permits metadata/name/description | No reviewed API workflow was found for moving backing S3 content while preserving the same artifact EUID and existing shares |
| Generic service principals are distinct from personal user tokens | Do not assume a service API key can consume a human managed share |
| Domain recipient grants exist; domain-to-organization onboarding is elsewhere | No evidence here establishes safe automatic tenant creation/join or email-confirmation behavior in deployed Login/Cognito |

## 7. What was not established

- Counts of current shares, recipients, artifacts, downloads or storage bytes; actual persisted lifetime defaults.
- Successful new external-recipient registration, verified-mailbox proof, invitation delivery, cross-tenant access, or public-network access.
- Functional report/sidecar viewing, Range transfer, recursive collection, revocation during use, or analytics reconciliation in production.
- Full embedded TapDB route inventory or acceptance of adjacent Login, Cognito, QEO, Kahlo, Atlas, Bloom, Ursa or infrastructure services.

These are evidence limits, not conclusions that the corresponding source functionality is broken. They must remain visible in the later gap/acceptance work.

## 8. Complete live OpenAPI operation inventory

The following inventory is extracted from the live document, not reconstructed from older docs. “Advertised” does not mean all parameters/delivery modes work or that the operation is authorized for the reader. Disabled and retired exceptions are marked. Hidden GUI/content routes are covered above and in the separate static inventory.

| Method | Path | Operation / qualification |
|---|---|---|
| `HEAD` | `/shares/{share_euid}/files/{target_euid}` | Share File |
| `GET` | `/shares/{share_euid}/files/{target_euid}` | Share File |
| `POST` | `/api/v1/records/{euid}/preview` | Retired Record Preview — retired; use explicit managed share |
| `POST` | `/api/v1/registry/shares/{share_euid}/preview` | Create Preview |
| `POST` | `/api/v1/registry/shares/{share_euid}/preview/{context_euid}/handoff` | Issue Handoff |
| `POST` | `/api/v1/registry/shares/{share_euid}/presign` | Share Presign |
| `PATCH` | `/api/v1/records/{euid}/owner` | Owner |
| `POST` | `/api/v1/records` | Register |
| `GET` | `/api/v1/records/{euid}` | Resolve |
| `PATCH` | `/api/v1/records/{euid}` | Edit |
| `GET` | `/api/v1/records/{euid}/metadata` | Record Metadata |
| `GET` | `/api/v1/records/{euid}/activity` | Record Activity |
| `GET` | `/api/v1/records/{euid}/members` | Record Members |
| `POST` | `/api/v1/records/{euid}/members` | Add Member |
| `POST` | `/api/v1/records/{euid}/archive` | Archive — prohibited by deletion policy |
| `PATCH` | `/api/v1/records/{euid}/permissions` | Permissions |
| `GET` | `/api/v1/records/{euid}/contents` | Contents |
| `DELETE` | `/api/v1/records/{euid}/members/{member_euid}` | Remove Member — prohibited by deletion policy |
| `POST` | `/api/v1/records/{euid}/access` | Access |
| `POST` | `/api/v1/records/{euid}/shares` | Share |
| `POST` | `/api/v1/records/{euid}/shares/preview` | Preview Selection |
| `POST` | `/api/v1/registry/search` | Search |
| `POST` | `/api/v1/registry/search/counts` | Search Counts |
| `GET` | `/api/v1/registry/shares` | Share Index |
| `GET` | `/api/v1/registry/shares/{euid}` | Share Detail |
| `PATCH` | `/api/v1/registry/shares/{euid}` | Share Edit |
| `GET` | `/api/v1/registry/shares/{euid}/contents` | Share Contents |
| `GET` | `/api/v1/registry/shares/{euid}/activity` | Share Activity |
| `POST` | `/api/v1/registry/shares/{euid}/grants/{grant_euid}/revoke` | Revoke Grant |
| `POST` | `/api/v1/registry/shares/{euid}/revoke` | Share Revoke |
| `POST` | `/api/v1/registry/shares/{euid}/invite` | Invite |
| `GET` | `/api/v1/storage/buckets` | Buckets |
| `GET` | `/api/v1/storage/object` | Object Detail |
| `POST` | `/api/v1/storage/access` | Storage Access |
| `POST` | `/api/v1/storage/uploads` | Upload |
| `PUT` | `/api/v1/storage/uploads/{euid}/parts/{number}` | Part |
| `POST` | `/api/v1/storage/uploads/{euid}/complete` | Complete |
| `POST` | `/api/v1/storage/uploads/{euid}/abort` | Abort — prohibited by deletion policy |
| `POST` | `/api/v1/storage/deletions/preview` | Deletion Preview — prohibited by deletion policy |
| `POST` | `/api/v1/storage/deletions/{euid}/execute` | Deletion Execute — prohibited by deletion policy |
| `GET` | `/api/v1/storage/operations/{euid}` | Operation |
| `GET` | `/api/v1/account/tokens` | Tokens |
| `POST` | `/api/v1/account/tokens` | Token Create |
| `GET` | `/api/v1/registry/admin` | Administration |
| `GET` | `/api/v1/registry/defaults` | Defaults |
| `PATCH` | `/api/v1/registry/defaults` | Change Defaults |
| `POST` | `/api/v1/account/tokens/{euid}/revoke` | Token Revoke |
| `POST` | `/api/v1/annotations/uploads/{operation_id}` | Create |
| `POST` | `/api/v1/annotations/uploads/{operation_id}/resume` | Resume |
| `POST` | `/api/v1/annotations/uploads/{operation_id}/complete` | Complete |
| `POST` | `/api/v1/annotations/artifacts/{euid}/context` | Context |
| `GET` | `/api/v1/annotations/artifacts/{euid}` | Resolve |
| `POST` | `/api/v1/annotations/artifacts/{euid}/access` | Access |
| `POST` | `/api/v2/sequencer-runs/register` | Register |
| `GET` | `/api/dag/manifest` | Dag V2 Manifest |
| `GET` | `/api/dag/v2/object/{euid}` | Dag V2 Object |
| `GET` | `/api/dag/v2/data` | Dag V2 Data |
| `GET` | `/api/dag/v2/search` | Dag V2 Search |
| `GET` | `/healthz` | Healthz |
| `GET` | `/readyz` | Readyz |
| `GET` | `/health` | Health |
| `GET` | `/obs_services` | Obs Services |
| `GET` | `/api_health` | Api Health |
| `GET` | `/endpoint_health` | Endpoint Health |
| `GET` | `/db_health` | Db Health |
| `GET` | `/my_health` | My Health |
| `GET` | `/api/v1/me/preferences` | Current User Preferences |
| `PUT` | `/api/v1/me/preferences` | Update Current User Preferences |
| `GET` | `/auth_health` | Auth Health |
| `GET` | `/api/anomalies` | List Anomalies |
| `GET` | `/api/anomalies/{anomaly_id}` | Get Anomaly |
| `POST` | `/api/v1/literature/search` | Literature Search |
| `POST` | `/api/v1/literature/save` | Literature Save |
| `PATCH` | `/api/v1/literature/saves/{literature_save_euid}` | Literature Save Visibility |
| `GET` | `/api/v1/literature/saves/mine` | My Literature Saves |
| `GET` | `/api/v1/artifacts/{artifact_euid}` | Get Artifact |
| `GET` | `/api/v1/artifacts/{artifact_euid}/children` | Get Artifact Children |
| `GET` | `/api/v1/artifacts/{artifact_euid}/parents` | Get Artifact Parents |
| `GET` | `/api/v1/artifacts/{artifact_euid}/graph` | Get Artifact Graph |
| `GET` | `/api/v1/storage/browse` | Browse Storage Prefix |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/verify` | Verify Artifact Storage |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/lock` | Lock Artifact Storage |
| `GET` | `/api/v1/artifacts` | List Artifacts |
| `POST` | `/api/v1/artifacts` | Register Artifact |
| `POST` | `/api/v1/artifacts/import` | Import Artifact |
| `POST` | `/api/v1/artifact-prefixes` | Register Artifact Prefix |
| `POST` | `/api/v1/artifacts/import-run-prefix` | Import Run Prefix |
| `POST` | `/api/v1/sequencer-runs/register` | Register Sequencer Run |
| `POST` | `/api/v1/analysis-results/register` | Register Analysis Results |
| `POST` | `/api/v1/artifacts/upload-sessions` | Create Upload Session |
| `POST` | `/api/v1/artifacts/upload-sessions/{upload_token}/complete` | Complete Upload Session |
| `GET` | `/api/v1/artifact-sets/{artifact_set_euid}` | Get Artifact Set |
| `GET` | `/api/v1/artifact-sets` | List Artifact Sets |
| `POST` | `/api/v1/artifact-sets` | Create Artifact Set |
| `POST` | `/api/v1/artifact-sets/analysis/register` | Register Analysis Artifact Set |
| `POST` | `/api/v1/artifact-sets/multiqc/register` | Register Multiqc Artifact Set |
| `POST` | `/api/v1/artifact-sets/{artifact_set_euid}/members` | Add Artifact Set Member |
| `DELETE` | `/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}` | Remove Artifact Set Member — prohibited by deletion policy |
| `POST` | `/api/v1/resolve/multiqc` | Resolve Multiqc |
| `POST` | `/api/v1/resolve/artifact` | Resolve Artifact |
| `POST` | `/api/v1/resolve/artifact-set` | Resolve Artifact Set |
| `POST` | `/api/v1/shares` | Create Share |
| `GET` | `/api/v1/shares/{share_euid}` | Get Share |
| `POST` | `/api/v1/shares/{share_euid}/access-package` | Create Share Access Package |
| `POST` | `/api/v1/shares/{share_euid}/revoke` | Revoke Share |
| `GET` | `/api/v1/shares/{share_euid}/audit` | List Share Audit |
| `POST` | `/api/v1/share-roots` | Create Share Root |
| `POST` | `/api/v1/share-roots/{share_root_euid}/subsets` | Create Share Root Subset |
| `GET` | `/api/v1/artifacts/{artifact_euid}/shares` | List Artifact Shares |
| `POST` | `/api/search/v2/query` | Search V2 Query |
| `POST` | `/api/search/v2/export` | Search V2 Export |
| `POST` | `/api/v1/external-objects` | Create External Object |
| `POST` | `/api/v1/external-object-relations` | Attach External Object Relation |
| `GET` | `/api/v1/{target_type}/{target_euid}/external-object-relations` | List External Object Relations |

## Immutable source references

All source references below are pinned to the observed release `11.0.10`.

[app]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/app.py
[registry-api]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/registry_api.py
[registry]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py
[ui-template]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/templates/registry.html
[sharing]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py
[policy]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/share_policy.py
[edit]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py#L590
[invite]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L364
[protected]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py#L305
[auth]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/auth.py#L303
[context]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_context.py
[routing]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_routing.py
[access]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/registry_access.py
[gateway]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_gateway.py
[report]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/report_preview.py
[sessions]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/preview_sessions.py
[tokens]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L618
[storage]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry_storage.py
[artifacts]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/artifacts.py
[search]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/search.py
[literature]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/literature.py
[runs]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/docs/sequencer_run_registration.md
[owner-api]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/labcore_owner_api.py
[sets-source]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/artifact_set_registration.py
[external]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/external_objects.py
[tapdb]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/integrations/tapdb_ui.py
[annotations]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/docs/managed_annotations.md
[settings]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/settings.py
[deletion]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/deletion_policy.py
[cli]: https://github.com/Daylily-Informatics/dewey/tree/11.0.10/dewey_service/cli
[project]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/pyproject.toml
