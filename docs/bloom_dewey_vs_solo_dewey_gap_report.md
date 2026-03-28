# Bloom Dewey vs Solo Dewey Gap Report

Date: 2026-03-27

## Summary

This report compares the 2025 embedded Dewey functionality in old Bloom with the current extracted solo Dewey service.

Scope:

- Legacy source of truth:
  - `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py`
  - `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py`
  - `/Users/jmajor/.codex/worktrees/b91f/bloom/templates/dewey.html`
- Solo Dewey source of truth:
  - `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py`
  - `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/service.py`
  - `/Users/jmajor/.codex/worktrees/9aa5/dewey/README.md`
- Current Bloom is referenced only to confirm cutover intent and current ownership boundaries:
  - `/Users/jmajor/projects/daylily/bloom/bloom_lims/docs/dewey.md`
  - `/Users/jmajor/projects/daylily/bloom/bloom_lims/integrations/dewey/client.py`

Classification:

- `Equivalent`
- `Partial / renamed`
- `Probable gap`
- `Intentional scope reduction`

High-level conclusion:

- Old Bloom Dewey was a file manager: intake, storage mutation, query, retrieval, and concrete sharing of files.
- Solo Dewey is a canonical artifact registry: identity, metadata, set membership, abstract share-reference issuance, external object linking, and idempotent API writes.
- Many missing legacy behaviors are intentional scope cuts, not extraction misses.
- The largest likely gaps before larger solo-Dewey feature work are search/discoverability, richer set metadata, and the concrete semantics of share references.

## Route And API Diff Matrix

Legacy Dewey route cluster:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2243`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2337`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2613`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2704`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2867`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2941`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:3037`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:3358`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:3528`

Solo Dewey public surface:

- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:209`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:266`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:282`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:361`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:452`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:472`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:498`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:521`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:546`

| Legacy route | Purpose | Solo counterpart | Status | Evidence | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `GET /dewey` | All-in-one operator page for register, download, search, file-set creation, file-set search | `GET /ui` | `Partial / renamed` | Old UI bundles operational workflows in one screen; solo UI is a small console listing artifacts and sets | Keep as-is if Dewey remains registry-first; otherwise define a new operator workflow layer explicitly |
| `GET /bulk_create_files` | Bulk ingest page | None | `Intentional scope reduction` | Legacy page is part of operator ingestion UX, not registry ownership | Leave outside solo Dewey unless Dewey is expected to own batch intake |
| `POST /create_file` | Upload/import local files, directories, URLs, and S3 URIs; optionally create a set | `POST /api/v1/artifacts`, `POST /api/v1/artifacts/import`, `POST /api/v1/artifact-sets`, member APIs | `Partial / renamed` | Solo can register storage-backed artifacts and manage sets, but does not move bytes or orchestrate one-shot intake | Add orchestration only if callers require a single-step intake flow |
| `POST /download_file` | Download bytes with `dewey` / `hybrid` / `orig` naming and optional `.dewey.yaml` metadata file | None | `Intentional scope reduction` | Legacy route pulls objects from S3 and writes temp files | Keep out of registry core unless operator download is a product requirement |
| `GET /delete_temp_file` | Clean up temp downloads | None | `Intentional scope reduction` | Coupled directly to legacy temp-download flow | No action unless download flow returns |
| `POST /search_files` | Rich metadata and date search over files | `GET /api/v1/artifacts` | `Probable gap` | Solo listing is limited to `artifact_type` and `producer_system`; legacy search covered business metadata and date windows | Add richer artifact query/filter support if feature work depends on operator discovery |
| `POST /create_file_set` | Create a set, attach files, optionally create concrete sharing mechanism | Artifact-set APIs plus `POST /api/v1/share-references` | `Partial / renamed` | Solo preserves membership, but not concrete transport generation | Decide whether Dewey sharing stays abstract or must produce usable access handles |
| `POST /share_file_set` | Add presigned or rclone-based sharing to an existing file set | `POST /api/v1/share-references` | `Probable gap` | Legacy flow created concrete per-file URLs or rclone serving config; solo only creates a share-reference record | Add materialized share behavior if downstream systems require direct access |
| `POST /search_file_sets` | Search file sets by metadata and sharing state | `GET /api/v1/artifact-sets` | `Probable gap` | Solo list only filters by `artifact_set_type`; legacy set search covered tags/comments/ref state | Add set search/filter contract if sets must be operator-discoverable |
| `GET /file_set_urls` | Show concrete share URLs and active windows for a file set | None | `Probable gap` | Legacy route enumerated per-file presigned links for a set | Add read/list API for issued shares if concrete sharing remains in scope |
| `POST /bulk_create_files_from_tsv` | Bulk ingest from TSV, create a set, write outcome TSV | None | `Intentional scope reduction` | Operator batch import and served TSV output are outside current Dewey ownership | Keep external unless Dewey must become batch-ingest system |
| `GET /visual_report` | Produce visual report from exported TSV | None | `Intentional scope reduction` | Analytics/reporting on exported search results is not registry core behavior | No action |
| `GET /dewey_counts` | Return file and file-set counts for legacy home page | UI list counts / API `total` | `Partial / renamed` | Solo UI implicitly exposes counts and APIs return totals | Optional small dashboard endpoint if operators want direct counters |
| `GET /file_tag_suggestions` | Tag typeahead for legacy forms | None | `Intentional scope reduction` | Supports old embedded UI only | No action unless rich tag-based UI returns |
| `GET /file_set_tag_suggestions` | File-set tag typeahead for legacy forms | None | `Intentional scope reduction` | Supports old embedded UI only | No action unless rich tag-based UI returns |
| `GET /serve_endpoint/{file_path:path}` | Serve generated result files and TSV outputs | None | `Intentional scope reduction` | Legacy helper for downloaded/generated artifacts in local app storage | Keep outside Dewey |

