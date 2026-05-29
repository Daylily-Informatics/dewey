# Sequencer Run Registration Contract

Dewey is the canonical evidence registry for sequencer run roots and terminal analysis-result artifact sets. It records immutable pointers, observed storage facts, receipts, lineage, and broker-ready outbox events. Dewey does not prove transfer completion, crawl arbitrary workflow directories, parse QC meaning, or execute sidecar shell.

## Run Registration

`POST /api/v1/sequencer-runs/register` registers a top-level S3 run directory plus only downstream-needed files.

Required request fields:

- `run_root_uri`: S3 prefix for the sequencer run root.
- `platform`: `ILMN`, `ONT`, `ULTIMA`, or `HYBRID_ILMN_ONT`.
- `trigger_policy`: `register_only` or `trigger_ursa`.

Optional request fields include `run_euid`, `run_xid`, `bloom_run_euid`, `atlas_order_euid`, `metadata`, `expected_files`, `expected_manifest_sha256`, and `sidecar_required`.

Dewey registers the run root as a prefix artifact. Files discovered by S3 listing are recorded as `storage_status="observed"`, not `verified`, because S3 list responses do not carry version IDs or SHA256 checksum proof. If explicit expected-file metadata is supplied, Dewey rejects missing required files and size/checksum mismatches when storage reports comparable evidence.

Selectors intentionally exclude raw image/signal/internal files such as BCL internals, image files, FAST5/POD5, and other raw signal files unless they are explicitly supplied as required downstream evidence. Prefix registration is not transfer verification.

## Sidecar

The sidecar key is:

```text
<run-prefix>/<run-dir-basename>.analysis_pipeline_order.tsv
```

It is UTF-8 TSV with no header and one job per non-empty line:

```text
pipeline_code<TAB>params_json<TAB>dewey_status<TAB>dewey_date<TAB>pipeline_status<TAB>pipeline_date[<TAB>pipeline_status<TAB>pipeline_date]*
```

`pipeline_code` must match a catalog command ID. `params_json` must be a JSON object. Dewey appends sidecar jobs after the simple platform QC command; it does not execute shell from the sidecar.

Simple QC commands:

- `ILMN`: `illumina_run_qc`
- `ONT`: `ont_run_qc`
- `ULTIMA`: `ultima_run_qc`
- `HYBRID_ILMN_ONT`: `illumina_run_qc`

Accepted kitchen-sink command IDs:

- `illumina_snv_alignstats_relatedness_vep_multiqc`
- `ultima_snv_alignstats_kitchensink`
- `ont_snv_alignstats_kitchensink`
- `hybrid_ilmn_ont_snv_kitchensink`

## Analysis Results

`POST /api/v1/analysis-results/register` is the Ursa terminal callback. It records pass/fail/canceled result roots and required result artifacts, including sample/library EUID/XID metadata when supplied.

Required fields:

- `analysis_euid`
- `command_id`
- `result_status`
- `result_root_uri`
- `artifacts`

Result artifacts are linked under an analysis-result artifact set. Artifacts with explicit SHA256 and version evidence are marked `verified`; otherwise they are marked `observed`.

## Idempotency

Both endpoints compute deterministic idempotency keys from canonical request JSON. If an `Idempotency-Key` header is supplied, it must match the computed key. Missing headers are accepted on these two deterministic endpoints.

## Events

Dewey persists outbox events in TapDB:

- `lsmc.dewey.sequencer-run.registered.v1`
- `lsmc.dewey.analysis-results.registered.v1`

Event payloads contain EUIDs, manifest hashes, command/status fields, and platform hints only. They do not include PHI, filesystem paths, sample names, DOB, MRN, or patient-facing identifiers.
