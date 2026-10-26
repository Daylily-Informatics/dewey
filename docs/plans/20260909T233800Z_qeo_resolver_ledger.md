# QEO resolver access and report/package contract

## 2026-09-10 — container CLI correction in approved resolver scope

Live public `dewey qeo status` failed because only the Conda CLI backend was
supported; package-register has the same enforced guard. No registration was
attempted through persistence internals or spoofed Conda variables. Correct the
actual public CLI: explicit dewey-container backend, actual container/file
markers, same dependency checks, enforced guard and no skip flag. Keep the
Conda backend for real local activation. Unknown explicit backend must fail.

This is a source correction and GitHub rebuild/redeployment of the already
approved Dewey resolver scope, not a QEO image rebuild or TapDB release.
Only services.dewey may change. Baseline now includes the newer QEO deployment;
the shared boot SHA is b64d9650729091b99c1cbe36eabbb25d969330d2dbe7fc909a7d346b908af333.
Do not replay the original one-shot Dewey deployment helper or reissue its token.

Local first test pass: two passed, one failed because cli-core's RuntimeSpec
does not reject an unknown default backend at construction. ATTEMPTING_BUGFIX:
validate the explicit selector in Dewey before constructing the spec.
GitHub smoke must now exercise the real public `dewey runtime check` in the
published container without a database or network. Source import alone is not
proof of the CLI execution contract.

Owner inventory found 19 actual MultiQC data files, although the producing
analysis_artifacts.tsv lists only multiqc_data.json and the HTML report. Do not
register a two-member JSON/report package as complete; preserve all 19 files.

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
| DEPLOY-BASE | Current image/source/config and rollback target | SUCCESS | No application writable-layer changes; base Python source matches 8.0.2; old /tmp artifacts will be backed up |
| DEPLOY-BUILD | One GitHub-built immutable Dewey candidate | SUCCESS | Build 34420189915 published c62cc4dd...; verification-only run 34420688236 passed against that exact digest, no rebuild |
| DEPLOY-LIVE | Dewey-only replacement and generated boot entry | SUCCESS | Running c62cc4dd...; boot promoted after health; all 11 siblings unchanged; private backup and credential retained |
| DEPLOY-PROOF | Health, resolver and browser regression evidence | BLOCKED | Health/readiness and credential isolation passed; Google requires interactive password reauthentication before authenticated GUI acceptance |

Image source commit: `7782aef47b867c7389f96832c2bc4636aca46d92`.
Image digest: `sha256:c62cc4dd6076b076b1c10d5ab93caf6e6c1c74fdbf44982173bd3fb72571ad1b`.
Dependencies and package version stay at deployed Dewey 8.0.2 / TapDB 9.0.9;
OCI revision identifies the resolver patch. One image was built. Two smoke-harness
issues (missing deployment code, missing writable ephemeral XDG directories) were
fixed without changing the image. Final verification run 34420688236 succeeded.
Helper SHA256 `1740706bd2497fa8fbe45c22703554fd8cc25ae225468e05c40d94f9b8d33451`;
SSM delivery `b940bdd4-242b-4cb8-8ebd-a4f26efb0719` succeeded. Dry preflight reports
the original base hash and all 11 siblings. Application build source has not changed.

### Live result — 2026-09-10 00:20–00:22 UTC

- Deployment helper completed successfully. New container
  `7b64910d60f9638679cb0bac5d759f99dfe8e3c2fe4945950b40e9abcc2db7f9`.
- Boot Compose after SHA256:
  `0cf8cfdaffc6e5f461c8656f398f8144fb9945bb31971fdbf228df4b5edde4de`.
- Only `services.dewey` changed: image plus resolver hash/expiry and source SHA
  environment values. All other service/global definitions preserved; all 11
  sibling container IDs, images and start times unchanged.
- `/healthz` 200; `/readyz` 200 with database check `ok`.
- New resolver without token: 401. With dedicated token and actual report
  `M-DGX-NKDM`: authenticated owner lookup returns 404, explicitly no package yet.
  Same token against general artifact resolver: 401. **This proves credential
  isolation, not successful package resolution or QEO ingestion.**
