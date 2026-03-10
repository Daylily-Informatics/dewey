# Dewey

Dewey is the canonical artifact registry and artifact-resolution platform service for LSMC.

## Authority Scope

Dewey is authoritative for:

- `artifact` identity and metadata
- `artifact_set` identity and membership
- storage metadata and artifact resolution
- `share_reference` issuance
- registration/import of artifacts
- external cross-system artifact links

Dewey does not own Atlas release visibility or attachment policy decisions.

## Quick Start

```bash
cd /Users/jmajor/projects/lims3/dewey
source dewey_activate
python -m pip install -e .[dev]
dewey db build --target local
dewey server start --port 8913
```

TapDB local dev uses port `5439` via `config/tapdb-config-dewey.yaml`.

## Auth

- API: `Authorization: Bearer <token>` is required for all `/api/*` routes.
- UI: Cognito Hosted UI session auth (`/auth/login` -> `/auth/callback`).
- Mutating API routes require `Idempotency-Key`.

## Canonical API Routes

- `POST /api/v1/artifacts`
- `POST /api/v1/artifacts/import`
- `GET /api/v1/artifacts`
- `GET /api/v1/artifacts/{artifact_euid}`
- `POST /api/v1/artifact-sets`
- `GET /api/v1/artifact-sets`
- `GET /api/v1/artifact-sets/{artifact_set_euid}`
- `POST /api/v1/artifact-sets/{artifact_set_euid}/members`
- `DELETE /api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}`
- `POST /api/v1/resolve/artifact`
- `POST /api/v1/resolve/artifact-set`
- `POST /api/v1/share-references`
- `POST /api/v1/external-objects`
- `POST /api/v1/external-object-relations`
- `GET /api/v1/{target_type}/{target_euid}/external-object-relations`

## CLI Groups

```bash
dewey info
dewey server start --help
dewey db --help
dewey tapdb --help
dewey cognito --help
dewey test --help
dewey quality --help
dewey config --help
dewey env --help
```
