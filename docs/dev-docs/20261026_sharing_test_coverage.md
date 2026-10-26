# Dewey 12 sharing validation and coverage contract

The release requires at least **80% line coverage and 80% branch coverage of added or modified executable code**, with separate gates for Dewey Python, Dewey browser JavaScript, Login Python, and the maintained Dayhoff ingress/build tools. A passing combined average cannot hide a failing group. Coverage does not replace behavioral assertions, native PostgreSQL contracts, deployed delivery checks, or user acceptance.

The user approved the expanded changed-code coverage pass on 2026-10-26 after requesting extensive tests for the new functionality. Full main-suite CI, PR creation, and merging remain a later phase. Feature-branch pushes do not run these workflows. Local validation uses the existing Python environments, mocked network/build boundaries, and locked Node test tooling; no laptop container builds are permitted.

## Measurement

`scripts/check_changed_coverage.py` intersects Git added/modified lines with measured executable lines. Branches count when their origin line changed. It reports each file, missing lines and branch alternatives, the resolved baseline commit, measured HEAD, working-tree state, thresholds, and any unmeasured files. An unmeasured changed source file fails the gate. Removed lines, comments, and unchanged legacy code are outside this change-specific denominator; this is not a claim of 80% whole-repository coverage.

| Gate | Immutable release baseline | Source scope |
|---|---|---|
| Dewey Python | `11.0.10` | `dewey_service/` Python files |
| Dewey browser | `11.0.10` | Changed JavaScript under `dewey_service/static/` |
| Login Python | `4.0.5` | `lsmc_oauth_login/` Python files |
| Dayhoff tooling | `0b40c85a1b9ee9f6878092bd9ab6640fe148cf2d` | `scripts/dewey_recipient_ingress.py`, `scripts/build_push_container_release_manifest.py` |

Python measurements use coverage.py with branch tracing. Browser tests execute the shipped scripts through Node's VM with their actual filenames, then use the standard [c8 V8/Istanbul conversion](https://github.com/bcoe/c8) and the same changed-source gate. Each inline JavaScript branch alternative remains distinct. DOM and fetch doubles exercise actual handlers and request payloads; they do not claim real browser layout or authentication success. Those have separate deployed evidence.

Main/PR CI separates unit coverage from a native PostgreSQL job. The native job creates a fresh loopback-only `dewey12_contract` database through the existing supported TapDB lifecycle preparer and passes an explicit matching DSN/config to the contract group. The unit job explicitly excludes that group because it has no database; the native job does not silently skip it or infer any production connection. This CI wiring is authored for the later main/PR phase and is not a claim that GitHub Actions ran during this release.

The gate utility itself has focused tests for exact thresholds, empty denominators, missing-file failure, added/deleted-line parsing, and distinct inline JavaScript branches. Coverage instrumentation dependencies are test-only and do not change Dewey, Login, or shared-library runtime pins.

## Required behavioral groups

- **Policy and lifecycle:** verified email, pending/mixed recipients, registered-public audience, no anonymous admission, default/indefinite expiry, current grants, delegation restrictions, stale edits, native envelope ownership, atomic rollback, and historical lineage preservation.
- **Aliases and migration:** invalid/reserved names, global claims and tombstones, ownership corruption, preserving inventory/apply/verify, reviewed digest and source drift, idempotent conversion, and ambiguous records. Original isolated PostgreSQL evidence remains the concurrency/transaction proof; persistence fakes are not a substitute.
- **Delivery and reports:** browser versus machine admission, path traversal, MIME/filename/validators, HEAD/ranges/conditions, complete pagination, cursor invalidation, archive source changes and cleanup, per-member policy checks, recursive receipts/resume, isolated report context and sidecars.
- **Identity and onboarding:** Cognito current state, provider revocation versus outage, verified canonical identity, expiry, independent personal credentials, restricted public callbacks, share-only accounts, SES accepted/failed/uncertain receipts, and private state initialization.
- **Rebind and audit:** metadata-only destination equivalence, identity collisions, stale location revisions, stable artifact/share links, event reconciliation, precise server completion/bytes, windows, filters, inventory watermarks and completeness.
- **Interfaces and release:** API/GUI/CLI payload parity, null versus omitted expiry, explicit obsolete-contract rejection, secret-free output, retained configuration authority, exact ingress resources/listeners, source/tag/OCI build arguments, and unchanged sibling services.

## Execution and receipts

Run the selected changed-code groups once with coverage, then rerun only new, changed, or failing tests. Coverage may be accumulated only while the measured production source is unchanged; preserve each command, exit result, and intermediate coverage snapshot. A source correction invalidates affected measurements and requires its affected tests again. Do not increase coverage by skipping failures, removing policy checks, or adding exclusion pragmas.

The final expanded selection passed **771 tests with zero failures or skips**: 525 Dewey, 148 Login, 55 Dayhoff and 43 browser-script tests. All four independent changed-code gates passed:

| Group | Changed line coverage | Changed branch coverage |
|---|---:|---:|
| Dewey Python |96.26% (1777/1846)|90.51% (706/780)|
| Dewey browser JavaScript |100% (108/108)|88.15% (186/211)|
| Login Python |96.95% (476/491)|95.90% (117/122)|
| Dayhoff release/ingress tooling |98.74% (391/396)|98.41% (124/126)|

The [coverage summary](../plans/evidence/20261026_dewey12/expanded-coverage-summary.json), [exact commands](../plans/evidence/20261026_dewey12/expanded-validation-commands.json), individual gate receipts, logs and JUnit reports are committed under the [release ledger](../plans/20261026T010947Z_dewey_12_sharing_release_ledger.md). Measured source-file SHA256 values bind the receipts to the released code. The earlier isolated PostgreSQL result remains the native contract proof and was not rerun for this expansion. Archived operator recipes have reviewed execution receipts and are outside the maintained-product coverage denominator. Full main CI and human acceptance remain separate.

The final container is built from an immutable annotated tag on EC2, once per actual source correction. Build tests mock Docker/AWS execution and verify command/provenance contracts; the real EC2 image digest and deployed OCI/package checks establish release provenance. Login and unrelated images are not rebuilt for test-only changes.
