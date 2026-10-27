# Dewey no-expiration default release

## Current continuation state
User explicitly requires global default NONE with explicit finite share/grant
expirations still available for both LSMC domains and every other domain.
Source branch codex/dewey-share-mail-20261027; immutable baseline12.0.9.
Next patch12.0.10. No Login or Dayhoff image build. No pytest/lint/CI campaign.
Only final selected image builds on EC2i-07df3a933e4839f52/us-west-2.
Runtime cutover remains HOLD until coordinator confirms recursive upload fully
completed, to avoid uncertain multipart operations.

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
