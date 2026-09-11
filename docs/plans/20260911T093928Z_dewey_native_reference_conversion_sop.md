# Native reference conversion from preserved local lineage

Prepared by C for O's operator execution and E's independent acceptance.
Script `scripts/dewey_native_reference_conversion.py`, SHA-256
`006cc4ec8b7ac18363568273784a8ff00f644d02e6ebe6f82839ca4310484f1b`.
This is a one-time data operation for the immutable TapDB 10.1.1rc1 target.

1. Complete the exact scoped template setup, native runtime rebind, metadata
   conversion and its successful native identity comparison. Use the resulting
   full native after inventory as this step's before; pass the actual native
   verification stdout JSON as `--metadata-verification`. Its valid seal,
   `ok=true`, empty violations and exact matching after identity seal are required.
   The source stays closed and both old/candidate containers stay stopped.
2. Stage the helper beside the accepted metadata, template-port-fix and copy
   helpers. Stage **only the exact committed adapter module** from D commit
   `0f3509cefe4df4a326403af9d2268ca8f2c6cda6` as
   `dewey_native_reference_adapter.py` in the protected operator root. Its
   required SHA is
   `f433e4a3382ba5738cf4d75de00c1d5e254e8f3420db2387b73357825503d298`.
   No app installation, startup, package patch or alternate module discovery
   is needed. Create an explicit new private output directory.
3. Run the read-only plan below in O's retained ubuntu session, using its
   established targeted-sudo invocation and explicit AWS environment. Preserve
   all stdout/stderr and actual RC privately. O supplies the exact stopped
   container, actor, actual metadata after/proof paths and output directory.

```bash
C_ROOT=/home/ubuntu/dewey_ops/tapdb101-20260911
C_PY="$C_ROOT/venv/bin/python"
C_REFERENCE="$C_ROOT/dewey_native_reference_conversion.py"
C_ADAPTER="$C_ROOT/dewey_native_reference_adapter.py"
C_OPERATOR="$C_ROOT/rehearsal-operator.yaml"
C_RUNTIME=/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml
C_OID=645854
C_REFERENCE_BEFORE="$C_METADATA_AFTER"

"$C_PY" "$C_REFERENCE" plan \
  --operator-config "$C_OPERATOR" --runtime-config "$C_RUNTIME" \
  --adapter "$C_ADAPTER" --before "$C_REFERENCE_BEFORE" \
  --metadata-verification "$C_METADATA_NATIVE_VERIFY" \
  --output-dir "$C_REFERENCE_DIR" --target-oid "$C_OID" \
  --candidate-container "$C_CANDIDATE_CONTAINER" --actor "$C_ACTOR"
```

The plan opens a public read-only operator census, closes that connection, then
opens the exact bound runtime principal with public `TAPDBConnection`.
`session_scope` installs the M/dewey runtime context before reads. Its fresh
transaction is REPEATABLE READ and explicitly read-only. The runtime config
retains NULL tenant and `allow_global_claims=false`; it contains no operator
credential section. The exact configured CA file must exist. No native attach
is called during planning and no identifiers are allocated.

The runtime view must contain both exact canonical scoped XRF templates and
no preexisting native XRF instances/links. For each historical relation, the
accepted adapter resolves its two authoritative active lineage parents and
checks their scopes. Every original participant's full native row hash must
match the accepted before inventory. Archived graph metadata supplies no edge.

| Historical system/type | Relations | Disposition |
|---|---:|---|
| atlas/patient | 1 | Native TapDB object |
| bloom/sequencer | 1 | Native TapDB object |
| bloom/sequencing_run | 131 | Native TapDB object |
| ursa/analysis | 1 | Native TapDB object |
| ursa/analysis_job | 152 | Native TapDB object |
| dyec/dayoa_analysis_directory | 6 | Retain typed local DGX relation |
| ursa/run_directory_analysis_trigger | 148 | Retain typed local DGX relation |

The plan requires exactly 440 relations: 286 native assertions and 154 explicit
non-federated dispositions. It computes the actual unique native-target count
using the released target's exact `identity_key` (service plus remote EUID),
excluding object kind. It refuses duplicate source/target/relationship
assertions, conflicting non-null descriptors and any descriptor enrichment
that would change a newly created reference later in the same operation.
The unique target count is an actual-plan fact, not an invented fixed count.
E reviews that count and the exact row-safe plan hash before apply.

4. Apply only that exact plan, with all input paths/content unchanged:

```bash
"$C_PY" "$C_REFERENCE" apply \
  --operator-config "$C_OPERATOR" --runtime-config "$C_RUNTIME" \
  --adapter "$C_ADAPTER" --before "$C_REFERENCE_BEFORE" \
  --metadata-verification "$C_METADATA_NATIVE_VERIFY" \
  --output-dir "$C_REFERENCE_DIR" --target-oid "$C_OID" \
  --candidate-container "$C_CANDIDATE_CONTAINER" --actor "$C_ACTOR" \
  --reviewed-plan-sha256 "$C_REFERENCE_PLAN_FILE_SHA" \
  --review-reference "$C_REFERENCE_REVIEW"
```

Apply rebuilds the same read-only plan before writing its exclusive started
marker. Only D's accepted `attach_external_relation` invokes the released
`ExternalReferenceService`; no raw object/lineage insertion or reconstruction
occurs. The 154 local dispositions allocate nothing. New native assertions use
the original relation creation timestamp, fixed authority
`dewey.external_object_relation` and deterministic provenance from the actual
relation and its two preserved lineage UIDs. Existing DGX objects and lineages
are retained unchanged. No endpoint is inferred from EUID syntax.

Each native assertion must return a newly created lineage with exactly the
planned source, target identity, relationship, authority, timestamp and
provenance. New references have XRF prefix and canonical native coordinates.
The helper reads and hashes every actual new instance, lineage and audit row;
requires one INSERT audit row per new instance/lineage with exact actor/scope;
and writes its result only after the runtime transaction commit returns.
Native identity claims may consume unused generator values on conflicts for
references shared by different sources. Preserve those values too.

5. Capture a fresh **operator** native identity/sequence inventory afterward,
   using the unchanged operator config, complete family, mappings and limits.
   Set its actual path as `C_REFERENCE_AFTER`, then generate and verify the
   narrowly additive manifest:

```bash
"$C_PY" "$C_REFERENCE" manifest \
  --operator-config "$C_OPERATOR" --runtime-config "$C_RUNTIME" \
  --adapter "$C_ADAPTER" --before "$C_REFERENCE_BEFORE" \
  --after "$C_REFERENCE_AFTER" \
  --metadata-verification "$C_METADATA_NATIVE_VERIFY" \
  --output-dir "$C_REFERENCE_DIR" --target-oid "$C_OID" \
  --candidate-container "$C_CANDIDATE_CONTAINER" --actor "$C_ACTOR"

"$C_ROOT/venv/bin/tapdb" --config "$C_OPERATOR" --json db identity verify \
  --before "$C_REFERENCE_BEFORE" --after "$C_REFERENCE_AFTER" \
  --conversion-manifest "$C_REFERENCE_DIR/reference-conversion-manifest.json"
```

Native comparison must retain every original cell/table/schema exactly. The
only manifest permissions are added rows in instance, lineage and audit.
The helper separately requires that every allowed new row's hash/count matches
the actual committed native outcomes, and that those outcomes match the exact
planned assertions. E's actual result/native comparison acceptance remains
mandatory before application acceptance. Protected full evidence contains
actual identifiers; publish only reviewed safe projections and hashes.

The helper never auto-continues after a plan or failed/ambiguous apply. Preserve
the started marker, failed output, full recovery family and all journal heads;
do not delete evidence, reclassify existing references as a fresh conversion,
reseed counters or blindly retry. Rehearsal's final exposure plan must include
all allocations from templates, metadata audits, native references and later
application acceptance. Use the existing
`exposure-after-completed-transition-plan.json` workflow with the complete
family, after all writers stop. Its exposure transfers into the separate final
copy's first advancement. Never use the reduced completed-transition floor
file as the final exposure input.

For final, use the actual final OID, `replacement-operator.yaml`, fixed runtime
path `/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml`, role `dewey_runtime_9`
and entirely new per-phase receipt directories. Initial native advancement
above frozen source and complete rehearsal exposure precedes all setup/data
allocations. Repeat the reviewed template/bind/metadata/native-reference phases
without changing accepted helper code. No new backups or old-source reopening.

Validation: four new pure tests passed once for identity/descriptor conflicts,
assertion uniqueness, explicit enrichment refusal and exact manifest/result
linkage. Root's frozen Ruff 0.15.14 lint and test formatting check passed.
An exact published RC offline smoke proved constructor/engine read-only
options, NULL-tenant context and three PostgreSQL JSON projections without
acquiring a connection. Its first harness attempt stopped at a missing optional
`certifi` import; only that unexecuted smoke was rerun with the verified existing
CA file. No package dependency was added and no prior test suite was repeated.
