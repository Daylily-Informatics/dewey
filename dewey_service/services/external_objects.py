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


DEWEY_EXTERNAL_GRAPH_SOURCE_FIELD = "dewey.external_object_relation"


class ExternalObjectServiceMixin:
    @staticmethod
    def _copy_graph_field(
        ref: dict[str, Any],
        *,
        field: str,
        relation_payload: dict[str, Any],
        external_payload: dict[str, Any],
    ) -> None:
        relation_metadata = relation_payload.get("metadata")
        external_metadata = external_payload.get("metadata")
        candidates = []
        if isinstance(relation_metadata, dict):
            candidates.append(relation_metadata)
        if isinstance(external_metadata, dict):
            candidates.append(external_metadata)
        candidates.append(external_payload)
        for source in candidates:
            value = source.get(field)
            if value is not None and str(value).strip():
                ref[field] = value
                return

    @staticmethod
    def _is_dewey_external_graph_ref(ref: Any) -> bool:
        return (
            isinstance(ref, dict)
            and str(ref.get("source_field") or "") == DEWEY_EXTERNAL_GRAPH_SOURCE_FIELD
        )

    @staticmethod
    def _external_graph_ref_key(ref: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(ref.get("system") or "").strip().lower(),
            str(ref.get("root_euid") or "").strip(),
            str(ref.get("relationship_type") or "").strip(),
            str(ref.get("tenant_id") or "").strip(),
        )

    def _external_graph_ref_from_payloads(
        self,
        *,
        relation_payload: dict[str, Any],
        external_payload: dict[str, Any],
    ) -> dict[str, Any]:
        relation_euid = str(relation_payload.get("external_object_relation_euid") or "").strip()
        external_euid = str(relation_payload.get("external_object_euid") or "").strip()
        system = str(external_payload.get("external_system") or "").strip().lower()
        root_euid = str(external_payload.get("external_object_id") or "").strip()
        relationship_type = str(relation_payload.get("relation_type") or "").strip()
        if not system:
            raise ValueError(f"External object relation {relation_euid} is missing external_system")
        if not root_euid:
            raise ValueError(
                f"External object relation {relation_euid} is missing external_object_id"
            )
        if not relationship_type:
            raise ValueError(f"External object relation {relation_euid} is missing relation_type")

        ref: dict[str, Any] = {
            "system": system,
            "root_euid": root_euid,
            "target_euid": root_euid,
            "relationship_type": relationship_type,
            "source_field": DEWEY_EXTERNAL_GRAPH_SOURCE_FIELD,
            "label": f"{system}:{relationship_type}:{root_euid}",
            "external_object_euid": external_euid,
            "external_object_relation_euid": relation_euid,
        }
        object_type = external_payload.get("external_object_type")
        if object_type is not None and str(object_type).strip():
            ref["external_object_type"] = object_type
        external_uri = external_payload.get("external_uri")
        if external_uri is not None and str(external_uri).strip():
            ref["href"] = external_uri
        for field in (
            "tenant_id",
            "base_url",
            "graph_data_path",
            "object_detail_path_template",
            "auth_mode",
        ):
            self._copy_graph_field(
                ref,
                field=field,
                relation_payload=relation_payload,
                external_payload=external_payload,
            )
        return ref

    def _external_object_for_relation(self, session, relation_payload: dict[str, Any]):
        external_euid = str(relation_payload.get("external_object_euid") or "").strip()
        external = self.backend.find_by_euid(
            session,
            template_code=EXTERNAL_OBJECT_TEMPLATE,
            euid=external_euid,
        )
        if external is None:
            relation_euid = str(
                relation_payload.get("external_object_relation_euid") or ""
            ).strip()
            raise DeweyNotFoundError(
                f"External object not found for relation {relation_euid}: {external_euid}"
            )
        return external

    def _external_object_relation_response_with_external(
        self,
        session,
        relation,
    ) -> dict[str, Any]:
        body = self._external_object_relation_response(relation)
        external = self._external_object_for_relation(session, body)
        external_payload = self._external_object_response(external)
        graph_ref = self._external_graph_ref_from_payloads(
            relation_payload=body,
            external_payload=external_payload,
        )
        return {
            **body,
            "external_system": external_payload.get("external_system"),
            "external_object_type": external_payload.get("external_object_type"),
            "external_object_id": external_payload.get("external_object_id"),
            "external_uri": external_payload.get("external_uri"),
            "external_object": external_payload,
            "external_graph_ref": graph_ref,
        }

    def _sync_external_graph_refs_for_target(self, session, target) -> None:
        target_payload = dict(target.json_addl or {})
        properties = dict(target_payload.get("properties") or {})
        external_payload = dict(properties.get("external_payload") or {})
        raw_refs = external_payload.get("tapdb_graph", [])
        if raw_refs is None:
            raw_refs = []
        if not isinstance(raw_refs, list):
            raise ValueError("properties.external_payload.tapdb_graph must be a list")

        preserved_refs = [ref for ref in raw_refs if not self._is_dewey_external_graph_ref(ref)]
        relations = self.backend.list_children(
            session,
            parent=target,
            relationship_type="has_external_relation",
        )
        derived_refs: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for relation in relations:
            relation_payload = self._external_object_relation_response(relation)
            external = self._external_object_for_relation(session, relation_payload)
            ref = self._external_graph_ref_from_payloads(
                relation_payload=relation_payload,
                external_payload=self._external_object_response(external),
            )
            key = self._external_graph_ref_key(ref)
            if key in seen:
                continue
            seen.add(key)
            derived_refs.append(ref)

        next_external_payload = {
            **external_payload,
            "tapdb_graph": preserved_refs + derived_refs,
        }
        next_properties = {
            **properties,
            "external_payload": next_external_payload,
        }
        if target_payload.get("properties") == next_properties:
            return
        self.backend.update_instance_json(session, target, {"properties": next_properties})
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
        self._sync_external_graph_refs_for_target(session, artifact_instance)

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
                self.backend.create_lineage(
                    session,
                    parent=target,
                    child=existing,
                    relationship_type="has_external_relation",
                )
                self.backend.create_lineage(
                    session,
                    parent=external_object,
                    child=existing,
                    relationship_type="is_external_relation_for",
                )
                self._sync_external_graph_refs_for_target(session, target)
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
            self._sync_external_graph_refs_for_target(session, target)

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

        with self.backend.session_scope(commit=True) as session:
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

            self._sync_external_graph_refs_for_target(session, target)
            rows = self.backend.list_children(
                session,
                parent=target,
                relationship_type="has_external_relation",
            )
            return [
                self._external_object_relation_response_with_external(session, row)
                for row in rows[:limit]
            ]
