# Exact scoped XRF template setup

O stopped candidate `c6406b8ffb40` before this work; source remains continuously
closed. This C-authored SOP requires E's static and actual-plan acceptance.
It creates no backup, restarts no process and edits no existing template.

Script: `scripts/dewey_xrf_template_setup.py`, SHA-256
`a59c18d74d3ebf251e418c79beb5597fcac42fba706a0f54512578e6ed14cdd9`.
Stage under `/home/ubuntu/dewey_ops/tapdb101-20260911/` alongside the already
accepted `dewey_rehearsal_copy.py` SHA `d7a316eb10e9788e8f5a0d7459845c31a52b2b813d7584c8f43323a0cc121733`.
Use the installed exact RC operator Python and the existing targeted-sudo
interactive `ubuntu` invocation with its explicit AWS environment.

```bash
C_PY=/home/ubuntu/dewey_ops/tapdb101-20260911/venv/bin/python
C_SETUP=/home/ubuntu/dewey_ops/tapdb101-20260911/dewey_xrf_template_setup_port_fix.py
C_TEMPLATE_PLAN=/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/rehearsal-xrf-template-plan.json
```

O supplies `C_CANDIDATE_CONTAINER` as its exact already stopped candidate name or
full ID and an explicit `C_ACTOR` for real DB audit attribution. Do not use the
short image version as a guessed container identity.

```bash
"$C_PY" "$C_SETUP" plan --lane rehearsal --target-oid 645854 \
  --candidate-container "$C_CANDIDATE_CONTAINER" \
  --receipt "$C_TEMPLATE_PLAN" --actor "$C_ACTOR"
```

The plan performs only reads and writes a new operator plan file. It verifies
the closed original source, frozen copy receipt, stopped exact candidate and
absence of every other target DB session. It records exact target/config,
registry, installed core-source and helper hashes. Its operator view inventories
all original template row hashes and checks these exact M/dewey coordinates:

- `reference/external_identifier/tapdb_object/1.0/`
- `reference/external_identifier/opaque/1.0/`

Both definitions must come from the immutable RC's bundled core loader, with
prefix XRF. Existing exact rows are preserved; divergent/deleted/ambiguous scoped
rows fail. Runtime-visible absence is not substituted for this operator check.
With the observed untouched 22-template baseline and both scoped rows absent,
expect two new templates. E reviews the actual plan before apply.

```bash
"$C_PY" "$C_SETUP" apply --lane rehearsal --target-oid 645854 \
  --candidate-container "$C_CANDIDATE_CONTAINER" \
  --receipt "$C_TEMPLATE_PLAN" --actor "$C_ACTOR" \
  --reviewed-plan-sha256 "$C_REVIEWED_TEMPLATE_PLAN_FILE_SHA" \
  --review-reference "$C_TEMPLATE_REVIEW"
```

The script rebuilds the identical plan, then calls public `seed_templates` with
only those two bundled definitions, `overwrite=False`, domain M, owner dewey
and the exact configured registries. It requires every original row hash to
remain unchanged and both resulting scoped templates to match the native
canonical contract before commit. Public prefix provisioning verifies an
existing allocator or provisions/annotates the native generator; it never
repairs an existing counter (`sequences.py:989`). DB-generated TPX/audit
identities and all consumed sequence values are retained. The template result
is written only after the actual transaction commit returns.

Outputs use the plan stem plus `.apply-started.json` and `.result.json`.
Existing outputs stop the SOP. An ambiguous failure may have consumed sequence
values; O must retain its evidence and capture allocator state before deciding
recovery. Never delete markers or blindly repeat apply.

Next: native principal bind plan/apply against the same fixed runtime config
path, refreshing grants for the now present XRF templates/generator. Keep the
existing family/operator config unchanged. Obtain a fresh native identity
inventory after setup/bind for the subsequent metadata conversion baseline.
Then exact metadata conversion and runtime-scoped native reference creation
run under their own reviews. All original data and native journals remain.

For final, use lane `production`, the actual final OID, explicit stopped final
candidate identity and a new final plan path. Its first native allocator
advancement must precede these new template/reference/audit allocations.

New local validation only: exact installed RC loader returned both canonical
XRF definitions; the all-template JSON projection compiled with PostgreSQL's
dialect. Script AST, Ruff and diff checks passed. No broad/native test suite,
live query or mutation was run by C.

O's first read-only plan with the original `df765690...` helper failed before
any plan/intent/template write: native `physical_target` rejects an unnormalized
string port from `get_db_config`. The bounded correction passes the constructed
target through public `validate_target` before physical verification. Preserve
the original helper and diagnostic receipt; stage the corrected hash above
under the explicit `_port_fix.py` filename. A new exact-RC offline check confirms
the observed string `5432` becomes integer `5432`. An initial check incorrectly
expected an unprovided optional `server_port` key; the corrected check verifies
only the actual provided port. No deployment or package change is involved.
