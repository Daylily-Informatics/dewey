# Dewey copy and native migration conversion manifests

**Status:** The same-target native migration manifest is prepared with no
permission to change any original cell. The copy and final source-to-target
manifests require only the actual copied inventory's `target` binding. Native
execution and independent E acceptance remain outstanding; this is C's author
review. No application conversion, database operation, or backup was performed.

| Artifact | Use |
|---|---|
| [Copy conversion policy](evidence/20260911T055609Z_dewey_copy_conversion_policy.json) | Bind its `target` from the actual untouched-copy receipt before source-to-copy verification |
| [Native migration manifest](evidence/20260911T055609Z_dewey_native_migration_manifest.json) | Ready for copied-before to migrated-after verification on the same exact target; no target substitution permitted |
| [Source and migration asset review](evidence/20260911T055609Z_dewey_migration_asset_review.json) | Original receipt references, exact tagged SQL/include hashes, five source migration hash pairs, eight pending filenames, and data preconditions |

Native migration manifest SHA256:
`af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8`.
Copy policy SHA256:
`6885079d900c747f68e19cc4c2d0b1fc1bff6d49ad9b00478e1f4991df8bf870`.

## Source-backed scope

The successful mapped native capture ended at `2026-09-11T05:48:23.633925Z`
with exit 0. Original identity content remains unchanged from the earlier
capture. The coordinator's existing protected receipt and its sanitized
`mapped-source-summary.json` supplied these facts; no additional database read
was needed by this author.

| Evidence | Value |
|---|---|
| Native source contract SHA256 | `b4fa8198d2c8082e551011f227497b4d17b379d79d4350ff15635e1c9a9f6e75` |
| Source identity inventory SHA256 | `4a4d2df17d60f3caacd0b6decd3cee8ebc6263a9ad46b8908fb168b79cd2164f` |
| Native source file SHA256 | `c8d8d02e4ee93a6e615b960a20fa761e0456ba2a4d2a6318107f1441583b79f3` |
| Source contract path | `/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/source-mapped-inventory-10.1.1rc1.json` |
| `audit_log.changed_by` | Present; zero stored column hashes for NULL or empty string |
| `generic_template.validator_ref` | Present; zero stored column hashes for NULL or empty string |
| Native `outbox_event` | Zero rows, existing `message_uid`, no legacy `event_id` column |
| Existing scoped rows | Every observed `tenant_id` is NULL; preserve it |
| Existing instances | All 12,204 `machine_uuid` values are NULL; preserve them |

The five applied migration names were recovered by exact one-to-one comparison
against the tagged candidate filenames, using both native
`SHA256(canonical_json([filename]))` row keys and
`SHA256(canonical_json(filename))` column hashes. Every original row matched
exactly once; each has count 1. Both observed hashes are retained in the asset
review. No filename or applied record was manufactured.

1. `20260303_120000_add_tenant_id.sql`
2. `20260303_120010_add_outbox_event.sql`
3. `20260405_120000_add_domain_scoping.sql`
4. `20260612_154200_add_template_validator_ref.sql`
5. `20260612_154210_instance_prefix_from_template.sql`

