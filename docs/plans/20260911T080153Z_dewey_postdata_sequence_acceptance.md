# Actual rehearsal post-migration and sequence-plan acceptance

**E accepts the actual post-migration preservation result and the exact next
sequence apply on rehearsal OID 645854.** This disposition was sent to O before
this document was committed. The unchanged release is TapDB `10.1.1rc1`, commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. O alone executes live operations and
updates the controlling ledger.

## Exact apply boundary

| Input | Reviewed SHA-256 |
|---|---|
| `rehearsal-post-migration-review.json` | `fb4d94a4e4c17555d54faaae769fdfabec9f0f492bc1f608e8d081ad8ce35090` |
| `rehearsal-sequence-plan.json`, 76375 bytes | `3fcdef0f0d8a6965fadc4e22c5117535d0635b30719a966823f7675d5e4d3aef` |
| `rehearsal-external-floors.json`, 38 records | `b5faf66ce3955203c67cf6fc82f76d3ab815f4c5d69607ad58b186075055f99f` |
| Sequence-plan completion | `c4693475f89d741f8f78c1528dad12a01dbd8984691c09dcf33712b6c440c03a` |
| Floor-preparation completion | `f54e3c86abcfc5d50f4ddbd644548b47778ab3cd1dda81ef905b217698d409a9` |
| Corrected operator wrapper | `e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407` |
| Unchanged execution capsule | `7fbe0e00e5557bde7ffb2afaa50606ade8c391136a5ce77eb95fd7afd89f001d` |
| Copy operator configuration | `9208dde2d25577ff06679e2bd19a37870ddc1c5d3039edc11dd31f3da8f53520` |

The native plan seal is
`83f86ca0aae608b2de42147c68280534848029d057c7b60cec72eabeda7f2791`.
The retained complete-family state seal is
`bd4788c655ffa5f95c85b56d4385918bcba6dbacf69255f42d85361fc8399c7c`.
The full unchanged family descriptor has seal
`a6defebdfce4fa923ba64e67f35a742c0859239ac90e2ee82664b26a521cfc9b`
and UUID `bfb30029-5dd1-42ec-8bf8-3094e78ae2f6`.

This acceptance permits `sequence-apply` using the full plan file hash above
as `--reviewed-plan-sha256` and this E review as `--review-reference`, with the
already reviewed capsule. The target remains
`dewey_tapdb10_rehearsal_20260911`, schema `tapdb_dewey_lsmcok1_local`, domain M,
owner dewey, physical OID 645854 on `10.0.2.148/32:5432`, and config identity
`/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-operator.yaml`.
It does not authorize runtime activation or substitute for the native apply's
fresh target, family-state and writer-fence checks.

## Actual data result

Native schema apply completed RC 0 at `2026-09-11T07:33:01.727267Z`; its
473577700-byte private result has file hash
`9abc8f3534ac3ef715e6cfdafb04668eef087e224ec8183f42635e8b42756689`.
The outer recovery completion is committed, allocator verification is true,
and the target writer fence is released. The inner migration record's
`commit_status: pending_caller_commit` is the retained pre-commit record;
the separate terminal recovery/allocator result supplies the actual outcome.

The actual current-schema capture completed RC 0 at 07:38:22Z. Its file hash
is `8ccf9d7f396451c7665b850ca54bf61d98e9ba943c57822a662c470da38d7c8b`,
identity seal
`0038875e5ee67cb572a7984219462a65730cdb6c70d16f128f83efa184c75eca`, and sequence
seal `ff70c88d6c5f2db82b53b7e74066b6f2452553fec562d3a236e411ea81db8b1b`.
Both seals agree with the committed migration postflight and the exact new
sequence preflight.

Native identity verification completed RC 0 at 07:41:20Z with `ok: true` and
no violations, using the accepted manifest
`af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8`.
E validated the verification receipt seal and reconstructed the exact original
344-byte stdout from its complete projected native fields; file hash
`73041c917eb33afd5be761243599f1d5732023c45ee2fe8525a3cb16cf926843` agrees.

The complete safe catalog/count projection and existing exhaustive hash diff
show:

- All 79918 original rows retain every original cell, row key and multiplicity.
  There are no original-row deletions, additions outside migration tracking,
  or original-column changes.
- The only added rows are eight `_tapdb_migrations` records. E recomputed their
  primary-key hashes from the exact accepted native filenames; all eight agree.
  Five original migration records remain unchanged. Total rows are 79926.
