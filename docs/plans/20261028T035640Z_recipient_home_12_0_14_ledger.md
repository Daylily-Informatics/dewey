# Dewey12.0.14 recipient home and management Shares section

## Current continuation state

Objective: share-only browser `/` must provide an identity-scoped share table
and an explicit logout/account-change path; full authorized `/ui` must also show
a polished Shares section. Stop condition for this worker: source ready for
coordinator review and exact next release. Deployment and user acceptance remain
separate.

Repo: `/Users/jmajor/projects/dewey-sharing-docs-20261025`, branch
`codex/dewey-share-mail-20261027`. Intended annotated numeric release12.0.14.
Package version is dynamically owned by setuptools_scm/the immutable release
tag; no duplicate manual version constant is introduced.

Authority: user's explicit recipient-home request and subsequent full-home
Shares amendment, relayed by coordinator2026-10-28. Source edits/docs only:
no tests, lint, syntax/browser checks, checksum/readback/HEAD/QC, commit, build or
deployment by this worker. No credential changes, management access expansion,
share mutation or notification was requested or performed.

Current state: SOURCE_READY_FOR_REVIEW. Implemented recipient root, narrowly
scoped recipient index, home table/toggle/logout, and management homepage Shares
card with pagination and existing Open/Manage controls. Source-only review is the
authorized validation method; no tests/checks were run. Coordinator owns the
next commit/tag, final EC2 image and selected Dewey-only deployment.

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

No runtime release result is claimed here. Coordinator's source review,
commit/tag, final-image command outcome and selected deployment outcome should
be recorded as subsequent entries without inventing tests or user acceptance.
