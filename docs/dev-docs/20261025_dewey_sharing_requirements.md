# Dewey sharing requirements — 2026-10-25

Status: proposed product requirements for user review. No implementation, deployment, migration, invitation, or multi-agent implementation plan is authorized by this document.

Baseline: [Dewey capabilities and feature analysis](20261025_dewey_capabilities.md), deployed release `11.0.10`. Requirements below describe the desired product, including changes to existing behavior. They do not assert that the features already work.

## Approved execution decisions — 2026-10-26

The user approved **Dewey 12.0.0 + Login 4.1.0**, scoped Dayhoff ingress and preserving conversion. The [controlling ledger](../plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) owns validation/deployment status. Deployment preparation required immutable corrective patches: **12.0.1** preserves the existing logout service query; **12.0.2** limits template comparison and native export to the explicitly selected release templates. Login remains 4.1.0. Requirement IDs below remain stable; earlier proposed choices are superseded as follows:

- Canonical fetch identity is the share EUID; aliases are global atomic claims with permanent tombstones.
- Creator delegation authorizes verified recipients without independent artifact ACLs. Named recipients and Public with registration never permit anonymous access. New external users are share-only, without automatic domain tenant membership.
- Omitted expiry means 30 days; explicit null means indefinite. Revisions atomically change recipients/targets/filters/expiry. Conversion preserves identities, recipients, scope, lifecycle and history; ambiguity blocks cutover.
- Collection delivery is uncompressed streaming TAR after complete inventory; manifests and resumable per-file CLI retrieval handle trees. TAR restarts; admitted individual-file responses may finish, while later requests/members recheck policy.
- Managed raw S3 presign issuance is retired, with old issued URL deadlines explicitly tracked. WWW reports use isolated per-context content hosts and current asset authorization.
- Login retains encrypted provider credentials and supplies opaque bindings. Introspection checks current enabled/verified-email state and provider revocation with positive caching at most 60 seconds. Personal credentials are finite; explicit SES invitations have accepted/failed/uncertain receipts.
- Dedicated HTTPS ALB and restricted private 8443/8444 listeners expose recipient routes only. Existing shared 443, private management, tailnet/backchannels and sibling services remain preserved.
- Rebind requires complete qualified content equivalence and collision checks, with native location history. Physical S3 moves/deletes are excluded.
- Changed-code tests, one isolated PostgreSQL contract group, one integrated focused pass and bounded controlled production acceptance are approved. Full main CI, PR creation and merges remain a separate later phase.

See [Managed sharing](../sharing.md) for implemented interfaces and operational limits. This amendment is not a deployment or acceptance receipt.

## 1. Intended outcome

Dewey should be the durable, human-usable and machine-usable entrypoint for important stored artifacts. Users and systems should retain Dewey identities and HTTPS links while Dewey resolves the current authorized storage location. Internal, external and worldwide recipients should be supported without giving them direct S3 credentials or requiring them to join the LSMC network.

A sharing user intentionally chooses recipients. The share grants access; the recipient does not need pre-existing artifact permission, an LSMC organization membership, or a pre-existing Dewey account. At access time, Dewey must establish who the recipient is and verify their email. **No anonymous share consumption is allowed.**

Two content behaviors are required: downloadable files/recursive collections and `www` HTML report bundles with their permitted sibling/subdirectory assets. Audience is a separate choice: named recipients or **Public with registration**. Both audiences require authentication. A share can mix LSMC and outside recipients, expire, be revoked, or explicitly remain indefinite for registered users.

Interpretation of the storage goal: backing S3 locations may change without breaking durable Dewey links. Original direct S3 links may cease to work. A successful storage move must not silently turn an artifact into different content.

## 2. Terms and proposed identifier contract

| Term | Meaning |
|---|---|
| Artifact EUID | Existing persisted identity for an object or prefix; identifies the content/storage reference |
| Set EUID | Existing persisted selection of artifact objects/prefixes |
| Share EUID | Existing persisted identity for one access policy, target selection, lifecycle and audit history |
| Recipient | Registered identity with a confirmed email, or an email grant awaiting that identity's first verified use |
| Share manager | Creator/owner or appropriately authorized administrator who may change the share; downloading does not automatically grant management or resharing |
| Named-recipient share | Access is restricted to explicit email grants; existing deliberate domain grants can remain an additional capability |
| Public with registration | Any registered, authenticated identity with verified email may access this share while it is active; no prior individual invitation is required |
| Download share | Files/prefixes/sets delivered as attachments or a complete recursive collection |
| WWW share | Explicit report entry file and authorized bundle root, rendered with linked HTML/CSS/JS/images/data |

