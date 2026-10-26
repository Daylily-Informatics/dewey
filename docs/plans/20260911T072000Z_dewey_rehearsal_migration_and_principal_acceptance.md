# Actual rehearsal migration and principal plan acceptance

E independent review of O's actual receipts, fixed TapDB `10.1.1rc1` release
commit `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. O alone owns live execution
and the controlling Dewey ledger. No tests, live queries, credentials or
database mutations were executed by E for these decisions.

## Exact native migration apply accepted

**Accepted:** The corrected native migration preflight may be applied to the
existing rehearsal copy under the user's existing migration authorization.
Use the unchanged capsule, historical copy, family, mappings and the corrected
CLI-mode wrapper. This decision covers the eight native assets on this copy;
it does not claim successful apply, post-migration preservation, allocator
advancement, principal binding or service acceptance.

| Review input | Exact value |
|---|---|
| O's safe projection | `docs/plans/evidence/20260911_dewey_rc_inventory/rehearsal-migration-plan-review.json` in the controlling worktree |
| Projection file SHA-256, independently rehashed | `7f6a72742e229492363502288f9d909e1ab42336bc1c33e8d9c4740e4b2f96f4` |
| Native plan file SHA-256 for `--reviewed-plan-sha256` | `395433c166eda38dc8b7fa1828426377f3e74032884ff221ddb688bae86d9964` |
| Native plan evidence seal | `099586c0fb5477dc59ec67cef5916fb8e1981d5262b84daa0be017e3257b5702` |
| Native plan file size | 675150129 bytes, retained privately by O |
| Successful preflight completion | RC 0, `2026-09-11T07:19:05.789959+00:00` |
| Immutable capsule SHA-256 | `7fbe0e00e5557bde7ffb2afaa50606ade8c391136a5ce77eb95fd7afd89f001d` |
| Corrected wrapper SHA-256 | `e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407` |
| Actual copy | `dewey_tapdb10_rehearsal_20260911`, OID 645854, `10.0.2.148/32:5432` |
| Immutable copy operator config | `/home/ubuntu/dewey_ops/tapdb101-20260911/rehearsal-operator.yaml` |
| Family UUID | `bfb30029-5dd1-42ec-8bf8-3094e78ae2f6` |
| Native family seal | `a6defebdfce4fa923ba64e67f35a742c0859239ac90e2ee82664b26a521cfc9b` |
| Family file hash in actual command inputs | `b93e4eee00793bfc03b1aa8849ded6a1423c9fe42d19955077a1a00d57f37bee` |
| Family historical source seal | `a9dda93e32c3fad7b0d98a3fa0344a9562c38679743605f9705ed3ea99348d5c` |
| Historical source file hash | `02a1d920158669867979a579eee004fbf77d30ed7c8e50ea2f05dd009434bd23` |

E compared every pending migration's expanded SQL hash and all seven declared
allowance fields to the immutable release source. The five already-applied
filenames and asset hashes also match the earlier accepted source inventory.
The eight pending assets are exactly:

1. `20260902_010000_natural_identity_and_owner_uniqueness.sql`
2. `20260902_010100_legacy_outbox_message_conversion.sql`
3. `20260902_020000_force_rls_and_audit_attribution.sql`
4. `20260903_031820_runtime_ddl_guard.sql`
5. `20260904_061819_tenant_scoped_natural_identity.sql`
6. `20260910_203200_aurora_operator_principals.sql`
7. `20260910_220000_sequence_prefix_bindings.sql`
8. `20260910_233000_pin_managed_allocator_resolution.sql`

The expanded hashes include the released `rls.sql` and
`allocator_functions.sql` content where declared. No private TapDB helper was
called. This was a local comparison of the actual safe receipt to source,
not another suite or native migration execution.

E independently verified the native family, complete sequence inventory and
allocator-plan seals, allocator state hash and family state hash. All target
and physical fields agree across those objects. The only family member is the
actual copied origin; its explicit journal is
`/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-native-journal`.
Both retained pending maps are empty, with no retained operation floors or
inventories. All 20 generators are present and included in the strict native
plan. The unchanged original copied identity and sequence seals are
`676bee3e89b76dd4a0c2ac0b79b8e1580a5e92c8b31ffc01d9b772fcc6f5bbb2` and
`2add38618cd555a4b23a17f3ace437a2730df6040e3414f4947fadce0d1add85`.
The preflight still covers 79918 source rows, 173423825 evidence bytes and
the accepted 1-million-row / 8-MiB-row / 512-MiB-evidence policy.

[Independent comparison results](20260911T051700Z_tapdb1011rc1_evidence/20260911T072000Z_rehearsal_migration_plan_acceptance.json)
retain the exact checks and expanded asset hashes. The complete row-bearing
675 MB native plan stayed on the operator host; the successful native capture,
accepted prior exhaustive parity and its hash-bound completion establish that
artifact. E did not claim to rehash the private full plan locally.

Post-apply acceptance remains the already reviewed sequence: native migration
and terminal recovery/fence-release success, exhaustive native identity
verification plus narrow catalog-difference review, then separately reviewed
external source-floor advance and strict verification. No unrelated schema
change, original-cell conversion or remint is authorized. The original
`identity_key` cells remain NULL; expected additions are eight migration
tracking rows and two empty new tables before binding. The source stays closed
with its old container stopped. No additional backup or queue-preservation gate
is introduced.

## Runtime-principal wrapper and actual rehearsal bootstrap plan

**Accepted for its later bootstrap-apply stage after migration/floor gates:**
D's public-API wrapper at commit `c94191d`, file SHA-256
`9921210bd5b3ee4fcc52f06184dd88a6efa986e23e608f3672ccffcd529372f2`, and O's
`rehearsal-bootstrap-plan.json`, file SHA-256
`250e70eac8ba7e38a3bbb4089dba4fd0bee59e8ba17dafbdee00bc33837c6e2e`.
E independently verified both outer seal
`ffa76b81b4e77e4a0561425ea77843709bc540cac8e42fbe97f8abd43b6f766d` and native
bootstrap seal
`bba0522a8ae3e5f64a176928adbd10a43c4f6867bc235885d4e5bc67295b416b`.

The offline plan covers only `dewey_rehearsal_9` on the rehearsal database:
LOGIN true; SUPERUSER, BYPASSRLS, CREATEDB, CREATEROLE, REPLICATION and INHERIT
false; no memberships; CONNECT only; no schema changes. The native apply
authenticates the exact operator, creates the role if absent or validates an
existing role, then grants only target-database CONNECT. It does not rotate an
existing role's password or claim role existence from the offline plan.

The wrapper compares exact scope/transport/runtime credential references,
rejects operator fields in the runtime YAML, and overlays only the five
previously accepted operator keys in memory. The actual runtime identity is
`/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml`, hash
`a5ee191de51ae3912c96878ac92a3f80429888638d578ccb191f6cf1b6025117`.
It preserves empty tenant, `allow_global_claims=false`, domain M and owner
dewey. Both plan/apply compare the exact launcher/config/registry/CA/secret
reference hashes. The runtime file receives no operator credential references.

The accepted rehearsal secret-reference file hash is
`8bc774bd8ea78181a9deacf6a26189debcaa43615a3b8e584134b2f7e9e8721e`, recorded
version `092f355d-e532-4efb-b7af-d8dcb475f0ab`. E checked its role, lane, ARN
reference and version against the wrapper inputs. O reports a fresh owning
DescribeSecret confirmation of operator AWSCURRENT version
`d663d111-fc8f-8f82-d6e4-d15ee1a4807b`. The native credential accessor fetches
current secret material; the wrapper's version labels record reviewed evidence
and do not pin Secret Manager retrieval. D's SOP correctly requires O to retain
the matching current-version receipt and exclude rotation during these stages.

Native `bootstrap_runtime_principal` and `bind_runtime_principal` signatures and
behaviors were read at `runtime_principal.py:176–239,451–505,698–720,1083–1226`.
The actual bind plan must be generated and independently accepted separately;
native apply then rejects changed role/scope/ownership/privileges/catalog.
The wrapper requires native TEMP denial and privilege-verification success.
Its later runtime-only verification disposes cached engines, checks exact
login/scope, reads eleven existing DGX template bindings through public APIs,
and requires SQLSTATE 42501 for fixed nonallocating TEMP/schema DDL probes.
These checks are implementation review only until the fresh isolated image
produces its own real receipt. They are not part of the bootstrap apply decision.

E read D's 16 newly added offline guard tests and their committed passing report;
they were not rerun. No must-fix finding remains in the reviewed principal
wrapper. The production lane requires its own actual plans and final physical
copy acceptance; rehearsal receipts do not authorize reuse against production.
