# Dewey GUI audit control ledger

Updated: 2026-09-16T20:16:32.917651+00:00

## Controlling instructions

Exactly two iterations: two GUI attempts per feature on the current deployment; freeze the entire baseline before code fixes; one scoped tagged Dewey release/deployment; two attempts per feature after deployment; stop. Preserve all records and files. No deletes, overwrites, replacements, archives, member removal, upload abort, revocation, purge, data restore or cleanup. No pytest/lint/coverage/CI, PR, merge, dependency deployment or laptop container build.

## Gate 0 baseline

{
  "repo": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913",
  "branch": "codex/ursa-final-gap-dewey-20260913",
  "commit": "df6d4d0646fc1385c35ff2b6353478a46b4587ac",
  "tag": "10.0.5",
  "initial_status": "clean",
  "remote_tag_10.0.6": "absent at 2026-09-16T18:59Z",
  "production_refresh": {
    "compose": "/opt/dayhoff/deployments/day/compose/docker-compose.yml",
    "compose_sha256": "aef0b6b96b3ad1aadf008062a765271b97f6d5307776cf33ca1293a941dccf78",
    "non_dewey_compose_sha256": "80071d98b8a9cc2962c41250ad51c9b1833e96771cd055bc541185684c95cc80",
    "dewey_image": "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:91bce850ad777244f443e933e9ced92664a1d70dc092f632881810e3a0860687",
    "containers": [
      {
        "name": "/dayhoff-day-ursa-v2-run-worker-1",
        "id": "0e689807c272e18b309cde0bee7730f6d7cd5aedf95047231c011df61e89e15d",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-ursa-v2-run-monitor-1",
        "id": "c365c6649a9c39a950d8fe2b0702cae44c36c72dd3c7a2a2e26215a0c91ab622",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-ursa-cluster-sweeper-1",
        "id": "5249b887fdeb7ed3267e647d994b8dbe307e33756282552b6e177f492b112dc6",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-ursa-placement-scheduler-1",
        "id": "1bd63e53d8aa72246c5b22aed3794707c79df77cb90f9cb48b04542d61978d40",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-ursa-cost-guardrail-scheduler-1",
        "id": "02e367ed88821de125aa67190cb604cd08e5d42120566202a076d6f03f784859",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-ursa-1",
        "id": "15fc22816575cb74d82611433c0590b351c1c7798149d7f2fd96920d350b8fdb",
        "image": "sha256:387518ac3aacf65eac5b5b09908afc5c3c1b5a01d6e0c3aeb03da788238ba96a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-bloom-1",
        "id": "3de32bc9b8b3c98c0f719847a60c2d2bc45648e4c6b6a7136787c6e8fefc5cbf",
        "image": "sha256:590a8af40c0412c5e8d24c390597be253f12ac20642429ec4e338cd0b8ff2df2",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-qeo-1",
        "id": "56bf2291980850596b03864a3399ccb708217600ee0cf7c24e9fae04f6dc4ea2",
        "image": "sha256:82810a338b93489ffce125d206bd30556d9f6e7f3236940bbdc930ffc8b5f312",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-dewey-1",
        "id": "8b2b887d7f8db4fdaa69d15f27b2d9c19576747cd9cdc1a5c3238289c2df3915",
        "image": "sha256:91bce850ad777244f443e933e9ced92664a1d70dc092f632881810e3a0860687",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-kahlo-1",
        "id": "53f225f0693d71164b43611ec8319a82e02f2c22111a7c7b2be4a6228ad02c50",
        "image": "sha256:0a27b543474cfab49873014940b5f2b7b16300f2f59f97639f22c0494aa2ffa3",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-atlas-1",
        "id": "9dc66ad2a1f7353132769bf10de83865ea83bac34e03145b50ee2f42ba0adf01",
        "image": "sha256:cf1c0690ae277e4ef2d0621724575771e72856930a81d959a6d465de2ad94c7a",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-login-1",
        "id": "0c905a1041a6c6cd4db65c246aa593612109e2f02dbfa3116653f5c99f69a034",
        "image": "sha256:d955b71ef2a1f69bf06018a61336c764af46969402433bbe6196280dd283c8ba",
        "status": "running",
        "restart_count": 0
      },
      {
        "name": "/dayhoff-day-zebra-day-1",
        "id": "4f2b16fc88c28440d22ebd12f24a05849238663b7239bad9d4b89df1cf4256b2",
        "image": "sha256:c3c93ed8d2a79381a22f1d2c3575b1e5cd7a9f166d683aa22217ce3e37185593",
        "status": "running",
        "restart_count": 0
      }
    ]
  },
  "health": {
    "contract_version": "v3",
    "service": "dewey",
    "environment": "day",
    "instance_id": "47270698905e42238deafabfce2d16e6",
    "observed_at": "2026-09-16T19:01:45.078543+00:00",
    "status": "ok",
    "request_id": "a19l-LO9MvPuB5sPzHffjFWWSdvzntHU",
    "correlation_id": "bfcca6686b16992c",
    "build": {
      "version": "10.0.5",
      "sha": "df6d4d0646fc1385c35ff2b6353478a46b4587ac"
    },
    "checks": {
      "process": {
        "status": "ok",
        "started_at": "2026-09-13T07:47:32.603717+00:00"
      }
    },
    "projection": {
      "state": "ready",
      "stale": false,
      "observed_at": "2026-09-16T19:01:45.078543+00:00",
      "last_synced_at": "2026-09-16T19:01:45.078543+00:00",
      "detail": null
    }
  },
  "fixture_prefix": {
    "IsTruncated": false,
    "Name": "lsmc-dewey-0",
    "Prefix": "gui-audit/20260916T183133Z/",
    "MaxKeys": 1,
    "EncodingType": "url",
    "KeyCount": 0
  }
}

