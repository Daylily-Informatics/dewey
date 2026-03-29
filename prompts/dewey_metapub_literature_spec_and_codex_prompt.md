# Dewey + metapub literature discovery MVP spec

## 1. Recommended implementation home

Build this in Dewey using metapub as a library.

That is the fastest robust path from the actual repos.

Why:

- `dewey/README.md` and `dewey/dewey_service/app.py` show Dewey already owns the web surface, Cognito-backed browser UI, TapDB persistence, S3-managed artifact handling, and the canonical artifact/search APIs.
- `dewey/dewey_service/service.py` already has the right mutation primitives: persisted idempotency, artifact registration, external-object linking, and direct `http(s)`/`s3` copy into managed S3.
- `metapub/README.md`, `metapub/metapub/pubmedfetcher.py`, `metapub/metapub/pubmedarticle.py`, and `metapub/metapub/findit/*` show metapub is a lookup/discovery library plus CLI utilities, not a web app framework.
- I found no FastAPI/Flask/Django web module in metapub. Putting UI/auth/persistence there would create a second conflicting stack and invert Dewey’s stated ownership boundary.

Primary recommendation for implementation location:

- **Dewey core**, but implemented as a **small Dewey-local module/package inside the Dewey repo** so it can be extracted later if needed.
- **Do not put this feature in metapub.**
- **Do not create a separate shared service/package for MVP.**

Plain answers up front:

- **Fastest robust path:** Dewey-first.
- **Model saved literature as:** Dewey artifacts, with external-object links for PubMed/DOI/PMCID, plus one new Dewey save/visibility record template.
- **Smallest correct TapDB template change:** add one template for per-user literature saves/visibility.
- **Operator-only or broad end-user first:** operator-only first, in the existing Cognito-backed Dewey UI.

---

## 2. Repo-grounded findings

### Dewey already has the right home for this feature

1. **Canonical registry ownership already lives in Dewey.**  
   `dewey/README.md` says Dewey owns artifact identity/metadata, artifact-set identity/membership, artifact resolution/storage metadata lookup, share-reference issuance, and external-object links. It explicitly does **not** own unrelated execution-state concerns.

2. **The runtime shape already fits the requested product.**  
   `dewey/dewey_service/app.py` wires:
   - FastAPI app creation
   - Cognito-backed UI session auth via `require_ui_session`
   - server-rendered UI routes (`/ui`, `/search`, `/search/export`)
   - bearer-token API routes for machine use

3. **The current UI/auth split is real and should be reused, not replaced.**  
   In `dewey/dewey_service/app.py`, Cognito callback stores:
   - `operator_profile.email`
   - `operator_profile.sub`
   - `operator_profile.groups`  
   That is enough for a minimal owner/visibility model without inventing a second auth source.

4. **Dewey already has idempotent mutation patterns that should be preserved.**  
   `dewey/dewey_service/service.py` persists request fingerprints and stored responses for mutating flows. This is already exercised in `tests/test_idempotency.py` and `tests/conftest.py`.

5. **Dewey already has a usable canonical integration-link model.**  
   `dewey/dewey_service/tapdb_backend.py` defines:
   - `artifact`
   - `artifact_set`
   - `share_reference`
   - `external_object`
   - `external_object_relation`
   - `idempotency_request`  
   This is exactly the right base for PubMed/DOI/PMCID linking.

6. **Dewey already has a managed-byte ingestion path.**  
   In `dewey/dewey_service/service.py`, `import_artifact_from_uri(..., import_mode="copy")` can:
   - copy from `s3://...`
   - download from `http(s)://...`
   - write bytes into managed S3
   - register the artifact idempotently

7. **Dewey search is thin but extensible.**  
   `dewey/dewey_service/service.py` search v2 currently:
   - searches only `artifact` and `share_reference`
   - full-text matches over artifact metadata and external-object JSON
   - does in-memory filtering/sorting over TapDB rows  
   That is not a full search engine, but it is enough for MVP saved-literature discovery.

8. **The repo itself says richer discovery is a likely next step.**  
   `dewey/docs/bloom_dewey_vs_solo_dewey_gap_report.md` explicitly calls out search/discoverability as the largest likely gap before bigger Dewey feature work.

### Dewey is missing a few things this feature needs

