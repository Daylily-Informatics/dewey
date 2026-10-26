"""Atomic TapDB authority for strict Labcore sequencing-run ownership."""

from __future__ import annotations

import hashlib

from dewey_service.integrations.tapdb_external_references import attach_external_relation
from dewey_service.labcore_owner_command import LabcoreSequencingRunRegistrationCommandV2
from dewey_service.labcore_owner_contracts import LabcoreSequencingRunOwnerContractV1
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

_OPERATION = "labcore_owner.sequencing_run.register/v2"
_ARTIFACT_TYPES = frozenset({"sequencing_run"})


class LabcoreOwnerServiceMixin:
    """Persist a globally unique Labcore run owner/relation/receipt transaction."""

    @staticmethod
    def _expected_files(request: LabcoreSequencingRunOwnerContractV1) -> list[dict[str, object]]:
        return [item.model_dump(mode="json") for item in request.expected_files]

    def _assert_target_authority(
        self, artifact, command: LabcoreSequencingRunRegistrationCommandV2
    ) -> None:
        request = command.owner_request
        payload = normalize_instance_payload(artifact)
        metadata = payload.get("metadata")
        owner = metadata.get("labcore_owner") if isinstance(metadata, dict) else None
        required = {
            "tenant_euid": request.tenant_euid,
            "test_euid": command.test_euid,
            "processing_site_euid": request.processing_site_euid,
            "platform": request.platform,
            "dataset_root_uri": request.dataset_root_uri,
            "dataset_revision": request.dataset_revision,
            "inventory_sha256": request.inventory_sha256,
            "labcore_binding_receipt_id": request.labcore_binding_receipt_id,
            "labcore_binding_receipt_sha256": request.labcore_binding_receipt_sha256,
            "labcore_sequencing_run_euid": request.labcore_sequencing_run_euid,
        }
        valid = (
            str(payload.get("artifact_type") or "") in _ARTIFACT_TYPES
            and str(payload.get("storage_kind") or "") == "prefix"
            and str(payload.get("storage_backend") or "") == "s3"
            and str(payload.get("storage_uri") or "") == request.dataset_root_uri
            and str(payload.get("producer_system") or "") == "labcore"
            and str(payload.get("producer_object_euid") or "")
            == request.labcore_sequencing_run_euid
            and isinstance(owner, dict)
            and all(owner.get(field) == value for field, value in required.items())
            and owner.get("expected_files") == self._expected_files(request)
        )
        if not valid:
            raise DeweyConflictError("Target artifact lacks immutable Labcore owner evidence")

    @staticmethod
    def _assert_matching_owner(
        instance, command: LabcoreSequencingRunRegistrationCommandV2
    ) -> None:
        request = command.owner_request
        payload = normalize_instance_payload(instance)
        if (
            payload.get("labcore_owner_tenant_euid") != request.tenant_euid
            or payload.get("labcore_owner_command_sha256") != command.command_sha256
        ):
            raise DeweyConflictError("Labcore run already has conflicting global authority")

    def register_labcore_sequencing_run_owner(
        self,
        *,
        request_body: LabcoreSequencingRunRegistrationCommandV2,
        principal_id: str,
    ) -> tuple[int, dict[str, str]]:
        """Register exactly one TestEUID-bound owner relation for a global run."""

        command = request_body
        request = command.owner_request
        command_payload = command.model_dump(mode="json")
        if not principal_id or not principal_id.strip():
            raise ValueError("Authenticated principal ID is required")
        object_identity = f"labcore:sequencing_run:{request.labcore_sequencing_run_euid}"
        identity_key = (
            "labcore-sequencing-run:" + hashlib.sha256(object_identity.encode("utf-8")).hexdigest()
        )
        with self.backend.session_scope(commit=True) as session:
            external, created = self.backend.claim_global_instance(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                identity_key=identity_key,
                name=object_identity,
                command_evidence={
                    "command_sha256": command.command_sha256,
                    "tenant_euid": request.tenant_euid,
                    "principal_id": principal_id,
                },
                json_addl={
                    "external_system": request.external_system,
                    "external_object_type": request.external_object_type,
                    "external_object_id": request.external_object_id,
                    "external_uri": None,
                    "metadata": {},
                    "external_identity_key": object_identity,
                    "labcore_owner_tenant_euid": request.tenant_euid,
                    "labcore_owner_request_sha256": request.request_sha256,
                    "labcore_owner_command_sha256": command.command_sha256,
                    "labcore_owner_command": command_payload,
                    "principal_id": principal_id,
                    "created_at": utc_now_iso(),
                },
            )
            if external.is_deleted:
                raise DeweyConflictError("Deleted Labcore identity remains reserved")
            self._assert_matching_owner(external, command)
            if not created:
                replay = self._idempotency_replay(
                    session,
                    operation=_OPERATION,
                    idempotency_key=command.command_sha256,
                    fingerprint=command.command_sha256,
                )
                if replay is None:
                    raise RuntimeError("Labcore claim is missing its committed receipt")
                return 200, {str(key): str(value) for key, value in replay.response.items()}

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=request.target_euid,
                for_update=True,
            )
            if artifact is None:
                raise DeweyNotFoundError("Target artifact not found")
            self._assert_target_authority(artifact, command)

            relation_identity = (
                f"artifact:{request.target_euid}:{external.euid}:{request.relation_type}"
            )
            relation = self.backend.create_instance(
                session,
                template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,
                name=relation_identity,
                json_addl={
                    "target_type": request.target_type,
                    "relation_type": request.relation_type,
                    "metadata": {},
                    "relation_identity_key": relation_identity,
                    "labcore_owner_tenant_euid": request.tenant_euid,
                    "labcore_owner_command_sha256": command.command_sha256,
                    "principal_id": principal_id,
                    "created_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session, parent=artifact, child=relation, relationship_type="has_external_relation"
            )
            self.backend.create_lineage(
                session,
                parent=external,
                child=relation,
                relationship_type="is_external_relation_for",
            )
            attach_external_relation(session, relation)
            receipt = self.backend.create_instance(
                session,
                template_code=REGISTRATION_RECEIPT_TEMPLATE,
                name=f"labcore_owner_registration:{request.labcore_sequencing_run_euid}:{command.command_sha256}",
                json_addl={
                    "registration_kind": "labcore_sequencing_run_owner/v2",
                    "principal_id": principal_id,
                    "labcore_owner_tenant_euid": request.tenant_euid,
                    "labcore_owner_request_sha256": request.request_sha256,
                    "labcore_owner_command_sha256": command.command_sha256,
                    "created_at": utc_now_iso(),
                },
            )
            for parent in (artifact, external, relation):
                self.backend.create_lineage(
                    session,
                    parent=parent,
                    child=receipt,
                    relationship_type="has_registration_receipt",
                )
            body = {
                "registration_receipt_euid": receipt.euid,
                "request_sha256": request.request_sha256,
                "command_sha256": command.command_sha256,
                "tenant_euid": request.tenant_euid,
                "external_object_euid": external.euid,
                "external_object_relation_euid": relation.euid,
            }
            self.backend.update_instance_json(session, receipt, {"response": body})
            self._store_idempotency(
                session,
                operation=_OPERATION,
                idempotency_key=command.command_sha256,
                fingerprint=command.command_sha256,
                status_code=201,
                response=body,
            )
            return 201, body
