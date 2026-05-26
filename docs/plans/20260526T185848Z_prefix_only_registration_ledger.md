# Dewey Prefix-Only Registration Ledger

Created: 2026-05-26T18:58:48Z

## Summary

Add an explicit Dewey endpoint and GUI form that register a single S3 prefix as one Dewey artifact. This must not expand the prefix into child objects, infer alternate endpoints, mutate AWS storage, tag objects, lock objects, or reuse the specialized sequencing run-prefix importer.

## Gate 0 Inventory

- Repo: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey`
- Branch: `codex/security-dewey-share-auth-20260526`
- Initial status: clean
- Activation: `source ./activate local` succeeded with conda env `DEWEY-local`
- Current behavior:
  - `POST /api/v1/artifacts` registers object-shaped artifacts only.
  - `POST /api/v1/artifacts/import` references or copies object sources.
  - `POST /api/v1/artifacts/import-run-prefix` registers prefix artifacts, but only through the Ultima sequencing hierarchy importer.
  - Browser S3 prefix intake expands prefixes to object artifacts.

## Ledger Rows

| ID | Area | Requirement | Status | Evidence | Terminal Note |
|---|---|---|---|---|---|
| LEDGER-001 | Planning | Create ledger with Gate 0 inventory | SUCCESS | This file | Inventory recorded before code edits. |
| API-001 | API | Add prefix-only request model and endpoint | SUCCESS | `dewey_service/app.py` adds `ArtifactPrefixRegisterRequest` and `POST /api/v1/artifact-prefixes`. | API endpoint added with bearer auth and idempotency. |
| SVC-001 | Service | Add service method that creates one prefix artifact without S3 listing or object mutation | SUCCESS | `dewey_service/services/artifacts.py`; `tests/test_service_artifacts.py::test_register_artifact_prefix_creates_single_prefix_without_s3_scan`. | Service records one `storage_kind=prefix` artifact and does not enumerate/tag S3. |
| GUI-001 | GUI | Add browser form for prefix-only registration | SUCCESS | `dewey_service/templates/artifacts.html`, `dewey_service/app.py`; `tests/test_artifacts_ui.py::test_artifacts_prefix_registration_form_creates_one_prefix_artifact`. | Browser form posts to `/artifacts/register-prefix`. |
| TEST-001 | Tests | Add API, service, GUI, route, and docs tests | SUCCESS | Focused validation command below -> `22 passed`; py_compile passed. Broader route coverage still has unrelated pre-existing share access/revoke gaps. | Prefix feature test coverage added and passed. |
| DOC-001 | Docs | Update API/GUI docs for prefix-only registration | SUCCESS | `docs/apis.md`, `docs/gui.md`; `tests/test_docs_smoke.py` passed. | Docs include API and GUI behavior. |
| FINAL-001 | Acceptance | Focused validation passes; no live AWS work | SUCCESS | No AWS/runtime commands beyond local tests. | Feature complete locally; no live mutation performed. |

## Constraints

- No live AWS, database, or runtime mutation.
- No fallback behavior, guessed endpoints, service-side discovery, or compatibility alias.
- Prefix registration requires an explicit `s3://bucket/prefix/` style URI with a non-empty key.
- Prefix registration records one prefix artifact and does not enumerate S3 descendants.

## Test Evidence

- `source ./activate local` -> activated `DEWEY-local`.
- `python -m py_compile dewey_service/app.py dewey_service/services/artifacts.py tests/conftest.py tests/test_artifact_registration.py tests/test_artifacts_ui.py tests/test_service_artifacts.py tests/test_docs_smoke.py` -> passed.
- `python -m pytest tests/test_service_artifacts.py::test_register_artifact_prefix_creates_single_prefix_without_s3_scan tests/test_artifact_registration.py tests/test_artifacts_ui.py tests/test_docs_smoke.py -q` -> `22 passed`.
- Broader `tests/test_route_surface_coverage.py::test_runtime_route_inventory_covers_first_party_surfaces` remains blocked by pre-existing direct-test gaps for `POST /api/v1/share-references/{share_reference_euid}/access` and `/revoke`; the new prefix endpoint is directly exercised by focused tests.
