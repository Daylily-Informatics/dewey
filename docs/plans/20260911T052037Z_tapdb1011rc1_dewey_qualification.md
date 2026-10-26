# Dewey qualification of immutable TapDB 10.1.1rc1

Recorded 2026-09-11 by agent B/E after the user explicitly selected
`daylily-tapdb==10.1.1rc1`. This is an exact prerelease target, not permission to
select stable 10.1.1, a newer package, or modify upstream. The coordinator alone
edits the controlling Dewey ledger. Previous 10.1.0 evidence and its source-size
failure remain preserved in the separate `tapdb101-dewey-qualification-20260911`
worktree.

## Disposition

| Requirement | Evidence and disposition |
|---|---|
| Published immutable RC | Independently downloaded PyPI wheel and sdist match PyPI and GitHub digests; annotated remote tag verified |
| Fixed 128 MiB inventory ceiling | Public validated budgets now exist; selected policy and usage are hash-sealed and checked; complete evidence is still mandatory |
| Read-only native census | Public `db census` exists; release's local 16.13 receipt verified; coordinator reports actual Aurora census succeeded in 1.619 seconds with 25 roles and 153 objects |
| Global drift JSON | Root and command-local `--json` use the correct emitter and exit 0/1/2; eight release cases verified from existing evidence |
| Newly affected historical limit propagation | **1 passed** on exact PostgreSQL 16.13 against the installed public RC, 3.67 seconds, no skips |
| Existing qualification | Reused 123 RC release tests and previous 301 tests; neither suite rerun |
| Actual Dewey capacity and preservation | Coordinator's native source capture succeeded: 79918 rows, 173423825 evidence bytes, 225211759 serialized bytes; later populated-data restoration remains separate |
| Final source exclusion and setup | User-authorized outage plus separately verified database copy can enter native target inventory/migrate/floors/bind without an additional backup artifact; no new release required. See [the source-backed SOP contract](20260911T052037Z_dewey_source_outage_sop_contract.md) |

No AWS, live database, service, schema, role, release tag, or upstream package
was changed by this agent. The only new database work used the existing local
disposable test infrastructure. This document does not close migration or
production acceptance.

## Provenance

| Item | Independently observed |
|---|---|
| Package | `daylily-tapdb==10.1.1rc1` |
| Annotated tag object | `1ac2f09a1787b9e747eda582c45a628ca60b7020` |
| Peeled release commit | `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c` |
| Remote main at inspection | `6f378b8d9387937c7041b9b765b497c24aef8f5e`; RC was not merged to main |
| GitHub release | ID 386795173, published 2026-09-11T04:58:16Z, prerelease true, draft false |
| Wheel | `daylily_tapdb-10.1.1rc1-py3-none-any.whl`, 667238 bytes |
| Wheel SHA-256 | `26de691dd5f9c8fac596a18119c9220f4ea78826094753b47f9eb936b0677ce7` |
| Sdist | `daylily_tapdb-10.1.1rc1.tar.gz`, 1337506 bytes |
| Sdist SHA-256 | `abf2e5b18184db736c8e54fb77cbc96e78c77921f0f65b7c8f026ebb20a8a5fb` |
| Required Python | `>=3.12` |
| Meridian | Exact `0.4.8`, unchanged |
| CLI framework | Exact `cli-core-yo==2.1.1`, unchanged |
| Local interpreter | Python 3.13.13 in a new non-editable `.venv` |

