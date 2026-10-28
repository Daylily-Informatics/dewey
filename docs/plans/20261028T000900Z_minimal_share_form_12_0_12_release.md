# Dewey12.0.12 minimal share form

## Current continuation state
Updated: 2026-10-28T00:06:05.255003+00:00
Objective/stop condition: deploy a minimal share creation form with sensible defaults, accessible tooltips and inline help, retaining detailed sharing policy under Advanced and preserving existing complex shares on edit.
Source: /Users/jmajor/projects/dewey-sharing-docs-20261025, branch codex/dewey-share-mail-20261027, current production source12.0.11/81a803f9e5bdd1974231d64945fc4b7860c74bfb. Intended next immutable annotated numeric tag12.0.12. Earlier uncommitted upload-hardening12.0.12 work was canceled and removed before any tag/build/deploy; that scope is not part of this release.
Authority: user2026-10-27 requests share form defaults/tooltips and minimal basic inputs with power controls separated. Existing implementation/deployment authority covers Dewey-only release. Trust documented public/routine-use return/success results. No extra QC/readback/HEAD/hashing/probe campaign, pytest/lint/CI, PR/merge, local image builds, sibling-service changes or credential work.
Gate0: native registry_api.py/services/registry_storage.py/storage.py restored to existing12.0.11 HEAD after withdrawal of interrupted upload-hardening. Abandoned-release note retained. Scoped UI worker owns sharing.js/CSS/help source only; coordinator owns release ledger/tag, accounting owns designated EC2 final-image deployment. Reuse existing approved gpt-6.1-sol/medium workers.
Behavior: basic name, recipient emails, plain expiration/default summary; HTML report option when relevant. Advanced holds domain/public audience, explicit grants, file filters, exclusions, per-grant expiry/target scope, report bundle and timezone offsets. Exact internal creator plus entire exact internal audience defaults noexpiry; other scopes14days, maximum365days, no infinite. Emails continue through native notification/onboarding fromdewey@lsmc.com. No recipient/share mutation merely opening form.
Build/deploy target: AWSprofilelsmc, EC2i-07df3a933e4839f52/us-west-2, ubuntu, existing selected-service build helpers, live compose /opt/dayhoff/deployments/day/compose/docker-compose.yml/projectdayhoff-day. Build finaltaggedDeweyimage once; deploy onlydewey via native docker compose documented result. No secondary success checks.
Current state: source ready and reviewed; no12.0.12tag/build/deploy yet. Simplified share form and CSS, inline help/tooltips, corrected obsolete sharing defaults/notification documentation. HTML object report filename defaults from its persisted original_filename only; other report paths remain explicit. Next: commit/tag/push exact revision, run final native EC2 build and scoped compose deployment, record returned result here and main Matrix ledger. User acceptance remains separate.

## Requirements
| ID | Requirement | State | Evidence |
|---|---|---|---|
| UI-01 | Basic inputs + defaults + Advanced controls | SUCCESS | dewey_service/static/sharing.js |
| UI-02 | Accessible tooltips + user-facing help | SUCCESS | sharing.js/CSS + docs/sharing.md + inline help |
| UI-03 | Preserve scoped expiration and existing advanced edit policies | SUCCESS | NativeAPI unchanged; source-reviewed UI retains original deadlines/grant IDs/scopes |
| REL-01 | Exact immutable tag and final-image build | OPEN | selected EC2 builder |
| REL-02 | Dewey-only deployment using native command result | OPEN | scoped compose command |

## Superseded QC work
User rejected redundant full readback and proposed HEAD replacement. Native upload-hardening was removed before release. Matrix uploader cleanup committed5e353be in product-definitions; global/DayOA/DYEC policy and explicit persistent memory note saved. Historical evidence is preserved, not a mandate to repeat checks. No additional exact QC has two approvals.

## Cost/time evidence
Redundant upload readbacks occurred before the correction and caused one reported connection-reset interruption despite completed native upload. The coordinator then proposed a HEAD substitute; that was also the prohibited pattern and was withdrawn. Historical upload receipts remain in product-definitions/matrix/v2/evidence and private work/R29_upload_receipt.json. No attributable billing or token totals are available from the tools used here; none are invented. No recurring cost report is scheduled.
