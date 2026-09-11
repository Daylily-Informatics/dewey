# Dewey 9.0.0 runtime and acceptance preparation

Prepared 2026-09-11 from Dewey `9a4463d7312ee91d5363157b35e23131a3e0d78f`;
runtime/build inputs are identical to coordinator commit `214b207`. This is D's
source-backed preparation, not a build, deployment or acceptance receipt. The
coordinator owns the controlling ledger and all live operations. The user's
release/deployment authorization and no-additional-backup amendment remain in
force. This note neither creates a backup nor changes the migration runbook.

Companions:

- [Dewey-only override](20260911T061000Z_dewey_900_runtime_override.yaml)
- [Acceptance request inputs](20260911T061000Z_dewey_900_acceptance_inputs.json)
- [Writer and full-image inventory](20260911T053125Z_dewey_writer_and_image_preparation.md)
- [Existing local implementation and test receipts](20260911T051420Z_dewey_tapdb101rc1_implementation.md)

## Exact runtime identity

| Field | Required value or evidence |
| --- | --- |
| Dewey / TapDB / Meridian | `9.0.0` / `10.1.1rc1` / `0.4.8`; Python 3.12 or newer |
| Database | `dewey_prod_tapdb10`, after the coordinator's copied-database migration gates |
| Preserved schema | `tapdb_dewey_lsmcok1_local` |
| Namespace metadata | `client_id=dewey`, `database_name=dewey-day`, `owner_repo_name=dewey` |
| Historical domain | `M`; retain all existing issuer/tenant identities and all 11 Dewey templates with `DGX` instance prefixes |
| Aurora | `dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com:5432`, `us-west-2`, native `verify-full` |
| New Dewey config | `/opt/dewey/day/releases/9.0.0/dewey-config.yaml` |
| New TapDB runtime config | `/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml` |
| Registry files | `/opt/dayhoff/deployments/day/tapdb-registry/domain_code_registry.json` and `prefix_ownership_registry.json`, retained at the same absolute container paths |
| Runtime user | Explicit `0:0`, matching the coordinator's observed existing service; explicit `HOME=/root` |
| CA mount | Existing host `/home/ubuntu/.config/tapdb/rds-ca-bundle.pem` to `/root/.config/tapdb/rds-ca-bundle.pem`, read-only |

The two new config paths were accepted by the coordinator and were **not yet
created** when this preparation was written. Native configuration metadata and
the database/schema must agree with Dewey's explicit settings. The runtime login
and its secret reference must be the constrained role prepared for the final
runtime config identity, not the source database owner `dayhoff` or an operator
credential. Principal creation/binding and sequence-floor work remain external.

The coordinator's RC source inventory at 05:22:40Z recorded all 11 historical
bindings: `data/artifact`, `data/artifact_set`, `access/share`, `access/share_root`,
`integration/external_object`, `integration/external_object_relation`,
`access/literature_save`, `operational/anomaly`, `system/idempotency_request`,
`system/registration_receipt`, `system/outbox_event`, each `generic/1.0` in domain
`M` with `DGX` instance prefix. Source evidence is
`docs/plans/evidence/20260911_dewey_rc_inventory/source-summary.json` in the
coordinator branch. These source observations are not target acceptance.

`DeweyService.verify_existing()` is the unconditional startup operation. There
is no configurable startup-mode flag to set. `TapDBBackend.ensure_templates()`
only reads template definitions, rejects missing templates or a non-`DGX`
instance prefix, and never creates templates, schema, claims or principals.
Do not run `config init`, schema migration, seed, allocator preparation or
principal preparation from the application entrypoint. No fresh schema or
template overwrite is part of this release.

## New private configuration preparation

1. Use the released native CLI to create a **new**, explicit TapDB runtime config
   with the target identity above and the reviewed runtime credential. Preserve
   the existing Dewey service settings in the new Dewey file, including broker,
   Cognito, cookie secret, storage, resolver credential hash/expiry, approved
   origins/hosts, signing keys and AWS profile. Change only the explicit target
   wiring and required release settings. Do not edit the active old config.
