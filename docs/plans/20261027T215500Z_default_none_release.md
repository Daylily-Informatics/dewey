# Dewey no-expiration default release

## Current continuation state
Updated2026-10-27T22:00UTC. Dewey12.0.10 is deployed and native health/readiness
PASS through21:59:15UTC with0restarts. Exact annotated source793db17e5f2a0938bea1bc91c19abd3b4828fcdd; final EC2 image digest
9a48b00795666767e317b039faddb3a2224c174074977f1d7e40aabfaae1c551.
Login4.1.2 and all11other siblings retained their exact IDs/images/starttimes.
No Login/Dayhoff image build or fleet deployment. Final Dewey image built only
on EC2i-07df3a933e4839f52/us-west-2,21:55:11–21:56:43UTC.

User explicitly requires global default NONE while finite share/grant deadlines
remain available for both LSMC domains and every other domain. Code/config/UI
now accept null consistently; no persisted share/grant deadline was rewritten.
The coordinator owns the remaining native ADMIN management-session
PATCH /api/v1/registry/defaults {"share_lifetime_days":null} and GET/UI proof.
The new process still reports the existing persisted30-day setting until that
explicit native update; no silent override or raw database mutation occurred.

The original full-upload-complete cutover HOLD was SUPERSEDED by the
coordinator's explicit safe-window instruction after uploader session34266
exited1: all130object operations reportedcomplete, no mutating multipart
request pending. That exact stopped-upload authority was retained in the
cutover receipt before graceful Dewey-only drain (exit0) and restart.

Controlling execution ledger remains product-definitions/docs/plans/
20261027_lsmc_matrix_v2_completion_ledger.md. Detached evidence/addendum: 
product-definitions/matrix/v2/evidence/deployment/20261027_default_none_source.json
and20261027_default_none_runtime.json. Sealed R28 payload remains untouched.
No pytest/lint/CI campaign, test mail, service-token elevation, schema
initialization/migration, or unreviewed analysis was performed.

## Implementation and focused evidence
Settings/config preparation default to null. Native persisted defaults accept
null through the admin API; missing share expiry resolves that exact setting.
Admin form serializes blank as null and displays No expiration. New share
editor reads the native setting; existing finite editors retain their saved
values. Explicit finite share deadlines retain maximum, timezone and future
validation. Existing per-email/domain grant controls retain their own deadlines.
No LSMC-domain exception, existing-record migration, permanent credential, or
anonymous-access rule was added.

Focused no-network capture scripts live at
`docs/plans/evidence/20261027_default_none/`. Backend exercises actual persisted
30→PATCHnull→GETnull behavior, indefinite omission, explicit finite defaults,
finite grants for six email/domain cases, and malformed inputs. UI capture
exercises actual editor creation/editing and native default-form serialization.
No provider, database or email calls.

## Deployment completion conditions
1. Exact12.0.10 annotated source tag and final EC2 image provenance.
2. Coordinator upload-complete gate before graceful selected Dewey-only cutover.
3. Native admin-session PATCH share_lifetime_days=null after code accepts null;
   GET/admin/new-share UI agree. Read-write publishing token must not be elevated.
4. Native health/readiness/stability plus12unchanged sibling identities.
5. Report source/addendum separately from sealed R28 payload; do not mutate it.
