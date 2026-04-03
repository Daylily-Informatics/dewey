"""External object workflows for Dewey service."""

from __future__ import annotations

from typing import Any

from dewey_service.services.base import DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    utc_now_iso,
)


class ExternalObjectServiceMixin:
    def _find_or_create_external_object(
        self,
        session,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
    ):
        identity_key = f"{external_system}:{external_object_type}:{external_object_id}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            field="external_identity_key",
            value=identity_key,
        )
        if existing is not None:
            return existing
        return self.backend.create_instance(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            name=identity_key,
            json_addl={
                "external_system": external_system,
                "external_object_type": external_object_type,
                "external_object_id": external_object_id,
                "external_uri": external_uri,
                "metadata": {},
                "external_identity_key": identity_key,
                "created_at": utc_now_iso(),
            },
        )

    def _ensure_external_object_relation(
        self,
        session,
        *,
        artifact_instance,
        external_object,
        relation_type: str,
    ) -> None:
        relation_identity = (
            f"artifact:{artifact_instance.euid}:{external_object.euid}:{relation_type}"
        )
        existing = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
            field="relation_identity_key",
            value=relation_identity,
        )
        if existing is None:
            existing = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                name=relation_identity,
                json_addl={
                    "target_type": "artifact",
                    "target_euid": artifact_instance.euid,
                    "external_object_euid": external_object.euid,
                    "relation_type": relation_type,
                    "metadata": {},
                    "relation_identity_key": relation_identity,
                    "created_at": utc_now_iso(),
                },
            )
        self.backend.create_lineage(
            session,
            parent=artifact_instance,
            child=existing,
            relationship_type="has_external_relation",
        )
        self.backend.create_lineage(
            session,
            parent=external_object,
            child=existing,
            relationship_type="is_external_relation_for",
        )

    def _find_artifact_by_external_identity(
        self,
        session,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
    ):
        external = self.backend.find_by_json_field(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            field="external_identity_key",
            value=f"{external_system}:{external_object_type}:{external_object_id}",
        )
        if external is None:
            return None
        relations = self.backend.list_children(
            session,
            parent=external,
            relationship_type="is_external_relation_for",
        )
        for relation in relations:
            parents = self.backend.list_parents(
                session,
                child=relation,
                relationship_type="has_external_relation",
            )
            if parents:
                return parents[0]
        return None

    def create_external_object(
        self,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "external_system": str(external_system or "").strip().lower(),
            "external_object_type": str(external_object_type or "").strip().lower(),
            "external_object_id": str(external_object_id or "").strip(),
            "external_uri": str(external_uri or "").strip() or None,
            "metadata": dict(metadata or {}),
        }
        if not payload["external_system"]:
            raise ValueError("external_system is required")
        if not payload["external_object_type"]:
            raise ValueError("external_object_type is required")
        if not payload["external_object_id"]:
            raise ValueError("external_object_id is required")

        fingerprint = self._fingerprint(payload)
        identity_key = (
            f"{payload['external_system']}:"
            f"{payload['external_object_type']}:"
            f"{payload['external_object_id']}"
        )

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="external_object.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            existing = self.backend.find_by_json_field(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                field="external_identity_key",
                value=identity_key,
            )
            if existing is not None:
                body = self._external_object_response(existing)
                self._store_idempotency(
                    session,
                    operation="external_object.create",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body

            created = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                name=identity_key,
                json_addl={
                    **payload,
                    "external_identity_key": identity_key,
                    "created_at": utc_now_iso(),
                },
            )
            body = self._external_object_response(created)
            self._store_idempotency(
                session,
                operation="external_object.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def attach_external_object_relation(
        self,
        *,
        target_type: str,
        target_euid: str,
        external_object_euid: str,
        relation_type: str,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")

        payload = {
            "target_type": clean_target_type,
            "target_euid": str(target_euid or "").strip(),
            "external_object_euid": str(external_object_euid or "").strip(),
            "relation_type": str(relation_type or "").strip() or "linked",
            "metadata": dict(metadata or {}),
        }
        if not payload["target_euid"]:
            raise ValueError("target_euid is required")
        if not payload["external_object_euid"]:
            raise ValueError("external_object_euid is required")

        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="external_object_relation.attach",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            if clean_target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=payload["target_euid"],
                )
            else:
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=payload["target_euid"],
                )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {payload['target_euid']}")

            external_object = self.backend.find_by_euid(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                euid=payload["external_object_euid"],
            )
            if external_object is None:
                raise DeweyNotFoundError(
                    f"External object not found: {payload['external_object_euid']}"
                )

            relation_identity = (
                f"{payload['target_type']}:{payload['target_euid']}:"
                f"{payload['external_object_euid']}:{payload['relation_type']}"
            )
            existing = self.backend.find_by_json_field(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                field="relation_identity_key",
                value=relation_identity,
            )
            if existing is not None:
                body = self._external_object_relation_response(existing)
                self._store_idempotency(
                    session,
                    operation="external_object_relation.attach",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=200,
                    response=body,
                )
                return 200, body

            relation = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                name=relation_identity,
                json_addl={
                    **payload,
                    "relation_identity_key": relation_identity,
                    "created_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=target,
                child=relation,
                relationship_type="has_external_relation",
            )
            self.backend.create_lineage(
                session,
                parent=external_object,
                child=relation,
                relationship_type="is_external_relation_for",
            )

            body = self._external_object_relation_response(relation)
            self._store_idempotency(
                session,
                operation="external_object_relation.attach",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def list_external_object_relations(
        self,
        *,
        target_type: str,
        target_euid: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_target_type = str(target_type or "").strip().lower()
        if clean_target_type not in {"artifact", "artifact_set"}:
            raise ValueError("target_type must be artifact or artifact_set")

        with self.backend.session_scope(commit=False) as session:
            if clean_target_type == "artifact":
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=str(target_euid or "").strip(),
                )
            else:
                target = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_SET_TEMPLATE,
                    euid=str(target_euid or "").strip(),
                )
            if target is None:
                raise DeweyNotFoundError(f"Target not found: {target_euid}")

            rows = self.backend.list_children(
                session,
                parent=target,
                relationship_type="has_external_relation",
            )
            return [self._external_object_relation_response(row) for row in rows[:limit]]
