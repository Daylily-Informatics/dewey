# Independent native copy lifecycle review

E source review recorded 2026-09-11T07:09:26Z. The controlling Dewey ledger
remains owned by O. This review changes no migration implementation, immutable
TapDB package, release tag, database or service.

## Disposition and exact inputs

**Accepted with the subsequent CLI-mode correction documented below.** The
initial review missed that schema migration rejects global JSON mode. Actual
preflight failed at that command-contract check, before database access; O
corrected only command construction. The corrected staged capsule is accepted
for native copy verification, family capture and migration preflight. Both
mutation stages remain separately gated by the actual independently reviewed
plan file SHA-256 and review reference. Static capsule acceptance is not
acceptance of an unobserved migration, allocator result or deployment.

| Reviewed input | Exact identity |
|---|---|
| C script | `/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-data-migration-20260911/scripts/dewey_copy_native_lifecycle.py` |
| Script commit | `92ac3f9` |
| Script SHA-256 | `264fee93e0d450841163876b438c2cc8d4d7742a198a2940de511c327a3b52f7` |
| Corrected O script SHA-256 | `e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407` |
| C instructions and new validation | `docs/plans/20260911T070212Z_dewey_native_copy_capsule.md`, through C commit `763fa74001fd63ba0d4e772189922582e0f6177a` |
| Instructions SHA-256 | `8c65b6f380b127eacde7cf5faed9fd7c459ebce97648f308ea069fcc348bdfec` |
| Released native implementation | TapDB `10.1.1rc1`, `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c` |
| Actual copy receipt SHA-256 | `2e477de116715b8c42c127618188d9607ac26826fb97453059b7921dd6c6ba7c` |
| Actual rehearsal identity | `dewey_tapdb10_rehearsal_20260911`, OID 645854, operator/owner `dayhoff` |
| Source identity | `dewey_prod`, OID 16749; continuously closed after the retained pre-gate cutoff |
| Control identity | `postgres`, OID 5, same observed Aurora server |
| Mapping SHA-256 | `5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8` |
| Migration conversion manifest SHA-256 | `af99535d9328b6de1e62b5a3758b36dbcd75ec7aa046f1663d16a8efa25261b8` |

The actual copy result is independently accepted in
[the copy review](20260911T063007Z_dewey_rehearsal_copy_review.md). The exact
native configuration, provider, principal and runtime path requirements remain
in [the execution checklist](20260911T060545Z_dewey_native_execution_inputs.md).

## Source-backed checks

| Boundary | E inspection and implication |
|---|---|
| One operation at a time | Script lines 242–382 selects one explicit stage. Both applies require a reviewed actual plan file SHA and reference before invoking the native command. No automatic follow-on apply or failure retry exists. |
| Fixed operator capsule | Lines 145–190 require exact keys, approved distinct database/OID, canonical UUID, existing canonical paths, pinned config/copy/next/mapping/manifest/control/provider files and explicit extra-exposure list. Owner, schema, domain, repo, host and Aurora cluster must match. O must retain the reviewed script bytes and the same complete capsule file across stages. |
| Real capture provenance | Lines 262–278 consume the already completed native capture and its actual terminal RC 0. They do not invent a helper completion record or recapture source. Complete source/identity/sequence seals are checked and source/copy physical OIDs are explicit. |
| Relocation-only copy | Lines 278–292 compare every sequence inventory field except exact target, physical target and native seal. The native identity manifest contains only the actual copied target plus empty tables/added_tables. Native `identity verify --before ... --after ... --conversion-manifest ...` checks the explicit config and all original identity evidence. |
| New family | Lines 293–311 require successful copy verification, an unused family path and empty explicit journal root. Native inventory receives all four new-family flags and source version. The new historical capture must equal the untouched identity/sequence evidence and contain the exact native family descriptor. The operator config path remains immutable family identity. |
| Migration lifecycle | Lines 301–325 use native `schema migrate --dry-run`, then explicit `--apply --preflight-receipt` with the same historical copy, mappings, family and journal plus native target/control/provider fencing. Post-capture requires native migration, recovery completion and writer-fence release fields. |
| Migration comparison | Lines 326–331 use only the already accepted narrow same-copy conversion manifest. E still reviews actual catalog/cell differences; broad table-level schema allowances do not authorize unrelated changes. |
| Source floors | Lines 332–352 bind the original next-plan inventory SHA to the retained frozen source sequence receipt. The floor document is an operator input, never called a native receipt. It preserves assigned/allocated floors, all retained floors and every native planned-next integer unchanged, with original file/native hashes in provenance. |
| Family exposure staleness | Lines 119–142 call public native validators and rebuild each plan with the full current family journals. Exact plan equality is required; terminal family history is checked first. Changed retained history cannot silently reuse an earlier exposure plan. |
| Native advance/verify | Lines 353–367 use the exact public floor, mappings, family, plan, control, provider and journal arguments. Native apply recaptures the target and rejects stale inventory, mappings, floors or family state. Native verification has no receipt flag; stdout and actual RC are retained. |
| Evidence retention | Lines 196–201 rehash required-stage inputs/outputs against the same capsule hash. Lines 212–238 exclusively create protected command/RC/stdout/stderr/completion files and require declared native outputs. Failure preserves partial evidence and journals. |

