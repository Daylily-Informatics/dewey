# Bloom and Ursa: TapDB migration handoff and cost controls

Written after Dewey production acceptance on 2026-09-11. This is the entry
point for follow-on agents, not authorization to change Bloom or Ursa.
The user reports nearly five hours and $600 in tokens for Dewey. Do not repeat
that execution pattern. Billing was not independently measured here.

## Instructions to the next agent

> Migrate the named service to exactly TapDB **10.1.1rc1**, using this handoff
> and the completed Dewey evidence. Start with the service's actual live source
> and data. Use one operator, one short ledger, and bounded independent review
> of the identity/allocator and runtime privilege boundaries. Do not recreate
> Dewey's original eight-role agent plan or requalify all of TapDB.
>
> **Build one final production container, with no intermediate container
> builds.** Finish source changes and data-shape checks first. Use the same
> immutable image digest for isolated acceptance and deployment.
>
> **Run the broad suite once; allow at most one informative rerun.** Count CI
> runs toward that limit. Reuse recent evidence when its relevant inputs have
> not changed. Use focused checks for a demonstrated failure. Do not run tests
> just to run tests, rebuild for documentation, or trigger CI on every edit.
>
> Keep updates short and milestone-based. Do not spend model turns waiting,
> narrating unchanged polls, or asking other agents to repeat accepted checks.
> Prefer a documented, bounded migration/setup SOP using the released package
> when it safely addresses a gap. Do not start another TapDB feature/release
> project unless a concrete preservation or runtime requirement cannot be met.
>
> Preserve identities, prefixes, authoritative relationships and allocator
> floors. These are completion requirements. Stop on an unresolved violation;
> cost limits do not permit deploying a known-broken image or losing identities.
> If a proven defect forces an exception to the build/test limit, state the
> defect and precisely which evidence it invalidates before expanding work.

## What actually shipped

| Item | Completed Dewey result |
|---|---|
| Service | Dewey 9.0.0, live at `https://dewey.day.lsmc.bio` |
| TapDB | `daylily-tapdb[aurora,gui]==10.1.1rc1` — explicitly accepted prerelease |
| Other runtime pins | Python 3.12; `meridian-euid==0.4.8` |
| Dewey main / annotated tag commit | `1f634ef66082eee32c788e0d8c386a20c2b8563e` / `9.0.0` |
| TapDB release commit | `02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c` |
| TapDB wheel SHA-256 | `26de691dd5f9c8fac596a18119c9220f4ea78826094753b47f9eb936b0677ce7` |
| Final image digest | `sha256:bce8846d42320467824ce9473dd2315922ea7575c92633e04ca0a159c25c613b` |
| Database | Aurora PostgreSQL 16.13; replacement `dewey_prod_tapdb10` |
| Preserved scope | Schema `tapdb_dewey_lsmcok1_local`, domain `M`, actual historical DGX bindings |
| Acceptance | Identity/conversion comparisons passed; all 20 allocator floors verified; fresh-session privileges, authenticated read/write/replay/conflict, QEO package replay, login, embedded GUI and DAG passed |
| Observation | 60 minutes: 12 healthy samples, zero restarts, HTTP 5xx log entries or tracebacks |
| Retained source | Original `dewey_prod` closed; no original-database deletion; 12 sibling services unchanged |

