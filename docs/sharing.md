# Managed Dewey sharing — 12.0.0

This is the schema-3 source contract. The [release ledger](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) separates implementation, tests, tagged images, deployment and acceptance. The [11.0.10 analysis](dev-docs/20261025_dewey_capabilities.md) remains a historical baseline.

## Authority, recipients and selection

A creator needs delegation authority over every selected target. An active share then authorizes its verified recipient without a separate artifact ACL, S3 permission or tenant membership. Owners/managers still need a recipient grant to read bytes. Management stays on trusted ingress; public ingress exposes only recipient, authentication and isolated-report routes.

Choose `audience: recipients` for mixed internal/external email or deliberate domain grants, or `audience: public_registered` for any current verified registered email. Neither permits anonymous access. A pending grant can name an unregistered person. Login creates share-only identities without automatic tenant admission. Domain grants match exactly unless `include_subdomains` is true; a domain predicate does not confer organization membership.

Objects are fixed targets. A selection/set freezes persisted member targets; prefixes remain live and include later matching descendants. A fixed set containing a prefix therefore has fixed roots and live contents beneath that prefix. No selection copies or freezes S3 bytes.

Filters are case-sensitive and target-relative: `*` stays within a segment, `**` crosses segments, and `?` matches one non-separator. Share-wide exclusions constrain every grant; grant exclusions narrow that grant only. `denied_emails` overrides all grants for that address. Grant `target_euids` limits the applicable native members. Preview is bounded; a partial count or empty filtered page is not complete enumeration.

Omitted `expires_at` means 30 days; explicit `expires_at: null` means indefinite. Finite timestamps must be future, timezone-bearing ISO 8601, within the configured ceiling. Grant expiry cannot exceed share expiry. Credentials remain finite. Atomic edits use the current `policy_revision` and can change recipients, targets, filters, deadline and content settings; stale edits return 409. Removing a target retains its artifact/S3 bytes. Native revisions and lineage preserve history; revoked shares cannot be silently revived.

## URLs and delivery

Use `/fetch/<share-euid>` or `/fetch/<claimed-slug>`. A single file resolves at the root; a single prefix preserves relative paths; multiple targets use `<target-euid>/<relative-path>`. The namespace follows the whole share even when a recipient sees only one target. Existing `/shares/<share-euid>` URLs remain authenticated entrypoints.

Slugs use one global namespace: lowercase ASCII letters, digits and hyphens, 3–63 characters. Reserved control/EUID names fail. Claims are atomic; a conflict never adds a suffix. Aliases have native lineage to one share; retired names remain permanent tombstones.

GET/HEAD provide filename, MIME, size, one byte range and ETag/date conditions. Browser login retains the exact deep destination. Unauthenticated machines receive 401. Traversal, ambiguous paths and invalid encodings fail explicitly.

- `?format=manifest` returns authorized entries and continuation metadata. Follow every token, including empty filtered pages. Cursors bind current policy and storage-location revisions.
- `?format=tar` streams uncompressed PAX TAR after complete inventory. The inventory cap is one million objects or 256 MiB of metadata; larger requests fail before headers and can use manifest/CLI retrieval.
- Version/conditional reads detect changed or missing content. Policy is rechecked before every TAR member. An aborted archive is incomplete; TAR restarts, while individual files support conditional resume.
- Each request checks current policy. An admitted individual-file response may finish; revocation prevents subsequent requests and archive members.

New managed-share raw S3 presigns are disabled. Obsolete modes/payloads fail explicitly. Existing presigns last until their original deadlines; the release ledger records the remaining window. Downloaded bytes cannot be recalled.

## WWW reports

Declare `content_mode: www`, `report_entrypoint` and `report_bundle_root`. `/fetch/<identifier>/multiqc.html` opens a trusted application wrapper. Include the sibling/subdirectory assets in the selected prefix and bundle; sharing just the HTML object does not authorize siblings.

Report HTML/CSS/JavaScript/data execute on a unique `pv-<context>.dewey-content.day.lsmc.bio` host. A one-use POST handoff and Secure HttpOnly host cookie bind the viewer and finite context. Every asset checks current identity/policy and stays within its bundle. Logout, expiry, revocation or session invalidation prevents subsequent assets.

The isolated iframe allows scripts and same-origin within its separate content host. CSP excludes workers, nested frames and form submission. Application cookies/APIs are unavailable to report scripts. Reports requiring additional browser capabilities need a separate product decision.

## Credentials and invitations

At `/recipient/account`, issue a separately revocable personal credential for 1–30 days, capped by the provider grant. Normal browser logout preserves personal credentials. Login stores encrypted provider tokens server-side; Dewey holds opaque bindings. Private introspection checks current enabled/verified-email state and provider revocation, with positive caching capped at 60 seconds. A locally valid JWT alone is insufficient.

For CLI, set `DEWEY_API_URL` to the exact HTTPS origin and `DEWEY_API_TOKEN_FILE` to an absolute mode-600 file. Curl/wget send the credential through `Authorization: Bearer …`. Never put it in a durable URL.

Creating a grant sends no email. Explicit invitation requests use SES and record accepted, failed or uncertain submission; acceptance is not inbox delivery. Cognito owns verification/recovery and retains its existing default-email quota. Failures keep the pending grant/destination and do not start resend loops.

