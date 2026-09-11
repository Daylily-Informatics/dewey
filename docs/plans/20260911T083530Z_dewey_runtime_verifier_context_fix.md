# Fresh runtime verifier context repair

The `runtime-verify` phase now establishes TapDB's public process context after
the existing absolute/private config, strict lane/scope, image-version and new-output
checks, before creating fresh native engines. This addresses the same no-path metrics
settings call as the application repair in `5251d1e6a42452284b36dc511c73b1446ff21ee0`.

The bootstrap/bind plan/apply bodies and inputs are unchanged. O must retain the
historical helper with SHA256
`9921210bd5b3ee4fcc52f06184dd88a6efa986e23e608f3672ccffcd529372f2`
alongside its actual principal receipts. Stage the corrected helper in the new mounted
acceptance capsule for fresh-session verification; do not reapply bootstrap/bind or
rewrite previous evidence.

Four new regression cases cover native engine/metrics construction without an existing
shared CLI context and rejection before binding for invalid config, image version or
existing output. They use the real released context/config/engine API with a local
nonconnecting target and stop before opening a database session. The fixed production
lane validator is substituted for the temporary fixture in these orchestration cases;
the existing validator and DDL-denial tests remain in the suite.

Validation: `python -m pytest tests/test_runtime_principal_prepare.py -k runtime -q`
passed **23 cases** (the file name matched the selector, so all cases in this affected
helper file ran). Ruff for the helper/test and `git diff --check` passed. No live host,
database, credential or application write was performed by D. Actual fresh-session
verification remains O/E acceptance work against the rebuilt source image.