## Execution ledger

| ID | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|
| G00 | Refresh production/source/configuration/rollback inventory | SUCCESS | active_product_contract | user-approved plan | primary | production-baseline.json; health-baseline.json; fixture-prefix-baseline.json |  | Live source/image/configuration and sibling baselines recorded |
| G01 | Inventory all distinct pages, links, controls and flows | SUCCESS | active_product_contract | G00 | primary | features.json; observations.jsonl; bugs.json; baseline-freeze.json |  | 189 distinct feature/surface rows reconciled with live navigation and source routes. |
| G02 | Iteration 1, attempts A and B, all features | SUCCESS | active_product_contract | G01 | primary | features.json; observations.jsonl; bugs.json; baseline-freeze.json |  | Both baseline attempts have a result or explicit blocker/exclusion for every inventoried row. |
| G03 | Freeze complete baseline bug inventory before source fixes | SUCCESS | active_product_contract | G02 | primary | features.json; observations.jsonl; bugs.json; baseline-freeze.json |  | Five substantiated defects frozen before source edits; D03 withdrawn and preserved. |
| G04 | Implement collected Dewey fixes | SUCCESS | active_product_contract | G03 | primary | Source diff: registry_storage.py, registry_api.py, registry.js; deploy_dewey.py |  | Five frozen defect fixes implemented and manually reviewed. No automated code checks; production GUI verification follows deployment. |
| G05 | Commit/push/annotated tag/EC2 build/Dewey-only deployment | IN_PROGRESS | active_product_contract | G04 | primary |  |  |  |
| G06 | Iteration 2, attempts A and B; stop | OPEN | active_product_contract | G05 | primary |  |  |  |
| G07 | Finalize/commit/push report and evidence without another build | OPEN | active_product_contract | G06 | primary |  |  |  |

## Bug ledger

