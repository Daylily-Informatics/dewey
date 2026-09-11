# Independent Dewey adoption and mapping acceptance

Agent E reviewed Dewey commit `492c0ffd2a385cf1331103ebb2daa6c618605503`
against fixed published TapDB `10.1.1rc1`, release commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`. The coordinator integrated D normally
as `ee4edfe674edf22f8cf319333f1398c20b78dc7c`; a comparison against coordinator
HEAD `29e4b050c86ea9bfd7e5ebb34a215793f78ff8f4` found no differences in the
reviewed application, config, lock, Dockerfile, tests or workflows.

**Disposition:** No blocking finding in the changed public runtime, startup or
DAG/auth paths. Local adoption is accepted for actual-data qualification. This
does not claim a release image, deployment, real authenticated browser session,
database-backed application acceptance or production migration has completed.

## Review and reused evidence

| Requirement | Independently inspected evidence |
|---|---|
| Exact package | `pyproject.toml:18`, frozen lock and runtime guard require TapDB `10.1.1rc1` and Meridian `0.4.8`; Dockerfile checks the installed pair |
| Public config/runtime | `integrations/tapdb_runtime.py:45` calls documented `get_db_config` with an existing absolute path and explicit client/database identity; mismatched engine/domain/owner fails. `tapdb_backend.py:96` uses public `web.runtime.get_db` |
| Verification-only startup | `app.py:461` calls `verify_existing`; `services/base.py:107` opens `commit=False`, and `tapdb_backend.py:130` only reads templates. Native `TemplateManager.get_template` is SELECT-only; no allocator, seed or principal preparation is invoked |
| Runtime transaction authority | Native `web/runtime.py:142` applies the exact bound config/schema/domain/owner/tenant/global scope and actor, then rolls back a noncommitting session. `commit=False` alone is not proof that arbitrary code cannot allocate; the actual startup call graph contains no allocations |
| Canonical GUI | `integrations/tapdb_ui.py:104` mounts the published GUI with host-session bridge; native GUI construction and lifespan do not bootstrap the database (`gui/router.py:3420`) |
| Authenticated DAG v2 | Host-session stable subject or explicit configured service-token actor is passed to native DAG dependency; all native manifest/data/search/object routes require it (`integrations/tapdb_ui.py:85`, native `web/dag_v2.py:301`). Mount failure aborts startup |
| Removed mutation shortcuts | Old bootstrap/seed/template-overwrite, DAG v1 factories and external proxy routes are removed; no replacement compatibility engine is added |
| Strict drift receipt | Explicit config and command-local `--json --strict`; exit/status/count inconsistencies fail. Native RC also supports global JSON, but D need not change its already-correct argv |
| Behavioral changes | Managed literature download/storage errors remain errors; invalid search scopes/operators/filters/sort controls fail. Reviewed changed tests cover these outcomes |

The committed D validation JSON was parsed: **120 distinct latest test outcomes
passed**, none failed or skipped. D's already-completed frozen install, Ruff,
format, Bandit and development-wheel validation are reused; they were not
rerun. Tests of GUI/auth use actual published route factories and service fakes,
so they do not replace populated database or real browser acceptance.

[Independent review summary](20260911T051700Z_tapdb1011rc1_evidence/dewey-review-summary.json)
retains the exact D validation hash and source-coordinate comparisons.

## Historical DGX/TPX acceptance

E parsed D's eleven startup template constants without importing or starting
the application, then compared each exact category/type/subtype/version to the
coordinator's actual native-source summary. Every required coordinate occurs
exactly once, with domain `M`, template prefix `DGX` and instance prefix `DGX`.
The other eleven native templates have template prefix `TPX` and retain their
own distinct instance prefixes. D checks only its eleven required coordinates;
it does not demand converting native TPX templates to DGX.

This independently resolves the earlier DGX assumption for this actual source.
The sealed full identity receipts remain the authority for tenant/issuer,
UID/EUID, complete rows and all other identity fields. The sanitized index is
not a replacement for those receipts, nor is startup's template check a full
preservation check.

The retained existing external-object-relations GET still commits a metadata
projection (`services/external_objects.py:511`, line 538). It is not part of
verification-only startup or an added TapDB compatibility mechanism; native DAG
v2 no longer advertises that old projection. Treat all HTTP processes as source
writers during the outage. Do not rewrite historical metadata as a side effect
of this adoption or treat it as authoritative lineage.

## Four dormant allocator mappings accepted

Input owned by C:
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-data-migration-20260911/docs/plans/evidence/20260911T053316Z_dewey_source_sequence_mappings.json`.
SHA-256 `5b69e68dea09d25bb18e0b3383e96c0250848c8c6eba5ccba8ec42658e862bf8`.

