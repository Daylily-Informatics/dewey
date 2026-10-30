# Dewey12.0.14 recipient home and management Shares section

## Current continuation state

DEPLOYED: Dewey12.0.14/source818ea7e8f7aa53eddb26f4cfec8b19e95fa0e345, annotated numeric tag pushed on codex/dewey-share-mail-20261027. Native final-image build0 at2026-10-28T04:08:14.880228Z; selected Compose0/Recreated/Started at04:13:50.200819Z. Image108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:f884c547ac58e4f0b03ee4d3af5f238f8e9eceb91870aa1f31d4a8898a4cab2d. Targeti-07df3a933e4839f52/us-west-2, ubuntuSSM82422, /home/ubuntu/dewey-recipient-home-release-12.0.14. No sibling deployment.

Implemented: share-only browser root provides its verified-recipient share table, EUID/name/shared date/effective expiry/status, expired toggle and Logout/account switching. Full authorized /ui homepage has polished Shares section with native Open/Manage controls. Restricted API root remains403. No grant/credential/expiry mutation, new mail or broadened management access.

Authority: user's explicit recipient-home request and subsequent full-home Shares amendment. Root completed source review/commit/tag/build/deploy. Tests, lint, syntax/browser checks, hashing/readback/HEAD/QC were not run. Native successful operations are authoritative; user acceptance remains the user's observation.

Ingress: Dayhoff source7ce0b75b pushed, exact3home/index/JS route allowances; native CloudFormation UPDATE_COMPLETE. Selected Apache recipient vhost insertion and native graceful0/GRACEFUL_SUCCEEDED completed2026-10-28T04:14:37.035525Z; no configtest/health or secondary success gate. Installed origin /etc/apache2/sites-available/dewey12-recipient.conf. Final ingress result: /Users/jmajor/projects/lsmc/dayhoff/docs/plans/20261028T041105Z_dewey_recipient_home_ingress_ledger.md, pushed throughbe6f55cd.

Receipt: /Users/jmajor/projects/lsmc/product-definitions/matrix/v2/evidence/deployment/20261028_recipient_home_execution.json. Root waited for R35 nativeupload/register/share0 before Compose. New Matrix review https://dewey.day.lsmc.bio/fetch/M-DGX-16SW8; all previous publications preserved. This requested feature/release is complete through native successful build/deploy/ingress controls. User acceptance remains separate. No further build, tests, replay checks or probes are pending.

## Owning contracts and boundaries

- `RegistryPrincipalMiddleware` resolves current browser/token identity and
  validates recipient identity bindings. Share-only browser GET `/` with
  `Accept: text/html` now reaches the home; non-HTML restricted root remains403.
  Expired browser-root identity returns to the existing login page. Management
  routes retain their existing denials for recipient-only credentials.
- The recipient index uses typed share/grant lineage and the existing verified
  recipient predicates before pagination, with no owner/admin shortcut. It
  requires active current-revision grants and active nonarchived shares, respects
  denied emails, and discloses only minimal container metadata. Explicit expired
  inclusion skips deadlines only, not grant revocation or identity predicates.
- Recipient expiry is the latest remaining matching-grant deadline capped by the
  share deadline. Indefinite access remains null. No share or grant is revived.
- Existing `/shares/<EUID>` links continue through the normal fetch/viewer and
  canonical content authorization. The list cannot authorize bytes.
- Logout reuses `POST /auth/logout`: local browser session clearing, browser
  identity revocation, then the configured broker/provider logout. No alternate
  login service URL, credential extraction or new identity mechanism.
- Full `/ui` Shares uses `/api/v1/registry/shares`, existing management-filtered
  authorization and native share responses. New `include_expired` defaults true
  for existing clients; the homepage requests false before pagination. The
  existing Sharing page, editors and management actions remain intact.

## Public ingress integration owned by coordinator

The owning Dayhoff ingress is Apache plus ALB, not nginx. Its source is
`/Users/jmajor/projects/lsmc/dayhoff/scripts/dewey_recipient_ingress.py`:
`DEWEY_ROUTES` and `DEWEY_ALB_PATHS` must admit exactly GET `/`, GET
`/api/v2/recipient/shares`, and GET/HEAD `/static/recipient-home.js`. Dewey's
application allowlist has these exact additions. Coordinator identified the
installed selected origin config as
`/etc/apache2/sites-available/dewey12-recipient.conf` and owns the scoped source,
rendered route allowance/ALB update and Apache reload. Existing assertions,
private and sibling routes must be preserved; no broad `/api` or `/static`
allowance is needed. This worker did not alter Dayhoff or live ingress.

## Source handoff

`dewey_service/app.py`, `registry_access.py`, `recipient_api.py`,
`share_routing.py`, `registry_api.py`, `services/sharing.py`,
`templates/recipient_home.html`, `static/recipient-home.js`, `static/registry.js`,
`static/registry.css`, and `docs/sharing.md`.

Historical source handoff above preceded the actual native release recorded in the current continuation state. No user acceptance is inferred.
