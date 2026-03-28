You are working in the Dewey repo.

First inspect these files before changing anything:

- `README.md`
- `AGENTS.md`
- `dewey_service/app.py`
- `dewey_service/service.py`
- `dewey_service/tapdb_backend.py`
- `dewey_service/auth.py`
- `dewey_service/settings.py`
- `dewey_service/templates/ui_home.html`
- `dewey_service/templates/search.html`
- `tests/conftest.py`
- `tests/test_search_and_storage.py`
- `tests/test_service_unit.py`
- `docs/bloom_dewey_vs_solo_dewey_gap_report.md`
- `docs/dewey_cutover_execution_plan.md`

Also inspect these metapub files as the library source of truth:

- `metapub/README.md`
- `metapub/metapub/pubmedfetcher.py`
- `metapub/metapub/pubmedarticle.py`
- `metapub/metapub/findit/findit.py`
- `metapub/metapub/findit/logic.py`
- `metapub/metapub/findit/FINDIT_ERROR_PHILOSOPHY.md`

Goal:
Implement a Dewey-first MVP for PubMed literature discovery and Dewey registration using metapub as a library. Do not build anything inside metapub. Do not vendor or rewrite metapub.

Product behavior to implement:
- new Dewey operator page for PubMed search
- search results show title/journal/year/authors/PMID/DOI/abstract snippet
- search results show badges:
  - already in Dewey
  - saved by me
  - saved by another user
  - downloadable
  - external-link only
- user can save a result into Dewey
- save mode supports:
  - auto
  - managed artifact
  - external reference
- if Dewey can lawfully/technically store bytes, create/update a managed Dewey artifact
- otherwise create/update an external-reference Dewey artifact
- each save has owner + visibility:
  - private
  - selected users/groups
  - all users
- saved literature should appear in Dewey `/search`
- `/search` should indicate when a literature item is saved by another visible user

Hard constraints:
- keep Dewey as canonical system of record
- keep metapub as a library only
- no new search backend
- no relational side tables outside TapDB
- preserve Dewey idempotency patterns
- use existing Cognito session auth for the human literature UI
- do not redesign bearer auth in this task
- do not bypass publisher paywalls or POST-only download flows
- be conservative about managed-copy legality:
  - allow managed copy for PMC / Europe PMC by default
  - and for explicitly allowlisted domains only
  - otherwise fall back to external reference

Implementation decisions to follow:
1. Saved papers are always Dewey `artifact` records with `artifact_type="literature"`.
2. PubMed/DOI/PMCID identity is stored via existing `external_object` + `external_object_relation`.
3. Add one new TapDB template only:
   - `dewey/access/literature_save/1.0/`
   - suggested prefix `LS`
4. Ownership/visibility lives on `literature_save`, not on the artifact.
5. One canonical artifact per paper.
6. If a paper exists as external-reference-only and later becomes managed-copy eligible, promote the same artifact in place instead of minting a second canonical paper record.
7. `already saved by another user` must be computed from visible `literature_save` records only. Private saves owned by others must not leak through the UI.

Suggested file changes:

### 1) `dewey_service/tapdb_backend.py`
- add `LITERATURE_SAVE_TEMPLATE = "dewey/access/literature_save/1.0/"`
- add the new `TemplateDefinition`
- use prefix `LS`
- do not add any other templates

### 2) `dewey_service/settings.py`
Add minimal settings for literature integration:
- `literature_managed_copy_allowed_domains` as a comma-separated string or equivalent
  - default should at least include `europepmc.org,ncbi.nlm.nih.gov`
- optional metapub cache / timeout settings if you need them
Keep config style consistent with the existing settings module.
Do not invent a PyPI version pin for metapub. If packaging cannot be wired without path assumptions, add a clear runtime import guard and README note instead of guessing.

### 3) Create a new helper module, e.g. `dewey_service/literature.py`
Implement:
- a small `ViewerContext` helper built from current `operator_profile`
- a thin `MetapubAdapter` wrapper around:
  - `PubMedFetcher.pmids_for_query`
  - `PubMedFetcher.article_by_pmid`
  - `FindIt`
- normalization helpers for PMID / DOI / PMCID
- fulltext/copy-eligibility helpers
- visibility evaluation helpers

