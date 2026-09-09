# QEO resolver access and report/package contract

## Authority and Gate 0

2026-09-09: user explicitly expanded scope to establish QEO's Dewey resolver
access and report-to-data-package contract. Base: Dewey 8.0.2,
`dea0009b743ad5b627177acdf21c87dd5c1d67c1`, isolated branch
`codex/dewey-qeo-resolver-20260909`. No existing modifications.

Existing resolver tokens also authorize writes. The observed report has no
authoritative package membership. Existing MultiQC registration requires an
analysis identifier; this integration must not invent one. Preserve existing
registrations and dispatch; no TapDB upgrade or shared-cluster changes.

| Item | State | Acceptance |
|---|---|---|
| ACCESS | SUCCESS | Dedicated expiring resolver credential implementation; reserved namespace cannot authorize general API writes |
| CONTRACT | SUCCESS | Explicit complete manifest, artifact membership through existing typed lineage, no inferred directory |
| QEO | SUCCESS | Companion local QEO source accepts report URL/package ID through common acquisition |
| TESTS | SUCCESS | 28 Dewey tests and 34 QEO tests passed; focused Ruff and diff checks passed |
| LIVE | BLOCKED | Additional Dewey GitHub image/deployment and generated services.dewey boot-entry amendment not yet approved; real credential/package remain unprovisioned |

Production has not changed. No image builds are part of this source checkpoint.

## Local completion receipt

2026-09-09: activated isolated `DEWEY-qeores` through the repository's supported
activation script (environment plus its one editable install, no image build).
`dewey qeo resolver-credential-create --help` and `dewey qeo package-register
--help` resolve through the public CLI. Unit tests use temporary local fixture
credentials, never real production credentials.

Focused suite: `test_qeo_package_resolver.py`, `test_auth_enforcement.py`,
`test_auth_unit.py`, `test_qeo_multiqc_registration.py`: **28 passed**.
QEO companion suites: `test_dewey_package.py`, `test_unified_ingestion.py`,
`test_pages.py`, `test_gui_api_boundary.py`: **34 passed**. Changed Python files
pass Ruff; both trees pass `git diff --check`. No full coverage, container checks,
GitHub build, push, live database write, production secret, or deployment.

Contract and live handoff:
`20260909T235100Z_qeo_package_contract.md`.
All five rows terminal: yes (4 SUCCESS, 1 BLOCKED).
Local implementation objective complete: yes. Live resolver access objective
complete: **no**. Next approval is a narrowly bounded Dewey image/deployment and
its generated boot-entry amendment, not another approval of the same source work.