The [completed ledger](20260910T185538Z_dewey_tapdb10_major_ledger.md) and
[deployment acceptance summary](evidence/20260911_dewey_rc_inventory/deployment-acceptance-summary.json)
are the controlling evidence. [Dewey release](https://github.com/lsmc-bio/dewey/releases/tag/9.0.0).
Earlier plans are historical: their pending states, source pins and assumptions
are not the final result. In particular, the old metadata SOP's **two audit
rows per update is wrong**; the corrected helper and final receipts govern.

## Cheap execution order

1. **Inventory once.** Record the service's live image/source, writable-layer
   application differences, Git baseline, exact dependency, explicit configs,
   engine/database/schema/provider identity, roles, writer processes and
   recovery arrangements. Reconcile deployed code into the release branch;
   preserve unrelated branch work separately. Do not scan sibling services'
   source or turn this into a portfolio audit.
2. **Probe actual data before building.** Use released inventory/census and
   small public-API checks to identify missing metadata envelopes, retired
   graph projections, external-reference types and template requirements.
   Prepare a service-specific conversion manifest. Port removed APIs and
   initialize the embedded runtime's explicit configuration. These issues
   caused Dewey's early images to become obsolete.
3. **Freeze and copy once per required destination.** If the approved outage
   permits, keep the source closed throughout rehearsal and final copy. Use
   the copy SOP below and one informative database rehearsal. Disable outbound
   mutations/dispatch in isolation. Do not create another clone for every
   helper correction. A final-only conversion waiver used during expedited
   Dewey work does not automatically apply to another service.
4. **Complete native migration and reviewed conversion.** Preserve the
   exact baseline and intended transformations. Establish strict allocator
   advancement using every applicable source/rehearsal/recovery exposure.
   Prepare/bind the runtime principal after final schema/template setup.
5. **Finish source, then release/build once.** Batch changes, perform focused
   checks, let the designated broad/CI run own the release gate, merge normally
   to `main`, and annotate the service's own release version. Build the full
   image from that exact source and frozen dependencies. Do not reuse Dewey's
   service version or image for Bloom/Ursa.
6. **Accept and promote the same digest.** Check the actual migrated data,
   fresh runtime sessions, authenticated service workflows and embedded GUI.
   Stop the isolated process and switch only the intended service. Capture
   final allocator exposure after controlled writes and retain recovery files.
7. **Observe and close.** Use a bounded operator-side observation command with
   an agreed duration, low-rate sampling and terminal receipt. No perpetual
   monitor, busy polling, or extra agent to wait. Record release, deployment
   and acceptance separately; deferred features/PRs belong in Phase 2.

For each ledger row keep requirement, owner, status, exact evidence, and next
action only where needed. Reuse the established statuses. One coordinator
updates the ledger from terminal results; do not create a new review document
for every command. Do not declare a still-running observation complete.

### Agent and evidence budget

- Default to one implementation/operator agent. Use one independent reviewer
  for the actual conversion/allocator plan and final runtime privilege proof;
  it must not author what it independently accepts. Give it exact files and
  a bounded question. Routine packaging, documentation and polling need no
  separate agents. No automatic maximum-effort agent fan-out.
- Reuse an existing pass if the relevant code, lock, config and data assumptions
  remain valid. Record the input fingerprint once. Formatting-only changes do
  not invalidate behavioral results, although final application bytes must be
  present in the final image.
- Avoid running the same broad suite locally and in CI. Run lint/format before
  the final push to avoid a formatting failure wasting a full release cycle.
  Documentation-only verification is `git diff --check`.
- Keep large receipts on the operator host. Send agents a compact projection:
  paths, hashes/native seals, counts, violations, operation status and relevant
  diff. Dewey's source inventory exceeded 225 MB; repeatedly printing, copying
  or parsing it for different agents was unnecessary.
- A terminal native receipt owns its operation's result. A shell-output parser
  or transport error is not grounds to repeat a committed migration. Inspect
  the existing receipt and journal first. Helpers commonly write
  `*.completed.json`; do not wait forever for an assumed `.rc` filename.
- Give short updates on completion, changed scope or a concrete failure. No
  repeated background, unchanged status prose or full-history agent handoffs.

## Working Aurora source-isolation and copy SOP

Dewey did **not** need a new TapDB release to hold a healthy source isolated.
One operator used a documented database administration SOP, then the released
TapDB migration/identity/allocator interfaces.

1. Stop all writers and close connection pools. Include workers, dispatchers,
   schedulers and operator tools. Do not assume GET endpoints are read-only:
   an old Dewey external-relation GET performed writes.
2. From a distinct explicit control database, close the source using
   `ALLOW_CONNECTIONS=false` and drain existing sessions. Verify source OID,
   provider identity and zero remaining sessions. Keep it closed.
3. On the supported standard Aurora engine, create the **absent, exact named**
   destination with `CREATE DATABASE ... TEMPLATE ...` from the frozen source,
   outside a transaction. The reviewed Dewey SOP created the copy closed,
   revoked PUBLIC CONNECT/TEMP, then opened it with owner-only access. Database
   settings and connection policy must be explicitly prepared, not assumed to
   have been inherited. Existing destination means stop, not overwrite or
   silently choose another name.
4. Verify untouched-copy parity before native schema migration. Record the
   copy's actual physical identity. Establish its native recovery family and
   journal with explicit control DB and provider evidence; do not fabricate a
   native original-source fence or claim the copy is an old family member.
5. Run native migration and conversion with fixed reviewed inputs. Preserve
   journals, head anchors, registries, principal-state receipts and protected
   config/secret-recovery references separately from database protection.

This is a bounded setup SOP, not permission to substitute raw schema SQL or
patch installed TapDB. Confirm engine support for the next service; do not
assume this template-copy approach works for Aurora Limitless or every engine.

**Dewey-specific approvals:** existing Aurora backups were accepted, so no
additional dump/snapshot/backup was created; inbox/outbox messages could be
lost; a long outage was acceptable. Apply these to Bloom/Ursa only if the user
has extended the scope. Do not silently discard accepted workflow work. Resolve
necessary scope once and retain it; do not repeatedly request existing approval.
Destructive restore/reset/delete retains separate exact-effect confirmation.

## Known snags and the fixes that worked

| Symptom | Working fix; avoid repeating the investigation |
|---|---|
| TapDB 10.1.0 identity capture exceeds 128 MiB | Use the approved **10.1.1rc1** package and its receipt-limit policy. RC handled Dewey's actual inventory. Do not retry the old hard cap or patch site-packages. |
| `db schema migrate` rejects global `--json` | Omit global `--json` for this command and use its native `--receipt`. Identity/sequence commands can use their supported JSON mode. The corrected lifecycle helper handles this distinction. |
| Physical-target comparison rejects a textual port | Call public `validate_target` before `physical_target`; compare normalized values. |
| Embedded web/metrics reads service YAML as TapDB config | Initialize released `set_cli_context` with the explicit TapDB runtime config before embedded runtime initialization. Fix this in service integration before the final build. |
| Docker refuses a newly added absent NCBI key mount | Dewey's loader already treated that key as optional. Remove the invented mandatory bind; preserve the existing optional behavior. Do not create an empty secret or invent a fallback. |
| Native DAG returns `json_addl.properties must be an object` | Census the actual data first. Dewey's writers had replaced the native envelope. Preserve it in new writes; add `{}` only where absent through the reviewed public-API conversion. Reject malformed existing values. |
| Retired `properties.external_payload.tapdb_graph` | Dewey archived the exact historical projection under `dewey_tapdb10_archive["properties.external_payload.tapdb_graph"]`, then removed the active retired key. Existing authoritative lineage was independently matched first. Do not reconstruct relationships from metadata. |
| Metadata helper expected two audit rows and rolled back | Native timestamp serialization produced three rows (`created_dt`, `json_addl`, `modified_dt`) per Dewey update while the creation instant stayed unchanged. A one-row rollback probe established this. Correct the operator assertion; preserve native audit and require exact creation-instant equality. Do not patch TapDB or blindly assume three for another source shape. |
| Completed sequence transition appears below its own floor | Verify the completed operation against its exact **prior plan floors**. Its newly reserved next values remain future recovery floors, not a reason to advance repeatedly. Require committed result, sealed inputs, released fence and reconciled journal first. |
| Floor arrays differ only in duplicate count | Native family deduplicates identical `(name, value, source)` records. The corrected SOP compares that exact set while retaining all original receipts. Dewey had 371 records versus 333 distinct, with 38 exact duplicates. Do not ignore changed values/provenance or drop future floors. |

For an ambiguous apply or lost acknowledgement, retain intent/journals/fences
and use native reconciliation. A failed or rolled-back transaction can still
consume sequence values. Never reset to table row maxima or retry blindly.

## Preservation and runtime requirements that still matter

- Inventory **every** generator, including dormant/new prefixes. Preserve stored
  UID/EUID, prefix, domain, machine/issuer/tenant and creation identities,
  deleted records, audit and authoritative lineage. Dewey's 20 generators,
  domain M and DGX bindings are observations, not constants for other services.
- The first resumed allocation must exceed applicable assigned, reserved,
  previously available source-next, rehearsal and recovery floors. Check actual
  increments/alignment/cache/bounds/ownership; unknown mapping, unsupported
  cache state, cycling or exhaustion needs resolution before write reopening.
  Retain new exposures for future recovery even after current verification.
- Use native typed external references via
  `daylily_tapdb.external_references` where appropriate. Do not invent remote
  EUIDs, tenants or public scope. Dewey retained local DYEC directory and Ursa
  trigger identifiers as existing non-federated typed DGX objects plus lineage.
  Existing external objects were preserved; native assertions were additive.
- Explicit template preparation used `seed_templates(overwrite=False)` and
  verified original template rows unchanged. Do not force fresh-schema TPX
  bindings onto historical DGX objects. Bind runtime privileges again if setup
  introduces a required new sequence grant.
- Native runtime-principal bootstrap prepares the constrained login/CONNECT;
  **bind** establishes final scope and privileges. Review named-database PUBLIC
  TEMP revocation and needed operator grants. Recreate every runtime session;
  verify intended principal, effective TEMP=false and forbidden DDL denial.
- Startup uses `verify_existing`: no migration, seeding or principal preparation.
  Mount runtime config only into the application, preserve its actual auth and
  host mappings, and do not expose operator credentials.
- Promote only the named service, e.g. the reviewed Compose invocation with
  `up -d --no-deps --pull never SERVICE`. No shared-stack restart, `down`,
  pruning or sibling changes. Preserve DNS, cluster and data-object locations.
- Once new writes are accepted, repair forward. An image-only rollback loses
  the data/allocator contract. Any return to the old source must reconcile
  accepted writes and raise its allocators above all retained exposures.

## Reusable code and final evidence

Read these at Dewey handoff baseline commit
`43f883a61c27ba8dc647d3106b3c0e362a32d40b` or a reviewed descendant.
They contain **Dewey-specific paths, identities, counts and assertions**;
adapt them deliberately, never run them unchanged against Bloom or Ursa.

| Need | Corrected repository entry point |
|---|---|
| Freeze/copy SOP | [dewey_rehearsal_copy.py](../../scripts/dewey_rehearsal_copy.py); [final-copy handoff](20260911T082236Z_dewey_final_copy_native_handoff.md) for ordering, not stale pins |
| Native CLI lifecycle / JSON fix | [dewey_copy_native_lifecycle.py](../../scripts/dewey_copy_native_lifecycle.py) |
| Prior-versus-future floor verification / dedup fix | [dewey_sequence_transition_sop.py](../../scripts/dewey_sequence_transition_sop.py) |
| Port normalization / additive templates | [dewey_xrf_template_setup.py](../../scripts/dewey_xrf_template_setup.py) |
| Public metadata conversion / corrected audit assertion | [dewey_metadata_conversion.py](../../scripts/dewey_metadata_conversion.py) |
| Native reference conversion | [dewey_native_reference_conversion.py](../../scripts/dewey_native_reference_conversion.py) |
| Runtime principal preparation | [dewey_runtime_principal_prepare.py](../../scripts/dewey_runtime_principal_prepare.py) |
| Single final image pattern | [final-image handoff](20260911T094049Z_dewey_900_single_final_image_handoff.md); use the completed ledger for final release pins |
| Live acceptance / future exposure | [deployment summary](evidence/20260911_dewey_rc_inventory/deployment-acceptance-summary.json), [metadata verification](evidence/20260911_dewey_rc_inventory/final-metadata-identity-verification.json), [reference verification](evidence/20260911_dewey_rc_inventory/final-reference-identity-verification.json) |
| Observation result | [production-observation.json](evidence/20260911_dewey_rc_inventory/production-observation.json) |

Full protected receipts remain under
`/home/ubuntu/dewey_ops/tapdb101-20260911` on the Dewey operator EC2 host.
Use compact sanitized evidence first. Old staged helper names with `_cli_fix`,
`_dedup_fix`, `_port_fix` or `_audit_fix` document fixes now represented in the
repository scripts; earlier SOPs may still show the pre-fix hashes/assumptions.
Do not import old provisional instructions as new blockers.

The aim is one service-specific migration with reused evidence and targeted
acceptance—not another upstream TapDB qualification campaign.
