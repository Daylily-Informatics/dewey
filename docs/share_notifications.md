# Share recipient notification contract

Explicit normalized email grants create durable notification intents in the same transaction as accepted share policy changes. Domain-only grants do not broadcast. Unchanged recipients and metadata-only edits create no new intent; removal and explicit re-addition create a fresh grant notification. Request-bound dispatch occurs after commit, without a scheduled worker.

Set `LSMC_AUTH_BROKER_SHARE_NOTIFICATION_URL` to the explicit Login HTTPS endpoint `/api/v1/dewey/share-notifications`. No endpoint is inferred. Existing `LSMC_AUTH_BROKER_CALLBACK_URL` supplies the registered Dewey origin, and `LSMC_AUTH_BROKER_SERVICE_TOKEN` authenticates Dewey. Missing configuration leaves intents pending with a visible error.

Before mail submission, the intent records current report name, deep link and expiry, then durably fences it as uncertain. Login uses the same operation identity as a second durable idempotency fence. Accepted, failed, uncertain and capture outcomes are retained and visible in the manager share detail/API. Provider acceptance does not establish inbox delivery. A crash or timeout never causes an automatic resend. Explicit resend of uncertain submissions requires reconciliation of the existing Dewey operation and Login claim/provider receipt; no automatic resend/retry endpoint is provided.

Login requires `email.sender: dewey@lsmc.com`, including manual share invitations and registration mail. Its existing SES authorization must be verified separately before production delivery. Known-user roles/groups/entitlements remain unchanged. Production native TapDB/Postgres persistence, SES authorization and browser acceptance remain release/runtime checks.
