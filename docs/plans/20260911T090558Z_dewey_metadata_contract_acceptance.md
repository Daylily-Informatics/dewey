# Dewey metadata conversion: independent released-contract review

E accepts the bounded preparation below for exact TapDB `10.1.1rc1`. This is
source and receipt review, not acceptance of an applied conversion. O remains
the sole live operator; O/C/D own the implementation and controlling ledger.
No package change, new release, live query, mutation or test rerun was performed
by E. Original `dewey_prod` remains closed under the accepted source SOP.

## Actual evidence and scope

Dewey source inspected: commit
`5e8761b9e9bbfd353bf759e8a4e009fcaabfbd2d` in the controlling worktree.
Released TapDB source: commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`, exact `10.1.1rc1`.
The installed public `daylily_tapdb/external_references.py` is byte-identical to
that source; SHA-256
`db027beea6363415cf5dddd4b65478878f265e69c0fcd0d5a9d4cb967e76ddef`.

The controlling worktree is
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-tapdb10-major-20260910`.
All following actual receipts are under its
`docs/plans/evidence/20260911_dewey_rc_inventory/` directory.

| Actual receipt | SHA-256 | Accepted meaning |
|---|---|---|
| `rehearsal-c6406b8ffb40-runtime-verified.json` | `197cd09c7a2ea876316d80fc33f1e0b0620751a4a348ecc2e3ed288cc59e8d86` | Fresh runtime login/scope/privilege-denial and 11 historical DGX template bindings passed. E reproduced the helper seal `20545b6d27c7183432cc419f3898664dabb31c8b4c9112c20363540cf6cce824`. This is a Dewey helper receipt, not a native TapDB receipt format. |
| `rehearsal-c6406b8ffb40-app-read.json` | `700af89b99f7b30171094f63b44fadd12caaa20509d2886475487ae518333b82` | Ten preceding checks completed; the graph request returned 409. The read phase is failed, with no controlled-write acceptance. |
| `rehearsal-c6406b8ffb40-metadata-shapes.json` | `617389a02b41075809f4157c89f4114ca2e52c870b4dfaf715a390f98e89986e` | 12,091 Dewey instances lack `properties`; 109 have object properties and graph metadata. Of 1,015 visible lineages, 1,014 lack `properties`. These are shape counts, not permission to transform every database row. |
| `rehearsal-c6406b8ffb40-external-relation-census.json` | `71946640e8e194665a1c93878b1c2588b9cdb718cd238972943d6b7fbb004e95` | Runtime `dewey_rehearsal_9` on exact rehearsal database: 396 external objects, 440 relation objects, 880 authoritative endpoint edges, all relevant endpoints active and NULL tenant; no endpoint or graph mismatch. All 440 graph entries on 109 active rows carry the Dewey relation source marker. No canonical reference template is runtime-visible. |

E read the retained census producer. It reads under the actual runtime RLS
scope and does not filter away deleted rows in its underlying object/graph
queries. The reported external objects, relation objects and graph rows are
active. It establishes local authoritative relation agreement, not remote
ownership. Its `identifier_validates_as_euid` flag proves syntax only.

The census's `duplicate_native_assertion_groups` key includes
`external_object_type`; the native TapDB-target identity does not. The actual
conversion plan must additionally detect collisions using the native keys
below. This can use the already captured rows; it is not a request to repeat
the census.

## Metadata envelope and historical projection retirement

1. Preserve the native factory envelope for new ordinary Dewey instances.
   `InstanceFactory._build_json_addl` materializes `properties`, `action_groups`
   and `audit_log` from the template. Dewey's current `create_instance` replaces
   that envelope at `dewey_service/tapdb_backend.py:169`; the writer correction
   must retain it while preserving the existing flat application payload.
   Do not silently coerce a malformed properties value. New lineages also need
   an object-valued properties envelope if they are to support native detail
   projection.