1. **No literature-specific UI exists.**
2. **No user-save or visibility model exists.**
3. **No subject-aware search filtering exists for human users.**
4. **No canonical PubMed/DOI/PMCID dedupe helper exists.**
5. **No reference-only literature save flow exists as a product feature.**
6. **No server-side user preference/profile persistence exists.**
7. **No explicit legal-copy eligibility policy exists for publisher-hosted PDFs.**

### metapub already provides the right library pieces

1. **PubMed query and article hydration.**  
   `metapub/metapub/pubmedfetcher.py` provides:
   - `pmids_for_query(...)`
   - `article_by_pmid(...)`
   - `article_by_doi(...)`
   - `article_by_pmcid(...)`

2. **Structured bibliographic metadata.**  
   `metapub/metapub/pubmedarticle.py` exposes:
   - PMID
   - DOI
   - PMCID
   - title
   - authors / author list
   - journal
   - year / pubdate
   - abstract
   - keywords / MeSH / other article metadata

3. **Best-effort full-text discovery.**  
   `metapub/metapub/findit/findit.py` and `metapub/metapub/findit/logic.py` provide `FindIt`, which tries to discover direct PDF URLs or returns a reason when it cannot.

4. **Reason taxonomy that is product-usable.**  
   `metapub/metapub/findit/FINDIT_ERROR_PHILOSOPHY.md` defines reasons such as:
   - `PAYWALL`
   - `DENIED`
   - `POSTONLY`
   - `NOFORMAT`
   - `TXERROR`
   - `MISSING`  
   Those reasons are useful for Dewey UI badges and save-mode decisions.

5. **Important repo-grounded legal/behavior boundary.**  
   `metapub/metapub/findit/logic.py` explicitly says **FindIt does not download PDFs**. It discovers URLs and verifies access patterns, but it is not a storage or ingestion system.

6. **The journal registry is substantial.**  
   `metapub/tests/test_findit.py` expects the registry to contain more than 10,000 journals. That is enough to justify using it as the primary discovery helper instead of reinventing publisher handling in Dewey.

### metapub does not provide, and should not be forced to own

1. Web UI
2. Cognito/auth/session management
3. TapDB persistence
4. S3 artifact storage policy
5. Dewey artifact identity
6. Dewey ownership/visibility records
7. Dewey search integration
8. Dewey idempotent write semantics
9. A second conflicting artifact registry

### Assumptions and trade-offs I am making

1. **This ships first as a browser UI feature.**  
   That is consistent with Dewey’s current real auth/UI surface.

2. **The library source of truth is the inspected metapub repo, not PyPI behavior.**  
   I am not assuming any not-inspected web module or richer API than the repo actually contains.

3. **Auto-copy to managed S3 must be conservative.**  
   metapub can find legal access links, but that is not the same thing as Dewey having redistribution/storage rights. For MVP, managed-copy should be limited to:
   - PubMed Central / Europe PMC style open repositories
   - and/or an explicit allowlist of copy-eligible domains  
   Everything else should fall back to reference-only save.

---

## 3. Proposed MVP architecture

### Chosen implementation home inside Dewey

Implement this **in Dewey core**, but isolate it as a Dewey-local module so the seams are clean:

- `dewey_service/literature.py` (or equivalent)
  - metapub adapter
  - viewer/visibility helpers
  - literature identity normalization
  - copy-eligibility rules
- `dewey_service/service.py`
  - canonical save/dedupe/promote logic
  - search enrichment for saved literature
- `dewey_service/app.py`
  - UI routes + session-authenticated JSON endpoints
- `dewey_service/templates/literature.html`
  - the new Dewey literature page

This is **not** a metapub feature. It is a Dewey feature that calls metapub.

### MVP component interaction

#### A. Literature search UI inside Dewey

1. User opens **`GET /literature`** in Dewey.
2. Dewey submits the query to a Dewey-local metapub adapter.
3. The adapter:
   - calls `PubMedFetcher.pmids_for_query`
   - hydrates each PMID via `article_by_pmid`
   - optionally runs `FindIt` to classify access
4. Dewey enriches each result with registry state:
   - matching canonical Dewey artifact, if any
   - whether current user already saved it
   - whether another visible user saved it
   - whether Dewey can manage-copy it under current copy-eligibility rules
5. Dewey renders the results in the existing browser UI style.

#### B. Save/register flow

For each result, Dewey evaluates three things:

1. **Canonical article identity**
   - PMID first
   - then DOI
   - then PMCID
   - stored as `external_object` links

