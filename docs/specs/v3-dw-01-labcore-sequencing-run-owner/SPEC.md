# V3-DW-01 Labcore sequencing-run owner reference contract

## Outcome

This task adds an inert, provider-owned reference contract for the future
Labcore sequencing-run registration and artifact relation lane. It does not add
or register a route, persistence model, allowlist, client, writer, or service
integration. Scaffold issue `#146` tracks delivery because Dewey Issues are
disabled.

## Compatibility boundary

- Existing generic external-object, Bloom-owned sequencer-run, artifact, and
  analysis-result contracts, routes, storage behavior, and fixtures remain
  byte-for-byte unchanged.
- The new model is not imported by Dewey application or service startup code.
- Owner `labcore`, object type `sequencing_run`, relation
  `labcore_sequencing_run`, and target `artifact` are exact literals. Bloom,
  Atlas, aliases, unknown keys, metadata bags, lifecycle state, and PHI-shaped
  fields fail validation.
- The contract is evidence only. It cannot create an external object, relation,
  artifact, or other mutable authority until a separately reviewed V3-DW-02
  implementation supplies disabled, allowlisted routes and persistence.

## Identity and evidence

The owner reference binds one exact Labcore sequencing run to one Dewey artifact.
`external_object_id` must equal `labcore_sequencing_run_euid`. Tenant, processing
site, ILMN/ONT platform, normalized S3 dataset root, dataset revision,
destination inventory hash, Labcore binding receipt ID/hash, target artifact,
and non-empty immutable expected-file evidence are required. `dataset_revision`
and all evidence hashes are lowercase SHA-256 values; no mutable status is part
of identity. Both model levels are frozen and `expected_files` is retained as
an immutable tuple after validation, so bound hash evidence cannot drift through
top-level, nested, or collection mutation.

## Dewey canonical request-hash domain

The hash domain literal is
`dewey.labcore-sequencing-run-owner.request/v1`. It is a required field inside
the hashed payload. Canonical bytes are UTF-8 JSON produced from the normalized
contract after excluding only `request_sha256` and `idempotency_key`, with keys
sorted by Unicode code point, no insignificant whitespace, and non-ASCII
characters escaped (the existing Dewey `json.dumps(..., sort_keys=True,
separators=(",", ":"), ensure_ascii=True)` convention). Array order is
preserved. The required request hash is SHA-256 of exactly those bytes, and the
idempotency key must equal that digest. The committed PHI-free golden vector
publishes the normalized object, exact canonical bytes as base64, and digest
for downstream cross-language consumers.

## Scope and follow-on

V3-DW-01 contains only the strict Python reference model, generated JSON Schema,
golden vector, focused compatibility tests, and this specification. V3-DW-02
must separately design and review route authorization, tenant enforcement,
idempotent writes, TapDB persistence, allowlisting, service registration,
deployment, and rollback before any runtime use.

## Validation

Acceptance requires golden/schema parity, strict negative tests, existing
generic-owner and Bloom compatibility tests, Ruff, Bandit, the full pytest
suite, package build, a five-file diff audit, source/test size audit, secret
scan, and proof that no runtime module imports this reference contract.

## Implementation checkpoint (2026-08-20)

The five-file inert contract is implemented against `jemdev10` commit
`dea0009b743ad5b627177acdf21c87dd5c1d67c1`. Focused contract plus existing
generic-owner/Bloom compatibility tests pass; all 394 non-browser tests pass;
Ruff check, focused Ruff format, Bandit, package build, schema/golden/hash,
five-file scope, legacy-blob, size, import-scope, and secret checks pass.

Two repository-wide validations remain external to this five-file change. Full
pytest reaches 393 passing tests but cannot construct its two E2E fixtures
because the activated Playwright 1.62 environment lacks required Chromium
revision 1234; this task did not install an additional browser. Repository-wide
Ruff format also reports the pre-existing `dewey_service/services/sharing.py`
line 526 at the unchanged base as needing format. The two new Python files pass
the same format check. Neither unrelated baseline condition is changed here.
