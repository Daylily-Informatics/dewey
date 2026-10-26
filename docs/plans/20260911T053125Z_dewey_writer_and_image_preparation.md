# Dewey planned-outage writer and full-image preparation

Recorded 2026-09-11T05:31:25Z by D. This is read-only preparation for the
user-authorized occasional migration SOP, based on Dewey source commit
`492c0ffd2a385cf1331103ebb2daa6c618605503` (integrated by the coordinator at
`ee4edfe`). It does not edit the controlling ledger or C's migration runbook.
No AWS/live commands, tests, image builds, publication or release were performed.

## Findings requiring explicit outage controls

1. Blocking only POST/PUT/PATCH/DELETE is insufficient. The GET external-object
   relation listing can update target JSON through `_sync_external_graph_refs_for_target`
   in `services/external_objects.py:511`. Stop/admit no new traffic to the entire
   Dewey service, including `/tapdb`, direct backend access and browser sessions.
2. QEO dispatch sends its HTTP request before recording the result in Dewey.
   Drain the dispatcher and preserve its final acknowledgement evidence before
   source capture. Killing it in that interval can leave an accepted QEO event
   represented as pending/error locally; replay requires the original event and
   idempotency identity, not fabricated completion or deletion.
3. Share access attempts are writers: both allowed and denied attempts append
   durable audit data; allowed access also increments counts. Artifact download
   redirect creates a share and access package. These are not read-only controls.
4. Existing presigned S3 upload URLs can still write S3 after Dewey stops.
   Preserve and account for issued upload sessions, outstanding object uploads,
   completion requests, object versions and retries. HTTP/DB quiescence alone
   does not prove there are no outstanding external-storage effects.
5. Native TapDB GUI object/template/lineage and lifecycle entrypoints are present
   under `/tapdb`; normal Dewey API controls do not cover them separately.
6. Source inspection found no background thread/task/consumer/scheduler launcher
   in `dewey_service`. QEO dispatch is an explicit synchronous CLI operation.
   This is not proof that the live host has no cron, timer, tmux, remote caller,
   standalone Python process or operator running those commands.

## Writer ownership and processes to inventory

| Path/process | Effects and evidence source | Outage disposition |
| --- | --- | --- |
| Foreground container Python/Uvicorn | `container_entry.main` calls server start with `background=False`, `reload=False`; first-party and native routes share the service process | Drain in-flight requests, then stop every Dewey instance; retain final logs/request IDs and prevent service-specific automatic restart during capture |
| Background CLI Uvicorn | `cli/server.py:306` can spawn a detached `python -m uvicorn ... --factory`, record PID/state/logs, and optionally enable reload | Inventory host and container processes, not only the named Compose service; stop the actual supervisor/reloader and children |
| Runtime database pools | Dewey backend plus native GUI/DAG use public `web.runtime.get_db`; engines/session factories are cached per explicit config path/schema | Close every old process/pool before final capture and after principal binding; native census is observation, not an isolation control |
| `dewey qeo package-register` | `cli/qeo.py:36`, `artifact_sets.py:83`: atomic package, membership lineage and idempotency writes | Suspend operators/scripts using the source config; retain manifest/idempotency keys and exact terminal receipts |
| `dewey qeo dispatch` | `cli/qeo.py:72`, `services/outbox.py:81`: reads pending rows (or error with explicit retry), HTTP POST to QEO, then row update | Stop new dispatch invocations, let current bounded attempts settle; retain pending/error/local_only/dispatched statuses and remote acknowledgement IDs |
| Low-level delegated CLI | `dewey tapdb run ...`, native `tapdb ...`, imported `DeweyService`/backend scripts | Inventory all holders of runtime and operator credentials; only the explicitly designated migration operator remains permitted by the reviewed SOP |
| Native GUI operators | `/tapdb` object/template/lineage/repair and backup/restore controls | Entire mount unavailable during outage; a permission-denied expectation is not the isolation mechanism |
| Config and credential operators | `dewey config init`, `config set-artifact-bucket`, `qeo resolver-credential-create`; admin storage form | Freeze deployment/config/credential changes; preserve config/credential receipt identity without printing secret values |
| Shared auth delegation | `dewey cognito ...` delegates external Cognito/Daycog lifecycle; preferences PUT goes to the configured login broker | Freeze Dewey-specific operator changes and in-flight forwarded changes; do not stop or mutate sibling services globally |
| Acceptance utilities | `scripts/prod_share_delivery_acceptance.py` creates/revokes shares and obtains access packages through HTTP | Explicitly account for any active invocation; never run it as a supposedly read-only readiness check |
| External API callers | Any producer/integration using Dewey's registration/import/upload/share APIs can create objects/lineage/idempotency/outbox entries | Coordinator must list actual producers, queued retries and owners from live evidence; source names alone do not prove deployment |
| Storage/literature work | `storage.py` copy/put/tag/retention; literature PDF fetch+managed upload; archive construction/network reads | Drain pending side effects; retain any already-issued upload URLs and pending completion work; no blanket S3 deletion/revocation is implied |
| Runtime filesystem work | Server state/log directories; configured metapub cache; config edits; local credential files; stdout access logs | Preserve state required for resume/acknowledgement and provide private writable runtime directories in the replacement |