2. **Storage path**
   - **managed** if a direct PDF is available **and** Dewey is allowed to store it
   - **external reference** otherwise

3. **User-specific save**
   - owner = current Cognito user
   - visibility = private / selected / all users

#### C. Canonical saved object strategy

Use **one canonical Dewey artifact per paper** for MVP.

- `artifact_type = "literature"`
- `metadata.storage_mode = "managed"` or `"external_reference"`
- PubMed/DOI/PMCID are attached via `external_object` relations
- user-specific ownership and visibility live in a new `literature_save` template

This avoids making Dewey search/users reason about duplicate paper objects.

### Why I am not recommending a metapub web module

Because the metapub repo does not justify it:

- no existing web framework
- no auth model
- no persistence layer
- no S3 artifact semantics
- no registry ownership  
  Building that there would be slower and architecturally wrong.

### Why I am not recommending a separate shared package first

Because the fastest robust path is to keep the feature where the real boundary already is:

- Dewey already owns saved-object identity
- Dewey already owns the browser UI
- Dewey already owns artifact persistence and search
- the metapub seam can be one small adapter class inside Dewey

A separate package can come later if the feature stabilizes and multiple apps truly need it.

### MVP search/index strategy

**Sufficient for MVP:**

- metapub for upstream PubMed search
- TapDB + Dewey search v2 for saved-item discovery
- `external_object.external_identity_key` lookup for exact PMID/DOI/PMCID matching
- existing search-v2 metadata text matching for title/journal/authors/abstract/IDs

**Not needed for MVP:**

- Elasticsearch/OpenSearch
- a new literature index
- a second search service

This matches the repo’s current posture: `dewey/docs/bloom_dewey_vs_solo_dewey_gap_report.md` and current `service.py` both point toward “extend Dewey search,” not “invent a separate search stack.”

### Direct answers to the architecture questions

1. **Is the fastest robust path Dewey-first or metapub-first?**  
   **Dewey-first.**

2. **Should the feature live in Dewey core, a Dewey module, a shared package, or metapub itself?**  
   **Dewey core, implemented as a Dewey-local module/package inside the Dewey repo.**

3. **Should this be operator-only first, or user-facing in the main Dewey UI?**  
   **Operator-only first, inside the existing Cognito-backed Dewey UI.**

---

## 4. Data model and persistence design

### Smallest correct TapDB template set change

Add **one** new template:

- **`dewey/access/literature_save/1.0/`**
- suggested prefix: **`LS`**

Do **not** add a second literature-work template for MVP.  
Do **not** add relational side tables.  
Do **not** move ownership into metapub.

Everything else reuses existing Dewey templates:

- `artifact`
- `external_object`
- `external_object_relation`
- `idempotency_request`

### Why one new template is necessary

Storing ownership/visibility directly on `artifact` is wrong for this use case because one paper may be:

- saved by multiple users
- with different visibility settings
- without duplicating the canonical Dewey paper record

That is a many-to-one relationship. A separate save record is the smallest correct model.

### Canonical literature artifact model

Use the existing `artifact` template for the saved paper itself.

#### Artifact core fields

For all literature artifacts:

- `artifact_type = "literature"`
- `producer_system = "pubmed"`
- `producer_object_euid = <PMID>`
- `metadata.record_family = "literature"`

#### Managed-copy artifact

When Dewey stores bytes in S3:

- `storage_backend = "s3"`
- `bucket = <managed bucket>`
- `key = <managed key>`
- `availability_status = "available"`
- `import_mode = "copy"`
- `storage_status = "verified"`

#### External-reference artifact

When Dewey cannot or should not store bytes:

- `storage_backend = "https"` or `"http"` (matching the chosen landing URL scheme)
- `bucket = <URL host>`
- `key = <URL path and query>`
- `availability_status = "external_only"`
- `import_mode = "register"`
- `storage_status = "registered"`

This is a pragmatic fit with the existing artifact model and does **not** require a second “reference” template.

### Canonical literature metadata contract on the artifact

Store this in `artifact.metadata`:

```json
{
  "record_family": "literature",
  "title": "Example paper title",
  "authors": ["A Author", "B Author"],
  "journal": "Nature",
  "year": 2024,
  "abstract": "Full abstract if available",
  "abstract_snippet": "Short snippet for search/UI",
  "pmid": "12345678",
  "doi": "10.1000/example",
  "pmcid": "PMC1234567",
  "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "doi_url": "https://doi.org/10.1000/example",
  "pmc_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
  "source_urls": [
    "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    "https://doi.org/10.1000/example"
  ],
  "best_fulltext_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf/",
  "findit_reason": null,
  "storage_mode": "managed",
  "acquisition_mode": "pmc_pdf",
  "fulltext_status": "downloadable"
}
```

