# Managed Dewey sharing

This guide describes the managed-share source contract. Release, deployment, runtime observations, and user acceptance are recorded separately in the [implementation ledger](plans/20261004T000136Z_dewey_filtered_sharing_options_ledger.md).

## Access and delivery

Every managed-share operation requires **trusted Tailscale ingress, a verified Login identity, and current authorization**. Tailscale membership alone does not grant file access. A permitted email/domain alone does not grant network access. A share owner or manager can manage the policy; ownership does not bypass recipient grants when reading files.

The default delivery mode is `gateway`. The recipient opens `/shares/<share-euid>` and browses within that share. Each list, download, report asset, and credential request evaluates current grants and filters. File requests use `GET` or `HEAD /shares/<share-euid>/files/<target-euid>?relative_key=<exact-key>`; the gateway supports a single byte range and HTTP conditions. Revocation prevents subsequent requests. An already admitted response may finish, and downloaded files cannot be recalled.

The owner or authorized manager can explicitly enable `presigned` alongside `gateway`. Gateway permission alone does not permit presign issuance. Issuing a URL still requires Tailscale, identity, a matching current grant, and the explicit delivery permission. Consumption of an issued **raw S3 URL is the sole exception**: anyone holding it can use it without Tailscale or Dewey sign-in until expiry. Do not treat it as recipient-bound or immediately revocable.

Raw S3 URLs default to 900 seconds, allow 1–3600 seconds, and are capped by the remaining share/grant lifetime. The response and dialog expose `expires_at` from the signed URL. Signing credentials can make a URL stop working earlier. Issuance is audited separately from completed downloads; forwarding the URL does not transfer a Dewey identity.

## Recipients, selection, and expiration

Use individual `email` grants or `domain` grants. Domains match exactly unless that grant explicitly sets `include_subdomains: true`. Each grant can select different include/exclude patterns, persisted target members, and expiration. Share-wide `denied_emails` overrides this share's allow grants; it does not revoke independent rights from another share or native storage permissions.

A prefix is live: later matching descendants are included. An explicit set fixes the persisted member targets reviewed at creation; later additions to the registered set are excluded. A prefix member of a set remains live within that member. Fixed member targets do not freeze or copy S3 bytes.

Patterns are case-sensitive. For prefixes they match literal root-relative keys; for a single object they match its filename. `*` stays within a path segment, `**` crosses segments, and `?` matches one non-separator character. `['**']` means all. A file must satisfy the share-wide selection and at least one matching grant. Exclusions override includes within their scope: share-wide exclusions defeat every grant; a grant's exclusions narrow that grant. Another applicable grant may independently allow the key. Use share-wide exclusions to deny a path across all recipients. Use exact names, spaces, and repeated separators without normalization. The editor rejects empty includes; the API treats an explicit empty include list as matching no files. An omitted grant `target_euids` selects all reviewed share targets; a supplied list must be a nonempty subset of persisted member identifiers.

Expiration must be future, timezone-bearing ISO 8601, such as `2026-10-17T17:00:00-04:00` (replace with the intended future date). Grant expiration cannot exceed share expiration. The browser presents a local datetime, the named browser timezone, an explicit UTC offset, and the resolved UTC timestamp. It rejects nonexistent local times and offsets that fail the timezone round trip. During a repeated daylight-saving hour, either valid offset can be selected. Naive API timestamps are rejected.

The selection preview shows paths selected by at least one audience in the draft; it does not simulate a particular recipient's effective access. Recipient contents use the current viewer's grants. Both are bounded metadata scans. Follow `continuation_token` and inspect `incomplete`. A partial page, empty filtered page, or preview count is not a complete inventory. Browsing does not register descendants.

## Browser workflow

1. Open a registered S3 object, prefix, or set and select **Share**. Add email/domain grants, filters, deadlines, and optional member restrictions. Leave raw presigns disabled unless intended.
2. Use **Preview matching selection**, then create the share. Creating a share does not send invitations.
3. Recipients open the stable share link over Tailscale, sign in, and use **Download** or **View report** inside that share.
4. Managers use **Edit share**, **Revoke recipient grant**, or **Revoke share**. Edits/revocations require the current integer `policy_revision`; a conflict requires reloading and reviewing the current policy. Expired/revoked shares cannot be reactivated by editing.
5. Use **Load activity** and **Export loaded activity JSON**. Export identifies whether further pages remain. Transfer events distinguish authorization, issuance, server bytes, completion, disconnect, and unknown outcomes.
6. **Send login invitation** is a separate explicit email-sending action for an already permitted recipient. Domain permission does not automatically provision every domain member. No invitation is sent automatically.