Do not put TapDB persistence in this adapter. Keep it a library wrapper only.

### 4) `dewey_service/service.py`
Extend `DeweyService` conservatively:
- accept an optional literature/metapub adapter in `__init__`
- add methods for:
  - `search_literature(...)`
  - `save_literature(...)`
  - `update_literature_save_visibility(...)`
  - `list_my_literature_saves(...)`
- add helper methods for:
  - resolving existing artifact by PMID/DOI/PMCID using external objects
  - creating/updating literature artifacts
  - creating/upserting `literature_save`
  - promoting an external-reference artifact to managed S3 in place
  - evaluating visible save summaries for a viewer
- keep all mutating literature methods idempotent
- use existing `backend.update_instance_json(...)` rather than inventing a new persistence system

Artifact rules:
- `artifact_type="literature"`
- `producer_system="pubmed"`
- `producer_object_euid=<pmid>`
- artifact metadata must include:
  - title
  - authors
  - journal
  - year
  - abstract or abstract_snippet
  - pmid
  - doi
  - pmcid
  - source_urls
  - best_fulltext_url
  - findit_reason
  - storage_mode
  - acquisition_mode
  - fulltext_status
  - `record_family="literature"`

Reference-only artifact rules:
- store a stable landing URL in the artifact storage fields using `https`/`http` backend
- use `availability_status="external_only"`

Managed artifact rules:
- store bytes in Dewey managed S3
- verify PDF before storing
- do not call managed-copy success if the response is not actually a PDF

Search integration:
- extend search-v2 artifact-row enrichment so literature artifacts can expose:
  - title
  - pmid / doi
  - storage_mode
  - saved_by_me
  - saved_by_others_count
  - visible owner labels
- update the existing UI search route to pass viewer context into the service for literature enrichment

### 5) `dewey_service/app.py`
Add:
- request models for literature search/save/update visibility
- `GET /literature` (session-auth HTML route)
- `POST /api/v1/literature/search` (session-auth JSON)
- `POST /api/v1/literature/save` (session-auth JSON, requires `Idempotency-Key`)
- `PATCH /api/v1/literature/saves/{literature_save_euid}` (session-auth JSON, requires `Idempotency-Key`)
- `GET /api/v1/literature/saves/mine` (session-auth JSON)

Keep the existing auth split:
- literature endpoints use `require_ui_session`
- do not convert them to bearer-only endpoints
- do not redesign generic bearer auth in this task

If metapub is unavailable at runtime:
- do not crash the whole app
- fail literature endpoints with a clear 503/runtime error message that metapub must be installed from the inspected source repo

### 6) Templates
Create:
- `dewey_service/templates/literature.html`

Update:
- `dewey_service/templates/ui_home.html` to link to `/literature`
- `dewey_service/templates/search.html` to show literature-specific info/badges when a result row is a literature artifact

UI should stay consistent with the current Dewey template style. Do not build a new frontend stack.

### 7) Tests
Add tests without live network access.

Update `tests/conftest.py`:
- extend `FakeDeweyService` with minimal literature methods needed by route tests

Add/extend tests for:
- literature page requires login and renders after Cognito session login
- literature search endpoint returns normalized results
- literature save endpoint enforces idempotency key
- saving a new paper creates:
  - one artifact
  - external-object links
  - one `literature_save`
- saving the same paper from another user reuses the artifact and creates another save record
- private saves do not leak through “saved by another user”
- selected-user and group visibility works
- external-reference artifact can be promoted in place to managed
- `/search` shows literature rows and ownership badges

Use the existing service-unit style in `tests/test_service_unit.py` for logic-heavy cases.
Use the existing route/UI test style in `tests/test_search_and_storage.py` and `tests/test_ui_session_auth.py` for app-level cases.

Do not add tests that hit NCBI or publisher sites.
Mock/stub the Dewey-local metapub adapter.

Acceptance criteria:
- all existing tests still pass
- new literature tests pass
- Dewey now has a working operator literature search/save flow
- saved literature is searchable through existing Dewey search
- ownership/visibility is explicit and minimally correct
- no metapub web/persistence/auth changes were introduced
- no second search/auth stack was introduced

When done, provide:
1. a short summary of the file changes
2. any follow-up risks or TODOs that you intentionally left deferred