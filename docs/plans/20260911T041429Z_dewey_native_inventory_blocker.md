# Actual Dewey inventory blocks the fixed TapDB 10.1.0 migration

Recorded 2026-09-11T04:14:29Z. Controlling rows L02/L03 and all dependent migration,
acceptance and release gates remain blocked. Production is unchanged.

## Observed result

The isolated public TapDB 10.1.0 installation reached the existing Aurora
`dewey_prod` through its explicitly configured `dayhoff` operator. Its supported
read-only historical inventory command returned:

```json
{
  "error": {
    "code": "identity_inventory_error",
    "details": null,
    "message": "Identity receipt exceeds the declared size bound"
  }
}
```

The command ran once. No inventory retry, partial inventory, package patch,
database mutation, writer fence, restoration, source switch or release followed.
The requested receipt file does not exist. The original failure is retained at
`/home/ubuntu/dewey_ops/tapdb101-20260911/logs/source-inventory.log` on the approved
EC2 host, with a byte-for-byte copy in
[source-inventory-error.json](evidence/20260911_dewey_native_inventory/source-inventory-error.json).

Exact native invocation from the interactive SSM `ubuntu` session, in the
persistent `dewey-tapdb101-operator-20260911` tmux session:

```bash
sudo env AWS_PROFILE=lsmc AWS_REGION=us-west-2 \
  AWS_CONFIG_FILE=/home/ubuntu/.aws/config \
  AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
  PYTHONDONTWRITEBYTECODE=1 \
  /home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/tapdb \
  --config /home/ubuntu/dewey_ops/tapdb101-20260911/source-operator.yaml \
  --json db identity inventory --source-version 9.0.9 \
  --receipt /home/ubuntu/dewey_ops/tapdb101-20260911/receipts/source-discovery.json \
  > /home/ubuntu/dewey_ops/tapdb101-20260911/logs/source-inventory.log 2>&1
```

## Exact immutable limitation

The installed release is the approved public wheel with SHA-256
`f46cb2abfccb3000b9f9443ea00045e83fb96f6b320d2aeac0ad800ea47e8801`, matching annotated
tag `10.1.0` and commit `9db1abb4525f2594ebdbf2a307eb8b49aa51883d`.

[`identity_inventory.py:24`](https://github.com/Daylily-Informatics/daylily-tapdb/blob/10.1.0/daylily_tapdb/identity_inventory.py#L24)
sets `MAX_RECEIPT_BYTES = 128 * 1024 * 1024` (134,217,728 bytes). The counter at
lines 436–439 accumulates each distinct row's canonical evidence and key across
every physical table. Actual Dewey capture exceeds that evidence-size bound.
This is not a measurement of database size or a claim about the number of rows.
The separately enforced 250,000-row and 8 MiB individual-row limits produce a
different error; neither is the observed failure.

There is no supported CLI, configuration, environment or public capture-API
parameter for increasing the full identity receipt bound. Agent B independently
confirmed this against the installed package and tagged source, without changing
either or rerunning the existing qualification suite.

`capture_source_contract` captures identity evidence before sequence evidence.
Consequently this failure precedes allocator inventory, source sealing, recovery
family generation and receipt publication. A usable historical source contract
was not produced. Full historical backup, migration preflight and restored-data
comparison reuse the same bounded capture. Changing the output path, omitting
`--source-version`, or attempting backup does not remove the limitation.

## Baseline and preparation completed

| Item | Evidence |
|---|---|
| Live application | Dewey 8.0.2, TapDB 9.0.9, Meridian 0.4.7; freshly read installed distribution metadata |
| Container | `872434f0530335fd5a985a920f498fe39a36fd5eab40b9cb3934b185ceddeb36` |
| Live image | `sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f` |
| Image source | `556dfcf936ea11e25f6126931fe1f655482d00a6`; refreshed image labels and writable-layer inspection preserve the prior 73-file parity proof |
| Configured source | `dewey_prod`, schema `tapdb_dewey_lsmcok1_local`, domain `M` |
| Aurora | `dayhoff-lsmcok1-tapdb`, resource `cluster-AA24MJP2WJNSFOFGXGHAXWHVKU`, available Aurora PostgreSQL 16.13, encrypted, deletion protected, 14-day retention |
| Operator installation | Separate `/home/ubuntu/dewey_ops/tapdb101-20260911/venv`; TapDB 10.1.0, Meridian 0.4.8, package hash and `pip check` verified |
| Operator config | Native `db-config init` generated a separate complete config from explicit source identity, registry/TLS paths and protected credential references; original config unchanged |
| Local native qualification | 301 passed, zero failures/errors/skips, exact PostgreSQL 16.13; existing receipts reused |

The EC2 host initially lacked `ensurepip`; an apt simulation exposed unrelated
kernel-package dependency failures. No OS package repair was performed. The
same isolated Python 3.12 environment was bootstrapped with the SHA-verified
PyPI pip 25.1.1 wheel and then the approved TapDB wheel. Failed setup files and
logs were retained. A guessed `--version` probe was corrected to the supported
CLI surface; it was an operator-helper defect, not a TapDB migration failure.

An attempted native `db-config update` of a protected old-format copy failed
because the historical config lacks `root.admin`. Native `db-config init` was
then qualified as a config-only operation and used successfully for the
separate operator file. No missing sections were hand-filled and no source
password was copied or exposed. That inventory-only configuration is not
approved for runtime binding or future runtime authentication.

## Disposition and unblock condition

The fixed 10.1.0 migration cannot proceed under the approved requirements.
Its passing small-fixture tests do not establish capacity for actual Dewey.
L02 is **BLOCKED**, not `FAIL`: the immutable package must not be modified for a
bugfix attempt. Dependent gates retain this root cause. No claimed allocator
floors, restoration proof or production acceptance can be fabricated from the
failed capture.

Unblocking requires an explicit user amendment to the exact-version/released-tool
constraint and a released, qualified full-inventory capability that supports
the complete actual Dewey dataset. A constant patch, partial inventory, omitted
tables or automatic upgrade is not authorized. This document does not choose a
replacement release or initiate upstream changes.

A separate Gate 0 gap also remains: 10.1.0 has no complete public principal and
writer census command. Its service-readiness contract assigns that evidence to
the owning system. The Dewey AGENTS no-circumvention rule requires explicit
permission before a separate catalog-inspection path. That proposal is paused
because it cannot solve the inventory-size blocker.

Current implementation work is limited to reviewable local adoption and
migration-preparation artifacts. Source data, EUID/prefix bindings, sequence
values, running application, sibling services and deployment configuration have
not been changed. Phase 2 has not begun.