## Linked HTML reports

Choose the exact HTML key and an explicit target-relative bundle directory. A nonempty `bundle_root` ends in `/`; empty means the target root. Linked assets must stay inside that root and satisfy current grants. A single-object report uses empty `relative_key` and empty `bundle_root`; it does not authorize sibling assets.

Reports run on a separate origin for each persisted context below the configured content suffix. The app checks the iframe's exact origin, window source, and context identifier during the challenge. A short-lived one-use handoff travels in a POST body, then a Secure HttpOnly host cookie supports linked assets. There are no bearer preview URLs. The context binds the current viewer and browser session, expires no later than 900 seconds or the grant/session deadline, and reauthorizes each asset. Sign out or session invalidation ends its authority; reopen from Dewey after renewal.

The iframe uses `sandbox="allow-scripts allow-same-origin"` on the separate content origin. Report scripts/styles and permitted relative assets work inside that context; application APIs are excluded from content hosts. CSP confines scripts and connections to the report origin and excludes workers, nested frames, and form submission. Reports requiring those features need an explicit product decision. Generic record previews direct the user to an explicit managed share; the former bearer preview path is retired.

## CLI

Activate the intended repository environment with `source ./activate <deploy-name>`. Configure `DEWEY_API_URL` as the exact HTTPS service origin and `DEWEY_API_TOKEN_FILE` as an absolute private file with mode 600 containing the user's personal token. Use Tailscale. Do not print tokens or use AWS commands as a download substitute.

Replace every angle-bracket placeholder with an identifier returned by Dewey or a chosen local path. Policy files must contain JSON objects; dates must be actual future offset-bearing timestamps.

```sh
dewey shares preview '<target-euid>' --policy /absolute/policy.json
dewey shares create '<target-euid>' --policy /absolute/policy.json --idempotency-key '<unique-request-key>'
dewey shares list 'Reviewed reports' --page 1
dewey shares get '<share-euid>'
dewey shares contents '<share-euid>' --target-euid '<target-euid>' --prefix 'reports/'
dewey shares contents '<share-euid>' --target-euid '<target-euid>' --prefix 'reports/' --continuation-token '<returned-token>'
dewey shares download '<share-euid>' '<target-euid>' --relative-key 'reports/report.html' --output /absolute/new-report.html
dewey shares presign '<share-euid>' '<target-euid>' --relative-key 'reports/report.html' --ttl-seconds 900
dewey shares report '<share-euid>'
dewey shares update '<share-euid>' --changes /absolute/reviewed-changes.json
dewey shares revoke-grant '<share-euid>' '<grant-euid>' --policy-revision 1 --reason 'Recipient access ended'
dewey shares revoke '<share-euid>' --policy-revision 1 --reason 'Delivery closed'
dewey shares activity '<share-euid>' --limit 100
dewey shares invite '<share-euid>' --email 'recipient@example.org'
```

`shares preview` previews a draft selection for a **target record**; `shares report` returns the signed-in browser share page for report viewing. `shares download` streams through the authenticated gateway, refuses to overwrite an existing output, and can leave partial bytes after a failed transfer. For a single-object target, omit `--relative-key`. Activity is JSON; follow its continuation token to export additional pages. The invitation command sends email; invoke it only when that action is intended.

Example prefix creation policy (replace the timestamp placeholders; use filename patterns for a single-object target):

```json
{
  "name": "Reviewed reports",
  "purpose": "Collaborator delivery",
  "audience": "recipients",
  "expires_at": "<future-ISO8601-timestamp-with-offset>",
  "include_patterns": ["reports/**"],
  "exclude_patterns": ["reports/internal/**"],
  "denied_emails": ["excluded@example.org"],
  "delivery_modes": ["gateway"],
  "grants": [
    {
      "recipient_type": "domain",
      "recipient": "example.org",
      "include_subdomains": false,
      "include_patterns": ["**"],
      "exclude_patterns": ["**/*.tmp"],
      "expires_at": "<future-ISO8601-timestamp-with-offset>"
    }
  ]
}
```

For edits, send the reviewed policy fields plus the current `policy_revision`, and omit creation-only `audience` and `lifetime_days`. New recipient rules use `grants`; `allowed_users` and `allowed_domains` remain supported canonical inputs. Preserve intended grant restrictions when replacing rules. Revocation uses persisted grant identifiers returned by detail, never invented identifiers.

## API routes

All routes below require the authenticated managed-share context. Paths starting `/api/v1` use the registry API; file routes use the application origin. Creation requires an `Idempotency-Key` header.

