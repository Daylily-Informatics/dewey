"""Transactional outbox helpers for Dewey domain events."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, cast

from dewey_service.registration_contracts import OutboxEventEnvelope, canonical_json
from dewey_service.tapdb_backend import OUTBOX_EVENT_TEMPLATE


class OutboxServiceMixin:
    def _build_outbox_event(
        self,
        *,
        event_type: str,
        occurred_at: str,
        payload: dict[str, Any],
        correlation_id: str,
        causation_id: str | None = None,
    ) -> OutboxEventEnvelope:
        event_seed = {
            "event_type": event_type,
            "payload": payload,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
        }
        event_id = sha256(canonical_json(event_seed).encode("utf-8")).hexdigest()
        return OutboxEventEnvelope(
            event_id=event_id,
            event_type=cast(Any, event_type),
            occurred_at=occurred_at,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def _persist_outbox_event(
        self,
        session,
        *,
        event: OutboxEventEnvelope,
        idempotency_key: str,
        receipt_euid: str,
        local_only: bool,
    ):
        payload = event.model_dump(mode="json")
        lookup_key = f"{payload['event_type']}:{payload['event_id']}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=OUTBOX_EVENT_TEMPLATE,
            field="outbox_lookup_key",
            value=lookup_key,
        )
        if existing is not None:
            return existing
        return self.backend.create_instance(
            session,
            template_code=OUTBOX_EVENT_TEMPLATE,
            name=lookup_key,
            json_addl={
                **payload,
                "outbox_lookup_key": lookup_key,
                "idempotency_key": idempotency_key,
                "receipt_euid": receipt_euid,
                "dispatch_status": "local_only" if local_only else "pending",
                "local_only": bool(local_only),
            },
        )


__all__ = ["OutboxServiceMixin"]
