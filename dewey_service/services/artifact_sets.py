"""Artifact set workflows for Dewey service."""

from __future__ import annotations

from typing import Any

from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

_REGISTERED_ARTIFACT_SET_TYPES = {"analysis_artifact_set", "multiqc_artifact_set"}
_REGISTERED_ARTIFACT_SET_KINDS = {"analysis", "multiqc"}
_QEO_RECEIPT_FIELDS = {
    "schema_version",
    "request_id",
    "idempotency_key",
    "artifact_set_euid",
    "artifact_set_kind",
    "report_kind",
    "manifest_sha256",
    "registered_artifacts",
    "skipped_existing",
    "failed",
    "registered_at",
    "status",
    "source_service",
    "source_version",
    "parser_hint",
}


class ArtifactSetServiceMixin:
    def create_artifact_set(
        self,
        *,
        artifact_set_type: str,
        label: str | None,
        description: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_type = str(artifact_set_type or "").strip().lower()
        if not clean_type:
            raise ValueError("artifact_set_type is required")

        payload = {
            "artifact_set_type": clean_type,
            "label": str(label or "").strip() or None,
            "description": str(description or "").strip() or None,
            "metadata": dict(metadata or {}),
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            now_iso = utc_now_iso()
            artifact_set = self.backend.create_instance(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                name=payload["label"] or f"artifact_set:{clean_type}",
                json_addl={
                    "artifact_set_type": clean_type,
                    "label": payload["label"],
                    "description": payload["description"],
                    "metadata": payload["metadata"],
                    "created_at": now_iso,
                },
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def add_artifact_set_member(
        self,
        *,
        artifact_set_euid: str,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_set_euid": str(artifact_set_euid or "").strip(),
            "artifact_euid": str(artifact_euid or "").strip(),
        }
        if not payload["artifact_set_euid"]:
            raise ValueError("artifact_set_euid is required")
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")

        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.member.add",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=payload["artifact_set_euid"],
                for_update=True,
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {payload['artifact_set_euid']}")

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            self.backend.create_lineage(
                session,
                parent=artifact_set,
                child=artifact,
                relationship_type="artifact_set_member",
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.member.add",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def remove_artifact_set_member(
        self,
        *,
        artifact_set_euid: str,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_set_euid": str(artifact_set_euid or "").strip(),
            "artifact_euid": str(artifact_euid or "").strip(),
        }
        if not payload["artifact_set_euid"]:
            raise ValueError("artifact_set_euid is required")
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")

        fingerprint = self._fingerprint(payload)
        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact_set.member.remove",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=payload["artifact_set_euid"],
                for_update=True,
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {payload['artifact_set_euid']}")

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            self.backend.delete_lineage(
                session,
                parent=artifact_set,
                child=artifact,
                relationship_type="artifact_set_member",
            )
            body = self._artifact_set_response(session, artifact_set)
            self._store_idempotency(
                session,
                operation="artifact_set.member.remove",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def get_artifact_set(self, artifact_set_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=str(artifact_set_euid or "").strip(),
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
            return self._artifact_set_response(session, artifact_set)

    def list_artifact_sets(
        self,
        *,
        artifact_set_type: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_type = str(artifact_set_type or "").strip().lower()
        with self.backend.session_scope(commit=False) as session:
            items = self.backend.list_by_template(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            rows: list[dict[str, Any]] = []
            for item in items:
                payload = normalize_instance_payload(item)
                if clean_type and str(payload.get("artifact_set_type") or "").lower() != clean_type:
                    continue
                rows.append(self._artifact_set_response(session, item))
            return rows

    def resolve_artifact(self, artifact_euid: str) -> dict[str, Any]:
        return self.get_artifact(artifact_euid)

    def resolve_artifact_set(self, artifact_set_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            artifact_set = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=str(artifact_set_euid or "").strip(),
            )
            if artifact_set is None:
                raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")

            payload = normalize_instance_payload(artifact_set)
            if self._is_registered_qeo_artifact_set(payload):
                return self._qeo_registration_receipt_for_artifact_set(
                    session,
                    artifact_set_euid=artifact_set.euid,
                )
            return self._artifact_set_response(session, artifact_set)

    @staticmethod
    def _is_registered_qeo_artifact_set(payload: dict[str, Any]) -> bool:
        artifact_set_type = str(payload.get("artifact_set_type") or "").strip().lower()
        registration_kind = str(payload.get("registration_kind") or "").strip().lower()
        return (
            artifact_set_type in _REGISTERED_ARTIFACT_SET_TYPES
            or registration_kind in _REGISTERED_ARTIFACT_SET_KINDS
        )

    def _qeo_registration_receipt_for_artifact_set(
        self,
        session,
        *,
        artifact_set_euid: str,
    ) -> dict[str, Any]:
        receipt = self.backend.find_by_json_field(
            session,
            template_code=REGISTRATION_RECEIPT_TEMPLATE,
            field="artifact_set_euid",
            value=artifact_set_euid,
        )
        if receipt is None:
            raise DeweyConflictError(
                f"Registered artifact set is missing its registration receipt: {artifact_set_euid}"
            )
        payload = dict(receipt.json_addl or {})
        missing = [
            field
            for field in ("artifact_set_kind", "manifest_sha256", "source_service")
            if not str(payload.get(field) or "").strip()
        ]
        if missing:
            raise DeweyConflictError(
                "Registered artifact set receipt is not QEO-compatible; missing "
                + ", ".join(missing)
            )
        return {field: payload.get(field) for field in _QEO_RECEIPT_FIELDS if field in payload}
