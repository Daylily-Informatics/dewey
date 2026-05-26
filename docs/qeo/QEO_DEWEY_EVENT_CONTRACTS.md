# QEO/KEO Dewey Event Contracts

## Boundary

Dewey persists a local transactional outbox for QEO/KEO handoff. It does not expose a public message-bus API and does not dispatch to a broker in this change.

Outbox rows are stored as TapDB instances:

- Template: `DGX/system/outbox_event/1.0/`
- Code: `dewey_service/services/outbox.py`

The outbox write occurs in the same TapDB transaction as artifact records, artifact-set records, lineage, receipt, and idempotency state.

## Envelope

`OutboxEventEnvelope` fields:

- `event_id`
- `event_type`
- `occurred_at`
- `producer`
- `schema_version`
- `payload`
- `correlation_id`
- `causation_id`

`producer` is `dewey`. `schema_version` is `1.0`. `correlation_id` is the deterministic Dewey receipt `request_id`. `causation_id` is the deterministic idempotency key.

## Event Types

- `lsmc.daylily.artifact-set.registered.v1`
- `lsmc.daylily.multiqc-artifact-set.registered.v1`

## Payload

Payload fields:

- `artifact_set_euid`
- `analysis_euid`
- `manifest_sha256`
- `parser_family_hint` when supplied or derivable

Payloads intentionally do not contain:

- PHI
- sample names
- local filesystem paths
- `storage_uri`
- `relative_path`
- artifact lists
- share URLs
- bearer tokens

Consumers must resolve details from Dewey receipts and artifact/set read APIs using scoped service auth.

## Local-Only Mode

When registration request `local_only` is true:

- receipt `status` is `local_only`
- outbox `dispatch_status` is `local_only`
- Dewey still validates the manifest and storage metadata

Local-only mode is explicit and not a silent validation bypass.

## Consumer Rules

QEO/KEO consumers must be idempotent. Dewey events are at-least-once evidence handoffs. Consumers should key processing by `event_id`, `artifact_set_euid`, and `manifest_sha256`, then fetch receipt/artifact details from Dewey instead of crawling workflow storage.
