# Source-backed Dewey dormant generator mappings

**Status:** B independently accepted the four explicit mappings and their
source/catalog evidence. Native recapture remains required. This document is
role C's author evidence; independent acceptance is retained separately by B/E.
No database, sequence, registry, package, or production service was modified.

| Input | Exact reference |
|---|---|
| Mapping file | [Four-entry native input](evidence/20260911T053316Z_dewey_source_sequence_mappings.json) |
| Mapping file SHA256 | `5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8` |
| Historical source | TapDB tag `9.0.9`, peeled commit `52d5f498dc4751b7e42d346bee2811a14080e5a5` |
| Source asset | `schema/tapdb_schema.sql` |
| Exact asset SHA256 | `64362e2882a7b424f6bf3c6b3d9c21d1e859ec98d4ee61ca2a728cecfd134584` |
| Native platform | Published `10.1.1rc1`, commit `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c` |
| Native source contract SHA256 | `645315ea89b62edf78f30bdb83d282ea2bf782d4a98912f23662baeef2eba1b3` |
| Original native file SHA256 | `45776ac58ee2e9889a5590490a8a75d59c9745bca5dcc40ca982f0d75364a937` |
| Native sequence inventory SHA256 | `7dc63a2ae200cb19aa027994ee9a354be8108fe40c1ea9d478216f287ab4e1fc` |
| Source physical identity | `dewey_prod`, database OID `16749`, server `10.0.2.148/32:5432`, schema `tapdb_dewey_lsmcok1_local` |

The coordinator supplied the complete native sequence subreceipt in the
sanitized discovery index at
`docs/plans/evidence/20260911_dewey_rc_inventory/source-summary.json` in the
controlling worktree. Its sequence checksum was independently recomputed before
preparing this input. The complete private 225,211,759-byte source file remains
on the controlling EC2 host; this author did not copy its identity rows.

## Exact declarations and catalog match

The historical SQL asset explicitly declares each prefix in the corresponding
CREATE statement's source comment. This is source evidence, rather than prefix
inference from sequence names or ordinary live catalog comments.

| Actual generator | Explicit source declaration | Source line |
|---|---|---:|
| `wx_instance_seq` | `CREATE SEQUENCE IF NOT EXISTS wx_instance_seq; -- WX (workflow)` | 10 |
| `wsx_instance_seq` | `CREATE SEQUENCE IF NOT EXISTS wsx_instance_seq; -- WSX (workflow_step)` | 11 |
| `xx_instance_seq` | `CREATE SEQUENCE IF NOT EXISTS xx_instance_seq; -- XX (action)` | 12 |
| `ay_instance_seq` | `CREATE SEQUENCE IF NOT EXISTS ay_instance_seq; -- AY (assay)` | 13 |

The mapping's `source_declaration` preserves the exact source line including
spacing. Each native catalog definition matches the source DDL: increment 1,
minimum 1, maximum 9223372036854775807, start 1, cache 1, cycle false. All four
are owned by `dayhoff` and have only the observed schema dependency. Their
observed current state is `last_value=10000`, `is_called=false`, with no native
assigned or allocated floor. **Declared start 1 does not authorize resetting
current state.** Current counter state remains evidence; native source-next
planning and strict retained-floor advancement own the resumed values.

The RC's source-backed historical test evidence producer uses this same proof:
explicit exact-source prefix declaration, asset checksum, and matching complete
catalog definition. Its output contract is one object per actual generator with
exactly `kind`, `prefix`, and nonempty `evidence`. This input follows that public
mapping shape, with `kind: prefix` and a serialized evidence object. Additional
provenance inside the evidence string binds the actual source file/contract,
native sequence inventory, physical identity, owner, dependencies, and observed
state. The other 16 source generators keep their existing native mappings.

TapDB 9.0.9's CLI also lists `WX`, `WSX`, `XX`, and `AY` as reserved prefixes.
Its packaged ownership registry version `0.4.0` contains only domain `Z` native
ownership; it does not grant these four prefixes or domain `M` ownership. The
mapping preserves existing dormant allocator semantics. It does **not** create
a prefix claim, add an issuing template, modify a registry, or authorize future
use of those optional library prefixes by Dewey. Actual deployed ownership and
historical `DGX`/`TPX` bindings remain separate runtime acceptance evidence.

## Coordinator's next native step

Following the independent review, bind `SOURCE_MAPPINGS` to the exact absolute path of
the byte-identical reviewed JSON on the operator host. Use a distinct new
receipt path. The historical source version remains `9.0.9` even though the
operator tool is `10.1.1rc1`:

```bash
tapdb --config "$SOURCE_CONFIG" --json db identity inventory \
  --source-version 9.0.9 --sequence-mappings "$SOURCE_MAPPINGS" \
  --receipt "$SOURCE_MAPPED_DISCOVERY"
```

This read-only discovery recapture adds mapping evidence to the new sealed
inventory; do not patch or replace the old receipt. Require all original
generators to remain present, no `unmapped` mappings or missing generators, and
the four explicit declarations to survive unchanged. Compare any changed row
or sequence state to the actual intervening source activity; discovery is not a
frozen cutoff. Family creation and final isolated source capture use the same
reviewed mapping input and the exact native family flags in the
[migration runbook](20260911T040703Z_dewey_tapdb10_migration_preparation.md).
The restored target must prove its own matching definitions; the retained source
provenance remains unchanged rather than being rewritten to the target identity.

**Author validation:** the exact source commit and asset checksum, native
sequence subreceipt seal, four-key completeness, explicit prefix comments,
complete catalog definitions, owner/dependencies, and reported counter state
were checked offline against the supplied evidence. JSON parsing and
`git diff --check` are the required local checks for this data/docs amendment;
no unchanged helper tests or live database tests are rerun. Native acceptance of
the input and all subsequent migration/recovery acceptance belong to O/B/E.

## Immutable source references

- [TapDB 9.0.9 declarations](https://github.com/Daylily-Informatics/daylily-tapdb/blob/52d5f498dc4751b7e42d346bee2811a14080e5a5/schema/tapdb_schema.sql#L9-L14)
- [Historical reserved-prefix declaration](https://github.com/Daylily-Informatics/daylily-tapdb/blob/52d5f498dc4751b7e42d346bee2811a14080e5a5/daylily_tapdb/cli/db.py#L65)
- [Historical packaged ownership registry](https://github.com/Daylily-Informatics/daylily-tapdb/blob/52d5f498dc4751b7e42d346bee2811a14080e5a5/daylily_tapdb/etc/prefix_ownership_registry.json)
- [RC historical source evidence producer](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/tests/test_identity_inventory_helpers.py)
- [RC native allocator mapping contract](https://github.com/Daylily-Informatics/daylily-tapdb/blob/02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c/daylily_tapdb/sequences.py)
