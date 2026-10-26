# Historical metadata conversion, exact RC

C authored `scripts/dewey_metadata_conversion.py`, SHA-256
`d99d763572d7fbc350a8f296051232539c1caca0136fcee0f9a36b53e36b9579`.
E's static source review found no must-fix issue. Actual native input, read-only
plan, committed result and native comparison require separate acceptance.
O alone runs these stages in the retained interactive ubuntu operator session.

1. Finish the independently accepted two-template setup and refreshed native
   runtime binding. Keep the candidate stopped, original source closed and
   every other target session absent. Retain a **new native before inventory
   after setup/binding**, using the same fixed operator config, mapping input,
   identity limit policy and complete recovery family. The old pre-template
   inventory is not the conversion baseline.
2. Stage the exact metadata helper beside the accepted
   `dewey_xrf_template_setup_port_fix.py` (SHA
   `a59c18d74d3ebf251e418c79beb5597fcac42fba706a0f54512578e6ed14cdd9`)
   and `dewey_rehearsal_copy.py` (SHA
   `d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`).
   Create a new private output directory and record its exact path.
3. Run the read-only plan below; obtain E's review of its file hash and exact
   cells before invoking the separate apply stage. O supplies the actual
   native before path, existing private output directory, stopped candidate
   identity and explicit audit actor; those inputs remain identical at apply.

```bash
C_ROOT=/home/ubuntu/dewey_ops/tapdb101-20260911
C_PY="$C_ROOT/venv/bin/python"
C_METADATA="$C_ROOT/dewey_metadata_conversion.py"
C_OPERATOR="$C_ROOT/rehearsal-operator.yaml"
C_OID=645854

"$C_PY" "$C_METADATA" plan --config "$C_OPERATOR" \
  --before "$C_METADATA_BEFORE" --target-oid "$C_OID" \
  --output-dir "$C_METADATA_DIR" --actor "$C_ACTOR" \
  --candidate-container "$C_CANDIDATE_CONTAINER"

"$C_PY" "$C_METADATA" apply --config "$C_OPERATOR" \
  --before "$C_METADATA_BEFORE" --target-oid "$C_OID" \
  --output-dir "$C_METADATA_DIR" --actor "$C_ACTOR" \
  --candidate-container "$C_CANDIDATE_CONTAINER" \
  --reviewed-plan-sha256 "$C_METADATA_PLAN_FILE_SHA" \
  --review-reference "$C_METADATA_REVIEW"
```

These commands use O's existing targeted-sudo invocation and approved explicit
AWS environment; they do not grant new privilege. The helper requires that
targeted invocation, exact installed TapDB 10.1.1rc1, operator dayhoff and M/dewey
scope. Public `operator_connection` owns the transaction and public
`update_object` owns every metadata update. There is no application startup,
template seeding, native reference creation or source reconnect in this step.

The actual census requires 12,200 DGX instance and 1,015 lineage records in
scope, all active. Exactly 13,214 rows change:

| Change | Instances | Lineages |
|---|---:|---:|
| Add absent `properties: {}` | 12,091 | 1,014 |
| Archive and remove the obsolete active graph key | 109 | 0 |

Existing flat business fields remain in their original location. Each observed
graph list is copied verbatim to top-level
`dewey_tapdb10_archive["properties.external_payload.tapdb_graph"]`, then the
active `properties.external_payload.tapdb_graph` key is removed. Empty parent
objects remain. Archive collisions, malformed properties, unknown projection
owners, unexpected pseudo-edge fields, deleted records/endpoints, changed
input cells or lossy JSON decoding stop before commit. The graph is retained
as non-authoritative evidence, never interpreted to create relationships.
The four other-scope GVR records and every template remain untouched.

Every original UID/EUID, prefix, domain/issuer/tenant, creation timestamp,
relationship type and lineage endpoint remains immutable. PostgreSQL sets
`modified_dt` to the exact transaction timestamp and creates exactly two audit
rows per changed record, one for metadata and one for its modification time:
26,428 new audit rows. The helper verifies actual actor, scope, operation,
target and original/new JSON hashes; it stores each new audit row hash.
The committed result is written only after the real outer commit returns.

4. Retain the actual terminal RC and result. Capture a new native identity and
   sequence inventory with the same config/family/mappings as the before
   capture. Supply its exact path as `C_METADATA_AFTER`:

```bash
"$C_PY" "$C_METADATA" manifest --config "$C_OPERATOR" \
  --before "$C_METADATA_BEFORE" --after "$C_METADATA_AFTER" \
  --target-oid "$C_OID" --output-dir "$C_METADATA_DIR" \
  --actor "$C_ACTOR" --candidate-container "$C_CANDIDATE_CONTAINER"

"$C_ROOT/venv/bin/tapdb" --config "$C_OPERATOR" --json db identity verify \
  --before "$C_METADATA_BEFORE" --after "$C_METADATA_AFTER" \
  --conversion-manifest "$C_METADATA_DIR/metadata-conversion-manifest.json"
```

Record native verify stdout and actual RC in new private files. The manifest
allows only the exact reviewed per-row JSON and DB timestamp before/after
hashes, plus audit additions. It allows no schema changes, missing rows or
identity mutation. Native comparison independently checks all other cells;
E additionally checks that the broad native audit-addition permission is
bounded by the exact new audit rows in the committed result. Original full
receipts stay private; publish only hashes, counts and acceptance metadata.

5. After that proof, the separate runtime-scoped native-reference plan may
   derive canonical assertions from the existing authoritative two-lineage
   pairs through D's accepted adapter. The two explicitly non-federated
   operational types retain their original DGX records and lineage. No native
   attachment runs as unrestricted operator, and no runtime template seeding
   or old-shape fallback is introduced.

All outputs use exclusive creation. Preserve any started marker, failure and
native journal; never delete them to replay an ambiguous apply. Even rolled
back writes can consume allocator values. Retain all sequence state from these
operations and the complete family in the later final exposure plan. For the
final fresh copy, first advance above frozen source and full rehearsal exposure
floors, then use the actual final OID, replacement-operator config and new
conversion receipt paths. Repeat these reviewed phase boundaries; create no
backup and reopen no old source.

Focused local validation: eight new pure conversion/manifest guard tests passed
once using `pytest --noconftest -q tests/test_dewey_metadata_conversion.py`.
These tests do not claim a native or database rehearsal. Ruff and syntax
checks passed. Existing suites were not repeated. Actual PostgreSQL mutation,
audit counts and native preservation remain O/E's pending evidence.
