# Dewey12.0.12 minimal share form

## Current continuation state
Updated: 2026-10-28T00:18:56.682328+00:00
Objective/stop condition: deploy a minimal share creation form with sensible defaults, accessible tooltips and inline help, retaining detailed sharing policy under Advanced and preserving existing complex shares on edit.
Source: /Users/jmajor/projects/dewey-sharing-docs-20261025, branch codex/dewey-share-mail-20261027, current production source12.0.11/81a803f9e5bdd1974231d64945fc4b7860c74bfb. Intended next immutable annotated numeric tag12.0.12. Earlier uncommitted upload-hardening12.0.12 work was canceled and removed before any tag/build/deploy; that scope is not part of this release.
Authority: user2026-10-27 requests share form defaults/tooltips and minimal basic inputs with power controls separated. Existing implementation/deployment authority covers Dewey-only release. Trust documented public/routine-use return/success results. No extra QC/readback/HEAD/hashing/probe campaign, pytest/lint/CI, PR/merge, local image builds, sibling-service changes or credential work.
Gate0: native registry_api.py/services/registry_storage.py/storage.py restored to existing12.0.11 HEAD after withdrawal of interrupted upload-hardening. Abandoned-release note retained. Scoped UI worker owns sharing.js/CSS/help source only; coordinator owns release ledger/tag, accounting owns designated EC2 final-image deployment. Reuse existing approved gpt-6.1-sol/medium workers.
Behavior: basic name, recipient emails, plain expiration/default summary; HTML report option when relevant. Advanced holds domain/public audience, explicit grants, file filters, exclusions, per-grant expiry/target scope, report bundle and timezone offsets. Exact internal creator plus entire exact internal audience defaults noexpiry; other scopes14days, maximum365days, no infinite. Emails continue through native notification/onboarding fromdewey@lsmc.com. No recipient/share mutation merely opening form.
Build/deploy target: AWSprofilelsmc, EC2i-07df3a933e4839f52/us-west-2, ubuntu, existing selected-service build helpers, live compose /opt/dayhoff/deployments/day/compose/docker-compose.yml/projectdayhoff-day. Build finaltaggedDeweyimage once; deploy onlydewey via native docker compose documented result. No secondary success checks.
Current state: DEPLOYED12.0.12/source86b0189d4c6854601d21f598414f13b1b67da931, annotated tag pushed. Native cached final build exit0 (00:13:53.375291–00:17:07.764231UTC), native selected Compose exit0/Started (00:17:31.259879–00:17:40.021490UTC), 2026-10-28. Image `108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:6b55de955946b01a6740211e9e862850d139b6c6e06c0772248092b21aac0836`. R1 permission error corrected using targeted privileged read of the same native manifest; failed log preserved. Final remote workdir /home/ubuntu/dewey-ui-release-12.0.12-r2. No followup checks/tests, success-log readback, mail, orphan cleanup or sibling deployments. User acceptance is pending the user's review; no further build/deploy work remains for this feature. Main execution receipt: /Users/jmajor/projects/lsmc/product-definitions/matrix/v2/evidence/deployment/20261027_minimal_dewey_ui_execution.json. All requirement rows terminal.

## Requirements
| ID | Requirement | State | Evidence |
|---|---|---|---|
| UI-01 | Basic inputs + defaults + Advanced controls | SUCCESS | dewey_service/static/sharing.js |
| UI-02 | Accessible tooltips + user-facing help | SUCCESS | sharing.js/CSS + docs/sharing.md + inline help |
| UI-03 | Preserve scoped expiration and existing advanced edit policies | SUCCESS | NativeAPI unchanged; source-reviewed UI retains original deadlines/grant IDs/scopes |
| REL-01 | Exact immutable tag and final-image build | SUCCESS | Native build0, exact annotated12.0.12/source/image above |
| REL-02 | Dewey-only deployment using native command result | SUCCESS | Native Compose0/Started, finished2026-10-28T00:17:40.021490Z |

## Superseded QC work
User rejected redundant full readback and proposed HEAD replacement. Native upload-hardening was removed before release. Matrix uploader cleanup committed5e353be in product-definitions; global/DayOA/DYEC policy and explicit persistent memory note saved. Historical evidence is preserved, not a mandate to repeat checks. No additional exact QC has two approvals.

## Cost/time evidence
Redundant upload readbacks occurred before the correction and caused one reported connection-reset interruption despite completed native upload. The coordinator then proposed a HEAD substitute; that was also the prohibited pattern and was withdrawn. Historical upload receipts remain in product-definitions/matrix/v2/evidence and private work/R29_upload_receipt.json. No attributable billing or token totals are available from the tools used here; none are invented. No recurring cost report is scheduled.

## Actual build failure and scoped correction
Observed 2026-10-28T00:13:41.170432+00:00: native builder returned exit1 before image build because ubuntu could not read root-owned /opt/dayhoff/deployments/day/container-release-manifest.json. Production unchanged. Corrected access: targeted sudo read of that exact manifest into private release base-manifest.json; native builder receives the same input via explicit path. Preserve first attempt log; rerun same final12.0.12/source86b0189d4c6854601d21f598414f13b1b67da931 in /home/ubuntu/dewey-ui-release-12.0.12-r2. No alternative builder, new image version, configuration/credential change or secondary QC. Native failure is accepted as failure; no success result was second-guessed.

## Executed final commands
```sh
python3 /home/ubuntu/dewey-ui-release-12.0.12.py build --tag 12.0.12 --commit 86b0189d4c6854601d21f598414f13b1b67da931 --work-dir /home/ubuntu/dewey-ui-release-12.0.12-r2
sudo python3 /home/ubuntu/dewey-ui-release-12.0.12.py deploy --tag 12.0.12 --commit 86b0189d4c6854601d21f598414f13b1b67da931 --work-dir /home/ubuntu/dewey-ui-release-12.0.12-r2
```
Native selected deploy: `docker compose -p dayhoff-day -f /opt/dayhoff/deployments/day/compose/docker-compose.yml up -d --no-deps --no-build --pull never dewey`. Both final phase results returned0. No extra QC was used to establish success.
