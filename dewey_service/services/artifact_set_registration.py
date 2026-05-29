"""QEO/KEO artifact-set registration workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from dewey_service.registration_contracts import (
    AnalysisArtifactSetRegistrationRequest,
    FileArtifact,
    MultiQCArtifactSetRegistrationRequest,
    ReceiptArtifact,
    RegistrationReceipt,
    canonical_json,
    canonical_sha256,
    computed_registration_idempotency_key,
    deterministic_request_id,
    manifest_sha256_for_request,
)
from dewey_service.services.artifacts import ARTIFACT_HIERARCHY_RELATIONSHIP
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.storage import StorageObject, StorageObjectNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    SERVICE_VERSION,
    normalize_instance_payload,
    utc_now_iso,
)

ANALYSIS_REGISTER_OPERATION = "artifact_set.analysis.register"
MULTIQC_REGISTER_OPERATION = "artifact_set.multiqc.register"
ANALYSIS_EVENT_TYPE = "lsmc.dewey.artifact_set.registered.v1"
MULTIQC_EVENT_TYPE = "lsmc.dewey.multiqc_artifact_set.registered.v1"


@dataclass(frozen=True)
class _PreparedArtifact:
    artifact: FileArtifact
    storage_object: StorageObject | None
    bucket: str
    key: str
    storage_kind: str
    node_kind: str


class ArtifactSetRegistrationServiceMixin:
    def register_analysis_artifact_set(
        self,
        request: AnalysisArtifactSetRegistrationRequest | dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        body = self._coerce_analysis_registration(request)
        computed_key = self._registration_idempotency_key(
            request=body,
            supplied_idempotency_key=idempotency_key,
        )
        self._validate_manifest_sha256(body)
        fingerprint = canonical_sha256(body)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation=ANALYSIS_REGISTER_OPERATION,
                idempotency_key=computed_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            prepared = self._preflight_file_artifacts(body.artifacts)
            now_iso = utc_now_iso()
            artifact_set = self.backend.create_instance(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                name=f"analysis_artifact_set:{body.analysis_euid}",
                json_addl=self._analysis_artifact_set_payload(body, created_at=now_iso),
            )
            self._link_optional_parent_artifact_sets(
                session,
                artifact_set=artifact_set,
                parent_analysis_artifact_set_euid=body.parent_analysis_artifact_set_euid,
                rerun_of=body.rerun_of,
            )
            registered, skipped = self._register_artifacts_for_set(
                session,
                artifact_set=artifact_set,
                prepared=prepared,
                registration_kind="analysis",
                manifest_sha256=body.manifest_sha256,
                analysis_euid=body.analysis_euid,
                created_at=now_iso,
            )
            receipt = self._build_registration_receipt(
                idempotency_key=computed_key,
                artifact_set_euid=artifact_set.euid,
                artifact_set_kind="analysis_artifact_set",
                report_kind=None,
                manifest_sha256=body.manifest_sha256,
                registered_artifacts=registered,
                skipped_existing=skipped,
                registered_at=now_iso,
                local_only=body.local_only,
                parser_hint=body.parser_family_hint,
            )
            receipt_instance = self._persist_registration_receipt(
                session,
                receipt=receipt,
                registration_kind="analysis",
                manifest_sha256=body.manifest_sha256,
            )
            event = self._build_outbox_event(
                event_type=ANALYSIS_EVENT_TYPE,
                occurred_at=now_iso,
                payload=self._event_payload(
                    artifact_set_euid=artifact_set.euid,
                    analysis_euid=body.analysis_euid,
                    manifest_sha256=body.manifest_sha256,
                    parser_family_hint=body.parser_family_hint,
                ),
                correlation_id=receipt.request_id,
                causation_id=computed_key,
            )
            self._persist_outbox_event(
                session,
                event=event,
                idempotency_key=computed_key,
                receipt_euid=receipt_instance.euid,
                local_only=body.local_only,
            )
            response = self._deterministic_receipt_dict(receipt)
            self._store_idempotency(
                session,
                operation=ANALYSIS_REGISTER_OPERATION,
                idempotency_key=computed_key,
                fingerprint=fingerprint,
                status_code=201,
                response=response,
            )
            return 201, response

    def register_multiqc_artifact_set(
        self,
        request: MultiQCArtifactSetRegistrationRequest | dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        body = self._coerce_multiqc_registration(request)
        computed_key = self._registration_idempotency_key(
            request=body,
            supplied_idempotency_key=idempotency_key,
        )
        self._validate_manifest_sha256(body)
        fingerprint = canonical_sha256(body)
        artifacts = self._multiqc_artifacts(body)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation=MULTIQC_REGISTER_OPERATION,
                idempotency_key=computed_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            prepared = self._preflight_file_artifacts(artifacts)
            now_iso = utc_now_iso()
            artifact_set = self.backend.create_instance(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                name=f"multiqc_artifact_set:{body.analysis_euid}:{body.report_kind}",
                json_addl=self._multiqc_artifact_set_payload(body, created_at=now_iso),
            )
            registered, skipped = self._register_artifacts_for_set(
                session,
                artifact_set=artifact_set,
                prepared=prepared,
                registration_kind="multiqc",
                manifest_sha256=body.manifest_sha256,
                analysis_euid=body.analysis_euid,
                created_at=now_iso,
            )
            receipt = self._build_registration_receipt(
                idempotency_key=computed_key,
                artifact_set_euid=artifact_set.euid,
                artifact_set_kind="multiqc_artifact_set",
                report_kind=body.report_kind,
                manifest_sha256=body.manifest_sha256,
                registered_artifacts=registered,
                skipped_existing=skipped,
                registered_at=now_iso,
                local_only=body.local_only,
                parser_hint=body.parser_family_hint or body.report_kind,
            )
            receipt_instance = self._persist_registration_receipt(
                session,
                receipt=receipt,
                registration_kind="multiqc",
                manifest_sha256=body.manifest_sha256,
            )
            event = self._build_outbox_event(
                event_type=MULTIQC_EVENT_TYPE,
                occurred_at=now_iso,
                payload=self._event_payload(
                    artifact_set_euid=artifact_set.euid,
                    analysis_euid=body.analysis_euid,
                    manifest_sha256=body.manifest_sha256,
                    parser_family_hint=body.parser_family_hint or body.report_kind,
                ),
                correlation_id=receipt.request_id,
                causation_id=computed_key,
            )
            self._persist_outbox_event(
                session,
                event=event,
                idempotency_key=computed_key,
                receipt_euid=receipt_instance.euid,
                local_only=body.local_only,
            )
            response = self._deterministic_receipt_dict(receipt)
            self._store_idempotency(
                session,
                operation=MULTIQC_REGISTER_OPERATION,
                idempotency_key=computed_key,
                fingerprint=fingerprint,
                status_code=201,
                response=response,
            )
            return 201, response

    def list_outbox_events(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=OUTBOX_EVENT_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            return [normalize_instance_payload(row) for row in rows]

    def list_registration_receipts(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=REGISTRATION_RECEIPT_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            return [normalize_instance_payload(row) for row in rows]

    @staticmethod
    def _coerce_analysis_registration(
        request: AnalysisArtifactSetRegistrationRequest | dict[str, Any],
    ) -> AnalysisArtifactSetRegistrationRequest:
        if isinstance(request, AnalysisArtifactSetRegistrationRequest):
            return request
        return AnalysisArtifactSetRegistrationRequest.model_validate(request)

    @staticmethod
    def _coerce_multiqc_registration(
        request: MultiQCArtifactSetRegistrationRequest | dict[str, Any],
    ) -> MultiQCArtifactSetRegistrationRequest:
        if isinstance(request, MultiQCArtifactSetRegistrationRequest):
            return request
        return MultiQCArtifactSetRegistrationRequest.model_validate(request)

    @staticmethod
    def _registration_idempotency_key(
        *,
        request: AnalysisArtifactSetRegistrationRequest | MultiQCArtifactSetRegistrationRequest,
        supplied_idempotency_key: str | None,
    ) -> str:
        computed_key = computed_registration_idempotency_key(request)
        supplied = str(supplied_idempotency_key or "").strip()
        if supplied and supplied != computed_key:
            raise DeweyConflictError(
                "Idempotency-Key does not match deterministic registration request hash"
            )
        return computed_key

    @staticmethod
    def _validate_manifest_sha256(
        request: AnalysisArtifactSetRegistrationRequest | MultiQCArtifactSetRegistrationRequest,
    ) -> None:
        expected = manifest_sha256_for_request(request)
        if request.manifest_sha256 != expected:
            raise ValueError("manifest_sha256 does not match canonical registration manifest")

    def _preflight_file_artifacts(
        self,
        artifacts: list[FileArtifact],
    ) -> list[_PreparedArtifact]:
        prepared: list[_PreparedArtifact] = []
        storage = self._require_storage()
        for artifact in artifacts:
            bucket, key = self._parse_s3_uri(artifact.storage_uri)
            is_directory = artifact.artifact_role == "directory"
            uri_is_prefix = artifact.storage_uri.endswith("/")
            if is_directory:
                self._validate_directory_artifact(artifact)
                prepared.append(
                    _PreparedArtifact(
                        artifact=artifact,
                        storage_object=None,
                        bucket=bucket,
                        key=key.rstrip("/") + "/",
                        storage_kind="prefix",
                        node_kind="directory",
                    )
                )
                continue
            if uri_is_prefix:
                raise ValueError(
                    "directory-shaped storage_uri requires artifact_role=directory"
                )
            try:
                storage_object = storage.head_object(bucket=bucket, key=key)
            except StorageObjectNotFoundError as exc:
                label = "Required artifact missing" if artifact.required else "Artifact missing"
                raise DeweyNotFoundError(
                    f"{label}: {artifact.logical_name} ({artifact.storage_uri})"
                ) from exc
            self._validate_storage_metadata(artifact=artifact, storage_object=storage_object)
            prepared.append(
                _PreparedArtifact(
                    artifact=artifact,
                    storage_object=storage_object,
                    bucket=bucket,
                    key=key,
                    storage_kind="object",
                    node_kind="file",
                )
            )
        return prepared

    @staticmethod
    def _validate_directory_artifact(artifact: FileArtifact) -> None:
        if not artifact.storage_uri.endswith("/"):
            raise ValueError("directory artifacts require storage_uri ending in '/'")
        if artifact.mime_type != "inode/directory":
            raise ValueError("directory artifacts require mime_type inode/directory")
        if artifact.size_bytes != 0:
            raise ValueError("directory artifacts require size_bytes=0")

    @staticmethod
    def _validate_storage_metadata(
        *,
        artifact: FileArtifact,
        storage_object: StorageObject,
    ) -> None:
        if storage_object.size is not None and int(storage_object.size) != artifact.size_bytes:
            raise ValueError(
                f"size_bytes mismatch for {artifact.logical_name}: "
                f"manifest={artifact.size_bytes} storage={storage_object.size}"
            )
        reported_sha256 = ArtifactSetRegistrationServiceMixin._reported_storage_sha256(
            storage_object
        )
        if reported_sha256 is not None and reported_sha256 != artifact.sha256:
            raise ValueError(
                f"sha256 mismatch for {artifact.logical_name}: "
                f"manifest={artifact.sha256} storage={reported_sha256}"
            )

    @staticmethod
    def _reported_storage_sha256(storage_object: StorageObject) -> str | None:
        for attr_name in ("sha256", "checksum_sha256"):
            value = str(getattr(storage_object, attr_name, "") or "").strip().lower()
            if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
                return value
        return None

    def _register_artifacts_for_set(
        self,
        session,
        *,
        artifact_set,
        prepared: list[_PreparedArtifact],
        registration_kind: str,
        manifest_sha256: str,
        analysis_euid: str,
        created_at: str,
    ) -> tuple[list[ReceiptArtifact], list[ReceiptArtifact]]:
        registered: list[ReceiptArtifact] = []
        skipped: list[ReceiptArtifact] = []
        for item in prepared:
            payload = self._registration_artifact_payload(
                prepared=item,
                registration_kind=registration_kind,
                manifest_sha256=manifest_sha256,
                analysis_euid=analysis_euid,
                created_at=created_at,
            )
            status_code, artifact_response = self._upsert_registration_artifact(
                session,
                prepared=item,
                payload=payload,
                created_at=created_at,
            )
            artifact_instance = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=artifact_response["artifact_euid"],
            )
            if artifact_instance is None:
                raise DeweyNotFoundError(
                    f"Artifact not found after registration: {artifact_response['artifact_euid']}"
                )
            self.backend.create_lineage(
                session,
                parent=artifact_set,
                child=artifact_instance,
                relationship_type="artifact_set_member",
            )
            for parent_euid in item.artifact.parent_artifact_euids:
                parent_artifact = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=parent_euid,
                )
                if parent_artifact is None:
                    raise DeweyNotFoundError(f"Parent artifact not found: {parent_euid}")
                self.backend.create_lineage(
                    session,
                    parent=parent_artifact,
                    child=artifact_instance,
                    relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
                )
            receipt_artifact = self._receipt_artifact(
                artifact_euid=artifact_response["artifact_euid"],
                artifact=item.artifact,
            )
            if status_code == 201:
                registered.append(receipt_artifact)
            else:
                skipped.append(receipt_artifact)
        return self._sort_receipt_artifacts(registered), self._sort_receipt_artifacts(skipped)

    def _registration_artifact_payload(
        self,
        *,
        prepared: _PreparedArtifact,
        registration_kind: str,
        manifest_sha256: str,
        analysis_euid: str,
        created_at: str,
    ) -> dict[str, Any]:
        artifact = prepared.artifact
        metadata = {
            "registration_kind": registration_kind,
            "analysis_euid": analysis_euid,
            "manifest_sha256": manifest_sha256,
            "logical_name": artifact.logical_name,
            "relative_path": artifact.relative_path,
            "artifact_role": artifact.artifact_role,
            "parser_hint": artifact.parser_hint,
            "required": artifact.required,
            "produced_by": artifact.produced_by,
            "parent_artifact_euids": list(artifact.parent_artifact_euids),
        }
        payload = self._artifact_payload(
            artifact_type="folder"
            if prepared.storage_kind == "prefix"
            else artifact.artifact_role,
            storage_backend="s3",
            bucket=prepared.bucket,
            key=prepared.key,
            version_id=prepared.storage_object.version_id if prepared.storage_object else None,
            size=artifact.size_bytes,
            checksums={"sha256": artifact.sha256},
            content_type=artifact.mime_type,
            original_filename=artifact.logical_name,
            producer_system=artifact.produced_by,
            producer_object_euid=analysis_euid,
            storage_class=prepared.storage_object.storage_class
            if prepared.storage_object
            else None,
            availability_status="available",
            metadata=metadata,
            source_uri=artifact.storage_uri,
            import_mode="register",
            storage_status="registered"
            if prepared.storage_kind == "prefix"
            else "verified",
            storage_verified_at=None if prepared.storage_kind == "prefix" else created_at,
            storage_kind=prepared.storage_kind,
            node_kind=prepared.node_kind,
            is_terminal=prepared.storage_kind != "prefix",
            artifact_identity_key=self._registration_artifact_identity_key(artifact),
        )
        payload["artifact_role"] = artifact.artifact_role
        return payload

    @staticmethod
    def _registration_artifact_identity_key(artifact: FileArtifact) -> str:
        return ":".join(
            [
                "dewey.registration",
                artifact.storage_uri,
                artifact.sha256,
                str(artifact.size_bytes),
                artifact.artifact_role,
            ]
        )

    def _upsert_registration_artifact(
        self,
        session,
        *,
        prepared: _PreparedArtifact,
        payload: dict[str, Any],
        created_at: str,
    ) -> tuple[int, dict[str, Any]]:
        existing_by_uri = self.backend.find_by_json_field(
            session,
            template_code=ARTIFACT_TEMPLATE,
            field="storage_uri",
            value=prepared.artifact.storage_uri,
        )
        if existing_by_uri is not None:
            self._assert_existing_artifact_matches(
                existing_by_uri,
                artifact=prepared.artifact,
            )
            return 200, self._artifact_response(existing_by_uri)
        return self._upsert_artifact_record(
            session,
            payload=payload,
            created_at=created_at,
            refresh_existing=False,
        )

    @staticmethod
    def _assert_existing_artifact_matches(instance, *, artifact: FileArtifact) -> None:
        payload = normalize_instance_payload(instance)
        metadata = dict(payload.get("metadata") or {})
        existing_sha256 = str((payload.get("checksums") or {}).get("sha256") or "")
        exact = (
            str(payload.get("storage_uri") or "") == artifact.storage_uri
            and existing_sha256 == artifact.sha256
            and int(payload.get("size") or 0) == artifact.size_bytes
            and str(payload.get("artifact_role") or metadata.get("artifact_role") or "")
            == artifact.artifact_role
        )
        if not exact:
            raise DeweyConflictError(
                "Existing artifact record conflicts with immutable registration manifest"
            )

    @staticmethod
    def _receipt_artifact(*, artifact_euid: str, artifact: FileArtifact) -> ReceiptArtifact:
        return ReceiptArtifact(
            artifact_euid=artifact_euid,
            logical_name=artifact.logical_name,
            relative_path=artifact.relative_path,
            storage_uri=artifact.storage_uri,
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
            artifact_role=artifact.artifact_role,
            parser_hint=artifact.parser_hint,
            required=artifact.required,
        )

    @staticmethod
    def _sort_receipt_artifacts(items: list[ReceiptArtifact]) -> list[ReceiptArtifact]:
        return sorted(
            items,
            key=lambda item: (item.relative_path, item.logical_name, item.artifact_euid),
        )

    @staticmethod
    def _build_registration_receipt(
        *,
        idempotency_key: str,
        artifact_set_euid: str,
        artifact_set_kind: str,
        report_kind: str | None,
        manifest_sha256: str,
        registered_artifacts: list[ReceiptArtifact],
        skipped_existing: list[ReceiptArtifact],
        registered_at: str,
        local_only: bool,
        parser_hint: str | None,
    ) -> RegistrationReceipt:
        return RegistrationReceipt(
            request_id=deterministic_request_id(idempotency_key),
            idempotency_key=idempotency_key,
            artifact_set_euid=artifact_set_euid,
            artifact_set_kind=artifact_set_kind,
            report_kind=report_kind,
            manifest_sha256=manifest_sha256,
            registered_artifacts=registered_artifacts,
            skipped_existing=skipped_existing,
            failed=[],
            registered_at=registered_at,
            status="local_only" if local_only else "registered",
            source_service="dewey",
            source_version=SERVICE_VERSION,
            parser_hint=parser_hint,
        )

    def _persist_registration_receipt(
        self,
        session,
        *,
        receipt: RegistrationReceipt,
        registration_kind: str,
        manifest_sha256: str,
    ):
        payload = self._deterministic_receipt_dict(receipt)
        existing = self.backend.find_by_json_field(
            session,
            template_code=REGISTRATION_RECEIPT_TEMPLATE,
            field="idempotency_key",
            value=receipt.idempotency_key,
        )
        if existing is not None:
            return existing
        return self.backend.create_instance(
            session,
            template_code=REGISTRATION_RECEIPT_TEMPLATE,
            name=f"registration_receipt:{receipt.request_id}",
            json_addl={
                **payload,
                "registration_kind": registration_kind,
                "manifest_sha256": manifest_sha256,
            },
        )

    @staticmethod
    def _deterministic_receipt_dict(receipt: RegistrationReceipt) -> dict[str, Any]:
        payload = json.loads(canonical_json(receipt))
        if not isinstance(payload, dict):
            raise ValueError("registration receipt did not serialize to an object")
        return payload

    @staticmethod
    def _event_payload(
        *,
        artifact_set_euid: str,
        analysis_euid: str,
        manifest_sha256: str,
        parser_family_hint: str | None,
    ) -> dict[str, Any]:
        payload = {
            "artifact_set_euid": artifact_set_euid,
            "analysis_euid": analysis_euid,
            "manifest_sha256": manifest_sha256,
        }
        if parser_family_hint:
            payload["parser_family_hint"] = parser_family_hint
        return payload

    @staticmethod
    def _analysis_artifact_set_payload(
        request: AnalysisArtifactSetRegistrationRequest,
        *,
        created_at: str,
    ) -> dict[str, Any]:
        metadata = request.model_dump(
            mode="json",
            exclude={"artifacts", "manifest_sha256"},
        )
        metadata["manifest_sha256"] = request.manifest_sha256
        metadata["artifact_manifest"] = [
            artifact.model_dump(mode="json") for artifact in request.artifacts
        ]
        return {
            "artifact_set_type": "analysis_artifact_set",
            "label": f"{request.pipeline_name}:{request.analysis_euid}",
            "description": None,
            "metadata": metadata,
            "registration_kind": "analysis",
            "analysis_euid": request.analysis_euid,
            "manifest_sha256": request.manifest_sha256,
            "status": request.status,
            "created_at": created_at,
        }

    @staticmethod
    def _multiqc_artifact_set_payload(
        request: MultiQCArtifactSetRegistrationRequest,
        *,
        created_at: str,
    ) -> dict[str, Any]:
        metadata = request.model_dump(
            mode="json",
            exclude={
                "html_artifact",
                "data_dir_artifact",
                "key_files",
                "parser_relevant_files",
                "manifest_sha256",
            },
        )
        metadata["manifest_sha256"] = request.manifest_sha256
        metadata["html_artifact"] = request.html_artifact.model_dump(mode="json")
        metadata["data_dir_artifact"] = request.data_dir_artifact.model_dump(mode="json")
        metadata["key_files"] = [
            artifact.model_dump(mode="json") for artifact in request.key_files
        ]
        metadata["parser_relevant_files"] = [
            artifact.model_dump(mode="json") for artifact in request.parser_relevant_files
        ]
        return {
            "artifact_set_type": "multiqc_artifact_set",
            "label": f"{request.report_kind}:{request.analysis_euid}",
            "description": None,
            "metadata": metadata,
            "registration_kind": "multiqc",
            "analysis_euid": request.analysis_euid,
            "manifest_sha256": request.manifest_sha256,
            "created_at": created_at,
        }

    @staticmethod
    def _multiqc_artifacts(
        request: MultiQCArtifactSetRegistrationRequest,
    ) -> list[FileArtifact]:
        rows = [
            request.html_artifact,
            request.data_dir_artifact,
            *request.key_files,
            *request.parser_relevant_files,
        ]
        seen: set[tuple[str, str, str]] = set()
        deduped: list[FileArtifact] = []
        for artifact in rows:
            key = (artifact.storage_uri, artifact.logical_name, artifact.artifact_role)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(artifact)
        return deduped

    def _link_optional_parent_artifact_sets(
        self,
        session,
        *,
        artifact_set,
        parent_analysis_artifact_set_euid: str | None,
        rerun_of: str | None,
    ) -> None:
        for target_euid, relationship_type in [
            (parent_analysis_artifact_set_euid, "analysis_artifact_set_parent"),
            (rerun_of, "analysis_artifact_set_rerun_of"),
        ]:
            if not target_euid:
                continue
            parent = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_SET_TEMPLATE,
                euid=target_euid,
            )
            if parent is None:
                raise DeweyNotFoundError(f"Artifact set lineage target not found: {target_euid}")
            self.backend.create_lineage(
                session,
                parent=parent,
                child=artifact_set,
                relationship_type=relationship_type,
            )


__all__ = [
    "ANALYSIS_EVENT_TYPE",
    "MULTIQC_EVENT_TYPE",
    "ArtifactSetRegistrationServiceMixin",
]
