# Released TapDB contract for Dewey's source outage and database-copy SOP

Reviewed against immutable TapDB `10.1.1rc1`, commit
`02ab7c9d0325dfcbf9dc47a03be66b62e0a22f2c`, on 2026-09-11. The coordinator owns
the controlling ledger, Aurora capability checks, exact operator commands and
live mutation/confirmation gates. This note is contract review, not migration
tooling, provider-copy execution or an additional backup request.

## Current disposition and user direction

**Use the fixed released package with the authorized source outage SOP. No new
TapDB release or additional backup artifact is required by the native migration,
sequence or principal-binding APIs.** The user explicitly stopped additional
backup preparation because the Aurora cluster already has backup protection.
No new backup was created. Existing protection remains the provider's recovery
claim; it is not itself a final cutover-state or native family receipt.

The earlier claim that L04 necessarily required a new native source-quarantine
entry point is withdrawn. The source's writer exclusion can be owned by the
authorized service outage SOP. TapDB still physically enforces its own target
fences during mutation. A provider-supported database copy into the exact new
`dewey_prod_tapdb10`, created separately by the coordinator, can enter native
inventory, migration, floor and principal workflows without a logical backup.
The coordinator reports AWS official documentation supports the regular Aurora
database-template copy and is recording AM04. This agent did not execute or
independently qualify that provider copy operation.

No generic external-writer attestation can be passed as `writer_fence`.
Native `validate_writer_fence` accepts only physically verified
`exclusive_database_connect` or retained-session
`database_connections_disabled` contracts (`sequences.py:576`). Keep service
outage evidence separate; do not fabricate a fence, restore receipt, family
join or deliberately interrupted native epoch.

## Initial family condition

C and the coordinator confirm no recovery family or journal has been created
or used in this task. Both original source contracts have no family entry;
only operator installation, config, census and discovery receipts exist. This
permits the following initial-family order. Existing history could not be
replaced by a new empty family.

The released family descriptor has one exact physical origin and immutable
explicit journal roots (`backup/recovery.py:81`). A separately copied database
cannot pretend to join a source-originated family: `require_family_member`
checks evidenced physical membership (`backup/recovery.py:393`). For this new
initial migration family, its origin is the **verified untouched copy**, before
any mutation. Original-source receipts and allocation evidence remain separate
inputs to preservation and target floor acceptance.

## Required source/copy/native order

1. Establish the reviewed outage of **all** Dewey HTTP processes, workers,
   schedulers/drains, CLI clients, connection pools and any other clients using
   old `dayhoff` credentials. Prevent automatic restarts. GET routes are not
   assumed read-only: external-object-relations GET synchronizes metadata and
   commits. Operator access cannot distinguish another client using the same
   login, so service shutdown evidence is essential.
2. Review native source census and account for every remaining source session.
   Census is an observation, not a fence or disconnected-client inventory.
   Capture the final complete source contract using exact `9.0.9`, all verified
   allocator mappings, selected limits and no new family. The 225 MB discovery
   receipt is not final-outage evidence.
3. Take the native read-only source-next observation with
   `db sequences advance --floors <explicit-input> --receipt <new-path>
   --sequence-mappings <source-mappings>`, without `--apply` or a replacement
   family. Require its complete inventory hash to match the final source
   contract's sequence-inventory hash. `next_value` is the native conservative
   safe next after supplied/assigned/allocated floors (`sequences.py:488`).
4. Keep source writers stopped. The coordinator creates the exact unused
   replacement by the separately verified provider/database-copy operation.
   No direct dump/restore or additional backup artifact is part of this order.
   Keep the copy isolated from service writers until all acceptance completes.
5. Capture native historical inventory on the untouched copy with the same
   limits and verified mapping input. Compare original source to copy through
   `db identity verify --before ... --after ... --conversion-manifest ...` on
   the explicit target config. The conversion declares **only** the exact
   copied target (`tables={}`, `added_tables=[]`); every original row, column,
   identity and schema must compare without waivers (`identity_inventory.py:863`).
   Independently compare all twenty generator definitions/states and original
   final next/floor evidence. Any drift stops the procedure.
