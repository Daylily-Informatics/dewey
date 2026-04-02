from __future__ import annotations

import hashlib
import io
import json
import zipfile
from typing import Any

import yaml

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.settings import Settings


class FakeDeweyService:
    def __init__(self) -> None:
        self._artifact_seq = 1
        self._artifact_set_seq = 1
        self._share_seq = 1
        self._external_seq = 1
        self._external_rel_seq = 1
        self._literature_save_seq = 1
        self._upload_seq = 1
        self._anomaly_seq = 1
        self.literature = object()
        self.artifacts: dict[str, dict[str, Any]] = {}
        self.artifact_sets: dict[str, dict[str, Any]] = {}
        self.share_references: dict[str, dict[str, Any]] = {}
        self.external_objects: dict[str, dict[str, Any]] = {}
        self.external_relations: list[dict[str, Any]] = []
        self.literature_saves: dict[str, dict[str, Any]] = {}
        self.anomalies: dict[str, dict[str, Any]] = {
            "ANM-000001": {
                "anomaly_id": "ANM-000001",
                "anomaly_identity_key": "dewey.readiness.bootstrap_gap",
                "category": "readiness",
                "severity": "medium",
                "status": "open",
                "title": "Readiness probe observed a bootstrap gap",
                "summary": "The local readiness surface recorded a brief backend-unavailable state during bootstrap.",
                "source": "readyz",
                "first_seen_at": "2026-03-10T00:00:00Z",
                "last_seen_at": "2026-03-10T00:00:00Z",
                "occurrence_count": 1,
                "redacted_context": {"database_status": "unknown"},
                "recommended_action": "Review readiness and database startup timing.",
                "source_view_url": "/ui/anomalies/ANM-000001",
                "created_at": "2026-03-10T00:00:00Z",
            },
            "ANM-000002": {
                "anomaly_id": "ANM-000002",
                "anomaly_identity_key": "dewey.auth.session_activity_low",
                "category": "auth",
                "severity": "low",
                "status": "monitoring",
                "title": "Operator session activity is sparse",
                "summary": "No recent browser-session auth events are present in the local anomaly record.",
                "source": "auth_health",
                "first_seen_at": "2026-03-10T00:00:00Z",
                "last_seen_at": "2026-03-10T00:00:00Z",
                "occurrence_count": 1,
                "redacted_context": {"recent_successes": 0},
                "recommended_action": "Confirm an operator can complete browser login during smoke testing.",
                "source_view_url": "/ui/anomalies/ANM-000002",
                "created_at": "2026-03-10T00:00:00Z",
            },
        }
        self.literature_records: dict[str, dict[str, Any]] = {
            "123456": {
                "pmid": "123456",
                "doi": "10.1000/example-123456",
                "pmcid": "PMC123456",
                "title": "Gene Therapy For Example Disease",
                "journal": "Example Journal",
                "year": "2024",
                "authors": ["Example A", "Author B"],
                "abstract_snippet": "Example abstract snippet for Dewey literature tests.",
                "source_urls": [
                    "https://pubmed.ncbi.nlm.nih.gov/123456/",
                    "https://doi.org/10.1000/example-123456",
                ],
                "best_fulltext_url": "https://europepmc.org/articles/PMC123456?pdf=render",
                "findit_reason": None,
                "storage_mode": "managed",
                "downloadable": True,
                "external_link_only": False,
            }
        }
        self.upload_sessions: dict[str, dict[str, Any]] = {}
        self.idempotency: dict[str, tuple[str, int, dict[str, Any]]] = {}

    @staticmethod
    def _fp(payload: dict[str, Any]) -> str:
        raw = repr(sorted(payload.items())).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _idempotent(self, op: str, key: str, payload: dict[str, Any]):
        lookup = f"{op}:{key}"
        fp = self._fp(payload)
        if lookup in self.idempotency:
            existing_fp, code, body = self.idempotency[lookup]
            if existing_fp != fp:
                from dewey_service.service import DeweyConflictError

                raise DeweyConflictError("Idempotency-Key reuse with different request payload")
            return code, body
        return None

    def _remember(
        self, op: str, key: str, payload: dict[str, Any], code: int, body: dict[str, Any]
    ) -> None:
        lookup = f"{op}:{key}"
        self.idempotency[lookup] = (self._fp(payload), code, dict(body))

    def bootstrap(self) -> None:
        return

    def _require_literature(self) -> None:
        if self.literature is None:
            from dewey_service.literature import LiteratureUnavailableError

            raise LiteratureUnavailableError(
                "Literature endpoints require metapub to be installed from the forked source repo."
            )

    def _literature_record(self, pmid: str) -> dict[str, Any]:
        key = str(pmid).strip()
        if key not in self.literature_records:
            self.literature_records[key] = {
                "pmid": key,
                "doi": f"10.1000/{key}",
                "pmcid": f"PMC{key}",
                "title": f"Literature Record {key}",
                "journal": "Example Journal",
                "year": "2024",
                "authors": ["Example Author"],
                "abstract_snippet": f"Abstract snippet for PMID {key}.",
                "source_urls": [f"https://pubmed.ncbi.nlm.nih.gov/{key}/"],
                "best_fulltext_url": f"https://europepmc.org/articles/PMC{key}?pdf=render",
                "findit_reason": None,
                "storage_mode": "managed",
                "downloadable": True,
                "external_link_only": False,
            }
        return dict(self.literature_records[key])

    def _literature_visibility(self, artifact_euid: str, viewer) -> dict[str, Any]:
        saved_by_me = False
        visible_owner_labels: list[str] = []
        viewer_email = str(getattr(viewer, "email", "") or "").strip().lower()
        viewer_subject = str(getattr(viewer, "subject", "") or "").strip()
        viewer_groups = set(getattr(viewer, "groups", ()) or ())
        for save in self.literature_saves.values():
            if save["artifact_euid"] != artifact_euid:
                continue
            scope = save["visibility_scope"]
            visible = save["owner_subject"] == viewer_subject
            if scope == "all_users":
                visible = True
            elif scope == "restricted":
                visible = viewer_email in set(save["allowed_users"]) or bool(
                    viewer_groups & set(save["allowed_groups"])
                )
            if not visible:
                continue
            if save["owner_subject"] == viewer_subject:
                saved_by_me = True
            elif save["owner_label"] not in visible_owner_labels:
                visible_owner_labels.append(save["owner_label"])
        return {
            "saved_by_me": saved_by_me,
            "saved_by_others_count": len(visible_owner_labels),
            "visible_owner_labels": visible_owner_labels,
        }

    def register_artifact(self, *, idempotency_key: str, **kwargs):
        payload = dict(kwargs)
        replay = self._idempotent("artifact.register", idempotency_key, payload)
        if replay:
            return replay
        euid = f"AT-{self._artifact_seq:06d}"
        self._artifact_seq += 1
        item = {
            "artifact_euid": euid,
            "artifact_type": kwargs["artifact_type"],
            "storage_backend": kwargs["storage_backend"],
            "bucket": kwargs["bucket"],
            "key": kwargs["key"],
            "version_id": kwargs.get("version_id"),
            "size": kwargs.get("size"),
            "checksums": dict(kwargs.get("checksums") or {}),
            "content_type": kwargs.get("content_type"),
            "original_filename": kwargs.get("original_filename"),
            "producer_system": kwargs.get("producer_system"),
            "producer_object_euid": kwargs.get("producer_object_euid"),
            "storage_class": kwargs.get("storage_class"),
            "availability_status": kwargs.get("availability_status"),
            "metadata": dict(kwargs.get("metadata") or {}),
            "storage_uri": f"{kwargs['storage_backend']}://{kwargs['bucket']}/{kwargs['key']}",
            "source_uri": kwargs.get("source_uri")
            or f"{kwargs['storage_backend']}://{kwargs['bucket']}/{kwargs['key']}",
            "import_mode": kwargs.get("import_mode", "register"),
            "storage_status": kwargs.get("storage_status", "registered"),
            "storage_verified_at": kwargs.get("storage_verified_at"),
            "retention_mode": kwargs.get("retention_mode"),
            "retain_until": kwargs.get("retain_until"),
            "share_status": kwargs.get("share_status"),
            "share_last_issued_at": kwargs.get("share_last_issued_at"),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.artifacts[euid] = item
        self._remember("artifact.register", idempotency_key, payload, 201, item)
        return 201, dict(item)

    def import_artifact_from_uri(
        self,
        *,
        artifact_type: str,
        storage_uri: str | None = None,
        source_uri: str | None = None,
        import_mode: str | None = None,
        lock_after_import: bool = False,
        producer_system: str | None = None,
        producer_object_euid: str | None = None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        source = source_uri or storage_uri or ""
        meta = dict(metadata or {})
        if not source.startswith(("s3://", "https://", "http://")):
            raise ValueError("source_uri must use s3:// or https://")
        if (import_mode or "reference") == "reference":
            if not source.startswith("s3://"):
                raise ValueError("reference import requires an s3:// source_uri")
            bucket_and_key = source[5:]
            bucket, key = bucket_and_key.split("/", 1)
            return self.register_artifact(
                artifact_type=artifact_type,
                storage_backend="s3",
                bucket=bucket,
                key=key,
                version_id=None,
                size=meta.get("size"),
                checksums=dict(meta.get("checksums") or {}),
                content_type=meta.get("content_type"),
                original_filename=meta.get("original_filename"),
                producer_system=producer_system or meta.get("producer_system"),
                producer_object_euid=producer_object_euid or meta.get("producer_object_euid"),
                storage_class=meta.get("storage_class"),
                availability_status=meta.get("availability_status") or "available",
                metadata=meta,
                source_uri=source,
                import_mode="reference",
                storage_status="verified",
                storage_verified_at="2026-03-10T00:00:00Z",
                retention_mode="GOVERNANCE" if lock_after_import else None,
                retain_until="2126-03-10T00:00:00Z" if lock_after_import else None,
                idempotency_key=idempotency_key,
            )
        return self.register_artifact(
            artifact_type=artifact_type,
            storage_backend="s3",
            bucket="managed-bucket",
            key=f"imports/{artifact_type}/{source.split('/')[-1]}",
            version_id=None,
            size=meta.get("size"),
            checksums=dict(meta.get("checksums") or {}),
            content_type=meta.get("content_type"),
            original_filename=meta.get("original_filename") or source.split("/")[-1],
            producer_system=producer_system or meta.get("producer_system"),
            producer_object_euid=producer_object_euid or meta.get("producer_object_euid"),
            storage_class=meta.get("storage_class"),
            availability_status=meta.get("availability_status") or "available",
            metadata=meta,
            source_uri=source,
            import_mode="copy",
            storage_status="verified",
            storage_verified_at="2026-03-10T00:00:00Z",
            retention_mode="GOVERNANCE" if lock_after_import else None,
            retain_until="2126-03-10T00:00:00Z" if lock_after_import else None,
            idempotency_key=idempotency_key,
        )

    def create_upload_session(
        self,
        *,
        artifact_type: str,
        original_filename: str,
        content_type: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        metadata: dict[str, Any] | None,
        lock_after_import: bool,
        idempotency_key: str,
    ):
        payload = {
            "artifact_type": artifact_type,
            "original_filename": original_filename,
            "content_type": content_type,
            "producer_system": producer_system,
            "producer_object_euid": producer_object_euid,
            "metadata": dict(metadata or {}),
            "lock_after_import": lock_after_import,
        }
        replay = self._idempotent("artifact.upload_session.create", idempotency_key, payload)
        if replay:
            return replay
        token = f"upload-{self._upload_seq:06d}"
        self._upload_seq += 1
        session = {
            **payload,
            "bucket": "managed-bucket",
            "key": f"uploads/{token}/{original_filename}",
        }
        self.upload_sessions[token] = session
        body = {
            "upload_token": token,
            "upload_method": "PUT",
            "upload_url": f"https://uploads.example.com/{token}",
            "upload_headers": {"Content-Type": content_type} if content_type else {},
            "bucket": session["bucket"],
            "key": session["key"],
            "storage_uri": f"s3://{session['bucket']}/{session['key']}",
            "expires_in": 900,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self._remember("artifact.upload_session.create", idempotency_key, payload, 201, body)
        return 201, body

    def complete_upload_session(
        self,
        *,
        upload_token: str,
        checksums: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        from dewey_service.service import DeweyNotFoundError

        if upload_token not in self.upload_sessions:
            raise DeweyNotFoundError("Uploaded object not found")
        session = self.upload_sessions[upload_token]
        merged_metadata = dict(session.get("metadata") or {})
        merged_metadata.update(dict(metadata or {}))
        return self.register_artifact(
            artifact_type=session["artifact_type"],
            storage_backend="s3",
            bucket=session["bucket"],
            key=session["key"],
            version_id=None,
            size=None,
            checksums=dict(checksums or {}),
            content_type=session.get("content_type"),
            original_filename=session["original_filename"],
            producer_system=session.get("producer_system"),
            producer_object_euid=session.get("producer_object_euid"),
            storage_class=None,
            availability_status="available",
            metadata=merged_metadata,
            source_uri=f"s3://{session['bucket']}/{session['key']}",
            import_mode="upload",
            storage_status="verified",
            storage_verified_at="2026-03-10T00:00:00Z",
            retention_mode="GOVERNANCE" if session.get("lock_after_import") else None,
            retain_until="2126-03-10T00:00:00Z" if session.get("lock_after_import") else None,
            idempotency_key=idempotency_key,
        )

    def upload_artifact_bytes(
        self,
        *,
        artifact_type: str,
        original_filename: str,
        body: bytes,
        content_type: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        metadata: dict[str, Any] | None,
        lock_after_import: bool,
        idempotency_key: str,
        checksums: dict[str, Any] | None = None,
    ):
        _ = body
        self.create_upload_session(
            artifact_type=artifact_type,
            original_filename=original_filename,
            content_type=content_type,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            metadata=metadata,
            lock_after_import=lock_after_import,
            idempotency_key=f"{idempotency_key}:create",
        )
        token = f"upload-{self._upload_seq - 1:06d}"
        return self.complete_upload_session(
            upload_token=token,
            checksums=checksums,
            metadata=metadata,
            idempotency_key=f"{idempotency_key}:complete",
        )

    def verify_artifact_storage(self, *, artifact_euid: str, idempotency_key: str):
        item = self.get_artifact(artifact_euid)
        item["storage_status"] = "verified"
        item["storage_verified_at"] = "2026-03-10T00:00:00Z"
        self.artifacts[artifact_euid] = item
        return 200, dict(item)

    def lock_artifact_storage(
        self,
        *,
        artifact_euid: str,
        mode: str,
        retain_until: str,
        idempotency_key: str,
    ):
        item = self.get_artifact(artifact_euid)
        item["retention_mode"] = mode
        item["retain_until"] = retain_until
        self.artifacts[artifact_euid] = item
        return 200, dict(item)

    def get_artifact(self, artifact_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        return dict(self.artifacts[artifact_euid])

    def list_artifacts(
        self,
        *,
        artifact_type: str | None = None,
        producer_system: str | None = None,
        limit: int = 200,
    ):
        rows = list(self.artifacts.values())
        if artifact_type:
            rows = [row for row in rows if row["artifact_type"] == artifact_type]
        if producer_system:
            rows = [row for row in rows if row.get("producer_system") == producer_system]
        return rows[:limit]

    def create_artifact_set(
        self,
        *,
        artifact_set_type: str,
        label: str | None,
        description: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        payload = {
            "artifact_set_type": artifact_set_type,
            "label": label,
            "description": description,
            "metadata": dict(metadata or {}),
        }
        replay = self._idempotent("artifact_set.create", idempotency_key, payload)
        if replay:
            return replay
        euid = f"AS-{self._artifact_set_seq:06d}"
        self._artifact_set_seq += 1
        item = {
            "artifact_set_euid": euid,
            "artifact_set_type": artifact_set_type,
            "label": label,
            "description": description,
            "metadata": dict(metadata or {}),
            "artifact_euids": [],
            "members": [],
            "member_count": 0,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.artifact_sets[euid] = item
        self._remember("artifact_set.create", idempotency_key, payload, 201, item)
        return 201, dict(item)

    def add_artifact_set_member(
        self, *, artifact_set_euid: str, artifact_euid: str, idempotency_key: str
    ):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        payload = {"artifact_set_euid": artifact_set_euid, "artifact_euid": artifact_euid}
        replay = self._idempotent("artifact_set.member.add", idempotency_key, payload)
        if replay:
            return replay
        aset = self.artifact_sets[artifact_set_euid]
        if artifact_euid not in aset["artifact_euids"]:
            aset["artifact_euids"].append(artifact_euid)
        aset["members"] = [self.artifacts[euid] for euid in aset["artifact_euids"]]
        aset["member_count"] = len(aset["artifact_euids"])
        self._remember("artifact_set.member.add", idempotency_key, payload, 200, dict(aset))
        return 200, dict(aset)

    def remove_artifact_set_member(
        self, *, artifact_set_euid: str, artifact_euid: str, idempotency_key: str
    ):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        if artifact_euid not in self.artifacts:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        payload = {"artifact_set_euid": artifact_set_euid, "artifact_euid": artifact_euid}
        replay = self._idempotent("artifact_set.member.remove", idempotency_key, payload)
        if replay:
            return replay
        aset = self.artifact_sets[artifact_set_euid]
        aset["artifact_euids"] = [e for e in aset["artifact_euids"] if e != artifact_euid]
        aset["members"] = [self.artifacts[euid] for euid in aset["artifact_euids"]]
        aset["member_count"] = len(aset["artifact_euids"])
        self._remember("artifact_set.member.remove", idempotency_key, payload, 200, dict(aset))
        return 200, dict(aset)

    def get_artifact_set(self, artifact_set_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if artifact_set_euid not in self.artifact_sets:
            raise DeweyNotFoundError(f"Artifact set not found: {artifact_set_euid}")
        return dict(self.artifact_sets[artifact_set_euid])

    def list_artifact_sets(self, *, artifact_set_type: str | None = None, limit: int = 200):
        rows = list(self.artifact_sets.values())
        if artifact_set_type:
            rows = [row for row in rows if row["artifact_set_type"] == artifact_set_type]
        return rows[:limit]

    def resolve_artifact(self, artifact_euid: str):
        return self.get_artifact(artifact_euid)

    def resolve_artifact_set(self, artifact_set_euid: str):
        return self.get_artifact_set(artifact_set_euid)

    def create_share_reference(
        self,
        *,
        target_type: str,
        target_euid: str,
        purpose: str | None,
        scope: str | None,
        expires_at: str | None,
        issued_by: str | None,
        transport: str | None = None,
        transport_config: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        idempotency_key: str,
    ):
        payload = {
            "target_type": target_type,
            "target_euid": target_euid,
            "purpose": purpose,
            "scope": scope,
            "expires_at": expires_at,
            "issued_by": issued_by,
            "transport": transport or "presigned_s3",
            "transport_config": dict(transport_config or {}),
            "ttl_seconds": ttl_seconds,
        }
        replay = self._idempotent("share_reference.create", idempotency_key, payload)
        if replay:
            return replay
        euid = f"SH-{self._share_seq:06d}"
        self._share_seq += 1
        if target_type == "artifact":
            self.get_artifact(target_euid)
            manifest: list[dict[str, Any]] = []
            connection: dict[str, Any] = {}
            access_url = f"https://downloads.example.com/{euid}"
        else:
            artifact_set = self.get_artifact_set(target_euid)
            if (transport or "presigned_s3") == "presigned_s3":
                manifest = [
                    {
                        "artifact_euid": artifact["artifact_euid"],
                        "status": "active",
                        "access_url": f"https://downloads.example.com/{artifact['artifact_euid']}",
                    }
                    for artifact in artifact_set["members"]
                ]
                connection = {}
                access_url = None
            else:
                host = str((transport_config or {}).get("host") or "0.0.0.0")
                port = int((transport_config or {}).get("port") or 8080)
                user = str((transport_config or {}).get("user") or "user")
                password = str((transport_config or {}).get("passwd") or "passwd")
                connection = {
                    "endpoint": (
                        f"http://{host}:{port}/"
                        if (transport or "") == "rclone_http"
                        else f"sftp://{user}@{host}:{port}/"
                    ),
                    "username": user,
                    "password": password,
                    "host": host,
                    "port": port,
                    "bucket": (transport_config or {}).get("bucket"),
                }
                manifest = []
                access_url = connection["endpoint"] if (transport or "") == "rclone_http" else None
        body = {
            "share_reference_euid": euid,
            "target_type": target_type,
            "target_euid": target_euid,
            "purpose": purpose,
            "scope": scope,
            "transport": transport or "presigned_s3",
            "status": "active",
            "starts_at": "2026-03-10T00:00:00Z",
            "expires_at": expires_at or "2026-03-10T12:00:00Z",
            "access_url": access_url,
            "manifest": manifest,
            "connection": connection,
            "member_count": len(manifest) if target_type == "artifact_set" else 0,
            "transport_config": dict(transport_config or {}),
            "issued_by": issued_by,
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.share_references[euid] = body
        if target_type == "artifact" and target_euid in self.artifacts:
            self.artifacts[target_euid]["share_status"] = "active"
            self.artifacts[target_euid]["share_last_issued_at"] = body["created_at"]
        self._remember("share_reference.create", idempotency_key, payload, 201, body)
        return 201, body

    def get_share_reference(self, share_reference_euid: str):
        from dewey_service.service import DeweyNotFoundError

        if share_reference_euid not in self.share_references:
            raise DeweyNotFoundError(f"Share reference not found: {share_reference_euid}")
        return dict(self.share_references[share_reference_euid])

    def list_share_references(
        self,
        *,
        target_type: str | None = None,
        target_euid: str | None = None,
        limit: int = 200,
    ):
        rows = list(self.share_references.values())
        if target_type:
            rows = [row for row in rows if row["target_type"] == target_type]
        if target_euid:
            rows = [row for row in rows if row["target_euid"] == target_euid]
        return rows[:limit]

    def list_anomalies(self, *, limit: int = 200):
        return list(self.anomalies.values())[:limit]

    def get_anomaly(self, anomaly_id: str):
        from dewey_service.service import DeweyNotFoundError

        if anomaly_id not in self.anomalies:
            raise DeweyNotFoundError(f"Anomaly not found: {anomaly_id}")
        return dict(self.anomalies[anomaly_id])

    def create_external_object(
        self,
        *,
        external_system: str,
        external_object_type: str,
        external_object_id: str,
        external_uri: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ):
        payload = {
            "external_system": external_system,
            "external_object_type": external_object_type,
            "external_object_id": external_object_id,
            "external_uri": external_uri,
            "metadata": dict(metadata or {}),
        }
        replay = self._idempotent("external_object.create", idempotency_key, payload)
        if replay:
            return replay
        euid = f"EO-{self._external_seq:06d}"
        self._external_seq += 1
        body = {
            "external_object_euid": euid,
            "external_system": external_system,
            "external_object_type": external_object_type,
            "external_object_id": external_object_id,
            "external_uri": external_uri,
            "metadata": dict(metadata or {}),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.external_objects[euid] = body
        self._remember("external_object.create", idempotency_key, payload, 201, body)
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
    ):
        from dewey_service.service import DeweyNotFoundError

        payload = {
            "target_type": target_type,
            "target_euid": target_euid,
            "external_object_euid": external_object_euid,
            "relation_type": relation_type,
            "metadata": dict(metadata or {}),
        }
        replay = self._idempotent("external_object_relation.attach", idempotency_key, payload)
        if replay:
            return replay
        if target_type == "artifact":
            self.get_artifact(target_euid)
        else:
            self.get_artifact_set(target_euid)
        if external_object_euid not in self.external_objects:
            raise DeweyNotFoundError(f"External object not found: {external_object_euid}")
        euid = f"ER-{self._external_rel_seq:06d}"
        self._external_rel_seq += 1
        row = {
            "external_object_relation_euid": euid,
            "target_type": target_type,
            "target_euid": target_euid,
            "external_object_euid": external_object_euid,
            "relation_type": relation_type,
            "metadata": dict(metadata or {}),
            "created_at": "2026-03-10T00:00:00Z",
        }
        self.external_relations.append(row)
        self._remember("external_object_relation.attach", idempotency_key, payload, 201, row)
        return 201, row

    def list_external_object_relations(
        self, *, target_type: str, target_euid: str, limit: int = 200
    ):
        rows = [
            row
            for row in self.external_relations
            if row["target_type"] == target_type and row["target_euid"] == target_euid
        ]
        return rows[:limit]

    def expand_s3_sources(self, source_uri: str, *, limit: int = 1000):
        if source_uri.endswith("/"):
            return [
                f"{source_uri.rstrip('/')}/file-{index}.dat"
                for index in range(1, min(limit, 3))
            ]
        return [source_uri]

    def build_artifact_download_archive(
        self,
        *,
        artifact_euids: list[str],
        naming_mode: str = "hybrid",
        include_metadata: bool = True,
    ):
        _ = naming_mode
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for artifact_euid in artifact_euids:
                artifact = self.get_artifact(artifact_euid)
                filename = artifact.get("original_filename") or f"{artifact_euid}.bin"
                zf.writestr(filename, f"payload for {artifact_euid}".encode("utf-8"))
                if include_metadata:
                    zf.writestr(
                        f"{filename}.dewey.yaml",
                        yaml.safe_dump(artifact, sort_keys=True),
                    )
        return "dewey-artifacts-test.zip", buffer.getvalue()

    def search_literature(self, *, viewer, query: str, page: int = 1, page_size: int = 20):
        self._require_literature()
        rows = []
        lowered = str(query or "").strip().lower()
        for record in self.literature_records.values():
            haystack = json.dumps(record, sort_keys=True).lower()
            if lowered and lowered not in haystack:
                continue
            artifact = next(
                (
                    item
                    for item in self.artifacts.values()
                    if item["artifact_type"] == "literature"
                    and item.get("metadata", {}).get("pmid") == record["pmid"]
                ),
                None,
            )
            visibility = (
                self._literature_visibility(artifact["artifact_euid"], viewer)
                if artifact
                else {
                    "saved_by_me": False,
                    "saved_by_others_count": 0,
                    "visible_owner_labels": [],
                }
            )
            rows.append(
                {
                    **record,
                    "artifact_euid": artifact["artifact_euid"] if artifact else None,
                    "already_in_dewey": artifact is not None,
                    **visibility,
                }
            )
        return {
            "items": rows[:page_size],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
            "has_more": len(rows) > page_size,
            "timing_ms": 1,
        }

    def save_literature(
        self,
        *,
        viewer,
        pmid: str,
        save_mode: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ):
        self._require_literature()
        payload = {
            "viewer_subject": viewer.subject,
            "pmid": pmid,
            "save_mode": save_mode,
            "visibility_scope": visibility_scope,
            "allowed_users": list(allowed_users or []),
            "allowed_groups": list(allowed_groups or []),
        }
        replay = self._idempotent("literature.save", idempotency_key, payload)
        if replay:
            return replay

        record = self._literature_record(pmid)
        artifact = next(
            (
                item
                for item in self.artifacts.values()
                if item["artifact_type"] == "literature"
                and item.get("metadata", {}).get("pmid") == record["pmid"]
            ),
            None,
        )
        if artifact is None:
            artifact_code, artifact = self.register_artifact(
                artifact_type="literature",
                storage_backend="s3" if save_mode != "external_reference" else "https",
                bucket="managed-bucket"
                if save_mode != "external_reference"
                else "pubmed.ncbi.nlm.nih.gov",
                key=f"literature/{record['pmid']}.pdf"
                if save_mode != "external_reference"
                else record["pmid"],
                version_id=None,
                size=None,
                checksums={},
                content_type="application/pdf" if save_mode != "external_reference" else None,
                original_filename=record["title"],
                producer_system="pubmed",
                producer_object_euid=record["pmid"],
                storage_class=None,
                availability_status="available"
                if save_mode != "external_reference"
                else "external_only",
                metadata={
                    **record,
                    "record_family": "literature",
                    "storage_mode": "managed"
                    if save_mode != "external_reference"
                    else "external_reference",
                    "acquisition_mode": save_mode,
                    "fulltext_status": "downloadable"
                    if save_mode != "external_reference"
                    else "external_link_only",
                },
                idempotency_key=f"lit-artifact-{record['pmid']}",
            )
        else:
            artifact_code = 200

        save = next(
            (
                item
                for item in self.literature_saves.values()
                if item["artifact_euid"] == artifact["artifact_euid"]
                and item["owner_subject"] == viewer.subject
            ),
            None,
        )
        if save is None:
            euid = f"SAV-{self._literature_save_seq:06d}"
            self._literature_save_seq += 1
            save = {
                "literature_save_euid": euid,
                "artifact_euid": artifact["artifact_euid"],
                "owner_subject": viewer.subject,
                "owner_email": viewer.email,
                "owner_label": viewer.email or viewer.subject,
                "visibility_scope": visibility_scope,
                "allowed_users": [
                    str(item).strip().lower() for item in allowed_users or [] if str(item).strip()
                ],
                "allowed_groups": [
                    str(item).strip() for item in allowed_groups or [] if str(item).strip()
                ],
                "artifact": {
                    "artifact_euid": artifact["artifact_euid"],
                    "title": artifact["metadata"]["title"],
                    "pmid": artifact["metadata"]["pmid"],
                    "doi": artifact["metadata"]["doi"],
                    "pmcid": artifact["metadata"]["pmcid"],
                    "storage_mode": artifact["metadata"]["storage_mode"],
                    "fulltext_status": artifact["metadata"]["fulltext_status"],
                },
                "created_at": "2026-03-10T00:00:00Z",
                "updated_at": "2026-03-10T00:00:00Z",
            }
            self.literature_saves[euid] = save
            save_code = 201
        else:
            save["visibility_scope"] = visibility_scope
            save["allowed_users"] = [
                str(item).strip().lower() for item in allowed_users or [] if str(item).strip()
            ]
            save["allowed_groups"] = [
                str(item).strip() for item in allowed_groups or [] if str(item).strip()
            ]
            save_code = 200
        body = {"artifact": artifact, "literature_save": dict(save)}
        code = 201 if artifact_code == 201 or save_code == 201 else 200
        self._remember("literature.save", idempotency_key, payload, code, body)
        return code, body

    def update_literature_save_visibility(
        self,
        *,
        viewer,
        literature_save_euid: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ):
        payload = {
            "viewer_subject": viewer.subject,
            "literature_save_euid": literature_save_euid,
            "visibility_scope": visibility_scope,
            "allowed_users": list(allowed_users or []),
            "allowed_groups": list(allowed_groups or []),
        }
        replay = self._idempotent("literature.save.visibility.update", idempotency_key, payload)
        if replay:
            return replay
        if literature_save_euid not in self.literature_saves:
            from dewey_service.service import DeweyNotFoundError

            raise DeweyNotFoundError(f"Literature save not found: {literature_save_euid}")
        save = self.literature_saves[literature_save_euid]
        save["visibility_scope"] = visibility_scope
        save["allowed_users"] = [
            str(item).strip().lower() for item in allowed_users or [] if str(item).strip()
        ]
        save["allowed_groups"] = [
            str(item).strip() for item in allowed_groups or [] if str(item).strip()
        ]
        self._remember(
            "literature.save.visibility.update",
            idempotency_key,
            payload,
            200,
            dict(save),
        )
        return 200, dict(save)

    def list_my_literature_saves(self, *, viewer, limit: int = 200):
        self._require_literature()
        rows = [
            dict(item)
            for item in self.literature_saves.values()
            if item["owner_subject"] == viewer.subject
        ]
        return rows[:limit]

    @staticmethod
    def _extract_path_values(payload: Any, path: str) -> list[Any]:
        parts = [part for part in str(path or "").split(".") if part]
        if not parts:
            return []

        def _walk(value: Any, remaining: list[str]) -> list[Any]:
            if not remaining:
                return [value]
            head, *tail = remaining
            if isinstance(value, list):
                rows: list[Any] = []
                for item in value:
                    rows.extend(_walk(item, remaining))
                return rows
            if not isinstance(value, dict) or head not in value:
                return []
            return _walk(value[head], tail)

        return _walk(payload, parts)

    def _matches_property_filter(self, row: dict[str, Any], item: dict[str, Any]) -> bool:
        path = str(item.get("path") or "").strip()
        op = str(item.get("op") or "eq").strip().lower()
        value = item.get("value")
        values = self._extract_path_values(row, path)
        if op == "in":
            acceptable = value if isinstance(value, list) else [value]
            return any(candidate in acceptable for candidate in values)
        if op == "contains":
            needle = str(value or "").lower()
            return any(needle in str(candidate or "").lower() for candidate in values)
        if op == "gte":
            return any(str(candidate or "") >= str(value or "") for candidate in values)
        if op == "lte":
            return any(str(candidate or "") <= str(value or "") for candidate in values)
        return any(candidate == value for candidate in values)

    def query_search_v2(self, request: dict[str, Any] | None, *, viewer_context=None):
        query = dict(request or {})
        scopes = query.get("scopes") or ["artifact", "share_reference"]
        viewer = viewer_context
        rows: list[dict[str, Any]] = []
        if "artifact" in scopes:
            for row in self.artifacts.values():
                search_row = {
                    "record_type": "artifact",
                    "source_kind": "dewey.artifact",
                    "euid": row["artifact_euid"],
                    "name": row.get("original_filename") or row["artifact_euid"],
                    "created_at": row["created_at"],
                    "modified_at": row["created_at"],
                    **row,
                }
                if row["artifact_type"] == "literature":
                    metadata = dict(row.get("metadata") or {})
                    search_row.update(
                        {
                            "title": metadata.get("title"),
                            "pmid": metadata.get("pmid"),
                            "doi": metadata.get("doi"),
                            "storage_mode": metadata.get("storage_mode"),
                        }
                    )
                    if viewer is not None:
                        search_row.update(self._literature_visibility(row["artifact_euid"], viewer))
                rows.append(search_row)
        if "artifact_set" in scopes:
            rows.extend(
                {
                    "record_type": "artifact_set",
                    "source_kind": "dewey.artifact_set",
                    "euid": row["artifact_set_euid"],
                    "name": row.get("label") or row["artifact_set_euid"],
                    "created_at": row["created_at"],
                    "modified_at": row["created_at"],
                    **row,
                }
                for row in self.artifact_sets.values()
            )
        if "share_reference" in scopes:
            rows.extend(
                {
                    "record_type": "share_reference",
                    "source_kind": "dewey.share_reference",
                    "euid": row["share_reference_euid"],
                    "name": row["share_reference_euid"],
                    "created_at": row["created_at"],
                    "modified_at": row["created_at"],
                    **row,
                }
                for row in self.share_references.values()
            )
        q = str(query.get("q") or "").strip().lower()
        if q:
            rows = [
                row for row in rows if q in json.dumps(row, sort_keys=True, default=str).lower()
            ]
        created_at_start = str(query.get("created_at_start") or "").strip()
        if created_at_start:
            rows = [row for row in rows if str(row.get("created_at") or "") >= created_at_start]
        created_at_end = str(query.get("created_at_end") or "").strip()
        if created_at_end:
            rows = [row for row in rows if str(row.get("created_at") or "") <= created_at_end]
        for item in query.get("property_filters") or []:
            rows = [row for row in rows if self._matches_property_filter(row, item)]
        page_size = int(query.get("page_size") or 25)
        return {
            "items": rows[:page_size],
            "facets": {
                "artifact": sum(1 for row in rows if row["record_type"] == "artifact"),
                "artifact_set": sum(1 for row in rows if row["record_type"] == "artifact_set"),
                "share_reference": sum(
                    1 for row in rows if row["record_type"] == "share_reference"
                ),
            },
            "total": len(rows),
            "page": int(query.get("page") or 1),
            "page_size": page_size,
            "has_more": False,
            "timing_ms": 1,
        }

    def collect_search_export_rows(self, request: dict[str, Any] | None, *, viewer_context=None):
        result = self.query_search_v2(request, viewer_context=viewer_context)
        return list(result["items"]), 1, False


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="https://dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


@pytest.fixture
def fake_service() -> FakeDeweyService:
    return FakeDeweyService()


@pytest.fixture
def client(test_settings: Settings, fake_service: FakeDeweyService) -> TestClient:
    app = create_app(settings=test_settings, service=fake_service)
    with TestClient(app, base_url="https://localhost:8914") as tc:
        yield tc
