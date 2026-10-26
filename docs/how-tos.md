# Dewey How-Tos

These workflows describe release 12.0.7. The day service uses shared Login; management remains on approved-network ingress, while verified recipients use the explicit public fetch/auth/content surfaces. See [Managed sharing](sharing.md) for the full contract and [the release ledger](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) for acceptance status.

## Activate And Inspect The Repo Environment

Use the supported environment and CLI:

```bash
source ./activate <deploy-name>
dewey --help
dewey runtime check
dewey --json version
dewey config path
dewey server status
```

Root-global `--json` is supported only by commands that declare it. Business CLI commands use authenticated HTTP; server/database lifecycle commands require their explicit local configuration.

## Configure Existing Storage And Start The Service

Release 12.0.7 pins TapDB 11.0.9, `meridian-euid==0.4.8` and `daylily-auth-cognito==2.1.5` on Python >=3.12. All Python dependencies live in `project.dependencies` and the frozen lock. Pass every service/TapDB config path explicitly as an absolute path.

```bash
dewey config init
dewey config validate
dewey config status
export TAPDB_CONFIG_PATH=/absolute/path/to/tapdb-config.yaml
dewey db lifecycle
dewey db verify-templates
dewey server start --port 8914
dewey server status
dewey server logs
```

The configured runtime principal and existing templates must match the intended database. `dewey db lifecycle` delegates low-level lifecycle work to the supported TapDB CLI. Startup reads existing templates; it does not repair, reset or seed production automatically. Schema-3 sharing conversion uses the explicit inventory/digest/apply/verify workflow and preserves historical identities. Do not substitute the historical share-retirement workflow or repeat an already verified production conversion.

The day sharing release is already deployed. Its completed backup/conversion receipts and rollback restrictions belong to the release ledger. Container images are built on the designated EC2 host from the immutable intended release tag, never on the laptop.

## Register Records And Create A Set

1. Sign in through the configured Login service and open **Library**.
2. Use **Add** (`/add`, also `/artifacts`) to register the selected object, prefix, URL reference or set. Use **S3 Browser** to inspect a permitted location and register selected existing objects/prefixes.
3. Open the returned persisted EUID to inspect metadata, permissions and available actions.
4. Use **Sets** or the set's record controls to assemble explicit existing Object/Prefix members.

Registering a prefix records its identity without recursively registering descendants. Metadata visibility and download permission are independent. Upload/copy workflows require their configured managed storage and write authority; an existing readable S3 reference does not imply ownership of the bucket. Registry archiving and artifact-set member removal remain prohibited by the deletion policy. Removing a target from a managed share is a separate access-policy edit and retains the registry object and S3 bytes.

Existing service intake APIs for S3 reference/copy, prefix-only registration, upload sessions and analysis/MultiQC manifests remain documented in [API Surface](apis.md). The current GUI is the Library/Add interface; old dashboard and bulk-intake screenshots are historical.

## Search

Use Library, Sets and Sharing to search their authorized populations before pagination. Record filters include metadata paths and explicit operators. Management HTTP clients use `/api/v1/registry/search`; the normalized service search APIs `/api/search/v2/query` and `/api/search/v2/export` retain their explicit scope/filter contracts. Do not interpret one page as a complete export.

## Create And Edit A Share

1. Open the registered Object, Prefix or Set and select **Share**.
2. Choose **Named recipients** or **Public with registration**. Add the intended internal/external emails or deliberate domain grants. A person may register later; no anonymous audience exists.
3. Choose the deadline. Omitted API expiry defaults to 30 days; explicit `expires_at: null` means indefinite.
4. Review targets and include/exclude patterns. Prefix selection remains live for future matching descendants. A bounded preview marked incomplete is not a full inventory.
5. Save, retain the share EUID, and copy its `/fetch/<share-euid>` URL. Send an invitation only through the explicit invitation action when wanted.

Open **Sharing** to edit recipients, expiry, target membership and filters. Each edit includes the reviewed `policy_revision`; reload after a conflict. Removing a recipient or target preserves historical grant/scope lineage. Expired/revoked shares cannot be reactivated by editing. A granted recipient needs no separate artifact ACL, S3 permission or organization membership.

