# Rehearsal post-migration acceptance inputs

Prepared by independent E at 2026-09-11T07:38:09Z. O reports successful
corrected native schema apply, RC 0, completed
`2026-09-11T07:33:01.727267Z`. Its private result is 473577700 bytes, file
SHA-256 `9abc8f3534ac3ef715e6cfdafb04668eef087e224ec8183f42635e8b42756689`.
Reported recovery and allocator outcomes are committed, allocator verification
is true, and the writer-fence release seal is
`d0d58806ced83762054eb809e8d6f5ec487ae4abfd64f06cff01d3777268d2ce`.
This status is O's result report; E's next actual receipt review is separate.

Use the results of the already running capture and planned native verification,
diff and sequence stages. No source reconnection, new census, full receipt
transfer, new test suite, package change or additional backup is needed.

## Compact evidence bundle

| Stage | Preserve in the safe projection | E acceptance condition |
|---|---|---|
| Migration completion | Real command RC and input/output hashes; native preflight, result and postflight seals; applied filenames; recovery/allocator result links; fence acquire/release physical identity | Exactly accepted preflight `099586c0...`, eight accepted assets, committed terminal recovery/allocator outcome, verification true, released fence on rehearsal OID 645854 |
| New current-schema capture | Real completion; full file and native source/identity/sequence seals; schema/target/physical identity; complete family descriptor; row/table counts and limits | Same operator config, copy OID/server, domain M, owner dewey and family `a6defebd...`; capture source-version explicitly `10.1.1rc1` |
| Native identity comparison | Actual stdout/RC with before/after seals, `ok`, `violations`; manifest input hash | RC 0, `ok: true`, empty violations; exact accepted same-copy manifest `af99535d...` |
| Detailed inventory comparison | All actual catalog differences; missing/added key counts and hashed keys; original-column change/multiplicity counts; added-column NULL counts; new table metadata/content | Only the already accepted schema additions and tracking rows below; no unexpected original row/cell change |
| External floor preparation | Exact floor-input file/hash and unchanged native source-next plan file/hash; provenance and all integer records | All source allocated/assigned, retained and native planned-next boundaries copied without arithmetic or omission; rehearsal currently has no extra cross-copy input |
| Native sequence preflight | Complete small native plan; real command completion; exact config/mappings/floors/family input hashes; current family state/pending/heads | All 20 generators included with complete current journal history; no pending operation; each native planned next strictly exceeds applicable retained/source boundary; exact plan file hash reviewed before apply |
| Native sequence completion | Applied receipt with plan link, committed outcome and fence release; actual strict verify stdout/RC | Same reviewed plan; successful native release and strict verify RC 0 / true / no violations before binding |

The complete row-bearing inputs remain in O's protected evidence directory.
Where a projection abbreviates a digest for display, retain the full digest in
the underlying safe JSON. A projection is not a replacement native receipt;
the real command completion links it to the private full file.

## Exact preservation envelope before runtime binding

- Expected total: **11 tables and 79926 rows**, derived from the accepted 79918
  original rows plus eight tracking rows. Counts supplement exhaustive native
  comparison; they do not replace it.
- Retain every original row key, multiplicity, identity and original-column
  cell. `_tapdb_migrations` receives only the eight exact accepted filenames and
  their native application timestamps, with five original rows unchanged.
- `generic_instance` adds only `identity_key`; all **12204** original rows have
  NULL in that new column. No backfill, remint or original-cell transformation
  is permitted by the accepted comparison manifest.
- `tapdb_legacy_outbox_mapping` and `tapdb_runtime_principal_scope` are the only
  new tables and are empty at this stage. Binding its exact runtime scope is a
  later separately reviewed change.
- Match every actual table-catalog difference to the eight immutable migration
  assets. Per-table `schema_changes` permission does not authorize unrelated
  ownership, primary-key, column, RLS, policy, trigger or constraint changes.
- Preserve all **20** sequence names, definitions, owners, dependencies and
  prefix/owned-column meanings. Only the released additions to catalog prefix
  evidence are allowed for AY, MSG, WSX, WX and XX; existing evidence remains.
  Any allocator position change must be owned by its native plan/result.

The original-source next-plan file hash remains
`019284408c20d71c415550ed081c893549e6f407966dd9f4991cc2e6d62c495f`, bound to
source sequence seal `903928e63a8cd22f078f429d3aa55c125b48fc212925a29cbff91f0c41482cc0`.
Do not substitute the copy's target identity for the original observation or
join the original source to the new copy-rooted family.

Source basis: native `migration_identity.py:703–1094` checks original rows,
cells, exact generator definitions/ownership and declared additive prefix
evidence; lines 1240–1396 link native migration, separate post-commit
observation and terminal allocator/recovery results. C's already accepted
hash-only diff reader covers all inventory catalog fields and original
row/column hashes (`scripts/tapdb10_inventory_diff.py:63–218`). No new
comparison implementation is introduced by this checklist.

The user's queue preservation/acknowledgement/replay waiver remains in force;
this checklist adds no queue-specific gate. Source remains closed and its old
container stopped. Actual native binding, fresh runtime privilege/context
checks and isolated image acceptance follow the existing sequence, with no
automatic activation based solely on schema apply success.