- All 12204 original instances have NULL in the new `identity_key` column.
  `tapdb_legacy_outbox_mapping` and `tapdb_runtime_principal_scope` are the only
  new tables; both are empty before binding. Total tables are 11.
- All actual catalog differences match the eight immutable migration assets:
  nullable natural identity and its check/indexes, immutable identity protection,
  forced RLS and the declared policies, required audit attribution, lineage
  endpoint scope trigger, and the two native tables. Owners, primary keys and
  all original columns are retained; the sole changed original-column catalog
  property is the declared `audit_log.changed_by` NOT NULL constraint.
- All 20 generator names, definitions, states, owners and dependencies match
  the accepted historical preflight. Only the declared additive catalog prefix
  annotations for AY, MSG, WSX, WX and XX differ; original mappings remain.

E checked the complete projected catalog fields against released source and
independently recomputed all 20 before/after table-catalog hashes. The source
basis includes `identity_inventory.py:523` for filename-key hashing,
`schema/rls.sql:11` for runtime scope, `schema/rls.sql:60` for operator policies,
`schema/rls.sql:314` for audit attribution, `schema/rls.sql:536` for lineage
scope, and the already accepted natural-identity, legacy-mapping and prefix
annotation migrations. The projection adds no native acceptance authority.

## Exact source-floor retention and target advances

Using the published public functions from the existing isolated RC environment,
E reproduced the original-source native plan seal
`56d3d1a081d130f91da3848526db5d1f9510359c4918d0efc75d4e58c3e746f3`
from the retained full sequence inventory. Its file hash remains
`019284408c20d71c415550ed081c893549e6f407966dd9f4991cc2e6d62c495f`.
All 38 allocated/assigned/native-planned-next floor records reproduce exactly,
including provenance and unchanged integer values. They are exactly the
new plan's `input_floors` and are all present in its 130 complete floor records.

E separately recomputed the plan's arithmetic using its full sealed 130 floors.
All 20 advances agree with the native receipt and strictly exceed the original
source's planned next values:

| Sequence | Reviewed next value |
|---|---:|
| adt_instance_seq | 76691 |
| audit_log_uid_seq | 66692 |
| ay_instance_seq | 10001 |
| dgx_instance_seq | 22204 |
| edg_instance_seq | 11016 |
| generic_instance_lineage_uid_seq | 1017 |
| generic_instance_uid_seq | 12206 |
| generic_template_uid_seq | 24 |
| gse_instance_seq | 2 |
| gvr_instance_seq | 6 |
| inbox_message_uid_seq | 2 |
| msg_instance_seq | 10001 |
| outbox_event_attempt_uid_seq | 2 |
| outbox_event_id_seq | 2 |
| sys_instance_seq | 10001 |
| tpx_instance_seq | 10012 |
| wsx_instance_seq | 10001 |
| wx_instance_seq | 10001 |
| xrf_instance_seq | 2 |
| xx_instance_seq | 10001 |

The local arithmetic check did not claim to replay private remote journal
history. The native plan carries the complete family and current state seal;
the terminal migration/fence receipts and subsequent read-only captures supply
the observed lifecycle. Native `cli/sequences.py:133–195` recaptures and requires
exact equality with the reviewed plan before acquiring its actual target fence,
then records committed advancement and fence release. Those checks remain
mandatory. No additional census or test is required by this E decision.

## Remaining acceptance and ledger disposition

L08 can advance to SUCCESS for the actual preservation and accepted manifest.
L04/L05/L09 retain IN_PROGRESS while recording successful actual schema/data
acceptance and this exact allocator-plan clearance. L10 can advance to
IN_PROGRESS for independent actual PostgreSQL/data acceptance. O remains the
sole ledger writer.

Next, retain and review the actual sequence result, its committed outcome and
released writer fence, and the actual strict native sequence verification.
Binding, runtime authentication/privilege checks, concurrency, isolated image
acceptance, accepted-state recovery and final production acceptance remain
separate. The original source stays closed and its old container stopped.
The user's no-additional-backup instruction and queue preservation waiver
remain in force.

E made zero database calls, downloaded no private row receipts, and ran no test
suite. The existing fixture and release tests were reused. Local work was source
and actual receipt validation only. Private full artifact hashes are linked by
O's native command completions; they were not rehashed on E's workstation.

[Machine-readable review evidence](20260911T051700Z_tapdb1011rc1_evidence/20260911T080153Z_rehearsal_postdata_sequence_acceptance.json)
has file SHA-256
`4e5264386d7f11f0c646c13d91dfd21e6ed77d3f42f4c79f3de156074be9ad8d`.
