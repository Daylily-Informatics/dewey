# Dewey Metapub Literature MVP Implementation Plan

## Summary

- Target document: `prompts/dewey_metapub_codex_implementation_plan.md`. When execution starts, first create feature branch `codex/dewey-metapub-mvp` from the current detached `HEAD`, then write this document into that path before code changes.
- Add a Dewey-first literature workflow on the existing FastAPI + TapDB + Cognito stack only: PubMed search, canonical literature artifact creation/reuse, per-user save/visibility records, and literature-aware `/search` enrichment.
- Keep `metapub` external to Dewey. Do not vendor it and do not pin a guessed version in project dependencies. Use an optional runtime import guard plus a README note pointing maintainers at the pip-installable forked repo source the user identified.

## Public Interfaces

- Add settings for `literature_managed_copy_allowed_domains` with default `europepmc.org,ncbi.nlm.nih.gov`, plus minimal optional literature cache/timeout settings used by the metapub adapter.
- Add session-auth HTML route `GET /literature`. Keep it server-rendered like the current Dewey UI, with query params `q`, `page`, and `page_size`; use small inline JS only for save and visibility-update actions.
- Add session-auth JSON route `POST /api/v1/literature/search` with body `{query, page=1, page_size=20}` and response items containing `pmid`, `doi`, `pmcid`, `title`, `journal`, `year`, `authors`, `abstract_snippet`, `source_urls`, `best_fulltext_url`, `findit_reason`, `storage_mode`, `downloadable`, `external_link_only`, `artifact_euid`, `already_in_dewey`, `saved_by_me`, `saved_by_others_count`, and `visible_owner_labels`.
- Add session-auth JSON route `POST /api/v1/literature/save` requiring `Idempotency-Key`, with body `{pmid, save_mode, visibility_scope, allowed_users, allowed_groups}` where `save_mode` is `auto|managed_artifact|external_reference` and `visibility_scope` is `private|restricted|all_users`. Return the current Dewey mutating-route style: HTTP 200 with embedded `status_code` plus `artifact` and `literature_save` payloads.
- Add session-auth JSON route `PATCH /api/v1/literature/saves/{literature_save_euid}` requiring `Idempotency-Key`, limited to visibility updates on the caller’s own save record.
- Add session-auth JSON route `GET /api/v1/literature/saves/mine` returning the caller’s saves newest-first with artifact summary, identifiers, storage mode, and visibility fields.
- Extend search-v2 artifact rows so literature artifacts expose `title`, `pmid`, `doi`, `storage_mode`, `saved_by_me`, `saved_by_others_count`, and `visible_owner_labels`. Extend TSV export columns to include the new literature fields.

## Implementation Changes

- Add one new TapDB template only: `dewey/access/literature_save/1.0/` with prefix `LS`. Use a single `literature_save` record per `(artifact_euid, owner_subject)` pair and store a `literature_save_identity_key` for upsert/idempotency.
- Add a `ViewerContext` helper built from the current session `operator_profile`. Use Cognito `sub` as the stable owner identity when present, falling back to email; use email as the visible owner label; use exact Cognito group names plus lowercased emails for visibility checks.
- Create a new `dewey_service.literature` module with:
  - Optional `metapub` imports guarded behind a clear runtime error.
  - `MetapubAdapter` wrapping `PubMedFetcher.pmids_for_query`, `PubMedFetcher.article_by_pmid`, and `FindIt`.
  - Identifier normalization helpers for PMID, DOI, and PMCID.
  - Result normalization that turns `PubMedArticle` and `FindIt` output into Dewey search/save payloads.
  - Full-text eligibility helpers that mark a result `downloadable` only when the best fulltext URL is on PMC/Europe PMC or an allowlisted domain, is not a paywall or POST-only flow, and later verifies as a real PDF.
