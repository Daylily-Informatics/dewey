"""Sequencer run and analysis-result registration workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dewey_service.artifact_ui import resolve_artifact_type
from dewey_service.sequencer_run_contracts import (
    AnalysisResultsRegistrationRequest,
    FileEvidence,
    OutboxEventEnvelope,
    RegistrationReceipt,
    SequencerRunRegistrationRequest,
    canonical_sha256,
    deterministic_idempotency_key,
    parse_pipeline_order_tsv,
)
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.storage import StorageObject, StorageObjectNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

RUN_REGISTRATION_EVENT_TYPE = "lsmc.dewey.sequencer-run.registered.v1"
ANALYSIS_RESULTS_EVENT_TYPE = "lsmc.dewey.analysis-results.registered.v1"
SEQUENCER_RUN_ARTIFACT_SET_TYPE = "sequencer_run"
ANALYSIS_RESULTS_ARTIFACT_SET_TYPE = "analysis_results"

SIMPLE_QC_COMMAND_BY_PLATFORM = {
    "ILMN": "illumina_run_qc",
    "ONT": "ont_run_qc",
    "ULTIMA": "ultima_run_qc",
    "HYBRID_ILMN_ONT": "illumina_run_qc",
}
CATALOG_COMMAND_IDS = {
    "illumina_run_qc",
    "ont_run_qc",
    "ultima_run_qc",
    "illumina_snv_alignstats_relatedness_vep_multiqc",
    "ultima_snv_alignstats_kitchensink",
    "ont_snv_alignstats_kitchensink",
    "hybrid_ilmn_ont_snv_kitchensink",
}
RAW_RUN_SUFFIXES = {
    ".bcl",
    ".cbcl",
    ".filter",
    ".locs",
    ".clocs",
    ".tif",
    ".tiff",
    ".jpg",
    ".jpeg",
    ".png",
    ".fast5",
    ".pod5",
    ".blow5",
}
PHI_EVENT_KEYS = {
    "patient",
    "patient_id",
    "patient_name",
    "name",
    "dob",
    "date_of_birth",
    "mrn",
    "email",
    "sample_name",
    "subject_name",
}


class SequencerRunRegistrationServiceMixin:
    @staticmethod
    def sequencer_run_idempotency_key(
        request_body: SequencerRunRegistrationRequest | dict[str, Any],
    ) -> str:
        return deterministic_idempotency_key("sequencer_run.register", request_body)

    @staticmethod
    def analysis_results_idempotency_key(
        request_body: AnalysisResultsRegistrationRequest | dict[str, Any],
    ) -> str:
        return deterministic_idempotency_key("analysis_results.register", request_body)

    @staticmethod
    def _parse_s3_uri_strict(uri: str, *, field_name: str) -> tuple[str, str, str]:
        parsed = urlparse(str(uri or "").strip())
        if parsed.scheme.lower() != "s3":
            raise ValueError(f"{field_name} must use s3://")
        bucket = str(parsed.netloc or "").strip()
        key = str(parsed.path or "").strip().lstrip("/")
        if not bucket or not key:
            raise ValueError(f"{field_name} must include bucket and key")
        return bucket, key, f"s3://{bucket}/{key}"

    @staticmethod
    def _run_relative_path(root_prefix: str, object_key: str) -> str:
        if not object_key.startswith(root_prefix):
            raise ValueError("selected object is outside the run root")
        return object_key[len(root_prefix) :].lstrip("/")

    @staticmethod
    def _run_label(root_prefix: str) -> str:
        return str(root_prefix or "").strip().rstrip("/").split("/")[-1]

    @staticmethod
    def _is_raw_run_file(relative_path: str) -> bool:
        lower = relative_path.lower()
        return any(lower.endswith(suffix) for suffix in RAW_RUN_SUFFIXES)

    @staticmethod
    def _artifact_role_for_relative_path(platform: str, relative_path: str) -> str | None:
        lower = relative_path.lower()
        name = Path(lower).name
        if SequencerRunRegistrationServiceMixin._is_raw_run_file(relative_path):
            return None
        if name == "runinfo.xml":
            return "run_info"
        if name in {"runparameters.xml", "runparameters.json"}:
            return "run_parameters"
        if name == "samplesheet.csv":
            return "sample_sheet"
        if lower.startswith("interop/"):
            return "interop_metrics"
        if "demux" in lower or "bclconvert" in lower or "reports/" in lower:
            return "demux_report"
        if lower.endswith((".fastq.gz", ".fq.gz", ".fastq", ".fq")):
            return "fastq"
        if lower.endswith(".bam"):
            return "bam"
        if lower.endswith(".cram"):
            return "cram"
        if lower.endswith(".cram.crai") or lower.endswith(".crai"):
            return "cram_index"
        if lower.endswith((".json", ".csv", ".tsv", ".txt", ".html", ".xml", ".h5")):
            if platform == "ONT" and "sequencing_summary" in lower:
                return "sequencing_summary"
            return "data_file"
        return None

    @classmethod
    def _select_run_objects(
        cls,
        *,
        platform: str,
        root_prefix: str,
        objects: list[StorageObject],
        sidecar_key: str,
        expected_files: list[FileEvidence],
    ) -> dict[str, tuple[StorageObject, str]]:
        expected_paths = {item.relative_path for item in expected_files}
        selected: dict[str, tuple[StorageObject, str]] = {}
        for obj in objects:
            relative_path = cls._run_relative_path(root_prefix, obj.key)
            if not relative_path:
                continue
            if obj.key == sidecar_key:
                selected[relative_path] = (obj, "analysis_pipeline_order_sidecar")
                continue
            if relative_path in expected_paths:
                role = next(
                    item.artifact_role
                    for item in expected_files
                    if item.relative_path == relative_path
                )
                selected[relative_path] = (obj, role)
                continue
            role = cls._artifact_role_for_relative_path(platform, relative_path)
            if role:
                selected[relative_path] = (obj, role)
        return selected

    def _validate_expected_files(
        self,
        *,
        selected: dict[str, tuple[StorageObject, str]],
        expected_files: list[FileEvidence],
    ) -> None:
        for expected in expected_files:
            row = selected.get(expected.relative_path)
            if row is None:
                if expected.required:
                    raise DeweyNotFoundError(
                        f"required run artifact missing: {expected.relative_path}"
                    )
                continue
            obj, _role = row
            if expected.size_bytes is not None and int(obj.size or -1) != expected.size_bytes:
                raise ValueError(f"size mismatch for {expected.relative_path}")
            observed_sha = str(getattr(obj, "sha256", "") or "").strip().lower()
            if expected.sha256 and observed_sha and observed_sha != expected.sha256:
                raise ValueError(f"checksum mismatch for {expected.relative_path}")

    @staticmethod
    def _event_has_phi(value: Any) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key or "").strip().lower() in PHI_EVENT_KEYS:
                    return True
                if SequencerRunRegistrationServiceMixin._event_has_phi(item):
                    return True
        elif isinstance(value, list):
            return any(SequencerRunRegistrationServiceMixin._event_has_phi(item) for item in value)
        return False

    def _create_outbox_event(
        self,
        session,
        *,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str,
        causation_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if self._event_has_phi(payload):
            raise ValueError("outbox event payload contains disallowed PHI-like keys")
        occurred_at = utc_now_iso()
        envelope = OutboxEventEnvelope(
            event_id=f"dewey-event-{canonical_sha256({'event_type': event_type, 'payload': payload, 'occurred_at': occurred_at})}",
            event_type=event_type,
            occurred_at=occurred_at,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        ).model_dump(mode="json", exclude_none=True)
        event = self.backend.create_instance(
            session,
            template_code=OUTBOX_EVENT_TEMPLATE,
            name=f"outbox:{event_type}",
            json_addl={
                **envelope,
                "status": "pending",
                "created_at": occurred_at,
            },
        )
        return event.euid, envelope

    def _create_receipt(
        self,
        session,
        *,
        receipt: RegistrationReceipt,
    ) -> tuple[str, dict[str, Any]]:
        payload = receipt.model_dump(mode="json", exclude_none=True)
        instance = self.backend.create_instance(
            session,
            template_code=REGISTRATION_RECEIPT_TEMPLATE,
            name=f"receipt:{receipt.registration_kind}:{receipt.artifact_set_euid}",
            json_addl={
                **payload,
                "receipt_sha256": canonical_sha256(payload),
            },
        )
        return instance.euid, payload

    def _assert_no_conflicting_artifact(
        self,
        session,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        existing = self.backend.find_by_json_field(
            session,
            template_code=ARTIFACT_TEMPLATE,
            field="storage_uri",
            value=str(payload.get("storage_uri") or ""),
        )
        if existing is None:
            return None
        existing_payload = normalize_instance_payload(existing)
        existing_role = str(existing_payload.get("metadata", {}).get("artifact_role") or "")
        incoming_role = str(payload.get("metadata", {}).get("artifact_role") or "")
        existing_sha = str((existing_payload.get("checksums") or {}).get("sha256") or "")
        incoming_sha = str((payload.get("checksums") or {}).get("sha256") or "")
        comparable = {
            "storage_uri": str(payload.get("storage_uri") or ""),
            "size": payload.get("size"),
            "sha256": incoming_sha,
            "artifact_role": incoming_role,
            "storage_kind": str(payload.get("storage_kind") or ""),
        }
        current = {
            "storage_uri": str(existing_payload.get("storage_uri") or ""),
            "size": existing_payload.get("size"),
            "sha256": existing_sha,
            "artifact_role": existing_role,
            "storage_kind": str(existing_payload.get("storage_kind") or ""),
        }
        if comparable != current:
            raise DeweyConflictError(
                f"artifact already exists with conflicting immutable metadata: {payload.get('storage_uri')}"
            )
        return self._artifact_response(existing)

    def _create_artifact_set_with_members(
        self,
        session,
        *,
        artifact_set_type: str,
        label: str,
        description: str | None,
        metadata: dict[str, Any],
        members: list[dict[str, Any]],
    ) -> dict[str, Any]:
        artifact_set = self.backend.create_instance(
            session,
            template_code=ARTIFACT_SET_TEMPLATE,
            name=label,
            json_addl={
                "artifact_set_type": artifact_set_type,
                "label": label,
                "description": description,
                "metadata": dict(metadata),
                "created_at": utc_now_iso(),
            },
        )
        for member in members:
            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=str(member.get("artifact_euid") or ""),
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {member.get('artifact_euid')}")
            self.backend.create_lineage(
                session,
                parent=artifact_set,
                child=artifact,
                relationship_type="artifact_set_member",
            )
        return self._artifact_set_response(session, artifact_set)

    def _manifest_rows(self, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for artifact in artifacts:
            rows.append(
                {
                    "artifact_euid": artifact.get("artifact_euid"),
                    "artifact_role": artifact.get("metadata", {}).get("artifact_role"),
                    "checksums": dict(artifact.get("checksums") or {}),
                    "relative_path": artifact.get("metadata", {}).get("relative_path"),
                    "size": artifact.get("size"),
                    "storage_kind": artifact.get("storage_kind"),
                    "storage_status": artifact.get("storage_status"),
                    "storage_uri": artifact.get("storage_uri"),
                    "version_id": artifact.get("version_id"),
                }
            )
        rows.sort(
            key=lambda item: (
                str(item.get("relative_path") or ""),
                str(item.get("storage_uri") or ""),
                str(item.get("artifact_role") or ""),
            )
        )
        return rows

    def register_sequencer_run(
        self,
        *,
        request_body: SequencerRunRegistrationRequest,
        idempotency_key: str | None,
        request_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        computed_key = self.sequencer_run_idempotency_key(request_body)
        clean_idempotency_key = str(idempotency_key or computed_key).strip()
        if clean_idempotency_key != computed_key:
            raise DeweyConflictError("Idempotency-Key does not match deterministic request key")

        bucket, root_prefix, normalized_root_uri = self._normalize_s3_prefix_uri(
            request_body.run_root_uri
        )
        platform = request_body.platform
        run_label = self._run_label(root_prefix)
        sidecar_key = f"{root_prefix}{run_label}.analysis_pipeline_order.tsv"
        storage = self._require_storage()
        objects = storage.list_objects(bucket=bucket, prefix=root_prefix, limit=250000)
        if not objects:
            raise DeweyNotFoundError(f"No S3 objects found for prefix: {normalized_root_uri}")
        object_map = {item.key: item for item in objects}
        expected_files = list(request_body.expected_files)
        selected = self._select_run_objects(
            platform=platform,
            root_prefix=root_prefix,
            objects=objects,
            sidecar_key=sidecar_key,
            expected_files=expected_files,
        )
        self._validate_expected_files(selected=selected, expected_files=expected_files)
        sidecar_object = object_map.get(sidecar_key)
        if request_body.sidecar_required and sidecar_object is None:
            raise DeweyNotFoundError(f"required sidecar missing: s3://{bucket}/{sidecar_key}")

        pipeline_plan = [
            {
                "source": "simple_qc",
                "pipeline_code": SIMPLE_QC_COMMAND_BY_PLATFORM[platform],
                "params": {},
            }
        ]
        sidecar_artifact_relative_path: str | None = None
        if sidecar_object is not None:
            sidecar_artifact_relative_path = self._run_relative_path(root_prefix, sidecar_key)
            sidecar_bytes = storage.get_object_bytes(
                bucket=bucket,
                key=sidecar_key,
                version_id=sidecar_object.version_id,
            )
            for entry in parse_pipeline_order_tsv(sidecar_bytes.decode("utf-8")):
                if entry.pipeline_code not in CATALOG_COMMAND_IDS:
                    raise ValueError(f"unsupported catalog pipeline_code: {entry.pipeline_code}")
                pipeline_plan.append(
                    {
                        "source": "sidecar",
                        "pipeline_code": entry.pipeline_code,
                        "params": entry.params,
                        "dewey_status": entry.dewey_status,
                        "dewey_date": entry.dewey_date,
                        "pipeline_attempts": entry.pipeline_attempts,
                    }
                )

        manifest_preview = [
            {
                "relative_path": relative_path,
                "storage_uri": f"s3://{bucket}/{obj.key}",
                "size": obj.size,
                "version_id": obj.version_id,
                "artifact_role": role,
                "storage_status": "observed",
            }
            for relative_path, (obj, role) in sorted(selected.items())
        ]
        manifest_sha256 = canonical_sha256(
            {
                "schema_version": request_body.schema_version,
                "run_root_uri": normalized_root_uri,
                "platform": platform,
                "files": manifest_preview,
                "pipeline_plan": pipeline_plan,
            }
        )
        if (
            request_body.expected_manifest_sha256
            and request_body.expected_manifest_sha256 != manifest_sha256
        ):
            raise ValueError("manifest_sha256 mismatch")

        fingerprint = canonical_sha256(request_body)
        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="sequencer_run.register",
                idempotency_key=clean_idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            observed_total_bytes = sum(int(item.size or 0) for item in objects)
            run_payload = self._artifact_payload(
                artifact_type="folder",
                storage_backend="s3",
                bucket=bucket,
                key=root_prefix,
                version_id=None,
                size=observed_total_bytes,
                checksums={},
                content_type=None,
                original_filename=run_label,
                producer_system="sequencer",
                producer_object_euid=request_body.run_euid,
                storage_class=None,
                availability_status="available",
                metadata={
                    "artifact_role": "sequencer_run_root",
                    "relative_path": "",
                    "platform": platform,
                    "run_root_uri": normalized_root_uri,
                    "run_euid": request_body.run_euid,
                    "run_xid": request_body.run_xid,
                    "bloom_run_euid": request_body.bloom_run_euid,
                    "atlas_order_euid": request_body.atlas_order_euid,
                    "observed_object_count": len(objects),
                    "observed_total_bytes": observed_total_bytes,
                    "registration_contract": "sequencer_run.v1",
                    **dict(request_body.metadata),
                },
                source_uri=normalized_root_uri,
                import_mode="register",
                storage_status="registered",
                storage_kind="prefix",
                node_kind="run_folder",
                is_terminal=False,
            )
            registered: list[dict[str, Any]] = []
            skipped: list[dict[str, Any]] = []
            artifact_members: dict[str, dict[str, Any]] = {}
            existing_run = self._assert_no_conflicting_artifact(session, payload=run_payload)
            if existing_run is not None:
                run_artifact = existing_run
                skipped.append(existing_run)
            else:
                _status, run_artifact = self._upsert_artifact_record(
                    session,
                    payload=run_payload,
                    created_at=utc_now_iso(),
                    refresh_existing=False,
                )
                registered.append(run_artifact)
            artifact_members[run_artifact["artifact_euid"]] = run_artifact

            for relative_path, (obj, role) in sorted(selected.items()):
                expected = next(
                    (item for item in expected_files if item.relative_path == relative_path),
                    None,
                )
                checksums = {"sha256": expected.sha256} if expected and expected.sha256 else {}
                file_payload = self._artifact_payload(
                    artifact_type=resolve_artifact_type(None, obj.key),
                    storage_backend="s3",
                    bucket=bucket,
                    key=obj.key,
                    version_id=obj.version_id,
                    size=obj.size,
                    checksums=checksums,
                    content_type=obj.content_type,
                    original_filename=Path(obj.key).name,
                    producer_system="sequencer",
                    producer_object_euid=request_body.run_euid,
                    storage_class=obj.storage_class,
                    availability_status="available",
                    metadata={
                        "artifact_role": role,
                        "relative_path": relative_path,
                        "platform": platform,
                        "run_root_uri": normalized_root_uri,
                        "run_euid": request_body.run_euid,
                        "parser_hint": expected.parser_hint if expected else None,
                    },
                    source_uri=f"s3://{bucket}/{obj.key}",
                    import_mode="reference",
                    storage_status="observed",
                    storage_verified_at=None,
                    storage_kind="object",
                    node_kind="file",
                    is_terminal=True,
                )
                existing = self._assert_no_conflicting_artifact(session, payload=file_payload)
                if existing is not None:
                    file_artifact = existing
                    skipped.append(existing)
                else:
                    _status, file_artifact = self._upsert_artifact_record(
                        session,
                        payload=file_payload,
                        created_at=utc_now_iso(),
                        refresh_existing=False,
                    )
                    registered.append(file_artifact)
                artifact_members[file_artifact["artifact_euid"]] = file_artifact
                self._create_artifact_lineage(
                    session,
                    parent_euid=run_artifact["artifact_euid"],
                    child_euid=file_artifact["artifact_euid"],
                )

            manifest_rows = self._manifest_rows(list(artifact_members.values()))
            artifact_set = self._create_artifact_set_with_members(
                session,
                artifact_set_type=SEQUENCER_RUN_ARTIFACT_SET_TYPE,
                label=f"sequencer-run:{run_label}",
                description="Sequencer run registration artifact set",
                metadata={
                    "schema_version": request_body.schema_version,
                    "run_root_uri": normalized_root_uri,
                    "platform": platform,
                    "run_euid": request_body.run_euid,
                    "run_xid": request_body.run_xid,
                    "bloom_run_euid": request_body.bloom_run_euid,
                    "atlas_order_euid": request_body.atlas_order_euid,
                    "manifest_sha256": manifest_sha256,
                    "pipeline_plan": pipeline_plan,
                    "sidecar_relative_path": sidecar_artifact_relative_path,
                    "trigger_policy": request_body.trigger_policy,
                    "registration_contract": "sequencer_run.v1",
                },
                members=list(artifact_members.values()),
            )
            event_payload = {
                "artifact_set_euid": artifact_set["artifact_set_euid"],
                "run_euid": request_body.run_euid,
                "platform": platform,
                "manifest_sha256": manifest_sha256,
                "trigger_policy": request_body.trigger_policy,
                "pipeline_codes": [item["pipeline_code"] for item in pipeline_plan],
            }
            outbox_euid, outbox = self._create_outbox_event(
                session,
                event_type=RUN_REGISTRATION_EVENT_TYPE,
                payload=event_payload,
                correlation_id=correlation_id,
                causation_id=request_id,
            )
            receipt = RegistrationReceipt(
                request_id=request_id,
                idempotency_key=clean_idempotency_key,
                registration_kind="sequencer_run",
                artifact_set_euid=artifact_set["artifact_set_euid"],
                registered_artifacts=[
                    {"artifact_euid": item["artifact_euid"], "storage_uri": item["storage_uri"]}
                    for item in registered
                ],
                skipped_existing=[
                    {"artifact_euid": item["artifact_euid"], "storage_uri": item["storage_uri"]}
                    for item in skipped
                ],
                failed=[],
                registered_at=utc_now_iso(),
                status="local_only"
                if request_body.trigger_policy == "register_only"
                else "registered_trigger_pending",
                local_only=request_body.trigger_policy == "register_only",
                outbox_event_euid=outbox_euid,
            )
            receipt_euid, receipt_payload = self._create_receipt(session, receipt=receipt)
            response = {
                "receipt_euid": receipt_euid,
                "receipt": receipt_payload,
                "artifact_set": artifact_set,
                "manifest": manifest_rows,
                "manifest_sha256": manifest_sha256,
                "pipeline_plan": pipeline_plan,
                "outbox_event": outbox,
            }
            self._store_idempotency(
                session,
                operation="sequencer_run.register",
                idempotency_key=clean_idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=response,
            )
            return 201, response

    def register_analysis_results(
        self,
        *,
        request_body: AnalysisResultsRegistrationRequest,
        idempotency_key: str | None,
        request_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        computed_key = self.analysis_results_idempotency_key(request_body)
        clean_idempotency_key = str(idempotency_key or computed_key).strip()
        if clean_idempotency_key != computed_key:
            raise DeweyConflictError("Idempotency-Key does not match deterministic request key")
        bucket, root_prefix, normalized_root_uri = self._normalize_s3_prefix_uri(
            request_body.result_root_uri
        )
        storage = self._require_storage()
        preflight: list[tuple[Any, StorageObject, str, str]] = []
        for artifact in request_body.artifacts:
            storage_uri = str(artifact.storage_uri or "").strip()
            if storage_uri:
                item_bucket, item_key, normalized_uri = self._parse_s3_uri_strict(
                    storage_uri,
                    field_name="storage_uri",
                )
            else:
                item_bucket = bucket
                item_key = f"{root_prefix}{artifact.relative_path}"
                normalized_uri = f"s3://{item_bucket}/{item_key}"
            try:
                obj = storage.head_object(
                    bucket=item_bucket,
                    key=item_key,
                    version_id=artifact.version_id,
                )
            except StorageObjectNotFoundError:
                if artifact.required:
                    raise
                continue
            if artifact.size_bytes is not None and int(obj.size or -1) != artifact.size_bytes:
                raise ValueError(f"size mismatch for {artifact.logical_name}")
            observed_sha = str(getattr(obj, "sha256", "") or "").strip().lower()
            if artifact.sha256 and observed_sha and observed_sha != artifact.sha256:
                raise ValueError(f"checksum mismatch for {artifact.logical_name}")
            relative_path = str(artifact.relative_path or "").strip().lstrip(
                "/"
            ) or item_key.removeprefix(root_prefix).lstrip("/")
            preflight.append((artifact, obj, normalized_uri, relative_path))

        fingerprint = canonical_sha256(request_body)
        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="analysis_results.register",
                idempotency_key=clean_idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            root_payload = self._artifact_payload(
                artifact_type="folder",
                storage_backend="s3",
                bucket=bucket,
                key=root_prefix,
                version_id=None,
                size=None,
                checksums={},
                content_type=None,
                original_filename=self._run_label(root_prefix),
                producer_system="ursa",
                producer_object_euid=request_body.analysis_euid,
                storage_class=None,
                availability_status="available",
                metadata={
                    "artifact_role": "analysis_result_root",
                    "relative_path": "",
                    "analysis_euid": request_body.analysis_euid,
                    "command_id": request_body.command_id,
                    "result_status": request_body.result_status,
                    "registration_contract": "analysis_results.v1",
                },
                source_uri=normalized_root_uri,
                import_mode="register",
                storage_status="registered",
                storage_kind="prefix",
                node_kind="analysis_result_folder",
                is_terminal=False,
            )
            registered: list[dict[str, Any]] = []
            skipped: list[dict[str, Any]] = []
            artifact_members: dict[str, dict[str, Any]] = {}
            existing_root = self._assert_no_conflicting_artifact(session, payload=root_payload)
            if existing_root is not None:
                root_artifact = existing_root
                skipped.append(existing_root)
            else:
                _status, root_artifact = self._upsert_artifact_record(
                    session,
                    payload=root_payload,
                    created_at=utc_now_iso(),
                    refresh_existing=False,
                )
                registered.append(root_artifact)
            artifact_members[root_artifact["artifact_euid"]] = root_artifact

            for artifact, obj, _normalized_uri, relative_path in preflight:
                checksums = {"sha256": artifact.sha256} if artifact.sha256 else {}
                storage_status = (
                    "verified" if artifact.sha256 and artifact.version_id else "observed"
                )
                payload = self._artifact_payload(
                    artifact_type=resolve_artifact_type(None, obj.key),
                    storage_backend="s3",
                    bucket=obj.bucket,
                    key=obj.key,
                    version_id=artifact.version_id or obj.version_id,
                    size=obj.size,
                    checksums=checksums,
                    content_type=artifact.mime_type or obj.content_type,
                    original_filename=Path(obj.key).name,
                    producer_system="ursa",
                    producer_object_euid=request_body.analysis_euid,
                    storage_class=obj.storage_class,
                    availability_status="available",
                    metadata={
                        "artifact_role": artifact.artifact_role,
                        "logical_name": artifact.logical_name,
                        "relative_path": relative_path,
                        "analysis_euid": request_body.analysis_euid,
                        "run_artifact_set_euid": request_body.run_artifact_set_euid,
                        "run_euid": request_body.run_euid,
                        "command_id": request_body.command_id,
                        "result_status": request_body.result_status,
                        "parser_hint": artifact.parser_hint,
                        "sample_identifiers": [
                            item.model_dump(mode="json", exclude_none=True)
                            for item in artifact.sample_identifiers
                        ],
                    },
                    source_uri=f"s3://{obj.bucket}/{obj.key}",
                    import_mode="reference",
                    storage_status=storage_status,
                    storage_verified_at=utc_now_iso() if storage_status == "verified" else None,
                    storage_kind="object",
                    node_kind="file",
                    is_terminal=True,
                )
                existing = self._assert_no_conflicting_artifact(session, payload=payload)
                if existing is not None:
                    result_artifact = existing
                    skipped.append(existing)
                else:
                    _status, result_artifact = self._upsert_artifact_record(
                        session,
                        payload=payload,
                        created_at=utc_now_iso(),
                        refresh_existing=False,
                    )
                    registered.append(result_artifact)
                artifact_members[result_artifact["artifact_euid"]] = result_artifact
                self._create_artifact_lineage(
                    session,
                    parent_euid=root_artifact["artifact_euid"],
                    child_euid=result_artifact["artifact_euid"],
                )

            manifest_rows = self._manifest_rows(list(artifact_members.values()))
            manifest_sha256 = canonical_sha256(
                {
                    "schema_version": request_body.schema_version,
                    "analysis_euid": request_body.analysis_euid,
                    "result_root_uri": normalized_root_uri,
                    "result_status": request_body.result_status,
                    "artifacts": manifest_rows,
                }
            )
            artifact_set = self._create_artifact_set_with_members(
                session,
                artifact_set_type=ANALYSIS_RESULTS_ARTIFACT_SET_TYPE,
                label=f"analysis-results:{request_body.analysis_euid}",
                description="Analysis terminal result artifact set",
                metadata={
                    "schema_version": request_body.schema_version,
                    "analysis_euid": request_body.analysis_euid,
                    "run_artifact_set_euid": request_body.run_artifact_set_euid,
                    "run_euid": request_body.run_euid,
                    "sidecar_artifact_euid": request_body.sidecar_artifact_euid,
                    "command_id": request_body.command_id,
                    "result_status": request_body.result_status,
                    "result_root_uri": normalized_root_uri,
                    "manifest_sha256": manifest_sha256,
                    "sample_identifiers": [
                        item.model_dump(mode="json", exclude_none=True)
                        for item in request_body.sample_identifiers
                    ],
                    "registration_contract": "analysis_results.v1",
                    **dict(request_body.metadata),
                },
                members=list(artifact_members.values()),
            )
            event_payload = {
                "artifact_set_euid": artifact_set["artifact_set_euid"],
                "analysis_euid": request_body.analysis_euid,
                "manifest_sha256": manifest_sha256,
                "command_id": request_body.command_id,
                "result_status": request_body.result_status,
            }
            outbox_euid, outbox = self._create_outbox_event(
                session,
                event_type=ANALYSIS_RESULTS_EVENT_TYPE,
                payload=event_payload,
                correlation_id=correlation_id,
                causation_id=request_id,
            )
            receipt = RegistrationReceipt(
                request_id=request_id,
                idempotency_key=clean_idempotency_key,
                registration_kind="analysis_results",
                artifact_set_euid=artifact_set["artifact_set_euid"],
                registered_artifacts=[
                    {"artifact_euid": item["artifact_euid"], "storage_uri": item["storage_uri"]}
                    for item in registered
                ],
                skipped_existing=[
                    {"artifact_euid": item["artifact_euid"], "storage_uri": item["storage_uri"]}
                    for item in skipped
                ],
                failed=[],
                registered_at=utc_now_iso(),
                status="registered",
                outbox_event_euid=outbox_euid,
            )
            receipt_euid, receipt_payload = self._create_receipt(session, receipt=receipt)
            response = {
                "receipt_euid": receipt_euid,
                "receipt": receipt_payload,
                "artifact_set": artifact_set,
                "manifest": manifest_rows,
                "manifest_sha256": manifest_sha256,
                "outbox_event": outbox,
            }
            self._store_idempotency(
                session,
                operation="analysis_results.register",
                idempotency_key=clean_idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=response,
            )
            return 201, response
