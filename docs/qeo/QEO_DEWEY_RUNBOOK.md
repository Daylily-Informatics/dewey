# QEO/KEO Dewey Registration Runbook

## Producer Flow

1. Daylily/Snakemake writes the analysis or MultiQC manifest from its explicit workflow outputs.
2. The producer computes `manifest_sha256` from Dewey canonical JSON with the `manifest_sha256` field omitted.
3. The producer calls the relevant Dewey registration endpoint with bearer auth.
4. Dewey validates the manifest hash, required artifacts, storage size, storage SHA-256 when reported, directory artifact shape, immutable conflicts, and rerun links.
5. Dewey writes artifacts, artifact set, lineage, receipt, outbox event, and idempotency row in one TapDB transaction.
6. QEO consumes the receipt and/or outbox event, resolves Dewey artifact refs, and performs interpretation outside Dewey.

## Commands

Activate the repo-owned environment:

```bash
source ./activate qeoart
```

Run focused tests:

```bash
pytest -q tests/test_qeo_artifact_set_registration.py tests/test_qeo_multiqc_registration.py tests/test_qeo_registration_events.py tests/test_qeo_registration_security.py
```

Run acceptance:

```bash
dewey test run
dewey quality check
```

## Reruns And Reanalysis

An exact replay of the same canonical request reuses the stored receipt and does not create new records.

A reprocessing run with a different canonical manifest creates a new artifact set. If artifacts already exist and match exactly, Dewey links the existing artifacts and records them in `skipped_existing`.

Use `parent_analysis_artifact_set_euid` and `rerun_of` for explicit set-to-set lineage. Supplied artifact-set EUIDs must already exist.

## Why Filesystem Crawling Is Forbidden

Dewey is an artifact evidence registry, not a workflow directory auditor. Filesystem or prefix crawling would make Dewey infer completeness and workflow intent. Daylily/Snakemake must push explicit manifests; Dewey records exactly what was declared and validated.

## Immutable Artifacts

Artifact bytes are immutable. If bytes or checksums change, the producer must create a new artifact and a new artifact set. Dewey rejects attempts to reinterpret an existing storage URI with different checksum, size, or role.

## QEO Consumption

QEO should ingest:

- Dewey receipt JSON
- artifact-set EUID
- artifact EUIDs
- manifest SHA-256
- storage retrieval refs from Dewey artifact records
- parser hints

QEO should not ingest local filesystem paths, crawl workflow directories, or treat Dewey events as QC pass/fail decisions.

## Troubleshooting

- `400 manifest_sha256 does not match`: recompute using Dewey canonical JSON after model validation.
- `400 size_bytes mismatch`: manifest size does not match storage `head_object`.
- `400 sha256 mismatch`: storage adapter reported a hex SHA-256 that differs from the manifest.
- `404 Required artifact missing`: required object was not visible to Dewey storage auth.
- `409 Idempotency-Key does not match`: supplied header is not the deterministic request hash.
- `409 immutable registration manifest`: the storage URI is already registered with different checksum, size, or role.