## API and CLI

Creation requires `Idempotency-Key`. Management requires trusted ingress and the owner's/delegated manager's authority; recipient APIs expose only the current authorized share and own credentials.

| Operation | API |
|---|---|
| Create / preview | `POST /api/v1/records/<target-euid>/shares[/preview]` |
| Detail / edit | `GET/PATCH /api/v1/registry/shares/<share-euid>` |
| Revoke share / grant | `POST …/<share-euid>/revoke` or `…/<share-euid>/grants/<grant-euid>/revoke` |
| Alias list / claim / retire | `GET/POST …/<share-euid>/aliases`, `POST …/<share-euid>/aliases/<slug>/revoke` |
| Invitation / activity | `POST …/<share-euid>/invite`, `GET …/<share-euid>/activity` |
| Recipient detail / contents | `GET /api/v2/recipient/shares/<identifier>[/contents]` |
| Own credentials | `GET/POST /api/v2/recipient/tokens`, `POST /api/v2/recipient/tokens/<token-euid>/revoke` |
| Aggregates / inventory | `GET /api/v1/registry/sharing-report`, `GET /api/v1/registry/sharing-inventory` |
| Storage rebind | `POST /api/v1/records/<artifact-euid>/location-rebind` |

Replace placeholders with identifiers returned by the owning service:

```sh
dewey shares create '<target-euid>' --policy /absolute/policy.json --idempotency-key '<request-key>'
dewey shares update '<share-euid>' --changes /absolute/reviewed-changes.json
dewey shares claim-slug '<share-euid>' reviewed-report --policy-revision 1
dewey shares retire-slug '<share-euid>' reviewed-report --policy-revision 1
dewey shares fetch '<share-euid>' --output /absolute/collection --recursive --resume
dewey shares manifest '<share-euid>' --output /absolute/manifest.json
dewey shares report '<share-euid>'
dewey shares invite '<share-euid>' --email 'recipient@example.org'
dewey shares audit-report --starts-at '<past-ISO8601-with-offset>'
dewey shares audit-report --starts-at '<past-ISO8601-with-offset>' --inventory --output /absolute/shares.json
dewey artifacts location-rebind '<artifact-euid>' --storage-uri 's3://bucket/equivalent-key' --expected-location-revision 1 --reason 'Verified relocation'
```

The downloader retains `.dewey-download-state` validators, partial bytes and receipts. `--resume` checks completed files and resumes partial files conditionally. It never adopts/overwrites unrelated output; changed validators, unsafe paths and incomplete enumeration fail. TAR restarts.

Example named-recipient policy (omitted expiry means 30 days):

```json
{"name":"Reviewed reports","audience":"recipients","content_mode":"download","include_patterns":["reports/**"],"exclude_patterns":["reports/internal/**"],"grants":[{"recipient_type":"email","recipient":"recipient@example.org"}]}
```

For registration-open indefinite access, use `audience: public_registered` and `expires_at: null` without named grants. Edits carry `policy_revision` and all replacement restrictions intended to remain.

## Reports and storage references

Reports cover current lifecycle/audience/mode, finite duration buckets, indefinite shares, age, last access, verified viewers and unused shares. Windowed native events distinguish authorization evaluations, report entries/assets, HEAD/304/ranges, archives, interruption and server bytes. Retries produce separate responses; server completion never proves client persistence. Historical raw-presign consumption is unobserved.

Version 12.0.6 also persists authenticated denials during share identifier resolution. Earlier missing denial events are not backfilled; report completeness describes the retained source inventory and events, not reconstructed historical requests. The release ledger records the correction and its acceptance window.

Inventory pages bind `observed_at` and `inventory_sha256`; send the latter as `expected_inventory_sha256` on following pages. Drift fails 409 rather than mixing exports. Exports report windows, watermarks and completeness. Owners see their inventory; admins can select other owners. Preserved legacy history has separate coverage.

Rebind compares complete size and qualified S3 FULL_OBJECT SHA-256 evidence, rejects identity collisions/mismatch, then records a native location revision. Missing qualified evidence fails; ETags alone are insufficient. Artifact/share EUIDs, aliases and paths stay stable; location-bound cursors are invalidated. No physical S3 move/delete occurs.

## Deployment and preservation

Use explicit configuration and independent public/private proxy assertions. Strip caller assertions/forwarded trust headers; the loopback transport peer plus configured secret establishes ingress class. Public paths exclude management, generic Login pages, service backchannels and sibling services.

`dewey config prepare-sharing-v12` writes a reviewed new configuration. Enable Login's optional `recipient_access` contract and run `lsmc-login state init-recipients` against its existing explicit state database. Preserve Cognito pool/app clients/providers and shared-library pins. Install only `sharing3.repository-pack.json` through `dewey db registry-templates` with the reviewed operator config.

Run `dewey db upgrade-sharing-v3 --phase inventory|apply|verify` with private inventory, exact digest and attribution. Fence sharing writes, drain delivery, recheck inventory, convert and reconcile before starting Dewey 12. Preserve identities, grants, scope, inactive history and lineage; ambiguity blocks cutover. **Never rerun historical `upgrade-sharing` retirement logic.** After schema 3/new writes, image-only rollback is invalid: fence and repair forward or separately review a restoration preserving intervening writes/history.
