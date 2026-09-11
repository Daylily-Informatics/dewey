# Dewey native metadata and external-reference adoption

Date: 2026-09-11. Owner: D (application), coordinated with C (conversion), E
(independent acceptance), and O (sole live operator). Application baseline: normal
merge of coordinated commit `5e8761b`. Dependency remains the released, immutable
`daylily-tapdb==10.1.1rc1`; no dependency or build-input pin changes are included.

## Observed failure and application correction

Candidate `c6406b8ffb40e58feaba31e2163d77448d47698c` passed initial application and
runtime-principal checks on the isolated migrated database, but native DAG v2
rejected historical ordinary instances because `json_addl.properties` was absent.
Dewey's instance writer discarded the native factory envelope. Its external
relation reader also persisted an obsolete metadata graph projection.

The corrected writer retains the factory's `properties`, `action_groups`, and
`audit_log`, together with flat Dewey application fields and creation audit.
Existing reads and updates require a valid properties object. New lineages have
`properties: {}`. No runtime old-shape conversion is present. Flat application
fields remain in their existing query locations; authoritative relationships are
resolved from lineage.

The old metadata graph writer and generated `external_graph_ref` response are
removed. Relation listing uses a read-only session. Existing stored idempotency
responses remain immutable historical evidence and never establish native edges.
An existing relation with missing, duplicate, deleted, wrongly scoped, or mismatched
canonical endpoints fails; replay cannot reconstruct its endpoints from copied IDs.

## Shared native adapter contract

`dewey_service.integrations.tapdb_external_references` exposes:

- `resolve_relation_endpoints(session, relation)`: exactly one active
  `has_external_relation` source lineage and one `is_external_relation_for`
  external-object lineage. Nodes and lineages must match relation domain, Dewey
  issuer, and tenant. Sources are typed Dewey artifacts or artifact sets.
- `build_external_target(payload)`: explicit semantic target classification.
- `build_external_link_spec(relation, endpoints)`: native immutable specification,
  or `None` only for an explicitly non-federated target.
- `attach_external_relation(session, relation)`: public native
  `ExternalReferenceService.attach`, or `status="non_federated"`. It neither
  commits nor seeds templates nor changes historical DGX objects.
- `lock_external_relation_source(session, source)`: locks the real source before
  the application looks up or creates its local DGX relation. Native attachment
  retains TapDB's own locking, identity claims, and conflict checks.

Native assertion authority is `dewey.external_object_relation`. The assertion
timestamp is the persisted relation's timezone-aware `created_dt`. Provenance is
canonical JSON with contract `dewey.external_object_relation/v1`, relation UID,
source-lineage UID, and external-lineage UID. Migration and later application
attachment produce the same specification; actor, current time, image, and
migration-run identifiers do not change it.

TapDB target identity is exact service ID plus remote EUID. Target kind and tenant
are descriptors, not identity-key components. Conversion must group by the native
identity key, reject conflicting non-null descriptors, and group assertions by
source UID, native target identity, and relationship type. The native service
enforces those conflicts for routine writes.

## Reviewed semantic mapping

The controlling private-safe census is
`docs/plans/evidence/20260911_dewey_rc_inventory/rehearsal-c6406b8ffb40-external-relation-census.json`,
SHA-256 `71946640e8e194665a1c93878b1c2588b9cdb718cd238972943d6b7fbb004e95`.
O owns verification of the remote service contracts supporting these mappings.

| External system / type | Native disposition |
| --- | --- |
| `atlas / patient` | TapDB object target |
| `bloom / sequencer` | TapDB object target |
| `bloom / sequencing_run` | TapDB object target |
| `ursa / analysis` | TapDB object target |
| `ursa / analysis_job` | TapDB object target |
| `dyec / dayoa_analysis_directory` | Non-federated local DGX identity and lineage |
| `ursa / run_directory_analysis_trigger` | Non-federated local DGX identity and lineage |

The five native kinds account for 286 historical assertions; the two operational
kinds account for 154. Operational identifiers never become federated or public
because their strings happen to resemble EUIDs. NULL tenant does not imply public
scope. Existing literature identifiers have explicit public semantics:
`pubmed/pmid`, `pubmedcentral/pmcid`, and `doi/doi` use native opaque identifiers in
their matching namespace, kind `article`, scope `public_global`.

Future unknown kinds require an explicit `reference_target` in the external-object
create request: `tapdb_object`, `opaque`, or `non_federated`, with only the declared
fields accepted. A supplied descriptor cannot contradict a reviewed known kind.
The validated GUI external-object path supplies `tapdb_object` explicitly.
Remote object IDs are retained exactly; the adapter never mints remote EUIDs or
uses metadata URL fields to construct federation routes.

## Conversion and deployment boundary

C owns the separate one-time conversion: add missing properties objects, preserve
all other flat values, archive each old graph value verbatim under
`dewey_tapdb10_archive["properties.external_payload.tapdb_graph"]`, and remove the
active obsolete key. Historical DGX objects and their paired lineage stay intact.
The archive is evidence, never native relationship input.

The operator must provision only the two reviewed bundled native XRF templates,
refresh native runtime binding for the resulting allocator grants, and run native
attachment using the actual bound Dewey runtime principal. Runtime startup does
not provision templates, migrate metadata, or change permissions. No allow-global
policy change is included. C/O/E own actual PostgreSQL conversion and concurrency
acceptance; these local application checks do not substitute for that evidence.

O must merge the accepted application commit normally, build a complete new image,
and perform native DAG and authenticated workflow acceptance against converted
data. This source change alone is not a deployed or accepted release.

## Focused validation

Environment: Python 3.12, `source ./activate day`, exact TapDB `10.1.1rc1` and
Meridian `0.4.8`. Recent full CI `34580376918` passed baseline `5e8761b` and was not
repeated merely for coverage. Only newly affected behavior was checked:

| Check | Result |
| --- | --- |
| Backend unit file | 12 passed |
| New adoption cases, relationship, literature, and external-link files | 30 passed; one new DAG assertion used the wrong native response path |
| Corrected native DAG assertion, changed relation GET case, search file | 18 passed |
| Added lineage-scope cases, native attach, normal relation lifecycle | 5 passed |
| Added corrupt-existing-relation cases, normal lifecycle, literature | 8 passed; two new tests expected the wrong exception class |
| Only those two corrected conflict expectations | 2 passed |
| Ruff on application and affected test files; `git diff --check` | Passed |

The two test-authoring corrections did not change native behavior: DAG v2 places
nodes under `elements.nodes`, and a mismatched canonical pair correctly raises
`DeweyConflictError`. Test doubles verify caller ordering and read-only behavior;
the DAG payload builder and native target/spec classes come from the installed
release. PostgreSQL identity claims, XRF allocator state, and runtime authorization
remain independent acceptance gates.