The native preflight must therefore report exactly these eight pending assets
from immutable `10.1.1rc1`, commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`:

| Pending migration | Intended effect relevant to the manifest |
|---|---|
| `20260902_010000_natural_identity_and_owner_uniqueness.sql` | Add nullable `generic_instance.identity_key`; native natural-identity indexes/constraints and owner-aware template uniqueness |
| `20260902_010100_legacy_outbox_message_conversion.sql` | Add the native mapping table and outbox constraints; the observed source has no legacy `event_id`, so no source-row conversion or new message instance is permitted |
| `20260902_020000_force_rls_and_audit_attribution.sql` | Add runtime-principal scope table and install native RLS/audit functions/policies; original audit cell values remain frozen by this manifest |
| `20260903_031820_runtime_ddl_guard.sql` | Revoke runtime/PUBLIC schema CREATE through native privilege preparation |
| `20260904_061819_tenant_scoped_natural_identity.sql` | Native natural-identity index/constraint changes and lineage scope function; no tenant or relationship rewrite |
| `20260910_203200_aurora_operator_principals.sql` | Exact native Aurora operator policies and shared RLS asset |
| `20260910_220000_sequence_prefix_bindings.sql` | Add source-backed catalog annotations to existing optional generators; no generator creation or counter reset |
| `20260910_233000_pin_managed_allocator_resolution.sql` | Native allocator function replacements with managed-schema resolution; no source cell conversion |

The asset review records each unexpanded SQL asset and included asset SHA256.
Native preflight hashes the expanded source; retain that owning preflight hash
as well. Do not confuse an individual file checksum with the expanded checksum,
skip an unexpected migration, or edit a package migration to fit this review.

## Exact native manifest permissions

The native public shape is `tapdb-identity-conversion/v1` with only `tables`,
`added_tables`, and optional `target`. The copy policy has empty table permissions
and no added tables. Binding `target` permits the explicit configured/physical
relocation, while all original table metadata, rows, cells, and multiplicity
must remain identical. Bind physical destination identity independently to O's
actual copy/control/provider evidence; a manifest is not a provider receipt.

The migration manifest grants:

| Item | Exact permitted difference |
|---|---|
| Original source cells | None: every `changed_columns` contract is absent |
| Original source row keys/multiplicity | No loss or modification; no added rows except migration tracking |
| `_tapdb_migrations` | Add exactly the eight approved pending filenames and native application timestamps; retain all five original rows unchanged |
| `generic_instance` | Add only `identity_key`; all original rows must have NULL in that new column |
| Eight original tables except `_tapdb_migrations` | Native catalog changes declared by the tagged migrations: RLS, native policies/functions/triggers/constraints/indexes and required nullability; retain original ownership/kind/columns/primary keys |
| New `tapdb_legacy_outbox_mapping` | Exact native table/schema, empty for this source |
| New `tapdb_runtime_principal_scope` | Exact native table/schema, empty before principal binding; later binding additions require the separate exact principal receipt |

Native `schema_changes: true` is a per-table permission, so independent review
must match every actual catalog difference to the tagged source. Native
`added_rows: true` for tracking and `added_tables` also require exact added-key,
count, timestamp, and table-content review. These permissions do not silently
approve unrelated DDL, records, or runtime principals. Native primary-key and
original-column preservation checks remain mandatory.

With the unchanged mapped source and exactly eight applied tracking rows, the
post-migration inventory before binding/probes should contain 11 tables and
79,926 rows. This derived expectation is not a substitute for full native
comparison. Any changed cutoff data requires a fresh source-derived review.

The native audit migration considers NULL/trimmed-empty attribution. The supplied
hash census establishes zero NULL/empty-string hashes, and this manifest permits
no audit changes. Complete before/after comparison must prove that no other row
changed. Do not add a transformation allowance in response to a failed check.

Preserve every original UID/EUID, DGX/TPX binding, domain/issuer/tenant/machine
value, creation timestamp, deleted record, lineage endpoint, audit field,
idempotency/share/membership record, and integration payload. Existing NULL
machine UUIDs and tenant values are historical state, not a backfill request.

## Materialize the actual target binding

All paths below are explicit absolute operator inputs. `TARGET_COPY` is the
actual untouched-copy native contract; `COPY_POLICY` and `MIGRATION_MANIFEST`
are the byte-identical reviewed files above. `COPY_TARGET_MANIFEST` and
`FINAL_TARGET_MANIFEST` must be new private files in an existing evidence
directory. `REVIEW_MAX_INPUT_BYTES` is the reviewed finite complete-file limit.

This offline recipe uses the already-tested receipt reader to validate seals.
It copies only the native target into a fixed reviewed policy; it does not infer
permissions from differences, edit a native receipt, or contact a database:

```bash
PYTHONPATH="$DEWEY_MIGRATION_REPO/scripts" python - \
  "$TARGET_COPY" "$COPY_POLICY" "$MIGRATION_MANIFEST" \
  "$COPY_TARGET_MANIFEST" "$FINAL_TARGET_MANIFEST" \
  "$REVIEW_MAX_INPUT_BYTES" <<'PY'
import json
import os
import sys
from pathlib import Path
from tapdb10_inventory_diff import read_inventory

after, reference = read_inventory(Path(sys.argv[1]), max_input_bytes=int(sys.argv[6]))
jobs = [(Path(sys.argv[2]), Path(sys.argv[4])),
        (Path(sys.argv[3]), Path(sys.argv[5]))]
assert len({str(output) for _, output in jobs}) == 2
policies = []
for policy_path, output in jobs:
    assert policy_path.is_absolute() and policy_path.is_file()
    assert output.is_absolute() and output.parent.is_dir() and not output.exists()
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert set(policy) == {"schema_version", "tables", "added_tables"}
    assert policy["schema_version"] == "tapdb-identity-conversion/v1"
    assert all(not item.get("changed_columns") for item in policy["tables"].values())
    policies.append((output, {**policy, "target": after["target"]}))
