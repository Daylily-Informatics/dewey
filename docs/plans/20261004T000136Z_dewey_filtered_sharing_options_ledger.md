# Dewey filtered, recipient-controlled sharing: review and options

## Current continuation state

Updated: 2026-10-04T00:10:37Z (2026-10-03, America/New_York).
Objective: review Dewey and propose options for URL-based sharing of files and S3 prefixes, including selected descendants/patterns, email/domain audiences, expiration datetime, audit and revocation; preserve presigned URLs. Stop after a source-grounded proposal.
Authority: the current user request authorizes review and proposal. No implementation, tests, release, deployment, invitations or share issuance requested. No agents or recurring work started.
Working source: `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-tapdb-globaldag-20260926`, branch `codex/dewey-tapdb-globaldag-20260926`, initial clean HEAD `8077e6b3bd415c72b8a5628b62fd781b6cfcd3b5`.
Completed: source, route, UI, CLI, audit and delivery review; current AWS documentation comparison; proposal below. All four review rows are terminal SUCCESS. Public read-only `/healthz` reports version `10.0.13`, build SHA `92a3c80ccc6a5edd56cc623a4248732cea5f5d4f`; remote `10.0.13` peels to `8077e6b3bd415c72b8a5628b62fd781b6cfcd3b5`. This provenance discrepancy is unresolved; do not claim deployed code matches the tag. Core sharing, registry storage, CloudFront, preview, UI and registry API files do not differ between those commits; native audit/auth/backend integration has later differences. No application implementation or production change made.
Next: user selects delivery/revocation semantics and live-versus-snapshot membership before an implementation plan. Recommendation: extend existing Dewey shares, offer authenticated gateway delivery for recipient-bound access, and retain explicit presigned delivery for large transfers and automation.
Limits: source review and one health read are not recipient acceptance. Runtime CloudFront, recipient onboarding and access-log configuration have not been inspected.

## Gate 0 baseline

- Git status before this document: clean, branch above. Remote: `git@github.com:Daylily-Informatics/dewey.git`.
- Local and remote `main`: `818bf15c7cfd65a351acf6816293057ee2ba8bf6`. This is older than the reviewed working branch; no merge/fetch/reset performed.
- Live health observation: `2026-10-04T00:00:04Z`, HTTP 200, version/SHA above. This establishes only self-reported identity and process health.
- Inspected instructions: supplied OWY/global user policies, applicable `/Users/jmajor/projects/AGENTS.md`, Dewey `AGENTS.md`, and plan-ledger SOP. Dewey is documented as an approved-network customer/collaborator service.
- Source scope: `services/sharing.py`, `services/registry.py`, `services/registry_storage.py`, `registry_api.py`, `registry_access.py`, `auth.py`, UI/CLI sharing, CloudFront signer, storage and audit integration.
- No tests, lint, builds, AWS mutations, messages or production share operations run.

## Review ledger

| ID | Area | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| REV-01 | Baseline | Identify reviewed source and runtime limits | SUCCESS | active_product_contract | Review only | primary | Gate 0 above | | Provenance discrepancy recorded; source and runtime claims separated |
| REV-02 | Existing capability | Trace sharing, access, audit, UI and CLI | SUCCESS | active_product_contract | Review only | primary | Source evidence table below | | Existing primitives and missing guarantees identified; not runtime acceptance |
| REV-03 | Design | Compare recipient-controlled delivery options and limitations | SUCCESS | plan_amendment | Proposal only | primary | Option matrix and linked AWS documentation below | | Four approaches compared, including revocation and hostname limits |
| REV-04 | Proposal | Recommend scoped changes and decisions | SUCCESS | plan_amendment | Proposal only | primary | Proposed policy, enforcement, delivery and acceptance contracts below | | Review/proposal objective complete; feature implementation remains future work |

## Findings and proposal

This document proposes future work; it does not authorize implementation or operation.

### Recommendation

Extend Dewey's existing managed-share model. Use stable authenticated Dewey links as the recipient entry point. Add a file gateway for shares requiring identity checks and revocation on every new request, while keeping short-lived S3 presigned URLs as an explicit delivery option for large downloads and programmatic clients. CloudFront is an optional later delivery optimization, not necessary to provide the requested sharing UI.

Yes, share pages and controlled file URLs can use `dewey.day.lsmc.bio`. `/shares/{share_euid}` already exists. A proposed file route is `/shares/{share_euid}/files/{relative_path}`; the identifier must be issued by Dewey/TapDB, not fabricated. A friendly URL alone does not enforce access: the server must authorize the current recipient and exact requested key.

### Existing source capability

Paths and line numbers below refer to review HEAD `8077e6b`.

