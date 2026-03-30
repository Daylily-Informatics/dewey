# Dewey

Dewey is the canonical artifact registry and artifact-resolution service in this workspace.

It owns:

- artifact identity and metadata
- artifact-set identity and membership
- artifact resolution and storage metadata lookup
- share-reference issuance
- external object links to artifacts and artifact sets

It does not own:

- customer release visibility decisions
- Atlas storage policy authority
- Bloom or Ursa execution state

## Runtime Shape

Primary package: `dewey_service`

Primary entrypoints:

- app factory: `dewey_service.app:create_app`
- CLI command: `dewey`

The service exposes both API routes and a small Cognito-backed browser UI.

## API Surface

Current routes:

- `GET /api/v1/artifacts`
- `GET /api/v1/artifacts/{artifact_euid}`
- `POST /api/v1/artifacts`
- `POST /api/v1/artifacts/import`
- `GET /api/v1/artifact-sets`
- `GET /api/v1/artifact-sets/{artifact_set_euid}`
- `POST /api/v1/artifact-sets`
- `POST /api/v1/artifact-sets/{artifact_set_euid}/members`
- `DELETE /api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}`
- `POST /api/v1/resolve/artifact`
- `POST /api/v1/resolve/artifact-set`
- `POST /api/v1/share-references`
- `POST /api/v1/external-objects`
- `POST /api/v1/external-object-relations`
- `GET /api/v1/{target_type}/{target_euid}/external-object-relations`

UI/auth routes:

- `/login`
- `/auth/login`
- `/auth/callback`
- `/search`
- `/ui`
- `/ui/anomalies`
- `/ui/observability`
- `POST /logout`

## Auth

- API routes require `Authorization: Bearer <token>`
- mutating API routes require `Idempotency-Key`
- browser UI uses Cognito Hosted UI session auth

## CLI Surface

Primary root commands:

- `dewey version`
- `dewey info`
- `dewey config`
- `dewey env`

Primary plugin groups:

- `dewey server`: start the API/UI server
- `dewey db`: build, seed, reset Dewey on top of TapDB
- `dewey test`, `dewey quality`

## Quick Start

```bash
source ./activate
dewey config init
dewey db build --target local
dewey server start --port 8914
```

HTTPS is mandatory. Place certs at `certs/cert.pem` and `certs/key.pem` before starting the server.

`dewey config show` now prints raw YAML. Use `dewey config status` to inspect merged runtime settings.

Use `tapdb` directly for shared DB/runtime lifecycle and `daycog` directly for shared Cognito lifecycle. Dewey keeps only Dewey-specific overlay build/seed/reset behavior.

The canonical `source ./activate` workflow installs `metapub` through `dewey_env.yaml` so literature search/save works in the standard local environment.

Dewey template definitions are authored as JSON packs under
`config/tapdb_templates/` and loaded through TapDB during Dewey bootstrap.

Literature search/save flows use `metapub` for PubMed discovery and full-text detection. If the adapter is unavailable at runtime, Dewey returns a clear 503 on literature endpoints.

Browser UI scope is intentionally narrow:

- supported in-browser: literature search/save, unified search/export, anomaly browsing, observability, admin stub
- not supported in-browser: direct upload/register-S3 or other artifact ingestion flows; use the API or CLI instead

## Current Docs

- [Docs index](docs/README.md)

Historical cutover planning lives in `docs/` as background only.

<!-- release-sweep: 2026-03-10 -->
 
