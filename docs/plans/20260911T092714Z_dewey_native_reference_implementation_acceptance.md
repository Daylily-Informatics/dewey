# Dewey native reference implementation and template-plan acceptance

Independent reviewer E accepts the D application commit and the exact rehearsal
template setup apply described below. This does not accept an unobserved
metadata conversion, XRF insertion, principal rebind or application launch.
O remains the sole live operator and controlling-ledger writer. E performed
source and local receipt review only; no live calls or test-suite reruns.

## Application implementation

D commit `0f3509cefe4df4a326403af9d2268ca8f2c6cda6`, tree
`f0481c594b8800b7e149e927126f5ebd85dc0533`, matches the final source previously
reviewed by E. Its worktree was clean when checked. There are no remaining
must-fix findings in this bounded implementation.

| File in D worktree | SHA-256 |
|---|---|
| `dewey_service/integrations/tapdb_external_references.py` | `f433e4a3382ba5738cf4d75de00c1d5e254e8f3420db2387b73357825503d298` |
| `dewey_service/tapdb_backend.py` | `9fa41b2a00b85dbe86a500ec6526462686c7186c986293534bd38e9603176d4b` |
| `dewey_service/services/external_objects.py` | `0af66ea5b8826715debe44b2590b5f873a898ec49993b77f9992d8ca16c44dd2` |
| `docs/plans/20260911T091833Z_dewey_native_reference_adoption.md` | `9d89efab1d34ff66e7d46d75270ef0ba0d703ac5a79be4bffcbceb9a30f3261e` |

The implementation preserves the native factory envelope and existing flat
application payload, rejects malformed envelopes, retires the graph-projection
writer and makes relation listing read-only. It derives reference targets from
the persisted external object and two authoritative DGX endpoint lineages.
Both lineage rows and both endpoint objects must match the relation's domain,
owner and tenant. Existing relations cannot recreate missing endpoints from
request fields: their persisted pair must resolve and match the requested pair.

The native assertion uses the persisted relation creation time and immutable
relation/lineage UIDs. Replays do not substitute a new actor or current time.
Private directory identifiers and all historical Ursa trigger keys remain
explicitly non-federated local identifiers; no invented tenant or public scope
is introduced. Historical idempotency responses remain preserved and are not
inputs to native reference construction.

E reused D's documented focused validation: 12 backend cases; the adoption,
read/search and native-DAG checks; the additional lineage-scope checks; and the
existing-relation corruption/replay cases. D documented the initially incorrect
test expectations and the narrowly corrected reruns. Ruff and diff checks
passed. These are local proofs, not proof of actual native database attachment,
privileges, concurrency, or a newly built/deployed image.

## Exact template setup apply

Actual read-only plan retained in this worktree:
`20260911T051700Z_tapdb1011rc1_evidence/rehearsal-xrf-template-plan.json`
(4,694 bytes), SHA-256
`9be5da6144d9f37889fd5c01c00ab2f670a7a09b55344a4ed914c67d58484301`.

The original helper's read-only attempt failed before writing a plan or intent:
the unnormalized config port was a string while native `physical_target`
requires the validated integer port. The bounded fix invokes public
`validate_target` before `physical_target`; it changes no target value. The
failed evidence and original helper remain retained by O.

The accepted corrected helper is SHA-256
`a59c18d74d3ebf251e418c79beb5597fcac42fba706a0f54512578e6ed14cdd9`,
staged as `dewey_xrf_template_setup_port_fix.py`. E accepts only the same
arguments as the reviewed plan, with operation `apply`, the exact reviewed
plan SHA-256 and an explicit independent review reference.

| Bound field | Reviewed value |
|---|---|
| Target database / OID | `dewey_tapdb10_rehearsal_20260911` / `645854` |
| Physical server | `10.0.2.148/32:5432` |
| Domain / owner / schema | `M` / `dewey` / `tapdb_dewey_lsmcok1_local` |
| Operator config SHA-256 | `9208dde2d25577ff06679e2bd19a37870ddc1c5d3039edc11dd31f3da8f53520` |
| Control config SHA-256 | `42491d0bf321d4d8027ef52918a1396e4e4c7f2c7bdecdabd82449b86b87686a` |
| Actor | `dewey-tapdb10-migration` |
| Original templates / matching scoped templates | `22` / `0` |
| Expected inserted / overwrite | `2` / `false` |

E independently reproduced both canonical definition hashes from the installed
exact `10.1.1rc1` public core loader. They match the plan: opaque
`a7f1ce51946c25e452be0346d49c76b0f0d1fd9e98c2924e7554670a45218263`
and tapdb_object
`319725fef0e110d7605af7b093e6749d16ea55ba8e9158d64778a28554fe2a65`.
Both bundled source-file hashes also match. This was a local artifact hash
comparison, not a database call or test-suite rerun.

The exact source freeze, stopped old container, stopped candidate, registry
hashes and dependency hash match the retained plan. Before writing, the helper
rechecks the entire plan, exact physical copy and absence of other sessions.
It invokes public `seed_templates` for only the two bundled M/dewey XRF
definitions with `overwrite=False`. Before commit it requires exactly two new
canonical rows, zero updates, and preservation of every original template's
whole-row hash. No runtime grant or XRF instance is part of this operation.

Acceptance after apply requires the committed result matching this plan,
22 unchanged original row hashes and exactly two new canonical templates.
The subsequent native principal binding plan remains a separate review.

## Metadata helper source acceptance

E inspected metadata helper SHA-256
`d99d763572d7fbc350a8f296051232539c1caca0136fcee0f9a36b53e36b9579`.
It is unchanged in C commit `78a0608ebad2fd37e9dff653d52e9c47be6d57c9`,
tree `acbb0d5e624ed2fe8f5fa9c8af0c2fc8629f40cf`. E accepts this exact helper
for the next read-only metadata plan; the actual apply remains separately gated.
Its exact plan membership, original cell/precision checks, transaction timestamp,
audit attribution and new-row hashes, source freeze and candidate/session guards
are present. Native `identity_inventory.py:520-556` hashes the complete
PostgreSQL JSON row after `parse_float=str`, keys the receipt by the primary-key
list hash and exposes numeric `identity.uid`; this matches the helper's audit
serialization and later fresh-inventory comparison.

No concrete must-fix was found. E read the final SOP
`20260911T092832Z_dewey_metadata_conversion_sop.md`, SHA-256
`95314366f6f4999d4e381381744a5ab2dbaed2c433ebc1cc69ff0f8ddb1e8fe0`,
and reused C's eight new pure conversion/manifest guard tests, which passed once.
Ruff and syntax checks passed. No database-test or actual conversion claim is
made from those local cases. The SOP correctly identifies 13,214 changed
original rows and 26,428 expected attributed audit additions.

Apply acceptance must bind to the actual read-only plan. Its native before inventory
must be fresh after template setup and any principal rebind, so this separate
metadata manifest does not silently authorize earlier setup changes. The
existing schema-only preservation manifest cannot authorize these new changes.

The controlling metadata/XRF constraints remain in
`20260911T090558Z_dewey_metadata_contract_acceptance.md`. Native reference
attachment, native audit/DAG acceptance, preserved original data and allocator
exposure, and actual image/read/write/replay evidence remain required later.