**Recommended interpretation for `/fetch/<DEWEY-EUID>`: use the existing share EUID.** An artifact can belong to several shares with different recipients, deadlines and selections. An artifact identifier alone does not identify which policy to use. Selecting a share EUID avoids a separate opaque-link mapping service and makes revocation/audit unambiguous. Artifact EUIDs remain the storage targets. The user specifically also described slug-to-share-EUID mapping; this interpretation keeps both URL forms consistent. This is a proposal to review, not a silent decision to change existing routes.

Proposed public shapes, with placeholders rather than invented persisted EUIDs:

```text
https://dewey.day.lsmc.bio/fetch/<share-euid>
https://dewey.day.lsmc.bio/fetch/<share-euid>/<root-relative-path>
https://dewey.day.lsmc.bio/fetch/<share-euid>/multiqc.html
https://dewey.day.lsmc.bio/fetch/<human-chosen-slug>/multiqc.html
```

A single-object share can return its object at the root. A single-prefix/report share preserves its relative tree. A multi-root set needs an unambiguous namespace: recommend `<target-euid>/<relative-path>` beneath the share root. Two selected roots containing the same filename must never overwrite one another or resolve by guesswork. A share's identity and aliases do not change when its reviewed policy/content selection is edited.

## 3. Normative requirements

“Must” is required for the requested product. Concrete defaults marked **proposed** need review. Acceptance examples are future criteria, not instructions to run tests now.

