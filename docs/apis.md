# Dewey API Surface

This page indexes the HTTP contract in `dewey_service/app.py`, `registry_api.py`,
`fetch.py`, `recipient_api.py` and `report_preview.py` at release 12.0.8. The
configured service's OpenAPI document supplies request schemas; hidden browser
routes are described separately below.

Authentication uses the `daylily-auth-cognito` 2.x library boundaries. The day
deployment uses shared Login as its external broker; direct Cognito mode is a
separate explicit configuration. Cognito lifecycle changes stay in `daycog`.

## API Design Notes

Current design rules that matter to integrators:

- current EUID registry APIs accept authenticated session-or-bearer principals; older service APIs retain the bearer requirements listed below
- management pages and APIs remain on trusted-network ingress; the public ingress exposes only the explicit recipient/auth/content allowlist
- managed-share access requires a current verified email and verified ingress; a recipient grant does not grant management authority
- creates require `Idempotency-Key` where declared; lifecycle edits use explicit revision fields
- search has canonical `/api/search/v2/*` endpoints
- the current repo does not expose a separate public messaging or event-stream API

## Auth Modes

Current auth modes used in this document:

- `none`: no auth required
- `bearer token`: valid Dewey API bearer token required
- `UI session`: a verified browser session through the configured auth mode
- `session or bearer token`: valid session or bearer token accepted
- `admin session`: valid UI session with `ADMIN` role required

## Health And Observability

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/healthz` | `none` | Liveness probe |
| `GET` | `/readyz` | `none` | Readiness plus DB probe |
| `GET` | `/health` | `session or bearer token` | Overall health summary |
| `GET` | `/obs_services` | `session or bearer token` | Advertised Dewey capability surface |
| `GET` | `/api_health` | `session or bearer token` | Request-family rollups |
| `GET` | `/endpoint_health` | `session or bearer token` | Route-template rollups with paging |
| `GET` | `/db_health` | `session or bearer token` | DB probe and slow-operation summary |
| `GET` | `/my_health` | `UI session` | Authenticated self view |
| `GET` | `/auth_health` | `session or bearer token` | Auth-mode rollups |
| `GET` | `/api/anomalies` | `bearer token` | Local anomaly list |
| `GET` | `/api/anomalies/{anomaly_id}` | `bearer token` | Local anomaly detail |

Release 12.0.8 keeps sharing readiness inside
`checks.database.details.sharing_schema` (`verified` or `conversion_required`),
within the pinned Dayhoff readiness schema. This corrects the top-level diagnostic
in 12.0.7; the deployed response passes the unchanged canonical schema.
Readiness still requires both a healthy database and the verified sharing schema.

## Auth Pages And Session UX

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | `none` | Redirects to `/ui` |
| `GET` | `/login` | `none` | Login page |
| `GET` | `/auth/login` | `none` | Starts the configured shared Login or direct Cognito flow |
| `GET` | `/auth/callback` | `none` | Direct Cognito-mode callback; not the day public broker callback |
| `GET` | `/auth/lsmc/callback` | `none` | Completes shared Login broker handoff; validates the saved return path |
| `GET` | `/auth/error` | `none` | Auth error page |
| `GET` | `/auth/logout` | `none` | Logout redirect |
| `POST` | `/auth/logout` | `none` | Logout action |
| `POST` | `/logout` | `none` | Logout alias |

For shared links, browser sign-in returns to the exact permitted fetch path.
Missing/invalid machine credentials return 401 instead of a successful HTML login
page. Routes requiring no application credentials may still be network-restricted.

## Current GUI Entrypoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/ui`, `/search` | `UI session` | Authorized Library |
| `GET` | `/storage` | `UI session` | S3 Browser |
| `GET` | `/sets` | `UI session` | Artifact sets |
| `GET` | `/add`, `/artifacts` | `UI session` | Add/register; actions require the appropriate write authority |
| `GET` | `/records/{euid}`, `/artifacts/euid/{euid}` | `UI session` | Record detail and authorized actions |
| `GET` | `/shares` | `UI session` | Sharing management on trusted-network ingress |
| `GET` | `/shares/{euid}` | `UI session` | Management detail; public/recipient-only callers redirect to canonical fetch |
| `GET` | `/account` | `UI session` | Management account and personal-token controls |
| `GET` | `/recipient/account` | `UI session` | Own finite read-only credentials; recipient surface |
| `GET` | `/literature` | `UI session` | PubMed search and save page |
| `GET` | `/search/export` | `UI session` | Unified Search export |
| `GET` | `/ui/anomalies` | `admin session` | Anomaly list page |
| `GET` | `/ui/anomalies/{anomaly_id}` | `admin session` | Anomaly detail page |
| `GET` | `/ui/observability` | `admin session` | Observability page |
| `GET` | `/tapdb` | `admin session` | Mounted TapDB admin landing page |
| `GET` | `/admin` | `admin session` | Admin page |
| `POST` | `/admin/artifact-storage` | `admin session` | Update managed artifact bucket |

