"""Artifact set workflows for Dewey service."""

from __future__ import annotations

from typing import Any

from dewey_service.services.base import DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)


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
        return self.get_artifact_set(artifact_set_euid)
