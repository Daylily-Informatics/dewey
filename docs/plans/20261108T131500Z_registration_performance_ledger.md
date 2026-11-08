# Dewey registration performance release

## Scope and authorization

The user requested resolving the very slow Dewey operations and deploying Dewey with fixes on 2026-11-08. This release is scoped to Dewey only, from the current working branch, with an immutable annotated numeric tag. No PR, merge, test/lint/coverage campaign, index/schema change, capacity increase, credential change or sibling deployment is included. Existing audiences, security and runtime configuration are preserved.

Source worktree: `/Users/jmajor/projects/dewey-registration-pool-20261108`.
Branch: `codex/dewey-registration-pool-20261108`.
Deployed baseline: `12.0.27`, `d4e80077c02563f66493bafe590987040ee37e71`.
Selected next version: `12.0.28`.

## Diagnosis

Two retained registration requests took 25.6 and 29.1 minutes with 616 SQL statements each, approximately 99% of elapsed time in SQL. The shared Aurora writer was CPU-saturated while the application EC2 host was not. Nested session acquisition and post-commit token audit failures caused connection-pool errors and ambiguous responses.

A planner-only review of an existing 22-EUID authorization query attributed 278,622.86 of 288,753.46 estimated cost to the ancestor/restriction anti-check. Its original filter evaluated expensive policy subplans before exact storage-coordinate relevance. A CASE guard enforces relevance first. The equivalent guarded plan changes the alias candidate node to a 9,393.42-cost bitmap heap scan, but total estimated query cost remains 287,795.49. These are planner estimates, not execution measurements or a claimed speedup. No EXPLAIN ANALYZE or production load replay ran.

## Changes

- Reuse the existing transaction for nested storage authorization.
- Authorize discovered report dependencies in batches of at most 100 exact paths, with DB sessions closed before document reads.
- Read documents lazily and reject oversized dependency bodies before caching.
- Keep an authoritative final idempotency lock/check, batch reauthorization, conditional ETag/version HEADs and final policy evaluation before persistence.
- Persist successful registration/replay token audits atomically with the registration receipt; skip middleware's separate audit only for that exact committed response.
- Guard expensive ancestor policy subqueries with the unchanged exact S3 bucket/key/prefix relevance predicate. Relevant aliases and restricted ancestors retain their existing checks.

## Review and limitations

Static source review completed by implementation and release owners. No tests, lint, coverage, compilation or CI campaign was run, following the user's release policy. One prefetch-memory regression found during review was fixed by lazy document consumption and immediate dependency-size rejection.

Final integrity HEADs still hold a database connection. Section registrations may inspect a parent dependency closure again; no cross-request permission cache is introduced. Candidate coordinate scans and other SQL costs remain. Real resumed production work, not a synthetic test campaign, is needed to quantify the latency improvement. No throughput claim is made here.

## Deployment procedure

Use the retained scoped Dayhoff builder on EC2 `i-07df3a933e4839f52`, `us-west-2`, from interactive SSM as ubuntu. Build only `--service dewey` using the current manifest as base and the final immutable tag. Preserve prior Compose and manifest for recovery. Update only Dewey with native Compose `--no-deps --no-build --pull never --wait`; no fleet bootstrap or schema operations.

The current image/Compose has no Docker healthcheck, so native Compose wait establishes running state only. Perform one application readiness observation after deployment through the established approved local diagnostic path. Do not add repetitive success probes.

## Status

Implementation and source review complete. Source publication, EC2 build, deployment and application readiness remain pending. Release provenance and native outcomes will be appended after completion.
