# TapDB 10.1.0 published-package qualification for Dewey

Recorded 2026-09-11T03:57:03Z by agent B. The controlling Dewey ledger remains
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-tapdb10-major-20260910/docs/plans/20260910T185538Z_dewey_tapdb10_major_ledger.md`;
its coordinator is the sole writer. This file records local evidence, not a new
release decision or a substitute for actual Dewey acceptance.

## Result and boundary

**PASS:** 301 focused tests, zero failures/errors/skips, 20.00 seconds on exact
community PostgreSQL 16.13. The subject was the freshly installed published
10.1.0 wheel. No TapDB implementation, package metadata, version, release tag,
or existing test changed. No AWS, production database, or live service command
was executed by this agent. No full release CI or waived upstream gate was rerun.

| Item | Observed evidence |
|---|---|
| Source tag | Annotated `10.1.0`, peeled `9db1abb4525f2594ebdbf2a307eb8b49aa51883d` |
| Worktree branch | `codex/tapdb101-dewey-qualification-20260911`, initially clean at the exact tag |
| Public package | `daylily-tapdb==10.1.0`, fresh download and non-editable install |
| Wheel SHA-256 | `f46cb2abfccb3000b9f9443ea00045e83fb96f6b320d2aeac0ad800ea47e8801` |
| Python | 3.13.13, isolated `.venv` |
| Pinned dependency | `meridian-euid==0.4.8` |
| Dependency validation | `python -m pip check`: no broken requirements |
| Native server | Existing source build `runtime/postgres-16.13/bin/postgres` in the separate TapDB service-readiness worktree; reports 16.13 |
| Test instance | Fresh disposable fixture on localhost port 15449, exact version required with `TAPDB_TEST_EXPECTED_PG_VERSION=16.13`; fixture teardown completed |

The unchanged tag's `tests`, `schema`, and `config` directories were copied to
ignored `runtime/qualification/published-harness/`. That harness contains no
`daylily_tapdb` or `admin` Python package. The installed interpreter ran
`python -I -m pytest` there, excluding the source working directory from Python's
initial import path. Package provenance independently confirms the import from
`.venv/lib/python3.13/site-packages/daylily_tapdb`, version 10.1.0, and no editable
distribution URL.

## Retained evidence

- [Package provenance](20260911T035703Z_tapdb101_dewey_qualification_evidence/package-provenance.json)
- [Machine-readable test totals](20260911T035703Z_tapdb101_dewey_qualification_evidence/test-summary.json)
- [Complete pytest output](20260911T035703Z_tapdb101_dewey_qualification_evidence/published-pg1613.log)
- [JUnit test cases](20260911T035703Z_tapdb101_dewey_qualification_evidence/published-pg1613.xml)

| Unchanged release tests | Passed |
|---|---:|
| `test_identity_inventory_pg.py` | 10 |
| `test_identity_inventory_cli.py` | 15 |
| `test_sequence_protection.py` | 54 |
| `test_sequence_protection_pg.py` | 23 |
| `test_sequence_protection_restart_pg.py` | 10 |
| `test_sequence_protection_cli.py` | 28 |
| `test_runtime_principal_pg.py` | 38 |
| `test_runtime_principal.py` | 96 |
| `test_backup_source_contract.py` | 19 |
| `test_recovery_floor_pg.py` | 5 |
| Frozen 9.0.9 digest, restore/migration, and failed-migration cases | 3 |
| **Total** | **301** |

The historical cases are exactly:

1. `test_frozen_9_0_9_assets_match_their_exact_release_digests`
2. `test_released_restore_and_separate_migration_preserve_all_original_rows[9.0.9]`
3. `test_failed_migration_retains_consumed_values_after_actual_rollback[9.0.9]`

The fixture uses frozen 9.0.9 commit
`52d5f498dc4751b7e42d346bee2811a14080e5a5` and verifies original SQL asset hashes.
It populates objects, soft-deleted history, lineage and duplicate extension rows,
and intentionally retains differing stored object prefixes and template prefix
bindings. It exercises full historical backup, isolated restore requiring
principal binding, separate migration and rollback allocation retention. This
is synthetic native qualification; actual Dewey data and DGX bindings still
require their own preservation evidence.

Exact test selection, run from the copied `published-harness` with the existing
16.13 `bin` and this worktree's `.venv/bin` first in `PATH`:

```bash
TAPDB_TEST_EXPECTED_PG_VERSION=16.13 python -I -m pytest \
  tests/test_identity_inventory_pg.py \
  tests/test_identity_inventory_cli.py \
  tests/test_sequence_protection.py \
  tests/test_sequence_protection_pg.py \
  tests/test_sequence_protection_restart_pg.py \
  tests/test_sequence_protection_cli.py \
  tests/test_runtime_principal_pg.py \
  tests/test_runtime_principal.py \
  tests/test_backup_source_contract.py \
  tests/test_recovery_floor_pg.py \
  'tests/test_backup_historical_pg.py::test_frozen_9_0_9_assets_match_their_exact_release_digests' \
  'tests/test_backup_historical_pg.py::test_released_restore_and_separate_migration_preserve_all_original_rows[9.0.9]' \
  'tests/test_backup_historical_pg.py::test_failed_migration_retains_consumed_values_after_actual_rollback[9.0.9]' \
  --tapdb-test-pg-port 15449 -q --tb=short \
  --junitxml=/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/tapdb101-dewey-qualification-20260911/runtime/qualification/published-pg1613.xml