| ID | Requirement | Required result / acceptance criterion |
|---|---|---|
| SHR-01 | File, set and recursive prefix scope | Create a share for one file, several selected files, one or more directories/prefixes and all matching subdirectories. Retain exact relative keys and exclude controls. State whether selection is live or fixed; do not silently change its meaning. |
| SHR-02 | Intentional delegation is sufficient | Verify the creator's authority to share the selected content. Do not require the recipient to already possess the underlying artifact/ancestor ACL, S3 rights or organization membership. A valid share grant authorizes that recipient within its scope after identity verification. Unshareable content must be explained to the creator before publication, not unexpectedly denied because the recipient lacks an independent ACL. |
| SHR-03 | Mixed recipients and pending identities | Accept any syntactically valid intended email, including a new external address. Permit internal and external addresses in one share. Record pending grants without manufacturing a verified user. The new person can register/verify from the shared-link flow and then use the same URL. No blanket domain or organization membership is inferred from an individual grant. |
| SHR-04 | Editable lifecycle and contents | Managers can add/remove recipients, change expiry, revoke the share, add/remove selected objects/prefix targets and change included paths. Keep the same share EUID and aliases; publish an atomic policy revision and audit changes. Stale concurrent edits fail explicitly. Removing content from a share removes access, not the S3 object or artifact registration. |
| SHR-05 | Finite and indefinite duration | Default to a finite lifetime; **proposed default: 30 days**, subject to review of the actual persisted default. Allow explicit indefinite duration only with registered/authenticated access. Represent “no expiry” explicitly rather than a far-future timestamp. Share expiry and credential/session expiry remain separate. Show indefinite status, creation age, last access and review need; indefinite is never anonymous or irrevocable. |
| SHR-06 | Two audience types | Named-recipient shares and `Public with registration` must be distinct UI/API choices. Registration-open means any verified registered email can access, including people unknown to LSMC. It does not expose the artifact library or other shares, grant tenant-wide privileges, or imply listing the share in a public directory. Mixed internal/external grants work in named-recipient mode. |
| SHR-07 | Stable Dewey fetch URLs | Resolve existing share EUIDs directly at `/fetch/<share-euid>` and preserve deep paths. Authenticate browser visitors and return to the exact authorized entry path after login/registration. A signed-in unshared person is denied without names, bytes, listings or sidecars leaking. Machine unauthenticated requests receive an explicit 401/auth requirement rather than a successful download containing a login page. |
| SHR-08 | Human URL mappings | Managers request a human-chosen URL-safe slug mapped to the share EUID. Grant it only if available; collision/reserved/invalid names return an explicit error, with no automatic suffix or reassignment. EUID and slug URLs share identical policy, lifecycle and audit. Aliases are owned and audited Dewey records/relationships, not another mapping service. |
| SHR-09 | Standard HTTPS file consumption | A recipient can fetch authorized bytes through HTTPS using a browser, curl, wget or another client supporting credentials. Support GET, HEAD, Range/resume, relevant conditional responses, MIME type, filename and size. Preserve exact URL encoding; reject ambiguous/traversal paths. Keep S3 locations and credentials out of durable share links. Do not use a transferable raw S3 bearer URL as the implementation of “registered users only.” |
| SHR-10 | Complete recursive retrieval | Provide a complete, paginated manifest and a supported tree download that preserves paths. Also provide a downloadable collection/archive representation for clients that can consume only one object URL. Final archive endpoint/format is a review decision. Do not represent an arbitrary directory as if plain curl downloads its children automatically. Report incomplete enumeration, changing selection, failed files and resumability honestly; never call a truncated page a complete download. |
| SHR-11 | WWW/report bundle behavior | A share declares an exact report entrypoint and bundle root. Opening `/fetch/<share-euid>/multiqc.html` prompts for login if needed and, for an allowed verified identity, renders the report with every authorized relative sibling/subdirectory dependency. Recheck policy for assets and reloads; exclude paths outside the selected bundle. Report scripts must remain isolated from Dewey application credentials/APIs. Entry URL can be Dewey while rendering uses an isolated content origin. |
| SHR-12 | Shared verified identity onboarding | Reuse shared Login/Cognito for sign-in, registration, email proof, account recovery and identity lifecycle. Require trusted verified-email evidence, not just an entered address or an administrator-confirmed account. Preserve the requested destination through onboarding. An email change requires verification/rebinding; old grants must not automatically migrate to an unrelated new address. |
| SHR-13 | Organization/tenant handling without unintended access | Do not make tenant admission a prerequisite to consuming an intentional share. Prefer existing Login guest/share-only identities and organization facilities. If domain grouping is needed, associate/create a share-only domain group through the owning identity service and reuse it for later eligible users. Domain grouping must not confer organization admin, existing org data visibility, or cross-service roles. Treat shared mail providers separately; `gmail.com` is not one customer tenant. |
| SHR-14 | Worldwide recipient reachability | An intended recipient outside LSMC and outside Tailscale must be able to reach the approved authentication and fetch/report surfaces. Authentication remains mandatory. Explicit service-host, TLS and content-host configuration replaces the current managed-share Tailscale prerequisite for this use case; no broad sibling-service exposure or wildcard fallback routing is implied. |
| SHR-15 | Durable share/access audit | Persist creator/manager, changes, recipients/grant history, content scope, lifetime, policy revision, grant/revoke decisions, access outcomes and transfer observations with timestamps/correlation. Record successful and denied access without disclosing private names to unauthorized readers. Distinguish credential issuance, request admission, report views/assets, server bytes, server response completion and client-confirmed receipt. Preserve history after removal/revocation. |
| SHR-16 | Useful aggregate sharing report | Provide authorized counts by audience/content type/status, finite-duration buckets and indefinite count; created/expired/revoked/active shares; age, last access and unused/old shares; recipients/unique viewers, report views, file requests, bytes and transfer outcomes. Filter by owner/date/status/type, drill into a share and export a complete report with coverage/time-window metadata. Owners see their shares; appropriately authorized admins see the wider inventory. |
| SHR-17 | Storage relocation without broken links | Provide an explicit, audited rebind/move-of-reference workflow for backing S3 locations that preserves artifact EUID, share EUID, slug and relative fetch paths when content identity is preserved. Verify the destination identity/version before switching, keep lineage/history, fail clearly if content is missing or differs, and invalidate affected caches. This does not authorize physical S3 moves/deletes or silent fallback between locations. |
| SHR-18 | Human and machine interfaces | Provide the required lifecycle via API and GUI, with CLI support for machine retrieval and common share administration. Reuse existing personal-token capabilities where sufficient; machine credentials must identify a registered owner and stay within current share rights. Never place permanent tokens in shared URLs. Explicitly document acquisition, expiry/renewal and failure behavior; indefinite shares still use expiring credentials. |
| SHR-19 | Consistent revocation and bounded delivery | Current policy applies to EUID URLs, slug URLs, manifests, archives, listings, report assets and machine access. Revocation/removal blocks subsequent requests. Define the boundary for an already admitted response and any archive already being assembled. No promise to recall downloaded bytes. Preserve bounded listing/streaming, explicit capacity failures and usable retry/resume behavior for large sequencing artifacts. |
| SHR-20 | Faithful product documentation | README, API schemas and CLI/GUI help must distinguish supported behavior, forbidden operations, permission requirements and evidence limits. Publish copyable EUID/slug and authenticated download/report workflows. No claimed end-to-end capability based only on health, route presence or a source test name. |

## 4. Concrete user journeys

### Private external file delivery