2. On exactly enumerated ordinary historical rows with a missing key, adding
   `properties: {}` is an honest envelope repair. Retain every existing flat
   field and value, including descriptions and denormalized relationship
   fields. They may support existing search/display, but must not establish
   DAG edges or remote ownership. Do not promote all flat payload fields into
   public properties, and do not create a runtime compatibility reader.
3. Retire `_sync_external_graph_refs_for_target` and the old graph-reference
   renderer. The current GET listing path calls the synchronizer inside
   `commit=True`; the corrected listing must not persist graph or XRF changes.
   Relationship mutations must write through the explicit authoritative path
   in their own outer transaction.
4. Preserve exact obsolete graph values as bounded migration evidence before
   removing their active `properties.external_payload.tapdb_graph` key. Keep
   the containing properties and every unrelated external-payload field.
   Merely setting the graph to `[]` is insufficient: DAG rejection tests a
   nonempty value, but the native audit flags key presence. No relocation to a
   live metadata field, alternate parser, URL resolver or replay source is
   accepted.
5. An archive is legitimate only when it is explicitly historical and
   non-authoritative, bound to the original row identity and exact old-value
   hash, retained with the conversion receipt, and consumed by no relationship
   writer or graph reader. Use one reviewed evidence mechanism; this is
   retention of the changed projection's evidence, not a new database backup.
   Public/Git evidence should contain only safe counts, keys and hashes.

The graph blobs are not inputs to typed-link derivation. They are checked
against and retired in favor of the already persisted authoritative data.

## Typed links and opaque identifiers

An eligible existing local relationship has exactly one active
`has_external_relation` edge from the artifact/artifact set to the persisted
DGX relation, plus exactly one active `is_external_relation_for` edge from the
persisted DGX external object to that same relation. The existing payload's
target and external-object identifiers must agree with these endpoints. The
relation supplies the business relationship; the external object supplies the
existing target identifier and owning-system classification. Preserve all
original DGX rows and both original edges, including their identities.

For a remote TapDB object, use only public `TapDBObjectTarget` and
`ExternalReferenceService.attach`:

- The service ID is the exact registered owning service ID. Do not infer it
  from a URI, prefix or alternate alias.
- The remote EUID must be an actual owning-service identifier supported by the
  owning contract/evidence. A string passing `validate_euid` is insufficient.
- Native target identity is exact `(service_id, object_euid)`, independent of
  `target_object_kind` and remote tenant descriptors. Reject conflicting
  non-null descriptors across that key. Optional missing descriptors may be
  enriched by the native service; conflicting ones may not.
- A native assertion is keyed by local source, that XRF identity and the exact
  relationship type. Check duplicates at this grain, without adding the old
  external-object type as another identity dimension.
- The source passed to the service is the authoritative local artifact or
  artifact set, loaded in that transaction. The service owns the newly
  persisted source-to-XRF lineage and generated XRF/lineage identifiers.
  Do not use the old graph list, direct generic XRF writes or raw sequence SQL.

The census contains three private `dyec/dayoa_analysis_directory` path
identifiers and 148 `ursa/run_directory_analysis_trigger` objects, of which
114 have EUID-shaped values and 34 do not. E independently inspected Ursa
commit `b401623d68be7e7111fa18d2fbbb8195506c62c8`:

- `daylib_ursa/resource_store.py:558–563` exposes the stored logical
  `payload.trigger_euid` when present.
- At lines 2637–2644, the older creation path retains a supplied logical key
  even when it differs from the newly minted instance EUID. Lines 2696–2705
  describe a newer path assigning the minted EUID. Historical kind plus EUID
  syntax therefore cannot distinguish the two representations.
- `daylib_ursa/workset_api.py:11393–11400` sends that logical trigger identifier
  to Dewey, while lines 11407–11414 send `job.job_euid` for `analysis_job`.

