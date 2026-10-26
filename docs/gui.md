# Dewey GUI Guide

This guide describes release 12.0.7. Main navigation is **Library**, **S3 Browser**, **Sets**, **Sharing** and **Literature**. Writable principals see **Add**; administrators see **Admin**. The day deployment uses shared Login. Management remains on approved-network ingress; outside recipients use the configured fetch, authentication and isolated content surfaces.

## Roles And Record Capabilities

Roles remain `READ_ONLY`, `READ_WRITE` and `ADMIN`. The configured identity service supplies roles; an email domain is not an entitlement. Metadata visibility, download, editing and delegation are separate record capabilities. Controls use returned capabilities, and the server enforces them on every operation.

A share manager is the creator/owner or an authorized administrator. A recipient may consume the current grant without independently having the artifact ACL or S3 permission. Recipient-only identities cannot use management APIs. Registration grants no automatic organization membership or access to unrelated records.

## Library, Records And Sets

| Page | Path | Purpose |
| --- | --- | --- |
| Library | `/ui`, `/search` | Search and page authorized records, open a persisted EUID and use metadata filters |
| Record | `/records/<euid>` | Inspect metadata, storage and activity; perform permitted actions |
| Sets | `/sets` | Create and inspect explicit artifact selections; add/remove permitted members |
| Add | `/add`, `/artifacts` | Register an object, prefix, URL reference or set; use supported upload controls |
| S3 Browser | `/storage` | Browse configured locations and register selected storage references |

Prefix registration records a prefix identity without enumerating every child. Metadata visibility does not itself grant download permission. Archiving a registration, removing a member or revoking a share does not delete S3 bytes. The earlier `/artifacts/euid/<euid>` entry opens the same Record page. Retained dashboard/intake screenshots under `docs/assets/` describe the older interface, not the current Library/Add layout.

## Create And Edit A Share

Open a registered Object, Prefix or Set and choose **Share**. Review:

- Name and purpose.
- **Named recipients** or **Public with registration**; both require verified-email sign-in and prohibit anonymous access.
- A finite deadline or explicit indefinite expiry; new shares default to 30 days.
- **File downloads** or **WWW report**, with an HTML entrypoint and bundle root for WWW.
- Share-wide include/exclude patterns and explicit email/domain grants, including optional target/path restrictions and grant deadlines.

An intended internal or external email may have a pending grant before registration. Grant creation does not manufacture a verified identity. Domain grants are deliberate predicates, not organization enrollment. Prefix shares include future matching descendants. Patterns are case-sensitive; `*` stays within a segment, `**` crosses segments, and exclusions win.

The selection preview is bounded. An incomplete preview is not a complete inventory. Use **Sharing** (`/shares`) to reopen a managed share. Editing can replace recipients, deadlines, targets and filters while retaining its EUID. The client submits the reviewed `policy_revision`; a conflict requires reloading and reviewing current state. Expired/revoked shares cannot be reactivated by editing. Revoke a share to remove all access rather than publishing an empty active share.

Invitations are explicit actions after a grant exists. Accepted submission, failed submission and uncertain submission have different receipts. Submission acceptance does not prove mailbox delivery; do not blindly resend a pending or uncertain operation.

## Canonical Links And Friendly Aliases

Copy `/fetch/<share-euid>` as the durable URL. A single object resolves at the root; one prefix retains relative paths; multiple roots use `<target-euid>/<relative-path>` below the share.

Alias controls claim a global lowercase ASCII slug of 3–63 letters, digits and hyphens with alphanumeric ends. Invalid/reserved names and collisions fail. Retiring an alias leaves a permanent tombstone; it cannot be reassigned. EUID and slug links use the same current policy. Existing `/shares/<share-euid>` links redirect public/recipient-only callers to fetch; management detail remains private.

## Recipient Downloads And WWW Reports

An unauthenticated browser follows Login and returns to the exact shared path. An authenticated person without a current grant receives a denial. Public with registration admits any current verified registered identity without making other records visible.

The file page offers individual files, a paginated manifest and **Download all as TAR**. A page states whether more pages follow. TAR is uncompressed and starts only after complete inventory; an interrupted archive restarts. The CLI supports conditional per-file resume and partial-failure receipts. Raw S3 presign issuance is not a managed-share option.

For MultiQC and other HTML reports, share the containing prefix and permitted sidecars, choose WWW, and declare the exact HTML entrypoint/bundle root. Open `/fetch/<share-euid-or-slug>/multiqc.html` in a normal tab. The wrapper establishes an isolated per-context host; CSS, JavaScript, images and data are authorized there. Report scripts cannot use the application's cookies or APIs as the user. Client-generated report exports, including MultiQC image downloads, are supported; network form submission remains blocked.

Revocation applies to subsequent requests, sidecars and TAR members. An already admitted individual response may finish. Previously downloaded bytes cannot be recalled.

## Personal Credentials

Recipients use `/recipient/account` to create and revoke their own read-only credentials. Lifetime is 1–30 days even for indefinite shares. Copy the token once into a private file; never add it to a durable link. Each request evaluates current identity and share rights. Management Account (`/account`) provides corresponding controls within the caller's authorized role.

See [How-tos](how-tos.md#use-curl-wget-and-the-cli) for the CLI's explicit HTTPS origin and private token-file configuration.

## Rebind And Sharing Reports

On an editable S3 record, **Rebind artifact location** requires the reviewed location revision, destination URI, optional object version and a reason. Dewey requires qualified equivalence evidence and rejects mismatches, identity collisions or stale revisions. Artifact/share identities and paths remain; no storage bytes are copied, moved or deleted.

Sharing reports expose owner-authorized lifecycle inventory, date/status/audience/type filters, age and last access, recipients/viewers, request and archive outcomes, and server bytes. Administrators may select a wider population. Full inventory export walks a frozen observation time/digest; inventory drift requires a fresh export. Duration statistics use exact native creation-to-deadline timestamps, so small clock differences may cross an exact day boundary.

Known-share resolution denials are audited without returning target metadata. Unknown/retired identifiers do not invent share relationships. Historical missing events are not reconstructed. Server completion and browser-generated export creation do not prove that a recipient saved bytes to disk.

## Literature, Operations And Embedded TapDB

Literature (`/literature`) retains PubMed search and saved-reference workflows. `/ui/observability`, `/ui/anomalies` and `/admin` require Dewey administrator access on the private management surface; a share grant does not admit recipients to them.

Configured deployments mount the pinned TapDB operator UI under `/tapdb`, with native object/query/DAG pages and Dewey administrator authentication. DAG v2 is at `/api/dag/v2/*` with `/api/dag/manifest`; configured dedicated DAG-reader credentials may use supported API reads. `/graph` embeds the native graph. These are management capabilities, not public recipient routes.

## Evidence Boundary

This guide documents source behavior. The [release ledger](plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) separates software checks, deployed provenance, actual browser/client acceptance and user acceptance. Internal signup is confirmed; internal application admission/scoped access and final user acceptance remain unverified. The release objective is not declared complete here.