## Literature API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/v1/literature/search` | `UI session` | no |
| `POST` | `/api/v1/literature/save` | `UI session` | yes |
| `PATCH` | `/api/v1/literature/saves/{literature_save_euid}` | `UI session` | yes |
| `GET` | `/api/v1/literature/saves/mine` | `UI session` | no |

Current save request fields:

- `pmid`
- `save_mode`: `auto`, `managed_artifact`, `external_reference`
- `visibility_scope`: `private`, `restricted`, `all_users`
- `allowed_users`
- `allowed_groups`

## Artifacts API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `GET` | `/api/v1/artifacts` | `bearer token` | no |
| `POST` | `/api/v1/artifacts` | `bearer token` | yes |
| `POST` | `/api/v1/artifacts/import` | `bearer token` | yes |
| `POST` | `/api/v1/artifact-prefixes` | `bearer token` | yes |
| `POST` | `/api/v1/artifacts/upload-sessions` | `bearer token` | yes |
| `POST` | `/api/v1/artifacts/upload-sessions/{upload_token}/complete` | `bearer token` | yes |
| `GET` | `/api/v1/artifacts/{artifact_euid}` | `bearer token` | no |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/verify` | `bearer token` | yes |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/lock` | `bearer token` | yes |

Current artifact register fields include:

- artifact identity and storage coordinates
- checksums
- original filename and content type
- producer system and producer object EUID
- storage class and availability status
- freeform metadata

Prefix-only registration uses `POST /api/v1/artifact-prefixes` with `root_uri`, `artifact_type`, optional producer fields, and metadata. It creates one `storage_kind=prefix` artifact and does not expand or list child objects.

Current import fields include:

- `artifact_type`
- `storage_uri` or `source_uri`
- `import_mode`: `copy` or `reference`
- `lock_after_import`
- producer fields
- metadata

Current upload-session flow:

1. create upload session
2. upload bytes to the returned storage target
3. complete the upload session

## Artifact Set API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `GET` | `/api/v1/artifact-sets` | `bearer token` | no |
| `POST` | `/api/v1/artifact-sets` | `bearer token` | yes |
| `POST` | `/api/v1/artifact-sets/analysis/register` | `bearer token` | computed |
| `POST` | `/api/v1/artifact-sets/multiqc/register` | `bearer token` | computed |
| `GET` | `/api/v1/artifact-sets/{artifact_set_euid}` | `bearer token` | no |
| `POST` | `/api/v1/artifact-sets/{artifact_set_euid}/members` | `bearer token` | yes |
| `DELETE` | `/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}` | `bearer token` | yes |

Current create fields:

- `artifact_set_type`
- `label`
- `description`
- `metadata`

QEO/KEO registration fields are defined in
`docs/qeo/QEO_DEWEY_REGISTRATION_CONTRACT.md`. These two endpoints compute their
idempotency key from canonical request JSON; a supplied `Idempotency-Key` must
match that computed key.

## Resolution API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/v1/resolve/artifact` | `bearer token` | no |
| `POST` | `/api/v1/resolve/artifact-set` | `bearer token` | no |

Current resolution is a lookup contract, not a workflow engine.

## Managed Sharing API

### Management And Audit

These endpoints accept the current session-or-bearer principal, enforce creator/
owner/admin policy, and remain on trusted-network ingress. Replace placeholders
with identities returned by Dewey; never construct EUIDs.