The `qeo_consumer_group` field is the identity sent to QEO. It is not evidence
of a locally running queue consumer. Registration methods persist outbox events
inside the same transaction as registration receipts. Dispatch is invoked only
when an operator/script calls it; this source does not schedule it automatically.

## Durable state and acknowledgement boundaries

- Database writers use generic instances, generic lineage and their native audit
  substrate. Application records include artifact, artifact set, share/share root,
  external object/relation, literature save, anomaly, idempotency request,
  registration receipt and outbox event templates. Preserve all existing data,
  including dormant/soft-deleted rows and allocator floors; never derive an
  inventory only from currently visible artifact lists.
- `_share_access_session` (`services/sharing.py:156`) deliberately commits a
  denied-access audit before raising the public error. A 4xx is not proof that
  no database write occurred.
- `upload_artifact_bytes` (`services/artifacts.py:1537`) creates an upload session,
  performs S3 PUT, then completes it. Imports/copies, tagging and retention also
  have external side effects that a database rollback cannot undo.
- `_dispatch_qeo_outbox_row` (`services/outbox.py:223`) posts the event and group,
  then `_update_outbox_dispatch` opens a separate committing session. The receipt
  must distinguish remote acceptance, local acknowledgement and unknown outcome.
- Search/export, direct archive download and the three resolve POST routes are
  read operations in Dewey source. Nevertheless the service should remain fully
  unavailable during the short outage: GET relation synchronization, mounted
  GUI operations and shared pools make an HTTP-verb allowlist insufficient.
- Request observability rolls up counters in memory and writes structured access
  logs. It does not seed database anomalies at startup. Session cookies/auth
  exchanges and broker preferences have separate external/local state ownership.

## Reviewable outage SOP inputs

This note supplies the application containment checklist, not a second migration
runbook. C's supported native command sequence and the coordinator's ledger own
execution. An occasional human-operated outage can use explicit process and
operator controls plus durable evidence; another TapDB release solely to automate
source isolation is not assumed. Required native fence/control-database receipts
must still be truthful and satisfied; an empty census is not a fabricated fence.

1. Before the outage, record exact source DB/schema/provider, every credentialed
   writer principal, each service/process/job and its restart owner, explicit
   runtime/operator config references, current image/user/mount/boot definition,
   source and target identity receipts, and the approved stop/resume order.
2. Stop admission for all Dewey routes/direct backend access. Suspend scheduled
   and manual source-writing commands, upstream retries and dispatch invocations.
   Capture the service-specific control that prevents automatic restart.
3. Drain existing requests, uploads/copies and QEO attempts. Preserve accepted,
   failed and uncertain outcomes with their original keys/IDs; do not erase or
   relabel pending outbox/upload/idempotency records to make the queue appear empty.
4. Stop every Dewey process/worker/reloader and close its pools. Coordinator
   verifies actual source sessions and generator state using the approved native
   evidence, and records human/operator isolation controls and exceptions. Do not
   assume a stopped browser, empty process listing or single instant of zero
   sessions proves all credentialed writers have been contained.