Released source checked directly: `cli/identity.py:87–260`,
`cli/db.py:1536–1830`, `cli/sequences.py:35–277`,
`backup/source_contract.py:18–115`, `backup/recovery.py:180–425`, and
`sequences.py:454–578`. Source-contract checksums use the same public
`content_hash` excluding `sha256` as `validate_receipt`; the script's generic
seal check therefore matches the native source-contract seal. Native consumers
also perform their full owning contract validation. The post-migration version
`10.1.1rc1` is permitted as an explicit operator-declared version; migration
asset/receipt evidence proves actual schema application.

## Reused new-helper evidence

C committed ten new offline guard/projection tests in `baf9e10` and recorded
their passing result; E read their scope and did not rerun them. The stubbed
projection test is not native RC acceptance.

C then used E's existing noneditable exact-RC interpreter for one newly
informative in-memory API check against actual mapped source sequence seal
`903928e63a8cd22f078f429d3aa55c125b48fc212925a29cbff91f0c41482cc0`.
C reports that native validation and plan construction, this helper's unchanged
projection, and a second native plan preserved all 20 prior planned-next
boundaries in 38 floor records; all 20 new planned-next values strictly exceeded
their original boundaries. E read the committed result in `763fa74`; it is
author-executed evidence, not a live advance or an E rerun. Family-bearing actual
plans remain their separate operator acceptance. Previous 123/301 native suites
and application tests remain reused without repetition.

## Required actual-stage acceptance

1. Retain the actual immutable capsule hash, current script hash, real copy
   capture RC and exact native target-only verification output. Require
   `ok: true` with no undeclared differences and complete generator equality.
2. Review the new native family origin/config/OID, explicit journal root and
   actual migration plan. Expected pending assets are the eight already
   reviewed September migrations; no bootstrap, remint or undeclared source
   cell conversion is authorized.
3. After apply, review native recovery/release success and the exhaustive
   before/after identity comparison. Restrict schema differences to those
   assets, eight new tracking rows, NULL original `identity_key` cells and two
   empty new tables before binding. All other original cells stay preserved.
4. Review the actual external floor input and native sequence plan, including
   every original source boundary and complete current copy-family history.
   Require strict native verification after the separately reviewed apply.
5. Capture rehearsal exposure only after rehearsal writers stop and sessions
   and journals are terminal. Keep that copy stopped thereafter. Final copy
   inputs include its explicit hashed exposure plan; final native family is new
   and rooted in the actual final copy, with no fabricated external-copy join.

The original source remains closed and its old container stopped through
rehearsal/final cutover. No source reconnect, new backup/snapshot, runtime
bootstrap/binding or service start is authorized by this capsule review.
The user's inbox/outbox preservation, acknowledgement and replay waiver is
retained; do not add a queue acceptance gate. All other identity, data and
allocator preservation requirements remain in force. Existing Aurora recovery
protection and the retained current-member recovery plan remain the operational
recovery posture.

## Actual untouched-copy parity accepted

E read O's safe `rehearsal-copy-parity.json` bundle, file SHA-256
`f6df7bba369a43edf9cd62d4ba844e9914ec549c6a634f22b66bb83f02f9b06f`, and
`rehearsal-native-capsule.json`, file SHA-256
`7fbe0e00e5557bde7ffb2afaa50606ade8c391136a5ce77eb95fd7afd89f001d`.
Both are durable under the controlling worktree's
`docs/plans/evidence/20260911_dewey_rc_inventory/`.

