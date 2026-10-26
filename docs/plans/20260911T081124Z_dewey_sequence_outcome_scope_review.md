# Committed allocator outcome and verification scope

**E accepts the actual committed rehearsal sequence advancement and released
target fence.** The later family-aware verification failed because it included
the current operation's newly reserved next values. E reproduced both native
verification receipts exactly from the same actual inventory. No additional
advance or reconciliation is indicated.

This corrects E's earlier generic requirement for immediate family-aware strict
verification after each successful advance. That requirement was too broad.
The released `10.1.1rc1` implementation already distinguishes the current
transition's applicable floors from its reservations for future recovery.
The original RC 1 and all family receipts remain unchanged.

## Actual receipt decision

| Evidence | Independently rehashed file SHA-256 |
|---|---|
| Sequence result, 94937 bytes | `bcdd9a30ef0265aca481ea70b0b9750fd6dd09e0130c9dc56f86e98e4104dff1` |
| Apply completion | `77c44d7ced0f290145db5fce8cef442bf125a087dc70cdd5f364b0c01bace152` |
| Failed native verification stdout, 43470 bytes | `0f554cf52a9053e7046dccde5f64bfbb3fa51027fb24b3d6777559fec75e4fe3` |
| Failed verification completion | `9fcdc3b8ad9bc43f157665d7cefb9bb06e73cf59c5b463607fdb0cb2c6320881` |

Apply completed RC 0 at `2026-09-11T08:02:31.500288Z`. Its native committed
result seal is
`8627fc06c629d2bc921e6f49370e1469e6db949ae9da086ff4aecf10d9c4217e`, linked to
the exact accepted plan seal
`83f86ca0aae608b2de42147c68280534848029d057c7b60cec72eabeda7f2791`.
The allocator intent is `000013-20260911T080228Z`.

The released writer-fence receipt has seal
`ebb123f4b1463cba675224e0cc9e93c9d2ca7629b26d0f3de2af0c5634d8c72e` and links
the exact committed payload before its release envelope, seal
`3fc0215035c8c865746d89f09bfa53cc41d763f51c4f3c87f12a9099d34f3c23`.
Physical identity remains rehearsal OID 645854, `10.0.2.148/32:5432`;
config, domain, owner and copy-rooted family remain exactly accepted.
The restored database ACL contains only owner dayhoff's CONNECT, CREATE and
TEMPORARY privileges. Runtime binding is a later operation.

All 20 actual available next values exactly equal the accepted plan. Other
sequence fields are unchanged except `last_value`, `is_called` and
`allocated_floor`, which are the native allocator-state changes.
The actual post-apply inventory seal is
`584a01f80984c14cd15a79cff007b4e260fafd97481ab8f80b03aaae7c56e170`.

The successful apply's native verification seal is
`84c97198683d71494277cf05ccfb6df058481560d8c53a064b8855bb439c8eab`, with
`ok: true`, no violations and all 130 reviewed prior floor records. E validated
every complete native receipt seal and recomputed that verification using
the published public `verify_sequence_floors` function and the actual inventory.

## Why the subsequent check failed

The failed check completed RC 1 at `2026-09-11T08:03:35.084084Z` and reports the
same post-apply inventory seal. Its native receipt seal is
`3cd542a08a571676db9b589553789b4b02e5c4e7e1bc6f2d2e461d848be4c607`.
All 20 violations were reproduced exactly from its complete 188 floor records.

| Floor set | Records | Purpose |
|---|---:|---|
| Reviewed `plan.floors` and committed `result.verification.floors` | 130 | Boundaries this completed transition must strictly exceed |
| Committed `result.floors` | 150 | All 130 prior boundaries plus this operation's 20 reserved next values, retained for future attempts/recovery |
| Subsequent family-aware verification | 188 | The complete 150 retained result records plus the original 38 external input records |

E compared these lists exactly, including provenance and duplicates. For every
generator the failing maximum is its current operation's own new
`sequence_advance_intent` reservation, exactly equal to its current available
next value. There is no changed inventory, missing prior floor or unexpected
larger boundary hidden in these failures.

The release documents this directly in `daylily_tapdb/sequences.py:738–756`:
`verification.floors` contains prior applicable source/attempt floors, while
`floors` additionally retains each exposed planned next for future attempts or
recovery; current next may equal its own new reservation. The implementation
records those 20 reservations at lines 837–861 and verifies against the prior
plan floors and exact planned next values at lines 876–887.
`backup/recovery.py:335–360` intentionally retains intent/result floors after a
committed family operation. Another advance would introduce another set of
reservations; it is not the remedy for this completed-operation check.

