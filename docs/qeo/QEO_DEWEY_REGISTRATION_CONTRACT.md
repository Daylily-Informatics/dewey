# QEO/KEO Dewey Registration Contract

## Ownership

Dewey owns canonical artifact registration because it is the Data Plane evidence spine for artifact existence, storage pointers, checksums, immutable identities, and retrieval semantics. QEO consumes Dewey evidence and interprets observational QC meaning. R2 interprets scientific validity. Daylily/Snakemake produces manifests and pushes them into Dewey.

Dewey does not crawl workflow directories, infer completeness, compute QC pass/fail, or mutate old artifact bytes. Reprocessing creates a new artifact set unless the full canonical registration request is an exact idempotent replay.

## Endpoints

Both endpoints require the existing Dewey bearer token:

- `POST /api/v1/artifact-sets/analysis/register`
- `POST /api/v1/artifact-sets/multiqc/register`

Existing read surfaces remain:

- `GET /api/v1/artifact-sets/{artifact_set_euid}`
- `GET /api/v1/artifacts/{artifact_euid}`

No `/api/v1/qeo/ingest-ready` route is added. QEO handoff is the registration receipt plus transactional outbox event.

## Idempotency

Dewey computes a deterministic `idempotency_key` from canonical JSON for the validated request.

- If `Idempotency-Key` is omitted, Dewey uses the computed key.
- If `Idempotency-Key` is supplied and differs from the computed key, Dewey returns `409`.
- Exact replay returns the stored response without creating additional artifacts, sets, receipts, or outbox rows.

## Manifest Hash

`manifest_sha256` is the canonical SHA-256 of the validated request with `manifest_sha256` omitted. Dewey rejects a mismatch before any mutation.

Use `dewey_service.registration_contracts.manifest_sha256_for_request` when constructing producer tests or clients in this repo.

## File Artifact

`FileArtifact` fields:

- `logical_name`
- `relative_path`
- `storage_uri`
- `sha256`
- `size_bytes`
- `mime_type`
- `artifact_role`
- `parser_hint`
- `required`
- `produced_by`
- `parent_artifact_euids`
- `metadata`

`relative_path` is a manifest path, not a filesystem path to crawl. It must be relative and must not contain `..`.

Directory artifacts must use:

- `artifact_role: "directory"`
- `mime_type: "inode/directory"`
- `storage_uri` ending in `/`
- `size_bytes: 0`

Dewey records the prefix pointer and never expands descendants.

## Analysis Artifact Set

`AnalysisArtifactSetRegistrationRequest` fields:

- `schema_version`
- `analysis_euid`
- `run_euid`
- `workset_euid`
- `project_euid`
- `assay_id`
- `pipeline_name`
- `pipeline_version`
- `workflow_engine`
- `workflow_engine_version`
- `snakemake_version`
- `workflow_git_sha`
- `workflow_config_sha256`
- `workflow_profile`
- `generated_at`
- `manifest_sha256`
- `parent_analysis_artifact_set_euid`
- `rerun_of`
- `status`
- `artifacts`
- `lineage_refs`
- `metadata`
- `local_only`
- `parser_family_hint`

Dewey creates `artifact_set_type == "analysis_artifact_set"` and member lineage from the set to each registered artifact. If `parent_analysis_artifact_set_euid` or `rerun_of` is supplied, the referenced artifact set must exist.

## MultiQC Artifact Set

`MultiQCArtifactSetRegistrationRequest` fields:

- `schema_version`
- `analysis_euid`
- `report_kind`
- `multiqc_version`
- `html_artifact`
- `data_dir_artifact`
- `key_files`
- `parser_relevant_files`
- `generated_at`
- `manifest_sha256`
- `metadata`
- `local_only`
- `parser_family_hint`

`html_artifact.artifact_role` must be `multiqc_html`. `data_dir_artifact.artifact_role` must be `directory`.

Dewey creates `artifact_set_type == "multiqc_artifact_set"`.

## Receipt

Registration returns deterministic receipt JSON:

- `schema_version`
- `request_id`
- `idempotency_key`
- `artifact_set_euid`
- `registered_artifacts`
- `skipped_existing`
- `failed`
- `registered_at`
- `status`
- `metadata`

`registered_artifacts` and `skipped_existing` carry Dewey artifact EUIDs plus manifest artifact refs. On success, `failed` is empty. Dewey rejects invalid requests before mutation rather than returning partial success.

`status` is `registered` or `local_only`. Replay returns the stored original receipt.

## Immutable Semantics

An existing artifact can be reused only when `storage_uri`, `sha256`, `size_bytes`, and `artifact_role` match exactly. Conflicting existing records return `409`. Dewey never rewrites an existing artifact record to satisfy a new registration manifest.