The native `tapdb-identity-verification/v1` result has `ok: true`, no
violations and native seal
`27ad51d64a5c05c9537126c2b92dcb02d7f590fc224566e48a02181bda229a50`.
E independently recomputed that native seal and the supplied stdout file hash;
the latter matches the actual completed-command record. Completion is
`2026-09-11T07:08:53.484986+00:00`, RC 0. Its before identity is the accepted
source seal `4a4d2df17d60f3caacd0b6decd3cee8ebc6263a9ad46b8908fb168b79cd2164f`;
the copied identity seal is
`676bee3e89b76dd4a0c2ac0b79b8e1580a5e92c8b31ffc01d9b772fcc6f5bbb2`.

The same capsule hash appears in both the real completion and the operator's
full generator comparison. All 20 generators are equal except for explicit
target/physical relocation. Source sequence seal is the accepted `903928e6...`;
copy sequence seal is
`2add38618cd555a4b23a17f3ace437a2730df6040e3414f4947fadce0d1add85`.
The completed command's original cutoff file hash is the retained
`c8d8d02e4ee93a6e615b960a20fa761e0456ba2a4d2a6318107f1441583b79f3`;
its copied full receipt file hash is
`bb79197709f0adf4b38da973885b3609672e4458d92c33d3b4d9df235f85ba32`.

**Independent E acceptance:** Source-to-untouched-copy identity preservation
and complete generator equality pass for the exact reviewed relocation. The
immutable capsule explicitly selects family UUID
`bfb30029-5dd1-42ec-8bf8-3094e78ae2f6` and new journal root
`/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-native-journal`.
Family capture and actual migration preflight remain their next separate
results; this acceptance does not claim their completion. The large private
source/copy receipts were not requested or recaptured by E.

## Later final-copy SOP draft

E also read O's separate `scripts/dewey_final_copy.py`, SHA-256
`a85dabc1a04e021b0afa6c7e781b9d6a7bd70637e259a40be9b59c609829501b`, with imported
reviewed helper SHA-256
`d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`.
No must-fix static finding remains for preparing its later read-only plan.
It checks the continuously closed source, no source sessions, exact stopped
container and unchanged source physical identity through the operator control
connection; the fixed final database must be absent. The three actions create
`dewey_prod_tapdb10` closed from the frozen source, revoke PUBLIC CONNECT/TEMP,
then open and verify owner-only admission. It does not reconnect source or
create a backup.

The draft binds its actual control/replacement config, source receipt,
script/helper, exposure-file hash and acceptance reference into the plan and
compares the complete fingerprint before apply. The exposure file is hashed,
not native-validated by this SOP itself. Therefore its later exact apply
acceptance must identify the independently accepted terminal rehearsal
exposure result after rehearsal writers stop, as already required by the
capsule instructions. No final-copy plan or apply has been accepted from this
draft review alone.

## Actual migration preflight CLI-mode failure and bounded correction

The initial static review above incorrectly accepted unconditional global
`--json` for migration. O's actual first `migration-plan` invocation returned
**RC 2**, empty stderr, and this command-contract failure on stdout:

```json
{"error":{"code":"contract_violation","details":{"command":"db/schema/migrate"},"message":"JSON mode is not supported for this command."}}
```

O confirms no `migration-plan.json` native receipt exists and the native journal
remains empty. This is a wrapper argument failure, not a TapDB migration
failure. Tagged `cli/_registry_v2.py:11–22` registers global JSON support for
identity, sequence and drift commands but not schema migration. Installed
`cli-core-yo==2.1.1` raises this exact failure in `app.py:386–420` during root
preflight, before runtime setup or native command callback. Therefore this
specific rejection never enters `db_migrate` or its database/fence/journal path.

E inspected O's exact correction against the reviewed C script: choose an empty
global-mode argument list only when the command prefix is
`db schema migrate`; otherwise retain `--json`. The authoritative migration
output remains the explicit native `--receipt` file. No source, family,
configuration, provider, floor, manifest or native CLI argument changes.

Corrected script SHA-256 is
`e663fe49a9c8e27d8109b195d34b22d1d7f1414d5df6626d4a7fafe884c69407`.
O stages it under a new `dewey_copy_native_lifecycle_cli_fix.py` filename,
preserving the original script. The failed generic `.started`, `.stdout`,
`.stderr`, `.rc` and `.completed` files are retained in the explicit
`failed-migration-plan-json-mode` evidence directory with their relocation/hash
index. No native receipt or journal history moves.

**E disposition:** The corrected command construction is accepted. Repeat only
the failed dry migration-plan invocation using the unchanged capsule and
historical copy/family, with new invocation logs. Preserve the first failure;
do not rerun copy capture/parity/family capture or any previous test suite.
The actual resulting native plan still requires its normal independent apply
review. No TapDB package change or release is required. E's original static
signoff is superseded on this single CLI-mode point.
