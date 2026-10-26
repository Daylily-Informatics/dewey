# Dewey 9 historical external-identity conversion scope

This is the explicit AM10 conversion disposition under the controlling ledger.
It uses the existing typed objects and authoritative lineage. No external
identifier is minted, rewritten or classified by its spelling.

## Actual relationship inventory

The read-only rehearsal census is
`evidence/20260911_dewey_rc_inventory/rehearsal-c6406b8ffb40-external-relation-census.json`,
SHA-256 `71946640e8e194665a1c93878b1c2588b9cdb718cd238972943d6b7fbb004e95`.
It covers 396 original external objects, 440 relation objects and 880
authoritative endpoint lineages. All are active and un-tenanted. Every one of
the 440 obsolete projection entries agrees with its authoritative endpoints;
no unknown projection or mismatched endpoint was found.

| Existing system/type | Objects | Relations | Conversion disposition |
|---|---:|---:|---|
| atlas/patient | 1 | 1 | Add canonical TapDB object reference |
| bloom/sequencer | 1 | 1 | Add canonical TapDB object reference |
| bloom/sequencing_run | 93 | 131 | Add canonical TapDB object reference |
| ursa/analysis | 1 | 1 | Add canonical TapDB object reference |
| ursa/analysis_job | 149 | 152 | Add canonical TapDB object reference |
| dyec/dayoa_analysis_directory | 3 | 6 | Retain typed local non-federated identifier |
| ursa/run_directory_analysis_trigger | 148 | 148 | Retain typed local non-federated identifier |
| Total | 396 | 440 | Preserve every original DGX object and both endpoint edges |

The canonical-reference subset is 245 objects and 286 assertions. Actual new
XRF identity counts must be established by the plan using the native key
`(service_id, object_euid)`, without adding object type to that key. Reject
conflicting non-null target-kind or tenant descriptors. Native assertion
deduplication uses local source, native target identity and relationship type.

The local-identifier subset is 151 objects and 154 relationships. These are
explicit semantic kinds, not a fallback after a failed remote lookup.
NULL tenant does not mean that an internal path or logical trigger key is a
public identifier. Preserve NULL tenant and the existing access scope; do not
use native opaque public-global scope or invent a tenant for these records.

## Owning trigger contract

Ursa source commit `b401623d68be7e7111fa18d2fbbb8195506c62c8` was inspected at
`/Users/jmajor/projects/mega_dayhoff/repos_work/daylily-ursa-10.0.20-dyec-13.0.5`.
`daylib_ursa/resource_store.py:563` exposes the stored logical
`payload.trigger_euid`; lines2637-2644 retain a supplied logical key even when
the instance has a different minted EUID. The newer claim at2696-2705 stores
the minted EUID. `daylib_ursa/workset_api.py:11393` sends the returned trigger
field as Dewey's external identifier. Thus the 114 EUID-shaped and 34 other
stored values share a logical-key contract; syntax is not ownership proof.
Ursa's analysis-job relation separately uses the owning `job.job_euid`.

E independently reviewed these exact source locations and accepted the
disposition in commit26d9769 of its TapDB qualification worktree. The review is
copied into this repository as
`20260911T090558Z_dewey_metadata_contract_acceptance.md`.
This source establishes identifier semantics; it is not a new live Ursa
deployment or a mutation of that service.

## Preservation and application changes

- Retain every original object/lineage UID, EUID, prefix, owner, domain, tenant,
  creation identity, endpoint and existing audit record.
- For missing envelopes only, add `properties: {}`. The actual deletion
  census SHA-256
  `93bdb29c4031c3d242e82c1d8300b46f8e780cc0f4205545d2cd6a962f9b612f`
  shows all 12,200 Dewey instances and 1,015 lineages active. The archive key
  does not already exist.
- Preserve each old graph value verbatim under the explicitly historical,
  non-authoritative `dewey_tapdb10_archive` root and remove only the active
  `properties.external_payload.tapdb_graph` key. Readers and writers must not
  consume this archive as an alternative relationship source.
- Plan exactly 13,214 ordinary row changes: 12,091 missing instance envelopes,
  109 archived instance projections and 1,014 missing lineage envelopes.
  Allow only exact planned JSON hashes, actual trigger-owned modified
  timestamps and additive audit records. Native comparison must reject all
  other original-cell changes.
- Seed the two exact bundled native reference templates into M/dewey through
  the public loader without overwriting any of the 22 original templates.
  Rebind the existing constrained runtime role using the native reviewed plan.
  Attach canonical references only through public ExternalReferenceService
  in that actual runtime scope, preserving stable assertion provenance.
- Remove the old graph projection writer and mutating relation GET behavior.
  Future objects retain the native factory envelope and use the explicit
  typed-reference contract. No installed TapDB package change is involved.

## Execution state

At09:13Z the isolated c6406b8 image was stopped gracefully with exit0 and no
OOM before conversion setup. Stop receipt SHA-256
`8df69f30769eb486cdb9dbb5f857691ee14aedbb8e8fe03080a548b58200f9e1`.
The original container is also stopped; the original source database remains
closed. No template provisioning, metadata conversion or reference creation
has been applied by this scope document.