| ID | Severity | Description | Status | Owner | Evidence | Root cause / next action |
|---|---|---|---|---|---|---|
| D01 | P3 | Release surfaces show a stale build branch despite correct deployed version/SHA. | ATTEMPTING_BUGFIX | Dewey | I1-A-ADMIN-RELEASE; production-baseline.json; independently reproduced in I1-B | Deployment operator updates only exact Dewey image and source SHA/branch environment fields. Post-deploy GUI verification pending. |
| D02 | P1 | S3 object download, registered object access and set manifests return HTTP500. | ATTEMPTING_BUGFIX | Dewey | I1-A-STORE-DOWNLOAD; I1-A-RECORD-DOWNLOAD; I1-A-RECORD-MANIFEST; I1-A-download-manifest-trace.txt; independently reproduced in I1-B | Keep set member query and serialization in the authorization session; capture the persisted receipt EUID before commit expires the ORM instance. APIs, lineage, and permissions are unchanged. |
| D03 | none | Apparent filter clearing failure withdrawn after normal keyboard clearing succeeded. | WITHDRAWN | Browser automation | All I1-A-STORE-FILTER observations retained | Empty-string locator fill did not clear the input; Select All/Backspace worked. No Dewey change warranted. |
| D04 | P2 | Add upload destination is unnamed because modal and background form reuse DOM id uri. | ATTEMPTING_BUGFIX | Dewey | I1-A-ADD-UPLOAD-MODE; independently reproduced in I1-B | Field and textarea helpers assign unique DOM IDs; API form names remain unchanged. Prevents background/modal label collisions. |
| D05 | P2 | Embedded template validation rejects same-site form with Origin not allowed. | ATTEMPTING_BUGFIX | Dewey | I1-A-TAP-TEMPLATE-VALIDATE; independently reproduced in I1-B | Dewey globally forced Referrer-Policy no-referrer, which gives native POST navigations Origin null under Fetch. Default same-origin now preserves a same-site form Origin and suppresses cross-site referrers; explicit preview no-referrer is retained. Origin enforcement remains intact. Inference from reproduced form rejection, actual form action, deployed header, source, and https://fetch.spec.whatwg.org/#append-a-request-origin-header; verify after deploy. |
| D06 | P2 | Protected record destination is lost after successful shared login. | ATTEMPTING_BUGFIX | Dewey | I1-A-LOGIN-RETURN; I1-B-LOGIN-RETURN; independently reproduced in I1-B | Registry pages now carry their exact path/query into the existing /login?next= flow. |

## Coverage and evidence

Feature inventory: `evidence/20260916T183133Z_dewey_gui_audit/features.json`. Append-only attempts: `evidence/20260916T183133Z_dewey_gui_audit/observations.jsonl`. Full matrix and attempt details are in `20260916T183133Z_dewey_gui_audit_report.md`.

## Amendments and limits

- User explicitly authorized GUI campaign twice; automated code test suites remain off.
- Four signup aliases approved; human completes new credential entry. Signup verification emails and replies authorized only for those test accounts.
- Destructive controls are inspection-only; retain all fixtures and partial uploads.
- No source edits before G03. Audit bookkeeping scripts are evidence tooling, not application bugfixes.
- GUI snapshots and screenshots are written from the supported browser APIs to the evidence directory; content export is unsupported.
- Early ADMIN-PAGE/ADMIN-RELEASE receipts numbered 3/4 captured the inactive account tab because of a recorder binding error. Corrected same-attempt timestamped receipts supersede them; original files retained.
- I1-A broadened the exact-URL inventory to all 60 displayed bucket roots; traversal is limited to each root first page and selected bounded fixtures.
- D03 was withdrawn after keyboard clearing succeeded; earlier failure evidence remains append-only.
- Token issuance and I1-A signup password handoff are pending user action; independent coverage continues.
- A downloaded canonical template pack and DAG export were verified on disk and retained; generation alone was not counted as delivery.
- I1-B reached all60bucket roots; the auditbucket blocked by browser in I1-A rendered in I1-B. QEO root remains blocked by existing bucket policy.
- Signup password submission/verification, recipient-role access, and token issuance remain blocked by user-action gates. Signup field validation and email verification are not claimed passed.
- Invitation API acceptance is observed but email delivery is unverified in both baseline attempts. No mailbox messages found for approved aliases.
- Repository-pack inventory requires a verified explicit server path; global/raw TapDB mutations remain excluded. No application source changed before baseline freeze.
- D05 diagnosis is a Dewey response-policy integration issue; the native POST Origin behavior is specified at https://fetch.spec.whatwg.org/#append-a-request-origin-header. No TapDB pin or origin allowlist change.
- Release and documentation commits include [skip ci] to preserve the user prohibition on a CI campaign. No test/lint/coverage suites run.

## Closeout

{
  "all_rows_terminal": false,
  "objective_complete": false
}