6. Before mutation, use native `db identity inventory` on the actual copy with
   `--source-version 9.0.9 --new-recovery-family-id <explicit-UUID>
   --family-receipts-dir <existing-root> --family-receipt <new-path>
   --receipt <new-contract> --sequence-mappings <verified-input>`. Repeat the
   root option for every declared future journal. Native CLI seals the family
   from that actual capture (`cli/identity.py:183`). All roots are explicit,
   existing, canonical absolute directories and remain complete/readable.
   Verify the new contract still matches the already accepted untouched copy.
7. Native schema migration uses this **copy's** exact historical contract,
   unchanged family and declared journal. It does not accept the old source's
   different physical identity as if it were the copy. Preflight recaptures and
   requires exact contract equality and physical family membership
   (`migration_identity.py:530`, line 543 and 593). No backup ID, archive,
   manifest or restore-purpose input is required (`cli/db.py:1536`).
8. Apply the unchanged preflight with native target fence establishment,
   distinct control config, exact provider contract and journal. Complete
   postcommit preservation/floor checks, then native final strict advancement
   and verification with the complete family and original-source floor input.
   No generator may be omitted because it is dormant or replacement-only.
9. Keep the old source unchanged and its writers stopped through copy
   acceptance and promotion. Any unexpected source writer/content/allocation
   invalidates the final-source capsule; stop and review new complete evidence,
   never edit receipts or silently repeat the copy operation.

The native family builder is not a recovery claim for ordinary unjournaled
application writes (`backup/recovery.py:140`). A source-only observation without
family does not waive the complete family at later native target operations.

## Native target and configuration prerequisites

| Stage | Released requirement |
|---|---|
| Target identity | Exact new physical copy, same managed schema and preserved owner; native inventory independently authenticates it |
| Migration | Explicit preflight/apply; `--establish-writer-fence --control-config ...` retains target/control sessions through apply, postcommit checks and release (`cli/db.py:1743`) |
| Sequence advance | Explicit reviewed plan/apply, original-source floors and complete unchanged family; native target fence/control/provider lifecycle (`cli/sequences.py:143`) |
| Control database | Explicit existing different database with successful operator authentication on the identical server transport; census existence alone is insufficient |
| Provider gate | Exact Aurora identity and owner authority; native gate validates competing sessions, prepared transactions, subscriptions, extensions/preloads, worker baseline and supported ACLs (`sequence_fence.py:137`, line 301 and 418) |
| Runtime binding | Final native bootstrap/bind after schema/data/floor verification; constrained `dewey_runtime_9`, exact domain/owner/tenant/global policy and fresh sessions |

The immutable runtime scope includes the **resolved absolute config path**
(`runtime_principal.py:879`). Prepare the final path used inside the container
before native bind. A host-only operator pathname and a different container
pathname are not interchangeable; native runtime sends that path in every
transaction (`web/runtime.py:150`). Do not edit a bound scope or seed/remint the
historical DGX/TPX templates. Bind discloses database-wide PUBLIC TEMP revocation
and requires all pre-binding runtime processes/pools to be recreated.

## Recovery boundary with existing Aurora protection

After any accepted target write, prefer repair forward on the current member
and current schema. Old source/image reactivation is permissible only if it
preserves every accepted write and all retained definitions/floors. An older
target missing a later generator is deliberately refused by
`backup/recovery.py:854` and `sequences.py:471`; do not shorten the family or
guess a generator recreation. Generator growth is conditional on actual native
target evidence: the released optional-prefix migration explicitly annotates
existing generators and does not create absent ones.

Existing Aurora backup/PITR recovery is provider-owned. A future provider
restore/copy with a different physical identity does not automatically join
the immutable native family, and ordinary application writes after its restore
point are not recovered by allocator floors. Such recovery needs separately
reviewed data preservation and physical-family entry; do not invent a native
join receipt. This note neither creates a new backup nor promises an unqualified
cross-database recovery route. Native interrupted target operations retain
their real journal and use native reconcile/takeover; do not manufacture an
epoch. Current-member repair forward remains the planned first response.

For completeness, earlier source review also found the ordinary native
`backup restore --mode isolated` purpose does not require a native old-source
fence (`backup/verify.py:1334`). That capability explains why no new release was
needed under the previous plan; it is **not selected or requested** by the
current no-additional-backup procedure. Existing local historical restore tests
remain valid qualification evidence, not authorization to rerun a backup.
