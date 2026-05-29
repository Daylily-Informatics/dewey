# TapDB Authenticated User Email Audit Pattern

Date: 2026-05-29
Owner: Agent 8
Scope: Dewey 3.0.27 reconciliation, authenticated user email audit metadata.

## Dewey Implementation Note

Dewey records the current browser-authenticated user email on TapDB-backed object JSON payloads through request-scoped audit context and the TapDB backend write boundary:

- Browser-session auth sets the current authenticated Dewey user email from the session principal.
- Service-token auth clears the user email context.
- TapDB `create_instance` writes `created_by_email` and `updated_by_email` only when a current authenticated user email is present.
- TapDB `update_instance_json` writes `updated_by_email` only when a current authenticated user email is present.
- Missing auth or service-token auth does not invent a fallback email.

This pattern keeps audit attribution tied to real user-authenticated routes and avoids caller-supplied or service-token-derived identity.

## Pattern For All TapDB Services

Apply the same pattern across Atlas, Bloom, Ursa, Kahlo, Zebra Day, and other TapDB-backed services:

- Put authenticated-user identity in a request-scoped context at the auth dependency boundary.
- Normalize email to lowercase and fail hard if a route that already requires browser/user auth has no user email.
- Clear audit user context for service-token, API-key, anonymous, and failed-auth paths.
- Stamp `created_by_email` / `updated_by_email` in the TapDB persistence layer, not independently in each route.
- Do not infer user email from service tokens, deployment names, owner fields, local usernames, config defaults, or payload metadata.

Focused tests should cover user create, user edit, and no fallback for missing/service auth.
