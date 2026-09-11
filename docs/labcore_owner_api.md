# Labcore sequencing owner API (Dewey 9.1.0)

Jameson's PRs #6 and #7 and transaction hardening #8 are integrated on main.
This is the Dewey endpoint; automatic Labcore calling remains a separate task.

Use only `POST /api/v2/sequencer-runs/register`. Send the unchanged v1 owner
request inside the strict v2 command, with TestEUID and matching canonical
`command_sha256` / body idempotency key / `Idempotency-Key` header. Canonical
helpers live in `dewey_service.labcore_owner_command`. The two old proposed
alternate endpoints are not mounted. New registration returns 201; identical
replay 200; conflicting run ownership 409. Authentication requires the configured
Labcore bearer, matching logical tenant, and `dewey.labcore-owner.write/v1`.

The target must already be a persisted Dewey sequencing-run artifact with the
exact Labcore producer, test/site/run, dataset and inventory evidence. Bloom's
sequencing run, OWY's pickup and Labcore's test-bound run are distinct identities.
Labcore owns its PostgreSQL run record; Dewey represents that external identity
with a typed opaque XRF and authoritative lineage, not a fabricated TapDB EUID.

Global native claims reserve each Labcore run across logical tenants, including
soft-deleted objects. Claim, native reference, relation, attributed receipt and
idempotency result commit together. Receipt endpoints resolve through lineage.
The runtime requires existing templates and privileges; startup does not seed.

Configure `labcore_owner.api_enabled` and the explicit `service_principals` list
in the named Dewey YAML config, using `dewey --config /absolute/path config edit`.
Each principal has `principal_id`, `bearer_token`, `tenant_euid`, and a `scopes`
list. Bearers must differ from general Dewey API credentials. Keep secrets in
protected deployment config/secret management, never Git. Missing files, malformed
configuration or enabled-without-principals fail clearly. Explicit environment
overrides are `DEWEY_LABCORE_OWNER_API_ENABLED` (exactly true or false) and
`DEWEY_LABCORE_OWNER_SERVICE_PRINCIPALS` (JSON array). Config status redacts tokens.

Requests are bounded before JSON parsing at 16 MiB, then at 50,000 expected files
and 1,024 UTF-8 bytes per relative path. Oversized bodies return 413; invalid
commands return a redacted 422. No truncation or hash rewriting occurs.

For controlled acceptance with no real Labcore record, the user authorized a
clearly labelled synthetic tenant/run/test. Persist the Dewey artifact through
Dewey, use its real allocated identity, and retain the canary receipt. This does
not establish a real Labcore workflow. Do not grant the acceptance token to the
live Labcore service. A later caller task must bind its real tenant and actor,
implement the sequencing trigger and durable retries, and persist receipts.

Rollback: disable this feature in explicit configuration and recreate Dewey's
process. Retain committed objects, receipts and allocator state. No database
restore, identity reuse, or Labcore ECS deployment is involved.

## Caller follow-up

The existing Labcore ECS deployment has no Dewey caller credentials configured.
Its sequencing persistence models a `SequencingRun` attempt beneath a branch,
`SequencingRunMember` test membership, and `SequencingRunArtifactBinding` evidence.
The current Dewey command binds one exact TestEUID into a global run claim; a
second different TestEUID for the same run conflicts. Before adding an automatic
caller, reconcile that contract with any Labcore run containing multiple tests.
Do not silently pick a test or repurpose a Bloom/OWY identifier.

The caller task must select the real trigger and tenant, supply a trusted existing
artifact and binding evidence, issue the exact v2 canonical command, persist the
returned receipt, and retry the same command after an ambiguous acknowledgement.
Rotate/configure a real dedicated principal when that caller is ready. The
synthetic acceptance principal is not a production Labcore integration token.
