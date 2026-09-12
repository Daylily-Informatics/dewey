# Dewey 10 implementation crosswalk

The approved execution ledger is `20260912T070011Z_dewey10_ux_registry_s3_ledger.md`.
This crosswalk describes implementation work; it does not establish production
acceptance or authorize tests. No tests, lint, coverage or CI campaign is run.

| User operation | Authoritative public API | GUI | User CLI |
| --- | --- | --- | --- |
| Resolve an Object, Prefix or Set EUID | GET /api/v1/records/{euid} | Open EUID; record detail | dewey artifacts get EUID |
| Register one artifact or explicit set | POST /api/v1/records | Add | dewey artifacts register --manifest FILE --idempotency-key KEY |
| Inspect prefix or set contents | GET /api/v1/records/{euid}/contents | Record contents | dewey artifacts contents EUID |
| Request authorized object delivery or member manifest | POST /api/v1/records/{euid}/access | Download / Access manifest | dewey artifacts access EUID |
| Edit arbitrary metadata | PATCH /api/v1/records/{euid} | Metadata editor | dewey artifacts update EUID --changes FILE |
| Transfer ownership | PATCH /api/v1/records/{euid}/owner | Owner control | dewey artifacts owner EUID --email EMAIL |
| Isolated report preview with authorized relative assets | POST /api/v1/records/{euid}/preview | Preview report | dewey artifacts preview EUID |
| Archive registration, retain bytes | POST /api/v1/records/{euid}/archive | Registration lifecycle | dewey artifacts archive EUID --confirm |
| Manage independent metadata/download policies | PATCH /api/v1/records/{euid}/permissions | Manage permissions | dewey artifacts permissions EUID --policy FILE |
| Add/remove set members | POST/DELETE /api/v1/records/{euid}/members | Set detail | dewey sets add-member / remove-member |
| Create stable authenticated share | POST /api/v1/records/{euid}/shares | Share | dewey shares create EUID --policy FILE --idempotency-key KEY |
| Inspect/edit/revoke share | /api/v1/registry/shares/{euid} | Sharing / recipient view | dewey shares get / update / revoke |
| Explicit shared-login recipient invitation | POST /api/v1/registry/shares/{euid}/invite | Send login invitation | dewey shares invite EUID --email EMAIL |
| Query full authorized registry | POST /api/v1/registry/search | Library, Sets, Sharing | dewey artifacts search |
| List server-visible buckets and registered locations | GET /api/v1/storage/buckets | S3 Browser | dewey storage buckets |
| List a bounded S3 prefix page | GET /api/v1/storage/browse | Address bar, breadcrumbs | dewey storage browse URI |
| Inspect exact object | GET /api/v1/storage/object | Object panel | dewey storage object URI |
| Multipart upload with conditional completion | /api/v1/storage/uploads | Upload files | dewey storage upload FILE --uri URI |
| Review and execute exact admin deletion | /api/v1/storage/deletions | Reviewed manifest confirmation | dewey storage delete-preview / delete-execute |
| Inspect operation outcomes | GET /api/v1/storage/operations/{euid} | Operation receipt | dewey storage operation EUID |

Other Dayhoff callers should persist Dewey EUIDs as their durable local references.
They resolve storage coordinates or delivery URLs when needed. Prefix browsing
does not create child registrations. A set stores membership through
`artifact_set_member` lineage and never replaces member EUIDs.

Existing OWY, Ursa, resolution, external-reference and Labcore endpoints remain.
The historical OWY register fingerprint is computed before correcting the declared
sequencing-directory presentation. Historical idempotency receipt bodies remain
unchanged; replay is gated by the target's current authorization.

## Explicit conversion and rollback

1. Capture current immutable image, Dewey-only compose fields, private configuration
   and database target. Keep protected configuration copies on the operator host.
2. Create only the three new templates with `dewey db registry-templates` using
   explicit `--operator-config`, `--repository-pack`, `--receipt-pack` and `--actor`.
   This owned CLI delegates to TapDB's governed loader with overwrite disabled and
   requires the operator and runtime database identities to agree. The new definitions
   are `config/tapdb_templates/dewey/registry10.repository-pack.json`.
   Native `tapdb templates import` is reserved for previously exported packs and
   requires a real export receipt; this new-template command creates that receipt
   after persistence. It never seeds unrelated core or existing service templates.
   Do not reseed existing templates or change DGX/M identity bindings.
3. Quiesce the Dewey writer during the final conversion/deployment interval.
4. Run `dewey db registry-conversion plan --actor ACTOR --manifest ABS` with
   explicit production Dewey/TapDB configuration. This command is implemented in
   `dewey_service/cli/db.py`; it does not run during server startup.
   Review every ambiguous row individually; no
   trailing-slash-only classification is accepted.
5. Apply the exact reviewed manifest with `apply --expected-sha256 DIGEST --receipt ABS`.
   The receipt records actual persisted policy EUIDs and reversible field projections.
6. Start only the final tagged Dewey image and observe runtime availability.

An image rollback alone is insufficient after conversion. Stop the Dewey writer,
inspect the committed conversion receipt, reverse the exact manifest with
`reverse --expected-sha256 DIGEST --receipt ABS`, restore the captured Dewey image
and configuration, then observe availability. Reversal fails if affected fields,
coordinates or policies have changed. New registrations, edits and grants made
after release require individual preservation decisions; never restore a stale
whole-database snapshot over accepted work.

Prepared or pending-commit receipts indicate uncertainty, not committed success.
Inspect database state before retrying. New templates may remain installed after
rollback; removing historical identity-bearing rows is not part of reversal.

## Runtime configuration

- `registry.internal_domains`: explicit internal domains (initially `lsmc.com`).
- `registry.service_principals`: SHA256 of each existing general service bearer
  mapped to its attributable subject and explicit roles. Unmapped accepted
  credentials fail with a clear configuration error; no inferred identity.
- `registry.default_share_lifetime_days`: initial explicit default 30.
- `share.default_signed_ttl_seconds`: initial explicit default 900.
- `DEWEY_NCBI_API_KEY_FILE=/home/ubuntu/.config/ncbi/key.txt`: protected host file,
  read-only mounted at that same container path. Load before importing Metapub.
- Personal CLI clients use explicit `DEWEY_API_URL` and a private absolute
  `DEWEY_API_TOKEN_FILE`. Tokens are revocable and expire; token creation does not
  expose the server's AWS credentials.
- `dewey config prepare-registry-release --destination ABS --principals ABS`
  prepares a new private configuration and requires exact coverage of the existing
  general API credential fingerprints. It never rewrites the active configuration.
- Administration can change share/delivery defaults through `/api/v1/registry/defaults`.
  Personal API clients select a role bounded by their issuer's role; issued credentials
  are displayed once and can be revoked through Account and the public API. The four user CLI groups transact registry records, shares and storage; token lifecycle remains in Account/API.

Report previews use short-lived delivery capabilities, an opaque sandbox origin,
per-asset authorization and no application cookies. Delivery issuance is audited
separately from completed downloads. Recipient invitations are explicit actions;
creating a share does not send a message.

## Release boundaries

10.0.2 is deployed; 10.0.3 completes two presentation findings from the deployed review. No PR, merge or broad
Dayhoff rollout is included. Ursa/Kahlo browser removal follows the user's
acceptance of deployed Dewey, with separate scoped releases.