E independently read exact historical tag `9.0.9`, peeled commit
`52d5f498dc4751b7e42d346bee2811a14080e5a5`; its `schema/tapdb_schema.sql`
SHA-256 is `64362e2882a7b424f6bf3c6b3d9c21d1e859ec98d4ee61ca2a728cecfd134584`.

| Sequence | Explicit prefix comment | Historical line |
|---|---|---:|
| `wx_instance_seq` | WX (workflow) | 10 |
| `wsx_instance_seq` | WSX (workflow_step) | 11 |
| `xx_instance_seq` | XX (action) | 12 |
| `ay_instance_seq` | AY (assay) | 13 |

For every entry E checked the exact declaration, source hash/commit/line,
all six live catalog definition values, operator owner, schema-only dependency,
physical database identity and observed `last_value=10000, is_called=false`.
The mapping input covers exactly the four unmapped entries in the complete
twenty-generator native subreceipt. Its native sequence hash
`7dc63a2ae200cb19aa027994ee9a354be8108fe40c1ea9d478216f287ab4e1fc` was independently
recomputed from the coordinator's complete sequence subreceipt.

The input shape matches released explicit prefix mappings
(`sequences.py:295`) and the existing historical test producer
(`tests/test_identity_inventory_helpers.py:13`). It does not assign new EUIDs,
change counters or substitute guessed name-based ownership. The other sixteen
native mappings remain intact. Accepted as an explicit input to the next
required native capture; that command still validates the actual current
catalog and strict complete source contract.

[Mapping acceptance receipt](20260911T051700Z_tapdb1011rc1_evidence/sequence-mapping-review.json)
records the comparisons. No live database, raw SQL or private TapDB API was
used in this review.

## Ready operator prerequisites and actual-data acceptance

1. Use the existing isolated exact RC operator environment and the coordinator's
   separately verified Aurora database-copy procedure. The user stopped further
   backup preparation; no new backup or direct dump/restore is required by the
   native migration, sequence or binding APIs. Preserve the existing Aurora
   backup/recovery evidence without requesting another artifact.
2. Finalize the exact container runtime config path before native bind.
   Immutable scope records that resolved path, schema, domain, owner, tenant and
   global-row policy (`runtime_principal.py:879`). Host and container paths must
   be the same binding identity. Select the explicit existing distinct control
   database and prove its operator connection on the exact Aurora transport;
   retain the native provider contract. Census existence is not authentication.
3. Execute the coordinator's authorized full source outage, native final source
   and next capture, and separately verified database copy. After exhaustive
   native source-to-copy equality and generator comparison, establish the new
   native family at the untouched copy only if no prior family/history is being
   discarded. Preserve source floors separately and retain the complete family
   for all target mutations. The [SOP contract](20260911T052037Z_dewey_source_outage_sop_contract.md)
   gives the exact entry requirements without a new backup artifact.
4. Review native migration preflight/apply/postcommit and floor verification
   outputs for the exact replacement. Require successful
   exhaustive original-row/cell/identity comparison, explicit allowed
   conversions only, complete family heads and no unresolved operation.
   Compare source-to-destination generator definitions, conservative floors and
   native planned-next values. Never shorten the family to fit an older target.
5. After all schema/data acceptance, run native runtime-principal bootstrap and
   binding plan/apply against the final runtime identity. Bind discloses PUBLIC
   TEMP revocation, verifies effective forbidden privileges, and leaves the
   explicit session-recreation requirement (`runtime_principal.py:951`). Close
   and recreate all runtime processes/pools before acceptance. A plan or
   successful operator connection alone does not prove fresh runtime behavior.
6. Use the new release image and bound runtime sessions to accept existing
   artifacts, sets, shares/downloads/manifests, QEO, lineage, idempotency and
   outbox/inbox behavior, plus authenticated GUI/DAG and tenant/actor isolation.
   Keep full row data and user credentials private; E can assess the native
   operation IDs, receipt digests, counts, violations, privilege/scope results
   and sanitized workflow outcomes. Failures keep the old source stopped and
   the target under the applicable native recovery posture.
7. Before enabling general writes, retain existing Aurora recovery protection
   and the current-member repair-forward plan. After accepted target writes,
   never claim image-only rollback or stale-source restoration preserves those
   writes. A provider-restored different physical database does not
   automatically join the immutable native family.

The exact release/publication and production mutation confirmations remain the
coordinator's gates. This report recommends no new TapDB release and performs
no deployment or source/data change.