The authenticated HTTP CLI supports the same management operations:

```bash
dewey shares create "${ARTIFACT_OR_SET_EUID}" \
  --policy /absolute/private/share-policy.json \
  --idempotency-key "${IDEMPOTENCY_KEY}"
dewey shares get "${SHARE_EUID}"
dewey shares update "${SHARE_EUID}" --changes /absolute/private/share-edit.json
dewey shares invite "${SHARE_EUID}" --email "${RECIPIENT_EMAIL}"
```

The policy/edit files contain only the reviewed request fields; an edit file must include the current integer `policy_revision`. Environment EUID variables above are actual identifiers returned by Dewey. Invitation receipts distinguish accepted, failed and uncertain submission; accepted submission is not proof of mailbox delivery.

## Claim Or Retire A Friendly URL

Use the share's alias controls or:

```bash
dewey shares aliases "${SHARE_EUID}"
dewey shares claim-slug "${SHARE_EUID}" "${CHOSEN_SLUG}" \
  --policy-revision "${POLICY_REVISION}"
dewey shares retire-slug "${SHARE_EUID}" "${CHOSEN_SLUG}" \
  --policy-revision "${POLICY_REVISION}"
```

A slug has 3–63 lowercase ASCII letters/digits/hyphens with alphanumeric ends. Reserved/invalid names and collisions fail; no suffix is silently added. Retirement is permanent. EUID and slug URLs evaluate the same policy.

## Use curl, wget And The CLI

Sign in at `/recipient/account`, create a finite read-only credential, and save its one-time value in a private file with mode 0600. Credentials last 1–30 days and remain separately revocable. Share lifetime does not extend a credential.

The CLI requires both an explicit HTTPS origin and an absolute token-file path. It does not read the shell variable used by the adjacent curl/wget examples:

```bash
export DEWEY_API_URL=https://dewey.day.lsmc.bio
export DEWEY_API_TOKEN_FILE=/absolute/private/dewey-token

dewey shares contents "${SHARE_EUID}"
dewey shares manifest "${SHARE_EUID}" --output ./manifest.json
dewey shares fetch "${SHARE_EUID}" --output ./collection --recursive --resume
```

`manifest` follows every page before publishing the complete output. The manifest output must be a new file. `fetch --recursive --resume` validates retained per-file receipts and uses conditional ranges. Changed content/policy, failed files and partial outputs are reported explicitly; a partial collection is not a successful complete download.

For curl/wget, supply the credential through a private client configuration or the caller's private `DEWEY_TOKEN` environment variable, never the URL:

```bash
curl --fail -H "Authorization: Bearer ${DEWEY_TOKEN}" \
  "https://dewey.day.lsmc.bio/fetch/${SHARE_EUID}" -o artifact.bin
wget --header="Authorization: Bearer ${DEWEY_TOKEN}" \
  "https://dewey.day.lsmc.bio/fetch/${SHARE_EUID}?format=tar" -O collection.tar
```

A single-object share resolves at its root. Prefix files preserve relative paths; multiple targets require `<target-euid>/<relative-path>`. TAR is uncompressed, inventories before streaming, has explicit capacity limits and restarts after interruption. Missing/invalid machine credentials return 401. Raw presigns and old rclone/CloudFront managed-share transport payloads are rejected.

## Share A WWW Report

1. Register the report's containing prefix, including the necessary sibling/nested assets.
2. Choose **WWW report**, an exact HTML entrypoint such as `multiqc.html`, and the permitted bundle root (empty or a relative directory ending in `/`).
3. For multiple targets, start the entrypoint with its persisted target EUID. Include/exclude filters must admit the entrypoint and required assets.
4. Open `/fetch/<share-euid-or-slug>/<declared-report-entrypoint>` in a normal browser tab, for example `/fetch/<share-euid-or-slug>/multiqc.html` for a single report root. Login returns to the same permitted path.
5. Use the report's own export controls for client-generated output, including MultiQC images.