```

The allocator selection covers called/uncalled positions, nonunit increments,
strict-next floors, caches and stale sessions, missing/unknown mappings,
exhaustion and invalid definitions, stale receipts, transaction rollback,
strong fencing, process-loss recovery and durable retained floors. Principal
tests cover CONNECT-only bootstrap, forced-RLS preservation, exact-role and
scope checks, receipt-bound TEMP revocation, fresh-session temporary-object
denial, preserved operator TEMP and refusal to cascade dependent grants.

## Operator installation and source configuration

`[aurora,gui]` is sufficient on the operator host: CLI and its framework are
core dependencies. The `dev` extra was installed only in the local test venv.
Keep the 10.1.0 operator venv separate from the running 9.0.9 service/container.

The following commands require explicitly chosen new absolute paths in
`DEWEY_OPERATOR_ENV` and `DEWEY_PACKAGE_DIR`. Run as the existing authorized
`ubuntu` operator, with no shell tracing. The host has `/usr/bin/python3.12`.

```bash
(
set -eu
: "${DEWEY_OPERATOR_ENV:?Set the explicit new absolute operator venv path}"
: "${DEWEY_PACKAGE_DIR:?Set the explicit new absolute package directory}"
case "$DEWEY_OPERATOR_ENV" in /*) ;; *) exit 2 ;; esac
case "$DEWEY_PACKAGE_DIR" in /*) ;; *) exit 2 ;; esac
umask 077
test ! -e "$DEWEY_OPERATOR_ENV"
test ! -e "$DEWEY_PACKAGE_DIR"
/usr/bin/python3.12 -m venv "$DEWEY_OPERATOR_ENV"
mkdir "$DEWEY_PACKAGE_DIR"
"$DEWEY_OPERATOR_ENV/bin/python" -m pip download --no-cache-dir --no-deps \
  --only-binary=:all: 'daylily-tapdb==10.1.0' --dest "$DEWEY_PACKAGE_DIR"
"$DEWEY_OPERATOR_ENV/bin/python" -I - "$DEWEY_PACKAGE_DIR/daylily_tapdb-10.1.0-py3-none-any.whl" <<'PY'
import hashlib
import pathlib
import sys
assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest() == (
    "f46cb2abfccb3000b9f9443ea00045e83fb96f6b320d2aeac0ad800ea47e8801"
)
PY
"$DEWEY_OPERATOR_ENV/bin/python" -m pip install --no-cache-dir \
  "$DEWEY_PACKAGE_DIR/daylily_tapdb-10.1.0-py3-none-any.whl[aurora,gui]"
"$DEWEY_OPERATOR_ENV/bin/python" -m pip check
"$DEWEY_OPERATOR_ENV/bin/tapdb" version
)
```

The live v4 format remains supported. An inventory operator config needs its
explicit database/schema/domain/owner, existing governance-registry paths,
Aurora host/region/cluster/TLS/auth fields, and a distinct `target.operator`.
The declared runtime and operator user names must differ. The coordinator
selected the future runtime identity `dewey_runtime_9`; the authenticated
source operator remains `dayhoff` through its existing secret ARN.

After making a protected source-config copy, use the installed public group
`db-config`, not `config`:

```bash
"$DEWEY_OPERATOR_ENV/bin/tapdb" --config "$DEWEY_SOURCE_OPERATOR_CONFIG" \
  db-config update \
  --user dewey_runtime_9 \
  --operator-user dayhoff \
  --operator-secret-arn "$DEWEY_SOURCE_SECRET_ARN" \
  --no-operator-iam-auth \
  --tenant-id '' \
  --no-allow-global-claims
```

Read only the existing secret ARN from the protected config without printing
it. Do not retrieve or place its password in shell commands, logs, Git or
messages. Keep the copy mode 0600. No runtime credentials are resolved during
this offline update or during operator-only inventory. The empty/false tenant
and global settings explicitly constrain an unused future runtime identity in
this inventory-only copy; they do not filter operator capture and do not decide
the eventual Dewey runtime scope. The runtime role need not exist for capture.
Do not bootstrap or bind on the historical source just to take inventory.

The update requires the existing v4 admin subsections. Missing sections are a
reported config-contract failure, not permission to fill them by hand.

**Output limitation:** `db-config update` prints each supplied target update
value without generic credential masking (`cli/__init__.py:1987–1994`). Do not
pass target password or secret-value flags. The operator fields above are
stored separately and are not printed; the target updates print only the benign
user and empty tenant. Do not run `config show` on the protected file.

## Source inventory and complete allocator mapping

Installed help verifies this exact public invocation:

```bash
"$DEWEY_OPERATOR_ENV/bin/tapdb" --config "$DEWEY_SOURCE_OPERATOR_CONFIG" --json \
  db identity inventory --source-version 9.0.9 \
  --receipt "$DEWEY_INITIAL_SOURCE_RECEIPT"
```

The receipt path must be a new absolute file. This non-family capture enumerates
every physical table and sequence. It executes through a read-only repeatable
read operator transaction, without ORM/schema initialization or allocation
(`cli/identity.py:156–172`, `runtime_principal.py:274–295`).

Inspect every `.sequence_inventory.sequences[]`, including name, owner,
dependencies, mapping, last value, called state, start/increment/bounds/cache,
assigned floor and allocated floor. Do not assume the previous count of 20 is
the complete current set. Check `.missing_generators` too. Unknown mappings are
retained as `mapping.kind = "unmapped"` in this initial discovery receipt;
their presence blocks validated backup/advance/floor operations. Successful
discovery is not a validated migration-source contract.

Native mapping evidence is owned-column dependencies, stored prefix bindings,
versioned catalog annotations, or explicit verified source declarations
(`sequences.py:138–376`). Unreferenced historical declarations can be supplied
as a JSON object with one exact entry per verified sequence:

```text
sequence_name -> {"kind": "prefix", "prefix": exact_source_prefix,
                  "evidence": source_hash_statement_and_verified_catalog_evidence}
```

Only `kind`, `prefix`, and nonempty `evidence` are accepted for such an entry.
Matching a generator name alone is not evidence. The original 9.0.9 schema
(`tests/test_backup_historical_assets.py:7–36`) explicitly declares:

| Generator | Original documented prefix |
|---|---|
| `wx_instance_seq` | WX |
| `wsx_instance_seq` | WSX |
| `xx_instance_seq` | XX |
| `ay_instance_seq` | AY |
| `msg_instance_seq` | MSG |

Its schema SHA-256 is
`64362e2882a7b424f6bf3c6b3d9c21d1e859ec98d4ee61ca2a728cecfd134584`.
Those exact bare CREATE statements define start/min/increment/cache 1,
max 9223372036854775807 and cycle false. Compare the public source receipt's
catalog fields to this source before declaring mappings; preserve each exact
statement and evidence. Existing test evidence producer
`tests/test_identity_inventory_helpers.py` demonstrates this verification.
It is test infrastructure, not a reason to execute private SQL on production.
Additional service-specific or persisted bindings require their owning source.

Then recapture to another new receipt with
`--sequence-mappings "$DEWEY_VERIFIED_SEQUENCE_MAPPINGS"`. A recovery-family
capture also requires the explicit UUID, all existing source/replacement
journal roots and a distinct new family receipt. Every generated contract,
family and journal anchor remains immutable. Native validation rejects missing
generators, unknown mappings and unsafe floors; do not edit sealed receipts.

## Ledger implications and remaining evidence

| Dewey row | Evidence supplied here | Still required by its owner |
|---|---|---|
| L02 | Published CLI, historical9.0.9 fixture, complete physical capture contract and operator invocation | Current Dewey source receipt and verified complete mappings |
| L04 | Strict advancement/fencing/recovery and bootstrap/bind/TEMP qualification on16.13 | Actual source/replacement roles, scope, controls, journal family and independent service acceptance |
| L05 | Public wheel provenance and frozen9.0.9 historical restore/migration tests | Populated Dewey restoration/migration on matching deployment infrastructure, conversion manifest and timed recovery |

These local prerequisites pass. L02/L04/L05 must not be marked wholly complete
from this fixture alone. The agent will not author Dewey migration tooling and
remains available for separately assigned independent acceptance of actual
source/target receipts and Dewey behavior. All source-code files remain equal
to approved tag10.1.0.

## Additional Gate 0 census boundary

Installed public `db`, `pg`, `validation`, `schema`, `identity`, `sequences`
and `runtime-principal` help and their owning implementations were inspected.
There is no public read-only command producing a complete historical principal
and writer census: all login attributes, memberships, database/schema/object
ownership and ACLs, effective TEMP, runtime scopes, IAM mapping and current
writers. `docs/service-readiness.md:33` explicitly assigns principal-state
capture to the owning system.

The offline bootstrap plan has no observed principal state. A bind plan reads
selected principal and privilege state but requires an existing constrained
runtime role and canonical current schema; it cannot substitute for a 9.0.9
source census. The internal `sequence_fence.role_catalog` and fence-census
helpers are not public operator census commands. They were not called.

`db identity inventory` against an explicit existing control target can return
the authenticated physical database identity. A failed connection cannot prove
database absence. Do not use `db schema status` as authoritative absence proof:
its internal `_check_db_exists` uses the runtime role and literal maintenance
database `postgres`, and collapses query failure to false
(`cli/db.py:775–790`, `cli/db.py:1221–1237`).

After a verified backup exists, public `backup restore-plan --mode isolated
--target-database EXACT --target-schema EXACT` inspects the explicit destination
without performing restoration. Its `target.empty` check distinguishes a new
database (`will be created from template0`) from an existing empty schema target
and an occupied target (`backup/verify.py:655–719`). Its owning existence probe
authenticates as the configured operator against the explicit configured
database and raises on query failure (`backup/verify.py:1635–1658`). This is a
later receipt-bound restore-plan check, not a standalone Gate 0 census command.

Therefore complete Gate 0 principal/writer census and preliminary destination
absence are not established by this qualification. The coordinator needs an
authorized owning-system evidence source or a scope decision. No raw SQL,
private API, bootstrap, fence, package patch or version change was used to work
around the missing public census surface.
