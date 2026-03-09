# Dewey

Dewey is the canonical artifact registry/control-plane service for LSMC beta.

## Scope

- canonical artifact identity (`artifact`, `artifact_set`, `share_reference`)
- artifact registration and lookup
- artifact-set membership and resolution
- authenticated API and operator UI surfaces

## Local run

```bash
cd /Users/jmajor/projects/lims3/dewey
python -m pip install -e .[dev]
dewey serve --port 8920
```

API requests require:

- `Authorization: Bearer <token>`

Canonical API routes:

- `POST /api/v1/artifacts`
- `GET /api/v1/artifacts/{artifact_euid}`
- `POST /api/v1/artifact-sets`
- `POST /api/v1/artifact-sets/{artifact_set_euid}/members`
- `POST /api/v1/resolve/artifact`
- `POST /api/v1/resolve/artifact-set`
- `POST /api/v1/share-references`

Unauthenticated API requests return `401`.

Operator UI requires:

- session login via `/login`
