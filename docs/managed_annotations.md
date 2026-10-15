# Managed annotations from Kahlo

`/api/v1/annotations` accepts broker human credentials bound to audience, operation and resource. Dewey introspects using its registered credential and resolves its human roles. Internal humans may create an annotation only at their operation's exact managed key. General write access is not granted; existing object/ancestor metadata restrictions remain. Artifact resolve/access retain current human permissions.

Create accepts filename, declared size1..50MiB, content type and Kahlo target. Registration records canonical owner, Kahlo caller and operation ID. Native audit records the human. Conditional PUT prevents overwrite; files remain opaque.

Completion verifies original signed session, same human/operation, exact managed location and stored size before normal idempotent registration. Resume reports stored bytes or renews only PUT instructions at the same location; original registration token and idempotency key survive expiry. Fresh human authorization is required. Recovery creates no duplicate artifact, deletes no bytes and changes no access policy. Deletion remains disabled.

GET artifacts/{EUID} resolves a persisted record. POST artifacts/{EUID}/access issues a short-lived URL under current permissions. URLs are not durable identifiers. Functional validation remains unexecuted. Coordinated ledger: Kahlo `docs/plans/20261015T075127Z_seqnas_performance_annotations_ledger.md`.
