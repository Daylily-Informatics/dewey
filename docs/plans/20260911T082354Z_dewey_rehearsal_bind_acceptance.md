# Actual transition verification, bootstrap and binding-plan acceptance

**E accepts the fresh completed-transition verification, actual rehearsal
runtime bootstrap, and exact native bind apply below.** The bind disposition
was sent to O immediately after receipt checks; documentation was not an
additional gate. Release `10.1.1rc1`, the reviewed operator/runtime inputs and
both accepted SOP helpers remain unchanged. O alone executes live operations.

## Exact binding apply boundary

| Evidence | Reviewed value |
|---|---|
| Native bind-plan file SHA-256 | `f841c1221979b0c3412016e4acf2a330a3c59b857f3f5679420a443b1d544eac` |
| Native bind-plan seal | `e65fdff7d846d58730696f5e54cb34936d470d8073d25f0c04ac2606cc360f86` |
| Companion input file SHA-256 | `9d4fe78d5c8e45208a84cf856a1eafe69501bdbdd3ebe7ae22360b9e2ebc3c9e` |
| Companion input seal | `8560a114ba006ac634d2a026d7333e050b3482d2bec2a8e88e54339b9383da41` |
| Unchanged principal helper SHA-256 | `9921210bd5b3ee4fcc52f06184dd88a6efa986e23e608f3672ccffcd529372f2` |
| Immutable runtime config identity | `/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml` |
| Runtime role | `dewey_rehearsal_9`, OID 646337 |
| Exact target | `dewey_tapdb10_rehearsal_20260911`, OID 645854 |
| Authenticated operator | session/current user `dayhoff` |
| Managed schema | `tapdb_dewey_lsmcok1_local`, OID 28108, owner dayhoff/OID 16409 |

E independently recomputed the full 152733-byte native plan hash and seal,
companion seal, and both actual bootstrap result seals. All companion inputs
are exactly equal to the previously accepted bootstrap inputs and actual
bootstrap result inputs. The fixed runtime configuration, matching runtime
secret reference, separate operator credential reference, registries and CA
hashes remain unchanged. No credentials were read by E.

The binding inserts a new immutable scope with domain M, issuer dewey, tenant
NULL, `allow_global_rows: false` and the exact runtime path above. Existing scope
is NULL. Runtime IAM and operator IAM remain false. The operator overlay changes
only the previously reviewed operator fields in memory; it does not put them
in the runtime YAML or change the native recovery family's operator path.

The actual catalog contains 31 objects, 19 policies, 30 routines and 19 triggers.
All objects remain owned by dayhoff. The ten protected native tables have
enabled and forced RLS; `_tapdb_migrations` retains its declared tracking-table
exception. Operator policies name only owner OID 16409. Native catalog preflight
validates the complete canonical routine, policy and trigger contract.
E independently checked the plan's three security asset hashes against the
immutable released files:

| Asset | SHA-256 |
|---|---|
| `allocator_functions.sql` | `0c0897df273fc581a02f133f8dde043c38d3149486598618189c1ae4388acbe3` |
| `rls.sql` | `85144de81d7ec7d9f5a30b7776b78adb9dd46de08e6506a8c76a6c1ae46a9afd` |
| `tapdb_schema.sql` | `f174ac8100c84aba3ed29a74b35df36a39b63e0b296271a66aa777194aad1ca8` |

The exact granted set is seven writable native tables, three read-only native
tables, 15 positively classified runtime sequences, and 30 canonical routines.
Schema access is USAGE and database access is CONNECT. The runtime scope table
receives no runtime grant. Planned default privileges and existing default ACLs
are empty. Runtime and PUBLIC TEMP are revoked; existing operator TEMP is
preserved without an added grant. The runtime currently has no effective schema
CREATE or database TEMP.

All 20 generators and their recovery floors remain preserved. The five
generators outside the proven runtime grant set are GSE, GVR, SYS, TPX and XRF;
their inventory evidence lacks the matching runtime scope required by the
native binding contract. This is grant classification, not allocator removal.
The 15 granted sequences retain their exact committed positions, definitions,
owners, dependencies and prefix meanings. Native
`runtime_principal.py:613–665` owns that classification; lines 899–978 specify
the grant set and lines 1101–1226 enforce exact fresh-plan equality and the
resulting privileges.

## Actual bootstrap accepted

The actual bootstrap result file hash is
`bb1fae3f055b911adc388a7a7642da1de7b3c387436899f970b939b09724eccb`; native result
seal `259ebed9eccbd1cc2c4f4b5fa81f4e570d80f99acf3022ee176a494118ebe6cb`.
It reports `created: true`, `status: applied`, and links accepted bootstrap plan
seal `bba0522a8ae3e5f64a176928adbd10a43c4f6867bc235885d4e5bc67295b416b`.
The role is LOGIN with SUPERUSER, BYPASSRLS, CREATEDB, CREATEROLE, REPLICATION
and INHERIT all false, no memberships, and CONNECT only on the exact rehearsal
database. The native bind plan observes that same role/OID and role attributes.

## Fresh allocator verification accepted

C committed the already accepted transition helper as `928c24d`; its exact
SHA-256 remains
`0e2765067beb776dfe914a553d02ef8d2710723ff2582cc5fa56e43b2b6378a1`.
O's fresh native verification completed RC 0 at
`2026-09-11T08:18:13.995753Z`. E compared the complete actual receipt to the
successful committed-apply verification; they are exactly equal.

| Actual artifact | File SHA-256 |
|---|---|
| All 130 prior floors, 27336 bytes | `d4d902717ade64e13c90d0cc5ae1d19fc28dab023accabd31169dc69e66ee548` |
| Preparation and terminal family evidence | `ddd6160c4f1907844358bf3eaa10ad13ac030b4752f77da2d8430ea4d6e95a5e` |
| Native verification stdout | `858ff517ba01068374e6e5061bf25787f139c4542f6806839cb312958f13e03d` |
| Successful completion | `982e78abb5092c7784a25f31baaaf199734b16db57c1f1697004f5f85a6dd61c` |

The native verification seal is
`84c97198683d71494277cf05ccfb6df058481560d8c53a064b8855bb439c8eab`, with the
same current inventory seal
`584a01f80984c14cd15a79cff007b4e260fafd97481ab8f80b03aaae7c56e170`, `ok: true`
and no violations. All 130 prior records are unchanged and all 150 future
result floors remain retained. The original family-aware RC 1 is preserved as
documented in the preceding scope review.

## Remaining acceptance

Native bind must retain its fresh stale-plan comparison. Its actual result must
report `status: applied`, the exact plan link, `privileges_verified: true` and
`runtime_temp_denied: true`. Binding explicitly does not close or validate old
runtime sessions: the recorded session requirement remains unperformed by
bind. Fresh isolated runtime sessions, runtime-only authentication/scope and
privilege checks, eleven historical DGX template bindings and full image
acceptance remain subsequent gates.

L04/L09 now have actual completed allocator verification and constrained
bootstrap evidence, with exact binding apply cleared. Runtime binding results,
application and final production acceptance remain separate; O alone updates
the controlling ledger. No new census, tests, backup or package change was
required for this review.

[Machine-readable acceptance](20260911T051700Z_tapdb1011rc1_evidence/20260911T082354Z_rehearsal_bind_plan_acceptance.json)
has file SHA-256
`ca17c05904d4bc983c19dafaf381423ae5c94cbb25ffc259b94e4f2cf5b5a7f8`.