| Method | Path | Required concurrency / behavior |
| --- | --- | --- |
| `POST` | `/api/v1/records/{euid}/shares` | `Idempotency-Key`; target is an existing Object, Prefix or Set |
| `POST` | `/api/v1/records/{euid}/shares/preview` | Bounded draft selection; `incomplete` is not a complete inventory |
| `GET` | `/api/v1/registry/shares` | Authorized paginated index |
| `GET`, `PATCH` | `/api/v1/registry/shares/{euid}` | PATCH requires current `policy_revision` |
| `POST` | `/api/v1/registry/shares/{euid}/revoke` | `policy_revision`, optional `reason` |
| `POST` | `/api/v1/registry/shares/{euid}/grants/{grant_euid}/revoke` | Same revision fence; preserves prior grants/history |
| `POST` | `/api/v1/registry/shares/{euid}/invite` | Explicit `email` already covered by the share; separate accepted/failed/uncertain submission receipt |
| `GET`, `POST` | `/api/v1/registry/shares/{euid}/aliases` | POST requires `slug` and `policy_revision` |
| `POST` | `/api/v1/registry/shares/{euid}/aliases/{slug}/revoke` | `policy_revision`; permanently retires the alias |
| `GET` | `/api/v1/registry/shares/{euid}/contents` | Current authorized contents with explicit continuation |
| `GET` | `/api/v1/registry/shares/{euid}/activity` | Append-only event pages; follow `continuation_token` |
| `GET` | `/api/v1/registry/sharing-report` | Finite `starts_at`, optional `ends_at`; owner/status/audience/content/date/age/unused filters |
| `GET` | `/api/v1/registry/sharing-inventory` | Lifecycle rows; preserve `observed_at` and `expected_inventory_sha256` across export pages |
| `POST` | `/api/v1/records/{euid}/location-rebind` | `storage_uri`, `expected_location_revision`, `reason`, optional `version_id`; verifies equivalent content, moves no bytes |

Create fields include `name`, `purpose`, `audience` (`recipients` or
`public_registered`), `allowed_users`, `allowed_domains`, or explicit `grants`,
`include_patterns`, `exclude_patterns`, `denied_emails`, `expires_at`,
`content_mode` (`download` or `www`), `report_entrypoint`, and
`report_bundle_root`. `delivery_modes` admits only `["gateway"]`.

Expiry is scoped to the **original creator and entire audience**. A verified
`lsmc.com`/`lsmc.bio` account creator sharing only with exact `lsmc.com`/`lsmc.bio`
email addresses or domains defaults to no expiry and may choose an explicit finite
expiration. Included subdomains, outside recipients, public registration,
service/unknown creators, and all other creators default to **14 days**, require a
finite future expiration, and have an explicit maximum of **365 days from now**.
An internal administrator editing an external-created share does not change the
original creator's eligibility. Explicit `expires_at: null` or
`lifetime_days: null` is accepted only for eligible internal shares. Positive
`lifetime_days` is validated under the same scope. Grant deadlines cannot outlive
a finite share; omission inherits its deadline. Preview, create, edit and revival
use the same native rules. Ownership and creator verification come from native
authenticated creation/audit records, not client fields.

PATCH can change recipients, targets, filters, content mode and expiry atomically.
For replacement targets, provide a reviewed `targets` list; each entry has
`target_kind` set to `artifact_object` or `artifact_prefix` and `target_euid` set to
the actual persisted identity. Stale policy or location revisions return 409;
no partial new revision is published. A valid share grant supplies recipient access without an independent
artifact ACL. Sharing does not confer management or organization membership.

Slugs use 3–63 lowercase ASCII letters/digits/hyphens with alphanumeric ends;
reserved names and collisions fail. Retired aliases never point to another share.

### Recipient Delivery And Credentials

All recipient endpoints require verified ingress and a current verified-email
identity. Named grants may include pending internal/external addresses. Public
with registration still requires sign-in and email verification.

| Method | Path | Behavior |
| --- | --- | --- |
| `GET`, `HEAD` | `/fetch/{identifier}` and `/fetch/{identifier}/{relative_path}` | Share EUID or active slug; file delivery, directory view or explicit representation |
| `GET` | `/api/v2/recipient/shares/{identifier}` | Sanitized current share summary; no storage coordinates |
| `GET` | `/api/v2/recipient/shares/{identifier}/contents` | Manifest page; `path`, `limit` 1–200, `continuation_token` |
| `POST` | `/api/v2/recipient/shares/{identifier}/preview` | Creates an isolated report context for an authorized HTML entrypoint/bundle |
| `POST` | `/api/v2/recipient/shares/{identifier}/preview/{context_euid}/handoff` | One-time viewer handoff; not a durable shared credential |
| `GET`, `POST` | `/api/v2/recipient/tokens` | List own credentials; create with `name`, `lifetime_days` 1–30, fixed read-only role |
| `POST` | `/api/v2/recipient/tokens/{token_euid}/revoke` | Revoke only the caller's credential |

