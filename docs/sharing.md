# Managed Dewey sharing — 12.x

This is the schema-3 source contract. The [release ledger](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) separates implementation, tests, tagged images, deployment and acceptance. The [11.0.10 analysis](dev-docs/20261025_dewey_capabilities.md) remains a historical baseline.

The current sharing behavior includes scoped expiration, explicit revival, and
recipient notification from `dewey@lsmc.com`. Release-specific build/deployment
results belong in the dated release ledgers; the 12.0.8 closeout below is historical,
not the current deployed-version record.

The shared-report viewer shows a compact title/session notice that can be
dismissed and disappears10seconds after page load. The report then fills the
available viewport, including on mobile. Access or handoff errors remain visible
and reappear if the notice has already disappeared. Ordinary registry success
notices also disappear after10seconds; errors remain visible.

A sharing session is restricted even when the account also has ordinary management
rights. An entitled manager can use [normal management sign-in](https://dewey.day.lsmc.bio/auth/login?next=%2Fui)
from an approved network to restore console access. This replaces that profile's
session without widening any share grant; separate profiles keep the two sessions independent.

## Authority, recipients and selection

### Your share home

A share-only browser session opens **Shared with me** at `/`. It lists only
shares matching the current verified email identity, with their persisted EUID,
name, date shared, access deadline and active/expired status. **Show expired
shares** is off initially; expired entries do not authorize opening content.
Revoked grants, denied recipients, obsolete policy revisions and archived or
revoked shares do not appear. Active links use the normal managed share viewer.
The displayed recipient deadline accounts for both share and matching-grant
expiration; the date shared is the creation date of the current matching grant.

**Logout / use a different account** uses Dewey's existing `POST /auth/logout`,
which clears the browser session, revokes its browser identity binding and
continues through the configured shared-login logout. Personal download
credentials remain separately managed. Sign in again through the normal login
page to choose another identity. A browser root request whose session has ended
returns to login; restricted non-HTML/API root requests still receive403.

The full authorized `/ui` library includes a separate **Shares** section with
persisted EUIDs, names, share creation dates, expiration, status and Open/Manage
links. Expired/inactive shares are hidden initially and can be included with the
toggle. Its paginated index uses existing management authorization; **Manage all
shares** preserves the complete sharing workflow. Share-only sessions cannot
open `/ui` or management APIs.

`GET /api/v2/recipient/shares?page=1&page_size=50&include_expired=false` is the
recipient index. It requires verified sharing ingress and current verified email
identity; permission filtering precedes pagination. Its response contains only
`euid`, `name`, `shared_at`, `expires_at`, `status`, and the managed `web_path`,
plus pagination fields. It does not expose targets, S3 locations, other
recipients or management authority. `include_expired=true` changes metadata
visibility only; normal content authorization remains in force.

The existing management index accepts `include_expired=false` for the homepage;
its default remains true for existing management clients. This is separate from
the recipient index and retains the existing owner/admin/current-recipient
authorization contract.

A creator needs delegation authority over every selected target. An active share then authorizes its verified recipient without a separate artifact ACL, S3 permission or tenant membership. Owners/managers still need a recipient grant to read bytes. Management stays on trusted ingress; public ingress exposes only recipient, authentication and isolated-report routes.

Choose `audience: recipients` for mixed internal/external email or deliberate domain grants, or `audience: public_registered` for any current verified registered email. Neither permits anonymous access. A pending grant can name an unregistered person. Login creates share-only identities without automatic tenant admission. Domain grants match exactly unless `include_subdomains` is true; a domain predicate does not confer organization membership.

Objects are fixed targets. A selection/set freezes persisted member targets; prefixes remain live and include later matching descendants. A fixed set containing a prefix therefore has fixed roots and live contents beneath that prefix. No selection copies or freezes S3 bytes.

Filters are case-sensitive and target-relative: `*` stays within a segment, `**` crosses segments, and `?` matches one non-separator. Share-wide exclusions constrain every grant; grant exclusions narrow that grant only. `denied_emails` overrides all grants for that address. Grant `target_euids` limits the applicable native members. Preview is bounded; a partial count or empty filtered page is not complete enumeration.

Omitted `expires_at` defaults to no expiration only for a verified exact `lsmc.com`/`lsmc.bio` original creator and an entirely exact internal audience. Other shares default to 14 days, have a maximum of 365 days, and cannot use indefinite access. Eligible internal shares may also set a finite date. Explicit `expires_at: null` is allowed only for the eligible internal scope. Finite timestamps must be future and timezone-bearing ISO 8601. Grant expiry cannot exceed share expiry. Credentials remain finite. Atomic edits use the current `policy_revision`; stale edits return 409. Removing a target retains its artifact/S3 bytes. Inactive shares can be explicitly revived with a new finite expiration and reviewed recipients; old aliases/contexts and revoked individual grants are not silently restored.

## URLs and delivery

Use `/fetch/<share-euid>` or `/fetch/<claimed-slug>`. A single file resolves at the root; a single prefix preserves relative paths; multiple targets use `<target-euid>/<relative-path>`. The namespace follows the whole share even when a recipient sees only one target. Existing `/shares/<share-euid>` URLs remain authenticated entrypoints.

Slugs use one global namespace: lowercase ASCII letters, digits and hyphens, 3–63
characters, starting and ending with a letter or digit. Reserved control names
and the EUID namespace fail. Claims are atomic; a conflict never adds a suffix.
Aliases have native lineage to one share; retired names remain permanent tombstones.

GET/HEAD provide filename, MIME, size, one byte range and ETag/date conditions. Browser login retains the exact deep destination. Unauthenticated machines receive 401. Traversal, ambiguous paths and invalid encodings fail explicitly.

For a WWW entrypoint, `?download=true` requests the original file instead of opening
the isolated viewer. A root collection URL presents a paginated file browser to
HTML clients and a manifest page to machine clients. Listing one page does not
establish complete recursive enumeration.

- `?format=manifest` returns authorized entries and continuation metadata. Follow every token, including empty filtered pages. Cursors bind current policy and storage-location revisions.
- `?format=tar` streams uncompressed PAX TAR after complete inventory. The inventory cap is one million objects or 256 MiB of metadata; larger requests fail before headers and can use manifest/CLI retrieval.
- Version/conditional reads detect changed or missing content. Policy is rechecked before every TAR member. An aborted archive is incomplete; TAR restarts, while individual files support conditional resume.
- Each request checks current policy. An admitted individual-file response may finish; revocation prevents subsequent requests and archive members.

New managed-share raw S3 presigns are disabled. Obsolete modes/payloads fail explicitly. Existing presigns last until their original deadlines; the release ledger records the remaining window. Downloaded bytes cannot be recalled.

## WWW reports

Declare `content_mode: www`, `report_entrypoint` and `report_bundle_root`. `/fetch/<identifier>/multiqc.html` opens a trusted application wrapper. Include the sibling/subdirectory assets in the selected prefix and bundle; sharing just the HTML object does not authorize siblings.

Report HTML/CSS/JavaScript/data execute on a unique `pv-<context>.dewey-content.day.lsmc.bio` host. A one-use POST handoff and Secure HttpOnly host cookie bind the viewer and finite context. Every asset checks current identity/policy and stays within its bundle. Logout, expiry, revocation or session invalidation prevents subsequent assets.

The isolated iframe allows scripts and same-origin within its separate content host. The iframe and content policy permit local form-driven exports and generated downloads. CSP still blocks network form submissions, workers and nested frames. Application cookies/APIs are unavailable to report scripts. Chrome may ask you to allow multiple downloads when MultiQC saves one file per selected plot. Reports requiring additional browser capabilities need a separate product decision.

Isolated report assets wait asynchronously for the delivery slots (three
per viewer, twelve per process). A browser's parallel script requests therefore
wait for capacity instead of losing plot dependencies to a download-capacity
429. Ordinary download admission retains its existing behavior. Report assets
use private, mandatory-revalidation caching: every request is authorized and
audited, and unchanged objects may return the provider's conditional 304 rather
than retransferring JavaScript, styles, fonts and plot data. Preview handoff and
application responses remain non-cacheable.

After allowing multiple downloads, click the report's download button again if
Chrome withheld the remaining files. Reopen the durable report URL to renew an
expired context or load a viewer update. Generated plot exports use data already
delivered to the browser; they are separate from downloading the original shared
files or a recursive TAR and cannot be recalled after delivery.

## Credentials and invitations

At `/recipient/account`, issue a separately revocable personal credential for 1–365 days, capped by the provider grant. Normal browser logout preserves personal credentials. Login stores encrypted provider tokens server-side; Dewey holds opaque bindings. Private introspection checks current enabled/verified-email state and provider revocation, with positive caching capped at 60 seconds. A locally valid JWT alone is insufficient.

For CLI, set `DEWEY_API_URL` to the exact HTTPS origin and `DEWEY_API_TOKEN_FILE` to an absolute mode-600 file. Curl/wget send the credential through `Authorization: Bearer …`. Never put it in a durable URL.

Creating or adding an explicit email recipient sends a share notification from `dewey@lsmc.com` for internal and external addresses. An unknown recipient also receives account-creation instructions in the invitation. Domain grants do not broadcast email. Native notification records distinguish accepted, failed or uncertain submission; acceptance means the mail provider accepted the request. Cognito owns verification/recovery. Failures retain the grant/destination without automatic resend loops.

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

Example named-recipient policy (omitted expiry follows the creator/audience policy):

```json
{"name":"Reviewed reports","audience":"recipients","content_mode":"download","include_patterns":["reports/**"],"exclude_patterns":["reports/internal/**"],"grants":[{"recipient_type":"email","recipient":"recipient@example.org"}]}
```

For registration-open access, use `audience: public_registered` without named grants. It defaults to 14 days and requires a finite expiration within 365 days; indefinite public access is not supported. Edits carry `policy_revision` and all replacement restrictions intended to remain.

## Reports and storage references

Reports cover current lifecycle/audience/mode, finite duration buckets, indefinite shares, age, last access, verified viewers and unused shares. Windowed native events distinguish authorization evaluations, report entries/assets, HEAD/304/ranges, archives, interruption and server bytes. Retries produce separate responses; server completion never proves client persistence. Historical raw-presign consumption is unobserved.

Version 12.0.6 also persists authenticated denials during share identifier resolution. Earlier missing denial events are not backfilled; report completeness describes the retained source inventory and events, not reconstructed historical requests. The release ledger records the correction and its acceptance window.

Inventory pages bind `observed_at` and `inventory_sha256`; send the latter as `expected_inventory_sha256` on following pages. Drift fails 409 rather than mixing exports. Exports report windows, watermarks and completeness. Owners see their inventory; admins can select other owners. Preserved legacy history has separate coverage.

Rebind compares complete size and qualified S3 FULL_OBJECT SHA-256 evidence, rejects identity collisions/mismatch, then records a native location revision. Missing qualified evidence fails; ETags alone are insufficient. Artifact/share EUIDs, aliases and paths stay stable; location-bound cursors are invalidated. No physical S3 move/delete occurs.

## Deployment and preservation

Use explicit configuration and independent public/private proxy assertions. Strip caller assertions/forwarded trust headers; the loopback transport peer plus configured secret establishes ingress class. Public paths exclude management, generic Login pages, service backchannels and sibling services.

`dewey config prepare-sharing-v12` writes a reviewed new configuration. Enable Login's optional `recipient_access` contract and run `lsmc-login state init-recipients` against its existing explicit state database. Preserve Cognito pool/app clients/providers and shared-library pins. Install only `sharing3.repository-pack.json` through `dewey db registry-templates` with the reviewed operator config.

Run `dewey db upgrade-sharing-v3 --phase inventory|apply|verify` with private inventory, exact digest and attribution. Fence sharing writes, drain delivery, recheck inventory, convert and reconcile before starting Dewey 12. Preserve identities, grants, scope, inactive history and lineage; ambiguity blocks cutover. **Never rerun historical `upgrade-sharing` retirement logic.** After schema 3/new writes, image-only rollback is invalid: fence and repair forward or separately review a restoration preserving intervening writes/history.

## Create or edit a share

The share form starts with its name, recipient email addresses (one per line), and
expiration. Recipients sign in using their verified email address.

No expiration is the default only when the original creator has a verified exact
`lsmc.com` or `lsmc.bio` address and the entire audience is also exact
`lsmc.com`/`lsmc.bio`. Other audiences default to 14 days and require a finite
expiration within 365 days. Dates use your local time zone; manual UTC offsets are
in Advanced for daylight-saving ambiguity. Existing expiration values are retained
unless you edit them.

For an HTML object or an existing WWW share, the form offers **Open as web report**.
The report-file field appears when WWW is selected. It requires an explicit relative
HTML path; Dewey does not discover report files. Other targets can select WWW in
Advanced. The share must include the report's permitted sidecars.

**Advanced** contains public/domain audiences, file patterns, excluded addresses,
per-recipient deadlines and target scopes, report-folder settings and manual time
zone offsets. Existing complex shares retain their recipient rules; their simple
email list is read-only. Editing individual rules switches recipient editing to
Advanced rather than flattening those rules into an email list.

The `?` help disclosures work by keyboard or tap. **Sharing help** in the dialog
contains a short guide without requiring a separate documentation page.
