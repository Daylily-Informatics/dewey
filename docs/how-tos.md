# Dewey How-Tos

These workflows use the current Dewey CLI, browser UI, and API surface exactly as they exist today.

## Activate The Repo Environment

Start every Dewey session the repo-supported way:

```bash
source ./activate <deploy-name>
dewey --help
```

Useful read-only checks:

```bash
dewey info
dewey config path
dewey server status
```

## Initialize Config And Build Local DB

If the deployment-scoped config does not exist yet:

```bash
source ./activate <deploy-name>
dewey config init
dewey config validate
dewey config status
```

Then bootstrap local persistence:

```bash
dewey db build --target local
```

If you need a destructive local reset, use Dewey's own CLI rather than bypassing it:

```bash
dewey db reset --target local
```

## Start The Service

Start Dewey through its service CLI:

```bash
source ./activate <deploy-name>
dewey server start --port 8914
```

Then inspect status and logs:

```bash
dewey server status
dewey server logs
```

By default the current config template expects HTTPS on `https://localhost:8914`.

## Quick Register From The Dashboard

Use the dashboard when you need a fast one-source intake.

1. Open `https://localhost:8914/login`.
2. Sign in through Cognito.
3. Open `Dashboard -> Quick Register`.
4. Choose exactly one source:
   `Local File`, `Public URL`, or `S3 URI`.
5. Optionally override the inferred artifact type.
6. Submit the form.

Use this for single-source intake. Use the full Artifacts surface for bulk and grouped workflows.

Current live caveat: `Local File` and copy/import-style flows need `managed_storage_bucket` to be configured. `S3 URI` in `reference` mode does not use the managed bucket.

## Register From The Artifacts Page

Use `Artifacts -> Register` when you need the broader intake workflow.

Current supported sources and options include:

- local files
- flat directory upload
- public URLs
- S3 URIs or prefixes
- grouping into a new or existing artifact set
- typed metadata fields plus extra JSON metadata
- optional lock-after-import behavior

Current live caveat: browser uploads, upload sessions, and copy-style imports need a configured managed artifact bucket. Reference-mode registration of an existing readable S3 object does not.

The browser page supports these common patterns:

### One S3 object in reference mode

1. Open `Artifacts`.
2. Choose artifact type or keep auto-detect where reasonable.
3. Set `S3 Mode` to `reference`.
4. Enter one `s3://bucket/key` URI that Dewey can read.
5. Add producer and metadata fields if needed.
6. Submit `Run Intake`.

### Multiple source types into one artifact set

1. Open `Artifacts`.
2. Provide one or more local files, URLs, or S3 URIs.
3. Choose `Artifact Set Grouping -> create`.
4. Fill in set type, label, description, and set metadata.
5. Submit `Run Intake`.

### Flat directory intake

The current UI accepts directory uploads, but current tests enforce a limit of `1000` files for that workflow.

## Bulk TSV Intake

Use the Artifacts page when you want row-driven intake.

1. Open `Artifacts -> Register`.
2. Download the template from `Bulk TSV Intake -> Download Template`.
3. Fill one row per intake action.
4. Upload the TSV file.
5. Submit `Run Bulk Intake`.
6. Review the row-level bulk report in the same page.

The current template supports:

- `source_mode`
- storage coordinates
- producer fields
- optional artifact-set grouping columns
- browser-supported artifact metadata columns

## Search And Export

Use `Unified Search` for normalized artifact and share-reference query flows.

1. Open `Unified Search`.
2. Enter full-text query, filters, and scopes.
3. Run the search.
4. Export the result set as JSON or TSV.

Current GUI filters include:

- artifact type
- producer system
- availability
- import mode
- share transport
- share status
- external object ID
- created-at window

For API users, the canonical endpoints are:

```bash
POST /api/search/v2/query
POST /api/search/v2/export
```

The `/api/v1/search/v2/*` aliases are still live but currently marked deprecated.

## Create And Share An Artifact Set

There are two current browser paths:

### Create From A Selection

1. Search artifacts in `Artifacts -> Search Artifacts`.
2. Select the artifacts you want.
3. Use `Create Artifact Set From Selection`.
4. Provide set type, label, and optional metadata.

### Create Directly In The Artifact Sets Section

1. Open `Artifacts -> Artifact Sets`.
2. Fill the `Create Artifact Set` form.
3. Submit.
4. Review the latest created set in the same page.

### Share A Set

1. Use `Artifacts -> Search Artifact Sets`.
2. Open or select the target set.
3. Fill `Share Selected Artifact Set`.
4. Choose the transport and expiry behavior.

Current code-backed transport behavior:

- `presigned_s3` for concrete per-member presigned URLs
- `rclone_http` and `rclone_sftp` for artifact-set connection metadata

Artifact-level browser sharing currently produces individual links for the selected artifacts.

## Save A PubMed Paper Into Dewey

Use `Literature Search` for this flow.

1. Open `Literature Search`.
2. Search PubMed by keywords.
3. Review the title, journal, year, abstract snippet, and full-text status.
4. Choose a save mode:
   `auto`, `managed_artifact`, or `external_reference`.
5. Choose visibility:
   `private`, `restricted`, or `all_users`.
6. Submit `Save To Dewey`.

Current behavior:

- Dewey searches through `metapub`
- Dewey stores saved papers as `artifact_type == literature`
- Dewey stores visibility through literature-save records
- Dewey can keep a managed copy when download is allowed and succeeds

## Inspect Observability And Anomalies

Use the GUI when you need a quick operator view:

- `Observability` for API, endpoint, DB, and auth rollups
- `Anomalies` for persisted anomaly records
- `Admin` for an admin-only anomaly and managed-bucket surface

Useful direct endpoints for service operators:

```bash
curl -k -H "Authorization: Bearer $DEWEY_API_TOKEN" https://localhost:8914/health
curl -k -H "Authorization: Bearer $DEWEY_API_TOKEN" https://localhost:8914/obs_services
curl -k -H "Authorization: Bearer $DEWEY_API_TOKEN" https://localhost:8914/api_health
curl -k -H "Authorization: Bearer $DEWEY_API_TOKEN" https://localhost:8914/db_health
```

Unauthenticated health endpoints:

```bash
curl -k https://localhost:8914/healthz
curl -k https://localhost:8914/readyz
```

## Update The Managed Artifact Bucket

The current UI exposes this only on the admin page.

1. Sign in as an admin user.
2. Open `Admin`.
3. Review the current config path and managed bucket.
4. Enter the bucket name only.
5. Submit `Save Bucket`.

The current CLI also exposes the same config-level operation:

```bash
dewey config set-artifact-bucket dewey-artifacts-example
```

## Run Current Verification Commands

These are the repo-supported commands used by the current docs:

```bash
source ./activate <deploy-name>
dewey --help
dewey server --help
dewey db --help
dewey test --help
dewey quality --help
pytest --collect-only -q
pytest --cov=dewey_service --cov-report=term-missing:skip-covered
```

Current measured verification on April 6, 2026:

- `256` collected tests
- `254` passed
- `0` failed
- `2` skipped
- `84%` coverage