- Host credential reference:
  `/opt/dewey/day/releases/qeo-resolver-7782aef47b86/resolver.token` (private;
  no token output/commit). Expiry `2026-12-09T00:20:01.857914+00:00`.
- Host rollback backup, preserved old-container `/tmp`, candidate Compose,
  credential receipt and deployment receipt are in
  `/opt/dewey/day/releases/qeo-resolver-7782aef47b86/`.
  Never replay the one-shot helper: baseline changed and its release directory
  now exists. Explicit rollback would restore **only Dewey** using its retained
  old image and definition after a fresh current-state check.
- Browser via existing Chrome plugin: Dewey login page rendered; shared LSMC
  login reached Cognito; Google option reached the expected account picker;
  selecting the existing account required a password. No credential entered.
  Tab 762551291 retained for user handoff. Login and challenge screenshots are
  in the task's tool evidence (no local screenshot file exported); concise
  browser evidence is recorded under `evidence/20260910_dewey_resolver/`.
  Full authenticated GUI acceptance remains BLOCKED on user reauthentication.
- No Dayhoff source, shared unit, QEO runtime, unrelated service or Aurora
  configuration changed. No reboot, DB migration, new TapDB release or second
  image build. Package version remains 8.0.2; image revision identifies the patch.

Deployment rows terminal: **yes**, 3 SUCCESS / 1 BLOCKED.
Approved image deployment and boot persistence: **complete**.
Authenticated GUI acceptance: **incomplete**. Full QEO release: **incomplete**;
real package registration, QEO consumer deployment and ingestion/query/export
remain separate next execution work, not a reason to repeat Dewey deployment.

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

## 2026-09-10 00:51Z production completion (supersedes historical blockers)

- GitHub build 34422137760 succeeded at source
  556dfcf936ea11e25f6126931fe1f655482d00a6. Exact published image:
  dayhoff/day/dewey@sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f.
  The actual image passed its public `dewey runtime check` container guard.
- Container 872434f0530335fd5a985a920f498fe39a36fd5eab40b9cb3934b185ceddeb36
  is healthy. Only services.dewey changed in generated boot Compose. All 11
  live siblings unchanged. Dedicated resolver credential preserved, not rotated.
  Boot SHA after promotion:
  05c45f50c839fb06ec78f64d3025f37e2d174289631ba3abc386cef2fa047884.
- Public container CLI `dewey --config /home/ubuntu/.config/dewey-day/dewey-config-day.yaml
  qeo status` passed. Legacy dispatch remains unconfigured/default-off.
- Existing authenticated LSMC Chrome session completed Dewey sign-in as
  the authenticated operator. The earlier separate-profile password challenge is no longer
  a blocker. No password/cookie/token was extracted or entered by the agent.
- Read-only exact S3 inventory found 19 backing files, not just the JSON.
  Authenticated Dewey S3 intake registered the 18 missing artifacts, retaining
  existing report M-DGX-NKDM and JSON M-DGX-NKFG. No source S3 objects changed.
- Public `dewey qeo package-register` succeeded with stable key
  qeo-multiqc-illumina-20260815-full-package-v1 and the checked-in 20-file
  manifest 20260910T005100Z_complete_multiqc_package.json. Actual persisted
  artifact set: **M-DGX-NNSS**. Response preserved at
  evidence/20260910_dewey_container_cli/package-registration.json.
  Manifest SHA: 4ed7e3e6938edb309a277042a42125d2ac58e99579809973e369054e1a67f4e9.
  Registration created typed membership through Dewey/TapDB; no raw SQL,
  bootstrap rerun, fabricated identity or inferred package directory.
- Focused checks: 15 container/package tests and 5 deployment-helper tests
  passed. The source-hashing helper initially used an unsupported context-body
  iterator; corrected to streaming read, then all 20 checksum/size checks passed.

Dewey access/deployment/package registration complete. QEO ingestion of the
real report link remains pending the separately approved QEO corrected image.
No further Dewey image build is required by these operator/receipt changes.