| Operation | Method and path | Input / result |
|---|---|---|
| Create | `POST /api/v1/records/<target-euid>/shares` | Creation policy above; returns persisted share EUID and revision |
| Selection preview | `POST /api/v1/records/<target-euid>/shares/preview` | Draft creation policy; bounded result with `incomplete` |
| Accessible shares | `GET /api/v1/registry/shares` | `q`, `page`, `page_size`, `sort` (`created_at` or `name`); sanitized current authorized shares, `has_more`, and bounded-search `incomplete` |
| Detail / edit | `GET` / `PATCH /api/v1/registry/shares/<share-euid>` | PATCH requires `policy_revision` and supported policy fields |
| Contents | `GET /api/v1/registry/shares/<share-euid>/contents` | `target_euid`, `prefix`, `limit`, `continuation_token`; authorized entries only |
| Download | `GET` / `HEAD /shares/<share-euid>/files/<target-euid>` | Exact `relative_key`; optional HTTP Range/conditions |
| Raw S3 presign | `POST /api/v1/registry/shares/<share-euid>/presign` | `{"target_euid":"<target-euid>","relative_key":"reports/report.html","ttl_seconds":900}`; URL and `expires_at` |
| Report context | `POST /api/v1/registry/shares/<share-euid>/preview` | `{"target_euid":"<target-euid>","relative_key":"reports/report.html","bundle_root":"reports/"}`; browser challenge/handoff metadata |
| Revoke grant | `POST /api/v1/registry/shares/<share-euid>/grants/<grant-euid>/revoke` | `{"policy_revision":1,"reason":"Recipient access ended"}` |
| Revoke share | `POST /api/v1/registry/shares/<share-euid>/revoke` | Current `policy_revision` and reason |
| Activity | `GET /api/v1/registry/shares/<share-euid>/activity` | `limit` up to 200 and `continuation_token`; manager access |
| Explicit invitation | `POST /api/v1/registry/shares/<share-euid>/invite` | `{"email":"recipient@example.org"}`; sends email through registered Login |

## Administrator setup

Use the deployment's explicit configuration and registered Login contract. Relevant settings names are:

- `share_trusted_proxy_peer`, `share_ingress_assertion_header`, `share_ingress_assertion`: exact transport peer and private ingress assertion. The proxy removes client-supplied assertion headers and sets its secret only on the Tailscale listener. Uvicorn must preserve the real transport peer; forwarded IP/Host headers are not proof of ingress.
- `share_application_origin`: exact HTTPS application origin without a path. `share_content_host_suffix`: explicitly configured lowercase DNS suffix on a separate content subtree. Configure its DNS, wildcard certificate, and trusted routing; reject unknown contexts and never expose application APIs on content hosts.
- `share_session_generation`: required browser-session generation for report contexts. Missing session/configuration fails closed; a session established before report binding setup requires a new sign-in.
- `share_max_lifetime_days`: policy lifetime ceiling. Raw S3 issuance uses the fixed 900-second default and 3600-second maximum described above.
- `external_broker_service_id`, `external_broker_login_url`, `external_broker_handoff_exchange_url`, `external_broker_service_token`, `external_broker_callback_url`, `external_broker_logout_url`, and `external_broker_ca_bundle`: registered shared Login configuration. Invitation preparation also requires the explicit `LSMC_AUTH_BROKER_SHARE_RECIPIENT_PREPARE_URL`; use Dewey's registered service credential.

Install the native sharing template pack through the supported Dewey DB controls. Existing records require the explicit `dewey db upgrade-sharing` inventory/apply/verify workflow with a mandatory timezone-bearing `--created-since`, reviewed private inventory, exact digest, attribution, and durable receipts. The same fixed creation cutoff is required for every phase. Only eligible shares are converted; older shares are retired through native archived status without deleting share records, lineage, audit or S3 files. Malformed or ambiguous eligible records block conversion. This one-time rollout cutoff does not shorten the lifetime of future shares. Do not raw-edit records or introduce runtime compatibility branches. Keep secrets, private inventories, and presigned credentials out of repository documentation and audit exports.

For historical shares represented only by an authoritative set-to-share edge, conversion inventories the complete current native set membership, locks and rechecks that scope, and creates explicit member relationships. It preserves the original relationships and audit. This freezes the reviewed cutover membership; it does not reconstruct membership at original creation. Existing direct-member shares never expand from later set changes. Older records excluded by the explicit creation cutoff are retired without importing their old policy or history into the new grant model. Eligible ambiguous records still require explicit disposition.