5. Perform C's reviewed native capture/restore/migration/preservation/floor/binding
   work while the source remains held and quarantined. Preserve original IDs and
   monotonically advancing floors across ambiguous, aborted and accepted writes.
6. Start only the intended replacement with its bound runtime config and new
   sessions. Complete controlled acceptance before admitting ordinary traffic.
   Resume writers in recorded order; reconcile uncertain QEO/upload outcomes
   before retrying with the original durable identity.
7. Returning to the old image after replacement writes is not sufficient recovery.
   The approved recovery path must retain accepted new writes and every exposed
   allocator floor. Old-source admission remains closed until that proof exists.

## Full-image and runtime preparation

### Exact build/version/provenance inputs

| Item | Concrete requirement from the current source |
| --- | --- |
| Build context | Exact clean reviewed Dewey main/release commit with `Dockerfile`, `pyproject.toml`, `uv.lock`, `README.md`, `config/`, `dewey_service/`, `docker/entrypoint.sh`; no TapDB 9 resolver overlay |
| Package version | Pass `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=9.0.0`; the Dockerfile otherwise defaults to `0.0.0`. It maps to `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DEWEY_SERVICE` and unsets the generic variable during both frozen installs |
| Python/dependencies | `--build-arg PYTHON_VERSION=3.12`; exact `daylily-tapdb[aurora,gui]==10.1.1rc1`, `meridian-euid==0.4.8`; both uv installs are `--frozen`; image construction asserts the exact pair |
| Builder/runtime bases | Current source uses `ghcr.io/astral-sh/uv:0.5.30-python3.12-bookworm-slim` and `python:3.12-slim-bookworm`; resolve and record their actual build digests and the verified production platform when building |
| OCI provenance | Supply `org.opencontainers.image.version=9.0.0`, `org.opencontainers.image.revision=<exact reviewed release commit>`, and the verified repository source label; these labels are not set by the Dockerfile itself |
| Runtime provenance | Set `LSMC_RELEASE_SHA` to that same commit for entrypoint OTEL attributes and `DEWEY_BUILD_SHA` for `observability._build_sha`; the latter does not read `LSMC_RELEASE_SHA` |
| Release binding | Bind annotated numeric tag `9.0.0`, peeled commit, image digest/platform, resolved dependency versions, lock and runtime-config receipt in the release record; do not use the previously built `8.0.3.dev20` wheel as a release |
| GUI Git metadata limitation | `.dockerignore` excludes `.git`, and the runtime stage does not install git. `ui_metadata.resolve_git_metadata` therefore reports unavailable/unreleased from the full image. OCI labels and the explicit runtime SHA do not populate that helper. Package metadata remains the version source; any GUI provenance repair is a separate reviewed code change, not a reason to copy `.git` or fabricate a branch/tag |
| CI/publication | CI currently performs frozen dependency checks/tests/wheel build. Old overlay publication workflows were removed. Coordinator must prepare the explicit full-image build/publish path; this note executes none |

### Runtime UID, private files and mounts

The Dockerfile declares `USER lsmc`, with a system-assigned numeric UID/GID rather
than fixed numeric values. The historical production receipt in
`20260901T064703Z_dewey_prod_reconciliation_capabilities_ledger.md:139` records
Compose `user: 0:0` overriding that default. The coordinator additionally reports
root-only live config/registry mounts. This read-only subtask has not refreshed
live file owners/modes or the current Compose user; retain those as coordinator
inputs, not new observations here.

- Select the intended runtime user explicitly in the candidate definition. Do
  not silently remove a retained `0:0` override and expect root-only mounts to
  work. If adopting the image's `lsmc` user, inspect its actual image UID/GID and
  prepare new private runtime copies/mounts readable by that identity, with parent
  directory traversal. Do not guess UID 1000 or broaden existing secret files to
  world-readable mode. Preserve original source files/permissions for recovery.
- A runtime file must contain only the intended constrained runtime credentials.
  Root/migration/operator credentials and lifecycle journals are not runtime
  mounts. Config creation and principal binding remain native operator work.
