# Dewey12.0.13 mobile report banner

## Current continuation state
Objective: make the isolated shared-report title/status announcement compact and dismissible, automatically hide it10seconds after page load, and let the report use the reclaimed viewport space. Report errors must remain visible even if they occur after the timer. Ordinary registry success notices also disappear after10seconds; registry errors persist. Functional navigation/account bars and deployment chrome stay unchanged.
Source: /Users/jmajor/projects/dewey-sharing-docs-20261025, branch codex/dewey-share-mail-20261027, current production12.0.12/source86b0189d4c6854601d21f598414f13b1b67da931. Intended next immutable annotated12.0.13; no commit/tag/build/deployment until coordinator reviews source and authorizes the final tag/commit.
Authority: explicit user request delegated by coordinator for this banner behavior. Preserve auth, sandbox, CSP, allowed origins and handshake unchanged. No tests, browser/syntax checks, QC, success-result audits, test mail or sibling/config/credential changes. Native build/Compose exit0 will suffice when deployment is authorized.
Gate0 source inspection: report_entry_page currently renders a fixed header plus iframe height calc(100vh-110px); nonce JavaScript handles the existing challenge/handoff and status text. Registry notice() currently keeps success and error text visible indefinitely. Changes are limited to these presentation surfaces plus docs/release preparation.
Current source: implemented compact report title/session notice, explicit dismiss button via existing nonce script, ten-second page-load timer, persistent/reappearing error state and flex100dvh iframe fill. Registry success notices auto-hide after10seconds with old timers canceled; errors do not auto-hide. Sharing help updated. Source-only; no tests/browser/syntax/QC commands run. Prepared local12.0.13 runner in product-definitions matrix/v2/evidence/deployment/20261028_mobile_banner_release.py; intended remote /home/ubuntu/dewey-mobile-banner-release-12.0.13.py and explicit workdir /home/ubuntu/dewey-mobile-banner-release-12.0.13. Not transferred or executed. Reuse existing exact EC2target i-07df3a933e4839f52/us-west-2, profilelsmc, ubuntu, native selected-service builder with registry cache and targeted privileged read of live base manifest. Merge only returned images.dewey into then-current live manifest. No production action under this source phase.
Stop condition: coordinator reviews source; then separate final source/tag build/deployment authorization. Historical12.0.12 ledger remains historical. Upload-hardening proposal remains abandoned.

## Requirements
| Item | State | Evidence |
|---|---|---|
| Compact auto-dismiss report notice and viewport fill | SOURCE_READY | report_preview.py |
| Errors persist/reappear, auth/isolation unchanged | SOURCE_READY | report_preview.py |
| Registry success10seconds/errors persist | SOURCE_READY | static/registry.js |
| Docs and selected12.0.13 release runner preparation | SOURCE_READY | pending source handoff |
| Commit/tag/build/deploy | PENDING_COORDINATOR_REVIEW | not authorized in source phase |
