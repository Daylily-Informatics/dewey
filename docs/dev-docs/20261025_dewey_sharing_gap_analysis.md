# Dewey sharing gap analysis — 2026-10-25

Status: dated gap baseline with implementation and release disposition updated below.

Baseline: [current capabilities](20261025_dewey_capabilities.md), observed deployed `11.0.10` / `7f6fde5429741780517cf461a615e5b3e5f102f2`. Target: [sharing requirements](20261025_dewey_sharing_requirements.md), SHR-01 through SHR-20. That original review was documentation-only; subsequent approved execution is recorded below.

## Dewey 12 implementation disposition — 2026-10-26

The original comparison below is the **11.0.10 baseline**, preserved for traceability. The user subsequently approved implementation. The [execution ledger](../plans/20261026T010947Z_dewey_12_sharing_release_ledger.md) controls completion; source changes alone do not close live acceptance.

| Requirements | Implemented source | Verified evidence and remaining acceptance |
|---|---|---|
| SHR-01,02,04,05,19 | Schema-3 revisions, delegation, atomic target/grant/expiry edits, preserved history | Native contracts and preserving conversion passed; lifecycle edits/removal/restoration/revocation passed. Internal and external recipient access now verified. |
| SHR-03,06,12,13 | Mixed/pending grants, registered audience, verified Login identities and restricted sessions | Actual confirmed internal account completed native share login, report/sidecars, complete set and management denial. Ordinary management login preserves its existing configured policies; sharing grants no management role. |
| SHR-07,08,09 | Canonical fetch, native global aliases/tombstones, HTTP/range/conditional behavior | Canonical/alias HTTP access and real curl/wget/CLI retrieval passed; revoked credential returned 401. |
| SHR-10,11 | Complete manifests, recursive CLI/resume receipts, streaming TAR, isolated WWW entry/assets | Complete manifest/recursive/TAR delivery and actual external MultiQC with sibling/nested sidecars passed. The 12.0.7 correction also passed all seven selected production plot downloads. |
| SHR-14 | Dedicated ALB and restricted origin/DNS operator | Dedicated ingress active; four targets healthy, public DNS INSYNC, nonmanagement-source boundaries passed. |
| SHR-15,16 | Native events, lifecycle inventory, windowed aggregate reports, complete frozen exports | Deployed 12.0.6 corrects early authenticated denial persistence. All 277 retained events reconcile; the final fixed window contains exactly one external denial and one manager contents read, with zero transfer bytes. Earlier missing denials are not backfilled. |
| SHR-17 | Qualified-equivalence rebind, collision checks, native location revisions | Controlled rebind and unchanged fetch URLs passed. |
| SHR-18,20 | Management/recipient API, GUI/CLI, README and sharing guide | Current docs, machine/browser handlers and live controlled journeys complete; all required ledger rows SUCCESS. Formal user signoff is separate. |

**Dewey12.0.8/Login4.1.1 production engineering and functional acceptance are complete (100%).** Migration preserved42 inactive shares; all113 installed Dewey files equal the tag/main; Login and11 other containers are unchanged by deployment. Current changed-code line/branch gates exceed80%. Existing external, machine/recursive/TAR, lifecycle, alias, rebind, export and audit proofs are retained. The user-supplied internal session now passes native share login/exact report return, isolated sidecars, complete five-file set and management denial. Normal LSMC manager root/Library/Admin access was restored by normal reauthentication. All15 original,9 integration and5 final rows SUCCESS. Formal user signoff is not inferred. [Final closeout](../plans/evidence/20261026_dewey12/release-closeout-12.0.8.json), [internal acceptance](../plans/evidence/20261026_dewey12/internal-acceptance-12.0.8.json).

The final audit receipt preserves earlier helper stops and reconciles the exact retained responses without repeating the denied fetch. Report completeness covers retained inventory/events; it does not reconstruct historical denials omitted before 12.0.6. The original dated baseline below remains unchanged.