Required preserved fields from the prompt:

- PMID
- DOI
- PMCID
- title
- authors
- journal
- year
- abstract or snippet
- source URLs
- acquisition mode
- storage mode

### New `literature_save` record model

Each user save becomes one `literature_save` instance linked to the artifact.

Suggested JSON payload:

```json
{
  "artifact_euid": "AT000123",
  "save_identity_key": "AT000123:user-sub-1",
  "owner_sub": "user-sub-1",
  "owner_email": "alice@example.com",
  "visibility_scope": "private",
  "shared_with_emails": [],
  "shared_with_groups": [],
  "created_at": "2026-03-10T00:00:00Z",
  "updated_at": "2026-03-10T00:00:00Z"
}
```

Suggested lineage:

- `artifact --has_literature_save--> literature_save`

### Visibility lives on the save record, not on the artifact

This is the key modeling choice.

- The **artifact** is the canonical Dewey paper record.
- The **save record** is the user’s ownership/visibility relationship to that artifact.

That is the only model here that cleanly supports:
- one canonical paper
- multiple saving users
- per-user visibility

### External-object linkage

For each saved paper, attach all available identifiers as Dewey external objects:

- `external_system = "pubmed"`, `external_object_type = "article"`, `external_object_id = <PMID>`
- `external_system = "doi"`, `external_object_type = "article"`, `external_object_id = <DOI>`
- `external_system = "pmc"`, `external_object_type = "article"`, `external_object_id = <PMCID>`

Attach each with the existing `external_object_relation` model.

This gives Dewey:

- exact identity lookup by PMID/DOI/PMCID
- clean search-v2 text exposure through `external_objects`
- better long-term interoperability than stuffing everything into freeform metadata only

### Canonical dedupe rule

Use this resolution order when saving/search-enriching a PubMed result:

1. exact PubMed external object match by PMID
2. exact DOI external object match
3. exact PMCID external object match

If any of those already resolves to an artifact, reuse that artifact.

If none resolve, create a new artifact and attach all available identifiers.

### Managed-copy eligibility rule

This is where legal and technical constraints matter.

#### MVP rule

Allow automatic managed copy **only** when all of the following are true:

1. `FindIt` (or equivalent Dewey re-check) yields a direct PDF URL
2. the response is actually a PDF (`content-type` includes PDF and/or content begins with `%PDF`)
3. the source domain is copy-eligible:
   - PMC / Europe PMC by default
   - plus any explicit Dewey allowlist domains configured later

Everything else becomes an external-reference artifact.

That is the quickest robust rule that does not silently turn “legal access link” into “approved for internal byte redistribution/storage.”

### Promote-in-place behavior for later managed copies

If a paper already exists as an external-reference artifact and a later save can lawfully/technically manage-copy the PDF, **promote the same artifact in place**:

- keep the same `artifact_euid`
- update storage fields to managed S3
- set `metadata.storage_mode = "managed"`
- preserve original landing URLs and provenance in metadata

Why I recommend this:

- search results stay stable
- save records do not need to be re-pointed
- no duplicate paper records appear in Dewey search

Trade-off:

- this introduces one targeted artifact update path, but that is still smaller and cleaner than inventing a second paper-representation model for MVP

### Search/index implications

For MVP, do **not** add a new index.

Extend current Dewey search behavior like this:

1. Saved literature artifacts remain normal `artifact` search rows.
2. Literature discovery in `/search` uses:
   - artifact metadata text
   - attached external objects
3. The search service augments literature artifact rows with:
   - `saved_by_me`
   - `saved_by_others_count`
   - visible owner labels
   - `storage_mode`
   - `pmid` / `doi` / `journal` / `year` convenience fields

That is sufficient for the requested MVP and consistent with the repo’s current search posture.

### Plain answer: artifact, external reference, or both?

**Always model the saved paper as a Dewey artifact.**  
A paper may be a managed-byte artifact or an external-reference artifact, but it is still an `artifact`.  
Use `external_object` links for PubMed/DOI/PMCID identity.  
Use `literature_save` for owner/visibility.

---

