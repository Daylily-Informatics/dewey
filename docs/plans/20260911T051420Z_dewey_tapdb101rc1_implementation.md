# Dewey TapDB 10.1.1rc1 application adoption

Owner: Agent D. Local implementation worktree:
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-implementation-20260911`.
Branch: `codex/dewey-implementation-20260911` from `ca77faeeb82ad4f284114b6d019decacd3dc51b1`.
Controlling requirements: L06/L07 in the approved migration ledger. The coordinator
alone updates that ledger and performs live operations; C owns migration tooling.

## Baseline and scope

The initial worktree was clean. Its source boundary is the deployed resolver and
container CLI plus reconciled main documentation. Initial inspection found the
TapDB 9.0.9 Git dependency, removed DAG v1 factories, private CLI context wiring,
startup anomaly insertion, SQL prefix/template bootstrap and template overwrite,
a managed-literature-copy exception fallback and invalid search-filter fallbacks.

Implement exact published `daylily-tapdb[aurora,gui]==10.1.0` and
`meridian-euid==0.4.8`, Python >=3.12, public scoped runtime sessions and DAG v2,
canonical embedded GUI, explicit target validation and verification-only startup.
Preserve QEO resolver/package/container CLI semantics and original persisted
identities, domain and prefix bindings. No migration, seeding, principal changes,
AWS operations, releases or production writes occur in this worktree.

The immutable TapDB package documents `get_db_config(config_path=...)` in its
root module example despite that function's CLI-module location. Runtime uses
that documented resolver and canonical `daylily_tapdb.web.runtime.get_db`; no
private context loader, alternate parser or installed-package patch is used.
TapDB 10.1.0 has no `verify_existing` API/CLI option. Dewey implements its own
startup verification method through template reads only; the deployment mode
remains the coordinator's separate configuration contract.

## Initial 10.1.0 execution (preserved evidence)

- `uv lock --python 3.12`: resolved 130 packages, selecting released TapDB 10.1.0
  and Meridian 0.4.8; added declared GUI auth dependencies bcrypt and passlib.
- `uv sync --frozen --python 3.12`: installed all 129 dependencies and local
  Dewey from the one project dependency set in the isolated `.venv`.
- The source inventory exceeded the immutable 10.1.0 receipt bound. The user
  paused execution at 04:23:30Z and separately authorized resumption against
  published 10.1.1rc1. No image, deployment or release occurred during this work.


## Resumed target and final local implementation

At 05:09:54Z the worktree was re-inventoried at base `ca77faeeb82ad4f284114b6d019decacd3dc51b1`;
all partial edits were retained. The explicit coordinator resumption changes only
the TapDB target to `daylily-tapdb[aurora,gui]==10.1.1rc1`. Published PyPI metadata
requires Python >=3.12 and exactly `meridian-euid==0.4.8`; Meridian is unchanged.
The public wheel SHA256 is
`26de691dd5f9c8fac596a18119c9220f4ea78826094753b47f9eb936b0677ce7`.

- Runtime now uses the documented `get_db_config` resolver with explicit absolute
  config and declared client/database identity, plus public pooled `get_db` and
  its scoped sessions. Declared target, domain and owner disagreements fail.
  Native runtime transaction context owns role, tenant/domain/owner checks;
  no replacement config parser or package patch is present.
- `verify_existing` reads required historical templates and validates their DGX
  instance-prefix binding. It never seeds anomalies, creates/updates templates,
  invokes an allocator, prepares principals or migrates schemas. The published
  session API exposes `commit`, without a database read-only flag: safety here
  comes from the SELECT-only application operations, not from assuming rollback
  reverses sequence allocation. Actual PostgreSQL privilege and populated-data
  acceptance remain independent gates.
- Required canonical GUI and DAG v2 mounts fail startup if unavailable. Host
  sessions project stable authenticated subjects; service tokens map to their
  explicit Dewey service principal. Observability publishes the successful
  native manifest. The old DAG v1/external-proxy paths and handwritten graph
  client are removed; `/graph` embeds `/tapdb/graph`.
- Old build/seed/repair/reset/nuke shortcuts, SQL prefix configuration and
  template overwrite are removed. `dewey db verify-templates` is read-only;
  `dewey db lifecycle` gives explicit supported native operator guidance.
  The example config now names a constrained runtime login requiring external
  preparation/binding. No historical data, template pack or identity registry
  was rewritten.
- Managed literature copies propagate download/storage failures, and explicit
  managed requests reject missing storage or full text. They do not become
  external references. The existing explicit `auto` acquisition policy remains:
  it selects a storage type from known source availability before acquisition.
  Unknown search scopes/operators, malformed property filters and sort controls
  fail instead of becoming match-all/default searches, including empty databases.
- Schema drift uses explicit config, strict comparison and command-local JSON;
  malformed, incomplete or inconsistent success receipts fail. The RC supports
  both local and global JSON natively. Shell ownership aliases no longer supply
  runtime scope.
- CI installs the single frozen project dependency set, with no `.[dev]` extra.
  Its healthz/readyz contract tests consume only two checked-in canonical Dayhoff
  schema fixtures, with exact source commit and SHA256 provenance. The false
  `DAYHOFF_PROJECT_ROOT = Dewey checkout` alias is removed.
- The full Dockerfile retains frozen installs, asserts the exact package pair
  and enables the existing container CLI backend. The TapDB 9 overlay Dockerfile,
  its two resolver CI workflows, executable deploy helper and obsolete helper
  tests are removed. Historical receipts remain untouched. Two existing source
  lines in CLI/sharing received Ruff formatting only; behavior is unchanged.
- QEO resolver/auth/package contracts and container entrypoint implementation
  remain intact; QEO CLI service construction now verifies existing templates.

## Verification receipts

Every command below ran only in this isolated worktree. Test commands supplied
`DEWEY_DEPLOYMENT_CODE=d9impl DEPLOYMENT_CODE=d9impl LSMC_DEPLOYMENT_CODE=d9impl`.
No live AWS or production database calls were made.

| Check | Result |
| --- | --- |
| `uv lock --python 3.12` | 130 packages; only TapDB changed from 10.1.0 to 10.1.1rc1 on resumption |
| `uv sync --frozen --python 3.12` | RC and local Dewey installed; exact Meridian 0.4.8 retained |
| `.venv/bin/python -I` metadata/import inspection | Exact RC/0.4.8 pair; TapDB imported from this worktree's non-editable site-packages |
| `uvx --from uv==0.5.30 uv lock --check` | Passed; same uv version as the full image builder understands the frozen lock |
| RC affected-test batch at 05:11:25Z | 103 passed, 1 failed: new graph test expected a redirect while the existing first-party route returns 401 |
| Corrected graph plus changed search/docs tests at 05:12:29Z | 24 passed; graph test now checks the existing 401 boundary and authenticated native graph rendering |
| Strict runtime/drift and helper tests at 05:13:45Z | 26 passed |
| Merged latest outcomes from those three JUnit receipts | 120 distinct tests passed, zero unresolved failures, zero skips in this RC subset |
| `.venv/bin/ruff check dewey_service tests` | Passed |
| `.venv/bin/ruff format --check dewey_service tests` | Passed: 113 files formatted |
| `.venv/bin/bandit -c pyproject.toml -r dewey_service -q` | Passed |
| `git diff --check` | Passed |
| `.venv/bin/python -m build --wheel --outdir /tmp/dewey-rc-wheel` | Passed; ordinary SCM development version 8.0.3.dev20, not a 9.0.0 release |
| Built wheel inspection | Exact RC/0.4.8 requirements; QEO resolver/package modules, container entrypoint and native graph template present; removed seed module absent |

The local development wheel SHA256 is
`9314fcfd5511daced2f2f38abadaa24a0f5233d9214da7bd49a6f24b925055f3`.
It is a packaging validation artifact, not an approved release image.

The first RC pytest batch selected these files with `-o addopts='' -q --tb=short`:
`test_route_surface_coverage`, `test_tapdb_ui_integration`,
`test_cli_auxiliary_unit`, `test_cli_test_unit`, `test_observability_contract`,
`test_service_search`, `test_service_literature`, `test_tapdb_runtime_unit`,
`test_packaging_metadata`, `test_verify_existing`, and `test_docs_smoke`.
The second batch selected the corrected graph test, `test_service_search`, and
`test_docs_smoke`. The third selected `test_tapdb_runtime_unit` and
`test_helper_modules_unit`. Exact per-case latest outcomes and batch counts are
in the adjacent validation JSON.

Earlier 10.1.0 broad testing had three remaining cases: CLI config-path argument
expectation, missing direct route samples, and omitted DAG manifest projection.
Those cases were fixed and passed in the RC subset. Two credentialed browser E2E
cases were skipped in that earlier broad run. Per the user's explicit instruction,
the full suite was not repeated after resumption. Native B qualification receipts
remain separate from this application subset and are not reclassified as Dewey
populated-data acceptance.

## L06/L07 disposition and remaining limits

Local source implementation, negative behavior tests, frozen installation,
lint/security and wheel packaging are complete and reviewable. The root ledger
owner must separately record integration and independent acceptance. Remaining:

1. Actual populated-source capture, restoration, preservation/floor comparison
   and PostgreSQL/Aurora/runtime-principal acceptance using the approved RC.
2. Independent application/auth/concurrency and database-backed GUI/DAG workflow
   acceptance; the local tests use service fakes and native route factories.
3. Full release image build/smoke, remote CI, publication, deployment and real
   authenticated browser acceptance. None was performed by D.
4. A Python 3.12 dependency warning from passlib's use of deprecated `crypt`
   remains visible; no dependency pin was changed to silence it.

The production version remains the coordinator's live-state claim. This commit
must not be treated as a Dewey 9.0.0 release or authorization to cut over.

## Exact changed paths

Relative to base `ca77faeeb82ad4f284114b6d019decacd3dc51b1`:

```text
M	.github/workflows/ci.yml
D	.github/workflows/dewey-qeo-resolver.yml
D	.github/workflows/verify-dewey-qeo-resolver.yml
M	AGENTS.md
M	Dockerfile
M	README.md
M	config/tapdb-config-dewey.yaml
M	dewey_service/app.py
M	dewey_service/cli/__init__.py
M	dewey_service/cli/_service.py
M	dewey_service/cli/common.py
M	dewey_service/cli/db.py
M	dewey_service/cli/qeo.py
M	dewey_service/cli/tapdb.py
D	dewey_service/db_seed.py
M	dewey_service/integrations/tapdb_runtime.py
M	dewey_service/integrations/tapdb_ui.py
M	dewey_service/observability.py
M	dewey_service/schema_drift.py
M	dewey_service/services/base.py
M	dewey_service/services/literature.py
M	dewey_service/services/search.py
M	dewey_service/services/sharing.py
M	dewey_service/settings.py
M	dewey_service/tapdb_backend.py
M	dewey_service/templates/tapdb_graph.html
D	docker/qeo-resolver.Dockerfile
M	docs/apis.md
M	docs/becoming_a_discoverable_service.md
M	docs/gui.md
M	docs/how-tos.md
A	docs/plans/20260911T051420Z_dewey_tapdb101rc1_implementation.md
A	docs/plans/20260911T051420Z_dewey_tapdb101rc1_validation.json
M	pyproject.toml
D	scripts/deploy_qeo_resolver.py
M	tests/conftest.py
A	tests/fixtures/dayhoff_observability/README.md
A	tests/fixtures/dayhoff_observability/healthz.schema.json
A	tests/fixtures/dayhoff_observability/provenance.json
A	tests/fixtures/dayhoff_observability/readyz.schema.json
M	tests/test_cli_auxiliary_unit.py
M	tests/test_cli_registry_v2.py
M	tests/test_cli_server_db_unit.py
M	tests/test_cli_test_unit.py
D	tests/test_db_seed_unit.py
D	tests/test_dewey_resolver_deploy.py
M	tests/test_docs_smoke.py
M	tests/test_helper_modules_unit.py
M	tests/test_observability_contract.py
M	tests/test_packaging_metadata.py
M	tests/test_route_surface_coverage.py
M	tests/test_service_artifacts.py
M	tests/test_service_literature.py
M	tests/test_service_search.py
M	tests/test_settings.py
M	tests/test_tapdb_backend_unit.py
D	tests/test_tapdb_bootstrap.py
M	tests/test_tapdb_runtime_unit.py
M	tests/test_tapdb_ui_integration.py
M	tests/test_ui_chrome.py
A	tests/test_verify_existing.py
M	uv.lock
```