- `DEWEY_CONFIG` and `TAPDB_CONFIG_PATH` must be absolute in-container paths to
  existing readable files. TapDB's domain/prefix registries, TLS root certificate,
  credential references and any configured private CloudFront signing key/QEO
  CA/NCBI key also need their explicit in-container paths and access checked under
  the chosen runtime user. A root-readable host path alone is insufficient.
- AWS S3 clients require an explicit profile/region. If the retained configuration
  uses mounted shared AWS files, a change of HOME/user can make `/root/.aws`
  inaccessible or undiscoverable. Prepare explicit readable shared-config and
  credential paths or the already approved credential mechanism; never silently
  substitute a different profile or expose secrets in build layers.
- Set explicit private writable `XDG_STATE_HOME`/`XDG_CACHE_HOME` (and any required
  CLI XDG runtime/config directories) under the chosen user. Server startup calls
  `mkdir` for state/log directories even in foreground mode. Configure the
  metapub cache deliberately; verify required writable temporary storage.
- Distinguish immutable runtime config from operator-editable service config.
  `/admin/artifact-storage` and `dewey config set-artifact-bucket` persist Dewey
  YAML. A read-only mounted Dewey config intentionally prevents those edits;
  the acceptance plan must record that behavior or prepare an explicitly scoped
  writable config mount. Do not make all registries/secrets writable for that one
  administrative form.
- Preserve the explicit runtime environment demanded by `docker/entrypoint.sh`:
  `LSMC_SERVICE_NAME`, `LSMC_ENV`, `LSMC_RUNTIME_CLASS`, `DEWEY_CONFIG`,
  `TAPDB_CONFIG_PATH`, `HOST`, `PORT`, `OTEL_EXPORTER_OTLP_ENDPOINT`. Supply
  `DEWEY_DEPLOYMENT_CODE` deliberately (settings derive CLI XDG identity from it)
  and retain the exact approved deployment/auth/network/storage settings. The
  image sets `DEWEY_EXECUTION_BACKEND=dewey-container`.
- `container_entry.main` starts foreground Uvicorn without TLS, reload or Cognito
  URI rewriting. Retain the established reverse proxy, approved ingress and
  callback settings. Any health/GUI smoke must run under the candidate's actual
  user, mount permissions and explicit config, not a root-only probe followed by
  deployment as a different UID.
- Native cached runtime bundles bind to config path/schema. Changing a config file
  underneath an existing pool does not establish fresh bound sessions. Restart
  the intended runtime after target/principal binding and keep old source pools
  closed.

Before approval, the coordinator needs a reviewable candidate service definition
showing exact image digest, user, environment names, source/destination mount
paths/modes and private permission receipts, plus its single-service switch and
recovery definition. No secret values belong in Git or this inventory.

## First-party writer route inventory

43 routes below can change Dewey DB state, service config or an external service.
Line numbers are from `dewey_service/app.py` at the source commit above.