## 5. Auth, ownership, and visibility model

### MVP auth stance

Use the existing Dewey operator auth model exactly as it exists today:

- UI routes and literature actions use `require_ui_session`
- owner identity comes from the Cognito-derived `operator_profile` already stored in session

Relevant available fields from the current repo:

- `profile.email`
- `profile.sub`
- `profile.groups`

### Ownership model

- **Owner key:** `operator_profile.sub`
- **Owner display:** `operator_profile.email`

Use `sub` as the stable owner identity and keep `email` as display/debug info.

### Visibility model

Use one explicit field on `literature_save`:

- `visibility_scope = "private" | "selected" | "all"`

Supporting fields:

- `shared_with_emails: list[str]`
- `shared_with_groups: list[str]`

Visibility evaluation:

| visibility_scope | visible to |
|---|---|
| `private` | owner only |
| `selected` | owner, listed emails, and/or listed groups |
| `all` | any authenticated Dewey UI user |

### Where visibility should live

**On `literature_save`, not on the artifact.**

Why:

- visibility is user-relative
- the artifact is canonical
- multiple users may save the same paper differently

### How “already saved by another user” should be computed

For a given current viewer and canonical artifact:

1. find all `literature_save` records attached to that artifact
2. keep only saves visible to the current viewer
3. exclude the viewer’s own save
4. if any remain, set:
   - `saved_by_another_user = true`
   - `saved_by_others_count = len(remaining)`
   - optionally expose `other_owner_emails` for visible non-private saves

Important privacy rule:

- **private saves owned by other users do not count as visible “already saved by another user” badges**

That is the minimal privacy-respecting interpretation consistent with the prompt.

### Operator-only first vs broader user-facing UI

**Operator-only first in the existing Dewey UI.**

Why:

- Dewey already has session auth for browser users
- Dewey bearer-token API auth is currently machine-token based, not user-subject based
- trying to make the generic bearer APIs permission-aware in MVP would create a second auth story and slow the feature down

### Bearer-token API stance for MVP

Do **not** redesign Dewey’s generic bearer auth in this feature.

For MVP:

- literature actions are session-authenticated operator routes/endpoints
- generic Dewey bearer APIs remain system-level/admin-level and out of this end-user permission model

That keeps the MVP honest and bounded.

### Preferences

The prompt asks for user preferences and visibility settings.

**MVP answer:**

- implement **per-save visibility settings** server-side
- do **not** add a server-side user-preference profile template yet
- optionally remember the last-used visibility in browser local storage for UI convenience

Reason:

- the repo has no user-profile persistence model today
- adding one is not necessary for a correct MVP
- per-save visibility is the part that changes Dewey behavior and needs to be persisted

---

## 6. API and UI specification

## New UI route

### `GET /literature`
**Auth:** UI session (`require_ui_session`)

Purpose:
- render PubMed search UI
- show result list with Dewey match badges
- show recent saves for current user

Suggested query params:
- `q` (optional)
- `page` (default `1`)
- `page_size` (default `10`, max `10` or `20` to control latency)
- `mine_only` (optional, default `false`)

Behavior:
- if `q` absent: show empty search form + recent saves
- if `q` present: run metapub search and render results

### UI surface on `/literature`

Required visible controls and elements:

1. **PubMed query form**
   - free-text query
   - page size selector
   - search button

2. **Result rows**
   - title
   - journal
   - year
   - authors
   - PMID
   - DOI
   - abstract snippet if available

3. **Status badges**
   - already in Dewey
   - saved by me
   - saved by another user
   - downloadable
   - external-link only

4. **Save controls**
   - `Save to Dewey` (default auto mode)
   - optional explicit mode selector:
     - auto
     - managed artifact
     - external reference
   - visibility selector:
     - private
     - selected users/groups
     - all users
   - selected emails/groups text inputs (comma-separated is fine for MVP)

5. **Recent saves**
   - my recent literature saves
   - with current visibility setting
   - link to Dewey artifact/search entry

---

## New session-authenticated JSON endpoints

### `POST /api/v1/literature/search`
**Auth:** UI session (`require_ui_session`)  
**Idempotency:** not required

Request body:

```json
{
  "q": "crispr base editor",
  "page": 1,
  "page_size": 10,
  "include_access_check": true
}
```

Response shape:

