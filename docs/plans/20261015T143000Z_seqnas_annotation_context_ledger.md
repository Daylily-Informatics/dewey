# Dewey searchable SeqNAS annotation context

## Current continuation state

Source prepared 2026-10-15. Controlling ledger: `/Users/jmajor/projects/mega_dayhoff/repos_work/kahlo-tapdb-globaldag-20260926/docs/plans/20261015T075127Z_seqnas_performance_annotations_ledger.md`, K20. The user authorized focused file uploads/existing-item links with descriptions and searchable run/transfer names. Baseline 11.0.5 / 56179a2bb7ee05886f4211c1a2bc1046276eb7f0 on codex/dewey-tapdb-globaldag-20260926, initially clean. Final next numeric release is 11.0.6, subject to remote tag absence. EC2-only final builds on i-07df3a933e4839f52; Login dependency first, then Dewey, then Kahlo. Tests source added, execution not authorized twice. No PR/merge, synthetic production contribution, file mutation or schema migration. Next: publish tagged source, EC2 build/selected deployment and readiness observations.

| ID | Work | Owner | Status | Category | Gate | Evidence | Blocker/root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|
| DC1 | Signed descriptions and searchable exact run/attempt context | Dewey | IN_PROGRESS | feature_implementation | User K20 | annotation_api.py, artifacts.py, external_objects.py, tapdb_external_references.py | Actual human upload/link acceptance pending | No created bytes or artifacts claimed |
| DC2 | Final immutable release and selected EC2 deployment | Coordinator | OPEN | active_product_contract | Existing release authority | Baseline live 11.0.5 | Source publication/build outstanding | Preserve other services |

Descriptions stay in signed upload instructions and the registered artifact. Existing-item links require the requesting human's native Dewey edit permission. Context is a typed external object plus authoritative lineage and native external identifier assertion; no invented run EUID. The stable annotation operation identity is explicitly opaque. It stores canonical human subject/email and server time. Native registry search already includes those external objects, making run_name, xfer_name and description searchable. Native idempotency and advisory locks serialize repeated context writes; changing a replay payload fails. Artifact/set permissions and file ownership are retained. File bytes remain entirely Dewey-managed.

Offline test source covers exact URL/attempt validation, opaque identity, edit authorization on replay, signed description/location agreement. No tests or live writes executed.
