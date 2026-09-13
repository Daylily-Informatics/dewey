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

The MultiQC route registers a package of existing Dewey file artifacts through the same service as `dewey qeo package-register`. It does not fetch workflow files or dispatch QEO ingestion. The existing dedicated-credential `POST /api/v1/resolve/multiqc` resolves authoritative package membership for QEO.

## Idempotency

Dewey computes a deterministic `idempotency_key` from canonical JSON for the validated request.

- If `Idempotency-Key` is omitted, Dewey uses the computed key.
- If `Idempotency-Key` is supplied and differs from the computed key, Dewey returns `409`.
- Exact replay returns the stored response without creating additional artifacts, sets, receipts, or outbox rows.

## Manifest Hash

For the analysis artifact-set request, `manifest_sha256` is the canonical SHA-256 of the validated request with `manifest_sha256` omitted. Dewey rejects a mismatch before any mutation.

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

## MultiQC Existing-Artifact Package

`POST /api/v1/artifact-sets/multiqc/register` accepts `PackageRegistration`:

- `contract`: `dewey.multiqc-package/v1`
- `complete_data_package`: `true`
- `label`: explicit package label
- `files`: `{artifact_euid, role, relative_path, sha256, size_bytes}` for each existing Dewey file artifact

Exactly one report plus either one complete archive or all data files is required. The request never creates or discovers file artifacts. Roles are `report`, `data`, or `archive`. Paths and artifact identities must be unique; each registered SHA256 and byte count must equal the supplied values. Zero bytes are valid. An unknown stored size/checksum does not establish equality.

API and CLI sort members by relative path and derive `qeo.package.register:<sha256(canonical request JSON)>`. A supplied key must match. Transactional key serialization protects canonical replay and package creation. Dewey creates `artifact_set_type=qeo_multiqc_package` with native `artifact_set_member` lineage.

Registration and `POST /api/v1/resolve/multiqc` return `{contract,artifact_set_euid,complete_data_package,label,files}`. Each returned member preserves `{artifact_euid,role,relative_path,sha256,size_bytes,url,version_id}`. `url` is its exact registered S3 object URI. `version_id` is the registered exact version string or null when absent; resolution does not look up a newer S3 version. A report reference must resolve through its unique persisted package membership; ambiguous matches fail.

The QEO consumer supporting `files[].version_id` must be deployed before this resolver response is deployed. Complete MultiQC artifact collection and Dewey registration are independent of the optional onward QEO ingestion flag.

## Native Ursa Analysis Results

The existing `POST /api/v1/analysis-results/register` requires new requests to include `metadata.registration_contract=analysis_results.v1`, the complete `artifact_manifest_rows` including exclusions, explicit `entity_owner_systems`, and exact `artifact_lineage` entries `{path,entity_type,entity_euid,relationship,source}`. Requested file artifacts must equal all and only importable rows and lie at their exact paths under `result_root_uri`. Sample/library projections must reconcile with the full plural typed associations.

Dewey persists prefix/file hierarchy and typed external-reference lineage to the owning Ursa execution and declared biological entities. Intermediate prefix records remain outside the exact API receipt/result-set member list: the returned manifest and receipt cover the root and requested files only. No reference implies scientific or customer acceptance.

Completed canonical registrations replay their historical response before new contract checks or storage HEAD. New registrations serialize their deterministic request key, verify exact supplied S3 versions and byte counts, and retain the observed version. Missing object size fails; zero-byte objects are supported. The existing current-principal authorization on stored receipts remains in force.

## Receipt

The analysis artifact-set and native analysis-result registrations return receipt JSON. The existing-artifact MultiQC package response is specified above.

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

An existing artifact can be reused only when `storage_uri`, exact `version_id`, `sha256`, `size_bytes`, and `artifact_role` match exactly for native analysis results. Conflicting existing records return `409`. Dewey never rewrites an existing artifact record to satisfy a new registration manifest.