| Capability | Source evidence | Current extent / gap |
|---|---|---|
| Individual emails and domains | `dewey_service/services/registry.py:323-368`; `registry_api.py:41-49` | Already accepts named users, domains, audience and `expires_at`; no include/exclude fields |
| Domain matching | `registry_access.py:78-117`; `services/sharing.py:89-120` | DNS suffix matching includes subdomains. No explicit exact-domain switch or per-email domain exception |
| Files, prefixes, sets and mixed targets | `services/sharing.py:173-280,282-434`; `services/registry.py:342-364` | Existing targets and lineage; prefix grants cover future permitted descendants. Sets link the members reviewed at creation; no saved, version-pinned filtered-prefix snapshot contract |
| Stable share URLs and UI | `registry_api.py:309-317,343-349`; `static/registry.js:139-147` | Login-gated page; current page links into general record browsing. Form uses lifetime days, although API supports datetime |
| Revocation and edits | `services/sharing.py:692-734`; `services/registry.py:405-434` | Manager/owner authorization, status/reason/actor/time; removes the grant for subsequent authorization, not credentials already minted |
| Direct S3 delivery | `services/registry_storage.py:189-261`; `storage.py:388-409` | Current registry path creates object presigns and a durable issuance receipt; explicitly reports `download_completion_observed=False` |
| Folder contents | `services/registry_storage.py:135-187` | Bounded S3 listing, path authorization and pagination; current UI name filter is only a filter on the loaded page (`static/registry.js:91`) |
| Prefix manifest | `services/sharing.py:594-601` | `presigned_s3_manifest` marks prefix targets `prefix_not_presigned`; it does not recursively produce a filtered file manifest |
| Share roots/subsets | `services/sharing.py:819-870` | Explicit registered targets under a root; no glob-based selection |
| CloudFront | `cloudfront.py:83-132`; `services/sharing.py:630-679` | Signing primitives exist. Explicit signer and approved origins required. Configuration, origin permissions and runtime use not verified |
| External recipients | `auth.py:323-365`; `services/registry.py:436-485` | Verified broker handoff and external-share entitlement path; invitation prepares a named recipient via shared login. Domain policy alone does not prove arbitrary new domain members can sign in |
| Audit | `services/sharing.py:123-160`; `services/registry.py:386-391`; `audit.py:100-121` | Share array retains the most recent 500 events; operation receipts and native TapDB attribution also exist. Complete delivery logging/retention is not established by this review |
| CLI | `cli/registry.py:98-116,206-214` | Shares list/get/create/update/revoke/invite use the public authorized APIs |
| HTTP/HTTPS references | `services/registry_storage.py:215-220` | Can return an external reference URL. Explicitly states revocation only affects Dewey; original host access is unchanged |

### Delivery options

| Option | Identity and revocation | Dewey hostname | Tradeoff |
|---|---|---|---|
| A. Authenticated Dewey file gateway | Check the current user, active grant, path and expiry on every GET/HEAD/Range request. Revocation blocks new requests once committed; authorization caches must not extend access | Share page and file requests stay on the exact requested host | Best match for recipient-bound sharing. Streaming bandwidth/concurrency, Range/resume and server-side transfer outcome tracking require implementation |
| B. Dewey authorizes, then issues short S3 presigns | Checks identity when issuing each object URL. Revocation stops issuance; an issued URL remains a bearer credential until expiry/credential invalidation | Share entry URL stays on Dewey; actual download uses an S3 URL | Smallest extension of current code; useful for large files. Cannot promise email-bound use of a forwarded presign or immediate recall |
| C. Dewey plus CloudFront | Native signed URL/cookie validates a capability and time window. Stateful viewer authorization is additional work if every request must check identity/revocation | Possible with explicit custom-domain, certificate and routing configuration | Good for high-volume delivery and linked report assets. Arbitrary filtered trees require per-object grants, an isolated materialized prefix, or a real policy evaluator at the viewer boundary |
| D. S3 Access Grants / IAM integration | AWS IAM or directory identities receive scoped temporary credentials; Dewey must map identity, expiration and rule lifecycle | Does not by itself supply a Dewey web portal or Dewey download URLs | Relevant if collaborators need native AWS CLI/SDK S3 access. More identity/infrastructure work than extending existing browser sharing |

AWS describes S3 presigned URLs as bearer credentials and checks expiration when a request starts. A transfer that began before expiration can continue. Temporary signing credentials can expire sooner than the requested URL lifetime. Recommendation for mode B: a configurable 60–300 second credential lifetime, bounded by remaining share lifetime, while retaining explicit existing presign capabilities. This is a proposal, not a configuration change. [AWS presigned URL contract](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)