`?format=manifest` is paginated; follow every continuation to establish
completeness. `?format=tar` inventories the entire selection before streaming an
uncompressed archive. TAR has explicit capacity limits and restarts after
interruption; the CLI supports conditional per-file resume. Single objects resolve
at the root, single prefixes retain relative keys, and multiple targets use
`<target-euid>/<relative-path>` beneath the share root.

File delivery supports HEAD, a single byte range and conditional requests. A WWW
browser entry initializes the isolated viewer; `download=true` requests file
delivery instead. Sidecars remain on the authorized content host. Client-generated
report exports can download there without permitting network form submission.
Current policy applies on each request and TAR member. An admitted individual
response may finish; subsequent requests are denied after revocation.

Known canonical-share resolution 403 decisions are durably audited; unknown or
retired identifiers do not create fabricated lineage. Reports distinguish server
completion/bytes from client receipt, and exact native creation-to-deadline
durations from indefinite lifetimes. Partial event pages are not aggregate totals.

### Retained Service Entrypoints

| Method | Path | Behavior |
| --- | --- | --- |
| `POST` | `/api/v1/shares` | Explicit-target create with `Idempotency-Key` and the schema-3 policy |
| `GET` | `/api/v1/shares/{share_euid}` | Authorized share detail |
| `POST` | `/api/v1/shares/{share_euid}/access-package` | Gateway paths for browser, manifest and TAR; other `delivery_mode` values fail request validation |
| `POST` | `/api/v1/shares/{share_euid}/revoke` | Revision-fenced revoke |
| `GET` | `/api/v1/shares/{share_euid}/audit` | Authorized share history |
| `GET` | `/api/v1/artifacts/{artifact_euid}/shares` | Bearer-authenticated shares index for an artifact |

`POST /api/v1/shares` remains the explicit-target create route for
`artifact_object`, `artifact_prefix`, `artifact_set` or `mixed_set`. Its schema
requires `target_euid` or explicit `targets` as appropriate and uses the same
audience/expiry/gateway rules. Existing share read/revoke/audit and share-root
subset routes retain their declared auth requirements. Access packages now return
authenticated `/fetch/` paths for gateway/manifest/TAR; they do not return S3
presigns or CloudFront cookies. Removed delivery modes fail explicitly.

See [Managed sharing](sharing.md) for limits and examples. The internal and external functional journeys now pass, including restricted
management denial. The [release ledger](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md)
records functional completion separately from formal user signoff.

## Search API

### Canonical endpoints

Omitted or null `scopes` uses the declared artifact/artifact-set default. An
explicit empty list or an unsupported scope is invalid; it does not broaden the
query to default scopes. Empty-list rejection is deployed in 12.0.8.

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/search/v2/query` | `bearer token` | no |
| `POST` | `/api/search/v2/export` | `bearer token` | no |

- `Link: </api/search/v2/query>; rel="successor-version"` or `</api/search/v2/export>; rel="successor-version"`

Current search request fields:

- `q`
- `scopes`
- `page`
- `page_size`
- `sort_field`
- `sort_dir`
- `property_filters`
- `created_at_start`
- `created_at_end`

Current searchable record families:

- `artifact`
- `artifact_set`
- `share`

The current browser uses the Library, Sets and Sharing views over the EUID
registry search API (`/api/v1/registry/search`). The normalized service search
endpoints above remain available with their explicit filters/scopes.

## External Objects API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/v1/external-objects` | `bearer token` | yes |
| `POST` | `/api/v1/external-object-relations` | `bearer token` | yes |
| `GET` | `/api/v1/{target_type}/{target_euid}/external-object-relations` | `bearer token` | no |

Current external-object create fields:

- `external_system`
- `external_object_type`
- `external_object_id`
- `external_uri`
- `metadata`

Current relation fields:

- `target_type`
- `target_euid`
- `external_object_euid`
- `relation_type`
- `metadata`

## TapDB DAG API

