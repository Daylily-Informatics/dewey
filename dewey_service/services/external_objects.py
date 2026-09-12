"""External object workflows for Dewey service."""

from __future__ import annotations

from typing import Any
from dewey_service.registry_access import require_record

from dewey_service.integrations.tapdb_external_references import (
    attach_external_relation,
    build_external_target,
    lock_external_relation_source,
    resolve_relation_endpoints,
)
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

LABCORE_OWNER_EXTERNAL_SYSTEM = "labcore"
LABCORE_OWNER_EXTERNAL_OBJECT_TYPE = "sequencing_run"
LABCORE_OWNER_RELATION_TYPE = "labcore_sequencing_run"


class ExternalObjectServiceMixin:
    @staticmethod
    def _assert_generic_external_identity_available(
        *, external_system: object, external_object_type: object
    ) -> None:
        system = str(external_system or "").strip().lower()
        object_type = str(external_object_type or "").strip().lower()
        if (
            system == LABCORE_OWNER_EXTERNAL_SYSTEM
            and object_type == LABCORE_OWNER_EXTERNAL_OBJECT_TYPE
        ):
            raise DeweyConflictError(
                "Labcore sequencing-run ownership must use the v2 Labcore owner API"
            )

    def _assert_generic_relation_available(self, *, external_object, relation_type: object) -> None:
        if str(relation_type or "").strip().lower() == LABCORE_OWNER_RELATION_TYPE:
            raise DeweyConflictError(
                "Labcore sequencing-run ownership must use the v2 Labcore owner API"
            )
        payload = self._external_object_response(external_object)
        self._assert_generic_external_identity_available(
            external_system=payload.get("external_system"),
            external_object_type=payload.get("external_object_type"),
        )

    @staticmethod
    def _require_external_relation_pair(session, relation, source, external_object) -> None:
        endpoints = resolve_relation_endpoints(session, relation)
        if (
            endpoints.source.uid != source.uid
            or endpoints.external_object.uid != external_object.uid
        ):
            raise DeweyConflictError("External relation lookup disagrees with canonical lineage")

    def _external_object_relation_response_with_external(self, session, relation) -> dict[str, Any]:
        endpoints = resolve_relation_endpoints(session, relation)
        payload = normalize_instance_payload(relation)
        external_payload = self._external_object_response(endpoints.external_object)
        return {
            "external_object_relation_euid": relation.euid,
            "target_type": endpoints.source.type,
            "target_euid": endpoints.source.euid,
            "external_object_euid": endpoints.external_object.euid,
            "relation_type": payload.get("relation_type"),
            "metadata": dict(payload.get("metadata") or {}),
            "created_at": payload.get("created_at"),
            "external_system": external_payload["external_system"],
            "external_object_type": external_payload["external_object_type"],
            "external_object_id": external_payload["external_object_id"],
            "external_uri": external_payload["external_uri"],
            "external_object": external_payload,
        }

    def _find_or_create_external_object(
        self,
        session,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
    ):
        build_external_target(
            {
                "external_system": external_system,
                "external_object_type": external_object_type,
                "external_object_id": external_object_id,
            }
        )
        self._assert_generic_external_identity_available(
            external_system=external_system, external_object_type=external_object_type
        )
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
        artifact_instance = lock_external_relation_source(session, artifact_instance)
        require_record(self.backend, session, artifact_instance, "edit")
        self._assert_generic_relation_available(
            external_object=external_object, relation_type=relation_type
        )
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
        else:
            self._require_external_relation_pair(
                session, existing, artifact_instance, external_object
            )
        attach_external_relation(session, existing)

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
            endpoints = resolve_relation_endpoints(session, relation)
            if endpoints.external_object.uid != external.uid:
                raise ValueError("External identity lineage endpoint disagrees")
            return endpoints.source
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
        reference_target: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "external_system": str(external_system or "").strip().lower(),
            "external_object_type": str(external_object_type or "").strip().lower(),
            "external_object_id": str(external_object_id or "").strip(),
            "external_uri": str(external_uri or "").strip() or None,
            "metadata": dict(metadata or {}),
        }
        if reference_target is not None:
            payload["reference_target"] = reference_target
        if not payload["external_system"]:
            raise ValueError("external_system is required")
        if not payload["external_object_type"]:
            raise ValueError("external_object_type is required")
        if not payload["external_object_id"]:
            raise ValueError("external_object_id is required")
        requested_target = build_external_target(payload)

        self._assert_generic_external_identity_available(
            external_system=payload["external_system"],
            external_object_type=payload["external_object_type"],
        )
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
                if build_external_target(existing.json_addl) != requested_target:
                    raise DeweyConflictError("External identity has a different target contract")
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
            external_object = self.backend.find_by_euid(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                euid=payload["external_object_euid"],
            )
            if external_object is None:
                raise DeweyNotFoundError("External object not found")
            self._assert_generic_relation_available(
                external_object=external_object, relation_type=payload["relation_type"]
            )
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
            target = lock_external_relation_source(session, target)
            require_record(self.backend, session, target, "edit")
            replay = self._idempotency_replay(
                session,
                operation="external_object_relation.attach",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

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
                self._require_external_relation_pair(session, existing, target, external_object)
                attach_external_relation(session, existing)
                body = self._external_object_relation_response_with_external(session, existing)
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
            attach_external_relation(session, relation)

            body = self._external_object_relation_response_with_external(session, relation)
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
            return [
                self._external_object_relation_response_with_external(session, row)
                for row in rows[:limit]
            ]