CloudFront signed cookies suit multiple private files and unchanged file URLs, but their built-in policy is not Dewey's per-email rule store. Inference from the documented verification flow: revoking a Dewey row alone will not invalidate an already-issued native cookie. Cache invalidation is not recipient revocation. [CloudFront cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-cookies.html) [URL versus cookie selection](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-choosing-signed-urls-cookies.html)

S3 Access Grants supports bucket, prefix and object scopes for IAM principals or directory users/groups. Directory integration uses IAM Identity Center; an arbitrary email-domain string is not the native grantee identity. [Grant scopes and principals](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-grants-grant.html) [Directory integration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-grants-directory-ids.html)

### Proposed sharing contract

1. **Source and scope:** use an existing object, prefix or explicit set registration. Keep durable relationships in TapDB lineage. A typed share/policy object stores rule values and revisions; target identifiers in JSON remain display/search denormalizations. Keep HTTP reference sharing distinct from controlled S3 bytes.
2. **Recipients:** accept individual emails and domains, using the shared login's verified identity and canonical subject/issuer. Add an explicit exact-domain versus include-subdomains choice for new policies. Allow separately revocable grants when different audiences need different subsets or expirations. A domain grant needs an explicit email exclusion/deny if one member must be excluded; removing their individual allow entry alone does not exclude them from the domain.
3. **Patterns:** evaluate case-sensitive, root-relative globs. Define `*` as one path segment, `**` as zero or more segments and `?` as one non-separator character. An explicit All choice becomes `include: ["**"]`; an empty include list must not silently mean all. Any exclusion wins within that grant. Exact paths and checked directory selections compile to the same policy representation. Start without unrestricted regular expressions.
4. **Membership:** offer live rules (future matching files included) and frozen membership. For reproducible delivery, freeze a complete reviewed key manifest and pin S3 version IDs where available. A key-only snapshot does not freeze bytes if the key can be overwritten; fail on changed object identity or use an explicitly managed immutable copy. Do not label a partial listing a completed snapshot.
5. **Time:** require a timezone-bearing expiration datetime, store UTC, and display the user's timezone. Validate future expiry and maximum allowed lifetime. Bound every derivative credential by the share/grant expiry, including very short remaining lifetimes. A datetime picker belongs in both create and edit forms.
6. **Revocation:** revoke a whole share or one recipient grant; record actor, reason, timestamp and policy revision. Evaluate current status at every gateway request and every presign issuance. Existing independent access (another share, internal policy or native AWS permissions) remains independent and must be visible in an effective-access explanation. Already downloaded files cannot be recalled. Aborting active streams would be a separate explicit capability.
7. **Audit:** persist separate append-only event records for creation, edits, membership revision, revocation, allow/deny decisions, listing, credential issuance and transfer outcomes. Link them to the share and typed target objects using lineage. Record canonical actor, matched rule/revision, object/version, UTC time and request correlation. Do not put signed URLs, cookies or invitation tokens into the log. Add paginated activity/export with defined retention; keep the 500-event share array as a summary only if retained.

Illustrative proposed policy, not a supported API request or a live share:

```yaml
root: s3://<bucket>/<approved-prefix>/
recipients:
  emails: [johnm@lsmc.com, sandra@lsmc.com]
  domains: [inflectionmedicine.com]
domain_match: exact
selection: live
include: [reports/**, qc/**/*.html, variants/*.vcf.gz]
exclude: [reports/internal/**, '**/*.tmp']
expires_at: '2026-10-17T17:00:00-04:00'
delivery: authenticated_gateway
```

Choosing `lsmc.com` instead of the two named addresses would admit the whole selected domain under that policy. If John, Sandra and Inflection need different content, use separate scoped grants rather than giving all recipients the union accidentally.

### Enforcement and hostname design

