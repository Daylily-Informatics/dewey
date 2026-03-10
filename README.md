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

The service exposes both API routes and a small Cognito-backed operator UI.

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
- `/ui`
- `POST /logout`

## Auth

- API routes require `Authorization: Bearer <token>`
- mutating API routes require `Idempotency-Key`
- operator UI uses Cognito Hosted UI session auth

## CLI Surface

Primary groups:

- `dewey server`: start the API/UI server
- `dewey db`: build, seed, reset Dewey on top of TapDB
- `dewey tapdb`: pass through TapDB commands in Dewey runtime context
- `dewey cognito`: Cognito/daycog helper commands
- `dewey test`, `dewey quality`, `dewey config`, `dewey env`

## Quick Start

```bash
source dewey_activate
pip install -e .[dev]
dewey db build --target local
dewey server start --port 8913 --no-ssl
```

For production-like local HTTPS, place certs at `certs/localhost.pem` and `certs/localhost-key.pem` and omit `--no-ssl`.

## Current Docs

- [Docs index](docs/README.md)

Historical cutover planning lives in `docs/` as background only.

<!-- release-sweep: 2026-03-10 -->