E accepts preserving all 148 triggers as non-federated local identifiers,
including the 114 EUID-shaped values. Together with the three DYEC directory
identifiers this accounts for 151 external objects and 154 original relations.
The other declared owning-object classes account for 245 external objects and
286 relations. These counts are a classification crosswalk, not permission to
skip exact native-key deduplication or a claim that remote objects were fetched
in this review.

`ExternalIdentifierTarget(scope="tenant")` requires the source's actual tenant
UUID. `scope="public_global"` is documented for genuinely public identifiers.
The existing un-tenanted internal path/trigger identifiers must not be relabeled
public or assigned an invented tenant to satisfy this enum. The safe released
disposition is to retain such records as the existing typed local DGX external
objects, relations and authoritative local lineage, explicitly non-federated.
Their obsolete graph projections are still retired. They remain searchable
through the existing application data; no false native external traversal is
claimed. A future tenant/identifier contract would be a separate change.

## Canonical template provisioning and native principal binding

The historical complete source receipt contains a TPX-identified
`reference/external_identifier/tapdb_object/1.0/` template, but the actual Dewey
runtime census sees no reference templates. Preserve historical rows;
provision exact released templates into the explicit `M` / `dewey` owner scope.

The bounded public-loader path is:

1. Load the installed core definitions using public
   `templates.loader.find_tapdb_core_config_dir` and `load_template_configs`.
   Select exactly `reference/external_identifier/tapdb_object/1.0/` and
   `reference/external_identifier/opaque/1.0/`. Keep their source metadata and
   canonical fields intact; do not reconstruct or edit the definitions. The
   native audit expects both kinds even when no opaque instances are created.
2. In an exact authenticated operator REPEATABLE READ transaction, call public
   `templates.loader.seed_templates` with that two-definition list,
   `overwrite=False`, `domain_code="M"`, `owner_repo_name="dewey"`, the installed
   core directory and the existing explicit domain/prefix registry paths.
   Require the actual precondition of no existing Dewey-owned copies; do not
   let skip-existing hide a divergent definition.
3. The public loader validates reserved XRF definitions and the existing
   `daylily-tapdb` reserved-prefix registry claim, provisions/verifies the XRF
   sequence and sets the explicit row owner context. It does not reassign the
   reserved prefix to Dewey. It creates new native template identities while
   preserving all 22 original templates, including 11 historical DGX bindings.
   The two-template list does not trigger core governance-object creation.
4. Preserve existing generator state. `ensure_instance_prefix_sequence` can
   add its native catalog annotation, but refuses a stale existing allocator;
   it never repairs or rewinds one. Template insertion/audit uses native
   allocators and must appear in the post-change inventory/floor evidence.
5. Capture and independently review a new native binding plan for the same
   immutable runtime path/scope, then apply it through the existing public
   overlay/bind lifecycle. The current scope does not change. The native
   classifier can now authorize XRF and TPX sequences through the new
   `M/dewey` template evidence; accept only the actual proven plan's additions.
   No manual grant, role escalation, new membership, schema CREATE or TEMP.

Do XRF attachment in the actual bound runtime session after provisioning and
binding. `TemplateManager.get_template` filters domain and coordinates but
does not add an issuer filter. An unrestricted operator can see both the
historical TapDB-owned template and a new Dewey-owned template. Runtime RLS
provides the required owner restriction, so an operator session is not the
appropriate XRF writer for this mixed-owner physical schema. Do not replace
the manager or inject a private template-selection helper.

The runtime remains tenant NULL with `allow_global_claims=false`. Native RLS
permits NULL-tenant rows when the current tenant is NULL; global TapDB XRFs do
not require broader configuration or grants. Preserve the exact bound role,
runtime configuration path, secret and domain/owner scope. The native XRF
service also validates that the reference and template owners match.

## Transactions, replay and deleted data

