# Dewey Hard Cutover Execution Plan

## Workspace Audit and Mismatch Notes

- Workspace root: `/Users/jmajor/projects/lims3`
- Atlas repo path in this workspace: `/Users/jmajor/projects/lims3/lsmc-atlas`
- Ursa repo path in this workspace: `/Users/jmajor/projects/lims3/daylily-ursa`
- `AI_GUIDANCE.md` is not present in `/Users/jmajor/projects/lims3`
- `AI_DIRECTIVE.md` is present at `/Users/jmajor/projects/lims3/daylily-tapdb/AI_DIRECTIVE.md`

## Dewey Domain Model (Canonical)

- `artifact`
- `artifact_set`
- `share_reference`
- `external_object`
- `external_object_relation`
- `idempotency_request` (operational)

## Dewey Persistence and Bootstrap Model

- FastAPI runtime with TapDB-backed persistence.
- TapDB templates under `dewey/*` namespace.
- Bootstrap performed by `dewey db build` and `python -m dewey_service.db_seed`.
- Idempotency state persisted in TapDB (request fingerprint + response body/status).

## Cross-Repo Integration Points

- Atlas -> Dewey
  - document artifact registration
  - release artifact resolution/share reference
  - Ursa-result artifact references accepted as Dewey EUIDs
- Bloom -> Dewey
  - run output artifact registration
- Ursa -> Dewey
  - analysis artifact register/resolve
  - portal file/manifest routes implemented via Dewey artifacts/artifact_sets

## Legacy Deletion Targets

- Dewey
  - remove in-memory storage scaffold
  - remove direct non-Cognito operator credential auth
- Atlas
  - remove `/internal/artifacts` and `/internal/artifacts/bulk`
  - remove Atlas-local artifact ownership writes where superseded by Dewey
- Bloom
  - remove superseded `file`/`file_set` ownership internals and docs
  - remove Dewey-owned UI residue served from Bloom
- Ursa
  - remove redundant artifact registry ownership
  - reimplement portal file/manifest internals on Dewey-backed model
