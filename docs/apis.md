# Dewey API Surface

This page documents the current HTTP contract implemented in `dewey_service/app.py`.

## API Design Notes

Current design rules that matter to integrators:

- the main registry API is bearer-token protected
- GUI pages use Cognito-backed browser sessions
- most write endpoints require `Idempotency-Key`
- search has canonical `/api/search/v2/*` endpoints plus deprecated `/api/v1/search/v2/*` aliases
- the current repo does not expose a separate public messaging or event-stream API

## Auth Modes

Current auth modes used in this document:

- `none`: no auth required
- `bearer token`: valid Dewey API bearer token required
- `UI session`: Cognito-backed browser session required
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

## Auth Pages And Session UX

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | `none` | Redirects to `/ui` |
| `GET` | `/login` | `none` | Login page |
| `GET` | `/auth/login` | `none` | Starts Cognito login |
| `GET` | `/auth/callback` | `none` | Completes Cognito callback |
| `GET` | `/auth/error` | `none` | Auth error page |
| `GET` | `/auth/logout` | `none` | Logout redirect |
| `POST` | `/auth/logout` | `none` | Logout action |
| `POST` | `/logout` | `none` | Logout alias |

## GUI Pages

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/ui` | `UI session` | Dashboard |
| `POST` | `/ui/register` | `UI session` | Dashboard quick-register action |
| `GET` | `/artifacts` | `UI session` | Full artifact console |
| `GET` | `/artifacts/euid/{artifact_euid}` | `UI session` | Artifact detail page |
| `GET` | `/artifacts/bulk-template.tsv` | `UI session` | Bulk TSV template |
| `POST` | `/artifacts/register` | `UI session` | Artifact intake workflow |
| `POST` | `/artifacts/bulk-upload` | `UI session` | Bulk TSV intake |
| `POST` | `/artifacts/search` | `UI session` | Artifact search page action |
| `POST` | `/artifacts/search/export` | `UI session` | Artifact search export |
| `POST` | `/artifacts/download` | `UI session` | ZIP download of selected artifacts |
| `POST` | `/artifacts/euid/{artifact_euid}/download` | `UI session` | Direct artifact download/share redirect |
| `POST` | `/artifacts/share` | `UI session` | Generate artifact links |
| `POST` | `/artifacts/sets/create` | `UI session` | Create set from current selection |
| `POST` | `/artifacts/sets/search` | `UI session` | Artifact-set search page action |
| `POST` | `/artifacts/sets/export` | `UI session` | Artifact-set export |
| `POST` | `/artifacts/sets/share` | `UI session` | Share selected artifact set |
| `GET` | `/literature` | `UI session` | PubMed search and save page |
| `GET` | `/search` | `UI session` | Unified Search page |
| `GET` | `/search/export` | `UI session` | Unified Search export |
| `GET` | `/ui/anomalies` | `UI session` | Anomaly list page |
| `GET` | `/ui/anomalies/{anomaly_id}` | `UI session` | Anomaly detail page |
| `GET` | `/ui/observability` | `UI session` | Observability page |
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
| `GET` | `/api/v1/artifact-sets/{artifact_set_euid}` | `bearer token` | no |
| `POST` | `/api/v1/artifact-sets/{artifact_set_euid}/members` | `bearer token` | yes |
| `DELETE` | `/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}` | `bearer token` | yes |

Current create fields:

- `artifact_set_type`
- `label`
- `description`
- `metadata`

## Resolution API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/v1/resolve/artifact` | `bearer token` | no |
| `POST` | `/api/v1/resolve/artifact-set` | `bearer token` | no |

Current resolution is a lookup contract, not a workflow engine.

## Share Reference API

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/v1/share-references` | `bearer token` | yes |
| `GET` | `/api/v1/share-references/{share_reference_euid}` | `bearer token` | no |
| `GET` | `/api/v1/artifacts/{artifact_euid}/share-references` | `bearer token` | no |

Current create fields include:

- `target_type`: `artifact` or `artifact_set`
- `target_euid`
- `purpose`
- `scope`
- `expires_at`
- `issued_by`
- `transport`
- `transport_config`
- `ttl_seconds`

Current transport behavior:

- artifacts: `presigned_s3` only
- artifact sets: `presigned_s3`, `rclone_http`, or `rclone_sftp`

## Search API

### Canonical endpoints

| Method | Path | Auth | `Idempotency-Key` |
| --- | --- | --- | --- |
| `POST` | `/api/search/v2/query` | `bearer token` | no |
| `POST` | `/api/search/v2/export` | `bearer token` | no |

### Deprecated aliases

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/api/v1/search/v2/query` | `bearer token` | Deprecated alias for `/api/search/v2/query` |
| `POST` | `/api/v1/search/v2/export` | `bearer token` | Deprecated alias for `/api/search/v2/export` |

Current alias response headers:

- `Deprecation: true`
- `Sunset: Wed, 30 Sep 2026 00:00:00 GMT`
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
- `share_reference`

The browser Unified Search page currently focuses on artifacts and share references. Artifact-set search is currently more explicit in the Artifacts page.

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

## Idempotency Rules

Current code requires `Idempotency-Key` on most write endpoints and returns:

- `400` when the header is missing where required
- `409` on key reuse with a different request fingerprint
- stored replay responses for safe retries when the same key and payload are reused

## Error Modes

Common current error shapes:

- `400` for malformed requests or missing idempotency header
- `401` for missing or invalid auth
- `403` for admin-only session surfaces
- `404` for missing artifact, set, share, literature save, or external object
- `409` for idempotency or ownership conflicts
- `502` for runtime/storage/literature backend failures surfaced by Dewey

## No Public Messaging API

Current Dewey code does not expose:

- a public event bus
- a webhook subscription API
- a streaming message contract
- a queue-consumer management surface

Historical governance documents may describe event families conceptually for the broader platform, but those are not implemented here as a public runtime API.
