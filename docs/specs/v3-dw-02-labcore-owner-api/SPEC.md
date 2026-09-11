# V3-DW-02 Labcore owner API

## Decision

Add a default-off, service-principal-only v2 registration lane for the strict
DW-01 Labcore sequencing-run owner contract. The three published POST paths
are alternate entry points to one atomic operation: exact-read and validate an
existing Dewey artifact, persist the Labcore external object, persist its typed
relation, and persist an immutable registration receipt in one TapDB
transaction.

## Safety boundary

The route surface is not mounted unless the explicit feature flag is true and
the service-principal allowlist is non-empty. The isolated YAML configuration
parses scopes as strict lists, rejects duplicate principal IDs or bearer tokens,
and never exposes bearer values through its effective view. Each allowlisted
principal is bound to exactly one tenant and must have the exact write scope.
The request tenant must equal that binding. Generic v1 external-object and
Bloom contracts cannot satisfy this lane. The generic v1 writers reject the
reserved `labcore` / `sequencing_run` identity and
`labcore_sequencing_run` relation, including generic relations to a reserved
Labcore object, so they cannot squat on or bypass the owner namespace.

The target must be a Dewey `sequencing_run` S3 prefix produced by the same
Labcore run. The V2 registration command adds an exact TestEUID around the
unchanged frozen DW-01 request and hashes those command bytes independently.
Its immutable `metadata.labcore_owner` evidence must exactly bind the request
tenant, command TestEUID, site, platform, dataset root/revision,
inventory, Labcore receipt, and expected file evidence. Rejection responses do
not return storage paths or raw material details.

## Idempotency and recovery

The V2 command digest is required in both the body and `Idempotency-Key`
header; the embedded DW-01 request digest remains immutable and unchanged. A
deterministic PostgreSQL transaction advisory lock over the global Labcore run
identity is acquired before reads, so a cross-tenant duplicate cannot create a
second authority. Concurrent identical requests return one authority/receipt
and divergent bindings serialize to a conflict. There is no file, memory, or provider fallback: the TapDB transaction
either commits the object, relation, receipt, and idempotency record together,
or rolls them back together.

The API handler is synchronous so FastAPI runs the transaction and any
advisory-lock wait in its worker threadpool instead of blocking the application
event loop.

The application-build TapDB surface registry conditionally attaches these
routes without eager package-import behavior. Its route class replaces FastAPI
validation detail with a closed error payload, so invalid body data never
reflects paths, file names, hashes, or other owner evidence to callers.


## Dewey 9.1.0 implementation amendment (2026-09-11)

The mainline implementation supersedes this branch-era packet's three aliases
and advisory locking. See `docs/labcore_owner_api.md`: one registration endpoint,
released TapDB natural claims, canonical XRF/receipt lineage, bounded requests,
strict explicit config and principal attribution. The v1 contract and valid v2
canonical command bytes remain unchanged. Production acceptance may use the
explicitly authorized synthetic fixture; automatic Labcore calling is separate.
