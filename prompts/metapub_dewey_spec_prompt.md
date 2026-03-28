# GPT-5.4 Pro Extended Prompt

You are GPT-5.4 Pro Extended.

Your task is to inspect the attached repositories directly and produce a practical implementation-grade specification for adding PubMed literature discovery and Dewey registration flows using metapub.

You must work repo-first.

Do not infer implementation details from memory, PyPI pages, blog posts, or generic assumptions.

If repo contents conflict with your assumptions, the repo contents win.

## Repositories to inspect first

- `dewey.tgz`
- `metapub.tgz`

You must inspect both archives directly before writing anything substantial.

## What I actually want decided

I want the quickest robust path.

You must explicitly decide between these two implementation homes:

1. **Dewey-native feature using metapub as a library/integration**
2. **A web module built inside metapub and imported or embedded into Dewey**

You must choose one primary recommendation and defend it concretely from the repos.

Do not hedge unless the code truly forces ambiguity.

## Current intent

The desired product behavior is:

- a small web interface that exposes metapub capabilities inside a Dewey-like GUI
- users can search PubMed literature from that interface
- for papers of interest, users can directly register them with Dewey
- when possible, Dewey should:
  - download the paper to managed S3 storage
  - register a canonical Dewey artifact record
- when a paper cannot be downloaded lawfully or technically, Dewey should instead:
  - create a Dewey reference-style record pointing at the external source
- literature search results should indicate whether a paper is already known to Dewey
- the system should also indicate whether a paper is already saved by another user
- users should have preferences and visibility settings
- each saved item should support visibility policies like:
  - private to owner only
  - visible to selected other users
  - visible to all users
- Dewey search should indicate when a found paper is owned by someone else

## Important architectural posture

Prefer the solution that is:

- fastest to implement correctly
- least likely to distort Dewey’s ownership boundaries
- least likely to create a second conflicting auth / UI / persistence stack
- most consistent with Dewey as canonical artifact registry
- compatible with future extraction as a plugin if needed

## Grounding hints from the repos you must verify yourself

You still need to inspect everything yourself, but these are likely relevant areas:

### Dewey likely-relevant files
- `dewey/README.md`
- `dewey/dewey_service/app.py`
- `dewey/dewey_service/service.py`
- `dewey/dewey_service/tapdb_backend.py`
- `dewey/dewey_service/auth.py`
- `dewey/dewey_service/settings.py`
- `dewey/dewey_service/templates/*`
- `dewey/tests/*`
- `dewey/docs/bloom_dewey_vs_solo_dewey_gap_report.md`
- `dewey/docs/dewey_cutover_execution_plan.md`

### metapub likely-relevant files
- `metapub/README.md`
- `metapub/pyproject.toml`
- `metapub/metapub/pubmedfetcher.py`
- `metapub/metapub/pubmedarticle.py`
- `metapub/metapub/pubmedcentral.py`
- `metapub/metapub/findit/*`
- `metapub/docs/*`
- `metapub/tests/*`

## What you must determine from the real code

Determine and state clearly:

1. what Dewey already has that should be reused
2. what Dewey is missing for this feature
3. what metapub already provides that is directly reusable
4. what metapub does **not** provide and should not be forced to own
5. whether the feature should live in:
   - Dewey core
   - a Dewey plugin/module package in the Dewey repo
   - a shared integration package
   - metapub itself
6. what data model additions are required in Dewey
7. what auth / permissions model changes are required
8. what search/index strategy is sufficient for MVP
9. what exact user-visible flows should exist for MVP
10. what must be deferred

## Non-negotiable constraints

- Do not redesign Dewey into a generic research knowledge platform.
- Do not redesign metapub into a full web application framework unless the repos strongly justify it.
- Keep Dewey the canonical system of record for saved artifacts / references.
- Respect Dewey’s existing FastAPI + TapDB + Cognito-backed operator UI structure if that is what the repo shows.
- Respect existing Dewey idempotency patterns if present.
- Respect existing Dewey search surface and decide how to extend it rather than inventing an unrelated second search stack.
- Do not assume relational side tables outside TapDB if Dewey is TapDB-only in practice.
- Do not assume direct PDF download is always legal or technically possible.
- Do not propose bypassing publisher access rules.
- Be explicit about copyright, access-control, and provenance implications.

