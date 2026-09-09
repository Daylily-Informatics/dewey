# Dewey → QEO MultiQC package contract v1

## Ownership

Dewey owns artifact EUIDs and authoritative `artifact_set_member` lineage.
QEO owns ingestion, immutable source archives, all-table Parquet preservation,
and DuckDB query serving. HTML is a report presentation, not QC backing data.
There is no required Analysis Execution, sample, library, or sequencer identity.
Arbitrary QEO report associations remain a separate explicit input contract.

## One read-only route

`POST /api/v1/resolve/multiqc` accepts exactly `kind` (`artifact` or
`artifact_set`) and `euid`. An artifact reference must be the report member.
Resolution reads registered package lineage. Zero matches returns 404;
multiple packages returns 409 and requires an explicit package EUID. Broken
membership, changed checksum/size, and version-qualified S3 artifacts fail
closed. No path substitution, bucket scan, share creation, registration,
synchronization, template seed, or dispatch occurs in this route.

Response fields: `contract: dewey.multiqc-package/v1`, `artifact_set_euid`,
`complete_data_package: true`, `label`, and `files`. Each file has
`artifact_euid`, `role`, `relative_path`, `sha256`, `size_bytes`, and `url`.
URLs come from persisted artifacts, not client-provided URLs or copied parent
metadata. Package manifest identifiers are validated against exact authoritative
lineage on every resolution; the metadata is not a replacement relationship store.

Exactly one `report` plus either one complete `archive` (ZIP) or one or more
`data` files is required. Individual-file mode includes every listed member,
including the report and unknown tools/auxiliary files, in QEO's source archive.
Archive mode ingests the complete data ZIP; the HTML remains owned by Dewey.
The publisher attests completeness: neither service can infer that an omitted
file exists. No tool/module allowlist, inferred directory, required fixed matrix,
or reconstruction from the HTML is part of this contract.

## Explicit operator registration

`dewey qeo package-register --manifest /absolute/package.json --idempotency-key KEY`
uses the explicitly configured Dewey runtime. This command does not bootstrap
the service. All artifacts must already exist; the command creates one typed
artifact-set and its membership lineage atomically through Dewey's existing
TapDB backend. Same idempotency key/body replays; a changed body conflicts.

The input manifest has the response shape except it omits `artifact_set_euid`
and each file's `url` (these are supplied by Dewey). Do not invent artifact
identifiers. Obtain real artifact receipts and byte hashes from the owning
publisher. Relative paths must be exact, unique, safe POSIX paths. SHA256 and
byte counts are mandatory for every member. Registration compares recorded
artifact size/hash when available; QEO always verifies downloaded data bytes.
Missing registrations or hashes must be resolved explicitly by the publisher.

## Dedicated credential, no shared write token

`dewey qeo resolver-credential-create --token-output-file /absolute/new-token --lifetime-days 90`
creates an exclusive 0600 file, never prints the token, and reports only its
SHA256, expiry, principal, scope and file reference. This local command needs
no database or cloud bootstrap. Do not execute in the repository or commit
the token. Provision the real credential on the deployment host, not the Mac.

Configure Dewey with `DEWEY_QEO_RESOLVER_TOKEN_SHA256` and
`DEWEY_QEO_RESOLVER_TOKEN_EXPIRES_AT` from the receipt. Configure QEO with
`QEO_DEWEY_BASE_URL=https://dewey.day.lsmc.bio` and
`QEO_DEWEY_RESOLVER_TOKEN_FILE` pointing to the explicitly read-only-mounted
token file. Do not put the token in `DEWEY_API_BEARER_TOKENS` or reuse
`QEO_DEWEY_API_TOKEN` (the separate, default-off legacy event integration).
The reserved token namespace is rejected by general Dewey API authentication.
Missing/expired resolver configuration returns 503; wrong/missing token 401.

Only the resolver receives this credential. QEO downloads data separately
using its own explicitly approved S3 source permissions and allowlisted prefixes.
It follows no redirects and forwards no Dewey token to S3 or other hosts.
Revocation: remove/replace the configured hash and restart only Dewey.
Rotation: explicitly issue a new file and replace both sides; no hidden overlap
or fallback token. No periodic job or automatic credential rotation is added.

## Production handoff, not completed by local tests

Review exact source commits and GitHub-built image digests for both services.
The existing authorization permits one corrected QEO GitHub build. This Dewey
8.0.2 source tree contains CI but no standalone image-publish workflow; its
image build/deployment must be separately made explicit before execution.
Do not build images on the Mac or EC2, modify Dayhoff source/shared units,
change Aurora configuration, or rebuild/restart unrelated services.

Before live configuration: record current containers, QEO/Dewey-only mounted
paths, source allowlists, and rollback digests. Preserve the QEO-only boot-entry
exception; it does not authorize editing Dewey's shared boot entry. A Dewey
boot-entry amendment would require exact additional approval.

Then provision the credential, configure only the two services, register a
publisher-verified complete real package, ingest its actual report link in
QEO, and record authenticated query/export evidence. No real credential or
production package has been created by this source checkpoint.