`ExternalReferenceService` never commits or rolls back its caller's outer
transaction. Attach locks an active persisted source, claims/reuses the XRF
and creates/reuses one source-to-XRF lineage. The one-time conversion and
future application writer must agree on stable assertion authority,
timezone-aware assertion time and provenance. An active replay compares all
three exactly. Use a stable persisted relation timestamp and provenance from
the persisted relation/lineage identities, or persist and replay the original
specification. Do not regenerate time, actor, image version or a new migration
run ID for an existing assertion.

`services.object_operations.update_object` is a public path for enumerated
ordinary instance/lineage metadata changes. It accepts a complete object-valued
`json_addl`, defaults to dry-run, flushes an applied change, and prohibits
generic template/XRF mutation. The `actor` parameter labels its receipt; the
database audit actor comes from the actual transaction context.

For operator metadata changes, public `operator_session`, a SQLAlchemy Session
bound to its connection, and public `apply_transaction_context` with the exact
operator identity/schema/domain/owner/tenant/actor are supported. The explicit
operator context uses `assert_runtime_role=False`; independently require exact
operator authority/physical identity. O/C must own clear begin/commit/rollback
boundaries because `operator_session` yields a Connection and rolls back
unfinished work on exit. This is separate from runtime XRF attachment.

Deleted rows are not silently revived or skipped from preservation evidence:

- Public `update_object` refuses a soft-deleted object. Native XRF attachment
  refuses a deleted source and refuses a soft-deleted canonical XRF winner.
- The lineage endpoint trigger executes on **every** update, including JSON
  changes, and requires active visible endpoints. A metadata-only update is
  not exempt.
- Current external-relation evidence reports no deleted relationship or graph
  cases. For the envelope repair, enumerate any deleted rows or lineages with
  unavailable endpoints in the exact plan. Preserve them unchanged and record
  their historical exclusion if no released public mutation applies; do not
  toggle deletion flags, disable triggers or broaden the manifest.
- Unknown/foreign graph entries must never become guessed XRF links. The
  actual census has none; an unexpected case in the exact plan is a stop for
  explicit disposition, with the full original projection retained.

O additionally reports a new deleted/archive census, SHA prefix `93bdb29c`,
showing all 12,200 Dewey instances and 1,015 lineages active and the proposed
archive key absent. Its full local receipt was not yet available to E at this
review; the exact conversion plan can carry and verify that existing receipt.
No repeated census is requested.

## Acceptance checklist for the actual conversion

1. Retain the failed graph/read receipt. Bind the conversion plan to exact
   rehearsal OID645854/config/source inventory, code hash, actual row set,
   stopped target writers and fresh output paths. No original-source access.
2. Before writing, require each complete old JSON value to match its native
   inventory cell hash. Preserve numeric JSON values exactly; an ordinary
   Python floating-point round trip cannot justify changed original values.
3. Enumerate exact old/new JSON hashes per changed row, unchanged identities,
   the precise archived graph values, missing-envelope insertions and any
   unchanged deleted/history exceptions. Retain every flat field and unrelated
   nested field. No copied string or graph blob becomes relationship authority.
4. Prove exactly the two canonical Dewey-owned template additions, expected
   native audit effects and native catalog annotation changes. Preserve all
   historical template definitions, UIDs/EUIDs and bindings. Review/apply the
   fresh same-scope native principal plan before runtime XRF writes.
5. Materialize an exact target/assertion plan from authoritative lineages and
   owning-type classifications. Check native target-key/descriptor conflicts
   and assertion-key duplicates. Account for all 440 original relationships as
   either a justified XRF assertion or an explicit preserved non-federated
   local relationship. Do not invent a fixed count before classification.
6. Capture actual public-service results, generated identities and audit
   provenance. Native XRF and lineage rows must have the canonical template,
   exact properties, correct owner/tenant, original local source endpoint and
   stable assertion data. All 880 original endpoint edges stay unchanged.