Not treated as Dewey parity targets:

- `/get_node_property`
- `/create_instance/{template_euid}`
- `/create_instance`
- `/admin_template` GET/POST
- `/protected_content`

These were generic Bloom utility/admin endpoints co-located with Dewey code, not core Dewey product behavior.

Solo-only public routes with no legacy equivalent:

- `POST /api/v1/resolve/artifact`
- `POST /api/v1/resolve/artifact-set`
- `POST /api/v1/external-objects`
- `POST /api/v1/external-object-relations`
- `GET /api/v1/{target_type}/{target_euid}/external-object-relations`

These are genuine solo Dewey additions rather than missing legacy parity.

## Feature Parity Matrix

| Area | Old Bloom Dewey | Solo Dewey | Status | Evidence | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Registration/import | Upload local files, directories, public URLs, S3 objects, and S3 prefixes; optional remote-pointer mode | Register artifact storage records directly or import from `s3://` URI | `Partial / renamed` | Old code moved bytes and tagged objects; solo code registers canonical storage identity | Keep registry-first by default; add orchestration only if needed |
| Storage lifecycle | Derived target bucket, uploaded/copied objects, tagged objects with Dewey metadata, optionally locked objects via S3 governance retention | Stores bucket/key/version/storage URI as metadata only | `Intentional scope reduction` | Solo never mutates storage backends directly | No action unless Dewey is meant to own storage policy execution |
| File metadata model | Rich operational metadata: patient, study, clinician, lab code, purpose, category, tags, upload group, comments | Core artifact fields plus freeform `metadata` | `Partial / renamed` | Solo can carry metadata but does not model/query old fields explicitly | Define canonical metadata contract if those fields matter to future features |
| File-set management | Create/update/search sets, attach files, track sharing configuration and tags | Create/list/get sets and add/remove members | `Partial / renamed` | Solo sets are simpler collection records | Consider richer set metadata if operator workflows depend on it |
| Sharing | Generates presigned URLs or rclone-backed endpoints and stores validity windows | Creates abstract share-reference records with expiry and purpose | `Probable gap` | Solo tracks issuance but does not create concrete access handles | Decide if share references are abstract records or deliverable access mechanisms |
| Search/discoverability | Rich file and file-set search, date windows, counts, UI tables, TSV export | Basic list/get APIs and a read-only console | `Probable gap` | This is the largest behavior gap if solo Dewey will support operator workflows directly | Add search/filter APIs before building more features on top |
| UI/auth | Full operator workflow inside Bloom with legacy session auth | Small Cognito-backed operator console plus bearer-protected APIs | `Partial / renamed` | Solo UI is intentionally much thinner | Keep thin unless operator task execution moves into Dewey |
| Concrete retrieval | Download bytes with naming strategies and optional companion YAML | None | `Intentional scope reduction` | Retrieval of bytes was removed from ownership boundary | No action unless Dewey reclaims file-manager scope |
| Bulk workflows | Bulk create page and TSV-driven batch ingest | None | `Intentional scope reduction` | Batch import was legacy operator tooling | No action |
| Cross-system linking | Mostly implicit via metadata and lineage in Bloom | First-class `external_object` and `external_object_relation` model | `Equivalent` improvement / solo-only | Solo is better here than legacy | Use this instead of overloading metadata |
| Idempotent writes | Not a first-class persisted contract | Persisted idempotency records with request fingerprint and stored response | solo-only capability | Stronger than legacy | Preserve and extend |

## Domain And Ownership Translation Notes

### Old `file` -> solo `artifact`

This is the closest mapping, but it is not exact.

Old Bloom `file` combined:

- registry identity
- business metadata
- storage placement
- storage mutation
- retrieval rules
- sharing hooks

Solo `artifact` intentionally narrows that to:

- canonical identity
- storage coordinates
- producer metadata
- freeform metadata

This is an intentional architectural change, not just an incomplete extraction.

### Old `file_set` -> solo `artifact_set`

This mapping is mostly sound.

What was preserved:

- collection identity
- membership
- lightweight descriptive metadata

What was cut:

- tags/comments as a meaningful search surface
- sharing configuration on the set
- concrete access URL workflows
- richer operational state

### Old `shared_ref` -> solo `share_reference`

This is only a partial mapping.

Legacy `shared_ref` represented a concrete sharing mechanism:

- presigned URL
- rclone serve mode
- start/end validity window
- visibility/comments

Solo `share_reference` currently represents a registry record that something was shared, for what purpose, and until when. It does not itself produce or expose access handles.

This is the clearest area where a future feature could hit a real gap, depending on product intent.

### Solo-only additions

Solo Dewey added first-class concepts absent from legacy Dewey:

- `external_object`
- `external_object_relation`
- persisted idempotency state

These align with the cutover design and give Dewey a cleaner integration contract than the old embedded file-manager model.

### Confirmed current ownership boundary

Current Bloom confirms the intended cutover boundary:

- Bloom is not the artifact registry.
- Bloom registers produced run artifacts into Dewey.
- Bloom keeps its own execution and lineage concerns separate.

Evidence:

- `/Users/jmajor/projects/daylily/bloom/bloom_lims/docs/dewey.md:7`
- `/Users/jmajor/projects/daylily/bloom/bloom_lims/integrations/dewey/client.py:43`
- `/Users/jmajor/projects/daylily/bloom/bloom_lims/domain/beta_lab.py:1306`

## Recommended Pre-Feature Backlog For Solo Dewey

### Likely needed before larger solo-Dewey feature work

1. Add richer artifact query/filter APIs.
   - Minimum likely filters: `producer_object_euid`, metadata key/value predicates, creation window, artifact-set membership.
   - Reason: legacy Dewey users had strong discovery workflows; solo Dewey currently does not.

2. Decide and document the canonical metadata contract.
   - Old Dewey repeatedly used fields such as `patient_id`, `study_id`, `clinician_id`, `lab_code`, `purpose`, `category`, `sub_category`, and tags.
   - If any of these are important to future product work, promote them from ad hoc metadata to documented fields or indexed metadata conventions.

3. Clarify share-reference semantics.
   - Decide whether a share reference is:
     - an abstract issuance record only, or
     - a record plus a materialized access mechanism.
   - If concrete sharing is required, add:
     - share listing by target
     - share lookup/readback
     - concrete access-handle generation contract

4. Decide whether artifact sets need richer metadata.
   - Legacy sets behaved more like first-class operator bundles.
   - If future features rely on curated sets, solo Dewey likely needs more than `artifact_set_type`, `label`, and `description`.

5. Tighten producer-side registration guidance.
   - Document required metadata and identity expectations for producer systems.
   - Make explicit what fields are expected from Bloom/Atlas/Ursa producers and what Dewey deduplicates on.

### Probably out of scope unless solo Dewey expands back into a file-manager product

1. Direct browser upload, directory upload, public-URL fetch, or TSV batch ingest.
2. Direct byte download from Dewey with naming-pattern selection.
3. Companion `.dewey.yaml` export files.
4. Direct S3 mutation from Dewey:
   - object tagging
   - object retention locking
   - bucket-placement logic
   - object copy/import execution
5. rclone-backed transport serving.
6. Legacy analytics/reporting pages built on exported TSV data.

## Appendix: Key Evidence

Legacy Dewey intent:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/docs/dewey.md:1`

Legacy operator hub:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/templates/dewey.html:168`

Legacy file creation/import:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2337`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:2921`

Legacy storage mutation and download:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3179`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3526`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3674`

Legacy file-set and sharing behavior:

- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2867`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/scripts/main.py:2941`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3705`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3841`
- `/Users/jmajor/.codex/worktrees/b91f/bloom/bloom_lims/bobjs.py:3986`

Solo Dewey contract and ownership:

- `/Users/jmajor/.codex/worktrees/9aa5/dewey/README.md:3`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/app.py:266`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/service.py:74`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/service.py:474`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/service.py:543`
- `/Users/jmajor/.codex/worktrees/9aa5/dewey/dewey_service/service.py:867`

Cutover intent:

- `/Users/jmajor/.codex/worktrees/9aa5/dewey/docs/dewey_cutover_execution_plan.md:11`
- `/Users/jmajor/projects/daylily/bloom/bloom_lims/docs/dewey.md:5`