Primary publication sources are [PyPI's exact version metadata](https://pypi.org/pypi/daylily-tapdb/10.1.1rc1/json)
and the [GitHub prerelease](https://github.com/Daylily-Informatics/daylily-tapdb/releases/tag/10.1.1rc1).
The GitHub release's `target_commitish` metadata says `main`; the verified
annotated tag and peeled commit above establish the actual release code.

Own checkout:
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/tapdb1011rc1-dewey-qualification-20260911`,
branch `codex/tapdb1011rc1-dewey-qualification-20260911`, created at the exact
peeled commit. `source ./activate --smoke` prepared the isolated venv without
installing editable TapDB. Installation then used:

```bash
.venv/bin/python -m pip install --isolated --no-cache-dir \
  --index-url https://pypi.org/simple 'daylily-tapdb[aurora,gui]==10.1.1rc1'
```

`pip check`, native `tapdb --json version`, imports, census help, identity help,
and config-update help passed. Import provenance points into this new venv's
`site-packages`, with no editable `direct_url`. `[aurora,gui]` still supplies the
operator/service dependencies; CLI is core. Only `pytest==9.1.1` was additionally
installed for the single local qualification case.

## Public configuration and safe source capture

`db-config update` adds these root `inventory_limits` fields. Native config
init remains the supported way to prepare a canonical admin/backup structure;
update still refuses an old file without its required admin mapping. The
coordinator's existing protected `source-operator.yaml` was already created
through native init.

| CLI option | Root field | Default |
|---|---|---:|
| `--inventory-max-rows` | `inventory_limits.max_rows` | 250000 |
| `--inventory-max-row-bytes` | `inventory_limits.max_row_bytes` | 8388608 |
| `--inventory-max-receipt-bytes` | `inventory_limits.max_receipt_bytes` | 134217728 |

Each value must be an integer from 1 through 9223372036854775807. Unknown fields,
booleans, strings, zero and overflow are rejected. Config options are at
`daylily_tapdb/cli/__init__.py:1422`; parsing is at
`daylily_tapdb/identity_inventory.py:89` and `cli/db_config.py:414`.

The coordinator selected this bounded policy for the new actual-source run:

```bash
tapdb --config /home/ubuntu/dewey_ops/tapdb101-20260911/source-operator.yaml \
  db-config update \
  --inventory-max-rows 1000000 \
  --inventory-max-row-bytes 8388608 \
  --inventory-max-receipt-bytes 536870912
```

These are 1 million rows, 8 MiB per raw source row, and 512 MiB of accumulated
row evidence. They are a selected policy, not a measured capacity requirement
or a process-memory limit. Complete evidence remains in memory. Hashing and
receipt-file output now stream to avoid extra complete JSON copies. The
command above supplies only inventory options; it does not print credentials.
Do not use general config-display output as a secrets-masking mechanism.

Use the exact RC executable from its isolated operator environment. Keep the
receipt and stdout/stderr files in an explicitly selected mode-0700 directory,
with new paths and shell tracing disabled. Native receipt files are immutable
mode 0444; privacy therefore relies on that protected parent directory.

```bash
umask 077
: "${DEWEY_PRIVATE_EVIDENCE_DIR:?Explicit existing private evidence directory}"
tapdb --config /home/ubuntu/dewey_ops/tapdb101-20260911/source-operator.yaml \
  --json db identity inventory --source-version 9.0.9 \
  --receipt "$DEWEY_PRIVATE_EVIDENCE_DIR/source-contract-rc1.json" \
  > "$DEWEY_PRIVATE_EVIDENCE_DIR/source-contract-rc1.stdout.json" \
  2> "$DEWEY_PRIVATE_EVIDENCE_DIR/source-contract-rc1.stderr.log"
```

Use new filenames for a subsequent reviewed invocation; never overwrite prior
evidence. Add `--sequence-mappings` only with the complete verified mapping
file, and the unchanged recovery-family options when that stage requires them.
An initial all-generator inventory can retain explicitly unmapped generators;
it does not authorize backup, advancement or migration with unresolved mappings.

A failure still publishes no successful partial receipt. Limit failures now
emit `identity_inventory_limit` with sanitized phase, table, processed rows,
accumulated/attempted bytes, limit name, configured value and attempted value
(`identity_inventory.py:122`, `cli/identity.py:75`). Diagnostics do not disclose
source row contents. Changing a policy requires native config update and a new
capture; never edit a sealed receipt.

## Census, destination and control identity

The source is always included. `--database` is repeatable and names exact
additional databases on the same configured server:

```bash
: "${DEWEY_CONTROL_DATABASE:?Explicitly select the control database; do not infer one}"
tapdb --config /home/ubuntu/dewey_ops/tapdb101-20260911/source-operator.yaml \
  --json db census \
  --database dewey_prod_tapdb10 --database "$DEWEY_CONTROL_DATABASE" \
  --statement-timeout-ms 10000 --max-catalog-rows 100000 \
  --receipt "$DEWEY_PRIVATE_EVIDENCE_DIR/principal-census-rc1.json" \
  > "$DEWEY_PRIVATE_EVIDENCE_DIR/principal-census-rc1.stdout.json" \
  2> "$DEWEY_PRIVATE_EVIDENCE_DIR/principal-census-rc1.stderr.log"
```

No existing control database is invented here. Later fencing requires a
different explicitly configured existing database on the identical transport,
with its own successful operator connection and exact provider identity.
Catalog existence is not successful authentication to that database.

`--database` also scopes session metadata. The command above includes source,
destination and control activity. There is no separate source-only activity
selector. Omitting all `--database` options captures only source activity and
source database existence; it cannot establish target/control existence.

Census authenticates the configured operator and physical source, uses
REPEATABLE READ/READ ONLY, and captures roles, memberships, direct IAM-role
memberships, database/schema/object owners and ACLs, column/default ACLs,
effective CONNECT/CREATE/TEMP and schema privileges, available runtime scope
bindings and named-database session metadata. It omits passwords and query
text. Named absence comes from authenticated `pg_database`, never a failed
connection (`principal_census.py:44`).

The 10000 ms statement and lock timeout applies after initial operator
authentication; it is not a connection or whole-operation deadline. Catalog
rows are limited per section, with overflow failing rather than truncating.
Both census numeric options accept 1 through 2147483646. Missing historical
scope tables/columns, filtered access and partial activity visibility are
explicitly marked. IAM database memberships do not certify external AWS IAM
policies or credential provenance. Census neither fences writers nor discovers
all HTTP clients, workers, schedulers or disconnected pools.

## Sealing and later policy retention

For an explicitly selected policy, identity receipts include hash-bound
`limits` and `usage`: total rows, cumulative evidence bytes and largest raw
source row. The resource policy is separate from physical database identity.
Verification checks receipt hashes, equal policies, recomputed evidence/row
usage and bounds (`identity_inventory.py:806`). Legacy v1 receipts without
policy metadata keep their original default shape; this is the released
contract, not a service-added adapter.

| Later stage | Public implementation reference |
|---|---|
| Source-contract capture | `backup/source_contract.py:26`; identity then sequence capture, both sealed into the envelope |
| Live identity comparison | `cli/identity.py:231`; retains reviewed receipt policy |
| Historical backup plan/create | `backup/service.py:477`; applies reviewed policy and rejects explicit conflicts |
| Restored identity comparison | `backup/postrestore.py:655`; adopts reviewed identity policy |
| Migration preflight/apply | `migration_identity.py:511` and line 1173 |
| Postcommit migration comparison | `migration_identity.py:1364` |
| Fenced-source recovery recapture | `backup/verify.py:1374` |
| Actual stalled-fence takeover | `sequence_fence.py:769`, line 894 and line 1021; policy is bound into the reviewed takeover plan |

`with_inventory_limits` rejects a conflicting explicit destination policy;
it does not silently change the reviewed resource budget. Receipt publication
remains atomic, refuses overwrite, and flushes/fsyncs before immutable linking
(`migration_identity.py:1450`). Hash sealing provides integrity evidence; it is
not a claim of a separate cryptographic signer.

## Qualification evidence

The [evidence summary](20260911T051700Z_tapdb1011rc1_evidence/qualification-summary.json)
links hashes and counts for all retained artifacts. Publication and installed
metadata are retained alongside it.

The release's existing XML verifies **123 passed**, zero errors/failures/skips,
3.368 seconds: 13 limits, 4 census, 8 drift JSON, 29 identity, 15 identity CLI,
19 source-contract, 34 migration-contract, and one affected CLI branch test.
Its complete synthetic capture exceeds the old 128 MiB ceiling and roundtrips
serialization. Its actual existing local 16.13 census reports READ ONLY,
source presence, two named absences, 16 roles and 173 objects. These are reused
release observations, not newly executed tests.

The one new [qualification test](20260911T051700Z_tapdb1011rc1_evidence/test_rc1_native_limits.py)
uses the exact release's unchanged `released_source[9.0.9]` fixture and
historical roundtrip test. It sets the policy through native config init/update
and asserts its presence in the complete source contract. The existing native
test then completes full backup, isolated restore requiring rebinding, fenced
migration, postcommit verification, every original cell hash and no pending
recovery. Policy comparisons reject mismatches at these newly changed stages.

The first attempt stopped before historical setup because the old fixture
lacked admin config. That [failure](20260911T051700Z_tapdb1011rc1_evidence/native-limits-roundtrip-fixture-failure.log)
is retained. Explicit native init prepared the fixture, and only the same
unexecuted case was retried: [1 passed](20260911T051700Z_tapdb1011rc1_evidence/native-limits-roundtrip.log),
3.67 seconds, two existing deprecation warnings. Exact PostgreSQL 16.13 was
required; the disposable fixture used port 15449 and completed teardown.

The harness copied only the exact release's tests/schema/config; no TapDB/admin
package was present. It ran from that harness using the new venv's
`python -I -m pytest tests/test_rc1_native_limits.py --tapdb-test-pg-port 15449`
with `TAPDB_TEST_EXPECTED_PG_VERSION=16.13` and the existing exact 16.13 binary
directory on PATH. The test runner needed no new migration engine or SQL in
the added qualification file. Its subsequent edits were import formatting and
a scoped pytest-fixture lint annotation only. Ruff and diff checks passed.

Actual source census/inventory receipts remain protected on EC2 and belong to
the coordinator. They are not copied into this repository. No full-suite CI,
production backup/restore, outage, fencing or deployment is claimed here.

## Actual-size reader and recovery review

The coordinator's sanitized source index reports a successful exact RC capture:
79918 rows, 173423825 accumulated evidence bytes, largest raw row 1706924 bytes,
and complete serialized file size 225211759 bytes. File SHA-256 is
`45776ac58ee2e9889a5590490a8a75d59c9745bca5dcc40ca982f0d75364a937`.
The native identity hash is
`4a4d2df17d60f3caacd0b6decd3cee8ebc6263a9ad46b8908fb168b79cd2164f`.
This is discovery evidence, not a writer-fenced final source contract.

Source inspection found no separate fixed 128 MiB file-reader ceiling in the
identity, backup, restore, migration, family, floors or reconcile path. CLI
readers use complete JSON loading (`cli/identity.py:30`, `cli/backup.py:49`,
`cli/db.py:1530`); postrestore checks download/hash the separate identity asset
and load it (`backup/verify.py:2234`); migration receipt loading is complete
(`migration_identity.py:1501`). Verification uses the sealed policy above,
not the formatted JSON file size (`identity_inventory.py:806`). The family and
allocator journals retain sequence inventories/floors; they impose no second
identity receipt-size cap (`backup/recovery.py:180`).

These full-object readers still require sufficient process memory and staging
space. The 512 MiB evidence policy is not a memory cap or final-file bound.
Actual full-volume native migration/verification resource usage is a bounded
acceptance item. No broad test rerun or synthetic duplicate of the existing
large-limit release test was performed. The user subsequently stopped all
additional backup preparation; existing Aurora protection is retained. The
database-copy/native-family entry, repair-forward recovery and immutable final
runtime config-path binding are described in the SOP contract; none requires
another release or shortened recovery evidence. Prior backup/restore source
review and the completed local historical test remain evidence only.