- Add one common authorization operation for `(verified principal, applicable grants, action, exact S3 location/version, current time)`. Enforce it on listing, metadata, direct access, raw-URI access, record aliases, set/mixed manifests, report assets and all credential issuance. A filtered share must not create an unrestricted parent-prefix grant in `registry_access.py` or `_storage_locations_batch`.
- Keep a share-scoped recipient browser so browsing from a share retains its root and scope. Generic library/storage routes may combine valid grants, but each grant must contribute only its permitted paths. Explicit protected-child restrictions and issuer delegation limits continue to apply.
- Show only permitted filenames and necessary ancestor directories; do not reveal unrelated names, counts or breadcrumbs. Preserve exact S3 keys, slashes and spaces. URL decoding and traversal rejection must not map one object name to another.
- List lazily beneath the declared root; preview matches using bounded metadata listings and report when preview/counts are incomplete. S3 listing supports prefixes and delimiters, not arbitrary glob evaluation, so broad patterns need application filtering or a persisted index/manifest. Do not read file bodies to select matches. [S3 ListObjectsV2](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html)
- Existing raw listing caches may be reusable if every response receives current authorization filtering. Never share an already-authorized response across different recipients or policy revisions. For immediate new-request revocation, stale authorization decisions cannot survive revocation.
- Gateway file delivery must implement GET/HEAD, Range and resume, disconnect handling, response headers and bounded streaming. The existing report preview is a useful streaming reference, but its token uses the stored issuing principal (`report_preview.py:102-106`); it must not be reused unchanged as proof of the current viewer's identity. Preserve the report sandbox and authorize every relative asset; do not place active report content into an unrestricted authenticated application page.
- The existing Dewey host can serve application and gateway paths through its current ingress. A CloudFront variant needs a single deliberate front door routing application paths to Dewey and delivery paths to approved S3 origins, plus the domain certificate and private-origin permissions. Replacing the hostname in an S3 presign is not a valid custom-domain implementation. [CloudFront alternate domains](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CreatingCNAME.html) [Private S3 origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- Dewey's repo policy currently requires approved-network customer/collaborator ingress. An allowed email/domain does not confer network reachability. Retain the approved-network boundary; globally reachable sharing would require an explicit ingress design decision, not just a share setting. Login onboarding for a new external domain must be established separately from path authorization.

### Specific source corrections before offering these guarantees

1. **Pattern enforcement is missing.** Current schemas reject unknown share fields. The existing loaded-page name filter cannot serve as an access rule. Add validated rules to the public contract and enforce them across all paths above.
2. **CloudFront cookie scope is too broad for object subsets.** `services/sharing.py:653-668` converts an object target into its parent prefix, and `cloudfront.py:87-89` signs `prefix/*`. If that origin contains unshared siblings, the resulting capability can cover them. A whole-prefix cookie also cannot enforce protected descendants after it is issued. Use object-scoped delivery, an explicitly isolated selection prefix, or per-request policy enforcement. This is a source finding, not a claim of observed production exposure.
3. **CloudFront expiration can exceed the share deadline.** The service clamps TTL to remaining lifetime, but `cloudfront.py:94-96,117-119` raises it back to at least 60 seconds. Remove that widening or reject issuance when the requested bound cannot be met. This does not affect the inspected S3 signer, which honors a one-second minimum.
4. **Datetime and domain semantics need an explicit contract.** `_normalize_expiry` currently accepts naive datetimes and uses `astimezone`; domain matching intentionally includes suffixes. Require an explicit timezone and make subdomain behavior visible without silently changing existing shares.
5. **Audit must distinguish credential issuance from file use.** Keep durable existing receipts and native attribution, but do not describe them as completed downloads. Gateway logs can identify the authenticated request and bytes served; raw presigns can be forwarded. S3/CloudFront data-plane evidence is complementary. S3 `GetObject` CloudTrail data events require explicit configuration and incur charges; their presence was not verified here. [AWS S3 data-event logging](https://docs.aws.amazon.com/AmazonS3/latest/userguide/enable-cloudtrail-logging-for-s3.html)
6. **External URLs retain their origin's permissions.** A revoked Dewey redirect cannot disable a public source URL. If the requirement includes arbitrary HTTP/HTTPS sources, enforce origin access through an approved authenticated connector/gateway or explicitly ingest an authorized copy into controlled storage. Do not add a general unrestricted URL-fetch proxy.

### Implementation sequence and acceptance definition

1. Resolve the reported build-SHA/tag mismatch and establish the exact implementation base. Select gateway versus bounded presign revocation, live versus frozen membership, and exact-domain/subdomain behavior.
2. Extend the existing share/policy model and authoritative lineage, common access evaluator, API and CLI. Add bounded selection preview and explicit policy revision semantics.
3. Extend the Share dialog and recipient folder browser; add datetime, patterns, selection preview, per-recipient revocation and activity history. Keep existing presigned delivery available.
4. Implement the selected data path. Add CloudFront only if required for delivery scale or chosen instead of the gateway; do not activate the existing broad cookie path for filtered shares.
5. Define acceptance around named-email and domain access, excluded users/subdomains, exact allowed/denied paths through every route, expiry boundaries, policy changes with warm caches, revocation with active sessions, multiple independent grants, Range/resume, snapshot changes and audit completeness. These are proposed acceptance cases, not authorization to execute tests, issue live shares or send invitations.

Documentation validation: `git diff --cached --check` passed for this proposal. No source tests, lint, builds or runtime sharing operations were executed.

All review rows terminal: yes (4 SUCCESS). Review/proposal objective complete: yes. Requested capability implemented or production-accepted: no; this turn was limited to the requested review and options.
