# Dewey GUI audit report

Updated: 2026-09-16T20:16:32.919032+00:00

Status: Baseline frozen; implementing one Dewey bugfix release.

Two independent GUI attempts are recorded per iteration. Inspection-only exclusions and blocked actions are not passes. Signed URLs, credentials, passwords and verification codes are excluded from durable evidence.

## Deployment

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

## Feature matrix

| ID | Feature | URL / surface | I1-A | I1-B | I2-A | I2-B |
|---|---|---|---|---|---|---|
| LOGIN-LOGIN | Existing Google sign-in and return | https://dewey.day.lsmc.bio/login | PASS | PASS | PENDING | PENDING |
| LOGIN-LOGOUT | Sign out and protected-page redirect | https://dewey.day.lsmc.bio/login | PASS | PASS | PENDING | PENDING |
| LOGIN-SIGNUP | Signup form and approved email entry | https://dewey.day.lsmc.bio/login | INSPECTED_ONLY | PASS | PENDING | PENDING |
| LOGIN-SIGNUP-COMPLETE | New account signup and email verification | https://dewey.day.lsmc.bio/login | BLOCKED | BLOCKED | PENDING | PENDING |
| LIB-PAGE | Library loads | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-SEARCH | Search names/EUID/metadata | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-EMPTY | Empty search result | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-KIND | Object and prefix filtering | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-SORT | Sort order | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-PAGE-NEXT | Pagination next/previous | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-FILTERS | Advanced JSON filters valid/invalid | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-SELECT | Selection and create-set navigation | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-LOOKUP | Open EUID | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| LIB-BACK | Browser back/forward restores results | https://dewey.day.lsmc.bio/ui | PASS | PASS | PENDING | PENDING |
| ADD-PAGE | Registration form | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-OBJECT | Register S3 object | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-URL | Register HTTP URL | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-PREFIX | Register prefix | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-SET | Register set | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-METADATA | JSON and key/value metadata | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-VALIDATION | Required and invalid input handling | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-DUPLICATE | Duplicate registration behavior | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| ADD-UPLOAD-MODE | Add form upload mode | https://dewey.day.lsmc.bio/add | FAIL | FAIL | PENDING | PENDING |
| STORE-BUCKETS | Bucket list | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-BUCKET-LINKS | Browse listed buckets | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-URI | Exact URI and Go | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-BREADCRUMBS | Breadcrumb and folder navigation | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-FILTER | Filter names on current page | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-PAGE-NEXT | Storage pagination | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-OBJECT | Object detail modal | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-REGISTER | Register selected object/folder links | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-SET | Register storage selection as set | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-UPLOAD | New small files upload | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-UPLOAD-MULTIPART | Bounded multipart upload | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-DOWNLOAD | Browser download and byte verification | https://dewey.day.lsmc.bio/storage | FAIL | FAIL | PENDING | PENDING |
| STORE-EMPTY | Empty prefix | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-ERROR | Invalid location/error feedback | https://dewey.day.lsmc.bio/storage | PASS | PASS | PENDING | PENDING |
| STORE-DELETE | Deletion interfaces only | https://dewey.day.lsmc.bio/storage | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| STORE-REPLACE | Replacement interface only | https://dewey.day.lsmc.bio/storage | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| STORE-ABORT | Upload-abort control only | https://dewey.day.lsmc.bio/storage | EXCLUDED | INSPECTED_ONLY | PENDING | PENDING |
| RECORD-OBJECT | Object detail | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-PREFIX | Prefix contents | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-SET | Set detail and member links | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-EDIT | Fixture metadata edit | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-PREVIEW | HTML report preview and assets | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-DOWNLOAD | Record download | https://dewey.day.lsmc.bio/records/{euid} | FAIL | FAIL | PENDING | PENDING |
| RECORD-MANIFEST | Prefix/set access manifest | https://dewey.day.lsmc.bio/records/{euid} | FAIL | FAIL | PENDING | PENDING |
| RECORD-MEMBER-ADD | Add existing member | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-OWNER | Fixture ownership transfer | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-PERMISSIONS | Fixture metadata/download permissions | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-ACTIVITY | Activity and technical detail | https://dewey.day.lsmc.bio/records/{euid} | PASS | PASS | PENDING | PENDING |
| RECORD-ARCHIVE | Archive interface only | https://dewey.day.lsmc.bio/records/{euid} | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| RECORD-MEMBER-REMOVE | Member removal interface only | https://dewey.day.lsmc.bio/records/{euid} | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| SET-PAGE | Sets page | https://dewey.day.lsmc.bio/sets | PASS | PASS | PENDING | PENDING |
| SET-SEARCH | Sets search/filter/sort | https://dewey.day.lsmc.bio/sets | PASS | PASS | PENDING | PENDING |
| SET-CREATE-SELECTION | Create set from library selection | https://dewey.day.lsmc.bio/sets | PASS | PASS | PENDING | PENDING |
| SHARE-PAGE | Sharing list | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-SEARCH | Sharing search/filter/sort | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-CREATE | Create private/approved-recipient fixture share | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-DETAIL | Share detail and activity | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-COPY | Copy link | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-OPEN | Open shared record | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-EDIT | Fixture share edit | https://dewey.day.lsmc.bio/shares | PASS | PASS | PENDING | PENDING |
| SHARE-INVITE | Send invitation to approved alias | https://dewey.day.lsmc.bio/shares | BLOCKED | BLOCKED | PENDING | PENDING |
| SHARE-RECIPIENT | Test account recipient access | https://dewey.day.lsmc.bio/shares | BLOCKED | BLOCKED | PENDING | PENDING |
| SHARE-REVOKE | Revocation interface only | https://dewey.day.lsmc.bio/shares | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| LIT-PAGE | Literature page | https://dewey.day.lsmc.bio/literature | PASS | PASS | PENDING | PENDING |
| LIT-SEARCH | PubMed search | https://dewey.day.lsmc.bio/literature | PASS | PASS | PENDING | PENDING |
| LIT-PAGE-NEXT | Literature pagination | https://dewey.day.lsmc.bio/literature | PASS | PASS | PENDING | PENDING |
| LIT-EMPTY | No matches/error states | https://dewey.day.lsmc.bio/literature | PASS | PASS | PENDING | PENDING |
| LIT-REGISTER | Register paper and open artifact | https://dewey.day.lsmc.bio/literature | PASS | PASS | PENDING | PENDING |
| ACCOUNT-PAGE | Account and CLI instructions | https://dewey.day.lsmc.bio/account | PASS | PASS | PENDING | PENDING |
| ACCOUNT-TOKEN-FORM | Personal token form | https://dewey.day.lsmc.bio/account | PASS | PASS | PENDING | PENDING |
| ACCOUNT-TOKEN-CREATE | Credential issuance gate | https://dewey.day.lsmc.bio/account | BLOCKED | BLOCKED | PENDING | PENDING |
| ACCOUNT-TOKEN-REVOKE | Revocation interface only | https://dewey.day.lsmc.bio/account | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| ADMIN-PAGE | Administration page | https://dewey.day.lsmc.bio/admin | PASS | PASS | PENDING | PENDING |
| ADMIN-CONFIG | Redacted configuration | https://dewey.day.lsmc.bio/admin | PASS | PASS | PENDING | PENDING |
| ADMIN-RELEASE | Release identity | https://dewey.day.lsmc.bio/admin | FAIL | FAIL | PENDING | PENDING |
| ADMIN-DEFAULTS | Defaults form inspection | https://dewey.day.lsmc.bio/admin | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| ADMIN-HEALTH | Health page | https://dewey.day.lsmc.bio/admin | BLOCKED | BLOCKED | PENDING | PENDING |
| ADMIN-OBS | Observability | https://dewey.day.lsmc.bio/admin | PASS | PASS | PENDING | PENDING |
| ADMIN-ANOMALIES | Anomalies and detail | https://dewey.day.lsmc.bio/admin | PASS | PASS | PENDING | PENDING |
| TAP-OVERVIEW | Overview/count links | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-SEARCH | Search instances/templates/lineage | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-OBJECT | Object detail and links | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-GRAPH | Graph controls | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-TEMPLATES | Templates and create/edit forms inspection | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-AUDIT | Audit explorer filters | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-HELP | Help | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-READINESS | Readiness | https://dewey.day.lsmc.bio/tapdb/ | BLOCKED | BLOCKED | PENDING | PENDING |
| TAP-INVENTORY | Inventory | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-MERIDIAN | Meridian | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-METRICS | Metrics | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-RUNTIME | Runtime | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-BACKUPS | Backup/recovery interfaces inspection | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| TAP-THEME | Theme/help controls | https://dewey.day.lsmc.bio/tapdb/ | PASS | PASS | PENDING | PENDING |
| ROUTES-ROOT | Root redirect | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-SEARCH | Search alternate route | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-ARTIFACTS | Artifacts alternate route | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-DAG | Artifact DAG alternate route | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-DETAIL | Artifact detail alternate route | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-GRAPH | Standalone graph | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-ADMIN-SHARES | Admin shares alternate route | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ROUTES-DOCS | API reference | https://dewey.day.lsmc.bio/ | PASS | PASS | PENDING | PENDING |
| ADD-UPLOAD-EXEC | Upload from Add without automatic registration | https://dewey.day.lsmc.bio/add | PASS | PASS | PENDING | PENDING |
| LIB-FILTERS-INVALID | Reject invalid advanced filter JSON | https://dewey.day.lsmc.bio/ui?page=2 | PASS | PASS | PENDING | PENDING |
| SET-PAGINATION | Sets pagination availability | https://dewey.day.lsmc.bio/sets?q=20260916+I1-A&sort=name&page=1 | BLOCKED | BLOCKED | PENDING | PENDING |
| BUCKET-aquarium-tfstate-dev | Bucket root aquarium-tfstate-dev | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-aquarium-tfstate-prod | Bucket root aquarium-tfstate-prod | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-asterism-note-screenshots-dev | Bucket root asterism-note-screenshots-dev | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd | Bucket root aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp | Bucket root aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-cdk-dayhoff-assets-108782052779-us-east-1 | Bucket root cdk-dayhoff-assets-108782052779-us-east-1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-cdk-dayhoff-assets-108782052779-us-west-2 | Bucket root cdk-dayhoff-assets-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1 | Bucket root cdk-hnb659fds-assets-108782052779-us-east-1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2 | Bucket root cdk-hnb659fds-assets-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-cf-templates-pfrobpqqun1c-us-east-2 | Bucket root cf-templates-pfrobpqqun1c-us-east-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-dayec-cur-108782052779-us-east-1 | Bucket root dayec-cur-108782052779-us-east-1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-daylily-customer-lsmc-a0477268 | Bucket root daylily-customer-lsmc-a0477268 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-atlas-demo | Bucket root lsmc-atlas-demo | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-atlas-dev | Bucket root lsmc-atlas-dev | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-aws-config-108782052779 | Bucket root lsmc-aws-config-108782052779 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1 | Bucket root lsmc-bio-oauth-static-site-108782052779-us-east-1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-copy-ultimagen-lsmc-cro-316 | Bucket root lsmc-copy-ultimagen-lsmc-cro-316 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-datalake-raw-dev | Bucket root lsmc-datalake-raw-dev | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-analysis-results-usw2 | Bucket root lsmc-dayoa-analysis-results-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-control-data-use1 | Bucket root lsmc-dayoa-control-data-use1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-control-data-usw2 | Bucket root lsmc-dayoa-control-data-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-omics-analysis-us-west-2 | Bucket root lsmc-dayoa-omics-analysis-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-references-use1 | Bucket root lsmc-dayoa-references-use1 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-references-usw2 | Bucket root lsmc-dayoa-references-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-runtime-assets-usw2 | Bucket root lsmc-dayoa-runtime-assets-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dayoa-staging-usw2 | Bucket root lsmc-dayoa-staging-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-dewey-0 | Bucket root lsmc-dewey-0 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-docs-public-108782052779-us-west-2 | Bucket root lsmc-docs-public-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-healthomics-failiover | Bucket root lsmc-healthomics-failiover | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-healthomics-results | Bucket root lsmc-healthomics-results | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-ifx-bjuice-pkgd-data | Bucket root lsmc-ifx-bjuice-pkgd-data | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-illumina-public-data | Bucket root lsmc-illumina-public-data | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-meridian-governance-registry | Bucket root lsmc-meridian-governance-registry | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2 | Bucket root lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2 | Bucket root lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2 | Bucket root lsmc-mvp-v1-labcore-ui-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779 | Bucket root lsmc-mvp-v1-status-alb-logs-108782052779 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-public-ont-data | Bucket root lsmc-public-ont-data | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2 | Bucket root lsmc-qeo-day-analytical-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-qeo-day-analytical-108782052779-us-west-2%2F | BLOCKED | BLOCKED | PENDING | PENDING |
| BUCKET-lsmc-ssf-sequencing-data | Bucket root lsmc-ssf-sequencing-data | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-terraform-state | Bucket root lsmc-terraform-state | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-terraform-state%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-twenty-prod-storage | Bucket root lsmc-twenty-prod-storage | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2 | Bucket root lsmc-ursa-cost-reports-108782052779-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-lsmc-ursa-customers-usw2 | Bucket root lsmc-ursa-customers-usw2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps | Bucket root marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie | Bucket root marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F | BLOCKED | PASS | PENDING | PENDING |
| BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo | Bucket root marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj | Bucket root marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl | Bucket root marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete | Bucket root parallelcluster-4da281c1dc024f1c-v1-do-not-delete | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete | Bucket root parallelcluster-730cb6d53cf2deec-v1-do-not-delete | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete | Bucket root parallelcluster-e781c59d26140bab-v1-do-not-delete | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-dev-media | Bucket root terrarium-dev-media | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-dev-web | Bucket root terrarium-dev-web | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-prod-media | Bucket root terrarium-prod-media | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-prod-web | Bucket root terrarium-prod-web | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-tfstate-dev | Bucket root terrarium-tfstate-dev | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-terrarium-tfstate-prod | Bucket root terrarium-tfstate-prod | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-ursa-us-west-2-052779-default-customer-1d8c14 | Bucket root ursa-us-west-2-052779-default-customer-1d8c14 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F | PASS | PASS | PENDING | PENDING |
| BUCKET-zebra-day-cfg-us-west-2 | Bucket root zebra-day-cfg-us-west-2 | https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F | PASS | PASS | PENDING | PENDING |
| TAP-OBJECT-JSON | Object JSON editor formatting without persistence | https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S | PASS | PASS | PENDING | PENDING |
| TAP-OBJECT-MUTATIONS | Raw admin object/lineage/repair interfaces | https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| TAP-SEARCH-TEMPLATE | Template-kind search | https://dewey.day.lsmc.bio/tapdb/search?q=M-DGX-1A&record_type=template&name_like=&euid_like=&category=&type=&subtype= | PASS | PASS | PENDING | PENDING |
| TAP-SEARCH-LINEAGE | Lineage-kind search | https://dewey.day.lsmc.bio/tapdb/search?q=M-EDG-G28C&record_type=lineage&name_like=&euid_like=&category=&type=&subtype= | PASS | PASS | PENDING | PENDING |
| TAP-CONTEXT-HELP | Context help and clipboard | https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TR3S&prefix= | PASS | PASS | PENDING | PENDING |
| TAP-TEMPLATE-DOWNLOAD | Canonical template JSON browser download | https://dewey.day.lsmc.bio/tapdb/templates?category=data | PASS | PASS | PENDING | PENDING |
| TAP-INSTANCE-CREATE | Raw instance creation interface | https://dewey.day.lsmc.bio/tapdb/create/M-DGX-1A | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| TAP-TEMPLATE-VALIDATE | Template builder read-only validation | https://dewey.day.lsmc.bio/tapdb/templates/validate | FAIL | FAIL | PENDING | PENDING |
| TAP-TEMPLATE-BUILDER | Template schema builder interface | https://dewey.day.lsmc.bio/tapdb/templates/validate | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| TAP-SEARCH-PAGINATION | Search continuation paging | https://dewey.day.lsmc.bio/tapdb/search?record_type=all&limit=25&cursor=eyJraW5kIjoiaW5zdGFuY2UiLCJ1aWQiOjl9 | PASS | PASS | PENDING | PENDING |
| TAP-OBJECT-GRAPH | Object graph with persisted lineage | https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S/graph | PASS | PASS | PENDING | PENDING |
| TAP-GRAPH-CONTROLS | Graph search/find/filter/layout/centering controls | https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S | PASS | PASS | PENDING | PENDING |
| TAP-GRAPH-EXPORT | Graph JSON browser download | https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S | PASS | PASS | PENDING | PENDING |
| TAP-GRAPH-MUTATIONS | Graph mutation gestures inspection | https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| ADMIN-ANOMALY-DETAIL | Persisted anomaly detail | https://dewey.day.lsmc.bio/ui/anomalies/M-DGX-9RJX | PASS | PASS | PENDING | PENDING |
| LOGIN-RETURN | Preserve requested record through login | https://dewey.day.lsmc.bio/ui | FAIL | FAIL | PENDING | PENDING |
| TAP-PACK-INVENTORY | Explicit repository pack inventory | https://dewey.day.lsmc.bio/tapdb/templates | BLOCKED | BLOCKED | PENDING | PENDING |
| TAP-PACK-EXPORT | Repository pack export interface only | https://dewey.day.lsmc.bio/tapdb/templates | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| TAP-BACKUP-MUTATIONS | Backup creation and recovery interfaces only | https://dewey.day.lsmc.bio/tapdb/admin/backups | INSPECTED_ONLY | INSPECTED_ONLY | PENDING | PENDING |
| SET-FILTER | Set metadata filters | https://dewey.day.lsmc.bio/sets?filters=%5B%7B%22path%22%3A%22metadata.gui_audit.attempt%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22I1-A%22%7D%5D&page=1 | PASS | PASS | PENDING | PENDING |
| SHARE-PAGINATION | Share continuation pages | https://dewey.day.lsmc.bio/shares?page=2 | PASS | PASS | PENDING | PENDING |
| SHARE-FILTER | Share property filters | https://dewey.day.lsmc.bio/shares?page=1&filters=%5B%7B%22path%22%3A%22audience%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22recipients%22%7D%5D | PASS | PASS | PENDING | PENDING |

## Counts

{
  "I1-A": {
    "PASS": 157,
    "INSPECTED_ONLY": 14,
    "BLOCKED": 10,
    "FAIL": 7,
    "EXCLUDED": 1
  },
  "I1-B": {
    "PASS": 159,
    "BLOCKED": 9,
    "FAIL": 7,
    "INSPECTED_ONLY": 14
  },
  "I2-A": {
    "PENDING": 189
  },
  "I2-B": {
    "PENDING": 189
  }
}

## Bugs

[
  {
    "id": "D01",
    "severity": "P3",
    "description": "Release surfaces show a stale build branch despite correct deployed version/SHA.",
    "status": "ATTEMPTING_BUGFIX",
    "owner": "Dewey",
    "evidence": "I1-A-ADMIN-RELEASE; production-baseline.json; independently reproduced in I1-B",
    "root_cause": "Deployment operator updates only exact Dewey image and source SHA/branch environment fields. Post-deploy GUI verification pending."
  },
  {
    "id": "D02",
    "severity": "P1",
    "description": "S3 object download, registered object access and set manifests return HTTP500.",
    "status": "ATTEMPTING_BUGFIX",
    "owner": "Dewey",
    "evidence": "I1-A-STORE-DOWNLOAD; I1-A-RECORD-DOWNLOAD; I1-A-RECORD-MANIFEST; I1-A-download-manifest-trace.txt; independently reproduced in I1-B",
    "root_cause": "Keep set member query and serialization in the authorization session; capture the persisted receipt EUID before commit expires the ORM instance. APIs, lineage, and permissions are unchanged."
  },
  {
    "id": "D03",
    "severity": "none",
    "description": "Apparent filter clearing failure withdrawn after normal keyboard clearing succeeded.",
    "status": "WITHDRAWN",
    "owner": "Browser automation",
    "evidence": "All I1-A-STORE-FILTER observations retained",
    "root_cause": "Empty-string locator fill did not clear the input; Select All/Backspace worked. No Dewey change warranted."
  },
  {
    "id": "D04",
    "severity": "P2",
    "description": "Add upload destination is unnamed because modal and background form reuse DOM id uri.",
    "status": "ATTEMPTING_BUGFIX",
    "owner": "Dewey",
    "evidence": "I1-A-ADD-UPLOAD-MODE; independently reproduced in I1-B",
    "root_cause": "Field and textarea helpers assign unique DOM IDs; API form names remain unchanged. Prevents background/modal label collisions."
  },
  {
    "id": "D05",
    "severity": "P2",
    "description": "Embedded template validation rejects same-site form with Origin not allowed.",
    "status": "ATTEMPTING_BUGFIX",
    "owner": "Dewey",
    "evidence": "I1-A-TAP-TEMPLATE-VALIDATE; independently reproduced in I1-B",
    "root_cause": "Dewey globally forced Referrer-Policy no-referrer, which gives native POST navigations Origin null under Fetch. Default same-origin now preserves a same-site form Origin and suppresses cross-site referrers; explicit preview no-referrer is retained. Origin enforcement remains intact. Inference from reproduced form rejection, actual form action, deployed header, source, and https://fetch.spec.whatwg.org/#append-a-request-origin-header; verify after deploy."
  },
  {
    "id": "D06",
    "severity": "P2",
    "description": "Protected record destination is lost after successful shared login.",
    "status": "ATTEMPTING_BUGFIX",
    "owner": "Dewey",
    "evidence": "I1-A-LOGIN-RETURN; I1-B-LOGIN-RETURN; independently reproduced in I1-B",
    "root_cause": "Registry pages now carry their exact path/query into the existing /login?next= flow."
  }
]

## Attempt records

### TAP-OVERVIEW I1-A — PASS

- **timestamp**: 2026-09-16T19:02:20.261Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/
- **expected**: Embedded overview loads with counts and navigation
- **observed**: Overview loaded with 16 templates, 17592 instances and 6434 lineage edges.
- **evidence**: I1-A-TAP-OVERVIEW-1.txt ; I1-A-TAP-OVERVIEW-1.png

### LIB-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:18.414Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / LIBRARY<br>  - heading "Library" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - searchbox "Search library"<br>  - combobox "Kind":<br>    - option "All kinds" [selected]<br>    - option "Objects"<br>    - option "Prefixes"<br>  - combobox "Sort":<br>    - option "Newest first" [selected]<br>    - option "Name"<br>  - button "Search"<br>  - button "Filters"<br>  - generic: 5,120 accessible records<br>  - button "Create set from selection"<br>  - link "New set":<br>    - /url: /add?kind=set<br>  - table:<br>    - rowgroup:<br>      - row "Name / EUID Kind Producer Created":<br>        - columnheader<br>        - columnheader "Name / EUID"<br>        - columnheader "Kind"<br>        - columnheader "Producer"<br>        - columnheader "Created"<br>    - rowgroup:<br>      - row "Select
- **evidence**: I1-A-LIB-PAGE-2.txt ; I1-A-LIB-PAGE-2.png

### ADD-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:18.843Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ADD<br>  - heading "Add" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Register an artifact" [level=2]<br>  - generic: What are you adding?<br>  - combobox "What are you adding?":<br>    - option "Object · one file or URL" [selected]<br>    - option "Prefix · one S3 folder or bucket"<br>    - option "Set · selected Object and Prefix EUIDs"<br>    - option "Upload · add a new file to S3"<br>  - generic: S3 URI or HTTP(S) URL<br>  - textbox "S3 URI or HTTP(S) URL"<br>  - generic: S3 keys are preserved exactly. A prefix receives one EUID; its children are not registered.<br>  - generic: Name<br>  - textbox "Name"<br>  - generic: Description<br>  - textbox "Description"<br>  - generic "Metadata"<br>  - button "Register"<br>  - complementary:<br>    - heading
- **evidence**: I1-A-ADD-PAGE-3.txt ; I1-A-ADD-PAGE-3.png

### SET-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:19.840Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / SETS<br>  - heading "Sets" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - searchbox "Search library"<br>  - combobox "Sort":<br>    - option "Newest first" [selected]<br>    - option "Name"<br>  - button "Search"<br>  - button "Filters"<br>  - generic: 10 accessible records<br>  - link "New set":<br>    - /url: /add?kind=set<br>  - table:<br>    - rowgroup:<br>      - row "Name / EUID Visible members Created":<br>        - columnheader "Name / EUID"<br>        - columnheader "Visible members"<br>        - columnheader "Created"<br>    - rowgroup:<br>      - row "Dewey 9.0.0 production acceptance M-DGX-NP19 1 9/11/2026":<br>        - cell "Dewey 9.0.0 production acceptance M-DGX-NP19":<br>          - link "Dewey 9.0.0 production acceptance":<br>            - /url: /recor
- **evidence**: I1-A-SET-PAGE-4.txt ; I1-A-SET-PAGE-4.png

### SHARE-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:20.550Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / SHARING<br>  - heading "Sharing" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - searchbox "Search library"<br>  - combobox "Sort":<br>    - option "Newest first" [selected]<br>    - option "Name"<br>  - button "Search"<br>  - button "Filters"<br>  - generic: 38 accessible shares<br>  - table:<br>    - rowgroup:<br>      - row "Name / EUID Audience / recipients Status Expires Owner Last access":<br>        - columnheader "Name / EUID"<br>        - columnheader "Audience / recipients"<br>        - columnheader "Status"<br>        - columnheader "Expires"<br>        - columnheader "Owner"<br>        - columnheader "Last access"<br>    - rowgroup:<br>      - row "Direct download M-DGX-NG57 M-DGX-NJK8 — john@daylilyinformatics.com expired 9/11/2026 john@daylilyinformat
- **evidence**: I1-A-SHARE-PAGE-5.txt ; I1-A-SHARE-PAGE-5.png

### LIT-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:20.966Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / LITERATURE<br>  - heading "Literature" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Search PubMed" [level=2]<br>  - searchbox "PubMed query"<br>  - button "Search"<br>  - paragraph: Register papers as ordinary Dewey artifacts with a PMID and rich metadata.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-LIT-PAGE-6.txt ; I1-A-LIT-PAGE-6.png

### ACCOUNT-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:04:21.506Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ACCOUNT<br>  - heading "Account" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "CLI and API access" [level=2]<br>  - paragraph: Create a personal token to use the same authorized EUID operations from your terminal.<br>  - generic: export DEWEY_API_URL="https://dewey.day.lsmc.bio" export DEWEY_API_TOKEN_FILE="/absolute/private/token-file" dewey artifacts get <EUID> dewey artifacts contents <PREFIX_EUID> dewey artifacts access <EUID><br>  - button "Create token"<br>  - heading "Your tokens" [level=2]<br>  - paragraph: No personal tokens.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":
- **evidence**: I1-A-ACCOUNT-PAGE-7.txt ; I1-A-ACCOUNT-PAGE-7.png

### ACCOUNT-TOKEN-FORM I1-A — PASS

- **timestamp**: 2026-09-16T19:05:14.801Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Token form exposes name, role and lifetime
- **observed**: Form opened with read-only/read-write/admin choices; prepared a one-day read-only fixture. No credential issued.
- **evidence**: I1-A-ACCOUNT-TOKEN-FORM-2.txt

### ADMIN-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:06:25.103Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Admin links and settings load
- **observed**: Service administration and embedded TapDB links loaded.
- **evidence**: I1-A-ADMIN-PAGE-3.txt ; I1-A-ADMIN-PAGE-3.png

### ADMIN-RELEASE I1-A — REVIEW

- **timestamp**: 2026-09-16T19:06:25.450Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Version/SHA/branch reflect actual deployed source
- **observed**: Release identity expanded for comparison against verified tag df6d4d0 and working branch.
- **evidence**: I1-A-ADMIN-RELEASE-4.txt ; I1-A-ADMIN-RELEASE-4.png

### ADMIN-PAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:07:08.308Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Admin links and settings load
- **observed**: Service administration and embedded TapDB links loaded. Corrects prior recorder binding to inactive token tab.
- **evidence**: I1-A-ADMIN-PAGE-1789585628308.txt ; I1-A-ADMIN-PAGE-1789585628308.png

### ADMIN-CONFIG I1-A — PASS

- **timestamp**: 2026-09-16T19:07:08.523Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Configuration values are visible with secrets redacted
- **observed**: Expanded effective configuration: service_token, authorization, API tokens and signing key fields are redacted; managed bucket lsmc-dewey-0.
- **evidence**: I1-A-ADMIN-CONFIG-1789585628523.txt ; I1-A-ADMIN-CONFIG-1789585628523.png

### ADMIN-RELEASE I1-A — FAIL

- **timestamp**: 2026-09-16T19:07:08.642Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Release branch/SHA/tag match deployed source
- **observed**: 10.0.5/SHA df6d4d0 agree, but GUI branch is stale codex/dewey-labcore-910; actual source is codex/ursa-final-gap-dewey-20260913.
- **evidence**: I1-A-ADMIN-RELEASE-1789585628642.txt ; I1-A-ADMIN-RELEASE-1789585628642.png

### ADMIN-DEFAULTS I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:07:20.761Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Defaults form loads; do not save shared settings
- **observed**: Edit defaults opened; shared production values not submitted.
- **evidence**: I1-A-ADMIN-DEFAULTS-1789585640761.txt

### ADMIN-HEALTH I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:07:45.832Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Health page loads in GUI
- **observed**: Browser navigation to /health failed with net::ERR_BLOCKED_BY_CLIENT; no protection bypass attempted.
- **evidence**: I1-A-ADMIN-HEALTH-1789585665832.txt

### ADMIN-OBS I1-A — PASS

- **timestamp**: 2026-09-16T19:07:46.448Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/observability
- **expected**: Page fully renders its expected content
- **observed**: c: p95 548317.608 ms<br>    - generic: 13 calls<br>  - article:<br>    - generic: service:registry_browse<br>    - generic: p95 1038.828 ms<br>    - generic: 17 calls<br>  - article:<br>    - generic: service:registry_buckets<br>    - generic: p95 486.571 ms<br>    - generic: 4 calls<br>  - article:<br>    - generic: service:require_storage_access<br>    - generic: p95 382.292 ms<br>    - generic: 60 calls<br>  - article:<br>    - generic: service:register_artifact<br>    - generic: p95 283.155 ms<br>    - generic: 2 calls<br>  - heading "Auth" [level=3]<br>  - generic: Recent auth events for session and bearer access.<br>  - generic: "Configured: True"<br>  - generic: "Sessions supported: False"<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 3f3af1ecebbd1410<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - heading "Local Anomalies" [level=3]<br>  - generic: Read-only local anomaly records persisted in TapDB.<br>  - link "Open anomaly view":<br>    - /url: /ui/anomalies<br>  - generic: "high: Artifact storage review is pending"<br>  - generic: "medium: Readiness probe observed a bootstrap gap"<br>  - generic: "low: Operator session activity is sparse"<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original"<br>  - option "light"<br>  - option "dark" [selected]<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-ADMIN-OBS-1789585666448.txt ; I1-A-ADMIN-OBS-1789585666448.png

### ADMIN-ANOMALIES I1-A — PASS

- **timestamp**: 2026-09-16T19:07:46.827Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/anomalies
- **expected**: Page fully renders its expected content
- **observed**:   - /url: /admin<br>  - button "Logout"<br>- main:<br>  - generic: Read-only local records<br>  - heading "Persisted anomaly records for this Dewey instance." [level=2]<br>  - paragraph: These are local operational summaries only. They are not release authority and they do not mutate backend state.<br>  - generic: 3 records<br>  - table:<br>    - rowgroup:<br>      - row "Anomaly Severity Status Source Action":<br>        - columnheader "Anomaly"<br>        - columnheader "Severity"<br>        - columnheader "Status"<br>        - columnheader "Source"<br>        - columnheader "Action"<br>    - rowgroup:<br>      - row "M-DGX-9RJX Artifact storage review is pending high open storage Open":<br>        - cell "M-DGX-9RJX Artifact storage review is pending":<br>          - generic: M-DGX-9RJX<br>          - generic: Artifact storage review is pending<br>        - cell "high"<br>        - cell "open"<br>        - cell "storage"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RJX<br>      - row "M-DGX-9RG1 Readiness probe observed a bootstrap gap medium open readyz Open":<br>        - cell "M-DGX-9RG1 Readiness probe observed a bootstrap gap":<br>          - generic: M-DGX-9RG1<br>          - generic: Readiness probe observed a bootstrap gap<br>        - cell "medium"<br>        - cell "open"<br>        - cell "readyz"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RG1<br>      - row "M-DGX-9RHZ Operator session activity is sparse low monitoring auth_health Open":<br>        - cell "M-DGX-9RHZ Operator session activity is sparse":<br>          - generic: M-DGX-9RHZ<br>          - generic: Operator session activity is sparse<br>        - cell "low"<br>        - cell "monitoring"<br>        - cell "auth_health"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RHZ<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-ADMIN-ANOMALIES-1789585666827.txt ; I1-A-ADMIN-ANOMALIES-1789585666827.png

### ROUTES-GRAPH I1-A — PASS

- **timestamp**: 2026-09-16T19:07:47.040Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/graph
- **expected**: Page fully renders its expected content
- **observed**: - generic: DAY<br>- main:<br>  - heading "TapDB Object Graph" [level=1]<br>  - paragraph:<br>    - link "Open the TapDB graph explorer":<br>      - /url: /tapdb/graph<br>  - iframe<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac
- **evidence**: I1-A-ROUTES-GRAPH-1789585667040.txt ; I1-A-ROUTES-GRAPH-1789585667040.png

### ROUTES-ADMIN-SHARES I1-A — PASS

- **timestamp**: 2026-09-16T19:07:48.483Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin/shares
- **expected**: Page fully renders its expected content
- **observed**: KP None M-DGX-9XKP Users: none Domains: none Groups: none error 0 Details"':<br>        - cell "M-DGX-9YKN share:artifact:M-DGX-9XKP":<br>          - link "M-DGX-9YKN":<br>            - /url: /shares/M-DGX-9YKN<br>          - generic: share:artifact:M-DGX-9XKP<br>        - cell "None M-DGX-9XKP":<br>          - generic: None<br>          - generic: M-DGX-9XKP<br>        - 'cell "Users: none Domains: none Groups: none"':<br>          - generic: "Users: none"<br>          - generic: "Domains: none"<br>          - generic: "Groups: none"<br>        - cell<br>        - cell "error":<br>          - generic: error<br>        - cell "0"<br>        - cell "Details":<br>          - link "Details":<br>            - /url: /shares/M-DGX-9YKN<br>      - 'row "M-DGX-9YHS share:artifact:M-DGX-9XX2 None M-DGX-9XX2 Users: none Domains: none Groups: none error 0 Details"':<br>        - cell "M-DGX-9YHS share:artifact:M-DGX-9XX2":<br>          - link "M-DGX-9YHS":<br>            - /url: /shares/M-DGX-9YHS<br>          - generic: share:artifact:M-DGX-9XX2<br>        - cell "None M-DGX-9XX2":<br>          - generic: None<br>          - generic: M-DGX-9XX2<br>        - 'cell "Users: none Domains: none Groups: none"':<br>          - generic: "Users: none"<br>          - generic: "Domains: none"<br>          - generic: "Groups: none"<br>        - cell<br>        - cell "error":<br>          - generic: error<br>        - cell "0"<br>        - cell "Details":<br>          - link "Details":<br>            - /url: /shares/M-DGX-9YHS<br>  - heading "Tracked Roots" [level=3]<br>  - generic: Registered customer/collaborator roots. Registration does not scan S3 children.<br>  - generic: No tracked share roots are registered.<br>  - heading "Share Detail" [level=3]<br>  - generic: Open a share to inspect policy, mint an access package, or review audit decisions.<br>  - generic: Select a share to inspect policy and access history.<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-ROUTES-ADMIN-SHARES-1789585668483.txt ; I1-A-ROUTES-ADMIN-SHARES-1789585668483.png

### ROUTES-DOCS I1-A — REVIEW

- **timestamp**: 2026-09-16T19:07:49.191Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/docs
- **expected**: Page fully renders its expected content
- **observed**: - generic: loading
- **evidence**: I1-A-ROUTES-DOCS-1789585669191.txt ; I1-A-ROUTES-DOCS-1789585669191.png

### TAP-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:07:50.106Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search
- **expected**: Page fully renders its expected content
- **observed**: eta-runs/M-BDT-9SDK/a9be03c0_R1.fastq.gz"<br>        - cell "system/idempotency_request/generic"<br>        - cell "active"<br>      - row "M-DGX-9RNQ instance s3://beta-runs/M-BDT-9SDK/a9be03c0_R2.fastq.gz data/artifact/generic active":<br>        - cell "M-DGX-9RNQ":<br>          - link "M-DGX-9RNQ":<br>            - /url: /tapdb/object/M-DGX-9RNQ<br>        - cell "instance"<br>        - cell "s3://beta-runs/M-BDT-9SDK/a9be03c0_R2.fastq.gz"<br>        - cell "data/artifact/generic"<br>        - cell "active"<br>      - row "M-DGX-9RPN instance artifact.register:M-BDT-9SDK:fastq:s3://beta-runs/M-BDT-9SDK/a9be03c0_R2.fastq.gz system/idempotency_request/generic active":<br>        - cell "M-DGX-9RPN":<br>          - link "M-DGX-9RPN":<br>            - /url: /tapdb/object/M-DGX-9RPN<br>        - cell "instance"<br>        - cell "artifact.register:M-BDT-9SDK:fastq:s3://beta-runs/M-BDT-9SDK/a9be03c0_R2.fastq.gz"<br>        - cell "system/idempotency_request/generic"<br>        - cell "active"<br>      - row "M-DGX-9RQK instance s3://lsmc-dewey-0/functional-tests/20260520T120220Z-0f07e1/variants.vcf.gz data/artifact/generic active":<br>        - cell "M-DGX-9RQK":<br>          - link "M-DGX-9RQK":<br>            - /url: /tapdb/object/M-DGX-9RQK<br>        - cell "instance"<br>        - cell "s3://lsmc-dewey-0/functional-tests/20260520T120220Z-0f07e1/variants.vcf.gz"<br>        - cell "data/artifact/generic"<br>        - cell "active"<br>      - row "M-DGX-9RRH instance artifact.register:20260520T120220Z-0f07e1:dewey-variant system/idempotency_request/generic active":<br>        - cell "M-DGX-9RRH":<br>          - link "M-DGX-9RRH":<br>            - /url: /tapdb/object/M-DGX-9RRH<br>        - cell "instance"<br>        - cell "artifact.register:20260520T120220Z-0f07e1:dewey-variant"<br>        - cell "system/idempotency_request/generic"<br>        - cell "active"<br>  - paragraph:<br>    - link "Next page":<br>      - /url: /tapdb/search?record_type=all&limit=25&cursor=eyJraW5kIjoiaW5zdGFuY2UiLCJ1aWQiOjl9<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-SEARCH-1789585670106.txt ; I1-A-TAP-SEARCH-1789585670106.png

### TAP-GRAPH I1-A — PASS

- **timestamp**: 2026-09-16T19:07:51.059Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph
- **expected**: Page fully renders its expected content
- **observed**: /placeholder: blank shows visible graph<br>  - generic: Depth<br>  - spinbutton "Depth": "4"<br>  - generic: Maximum Nodes<br>  - spinbutton "Maximum Nodes": "200"<br>  - generic: Maximum Edges<br>  - spinbutton "Maximum Edges": "500"<br>  - button "Load Graph"<br>  - button "Fit"<br>  - heading "🔎 Search & Find" [level=3]<br>  - generic: Fuzzy Search<br>  - textbox "Fuzzy Search":<br>    - /placeholder: Match id, name, type, subtype<br>  - generic: Find Exact EUID<br>  - textbox "Find Exact EUID":<br>    - /placeholder: Exact EUID in current graph<br>  - button "Apply Search"<br>  - button "Find"<br>  - heading "🧰 Filters" [level=3]<br>  - generic: Connected Edge Count ≤<br>  - slider "Connected Edge Count ≤": "1"<br>  - generic: "1"<br>  - generic: Relative Distance (0 = all)<br>  - slider "Relative Distance (0 = all)": "0"<br>  - generic: "0"<br>  - generic: Type Visibility<br>  - generic: Load graph to populate.<br>  - generic: Subtype Muting<br>  - generic: Load graph to populate.<br>  - heading "⚙️ Layout" [level=3]<br>  - generic: Layout Type<br>  - combobox "Layout Type":<br>    - option "Dagre (Hierarchical)" [selected]<br>    - option "CoSE (Force-directed)"<br>    - option "Breadth First"<br>    - option "Circle"<br>    - option "Grid"<br>  - heading "⌨️ Graph Gestures" [level=3]<br>  - strong: D + right click<br>  - text: ": delete node or edge"<br>  - strong: 3x left click node<br>  - text: ": child-wave glow (pink)"<br>  - strong: 3x right click node<br>  - text: ": parent-wave glow (aqua)"<br>  - strong: L + left click node<br>  - text: ": pick child, then click parent to create edge"<br>  - strong: N + left click node<br>  - text: ": neighborhood highlight"<br>  - generic: Ready.<br>  - heading "🎨 Legend" [level=3]<br>  - generic: No visible nodes.<br>  - heading "💾 Export" [level=3]<br>  - button "Save DAG" [disabled]<br>  - generic: Mermaid<br>  - generic: Load a graph to generate Mermaid.<br>  - heading "📋 Details" [level=3]<br>  - paragraph: Click a node or edge to see details<br>  - generic "Nodes and edges"<br>  - generic "Payload JSON"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-GRAPH-1789585671059.txt ; I1-A-TAP-GRAPH-1789585671059.png

### TAP-GRAPH I1-A — PASS

- **timestamp**: 2026-09-16T19:09:02.898Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=2&max_nodes=30&max_edges=50&start_euid=M-DGX-9SZ2
- **expected**: Bounded graph loads and supports layout, fit and exact find
- **observed**: Loaded known persisted EUID with depth 2/max 30 nodes/50 edges; Circle layout, Fit and exact find worked; no graph mutation gestures used.
- **evidence**: I1-A-TAP-GRAPH-1789585742898.txt ; I1-A-TAP-GRAPH-1789585742898.png

### TAP-TEMPLATES I1-A — PASS

- **timestamp**: 2026-09-16T19:09:03.607Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates
- **expected**: Page fully renders its expected content
- **observed**: Template":<br>        - cell "M-DGX-8W":<br>          - link "M-DGX-8W":<br>            - /url: /tapdb/object/M-DGX-8W<br>        - cell "Dewey Idempotency"<br>        - cell "system/idempotency_request/generic/1.0"<br>        - cell "DGX"<br>        - cell "UNIVERSAL_PASS@1":<br>          - code: UNIVERSAL_PASS@1<br>        - cell "pending"<br>        - cell "Create":<br>          - link "Create":<br>            - /url: /tapdb/create/M-DGX-8W<br>        - cell "Build New Template":<br>          - link "Build New Template":<br>            - /url: /tapdb/templates/new?seed_euid=M-DGX-8W<br>      - row "M-DGX-9YPF Dewey Outbox Event system/outbox_event/generic/1.0 DGX UNIVERSAL_PASS@1 pending Create Build New Template":<br>        - cell "M-DGX-9YPF":<br>          - link "M-DGX-9YPF":<br>            - /url: /tapdb/object/M-DGX-9YPF<br>        - cell "Dewey Outbox Event"<br>        - cell "system/outbox_event/generic/1.0"<br>        - cell "DGX"<br>        - cell "UNIVERSAL_PASS@1":<br>          - code: UNIVERSAL_PASS@1<br>        - cell "pending"<br>        - cell "Create":<br>          - link "Create":<br>            - /url: /tapdb/create/M-DGX-9YPF<br>        - cell "Build New Template":<br>          - link "Build New Template":<br>            - /url: /tapdb/templates/new?seed_euid=M-DGX-9YPF<br>      - row "M-DGX-9YNH Dewey Registration Receipt system/registration_receipt/generic/1.0 DGX UNIVERSAL_PASS@1 pending Create Build New Template":<br>        - cell "M-DGX-9YNH":<br>          - link "M-DGX-9YNH":<br>            - /url: /tapdb/object/M-DGX-9YNH<br>        - cell "Dewey Registration Receipt"<br>        - cell "system/registration_receipt/generic/1.0"<br>        - cell "DGX"<br>        - cell "UNIVERSAL_PASS@1":<br>          - code: UNIVERSAL_PASS@1<br>        - cell "pending"<br>        - cell "Create":<br>          - link "Create":<br>            - /url: /tapdb/create/M-DGX-9YNH<br>        - cell "Build New Template":<br>          - link "Build New Template":<br>            - /url: /tapdb/templates/new?seed_euid=M-DGX-9YNH<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-TEMPLATES-1789585743607.txt ; I1-A-TAP-TEMPLATES-1789585743607.png

### TAP-AUDIT I1-A — PASS

- **timestamp**: 2026-09-16T19:09:04.113Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/audit
- **expected**: Page fully renders its expected content
- **observed**: nk "M-DGX-TPQJ":<br>            - /url: /tapdb/object/M-DGX-TPQJ<br>        - cell "UPDATE"<br>        - cell "dewey"<br>        - cell "integration/external_object_relation/generic"<br>        - cell "artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run"<br>        - cell:<br>          - generic "values"<br>      - row "2026-09-16 08:25:53.540837+00:00 M-DGX-TPQJ UPDATE dewey integration/external_object_relation/generic artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run":<br>        - cell "2026-09-16 08:25:53.540837+00:00"<br>        - cell "M-DGX-TPQJ":<br>          - link "M-DGX-TPQJ":<br>            - /url: /tapdb/object/M-DGX-TPQJ<br>        - cell "UPDATE"<br>        - cell "dewey"<br>        - cell "integration/external_object_relation/generic"<br>        - cell "artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run"<br>        - cell:<br>          - generic "values"<br>      - row "2026-09-16 08:25:53.540837+00:00 M-DGX-TPQJ UPDATE dewey integration/external_object_relation/generic artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run":<br>        - cell "2026-09-16 08:25:53.540837+00:00"<br>        - cell "M-DGX-TPQJ":<br>          - link "M-DGX-TPQJ":<br>            - /url: /tapdb/object/M-DGX-TPQJ<br>        - cell "UPDATE"<br>        - cell "dewey"<br>        - cell "integration/external_object_relation/generic"<br>        - cell "artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run"<br>        - cell:<br>          - generic "values"<br>      - row "2026-09-16 08:25:53.540837+00:00 M-DGX-TPQJ UPDATE dewey integration/external_object_relation/generic artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run":<br>        - cell "2026-09-16 08:25:53.540837+00:00"<br>        - cell "M-DGX-TPQJ":<br>          - link "M-DGX-TPQJ":<br>            - /url: /tapdb/object/M-DGX-TPQJ<br>        - cell "UPDATE"<br>        - cell "dewey"<br>        - cell "integration/external_object_relation/generic"<br>        - cell "artifact:M-DGX-TPJW:M-DGX-TPNP:bloom_sequencing_run"<br>        - cell:<br>          - generic "values"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-AUDIT-1789585744113.txt ; I1-A-TAP-AUDIT-1789585744113.png

### TAP-HELP I1-A — PASS

- **timestamp**: 2026-09-16T19:09:04.544Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/help
- **expected**: Page fully renders its expected content
- **observed**: b/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "TapDB GUI guide" [level=1]<br>  - paragraph: This is TapDB's single supported standalone and embedded web interface.<br>  - heading "Objects and lineage" [level=2]<br>  - paragraph: Use Search to find templates, instances, and lineage. Object pages show canonical relationships, validation evidence, and audit history. Administrators may create ordinary instances, repair governed JSON, change status, and create lineage. Core external-reference templates cannot be written through the generic forms.<br>  - heading "External references and discovery" [level=2]<br>  - paragraph: Federated TapDB references and opaque external identifiers are displayed separately. TapDB-object references can be followed by DAG-v2 federation clients; opaque identifiers are visible and exactly searchable but are never fetched or expanded.<br>  - heading "Operator tools" [level=2]<br>  - paragraph: Administrators can inspect readiness, schema inventory, Meridian governance, sanitized runtime information, query metrics, backups, restore reviews, and durable receipts. Mutation forms are explicit and fail closed.<br>  - heading "API" [level=2]<br>  - paragraph: The authenticated JSON surfaces mirror GUI operations. DAG v2 is the only graph protocol; DAG v1 and outbound proxy routes are not supported.<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-HELP-1789585744544.txt ; I1-A-TAP-HELP-1789585744544.png

### TAP-READINESS I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:09:04.755Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/help
- **expected**: Page fully renders its expected content
- **observed**: /tapdb/admin/readiness: Error: Browser Use cannot open https://dewey.day.lsmc.bio/tapdb/admin/readiness in tab 2. Browser reported: net::ERR_BLOCKED_BY_CLIENT
- **evidence**: I1-A-TAP-READINESS-1789585744755.txt

### TAP-INVENTORY I1-A — PASS

- **timestamp**: 2026-09-16T19:09:05.236Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/inventory
- **expected**: Page fully renders its expected content
- **observed**: instance_polymorphic_identity\", \"instance_prefix\", \"is_deleted\", \"is_singleton\", \"issuer_app_code\", \"json_addl\", \"json_addl_schema\", \"modified_dt\", \"name\", \"polymorphic_discriminator\", \"subtype\", \"tenant_id\", \"type\", \"uid\", \"validator_ref\", \"version\" ], \"inbox_message\": [ \"domain_code\", \"error_code\", \"error_message\", \"issuer_app_code\", \"json_addl\", \"message_machine_uuid\", \"payload\", \"processed_dt\", \"receipt_machine_uuid\", \"received_dt\", \"source_destination\", \"source_domain_code\", \"source_issuer_app_code\", \"status\", \"tenant_id\", \"uid\" ], \"outbox_event\": [ \"attempt_count\", \"canceled_dt\", \"claim_token\", \"claimed_by\", \"claimed_dt\", \"created_dt\", \"dead_letter_dt\", \"dedupe_key\", \"destination\", \"domain_code\", \"id\", \"issuer_app_code\", \"last_attempt_dt\", \"last_error\", \"last_http_status\", \"last_response_body_excerpt\", \"last_response_headers\", \"lease_expires_dt\", \"message_uid\", \"next_attempt_at\", \"receipt_machine_uuid\", \"receipt_processed_dt\", \"receipt_received_dt\", \"receipt_status\", \"rejected_dt\", \"status\", \"tenant_id\" ], \"outbox_event_attempt\": [ \"attempt_finished_dt\", \"attempt_no\", \"attempt_started_dt\", \"claim_token\", \"domain_code\", \"http_status\", \"issuer_app_code\", \"json_addl\", \"outbox_event_id\", \"receipt_machine_uuid\", \"receipt_processed_dt\", \"receipt_received_dt\", \"receipt_status\", \"response_body_excerpt\", \"response_headers\", \"retry_scheduled_dt\", \"tenant_id\", \"transport_error\", \"transport_status\", \"uid\", \"worker_id\" ], \"tapdb_identity_prefix_config\": [ \"domain_code\", \"entity\", \"issuer_app_code\", \"prefix\", \"updated_dt\" ], \"tapdb_legacy_outbox_mapping\": [ \"mapped_dt\", \"message_euid\", \"message_euid_seq\", \"message_uid\", \"old_event_id\", \"old_outbox_id\", \"source_sha256\" ], \"tapdb_runtime_principal_scope\": [] }"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-INVENTORY-1789585745236.txt ; I1-A-TAP-INVENTORY-1789585745236.png

### TAP-MERIDIAN I1-A — PASS

- **timestamp**: 2026-09-16T19:09:05.684Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian
- **expected**: Page fully renders its expected content
- **observed**:  - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Meridian" [level=1]<br>  - table:<br>    - rowgroup:<br>      - row "Domain M":<br>        - rowheader "Domain"<br>        - cell "M"<br>      - row "Owner Repo dewey":<br>        - rowheader "Owner Repo"<br>        - cell "dewey"<br>      - row "Domain Registry /opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json":<br>        - rowheader "Domain Registry"<br>        - cell "/opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json"<br>      - row "Prefix Registry /opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json":<br>        - rowheader "Prefix Registry"<br>        - cell "/opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json"<br>      - row "Public Registry https://github.com/lsmc-bio/meridian-registry":<br>        - rowheader "Public Registry"<br>        - cell "https://github.com/lsmc-bio/meridian-registry"<br>      - row "Public Registry Version 0.1.1":<br>        - rowheader "Public Registry Version"<br>        - cell "0.1.1"<br>  - textbox "EUID"<br>  - textbox "prefix"<br>  - button "Validate"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-MERIDIAN-1789585745684.txt ; I1-A-TAP-MERIDIAN-1789585745684.png

### TAP-METRICS I1-A — PASS

- **timestamp**: 2026-09-16T19:09:06.060Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/metrics
- **expected**: Page fully renders its expected content
- **observed**:  - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "DB Metrics" [level=1]<br>  - table:<br>    - rowgroup:<br>      - row "Enabled True":<br>        - rowheader "Enabled"<br>        - cell "True"<br>      - row "File /run/dewey-production-state/state/tapdb/dewey/dewey-day/runtime/metrics/db_metrics_20260907.tsv":<br>        - rowheader "File"<br>        - cell "/run/dewey-production-state/state/tapdb/dewey/dewey-day/runtime/metrics/db_metrics_20260907.tsv"<br>      - row "Dropped 0":<br>        - rowheader "Dropped"<br>        - cell "0"<br>  - table:<br>    - rowgroup:<br>      - row "Path Method Count Total Seconds":<br>        - columnheader "Path"<br>        - columnheader "Method"<br>        - columnheader "Count"<br>        - columnheader "Total Seconds"<br>    - rowgroup:<br>      - row "4025":<br>        - cell<br>        - cell<br>        - cell "4025"<br>        - cell<br>      - row "/tapdb/ 22":<br>        - cell /tapdb/<br>        - cell<br>        - cell "22"<br>        - cell<br>      - row "/tapdb/audit 10":<br>        - cell "/tapdb/audit"<br>        - cell<br>        - cell "10"<br>        - cell<br>      - row "/tapdb/search 11":<br>        - cell "/tapdb/search"<br>        - cell<br>        - cell "11"<br>        - cell<br>      - row "/tapdb/admin/inventory 21":<br>        - cell "/tapdb/admin/inventory"<br>        - cell<br>        - cell "21"<br>        - cell<br>      - row "/tapdb/templates 10":<br>        - cell "/tapdb/templates"<br>        - cell<br>        - cell "10"<br>        - cell<br>      - row "/tapdb/api/dag/v2/object/M-DGX-9SZ2 24":<br>        - cell "/tapdb/api/dag/v2/object/M-DGX-9SZ2"<br>        - cell<br>        - cell "24"<br>        - cell<br>      - row "/tapdb/graph 576":<br>        - cell "/tapdb/graph"<br>        - cell<br>        - cell "576"<br>        - cell<br>      - row "/tapdb/api/graph 302":<br>        - cell "/tapdb/api/graph"<br>        - cell<br>        - cell "302"<br>        - cell<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-METRICS-1789585746060.txt ; I1-A-TAP-METRICS-1789585746060.png

### TAP-RUNTIME I1-A — PASS

- **timestamp**: 2026-09-16T19:09:06.551Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/runtime
- **expected**: Page fully renders its expected content
- **observed**: ics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Sanitized Runtime Information" [level=1]<br>  - paragraph: This is the same payload exposed by the CLI and authenticated API.<br>  - heading "package" [level=2]<br>  - generic: "{ \"name\": \"daylily-tapdb\", \"version\": \"10.1.1rc1\" }"<br>  - heading "python" [level=2]<br>  - generic: "{ \"implementation\": \"cpython\", \"version\": \"3.12.14\" }"<br>  - heading "meridian" [level=2]<br>  - generic: "{ \"package\": \"meridian-euid\", \"version\": \"0.4.8\" }"<br>  - heading "git" [level=2]<br>  - generic: "{ \"branch\": null, \"commit\": null, \"dirty\": null, \"tag\": null }"<br>  - heading "config" [level=2]<br>  - generic: "{ \"config_version\": 4, \"exists\": true, \"path\": \"/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml\", \"sha256\": \"987b25f1659a1e72593bd4231307b1f7f6c7122d5cb20193c3681ba41a2fe353\", \"target\": \"explicit\" }"<br>  - heading "database" [level=2]<br>  - generic: "{ \"database\": \"dewey_prod_tapdb10\", \"engine_type\": \"aurora\", \"host\": \"dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com\", \"port\": \"5432\", \"schema_name\": \"tapdb_dewey_lsmcok1_local\", \"server_version\": \"psql exit 2\", \"status\": \"error\" }"<br>  - heading "scope" [level=2]<br>  - generic: "{ \"client_id\": \"dewey\", \"database_name\": \"dewey-day\", \"domain_code\": \"M\", \"owner_repo_name\": \"dewey\" }"<br>  - heading "storage" [level=2]<br>  - generic: "{ \"aws_profile\": \"lsmc\", \"region\": \"us-west-2\", \"s3_buckets\": [], \"uris\": [] }"<br>  - heading "ui" [level=2]<br>  - generic: "{ \"pid\": null, \"port\": \"8910\", \"running\": false, \"status\": \"stopped\" }"<br>  - heading "dag" [level=2]<br>  - generic: "{ \"eligible\": false, \"service_id\": null, \"status\": \"not_configured\" }"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-RUNTIME-1789585746551.txt ; I1-A-TAP-RUNTIME-1789585746551.png

### TAP-BACKUPS I1-A — PASS

- **timestamp**: 2026-09-16T19:09:06.975Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/backups
- **expected**: Page fully renders its expected content
- **observed**: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Backups" [level=1]<br>  - paragraph:<br>    - strong: "Target:"<br>    - text: dewey/dewey-day/tapdb_dewey_lsmcok1_local@dewey_prod_tapdb10<br>  - strong: "Status: never_run"<br>  - text: No successful backup has ever been recorded for this target.<br>  - paragraph:<br>    - text: No cadence is configured, so this target is never reported as stale. Set<br>    - code: backup.expected_interval_hours<br>    - text: to enable staleness reporting.<br>  - heading "Create a backup" [level=2]<br>  - paragraph: Reads the database only; nothing is modified.<br>  - text: Class<br>  - combobox "Class":<br>    - option "full (logical dump)" [selected]<br>    - option "template-pack (definitions only)"<br>  - text: Note<br>  - textbox "Note":<br>    - /placeholder: optional<br>  - checkbox "Acknowledge measured schema drift (requires a verified source contract)"<br>  - text: Acknowledge measured schema drift (requires a verified source contract)<br>  - text: Reviewed source-contract JSON (required for historical or drifted schemas)<br>  - textbox "Reviewed source-contract JSON (required for historical or drifted schemas)"<br>  - text: Sealed recovery-family JSON (for recovery across replacements)<br>  - textbox "Sealed recovery-family JSON (for recovery across replacements)"<br>  - paragraph: A database backup does not include service configuration, runtime files, credentials or principal artifacts.<br>  - button "Create backup"<br>  - heading "Backups (0)" [level=2]<br>  - paragraph: "Storage: file:///opt/dewey/day/releases/9.0.0/backups"<br>  - paragraph: No backups have been taken for this target.<br>  - heading "Recent activity" [level=2]<br>  - paragraph: No lifecycle operations have been recorded.<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-BACKUPS-1789585746975.txt ; I1-A-TAP-BACKUPS-1789585746975.png

### STORE-BUCKETS I1-A — PASS

- **timestamp**: 2026-09-16T19:09:21.924Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage
- **expected**: Page fully renders its expected content
- **observed**: l "terrarium-dev-media":<br>          - link "terrarium-dev-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-dev-web us-west-2":<br>        - cell "terrarium-dev-web":<br>          - link "terrarium-dev-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-media us-west-2":<br>        - cell "terrarium-prod-media":<br>          - link "terrarium-prod-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-web us-west-2":<br>        - cell "terrarium-prod-web":<br>          - link "terrarium-prod-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-dev us-west-2":<br>        - cell "terrarium-tfstate-dev":<br>          - link "terrarium-tfstate-dev":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-prod us-west-2":<br>        - cell "terrarium-tfstate-prod":<br>          - link "terrarium-tfstate-prod":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>        - cell "us-west-2"<br>      - row "ursa-us-west-2-052779-default-customer-1d8c14 us-west-2":<br>        - cell "ursa-us-west-2-052779-default-customer-1d8c14":<br>          - link "ursa-us-west-2-052779-default-customer-1d8c14":<br>            - /url: /storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F<br>        - cell "us-west-2"<br>      - row "zebra-day-cfg-us-west-2 us-west-2":<br>        - cell "zebra-day-cfg-us-west-2":<br>          - link "zebra-day-cfg-us-west-2":<br>            - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>        - cell "us-west-2"<br>  - heading "Registered locations" [level=2]<br>  - paragraph: Includes explicitly registered external buckets and shared folders.<br>  - paragraph: No registered locations available.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-STORE-BUCKETS-1789585761924.txt ; I1-A-STORE-BUCKETS-1789585761924.png

### STORE-BUCKET-LINKS I1-A — PASS

- **timestamp**: 2026-09-16T19:10:39.466Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2F
- **expected**: Clicking bucket opens its bounded listing
- **observed**: lsmc-dewey-0 root loaded five prefixes; broader bucket-link coverage remains in progress.
- **evidence**: I1-A-STORE-BUCKET-LINKS-1789585839466.txt

### STORE-URI I1-A — PASS

- **timestamp**: 2026-09-16T19:10:51.810Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Go preserves the exact entered S3 prefix
- **observed**: Navigated to designated I1-A prefix with exact key components.
- **evidence**: I1-A-STORE-URI-1789585851810.txt

### STORE-EMPTY I1-A — PASS

- **timestamp**: 2026-09-16T19:10:51.830Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Empty prefix renders a useful empty state
- **observed**: No matching items shown; upload and registration actions available.
- **evidence**: I1-A-STORE-EMPTY-1789585851830.txt

### STORE-UPLOAD I1-A — PASS

- **timestamp**: 2026-09-16T19:14:51.059Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Four new synthetic files upload and register
- **observed**: Upload status reports 4 files uploaded and registered; byte sizes and persisted EUID links present.
- **evidence**: I1-A-STORE-UPLOAD-1789586091059.txt ; I1-A-STORE-UPLOAD-1789586091059.png

### STORE-OBJECT I1-A — PASS

- **timestamp**: 2026-09-16T19:15:20.408Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Object details show exact synthetic key, size and registration
- **observed**: Details display 80 bytes, text/plain, persisted EUID M-DGX-TQ2W
- **evidence**: I1-A-STORE-OBJECT-1789586120408.txt ; I1-A-STORE-OBJECT-1789586120408.png

### STORE-REPLACE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:15:20.621Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Replacement interface inspected without submission
- **observed**: Replace button present; execution excluded by no-replacement rule.
- **evidence**: I1-A-STORE-REPLACE-1789586120621.txt

### STORE-DELETE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:15:20.720Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Delete interface inspected without submission
- **observed**: Object Delete and folder Delete controls present; execution excluded.
- **evidence**: I1-A-STORE-DELETE-1789586120720.txt

### STORE-DOWNLOAD I1-A — FAIL

- **timestamp**: 2026-09-16T19:15:51.786Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Browser completes download and SHA256 matches uploaded fixture
- **observed**: Synthetic 80-byte text object Download returns HTTP 500; no delivery. BUG D02.
- **evidence**: I1-A-STORE-DOWNLOAD-1789586151786.txt ; I1-A-STORE-DOWNLOAD-1789586151786.png

### STORE-UPLOAD-MULTIPART I1-A — PASS

- **timestamp**: 2026-09-16T19:16:16.202Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: 17MiB multipart upload completes without replacing an existing object
- **observed**: Status reports uploaded and registered; M-DGX-TQKS displayed at 17.8M B.
- **evidence**: I1-A-STORE-UPLOAD-MULTIPART-1789586176202.txt ; I1-A-STORE-UPLOAD-MULTIPART-1789586176202.png

### STORE-FILTER I1-A — PASS

- **timestamp**: 2026-09-16T19:16:25.305Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Name filter narrows current page
- **observed**: Filter fixture leaves only fixture.json.
- **evidence**: I1-A-STORE-FILTER-1789586185305.txt

### STORE-FILTER I1-A — FAIL

- **timestamp**: 2026-09-16T19:17:05.525Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Clearing the name filter restores all current-page objects
- **observed**: Filter fixture narrows correctly, but filling empty immediately restores fixture and keeps other rows hidden. BUG D03.
- **evidence**: I1-A-STORE-FILTER-1789586225525.txt ; I1-A-STORE-FILTER-1789586225525.png

### STORE-SET I1-A — PASS

- **timestamp**: 2026-09-16T19:17:28.381Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Selected storage objects produce a retained set
- **observed**: Created M-DGX-TQRF with two selected members.
- **evidence**: I1-A-STORE-SET-1789586248381.txt ; I1-A-STORE-SET-1789586248381.png

### RECORD-SET I1-A — PASS

- **timestamp**: 2026-09-16T19:17:28.485Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Set details and member links render
- **observed**: Two visible members fixture.json and index.html with correct EUIDs.
- **evidence**: I1-A-RECORD-SET-1789586248485.txt

### RECORD-MEMBER-REMOVE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:17:28.493Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Removal controls inspected without activation
- **observed**: Remove buttons present; excluded by retained-data boundary.
- **evidence**: I1-A-RECORD-MEMBER-REMOVE-1789586248493.txt

### RECORD-MEMBER-ADD I1-A — PASS

- **timestamp**: 2026-09-16T19:17:38.089Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Add existing synthetic object to set without removing others
- **observed**: M-DGX-TQ2W added; member count increased 2 to 3.
- **evidence**: I1-A-RECORD-MEMBER-ADD-1789586258089.txt

### RECORD-EDIT I1-A — PASS

- **timestamp**: 2026-09-16T19:17:55.334Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Add description and nested metadata to synthetic set
- **observed**: Saved new description and gui_audit metadata while retaining name/members.
- **evidence**: I1-A-RECORD-EDIT-1789586275334.txt ; I1-A-RECORD-EDIT-1789586275334.png

### RECORD-PERMISSIONS I1-A — PASS

- **timestamp**: 2026-09-16T19:18:31.620Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Add approved alias while preserving existing audiences
- **observed**: Reloaded fixture set retains alias in metadata/download emails and delegated sharers, audiences remain internal.
- **evidence**: I1-A-RECORD-PERMISSIONS-1789586311620.txt

### RECORD-OWNER I1-A — PASS

- **timestamp**: 2026-09-16T19:19:30.468Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Fixture ownership changes only to approved alias with existing grants retained
- **observed**: M-DGX-TQRF owner now johnm+dewey-gui-20260916-i1a@lsmc.com; accessible after return navigation.
- **evidence**: I1-A-RECORD-OWNER-1789586370468.txt

### RECORD-ACTIVITY I1-A — PASS

- **timestamp**: 2026-09-16T19:19:43.811Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Recent activity shows persisted metadata, permissions and ownership operations
- **observed**: Three complete activity receipts displayed with issued EUIDs/timestamps.
- **evidence**: I1-A-RECORD-ACTIVITY-1789586383811.txt

### RECORD-ARCHIVE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:19:43.821Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Inspect archive control without revocation or removal
- **observed**: Archive registration button and access/share effects displayed; never submitted.
- **evidence**: I1-A-RECORD-ARCHIVE-1789586383821.txt

### RECORD-MANIFEST I1-A — FAIL

- **timestamp**: 2026-09-16T19:20:06.236Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Access manifest can be generated and browser-delivered
- **observed**: Set Access manifest returns HTTP500; no delivered manifest. BUG D02 pending root-cause grouping.
- **evidence**: I1-A-RECORD-MANIFEST-1789586406236.txt ; I1-A-RECORD-MANIFEST-1789586406236.png

### SHARE-CREATE I1-A — PASS

- **timestamp**: 2026-09-16T19:21:09.251Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Create retained share for approved alias only
- **observed**: M-DGX-TQZ1 active, recipients-only, one-day expiry, synthetic set target.
- **evidence**: I1-A-SHARE-CREATE-1789586469251.txt ; I1-A-SHARE-CREATE-1789586469251.png

### SHARE-DETAIL I1-A — PASS

- **timestamp**: 2026-09-16T19:21:09.294Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Share policy, identity, target and activity display
- **observed**: Correct owner, recipient, expiry, current empty activity and target link displayed.
- **evidence**: I1-A-SHARE-DETAIL-1789586469294.txt

### SHARE-REVOKE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:21:09.298Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Inspect revocation without action
- **observed**: Revoke share control visible; execution excluded.
- **evidence**: I1-A-SHARE-REVOKE-1789586469298.txt

### SHARE-COPY I1-A — PASS

- **timestamp**: 2026-09-16T19:21:09.560Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Copy button puts exact fixture share URL on clipboard
- **observed**: Clipboard equals https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **evidence**: I1-A-SHARE-COPY-1789586469560.txt

### SHARE-EDIT I1-A — PASS

- **timestamp**: 2026-09-16T19:21:24.155Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Add second approved recipient while retaining first and existing policy
- **observed**: Both approved I1 aliases displayed after save.
- **evidence**: I1-A-SHARE-EDIT-1789586484155.txt

### SHARE-INVITE I1-A — REVIEW

- **timestamp**: 2026-09-16T19:22:10.380Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **expected**: Approved account receives login invitation
- **observed**: GUI reports accepted by shared login, operation M-DGX-TR1X; email delivery verification pending.
- **evidence**: I1-A-SHARE-INVITE-1789586530380.txt

### SHARE-OPEN I1-A — PASS

- **timestamp**: 2026-09-16T19:22:11.143Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQRF
- **expected**: Share target link opens exact retained set
- **observed**: Open shared set links to M-DGX-TQRF and renders three member links.
- **evidence**: I1-A-SHARE-OPEN-1789586531143.txt

### RECORD-OBJECT I1-A — PASS

- **timestamp**: 2026-09-16T19:22:38.587Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQ2W
- **expected**: Registered object page renders identity and storage location
- **observed**: M-DGX-TQ2W renders owner, producer and exact Unicode URI; object size/content type absent from registration metadata.
- **evidence**: I1-A-RECORD-OBJECT-1789586558587.txt

### RECORD-DOWNLOAD I1-A — FAIL

- **timestamp**: 2026-09-16T19:22:47.176Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQ2W
- **expected**: Registered object delivers fixture bytes
- **observed**: Download / open returns HTTP500; no delivered file. BUG D02.
- **evidence**: I1-A-RECORD-DOWNLOAD-1789586567176.txt ; I1-A-RECORD-DOWNLOAD-1789586567176.png

### ADD-PREFIX I1-A — PASS

- **timestamp**: 2026-09-16T19:23:15.368Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TR3S
- **expected**: Register a single exact prefix without recursive registration
- **observed**: Created M-DGX-TR3S for designated I1-A prefix.
- **evidence**: I1-A-ADD-PREFIX-1789586595368.txt ; I1-A-ADD-PREFIX-1789586595368.png

### STORE-REGISTER I1-A — PASS

- **timestamp**: 2026-09-16T19:23:15.420Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TR3S
- **expected**: Storage Register this folder prepopulates and registers the exact URI
- **observed**: S3 browser link opened /add?kind=prefix&uri=... and created M-DGX-TR3S.
- **evidence**: I1-A-STORE-REGISTER-1789586595420.txt

### RECORD-PREFIX I1-A — PASS

- **timestamp**: 2026-09-16T19:24:18.408Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TR3S
- **expected**: Prefix details show bounded current contents and record links
- **observed**: Five synthetic objects with exact names/sizes and registered EUID links displayed.
- **evidence**: I1-A-RECORD-PREFIX-1789586658408.txt ; I1-A-RECORD-PREFIX-1789586658408.png

### RECORD-PREVIEW I1-A — PASS

- **timestamp**: 2026-09-16T19:24:31.053Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQAC
- **expected**: Isolated HTML renders fixture and relative SVG asset
- **observed**: Iframe shows Dewey GUI audit preview, retained-fixture paragraph and blue audit square.
- **evidence**: I1-A-RECORD-PREVIEW-1789586671053.txt ; I1-A-RECORD-PREVIEW-1789586671053.png

### ADD-VALIDATION I1-A — PASS

- **timestamp**: 2026-09-16T19:24:54.728Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **expected**: Empty registration rejected with readable error
- **observed**: Empty form rejected: HTTP(S) object URL without embedded credentials required.
- **evidence**: I1-A-ADD-VALIDATION-1789586694728.txt

### ADD-OBJECT I1-A — PASS

- **timestamp**: 2026-09-16T19:24:55.635Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQ2W
- **expected**: Exact S3 object registration resolves one stable identity
- **observed**: Existing uploaded key resolves M-DGX-TQ2W with original URI unchanged.
- **evidence**: I1-A-ADD-OBJECT-1789586695635.txt

### ADD-DUPLICATE I1-A — PASS

- **timestamp**: 2026-09-16T19:24:55.640Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQ2W
- **expected**: Repeated location registration reuses identity
- **observed**: Manual re-registration returned existing M-DGX-TQ2W without changing stored bytes.
- **evidence**: I1-A-ADD-DUPLICATE-1789586695640.txt

### ADD-URL I1-A — PASS

- **timestamp**: 2026-09-16T19:25:11.032Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TR8F
- **expected**: Register HTTP(S) reference as object
- **observed**: Created retained HTTPS example.com reference.
- **evidence**: I1-A-ADD-URL-1789586711032.txt

### ADD-METADATA I1-A — PASS

- **timestamp**: 2026-09-16T19:25:11.037Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TR8F
- **expected**: Metadata field editor applies JSON and persists
- **observed**: audit_attempt I1-A appears in persisted metadata.
- **evidence**: I1-A-ADD-METADATA-1789586711037.txt ; I1-A-ADD-METADATA-1789586711037.png

### ADD-UPLOAD-MODE I1-A — FAIL

- **timestamp**: 2026-09-16T19:25:41.955Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **expected**: Add upload modal exposes independently labelled destination
- **observed**: Selecting Upload opens form but Destination S3 folder label is bound to background URI input; dialog destination textbox is unnamed. BUG D04.
- **evidence**: I1-A-ADD-UPLOAD-MODE-1789586741955.txt ; I1-A-ADD-UPLOAD-MODE-1789586741955.png

### ADD-UPLOAD-EXEC I1-A — PASS

- **timestamp**: 2026-09-16T19:26:18.452Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **expected**: Upload from Add completes to new nested key with registration unchecked
- **observed**: Status 1 file uploaded; retained s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/nested/fixture.json.
- **evidence**: I1-A-ADD-UPLOAD-EXEC-1789586778452.txt

### LIB-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:26:33.842Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=20260916&sort=created_at&page=1
- **expected**: Search finds matching synthetic names and locations
- **observed**: Query 20260916 returns eight audit records.
- **evidence**: I1-A-LIB-SEARCH-1789586793842.txt

### LIB-KIND I1-A — PASS

- **timestamp**: 2026-09-16T19:26:36.889Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=20260916&sort=created_at&page=1&kind=prefix
- **expected**: Kind prefix restricts results
- **observed**: Query 20260916 plus Prefixes returns only M-DGX-TR3S.
- **evidence**: I1-A-LIB-KIND-1789586796889.txt

### LIB-SORT I1-A — PASS

- **timestamp**: 2026-09-16T19:26:57.541Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=20260916&sort=name&page=1
- **expected**: Name sort produces alphabetical records
- **observed**: Name order starts asset.svg, audit prefix/set/URL, fixture.json, hello, index, multipart.
- **evidence**: I1-A-LIB-SORT-1789586817541.txt

### LIB-SELECT I1-A — PASS

- **timestamp**: 2026-09-16T19:26:58.658Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add?kind=set&members=M-DGX-TR3S%0AM-DGX-TR8F
- **expected**: Selected prefix and object carry into set form
- **observed**: Form prepopulates M-DGX-TR3S and M-DGX-TR8F.
- **evidence**: I1-A-LIB-SELECT-1789586818658.txt

### SET-CREATE-SELECTION I1-A — PASS

- **timestamp**: 2026-09-16T19:26:59.289Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRC7
- **expected**: Selected existing records form an explicit set
- **observed**: Created library set with prefix and URL members.
- **evidence**: I1-A-SET-CREATE-SELECTION-1789586819289.txt

### ADD-SET I1-A — PASS

- **timestamp**: 2026-09-16T19:26:59.296Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRC7
- **expected**: Set registration preserves selected identities
- **observed**: Two members persisted through Add set form.
- **evidence**: I1-A-ADD-SET-1789586819296.txt ; I1-A-ADD-SET-1789586819296.png

### LIB-LOOKUP I1-A — PASS

- **timestamp**: 2026-09-16T19:27:13.673Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TQ2W
- **expected**: EUID lookup opens correct stored record
- **observed**: M-DGX-TQ2W opens Unicode fixture object.
- **evidence**: I1-A-LIB-LOOKUP-1789586833673.txt

### LIB-EMPTY I1-A — PASS

- **timestamp**: 2026-09-16T19:27:17.467Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=dewey-no-such-audit-result-20260916&sort=created_at&page=1
- **expected**: Nonmatching search produces explicit empty result
- **observed**: Unique nonmatching query displays zero accessible records.
- **evidence**: I1-A-LIB-EMPTY-1789586837467.txt

### LIB-BACK I1-A — PASS

- **timestamp**: 2026-09-16T19:27:50.586Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=dewey-no-such-audit-result-20260916&sort=created_at&page=1
- **expected**: Browser back/forward restores prior search state
- **observed**: Back restored library page1; forward restored nonmatching query and zero records.
- **evidence**: I1-A-LIB-BACK-1789586870586.txt

### LIB-PAGE-NEXT I1-A — PASS

- **timestamp**: 2026-09-16T19:27:54.600Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=2
- **expected**: Pagination advances to second page
- **observed**: Page2 renders new rows and Previous/Next controls.
- **evidence**: I1-A-LIB-PAGE-NEXT-1789586874600.txt

### LIB-FILTERS-INVALID I1-A — PASS

- **timestamp**: 2026-09-16T19:28:18.198Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=2
- **expected**: Non-array filters are rejected visibly
- **observed**: {} produces Filters must be a JSON array.
- **evidence**: I1-A-LIB-FILTERS-INVALID-1789586898198.txt

### LIB-FILTERS I1-A — PASS

- **timestamp**: 2026-09-16T19:28:21.267Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=1&filters=%5B%7B%22path%22%3A%22metadata.audit_attempt%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22I1-A%22%7D%5D
- **expected**: Valid JSON metadata filter returns matching fixture
- **observed**: metadata.audit_attempt eq I1-A returns URL record.
- **evidence**: I1-A-LIB-FILTERS-1789586901267.txt

### SET-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:28:39.412Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets?q=20260916+I1-A&sort=name&page=1
- **expected**: Sets search and name sort return fixture sets
- **observed**: Search 20260916 I1-A returns library set then storage set, with member counts2 and3.
- **evidence**: I1-A-SET-SEARCH-1789586919412.txt

### SET-PAGINATION I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:28:39.423Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets?q=20260916+I1-A&sort=name&page=1
- **expected**: Exercise next-page control where >25 sets exist
- **observed**: Current set result count below page size; no Next control available. No excess fixtures manufactured for pagination.
- **evidence**: I1-A-SET-PAGINATION-1789586919423.txt

### SHARE-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:28:43.089Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?q=20260916+I1-A&sort=name&page=1
- **expected**: Shares search and name sorting resolve retained fixture
- **observed**: Query 20260916 I1-A yields M-DGX-TQZ1 active share.
- **evidence**: I1-A-SHARE-SEARCH-1789586923089.txt

### STORE-FILTER I1-A — PASS

- **timestamp**: 2026-09-16T19:29:43.722Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F
- **expected**: Filter narrows and keyboard clearing restores all rows
- **observed**: Keyboard Select All / Backspace restores all six entries. Earlier fill-empty result was automation behavior, not substantiated Dewey defect; D03 withdrawn, original evidence retained.
- **evidence**: I1-A-STORE-FILTER-1789586983722.txt ; I1-A-STORE-FILTER-1789586983722.png

### STORE-BREADCRUMBS I1-A — PASS

- **timestamp**: 2026-09-16T19:29:44.446Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2Fnested%2F
- **expected**: Nested folder navigation preserves exact path and breadcrumbs
- **observed**: nested/ displays one unregistered fixture.json and breadcrumb back to I1-A.
- **evidence**: I1-A-STORE-BREADCRUMBS-1789586984446.txt

### STORE-ERROR I1-A — PASS

- **timestamp**: 2026-09-16T19:30:12.035Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=https%3A%2F%2Fexample.com%2F
- **expected**: Invalid non-S3 URI yields explicit error
- **observed**: https://example.com/ rejected: An explicit s3:// URI is required.
- **evidence**: I1-A-STORE-ERROR-1789587012035.txt

### LIT-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:30:30.388Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=genomics&page=1
- **expected**: PubMed search leaves loading state and displays paper metadata
- **observed**: Query genomics returned twenty rows with PMID/title/authors and registration controls after loading.
- **evidence**: I1-A-LIT-SEARCH-1789587030388.txt ; I1-A-LIT-SEARCH-1789587030388.png

### BUCKET-aquarium-tfstate-dev I1-A — PASS

- **timestamp**: 2026-09-16T19:30:44.064Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://aquarium-tfstate-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://aquarium-tfstate-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Faquarium-tfstate-dev%2F<br>  - link "aquarium-tfstate-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select aquarium/ prefix aquarium/ — Register":<br>        - cell "Select aquarium/ prefix":<br>          - checkbox "Select aquarium/"<br>          - generic: prefix<br>        - cell "aquarium/":<br>          - link "aquarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2Faquarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faquarium-tfstate-dev%2Faquarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-aquarium-tfstate-dev-1789587044064.txt ; I1-A-BUCKET-aquarium-tfstate-dev-1789587044064.png

### BUCKET-aquarium-tfstate-prod I1-A — PASS

- **timestamp**: 2026-09-16T19:30:44.575Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://aquarium-tfstate-prod/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://aquarium-tfstate-prod/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Faquarium-tfstate-prod%2F<br>  - link "aquarium-tfstate-prod":<br>    - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select aquarium/ prefix aquarium/ — Register":<br>        - cell "Select aquarium/ prefix":<br>          - checkbox "Select aquarium/"<br>          - generic: prefix<br>        - cell "aquarium/":<br>          - link "aquarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2Faquarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faquarium-tfstate-prod%2Faquarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-aquarium-tfstate-prod-1789587044575.txt ; I1-A-BUCKET-aquarium-tfstate-prod-1789587044575.png

### BUCKET-asterism-note-screenshots-dev I1-A — PASS

- **timestamp**: 2026-09-16T19:30:45.205Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://asterism-note-screenshots-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://asterism-note-screenshots-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F<br>  - link "asterism-note-screenshots-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select screenshots/ prefix screenshots/ — Register":<br>        - cell "Select screenshots/ prefix":<br>          - checkbox "Select screenshots/"<br>          - generic: prefix<br>        - cell "screenshots/":<br>          - link "screenshots/":<br>            - /url: /storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2Fscreenshots%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2Fscreenshots%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-asterism-note-screenshots-dev-1789587045205.txt ; I1-A-BUCKET-asterism-note-screenshots-dev-1789587045205.png

### BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd I1-A — PASS

- **timestamp**: 2026-09-16T19:30:46.139Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F
- **expected**: Page fully renders its expected content
- **observed**: d?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F7dd32744d3ef9196115bcc7ae8c1f3b8&kind=object<br>      - row "Select 8efd1317cee2fadc175612785c606a45 object 8efd1317cee2fadc175612785c606a45 1.5K B Register":<br>        - cell "Select 8efd1317cee2fadc175612785c606a45 object":<br>          - checkbox "Select 8efd1317cee2fadc175612785c606a45"<br>          - generic: object<br>        - cell "8efd1317cee2fadc175612785c606a45":<br>          - button "8efd1317cee2fadc175612785c606a45"<br>        - cell "1.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F8efd1317cee2fadc175612785c606a45&kind=object<br>      - row "Select bd9b5df9ed21415aabf9be3dd0bf872b object bd9b5df9ed21415aabf9be3dd0bf872b 30.7M B Register":<br>        - cell "Select bd9b5df9ed21415aabf9be3dd0bf872b object":<br>          - checkbox "Select bd9b5df9ed21415aabf9be3dd0bf872b"<br>          - generic: object<br>        - cell "bd9b5df9ed21415aabf9be3dd0bf872b":<br>          - button "bd9b5df9ed21415aabf9be3dd0bf872b"<br>        - cell "30.7M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2Fbd9b5df9ed21415aabf9be3dd0bf872b&kind=object<br>      - row "Select ed4f1d6620c05cf7bde78318883cf39a.template object ed4f1d6620c05cf7bde78318883cf39a.template 70.4K B Register":<br>        - cell "Select ed4f1d6620c05cf7bde78318883cf39a.template object":<br>          - checkbox "Select ed4f1d6620c05cf7bde78318883cf39a.template"<br>          - generic: object<br>        - cell "ed4f1d6620c05cf7bde78318883cf39a.template":<br>          - button "ed4f1d6620c05cf7bde78318883cf39a.template"<br>        - cell "70.4K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2Fed4f1d6620c05cf7bde78318883cf39a.template&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd-1789587046139.txt ; I1-A-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd-1789587046139.png

### BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp I1-A — PASS

- **timestamp**: 2026-09-16T19:30:47.127Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F
- **expected**: Page fully renders its expected content
- **observed**: l: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F5729682a35864d86a61ef536f2202235&kind=object<br>      - row "Select 6cee33cb01dfea2f15c39b110ea0f258 object 6cee33cb01dfea2f15c39b110ea0f258 2.6M B Register":<br>        - cell "Select 6cee33cb01dfea2f15c39b110ea0f258 object":<br>          - checkbox "Select 6cee33cb01dfea2f15c39b110ea0f258"<br>          - generic: object<br>        - cell "6cee33cb01dfea2f15c39b110ea0f258":<br>          - button "6cee33cb01dfea2f15c39b110ea0f258"<br>        - cell "2.6M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F6cee33cb01dfea2f15c39b110ea0f258&kind=object<br>      - row "Select 8eddd4fe4211c82df0dba27b419f973c.template object 8eddd4fe4211c82df0dba27b419f973c.template 43K B Register":<br>        - cell "Select 8eddd4fe4211c82df0dba27b419f973c.template object":<br>          - checkbox "Select 8eddd4fe4211c82df0dba27b419f973c.template"<br>          - generic: object<br>        - cell "8eddd4fe4211c82df0dba27b419f973c.template":<br>          - button "8eddd4fe4211c82df0dba27b419f973c.template"<br>        - cell "43K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F8eddd4fe4211c82df0dba27b419f973c.template&kind=object<br>      - row "Select ef3a4230ce6d6095f06e66e48a3b1b6f object ef3a4230ce6d6095f06e66e48a3b1b6f 2.6M B Register":<br>        - cell "Select ef3a4230ce6d6095f06e66e48a3b1b6f object":<br>          - checkbox "Select ef3a4230ce6d6095f06e66e48a3b1b6f"<br>          - generic: object<br>        - cell "ef3a4230ce6d6095f06e66e48a3b1b6f":<br>          - button "ef3a4230ce6d6095f06e66e48a3b1b6f"<br>        - cell "2.6M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2Fef3a4230ce6d6095f06e66e48a3b1b6f&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp-1789587047127.txt ; I1-A-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp-1789587047127.png

### BUCKET-cdk-dayhoff-assets-108782052779-us-east-1 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:48.647Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: fa2fa56f26eae5115153110bb7e0539cf78ddb75aadc6d981f95d.json"<br>        - cell "7.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Feb51e3eb4bcfa2fa56f26eae5115153110bb7e0539cf78ddb75aadc6d981f95d.json&kind=object<br>      - row "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json object f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json 2.9K B Register":<br>        - cell "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json object":<br>          - checkbox "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json"<br>          - generic: object<br>        - cell "f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json":<br>          - button "f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json"<br>        - cell "2.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Ff13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json&kind=object<br>      - row "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json object f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json 23.7K B Register":<br>        - cell "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json object":<br>          - checkbox "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json"<br>          - generic: object<br>        - cell "f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json":<br>          - button "f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json"<br>        - cell "23.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Ff6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-cdk-dayhoff-assets-108782052779-us-east-1-1789587048647.txt ; I1-A-BUCKET-cdk-dayhoff-assets-108782052779-us-east-1-1789587048647.png

### BUCKET-cdk-dayhoff-assets-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:49.307Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://cdk-dayhoff-assets-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://cdk-dayhoff-assets-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F<br>  - link "cdk-dayhoff-assets-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-cdk-dayhoff-assets-108782052779-us-west-2-1789587049307.txt ; I1-A-BUCKET-cdk-dayhoff-assets-108782052779-us-west-2-1789587049307.png

### BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:52.213Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: 9db6825aa986634d739c186.json"<br>        - cell "20.2K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2cc067435f7a391f1040595805be77671d10c519d9db6825aa986634d739c186.json&kind=object<br>      - row "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json object 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json 91.7K B Register":<br>        - cell "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json object":<br>          - checkbox "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json"<br>          - generic: object<br>        - cell "2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json":<br>          - button "2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json"<br>        - cell "91.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json&kind=object<br>      - row "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml object 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml 1.5K B Register":<br>        - cell "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml object":<br>          - checkbox "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml"<br>          - generic: object<br>        - cell "2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml":<br>          - button "2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml"<br>        - cell "1.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1-1789587052213.txt ; I1-A-BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1-1789587052213.png

### BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:54.795Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: 036727c52f03c043c010c.json"<br>        - cell "28.6K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd225b67f6a0a086cf5077a68d81b7c2e099839700cf036727c52f03c043c010c.json&kind=object<br>      - row "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json object d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json 35.9K B Register":<br>        - cell "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json object":<br>          - checkbox "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json"<br>          - generic: object<br>        - cell "d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json":<br>          - button "d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json"<br>        - cell "35.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json&kind=object<br>      - row "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json object d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json 28.8K B Register":<br>        - cell "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json object":<br>          - checkbox "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json"<br>          - generic: object<br>        - cell "d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json":<br>          - button "d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json"<br>        - cell "28.8K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2-1789587054795.txt ; I1-A-BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2-1789587054795.png

### BUCKET-cf-templates-pfrobpqqun1c-us-east-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:55.618Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F
- **expected**: Page fully renders its expected content
- **observed**: F<br>  - link "cf-templates-pfrobpqqun1c-us-east-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json object 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json 840 B Register":<br>        - cell "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json object":<br>          - checkbox "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json"<br>          - generic: object<br>        - cell "2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json":<br>          - button "2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json"<br>        - cell "840 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json&kind=object<br>      - row "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json object 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json 840 B Register":<br>        - cell "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json object":<br>          - checkbox "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json"<br>          - generic: object<br>        - cell "2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json":<br>          - button "2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json"<br>        - cell "840 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-cf-templates-pfrobpqqun1c-us-east-2-1789587055618.txt ; I1-A-BUCKET-cf-templates-pfrobpqqun1c-us-east-2-1789587055618.png

### BUCKET-dayec-cur-108782052779-us-east-1 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:56.468Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: l=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://dayec-cur-108782052779-us-east-1/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://dayec-cur-108782052779-us-east-1/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F<br>  - link "dayec-cur-108782052779-us-east-1":<br>    - /url: /storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select dayec-cur/ prefix dayec-cur/ — Register":<br>        - cell "Select dayec-cur/ prefix":<br>          - checkbox "Select dayec-cur/"<br>          - generic: prefix<br>        - cell "dayec-cur/":<br>          - link "dayec-cur/":<br>            - /url: /storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Fdayec-cur%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Fdayec-cur%2F&kind=prefix<br>      - row "Select aws-programmatic-access-test-object object aws-programmatic-access-test-object 4 B Register":<br>        - cell "Select aws-programmatic-access-test-object object":<br>          - checkbox "Select aws-programmatic-access-test-object"<br>          - generic: object<br>        - cell "aws-programmatic-access-test-object":<br>          - button "aws-programmatic-access-test-object"<br>        - cell "4 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Faws-programmatic-access-test-object&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-dayec-cur-108782052779-us-east-1-1789587056468.txt ; I1-A-BUCKET-dayec-cur-108782052779-us-east-1-1789587056468.png

### BUCKET-daylily-customer-lsmc-a0477268 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:57.051Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://daylily-customer-lsmc-a0477268/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://daylily-customer-lsmc-a0477268/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F<br>  - link "daylily-customer-lsmc-a0477268":<br>    - /url: /storage?uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-daylily-customer-lsmc-a0477268-1789587057051.txt ; I1-A-BUCKET-daylily-customer-lsmc-a0477268-1789587057051.png

### BUCKET-lsmc-atlas-demo I1-A — PASS

- **timestamp**: 2026-09-16T19:30:57.681Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-atlas-demo/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-atlas-demo/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-atlas-demo%2F<br>  - link "lsmc-atlas-demo":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select external-smoke/ prefix external-smoke/ — Register":<br>        - cell "Select external-smoke/ prefix":<br>          - checkbox "Select external-smoke/"<br>          - generic: prefix<br>        - cell "external-smoke/":<br>          - link "external-smoke/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2Fexternal-smoke%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-demo%2Fexternal-smoke%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-atlas-demo-1789587057681.txt ; I1-A-BUCKET-lsmc-atlas-demo-1789587057681.png

### BUCKET-lsmc-atlas-dev I1-A — PASS

- **timestamp**: 2026-09-16T19:30:58.836Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: 5b3-ba7b-a905d5605702%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fcf27f697-ec98-45b3-ba7b-a905d5605702%2F&kind=prefix<br>      - row "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/ prefix d29e45ac-5741-43b8-91bc-2b8354c32a97/ — Register":<br>        - cell "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/ prefix":<br>          - checkbox "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/"<br>          - generic: prefix<br>        - cell "d29e45ac-5741-43b8-91bc-2b8354c32a97/":<br>          - link "d29e45ac-5741-43b8-91bc-2b8354c32a97/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fd29e45ac-5741-43b8-91bc-2b8354c32a97%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fd29e45ac-5741-43b8-91bc-2b8354c32a97%2F&kind=prefix<br>      - row "Select da443ab3-f2cf-426a-a061-117808042a17/ prefix da443ab3-f2cf-426a-a061-117808042a17/ — Register":<br>        - cell "Select da443ab3-f2cf-426a-a061-117808042a17/ prefix":<br>          - checkbox "Select da443ab3-f2cf-426a-a061-117808042a17/"<br>          - generic: prefix<br>        - cell "da443ab3-f2cf-426a-a061-117808042a17/":<br>          - link "da443ab3-f2cf-426a-a061-117808042a17/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fda443ab3-f2cf-426a-a061-117808042a17%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fda443ab3-f2cf-426a-a061-117808042a17%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Ftmp%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-atlas-dev-1789587058836.txt ; I1-A-BUCKET-lsmc-atlas-dev-1789587058836.png

### BUCKET-lsmc-aws-config-108782052779 I1-A — PASS

- **timestamp**: 2026-09-16T19:30:59.440Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-aws-config-108782052779/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-aws-config-108782052779/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F<br>  - link "lsmc-aws-config-108782052779":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select AWSLogs/ prefix AWSLogs/ — Register":<br>        - cell "Select AWSLogs/ prefix":<br>          - checkbox "Select AWSLogs/"<br>          - generic: prefix<br>        - cell "AWSLogs/":<br>          - link "AWSLogs/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2FAWSLogs%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2FAWSLogs%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-aws-config-108782052779-1789587059440.txt ; I1-A-BUCKET-lsmc-aws-config-108782052779-1789587059440.png

### BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:08.876Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: - button "privacy.html"<br>        - cell "5.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fprivacy.html&kind=object<br>      - row "Select robots.txt object robots.txt 66 B Register":<br>        - cell "Select robots.txt object":<br>          - checkbox "Select robots.txt"<br>          - generic: object<br>        - cell "robots.txt":<br>          - button "robots.txt"<br>        - cell "66 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Frobots.txt&kind=object<br>      - row "Select site.webmanifest object site.webmanifest 337 B Register":<br>        - cell "Select site.webmanifest object":<br>          - checkbox "Select site.webmanifest"<br>          - generic: object<br>        - cell "site.webmanifest":<br>          - button "site.webmanifest"<br>        - cell "337 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fsite.webmanifest&kind=object<br>      - row "Select sitemap.xml object sitemap.xml 258 B Register":<br>        - cell "Select sitemap.xml object":<br>          - checkbox "Select sitemap.xml"<br>          - generic: object<br>        - cell "sitemap.xml":<br>          - button "sitemap.xml"<br>        - cell "258 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fsitemap.xml&kind=object<br>      - row "Select tos.html object tos.html 6.5K B Register":<br>        - cell "Select tos.html object":<br>          - checkbox "Select tos.html"<br>          - generic: object<br>        - cell "tos.html":<br>          - button "tos.html"<br>        - cell "6.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Ftos.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1-1789587068876.txt ; I1-A-BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1-1789587068876.png

### BUCKET-lsmc-copy-ultimagen-lsmc-cro-316 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:09.572Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F
- **expected**: Page fully renders its expected content
- **observed**: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-copy-ultimagen-lsmc-cro-316/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-copy-ultimagen-lsmc-cro-316/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F<br>  - link "lsmc-copy-ultimagen-lsmc-cro-316":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 2025-07-25/ prefix 2025-07-25/ — Register":<br>        - cell "Select 2025-07-25/ prefix":<br>          - checkbox "Select 2025-07-25/"<br>          - generic: prefix<br>        - cell "2025-07-25/":<br>          - link "2025-07-25/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F2025-07-25%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F2025-07-25%2F&kind=prefix<br>      - row "Select Feb27_2025_ugsb4_data/ prefix Feb27_2025_ugsb4_data/ — Register":<br>        - cell "Select Feb27_2025_ugsb4_data/ prefix":<br>          - checkbox "Select Feb27_2025_ugsb4_data/"<br>          - generic: prefix<br>        - cell "Feb27_2025_ugsb4_data/":<br>          - link "Feb27_2025_ugsb4_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2FFeb27_2025_ugsb4_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2FFeb27_2025_ugsb4_data%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-copy-ultimagen-lsmc-cro-316-1789587069572.txt ; I1-A-BUCKET-lsmc-copy-ultimagen-lsmc-cro-316-1789587069572.png

### BUCKET-lsmc-datalake-raw-dev I1-A — PASS

- **timestamp**: 2026-09-16T19:31:10.095Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-datalake-raw-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-datalake-raw-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F<br>  - link "lsmc-datalake-raw-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select raw/ prefix raw/ — Register":<br>        - cell "Select raw/ prefix":<br>          - checkbox "Select raw/"<br>          - generic: prefix<br>        - cell "raw/":<br>          - link "raw/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2Fraw%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2Fraw%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-datalake-raw-dev-1789587070095.txt ; I1-A-BUCKET-lsmc-datalake-raw-dev-1789587070095.png

### BUCKET-lsmc-dayoa-analysis-results-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:10.818Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: is-results-usw2%2Fdragen%2F&kind=prefix<br>      - row "Select staging/ prefix staging/ — Register":<br>        - cell "Select staging/ prefix":<br>          - checkbox "Select staging/"<br>          - generic: prefix<br>        - cell "staging/":<br>          - link "staging/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fstaging%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fstaging%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftmp%2F&kind=prefix<br>      - row "Select transfers/ prefix transfers/ — Register":<br>        - cell "Select transfers/ prefix":<br>          - checkbox "Select transfers/"<br>          - generic: prefix<br>        - cell "transfers/":<br>          - link "transfers/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftransfers%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftransfers%2F&kind=prefix<br>      - row "Select validation/ prefix validation/ — Register":<br>        - cell "Select validation/ prefix":<br>          - checkbox "Select validation/"<br>          - generic: prefix<br>        - cell "validation/":<br>          - link "validation/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fvalidation%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fvalidation%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-analysis-results-usw2-1789587070818.txt ; I1-A-BUCKET-lsmc-dayoa-analysis-results-usw2-1789587070818.png

### BUCKET-lsmc-dayoa-control-data-use1 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:11.822Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2F
- **expected**: Page fully renders its expected content
- **observed**: -data-use1%2Fdayoa_source_overlays%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fdayoa_source_overlays%2F&kind=prefix<br>      - row "Select genomic_data/ prefix genomic_data/ — Register":<br>        - cell "Select genomic_data/ prefix":<br>          - checkbox "Select genomic_data/"<br>          - generic: prefix<br>        - cell "genomic_data/":<br>          - link "genomic_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fgenomic_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fgenomic_data%2F&kind=prefix<br>      - row "Select staged_external_sequencing_data/ prefix staged_external_sequencing_data/ — Register":<br>        - cell "Select staged_external_sequencing_data/ prefix":<br>          - checkbox "Select staged_external_sequencing_data/"<br>          - generic: prefix<br>        - cell "staged_external_sequencing_data/":<br>          - link "staged_external_sequencing_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fstaged_external_sequencing_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fstaged_external_sequencing_data%2F&kind=prefix<br>      - row "Select ursa-hotpatch-source/ prefix ursa-hotpatch-source/ — Register":<br>        - cell "Select ursa-hotpatch-source/ prefix":<br>          - checkbox "Select ursa-hotpatch-source/"<br>          - generic: prefix<br>        - cell "ursa-hotpatch-source/":<br>          - link "ursa-hotpatch-source/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fursa-hotpatch-source%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fursa-hotpatch-source%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-control-data-use1-1789587071822.txt ; I1-A-BUCKET-lsmc-dayoa-control-data-use1-1789587071822.png

### BUCKET-lsmc-dayoa-control-data-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:12.552Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**:       - cell "staged_external_sequencing_data/":<br>          - link "staged_external_sequencing_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fstaged_external_sequencing_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fstaged_external_sequencing_data%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Ftmp%2F&kind=prefix<br>      - row "Select ursa-hotpatch-source/ prefix ursa-hotpatch-source/ — Register":<br>        - cell "Select ursa-hotpatch-source/ prefix":<br>          - checkbox "Select ursa-hotpatch-source/"<br>          - generic: prefix<br>        - cell "ursa-hotpatch-source/":<br>          - link "ursa-hotpatch-source/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fursa-hotpatch-source%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fursa-hotpatch-source%2F&kind=prefix<br>      - row "Select workflow_payloads/ prefix workflow_payloads/ — Register":<br>        - cell "Select workflow_payloads/ prefix":<br>          - checkbox "Select workflow_payloads/"<br>          - generic: prefix<br>        - cell "workflow_payloads/":<br>          - link "workflow_payloads/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fworkflow_payloads%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fworkflow_payloads%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-control-data-usw2-1789587072552.txt ; I1-A-BUCKET-lsmc-dayoa-control-data-usw2-1789587072552.png

### BUCKET-lsmc-dayoa-omics-analysis-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:14.588Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:        - button "ont_example.csv"<br>        - cell "5.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Font_example.csv&kind=object<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fs3_reference_data_version.info&kind=object<br>      - row "Select ultima_analysis_manifest.csv object ultima_analysis_manifest.csv 4.1K B Register":<br>        - cell "Select ultima_analysis_manifest.csv object":<br>          - checkbox "Select ultima_analysis_manifest.csv"<br>          - generic: object<br>        - cell "ultima_analysis_manifest.csv":<br>          - button "ultima_analysis_manifest.csv"<br>        - cell "4.1K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fultima_analysis_manifest.csv&kind=object<br>      - row "Select ultima_new_new_chemistry_202508_hg002_all.tsv object ultima_new_new_chemistry_202508_hg002_all.tsv 343K B Register":<br>        - cell "Select ultima_new_new_chemistry_202508_hg002_all.tsv object":<br>          - checkbox "Select ultima_new_new_chemistry_202508_hg002_all.tsv"<br>          - generic: object<br>        - cell "ultima_new_new_chemistry_202508_hg002_all.tsv":<br>          - button "ultima_new_new_chemistry_202508_hg002_all.tsv"<br>        - cell "343K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fultima_new_new_chemistry_202508_hg002_all.tsv&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-omics-analysis-us-west-2-1789587074588.txt ; I1-A-BUCKET-lsmc-dayoa-omics-analysis-us-west-2-1789587074588.png

### BUCKET-lsmc-dayoa-references-use1 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:16.944Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2F
- **expected**: Page fully renders its expected content
- **observed**: age?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fbbefa30e0e45538%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fbbefa30e0e45538%2F&kind=prefix<br>      - row "Select task-0fc3f2ec425e70f91/ prefix task-0fc3f2ec425e70f91/ — Register":<br>        - cell "Select task-0fc3f2ec425e70f91/ prefix":<br>          - checkbox "Select task-0fc3f2ec425e70f91/"<br>          - generic: prefix<br>        - cell "task-0fc3f2ec425e70f91/":<br>          - link "task-0fc3f2ec425e70f91/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fc3f2ec425e70f91%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fc3f2ec425e70f91%2F&kind=prefix<br>      - row "Select task-0fe86f0efff3db702/ prefix task-0fe86f0efff3db702/ — Register":<br>        - cell "Select task-0fe86f0efff3db702/ prefix":<br>          - checkbox "Select task-0fe86f0efff3db702/"<br>          - generic: prefix<br>        - cell "task-0fe86f0efff3db702/":<br>          - link "task-0fe86f0efff3db702/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fe86f0efff3db702%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fe86f0efff3db702%2F&kind=prefix<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Fs3_reference_data_version.info&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-references-use1-1789587076944.txt ; I1-A-BUCKET-lsmc-dayoa-references-use1-1789587076944.png

### BUCKET-lsmc-dayoa-references-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:19.414Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: -dayoa-references-usw2%2Ftask-09fd8d1a327ce02c6%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-09fd8d1a327ce02c6%2F&kind=prefix<br>      - row "Select task-0a052f69a5cd9cd5f/ prefix task-0a052f69a5cd9cd5f/ — Register":<br>        - cell "Select task-0a052f69a5cd9cd5f/ prefix":<br>          - checkbox "Select task-0a052f69a5cd9cd5f/"<br>          - generic: prefix<br>        - cell "task-0a052f69a5cd9cd5f/":<br>          - link "task-0a052f69a5cd9cd5f/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a052f69a5cd9cd5f%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a052f69a5cd9cd5f%2F&kind=prefix<br>      - row "Select task-0a08c1dc6c2902cd3/ prefix task-0a08c1dc6c2902cd3/ — Register":<br>        - cell "Select task-0a08c1dc6c2902cd3/ prefix":<br>          - checkbox "Select task-0a08c1dc6c2902cd3/"<br>          - generic: prefix<br>        - cell "task-0a08c1dc6c2902cd3/":<br>          - link "task-0a08c1dc6c2902cd3/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a08c1dc6c2902cd3%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a08c1dc6c2902cd3%2F&kind=prefix<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Fs3_reference_data_version.info&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-references-usw2-1789587079414.txt ; I1-A-BUCKET-lsmc-dayoa-references-usw2-1789587079414.png

### BUCKET-lsmc-dayoa-runtime-assets-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:20.262Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**:      - checkbox "Select tool_specific_resources/"<br>          - generic: prefix<br>        - cell "tool_specific_resources/":<br>          - link "tool_specific_resources/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Ftool_specific_resources%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Ftool_specific_resources%2F&kind=prefix<br>      - row "Select ursa-evidence/ prefix ursa-evidence/ — Register":<br>        - cell "Select ursa-evidence/ prefix":<br>          - checkbox "Select ursa-evidence/"<br>          - generic: prefix<br>        - cell "ursa-evidence/":<br>          - link "ursa-evidence/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-evidence%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-evidence%2F&kind=prefix<br>      - row "Select ursa-hotpatches/ prefix ursa-hotpatches/ — Register":<br>        - cell "Select ursa-hotpatches/ prefix":<br>          - checkbox "Select ursa-hotpatches/"<br>          - generic: prefix<br>        - cell "ursa-hotpatches/":<br>          - link "ursa-hotpatches/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-hotpatches%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-hotpatches%2F&kind=prefix<br>      - row "Select ursa/ prefix ursa/ — Register":<br>        - cell "Select ursa/ prefix":<br>          - checkbox "Select ursa/"<br>          - generic: prefix<br>        - cell "ursa/":<br>          - link "ursa/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-runtime-assets-usw2-1789587080262.txt ; I1-A-BUCKET-lsmc-dayoa-runtime-assets-usw2-1789587080262.png

### BUCKET-lsmc-dayoa-staging-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:21.030Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: oa-staging-usw2%2Fremote_stage_20260903T142019Z_473bd635%2F&kind=prefix<br>      - row "Select staged/ prefix staged/ — Register":<br>        - cell "Select staged/ prefix":<br>          - checkbox "Select staged/"<br>          - generic: prefix<br>        - cell "staged/":<br>          - link "staged/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged%2F&kind=prefix<br>      - row "Select staged_sample_data/ prefix staged_sample_data/ — Register":<br>        - cell "Select staged_sample_data/ prefix":<br>          - checkbox "Select staged_sample_data/"<br>          - generic: prefix<br>        - cell "staged_sample_data/":<br>          - link "staged_sample_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged_sample_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged_sample_data%2F&kind=prefix<br>      - row "Select staging/ prefix staging/ — Register":<br>        - cell "Select staging/ prefix":<br>          - checkbox "Select staging/"<br>          - generic: prefix<br>        - cell "staging/":<br>          - link "staging/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaging%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaging%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Ftmp%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dayoa-staging-usw2-1789587081030.txt ; I1-A-BUCKET-lsmc-dayoa-staging-usw2-1789587081030.png

### BUCKET-lsmc-dewey-0 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:21.799Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2F
- **expected**: Page fully renders its expected content
- **observed**:       - row "Select dayec-transient/ prefix dayec-transient/ — Register":<br>        - cell "Select dayec-transient/ prefix":<br>          - checkbox "Select dayec-transient/"<br>          - generic: prefix<br>        - cell "dayec-transient/":<br>          - link "dayec-transient/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fdayec-transient%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fdayec-transient%2F&kind=prefix<br>      - row "Select external-smoke/ prefix external-smoke/ — Register":<br>        - cell "Select external-smoke/ prefix":<br>          - checkbox "Select external-smoke/"<br>          - generic: prefix<br>        - cell "external-smoke/":<br>          - link "external-smoke/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fexternal-smoke%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fexternal-smoke%2F&kind=prefix<br>      - row "Select functional-tests/ prefix functional-tests/ — Register":<br>        - cell "Select functional-tests/ prefix":<br>          - checkbox "Select functional-tests/"<br>          - generic: prefix<br>        - cell "functional-tests/":<br>          - link "functional-tests/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Ffunctional-tests%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Ffunctional-tests%2F&kind=prefix<br>      - row "Select gui-audit/ prefix gui-audit/ — Register":<br>        - cell "Select gui-audit/ prefix":<br>          - checkbox "Select gui-audit/"<br>          - generic: prefix<br>        - cell "gui-audit/":<br>          - link "gui-audit/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-dewey-0-1789587081799.txt ; I1-A-BUCKET-lsmc-dewey-0-1789587081799.png

### BUCKET-lsmc-docs-public-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:31:22.502Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:  button "index.html"<br>        - cell "53.3K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Findex.html&kind=object<br>      - row "Select llms-full.txt object llms-full.txt 414.5K B Register":<br>        - cell "Select llms-full.txt object":<br>          - checkbox "Select llms-full.txt"<br>          - generic: object<br>        - cell "llms-full.txt":<br>          - button "llms-full.txt"<br>        - cell "414.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fllms-full.txt&kind=object<br>      - row "Select llms.txt object llms.txt 6.2K B Register":<br>        - cell "Select llms.txt object":<br>          - checkbox "Select llms.txt"<br>          - generic: object<br>        - cell "llms.txt":<br>          - button "llms.txt"<br>        - cell "6.2K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fllms.txt&kind=object<br>      - row "Select sitemap-0.xml object sitemap-0.xml 11.3K B Register":<br>        - cell "Select sitemap-0.xml object":<br>          - checkbox "Select sitemap-0.xml"<br>          - generic: object<br>        - cell "sitemap-0.xml":<br>          - button "sitemap-0.xml"<br>        - cell "11.3K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fsitemap-0.xml&kind=object<br>      - row "Select sitemap-index.xml object sitemap-index.xml 185 B Register":<br>        - cell "Select sitemap-index.xml object":<br>          - checkbox "Select sitemap-index.xml"<br>          - generic: object<br>        - cell "sitemap-index.xml":<br>          - button "sitemap-index.xml"<br>        - cell "185 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fsitemap-index.xml&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-docs-public-108782052779-us-west-2-1789587082502.txt ; I1-A-BUCKET-lsmc-docs-public-108782052779-us-west-2-1789587082502.png

### BUCKET-lsmc-healthomics-failiover I1-A — PASS

- **timestamp**: 2026-09-16T19:31:23.106Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-healthomics-failiover/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-healthomics-failiover/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F<br>  - link "lsmc-healthomics-failiover":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-healthomics-failiover-1789587083106.txt ; I1-A-BUCKET-lsmc-healthomics-failiover-1789587083106.png

### BUCKET-lsmc-healthomics-results I1-A — PASS

- **timestamp**: 2026-09-16T19:31:23.635Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-healthomics-results/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-healthomics-results/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-healthomics-results%2F<br>  - link "lsmc-healthomics-results":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 9998872/ prefix 9998872/ — Register":<br>        - cell "Select 9998872/ prefix":<br>          - checkbox "Select 9998872/"<br>          - generic: prefix<br>        - cell "9998872/":<br>          - link "9998872/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F9998872%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-healthomics-results%2F9998872%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-healthomics-results-1789587083635.txt ; I1-A-BUCKET-lsmc-healthomics-results-1789587083635.png

### LIT-REGISTER I1-A — PASS

- **timestamp**: 2026-09-16T19:32:05.572Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRF1
- **expected**: Paper registration yields persisted artifact and navigable record
- **observed**: PMID35750315 created M-DGX-TRF1; Open in Dewey renders publication title/authors/identifiers and fulltext unavailable status.
- **evidence**: I1-A-LIT-REGISTER-1789587125572.txt ; I1-A-LIT-REGISTER-1789587125572.png

### BUCKET-lsmc-ifx-bjuice-pkgd-data I1-A — PASS

- **timestamp**: 2026-09-16T19:32:16.519Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F
- **expected**: Page fully renders its expected content
- **observed**: ount<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ifx-bjuice-pkgd-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ifx-bjuice-pkgd-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F<br>  - link "lsmc-ifx-bjuice-pkgd-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select _probes/ prefix _probes/ — Register":<br>        - cell "Select _probes/ prefix":<br>          - checkbox "Select _probes/"<br>          - generic: prefix<br>        - cell "_probes/":<br>          - link "_probes/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F_probes%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F_probes%2F&kind=prefix<br>      - row "Select ifx-p2-1000-120-0715/ prefix ifx-p2-1000-120-0715/ — Register":<br>        - cell "Select ifx-p2-1000-120-0715/ prefix":<br>          - checkbox "Select ifx-p2-1000-120-0715/"<br>          - generic: prefix<br>        - cell "ifx-p2-1000-120-0715/":<br>          - link "ifx-p2-1000-120-0715/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2Fifx-p2-1000-120-0715%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2Fifx-p2-1000-120-0715%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-ifx-bjuice-pkgd-data-1789587136519.txt ; I1-A-BUCKET-lsmc-ifx-bjuice-pkgd-data-1789587136519.png

### BUCKET-lsmc-illumina-public-data I1-A — PASS

- **timestamp**: 2026-09-16T19:32:17.143Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2F
- **expected**: Page fully renders its expected content
- **observed**: c-illumina-public-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-illumina-public-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-illumina-public-data%2F<br>  - link "lsmc-illumina-public-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/ prefix NovaSeqX_WHGS_TruSeqPF_HG002-007/ — Register":<br>        - cell "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/ prefix":<br>          - checkbox "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/"<br>          - generic: prefix<br>        - cell "NovaSeqX_WHGS_TruSeqPF_HG002-007/":<br>          - link "NovaSeqX_WHGS_TruSeqPF_HG002-007/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_HG002-007%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_HG002-007%2F&kind=prefix<br>      - row "Select NovaSeqX_WHGS_TruSeqPF_NA12878/ prefix NovaSeqX_WHGS_TruSeqPF_NA12878/ — Register":<br>        - cell "Select NovaSeqX_WHGS_TruSeqPF_NA12878/ prefix":<br>          - checkbox "Select NovaSeqX_WHGS_TruSeqPF_NA12878/"<br>          - generic: prefix<br>        - cell "NovaSeqX_WHGS_TruSeqPF_NA12878/":<br>          - link "NovaSeqX_WHGS_TruSeqPF_NA12878/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_NA12878%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_NA12878%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-illumina-public-data-1789587137143.txt ; I1-A-BUCKET-lsmc-illumina-public-data-1789587137143.png

### BUCKET-lsmc-meridian-governance-registry I1-A — PASS

- **timestamp**: 2026-09-16T19:32:17.814Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-meridian-governance-registry/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-meridian-governance-registry/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F<br>  - link "lsmc-meridian-governance-registry":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select prefixes/ prefix prefixes/ — Register":<br>        - cell "Select prefixes/ prefix":<br>          - checkbox "Select prefixes/"<br>          - generic: prefix<br>        - cell "prefixes/":<br>          - link "prefixes/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2Fprefixes%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2Fprefixes%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-meridian-governance-registry-1789587137814.txt ; I1-A-BUCKET-lsmc-meridian-governance-registry-1789587137814.png

### BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:18.448Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: ROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F<br>  - link "lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select raw/ prefix raw/ — Register":<br>        - cell "Select raw/ prefix":<br>          - checkbox "Select raw/"<br>          - generic: prefix<br>        - cell "raw/":<br>          - link "raw/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fraw%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fraw%2F&kind=prefix<br>      - row "Select v2/ prefix v2/ — Register":<br>        - cell "Select v2/ prefix":<br>          - checkbox "Select v2/"<br>          - generic: prefix<br>        - cell "v2/":<br>          - link "v2/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fv2%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fv2%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2-1789587138448.txt ; I1-A-BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2-1789587138448.png

### BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:18.953Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:     - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F<br>  - link "lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select accessioning/ prefix accessioning/ — Register":<br>        - cell "Select accessioning/ prefix":<br>          - checkbox "Select accessioning/"<br>          - generic: prefix<br>        - cell "accessioning/":<br>          - link "accessioning/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2Faccessioning%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2Faccessioning%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2-1789587138953.txt ; I1-A-BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2-1789587138953.png

### BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:19.861Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:         - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Freceiving.html&kind=object<br>      - row "Select records.html object records.html 38.7K B Register":<br>        - cell "Select records.html object":<br>          - checkbox "Select records.html"<br>          - generic: object<br>        - cell "records.html":<br>          - button "records.html"<br>        - cell "38.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Frecords.html&kind=object<br>      - row "Select robots.txt object robots.txt 26 B Register":<br>        - cell "Select robots.txt object":<br>          - checkbox "Select robots.txt"<br>          - generic: object<br>        - cell "robots.txt":<br>          - button "robots.txt"<br>        - cell "26 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Frobots.txt&kind=object<br>      - row "Select sample-holds.html object sample-holds.html 38.8K B Register":<br>        - cell "Select sample-holds.html object":<br>          - checkbox "Select sample-holds.html"<br>          - generic: object<br>        - cell "sample-holds.html":<br>          - button "sample-holds.html"<br>        - cell "38.8K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Fsample-holds.html&kind=object<br>      - row "Select workspace.html object workspace.html 37.9K B Register":<br>        - cell "Select workspace.html object":<br>          - checkbox "Select workspace.html"<br>          - generic: object<br>        - cell "workspace.html":<br>          - button "workspace.html"<br>        - cell "37.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Fworkspace.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2-1789587139861.txt ; I1-A-BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2-1789587139861.png

### BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:20.519Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-status-alb-logs-108782052779/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-status-alb-logs-108782052779/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F<br>  - link "lsmc-mvp-v1-status-alb-logs-108782052779":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select status/ prefix status/ — Register":<br>        - cell "Select status/ prefix":<br>          - checkbox "Select status/"<br>          - generic: prefix<br>        - cell "status/":<br>          - link "status/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2Fstatus%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2Fstatus%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779-1789587140519.txt ; I1-A-BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779-1789587140519.png

### BUCKET-lsmc-public-ont-data I1-A — PASS

- **timestamp**: 2026-09-16T19:32:21.043Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-public-ont-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-public-ont-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-public-ont-data%2F<br>  - link "lsmc-public-ont-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 20250313/ prefix 20250313/ — Register":<br>        - cell "Select 20250313/ prefix":<br>          - checkbox "Select 20250313/"<br>          - generic: prefix<br>        - cell "20250313/":<br>          - link "20250313/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F20250313%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-public-ont-data%2F20250313%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-public-ont-data-1789587141043.txt ; I1-A-BUCKET-lsmc-public-ont-data-1789587141043.png

### BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2 I1-A — REVIEW

- **timestamp**: 2026-09-16T19:32:21.592Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-qeo-day-analytical-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - status: "User: arn:aws:sts::108782052779:assumed-role/Dayhoff-day-Compute-InstanceRole3CCE2F1D-Nt0s1SL3rfbr/i-07df3a933e4839f52 is not authorized to perform: s3:ListBucket on resource: \"arn:aws:s3:::lsmc-qeo-day-analytical-108782052779-us-west-2\" with an explicit deny in a resource-based policy"<br>  - heading "Unable to load this view" [level=2]<br>  - paragraph: See the error above. You can use the navigation to return to the Library.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789587141592.txt ; I1-A-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789587141592.png

### BUCKET-lsmc-ssf-sequencing-data I1-A — PASS

- **timestamp**: 2026-09-16T19:32:22.451Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2F
- **expected**: Page fully renders its expected content
- **observed**:    - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Freference%2F&kind=prefix<br>      - row "Select staged_external_data/ prefix staged_external_data/ — Register":<br>        - cell "Select staged_external_data/ prefix":<br>          - checkbox "Select staged_external_data/"<br>          - generic: prefix<br>        - cell "staged_external_data/":<br>          - link "staged_external_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fstaged_external_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fstaged_external_data%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Ftmp%2F&kind=prefix<br>      - row "Select ubuntu/ prefix ubuntu/ — Register":<br>        - cell "Select ubuntu/ prefix":<br>          - checkbox "Select ubuntu/"<br>          - generic: prefix<br>        - cell "ubuntu/":<br>          - link "ubuntu/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fubuntu%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fubuntu%2F&kind=prefix<br>      - row "Select README.md object README.md 7.6K B Register":<br>        - cell "Select README.md object":<br>          - checkbox "Select README.md"<br>          - generic: object<br>        - cell "README.md":<br>          - button "README.md"<br>        - cell "7.6K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2FREADME.md&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-ssf-sequencing-data-1789587142451.txt ; I1-A-BUCKET-lsmc-ssf-sequencing-data-1789587142451.png

### BUCKET-lsmc-terraform-state I1-A — PASS

- **timestamp**: 2026-09-16T19:32:23.143Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-terraform-state%2F
- **expected**: Page fully renders its expected content
- **observed**: "<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select log-archive/ prefix log-archive/ — Register":<br>        - cell "Select log-archive/ prefix":<br>          - checkbox "Select log-archive/"<br>          - generic: prefix<br>        - cell "log-archive/":<br>          - link "log-archive/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Flog-archive%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Flog-archive%2F&kind=prefix<br>      - row "Select management/ prefix management/ — Register":<br>        - cell "Select management/ prefix":<br>          - checkbox "Select management/"<br>          - generic: prefix<br>        - cell "management/":<br>          - link "management/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fmanagement%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fmanagement%2F&kind=prefix<br>      - row "Select production/ prefix production/ — Register":<br>        - cell "Select production/ prefix":<br>          - checkbox "Select production/"<br>          - generic: prefix<br>        - cell "production/":<br>          - link "production/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fproduction%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fproduction%2F&kind=prefix<br>      - row "Select security/ prefix security/ — Register":<br>        - cell "Select security/ prefix":<br>          - checkbox "Select security/"<br>          - generic: prefix<br>        - cell "security/":<br>          - link "security/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fsecurity%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fsecurity%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-terraform-state-1789587143143.txt ; I1-A-BUCKET-lsmc-terraform-state-1789587143143.png

### BUCKET-lsmc-twenty-prod-storage I1-A — PASS

- **timestamp**: 2026-09-16T19:32:23.987Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F
- **expected**: Page fully renders its expected content
- **observed**: vigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-twenty-prod-storage/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-twenty-prod-storage/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F<br>  - link "lsmc-twenty-prod-storage":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ prefix e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ — Register":<br>        - cell "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ prefix":<br>          - checkbox "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/"<br>          - generic: prefix<br>        - cell "e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/":<br>          - link "e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2Fe6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2Fe6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-twenty-prod-storage-1789587143987.txt ; I1-A-BUCKET-lsmc-twenty-prod-storage-1789587143987.png

### BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:24.648Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: D<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ursa-cost-reports-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ursa-cost-reports-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F<br>  - link "lsmc-ursa-cost-reports-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select reports/ prefix reports/ — Register":<br>        - cell "Select reports/ prefix":<br>          - checkbox "Select reports/"<br>          - generic: prefix<br>        - cell "reports/":<br>          - link "reports/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Freports%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Freports%2F&kind=prefix<br>      - row "Select ursa-deploy-scripts/ prefix ursa-deploy-scripts/ — Register":<br>        - cell "Select ursa-deploy-scripts/ prefix":<br>          - checkbox "Select ursa-deploy-scripts/"<br>          - generic: prefix<br>        - cell "ursa-deploy-scripts/":<br>          - link "ursa-deploy-scripts/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Fursa-deploy-scripts%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Fursa-deploy-scripts%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2-1789587144648.txt ; I1-A-BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2-1789587144648.png

### BUCKET-lsmc-ursa-customers-usw2 I1-A — PASS

- **timestamp**: 2026-09-16T19:32:25.260Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ursa-customers-usw2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ursa-customers-usw2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F<br>  - link "lsmc-ursa-customers-usw2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-lsmc-ursa-customers-usw2-1789587145260.txt ; I1-A-BUCKET-lsmc-ursa-customers-usw2-1789587145260.png

### BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps I1-A — PASS

- **timestamp**: 2026-09-16T19:32:25.866Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F<br>  - link "marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps-1789587145866.txt ; I1-A-BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps-1789587145866.png

### BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:32:54.565Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F
- **expected**: Page fully renders its expected content
- **observed**: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F: Error: Timed out waiting for tab 4 to navigate to https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F.
- **evidence**: I1-A-BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie-1789587174565.txt

### BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo I1-A — PASS

- **timestamp**: 2026-09-16T19:32:55.223Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F<br>  - link "marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo-1789587175223.txt ; I1-A-BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo-1789587175223.png

### BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj I1-A — PASS

- **timestamp**: 2026-09-16T19:32:55.931Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F
- **expected**: Page fully renders its expected content
- **observed**:  navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F<br>  - link "marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select audit/ prefix audit/ — Register":<br>        - cell "Select audit/ prefix":<br>          - checkbox "Select audit/"<br>          - generic: prefix<br>        - cell "audit/":<br>          - link "audit/":<br>            - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2Faudit%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2Faudit%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj-1789587175931.txt ; I1-A-BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj-1789587175931.png

### BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl I1-A — PASS

- **timestamp**: 2026-09-16T19:32:57.198Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2F
- **expected**: Page fully renders its expected content
- **observed**: eanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fa90ebf33932ad96c7f95045f39ca4273.template&kind=object<br>      - row "Select bd9b5df9ed21415aabf9be3dd0bf872b object bd9b5df9ed21415aabf9be3dd0bf872b 30.7M B Register":<br>        - cell "Select bd9b5df9ed21415aabf9be3dd0bf872b object":<br>          - checkbox "Select bd9b5df9ed21415aabf9be3dd0bf872b"<br>          - generic: object<br>        - cell "bd9b5df9ed21415aabf9be3dd0bf872b":<br>          - button "bd9b5df9ed21415aabf9be3dd0bf872b"<br>        - cell "30.7M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fbd9b5df9ed21415aabf9be3dd0bf872b&kind=object<br>      - row "Select c0eae6ac1f8491e980ecfdc9888864f0 object c0eae6ac1f8491e980ecfdc9888864f0 36.4M B Register":<br>        - cell "Select c0eae6ac1f8491e980ecfdc9888864f0 object":<br>          - checkbox "Select c0eae6ac1f8491e980ecfdc9888864f0"<br>          - generic: object<br>        - cell "c0eae6ac1f8491e980ecfdc9888864f0":<br>          - button "c0eae6ac1f8491e980ecfdc9888864f0"<br>        - cell "36.4M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fc0eae6ac1f8491e980ecfdc9888864f0&kind=object<br>      - row "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template object f8fabfa3d78a1f43ef40b3d4efc31df9.template 70.7K B Register":<br>        - cell "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template object":<br>          - checkbox "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template"<br>          - generic: object<br>        - cell "f8fabfa3d78a1f43ef40b3d4efc31df9.template":<br>          - button "f8fabfa3d78a1f43ef40b3d4efc31df9.template"<br>        - cell "70.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Ff8fabfa3d78a1f43ef40b3d4efc31df9.template&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl-1789587177198.txt ; I1-A-BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl-1789587177198.png

### BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete I1-A — PASS

- **timestamp**: 2026-09-16T19:32:57.729Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-4da281c1dc024f1c-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-4da281c1dc024f1c-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F<br>  - link "parallelcluster-4da281c1dc024f1c-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete-1789587177729.txt ; I1-A-BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete-1789587177729.png

### BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete I1-A — PASS

- **timestamp**: 2026-09-16T19:32:58.846Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-730cb6d53cf2deec-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-730cb6d53cf2deec-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F<br>  - link "parallelcluster-730cb6d53cf2deec-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete-1789587178846.txt ; I1-A-BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete-1789587178846.png

### BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete I1-A — PASS

- **timestamp**: 2026-09-16T19:33:00.180Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-e781c59d26140bab-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-e781c59d26140bab-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F<br>  - link "parallelcluster-e781c59d26140bab-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete-1789587180180.txt ; I1-A-BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete-1789587180180.png

### BUCKET-terrarium-dev-media I1-A — PASS

- **timestamp**: 2026-09-16T19:33:00.890Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F
- **expected**: Page fully renders its expected content
- **observed**: k "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-dev-media/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-dev-media/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>  - link "terrarium-dev-media":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select documents/ prefix documents/ — Register":<br>        - cell "Select documents/ prefix":<br>          - checkbox "Select documents/"<br>          - generic: prefix<br>        - cell "documents/":<br>          - link "documents/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2Fdocuments%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-media%2Fdocuments%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-media%2Fimages%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-dev-media-1789587180890.txt ; I1-A-BUCKET-terrarium-dev-media-1789587180890.png

### BUCKET-terrarium-dev-web I1-A — PASS

- **timestamp**: 2026-09-16T19:33:01.514Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F
- **expected**: Page fully renders its expected content
- **observed**: RI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-dev-web/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-dev-web/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>  - link "terrarium-dev-web":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select assets/ prefix assets/ — Register":<br>        - cell "Select assets/ prefix":<br>          - checkbox "Select assets/"<br>          - generic: prefix<br>        - cell "assets/":<br>          - link "assets/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2Fassets%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Fassets%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Fimages%2F&kind=prefix<br>      - row "Select index.html object index.html 482 B Register":<br>        - cell "Select index.html object":<br>          - checkbox "Select index.html"<br>          - generic: object<br>        - cell "index.html":<br>          - button "index.html"<br>        - cell "482 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Findex.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-dev-web-1789587181514.txt ; I1-A-BUCKET-terrarium-dev-web-1789587181514.png

### BUCKET-terrarium-prod-media I1-A — PASS

- **timestamp**: 2026-09-16T19:33:02.100Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F
- **expected**: Page fully renders its expected content
- **observed**: ture":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-prod-media/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-prod-media/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>  - link "terrarium-prod-media":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select documents/ prefix documents/ — Register":<br>        - cell "Select documents/ prefix":<br>          - checkbox "Select documents/"<br>          - generic: prefix<br>        - cell "documents/":<br>          - link "documents/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2Fdocuments%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-media%2Fdocuments%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-media%2Fimages%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-prod-media-1789587182100.txt ; I1-A-BUCKET-terrarium-prod-media-1789587182100.png

### BUCKET-terrarium-prod-web I1-A — PASS

- **timestamp**: 2026-09-16T19:33:02.752Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F
- **expected**: Page fully renders its expected content
- **observed**:  /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-prod-web/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-prod-web/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>  - link "terrarium-prod-web":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select assets/ prefix assets/ — Register":<br>        - cell "Select assets/ prefix":<br>          - checkbox "Select assets/"<br>          - generic: prefix<br>        - cell "assets/":<br>          - link "assets/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2Fassets%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Fassets%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Fimages%2F&kind=prefix<br>      - row "Select index.html object index.html 482 B Register":<br>        - cell "Select index.html object":<br>          - checkbox "Select index.html"<br>          - generic: object<br>        - cell "index.html":<br>          - button "index.html"<br>        - cell "482 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Findex.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-prod-web-1789587182752.txt ; I1-A-BUCKET-terrarium-prod-web-1789587182752.png

### BUCKET-terrarium-tfstate-dev I1-A — PASS

- **timestamp**: 2026-09-16T19:33:03.449Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-tfstate-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-tfstate-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>  - link "terrarium-tfstate-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select terrarium/ prefix terrarium/ — Register":<br>        - cell "Select terrarium/ prefix":<br>          - checkbox "Select terrarium/"<br>          - generic: prefix<br>        - cell "terrarium/":<br>          - link "terrarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2Fterrarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2Fterrarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-tfstate-dev-1789587183449.txt ; I1-A-BUCKET-terrarium-tfstate-dev-1789587183449.png

### BUCKET-terrarium-tfstate-prod I1-A — PASS

- **timestamp**: 2026-09-16T19:33:04.038Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-tfstate-prod/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-tfstate-prod/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>  - link "terrarium-tfstate-prod":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select terrarium/ prefix terrarium/ — Register":<br>        - cell "Select terrarium/ prefix":<br>          - checkbox "Select terrarium/"<br>          - generic: prefix<br>        - cell "terrarium/":<br>          - link "terrarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2Fterrarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2Fterrarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-terrarium-tfstate-prod-1789587184038.txt ; I1-A-BUCKET-terrarium-tfstate-prod-1789587184038.png

### BUCKET-ursa-us-west-2-052779-default-customer-1d8c14 I1-A — PASS

- **timestamp**: 2026-09-16T19:33:04.649Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F
- **expected**: Page fully renders its expected content
- **observed**: 1d8c14%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2Ftmp%2F&kind=prefix<br>      - row "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz object RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz 14.1M B Register":<br>        - cell "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz object":<br>          - checkbox "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz"<br>          - generic: object<br>        - cell "RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz":<br>          - button "RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz"<br>        - cell "14.1M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2FRIH0_ANA0-HG002_DBC0_0.R1.fastq.gz&kind=object<br>      - row "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz object RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz 15.2M B Register":<br>        - cell "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz object":<br>          - checkbox "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz"<br>          - generic: object<br>        - cell "RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz":<br>          - button "RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz"<br>        - cell "15.2M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2FRIH0_ANA0-HG002_DBC0_0.R2.fastq.gz&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-ursa-us-west-2-052779-default-customer-1d8c14-1789587184649.txt ; I1-A-BUCKET-ursa-us-west-2-052779-default-customer-1d8c14-1789587184649.png

### BUCKET-zebra-day-cfg-us-west-2 I1-A — PASS

- **timestamp**: 2026-09-16T19:33:05.246Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://zebra-day-cfg-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://zebra-day-cfg-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>  - link "zebra-day-cfg-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select zebra-day/ prefix zebra-day/ — Register":<br>        - cell "Select zebra-day/ prefix":<br>          - checkbox "Select zebra-day/"<br>          - generic: prefix<br>        - cell "zebra-day/":<br>          - link "zebra-day/":<br>            - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2Fzebra-day%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2Fzebra-day%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-BUCKET-zebra-day-cfg-us-west-2-1789587185246.txt ; I1-A-BUCKET-zebra-day-cfg-us-west-2-1789587185246.png

### ROUTES-ROOT I1-A — PASS

- **timestamp**: 2026-09-16T19:33:40.932Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Page fully renders its expected content
- **observed**: NFE"<br>        - cell "multiqc_bclconvert_bysample.txt M-DGX-NNFE":<br>          - link "multiqc_bclconvert_bysample.txt":<br>            - /url: /records/M-DGX-NNFE<br>          - generic: M-DGX-NNFE<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNDJ multiqc_bclconvert_bylane.txt M-DGX-NNDJ object — 9/9/2026":<br>        - cell "Select M-DGX-NNDJ":<br>          - checkbox "Select M-DGX-NNDJ"<br>        - cell "multiqc_bclconvert_bylane.txt M-DGX-NNDJ":<br>          - link "multiqc_bclconvert_bylane.txt":<br>            - /url: /records/M-DGX-NNDJ<br>          - generic: M-DGX-NNDJ<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNBP multiqc.parquet M-DGX-NNBP object — 9/9/2026":<br>        - cell "Select M-DGX-NNBP":<br>          - checkbox "Select M-DGX-NNBP"<br>        - cell "multiqc.parquet M-DGX-NNBP":<br>          - link "multiqc.parquet":<br>            - /url: /records/M-DGX-NNBP<br>          - generic: M-DGX-NNBP<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NN9T multiqc.log M-DGX-NN9T object — 9/9/2026":<br>        - cell "Select M-DGX-NN9T":<br>          - checkbox "Select M-DGX-NN9T"<br>        - cell "multiqc.log M-DGX-NN9T":<br>          - link "multiqc.log":<br>            - /url: /records/M-DGX-NN9T<br>          - generic: M-DGX-NN9T<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NN7Y llms-full.txt M-DGX-NN7Y object — 9/9/2026":<br>        - cell "Select M-DGX-NN7Y":<br>          - checkbox "Select M-DGX-NN7Y"<br>        - cell "llms-full.txt M-DGX-NN7Y":<br>          - link "llms-full.txt":<br>            - /url: /records/M-DGX-NN7Y<br>          - generic: M-DGX-NN7Y<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-ROUTES-ROOT-1789587220932.txt ; I1-A-ROUTES-ROOT-1789587220932.png

### ROUTES-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:33:41.837Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/search
- **expected**: Page fully renders its expected content
- **observed**: NFE"<br>        - cell "multiqc_bclconvert_bysample.txt M-DGX-NNFE":<br>          - link "multiqc_bclconvert_bysample.txt":<br>            - /url: /records/M-DGX-NNFE<br>          - generic: M-DGX-NNFE<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNDJ multiqc_bclconvert_bylane.txt M-DGX-NNDJ object — 9/9/2026":<br>        - cell "Select M-DGX-NNDJ":<br>          - checkbox "Select M-DGX-NNDJ"<br>        - cell "multiqc_bclconvert_bylane.txt M-DGX-NNDJ":<br>          - link "multiqc_bclconvert_bylane.txt":<br>            - /url: /records/M-DGX-NNDJ<br>          - generic: M-DGX-NNDJ<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNBP multiqc.parquet M-DGX-NNBP object — 9/9/2026":<br>        - cell "Select M-DGX-NNBP":<br>          - checkbox "Select M-DGX-NNBP"<br>        - cell "multiqc.parquet M-DGX-NNBP":<br>          - link "multiqc.parquet":<br>            - /url: /records/M-DGX-NNBP<br>          - generic: M-DGX-NNBP<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NN9T multiqc.log M-DGX-NN9T object — 9/9/2026":<br>        - cell "Select M-DGX-NN9T":<br>          - checkbox "Select M-DGX-NN9T"<br>        - cell "multiqc.log M-DGX-NN9T":<br>          - link "multiqc.log":<br>            - /url: /records/M-DGX-NN9T<br>          - generic: M-DGX-NN9T<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NN7Y llms-full.txt M-DGX-NN7Y object — 9/9/2026":<br>        - cell "Select M-DGX-NN7Y":<br>          - checkbox "Select M-DGX-NN7Y"<br>        - cell "llms-full.txt M-DGX-NN7Y":<br>          - link "llms-full.txt":<br>            - /url: /records/M-DGX-NN7Y<br>          - generic: M-DGX-NN7Y<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-ROUTES-SEARCH-1789587221837.txt ; I1-A-ROUTES-SEARCH-1789587221837.png

### ROUTES-ARTIFACTS I1-A — PASS

- **timestamp**: 2026-09-16T19:33:53.822Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ADD<br>  - heading "Add" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Register an artifact" [level=2]<br>  - generic: What are you adding?<br>  - combobox "What are you adding?":<br>    - option "Object · one file or URL" [selected]<br>    - option "Prefix · one S3 folder or bucket"<br>    - option "Set · selected Object and Prefix EUIDs"<br>    - option "Upload · add a new file to S3"<br>  - generic: S3 URI or HTTP(S) URL<br>  - textbox "S3 URI or HTTP(S) URL"<br>  - generic: S3 keys are preserved exactly. A prefix receives one EUID; its children are not registered.<br>  - generic: Name<br>  - textbox "Name"<br>  - generic: Description<br>  - textbox "Description"<br>  - generic "Metadata"<br>  - button "Register"<br>  - complementary:<br>    - heading "One stable reference" [level=2]<br>    - paragraph: Store the Dewey EUID in your other tools. Dewey resolves the location, metadata, contents, and authorized access.<br>    - paragraph: New registrations are visible and downloadable by internal LSMC users. You can change metadata and download permissions independently.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-ROUTES-ARTIFACTS-1789587233822.txt ; I1-A-ROUTES-ARTIFACTS-1789587233822.png

### ROUTES-DAG I1-A — PASS

- **timestamp**: 2026-09-16T19:33:54.423Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts/dag?artifact_euid=M-DGX-TR3S
- **expected**: Page fully renders its expected content
- **observed**: l "terrarium-dev-media":<br>          - link "terrarium-dev-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-dev-web us-west-2":<br>        - cell "terrarium-dev-web":<br>          - link "terrarium-dev-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-media us-west-2":<br>        - cell "terrarium-prod-media":<br>          - link "terrarium-prod-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-web us-west-2":<br>        - cell "terrarium-prod-web":<br>          - link "terrarium-prod-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-dev us-west-2":<br>        - cell "terrarium-tfstate-dev":<br>          - link "terrarium-tfstate-dev":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-prod us-west-2":<br>        - cell "terrarium-tfstate-prod":<br>          - link "terrarium-tfstate-prod":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>        - cell "us-west-2"<br>      - row "ursa-us-west-2-052779-default-customer-1d8c14 us-west-2":<br>        - cell "ursa-us-west-2-052779-default-customer-1d8c14":<br>          - link "ursa-us-west-2-052779-default-customer-1d8c14":<br>            - /url: /storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F<br>        - cell "us-west-2"<br>      - row "zebra-day-cfg-us-west-2 us-west-2":<br>        - cell "zebra-day-cfg-us-west-2":<br>          - link "zebra-day-cfg-us-west-2":<br>            - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>        - cell "us-west-2"<br>  - heading "Registered locations" [level=2]<br>  - paragraph: Includes explicitly registered external buckets and shared folders.<br>  - paragraph: No registered locations available.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-ROUTES-DAG-1789587234423.txt ; I1-A-ROUTES-DAG-1789587234423.png

### ROUTES-DETAIL I1-A — PASS

- **timestamp**: 2026-09-16T19:33:54.992Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts/euid/M-DGX-TQ2W
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / RECORD<br>  - heading "hello world ü.txt" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - generic: object<br>  - code: M-DGX-TQ2W<br>  - button "Download / open"<br>  - button "Share"<br>  - button "Edit metadata"<br>  - heading "Object" [level=2]<br>  - paragraph: — · object<br>  - heading "Metadata" [level=2]<br>  - generic: "{}"<br>  - complementary:<br>    - heading "Details" [level=2]<br>    - term: EUID<br>    - definition: M-DGX-TQ2W<br>    - term: Owner<br>    - definition: johnm@lsmc.com<br>    - term: Created<br>    - definition: 9/16/2026<br>    - term: Producer<br>    - definition: dewey<br>    - term: Location<br>    - definition: s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/hello world ü.txt<br>    - link "Open S3 Browser":<br>      - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-A%2F<br>    - heading "Access" [level=2]<br>    - paragraph: Metadata visibility and download access are managed independently.<br>    - button "Manage permissions"<br>    - button "Transfer ownership"<br>    - generic "Registration lifecycle"<br>    - generic "Recent activity"<br>    - generic "Technical details"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-A-ROUTES-DETAIL-1789587234992.txt ; I1-A-ROUTES-DETAIL-1789587234992.png

### ROUTES-DOCS I1-A — REVIEW

- **timestamp**: 2026-09-16T19:33:55.236Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/docs
- **expected**: Page fully renders its expected content
- **observed**: - generic: loading
- **evidence**: I1-A-ROUTES-DOCS-1789587235236.txt ; I1-A-ROUTES-DOCS-1789587235236.png

### ROUTES-DOCS I1-A — PASS

- **timestamp**: 2026-09-16T19:34:31.445Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/docs#/EUID%20registry/resolve_api_v1_records__euid__get
- **expected**: Swagger documentation loads and operation details expand
- **observed**: Dewey10.0.5 OAS3.1 rendered; GET record schema expanded. No API mutation submitted.
- **evidence**: I1-A-ROUTES-DOCS-1789587271445.txt ; I1-A-ROUTES-DOCS-1789587271445.png

### TAP-OBJECT I1-A — PASS

- **timestamp**: 2026-09-16T19:34:32.400Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S
- **expected**: Page fully renders its expected content
- **observed**: l "None"<br>        - cell "None"<br>      - row:<br>        - cell "2026-09-16 19:22:56.089561+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "json_addl"<br>        - 'cell "{\"key\": \"gui-audit/20260916T183133Z/I1-A/\", \"bucket\": \"lsmc-dewey-0\", \"metadata\": {}, \"audit_log\": [], \"checksums\": {}, \"node_kind\": \"folder\", \"created_at\": \"2026-09-16T19:22:56.132748Z\", \"properties\": {}, \"source_uri\": \"s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/\", \"version_id\": null, \"description\": \"Retained synthetic prefix for GUI audit\", \"import_mode\": \"register\", \"is_terminal\": false, \"storage_uri\": \"s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/\", \"storage_kind\": \"prefix\", \"action_groups\": {}, \"artifact_type\": \"prefix\", \"storage_status\": \"registered\", \"producer_system\": \"dewey\", \"storage_backend\": \"s3\", \"created_by_email\": \"johnm@lsmc.com\", \"updated_by_email\": \"johnm@lsmc.com\", \"original_filename\": \"Dewey GUI audit 20260916 I1-A prefix\", \"artifact_identity_key\": \"dewey::prefix:prefix:folder:s3:lsmc-dewey-0:gui-audit/20260916T183133Z/I1-A/::\"}"'<br>      - row "2026-09-16 19:22:56.089561+00:00 dewey UPDATE bstatus active":<br>        - cell "2026-09-16 19:22:56.089561+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "bstatus"<br>        - cell "active"<br>      - row "2026-09-16 19:22:56.089561+00:00 dewey UPDATE created_dt 2026-09-16T19:22:56.089561+00:00":<br>        - cell "2026-09-16 19:22:56.089561+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "created_dt"<br>        - cell "2026-09-16T19:22:56.089561+00:00"<br>      - row "2026-09-16 19:22:56.089561+00:00 dewey UPDATE modified_dt 2026-09-16T19:22:56.089561+00:00":<br>        - cell "2026-09-16 19:22:56.089561+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "modified_dt"<br>        - cell "2026-09-16T19:22:56.089561+00:00"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-OBJECT-1789587272400.txt ; I1-A-TAP-OBJECT-1789587272400.png

### TAP-OBJECT-JSON I1-A — PASS

- **timestamp**: 2026-09-16T19:35:24.424Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S
- **expected**: JSON editor format and compact controls operate without applying a repair
- **observed**: Editor formatting controls exercised; no persistent repair submitted.
- **evidence**: I1-A-TAP-OBJECT-JSON-1789587324424.txt

### TAP-OBJECT-MUTATIONS I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:35:24.468Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S
- **expected**: Inspect administrative setters, lineage, and repair submission without overwriting record data
- **observed**: Set Name/Status, Add Lineage and Create repair interfaces visible; Apply excluded to preserve domain-managed identity and no-overwrite boundary.
- **evidence**: I1-A-TAP-OBJECT-MUTATIONS-1789587324468.txt

### TAP-SEARCH I1-A — PASS

- **timestamp**: 2026-09-16T19:35:58.417Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-DGX-TR3S&record_type=instance&name_like=&euid_like=&category=&type=&subtype=
- **expected**: Embedded search resolves exact persisted instance
- **observed**: Instance query M-DGX-TR3S returns audit prefix.
- **evidence**: I1-A-TAP-SEARCH-1789587358417.txt

### TAP-SEARCH-TEMPLATE I1-A — PASS

- **timestamp**: 2026-09-16T19:35:58.701Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-DGX-1A&record_type=template&name_like=&euid_like=&category=&type=&subtype=
- **expected**: Template category search resolves issued template
- **observed**: Template M-DGX-1A returned.
- **evidence**: I1-A-TAP-SEARCH-TEMPLATE-1789587358701.txt

### TAP-SEARCH-LINEAGE I1-A — PASS

- **timestamp**: 2026-09-16T19:35:59.009Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-EDG-G28C&record_type=lineage&name_like=&euid_like=&category=&type=&subtype=
- **expected**: Lineage category search resolves persisted edge
- **observed**: Registry policy lineage M-EDG-G28C returned.
- **evidence**: I1-A-TAP-SEARCH-LINEAGE-1789587359009.txt

### TAP-AUDIT I1-A — PASS

- **timestamp**: 2026-09-16T19:36:26.466Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/audit?euid=M-DGX-TR3S&changed_by=dewey&operation_type=INSERT&limit=2
- **expected**: Object/actor/operation/limit filters and audit detail expand
- **observed**: M-DGX-TR3S + actor dewey + INSERT + limit2 returns one insertion; values expanded.
- **evidence**: I1-A-TAP-AUDIT-1789587386466.txt ; I1-A-TAP-AUDIT-1789587386466.png

### TAP-MERIDIAN I1-A — PASS

- **timestamp**: 2026-09-16T19:36:35.544Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TR3S&prefix=
- **expected**: Validate real persisted EUID under configured domain
- **observed**: M-DGX-TR3S reports EUID valid for M: True.
- **evidence**: I1-A-TAP-MERIDIAN-1789587395544.txt

### TAP-THEME I1-A — PASS

- **timestamp**: 2026-09-16T19:36:35.557Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TR3S&prefix=
- **expected**: Theme switch changes selected appearance
- **observed**: Dark selected and rendered; original selection restored afterward.
- **evidence**: I1-A-TAP-THEME-1789587395557.txt ; I1-A-TAP-THEME-1789587395557.png

### TAP-CONTEXT-HELP I1-A — PASS

- **timestamp**: 2026-09-16T19:36:48.175Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TR3S&prefix=
- **expected**: Context help opens and copy control responds
- **observed**: Help shows no CLI equivalent for current Meridian path; copied text inspected.
- **evidence**: I1-A-TAP-CONTEXT-HELP-1789587408175.txt

### TAP-TEMPLATES I1-A — PASS

- **timestamp**: 2026-09-16T19:36:59.154Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates?category=data
- **expected**: Template category filter preserves template metadata and controls
- **observed**: data filter displays two stored templates M-DGX-1A and M-DGX-28.
- **evidence**: I1-A-TAP-TEMPLATES-1789587419154.txt

### TAP-TEMPLATE-DOWNLOAD I1-A — PASS

- **timestamp**: 2026-09-16T19:37:35.435Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates?category=data
- **expected**: Browser completes canonical pack delivery; verify JSON file
- **observed**: Download event and /Users/jmajor/Downloads/tapdb-repository-template-pack.json verified:515bytes, SHA2567074c06f36a3fb33390673787b3a20632cf758d130dd077fa338496d46973532; retained copy I1-A-template-pack.json.
- **evidence**: I1-A-TAP-TEMPLATE-DOWNLOAD-1789587455435.txt

### TAP-INSTANCE-CREATE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:37:43.056Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/create/M-DGX-1A
- **expected**: Inspect raw template instance creation
- **observed**: Form renders name, child creation, properties JSON and Create. Submission excluded: raw administrative creation bypasses Dewey registration/storage contract.
- **evidence**: I1-A-TAP-INSTANCE-CREATE-1789587463056.txt

### TAP-TEMPLATE-VALIDATE I1-A — FAIL

- **timestamp**: 2026-09-16T19:38:07.762Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates/validate
- **expected**: Template builder validation returns structured validation outcome without saving
- **observed**: Build JSON followed by Validate navigates to Origin not allowed. No template saved. BUG D05.
- **evidence**: I1-A-TAP-TEMPLATE-VALIDATE-1789587487762.txt ; I1-A-TAP-TEMPLATE-VALIDATE-1789587487762.png

### TAP-TEMPLATE-BUILDER I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:38:07.801Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates/validate
- **expected**: Inspect template model forms without changing shared schema
- **observed**: Builder and Save reviewed; Save excluded by no model/schema changes. Read-only validation failed separately.
- **evidence**: I1-A-TAP-TEMPLATE-BUILDER-1789587487801.txt

### TAP-SEARCH-PAGINATION I1-A — PASS

- **timestamp**: 2026-09-16T19:38:48.987Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?record_type=all&limit=25&cursor=eyJraW5kIjoiaW5zdGFuY2UiLCJ1aWQiOjl9
- **expected**: Next search page produces distinct records with continuation cursor
- **observed**: Page advances from template/early instance list to later instances.
- **evidence**: I1-A-TAP-SEARCH-PAGINATION-1789587528987.txt

### TAP-OBJECT-GRAPH I1-A — PASS

- **timestamp**: 2026-09-16T19:38:49.762Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TR3S/graph
- **expected**: Page fully renders its expected content
- **observed**: s visible graph<br>    - text: M-DGX-TR3S<br>  - generic: Depth<br>  - spinbutton "Depth": "4"<br>  - generic: Maximum Nodes<br>  - spinbutton "Maximum Nodes": "1000"<br>  - generic: Maximum Edges<br>  - spinbutton "Maximum Edges": "500"<br>  - button "Load Graph"<br>  - button "Fit"<br>  - heading "🔎 Search & Find" [level=3]<br>  - generic: Fuzzy Search<br>  - textbox "Fuzzy Search":<br>    - /placeholder: Match id, name, type, subtype<br>  - generic: Find Exact EUID<br>  - textbox "Find Exact EUID":<br>    - /placeholder: Exact EUID in current graph<br>  - button "Apply Search"<br>  - button "Find"<br>  - heading "🧰 Filters" [level=3]<br>  - generic: Connected Edge Count ≤<br>  - slider "Connected Edge Count ≤": "1"<br>  - generic: "1"<br>  - generic: Relative Distance (0 = all)<br>  - slider "Relative Distance (0 = all)": "0"<br>  - generic: "0"<br>  - generic: Type Visibility<br>  - generic: Load graph to populate.<br>  - generic: Subtype Muting<br>  - generic: Load graph to populate.<br>  - heading "⚙️ Layout" [level=3]<br>  - generic: Layout Type<br>  - combobox "Layout Type":<br>    - option "Dagre (Hierarchical)" [selected]<br>    - option "CoSE (Force-directed)"<br>    - option "Breadth First"<br>    - option "Circle"<br>    - option "Grid"<br>  - heading "⌨️ Graph Gestures" [level=3]<br>  - strong: D + right click<br>  - text: ": delete node or edge"<br>  - strong: 3x left click node<br>  - text: ": child-wave glow (pink)"<br>  - strong: 3x right click node<br>  - text: ": parent-wave glow (aqua)"<br>  - strong: L + left click node<br>  - text: ": pick child, then click parent to create edge"<br>  - strong: N + left click node<br>  - text: ": neighborhood highlight"<br>  - generic: Ready.<br>  - heading "🎨 Legend" [level=3]<br>  - generic: No visible nodes.<br>  - heading "💾 Export" [level=3]<br>  - button "Save DAG" [disabled]<br>  - generic: Mermaid<br>  - generic: Load a graph to generate Mermaid.<br>  - heading "📋 Details" [level=3]<br>  - paragraph: Click a node or edge to see details<br>  - generic "Nodes and edges"<br>  - generic "Payload JSON"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-TAP-OBJECT-GRAPH-1789587529762.txt ; I1-A-TAP-OBJECT-GRAPH-1789587529762.png

### TAP-OBJECT-GRAPH I1-A — PASS

- **timestamp**: 2026-09-16T19:39:20.040Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S
- **expected**: Object graph loads persisted lineage around fixture
- **observed**: Automatic graph load completed:6 nodes and5 edges, correct prefix/set/policy identities.
- **evidence**: I1-A-TAP-OBJECT-GRAPH-1789587560040.txt ; I1-A-TAP-OBJECT-GRAPH-1789587560040.png

### TAP-GRAPH-CONTROLS I1-A — PASS

- **timestamp**: 2026-09-16T19:39:21.856Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S
- **expected**: Search, find, center, visibility, distance, layout and fit controls operate
- **observed**: Fixture graph searched/found; registry_policy toggled off/on; distance adjusted/restored; Grid layout and Fit applied.
- **evidence**: I1-A-TAP-GRAPH-CONTROLS-1789587561856.txt ; I1-A-TAP-GRAPH-CONTROLS-1789587561856.png

### TAP-GRAPH-EXPORT I1-A — PASS

- **timestamp**: 2026-09-16T19:40:20.759Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S
- **expected**: Save DAG delivers parseable graph snapshot
- **observed**: Browser Save DAG produced 7693byte JSON,6nodes5edges, SHA256a016ba33bfdc55d18702859ee89ceb028561e5ec6b6101e47f440643ecd7030e. Retained I1-A-dag-export.json. Blob download event was not emitted by tool but delivered file verified.
- **evidence**: I1-A-TAP-GRAPH-EXPORT-1789587620759.txt

### TAP-GRAPH-MUTATIONS I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:40:20.797Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TR3S
- **expected**: Inspect mutation gestures without deletion or model changes
- **observed**: D+rightclick delete and L+click edge creation documented; neither invoked.
- **evidence**: I1-A-TAP-GRAPH-MUTATIONS-1789587620797.txt

### LIT-PAGE-NEXT I1-A — PASS

- **timestamp**: 2026-09-16T19:40:35.256Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=genomics&page=2
- **expected**: Next page returns distinct PubMed results
- **observed**: genomics page2 loaded with new PMID rows, including36471243 and38784399.
- **evidence**: I1-A-LIT-PAGE-NEXT-1789587635256.txt

### ADMIN-ANOMALY-DETAIL I1-A — PASS

- **timestamp**: 2026-09-16T19:40:38.657Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/anomalies/M-DGX-9RJX
- **expected**: Page fully renders its expected content
- **observed**: - generic: DAY<br>- banner:<br>  - generic: Dewey Operator Console<br>  - heading "Anomaly Detail" [level=1]<br>  - generic: johnm@lsmc.com<br>  - link "Back to Anomalies":<br>    - /url: /ui/anomalies<br>  - link "Dashboard":<br>    - /url: /ui<br>  - link "Observability":<br>    - /url: /ui/observability<br>  - button "Logout"<br>- main:<br>  - generic: Local anomaly record<br>  - heading "Artifact storage review is pending" [level=2]<br>  - paragraph: This local anomaly record tracks artifacts that need a storage verification review.<br>  - generic: high severity<br>  - heading "Record" [level=3]<br>  - generic: Immutable local anomaly metadata.<br>  - text: ID<br>  - generic: M-DGX-9RJX<br>  - text: Category<br>  - generic: storage<br>  - text: Status<br>  - generic: open<br>  - text: Source<br>  - generic: storage<br>  - text: Source View<br>  - generic: /ui/anomalies/M-DGX-9RJX<br>  - heading "Operational Context" [level=3]<br>  - generic: Redacted fields are kept local and read-only.<br>  - generic: First seen 2026-05-20T09:40:36.224133Z<br>  - generic: Last seen 2026-05-20T09:40:36.224133Z<br>  - generic: Occurrences 1<br>  - generic: Inspect storage verification and retention status for recent artifacts.<br>  - generic: "{ \"scope\": \"local demo record\" }"<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-A-ADMIN-ANOMALY-DETAIL-1789587638657.txt ; I1-A-ADMIN-ANOMALY-DETAIL-1789587638657.png

### BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2 I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:32:21.592Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-qeo-day-analytical-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: Explicit S3 ListBucket deny in bucket policy. Root GUI displayed the denial; no bypass attempted. Same-attempt evidence classification corrected from REVIEW.
- **evidence**: I1-A-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789587141592.txt ; I1-A-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789587141592.png

### LIT-EMPTY I1-A — PASS

- **timestamp**: 2026-09-16T19:42:20.919Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=deweyguiauditnomatch20260916zz&page=1
- **expected**: Nonmatching PubMed query displays explicit empty state
- **observed**: Query deweyguiauditnomatch20260916zz submitted; resulting DOM retained.
- **evidence**: I1-A-LIT-EMPTY-1789587740919.txt

### STORE-PAGE-NEXT I1-A — PASS

- **timestamp**: 2026-09-16T19:42:26.755Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F&token=[REDACTED]
- **expected**: Storage continuation loads bounded second page
- **observed**: Next page changed continuation-token URL and displayed next100 root objects.
- **evidence**: I1-A-STORE-PAGE-NEXT-1789587746755.txt ; I1-A-STORE-PAGE-NEXT-1789587746755.png

### ACCOUNT-TOKEN-REVOKE I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:42:45.099Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Inspect available token revocation without executing
- **observed**: Account has no personal tokens, so no active Revoke row exists; revocation execution explicitly excluded.
- **evidence**: I1-A-ACCOUNT-TOKEN-REVOKE-1789587765099.txt

### ACCOUNT-TOKEN-CREATE I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:42:45.103Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Issue only after required action-time confirmation
- **observed**: Prepared READ_ONLY1day token form in tab1; confirmation remains pending, no credential issued.
- **evidence**: I1-A-ACCOUNT-TOKEN-CREATE-1789587765103.txt

### STORE-ABORT I1-A — EXCLUDED

- **timestamp**: 2026-09-16T19:43:07.664Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Retain every upload; never abort
- **observed**: Upload abort execution excluded by explicit no-abort instruction. All attempted I1-A uploads completed; no active operation retained for interactive abort inspection.
- **evidence**: I1-A-STORE-ABORT-1789587787664.txt

### LOGIN-LOGOUT I1-A — PASS

- **timestamp**: 2026-09-16T19:43:21.704Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/login
- **expected**: Signed-out protected record redirects to login
- **observed**: After Sign out, navigating to retained record displays login and return path.
- **evidence**: I1-A-LOGIN-LOGOUT-1789587801704.txt ; I1-A-LOGIN-LOGOUT-1789587801704.png

### LOGIN-LOGIN I1-A — PASS

- **timestamp**: 2026-09-16T19:44:37.887Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Existing authorized Google account signs in through shared login
- **observed**: Google flow returned authenticated Library as johnm@lsmc.com.
- **evidence**: I1-A-LOGIN-LOGIN-1789587877887.txt ; I1-A-LOGIN-LOGIN-1789587877887.png

### LOGIN-RETURN I1-A — FAIL

- **timestamp**: 2026-09-16T19:44:37.973Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Login after protected record navigation returns to requested record
- **observed**: Signed-out request /records/M-DGX-TQ2W redirected to /login without next; successful login returned /ui instead. BUG D06.
- **evidence**: I1-A-LOGIN-RETURN-1789587877973.txt

### LOGIN-SIGNUP I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:44:37.984Z
- **version**: 10.0.5
- **role**: Unauthenticated signup
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: Approved I1-A alias entered; password and submit handed off to user under browser credential policy.
- **expected**: Signup form and email input render
- **observed**: Approved I1-A alias entered; password and submit handed off to user under browser credential policy.
- **evidence**: I1-A-LOGIN-SIGNUP-1789587877984.txt

### LOGIN-SIGNUP-COMPLETE I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:44:37.988Z
- **version**: 10.0.5
- **role**: Unauthenticated signup
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: Required user password entry/submission remains pending. No password entered by agent.
- **expected**: Complete approved alias signup and email verification
- **observed**: Required user password entry/submission remains pending. No password entered by agent.
- **evidence**: I1-A-LOGIN-SIGNUP-COMPLETE-1789587877988.txt

### SHARE-RECIPIENT I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:44:37.992Z
- **version**: 10.0.5
- **role**: Unauthenticated signup
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: Alias signup is awaiting user password handoff; independent recipient role unavailable.
- **expected**: Approved alias authenticates and opens fixture share
- **observed**: Alias signup is awaiting user password handoff; independent recipient role unavailable.
- **evidence**: I1-A-SHARE-RECIPIENT-1789587877992.txt

### SHARE-INVITE I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:46:16.396Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TQZ1
- **inputs**: Shared login accepted operation M-DGX-TR1X, but two Gmail searches including spam/trash found no message for I1-A alias. Mailbox identity johnm@lsmc.com confirmed. Delivery remains unverified.
- **expected**: Invitation is delivered to approved mailbox
- **observed**: Shared login accepted operation M-DGX-TR1X, but two Gmail searches including spam/trash found no message for I1-A alias. Mailbox identity johnm@lsmc.com confirmed. Delivery remains unverified.
- **evidence**: I1-A-SHARE-INVITE-1789587976396.txt

### TAP-PACK-INVENTORY I1-A — BLOCKED

- **timestamp**: 2026-09-16T19:46:16.736Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates
- **inputs**: Repository path field present; no verified deployed repository pack path provided by UI. No guessed path or service-side discovery used.
- **expected**: Inspect an explicit existing repository pack through GUI
- **observed**: Repository path field present; no verified deployed repository pack path provided by UI. No guessed path or service-side discovery used.
- **evidence**: I1-A-TAP-PACK-INVENTORY-1789587976736.txt

### TAP-PACK-EXPORT I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:46:16.753Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates
- **inputs**: Explicit absolute-path export and immutable receipt interface inspected; server-side submission excluded, browser canonical download tested separately.
- **expected**: Inspect server-side export without overwriting or unapproved server fixtures
- **observed**: Explicit absolute-path export and immutable receipt interface inspected; server-side submission excluded, browser canonical download tested separately.
- **evidence**: I1-A-TAP-PACK-EXPORT-1789587976753.txt

### TAP-BACKUP-MUTATIONS I1-A — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:46:17.056Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/backups
- **inputs**: Backup class/note/source-contract/recovery-family controls inspected. No backup creation, restore, purge or shared configuration mutation submitted.
- **expected**: Inspect backup/restore/purge interfaces without global or data changes
- **observed**: Backup class/note/source-contract/recovery-family controls inspected. No backup creation, restore, purge or shared configuration mutation submitted.
- **evidence**: I1-A-TAP-BACKUP-MUTATIONS-1789587977056.txt

### STORE-BUCKETS I1-B — PASS

- **timestamp**: 2026-09-16T19:46:46.995Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage
- **inputs**: All60 server-visible buckets render; registered external locations currently empty.
- **expected**: Bucket and registered-location listing renders
- **observed**: All60 server-visible buckets render; registered external locations currently empty.
- **evidence**: I1-B-STORE-BUCKETS-1789588006995.txt

### STORE-URI I1-B — PASS

- **timestamp**: 2026-09-16T19:46:50.057Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: I1-B URI preserved exactly.
- **expected**: Exact new iteration prefix opens unchanged
- **observed**: I1-B URI preserved exactly.
- **evidence**: I1-B-STORE-URI-1789588010057.txt

### STORE-EMPTY I1-B — PASS

- **timestamp**: 2026-09-16T19:46:50.062Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: No matching items at previously unused I1-B prefix.
- **expected**: New fixture prefix is empty before writes
- **observed**: No matching items at previously unused I1-B prefix.
- **evidence**: I1-B-STORE-EMPTY-1789588010062.txt ; I1-B-STORE-EMPTY-1789588010062.png

### STORE-ABORT I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:47:02.875Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: Abort upload visible during active fixture upload; not clicked.
- **expected**: Inspect active abort control without activation
- **observed**: Abort upload visible during active fixture upload; not clicked.
- **evidence**: I1-B-STORE-ABORT-1789588022875.txt

### LIB-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T19:47:03.684Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Page fully renders its expected content
- **observed**: ds/M-DGX-NNQX<br>          - generic: M-DGX-NNQX<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNN1 multiqc_software_versions.txt M-DGX-NNN1 object — 9/9/2026":<br>        - cell "Select M-DGX-NNN1":<br>          - checkbox "Select M-DGX-NNN1"<br>        - cell "multiqc_software_versions.txt M-DGX-NNN1":<br>          - link "multiqc_software_versions.txt":<br>            - /url: /records/M-DGX-NNN1<br>          - generic: M-DGX-NNN1<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNK5 multiqc_illumina_run_qc_summary.txt M-DGX-NNK5 object — 9/9/2026":<br>        - cell "Select M-DGX-NNK5":<br>          - checkbox "Select M-DGX-NNK5"<br>        - cell "multiqc_illumina_run_qc_summary.txt M-DGX-NNK5":<br>          - link "multiqc_illumina_run_qc_summary.txt":<br>            - /url: /records/M-DGX-NNK5<br>          - generic: M-DGX-NNK5<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNH9 multiqc_citations.txt M-DGX-NNH9 object — 9/9/2026":<br>        - cell "Select M-DGX-NNH9":<br>          - checkbox "Select M-DGX-NNH9"<br>        - cell "multiqc_citations.txt M-DGX-NNH9":<br>          - link "multiqc_citations.txt":<br>            - /url: /records/M-DGX-NNH9<br>          - generic: M-DGX-NNH9<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>      - row "Select M-DGX-NNFE multiqc_bclconvert_bysample.txt M-DGX-NNFE object — 9/9/2026":<br>        - cell "Select M-DGX-NNFE":<br>          - checkbox "Select M-DGX-NNFE"<br>        - cell "multiqc_bclconvert_bysample.txt M-DGX-NNFE":<br>          - link "multiqc_bclconvert_bysample.txt":<br>            - /url: /records/M-DGX-NNFE<br>          - generic: M-DGX-NNFE<br>        - cell "object":<br>          - generic: object<br>        - cell "—"<br>        - cell "9/9/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-LIB-PAGE-1789588023684.txt ; I1-B-LIB-PAGE-1789588023684.png

### SET-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T19:47:04.634Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets
- **expected**: Page fully renders its expected content
- **observed**:        - cell "9"<br>        - cell "7/4/2026"<br>      - row "analysis_artifact_set:M-RGX-B10A M-DGX-ASMP 11 7/4/2026":<br>        - cell "analysis_artifact_set:M-RGX-B10A M-DGX-ASMP":<br>          - link "analysis_artifact_set:M-RGX-B10A":<br>            - /url: /records/M-DGX-ASMP<br>          - generic: M-DGX-ASMP<br>        - cell "11"<br>        - cell "7/4/2026"<br>      - row "multiqc_artifact_set:M-RGX-B07X:run_qc_illumina M-DGX-ARV9 9 7/4/2026":<br>        - cell "multiqc_artifact_set:M-RGX-B07X:run_qc_illumina M-DGX-ARV9":<br>          - link "multiqc_artifact_set:M-RGX-B07X:run_qc_illumina":<br>            - /url: /records/M-DGX-ARV9<br>          - generic: M-DGX-ARV9<br>        - cell "9"<br>        - cell "7/4/2026"<br>      - row "analysis_artifact_set:M-RGX-B07X M-DGX-ARC8 11 7/4/2026":<br>        - cell "analysis_artifact_set:M-RGX-B07X M-DGX-ARC8":<br>          - link "analysis_artifact_set:M-RGX-B07X":<br>            - /url: /records/M-DGX-ARC8<br>          - generic: M-DGX-ARC8<br>        - cell "11"<br>        - cell "7/4/2026"<br>      - row "multiqc_artifact_set:M-RGX-AZFG:run_qc_illumina M-DGX-AQKT 9 7/4/2026":<br>        - cell "multiqc_artifact_set:M-RGX-AZFG:run_qc_illumina M-DGX-AQKT":<br>          - link "multiqc_artifact_set:M-RGX-AZFG:run_qc_illumina":<br>            - /url: /records/M-DGX-AQKT<br>          - generic: M-DGX-AQKT<br>        - cell "9"<br>        - cell "7/4/2026"<br>      - row "analysis_artifact_set:M-RGX-AZFG M-DGX-AQF3 11 7/4/2026":<br>        - cell "analysis_artifact_set:M-RGX-AZFG M-DGX-AQF3":<br>          - link "analysis_artifact_set:M-RGX-AZFG":<br>            - /url: /records/M-DGX-AQF3<br>          - generic: M-DGX-AQF3<br>        - cell "11"<br>        - cell "7/4/2026"<br>      - row "analysis_artifact_set:M-RGX-AZFG M-DGX-AQ01 11 7/4/2026":<br>        - cell "analysis_artifact_set:M-RGX-AZFG M-DGX-AQ01":<br>          - link "analysis_artifact_set:M-RGX-AZFG":<br>            - /url: /records/M-DGX-AQ01<br>          - generic: M-DGX-AQ01<br>        - cell "11"<br>        - cell "7/4/2026"<br>  - generic: Page 1 · 25 per page<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-SET-PAGE-1789588024634.txt ; I1-B-SET-PAGE-1789588024634.png

### SHARE-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T19:47:05.311Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares
- **expected**: Page fully renders its expected content
- **observed**:     - cell "—"<br>      - row "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z M-DGX-K41Z — johnm@lsmc.com revoked 7/14/2026 johnm@lsmc.com —":<br>        - cell "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z M-DGX-K41Z":<br>          - link "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z":<br>            - /url: /shares/M-DGX-K41Z<br>          - generic: M-DGX-K41Z<br>        - cell "— johnm@lsmc.com":<br>          - text: —<br>          - generic: johnm@lsmc.com<br>        - cell "revoked":<br>          - generic: revoked<br>        - cell "7/14/2026"<br>        - cell "johnm@lsmc.com"<br>        - cell "—"<br>      - row "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z M-DGX-K3Z3 — johnm@lsmc.com revoked 7/14/2026 johnm@lsmc.com —":<br>        - cell "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z M-DGX-K3Z3":<br>          - link "Dewey production delivery acceptance dewey-prod-share-20260714T225631Z":<br>            - /url: /shares/M-DGX-K3Z3<br>          - generic: M-DGX-K3Z3<br>        - cell "— johnm@lsmc.com":<br>          - text: —<br>          - generic: johnm@lsmc.com<br>        - cell "revoked":<br>          - generic: revoked<br>        - cell "7/14/2026"<br>        - cell "johnm@lsmc.com"<br>        - cell "—"<br>      - row "Dewey production delivery acceptance dewey-prod-share-20260714T223433Z M-DGX-K3X7 — johnm@lsmc.com revoked 7/14/2026 johnm@lsmc.com 7/14/2026":<br>        - cell "Dewey production delivery acceptance dewey-prod-share-20260714T223433Z M-DGX-K3X7":<br>          - link "Dewey production delivery acceptance dewey-prod-share-20260714T223433Z":<br>            - /url: /shares/M-DGX-K3X7<br>          - generic: M-DGX-K3X7<br>        - cell "— johnm@lsmc.com":<br>          - text: —<br>          - generic: johnm@lsmc.com<br>        - cell "revoked":<br>          - generic: revoked<br>        - cell "7/14/2026"<br>        - cell "johnm@lsmc.com"<br>        - cell "7/14/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-SHARE-PAGE-1789588025311.txt ; I1-B-SHARE-PAGE-1789588025311.png

### LIT-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T19:47:05.667Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / LITERATURE<br>  - heading "Literature" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Search PubMed" [level=2]<br>  - searchbox "PubMed query"<br>  - button "Search"<br>  - paragraph: Register papers as ordinary Dewey artifacts with a PMID and rich metadata.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-LIT-PAGE-1789588025667.txt ; I1-B-LIT-PAGE-1789588025667.png

### STORE-UPLOAD I1-B — PASS

- **timestamp**: 2026-09-16T19:47:46.269Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: Status5 uploaded and registered, including Unicode80byte text and17MiB file.
- **expected**: Five distinct fixture files upload and register
- **observed**: Status5 uploaded and registered, including Unicode80byte text and17MiB file.
- **evidence**: I1-B-STORE-UPLOAD-1789588066269.txt ; I1-B-STORE-UPLOAD-1789588066269.png

### STORE-UPLOAD-MULTIPART I1-B — PASS

- **timestamp**: 2026-09-16T19:47:46.296Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: multipart-17MiB.txt registered M-DGX-TS8E.
- **expected**: Bounded17MiB multipart upload completes
- **observed**: multipart-17MiB.txt registered M-DGX-TS8E.
- **evidence**: I1-B-STORE-UPLOAD-MULTIPART-1789588066296.txt

### STORE-FILTER I1-B — PASS

- **timestamp**: 2026-09-16T19:47:46.306Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: fixture query shows only fixture.json; clearing via keyboard restores list.
- **expected**: Name filter and clearing operate
- **observed**: fixture query shows only fixture.json; clearing via keyboard restores list.
- **evidence**: I1-B-STORE-FILTER-1789588066306.txt

### STORE-OBJECT I1-B — PASS

- **timestamp**: 2026-09-16T19:47:46.802Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: 64byte fixture.json details and existing EUID render.
- **expected**: ASCII JSON object details resolve exact key
- **observed**: 64byte fixture.json details and existing EUID render.
- **evidence**: I1-B-STORE-OBJECT-1789588066802.txt

### STORE-DELETE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:47:46.823Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: Object Delete and folder Delete present; excluded.
- **expected**: Inspect delete control without submission
- **observed**: Object Delete and folder Delete present; excluded.
- **evidence**: I1-B-STORE-DELETE-1789588066823.txt

### STORE-REPLACE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:47:46.848Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: Replace control present; excluded.
- **expected**: Inspect replacement without submission
- **observed**: Replace control present; excluded.
- **evidence**: I1-B-STORE-REPLACE-1789588066848.txt

### STORE-DOWNLOAD I1-B — FAIL

- **timestamp**: 2026-09-16T19:47:47.173Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: ASCII filename also returns HTTP500; D02 reproduced independently.
- **expected**: Deliver synthetic JSON bytes
- **observed**: ASCII filename also returns HTTP500; D02 reproduced independently.
- **evidence**: I1-B-STORE-DOWNLOAD-1789588067173.txt ; I1-B-STORE-DOWNLOAD-1789588067173.png

### STORE-SET I1-B — PASS

- **timestamp**: 2026-09-16T19:47:49.605Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Created M-DGX-TSE2 with2members.
- **expected**: Storage selection creates retained set
- **observed**: Created M-DGX-TSE2 with2members.
- **evidence**: I1-B-STORE-SET-1789588069605.txt

### RECORD-SET I1-B — PASS

- **timestamp**: 2026-09-16T19:47:49.610Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: fixture.json/index.html retained as two members.
- **expected**: Set details render correct members
- **observed**: fixture.json/index.html retained as two members.
- **evidence**: I1-B-RECORD-SET-1789588069610.txt

### RECORD-MEMBER-REMOVE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:48:42.326Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Two Remove controls visible; neither activated.
- **expected**: Inspect member removal without execution
- **observed**: Two Remove controls visible; neither activated.
- **evidence**: I1-B-RECORD-MEMBER-REMOVE-1789588122326.txt

### RECORD-MEMBER-ADD I1-B — PASS

- **timestamp**: 2026-09-16T19:48:43.138Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Text fixture added to I1-B set; now3visible.
- **expected**: Add one synthetic member without removing existing members
- **observed**: Text fixture added to I1-B set; now3visible.
- **evidence**: I1-B-RECORD-MEMBER-ADD-1789588123138.txt

### RECORD-EDIT I1-B — PASS

- **timestamp**: 2026-09-16T19:48:43.956Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Nested gui_audit data and description displayed after save.
- **expected**: Add fixture metadata and description
- **observed**: Nested gui_audit data and description displayed after save.
- **evidence**: I1-B-RECORD-EDIT-1789588123956.txt

### RECORD-PERMISSIONS I1-B — PASS

- **timestamp**: 2026-09-16T19:48:45.399Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Reloaded permission form inspected for I1-B alias.
- **expected**: Add approved alias while preserving existing audiences
- **observed**: Reloaded permission form inspected for I1-B alias.
- **evidence**: I1-B-RECORD-PERMISSIONS-1789588125399.txt

### RECORD-OWNER I1-B — PASS

- **timestamp**: 2026-09-16T19:48:47.292Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Owner now I1-B alias and admin still accesses set.
- **expected**: Transfer fixture to approved account with existing grants retained
- **observed**: Owner now I1-B alias and admin still accesses set.
- **evidence**: I1-B-RECORD-OWNER-1789588127292.txt

### RECORD-ACTIVITY I1-B — PASS

- **timestamp**: 2026-09-16T19:48:47.821Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Metadata, permission and ownership receipts displayed.
- **expected**: Activity reflects completed changes
- **observed**: Metadata, permission and ownership receipts displayed.
- **evidence**: I1-B-RECORD-ACTIVITY-1789588127821.txt

### RECORD-ARCHIVE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:48:47.826Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Archive registration control visible, excluded.
- **expected**: Inspect lifecycle without archive
- **observed**: Archive registration control visible, excluded.
- **evidence**: I1-B-RECORD-ARCHIVE-1789588127826.txt

### RECORD-MANIFEST I1-B — FAIL

- **timestamp**: 2026-09-16T19:48:48.098Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Second independent set reproduces HTTP500; D02.
- **expected**: Set access manifest delivers valid JSON
- **observed**: Second independent set reproduces HTTP500; D02.
- **evidence**: I1-B-RECORD-MANIFEST-1789588128098.txt

### SHARE-CREATE I1-B — PASS

- **timestamp**: 2026-09-16T19:49:37.523Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: Created M-DGX-TSNK with1day lifetime.
- **expected**: Create recipients-only share for approved I1-B account
- **observed**: Created M-DGX-TSNK with1day lifetime.
- **evidence**: I1-B-SHARE-CREATE-1789588177523.txt

### SHARE-DETAIL I1-B — PASS

- **timestamp**: 2026-09-16T19:49:37.532Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: Active fixture share displays intended alias and expiry.
- **expected**: Share detail shows target/policy/expiry/activity
- **observed**: Active fixture share displays intended alias and expiry.
- **evidence**: I1-B-SHARE-DETAIL-1789588177532.txt

### SHARE-REVOKE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T19:49:37.537Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: Revoke control displayed; excluded.
- **expected**: Inspect revocation without action
- **observed**: Revoke control displayed; excluded.
- **evidence**: I1-B-SHARE-REVOKE-1789588177537.txt

### SHARE-COPY I1-B — PASS

- **timestamp**: 2026-09-16T19:49:37.804Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: Clipboard checked against current share URL.
- **expected**: Copy exact fixture share URL
- **observed**: Clipboard checked against current share URL.
- **evidence**: I1-B-SHARE-COPY-1789588177804.txt

### SHARE-EDIT I1-B — PASS

- **timestamp**: 2026-09-16T19:50:21.596Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: Both I1 aliases persisted in normalized alphabetical order.
- **expected**: Add approved second alias without removing first
- **observed**: Both I1 aliases persisted in normalized alphabetical order.
- **evidence**: I1-B-SHARE-EDIT-1789588221596.txt

### SHARE-INVITE I1-B — REVIEW

- **timestamp**: 2026-09-16T19:50:22.478Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: GUI accepted I1-B invitation; mailbox delivery verification pending.
- **expected**: Approved mailbox receives login invitation
- **observed**: GUI accepted I1-B invitation; mailbox delivery verification pending.
- **evidence**: I1-B-SHARE-INVITE-1789588222478.txt

### SHARE-OPEN I1-B — PASS

- **timestamp**: 2026-09-16T19:50:22.975Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSE2
- **inputs**: Opened M-DGX-TSE2 with3members.
- **expected**: Target link resolves intended set
- **observed**: Opened M-DGX-TSE2 with3members.
- **evidence**: I1-B-SHARE-OPEN-1789588222975.txt

### RECORD-OBJECT I1-B — PASS

- **timestamp**: 2026-09-16T19:50:23.423Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRRE
- **inputs**: I1-B Unicode text record renders exact S3 key.
- **expected**: Object identity/owner/storage location render
- **observed**: I1-B Unicode text record renders exact S3 key.
- **evidence**: I1-B-RECORD-OBJECT-1789588223423.txt

### RECORD-DOWNLOAD I1-B — FAIL

- **timestamp**: 2026-09-16T19:50:23.802Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRRE
- **inputs**: I1-B text record returns HTTP500; D02.
- **expected**: Registered object browser download completes
- **observed**: I1-B text record returns HTTP500; D02.
- **evidence**: I1-B-RECORD-DOWNLOAD-1789588223802.txt

### RECORD-PREVIEW I1-B — PASS

- **timestamp**: 2026-09-16T19:50:27.769Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TS0Y
- **inputs**: Isolated report heading and blue square render for I1-B.
- **expected**: HTML preview loads fixture and relative asset
- **observed**: Isolated report heading and blue square render for I1-B.
- **evidence**: I1-B-RECORD-PREVIEW-1789588227769.txt ; I1-B-RECORD-PREVIEW-1789588227769.png

### ADD-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T19:50:29.515Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add?kind=prefix&uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F
- **inputs**: Register prefix form prepopulated for I1-B.
- **expected**: Add form loads exact storage prefix context
- **observed**: Register prefix form prepopulated for I1-B.
- **evidence**: I1-B-ADD-PAGE-1789588229515.txt

### ADD-PREFIX I1-B — PASS

- **timestamp**: 2026-09-16T19:50:30.363Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TST9
- **inputs**: Created M-DGX-TST9.
- **expected**: Register one exact prefix
- **observed**: Created M-DGX-TST9.
- **evidence**: I1-B-ADD-PREFIX-1789588230363.txt

### STORE-REGISTER I1-B — PASS

- **timestamp**: 2026-09-16T19:50:30.371Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TST9
- **inputs**: Register this folder created one prefix identity.
- **expected**: Storage registration link preserves exact URI
- **observed**: Register this folder created one prefix identity.
- **evidence**: I1-B-STORE-REGISTER-1789588230371.txt

### RECORD-PREFIX I1-B — PASS

- **timestamp**: 2026-09-16T19:50:30.376Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TST9
- **inputs**: Five synthetic objects displayed with registration links.
- **expected**: Prefix shows bounded child listing
- **observed**: Five synthetic objects displayed with registration links.
- **evidence**: I1-B-RECORD-PREFIX-1789588230376.txt ; I1-B-RECORD-PREFIX-1789588230376.png

### ADD-VALIDATION I1-B — PASS

- **timestamp**: 2026-09-16T19:51:10.524Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **inputs**: Malformed JSON brace rejected visibly before request.
- **expected**: Malformed metadata JSON is rejected without registration
- **observed**: Malformed JSON brace rejected visibly before request.
- **evidence**: I1-B-ADD-VALIDATION-1789588270524.txt

### ADD-OBJECT I1-B — PASS

- **timestamp**: 2026-09-16T19:51:11.130Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRRE
- **inputs**: Resolved M-DGX-TRRE from exact uploaded key.
- **expected**: Exact object registration resolves retained identity
- **observed**: Resolved M-DGX-TRRE from exact uploaded key.
- **evidence**: I1-B-ADD-OBJECT-1789588271130.txt

### ADD-DUPLICATE I1-B — PASS

- **timestamp**: 2026-09-16T19:51:11.136Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRRE
- **inputs**: EUID remained M-DGX-TRRE.
- **expected**: Repeated registration reuses identity without storage write
- **observed**: EUID remained M-DGX-TRRE.
- **evidence**: I1-B-ADD-DUPLICATE-1789588271136.txt

### ADD-URL I1-B — PASS

- **timestamp**: 2026-09-16T19:51:13.144Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSY1
- **inputs**: Created M-DGX-TSY1 for synthetic example.com URL.
- **expected**: HTTP reference registers as object
- **observed**: Created M-DGX-TSY1 for synthetic example.com URL.
- **evidence**: I1-B-ADD-URL-1789588273144.txt

### ADD-METADATA I1-B — PASS

- **timestamp**: 2026-09-16T19:51:13.150Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TSY1
- **inputs**: audit_attempt I1-B retained on URL object.
- **expected**: Key/value editor persists metadata JSON
- **observed**: audit_attempt I1-B retained on URL object.
- **evidence**: I1-B-ADD-METADATA-1789588273150.txt

### ADD-UPLOAD-MODE I1-B — FAIL

- **timestamp**: 2026-09-16T19:51:13.491Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **inputs**: Second Add modal reproduces duplicate uri id and unnamed destination textbox; D04.
- **expected**: Upload destination has independent accessible label
- **observed**: Second Add modal reproduces duplicate uri id and unnamed destination textbox; D04.
- **evidence**: I1-B-ADD-UPLOAD-MODE-1789588273491.txt ; I1-B-ADD-UPLOAD-MODE-1789588273491.png

### ADD-UPLOAD-EXEC I1-B — PASS

- **timestamp**: 2026-09-16T19:52:07.765Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add
- **inputs**: I1-B/nested/fixture.json uploaded; status1file uploaded.
- **expected**: Add upload completes to unused nested path without auto-registration
- **observed**: I1-B/nested/fixture.json uploaded; status1file uploaded.
- **evidence**: I1-B-ADD-UPLOAD-EXEC-1789588327765.txt

### LIB-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T19:52:11.761Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=I1-B&sort=created_at&page=1
- **inputs**: I1-B query returns8 current fixture records.
- **expected**: Search returns matching records
- **observed**: I1-B query returns8 current fixture records.
- **evidence**: I1-B-LIB-SEARCH-1789588331761.txt

### LIB-KIND I1-B — PASS

- **timestamp**: 2026-09-16T19:52:14.802Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=I1-B&sort=created_at&page=1&kind=object
- **inputs**: I1-B plus Objects returns6objects.
- **expected**: Objects filter excludes prefix/set
- **observed**: I1-B plus Objects returns6objects.
- **evidence**: I1-B-LIB-KIND-1789588334802.txt

### LIB-SORT I1-B — PASS

- **timestamp**: 2026-09-16T19:52:17.853Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=I1-B&sort=name&page=1
- **inputs**: Alphabetic result ordering checked in retained DOM.
- **expected**: Name sorting orders fixture result names
- **observed**: Alphabetic result ordering checked in retained DOM.
- **evidence**: I1-B-LIB-SORT-1789588337853.txt

### LIB-SELECT I1-B — PASS

- **timestamp**: 2026-09-16T19:52:18.739Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/add?kind=set&members=M-DGX-TST9%0AM-DGX-TSY1
- **inputs**: Selected prefix and URL EUIDs retained in form.
- **expected**: Selection populates Add set member field
- **observed**: Selected prefix and URL EUIDs retained in form.
- **evidence**: I1-B-LIB-SELECT-1789588338739.txt

### SET-CREATE-SELECTION I1-B — PASS

- **timestamp**: 2026-09-16T19:52:19.627Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TT2S
- **inputs**: Created M-DGX-TT2S with2members.
- **expected**: Create retained set from selected records
- **observed**: Created M-DGX-TT2S with2members.
- **evidence**: I1-B-SET-CREATE-SELECTION-1789588339627.txt

### ADD-SET I1-B — PASS

- **timestamp**: 2026-09-16T19:52:19.633Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TT2S
- **inputs**: Prefix and URL membership preserved.
- **expected**: Add set registers explicit member identities
- **observed**: Prefix and URL membership preserved.
- **evidence**: I1-B-ADD-SET-1789588339633.txt

### LIB-LOOKUP I1-B — PASS

- **timestamp**: 2026-09-16T19:52:20.127Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TRRE
- **inputs**: Opened M-DGX-TRRE.
- **expected**: Lookup navigates to exact persisted EUID
- **observed**: Opened M-DGX-TRRE.
- **evidence**: I1-B-LIB-LOOKUP-1789588340127.txt

### LIB-EMPTY I1-B — PASS

- **timestamp**: 2026-09-16T19:52:23.853Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=dewey-no-such-result-I1B-20260916&sort=created_at&page=1
- **inputs**: I1-B unique no-match query returns0.
- **expected**: Nonmatching query shows zero results
- **observed**: I1-B unique no-match query returns0.
- **evidence**: I1-B-LIB-EMPTY-1789588343853.txt

### LIB-BACK I1-B — PASS

- **timestamp**: 2026-09-16T19:52:43.878Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?q=dewey-no-such-result-I1B-20260916&sort=created_at&page=1
- **inputs**: Back restored full listing and forward restored zero-result query.
- **expected**: Back/forward preserves query state
- **observed**: Back restored full listing and forward restored zero-result query.
- **evidence**: I1-B-LIB-BACK-1789588363878.txt

### LIB-PAGE-NEXT I1-B — PASS

- **timestamp**: 2026-09-16T19:53:49.182Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=1
- **inputs**: Moved to page2 and back to page1 with new rows.
- **expected**: Next and Previous paginate
- **observed**: Moved to page2 and back to page1 with new rows.
- **evidence**: I1-B-LIB-PAGE-NEXT-1789588429182.txt

### LIB-FILTERS-INVALID I1-B — PASS

- **timestamp**: 2026-09-16T19:53:49.752Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=1
- **inputs**: {} rejected with Filters must be a JSON array.
- **expected**: Reject non-array JSON filters
- **observed**: {} rejected with Filters must be a JSON array.
- **evidence**: I1-B-LIB-FILTERS-INVALID-1789588429752.txt

### LIB-FILTERS I1-B — PASS

- **timestamp**: 2026-09-16T19:53:52.804Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui?page=1&filters=%5B%7B%22path%22%3A%22metadata.audit_attempt%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22I1-B%22%7D%5D
- **inputs**: metadata.audit_attempt eq I1-B returns URL fixture.
- **expected**: JSON metadata query selects exact matching record
- **observed**: metadata.audit_attempt eq I1-B returns URL fixture.
- **evidence**: I1-B-LIB-FILTERS-1789588432804.txt

### SET-PAGINATION I1-B — BLOCKED

- **timestamp**: 2026-09-16T19:53:53.826Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets
- **inputs**: Unfiltered set list has fewer than25records; no Next control.
- **expected**: Exercise sets next page when available
- **observed**: Unfiltered set list has fewer than25records; no Next control.
- **evidence**: I1-B-SET-PAGINATION-1789588433826.txt

### SET-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T19:53:56.881Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets?q=20260916+I1-B&sort=name&page=1
- **inputs**: Two I1-B sets displayed with2/3members.
- **expected**: Set search/name sorting matches fixtures
- **observed**: Two I1-B sets displayed with2/3members.
- **evidence**: I1-B-SET-SEARCH-1789588436881.txt

### SHARE-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T19:54:00.477Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?q=20260916+I1-B&sort=name&page=1
- **inputs**: One matching active I1-B share.
- **expected**: Share list query returns exact fixture
- **observed**: One matching active I1-B share.
- **evidence**: I1-B-SHARE-SEARCH-1789588440477.txt

### BUCKET-aquarium-tfstate-dev I1-B — PASS

- **timestamp**: 2026-09-16T19:54:38.703Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://aquarium-tfstate-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://aquarium-tfstate-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Faquarium-tfstate-dev%2F<br>  - link "aquarium-tfstate-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select aquarium/ prefix aquarium/ — Register":<br>        - cell "Select aquarium/ prefix":<br>          - checkbox "Select aquarium/"<br>          - generic: prefix<br>        - cell "aquarium/":<br>          - link "aquarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-dev%2Faquarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faquarium-tfstate-dev%2Faquarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-aquarium-tfstate-dev-1789588478703.txt ; I1-B-BUCKET-aquarium-tfstate-dev-1789588478703.png

### BUCKET-aquarium-tfstate-prod I1-B — PASS

- **timestamp**: 2026-09-16T19:54:39.225Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://aquarium-tfstate-prod/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://aquarium-tfstate-prod/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Faquarium-tfstate-prod%2F<br>  - link "aquarium-tfstate-prod":<br>    - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select aquarium/ prefix aquarium/ — Register":<br>        - cell "Select aquarium/ prefix":<br>          - checkbox "Select aquarium/"<br>          - generic: prefix<br>        - cell "aquarium/":<br>          - link "aquarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Faquarium-tfstate-prod%2Faquarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faquarium-tfstate-prod%2Faquarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-aquarium-tfstate-prod-1789588479225.txt ; I1-B-BUCKET-aquarium-tfstate-prod-1789588479225.png

### BUCKET-asterism-note-screenshots-dev I1-B — PASS

- **timestamp**: 2026-09-16T19:54:39.851Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://asterism-note-screenshots-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://asterism-note-screenshots-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F<br>  - link "asterism-note-screenshots-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select screenshots/ prefix screenshots/ — Register":<br>        - cell "Select screenshots/ prefix":<br>          - checkbox "Select screenshots/"<br>          - generic: prefix<br>        - cell "screenshots/":<br>          - link "screenshots/":<br>            - /url: /storage?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2Fscreenshots%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fasterism-note-screenshots-dev%2Fscreenshots%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-asterism-note-screenshots-dev-1789588479851.txt ; I1-B-BUCKET-asterism-note-screenshots-dev-1789588479851.png

### BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd I1-B — PASS

- **timestamp**: 2026-09-16T19:54:40.755Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F
- **expected**: Page fully renders its expected content
- **observed**: d?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F7dd32744d3ef9196115bcc7ae8c1f3b8&kind=object<br>      - row "Select 8efd1317cee2fadc175612785c606a45 object 8efd1317cee2fadc175612785c606a45 1.5K B Register":<br>        - cell "Select 8efd1317cee2fadc175612785c606a45 object":<br>          - checkbox "Select 8efd1317cee2fadc175612785c606a45"<br>          - generic: object<br>        - cell "8efd1317cee2fadc175612785c606a45":<br>          - button "8efd1317cee2fadc175612785c606a45"<br>        - cell "1.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2F8efd1317cee2fadc175612785c606a45&kind=object<br>      - row "Select bd9b5df9ed21415aabf9be3dd0bf872b object bd9b5df9ed21415aabf9be3dd0bf872b 30.7M B Register":<br>        - cell "Select bd9b5df9ed21415aabf9be3dd0bf872b object":<br>          - checkbox "Select bd9b5df9ed21415aabf9be3dd0bf872b"<br>          - generic: object<br>        - cell "bd9b5df9ed21415aabf9be3dd0bf872b":<br>          - button "bd9b5df9ed21415aabf9be3dd0bf872b"<br>        - cell "30.7M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2Fbd9b5df9ed21415aabf9be3dd0bf872b&kind=object<br>      - row "Select ed4f1d6620c05cf7bde78318883cf39a.template object ed4f1d6620c05cf7bde78318883cf39a.template 70.4K B Register":<br>        - cell "Select ed4f1d6620c05cf7bde78318883cf39a.template object":<br>          - checkbox "Select ed4f1d6620c05cf7bde78318883cf39a.template"<br>          - generic: object<br>        - cell "ed4f1d6620c05cf7bde78318883cf39a.template":<br>          - button "ed4f1d6620c05cf7bde78318883cf39a.template"<br>        - cell "70.4K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd%2Fed4f1d6620c05cf7bde78318883cf39a.template&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd-1789588480755.txt ; I1-B-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-nr7kmk76fofd-1789588480755.png

### BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp I1-B — PASS

- **timestamp**: 2026-09-16T19:54:41.719Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F
- **expected**: Page fully renders its expected content
- **observed**: l: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F5729682a35864d86a61ef536f2202235&kind=object<br>      - row "Select 6cee33cb01dfea2f15c39b110ea0f258 object 6cee33cb01dfea2f15c39b110ea0f258 2.6M B Register":<br>        - cell "Select 6cee33cb01dfea2f15c39b110ea0f258 object":<br>          - checkbox "Select 6cee33cb01dfea2f15c39b110ea0f258"<br>          - generic: object<br>        - cell "6cee33cb01dfea2f15c39b110ea0f258":<br>          - button "6cee33cb01dfea2f15c39b110ea0f258"<br>        - cell "2.6M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F6cee33cb01dfea2f15c39b110ea0f258&kind=object<br>      - row "Select 8eddd4fe4211c82df0dba27b419f973c.template object 8eddd4fe4211c82df0dba27b419f973c.template 43K B Register":<br>        - cell "Select 8eddd4fe4211c82df0dba27b419f973c.template object":<br>          - checkbox "Select 8eddd4fe4211c82df0dba27b419f973c.template"<br>          - generic: object<br>        - cell "8eddd4fe4211c82df0dba27b419f973c.template":<br>          - button "8eddd4fe4211c82df0dba27b419f973c.template"<br>        - cell "43K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2F8eddd4fe4211c82df0dba27b419f973c.template&kind=object<br>      - row "Select ef3a4230ce6d6095f06e66e48a3b1b6f object ef3a4230ce6d6095f06e66e48a3b1b6f 2.6M B Register":<br>        - cell "Select ef3a4230ce6d6095f06e66e48a3b1b6f object":<br>          - checkbox "Select ef3a4230ce6d6095f06e66e48a3b1b6f"<br>          - generic: object<br>        - cell "ef3a4230ce6d6095f06e66e48a3b1b6f":<br>          - button "ef3a4230ce6d6095f06e66e48a3b1b6f"<br>        - cell "2.6M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Faws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp%2Fef3a4230ce6d6095f06e66e48a3b1b6f&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp-1789588481719.txt ; I1-B-BUCKET-aws-sam-cli-managed-default-samclisourcebucket-wyvracmmocbp-1789588481719.png

### BUCKET-cdk-dayhoff-assets-108782052779-us-east-1 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:43.093Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: fa2fa56f26eae5115153110bb7e0539cf78ddb75aadc6d981f95d.json"<br>        - cell "7.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Feb51e3eb4bcfa2fa56f26eae5115153110bb7e0539cf78ddb75aadc6d981f95d.json&kind=object<br>      - row "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json object f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json 2.9K B Register":<br>        - cell "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json object":<br>          - checkbox "Select f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json"<br>          - generic: object<br>        - cell "f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json":<br>          - button "f13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json"<br>        - cell "2.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Ff13b101884fd1f6646d89fa9214133f31a63cc61b3b8c271b97d4106c9a1e31c.json&kind=object<br>      - row "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json object f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json 23.7K B Register":<br>        - cell "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json object":<br>          - checkbox "Select f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json"<br>          - generic: object<br>        - cell "f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json":<br>          - button "f6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json"<br>        - cell "23.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-east-1%2Ff6afb82483a6ef184feaf99acf0c496771e3df611328fb377e33aeb6a444e5d7.json&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-cdk-dayhoff-assets-108782052779-us-east-1-1789588483093.txt ; I1-B-BUCKET-cdk-dayhoff-assets-108782052779-us-east-1-1789588483093.png

### BUCKET-cdk-dayhoff-assets-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:43.650Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://cdk-dayhoff-assets-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://cdk-dayhoff-assets-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F<br>  - link "cdk-dayhoff-assets-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fcdk-dayhoff-assets-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-cdk-dayhoff-assets-108782052779-us-west-2-1789588483650.txt ; I1-B-BUCKET-cdk-dayhoff-assets-108782052779-us-west-2-1789588483650.png

### BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:46.404Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: 9db6825aa986634d739c186.json"<br>        - cell "20.2K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2cc067435f7a391f1040595805be77671d10c519d9db6825aa986634d739c186.json&kind=object<br>      - row "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json object 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json 91.7K B Register":<br>        - cell "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json object":<br>          - checkbox "Select 2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json"<br>          - generic: object<br>        - cell "2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json":<br>          - button "2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json"<br>        - cell "91.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2d2624ca46a7f375500174a167ab0f45fb39eb8907b14093bc33578f9f834679.json&kind=object<br>      - row "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml object 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml 1.5K B Register":<br>        - cell "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml object":<br>          - checkbox "Select 2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml"<br>          - generic: object<br>        - cell "2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml":<br>          - button "2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml"<br>        - cell "1.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-east-1%2F2d943508b5771af35b5f2eac6e4f39b61d9314578ab97514375baf11705fdda5.toml&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1-1789588486404.txt ; I1-B-BUCKET-cdk-hnb659fds-assets-108782052779-us-east-1-1789588486404.png

### BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:49.182Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: 036727c52f03c043c010c.json"<br>        - cell "28.6K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd225b67f6a0a086cf5077a68d81b7c2e099839700cf036727c52f03c043c010c.json&kind=object<br>      - row "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json object d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json 35.9K B Register":<br>        - cell "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json object":<br>          - checkbox "Select d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json"<br>          - generic: object<br>        - cell "d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json":<br>          - button "d38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json"<br>        - cell "35.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd38f223e9ce8d7769e4cdcf9bb2b8f54aa6fe0a03b640a2235686ced2053a19e.json&kind=object<br>      - row "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json object d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json 28.8K B Register":<br>        - cell "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json object":<br>          - checkbox "Select d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json"<br>          - generic: object<br>        - cell "d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json":<br>          - button "d4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json"<br>        - cell "28.8K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2Fd4c055f5ca24b70c7fb6bbf73d0d066156b2113c3fe7bf538c508a7042ea898f.json&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2-1789588489182.txt ; I1-B-BUCKET-cdk-hnb659fds-assets-108782052779-us-west-2-1789588489182.png

### BUCKET-cf-templates-pfrobpqqun1c-us-east-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:50.096Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F
- **expected**: Page fully renders its expected content
- **observed**: F<br>  - link "cf-templates-pfrobpqqun1c-us-east-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json object 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json 840 B Register":<br>        - cell "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json object":<br>          - checkbox "Select 2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json"<br>          - generic: object<br>        - cell "2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json":<br>          - button "2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json"<br>        - cell "840 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F2026-02-05T190657.263Z6l3-runzero-cloudformation-stackset.json&kind=object<br>      - row "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json object 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json 840 B Register":<br>        - cell "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json object":<br>          - checkbox "Select 2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json"<br>          - generic: object<br>        - cell "2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json":<br>          - button "2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json"<br>        - cell "840 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fcf-templates-pfrobpqqun1c-us-east-2%2F2026-02-05T194045.217Zdy8-runzero-cloudformation-stackset.json&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-cf-templates-pfrobpqqun1c-us-east-2-1789588490096.txt ; I1-B-BUCKET-cf-templates-pfrobpqqun1c-us-east-2-1789588490096.png

### BUCKET-dayec-cur-108782052779-us-east-1 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:50.738Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: l=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://dayec-cur-108782052779-us-east-1/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://dayec-cur-108782052779-us-east-1/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F<br>  - link "dayec-cur-108782052779-us-east-1":<br>    - /url: /storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select dayec-cur/ prefix dayec-cur/ — Register":<br>        - cell "Select dayec-cur/ prefix":<br>          - checkbox "Select dayec-cur/"<br>          - generic: prefix<br>        - cell "dayec-cur/":<br>          - link "dayec-cur/":<br>            - /url: /storage?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Fdayec-cur%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Fdayec-cur%2F&kind=prefix<br>      - row "Select aws-programmatic-access-test-object object aws-programmatic-access-test-object 4 B Register":<br>        - cell "Select aws-programmatic-access-test-object object":<br>          - checkbox "Select aws-programmatic-access-test-object"<br>          - generic: object<br>        - cell "aws-programmatic-access-test-object":<br>          - button "aws-programmatic-access-test-object"<br>        - cell "4 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fdayec-cur-108782052779-us-east-1%2Faws-programmatic-access-test-object&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-dayec-cur-108782052779-us-east-1-1789588490738.txt ; I1-B-BUCKET-dayec-cur-108782052779-us-east-1-1789588490738.png

### BUCKET-daylily-customer-lsmc-a0477268 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:51.282Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://daylily-customer-lsmc-a0477268/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://daylily-customer-lsmc-a0477268/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F<br>  - link "daylily-customer-lsmc-a0477268":<br>    - /url: /storage?uri=s3%3A%2F%2Fdaylily-customer-lsmc-a0477268%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-daylily-customer-lsmc-a0477268-1789588491282.txt ; I1-B-BUCKET-daylily-customer-lsmc-a0477268-1789588491282.png

### BUCKET-lsmc-atlas-demo I1-B — PASS

- **timestamp**: 2026-09-16T19:54:51.883Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-atlas-demo/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-atlas-demo/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-atlas-demo%2F<br>  - link "lsmc-atlas-demo":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select external-smoke/ prefix external-smoke/ — Register":<br>        - cell "Select external-smoke/ prefix":<br>          - checkbox "Select external-smoke/"<br>          - generic: prefix<br>        - cell "external-smoke/":<br>          - link "external-smoke/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-demo%2Fexternal-smoke%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-demo%2Fexternal-smoke%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-atlas-demo-1789588491883.txt ; I1-B-BUCKET-lsmc-atlas-demo-1789588491883.png

### BUCKET-lsmc-atlas-dev I1-B — PASS

- **timestamp**: 2026-09-16T19:54:53.063Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: 5b3-ba7b-a905d5605702%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fcf27f697-ec98-45b3-ba7b-a905d5605702%2F&kind=prefix<br>      - row "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/ prefix d29e45ac-5741-43b8-91bc-2b8354c32a97/ — Register":<br>        - cell "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/ prefix":<br>          - checkbox "Select d29e45ac-5741-43b8-91bc-2b8354c32a97/"<br>          - generic: prefix<br>        - cell "d29e45ac-5741-43b8-91bc-2b8354c32a97/":<br>          - link "d29e45ac-5741-43b8-91bc-2b8354c32a97/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fd29e45ac-5741-43b8-91bc-2b8354c32a97%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fd29e45ac-5741-43b8-91bc-2b8354c32a97%2F&kind=prefix<br>      - row "Select da443ab3-f2cf-426a-a061-117808042a17/ prefix da443ab3-f2cf-426a-a061-117808042a17/ — Register":<br>        - cell "Select da443ab3-f2cf-426a-a061-117808042a17/ prefix":<br>          - checkbox "Select da443ab3-f2cf-426a-a061-117808042a17/"<br>          - generic: prefix<br>        - cell "da443ab3-f2cf-426a-a061-117808042a17/":<br>          - link "da443ab3-f2cf-426a-a061-117808042a17/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fda443ab3-f2cf-426a-a061-117808042a17%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Fda443ab3-f2cf-426a-a061-117808042a17%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-atlas-dev%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-atlas-dev%2Ftmp%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-atlas-dev-1789588493063.txt ; I1-B-BUCKET-lsmc-atlas-dev-1789588493063.png

### BUCKET-lsmc-aws-config-108782052779 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:53.719Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-aws-config-108782052779/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-aws-config-108782052779/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F<br>  - link "lsmc-aws-config-108782052779":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select AWSLogs/ prefix AWSLogs/ — Register":<br>        - cell "Select AWSLogs/ prefix":<br>          - checkbox "Select AWSLogs/"<br>          - generic: prefix<br>        - cell "AWSLogs/":<br>          - link "AWSLogs/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2FAWSLogs%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-aws-config-108782052779%2FAWSLogs%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-aws-config-108782052779-1789588493719.txt ; I1-B-BUCKET-lsmc-aws-config-108782052779-1789588493719.png

### BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:54.600Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2F
- **expected**: Page fully renders its expected content
- **observed**: - button "privacy.html"<br>        - cell "5.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fprivacy.html&kind=object<br>      - row "Select robots.txt object robots.txt 66 B Register":<br>        - cell "Select robots.txt object":<br>          - checkbox "Select robots.txt"<br>          - generic: object<br>        - cell "robots.txt":<br>          - button "robots.txt"<br>        - cell "66 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Frobots.txt&kind=object<br>      - row "Select site.webmanifest object site.webmanifest 337 B Register":<br>        - cell "Select site.webmanifest object":<br>          - checkbox "Select site.webmanifest"<br>          - generic: object<br>        - cell "site.webmanifest":<br>          - button "site.webmanifest"<br>        - cell "337 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fsite.webmanifest&kind=object<br>      - row "Select sitemap.xml object sitemap.xml 258 B Register":<br>        - cell "Select sitemap.xml object":<br>          - checkbox "Select sitemap.xml"<br>          - generic: object<br>        - cell "sitemap.xml":<br>          - button "sitemap.xml"<br>        - cell "258 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Fsitemap.xml&kind=object<br>      - row "Select tos.html object tos.html 6.5K B Register":<br>        - cell "Select tos.html object":<br>          - checkbox "Select tos.html"<br>          - generic: object<br>        - cell "tos.html":<br>          - button "tos.html"<br>        - cell "6.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-bio-oauth-static-site-108782052779-us-east-1%2Ftos.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1-1789588494600.txt ; I1-B-BUCKET-lsmc-bio-oauth-static-site-108782052779-us-east-1-1789588494600.png

### BUCKET-lsmc-copy-ultimagen-lsmc-cro-316 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:55.290Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F
- **expected**: Page fully renders its expected content
- **observed**: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-copy-ultimagen-lsmc-cro-316/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-copy-ultimagen-lsmc-cro-316/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F<br>  - link "lsmc-copy-ultimagen-lsmc-cro-316":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 2025-07-25/ prefix 2025-07-25/ — Register":<br>        - cell "Select 2025-07-25/ prefix":<br>          - checkbox "Select 2025-07-25/"<br>          - generic: prefix<br>        - cell "2025-07-25/":<br>          - link "2025-07-25/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F2025-07-25%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2F2025-07-25%2F&kind=prefix<br>      - row "Select Feb27_2025_ugsb4_data/ prefix Feb27_2025_ugsb4_data/ — Register":<br>        - cell "Select Feb27_2025_ugsb4_data/ prefix":<br>          - checkbox "Select Feb27_2025_ugsb4_data/"<br>          - generic: prefix<br>        - cell "Feb27_2025_ugsb4_data/":<br>          - link "Feb27_2025_ugsb4_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2FFeb27_2025_ugsb4_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-copy-ultimagen-lsmc-cro-316%2FFeb27_2025_ugsb4_data%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-copy-ultimagen-lsmc-cro-316-1789588495290.txt ; I1-B-BUCKET-lsmc-copy-ultimagen-lsmc-cro-316-1789588495290.png

### BUCKET-lsmc-datalake-raw-dev I1-B — PASS

- **timestamp**: 2026-09-16T19:54:55.797Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-datalake-raw-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-datalake-raw-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F<br>  - link "lsmc-datalake-raw-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select raw/ prefix raw/ — Register":<br>        - cell "Select raw/ prefix":<br>          - checkbox "Select raw/"<br>          - generic: prefix<br>        - cell "raw/":<br>          - link "raw/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2Fraw%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-datalake-raw-dev%2Fraw%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-datalake-raw-dev-1789588495797.txt ; I1-B-BUCKET-lsmc-datalake-raw-dev-1789588495797.png

### BUCKET-lsmc-dayoa-analysis-results-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:56.413Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: is-results-usw2%2Fdragen%2F&kind=prefix<br>      - row "Select staging/ prefix staging/ — Register":<br>        - cell "Select staging/ prefix":<br>          - checkbox "Select staging/"<br>          - generic: prefix<br>        - cell "staging/":<br>          - link "staging/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fstaging%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fstaging%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftmp%2F&kind=prefix<br>      - row "Select transfers/ prefix transfers/ — Register":<br>        - cell "Select transfers/ prefix":<br>          - checkbox "Select transfers/"<br>          - generic: prefix<br>        - cell "transfers/":<br>          - link "transfers/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftransfers%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Ftransfers%2F&kind=prefix<br>      - row "Select validation/ prefix validation/ — Register":<br>        - cell "Select validation/ prefix":<br>          - checkbox "Select validation/"<br>          - generic: prefix<br>        - cell "validation/":<br>          - link "validation/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fvalidation%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-analysis-results-usw2%2Fvalidation%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-analysis-results-usw2-1789588496413.txt ; I1-B-BUCKET-lsmc-dayoa-analysis-results-usw2-1789588496413.png

### BUCKET-lsmc-dayoa-control-data-use1 I1-B — PASS

- **timestamp**: 2026-09-16T19:54:57.242Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2F
- **expected**: Page fully renders its expected content
- **observed**: -data-use1%2Fdayoa_source_overlays%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fdayoa_source_overlays%2F&kind=prefix<br>      - row "Select genomic_data/ prefix genomic_data/ — Register":<br>        - cell "Select genomic_data/ prefix":<br>          - checkbox "Select genomic_data/"<br>          - generic: prefix<br>        - cell "genomic_data/":<br>          - link "genomic_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fgenomic_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fgenomic_data%2F&kind=prefix<br>      - row "Select staged_external_sequencing_data/ prefix staged_external_sequencing_data/ — Register":<br>        - cell "Select staged_external_sequencing_data/ prefix":<br>          - checkbox "Select staged_external_sequencing_data/"<br>          - generic: prefix<br>        - cell "staged_external_sequencing_data/":<br>          - link "staged_external_sequencing_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fstaged_external_sequencing_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fstaged_external_sequencing_data%2F&kind=prefix<br>      - row "Select ursa-hotpatch-source/ prefix ursa-hotpatch-source/ — Register":<br>        - cell "Select ursa-hotpatch-source/ prefix":<br>          - checkbox "Select ursa-hotpatch-source/"<br>          - generic: prefix<br>        - cell "ursa-hotpatch-source/":<br>          - link "ursa-hotpatch-source/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fursa-hotpatch-source%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-use1%2Fursa-hotpatch-source%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-control-data-use1-1789588497242.txt ; I1-B-BUCKET-lsmc-dayoa-control-data-use1-1789588497242.png

### BUCKET-lsmc-dayoa-control-data-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:07.463Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**:       - cell "staged_external_sequencing_data/":<br>          - link "staged_external_sequencing_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fstaged_external_sequencing_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fstaged_external_sequencing_data%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Ftmp%2F&kind=prefix<br>      - row "Select ursa-hotpatch-source/ prefix ursa-hotpatch-source/ — Register":<br>        - cell "Select ursa-hotpatch-source/ prefix":<br>          - checkbox "Select ursa-hotpatch-source/"<br>          - generic: prefix<br>        - cell "ursa-hotpatch-source/":<br>          - link "ursa-hotpatch-source/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fursa-hotpatch-source%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fursa-hotpatch-source%2F&kind=prefix<br>      - row "Select workflow_payloads/ prefix workflow_payloads/ — Register":<br>        - cell "Select workflow_payloads/ prefix":<br>          - checkbox "Select workflow_payloads/"<br>          - generic: prefix<br>        - cell "workflow_payloads/":<br>          - link "workflow_payloads/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fworkflow_payloads%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-control-data-usw2%2Fworkflow_payloads%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-control-data-usw2-1789588747463.txt ; I1-B-BUCKET-lsmc-dayoa-control-data-usw2-1789588747463.png

### BUCKET-lsmc-dayoa-omics-analysis-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:09.401Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:        - button "ont_example.csv"<br>        - cell "5.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Font_example.csv&kind=object<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fs3_reference_data_version.info&kind=object<br>      - row "Select ultima_analysis_manifest.csv object ultima_analysis_manifest.csv 4.1K B Register":<br>        - cell "Select ultima_analysis_manifest.csv object":<br>          - checkbox "Select ultima_analysis_manifest.csv"<br>          - generic: object<br>        - cell "ultima_analysis_manifest.csv":<br>          - button "ultima_analysis_manifest.csv"<br>        - cell "4.1K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fultima_analysis_manifest.csv&kind=object<br>      - row "Select ultima_new_new_chemistry_202508_hg002_all.tsv object ultima_new_new_chemistry_202508_hg002_all.tsv 343K B Register":<br>        - cell "Select ultima_new_new_chemistry_202508_hg002_all.tsv object":<br>          - checkbox "Select ultima_new_new_chemistry_202508_hg002_all.tsv"<br>          - generic: object<br>        - cell "ultima_new_new_chemistry_202508_hg002_all.tsv":<br>          - button "ultima_new_new_chemistry_202508_hg002_all.tsv"<br>        - cell "343K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-omics-analysis-us-west-2%2Fultima_new_new_chemistry_202508_hg002_all.tsv&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-omics-analysis-us-west-2-1789588749401.txt ; I1-B-BUCKET-lsmc-dayoa-omics-analysis-us-west-2-1789588749401.png

### BUCKET-lsmc-dayoa-references-use1 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:11.681Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2F
- **expected**: Page fully renders its expected content
- **observed**: age?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fbbefa30e0e45538%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fbbefa30e0e45538%2F&kind=prefix<br>      - row "Select task-0fc3f2ec425e70f91/ prefix task-0fc3f2ec425e70f91/ — Register":<br>        - cell "Select task-0fc3f2ec425e70f91/ prefix":<br>          - checkbox "Select task-0fc3f2ec425e70f91/"<br>          - generic: prefix<br>        - cell "task-0fc3f2ec425e70f91/":<br>          - link "task-0fc3f2ec425e70f91/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fc3f2ec425e70f91%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fc3f2ec425e70f91%2F&kind=prefix<br>      - row "Select task-0fe86f0efff3db702/ prefix task-0fe86f0efff3db702/ — Register":<br>        - cell "Select task-0fe86f0efff3db702/ prefix":<br>          - checkbox "Select task-0fe86f0efff3db702/"<br>          - generic: prefix<br>        - cell "task-0fe86f0efff3db702/":<br>          - link "task-0fe86f0efff3db702/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fe86f0efff3db702%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Ftask-0fe86f0efff3db702%2F&kind=prefix<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-use1%2Fs3_reference_data_version.info&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-references-use1-1789588751681.txt ; I1-B-BUCKET-lsmc-dayoa-references-use1-1789588751681.png

### BUCKET-lsmc-dayoa-references-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:14.016Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: -dayoa-references-usw2%2Ftask-09fd8d1a327ce02c6%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-09fd8d1a327ce02c6%2F&kind=prefix<br>      - row "Select task-0a052f69a5cd9cd5f/ prefix task-0a052f69a5cd9cd5f/ — Register":<br>        - cell "Select task-0a052f69a5cd9cd5f/ prefix":<br>          - checkbox "Select task-0a052f69a5cd9cd5f/"<br>          - generic: prefix<br>        - cell "task-0a052f69a5cd9cd5f/":<br>          - link "task-0a052f69a5cd9cd5f/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a052f69a5cd9cd5f%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a052f69a5cd9cd5f%2F&kind=prefix<br>      - row "Select task-0a08c1dc6c2902cd3/ prefix task-0a08c1dc6c2902cd3/ — Register":<br>        - cell "Select task-0a08c1dc6c2902cd3/ prefix":<br>          - checkbox "Select task-0a08c1dc6c2902cd3/"<br>          - generic: prefix<br>        - cell "task-0a08c1dc6c2902cd3/":<br>          - link "task-0a08c1dc6c2902cd3/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a08c1dc6c2902cd3%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Ftask-0a08c1dc6c2902cd3%2F&kind=prefix<br>      - row "Select s3_reference_data_version.info object s3_reference_data_version.info 9 B Register":<br>        - cell "Select s3_reference_data_version.info object":<br>          - checkbox "Select s3_reference_data_version.info"<br>          - generic: object<br>        - cell "s3_reference_data_version.info":<br>          - button "s3_reference_data_version.info"<br>        - cell "9 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-references-usw2%2Fs3_reference_data_version.info&kind=object<br>  - button "Next page"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-references-usw2-1789588754016.txt ; I1-B-BUCKET-lsmc-dayoa-references-usw2-1789588754016.png

### BUCKET-lsmc-dayoa-runtime-assets-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:14.859Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**:      - checkbox "Select tool_specific_resources/"<br>          - generic: prefix<br>        - cell "tool_specific_resources/":<br>          - link "tool_specific_resources/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Ftool_specific_resources%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Ftool_specific_resources%2F&kind=prefix<br>      - row "Select ursa-evidence/ prefix ursa-evidence/ — Register":<br>        - cell "Select ursa-evidence/ prefix":<br>          - checkbox "Select ursa-evidence/"<br>          - generic: prefix<br>        - cell "ursa-evidence/":<br>          - link "ursa-evidence/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-evidence%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-evidence%2F&kind=prefix<br>      - row "Select ursa-hotpatches/ prefix ursa-hotpatches/ — Register":<br>        - cell "Select ursa-hotpatches/ prefix":<br>          - checkbox "Select ursa-hotpatches/"<br>          - generic: prefix<br>        - cell "ursa-hotpatches/":<br>          - link "ursa-hotpatches/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-hotpatches%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa-hotpatches%2F&kind=prefix<br>      - row "Select ursa/ prefix ursa/ — Register":<br>        - cell "Select ursa/ prefix":<br>          - checkbox "Select ursa/"<br>          - generic: prefix<br>        - cell "ursa/":<br>          - link "ursa/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-runtime-assets-usw2%2Fursa%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-runtime-assets-usw2-1789588754859.txt ; I1-B-BUCKET-lsmc-dayoa-runtime-assets-usw2-1789588754859.png

### BUCKET-lsmc-dayoa-staging-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:15.784Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: oa-staging-usw2%2Fremote_stage_20260903T142019Z_473bd635%2F&kind=prefix<br>      - row "Select staged/ prefix staged/ — Register":<br>        - cell "Select staged/ prefix":<br>          - checkbox "Select staged/"<br>          - generic: prefix<br>        - cell "staged/":<br>          - link "staged/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged%2F&kind=prefix<br>      - row "Select staged_sample_data/ prefix staged_sample_data/ — Register":<br>        - cell "Select staged_sample_data/ prefix":<br>          - checkbox "Select staged_sample_data/"<br>          - generic: prefix<br>        - cell "staged_sample_data/":<br>          - link "staged_sample_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged_sample_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaged_sample_data%2F&kind=prefix<br>      - row "Select staging/ prefix staging/ — Register":<br>        - cell "Select staging/ prefix":<br>          - checkbox "Select staging/"<br>          - generic: prefix<br>        - cell "staging/":<br>          - link "staging/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaging%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Fstaging%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dayoa-staging-usw2%2Ftmp%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dayoa-staging-usw2-1789588755784.txt ; I1-B-BUCKET-lsmc-dayoa-staging-usw2-1789588755784.png

### BUCKET-lsmc-dewey-0 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:16.502Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2F
- **expected**: Page fully renders its expected content
- **observed**:       - row "Select dayec-transient/ prefix dayec-transient/ — Register":<br>        - cell "Select dayec-transient/ prefix":<br>          - checkbox "Select dayec-transient/"<br>          - generic: prefix<br>        - cell "dayec-transient/":<br>          - link "dayec-transient/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fdayec-transient%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fdayec-transient%2F&kind=prefix<br>      - row "Select external-smoke/ prefix external-smoke/ — Register":<br>        - cell "Select external-smoke/ prefix":<br>          - checkbox "Select external-smoke/"<br>          - generic: prefix<br>        - cell "external-smoke/":<br>          - link "external-smoke/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fexternal-smoke%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fexternal-smoke%2F&kind=prefix<br>      - row "Select functional-tests/ prefix functional-tests/ — Register":<br>        - cell "Select functional-tests/ prefix":<br>          - checkbox "Select functional-tests/"<br>          - generic: prefix<br>        - cell "functional-tests/":<br>          - link "functional-tests/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Ffunctional-tests%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Ffunctional-tests%2F&kind=prefix<br>      - row "Select gui-audit/ prefix gui-audit/ — Register":<br>        - cell "Select gui-audit/ prefix":<br>          - checkbox "Select gui-audit/"<br>          - generic: prefix<br>        - cell "gui-audit/":<br>          - link "gui-audit/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-dewey-0-1789588756502.txt ; I1-B-BUCKET-lsmc-dewey-0-1789588756502.png

### BUCKET-lsmc-docs-public-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:17.336Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:  button "index.html"<br>        - cell "53.3K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Findex.html&kind=object<br>      - row "Select llms-full.txt object llms-full.txt 414.5K B Register":<br>        - cell "Select llms-full.txt object":<br>          - checkbox "Select llms-full.txt"<br>          - generic: object<br>        - cell "llms-full.txt":<br>          - button "llms-full.txt"<br>        - cell "414.5K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fllms-full.txt&kind=object<br>      - row "Select llms.txt object llms.txt 6.2K B Register":<br>        - cell "Select llms.txt object":<br>          - checkbox "Select llms.txt"<br>          - generic: object<br>        - cell "llms.txt":<br>          - button "llms.txt"<br>        - cell "6.2K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fllms.txt&kind=object<br>      - row "Select sitemap-0.xml object sitemap-0.xml 11.3K B Register":<br>        - cell "Select sitemap-0.xml object":<br>          - checkbox "Select sitemap-0.xml"<br>          - generic: object<br>        - cell "sitemap-0.xml":<br>          - button "sitemap-0.xml"<br>        - cell "11.3K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fsitemap-0.xml&kind=object<br>      - row "Select sitemap-index.xml object sitemap-index.xml 185 B Register":<br>        - cell "Select sitemap-index.xml object":<br>          - checkbox "Select sitemap-index.xml"<br>          - generic: object<br>        - cell "sitemap-index.xml":<br>          - button "sitemap-index.xml"<br>        - cell "185 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-docs-public-108782052779-us-west-2%2Fsitemap-index.xml&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-docs-public-108782052779-us-west-2-1789588757336.txt ; I1-B-BUCKET-lsmc-docs-public-108782052779-us-west-2-1789588757336.png

### BUCKET-lsmc-healthomics-failiover I1-B — PASS

- **timestamp**: 2026-09-16T19:59:17.973Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-healthomics-failiover/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-healthomics-failiover/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F<br>  - link "lsmc-healthomics-failiover":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-failiover%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-healthomics-failiover-1789588757973.txt ; I1-B-BUCKET-lsmc-healthomics-failiover-1789588757973.png

### BUCKET-lsmc-healthomics-results I1-B — PASS

- **timestamp**: 2026-09-16T19:59:18.537Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-healthomics-results/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-healthomics-results/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-healthomics-results%2F<br>  - link "lsmc-healthomics-results":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 9998872/ prefix 9998872/ — Register":<br>        - cell "Select 9998872/ prefix":<br>          - checkbox "Select 9998872/"<br>          - generic: prefix<br>        - cell "9998872/":<br>          - link "9998872/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-healthomics-results%2F9998872%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-healthomics-results%2F9998872%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-healthomics-results-1789588758538.txt ; I1-B-BUCKET-lsmc-healthomics-results-1789588758538.png

### BUCKET-lsmc-ifx-bjuice-pkgd-data I1-B — PASS

- **timestamp**: 2026-09-16T19:59:19.155Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F
- **expected**: Page fully renders its expected content
- **observed**: ount<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ifx-bjuice-pkgd-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ifx-bjuice-pkgd-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F<br>  - link "lsmc-ifx-bjuice-pkgd-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select _probes/ prefix _probes/ — Register":<br>        - cell "Select _probes/ prefix":<br>          - checkbox "Select _probes/"<br>          - generic: prefix<br>        - cell "_probes/":<br>          - link "_probes/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F_probes%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2F_probes%2F&kind=prefix<br>      - row "Select ifx-p2-1000-120-0715/ prefix ifx-p2-1000-120-0715/ — Register":<br>        - cell "Select ifx-p2-1000-120-0715/ prefix":<br>          - checkbox "Select ifx-p2-1000-120-0715/"<br>          - generic: prefix<br>        - cell "ifx-p2-1000-120-0715/":<br>          - link "ifx-p2-1000-120-0715/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2Fifx-p2-1000-120-0715%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ifx-bjuice-pkgd-data%2Fifx-p2-1000-120-0715%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-ifx-bjuice-pkgd-data-1789588759155.txt ; I1-B-BUCKET-lsmc-ifx-bjuice-pkgd-data-1789588759155.png

### BUCKET-lsmc-illumina-public-data I1-B — PASS

- **timestamp**: 2026-09-16T19:59:19.823Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2F
- **expected**: Page fully renders its expected content
- **observed**: c-illumina-public-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-illumina-public-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-illumina-public-data%2F<br>  - link "lsmc-illumina-public-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/ prefix NovaSeqX_WHGS_TruSeqPF_HG002-007/ — Register":<br>        - cell "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/ prefix":<br>          - checkbox "Select NovaSeqX_WHGS_TruSeqPF_HG002-007/"<br>          - generic: prefix<br>        - cell "NovaSeqX_WHGS_TruSeqPF_HG002-007/":<br>          - link "NovaSeqX_WHGS_TruSeqPF_HG002-007/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_HG002-007%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_HG002-007%2F&kind=prefix<br>      - row "Select NovaSeqX_WHGS_TruSeqPF_NA12878/ prefix NovaSeqX_WHGS_TruSeqPF_NA12878/ — Register":<br>        - cell "Select NovaSeqX_WHGS_TruSeqPF_NA12878/ prefix":<br>          - checkbox "Select NovaSeqX_WHGS_TruSeqPF_NA12878/"<br>          - generic: prefix<br>        - cell "NovaSeqX_WHGS_TruSeqPF_NA12878/":<br>          - link "NovaSeqX_WHGS_TruSeqPF_NA12878/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_NA12878%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-illumina-public-data%2FNovaSeqX_WHGS_TruSeqPF_NA12878%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-illumina-public-data-1789588759823.txt ; I1-B-BUCKET-lsmc-illumina-public-data-1789588759823.png

### BUCKET-lsmc-meridian-governance-registry I1-B — PASS

- **timestamp**: 2026-09-16T19:59:20.435Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-meridian-governance-registry/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-meridian-governance-registry/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F<br>  - link "lsmc-meridian-governance-registry":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select prefixes/ prefix prefixes/ — Register":<br>        - cell "Select prefixes/ prefix":<br>          - checkbox "Select prefixes/"<br>          - generic: prefix<br>        - cell "prefixes/":<br>          - link "prefixes/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2Fprefixes%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-meridian-governance-registry%2Fprefixes%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-meridian-governance-registry-1789588760435.txt ; I1-B-BUCKET-lsmc-meridian-governance-registry-1789588760435.png

### BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:22.155Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: ROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F<br>  - link "lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select raw/ prefix raw/ — Register":<br>        - cell "Select raw/ prefix":<br>          - checkbox "Select raw/"<br>          - generic: prefix<br>        - cell "raw/":<br>          - link "raw/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fraw%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fraw%2F&kind=prefix<br>      - row "Select v2/ prefix v2/ — Register":<br>        - cell "Select v2/ prefix":<br>          - checkbox "Select v2/"<br>          - generic: prefix<br>        - cell "v2/":<br>          - link "v2/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fv2%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-event-sink-raw-108782052779-us-west-2%2Fv2%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2-1789588762155.txt ; I1-B-BUCKET-lsmc-mvp-v1-event-sink-raw-108782052779-us-west-2-1789588762155.png

### BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:22.666Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:     - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F<br>  - link "lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select accessioning/ prefix accessioning/ — Register":<br>        - cell "Select accessioning/ prefix":<br>          - checkbox "Select accessioning/"<br>          - generic: prefix<br>        - cell "accessioning/":<br>          - link "accessioning/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2Faccessioning%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2%2Faccessioning%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2-1789588762666.txt ; I1-B-BUCKET-lsmc-mvp-v1-labcore-accessioning-docs-108782052779-us-west-2-1789588762666.png

### BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:23.696Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**:         - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Freceiving.html&kind=object<br>      - row "Select records.html object records.html 38.7K B Register":<br>        - cell "Select records.html object":<br>          - checkbox "Select records.html"<br>          - generic: object<br>        - cell "records.html":<br>          - button "records.html"<br>        - cell "38.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Frecords.html&kind=object<br>      - row "Select robots.txt object robots.txt 26 B Register":<br>        - cell "Select robots.txt object":<br>          - checkbox "Select robots.txt"<br>          - generic: object<br>        - cell "robots.txt":<br>          - button "robots.txt"<br>        - cell "26 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Frobots.txt&kind=object<br>      - row "Select sample-holds.html object sample-holds.html 38.8K B Register":<br>        - cell "Select sample-holds.html object":<br>          - checkbox "Select sample-holds.html"<br>          - generic: object<br>        - cell "sample-holds.html":<br>          - button "sample-holds.html"<br>        - cell "38.8K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Fsample-holds.html&kind=object<br>      - row "Select workspace.html object workspace.html 37.9K B Register":<br>        - cell "Select workspace.html object":<br>          - checkbox "Select workspace.html"<br>          - generic: object<br>        - cell "workspace.html":<br>          - button "workspace.html"<br>        - cell "37.9K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-labcore-ui-108782052779-us-west-2%2Fworkspace.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2-1789588763696.txt ; I1-B-BUCKET-lsmc-mvp-v1-labcore-ui-108782052779-us-west-2-1789588763696.png

### BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:24.347Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-mvp-v1-status-alb-logs-108782052779/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-mvp-v1-status-alb-logs-108782052779/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F<br>  - link "lsmc-mvp-v1-status-alb-logs-108782052779":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select status/ prefix status/ — Register":<br>        - cell "Select status/ prefix":<br>          - checkbox "Select status/"<br>          - generic: prefix<br>        - cell "status/":<br>          - link "status/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2Fstatus%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-mvp-v1-status-alb-logs-108782052779%2Fstatus%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779-1789588764348.txt ; I1-B-BUCKET-lsmc-mvp-v1-status-alb-logs-108782052779-1789588764348.png

### BUCKET-lsmc-public-ont-data I1-B — PASS

- **timestamp**: 2026-09-16T19:59:24.862Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-public-ont-data/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-public-ont-data/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-public-ont-data%2F<br>  - link "lsmc-public-ont-data":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select 20250313/ prefix 20250313/ — Register":<br>        - cell "Select 20250313/ prefix":<br>          - checkbox "Select 20250313/"<br>          - generic: prefix<br>        - cell "20250313/":<br>          - link "20250313/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-public-ont-data%2F20250313%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-public-ont-data%2F20250313%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-public-ont-data-1789588764862.txt ; I1-B-BUCKET-lsmc-public-ont-data-1789588764862.png

### BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2 I1-B — REVIEW

- **timestamp**: 2026-09-16T19:59:25.362Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-qeo-day-analytical-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - status: "User: arn:aws:sts::108782052779:assumed-role/Dayhoff-day-Compute-InstanceRole3CCE2F1D-Nt0s1SL3rfbr/i-07df3a933e4839f52 is not authorized to perform: s3:ListBucket on resource: \"arn:aws:s3:::lsmc-qeo-day-analytical-108782052779-us-west-2\" with an explicit deny in a resource-based policy"<br>  - heading "Unable to load this view" [level=2]<br>  - paragraph: See the error above. You can use the navigation to return to the Library.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789588765362.txt ; I1-B-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789588765362.png

### BUCKET-lsmc-ssf-sequencing-data I1-B — PASS

- **timestamp**: 2026-09-16T19:59:26.196Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2F
- **expected**: Page fully renders its expected content
- **observed**:    - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Freference%2F&kind=prefix<br>      - row "Select staged_external_data/ prefix staged_external_data/ — Register":<br>        - cell "Select staged_external_data/ prefix":<br>          - checkbox "Select staged_external_data/"<br>          - generic: prefix<br>        - cell "staged_external_data/":<br>          - link "staged_external_data/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fstaged_external_data%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fstaged_external_data%2F&kind=prefix<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Ftmp%2F&kind=prefix<br>      - row "Select ubuntu/ prefix ubuntu/ — Register":<br>        - cell "Select ubuntu/ prefix":<br>          - checkbox "Select ubuntu/"<br>          - generic: prefix<br>        - cell "ubuntu/":<br>          - link "ubuntu/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fubuntu%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2Fubuntu%2F&kind=prefix<br>      - row "Select README.md object README.md 7.6K B Register":<br>        - cell "Select README.md object":<br>          - checkbox "Select README.md"<br>          - generic: object<br>        - cell "README.md":<br>          - button "README.md"<br>        - cell "7.6K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ssf-sequencing-data%2FREADME.md&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-ssf-sequencing-data-1789588766196.txt ; I1-B-BUCKET-lsmc-ssf-sequencing-data-1789588766196.png

### BUCKET-lsmc-terraform-state I1-B — PASS

- **timestamp**: 2026-09-16T19:59:44.256Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-terraform-state%2F
- **expected**: Page fully renders its expected content
- **observed**: "<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select log-archive/ prefix log-archive/ — Register":<br>        - cell "Select log-archive/ prefix":<br>          - checkbox "Select log-archive/"<br>          - generic: prefix<br>        - cell "log-archive/":<br>          - link "log-archive/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Flog-archive%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Flog-archive%2F&kind=prefix<br>      - row "Select management/ prefix management/ — Register":<br>        - cell "Select management/ prefix":<br>          - checkbox "Select management/"<br>          - generic: prefix<br>        - cell "management/":<br>          - link "management/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fmanagement%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fmanagement%2F&kind=prefix<br>      - row "Select production/ prefix production/ — Register":<br>        - cell "Select production/ prefix":<br>          - checkbox "Select production/"<br>          - generic: prefix<br>        - cell "production/":<br>          - link "production/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fproduction%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fproduction%2F&kind=prefix<br>      - row "Select security/ prefix security/ — Register":<br>        - cell "Select security/ prefix":<br>          - checkbox "Select security/"<br>          - generic: prefix<br>        - cell "security/":<br>          - link "security/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-terraform-state%2Fsecurity%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-terraform-state%2Fsecurity%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-terraform-state-1789588784256.txt ; I1-B-BUCKET-lsmc-terraform-state-1789588784256.png

### BUCKET-lsmc-twenty-prod-storage I1-B — PASS

- **timestamp**: 2026-09-16T19:59:44.968Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F
- **expected**: Page fully renders its expected content
- **observed**: vigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-twenty-prod-storage/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-twenty-prod-storage/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F<br>  - link "lsmc-twenty-prod-storage":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ prefix e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ — Register":<br>        - cell "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/ prefix":<br>          - checkbox "Select e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/"<br>          - generic: prefix<br>        - cell "e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/":<br>          - link "e6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2Fe6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-twenty-prod-storage%2Fe6b8200f-cd5f-44a4-8ff9-bf88d57f2cdb%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-twenty-prod-storage-1789588784968.txt ; I1-B-BUCKET-lsmc-twenty-prod-storage-1789588784968.png

### BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:45.658Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: D<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ursa-cost-reports-108782052779-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ursa-cost-reports-108782052779-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F<br>  - link "lsmc-ursa-cost-reports-108782052779-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select reports/ prefix reports/ — Register":<br>        - cell "Select reports/ prefix":<br>          - checkbox "Select reports/"<br>          - generic: prefix<br>        - cell "reports/":<br>          - link "reports/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Freports%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Freports%2F&kind=prefix<br>      - row "Select ursa-deploy-scripts/ prefix ursa-deploy-scripts/ — Register":<br>        - cell "Select ursa-deploy-scripts/ prefix":<br>          - checkbox "Select ursa-deploy-scripts/"<br>          - generic: prefix<br>        - cell "ursa-deploy-scripts/":<br>          - link "ursa-deploy-scripts/":<br>            - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Fursa-deploy-scripts%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Flsmc-ursa-cost-reports-108782052779-us-west-2%2Fursa-deploy-scripts%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2-1789588785658.txt ; I1-B-BUCKET-lsmc-ursa-cost-reports-108782052779-us-west-2-1789588785658.png

### BUCKET-lsmc-ursa-customers-usw2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:46.182Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://lsmc-ursa-customers-usw2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://lsmc-ursa-customers-usw2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F<br>  - link "lsmc-ursa-customers-usw2":<br>    - /url: /storage?uri=s3%3A%2F%2Flsmc-ursa-customers-usw2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-lsmc-ursa-customers-usw2-1789588786182.txt ; I1-B-BUCKET-lsmc-ursa-customers-usw2-1789588786182.png

### BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps I1-B — PASS

- **timestamp**: 2026-09-16T19:59:46.801Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F<br>  - link "marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps-1789588786801.txt ; I1-B-BUCKET-marvain-cleanroom-20260712t103857z-artifactbucket-mecojkek5eps-1789588786801.png

### BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie I1-B — PASS

- **timestamp**: 2026-09-16T19:59:47.400Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F<br>  - link "marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie-1789588787400.txt ; I1-B-BUCKET-marvain-cleanroom-20260712t103857z-auditbucket-yl3kufkgfdie-1789588787400.png

### BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo I1-B — PASS

- **timestamp**: 2026-09-16T19:59:48.133Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F<br>  - link "marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "No matching items.":<br>        - cell "No matching items."<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo-1789588788133.txt ; I1-B-BUCKET-marvain-cleanroom-20260712t111914z-artifactbucket-qkwenuto9bbo-1789588788133.png

### BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj I1-B — PASS

- **timestamp**: 2026-09-16T19:59:48.821Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F
- **expected**: Page fully renders its expected content
- **observed**:  navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F<br>  - link "marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj":<br>    - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select audit/ prefix audit/ — Register":<br>        - cell "Select audit/ prefix":<br>          - checkbox "Select audit/"<br>          - generic: prefix<br>        - cell "audit/":<br>          - link "audit/":<br>            - /url: /storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2Faudit%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj%2Faudit%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj-1789588788821.txt ; I1-B-BUCKET-marvain-cleanroom-20260712t111914z-auditbucket-wvcw5pjxz1kj-1789588788821.png

### BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl I1-B — PASS

- **timestamp**: 2026-09-16T19:59:50.058Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2F
- **expected**: Page fully renders its expected content
- **observed**: eanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fa90ebf33932ad96c7f95045f39ca4273.template&kind=object<br>      - row "Select bd9b5df9ed21415aabf9be3dd0bf872b object bd9b5df9ed21415aabf9be3dd0bf872b 30.7M B Register":<br>        - cell "Select bd9b5df9ed21415aabf9be3dd0bf872b object":<br>          - checkbox "Select bd9b5df9ed21415aabf9be3dd0bf872b"<br>          - generic: object<br>        - cell "bd9b5df9ed21415aabf9be3dd0bf872b":<br>          - button "bd9b5df9ed21415aabf9be3dd0bf872b"<br>        - cell "30.7M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fbd9b5df9ed21415aabf9be3dd0bf872b&kind=object<br>      - row "Select c0eae6ac1f8491e980ecfdc9888864f0 object c0eae6ac1f8491e980ecfdc9888864f0 36.4M B Register":<br>        - cell "Select c0eae6ac1f8491e980ecfdc9888864f0 object":<br>          - checkbox "Select c0eae6ac1f8491e980ecfdc9888864f0"<br>          - generic: object<br>        - cell "c0eae6ac1f8491e980ecfdc9888864f0":<br>          - button "c0eae6ac1f8491e980ecfdc9888864f0"<br>        - cell "36.4M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Fc0eae6ac1f8491e980ecfdc9888864f0&kind=object<br>      - row "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template object f8fabfa3d78a1f43ef40b3d4efc31df9.template 70.7K B Register":<br>        - cell "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template object":<br>          - checkbox "Select f8fabfa3d78a1f43ef40b3d4efc31df9.template"<br>          - generic: object<br>        - cell "f8fabfa3d78a1f43ef40b3d4efc31df9.template":<br>          - button "f8fabfa3d78a1f43ef40b3d4efc31df9.template"<br>        - cell "70.7K B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fmarvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl%2Ff8fabfa3d78a1f43ef40b3d4efc31df9.template&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl-1789588790058.txt ; I1-B-BUCKET-marvain-cleanroom-20260712t111914z-packagingbucket-bccev8bwblrl-1789588790058.png

### BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete I1-B — PASS

- **timestamp**: 2026-09-16T19:59:50.994Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-4da281c1dc024f1c-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-4da281c1dc024f1c-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F<br>  - link "parallelcluster-4da281c1dc024f1c-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-4da281c1dc024f1c-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete-1789588790994.txt ; I1-B-BUCKET-parallelcluster-4da281c1dc024f1c-v1-do-not-delete-1789588790994.png

### BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete I1-B — PASS

- **timestamp**: 2026-09-16T19:59:52.042Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-730cb6d53cf2deec-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-730cb6d53cf2deec-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F<br>  - link "parallelcluster-730cb6d53cf2deec-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-730cb6d53cf2deec-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete-1789588792042.txt ; I1-B-BUCKET-parallelcluster-730cb6d53cf2deec-v1-do-not-delete-1789588792042.png

### BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete I1-B — PASS

- **timestamp**: 2026-09-16T19:59:53.262Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F
- **expected**: Page fully renders its expected content
- **observed**: n "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://parallelcluster-e781c59d26140bab-v1-do-not-delete/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://parallelcluster-e781c59d26140bab-v1-do-not-delete/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F<br>  - link "parallelcluster-e781c59d26140bab-v1-do-not-delete":<br>    - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select parallelcluster/ prefix parallelcluster/ — Register":<br>        - cell "Select parallelcluster/ prefix":<br>          - checkbox "Select parallelcluster/"<br>          - generic: prefix<br>        - cell "parallelcluster/":<br>          - link "parallelcluster/":<br>            - /url: /storage?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2Fparallelcluster%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fparallelcluster-e781c59d26140bab-v1-do-not-delete%2Fparallelcluster%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete-1789588793262.txt ; I1-B-BUCKET-parallelcluster-e781c59d26140bab-v1-do-not-delete-1789588793262.png

### BUCKET-terrarium-dev-media I1-B — PASS

- **timestamp**: 2026-09-16T19:59:53.902Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F
- **expected**: Page fully renders its expected content
- **observed**: k "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-dev-media/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-dev-media/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>  - link "terrarium-dev-media":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select documents/ prefix documents/ — Register":<br>        - cell "Select documents/ prefix":<br>          - checkbox "Select documents/"<br>          - generic: prefix<br>        - cell "documents/":<br>          - link "documents/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2Fdocuments%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-media%2Fdocuments%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-media%2Fimages%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-dev-media-1789588793902.txt ; I1-B-BUCKET-terrarium-dev-media-1789588793902.png

### BUCKET-terrarium-dev-web I1-B — PASS

- **timestamp**: 2026-09-16T19:59:54.588Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F
- **expected**: Page fully renders its expected content
- **observed**: RI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-dev-web/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-dev-web/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>  - link "terrarium-dev-web":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select assets/ prefix assets/ — Register":<br>        - cell "Select assets/ prefix":<br>          - checkbox "Select assets/"<br>          - generic: prefix<br>        - cell "assets/":<br>          - link "assets/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2Fassets%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Fassets%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Fimages%2F&kind=prefix<br>      - row "Select index.html object index.html 482 B Register":<br>        - cell "Select index.html object":<br>          - checkbox "Select index.html"<br>          - generic: object<br>        - cell "index.html":<br>          - button "index.html"<br>        - cell "482 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-dev-web%2Findex.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-dev-web-1789588794588.txt ; I1-B-BUCKET-terrarium-dev-web-1789588794588.png

### BUCKET-terrarium-prod-media I1-B — PASS

- **timestamp**: 2026-09-16T19:59:55.203Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F
- **expected**: Page fully renders its expected content
- **observed**: ture":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-prod-media/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-prod-media/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>  - link "terrarium-prod-media":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select documents/ prefix documents/ — Register":<br>        - cell "Select documents/ prefix":<br>          - checkbox "Select documents/"<br>          - generic: prefix<br>        - cell "documents/":<br>          - link "documents/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2Fdocuments%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-media%2Fdocuments%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-media%2Fimages%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-prod-media-1789588795203.txt ; I1-B-BUCKET-terrarium-prod-media-1789588795203.png

### BUCKET-terrarium-prod-web I1-B — PASS

- **timestamp**: 2026-09-16T19:59:55.808Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F
- **expected**: Page fully renders its expected content
- **observed**:  /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-prod-web/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-prod-web/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>  - link "terrarium-prod-web":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select assets/ prefix assets/ — Register":<br>        - cell "Select assets/ prefix":<br>          - checkbox "Select assets/"<br>          - generic: prefix<br>        - cell "assets/":<br>          - link "assets/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2Fassets%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Fassets%2F&kind=prefix<br>      - row "Select images/ prefix images/ — Register":<br>        - cell "Select images/ prefix":<br>          - checkbox "Select images/"<br>          - generic: prefix<br>        - cell "images/":<br>          - link "images/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2Fimages%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Fimages%2F&kind=prefix<br>      - row "Select index.html object index.html 482 B Register":<br>        - cell "Select index.html object":<br>          - checkbox "Select index.html"<br>          - generic: object<br>        - cell "index.html":<br>          - button "index.html"<br>        - cell "482 B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-prod-web%2Findex.html&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-prod-web-1789588795808.txt ; I1-B-BUCKET-terrarium-prod-web-1789588795808.png

### BUCKET-terrarium-tfstate-dev I1-B — PASS

- **timestamp**: 2026-09-16T19:59:56.417Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-tfstate-dev/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-tfstate-dev/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>  - link "terrarium-tfstate-dev":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select terrarium/ prefix terrarium/ — Register":<br>        - cell "Select terrarium/ prefix":<br>          - checkbox "Select terrarium/"<br>          - generic: prefix<br>        - cell "terrarium/":<br>          - link "terrarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2Fterrarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2Fterrarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-tfstate-dev-1789588796417.txt ; I1-B-BUCKET-terrarium-tfstate-dev-1789588796417.png

### BUCKET-terrarium-tfstate-prod I1-B — PASS

- **timestamp**: 2026-09-16T19:59:56.941Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://terrarium-tfstate-prod/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://terrarium-tfstate-prod/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>  - link "terrarium-tfstate-prod":<br>    - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select terrarium/ prefix terrarium/ — Register":<br>        - cell "Select terrarium/ prefix":<br>          - checkbox "Select terrarium/"<br>          - generic: prefix<br>        - cell "terrarium/":<br>          - link "terrarium/":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2Fterrarium%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2Fterrarium%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-terrarium-tfstate-prod-1789588796941.txt ; I1-B-BUCKET-terrarium-tfstate-prod-1789588796941.png

### BUCKET-ursa-us-west-2-052779-default-customer-1d8c14 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:57.571Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F
- **expected**: Page fully renders its expected content
- **observed**: 1d8c14%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select tmp/ prefix tmp/ — Register":<br>        - cell "Select tmp/ prefix":<br>          - checkbox "Select tmp/"<br>          - generic: prefix<br>        - cell "tmp/":<br>          - link "tmp/":<br>            - /url: /storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2Ftmp%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2Ftmp%2F&kind=prefix<br>      - row "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz object RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz 14.1M B Register":<br>        - cell "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz object":<br>          - checkbox "Select RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz"<br>          - generic: object<br>        - cell "RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz":<br>          - button "RIH0_ANA0-HG002_DBC0_0.R1.fastq.gz"<br>        - cell "14.1M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2FRIH0_ANA0-HG002_DBC0_0.R1.fastq.gz&kind=object<br>      - row "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz object RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz 15.2M B Register":<br>        - cell "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz object":<br>          - checkbox "Select RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz"<br>          - generic: object<br>        - cell "RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz":<br>          - button "RIH0_ANA0-HG002_DBC0_0.R2.fastq.gz"<br>        - cell "15.2M B"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2FRIH0_ANA0-HG002_DBC0_0.R2.fastq.gz&kind=object<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-ursa-us-west-2-052779-default-customer-1d8c14-1789588797571.txt ; I1-B-BUCKET-ursa-us-west-2-052779-default-customer-1d8c14-1789588797571.png

### BUCKET-zebra-day-cfg-us-west-2 I1-B — PASS

- **timestamp**: 2026-09-16T19:59:58.149Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / S3 BROWSER<br>  - heading "S3 Browser" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - textbox "S3 URI":<br>    - /placeholder: s3://bucket/exact/prefix/<br>    - text: s3://zebra-day-cfg-us-west-2/<br>  - button "Go"<br>  - link "All buckets":<br>    - /url: /storage<br>  - generic: s3://zebra-day-cfg-us-west-2/<br>  - button "Upload files"<br>  - link "Register this folder":<br>    - /url: /add?kind=prefix&uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>  - link "zebra-day-cfg-us-west-2":<br>    - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>  - searchbox "Filter names on this page"<br>  - button "Register selection as a set"<br>  - table:<br>    - rowgroup:<br>      - row "Kind Name Size Registration":<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Size"<br>        - columnheader "Registration"<br>    - rowgroup:<br>      - row "Select zebra-day/ prefix zebra-day/ — Register":<br>        - cell "Select zebra-day/ prefix":<br>          - checkbox "Select zebra-day/"<br>          - generic: prefix<br>        - cell "zebra-day/":<br>          - link "zebra-day/":<br>            - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2Fzebra-day%2F<br>        - cell "—"<br>        - cell "Register":<br>          - link "Register":<br>            - /url: /add?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2Fzebra-day%2F&kind=prefix<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-BUCKET-zebra-day-cfg-us-west-2-1789588798149.txt ; I1-B-BUCKET-zebra-day-cfg-us-west-2-1789588798149.png

### LIT-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T20:00:03.540Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=genomics&page=1
- **inputs**: genomics
- **expected**: PubMed renders matching paper rows
- **observed**: genomics search returns 20 papers including PMID40071816.
- **evidence**: I1-B-LIT-SEARCH-1789588803540.txt ; I1-B-LIT-SEARCH-1789588803540.png

### LIT-REGISTER I1-B — PASS

- **timestamp**: 2026-09-16T20:00:28.798Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/records/M-DGX-TT5K
- **inputs**: PMID40071816 registered as M-DGX-TT5K and record details render.
- **expected**: Registered paper links to persistent record
- **observed**: PMID40071816 registered as M-DGX-TT5K and record details render.
- **evidence**: I1-B-LIT-REGISTER-1789588828798.txt ; I1-B-LIT-REGISTER-1789588828798.png

### ADMIN-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T20:00:38.182Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ADMIN<br>  - heading "Admin" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Service administration" [level=2]<br>  - paragraph: Dewey 10.0.5<br>  - link "Health":<br>    - /url: /health<br>  - link "Observability":<br>    - /url: /ui/observability<br>  - link "Anomalies":<br>    - /url: /ui/anomalies<br>  - link "All accessible shares":<br>    - /url: /shares<br>  - link "Clients and tokens":<br>    - /url: /account<br>  - paragraph: Shared login owns users, roles, and credentials. Dewey owns record policies, delegated access, and shares.<br>  - heading "Sharing defaults" [level=3]<br>  - paragraph: 30 days per share · 900 seconds per delivery credential<br>  - button "Edit defaults"<br>  - heading "TapDB administration" [level=2]<br>  - paragraph: Advanced templates, object repair, relationship graphs, audit, inventory, backups, and runtime inspection.<br>  - link "Open TapDB":<br>    - /url: /tapdb/<br>  - paragraph: These tools require Dewey admin access. Standalone TapDB probe failures do not establish that embedded Dewey is unavailable.<br>  - generic "Effective configuration · secrets redacted"<br>  - generic "Release identity"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ADMIN-PAGE-1789588838182.txt ; I1-B-ADMIN-PAGE-1789588838182.png

### ADMIN-CONFIG I1-B — PASS

- **timestamp**: 2026-09-16T20:00:47.969Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **inputs**: Expanded configuration fields show [REDACTED] values for secret-bearing settings.
- **expected**: Effective configuration masks secret fields
- **observed**: Expanded configuration fields show [REDACTED] values for secret-bearing settings.
- **evidence**: I1-B-ADMIN-CONFIG-1789588847969.txt ; I1-B-ADMIN-CONFIG-1789588847969.png

### ADMIN-RELEASE I1-B — FAIL

- **timestamp**: 2026-09-16T20:00:48.538Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **inputs**: 10.0.5 and df6d4d0 match; branch still codex/dewey-labcore-910 rather than source branch. D01.
- **expected**: Tag/SHA and branch reflect deployed source
- **observed**: 10.0.5 and df6d4d0 match; branch still codex/dewey-labcore-910 rather than source branch. D01.
- **evidence**: I1-B-ADMIN-RELEASE-1789588848538.txt ; I1-B-ADMIN-RELEASE-1789588848538.png

### ADMIN-DEFAULTS I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:00:48.892Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **inputs**: Form inspected without Save.
- **expected**: Defaults form usable; shared setting mutation excluded
- **observed**: Form inspected without Save.
- **evidence**: I1-B-ADMIN-DEFAULTS-1789588848892.txt ; I1-B-ADMIN-DEFAULTS-1789588848892.png

### ADMIN-HEALTH I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:01:05.221Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin
- **expected**: Page fully renders its expected content
- **observed**: /health: Error: Browser Use cannot open https://dewey.day.lsmc.bio/health in tab 4. Browser reported: net::ERR_BLOCKED_BY_CLIENT
- **evidence**: I1-B-ADMIN-HEALTH-1789588865221.txt

### ADMIN-OBS I1-B — PASS

- **timestamp**: 2026-09-16T20:01:05.662Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/observability
- **expected**: Page fully renders its expected content
- **observed**: c: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: denied via anonymous<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - article:<br>    - generic: ok via external_broker<br>    - generic: 0cd497666af84629<br>  - heading "Local Anomalies" [level=3]<br>  - generic: Read-only local anomaly records persisted in TapDB.<br>  - link "Open anomaly view":<br>    - /url: /ui/anomalies<br>  - generic: "high: Artifact storage review is pending"<br>  - generic: "medium: Readiness probe observed a bootstrap gap"<br>  - generic: "low: Operator session activity is sparse"<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-ADMIN-OBS-1789588865662.txt ; I1-B-ADMIN-OBS-1789588865662.png

### ADMIN-ANOMALIES I1-B — PASS

- **timestamp**: 2026-09-16T20:01:05.942Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/anomalies
- **expected**: Page fully renders its expected content
- **observed**:   - /url: /admin<br>  - button "Logout"<br>- main:<br>  - generic: Read-only local records<br>  - heading "Persisted anomaly records for this Dewey instance." [level=2]<br>  - paragraph: These are local operational summaries only. They are not release authority and they do not mutate backend state.<br>  - generic: 3 records<br>  - table:<br>    - rowgroup:<br>      - row "Anomaly Severity Status Source Action":<br>        - columnheader "Anomaly"<br>        - columnheader "Severity"<br>        - columnheader "Status"<br>        - columnheader "Source"<br>        - columnheader "Action"<br>    - rowgroup:<br>      - row "M-DGX-9RJX Artifact storage review is pending high open storage Open":<br>        - cell "M-DGX-9RJX Artifact storage review is pending":<br>          - generic: M-DGX-9RJX<br>          - generic: Artifact storage review is pending<br>        - cell "high"<br>        - cell "open"<br>        - cell "storage"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RJX<br>      - row "M-DGX-9RG1 Readiness probe observed a bootstrap gap medium open readyz Open":<br>        - cell "M-DGX-9RG1 Readiness probe observed a bootstrap gap":<br>          - generic: M-DGX-9RG1<br>          - generic: Readiness probe observed a bootstrap gap<br>        - cell "medium"<br>        - cell "open"<br>        - cell "readyz"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RG1<br>      - row "M-DGX-9RHZ Operator session activity is sparse low monitoring auth_health Open":<br>        - cell "M-DGX-9RHZ Operator session activity is sparse":<br>          - generic: M-DGX-9RHZ<br>          - generic: Operator session activity is sparse<br>        - cell "low"<br>        - cell "monitoring"<br>        - cell "auth_health"<br>        - cell "Open":<br>          - link "Open":<br>            - /url: /ui/anomalies/M-DGX-9RHZ<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-ADMIN-ANOMALIES-1789588865942.txt ; I1-B-ADMIN-ANOMALIES-1789588865942.png

### ADMIN-ANOMALY-DETAIL I1-B — PASS

- **timestamp**: 2026-09-16T20:01:06.255Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui/anomalies/M-DGX-9RG1
- **expected**: Page fully renders its expected content
- **observed**: - generic: DAY<br>- banner:<br>  - generic: Dewey Operator Console<br>  - heading "Anomaly Detail" [level=1]<br>  - generic: johnm@lsmc.com<br>  - link "Back to Anomalies":<br>    - /url: /ui/anomalies<br>  - link "Dashboard":<br>    - /url: /ui<br>  - link "Observability":<br>    - /url: /ui/observability<br>  - button "Logout"<br>- main:<br>  - generic: Local anomaly record<br>  - heading "Readiness probe observed a bootstrap gap" [level=2]<br>  - paragraph: The local readiness surface recorded a brief backend-unavailable state during bootstrap.<br>  - generic: medium severity<br>  - heading "Record" [level=3]<br>  - generic: Immutable local anomaly metadata.<br>  - text: ID<br>  - generic: M-DGX-9RG1<br>  - text: Category<br>  - generic: readiness<br>  - text: Status<br>  - generic: open<br>  - text: Source<br>  - generic: readyz<br>  - text: Source View<br>  - generic: /ui/anomalies/M-DGX-9RG1<br>  - heading "Operational Context" [level=3]<br>  - generic: Redacted fields are kept local and read-only.<br>  - generic: First seen 2026-05-20T09:40:36.224133Z<br>  - generic: Last seen 2026-05-20T09:40:36.224133Z<br>  - generic: Occurrences 1<br>  - generic: Review readiness and database startup timing.<br>  - generic: "{ \"database_status\": \"unknown\" }"<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-ADMIN-ANOMALY-DETAIL-1789588866255.txt ; I1-B-ADMIN-ANOMALY-DETAIL-1789588866255.png

### ROUTES-ROOT I1-B — PASS

- **timestamp**: 2026-09-16T20:01:07.084Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **expected**: Page fully renders its expected content
- **observed**:  M-DGX-TPJW 20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPJW prefix offwithyou 9/16/2026":<br>        - cell "Select M-DGX-TPJW":<br>          - checkbox "Select M-DGX-TPJW"<br>        - cell "20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPJW":<br>          - link "20260911_LH01106_0019_A23NFCMLT3":<br>            - /url: /records/M-DGX-TPJW<br>          - generic: M-DGX-TPJW<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "offwithyou"<br>        - cell "9/16/2026"<br>      - row "Select M-DGX-TPF3 20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPF3 prefix offwithyou 9/12/2026":<br>        - cell "Select M-DGX-TPF3":<br>          - checkbox "Select M-DGX-TPF3"<br>        - cell "20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPF3":<br>          - link "20260911_LH01106_0019_A23NFCMLT3":<br>            - /url: /records/M-DGX-TPF3<br>          - generic: M-DGX-TPF3<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "offwithyou"<br>        - cell "9/12/2026"<br>      - row "Select M-DGX-NP43 synthetic-labcore-run-2675d532089744db8e098480068caaa7 M-DGX-NP43 prefix labcore 9/11/2026":<br>        - cell "Select M-DGX-NP43":<br>          - checkbox "Select M-DGX-NP43"<br>        - cell "synthetic-labcore-run-2675d532089744db8e098480068caaa7 M-DGX-NP43":<br>          - link "synthetic-labcore-run-2675d532089744db8e098480068caaa7":<br>            - /url: /records/M-DGX-NP43<br>          - generic: M-DGX-NP43<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "labcore"<br>        - cell "9/11/2026"<br>      - row "Select M-DGX-NP19 Dewey 9.0.0 production acceptance M-DGX-NP19 set — 9/11/2026":<br>        - cell "Select M-DGX-NP19":<br>          - checkbox "Select M-DGX-NP19" [disabled]<br>        - cell "Dewey 9.0.0 production acceptance M-DGX-NP19":<br>          - link "Dewey 9.0.0 production acceptance":<br>            - /url: /records/M-DGX-NP19<br>          - generic: M-DGX-NP19<br>        - cell "set":<br>          - generic: set<br>        - cell "—"<br>        - cell "9/11/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ROUTES-ROOT-1789588867084.txt ; I1-B-ROUTES-ROOT-1789588867084.png

### ROUTES-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T20:01:07.732Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/search
- **expected**: Page fully renders its expected content
- **observed**:  M-DGX-TPJW 20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPJW prefix offwithyou 9/16/2026":<br>        - cell "Select M-DGX-TPJW":<br>          - checkbox "Select M-DGX-TPJW"<br>        - cell "20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPJW":<br>          - link "20260911_LH01106_0019_A23NFCMLT3":<br>            - /url: /records/M-DGX-TPJW<br>          - generic: M-DGX-TPJW<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "offwithyou"<br>        - cell "9/16/2026"<br>      - row "Select M-DGX-TPF3 20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPF3 prefix offwithyou 9/12/2026":<br>        - cell "Select M-DGX-TPF3":<br>          - checkbox "Select M-DGX-TPF3"<br>        - cell "20260911_LH01106_0019_A23NFCMLT3 M-DGX-TPF3":<br>          - link "20260911_LH01106_0019_A23NFCMLT3":<br>            - /url: /records/M-DGX-TPF3<br>          - generic: M-DGX-TPF3<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "offwithyou"<br>        - cell "9/12/2026"<br>      - row "Select M-DGX-NP43 synthetic-labcore-run-2675d532089744db8e098480068caaa7 M-DGX-NP43 prefix labcore 9/11/2026":<br>        - cell "Select M-DGX-NP43":<br>          - checkbox "Select M-DGX-NP43"<br>        - cell "synthetic-labcore-run-2675d532089744db8e098480068caaa7 M-DGX-NP43":<br>          - link "synthetic-labcore-run-2675d532089744db8e098480068caaa7":<br>            - /url: /records/M-DGX-NP43<br>          - generic: M-DGX-NP43<br>        - cell "prefix":<br>          - generic: prefix<br>        - cell "labcore"<br>        - cell "9/11/2026"<br>      - row "Select M-DGX-NP19 Dewey 9.0.0 production acceptance M-DGX-NP19 set — 9/11/2026":<br>        - cell "Select M-DGX-NP19":<br>          - checkbox "Select M-DGX-NP19" [disabled]<br>        - cell "Dewey 9.0.0 production acceptance M-DGX-NP19":<br>          - link "Dewey 9.0.0 production acceptance":<br>            - /url: /records/M-DGX-NP19<br>          - generic: M-DGX-NP19<br>        - cell "set":<br>          - generic: set<br>        - cell "—"<br>        - cell "9/11/2026"<br>  - generic: Page 1 · 25 per page<br>  - button "Next"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ROUTES-SEARCH-1789588867732.txt ; I1-B-ROUTES-SEARCH-1789588867732.png

### ROUTES-ARTIFACTS I1-B — PASS

- **timestamp**: 2026-09-16T20:01:08.113Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ADD<br>  - heading "Add" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "Register an artifact" [level=2]<br>  - generic: What are you adding?<br>  - combobox "What are you adding?":<br>    - option "Object · one file or URL" [selected]<br>    - option "Prefix · one S3 folder or bucket"<br>    - option "Set · selected Object and Prefix EUIDs"<br>    - option "Upload · add a new file to S3"<br>  - generic: S3 URI or HTTP(S) URL<br>  - textbox "S3 URI or HTTP(S) URL"<br>  - generic: S3 keys are preserved exactly. A prefix receives one EUID; its children are not registered.<br>  - generic: Name<br>  - textbox "Name"<br>  - generic: Description<br>  - textbox "Description"<br>  - generic "Metadata"<br>  - button "Register"<br>  - complementary:<br>    - heading "One stable reference" [level=2]<br>    - paragraph: Store the Dewey EUID in your other tools. Dewey resolves the location, metadata, contents, and authorized access.<br>    - paragraph: New registrations are visible and downloadable by internal LSMC users. You can change metadata and download permissions independently.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ROUTES-ARTIFACTS-1789588868113.txt ; I1-B-ROUTES-ARTIFACTS-1789588868113.png

### ROUTES-DAG I1-B — PASS

- **timestamp**: 2026-09-16T20:01:08.635Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts/dag
- **expected**: Page fully renders its expected content
- **observed**: l "terrarium-dev-media":<br>          - link "terrarium-dev-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-dev-web us-west-2":<br>        - cell "terrarium-dev-web":<br>          - link "terrarium-dev-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-dev-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-media us-west-2":<br>        - cell "terrarium-prod-media":<br>          - link "terrarium-prod-media":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-media%2F<br>        - cell "us-west-2"<br>      - row "terrarium-prod-web us-west-2":<br>        - cell "terrarium-prod-web":<br>          - link "terrarium-prod-web":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-prod-web%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-dev us-west-2":<br>        - cell "terrarium-tfstate-dev":<br>          - link "terrarium-tfstate-dev":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-dev%2F<br>        - cell "us-west-2"<br>      - row "terrarium-tfstate-prod us-west-2":<br>        - cell "terrarium-tfstate-prod":<br>          - link "terrarium-tfstate-prod":<br>            - /url: /storage?uri=s3%3A%2F%2Fterrarium-tfstate-prod%2F<br>        - cell "us-west-2"<br>      - row "ursa-us-west-2-052779-default-customer-1d8c14 us-west-2":<br>        - cell "ursa-us-west-2-052779-default-customer-1d8c14":<br>          - link "ursa-us-west-2-052779-default-customer-1d8c14":<br>            - /url: /storage?uri=s3%3A%2F%2Fursa-us-west-2-052779-default-customer-1d8c14%2F<br>        - cell "us-west-2"<br>      - row "zebra-day-cfg-us-west-2 us-west-2":<br>        - cell "zebra-day-cfg-us-west-2":<br>          - link "zebra-day-cfg-us-west-2":<br>            - /url: /storage?uri=s3%3A%2F%2Fzebra-day-cfg-us-west-2%2F<br>        - cell "us-west-2"<br>  - heading "Registered locations" [level=2]<br>  - paragraph: Includes explicitly registered external buckets and shared folders.<br>  - paragraph: No registered locations available.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ROUTES-DAG-1789588868635.txt ; I1-B-ROUTES-DAG-1789588868635.png

### ROUTES-DETAIL I1-B — PASS

- **timestamp**: 2026-09-16T20:01:09.085Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/artifacts/euid/M-DGX-TRW6
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / RECORD<br>  - heading "fixture.json" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - generic: object<br>  - code: M-DGX-TRW6<br>  - button "Download / open"<br>  - button "Share"<br>  - button "Edit metadata"<br>  - heading "Object" [level=2]<br>  - paragraph: — · object<br>  - heading "Metadata" [level=2]<br>  - generic: "{}"<br>  - complementary:<br>    - heading "Details" [level=2]<br>    - term: EUID<br>    - definition: M-DGX-TRW6<br>    - term: Owner<br>    - definition: johnm@lsmc.com<br>    - term: Created<br>    - definition: 9/16/2026<br>    - term: Producer<br>    - definition: dewey<br>    - term: Location<br>    - definition: s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/fixture.json<br>    - link "Open S3 Browser":<br>      - /url: /storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2F<br>    - heading "Access" [level=2]<br>    - paragraph: Metadata visibility and download access are managed independently.<br>    - button "Manage permissions"<br>    - button "Transfer ownership"<br>    - generic "Registration lifecycle"<br>    - generic "Recent activity"<br>    - generic "Technical details"<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ROUTES-DETAIL-1789588869085.txt ; I1-B-ROUTES-DETAIL-1789588869085.png

### ROUTES-GRAPH I1-B — PASS

- **timestamp**: 2026-09-16T20:01:09.242Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/graph
- **expected**: Page fully renders its expected content
- **observed**: - generic: DAY<br>- main:<br>  - heading "TapDB Object Graph" [level=1]<br>  - paragraph:<br>    - link "Open the TapDB graph explorer":<br>      - /url: /tapdb/graph<br>  - iframe<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac
- **evidence**: I1-B-ROUTES-GRAPH-1789588869242.txt ; I1-B-ROUTES-GRAPH-1789588869242.png

### ROUTES-ADMIN-SHARES I1-B — PASS

- **timestamp**: 2026-09-16T20:01:10.042Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/admin/shares
- **expected**: Page fully renders its expected content
- **observed**: KP None M-DGX-9XKP Users: none Domains: none Groups: none error 0 Details"':<br>        - cell "M-DGX-9YKN share:artifact:M-DGX-9XKP":<br>          - link "M-DGX-9YKN":<br>            - /url: /shares/M-DGX-9YKN<br>          - generic: share:artifact:M-DGX-9XKP<br>        - cell "None M-DGX-9XKP":<br>          - generic: None<br>          - generic: M-DGX-9XKP<br>        - 'cell "Users: none Domains: none Groups: none"':<br>          - generic: "Users: none"<br>          - generic: "Domains: none"<br>          - generic: "Groups: none"<br>        - cell<br>        - cell "error":<br>          - generic: error<br>        - cell "0"<br>        - cell "Details":<br>          - link "Details":<br>            - /url: /shares/M-DGX-9YKN<br>      - 'row "M-DGX-9YHS share:artifact:M-DGX-9XX2 None M-DGX-9XX2 Users: none Domains: none Groups: none error 0 Details"':<br>        - cell "M-DGX-9YHS share:artifact:M-DGX-9XX2":<br>          - link "M-DGX-9YHS":<br>            - /url: /shares/M-DGX-9YHS<br>          - generic: share:artifact:M-DGX-9XX2<br>        - cell "None M-DGX-9XX2":<br>          - generic: None<br>          - generic: M-DGX-9XX2<br>        - 'cell "Users: none Domains: none Groups: none"':<br>          - generic: "Users: none"<br>          - generic: "Domains: none"<br>          - generic: "Groups: none"<br>        - cell<br>        - cell "error":<br>          - generic: error<br>        - cell "0"<br>        - cell "Details":<br>          - link "Details":<br>            - /url: /shares/M-DGX-9YHS<br>  - heading "Tracked Roots" [level=3]<br>  - generic: Registered customer/collaborator roots. Registration does not scan S3 children.<br>  - generic: No tracked share roots are registered.<br>  - heading "Share Detail" [level=3]<br>  - generic: Open a share to inspect policy, mint an access package, or review audit decisions.<br>  - generic: Select a share to inspect policy and access history.<br>- contentinfo:<br>  - generic: Version 10.0.5<br>  - generic: Branch codex/dewey-labcore-910<br>  - generic: Tag 10.0.5<br>  - generic: Commit df6d4d0646fc1385c35ff2b6353478a46b4587ac<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-ROUTES-ADMIN-SHARES-1789588870042.txt ; I1-B-ROUTES-ADMIN-SHARES-1789588870042.png

### TAP-OVERVIEW I1-B — PASS

- **timestamp**: 2026-09-16T20:01:10.533Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/
- **expected**: Page fully renders its expected content
- **observed**: INSERT dewey R0-HG003-D0-0-D0-PCR-FREE-ILMN-NOVASEQ.pangenome_sr.spmd.sentpg.giabHC_x_clinvar_genes.rtg_vcfeval.bench.tsv":<br>        - cell "2026-09-16 20:00:03.878464+00:00"<br>        - cell "M-EDG-G3MJ":<br>          - link "M-EDG-G3MJ":<br>            - /url: /tapdb/object/M-EDG-G3MJ<br>        - cell "INSERT"<br>        - cell "dewey"<br>        - cell "R0-HG003-D0-0-D0-PCR-FREE-ILMN-NOVASEQ.pangenome_sr.spmd.sentpg.giabHC_x_clinvar_genes.rtg_vcfeval.bench.tsv"<br>      - 'row "2026-09-16 20:00:03.878464+00:00 M-XRF-982 INSERT dewey External identifier: pmcid/article"':<br>        - cell "2026-09-16 20:00:03.878464+00:00"<br>        - cell "M-XRF-982":<br>          - link "M-XRF-982":<br>            - /url: /tapdb/object/M-XRF-982<br>        - cell "INSERT"<br>        - cell "dewey"<br>        - 'cell "External identifier: pmcid/article"'<br>      - row "2026-09-16 20:00:03.878464+00:00 M-EDG-G3NG INSERT dewey artifact.import:ursa-dayoa-12-artifacts-20260710-08:child:27":<br>        - cell "2026-09-16 20:00:03.878464+00:00"<br>        - cell "M-EDG-G3NG":<br>          - link "M-EDG-G3NG":<br>            - /url: /tapdb/object/M-EDG-G3NG<br>        - cell "INSERT"<br>        - cell "dewey"<br>        - cell "artifact.import:ursa-dayoa-12-artifacts-20260710-08:child:27"<br>      - row "2026-09-16 20:00:03.878464+00:00 M-DGX-TTB7 INSERT dewey doi:doi:10.1002/ajpa.70010":<br>        - cell "2026-09-16 20:00:03.878464+00:00"<br>        - cell "M-DGX-TTB7":<br>          - link "M-DGX-TTB7":<br>            - /url: /tapdb/object/M-DGX-TTB7<br>        - cell "INSERT"<br>        - cell "dewey"<br>        - cell "doi:doi:10.1002/ajpa.70010"<br>      - row "2026-09-16 20:00:03.878464+00:00 M-DGX-TT9B UPDATE dewey pubmedcentral:pmcid:PMC11898561":<br>        - cell "2026-09-16 20:00:03.878464+00:00"<br>        - cell "M-DGX-TT9B":<br>          - link "M-DGX-TT9B":<br>            - /url: /tapdb/object/M-DGX-TT9B<br>        - cell "UPDATE"<br>        - cell "dewey"<br>        - cell "pubmedcentral:pmcid:PMC11898561"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-OVERVIEW-1789588870533.txt ; I1-B-TAP-OVERVIEW-1789588870533.png

### TAP-HELP I1-B — PASS

- **timestamp**: 2026-09-16T20:01:29.306Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/help
- **expected**: Page fully renders its expected content
- **observed**: b/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "TapDB GUI guide" [level=1]<br>  - paragraph: This is TapDB's single supported standalone and embedded web interface.<br>  - heading "Objects and lineage" [level=2]<br>  - paragraph: Use Search to find templates, instances, and lineage. Object pages show canonical relationships, validation evidence, and audit history. Administrators may create ordinary instances, repair governed JSON, change status, and create lineage. Core external-reference templates cannot be written through the generic forms.<br>  - heading "External references and discovery" [level=2]<br>  - paragraph: Federated TapDB references and opaque external identifiers are displayed separately. TapDB-object references can be followed by DAG-v2 federation clients; opaque identifiers are visible and exactly searchable but are never fetched or expanded.<br>  - heading "Operator tools" [level=2]<br>  - paragraph: Administrators can inspect readiness, schema inventory, Meridian governance, sanitized runtime information, query metrics, backups, restore reviews, and durable receipts. Mutation forms are explicit and fail closed.<br>  - heading "API" [level=2]<br>  - paragraph: The authenticated JSON surfaces mirror GUI operations. DAG v2 is the only graph protocol; DAG v1 and outbound proxy routes are not supported.<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-HELP-1789588889306.txt ; I1-B-TAP-HELP-1789588889306.png

### TAP-READINESS I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:01:29.522Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/help
- **expected**: Page fully renders its expected content
- **observed**: /tapdb/admin/readiness: Error: Browser Use cannot open https://dewey.day.lsmc.bio/tapdb/admin/readiness in tab 4. Browser reported: net::ERR_BLOCKED_BY_CLIENT
- **evidence**: I1-B-TAP-READINESS-1789588889522.txt

### TAP-INVENTORY I1-B — PASS

- **timestamp**: 2026-09-16T20:01:29.869Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/inventory
- **expected**: Page fully renders its expected content
- **observed**: instance_polymorphic_identity\", \"instance_prefix\", \"is_deleted\", \"is_singleton\", \"issuer_app_code\", \"json_addl\", \"json_addl_schema\", \"modified_dt\", \"name\", \"polymorphic_discriminator\", \"subtype\", \"tenant_id\", \"type\", \"uid\", \"validator_ref\", \"version\" ], \"inbox_message\": [ \"domain_code\", \"error_code\", \"error_message\", \"issuer_app_code\", \"json_addl\", \"message_machine_uuid\", \"payload\", \"processed_dt\", \"receipt_machine_uuid\", \"received_dt\", \"source_destination\", \"source_domain_code\", \"source_issuer_app_code\", \"status\", \"tenant_id\", \"uid\" ], \"outbox_event\": [ \"attempt_count\", \"canceled_dt\", \"claim_token\", \"claimed_by\", \"claimed_dt\", \"created_dt\", \"dead_letter_dt\", \"dedupe_key\", \"destination\", \"domain_code\", \"id\", \"issuer_app_code\", \"last_attempt_dt\", \"last_error\", \"last_http_status\", \"last_response_body_excerpt\", \"last_response_headers\", \"lease_expires_dt\", \"message_uid\", \"next_attempt_at\", \"receipt_machine_uuid\", \"receipt_processed_dt\", \"receipt_received_dt\", \"receipt_status\", \"rejected_dt\", \"status\", \"tenant_id\" ], \"outbox_event_attempt\": [ \"attempt_finished_dt\", \"attempt_no\", \"attempt_started_dt\", \"claim_token\", \"domain_code\", \"http_status\", \"issuer_app_code\", \"json_addl\", \"outbox_event_id\", \"receipt_machine_uuid\", \"receipt_processed_dt\", \"receipt_received_dt\", \"receipt_status\", \"response_body_excerpt\", \"response_headers\", \"retry_scheduled_dt\", \"tenant_id\", \"transport_error\", \"transport_status\", \"uid\", \"worker_id\" ], \"tapdb_identity_prefix_config\": [ \"domain_code\", \"entity\", \"issuer_app_code\", \"prefix\", \"updated_dt\" ], \"tapdb_legacy_outbox_mapping\": [ \"mapped_dt\", \"message_euid\", \"message_euid_seq\", \"message_uid\", \"old_event_id\", \"old_outbox_id\", \"source_sha256\" ], \"tapdb_runtime_principal_scope\": [] }"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-INVENTORY-1789588889869.txt ; I1-B-TAP-INVENTORY-1789588889869.png

### TAP-METRICS I1-B — PASS

- **timestamp**: 2026-09-16T20:01:30.218Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/metrics
- **expected**: Page fully renders its expected content
- **observed**:  - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "DB Metrics" [level=1]<br>  - table:<br>    - rowgroup:<br>      - row "Enabled True":<br>        - rowheader "Enabled"<br>        - cell "True"<br>      - row "File /run/dewey-production-state/state/tapdb/dewey/dewey-day/runtime/metrics/db_metrics_20260907.tsv":<br>        - rowheader "File"<br>        - cell "/run/dewey-production-state/state/tapdb/dewey/dewey-day/runtime/metrics/db_metrics_20260907.tsv"<br>      - row "Dropped 0":<br>        - rowheader "Dropped"<br>        - cell "0"<br>  - table:<br>    - rowgroup:<br>      - row "Path Method Count Total Seconds":<br>        - columnheader "Path"<br>        - columnheader "Method"<br>        - columnheader "Count"<br>        - columnheader "Total Seconds"<br>    - rowgroup:<br>      - row "4691":<br>        - cell<br>        - cell<br>        - cell "4691"<br>        - cell<br>      - row "/tapdb/ 22":<br>        - cell /tapdb/<br>        - cell<br>        - cell "22"<br>        - cell<br>      - row "/tapdb/graph 288":<br>        - cell "/tapdb/graph"<br>        - cell<br>        - cell "288"<br>        - cell<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-METRICS-1789588890218.txt ; I1-B-TAP-METRICS-1789588890218.png

### TAP-RUNTIME I1-B — PASS

- **timestamp**: 2026-09-16T20:01:30.585Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/runtime
- **expected**: Page fully renders its expected content
- **observed**: ics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Sanitized Runtime Information" [level=1]<br>  - paragraph: This is the same payload exposed by the CLI and authenticated API.<br>  - heading "package" [level=2]<br>  - generic: "{ \"name\": \"daylily-tapdb\", \"version\": \"10.1.1rc1\" }"<br>  - heading "python" [level=2]<br>  - generic: "{ \"implementation\": \"cpython\", \"version\": \"3.12.14\" }"<br>  - heading "meridian" [level=2]<br>  - generic: "{ \"package\": \"meridian-euid\", \"version\": \"0.4.8\" }"<br>  - heading "git" [level=2]<br>  - generic: "{ \"branch\": null, \"commit\": null, \"dirty\": null, \"tag\": null }"<br>  - heading "config" [level=2]<br>  - generic: "{ \"config_version\": 4, \"exists\": true, \"path\": \"/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml\", \"sha256\": \"987b25f1659a1e72593bd4231307b1f7f6c7122d5cb20193c3681ba41a2fe353\", \"target\": \"explicit\" }"<br>  - heading "database" [level=2]<br>  - generic: "{ \"database\": \"dewey_prod_tapdb10\", \"engine_type\": \"aurora\", \"host\": \"dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com\", \"port\": \"5432\", \"schema_name\": \"tapdb_dewey_lsmcok1_local\", \"server_version\": \"psql exit 2\", \"status\": \"error\" }"<br>  - heading "scope" [level=2]<br>  - generic: "{ \"client_id\": \"dewey\", \"database_name\": \"dewey-day\", \"domain_code\": \"M\", \"owner_repo_name\": \"dewey\" }"<br>  - heading "storage" [level=2]<br>  - generic: "{ \"aws_profile\": \"lsmc\", \"region\": \"us-west-2\", \"s3_buckets\": [], \"uris\": [] }"<br>  - heading "ui" [level=2]<br>  - generic: "{ \"pid\": null, \"port\": \"8910\", \"running\": false, \"status\": \"stopped\" }"<br>  - heading "dag" [level=2]<br>  - generic: "{ \"eligible\": false, \"service_id\": null, \"status\": \"not_configured\" }"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-RUNTIME-1789588890585.txt ; I1-B-TAP-RUNTIME-1789588890585.png

### TAP-BACKUPS I1-B — PASS

- **timestamp**: 2026-09-16T20:01:30.875Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/backups
- **expected**: Page fully renders its expected content
- **observed**: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Backups" [level=1]<br>  - paragraph:<br>    - strong: "Target:"<br>    - text: dewey/dewey-day/tapdb_dewey_lsmcok1_local@dewey_prod_tapdb10<br>  - strong: "Status: never_run"<br>  - text: No successful backup has ever been recorded for this target.<br>  - paragraph:<br>    - text: No cadence is configured, so this target is never reported as stale. Set<br>    - code: backup.expected_interval_hours<br>    - text: to enable staleness reporting.<br>  - heading "Create a backup" [level=2]<br>  - paragraph: Reads the database only; nothing is modified.<br>  - text: Class<br>  - combobox "Class":<br>    - option "full (logical dump)" [selected]<br>    - option "template-pack (definitions only)"<br>  - text: Note<br>  - textbox "Note":<br>    - /placeholder: optional<br>  - checkbox "Acknowledge measured schema drift (requires a verified source contract)"<br>  - text: Acknowledge measured schema drift (requires a verified source contract)<br>  - text: Reviewed source-contract JSON (required for historical or drifted schemas)<br>  - textbox "Reviewed source-contract JSON (required for historical or drifted schemas)"<br>  - text: Sealed recovery-family JSON (for recovery across replacements)<br>  - textbox "Sealed recovery-family JSON (for recovery across replacements)"<br>  - paragraph: A database backup does not include service configuration, runtime files, credentials or principal artifacts.<br>  - button "Create backup"<br>  - heading "Backups (0)" [level=2]<br>  - paragraph: "Storage: file:///opt/dewey/day/releases/9.0.0/backups"<br>  - paragraph: No backups have been taken for this target.<br>  - heading "Recent activity" [level=2]<br>  - paragraph: No lifecycle operations have been recorded.<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-BACKUPS-1789588890875.txt ; I1-B-TAP-BACKUPS-1789588890875.png

### TAP-BACKUP-MUTATIONS I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:01:30.909Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/backups
- **inputs**: Backup class/note/source-contract/recovery-family inputs inspected; no create/restore/purge submitted.
- **expected**: Review backup controls without data operations
- **observed**: Backup class/note/source-contract/recovery-family inputs inspected; no create/restore/purge submitted.
- **evidence**: I1-B-TAP-BACKUP-MUTATIONS-1789588890909.txt

### TAP-SEARCH I1-B — PASS

- **timestamp**: 2026-09-16T20:01:31.206Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-DGX-TST9&record_type=instance
- **expected**: Page fully renders its expected content
- **observed**: link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Search" [level=1]<br>  - textbox "EUID, name, type, status": M-DGX-TST9<br>  - combobox:<br>    - option "all"<br>    - option "template"<br>    - option "instance" [selected]<br>    - option "lineage"<br>  - textbox "name contains"<br>  - textbox "EUID contains"<br>  - textbox "category"<br>  - textbox "type"<br>  - textbox "subtype"<br>  - button "Search"<br>  - heading "Results" [level=2]<br>  - table:<br>    - rowgroup:<br>      - row "EUID Kind Name Type Status":<br>        - columnheader "EUID"<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Type"<br>        - columnheader "Status"<br>    - rowgroup:<br>      - row "M-DGX-TST9 instance Dewey GUI audit 20260916 I1-B prefix data/artifact/generic active":<br>        - cell "M-DGX-TST9":<br>          - link "M-DGX-TST9":<br>            - /url: /tapdb/object/M-DGX-TST9<br>        - cell "instance"<br>        - cell "Dewey GUI audit 20260916 I1-B prefix"<br>        - cell "data/artifact/generic"<br>        - cell "active"<br>      - row "M-DGX-TSV7 instance Access for M-DGX-TST9 access/registry_policy/generic active":<br>        - cell "M-DGX-TSV7":<br>          - link "M-DGX-TSV7":<br>            - /url: /tapdb/object/M-DGX-TSV7<br>        - cell "instance"<br>        - cell "Access for M-DGX-TST9"<br>        - cell "access/registry_policy/generic"<br>        - cell "active"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-SEARCH-1789588891206.txt ; I1-B-TAP-SEARCH-1789588891206.png

### TAP-SEARCH-TEMPLATE I1-B — PASS

- **timestamp**: 2026-09-16T20:01:31.495Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-DGX-1A&record_type=template
- **expected**: Page fully renders its expected content
- **observed**: r:<br>  - link "Dewey / TapDB":<br>    - /url: /tapdb/<br>  - navigation:<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Search" [level=1]<br>  - textbox "EUID, name, type, status": M-DGX-1A<br>  - combobox:<br>    - option "all"<br>    - option "template" [selected]<br>    - option "instance"<br>    - option "lineage"<br>  - textbox "name contains"<br>  - textbox "EUID contains"<br>  - textbox "category"<br>  - textbox "type"<br>  - textbox "subtype"<br>  - button "Search"<br>  - heading "Results" [level=2]<br>  - table:<br>    - rowgroup:<br>      - row "EUID Kind Name Type Status":<br>        - columnheader "EUID"<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Type"<br>        - columnheader "Status"<br>    - rowgroup:<br>      - row "M-DGX-1A template Dewey Artifact data/artifact/generic active":<br>        - cell "M-DGX-1A":<br>          - link "M-DGX-1A":<br>            - /url: /tapdb/object/M-DGX-1A<br>        - cell "template"<br>        - cell "Dewey Artifact"<br>        - cell "data/artifact/generic"<br>        - cell "active"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-SEARCH-TEMPLATE-1789588891495.txt ; I1-B-TAP-SEARCH-TEMPLATE-1789588891495.png

### TAP-SEARCH-LINEAGE I1-B — PASS

- **timestamp**: 2026-09-16T20:01:31.772Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?q=M-EDG-G28C&record_type=lineage
- **expected**: Page fully renders its expected content
- **observed**: ibrary":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Search" [level=1]<br>  - textbox "EUID, name, type, status": M-EDG-G28C<br>  - combobox:<br>    - option "all"<br>    - option "template"<br>    - option "instance"<br>    - option "lineage" [selected]<br>  - textbox "name contains"<br>  - textbox "EUID contains"<br>  - textbox "category"<br>  - textbox "type"<br>  - textbox "subtype"<br>  - button "Search"<br>  - heading "Results" [level=2]<br>  - table:<br>    - rowgroup:<br>      - row "EUID Kind Name Type Status":<br>        - columnheader "EUID"<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Type"<br>        - columnheader "Status"<br>    - rowgroup:<br>      - row "M-EDG-G28C lineage M-DGX-TR3S->M-DGX-TR4Q:registry_policy generic/lineage/instance_lineage active":<br>        - cell "M-EDG-G28C":<br>          - link "M-EDG-G28C":<br>            - /url: /tapdb/object/M-EDG-G28C<br>        - cell "lineage"<br>        - cell "M-DGX-TR3S->M-DGX-TR4Q:registry_policy"<br>        - cell "generic/lineage/instance_lineage"<br>        - cell "active"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-SEARCH-LINEAGE-1789588891772.txt ; I1-B-TAP-SEARCH-LINEAGE-1789588891772.png

### TAP-SEARCH-PAGINATION I1-B — PASS

- **timestamp**: 2026-09-16T20:01:32.360Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/search?record_type=all&limit=25&cursor=eyJraW5kIjoiaW5zdGFuY2UiLCJ1aWQiOjl9
- **inputs**: Next page link advanced to later instances; query contains continuation cursor.
- **expected**: Continuation changes displayed records
- **observed**: Next page link advanced to later instances; query contains continuation cursor.
- **evidence**: I1-B-TAP-SEARCH-PAGINATION-1789588892360.txt ; I1-B-TAP-SEARCH-PAGINATION-1789588892360.png

### TAP-OBJECT I1-B — PASS

- **timestamp**: 2026-09-16T20:01:32.821Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TST9
- **expected**: Page fully renders its expected content
- **observed**: wey::prefix:prefix:folder:s3:lsmc-dewey-0:gui-audit/20260916T183133Z/I1-B/::\"}"':<br>        - cell "2026-09-16 19:50:29.644814+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "json_addl"<br>        - 'cell "{\"key\": \"gui-audit/20260916T183133Z/I1-B/\", \"bucket\": \"lsmc-dewey-0\", \"metadata\": {}, \"audit_log\": [], \"checksums\": {}, \"node_kind\": \"folder\", \"created_at\": \"2026-09-16T19:50:29.688835Z\", \"properties\": {}, \"source_uri\": \"s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/\", \"version_id\": null, \"description\": \"\", \"import_mode\": \"register\", \"is_terminal\": false, \"storage_uri\": \"s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/\", \"storage_kind\": \"prefix\", \"action_groups\": {}, \"artifact_type\": \"prefix\", \"storage_status\": \"registered\", \"producer_system\": \"dewey\", \"storage_backend\": \"s3\", \"created_by_email\": \"johnm@lsmc.com\", \"updated_by_email\": \"johnm@lsmc.com\", \"original_filename\": \"Dewey GUI audit 20260916 I1-B prefix\", \"artifact_identity_key\": \"dewey::prefix:prefix:folder:s3:lsmc-dewey-0:gui-audit/20260916T183133Z/I1-B/::\"}"'<br>      - row "2026-09-16 19:50:29.644814+00:00 dewey UPDATE bstatus active":<br>        - cell "2026-09-16 19:50:29.644814+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "bstatus"<br>        - cell "active"<br>      - row "2026-09-16 19:50:29.644814+00:00 dewey UPDATE created_dt 2026-09-16T19:50:29.644814+00:00":<br>        - cell "2026-09-16 19:50:29.644814+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "created_dt"<br>        - cell "2026-09-16T19:50:29.644814+00:00"<br>      - row "2026-09-16 19:50:29.644814+00:00 dewey UPDATE modified_dt 2026-09-16T19:50:29.644814+00:00":<br>        - cell "2026-09-16 19:50:29.644814+00:00"<br>        - cell "dewey"<br>        - cell "UPDATE"<br>        - cell "modified_dt"<br>        - cell "2026-09-16T19:50:29.644814+00:00"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-OBJECT-1789588892821.txt ; I1-B-TAP-OBJECT-1789588892821.png

### TAP-OBJECT-JSON I1-B — PASS

- **timestamp**: 2026-09-16T20:01:47.166Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TST9
- **inputs**: Format and Compact controls exercised, no persistent repair submitted.
- **expected**: Client-side JSON editor formatting works
- **observed**: Format and Compact controls exercised, no persistent repair submitted.
- **evidence**: I1-B-TAP-OBJECT-JSON-1789588907166.txt

### TAP-OBJECT-MUTATIONS I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:01:47.191Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TST9
- **inputs**: Set Name, Set Status, Add Lineage and Create repair present; no Apply.
- **expected**: Raw mutation controls visible, no submission
- **observed**: Set Name, Set Status, Add Lineage and Create repair present; no Apply.
- **evidence**: I1-B-TAP-OBJECT-MUTATIONS-1789588907191.txt

### TAP-AUDIT I1-B — PASS

- **timestamp**: 2026-09-16T20:01:47.788Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/audit?euid=M-DGX-TST9&changed_by=dewey&operation_type=INSERT&limit=2
- **expected**: Page fully renders its expected content
- **observed**:    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Audit explorer" [level=1]<br>  - textbox "exact object EUID": M-DGX-TST9<br>  - textbox "exact actor": dewey<br>  - combobox:<br>    - option "ALL"<br>    - option "INSERT" [selected]<br>    - option "UPDATE"<br>    - option "DELETE"<br>  - spinbutton: "2"<br>  - button "Query"<br>  - table:<br>    - rowgroup:<br>      - row "Time EUID Operation Actor Kind Name Change":<br>        - columnheader "Time"<br>        - columnheader "EUID"<br>        - columnheader "Operation"<br>        - columnheader "Actor"<br>        - columnheader "Kind"<br>        - columnheader "Name"<br>        - columnheader "Change"<br>    - rowgroup:<br>      - row "2026-09-16 19:50:29.644814+00:00 M-DGX-TST9 INSERT dewey data/artifact/generic Dewey GUI audit 20260916 I1-B prefix":<br>        - cell "2026-09-16 19:50:29.644814+00:00"<br>        - cell "M-DGX-TST9":<br>          - link "M-DGX-TST9":<br>            - /url: /tapdb/object/M-DGX-TST9<br>        - cell "INSERT"<br>        - cell "dewey"<br>        - cell "data/artifact/generic"<br>        - cell "Dewey GUI audit 20260916 I1-B prefix"<br>        - cell:<br>          - generic "values"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-AUDIT-1789588907788.txt ; I1-B-TAP-AUDIT-1789588907788.png

### TAP-MERIDIAN I1-B — PASS

- **timestamp**: 2026-09-16T20:01:48.075Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TST9&prefix=
- **expected**: Page fully renders its expected content
- **observed**:  /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Admin":<br>      - /url: /admin<br>    - link "Overview":<br>      - /url: /tapdb/admin/overview<br>    - link "Search":<br>      - /url: /tapdb/search<br>    - link "Graph":<br>      - /url: /tapdb/graph<br>    - link "Templates":<br>      - /url: /tapdb/templates<br>    - link "Audit":<br>      - /url: /tapdb/audit<br>    - link "Help":<br>      - /url: /tapdb/help<br>    - link "Readiness":<br>      - /url: /tapdb/admin/readiness<br>    - link "Inventory":<br>      - /url: /tapdb/admin/inventory<br>    - link "Meridian":<br>      - /url: /tapdb/admin/meridian<br>    - link "Metrics":<br>      - /url: /tapdb/admin/metrics<br>    - link "Runtime":<br>      - /url: /tapdb/admin/runtime<br>    - link "Backups":<br>      - /url: /tapdb/admin/backups<br>    - link "Sign out":<br>      - /url: /auth/logout<br>  - generic: johnm@lsmc.com · admin<br>- main:<br>  - heading "Meridian" [level=1]<br>  - table:<br>    - rowgroup:<br>      - row "Domain M":<br>        - rowheader "Domain"<br>        - cell "M"<br>      - row "Owner Repo dewey":<br>        - rowheader "Owner Repo"<br>        - cell "dewey"<br>      - row "Domain Registry /opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json":<br>        - rowheader "Domain Registry"<br>        - cell "/opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json"<br>      - row "Prefix Registry /opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json":<br>        - rowheader "Prefix Registry"<br>        - cell "/opt/dayhoff/deployments/day/tapdb-registry/prefix_ownership_registry.json"<br>      - row "Public Registry https://github.com/lsmc-bio/meridian-registry":<br>        - rowheader "Public Registry"<br>        - cell "https://github.com/lsmc-bio/meridian-registry"<br>      - row "Public Registry Version 0.1.1":<br>        - rowheader "Public Registry Version"<br>        - cell "0.1.1"<br>  - textbox "EUID": M-DGX-TST9<br>  - textbox "prefix"<br>  - button "Validate"<br>  - generic: "EUID valid for M: True"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-MERIDIAN-1789588908075.txt ; I1-B-TAP-MERIDIAN-1789588908075.png

### TAP-THEME I1-B — PASS

- **timestamp**: 2026-09-16T20:01:48.106Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TST9&prefix=
- **inputs**: Dark selected; original restored after receipt.
- **expected**: Theme choice renders
- **observed**: Dark selected; original restored after receipt.
- **evidence**: I1-B-TAP-THEME-1789588908106.txt ; I1-B-TAP-THEME-1789588908106.png

### TAP-CONTEXT-HELP I1-B — PASS

- **timestamp**: 2026-09-16T20:01:59.936Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/admin/meridian?euid=M-DGX-TST9&prefix=
- **inputs**: Context help copied and inspected; no CLI equivalent for Meridian.
- **expected**: Help clipboard matches displayed context
- **observed**: Context help copied and inspected; no CLI equivalent for Meridian.
- **evidence**: I1-B-TAP-CONTEXT-HELP-1789588919936.txt

### TAP-TEMPLATES I1-B — PASS

- **timestamp**: 2026-09-16T20:02:00.553Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates?category=data
- **expected**: Page fully renders its expected content
- **observed**: - textbox "/absolute/path/to/template-pack.json"<br>  - button "Export New Repository Pack"<br>  - paragraph: Server-side repository export requires an explicit absolute path and writes both the pack and its immutable provenance receipt. Existing files are never overwritten.<br>  - table:<br>    - rowgroup:<br>      - row "EUID Name Code Instance Prefix Validator Repository":<br>        - columnheader "EUID"<br>        - columnheader "Name"<br>        - columnheader "Code"<br>        - columnheader "Instance Prefix"<br>        - columnheader "Validator"<br>        - columnheader "Repository"<br>        - columnheader<br>        - columnheader<br>    - rowgroup:<br>      - row "M-DGX-1A Dewey Artifact data/artifact/generic/1.0 DGX UNIVERSAL_PASS@1 pending Create Build New Template":<br>        - cell "M-DGX-1A":<br>          - link "M-DGX-1A":<br>            - /url: /tapdb/object/M-DGX-1A<br>        - cell "Dewey Artifact"<br>        - cell "data/artifact/generic/1.0"<br>        - cell "DGX"<br>        - cell "UNIVERSAL_PASS@1":<br>          - code: UNIVERSAL_PASS@1<br>        - cell "pending"<br>        - cell "Create":<br>          - link "Create":<br>            - /url: /tapdb/create/M-DGX-1A<br>        - cell "Build New Template":<br>          - link "Build New Template":<br>            - /url: /tapdb/templates/new?seed_euid=M-DGX-1A<br>      - row "M-DGX-28 Dewey Artifact Set data/artifact_set/generic/1.0 DGX UNIVERSAL_PASS@1 pending Create Build New Template":<br>        - cell "M-DGX-28":<br>          - link "M-DGX-28":<br>            - /url: /tapdb/object/M-DGX-28<br>        - cell "Dewey Artifact Set"<br>        - cell "data/artifact_set/generic/1.0"<br>        - cell "DGX"<br>        - cell "UNIVERSAL_PASS@1":<br>          - code: UNIVERSAL_PASS@1<br>        - cell "pending"<br>        - cell "Create":<br>          - link "Create":<br>            - /url: /tapdb/create/M-DGX-28<br>        - cell "Build New Template":<br>          - link "Build New Template":<br>            - /url: /tapdb/templates/new?seed_euid=M-DGX-28<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-TEMPLATES-1789588920553.txt ; I1-B-TAP-TEMPLATES-1789588920553.png

### TAP-PACK-INVENTORY I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:02:20.031Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates?category=data
- **inputs**: Repository pack inventory form reviewed; no verified absolute server path supplied.
- **expected**: Explicit deployed pack path required
- **observed**: Repository pack inventory form reviewed; no verified absolute server path supplied.
- **evidence**: I1-B-TAP-PACK-INVENTORY-1789588940031.txt

### TAP-PACK-EXPORT I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:02:20.037Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates?category=data
- **inputs**: Absolute-path export inspected, no submission.
- **expected**: Export interface visible; no server-side file writes
- **observed**: Absolute-path export inspected, no submission.
- **evidence**: I1-B-TAP-PACK-EXPORT-1789588940037.txt

### TAP-INSTANCE-CREATE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:02:20.465Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/create/M-DGX-1A
- **inputs**: Name, children and JSON properties form present; no raw instance created.
- **expected**: Raw create form renders
- **observed**: Name, children and JSON properties form present; no raw instance created.
- **evidence**: I1-B-TAP-INSTANCE-CREATE-1789588940465.txt

### TAP-TEMPLATE-DOWNLOAD I1-B — PASS

- **timestamp**: 2026-09-16T20:02:32.983Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates/new?seed_euid=M-DGX-1A
- **inputs**: Browser delivered 515 bytes; SHA256 7074c06f36a3fb33390673787b3a20632cf758d130dd077fa338496d46973532; retained I1-B-template-pack.json.
- **expected**: Browser delivers valid template JSON
- **observed**: Browser delivered 515 bytes; SHA256 7074c06f36a3fb33390673787b3a20632cf758d130dd077fa338496d46973532; retained I1-B-template-pack.json.
- **evidence**: I1-B-TAP-TEMPLATE-DOWNLOAD-1789588952983.txt

### TAP-TEMPLATE-BUILDER I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:02:33.258Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates/new?seed_euid=M-DGX-1A
- **inputs**: Build JSON exercised; Save excluded from schema mutation scope.
- **expected**: Builder controls render and generate JSON
- **observed**: Build JSON exercised; Save excluded from schema mutation scope.
- **evidence**: I1-B-TAP-TEMPLATE-BUILDER-1789588953258.txt

### TAP-TEMPLATE-VALIDATE I1-B — FAIL

- **timestamp**: 2026-09-16T20:02:33.644Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/templates/validate
- **inputs**: Second reproduction: Origin not allowed. D05.
- **expected**: Read-only validation returns structured result
- **observed**: Second reproduction: Origin not allowed. D05.
- **evidence**: I1-B-TAP-TEMPLATE-VALIDATE-1789588953644.txt ; I1-B-TAP-TEMPLATE-VALIDATE-1789588953644.png

### TAP-OBJECT-GRAPH I1-B — PASS

- **timestamp**: 2026-09-16T20:02:34.341Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/object/M-DGX-TST9/graph
- **expected**: Page fully renders its expected content
- **observed**: text: M-DGX-TST9<br>  - generic: Depth<br>  - spinbutton "Depth": "4"<br>  - generic: Maximum Nodes<br>  - spinbutton "Maximum Nodes": "1000"<br>  - generic: Maximum Edges<br>  - spinbutton "Maximum Edges": "500"<br>  - button "Load Graph"<br>  - button "Fit"<br>  - heading "🔎 Search & Find" [level=3]<br>  - generic: Fuzzy Search<br>  - textbox "Fuzzy Search":<br>    - /placeholder: Match id, name, type, subtype<br>    - text: GUI audit<br>  - generic: Find Exact EUID<br>  - textbox "Find Exact EUID":<br>    - /placeholder: Exact EUID in current graph<br>  - button "Apply Search"<br>  - button "Find"<br>  - heading "🧰 Filters" [level=3]<br>  - generic: Connected Edge Count ≤<br>  - slider "Connected Edge Count ≤": "1"<br>  - generic: "1"<br>  - generic: Relative Distance (0 = all)<br>  - slider "Relative Distance (0 = all)": "0"<br>  - generic: "0"<br>  - generic: Type Visibility<br>  - generic: Load graph to populate.<br>  - generic: Subtype Muting<br>  - generic: Load graph to populate.<br>  - heading "⚙️ Layout" [level=3]<br>  - generic: Layout Type<br>  - combobox "Layout Type":<br>    - option "Dagre (Hierarchical)"<br>    - option "CoSE (Force-directed)"<br>    - option "Breadth First"<br>    - option "Circle"<br>    - option "Grid" [selected]<br>  - heading "⌨️ Graph Gestures" [level=3]<br>  - strong: D + right click<br>  - text: ": delete node or edge"<br>  - strong: 3x left click node<br>  - text: ": child-wave glow (pink)"<br>  - strong: 3x right click node<br>  - text: ": parent-wave glow (aqua)"<br>  - strong: L + left click node<br>  - text: ": pick child, then click parent to create edge"<br>  - strong: N + left click node<br>  - text: ": neighborhood highlight"<br>  - generic: Ready.<br>  - heading "🎨 Legend" [level=3]<br>  - generic: No visible nodes.<br>  - heading "💾 Export" [level=3]<br>  - button "Save DAG" [disabled]<br>  - generic: Mermaid<br>  - generic: Load a graph to generate Mermaid.<br>  - heading "📋 Details" [level=3]<br>  - paragraph: Click a node or edge to see details<br>  - generic "Nodes and edges"<br>  - generic "Payload JSON"<br>- contentinfo: TapDB 10.1.1rc1<br>- text: Theme<br>- combobox "Theme":<br>  - option "original" [selected]<br>  - option "light"<br>  - option "dark"<br>  - option "CBF"<br>  - option "S.SF"<br>  - option "Viridis"<br>  - option "Viridis Dark"<br>- checkbox "Global" [checked]<br>- text: Global<br>- button "?"
- **evidence**: I1-B-TAP-OBJECT-GRAPH-1789588954341.txt ; I1-B-TAP-OBJECT-GRAPH-1789588954341.png

### TAP-OBJECT-GRAPH I1-B — PASS

- **timestamp**: 2026-09-16T20:03:12.940Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TST9
- **inputs**: Loaded 6 nodes and5 edges around M-DGX-TST9.
- **expected**: Persisted lineage loads
- **observed**: Loaded 6 nodes and5 edges around M-DGX-TST9.
- **evidence**: I1-B-TAP-OBJECT-GRAPH-1789588992940.txt ; I1-B-TAP-OBJECT-GRAPH-1789588992940.png

### TAP-GRAPH I1-B — PASS

- **timestamp**: 2026-09-16T20:03:13.065Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TST9
- **inputs**: Embedded graph successfully loaded fixture graph.
- **expected**: Graph page renders nodes/edges
- **observed**: Embedded graph successfully loaded fixture graph.
- **evidence**: I1-B-TAP-GRAPH-1789588993065.txt

### TAP-GRAPH-CONTROLS I1-B — PASS

- **timestamp**: 2026-09-16T20:03:14.350Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TST9
- **inputs**: Fuzzy I1-B, exact persisted prefix, center, distance and Circle/Fit exercised.
- **expected**: Search/find/center/filter/layout respond
- **observed**: Fuzzy I1-B, exact persisted prefix, center, distance and Circle/Fit exercised.
- **evidence**: I1-B-TAP-GRAPH-CONTROLS-1789588994350.txt ; I1-B-TAP-GRAPH-CONTROLS-1789588994350.png

### TAP-GRAPH-MUTATIONS I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:03:14.418Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TST9
- **inputs**: Delete and lineage-creation gestures inspected only.
- **expected**: Mutation gestures documented, no execution
- **observed**: Delete and lineage-creation gestures inspected only.
- **evidence**: I1-B-TAP-GRAPH-MUTATIONS-1789588994418.txt

### LIT-PAGE-NEXT I1-B — PASS

- **timestamp**: 2026-09-16T20:03:14.795Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=genomics&page=2
- **inputs**: Next page URL https://dewey.day.lsmc.bio/literature?q=genomics&page=2; inspect receipt for rows.
- **expected**: Second page renders more results
- **observed**: Next page URL https://dewey.day.lsmc.bio/literature?q=genomics&page=2; inspect receipt for rows.
- **evidence**: I1-B-LIT-PAGE-NEXT-1789588994795.txt ; I1-B-LIT-PAGE-NEXT-1789588994795.png

### TAP-GRAPH-EXPORT I1-B — PASS

- **timestamp**: 2026-09-16T20:03:41.777Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/tapdb/graph?depth=4&max_nodes=1000&max_edges=500&start_euid=M-DGX-TST9
- **inputs**: Delivered 7693 bytes,6nodes5edges SHA256 8cd08c997cc976418b7fce2103caee1552a01d2f494149ac14cedc1d2aad1eff; retained I1-B-dag-export.json.
- **expected**: Browser delivers usable graph JSON
- **observed**: Delivered 7693 bytes,6nodes5edges SHA256 8cd08c997cc976418b7fce2103caee1552a01d2f494149ac14cedc1d2aad1eff; retained I1-B-dag-export.json.
- **evidence**: I1-B-TAP-GRAPH-EXPORT-1789589021777.txt

### LIT-EMPTY I1-B — PASS

- **timestamp**: 2026-09-16T20:03:41.848Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/literature?q=deweyguiaudit20260916nomatch&page=1
- **inputs**: Synthetic nonexistent query shows No matching items.
- **expected**: Empty query result rendered explicitly
- **observed**: Synthetic nonexistent query shows No matching items.
- **evidence**: I1-B-LIT-EMPTY-1789589021848.txt ; I1-B-LIT-EMPTY-1789589021848.png

### STORE-BREADCRUMBS I1-B — PASS

- **timestamp**: 2026-09-16T20:04:10.895Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-dewey-0%2Fgui-audit%2F20260916T183133Z%2FI1-B%2Fnested%2F
- **inputs**: nested/ contains one64B unregistered fixture.json; ancestor I1-B link available.
- **expected**: Nested folder and ancestor breadcrumbs work
- **observed**: nested/ contains one64B unregistered fixture.json; ancestor I1-B link available.
- **evidence**: I1-B-STORE-BREADCRUMBS-1789589050895.txt ; I1-B-STORE-BREADCRUMBS-1789589050895.png

### STORE-ERROR I1-B — PASS

- **timestamp**: 2026-09-16T20:04:14.500Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=https%3A%2F%2Fexample.com%2F
- **inputs**: An explicit s3:// URI is required displayed.
- **expected**: Non-S3 input rejected clearly
- **observed**: An explicit s3:// URI is required displayed.
- **evidence**: I1-B-STORE-ERROR-1789589054500.txt

### STORE-PAGE-NEXT I1-B — PASS

- **timestamp**: 2026-09-16T20:04:20.048Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F&token=[REDACTED]
- **inputs**: Next page displayed 31 entries; continuation URL changed.
- **expected**: Next advances bounded root listing
- **observed**: Next page displayed 31 entries; continuation URL changed.
- **evidence**: I1-B-STORE-PAGE-NEXT-1789589060048.txt ; I1-B-STORE-PAGE-NEXT-1789589060048.png

### STORE-BUCKET-LINKS I1-B — PASS

- **timestamp**: 2026-09-16T20:04:20.140Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F&token=[REDACTED]
- **inputs**: All60bucket links attempted separately;59rendered,1explicit S3deny. Individual receipts are authoritative.
- **expected**: Every listed bucket root attempted
- **observed**: All60bucket links attempted separately;59rendered,1explicit S3deny. Individual receipts are authoritative.
- **evidence**: I1-B-STORE-BUCKET-LINKS-1789589060140.txt

### ACCOUNT-PAGE I1-B — PASS

- **timestamp**: 2026-09-16T20:04:20.518Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **expected**: Page fully renders its expected content
- **observed**: - banner:<br>  - link "dewey ARTIFACT LIBRARY":<br>    - /url: /ui<br>    - text: dewey<br>    - generic: ARTIFACT LIBRARY<br>  - navigation "Primary":<br>    - link "Library":<br>      - /url: /ui<br>    - link "S3 Browser":<br>      - /url: /storage<br>    - link "Sets":<br>      - /url: /sets<br>    - link "Sharing":<br>      - /url: /shares<br>    - link "Literature":<br>      - /url: /literature<br>  - link "+ Add":<br>    - /url: /add<br>  - link "Admin":<br>    - /url: /admin<br>  - link "Account":<br>    - /url: /account<br>- main:<br>  - paragraph: DEWEY / ACCOUNT<br>  - heading "Account" [level=1]<br>  - generic: Open an EUID<br>  - textbox "Open an EUID":<br>    - /placeholder: Open a Dewey EUID<br>  - button "Open"<br>  - heading "CLI and API access" [level=2]<br>  - paragraph: Create a personal token to use the same authorized EUID operations from your terminal.<br>  - generic: export DEWEY_API_URL="https://dewey.day.lsmc.bio" export DEWEY_API_TOKEN_FILE="/absolute/private/token-file" dewey artifacts get <EUID> dewey artifacts contents <PREFIX_EUID> dewey artifacts access <EUID><br>  - button "Create token"<br>  - heading "Your tokens" [level=2]<br>  - paragraph: No personal tokens.<br>- contentinfo:<br>  - generic: Dewey 10.0.5 · One EUID per object, prefix, or set<br>  - link "API reference":<br>    - /url: /docs<br>  - link "CLI access":<br>    - /url: /account<br>  - link "Sign out":<br>    - /url: /auth/logout
- **evidence**: I1-B-ACCOUNT-PAGE-1789589060518.txt ; I1-B-ACCOUNT-PAGE-1789589060518.png

### ACCOUNT-TOKEN-FORM I1-B — PASS

- **timestamp**: 2026-09-16T20:04:20.807Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **inputs**: Form inspected; no credential issued.
- **expected**: Token form and read-only duration inputs visible
- **observed**: Form inspected; no credential issued.
- **evidence**: I1-B-ACCOUNT-TOKEN-FORM-1789589060807.txt ; I1-B-ACCOUNT-TOKEN-FORM-1789589060807.png

### ACCOUNT-TOKEN-CREATE I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:04:20.850Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **inputs**: Pending confirmation from prepared I1-A form remains ungranted.
- **expected**: Action-time credential confirmation required
- **observed**: Pending confirmation from prepared I1-A form remains ungranted.
- **evidence**: I1-B-ACCOUNT-TOKEN-CREATE-1789589060850.txt

### ACCOUNT-TOKEN-REVOKE I1-B — INSPECTED_ONLY

- **timestamp**: 2026-09-16T20:04:20.855Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/account
- **inputs**: No tokens exist in account; no revocation.
- **expected**: Revocation execution excluded
- **observed**: No tokens exist in account; no revocation.
- **evidence**: I1-B-ACCOUNT-TOKEN-REVOKE-1789589060855.txt

### ROUTES-DOCS I1-B — REVIEW

- **timestamp**: 2026-09-16T20:04:21.238Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/docs
- **expected**: Page fully renders its expected content
- **observed**: - generic: loading
- **evidence**: I1-B-ROUTES-DOCS-1789589061238.txt ; I1-B-ROUTES-DOCS-1789589061238.png

### ROUTES-DOCS I1-B — PASS

- **timestamp**: 2026-09-16T20:04:48.416Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/docs#/EUID%20registry/resolve_api_v1_records__euid__get
- **inputs**: Dewey10.0.5 OAS3.1 loaded; GET record schema expanded.
- **expected**: Documentation renders and schema expands
- **observed**: Dewey10.0.5 OAS3.1 loaded; GET record schema expanded.
- **evidence**: I1-B-ROUTES-DOCS-1789589088416.txt

### LOGIN-LOGOUT I1-B — PASS

- **timestamp**: 2026-09-16T20:04:50.841Z
- **version**: 10.0.5
- **role**: anonymous
- **url**: https://dewey.day.lsmc.bio/login
- **inputs**: Protected record redirects to /login after logout.
- **expected**: Signout removes access and redirects protected page
- **observed**: Protected record redirects to /login after logout.
- **evidence**: I1-B-LOGIN-LOGOUT-1789589090841.txt ; I1-B-LOGIN-LOGOUT-1789589090841.png

### LOGIN-SIGNUP I1-B — PASS

- **timestamp**: 2026-09-16T20:05:24.023Z
- **version**: 10.0.5
- **role**: anonymous
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: I1-B approved email entered; password entry/submission reserved for user.
- **expected**: Signup form renders approved alias
- **observed**: I1-B approved email entered; password entry/submission reserved for user.
- **evidence**: I1-B-LOGIN-SIGNUP-1789589124023.txt ; I1-B-LOGIN-SIGNUP-1789589124023.png

### LOGIN-SIGNUP-COMPLETE I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:05:24.064Z
- **version**: 10.0.5
- **role**: anonymous
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: Password handoff remains pending. No signup submission or verification email.
- **expected**: User enters and submits new credential; verify email
- **observed**: Password handoff remains pending. No signup submission or verification email.
- **evidence**: I1-B-LOGIN-SIGNUP-COMPLETE-1789589124064.txt

### SHARE-RECIPIENT I1-B — BLOCKED

- **timestamp**: 2026-09-16T20:05:24.069Z
- **version**: 10.0.5
- **role**: anonymous
- **url**: https://lsmc-atlas-gui-users-8915-lsmcok1.auth.us-west-2.amazoncognito.com/signup?client_id=737empi6dno0kbefh28g23u9jv&response_type=code&scope=openid+email+profile&redirect_uri=https%3A%2F%2Flogin.day.lsmc.bio%2Fauth%2Fcallback&state=[REDACTED]
- **inputs**: I1-B account is not established; recipient role unavailable.
- **expected**: Approved alias signs in and views fixture share
- **observed**: I1-B account is not established; recipient role unavailable.
- **evidence**: I1-B-SHARE-RECIPIENT-1789589124069.txt

### LOGIN-LOGIN I1-B — PASS

- **timestamp**: 2026-09-16T20:05:38.926Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **inputs**: Shared login returned johnm@lsmc.com authenticated Library.
- **expected**: Existing Google login authenticates
- **observed**: Shared login returned johnm@lsmc.com authenticated Library.
- **evidence**: I1-B-LOGIN-LOGIN-1789589138926.txt ; I1-B-LOGIN-LOGIN-1789589138926.png

### LOGIN-RETURN I1-B — FAIL

- **timestamp**: 2026-09-16T20:05:39.036Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/ui
- **inputs**: Signed-out /records/M-DGX-TRW6 became /login without next; returned /ui after login. D06.
- **expected**: Requested record survives sign-in
- **observed**: Signed-out /records/M-DGX-TRW6 became /login without next; returned /ui after login. D06.
- **evidence**: I1-B-LOGIN-RETURN-1789589139036.txt ; I1-B-LOGIN-RETURN-1789589139036.png

### SET-FILTER I1-A — PASS

- **timestamp**: 2026-09-16T20:06:12.437Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets?filters=%5B%7B%22path%22%3A%22metadata.gui_audit.attempt%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22I1-A%22%7D%5D&page=1
- **inputs**: metadata.gui_audit.attempt eq I1-A returns one3member set.
- **expected**: Metadata equality narrows sets
- **observed**: metadata.gui_audit.attempt eq I1-A returns one3member set.
- **evidence**: I1-A-SET-FILTER-1789589172437.txt ; I1-A-SET-FILTER-1789589172437.png

### SET-FILTER I1-B — PASS

- **timestamp**: 2026-09-16T20:06:15.841Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/sets?filters=%5B%7B%22path%22%3A%22metadata.gui_audit.attempt%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22I1-B%22%7D%5D&page=1
- **inputs**: metadata.gui_audit.attempt eq I1-B returns one3member set.
- **expected**: Metadata equality narrows sets
- **observed**: metadata.gui_audit.attempt eq I1-B returns one3member set.
- **evidence**: I1-B-SET-FILTER-1789589175841.txt ; I1-B-SET-FILTER-1789589175841.png

### SHARE-PAGINATION I1-A — PASS

- **timestamp**: 2026-09-16T20:06:30.825Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?page=2
- **inputs**: Page2rendered with later shares.
- **expected**: Next loads second page
- **observed**: Page2rendered with later shares.
- **evidence**: I1-A-SHARE-PAGINATION-1789589190825.txt

### SHARE-PAGINATION I1-B — PASS

- **timestamp**: 2026-09-16T20:06:36.897Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?page=2
- **inputs**: Repeated page1→page2 navigation renders later shares.
- **expected**: Next loads second page
- **observed**: Repeated page1→page2 navigation renders later shares.
- **evidence**: I1-B-SHARE-PAGINATION-1789589196897.txt

### SHARE-FILTER I1-A — PASS

- **timestamp**: 2026-09-16T20:07:16.291Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?page=1&filters=%5B%7B%22path%22%3A%22audience%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22recipients%22%7D%5D
- **inputs**: audience eq recipients returns2retained auditshares.
- **expected**: Audience equality filters shares
- **observed**: audience eq recipients returns2retained auditshares.
- **evidence**: I1-A-SHARE-FILTER-1789589236291.txt ; I1-A-SHARE-FILTER-1789589236291.png

### SHARE-FILTER I1-B — PASS

- **timestamp**: 2026-09-16T20:07:26.778Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares?page=1&filters=%5B%7B%22path%22%3A%22audience%22%2C%22op%22%3A%22eq%22%2C%22value%22%3A%22recipients%22%7D%2C%7B%22path%22%3A%22name%22%2C%22op%22%3A%22contains%22%2C%22value%22%3A%22I1-B%22%7D%5D
- **inputs**: audience eq recipients AND name contains I1-B returns1share.
- **expected**: Combined property filters narrow shares
- **observed**: audience eq recipients AND name contains I1-B returns1share.
- **evidence**: I1-B-SHARE-FILTER-1789589246778.txt ; I1-B-SHARE-FILTER-1789589246778.png

### SHARE-INVITE I1-B — BLOCKED

- **timestamp**: 2026-09-16T19:50:22.478Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/shares/M-DGX-TSNK
- **inputs**: GUI accepted I1-B invitation; mailbox delivery verification pending.
- **expected**: Approved mailbox receives login invitation
- **observed**: GUI invitation accepted; Gmail search of approved I1-B alias at 20:03Z returned zero messages. Delivery not verified.
- **evidence**: I1-B-SHARE-INVITE-1789588222478.txt
- **classification_at**: 2026-09-16T20:08:29.175099+00:00

### BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2 I1-B — BLOCKED

- **timestamp**: 2026-09-16T19:59:25.362Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Flsmc-qeo-day-analytical-108782052779-us-west-2%2F
- **expected**: Page fully renders its expected content
- **observed**: Explicit ListBucket denial in bucket policy. No authorization bypass; source UI error retained.
- **evidence**: I1-B-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789588765362.txt ; I1-B-BUCKET-lsmc-qeo-day-analytical-108782052779-us-west-2-1789588765362.png
- **classification_at**: 2026-09-16T20:08:29.175627+00:00

### STORE-PAGE-NEXT I1-A — PASS

- **timestamp**: 2026-09-16T19:42:26.755Z
- **version**: 10.0.5
- **role**: johnm@lsmc.com / ADMIN
- **url**: https://dewey.day.lsmc.bio/storage?uri=s3%3A%2F%2Fcdk-hnb659fds-assets-108782052779-us-west-2%2F&token=[REDACTED]
- **expected**: Storage continuation loads bounded second page
- **observed**: Continuation URL changed and second page displayed 31 objects (32 table rows including header). Corrects earlier count prose; original screenshot/DOM retained.
- **evidence**: I1-A-STORE-PAGE-NEXT-1789587746755.txt ; I1-A-STORE-PAGE-NEXT-1789587746755.png
- **classification_at**: 2026-09-16T20:08:29.175633+00:00


## Retained fixtures

[
  {
    "attempt": "I1-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-A/hello world ü.txt",
    "size": 80,
    "sha256": "19dba8113384fee2dfce211f1ac2642fcc381ef92abcc684535eff73ece7abbf",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/hello world ü.txt"
  },
  {
    "attempt": "I1-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-A/fixture.json",
    "size": 64,
    "sha256": "e566115140b002aad963e1d0812f41f7a93dc0cedeba1556fc372e397aab2cd0",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/fixture.json"
  },
  {
    "attempt": "I1-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-A/index.html",
    "size": 176,
    "sha256": "50f481ff7aba66faaf44555b92a399fb1157249012a69088070a1d0579ae7647",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/index.html"
  },
  {
    "attempt": "I1-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-A/asset.svg",
    "size": 111,
    "sha256": "c763668ac86f122c1288f6d007cdd61a306958e7720247ced00650822a78d5de",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/asset.svg"
  },
  {
    "attempt": "I1-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-A/multipart-17MiB.txt",
    "size": 17825792,
    "sha256": "4c1e65ad2ad479377d351b7b62ce8c775324d77552f74e4fac42300382f18e6e",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-A/multipart-17MiB.txt"
  },
  {
    "attempt": "I1-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-B/hello world ü.txt",
    "size": 80,
    "sha256": "19dba8113384fee2dfce211f1ac2642fcc381ef92abcc684535eff73ece7abbf",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/hello world ü.txt"
  },
  {
    "attempt": "I1-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-B/fixture.json",
    "size": 64,
    "sha256": "e566115140b002aad963e1d0812f41f7a93dc0cedeba1556fc372e397aab2cd0",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/fixture.json"
  },
  {
    "attempt": "I1-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-B/index.html",
    "size": 176,
    "sha256": "50f481ff7aba66faaf44555b92a399fb1157249012a69088070a1d0579ae7647",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/index.html"
  },
  {
    "attempt": "I1-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-B/asset.svg",
    "size": 111,
    "sha256": "c763668ac86f122c1288f6d007cdd61a306958e7720247ced00650822a78d5de",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/asset.svg"
  },
  {
    "attempt": "I1-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I1-B/multipart-17MiB.txt",
    "size": 17825792,
    "sha256": "4c1e65ad2ad479377d351b7b62ce8c775324d77552f74e4fac42300382f18e6e",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I1-B/multipart-17MiB.txt"
  },
  {
    "attempt": "I2-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-A/hello world ü.txt",
    "size": 80,
    "sha256": "19dba8113384fee2dfce211f1ac2642fcc381ef92abcc684535eff73ece7abbf",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-A/hello world ü.txt"
  },
  {
    "attempt": "I2-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-A/fixture.json",
    "size": 64,
    "sha256": "e566115140b002aad963e1d0812f41f7a93dc0cedeba1556fc372e397aab2cd0",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-A/fixture.json"
  },
  {
    "attempt": "I2-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-A/index.html",
    "size": 176,
    "sha256": "50f481ff7aba66faaf44555b92a399fb1157249012a69088070a1d0579ae7647",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-A/index.html"
  },
  {
    "attempt": "I2-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-A/asset.svg",
    "size": 111,
    "sha256": "c763668ac86f122c1288f6d007cdd61a306958e7720247ced00650822a78d5de",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-A/asset.svg"
  },
  {
    "attempt": "I2-A",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-A/multipart-17MiB.txt",
    "size": 17825792,
    "sha256": "4c1e65ad2ad479377d351b7b62ce8c775324d77552f74e4fac42300382f18e6e",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-A/multipart-17MiB.txt"
  },
  {
    "attempt": "I2-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-B/hello world ü.txt",
    "size": 80,
    "sha256": "19dba8113384fee2dfce211f1ac2642fcc381ef92abcc684535eff73ece7abbf",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-B/hello world ü.txt"
  },
  {
    "attempt": "I2-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-B/fixture.json",
    "size": 64,
    "sha256": "e566115140b002aad963e1d0812f41f7a93dc0cedeba1556fc372e397aab2cd0",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-B/fixture.json"
  },
  {
    "attempt": "I2-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-B/index.html",
    "size": 176,
    "sha256": "50f481ff7aba66faaf44555b92a399fb1157249012a69088070a1d0579ae7647",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-B/index.html"
  },
  {
    "attempt": "I2-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-B/asset.svg",
    "size": 111,
    "sha256": "c763668ac86f122c1288f6d007cdd61a306958e7720247ced00650822a78d5de",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-B/asset.svg"
  },
  {
    "attempt": "I2-B",
    "path": "/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/ursa-final-gap-dewey-20260913/docs/plans/evidence/20260916T183133Z_dewey_gui_audit/fixtures/I2-B/multipart-17MiB.txt",
    "size": 17825792,
    "sha256": "4c1e65ad2ad479377d351b7b62ce8c775324d77552f74e4fac42300382f18e6e",
    "destination": "s3://lsmc-dewey-0/gui-audit/20260916T183133Z/I2-B/multipart-17MiB.txt"
  }
]

## Limits and exclusions

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

## Completion

{
  "all_rows_terminal": false,
  "objective_complete": false
}
