# Dewey F07/F08 source implementation

Source-only work from deployed10.0.4 commit `2c167eba01b70d07c28474f967a7d660dbbc58d8` in isolated `codex/ursa-final-gap-dewey-20260913`. The lead confirmed Ursa F06 deployed14.0.6 before authorizing these changes. No deployment or live acceptance is claimed here.

## Implemented

- `services/sequencer_runs.py`: new native analysis registrations require complete scoped manifests/owner mappings; importable files, exclusions, full paths and plural sample/library projections reconcile exactly. Completed canonical replay runs before new-contract checks and storage access. Request-key locks serialize writes with replay recheck. Exact object identity/version and nonnegative size are verified; zero bytes are accepted. Missing observed SHA256 is retained as request-only evidence rather than labeled independently verified.
- Exact intermediate S3 prefix records and native immediate-parent containment preserve the declared file hierarchy. Root, directories and requested files receive typed external-reference lineage to the actual declared Ursa execution; files receive every supplied owner association. API receipt/manifest/result-set membership remain exactly root plus requested files; intermediate prefixes do not break Ursa's reconciliation contract.
- `integrations/tapdb_external_references.py`: bounded helper uses the existing source lock and public `ExternalReferenceService.attach` with explicit owner target, relationship and deterministic assertion provenance. It stays inside the owning transaction. No synthetic EUID or metadata-only relationship substitute.
- `sequencer_run_contracts.py`: supplied native result version_id must be nonempty exact text with no control bytes.
- `tapdb_backend.py`: canonical-key advisory transaction lock. Existing10.0.4 runtime/template/snapshot behavior remains intact.
- `services/artifact_sets.py`: one existing-artifact MultiQC package service, members sorted by relative path before canonical hashing, serialized deterministic key and completed replay. Exact stored checksum/size and authoritative membership are required. Resolver exposes the stored exact version_id instead of rejecting version-qualified members; malformed stored versions fail.
- `app.py` and `cli/qeo.py`: existing MultiQC API and CLI both use `PackageRegistration` and `register_qeo_package`. No additional API or old-body compatibility dispatch. Current dedicated resolver credential and internal read-only QEO principal remain unchanged.
- `docs/qeo/QEO_DEWEY_REGISTRATION_CONTRACT.md`: settled native/package/version contract and release ordering documented.

## Settled public contracts

`POST /api/v1/analysis-results/register`: same envelope/route. New native `metadata` requires `registration_contract=analysis_results.v1`, complete `artifact_manifest_rows`, `artifact_lineage=[{path,entity_type,entity_euid,relationship,source}]`, and explicit `entity_owner_systems`. New files must match every importable row and exact `result_root_uri+relative_path`. Successful saved historical requests replay unchanged before the new requirements. Native returned manifest retains each exact observed file version. Receipt remains root plus requested files only.

`POST /api/v1/artifact-sets/multiqc/register` and `dewey qeo package-register`: `PackageRegistration={contract:"dewey.multiqc-package/v1",complete_data_package:true,label,files:[{artifact_euid,role,relative_path,sha256,size_bytes}]}`. Roles one report plus archive OR all data. Uses only existing owning Dewey artifacts. Optional supplied idempotency key must equal `qeo.package.register:<canonical sorted request SHA256>`.

`POST /api/v1/resolve/multiqc`: unchanged request `{kind:"artifact"|"artifact_set",euid}` and existing dedicated auth. Response `{contract,artifact_set_euid,complete_data_package,label,files}`; each file now adds `version_id: exact string|null` to its existing artifact/role/path/hash/size/url fields. Never infer or fetch a latest version during resolution.

## Preserved boundaries and evidence

10.0.4 registry authorization, exact storage keys, canonical folder/file node classification, OWY prefix classification, current resolver principal, embedded GUI and TapDB lifecycle fixes remain. Historical9.2.0 commit6916143 was used only to port reviewed source deltas into unchanged module sections; no branch merge or release downgrade occurred. Existing older non-public import helpers were not converted into a compatibility route; the public MultiQC route has the one current body contract.

Actual checks: baseline git status/revision, targeted git diffs and source reads, manual source/call-site review. No tests, lint, coverage, AST/compile checks, container builds, commits, tags, pushes, service/database/provider mutations or deployment were run by this agent. No budget/resource/identity changes.

## Remaining lead gates

Deploy the new QEO version-aware consumer FIRST, then release/deploy this Dewey source. QEO2.6.7's strict model rejects the added version field. Verify approved existing GetObjectVersion/KMS access and integration identities independently. Complete MultiQC artifacts register in Dewey regardless of whether onward QEO ingestion is requested. User acceptance and actual native hierarchy/lineage/package receipts remain unobserved for these new revisions. Tests remain off under the explicit policy.