2. Native `config init` creates the complete admin mapping and a private
   `admin.session.secret`. Use native `db-config update --admin-auth-mode tapdb`
   and `--admin-allowed-origin https://dewey.day.lsmc.bio`. Retain the generated
   session secret; do not print it. `admin.auth.mode=host_session` is invalid
   native YAML: Dewey supplies `TapdbHostBridge(auth_mode="host_session")` in code.
3. Set precisely the new file's `admin.security.production_like` boolean to
   `true`. RC init/update exposes no flag for this field. The coordinator has
   confirmed this bounded preparation is within the user's documented-SOP and
   release authorization. Require a mapping at root and `admin`; allow an absent
   `admin.security` mapping to be created, but reject any existing non-mapping.
   Reject a preexisting non-boolean `production_like`. Preserve every other field.
   Do not use the safety tier or database name as a substitute: native
   `get_admin_settings()` reads this field and resolves `target_name="target"`.
4. Validate using released public `get_db_config(config_path=..., client_id="dewey",
   database_name="dewey-day")` and `get_admin_settings(config_path=...)`. Assert
   the identity above, nonempty admin session secret, `auth_mode="tapdb"`,
   `production_like is True`, and the exact permitted origin; print only checks
   and nonsecret identity. A public runtime connection under the final runtime
   user/config identity must then pass the coordinator's read-only template and
   principal checks. Config parsing alone cannot establish a valid binding.
5. Keep both configs private and bind-mounted read-only. This deliberately
   prevents `/admin/artifact-storage` from rewriting service YAML; update such
   configuration through a reviewed new release config. Preserve original
   root-only files and permissions. No recursive chown/chmod is needed.

The exact RC Aurora public web runtime calls `ensure_ca_bundle()` at the fixed
`Path.home()/.config/tapdb/rds-ca-bundle.pem` cache, even when the config includes a
different `sslrootcert`. Verify the existing CA receipt before mounting it at
the root path; an existing native cache is returned without rehashing. The native
download expectation is SHA256
`e5bb2084ccf45087bda1c9bffdea0eb15ee67f0b91646106e466714f9de3c7e3`.
This preparation does not download or change that file.

Select the observed production AWS profile explicitly in the override and retain
its existing private credential/config mounts. Native Secrets Manager password
lookup uses the process boto3 credential chain, whereas IAM token generation
can use the configured profile; config metadata alone does not establish process
credentials. Retain explicit readable signing-key/QEO CA/NCBI paths and writable
state/cache/temp paths. Check them under the actual image's `0:0` user.

The override is a fragment for the existing `dewey` service. Compose merges
volume entries by destination: the coordinator must remove superseded **Dewey**
source/operator config mounts from the final rendered definition and preserve
the two exact registry mounts, existing AWS/auth/storage mounts, service network,
reverse proxy, port mapping, restart policy, OTEL endpoint and writable state/cache
paths. `LSMC_SERVICE_NAME`, `LSMC_ENV`, `LSMC_RUNTIME_CLASS`, `HOST`, `PORT`, and
`OTEL_EXPORTER_OTLP_ENDPOINT` remain required inherited entrypoint inputs. An
unrendered fragment is not a launch receipt. No source-tree or TapDB overlay mount
belongs in the final definition.

## Complete image and provenance inputs

Build from the reviewed clean release commit, using this repository's complete
Dockerfile and frozen `uv.lock`, never the archived TapDB 9 overlay. The exact
build argument is `SETUPTOOLS_SCM_PRETEND_VERSION=9.0.0`; without it this Dockerfile
uses `0.0.0` because `.git` is excluded from the build context. Also supply
`PYTHON_VERSION=3.12`, the verified production platform, and record resolved
builder/runtime base-image digests. The builder runs `uv sync --frozen` for the
single dependency set and enforces the exact TapDB/Meridian pair.

Supply image build labels `org.opencontainers.image.version=9.0.0`,
`org.opencontainers.image.revision=<exact release commit>`, and
`org.opencontainers.image.source=<verified Dewey repository URL>`. These are
build flags, not labels automatically inserted by the Dockerfile. Record the
resulting immutable image digest; use that digest as `DEWEY_RELEASE_IMAGE` in
the override. Container labels are supplemental and do not prove image content.
Set both `DEWEY_BUILD_SHA` (Dewey observability) and `LSMC_RELEASE_SHA` (entrypoint
OTEL attributes) to that same commit. They are distinct consumers.

