# Dewey Access Logging And AI-Agent Read Access Gap

Created: 2026-06-04T11:07:00Z

## Status

Dewey needs a follow-up implementation pass before Kahlo-issued AI-agent tokens can safely read Dewey search/share-reference surfaces directly.

## Required Contract

- Validate Kahlo-issued AI-agent bearer tokens against an explicit Dayhoff-generated allowlist.
- Accept only read-only endpoint IDs approved for Dewey search, artifact, and share-reference access routes.
- Record every endpoint access with request ID, correlation ID, route template, status, duration, client IP, auth mode, human user, service ID, AI-agent ID, authorizing human, token ID prefix/hash, scopes, and denial reason.
- Keep Dewey share-reference diagnostics sanitized: no raw presigned URLs, bucket keys, versions, or sensitive storage details for unprivileged users.

## Current Gap

Dewey has request/audit hooks in some domains, but current source does not prove uniform all-endpoint access logs with actor/IP/AI-agent provenance or Kahlo-issued AI-agent token validation.

## Acceptance

- Focused tests prove allowed AI-agent tokens can read only approved Dewey search/share-reference routes.
- Revoked, expired, mutating, and non-allowlisted AI-agent requests fail closed.
- Access-log tests prove sanitized principal/IP/request/token fields on success and denial paths.
