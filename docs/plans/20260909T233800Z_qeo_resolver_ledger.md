# QEO resolver access and report/package contract

## 2026-09-10 — approved Dewey production deployment

User approved building/deploying the Dewey image and changing **only
`services.dewey`** in the generated host boot Compose file. Prior shared-unit,
Aurora, Dayhoff source and unrelated-service exclusions remain in force.
This supersedes the earlier image/deployment approval blocker below.

Gate 0: local clean commit `f52bc9a`; isolated branch unchanged. Host
`i-07df3a933e4839f52`, interactive Ubuntu session. Dewey container
`4b66bc39c7ef63980c6d7a164c15298524992dcfa4421f988ac7ea5f91d12dc2`,
image `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:0780a42dd2b3d5620de2c538cada32acd661f5be5a0f0b60a08c9f941ea3af42`.
Generated Compose baseline SHA256
`b2a9c0977e125c628c970a294235ee2fc590acc0a4af6e9b7022177aea58ea8a`.
12 service definitions; preserve the other 11 and all global configuration.
ECR repository exists and is immutable. Existing approved role's actual name is
`github-actions-ecr-all-repos`; trust permits `repo:lsmc-bio/*`. No IAM changes.

| ID | Requirement | Status | Evidence / limits |
|---|---|---|---|
| DEPLOY-BASE | Current image/source/config and rollback target | IN_PROGRESS | Read-only host inventory; inspect writable-layer source before replacement |
| DEPLOY-BUILD | One GitHub-built immutable Dewey candidate | ATTEMPTING_BUGFIX | Run 34420189915 built/published c62cc4dd...; smoke failed because harness omitted DEWEY_DEPLOYMENT_CODE. Verify the existing digest with explicit day config; no rebuild |
| DEPLOY-LIVE | Dewey-only replacement and generated boot entry | OPEN | Exact hash guard, private backup, sibling/global equality, no shared-unit execution |
| DEPLOY-PROOF | Health, resolver and browser regression evidence | OPEN | Do not call the full QEO release complete from Dewey deployment |

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
