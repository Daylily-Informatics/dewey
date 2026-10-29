# Current continuation state

User requests Dewey tokens up to one year (including READ_WRITE), a global admin overview of all Dewey users/tokens/shares and usage, and per-token/per-share revocation. Implement through existing typed TapDB objects/lineage and existing role checks. Never expose token secrets/hashes. Ordinary users retain own-token access; recipient tokens retain READ_ONLY scope. This is implementation authority, not permission to revoke real credentials or shares as a test.

Baseline: clean Dewey bc5a4515 on codex/dewey-report-performance-12.0.17-20261028; new branch codex/dewey-token-governance-20261029. Login clean c862635d8b9af043424873516e0e937d94b7f58d / 4.1.2. No tests/lint/CI/PR/merge, live revocation, container build or deployment performed. Do not call source changes deployed.

Discovery: 30-day limits exist in Dewey service, recipient request schema/UI, Login request schema/service and provider grant settings cap. Login personal credentials are bounded by provider grant expiry and renewable Cognito credentials. A one-year UI limit alone cannot establish a working one-year token. Keep live provider revocation checks; reconcile provider grant runtime config and Cognito refresh lifetime before production claim. Existing short-lived browser sessions do not need extension. Admin list/revoke services already exist, but admin UI links to own-account token page and lacks global usage views. Existing share audit exists; token request usage lacks explicit token attribution.

Next: implement paginated admin views and typed per-token request audit, increase limits end-to-end, then inspect owning deployment identity/config for the provider horizon. Existing live deployment identities must be refreshed before action. No new budgets, runtime cutoffs, monitoring or secondary QC.

|ID|Requirement|State|
|---|---|---|
|T1|365-day token limits across Dewey and Login|SOURCE COMPLETE; runtime horizon pending|
|T2|Global Dewey user/token/share inventory and usage|SOURCE COMPLETE|
|T3|Per-token/share revocation from admin UI, existing server role checks|SOURCE COMPLETE|
|T4|Provider/runtime expiry alignment and versioned publication|AWAITING USER SCOPE CHOICE|

Historical usage cannot be retroactively attributed to a token if its identity was not recorded. Label coverage start and retain existing share audit. Shared Login remains the authority for identity/user administration; this dashboard inventories Dewey activity and issued access.

## Source implementation checkpoint
Paginated admin users/tokens/shares and token requests implemented. All known Dewey users are derived from native browser bindings and issued personal tokens; this is not a replacement Login directory. Tokens include issuer/roles/status/expiry/request count/last-use and individual revoke; shares link to existing global-authorized activity/revocation controls. New token issue/revoke events use operational lineage, HTTP request usage uses token_request lineage, and share events gain actor email plus token_share_event lineage. Hashes/secret values are excluded from admin responses. Existing recipient-only READ_ONLY boundary remains. Manual source inspection performed; no tests, lint, compile, CI, synthetic calls, live revocation or deployment.

Live read-only inspection: existing Login provider grant2592000 seconds and browser28800 seconds. Both exact Cognito clients in Login sibling plan have refresh validity30 days. User question pending for shared Login clients30→365 days; this impacts other services. Current daycog edit-app CLI lacks a refresh option: owning CLI/API contract must be respected. Source commits may be published for review while rollout is held. Next: receive scope choice, complete the supported configuration path, allocate unused annotated releases, then perform only the approved selected-service rollout. No token/share was issued or revoked during implementation.