for output, manifest in policies:
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
print(json.dumps({"bound_from": reference, "native_verification_required": True}))
PY
```

If output creation fails partway, retain the existing output and inspect the
exact failure; do not overwrite it or repeat the pair blindly. Record both
manifest file hashes and this binding recipe's source receipt reference. The
same-target migration manifest itself remains unchanged and has no `target`.

Run native verification at three explicit boundaries, retaining JSON stdout and
exit status in new files as described in the runbook:

```bash
tapdb --config "$DESTINATION_CONFIG" --json db identity verify \
  --before "$SOURCE_FINAL" --after "$TARGET_COPY" \
  --conversion-manifest "$COPY_TARGET_MANIFEST" \
  --sequence-mappings "$DESTINATION_MAPPINGS"

tapdb --config "$DESTINATION_CONFIG" --json db identity verify \
  --before "$TARGET_HISTORICAL" --after "$TARGET_AFTER" \
  --conversion-manifest "$MIGRATION_MANIFEST" \
  --sequence-mappings "$DESTINATION_MAPPINGS"

tapdb --config "$DESTINATION_CONFIG" --json db identity verify \
  --before "$SOURCE_FINAL" --after "$TARGET_AFTER" \
  --conversion-manifest "$FINAL_TARGET_MANIFEST" \
  --sequence-mappings "$DESTINATION_MAPPINGS"
```

`TARGET_AFTER` must describe the completed migration before application writes
or acceptance-test allocations. The separate exact allocator comparison and
strict source-next/family floor procedure remain in the
[runbook](20260911T040703Z_dewey_tapdb10_migration_preparation.md). Later authorized
runtime binding or acceptance writes require their own actual persisted-row
evidence; do not preapprove them as arbitrary migration additions.

The release's `db schema migrate` has no `--conversion-manifest` option.
Supply these manifests only to `db identity verify`. Migration preflight/apply
uses the exact copy-local historical contract with its current family and the
native declared migration contracts. If an approved preparatory sequence advance
changes the copy first, capture a new `9.0.9` contract on that same target with
`--recovery-family` before migration; never reuse stale pre-advance evidence.

## Application adoption and remaining inputs

Dewey implementation `9a4463d` retains the 11 historical template codes,
requires their `DGX` instance prefix, and uses verification-only startup.
`BaseDeweyService.verify_existing` performs template reads with `commit=False`;
`TapDBBackend.ensure_templates` neither seeds nor changes an existing template.
Existing application JSON identity keys remain in use. External-reference
objects and their lineage remain authoritative; the migration does not promote
graph-reference metadata or replace them with a new representation. No per-row
Dewey conversion is required by the inspected application adoption code.

Exact remaining inputs are:

1. Final isolated source contract and native planned-next receipt; their full
   row/cell and allocator evidence must confirm this discovery-based review.
2. Actual untouched-copy receipt and O's physical copy/access-control evidence;
   use its exact native `target`, not an invented config path/OID.
3. Native copy-origin family, target-local historical contract, migration
   preflight with the eight pending filenames/expanded hashes, applied result,
   and complete post-migration identity/sequence inventories.
4. Independent comparison of every actual catalog difference, the eight added
   tracking records, two new native tables, no original cell transitions, and
   final native strict-floor results before runtime acceptance.

**Validation boundary:** Only new JSON/data/doc preparation is added. Reuse the
existing 16-test helper receipt and the later 12-case RC delta receipt. No
unchanged test suite or live database test is rerun by C for these inputs.
New static checks passed for exact native JSON fields, restricted original-cell
permissions, both hashes for every source migration filename, binding-recipe
Python syntax, balanced code fences, and `git diff --check`.

## Controlling source references

- [Native public conversion contract](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/identity_inventory.py#L810-L964)
- [Native migration contracts and exhaustive preservation](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/migration_identity.py)
- [Tagged migration assets](https://github.com/Daylily-Informatics/daylily-tapdb/tree/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/schema/migrations)
- [Dewey verification-only backend](https://github.com/lsmc-bio/dewey/blob/9a4463d7312ee91d5363157b35e23131a3e0d78f/dewey_service/tapdb_backend.py)
- [Dewey startup verification](https://github.com/lsmc-bio/dewey/blob/9a4463d7312ee91d5363157b35e23131a3e0d78f/dewey_service/services/base.py)
- [Dewey preserved external-object/lineage service](https://github.com/lsmc-bio/dewey/blob/9a4463d7312ee91d5363157b35e23131a3e0d78f/dewey_service/services/external_objects.py)