The packaged runtime must report Dewey `9.0.0`, TapDB `10.1.1rc1`, Meridian
`0.4.8`; the final image's CLI and app must import from `/app/.venv` with no
runtime installation. The prior local development wheel and tests do not prove
that image. The UI git metadata helper shells out to git, which is absent in
the runtime image; its branch/commit display remains unavailable and its tag
display can read unreleased. Use the image digest, package version and health/
observability SHA receipt for release provenance, not that UI git display.

## Authenticated application acceptance inputs

Use `https://dewey.day.lsmc.bio`, the preserved approved-network boundary and an
existing authenticated browser session. Keep all credentials in the existing
private mechanism; do not export a browser cookie, print a bearer token, or store
authorization headers or signed URLs in Git. Authentication inputs are separate:
general Dewey bearer for normal API/DAG calls; existing QEO resolver-only token
for `/api/v1/resolve/multiqc`; real host session for embedded GUI access.

| Check | Exact invocation input and expected evidence |
| --- | --- |
| Readiness | `GET /healthz`, `GET /readyz`: package `9.0.0`, runtime DB ready and matching revision/digest receipts |
| Artifact/package read | General bearer `GET /api/v1/artifacts/M-DGX-NKDM`, `GET /api/v1/artifact-sets/M-DGX-NNSS`; existing persisted fixture and 20-member package |
| QEO resolver | Resolver-only bearer `POST /api/v1/resolve/multiqc`, each exact body in the companion JSON; complete package from either report or set |
| Credential isolation | The resolver-only token at general `POST /api/v1/resolve/artifact` with `{"artifact_euid":"M-DGX-NKDM"}` must receive `401` |
| Public DAG | General bearer `GET /api/dag/manifest`, `/api/dag/v2/object/M-DGX-NKDM`, `/api/dag/v2/data?start_euid=M-DGX-NNSS&depth=1&max_nodes=100`, `/api/dag/v2/search?euid=M-DGX-NKDM&limit=1` |
| Public DAG contract | `dag:v2`, `service_id=dewey`, native graph results, outward fetch disabled; public limits depth 6/nodes 500/search 100 |
| Embedded GUI/DAG | Authenticated browser `/artifacts/euid/M-DGX-NKDM`, `/graph`, `/tapdb/graph`, `/tapdb/object/M-DGX-NKDM`, `/tapdb/api/dag/manifest`; capture real loaded content and OAuth navigation evidence |
| Package replay | Public container CLI `dewey --config /opt/dewey/day/releases/9.0.0/dewey-config.yaml qeo package-register --manifest <absolute mounted original manifest> --idempotency-key qeo-multiqc-illumina-20260815-full-package-v1`; same existing `M-DGX-NNSS`, no additional package |

The embedded GUI uses the host bridge and its own native DAG limit defaults
(depth 8/nodes 1000). It does not accept the general API bearer as a host browser
session. The public DAG requires a verified session subject or Dewey service
bearer; the QEO-only resolver token is never a general writer/DAG credential.
Production-like native middleware rejects localhost Host headers. For loopback
rehearsal, preserve the approved production Host header through the explicit
local connection; do not turn off production checks or widen allowed hosts.

The existing fixture evidence is the committed package registration receipt and
original manifest listed in the companion JSON. These are genuine persisted
source identifiers, not generated examples. The private resolver token is at
`/opt/dewey/day/releases/qeo-resolver-7782aef47b86/resolver.token`; the historical
receipt expires `2026-12-09T00:20:01.857914+00:00`. Verify the retained config's
hash/expiry and target fixture availability before treating those as active inputs.

After successful target reads and the coordinator's write gate, POST the exact
`controlled_artifact_set_create.body` with its `Idempotency-Key`. Capture the
returned **persisted** `artifact_set_euid`; do not choose an EUID in advance.
The current HTTP route returns `200` with body `status_code:201`. Repeat the
identical body/key and require the identical receipt/EUID, then change the label
with the same key and require `409`. Add the existing report through the typed
membership route using only the returned set EUID and companion request, repeat
it with the same key, and read the set back. This writes an acceptance artifact
set, idempotency records and membership lineage, with no S3 mutation or QEO
dispatch. Retain this explicitly labeled record; no cleanup is proposed.
Native floors before/after and preservation comparisons remain coordinator gates.