7. Full native identity verification needs a newly reviewed conversion
   manifest: the earlier schema-only manifest allows none of these new data
   changes. Permit only the enumerated original-row JSON/modified-time changes,
   exact two new templates, expected new XRF/lineage rows and attributable new
   audit rows. Independently compare original immutable columns and all other
   cells. Generic `added_rows` permission alone is not evidence that arbitrary
   new rows are acceptable.
8. Under the actual runtime config, run released
   `tapdb --config ABSOLUTE_RUNTIME_CONFIG --json validation external-references
   --sample-limit 25` after conversion. Require valid canonical seed state,
   exact expected reference counts, no malformed XRFs, no duplicate links,
   no obsolete graph keys and no copied pseudo-edge properties. This newly
   relevant native audit does not replace the explicit missing-envelope and
   complete identity checks, and it makes no remote ownership proof.
9. Resume the bounded authenticated graph/read checks on the rebuilt writer
   image and actual converted data. Verify local retained edges plus justified
   canonical projections, no URL/auth graph routing, and explicit non-federated
   opaque disposition. Prove new-object envelopes and exact active replay with
   newly affected focused cases; reuse already passing unrelated tests.
10. Capture all exposed allocator boundaries after conversion/application
    acceptance through the accepted full-family exposure path. Carry every
    source/rehearsal floor into final-copy planning, including native values
    consumed by template/XRF/lineage/audit insertion or a failed transaction.
    Do not rerun the old completed-transition verification as if it described
    a later written inventory; retain its historical receipt.

This checklist makes conversion inputs reviewable with the released platform.
It does not authorize unreviewed row changes, broad seed/overwrite, a second
backup or scope changes. L08/L10 need actual amended conversion/application
evidence; earlier schema-only preservation and successful runtime privilege
checks remain valid for their original phases.

## Source references used

All native line references are against the exact released commit above.

| Source | Boundary |
|---|---|
| `daylily_tapdb/external_references.py:55–148, 284–321, 345–359, 453–579` | Target identities, exact canonical template/properties, lineage assertions and metadata rejection/projection |
| `daylily_tapdb/external_references.py:606–804, 831–943` | Active-source requirement, owner-consistent XRF claim, attach/replay, detach and authority-scoped reconciliation |
| `docs/external-references-and-federation.md:10–211, 399–441` | Application remote-validation ownership, public opaque scope, sole public writer, transaction ownership and explicit application migration |
| `daylily_tapdb/factory/instance.py:334–451, 529–562` | Natural-identity claim and native envelope |
| `daylily_tapdb/templates/loader.py:789–872, 875–1039` | Explicit owner template lookup/insertion, exact bundled reserved-prefix validation and bounded seeding |
| `daylily_tapdb/templates/manager.py:57–106` | Domain/coordinate lookup relies on runtime RLS for issuer isolation |
| `daylily_tapdb/runtime_principal.py:274–316, 613–673, 875–914, 1227–1256` | Public operator sessions, proven allocator grants, immutable scope and post-provisioning grant/bind boundary |
| `schema/rls.sql:337–368, 384–452, 470–537` | Audit attribution, NULL-tenant scope and active lineage endpoint guard |
| `daylily_tapdb/security_context.py:25–124, 194–238` | Explicit transaction context and independent operator authority |
| `daylily_tapdb/services/object_operations.py:184–273` | Public ordinary-object update, deleted/XRF/template restrictions and receipt actor |
| `daylily_tapdb/external_reference_audit.py:37–92, 94–244` | Scoped canonical seed/XRF audit and deleted-inclusive graph-key checks |
| `daylily_tapdb/cli/validation.py:121–143` | Native runtime-scoped read-only audit CLI |
| `dewey_service/services/external_objects.py:111–186, 208–274, 431–563` | Current flattened lookup, pseudo-graph writer and read-side mutation to retire |
| `dewey_service/tapdb_backend.py:149–182, 245–286` | Current ordinary instance/lineage payload construction |
