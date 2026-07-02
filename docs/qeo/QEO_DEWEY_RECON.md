# QEO/KEO Dewey Recon

## Baseline

- Worktree: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-qeo-keo-artifacts-20260526`
- Base commit: `8205223c47f568211a301d11aa384615f1bdc395`
- Branch: `codex/qeo-keo-artifact-registration-20260526`
- Ledger: `docs/plans/20260526T181458Z_qeo_keo_artifact_registration_8agent_ledger.md`

## Current Architecture

- `dewey_service/app.py:create_app` builds the FastAPI app, wires `DeweyService`, configures middleware, and registers the API/UI routes.
- `dewey_service/service.py:DeweyService` is a mixin-composed domain service. The QEO work adds `OutboxServiceMixin` and `ArtifactSetRegistrationServiceMixin` beside existing artifact, artifact-set, sharing, search, literature, and external-object mixins.
- `dewey_service/tapdb_backend.py:TapDBBackend` owns TapDB sessions, template checks, instance create/update/find/list helpers, and lineage creation/deletion.
- `dewey_service/storage.py:S3StorageClient` is the narrow S3 adapter for `head_object`, `list_objects`, `get_object_bytes`, upload/presign, tags, and retention.

## Existing Registration And Set Concepts

- `dewey_service/services/artifacts.py:ArtifactServiceMixin.register_artifact` registers one object-backed artifact behind `POST /api/v1/artifacts`.
- `dewey_service/services/artifacts.py:ArtifactServiceMixin.import_artifact_from_uri` supports S3 reference/copy flows behind `POST /api/v1/artifacts/import`.
- `dewey_service/services/artifacts.py:ArtifactServiceMixin.import_run_prefix` exists for explicit prefix import; it is not a workflow crawler for QEO. QEO/Daylily must push manifests.
- `dewey_service/services/artifact_sets.py:ArtifactSetServiceMixin.create_artifact_set` creates generic sets behind `POST /api/v1/artifact-sets`.
- `dewey_service/services/artifact_sets.py:ArtifactSetServiceMixin.add_artifact_set_member` stores `artifact_set_member` lineage from set to artifact.
- `dewey_service/services/base.py:BaseDeweyService._artifact_response` and `_artifact_set_response` are the response shaping points for existing `GET /api/v1/artifacts/{artifact_euid}` and `GET /api/v1/artifact-sets/{artifact_set_euid}`.

## Lineage, Pointer, And Checksum Handling

- `dewey_service/services/artifacts.py:ArtifactServiceMixin._artifact_payload` normalizes S3 coordinates into `storage_uri`, `bucket`, `key`, `storage_kind`, `node_kind`, `checksums`, and lifecycle fields.
- `dewey_service/services/artifacts.py:ArtifactServiceMixin._upsert_artifact_record` creates an artifact if the `artifact_identity_key` is new and reuses an existing artifact otherwise.
- `dewey_service/services/artifacts.py:ArtifactServiceMixin._create_artifact_lineage` uses relationship type `artifact_hierarchy`.
- `dewey_service/tapdb_backend.py:TapDBBackend.create_lineage` is idempotent for the same parent, child, and relationship type.
- `dewey_service/storage.py:StorageObject` now carries optional `sha256`; QEO registration rejects mismatches only when storage reports a hex SHA-256.

## Auth And Idempotency

- `dewey_service/auth.py:require_api_auth` protects bearer-token API routes.
- `dewey_service/app.py:api_auth_dep` applies bearer auth to the registry surface.
- `dewey_service/services/base.py:BaseDeweyService._fingerprint`, `_idempotency_replay`, and `_store_idempotency` persist replay-safe write responses in `system/idempotency_request/generic/1.0/`.
- Existing write routes require `Idempotency-Key`; the new deterministic registration routes may omit it because Dewey computes the key from canonical JSON.

## Event And Outbox Patterns

- Before this work, docs stated Dewey had no public event bus API.
- This work keeps that boundary: no public event-stream route was added.
- `dewey_service/services/outbox.py:OutboxServiceMixin._persist_outbox_event` stores local transactional outbox rows in `system/outbox_event/generic/1.0/`.
- Events are persisted in the same TapDB transaction as artifacts, artifact sets, lineage, idempotency rows, and receipts.

## API Style And UI Conventions

- FastAPI models are Pydantic v2 `BaseModel` classes with `ConfigDict(extra="forbid")`.
- API write handlers return `{"status_code": <domain_status>, **payload}` and map `DeweyConflictError` to `409`, `DeweyNotFoundError` to `404`, `ValueError` to `400`, and storage/config runtime failures to `502`.
- Jinja2 UI templates live in `dewey_service/templates/`; no QEO dashboard or UI was added.

## Storage, Share, And Download Assumptions

- Current storage is S3-oriented: `s3://bucket/key` objects and prefix pointers.
- Existing browser/download flows can generate ZIPs and presigned links for object-backed artifacts.
- Shares live in `dewey_service/services/sharing.py:SharingServiceMixin` and `data/share/generic/1.0/`.
- QEO registration does not expand bearer sharing, does not create shares, and does not crawl prefixes.

## MDR/TapDB Linkage

- TapDB is the persistence substrate for generic instances and lineages; Dewey owns artifact semantics.
- External system linkage is represented by `dewey_service/services/external_objects.py:ExternalObjectServiceMixin`, `integration/external_object/generic/1.0/`, and `integration/external_object_relation/generic/1.0/`.
- QEO registration stores lineage references as manifest metadata and only creates set-to-set lineage where a supplied artifact-set EUID is resolvable.

## Integration Seams

- Contract module: `dewey_service/registration_contracts.py`
- Registration service: `dewey_service/services/artifact_set_registration.py`
- Outbox service: `dewey_service/services/outbox.py`
- TapDB constants/templates: `dewey_service/tapdb_backend.py`, `config/tapdb_templates/dewey/templates.json`
- API routes: `dewey_service/app.py`
- Focused tests: `tests/test_qeo_artifact_set_registration.py`, `tests/test_qeo_multiqc_registration.py`, `tests/test_qeo_registration_events.py`, `tests/test_qeo_registration_security.py`

## Implementation Risks

- Producers must compute `manifest_sha256` with Dewey canonical JSON helpers or send a manifest Dewey can validate.
- S3 native `ChecksumSHA256` may be base64 in some AWS responses; Dewey only enforces checksum equality when a storage adapter reports a 64-character hex SHA-256.
- Existing `/api/v1/artifacts` and `/api/v1/artifact-sets` list routes remain bearer-protected but still enumerate to authorized callers; this work adds no broader enumeration surface.
- Directory artifacts are prefix pointers only. Consumers must not assume Dewey has enumerated descendants.