The release 12 runtime mounts the pinned TapDB 11.0.9 DAG v2
contract with Dewey administrator authentication or an explicitly configured
dedicated DAG-reader credential on supported reads. The successful mount
manifest is also advertised by `/obs_services`. Missing required configuration
or an unsuccessful native mount prevents startup.

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/dag/manifest` | `admin or configured DAG reader` | Exact mounted DAG v2 manifest |
| `GET` | `/api/dag/v2/object/{euid}` | `admin or configured DAG reader` | Native ownership lookup |
| `GET` | `/api/dag/v2/data` | `admin or configured DAG reader` | Native bounded DAG query |
| `GET` | `/api/dag/v2/search` | `admin or configured DAG reader` | Native bounded search |

The removed v1 endpoints and external graph proxy have no compatibility aliases.
DAG v2 advertises `outbound_fetch: false`; typed persisted external references
remain the owning substrate contract. Current deployment provenance and preserved
database history are recorded in the release ledger; the old Dewey 9 migration
candidate status is historical.

## Idempotency Rules

Endpoints that declare `Idempotency-Key` reject missing keys through their request
validation and return:

- `409` on key reuse with a different request fingerprint
- stored replay responses for safe retries when the same key and payload are reused

Share edits, recipient/share revocation and alias changes instead require the
reviewed `policy_revision`; location rebind requires `expected_location_revision`.
An invitation is an explicit submission with its own outcome receipt. Do not
blindly repeat a mutation whose result is unknown.

## Error Modes

Common current error shapes:

- `400` for malformed requests or missing idempotency header
- `401` for missing or invalid auth
- `403` for denied recipient or management authority
- `404` for missing artifact, set, share, literature save, or external object
- `409` for idempotency, alias, policy/location revision or inventory-drift conflicts
- `410` for explicitly retired delivery operations or archived shares where declared
- `502` for runtime/storage/literature backend failures surfaced by Dewey

## No Public Messaging API

Current Dewey code does not expose:

- a public event bus
- a webhook subscription API
- a streaming message contract
- a queue-consumer management surface

Historical governance documents may describe event families conceptually for the broader platform, but those are not implemented here as a public runtime API.


### Scoped expiry policy and explicit revival

`GET /api/v1/registry/share-expiry-policy` returns the authenticated prospective
creator's proof and scoped rule description. Share-manager detail returns
`expiry_policy` for the **original persisted creator**, including whether the
current no-expiry policy requires explicit review. Historical original-creator
proof may be recovered from the native creation audit; missing proof is bounded.

`GET /api/v1/registry/defaults` preserves the stored `share_lifetime_days` as a
historical setting and explicitly describes its non-authoritative scope in
`share_expiry_policy`. It is not a mutable global no-expiry authorization.
`PATCH /api/v1/registry/defaults` rejects the unsupported `share_lifetime_days`
field; it still supports `delivery_lifetime_seconds` and
`listing_cache_ttl_seconds`. Admin API, server-rendered summary and editor show
the fixed creator/audience rules rather than a global no-expiry toggle.

Inactive shares are not reactivated by PATCH. A manager explicitly calls
`POST /api/v1/registry/shares/{euid}/revive` with:

```json
{
  "policy_revision": 3,
  "expires_at": "2026-11-10T18:00:00+00:00",
  "grant_euids": ["<actual persisted previously-active grant identity>"],
  "reason": "Reviewed recipient and new expiration",
  "reauthorize_public_registered": false
}
```

Revival requires a new **finite** future expiration, the current revision, current
target delegation authority, and explicit selection of existing recipients.
The same original-creator/audience cap applies; an eligible internal finite
expiration may exceed 365 days. Previously revoked individual grants cannot be
selected. A public-with-registration audience requires its separate explicit
reauthorization flag. Targets, patterns and denied rules are retained; revival
cannot add recipients or broaden permissions. It increments policy revision and
activation generation, retains prior revoked/expired audit evidence, retires old
aliases and revokes old report contexts. It creates no automatic notification or
resend. Later recipient additions are separate reviewed policy edits.

New access-package paths carry policy-revision/activation pins; stale pins are
rejected by `/fetch`. Listing cursors and TAR inventories retain revision fences;
report contexts additionally retain permanent activation-generation fences.
Ordinary unversioned canonical URLs remain locators requiring current verified
identity and current grants on every request; they are not bearer credentials.
Personal/API identity credentials retain their separate finite lifetimes.

No source deployment automatically rewrites existing shares. A pre-existing
outside-audience no-expiry policy is a visible exception requiring explicit
review, not an endorsed grandfathered policy. Actual existing-share corrections
or revivals require their separately authorized action and native audit receipt.
