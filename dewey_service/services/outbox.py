"""Transactional outbox helpers for Dewey domain events."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, cast

import httpx

from dewey_service.registration_contracts import OutboxEventEnvelope, canonical_json
from dewey_service.tapdb_backend import (
    OUTBOX_EVENT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

_QEO_EVENT_FIELDS = set(OutboxEventEnvelope.model_fields)
_DISPATCHABLE_STATUSES = {"pending"}


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
                "dispatch_attempt_count": 0,
            },
        )

    def dispatch_qeo_outbox(
        self,
        *,
        limit: int = 100,
        retry_errors: bool = False,
    ) -> dict[str, Any]:
        """Dispatch pending Dewey outbox events to QEO through explicit config."""

        ingest_url, token, consumer_group, timeout, verify = self._qeo_dispatch_config()
        statuses = set(_DISPATCHABLE_STATUSES)
        if retry_errors:
            statuses.add("error")
        rows = self._list_qeo_outbox_candidates(limit=limit, statuses=statuses)
        results = [
            self._dispatch_qeo_outbox_row(
                row,
                ingest_url=ingest_url,
                token=token,
                consumer_group=consumer_group,
                timeout=timeout,
                verify=verify,
            )
            for row in rows
        ]
        counts: dict[str, int] = {}
        for result in results:
            counts[str(result["dispatch_status"])] = counts.get(str(result["dispatch_status"]), 0) + 1
        return {
            "requested_limit": max(1, min(int(limit or 100), 1000)),
            "attempted": len(results),
            "counts": counts,
            "results": results,
        }

    def _qeo_dispatch_config(self) -> tuple[str, str, str, float, bool | str]:
        ingest_url = str(getattr(self, "qeo_ingest_url", "") or "").strip().rstrip("/")
        token = str(getattr(self, "qeo_api_token", "") or "").strip()
        consumer_group = str(getattr(self, "qeo_consumer_group", "") or "").strip()
        if not ingest_url:
            raise RuntimeError("qeo.ingest_url is required for Dewey QEO outbox dispatch")
        if not ingest_url.startswith("https://"):
            raise RuntimeError("qeo.ingest_url must use an absolute https:// URL")
        if not token:
            raise RuntimeError("qeo.api_token is required for Dewey QEO outbox dispatch")
        if not consumer_group:
            raise RuntimeError("qeo.consumer_group is required for Dewey QEO outbox dispatch")
        timeout = max(1.0, float(getattr(self, "qeo_timeout_seconds", 10) or 10))
        ca_bundle = str(getattr(self, "qeo_ca_bundle_path", "") or "").strip()
        return ingest_url, token, consumer_group, timeout, ca_bundle or True

    def _list_qeo_outbox_candidates(
        self,
        *,
        limit: int,
        statuses: set[str],
    ) -> list[dict[str, Any]]:
        capped_limit = max(1, min(int(limit or 100), 1000))
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=OUTBOX_EVENT_TEMPLATE,
                limit=max(capped_limit, 1000),
            )
            candidates: list[dict[str, Any]] = []
            for row in rows:
                payload = normalize_instance_payload(row)
                if bool(payload.get("local_only")):
                    continue
                if str(payload.get("dispatch_status") or "") not in statuses:
                    continue
                event_type = str(payload.get("event_type") or "")
                if not event_type.startswith("lsmc.dewey."):
                    continue
                candidates.append(payload)
                if len(candidates) >= capped_limit:
                    break
            return candidates

    def _dispatch_qeo_outbox_row(
        self,
        row: dict[str, Any],
        *,
        ingest_url: str,
        token: str,
        consumer_group: str,
        timeout: float,
        verify: bool | str,
    ) -> dict[str, Any]:
        event = self._event_from_outbox_row(row)
        row_euid = str(row.get("euid") or "").strip()
        attempts = int(row.get("dispatch_attempt_count") or 0) + 1
        base_update = {
            "dispatch_attempt_count": attempts,
            "last_dispatch_attempt_at": utc_now_iso(),
        }
        try:
            response = httpx.post(
                ingest_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"event": event.model_dump(mode="json"), "consumer_group": consumer_group},
                timeout=timeout,
                verify=verify,
            )
        except httpx.HTTPError as exc:
            return self._update_outbox_dispatch(
                row_euid,
                {
                    **base_update,
                    "dispatch_status": "error",
                    "last_dispatch_error_class": exc.__class__.__name__,
                    "last_dispatch_error_message": str(exc),
                },
            )

        try:
            response_payload = response.json()
        except ValueError as exc:
            return self._update_outbox_dispatch(
                row_euid,
                {
                    **base_update,
                    "dispatch_status": "error",
                    "last_dispatch_http_status": response.status_code,
                    "last_dispatch_error_class": exc.__class__.__name__,
                    "last_dispatch_error_message": "QEO response was not JSON",
                },
            )

        envelope_payload = response_payload.get("payload", response_payload)
        request_id = str(response_payload.get("request_id") or "").strip() or None
        if response.is_error:
            return self._update_outbox_dispatch(
                row_euid,
                {
                    **base_update,
                    "dispatch_status": "error",
                    "last_dispatch_http_status": response.status_code,
                    "last_dispatch_error_class": "QeoHttpError",
                    "last_dispatch_error_message": self._short_error(response_payload),
                    "qeo_request_id": request_id,
                },
            )

        status = str(envelope_payload.get("status") or "").strip().upper()
        write_status = str(envelope_payload.get("write_status") or "").strip()
        if status == "PARSED" or write_status == "idempotent_noop":
            return self._update_outbox_dispatch(
                row_euid,
                {
                    **base_update,
                    "dispatch_status": "dispatched",
                    "dispatched_at": utc_now_iso(),
                    "last_dispatch_http_status": response.status_code,
                    "last_dispatch_error_class": "",
                    "last_dispatch_error_message": "",
                    "qeo_request_id": request_id,
                    "qeo_ingest_id": envelope_payload.get("ingest_id"),
                    "qeo_parser_ingestion_id": envelope_payload.get("qeo_ingestion_id"),
                    "qeo_dead_letter_id": "",
                },
            )

        return self._update_outbox_dispatch(
            row_euid,
            {
                **base_update,
                "dispatch_status": "error",
                "last_dispatch_http_status": response.status_code,
                "last_dispatch_error_class": "QeoIngestRejected",
                "last_dispatch_error_message": self._short_error(envelope_payload),
                "qeo_request_id": request_id,
                "qeo_ingest_id": envelope_payload.get("ingest_id"),
                "qeo_parser_ingestion_id": envelope_payload.get("qeo_ingestion_id"),
                "qeo_dead_letter_id": envelope_payload.get("dead_letter_id"),
            },
        )

    @staticmethod
    def _event_from_outbox_row(row: dict[str, Any]) -> OutboxEventEnvelope:
        payload = {key: row[key] for key in _QEO_EVENT_FIELDS if key in row}
        return OutboxEventEnvelope.model_validate(payload)

    @staticmethod
    def _short_error(payload: Any) -> str:
        text = canonical_json(payload) if isinstance(payload, dict) else str(payload)
        return text[:1000]

    def _update_outbox_dispatch(self, row_euid: str, updates: dict[str, Any]) -> dict[str, Any]:
        if not row_euid:
            raise RuntimeError("Outbox row has no EUID and cannot be updated")
        with self.backend.session_scope(commit=True) as session:
            row = self.backend.find_by_euid(
                session,
                template_code=OUTBOX_EVENT_TEMPLATE,
                euid=row_euid,
                for_update=True,
            )
            if row is None:
                raise RuntimeError(f"Outbox row not found: {row_euid}")
            self.backend.update_instance_json(session, row, updates)
            return normalize_instance_payload(row)


__all__ = ["OutboxServiceMixin"]
