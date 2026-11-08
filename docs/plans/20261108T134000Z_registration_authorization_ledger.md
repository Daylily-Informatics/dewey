# Dewey registration authorization optimization

## Scope

Continue the user's request to resolve very slow Dewey operations and deploy fixes. Dewey only; no PR, merge, test/lint/coverage campaign, pool/concurrency increase, database/index change, credential/permission change or sibling deployment.

Baseline: production 12.0.28, c380e302eb2a0baa1f0e6109a6b94afb3f54cbe2. Worktree: /Users/jmajor/projects/dewey-registration-pool-20261108. Current branch: codex/dewey-registration-pool-20261108. Planned immutable release: 12.0.29.

## Observed residual bottleneck

The ordinary authorized completion pass after 12.0.28 succeeded for all 16 remaining registrations. Thirteen client operations took 11.11–15.55 seconds; three MultiQC section HTMLs took 122.76–124.60 seconds. One retained-metric read showed the latter three requests executed 187 SQL statements each, with 118.5–119.3 seconds in SQL out of 121.9–123.5 seconds server time (96.64–97.36%). All three sections rebuilt the same 38-object report dependency inventory. Ordinary requests used 82–85 SQL statements and 9.7–13.7 seconds SQL.

The existing aggregate counters prove SQL dominance but do not provide individual statement durations. No successful registration was replayed, no synthetic workload was generated, and no repeated health probe was used for this diagnosis.

## Selected change

Materialize the exact relevant storage records and complete same-scope ancestor/alias candidates once per authorization phase. Evaluate existing direct policy predicates in SQL, then resolve only coordinate relationships and explicit SQL truth flags over those phase-local rows. Preserve current final reauthorization, exact-path scope, missing-policy errors, aliases across versions/templates, archived/explicit ancestor restrictions and atomic auditing. No cross-request permission cache or extra telemetry is intended.

## Release procedure

Commit intended changes and publish an immutable annotated numeric tag from the working branch. Run one selected-service build on EC2 through the established interactive SSM ubuntu path. Retain the prior Compose/manifest, update Dewey only with --no-deps/--no-build/--pull never, and perform one application readiness observation. No fleet bootstrap or database mutation.

## Status

Implementation and independent source review complete. Tests, compilation and benchmarks not run under user policy. Release, build and deployment pending; no unmeasured speedup is claimed.

The single application change is services/registry_storage.py. PostgreSQL MATERIALIZED target/relevant CTEs retain one-statement snapshot consistency; canonical SQL computes direct grants and explicit restrictions. Phase-local combination preserves SQL NULL truth, same-scope aliases across templates/versions, arbitrary string-prefix ancestry, and the existing exactly-one typed-policy failure for primary targets. The admin/maintenance shortcut calls the canonical predicate to preserve recipient-only precedence. Statement count is expected to remain comparable; reduced repeated SQL work is the intended benefit. No instrumentation was added.