## Required product decision

At the top of the answer, include a section titled exactly:

`Recommended implementation home`

That section must contain one of these exact conclusions:

- `Build this in Dewey using metapub as a library.`
- `Build this in metapub and embed/import it into Dewey.`

Then explain why, grounded in the inspected repos.

## Feature scope to spec

Spec an MVP that includes all of the following if feasible within the current repo architecture:

### A. Literature search UI inside Dewey
- PubMed query form
- results list with title, journal, year, authors, PMID, DOI, abstract snippet if available
- status badges such as:
  - already in Dewey
  - saved by me
  - saved by another user
  - downloadable
  - external-link only

### B. Save/register flow
For any search result, support:
- `Save to Dewey as managed artifact` when Dewey can lawfully/technically store bytes
- `Save to Dewey as external reference` when bytes cannot be stored

### C. Dewey metadata and provenance
A saved literature object should preserve enough structured metadata to support:
- PMID
- DOI
- PMCID if present
- title
- authors
- journal
- year
- abstract or snippet if available
- source URLs
- acquisition mode
- storage mode
- provenance of who saved it and when
- visibility policy

### D. Ownership / visibility
Design a minimal but explicit model for:
- owner
- visibility scope
- optional per-user or per-group sharing
- visibility-aware search results

### E. Dewey search integration
The saved literature records must appear in Dewey search in a way consistent with repo reality.
You must decide whether to:
- extend `artifact` records only,
- add a new literature-specific artifact subtype,
- add `external_object` linkage patterns,
- add a separate template,
- or use another repo-grounded approach.

You must justify the choice.

## Explicit questions you must answer

Your output must answer these plainly:

1. Is the fastest robust path Dewey-first or metapub-first?
2. Should literature items be modeled as Dewey artifacts, Dewey external references, or both?
3. What is the smallest correct TapDB template set change?
4. How should “already saved by another user” be computed?
5. Where should visibility live in the model?
6. Should this be operator-only first, or user-facing in the main Dewey UI?
7. What exact endpoints and UI routes are needed for MVP?
8. What tests must be added?
9. What work is risky enough to defer until phase 2?

## Deliverables

Produce exactly these sections, in this order:

### 1. Recommended implementation home
One strong recommendation.

### 2. Repo-grounded findings
Use concrete file paths and cite specific repo structures and behaviors.

### 3. Proposed MVP architecture
Explain how Dewey and metapub interact.

### 4. Data model and persistence design
Be concrete about TapDB templates, fields, lineage/relations, and any search/index implications.

### 5. Auth, ownership, and visibility model
Be explicit and minimal.

### 6. API and UI specification
List exact new or changed routes, payload shapes, and UI surfaces.

### 7. Save-flow decision matrix
Include cases like:
- open access PDF available
- PMCID full text available
- DOI known but no downloadable PDF
- metadata only
- duplicate already in Dewey
- another user already saved same paper

### 8. Implementation plan by phase
Phase 1 should be the smallest end-to-end useful slice.

### 9. Test plan
Unit, integration, and UI tests grounded in the repo test patterns.

### 10. Risks, non-goals, and deferred work
Be blunt.

### 11. Codex IDE implementation prompt
Write a second prompt, suitable for Codex IDE, that implements the chosen design in the real repo.
This prompt must be execution-oriented, file-specific, and conservative.

## Style requirements

- Be direct.
- State assumptions.
- Prefer one endorsed path.
- Do not write a theory essay.
- Do not produce a vague “options matrix” unless needed for a hard tradeoff.
- Use concrete file paths from the repos.
- Call out where the current repos are insufficient to support a clean implementation.

## Critical warning

Do not just describe a generic literature manager.

This task is specifically about extending the actual Dewey and metapub repos that were attached.

If something cannot be supported cleanly by the current repos, say so plainly and propose the smallest correct change.