```json
{
  "items": [
    {
      "pmid": "12345678",
      "doi": "10.1000/example",
      "pmcid": "PMC1234567",
      "title": "Example paper",
      "journal": "Nature",
      "year": 2024,
      "authors": ["A Author", "B Author"],
      "abstract_snippet": "Short abstract snippet",
      "source_urls": {
        "pubmed": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        "doi": "https://doi.org/10.1000/example",
        "pmc": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
        "best_fulltext": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf/"
      },
      "access": {
        "status": "downloadable",
        "reason": null,
        "managed_copy_eligible": true
      },
      "dewey": {
        "artifact_euid": "AT000123",
        "already_in_dewey": true,
        "saved_by_me": false,
        "my_save_euid": null,
        "saved_by_others_count": 1,
        "other_owner_emails": ["bob@example.com"],
        "storage_mode": "managed"
      }
    }
  ],
  "page": 1,
  "page_size": 10,
  "has_more": true
}
```

Notes:

- `access.status` values:
  - `downloadable`
  - `external_only`
  - `unknown`
- `managed_copy_eligible` is the Dewey storage decision, not just “FindIt found a URL”

### `POST /api/v1/literature/save`
**Auth:** UI session (`require_ui_session`)  
**Idempotency:** required via `Idempotency-Key`

Request body:

```json
{
  "pmid": "12345678",
  "doi": "10.1000/example",
  "pmcid": "PMC1234567",
  "title": "Example paper",
  "journal": "Nature",
  "year": 2024,
  "authors": ["A Author", "B Author"],
  "abstract": "Full abstract if available",
  "source_urls": {
    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    "doi": "https://doi.org/10.1000/example",
    "pmc": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
    "best_fulltext": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf/"
  },
  "access_status": "downloadable",
  "findit_reason": null,
  "preferred_save_mode": "auto",
  "visibility_scope": "selected",
  "shared_with_emails": ["bob@example.com"],
  "shared_with_groups": ["literature-reviewers"]
}
```

Allowed `preferred_save_mode` values:

- `auto`
- `managed`
- `external_reference`

Save rules:

- `auto`: managed if eligible, otherwise external reference
- `managed`: fail if managed copy is not eligible
- `external_reference`: always save as reference even if a managed copy is possible

Response shape:

```json
{
  "artifact": {
    "artifact_euid": "AT000123",
    "artifact_type": "literature",
    "availability_status": "available",
    "metadata": {
      "record_family": "literature",
      "pmid": "12345678",
      "doi": "10.1000/example",
      "storage_mode": "managed"
    }
  },
  "literature_save": {
    "literature_save_euid": "LS000001",
    "artifact_euid": "AT000123",
    "owner_email": "alice@example.com",
    "visibility_scope": "selected",
    "shared_with_emails": ["bob@example.com"],
    "shared_with_groups": ["literature-reviewers"],
    "created_at": "2026-03-10T00:00:00Z",
    "updated_at": "2026-03-10T00:00:00Z"
  },
  "effective_save_mode": "managed",
  "artifact_created": true,
  "artifact_promoted": false,
  "save_created": true
}
```

### `PATCH /api/v1/literature/saves/{literature_save_euid}`
**Auth:** UI session (`require_ui_session`)  
**Idempotency:** required via `Idempotency-Key`

Request body:

```json
{
  "visibility_scope": "all",
  "shared_with_emails": [],
  "shared_with_groups": []
}
```

Response:
- updated `literature_save` row

### `GET /api/v1/literature/saves/mine`
**Auth:** UI session (`require_ui_session`)

Purpose:
- feed the “My recent saves” block on `/literature`
- optionally power later “My Library” style UI

Response:
- paginated recent visible saves for the current owner, joined with artifact metadata

---

## Changed existing routes

### `GET /ui`
Add a nav link/card entry for **Literature**.

### `GET /search`
Keep the same route, but change the behavior for literature artifacts:

- pass current `profile` into search service enrichment
- show literature-specific row metadata:
  - title
  - PMID/DOI
  - journal/year
  - storage mode
  - “saved by me” / “saved by another user” badges

### `GET /search/export`
No new export format is required for MVP, but exported literature rows should include their metadata fields if they appear in the current user’s visible search results.

---

## What I would not add in MVP

1. No separate “metapub UI”
2. No public end-user route outside Dewey
3. No new generic permissions subsystem
4. No new search backend
5. No background worker requirement
6. No deletion/archive API unless explicitly needed

---

## 7. Save-flow decision matrix