## Bounded public verification SOP accepted in design

C owns the operator SOP/input preparation; E did not author migration tooling
or an operator floor file. The independently accepted procedure is:

1. Preserve the reviewed plan, committed result, released fence, full family
   history and failed verification. Require their exact hashes, native seals,
   physical/config/family identity and outcome links reviewed above.
2. Require `result.verification.floors == reviewed_plan.floors`. Copy that entire
   list of **130 records**, unchanged and in order, into a new document with the
   sole key `floors`. Do not use only the 38 source records or change any integer.
3. Run the public read-only command with the same configuration and mappings:

   ```text
   tapdb --config SAME_COPY_CONFIG --json db sequences verify \
     --floors NEW_COMPLETE_PRIOR_FLOORS_FILE \
     --sequence-mappings SAME_SOURCE_MAPPINGS
   ```

   O chooses the explicit new artifact/log paths through C's reviewed SOP. For
   this completed-transition check, omit `--recovery-family`; the prior floor
   document already contains the entire family history applicable to the
   reviewed operation. Public `cli/sequences.py:236–276` explicitly supports the
   optional family argument and performs a read-only current capture.
4. Retain the new real stdout and completion. Require RC 0, `ok: true`, empty
   violations, the same inventory seal `584a01f8…`, all 130 exact floors, and
   verification seal `84c97198…`. Unexpected drift stops this SOP for review.
   Do not retry an advance or relabel the failed receipt as successful.

For UTF-8 `json.dumps({"floors": plan["floors"]}, indent=2, sort_keys=True)` plus
one newline, E independently calculated 27336 bytes and expected file SHA-256
`d4d902717ade64e13c90d0cc5ae1d19fc28dab023accabd31169dc69e66ee548`.
This is a serialization expectation, not an E-created operator input.

All **150** committed result floors, the complete family and any later exposed
floors remain mandatory for every future advance, recovery and final-copy
exposure. This completed-operation verification does not discard or rewrite
that history, fabricate a family join, or weaken cross-copy requirements.
The original source stays closed; no new backup, sequence SQL, package change,
additional advance or new test suite is introduced.

## Review scope

This actual committed result advances L04/L09 evidence for native strict
allocator advancement and target-fence release. The fresh bounded verification,
runtime binding/authentication, isolated application acceptance and subsequent
final migration remain separate. O alone updates the controlling ledger.

E used local immutable source and actual receipt files only: zero database
calls, no remote journal replay, and no test suite. The public in-memory checks
validate these new actual receipts; they do not repeat earlier fixture tests.

[Machine-readable actual outcome review](20260911T051700Z_tapdb1011rc1_evidence/20260911T081124Z_rehearsal_sequence_outcome_review.json)
has file SHA-256
`3acc0ae48580277aa7a61eb79168c92d4801cba6659fbff5ec9b9dc1b8fe7d80`.

## Concrete C helper static acceptance

E reviewed all 205 lines of C's separate
`scripts/dewey_sequence_transition_sop.py`, SHA-256
`0e2765067beb776dfe914a553d02ef8d2710723ff2582cc5fa56e43b2b6378a1`, and accepts
that exact script for `prepare`, then `verify-completed`, under the unchanged
reviewed capsule. This clearance was sent to O before documentation commit.
No must-fix finding arose and E ran no helper or test.

The concrete helper validates the actual complete input/output references,
native result/verification/inventory/release seals, exact committed plan and
physical/config/family attribution. It requires a terminal unchanged full
family with the same 150 retained floors before projecting all 130 prior
records. The native verification uses the correct public arguments above,
requires exact equality with the successful apply verification object, and
checks unchanged family journal heads before and after the native read-only
capture. Output creation is exclusive; failed native stdout/stderr/RC remain
available without a fabricated success marker.

Its later `exposure-plan` operation explicitly requires
`completed-transition-verify.completed.json`, validates that proof and its
linked files, and requests a fresh public read-only sequence advance plan
with the complete recovery family and original external floors. It does not
reuse or rewrite the original failed `sequence-verify` completion. That
new exposure receipt remains subject to actual evidence review before
final-copy consumption.