The [full-source PR64](https://github.com/Daylily-Informatics/dewey/pull/64) is merged into main as `74b426b`. Main CI40399463503 passed 1,296 Python tests, 5 PostgreSQL contracts and 45 browser-script tests plus quality/security/package-build checks; 2 Cognito E2E cases require a separate pool. Python coverage of 83.63% lines/82.43% branches and browser coverage of 100%/88.79% exceed their independent 80% gates. Release 12.0.8 deploys its explicit empty-scope validation and canonical readiness diagnostic location. All installed application bytes equal merged main; the live readiness response passes the unchanged schema. [Merge receipt](../plans/evidence/20261026_dewey12/pr64-merge-main.json), [runtime provenance](../plans/evidence/20261026_dewey12/running-provenance-12.0.8.json), [main-code binding](../plans/evidence/20261026_dewey12/release-main-code-binding-12.0.8.json). The final internal acceptance receipt closes the previous live-session gap; formal user signoff remains separate.

## Historical 11.0.10 comparison

Sections 1–6 retain the findings and open questions as observed on 2026-10-25. The current 12.x disposition above supersedes their implementation-status statements; their baseline evidence remains unchanged.

## 1. Finding

Dewey has substantial reusable sharing functionality. It already models shares and grants, supports individual files and filtered prefix descendants, accepts mixed internal/external emails, edits recipient policies and finite deadlines, revokes access, streams authenticated bytes, isolates HTML reports, and stores access/transfer events.

**The requested product is not complete.** The main differences are policy and access architecture, not just README wording or adding a route alias:

1. Managed sharing currently requires Tailscale and can additionally require the recipient's direct permission on a protected artifact/ancestor.
2. Global verified-email onboarding and registration-open access are not established by the current Dewey contract.
3. `/fetch/` entrypoints, friendly slug claims, indefinite duration, editable target membership, storage relocation and complete recursive-delivery UX are absent or incomplete.
4. Current raw S3 presigns permit consumption by any holder, conflicting with the requested registered-only sharing rule.
5. Per-share events exist; aggregate lifecycle/usage reporting does not.

Retain the existing canonical share/grant evaluator, revision checks, native lineage, file gateway, personal-token support and isolated report viewer where they satisfy the new contract. A new link-shortening service, separate user database or replacement HTML renderer is not justified by these gaps.

## 2. Classification and evidence discipline

- **Reuse:** source implements the core requirement; authenticated acceptance still needs evidence.
- **Partial:** substantial pieces exist, but additional behavior or integration is required.
- **Missing:** no matching current product contract was found in the matched release/source/live catalog.
- **Policy conflict:** current behavior deliberately contradicts the requested behavior.
- **Dependency unverified:** the owning adjacent system may provide functionality, but it was not proven in this investigation.
- **Documented:** this documentation deliverable is satisfied; future feature changes will require corresponding docs updates.

These classifications describe product gaps, not implementation ledger states. The live health/readiness/OpenAPI/static-asset receipts establish the release baseline, not successful recipient workflows. The browser host was unavailable and no configured personal token was present; no authenticated mutation or test campaign was attempted. Do not turn those evidence limits into either “it works end to end” or “the feature is broken.”

## 3. Requirement-by-requirement comparison

| Requirement | Existing baseline and evidence | Gap / classification | Required change or decision |
|---|---|---|---|
| **SHR-01** File/set/prefix scope | CAP-08/11/18: S3 object, prefix, set and mixed targets; recursive prefix matching, explicit grants and filters. [sharing.py][sharing] | **Reuse**, with semantics to retain | Preserve fixed reviewed set targets and live matching prefix descendants; make the distinction visible. No new descendant-registration system is needed. |
| **SHR-02** Share grants sufficient recipient access | CAP-03/09: creator authority and grants exist; `_protected_share_path` separately intersects explicit underlying/ancestor policies with the recipient's direct permission. [protected path][protected] | **Policy conflict** | Resolve DEC-02: use creator-authorized delegation as the recipient's artifact authority. If non-delegable constraints exist, make them explicit at publication. Do not quietly retain a recipient-ACL prerequisite. |
| **SHR-03** Mixed/new recipients | CAP-09/10: grant validation takes email strings, mixes audiences, and does not query account existence. Explicit invitation delegates to Login. [grant normalization][policy], [invitation][invite] | **Partial** | Keep pending email grants. Complete/prove first-use registration from a shared link and exact verified-email binding without network or pre-existing-service-membership barriers. A source invitation call is not proof of email delivery or completed onboarding. |
| **SHR-04** Edit people/duration/files, revoke | CAP-12/13: revisioned policy edits, recipient/share revoke, filter changes and finite expiry work in source. PATCH allowlist excludes target membership. [share editing][edit] | **Partial** | Add atomic, audited target-membership revisions while retaining share EUID/slug. Changing an ordinary set does not update an existing share's frozen members. Keep content removal separate from record/S3 deletion; do not reopen global DELETE operations to implement unsharing. |
| **SHR-05** Finite/indefinite duration | CAP-13: omitted deadline resolves a finite persisted default; all evaluators/grants require parseable future timestamps and a maximum lifetime. [expiry][sharing], [policy][policy] | **Partial; indefinite missing** | Explicit no-expiry semantics across policy, grants, list predicates, tokens/report-context caps, UI and reporting. Keep finite default and expiring sessions/credentials; do not simulate infinity with a long TTL. |
| **SHR-06** Public with registration | CAP-09: canonical service allows only explicit email/domain recipient shares. Pydantic schema advertises broader audience values that the service rejects. [registry.py][registry], [policy][policy] | **Missing** | Add a distinct all-verified-registered-users audience, isolated from anonymous access and from whole-library permissions. Correct schemas/UI/docs. Domain grants or `authenticated` record metadata visibility do not implement this share type. |
| **SHR-07** EUID `/fetch/` and deep login return | CAP-14/16: `/shares/<euid>` page, files query route and Login next-path support exist. No `/fetch/` source route; `/fetch` observed 404. [HTTP evidence][http], [registry routes][routes] | **Missing entrypoint; reusable delivery/auth** | Decide DEC-01 share-EUID interpretation; route exact object/tree/report paths through the existing policy evaluator. Browser and machine failures must differ appropriately; preserve destination through registration and login. |
| **SHR-08** Human slug mapping | No claim API, persistent slug uniqueness or fetch alias routing was found. Existing “alias” checks in storage policy concern duplicate storage references, not human URLs. [source routes][source-routes] | **Missing** | Native unique slug-to-share relationship, exact host/namespace rules, conflict errors, ownership/history and no silent reassignment. A human slug necessarily has a mapping; keep it within Dewey/TapDB rather than adding another service. |
| **SHR-09** Standard authenticated HTTPS retrieval | CAP-14/15/19: gateway GET/HEAD, single Range/conditions, personal bearer tokens and single-file CLI streaming exist. Raw S3 presign issuance remains optional and forwardable. [gateway][gateway], [CLI][cli] | **Partial; presign policy conflict** | Reuse gateway for new fetch paths. Specify credential acquisition/renewal and auth failures for curl/wget. Resolve DEC-04 and prevent registered-only paths from becoming anonymous bearer links after a redirect. |
| **SHR-10** Whole recursive retrieval | CAP-11: paginated contents and bounded access packages. `create_share_access_package` fails when one page is incomplete; no tree download/archive CLI or route found. [contents/packages][sharing], [CLI][cli] | **Partial** | Complete manifest traversal, explicit inventory/version semantics, preserved paths, collision handling and accountable partial failures; provide the proposed single-object archive representation. Generic HTTP cannot recursively fetch an opaque prefix by itself. |
| **SHR-11** Deep-linked WWW reports | CAP-16: per-context origin, bundle root, current per-asset policy, challenge/handoff, short-lived host cookie and sandbox already exist. No direct `/fetch/.../multiqc.html` entry or proven real report rendering. [preview][report], [session binding][sessions] | **Partial; strong reuse candidate** | Add durable report-entry dispatch and credential renewal flow; retain origin isolation. Include all required authorized sidecars and verify compatibility against actual bundles later. Do not replace isolation with same-origin arbitrary scripts merely to make a URL look simpler. |
| **SHR-12** Verified registration/login | CAP-10/19: shared broker callbacks recognize external-share entitlement; invitation uses the registered Dewey service credential. Callback trusts the broker identity; this review did not establish its verified-email guarantee. [broker principal][auth], [invite][invite] | **Partial / dependency unverified** | Inspect Login/Cognito authoritative email-proof, enrollment, callback, email-change and disabled-account contracts, including personal tokens that currently retain issue-time identity/roles and check their local status/expiry. Confirmation alone is insufficient proof of mailbox verification. Extend the owner service if necessary, not Dewey with another identity store. |
| **SHR-13** Safe domain/tenant organization | Dewey consumes canonical user/role information and records recipient email/domain grants. No domain-organization provisioning implementation was established. | **Dependency unverified** | Review shared Login guest/organization facilities. Prefer share-only identities; if grouping by domain, prevent unintended access to an existing organization and handle consumer mail providers. Organization bookkeeping must not block intentional sharing. |
| **SHR-14** Global access without Tailscale | CAP-09/14/16: `share_context` and `share_routing` enforce private ingress for all managed share/content paths; repo policy describes approved-network exposure. [context][context], [routing][routing] | **Policy conflict / infrastructure dependency** | Adopt an explicitly reviewed public reachability design for auth/fetch/content hosts while preserving authenticated authorization and isolating unrelated services. Update code/config/host routing and controlling exposure policy coherently; a wider DNS/firewall rule alone is insufficient. |
| **SHR-15** Complete audit semantics | CAP-17: native share/grant/target-linked events, policy revisions, server bytes, response completion and failures. Pre-auth/ingress denials need not have a share event; client persistence is explicitly unknown. [events][sharing], [gateway][gateway] | **Partial** | Extend event vocabulary/correlation for new audiences, slugs, membership/location changes, recursive exports and report-entry vs asset activity. Establish coverage and failure reporting without inventing client-confirmed downloads. Preserve existing event history. |
| **SHR-16** Aggregate report | CAP-17: share index plus per-share activity and loaded-page JSON export; no aggregate report/API found. [share index/audit][sharing], live operation inventory | **Missing** | Add authorized inventory and time-window aggregations with exact metric definitions, pagination/coverage, owner/admin scope and export. Old/unused/indefinite shares should be directly reviewable. Do not equate request count, presign issuance or asset count with completed file downloads. |
| **SHR-17** Storage moves preserve links | CAP-01/03: durable identity and lazy resolution exist. Record edit permits only name/description/metadata; registrations are keyed by location/version identity. [registry edit][record-edit] | **Missing controlled rebind workflow** | Agree artifact identity rules and an auditable relocation operation with destination equivalence/version evidence, atomic reference change and cache/history behavior. Moving S3 data independently does not update Dewey automatically. Physical moves/deletion remain separate execution. |
| **SHR-18** API/GUI/CLI and systems | CAP-19/27: share management and file CLI, role-limited personal tokens, GUI controls and API. Managed shares explicitly reject service principals without human identity. [CLI][cli], [context][context], [tokens][tokens] | **Partial** | Reuse personal tokens where adequate and document their registered-user attribution/expiry. Define any additional machine identity need explicitly; do not assume an existing general service API key can consume a share. New fetch/recursive/alias/lifecycle behavior needs interface parity. |
| **SHR-19** Consistent revocation/capacity | CAP-13/14/16: current request policy checks, host boundary, no-store responses, per-process stream caps and isolated contexts. An admitted response may finish. [gateway][gateway], [routes][routes] | **Partial** | Apply one current-policy contract to new URLs, aliases, manifests, archives and content revisions. Decide behavior for policy changes during archive construction and long transfers. Verify no stale export/cache keeps serving a revoked share. |
| **SHR-20** Documentation | This baseline, requirements, gap analysis and new README Sharing section distinguish implemented/requested/evidence-limited behavior. | **Documented for this review** | Keep these review artifacts durable; correct feature schemas/help as implementation changes. The pre-existing README dependency text and old disabled-operation help are separately identified drift, not proof of current functionality. |

All twenty requirements have a comparison row. None of the source-only rows asserts functional production acceptance.

## 4. Reuse boundaries and changes that matter

| Existing component | Reuse value | Boundary that must change or be checked |
|---|---|---|
| Native share/grant/target/event lineage | Persistent authority, revision history, clear recipient ownership | Add new audience/lifetime/member/alias semantics without replacing the graph with copied EUID blobs |
| `normalize_grants`, `_evaluate_share` | One policy evaluator used by lists/downloads/assets | Registration-open and indefinite handling; creator-vs-recipient protection semantics; consistent alias/archive use |
| `modify_registry_share` | Locked policy revision and stale-edit rejection | Target additions/removals are not editable today; removing a member must also constrain current grants and cached inventory |
| Existing gateway | Byte streaming, HTTP semantics and server-side outcome evidence | Fetch path handling, public authenticated ingress, machine UX, recursive exports and scalability evidence |
| Existing report viewer | Per-context origin and per-asset authorization | Deep entrypoint, public content-host reachability, reauthentication and actual MultiQC sidecar compatibility |
| Shared Login invitation/callback | Existing identity authority and external-share role | First-use registration, verified-email proof, organization behavior, disabled-user/token/session lifecycle and exact return path |
| Personal token service | Existing curl/CLI credential model | Expiry/renewal and user attribution must remain clear; it does not supply a new nonhuman share credential contract |
| Share audit/index | Existing raw events and authorized share inventory | Aggregation definitions, denial/asset/export classification, completeness and retention evidence |

This is a dependency analysis, not work assignment, scheduling, implementation sequencing or a multi-agent plan.

## 5. Blocking decisions for document review

1. **Identity in the URL:** adopt the existing share EUID as the canonical fetch identifier, or specify an explicit artifact-EUID policy-selection rule. There should be no guess-the-share fallback.
2. **Delegation:** approve the requested shift from recipient underlying-ACL intersection to a creator-authorized share grant. Determine how any explicitly non-delegable content is represented without creating a recipient approval workflow.
3. **Audience and identity:** agree `Public with registration`, explicit no-expiry behavior, and shared Login's verified-email contract. Public registration does not imply tenant-wide membership or anonymous bytes.
4. **Network access:** the requested worldwide workflow supersedes the existing Tailscale-only share design as a product target. A later implementation must deliberately reconcile the old exposure policy; this review makes no network change.
5. **Download representation and credentials:** decide recursive archive format/limits and credential UX; reconcile raw presigns with “no anonymous consumption.” Existing data and share history must not be silently rewritten.
6. **URL/content lifetime:** settle slug non-reuse, multi-root path layout, fixed/live selection, and identity-preserving storage relocation. These choices determine whether old links remain trustworthy.

The requirements document supplies recommendations for each. No additional feature wishlist is needed before making these decisions.

## 6. Historical evidence questions from the 11.0.10 review

| Evidence question | Why it remains open | Controlling future receipt |
|---|---|---|
| Can a new external email register, verify and return to its private share? | No authenticated browser/onboarding was available; broker implementation/config not inspected | Identity verification evidence plus exact share access result for that identity |
| Can arbitrary outside networks reach only intended auth/fetch/content surfaces? | This review ran from the user's connected workstation; source enforces Tailscale | Explicit deployed host/routing identity and outside-network observation |
| Does the current isolated viewer render real MultiQC and sidecars? | Source is implemented; no real report or preview context was created | Exact share/entry/bundle, authorized assets and denied outside-scope assets |
| Do revocation and recipient/content edits affect every delivery path? | Current source provides request checks; new fetch/archive/slug behavior is absent | Policy revision and subsequent route outcomes, including assets/manifests/archives |
| Does recursive download include every permitted item? | Current packages are one bounded page; no tree downloader exists | Complete manifest, item counts/checksums where available, result/partial-error receipt |
| Can the backing location change with identifiers intact? | No controlled rebind product operation found | Before/after artifact identity and location evidence; unchanged link result |
| Are reported downloads/bytes accurate? | Server outcome events exist; no aggregate reconciliation was done | Defined metric window, raw-event/source coverage and matching aggregate result |
| Do old shares/URLs survive or retire intentionally? | No migration inventory or product disposition was authorized/performed | Later reviewed inventory and explicit per-contract disposition; no automatic deletion |

These are future acceptance needs, not requests to initiate a test campaign now. Existing tests and historical deployments are not substituted for these receipts.

## 7. Completion of this documentation task versus product completion

The requested review packet comprises the current-capability document, requirements, this gap analysis, the README Sharing section, and sanitized evidence. Publication is recorded in the [documentation delivery ledger](../plans/20261025T212629Z_dewey_documentation_review_ledger.md).

The original documentation delivery did not authorize implementation or establish authenticated acceptance. The user subsequently approved the [multiagent execution ledger](../plans/20261026T010947Z_dewey_12_sharing_release_ledger.md), which now controls implementation, release and remaining acceptance. The current disposition above distinguishes those states.

[sharing]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py
[policy]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/share_policy.py
[protected]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py#L305
[edit]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/sharing.py#L590
[invite]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L364
[registry]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L337
[record-edit]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L418
[tokens]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/services/registry.py#L618
[routes]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/registry_api.py
[context]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_context.py
[routing]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_routing.py
[auth]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/auth.py#L303
[gateway]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/share_gateway.py
[report]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/report_preview.py
[sessions]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/preview_sessions.py
[cli]: https://github.com/Daylily-Informatics/dewey/blob/11.0.10/dewey_service/cli/registry.py
[http]: evidence/20261025_dewey_sharing_review/http_observations.json
[source-routes]: evidence/20261025_dewey_sharing_review/source_routes.json