| Case | Dewey action | Artifact result | Save result | Notes |
|---|---|---|---|---|
| Open-access PDF available from PMC / Europe PMC | Download bytes to managed S3, create or reuse canonical artifact | `artifact_type=literature`, `storage_mode=managed`, `availability_status=available` | create/upsert `literature_save` | Fastest safe auto-managed path |
| Direct PDF URL available from non-PMC publisher and domain is explicitly allowlisted | Download bytes to managed S3 | managed artifact | create/upsert save | Only if Dewey config says this domain is copy-eligible |
| Direct PDF URL available but domain is **not** allowlisted | Do **not** copy; create or reuse external-reference artifact | `storage_mode=external_reference`, `availability_status=external_only` | create/upsert save | Conservative legal posture for MVP |
| PMCID exists but no direct PDF could be validated | Create/reuse external-reference artifact using PMCID/PMC landing page | external-reference artifact | create/upsert save | Keep IDs and links; no byte storage |
| DOI known but `FindIt` returns `PAYWALL`, `DENIED`, `POSTONLY`, `NOFORMAT`, or `TXERROR` | Create/reuse external-reference artifact using DOI or PubMed landing URL | external-reference artifact | create/upsert save | Persist `findit_reason` |
| Metadata only, no usable DOI/PMCID/fulltext URL | Create/reuse external-reference artifact using PubMed landing URL | external-reference artifact | create/upsert save | Still a valid Dewey save |
| Duplicate already in Dewey, current user has not saved it | Reuse canonical artifact | no new artifact unless promotion needed | create new `literature_save` | No duplicate paper object |
| Another user already saved the same paper and it is visible to me | Reuse canonical artifact | no new artifact unless promotion needed | create my save record too | UI shows “saved by another user” before save |
| Another user already saved the same paper but only privately | Reuse canonical artifact internally | no new artifact unless promotion needed | create my save record | No pre-save visibility leak in UI |
| Existing external-reference artifact later becomes managed-copy eligible | Promote same artifact in place to managed storage | same `artifact_euid`, now `storage_mode=managed` | existing saves remain attached | Avoid duplicate Dewey paper rows |
| User explicitly requests `managed` but no managed copy is eligible | return validation error; do not silently downgrade | unchanged | no save unless user retries with `auto` or `external_reference` | Better UX than pretending a managed save happened |
| User explicitly requests `external_reference` even though managed copy is eligible | keep/create external-reference artifact | external-reference artifact | create/upsert save | Honor explicit user choice |

---

## 8. Implementation plan by phase

### Phase 1 — smallest end-to-end useful slice

This is the recommended MVP.

#### Scope

1. Add a Dewey-local metapub adapter
2. Add `literature_save` TapDB template
3. Add `/literature` browser UI
4. Add session-authenticated search/save/update-visibility endpoints
5. Save PubMed results into Dewey as canonical `artifact_type="literature"`
6. Support both:
   - managed copy (PMC / allowlisted direct PDF only)
   - external reference fallback
7. Attach PubMed/DOI/PMCID via existing external-object models
8. Extend `/search` UI to show saved literature rows and ownership badges
9. Add tests with no live network dependency

#### Explicit Phase 1 decisions

- **Dewey-first**: yes
- **operator-only first**: yes
- **single canonical artifact per paper**: yes
- **one new template only**: yes
- **no metapub repo changes required**: yes
- **no new search engine**: yes

### Phase 2 — useful hardening

1. Add background/async access enrichment so literature search latency is less tied to `FindIt`
2. Add delete/archive/un-save behavior
3. Add better viewer filtering to more generic artifact APIs if product needs it
4. Add richer `/search` filters for literature fields (PMID, DOI, journal, year, owner)
5. Add better browser UI for editing selected users/groups
6. Add persistent server-side user defaults/preferences if they become necessary

### Phase 3 — extraction / broader platform work

1. Make bearer-auth literature APIs subject-aware if Dewey starts using per-user JWTs instead of only service tokens
2. Consider extracting the metapub adapter seam into a plugin package if multiple apps need it
3. Consider a richer “paper work vs representation” model only if the promote-in-place path becomes too limiting

---

## 9. Test plan

Ground this in the repo’s actual test patterns.

### Unit tests (`tests/test_service_unit.py`)

Add service-level tests using the existing in-memory backend / fake storage patterns for:

1. **PubMed identity normalization**
   - PMID/DOI/PMCID normalization
   - canonical artifact resolution by external object