- Extend `DeweyService` with optional literature adapter support plus `search_literature`, `save_literature`, `update_literature_save_visibility`, and `list_my_literature_saves`.
- Keep literature persistence inside `DeweyService`, not the adapter. Resolve canonical artifacts by external-object identity first, not by storage coordinates. Set literature `artifact_identity_key` to a stable paper key (`literature:pmid:<pmid>`) so external-only and managed-copy states can update the same artifact in place.
- Store every saved paper as one canonical `artifact` with `artifact_type="literature"`, `producer_system="pubmed"`, and `producer_object_euid=<pmid>`. Metadata must include the spec fields, with `authors` as an ordered list, `source_urls` as a deduped ordered list, `storage_mode` as `managed` or `external_reference`, `acquisition_mode` as the requested save mode, and `fulltext_status` as `downloadable|external_link_only|unavailable`.
- Represent paper identity through existing `external_object` and `external_object_relation` records: `pubmed/pmid`, `pubmedcentral/pmcid`, and `doi/doi`, each linked to the canonical artifact with existing relation mechanics.
- For external-reference artifacts, store the stable landing URL in the existing storage fields using `http` or `https` backend semantics and set `availability_status="external_only"`.
- For managed artifacts, download only from allowlisted URLs, verify the response is actually a PDF using `Content-Type` and PDF magic bytes, store bytes in Dewey-managed S3, and update the same artifact in place. If a save was previously external-only and later becomes managed-copy eligible, promote by `update_instance_json(...)` on the existing artifact.
- Save-mode behavior is fixed as follows: `auto` chooses managed when eligible else external reference; explicit `managed_artifact` also downgrades automatically to external reference when a managed copy is not lawful or technically verified; explicit `external_reference` never attempts a managed copy.
- Create a `literature_save` record with ownership and visibility only, plus lineage from artifact to save using a dedicated relationship such as `has_literature_save`. Visibility logic is fixed: visible when the viewer is the owner, or scope is `all_users`, or viewer email is in `allowed_users`, or any viewer group is in `allowed_groups`. Private saves owned by others must never contribute to badges, counts, or owner labels.
- Update existing `/search` service flow so UI routes pass `ViewerContext` into search-v2 enrichment. Literature artifact rows should render title-first, show PMID/DOI and journal/year/authors, and expose badges for storage mode plus visible save ownership state. Bearer-auth search endpoints stay unchanged except for safely carrying the extra literature fields when present.
- Update the UI templates conservatively: add a `/literature` link from the dashboard, add a dedicated literature page using the current console style, and update the unified search template to show literature-specific secondary text and badges without changing the layout model.
- In app startup, instantiate the literature adapter only if `metapub` imports cleanly. If not available, keep the app booting and make literature endpoints fail with a clear 503 message explaining that `metapub` must be installed from the forked source repo.

## Test Plan

- Extend `tests/conftest.py` `FakeDeweyService` with minimal literature search/save/update/list methods, visibility filtering, and literature row enrichment so route/UI tests stay isolated from live network calls.
- Extend service-unit coverage for identifier normalization, visibility evaluation, per-user save upsert, cross-user artifact reuse, external-object linking, private-save non-leakage, restricted user/group visibility, external-to-managed promotion-in-place, and managed-save downgrade behavior.
- Extend route/UI coverage for: `/literature` login enforcement and render; `/api/v1/literature/search` normalized results; `Idempotency-Key` enforcement on save and patch; save creation for first and second users; `GET /api/v1/literature/saves/mine`; 503 behavior when metapub is unavailable; and literature badges in `/search`.
- Keep all literature tests adapter-driven and fully offline. Stub the Dewey-local metapub adapter and monkeypatch any managed-copy HTTP download path so no NCBI or publisher requests occur.
- Verify with the same repo gates CI uses: `pytest`, `ruff check dewey_service tests`, and `ruff format --check dewey_service tests`.

## Assumptions And Defaults

- Restricted visibility is represented as `visibility_scope="restricted"` plus explicit `allowed_users[]` and `allowed_groups[]`.
- Owner identity is Cognito `sub` when present, with email retained for display and user-based visibility matching.
- The metapub source of truth for behavior inspection is `/Users/jmajor/projects/daylily/metapub`, but Dewey should consume the pip-installable fork rather than a vendored checkout.
- The current local `source ./activate` flow is failing due to a Conda prefix conflict (`bzip2` record already exists). Static planning proceeded anyway, but implementation and verification should assume a repaired or clean Dewey environment before running repo commands that depend on activation.
