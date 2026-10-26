# Verify the completed sequence transition and retain future floors

Bounded operator SOP for exact TapDB `10.1.1rc1`, commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. O owns execution. E independently
accepted the actual receipt interpretation in
`20260911T081124Z_dewey_sequence_outcome_scope_review.md`, E commit `591063f`.
No package change, second advancement, sequence SQL, journal modification,
source reconnection, runtime binding or new backup is part of this operation.

## Actual evidence

| Evidence | Value |
|---|---|
| Reviewed native plan | `83f86ca0aae608b2de42147c68280534848029d057c7b60cec72eabeda7f2791` |
| Committed result seal | `8627fc06c629d2bc921e6f49370e1469e6db949ae9da086ff4aecf10d9c4217e` |
| Result file SHA | `bcdd9a30ef0265aca481ea70b0b9750fd6dd09e0130c9dc56f86e98e4104dff1` |
| Apply completion | RC 0, `2026-09-11T08:02:31.500288+00:00` |
| Current inventory | `584a01f80984c14cd15a79cff007b4e260fafd97481ab8f80b03aaae7c56e170` |
| Successful apply verification | `84c97198683d71494277cf05ccfb6df058481560d8c53a064b8855bb439c8eab` |
| Released fence | `ebb123f4b1463cba675224e0cc9e93c9d2ca7629b26d0f3de2af0c5634d8c72e` |
| Later family verification | RC 1; seal `3cd542a08a571676db9b589553789b4b02e5c4e7e1bc6f2d2e461d848be4c607` |
| Physical target | Rehearsal OID `645854`, server `10.0.2.148/32:5432` |

Released `sequences.py:751–756` explicitly distinguishes two lists:

1. `result.verification.floors` is **all 130** applicable source and prior
   attempt boundaries, exactly equal to reviewed `plan.floors`.
2. `result.floors` additionally retains **20** own planned-next reservations for
   **future** attempts/recovery. Current next values may equal their own new
   reservations. This complete list has **150** records and remains retained.

The later family verification combined those 150 with the original 38 external
source records, yielding 188. All 20 failures compare each unchanged available
next with its own newly retained future reservation. E reproduced both outcomes
from the actual receipts. The inventory seal did not change. Another advance
would create another set of future reservations and does not fix the scope.

## Operator steps

Use `scripts/dewey_sequence_transition_sop.py`, the existing protected operator
Python, and the same absolute immutable rehearsal capsule. O supplies the
independent review reference. Run through the existing targeted-sudo interactive
`ubuntu` session with its unchanged explicit AWS environment.

```bash
"$OPERATOR_PYTHON" "$SEQUENCE_SOP_SCRIPT" prepare \
  --capsule "$CAPSULE" --review-reference "$INDEPENDENT_SOP_REVIEW"
```

This performs only file/public-API validation and exclusive input creation. It
checks native seals, committed apply, exact plan/result/family/release/physical
target, complete terminal family history, and the exact 130/150 lists. It writes
`completed-transition-floors.json` and `completed-transition-preparation.json`
inside the existing output directory. The floor file is exactly
`{"floors": plan.floors}`: every record, provenance string, order and integer
remains unchanged. E's expected serialization is **27,336 bytes**, SHA
`d4d902717ade64e13c90d0cc5ae1d19fc28dab023accabd31169dc69e66ee548`.
O checks the actual file before the next operation.

```bash
"$OPERATOR_PYTHON" "$SEQUENCE_SOP_SCRIPT" verify-completed \
  --capsule "$CAPSULE" --review-reference "$INDEPENDENT_SOP_REVIEW"
```

The released command is `tapdb --config EXACT_COPY_CONFIG --json db sequences
verify --floors NEW_COMPLETED_TRANSITION_FLOORS --sequence-mappings
EXACT_EXISTING_MAPPINGS`. The omission of `--recovery-family` applies **only**
to this completed-operation claim. All 130 previously applicable family/source
boundaries are already present in the native list.

The helper requires fresh native RC 0 and equality of the **entire** verification
with the successful apply verification: same inventory seal, all floor records,
`ok: true`, empty violations and seal `84c97198...`. Journal heads must remain
unchanged throughout. Any difference stops the operation without advance/retry.

Outputs use a new `completed-transition-verify` stem: `.started.json`, `.stdout`,
`.stderr`, `.rc`, `.completed.json`. The original `sequence-verify` RC 1, stdout
and completion stay intact. No success marker is written for that failed call.

## Future exposure and final copy

After isolated testing, O stops rehearsal writers and ensures terminal journals
before requesting future exposure. Use the **new explicit** stage:

```bash
"$OPERATOR_PYTHON" "$SEQUENCE_SOP_SCRIPT" exposure-plan \
  --capsule "$CAPSULE" --review-reference "$INDEPENDENT_EXPOSURE_REVIEW"
```

This requires the new successful completed-transition proof, not the old failed
`sequence-verify` completion. Do not invoke the earlier lifecycle helper's
blocked `exposure-plan` stage for this SOP. There is no OR condition, fallback,
overwritten failure or manufactured native receipt.

The new stage calls native read-only `db sequences advance` with the **complete
unchanged family**, original external floor input, current inventory and all
current history. Its receipt is `exposure-after-completed-transition-plan.json`.
It does not apply the plan or stop writers itself. Preserve this plan and every
original result/floor/family journal. The final copy retains every floor and
every planned next from this complete exposure plan through the existing
reviewed C projection. Its own advance must strictly exceed those boundaries,
including all 20 new reservations retained here.

The no-reuse guarantee holds: the completed transition proves next values
strictly exceed every applicable source/prior-attempt boundary. Its newly
exposed next values become additional boundaries for every subsequent attempt,
copy or recovery. They are retained in full. Runtime setup and acceptance remain
later gates. E accepted the concrete helper's static source; actual new native
verification remains O/E's execution gate.

Validation: source/actual-receipt inspection and new script syntax/Ruff/diff
checks only. E's existing receipt/API checks are reused. C ran no repeated test
suite or live command.