The rehearsal uses the separately agreed sibling paths
`/opt/dewey/day/releases/tapdb10-rehearsal-20260911/{dewey-config.yaml,tapdb-runtime.yaml}`,
a separate bound runtime role and isolated loopback publication. This is not
the production override above. Dewey has no global outbound-disable flag:
do not invoke QEO dispatch, storage/share/literature/user-preference mutations or
background/operator jobs during rehearsal; containment must enforce the reviewed
allowed requests and outbound controls. Missing dispatch credentials fail closed.

## Outage census field contract for the coordinator

The source-backed writer inventory remains the complete containment list. A
native TapDB outbox-table count of zero does not count Dewey's typed app outbox.
The coordinator authorized a reviewed SELECT-only census through public
`operator_connection(read_only=True)` for these narrow app metadata fields.
Do not call dispatch to inspect a queue and do not export whole JSON payloads.

Join each persisted `generic_template.uid` to `generic_instance.template_uid`,
restricted to domain `M`, the exact template category/type/subtype/version and
nondeleted instances. Dewey stores these fields at **`json_addl` root**, not under
`json_addl.properties` (`TapDBBackend.create_instance` assigns the payload).

| Population | Exact JSON fields and interpretation |
| --- | --- |
| `system/outbox_event/generic/1.0` from artifact-set registration | `dispatch_status`, `local_only`, `event_type`, `event_id`, `dispatch_attempt_count`, `occurred_at`; count `pending`/`error`/`local_only`/`dispatched` and unknown/malformed independently |
| Same template from sequencer registration | `status="pending"`, `created_at`, event envelope fields; `dispatch_status` is absent, so the current dispatcher skips this layout; count it separately |
| `system/idempotency_request/generic/1.0` upload creation | `operation="artifact.upload_session.create"`; `response.created_at` (UTC), `response.expires_in` (seconds), outer `created_at`, persisted row EUID |
| Same template upload completion | `operation="artifact.upload_session.complete"`; outer `created_at`, `status_code`, `response.artifact_euid` (already persisted) |

The queue dispatcher chooses `local_only=false`, `dispatch_status=pending`
(errors only on explicit `--retry-errors`) and `event_type` beginning
`lsmc.dewey.`. Its unfiltered search is bounded to 1,000 rows, and the service's
read list is bounded to 2,000. Neither `qeo status` nor a zero-attempt dispatch
receipt establishes an exhaustive empty queue. Preserve all unknown layouts
and pending rows for owner disposition, not automatic dispatch or acknowledgement.

Upload creation stores a token and presigned URL inside the response. **Never
select or emit `response.upload_token`, `upload_url`, or `upload_headers`.**
Use only row IDs, UTC creation times, positive integer TTL and aggregate counts.
Reject malformed/missing timestamps or TTL as unresolved rather than guessing.
The conservative authorization horizon is the latest creation time plus its
stored TTL after blocking new issuance. Completion records do not retain an
authoritative create-session link, so matching counts/idempotency keys do not
prove completion. Preserve the actual configured TTL and session-signing secret.

A presigned upload accepted before expiry can finish after expiry. Require active
client/request/process drain in addition to the expiry horizon, and close pending
remote-send/local-ack windows before whole HTTP shutdown. No recurring schedule,
outbox retry, completion call, storage scan or cleanup is introduced by this note.

## Validation and limits

This task performed static source/package reads, checked current app/build inputs
against the coordinator branch, and validated the new YAML/JSON syntax and exact
fixture manifest digest (`.venv/bin/python`, exit 0); `git diff --check` passed.
The YAML contains only `services.dewey` and three strict, read-only bind mounts.
Existing 120 distinct passing RC tests and prior native
receipts are reused. No test suite, image build, backup, live read, publication,
deployment or acceptance was rerun here. The missing production-like CLI field
is handled by the explicitly authorized new-file SOP above, with no package shim.
Image build/runtime permission receipts, copied-target acceptance, persisted
fixture reads and the final role/config binding are still coordinator evidence.
