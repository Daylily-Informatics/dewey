# Dewey Access Logging And AI-Agent Read Access Gap

Created: 2026-06-04T11:07:00Z

## Status

SUPERSEDED for local `jem-dev` source by commit `68e7e7a` and release tag
`4.0.1`. Dewey now has the local source pieces for Kahlo-issued read-only
AI-agent validation, broker-backed theme preferences, and common access logging.

Remaining acceptance moved to the Dayhoff final beta ledger:
`/Users/jmajor/projects/mega_dayhoff/dayhoff/docs/plans/20260606T080000Z_final_beta_release_consolidation_ledger.md`.
That acceptance requires the future `jemdev` deployment and must not use
production `day` services.

## Required Contract

- Validate Kahlo-issued AI-agent bearer tokens against an explicit Dayhoff-generated allowlist.
- Accept only read-only endpoint IDs approved for Dewey search, artifact, and share-reference access routes.
- Record every endpoint access with request ID, correlation ID, route template, status, duration, client IP, auth mode, human user, service ID, AI-agent ID, authorizing human, token ID prefix/hash, scopes, and denial reason.
- Keep Dewey share-reference diagnostics sanitized: no raw presigned URLs, bucket keys, versions, or sensitive storage details for unprivileged users.

## Historical Gap

At creation time, Dewey had request/audit hooks in some domains, but source did
not prove uniform all-endpoint access logs with actor/IP/AI-agent provenance or
Kahlo-issued AI-agent token validation. That is no longer the current local
`jem-dev` source state.

## Acceptance

- Focused tests prove allowed AI-agent tokens can read only approved Dewey search/share-reference routes.
- Revoked, expired, mutating, and non-allowlisted AI-agent requests fail closed.
- Access-log tests prove sanitized principal/IP/request/token fields on success and denial paths.