2. **Managed-copy eligibility**
   - PMC domain allowed
   - non-allowlisted publisher denied for managed copy
   - `managed` request fails when not eligible

3. **Save creation**
   - new artifact + new save
   - existing artifact + new save
   - existing save idempotent replay

4. **Reference-to-managed promotion**
   - existing external-reference artifact is promoted in place when a later eligible PDF appears

5. **Visibility evaluation**
   - private
   - selected email
   - selected group
   - all users

6. **“Saved by another user” calculation**
   - counts only visible non-owner saves
   - does not leak private saves

7. **Search v2 enrichment**
   - literature artifact rows get pmid/doi/title/owner summary fields
   - `/search` viewer sees own + shared literature rows correctly

### Route tests (`tests/test_literature_routes.py`)

Follow the same style as `tests/test_search_and_storage.py` and `tests/test_ui_session_auth.py`.

Add tests for:

1. `/literature` requires login
2. `/literature` renders after Cognito-session login
3. `/api/v1/literature/search` returns normalized result payload
4. `/api/v1/literature/save` requires `Idempotency-Key`
5. `/api/v1/literature/save` creates canonical artifact + save
6. `/api/v1/literature/saves/{id}` updates visibility
7. `/search` renders visible literature ownership badges

### Fake service / fixture changes (`tests/conftest.py`)

Extend `FakeDeweyService` with minimal literature methods:

- `search_literature(...)`
- `save_literature(...)`
- `update_literature_save_visibility(...)`
- `list_my_literature_saves(...)`

This keeps route tests aligned with how the existing app fixture is already structured.

### UI tests

Add at least one HTML assertion test for:

- Literature page title / form
- Result row rendering with badges
- Search page literature badge rendering

### metapub dependency rule for tests

**Do not run live NCBI/publisher network calls in Dewey tests.**

Instead:

- mock/stub the Dewey-local metapub adapter
- keep route tests deterministic
- keep service tests deterministic

This is especially important because the inspected metapub repo includes live-network tests and publisher verification behavior.

### Minimum required test additions before calling MVP done

1. unit tests for save/dedupe/promotion/visibility
2. route tests for `/literature` and save/update endpoints
3. one search UI integration test showing literature row discovery

---

## 10. Risks, non-goals, and deferred work

### Risks

1. **Publisher variability and latency**  
   `FindIt` can be slow or brittle because it depends on external publisher behavior.

2. **Legal copy ambiguity outside PMC/open repositories**  
   metapub can find legal access URLs, but that does not automatically grant Dewey rights to store/redistribute bytes internally. The MVP must be conservative.

3. **Current bearer auth is not user-subject aware**  
   Dewey’s current bearer model is for service tokens, not end-user permissions.

4. **Promote-in-place is pragmatic, not a full representation model**  
   It is the right MVP trade-off, but it is not a long-term paper/work/version ontology.

5. **Selected-user sharing by raw email/group strings is lightweight**  
   It works with current Cognito session claims, but it is not a full directory-backed collaboration system.

6. **Search scaling is limited**  
   Current search v2 does in-memory filtering over fetched rows. That is fine for MVP volume, not for a large institutional paper library.

### Non-goals

1. Do **not** redesign Dewey into a general research knowledge platform
2. Do **not** redesign metapub into a web app
3. Do **not** build a second auth stack
4. Do **not** bypass publisher paywalls, login flows, or POST-only download constraints
5. Do **not** scrape/render HTML into PDFs
6. Do **not** implement full-text parsing, OCR, or semantic extraction
7. Do **not** add Elasticsearch/OpenSearch for MVP
8. Do **not** add persistent server-side user preference profiles unless product insists

### Deferred work

1. server-side user defaults/preferences
2. group picker / directory-backed sharing UX
3. async/background access classification
4. bulk save/import from PubMed lists
5. richer search facets for literature-specific fields
6. delete/archive/un-save flow
7. broader subject-aware bearer APIs
8. plugin extraction if multiple apps start needing the same Dewey-local literature module

### Blunt recommendation on what must be deferred

The riskiest work to defer until phase 2 is:

- **broad non-PMC managed-copy support**
- **generic user-aware bearer APIs**
- **a richer multi-representation paper model**
- **server-side user preference profiles**
- **new search infrastructure**

Those are real projects. They are not needed for a correct MVP.

---

## 11. Codex IDE implementation prompt

```md
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
```