The wrapper establishes the isolated per-context content host; authorized sidecars remain there and cannot use Dewey application cookies/APIs. Form submit handlers and generated downloads work in the sandbox while network form submissions remain blocked. HTML-only sharing does not grant sibling assets. `dewey shares report "${SHARE_EUID}"` prints the browser URL, not a transferable session token.

## Revoke Access

Use the current policy revision for either operation:

```bash
dewey shares revoke-grant "${SHARE_EUID}" "${GRANT_EUID}" \
  --policy-revision "${POLICY_REVISION}" --reason "${REASON}"
dewey shares revoke "${SHARE_EUID}" \
  --policy-revision "${POLICY_REVISION}" --reason "${REASON}"
```

Reload the share revision after any successful mutation before a later command. Current policy applies to new requests, report assets and TAR members. An admitted individual response may finish. Downloaded bytes and previously issued raw storage URLs cannot be recalled. Credential revocation is a separate action on the recipient account page.

## Rebind An Equivalent Storage Location

Inspect the current record's `location_revision`, then use the record's rebind control or:

```bash
dewey artifacts location-rebind "${ARTIFACT_EUID}" \
  --storage-uri "${DESTINATION_S3_URI}" \
  --expected-location-revision "${LOCATION_REVISION}" --reason "${REASON}"
```

An object may also specify `--version-id`. Dewey requires qualified complete content-equivalence evidence, rejects collisions/stale revisions, and retains native location history. Different storage coordinates require matching S3 `FULL_OBJECT` SHA-256 checksums and byte counts; ETags and caller-supplied hashes do not prove equivalence. Stable artifact/share identifiers and relative paths remain. This does not perform physical S3 copy/move/delete.

## Review Activity And Export Sharing Inventory

`dewey shares activity "${SHARE_EUID}"` returns one event page; follow its continuation token. Use explicit report windows and authorized filters for aggregates or a complete frozen inventory export:

```bash
dewey shares audit-report --starts-at "${WINDOW_START}" --ends-at "${WINDOW_END}"
dewey shares audit-report --starts-at "${WINDOW_START}" \
  --inventory --output ./sharing-inventory.json
```

Use a new output filename. Full export retains `observed_at` and inventory digest across pages, verifies the final count, and leaves a `.partial` receipt if it cannot finish. `--older-than-days` and `--never-accessed` select reviewer-defined cleanup candidates; the command does not revoke them. Owners see their own population; administrators can select a broader authorized owner filter.

Reports separate authorization evaluations, denials, file response completion, HEAD/304/ranges, report entries/assets, archive outcomes and server bytes. Known-share resolution denials are durably recorded. Unknown/retired identifiers do not invent lineage, and old missing events are not backfilled. Exact native creation-to-deadline duration can be milliseconds above a nominal day boundary. Server completion is not client-persisted-byte evidence.

## Literature And Operational Inspection

Literature retains PubMed search through Metapub and supported save modes `auto`, `managed_artifact` and `external_reference`, with private/restricted/all-users visibility. Scientific interpretation remains outside Dewey.

Operators can use `/ui/observability`, `/ui/anomalies`, `/health`, `/obs_services`, `/api_health`, `/endpoint_health`, `/db_health`, `/my_health` and `/auth_health` within their configured management network/auth boundary. `/healthz` and `/readyz` are application probes; they are not public recipient routes. A successful health probe is not sharing acceptance.

Managed artifact bucket configuration uses the explicit service configuration, including `dewey config set-artifact-bucket <bucket-name>` where appropriate. Changes to runtime storage configuration are distinct from artifact location rebind.

## Validation And Acceptance

The [coverage contract](dev-docs/20261026_sharing_test_coverage.md) defines approved changed-code checks and the separate native PostgreSQL contract group. Main/PR CI and release deployment have separate receipts. Historical April test counts are not current validation evidence.

Internal signup is confirmed. Current internal application admission/scoped-access evidence and final user acceptance remain open in the release ledger; this guide does not declare the release objective complete.