| Method | Route | Service calls/effect | Source |
| --- | --- | --- | --- |
| `PUT` | `/api/v1/me/preferences` | `Outbound login-broker preference update` | `app.py:1657` |
| `POST` | `/ui/register` | `import_artifact_from_uri,upload_artifact_bytes` | `app.py:1724` |
| `POST` | `/admin/artifact-storage` | `Dewey YAML config plus in-memory managed-bucket setting` | `app.py:1863` |
| `POST` | `/artifacts/euid/{artifact_euid}/external-reference/create` | `attach_external_object_relation,create_external_object,get_artifact` | `app.py:2154` |
| `POST` | `/artifacts/register` | `add_artifact_set_member,create_artifact_set,expand_s3_sources,get_artifact_set,import_artifact_from_uri,register_artifact,upload_artifact_bytes` | `app.py:2231` |
| `POST` | `/artifacts/bulk-upload` | `add_artifact_set_member,create_artifact_set,import_artifact_from_uri,register_artifact` | `app.py:2437` |
| `POST` | `/artifacts/register-prefix` | `register_artifact_prefix` | `app.py:2581` |
| `POST` | `/artifacts/import-run-prefix` | `import_run_prefix` | `app.py:2631` |
| `POST` | `/sequencer-runs/register` | `register_sequencer_run` | `app.py:2673` |
| `POST` | `/artifacts/euid/{artifact_euid}/download` | `create_share,create_share_access_package,get_artifact` | `app.py:2779` |
| `POST` | `/shares/create` | `create_share,list_share_audit` | `app.py:2858` |
| `POST` | `/shares/{share_euid}/access-package` | `create_share_access_package,get_share,list_share_audit` | `app.py:2928` |
| `POST` | `/shares/{share_euid}/revoke` | `list_share_audit,revoke_share` | `app.py:2974` |
| `POST` | `/share-roots/create` | `create_share_root` | `app.py:3000` |
| `POST` | `/share-roots/{share_root_euid}/subsets/create` | `create_share_root_subset,list_share_audit` | `app.py:3042` |
| `POST` | `/artifacts/share` | `create_share` | `app.py:3090` |
| `POST` | `/artifacts/sets/create` | `add_artifact_set_member,create_artifact_set` | `app.py:3131` |
| `POST` | `/artifacts/sets/share` | `create_share` | `app.py:3227` |
| `POST` | `/api/v1/literature/save` | `save_literature` | `app.py:3291` |
| `PATCH` | `/api/v1/literature/saves/{literature_save_euid}` | `update_literature_save_visibility` | `app.py:3313` |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/verify` | `verify_artifact_storage` | `app.py:3427` |
| `POST` | `/api/v1/artifacts/{artifact_euid}/storage/lock` | `lock_artifact_storage` | `app.py:3450` |
| `POST` | `/api/v1/artifacts` | `register_artifact` | `app.py:3492` |
| `POST` | `/api/v1/artifacts/import` | `import_artifact_from_uri` | `app.py:3524` |
| `POST` | `/api/v1/artifact-prefixes` | `register_artifact_prefix` | `app.py:3552` |
| `POST` | `/api/v1/artifacts/import-run-prefix` | `import_run_prefix` | `app.py:3572` |
| `POST` | `/api/v1/sequencer-runs/register` | `register_sequencer_run` | `app.py:3601` |
| `POST` | `/api/v1/analysis-results/register` | `register_analysis_results` | `app.py:3631` |
| `POST` | `/api/v1/artifacts/upload-sessions` | `create_upload_session` | `app.py:3663` |
| `POST` | `/api/v1/artifacts/upload-sessions/{upload_token}/complete` | `complete_upload_session` | `app.py:3690` |
| `POST` | `/api/v1/artifact-sets/analysis/register` | `register_analysis_artifact_set` | `app.py:3740` |
| `POST` | `/api/v1/artifact-sets/multiqc/register` | `register_multiqc_artifact_set` | `app.py:3763` |
| `POST` | `/api/v1/artifact-sets` | `create_artifact_set` | `app.py:3786` |
| `POST` | `/api/v1/artifact-sets/{artifact_set_euid}/members` | `add_artifact_set_member` | `app.py:3808` |
| `DELETE` | `/api/v1/artifact-sets/{artifact_set_euid}/members/{artifact_euid}` | `remove_artifact_set_member` | `app.py:3831` |
| `POST` | `/api/v1/shares` | `create_share` | `app.py:3888` |
| `POST` | `/api/v1/shares/{share_euid}/access-package` | `create_share_access_package` | `app.py:3929` |
| `POST` | `/api/v1/shares/{share_euid}/revoke` | `revoke_share` | `app.py:3964` |
| `POST` | `/api/v1/share-roots` | `create_share_root` | `app.py:3984` |
| `POST` | `/api/v1/share-roots/{share_root_euid}/subsets` | `create_share_root_subset` | `app.py:4007` |
| `POST` | `/api/v1/external-objects` | `create_external_object` | `app.py:4098` |
| `POST` | `/api/v1/external-object-relations` | `attach_external_object_relation` | `app.py:4121` |
| `GET` | `/api/v1/{target_type}/{target_euid}/external-object-relations` | `list_external_object_relations` | `app.py:4146` |

## Native TapDB GUI containment inventory

These 32 published RC non-GET entrypoints include write attempts, validation,
exports and operator backup/restore workflows. They are listed for whole-mount
containment; this is not a claim that every route succeeds with the constrained
runtime role. Paths are mounted beneath `/tapdb`; source is immutable wheel
`daylily_tapdb/gui/router.py` for `10.1.1rc1`.

| Method | Mounted path | Published source |
| --- | --- | --- |
| `POST` | `/tapdb/templates/repository/export` | `gui/router.py:1565` |
| `POST` | `/tapdb/api/templates/repository/export` | `gui/router.py:1652` |
| `POST` | `/tapdb/api/templates/repository/import` | `gui/router.py:1677` |
| `POST` | `/tapdb/templates/validate` | `gui/router.py:1769` |
| `POST` | `/tapdb/api/templates/validate` | `gui/router.py:1788` |
| `POST` | `/tapdb/templates/save` | `gui/router.py:1812` |
| `POST` | `/tapdb/create/{template_euid}` | `gui/router.py:1932` |
| `POST` | `/tapdb/api/create/{template_euid}` | `gui/router.py:1998` |
| `PATCH` | `/tapdb/api/objects/{euid}` | `gui/router.py:2238` |
| `DELETE` | `/tapdb/api/objects/{euid}` | `gui/router.py:2267` |
| `POST` | `/tapdb/api/object/{euid}/assess` | `gui/router.py:2303` |
| `POST` | `/tapdb/api/object/{euid}/revalidate` | `gui/router.py:2327` |
| `POST` | `/tapdb/object/{euid}/repairs` | `gui/router.py:2377` |
| `POST` | `/tapdb/api/object/{euid}/repairs` | `gui/router.py:2405` |
| `POST` | `/tapdb/object/{euid}/edit-json` | `gui/router.py:2438` |
| `POST` | `/tapdb/object/{euid}/name` | `gui/router.py:2465` |
| `POST` | `/tapdb/api/object/{euid}/name` | `gui/router.py:2488` |
| `POST` | `/tapdb/api/object/{euid}/edit-json` | `gui/router.py:2511` |
| `POST` | `/tapdb/object/{euid}/status` | `gui/router.py:2545` |
| `POST` | `/tapdb/api/object/{euid}/status` | `gui/router.py:2568` |
| `POST` | `/tapdb/object/{euid}/lineage` | `gui/router.py:2591` |
| `POST` | `/tapdb/api/object/{euid}/lineage` | `gui/router.py:2630` |
| `POST` | `/tapdb/api/admin/backups` | `gui/router.py:3011` |
| `POST` | `/tapdb/api/admin/backups/{ref}/verify` | `gui/router.py:3030` |
| `POST` | `/tapdb/api/admin/backups/{ref}/restore/stage` | `gui/router.py:3052` |
| `POST` | `/tapdb/api/admin/backups/{ref}/restore/apply` | `gui/router.py:3072` |
| `POST` | `/tapdb/api/admin/backups/{ref}/rehearse` | `gui/router.py:3093` |
| `POST` | `/tapdb/admin/backups/create` | `gui/router.py:3114` |
| `POST` | `/tapdb/admin/backups/{ref}/verify` | `gui/router.py:3147` |
| `POST` | `/tapdb/admin/backups/{ref}/rehearse` | `gui/router.py:3178` |
| `POST` | `/tapdb/admin/backups/{ref}/restore/stage` | `gui/router.py:3247` |
| `POST` | `/tapdb/admin/backups/{ref}/restore` | `gui/router.py:3328` |

## Evidence and completion

Inspection used repository reads, AST route/call enumeration and targeted searches
for committing sessions, network/storage effects, launchers and runtime files.
The runtime/GUI APIs were read from the already installed public RC wheel. No
source code, installed package, live state or migration tool was modified. This
note is the only new deliverable; `git diff --check` is the docs-only validation.

Still required from the coordinator: refreshed actual process/job/principal/session
inventory and file-mode receipts; the recorded outage-owner controls; complete
native populated-source capture and preservation; exact built-image permission and
runtime smoke; final production acceptance. Source enumeration is complete for
this snapshot, while operational isolation is not yet claimed.