1. An authorized internal user chooses a registered file (or selected files), enters an outside email that has never used Dewey, chooses a deadline and creates the share.
2. Creation stores the grant and stable fetch URL. Email invitation is a separate explicit send action unless the user later selects a different product default; copying a URL requires no email delivery.
3. The recipient opens the URL from an ordinary internet connection, registers/signs in through shared Login and verifies the intended email. An existing registered recipient signs in directly.
4. Dewey grants only the selected share scope. An unlisted colleague opening the forwarded URL gets no content.
5. The manager adds another recipient, removes one, shortens/extends the deadline, or removes a file without changing the link. A subsequent request sees the new revision.

### Recursive download for a person or system

1. A prefix/set share clearly identifies live prefixes versus fixed members and presents the selected scope.
2. The recipient obtains credentials through the supported identity/token flow; curl/wget sends credentials in a header or private cookie file, not in a durable URL.
3. A manifest enumerates every selected target/path with size/version/checksum where available and an explicit completeness indicator. A supported client walks all pages; the archive representation provides a single downloadable object for a generic URL consumer.
4. Retries do not silently skip files or overwrite collisions. The result reports success/partial/failure and the exact manifest/selection revision used. Source changes during collection produce an explicit result, not an undocumented mixture.

### WWW/MultiQC report

1. The creator selects the HTML report and the bundle root containing its required sidecars, excluding unrelated files. A share of the HTML object alone is insufficient when siblings are needed.
2. A recipient follows the human-facing `/fetch/.../multiqc.html` link. Login/registration returns them to that exact report.
3. The Dewey entry page initializes the existing isolated rendering mechanism. Relative CSS, JS, images and data files load only when authorized; report code cannot call the application as the user.
4. An unshared or revoked identity cannot fetch the entry document or a guessed sidecar URL. Expired report sessions renew through the authenticated entry flow without changing the durable link.

### Public with registration and indefinite sharing

1. The creator explicitly selects **Public with registration** and sees that access is open to every verified registered user, including future users.
2. Visitors must register/verify/sign in before viewing or downloading. Registration grants no broader application or tenant authority.
3. The creator normally sets a finite deadline. Explicit indefinite duration remains valid only while the share is active and the viewer is registered/authenticated; revocation still applies.
4. The audit report identifies old/unused/indefinite shares so an owner can review them. This specification does not create reminders, scheduled reports or automatic cleanup.

## 5. Decisions and recommendations that materially affect feasibility

| Decision | Recommended resolution | Why it is necessary |
|---|---|---|
| DEC-01: Which EUID is in `/fetch/`? | Use the existing **share EUID**, with artifact/prefix EUIDs as targets | An artifact can be shared under multiple incompatible policies; guessing a policy undermines predictable revocation and the “no extra mapping layer” goal |
| DEC-02: What does a valid share override? | Recipient grants supply artifact access; enforce the creator's delegation rights at selection/publication and preserve explicit non-delegable constraints if the product defines any | Current protected-ancestor checks can defeat a deliberate share. Retaining the current recipient-ACL intersection would not fulfill the request. A general read right must also not silently become permission to redistribute |
| DEC-03: Domain organizations | Reuse shared Login identities; default to guest/share-only scope. Use domain grouping for organization/catalog purposes without broad tenant membership or implied access | Email-domain grouping alone does not establish an organization administrator or entitlement to unrelated data; public email providers cannot be treated as one customer organization |
| DEC-04: Raw S3 presigns | Exclude forwardable presign consumption from the new registered-only managed-share contract. Resolve existing-share migration explicitly before changing production | Raw presigns are bearer credentials. Sign-in at issuance does not authenticate the eventual consumer. This is a real conflict with “no anonymous shares,” not a naming issue |
| DEC-05: HTML origin | Keep the durable `/fetch/` entrypoint and retain isolated report execution beneath the existing configured content origin | Serving arbitrary report scripts directly in the application origin risks using the viewer's application authority. The existing isolated viewer already addresses this; replacing it is unnecessary |
| DEC-06: Recursive delivery | Provide a complete manifest plus a supported tree workflow; add an explicit archive representation for a single URL | HTTP retrieves representations, not implicit directory trees. Wget recursion needs links to follow; curl does not infer a tree from an S3 prefix |
| DEC-07: Fixed versus live content | Preserve current explicit member lists and live prefix semantics, label them clearly, and snapshot each recursive export's selected inventory | Silent expansion or a partial inventory would undermine what the sharer intentionally selected and what the recipient downloaded |
| DEC-08: Stable storage identity | Treat location changes as controlled reference revision with equivalence evidence; distinct content gets an explicit new version/identity | An unchanged link is useful only if its identity and provenance remain meaningful |

Cognito can verify mailbox control, but a confirmed account is not necessarily a verified email. That distinction supports SHR-12; the exact deployed pool/broker contract still needs inspection. [AWS Cognito confirmation and verification](https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html).

S3 presigned URLs confer access to their holder until applicable expiry/credential limits, supporting DEC-04. [AWS S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html). Wget's recursive HTTP behavior follows links in retrieved documents, supporting DEC-06; it does not discover a private storage tree from an opaque URL. [GNU Wget recursive retrieval](https://www.gnu.org/software/wget/manual/html_node/Recursive-Retrieval.html).

### Slug rules proposed for review

- One global namespace under the exact Dewey host; lowercase ASCII letters, digits and hyphens, 3–63 characters, alphanumeric first/last character. Show the normalized choice before submission.
- Reserve application/control names and the canonical EUID namespace; path separators, encoded separators and dot segments are invalid.
- Atomic uniqueness at persistence; concurrent requests for the same slug have one winner and an explicit conflict for the other.
- Persist alias-to-share relationships using Dewey/TapDB typed objects and lineage. Do not create an independent link-shortener database or infer relationships from copied EUID text.
- Retain revoked/retired aliases as tombstones so an old forwarded link cannot later point to somebody else's content. A share may have aliases, but an alias never bypasses policy or moves to a different share silently.

### Measurement definitions proposed for review

| Measure | Definition / required caveat |
|---|---|
| Shares created | Distinct persisted share EUIDs created within the report window, not policy revisions |
| Active shares | Not revoked, currently started, finite expiry in the future or explicitly indefinite; report snapshot time |
| Duration | Finite lifetime from creation/start to deadline, separately from actual time active before revoke; indefinite is a separate category |
| Accesses / unique viewers | Authorized access events and distinct verified subjects, separated from denials and background report assets |
| Report views | Successful report-entry/context starts; asset requests reported separately, not each counted as a new report view |
| File downloads | Explicit file GET attempts and server-completed responses; range requests/retries and archive requests need correlation/deduplication. Do not count HEAD/304 as downloaded files |
| Bytes served | Server-observed response bytes; range/retry bytes included and identified. Different from unique source bytes or client-persisted bytes |
| Client receipt | Only reported when a supported client supplies verifiable completion evidence; otherwise unknown, even for server-completed responses |
| Old / unused | Age and last successful access relative to a reviewer-selected threshold; never-accessed shares retain that status rather than a fabricated date |
| Report coverage | Time window, source watermark, pagination completion, retention limits and unavailable observations; never imply a global total from one authorized page |

## 6. Ownership boundaries

| Owner | Responsibility |
|---|---|
| Dewey | Share/target policy, fetch routing, slug claims, authorized manifests/downloads, report entry/viewing, audit events and reporting; stable artifact resolution |
| Shared Login / Cognito | Registration, verified-email identity, login/recovery, guest/service entitlements, organization association and identity revocation contracts |
| Dayhoff infrastructure | Explicit global reachability for approved auth/fetch/content hosts, TLS, proxy assertion/trust design and isolation from unrelated services |
| TapDB | Persisted typed identities, lineage, uniqueness/claim guarantees and auditable state; Dewey owns application policy |
| S3/storage executor | Stored bytes, version/checksum evidence, physical copy/move operations when separately requested; Dewey does not silently relocate or delete data |
| DayOA / DYEC / Ursa / Kahlo | Produce/register/use artifacts through existing contracts; scientific QC, workflow completion and clinical acceptance remain with their owners |

## 7. Review gates before an implementation plan

1. Agree on DEC-01 through DEC-08, especially EUID meaning, recipient-ACL override, global ingress, presigns and recursive archive delivery. These are product/architecture choices; this document itself does not mutate any policy.
2. Inspect the actual shared Login/Cognito onboarding and email-proof contract, effective sharing configuration, content hosts and public network path. Record what is confirmed versus source-only.
3. Decide migration/disposition for existing shares and URLs without changing published tags, source objects or deployed policy during this review.
4. Agree the bounded acceptance set: existing/new internal and external identities; mixed/private/registration-open audiences; wrong/unverified email; grant/content edits; finite/indefinite/revoked state; EUID/slug collision; recursive pagination; report sidecars; curl/wget; storage rebind; and audit reconciliation.
5. Only after document review and an explicit request, create the later multi-agent ledgered implementation plan. Tests, release/deployment, live invites, network changes and destructive work retain their separate authorization requirements.

No extra collaboration suite, public search directory, anonymous magic links, share-based editing of file contents, background monitors, billing system, or automatic content cleanup is proposed. The additions above address the requested workflows or concrete blockers to them.
