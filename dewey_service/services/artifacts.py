"""Artifact and storage workflows for Dewey service."""

from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from itsdangerous import BadSignature, SignatureExpired

from dewey_service.artifact_ui import resolve_artifact_type
from dewey_service.services.base import DeweyNotFoundError
from dewey_service.storage import (
    StorageObject,
    StorageObjectNotFoundError,
    StoragePermissionError,
    StoragePrefix,
)
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)

ARTIFACT_HIERARCHY_RELATIONSHIP = "artifact_hierarchy"
SUPPORTED_RUN_PREFIX_PLATFORMS = {"ultima"}
_NUCLEOTIDE_TOKEN_RE = re.compile(r"^[ACGTN]+$", re.IGNORECASE)
_RUN_ID_RE = re.compile(r"^RUN[0-9]+$", re.IGNORECASE)


class ArtifactServiceMixin:
    @staticmethod
    def _parse_s3_uri(uri: str) -> tuple[str, str]:
        parsed = urlparse(str(uri or "").strip())
        if parsed.scheme.lower() != "s3":
            raise ValueError("source_uri must use s3:// for S3 import flows")
        bucket = str(parsed.netloc or "").strip()
        key = str(parsed.path or "").strip().lstrip("/")
        if not bucket or not key:
            raise ValueError("source_uri must include bucket and key")
        return bucket, key

    @staticmethod
    def _source_filename(source_uri: str, original_filename: str | None = None) -> str:
        explicit = str(original_filename or "").strip()
        if explicit:
            return explicit
        parsed = urlparse(str(source_uri or "").strip())
        candidate = str(parsed.path or "").strip().rstrip("/").split("/")[-1]
        return candidate or "artifact.bin"

    def expand_s3_sources(self, source_uri: str, *, limit: int = 1000) -> list[str]:
        bucket, key = self._parse_s3_uri(source_uri)
        storage = self._require_storage()
        clean_uri = str(source_uri or "").strip()
        if clean_uri.endswith("/"):
            objects = storage.list_objects(bucket=bucket, prefix=key, limit=limit)
            if not objects:
                raise DeweyNotFoundError(f"No S3 objects found for prefix: {source_uri}")
            return [self._storage_uri("s3", bucket, item.key) for item in objects]
        try:
            storage.head_object(bucket=bucket, key=key)
            return [self._storage_uri("s3", bucket, key)]
        except StorageObjectNotFoundError:
            prefix = key.rstrip("/") + "/"
            objects = storage.list_objects(bucket=bucket, prefix=prefix, limit=limit)
            if not objects:
                raise DeweyNotFoundError(f"S3 object or prefix not found: {source_uri}")
            return [self._storage_uri("s3", bucket, item.key) for item in objects]

    @staticmethod
    def _filename_suffix(value: str) -> str:
        candidate = str(value or "").strip()
        if not candidate:
            return ""
        suffixes = Path(candidate).suffixes
        return "".join(suffixes) if suffixes else ""

    @staticmethod
    def _dedupe_filename(filename: str, used: set[str]) -> str:
        if filename not in used:
            used.add(filename)
            return filename
        stem = Path(filename).stem or "artifact"
        suffix = "".join(Path(filename).suffixes)
        counter = 2
        while True:
            candidate = f"{stem}-{counter}{suffix}"
            if candidate not in used:
                used.add(candidate)
                return candidate
            counter += 1

    def _download_filename(self, artifact: dict[str, Any], naming_mode: str) -> str:
        clean_mode = str(naming_mode or "hybrid").strip().lower() or "hybrid"
        original_name = self._safe_filename(
            artifact.get("original_filename"),
        )
        suffix = self._filename_suffix(original_name)
        if clean_mode == "dewey":
            return self._safe_filename(f"{artifact['artifact_euid']}{suffix or '.bin'}")
        if clean_mode == "orig":
            return original_name
        return self._safe_filename(f"{artifact['artifact_euid']}.{original_name}")

    def _download_artifact_bytes(self, artifact: dict[str, Any]) -> bytes:
        if not self._artifact_is_object(artifact):
            raise ValueError("download requires an object-backed artifact")
        backend = str(artifact.get("storage_backend") or "").strip().lower()
        if backend == "s3":
            return self._require_storage().get_object_bytes(
                bucket=str(artifact.get("bucket") or ""),
                key=str(artifact.get("key") or ""),
                version_id=str(artifact.get("version_id") or "").strip() or None,
            )
        source_uri = str(artifact.get("source_uri") or "").strip()
        if source_uri.startswith(("https://", "http://")):
            response = requests.get(source_uri, timeout=60)
            response.raise_for_status()
            return bytes(response.content)
        raise ValueError(f"direct download unsupported for storage backend: {backend or 'unknown'}")

    def build_artifact_download_archive(
        self,
        *,
        artifact_euids: list[str],
        naming_mode: str = "hybrid",
        include_metadata: bool = True,
    ) -> tuple[str, bytes]:
        selected = [str(item or "").strip() for item in artifact_euids if str(item or "").strip()]
        if not selected:
            raise ValueError("at least one artifact_euid is required")
        seen: set[str] = set()
        buffer = io.BytesIO()
        archive_name = (
            f"dewey-artifacts-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.zip"
        )
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for artifact_euid in selected:
                artifact = self.get_artifact(artifact_euid)
                filename = self._dedupe_filename(
                    self._download_filename(artifact, naming_mode),
                    seen,
                )
                zf.writestr(filename, self._download_artifact_bytes(artifact))
                if include_metadata:
                    metadata_name = self._dedupe_filename(f"{filename}.dewey.yaml", seen)
                    zf.writestr(
                        metadata_name,
                        yaml.safe_dump(
                            artifact,
                            sort_keys=True,
                            allow_unicode=False,
                        ),
                    )
        return archive_name, buffer.getvalue()

    def _managed_key(self, *, namespace: str, seed: str, filename: str) -> str:
        prefix = "/".join(
            item
            for item in [
                self.managed_storage_prefix,
                namespace,
                self._fingerprint({"seed": seed})[:16],
            ]
            if item
        )
        return f"{prefix}/{self._safe_filename(filename)}"

    @staticmethod
    def _storage_uri(storage_backend: str, bucket: str, key: str) -> str:
        return f"{storage_backend}://{bucket}/{key}"

    @staticmethod
    def _normalize_s3_prefix_uri(uri: str) -> tuple[str, str, str]:
        try:
            bucket, key = ArtifactServiceMixin._parse_s3_uri(uri)
        except ValueError as exc:
            raise ValueError(str(exc).replace("source_uri", "root_uri")) from exc
        prefix = key.rstrip("/") + "/"
        return bucket, prefix, f"s3://{bucket}/{prefix}"

    @staticmethod
    def _normalize_s3_browse_uri(uri: str) -> tuple[str, str, str]:
        parsed = urlparse(str(uri or "").strip())
        if parsed.scheme.lower() != "s3":
            raise ValueError("root_uri must use s3:// for S3 browse flows")
        bucket = str(parsed.netloc or "").strip()
        if not bucket:
            raise ValueError("root_uri must include a bucket")
        raw_key = str(parsed.path or "").strip().lstrip("/")
        prefix = raw_key.rstrip("/")
        normalized_prefix = f"{prefix}/" if prefix else ""
        normalized_uri = (
            f"s3://{bucket}/{normalized_prefix}" if normalized_prefix else f"s3://{bucket}/"
        )
        return bucket, normalized_prefix, normalized_uri

    @staticmethod
    def _normalize_owner_email(owner_email: str) -> str:
        clean = str(owner_email or "").strip().lower()
        if not clean:
            raise ValueError("owner_email is required")
        return clean

    @staticmethod
    def _parse_run_id_from_prefix(prefix: str) -> str | None:
        for segment in reversed([item for item in str(prefix or "").split("/") if item]):
            if _RUN_ID_RE.match(segment):
                return segment.upper()
        return None

    @staticmethod
    def _parse_seq_index(folder_label: str) -> str | None:
        token = str(folder_label or "").strip().split("-")[-1].upper()
        if token and _NUCLEOTIDE_TOKEN_RE.match(token):
            return token
        return None

    @staticmethod
    def _folder_label_from_prefix(prefix: str) -> str:
        return str(prefix or "").strip().rstrip("/").split("/")[-1]

    @staticmethod
    def _artifact_is_object(payload: dict[str, Any]) -> bool:
        return str(payload.get("storage_kind") or "object").strip().lower() == "object"

    @staticmethod
    def _artifact_is_prefix(payload: dict[str, Any]) -> bool:
        return str(payload.get("storage_kind") or "").strip().lower() == "prefix"

    @staticmethod
    def _object_updates(obj: StorageObject) -> dict[str, Any]:
        return {
            "version_id": obj.version_id,
            "size": obj.size,
            "content_type": obj.content_type,
            "storage_class": obj.storage_class,
            "availability_status": "available",
        }

    def _artifact_payload(
        self,
        *,
        artifact_type: str,
        storage_backend: str,
        bucket: str,
        key: str,
        version_id: str | None,
        size: int | None,
        checksums: dict[str, Any] | None,
        content_type: str | None,
        original_filename: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        storage_class: str | None,
        availability_status: str | None,
        metadata: dict[str, Any] | None,
        source_uri: str | None = None,
        import_mode: str | None = None,
        storage_status: str | None = None,
        storage_verified_at: str | None = None,
        storage_kind: str | None = None,
        node_kind: str | None = None,
        is_terminal: bool | None = None,
        retention_mode: str | None = None,
        retain_until: str | None = None,
        share_status: str | None = None,
        share_last_issued_at: str | None = None,
        artifact_identity_key: str | None = None,
    ) -> dict[str, Any]:
        clean_artifact_type = resolve_artifact_type(
            artifact_type, original_filename, key, source_uri
        )
        backend, bucket_value, key_value, version_value, storage_uri = self._normalize_storage(
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=version_id,
        )
        payload = {
            "artifact_type": clean_artifact_type,
            "storage_backend": backend,
            "bucket": bucket_value,
            "key": key_value,
            "version_id": version_value,
            "size": int(size) if size is not None else None,
            "checksums": dict(checksums or {}),
            "content_type": str(content_type or "").strip() or None,
            "original_filename": str(original_filename or "").strip() or None,
            "producer_system": str(producer_system or "").strip() or None,
            "producer_object_euid": str(producer_object_euid or "").strip() or None,
            "storage_class": str(storage_class or "").strip() or None,
            "availability_status": str(availability_status or "").strip() or None,
            "metadata": dict(metadata or {}),
            "storage_uri": storage_uri,
            "source_uri": str(source_uri or storage_uri).strip() or storage_uri,
            "import_mode": str(import_mode or "register").strip().lower() or "register",
            "storage_status": str(storage_status or "registered").strip().lower() or "registered",
            "storage_verified_at": str(storage_verified_at or "").strip() or None,
            "storage_kind": str(storage_kind or "object").strip().lower() or "object",
            "node_kind": str(node_kind or "file").strip().lower() or "file",
            "is_terminal": (
                bool(is_terminal)
                if is_terminal is not None
                else str(storage_kind or "object").strip().lower() != "prefix"
            ),
            "retention_mode": str(retention_mode or "").strip().upper() or None,
            "retain_until": str(retain_until or "").strip() or None,
            "share_status": str(share_status or "").strip().lower() or None,
            "share_last_issued_at": str(share_last_issued_at or "").strip() or None,
        }
        payload["artifact_identity_key"] = str(
            artifact_identity_key or ""
        ).strip() or self._artifact_identity_key(payload)
        return payload

    def _tag_artifact_object(
        self,
        *,
        artifact_payload: dict[str, Any],
        artifact_euid: str,
        tolerate_permission_errors: bool = False,
    ) -> None:
        if not self._artifact_is_object(artifact_payload):
            return
        if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
            return
        storage = self._require_storage()
        tags = {
            "dewey_artifact_euid": artifact_euid,
            "dewey_artifact_type": str(artifact_payload.get("artifact_type") or ""),
        }
        original_filename = str(artifact_payload.get("original_filename") or "").strip()
        if original_filename:
            tags["dewey_original_file_name"] = original_filename
        try:
            storage.put_object_tags(
                bucket=str(artifact_payload.get("bucket") or ""),
                key=str(artifact_payload.get("key") or ""),
                tags=tags,
            )
        except StoragePermissionError:
            if not tolerate_permission_errors:
                raise

    def _lock_artifact_payload(
        self,
        *,
        artifact_payload: dict[str, Any],
        mode: str,
        retain_until: datetime,
    ) -> None:
        if not self._artifact_is_object(artifact_payload):
            raise ValueError("storage lock requires an object-backed artifact")
        if str(artifact_payload.get("storage_backend") or "").lower() != "s3":
            raise ValueError("storage lock requires an s3-backed artifact")
        storage = self._require_storage()
        storage.set_retention(
            bucket=str(artifact_payload.get("bucket") or ""),
            key=str(artifact_payload.get("key") or ""),
            mode=mode,
            retain_until=retain_until,
        )

    def _upsert_artifact_record(
        self,
        session,
        *,
        payload: dict[str, Any],
        created_at: str | None = None,
        refresh_existing: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        existing = self.backend.find_by_json_field(
            session,
            template_code=ARTIFACT_TEMPLATE,
            field="artifact_identity_key",
            value=str(payload.get("artifact_identity_key") or ""),
        )
        if existing is not None:
            if refresh_existing:
                updates = dict(payload)
                updates["created_at"] = str(
                    normalize_instance_payload(existing).get("created_at")
                    or created_at
                    or utc_now_iso()
                )
                self.backend.update_instance_json(session, existing, updates)
            return 200, self._artifact_response(existing)

        artifact = self.backend.create_instance(
            session,
            template_code=ARTIFACT_TEMPLATE,
            name=str(
                payload.get("original_filename") or payload.get("storage_uri") or payload["key"]
            ),
            json_addl={
                **payload,
                "created_at": created_at or utc_now_iso(),
            },
        )
        return 201, self._artifact_response(artifact)

    def _artifact_instance(self, session, *, artifact_euid: str, for_update: bool = False):
        artifact = self.backend.find_by_euid(
            session,
            template_code=ARTIFACT_TEMPLATE,
            euid=str(artifact_euid or "").strip(),
            for_update=for_update,
        )
        if artifact is None:
            raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
        return artifact

    def _artifact_relationships(
        self,
        *,
        artifact_euid: str,
        direction: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            artifact = self._artifact_instance(session, artifact_euid=artifact_euid)
            rows = (
                self.backend.list_children(
                    session,
                    parent=artifact,
                    relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
                )
                if direction == "children"
                else self.backend.list_parents(
                    session,
                    child=artifact,
                    relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
                )
            )
            payloads = [self._artifact_response(row) for row in rows]
            payloads.sort(
                key=lambda item: (
                    str(item.get("node_kind") or ""),
                    str(item.get("original_filename") or item.get("storage_uri") or ""),
                    str(item.get("artifact_euid") or ""),
                )
            )
            return payloads[: max(1, min(limit, 2000))]

    def list_artifact_children(
        self, *, artifact_euid: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        return self._artifact_relationships(
            artifact_euid=artifact_euid,
            direction="children",
            limit=limit,
        )

    def list_artifact_parents(
        self, *, artifact_euid: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        return self._artifact_relationships(
            artifact_euid=artifact_euid,
            direction="parents",
            limit=limit,
        )

    def _create_artifact_lineage(
        self,
        session,
        *,
        parent_euid: str,
        child_euid: str,
    ) -> None:
        parent = self._artifact_instance(session, artifact_euid=parent_euid)
        child = self._artifact_instance(session, artifact_euid=child_euid)
        self.backend.create_lineage(
            session,
            parent=parent,
            child=child,
            relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
        )

    @staticmethod
    def _format_size(size: int | None) -> str | None:
        if size is None:
            return None
        value = float(size)
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        unit_index = 0
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        if unit_index == 0:
            return f"{int(value)} {units[unit_index]}"
        return f"{value:.1f} {units[unit_index]}"

    @staticmethod
    def _parent_prefix_uri(bucket: str, prefix: str) -> str | None:
        clean = str(prefix or "").strip().strip("/")
        if not clean:
            return None
        parts = [item for item in clean.split("/") if item]
        parent_parts = parts[:-1]
        parent_prefix = "/".join(parent_parts)
        if parent_prefix:
            return f"s3://{bucket}/{parent_prefix}/"
        return f"s3://{bucket}/"

    @staticmethod
    def _prefix_breadcrumbs(bucket: str, prefix: str) -> list[dict[str, str]]:
        crumbs = [{"label": bucket, "uri": f"s3://{bucket}/"}]
        segments = [item for item in str(prefix or "").strip().strip("/").split("/") if item]
        if not segments:
            return crumbs
        built: list[str] = []
        for segment in segments:
            built.append(segment)
            crumbs.append(
                {
                    "label": segment,
                    "uri": f"s3://{bucket}/{'/'.join(built)}/",
                }
            )
        return crumbs

    def _artifact_for_storage_uri(self, session, *, storage_uri: str) -> dict[str, Any] | None:
        row = self.backend.find_by_json_field(
            session,
            template_code=ARTIFACT_TEMPLATE,
            field="storage_uri",
            value=str(storage_uri or "").strip(),
        )
        if row is None:
            return None
        return self._artifact_response(row)

    def _browse_prefix_row(
        self,
        session,
        *,
        bucket: str,
        prefix: StoragePrefix,
    ) -> dict[str, Any]:
        storage_uri = f"s3://{bucket}/{prefix.prefix}" if prefix.prefix else f"s3://{bucket}/"
        registered = self._artifact_for_storage_uri(session, storage_uri=storage_uri)
        payload = {
            "entry_kind": "prefix",
            "label": self._folder_label_from_prefix(prefix.prefix),
            "bucket": bucket,
            "key": prefix.prefix,
            "storage_uri": storage_uri,
            "storage_console_url": self._artifact_storage_console_url(
                {
                    "storage_backend": "s3",
                    "bucket": bucket,
                    "key": prefix.prefix,
                }
            ),
            "registered_artifact": registered,
        }
        if registered is not None:
            payload["artifact_euid"] = registered["artifact_euid"]
        return payload

    def _browse_object_row(
        self,
        session,
        *,
        storage_object: StorageObject,
    ) -> dict[str, Any]:
        storage_uri = f"s3://{storage_object.bucket}/{storage_object.key}"
        registered = self._artifact_for_storage_uri(session, storage_uri=storage_uri)
        payload = {
            "entry_kind": "object",
            "label": Path(storage_object.key).name,
            "bucket": storage_object.bucket,
            "key": storage_object.key,
            "size": storage_object.size,
            "size_human": self._format_size(storage_object.size),
            "storage_class": storage_object.storage_class,
            "etag": storage_object.etag,
            "artifact_type": resolve_artifact_type(None, storage_object.key),
            "storage_uri": storage_uri,
            "storage_console_url": self._artifact_storage_console_url(
                {
                    "storage_backend": "s3",
                    "bucket": storage_object.bucket,
                    "key": storage_object.key,
                }
            ),
            "registered_artifact": registered,
        }
        if registered is not None:
            payload["artifact_euid"] = registered["artifact_euid"]
        return payload

    def browse_storage_prefix(
        self,
        *,
        root_uri: str,
        limit: int = 200,
        continuation_token: str | None = None,
    ) -> dict[str, Any]:
        bucket, prefix, normalized_uri = self._normalize_s3_browse_uri(root_uri)
        browse_result = self._require_storage().browse_prefix(
            bucket=bucket,
            prefix=prefix,
            limit=limit,
            continuation_token=continuation_token,
        )
        with self.backend.session_scope(commit=False) as session:
            current_artifact = self._artifact_for_storage_uri(session, storage_uri=normalized_uri)
            prefixes = [
                self._browse_prefix_row(session, bucket=bucket, prefix=item)
                for item in browse_result.get("prefixes", [])
            ]
            objects = [
                self._browse_object_row(session, storage_object=item)
                for item in browse_result.get("objects", [])
            ]
        return {
            "bucket": bucket,
            "prefix": prefix,
            "root_uri": normalized_uri,
            "parent_uri": self._parent_prefix_uri(bucket, prefix),
            "breadcrumbs": self._prefix_breadcrumbs(bucket, prefix),
            "current_artifact": current_artifact,
            "prefixes": prefixes,
            "objects": objects,
            "is_truncated": bool(browse_result.get("is_truncated")),
            "next_continuation_token": browse_result.get("next_continuation_token"),
        }

    @staticmethod
    def _artifact_browse_root_uri(artifact: dict[str, Any]) -> str | None:
        if str(artifact.get("storage_backend") or "").strip().lower() != "s3":
            return None
        bucket = str(artifact.get("bucket") or "").strip()
        key = str(artifact.get("key") or "").strip()
        if not bucket:
            return None
        if str(artifact.get("storage_kind") or "").strip().lower() == "prefix":
            return str(artifact.get("storage_uri") or "").strip() or f"s3://{bucket}/{key}"
        parent_parts = [item for item in key.split("/") if item][:-1]
        if not parent_parts:
            return f"s3://{bucket}/"
        return f"s3://{bucket}/{'/'.join(parent_parts)}/"

    def get_artifact_graph(
        self,
        *,
        artifact_euid: str,
        depth: int = 3,
        limit: int = 200,
    ) -> dict[str, Any]:
        max_depth = max(0, min(int(depth), 6))
        max_nodes = max(1, min(int(limit), 500))
        with self.backend.session_scope(commit=False) as session:
            root = self._artifact_instance(session, artifact_euid=artifact_euid)
            queue: list[tuple[Any, int]] = [(root, 0)]
            seen: set[str] = set()
            instances: dict[str, Any] = {root.euid: root}
            edges: set[tuple[str, str]] = set()

            while queue and len(instances) <= max_nodes:
                current, current_depth = queue.pop(0)
                current_euid = str(current.euid)
                if current_euid in seen:
                    continue
                seen.add(current_euid)
                if current_depth >= max_depth:
                    continue

                children = self.backend.list_children(
                    session,
                    parent=current,
                    relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
                )
                for child in children:
                    edges.add((current_euid, str(child.euid)))
                    if str(child.euid) not in instances and len(instances) < max_nodes:
                        instances[str(child.euid)] = child
                    if str(child.euid) not in seen and len(instances) <= max_nodes:
                        queue.append((child, current_depth + 1))

                parents = self.backend.list_parents(
                    session,
                    child=current,
                    relationship_type=ARTIFACT_HIERARCHY_RELATIONSHIP,
                )
                for parent in parents:
                    edges.add((str(parent.euid), current_euid))
                    if str(parent.euid) not in instances and len(instances) < max_nodes:
                        instances[str(parent.euid)] = parent
                    if str(parent.euid) not in seen and len(instances) <= max_nodes:
                        queue.append((parent, current_depth + 1))

            nodes: list[dict[str, Any]] = []
            for euid, instance in sorted(instances.items()):
                payload = self._artifact_response(instance)
                nodes.append(
                    {
                        "id": euid,
                        "artifact_euid": euid,
                        "label": str(
                            payload.get("original_filename")
                            or payload.get("storage_uri")
                            or payload.get("artifact_euid")
                        ),
                        "subtitle": str(
                            payload.get("node_kind") or payload.get("artifact_type") or "artifact"
                        ),
                        "artifact_type": payload.get("artifact_type"),
                        "node_kind": payload.get("node_kind"),
                        "storage_kind": payload.get("storage_kind"),
                        "is_terminal": payload.get("is_terminal"),
                        "storage_uri": payload.get("storage_uri"),
                        "storage_console_url": payload.get("storage_console_url"),
                        "detail_href": f"/artifacts/euid/{euid}",
                        "browse_root_uri": self._artifact_browse_root_uri(payload),
                        "metadata": payload.get("metadata") or {},
                    }
                )
        node_ids = {node["id"] for node in nodes}
        return {
            "root_euid": artifact_euid,
            "depth": max_depth,
            "nodes": nodes,
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "relationship_type": ARTIFACT_HIERARCHY_RELATIONSHIP,
                }
                for source, target in sorted(edges)
                if source in node_ids and target in node_ids
            ],
        }

    @staticmethod
    def _ultima_sidecar_candidates(cram_key: str) -> tuple[str, str, str]:
        stem = str(cram_key or "")[:-5]
        return (f"{cram_key}.crai", f"{stem}.json", f"{stem}.csv")

    def import_run_prefix(
        self,
        *,
        root_uri: str,
        platform: str,
        owner_email: str,
        run_id: str | None = None,
        finalize: bool = False,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_platform = str(platform or "").strip().lower()
        if clean_platform not in SUPPORTED_RUN_PREFIX_PLATFORMS:
            raise ValueError(
                f"platform must be one of: {', '.join(sorted(SUPPORTED_RUN_PREFIX_PLATFORMS))}"
            )
        clean_owner_email = self._normalize_owner_email(owner_email)
        bucket, root_prefix, normalized_root_uri = self._normalize_s3_prefix_uri(root_uri)
        clean_run_id = str(run_id or "").strip().upper() or self._parse_run_id_from_prefix(
            root_prefix
        )
        if not clean_run_id:
            raise ValueError(
                "run_id could not be inferred from root_uri; provide run_id explicitly"
            )

        storage = self._require_storage()
        objects = storage.list_objects(bucket=bucket, prefix=root_prefix, limit=250000)
        if not objects:
            raise DeweyNotFoundError(f"No S3 objects found for prefix: {normalized_root_uri}")

        run_label = self._folder_label_from_prefix(root_prefix)
        observed_object_count = len(objects)
        observed_total_bytes = sum(int(item.size or 0) for item in objects)
        run_state = "frozen" if finalize else "live"
        request_payload = {
            "root_uri": normalized_root_uri,
            "platform": clean_platform,
            "owner_email": clean_owner_email,
            "run_id": clean_run_id,
            "finalize": bool(finalize),
            "observed_object_count": observed_object_count,
            "observed_total_bytes": observed_total_bytes,
        }
        fingerprint = self._fingerprint(request_payload)

        folders: dict[str, list[StorageObject]] = {}
        for obj in objects:
            relative_key = str(obj.key or "")[len(root_prefix) :]
            if not relative_key or "/" not in relative_key:
                continue
            folder_label = relative_key.split("/", 1)[0]
            folder_objects = folders.get(folder_label)
            if folder_objects is None:
                folder_objects = []
                folders[folder_label] = folder_objects
            folder_objects.append(obj)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.import_run_prefix",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

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
                producer_system=None,
                producer_object_euid=None,
                storage_class=None,
                availability_status="available",
                metadata={
                    "owner_email": clean_owner_email,
                    "platform": clean_platform,
                    "run_id": clean_run_id,
                    "tags": ["ultima", "run_folder"],
                    "node_label": run_label,
                    "run_state": run_state,
                    "observed_object_count": observed_object_count,
                    "observed_total_bytes": observed_total_bytes,
                },
                source_uri=normalized_root_uri,
                import_mode="register",
                storage_status="registered",
                storage_kind="prefix",
                node_kind="run_folder",
                is_terminal=False,
            )
            existing_run = self.backend.find_by_json_field(
                session,
                template_code=ARTIFACT_TEMPLATE,
                field="artifact_identity_key",
                value=str(run_payload.get("artifact_identity_key") or ""),
            )
            if existing_run is not None:
                existing_run_state = str(
                    normalize_instance_payload(existing_run).get("metadata", {}).get("run_state")
                    or ""
                ).strip()
                if existing_run_state == "frozen":
                    run_body = self._artifact_response(existing_run)
                    response = {
                        "run_artifact": run_body,
                        "folder_nodes": {"created": 0, "updated": 0},
                        "file_artifacts": {"created": 0, "updated": 0},
                        "run_state": "frozen",
                    }
                    self._store_idempotency(
                        session,
                        operation="artifact.import_run_prefix",
                        idempotency_key=idempotency_key,
                        fingerprint=fingerprint,
                        status_code=200,
                        response=response,
                    )
                    return 200, response

            run_status_code, run_body = self._upsert_artifact_record(
                session,
                payload=run_payload,
                created_at=utc_now_iso(),
                refresh_existing=True,
            )

            folder_created = 0
            folder_updated = 0
            file_created = 0
            file_updated = 0

            for folder_label in sorted(folders):
                folder_objects = folders[folder_label]
                folder_prefix = f"{root_prefix}{folder_label}/"
                object_map = {str(item.key): item for item in folder_objects}
                cram_keys = sorted(key for key in object_map if key.endswith(".cram"))
                selected_keys: set[str] = set()
                for cram_key in cram_keys:
                    selected_keys.add(cram_key)
                    for candidate in self._ultima_sidecar_candidates(cram_key):
                        if candidate in object_map:
                            selected_keys.add(candidate)
                has_unmaterialized_descendants = any(key not in selected_keys for key in object_map)
                seq_index = self._parse_seq_index(folder_label)
                folder_metadata = {
                    "owner_email": clean_owner_email,
                    "platform": clean_platform,
                    "run_id": clean_run_id,
                    "tags": ["ultima", "sample_folder"],
                    "folder_label": folder_label,
                    "run_root_uri": normalized_root_uri,
                    "is_terminal": not has_unmaterialized_descendants,
                }
                if seq_index:
                    folder_metadata["seq_index"] = seq_index
                folder_payload = self._artifact_payload(
                    artifact_type="folder",
                    storage_backend="s3",
                    bucket=bucket,
                    key=folder_prefix,
                    version_id=None,
                    size=sum(int(item.size or 0) for item in folder_objects),
                    checksums={},
                    content_type=None,
                    original_filename=folder_label,
                    producer_system=None,
                    producer_object_euid=None,
                    storage_class=None,
                    availability_status="available",
                    metadata=folder_metadata,
                    source_uri=f"s3://{bucket}/{folder_prefix}",
                    import_mode="register",
                    storage_status="registered",
                    storage_kind="prefix",
                    node_kind="sample_folder",
                    is_terminal=not has_unmaterialized_descendants,
                )
                folder_status_code, folder_body = self._upsert_artifact_record(
                    session,
                    payload=folder_payload,
                    created_at=utc_now_iso(),
                    refresh_existing=True,
                )
                if folder_status_code == 201:
                    folder_created += 1
                else:
                    folder_updated += 1
                self._create_artifact_lineage(
                    session,
                    parent_euid=run_body["artifact_euid"],
                    child_euid=folder_body["artifact_euid"],
                )

                for object_key in sorted(selected_keys):
                    storage_object = object_map[object_key]
                    file_payload = self._artifact_payload(
                        artifact_type=resolve_artifact_type(None, object_key),
                        storage_backend="s3",
                        bucket=bucket,
                        key=object_key,
                        version_id=storage_object.version_id,
                        size=storage_object.size,
                        checksums={},
                        content_type=storage_object.content_type,
                        original_filename=Path(object_key).name,
                        producer_system=None,
                        producer_object_euid=None,
                        storage_class=storage_object.storage_class,
                        availability_status="available",
                        metadata={
                            "owner_email": clean_owner_email,
                            "platform": clean_platform,
                            "run_id": clean_run_id,
                            "folder_label": folder_label,
                            "run_root_uri": normalized_root_uri,
                            "sample_folder_uri": f"s3://{bucket}/{folder_prefix}",
                            **({"seq_index": seq_index} if seq_index else {}),
                        },
                        source_uri=f"s3://{bucket}/{object_key}",
                        import_mode="reference",
                        storage_status="observed",
                        storage_verified_at=None,
                        storage_kind="object",
                        node_kind="file",
                        is_terminal=True,
                    )
                    file_status_code, file_body = self._upsert_artifact_record(
                        session,
                        payload=file_payload,
                        created_at=utc_now_iso(),
                        refresh_existing=True,
                    )
                    if file_status_code == 201:
                        file_created += 1
                        self._tag_artifact_object(
                            artifact_payload=file_payload,
                            artifact_euid=file_body["artifact_euid"],
                            tolerate_permission_errors=True,
                        )
                    else:
                        file_updated += 1
                    self._create_artifact_lineage(
                        session,
                        parent_euid=folder_body["artifact_euid"],
                        child_euid=file_body["artifact_euid"],
                    )

            status_code = 201 if run_status_code == 201 or folder_created or file_created else 200
            response = {
                "run_artifact": self.get_artifact(run_body["artifact_euid"]),
                "folder_nodes": {"created": folder_created, "updated": folder_updated},
                "file_artifacts": {"created": file_created, "updated": file_updated},
                "run_state": run_state,
            }
            self._store_idempotency(
                session,
                operation="artifact.import_run_prefix",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=response,
            )
            return status_code, response

    def register_artifact_prefix(
        self,
        *,
        root_uri: str,
        artifact_type: str,
        producer_system: str | None = None,
        producer_object_euid: str | None = None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        bucket, prefix, normalized_root_uri = self._normalize_s3_prefix_uri(root_uri)
        prefix_label = self._folder_label_from_prefix(prefix)
        meta = dict(metadata or {})
        payload = self._artifact_payload(
            artifact_type=artifact_type,
            storage_backend="s3",
            bucket=bucket,
            key=prefix,
            version_id=None,
            size=None,
            checksums={},
            content_type=None,
            original_filename=prefix_label,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            storage_class=None,
            availability_status=str(meta.get("availability_status") or "").strip()
            or "available",
            metadata=meta,
            source_uri=normalized_root_uri,
            import_mode="register",
            storage_status="registered",
            storage_kind="prefix",
            node_kind="prefix",
            is_terminal=False,
        )
        fingerprint = self._fingerprint(
            {
                "root_uri": normalized_root_uri,
                "artifact_type": payload["artifact_type"],
                "producer_system": payload["producer_system"],
                "producer_object_euid": payload["producer_object_euid"],
                "metadata": payload["metadata"],
            }
        )

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="artifact.register_prefix",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            status_code, body = self._upsert_artifact_record(
                session,
                payload=payload,
                created_at=utc_now_iso(),
            )
            self._store_idempotency(
                session,
                operation="artifact.register_prefix",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

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
    ) -> tuple[int, dict[str, Any]]:
        source_value = str(source_uri or storage_uri or "").strip()
        if not source_value:
            raise ValueError("source_uri is required")

        mode = str(import_mode or "").strip().lower() or "reference"
        if mode not in {"copy", "reference"}:
            raise ValueError("import_mode must be copy or reference")

        meta = dict(metadata or {})
        clean_producer_system = (
            str(producer_system or meta.get("producer_system") or "").strip() or None
        )
        clean_producer_euid = (
            str(producer_object_euid or meta.get("producer_object_euid") or "").strip() or None
        )
        original_filename = self._source_filename(
            source_value,
            str(meta.get("original_filename") or "").strip() or None,
        )
        resolved_artifact_type = resolve_artifact_type(
            artifact_type, original_filename, source_value
        )
        payload = {
            "artifact_type": resolved_artifact_type,
            "source_uri": source_value,
            "import_mode": mode,
            "lock_after_import": bool(lock_after_import),
            "producer_system": clean_producer_system,
            "producer_object_euid": clean_producer_euid,
            "metadata": meta,
        }
        fingerprint = self._fingerprint(payload)
        parsed = urlparse(source_value)
        scheme = str(parsed.scheme or "").strip().lower()
        if scheme not in {"s3", "https", "http"}:
            raise ValueError("source_uri must use s3:// or https://")
        if mode == "reference" and scheme != "s3":
            raise ValueError("reference import requires an s3:// source_uri")

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.import",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            now_iso = utc_now_iso()
            storage = self._require_storage()

            if mode == "reference":
                source_bucket, source_key = self._parse_s3_uri(source_value)
                source_object = storage.head_object(bucket=source_bucket, key=source_key)
                artifact_payload = self._artifact_payload(
                    artifact_type=payload["artifact_type"],
                    storage_backend="s3",
                    bucket=source_bucket,
                    key=source_key,
                    version_id=source_object.version_id,
                    size=meta.get("size") or source_object.size,
                    checksums=dict(meta.get("checksums") or {}),
                    content_type=(
                        str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                        or source_object.content_type
                    ),
                    original_filename=original_filename,
                    producer_system=clean_producer_system,
                    producer_object_euid=clean_producer_euid,
                    storage_class=str(meta.get("storage_class") or "").strip()
                    or source_object.storage_class,
                    availability_status=str(meta.get("availability_status") or "").strip()
                    or "available",
                    metadata=meta,
                    source_uri=source_value,
                    import_mode="reference",
                    storage_status="verified",
                    storage_verified_at=now_iso,
                )
                status_code, body = self._upsert_artifact_record(
                    session,
                    payload=artifact_payload,
                    created_at=now_iso,
                )
                if status_code == 201:
                    self._tag_artifact_object(
                        artifact_payload=artifact_payload,
                        artifact_euid=body["artifact_euid"],
                        tolerate_permission_errors=True,
                    )
                if lock_after_import:
                    artifact = self.backend.find_by_euid(
                        session,
                        template_code=ARTIFACT_TEMPLATE,
                        euid=body["artifact_euid"],
                        for_update=True,
                    )
                    if artifact is None:
                        raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                    retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                    self._lock_artifact_payload(
                        artifact_payload=artifact_payload,
                        mode="GOVERNANCE",
                        retain_until=retain_until,
                    )
                    self.backend.update_instance_json(
                        session,
                        artifact,
                        {
                            "retention_mode": "GOVERNANCE",
                            "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                        },
                    )
                    body = self._artifact_response(artifact)
                self._store_idempotency(
                    session,
                    operation="artifact.import",
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    status_code=status_code,
                    response=body,
                )
                return status_code, body

            if not self.managed_storage_bucket:
                raise ValueError("managed_storage_bucket is required for copy imports")

            dest_key = self._managed_key(
                namespace="imports",
                seed=f"{payload['artifact_type']}:{source_value}",
                filename=original_filename,
            )
            try:
                dest_object = storage.head_object(
                    bucket=self.managed_storage_bucket,
                    key=dest_key,
                )
            except StorageObjectNotFoundError:
                if scheme == "s3":
                    source_bucket, source_key = self._parse_s3_uri(source_value)
                    storage.head_object(bucket=source_bucket, key=source_key)
                    dest_object = storage.copy_object(
                        source_bucket=source_bucket,
                        source_key=source_key,
                        dest_bucket=self.managed_storage_bucket,
                        dest_key=dest_key,
                    )
                else:
                    response = requests.get(source_value, timeout=60)
                    response.raise_for_status()
                    dest_object = storage.put_bytes(
                        bucket=self.managed_storage_bucket,
                        key=dest_key,
                        body=response.content,
                        content_type=(
                            str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                            or str(response.headers.get("content-type") or "").strip()
                            or None
                        ),
                    )

            artifact_payload = self._artifact_payload(
                artifact_type=payload["artifact_type"],
                storage_backend="s3",
                bucket=self.managed_storage_bucket,
                key=dest_key,
                version_id=dest_object.version_id,
                size=meta.get("size") or dest_object.size,
                checksums=dict(meta.get("checksums") or {}),
                content_type=(
                    str(meta.get("content_type") or meta.get("mime_type") or "").strip()
                    or dest_object.content_type
                ),
                original_filename=original_filename,
                producer_system=clean_producer_system,
                producer_object_euid=clean_producer_euid,
                storage_class=str(meta.get("storage_class") or "").strip()
                or dest_object.storage_class,
                availability_status=str(meta.get("availability_status") or "").strip()
                or "available",
                metadata=meta,
                source_uri=source_value,
                import_mode="copy",
                storage_status="verified",
                storage_verified_at=now_iso,
            )
            status_code, body = self._upsert_artifact_record(
                session,
                payload=artifact_payload,
                created_at=now_iso,
            )
            if status_code == 201:
                self._tag_artifact_object(
                    artifact_payload=artifact_payload,
                    artifact_euid=body["artifact_euid"],
                )
            if lock_after_import:
                artifact = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=body["artifact_euid"],
                    for_update=True,
                )
                if artifact is None:
                    raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                self._lock_artifact_payload(
                    artifact_payload=artifact_payload,
                    mode="GOVERNANCE",
                    retain_until=retain_until,
                )
                self.backend.update_instance_json(
                    session,
                    artifact,
                    {
                        "retention_mode": "GOVERNANCE",
                        "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                    },
                )
                body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.import",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

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
    ) -> tuple[int, dict[str, Any]]:
        if not self.managed_storage_bucket:
            raise ValueError("managed_storage_bucket is required for upload sessions")
        clean_type = resolve_artifact_type(artifact_type, original_filename)
        clean_filename = self._safe_filename(original_filename)
        payload = {
            "artifact_type": clean_type,
            "original_filename": clean_filename,
            "content_type": str(content_type or "").strip() or None,
            "producer_system": str(producer_system or "").strip() or None,
            "producer_object_euid": str(producer_object_euid or "").strip() or None,
            "metadata": dict(metadata or {}),
            "lock_after_import": bool(lock_after_import),
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.upload_session.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            storage = self._require_storage()
            key = self._managed_key(
                namespace="uploads",
                seed=f"{idempotency_key}:{fingerprint}",
                filename=clean_filename,
            )
            upload = storage.generate_presigned_upload(
                bucket=self.managed_storage_bucket,
                key=key,
                expires_in=self.upload_session_ttl_seconds,
                content_type=payload["content_type"],
            )
            token = self._upload_serializer.dumps(
                {
                    **payload,
                    "bucket": self.managed_storage_bucket,
                    "key": key,
                    "storage_uri": self._storage_uri("s3", self.managed_storage_bucket, key),
                }
            )
            body = {
                "upload_token": token,
                "upload_method": upload["method"],
                "upload_url": upload["url"],
                "upload_headers": upload["headers"],
                "bucket": self.managed_storage_bucket,
                "key": key,
                "storage_uri": self._storage_uri("s3", self.managed_storage_bucket, key),
                "expires_in": self.upload_session_ttl_seconds,
                "created_at": utc_now_iso(),
            }
            self._store_idempotency(
                session,
                operation="artifact.upload_session.create",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=201,
                response=body,
            )
            return 201, body

    def complete_upload_session(
        self,
        *,
        upload_token: str,
        checksums: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        try:
            token_payload = self._upload_serializer.loads(
                str(upload_token or "").strip(),
                max_age=self.upload_session_ttl_seconds,
            )
        except SignatureExpired as exc:
            raise ValueError("upload_token has expired") from exc
        except BadSignature as exc:
            raise ValueError("upload_token is invalid") from exc

        if not isinstance(token_payload, dict):
            raise ValueError("upload_token is invalid")

        merged_metadata = dict(token_payload.get("metadata") or {})
        merged_metadata.update(dict(metadata or {}))
        payload = {
            "upload_token": str(upload_token or "").strip(),
            "checksums": dict(checksums or {}),
            "metadata": merged_metadata,
        }
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.upload_session.complete",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            storage = self._require_storage()
            try:
                obj = storage.head_object(
                    bucket=str(token_payload.get("bucket") or "").strip(),
                    key=str(token_payload.get("key") or "").strip(),
                )
            except StorageObjectNotFoundError as exc:
                raise DeweyNotFoundError("Uploaded object not found") from exc

            now_iso = utc_now_iso()
            artifact_payload = self._artifact_payload(
                artifact_type=str(token_payload.get("artifact_type") or ""),
                storage_backend="s3",
                bucket=str(token_payload.get("bucket") or "").strip(),
                key=str(token_payload.get("key") or "").strip(),
                version_id=obj.version_id,
                size=obj.size,
                checksums=dict(checksums or {}),
                content_type=(
                    str(
                        merged_metadata.get("content_type")
                        or merged_metadata.get("mime_type")
                        or ""
                    ).strip()
                    or str(token_payload.get("content_type") or "").strip()
                    or obj.content_type
                ),
                original_filename=str(token_payload.get("original_filename") or "").strip() or None,
                producer_system=str(token_payload.get("producer_system") or "").strip() or None,
                producer_object_euid=str(token_payload.get("producer_object_euid") or "").strip()
                or None,
                storage_class=obj.storage_class,
                availability_status="available",
                metadata=merged_metadata,
                source_uri=str(token_payload.get("storage_uri") or "").strip() or None,
                import_mode="upload",
                storage_status="verified",
                storage_verified_at=now_iso,
            )
            status_code, body = self._upsert_artifact_record(
                session,
                payload=artifact_payload,
                created_at=now_iso,
            )
            if status_code == 201:
                self._tag_artifact_object(
                    artifact_payload=artifact_payload,
                    artifact_euid=body["artifact_euid"],
                )
            if bool(token_payload.get("lock_after_import")):
                artifact = self.backend.find_by_euid(
                    session,
                    template_code=ARTIFACT_TEMPLATE,
                    euid=body["artifact_euid"],
                    for_update=True,
                )
                if artifact is None:
                    raise DeweyNotFoundError(f"Artifact not found: {body['artifact_euid']}")
                retain_until = datetime.now(timezone.utc) + timedelta(days=36500)
                self._lock_artifact_payload(
                    artifact_payload=artifact_payload,
                    mode="GOVERNANCE",
                    retain_until=retain_until,
                )
                self.backend.update_instance_json(
                    session,
                    artifact,
                    {
                        "retention_mode": "GOVERNANCE",
                        "retain_until": retain_until.isoformat().replace("+00:00", "Z"),
                    },
                )
                body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.upload_session.complete",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

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
    ) -> tuple[int, dict[str, Any]]:
        _, upload = self.create_upload_session(
            artifact_type=artifact_type,
            original_filename=original_filename,
            content_type=content_type,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            metadata=metadata,
            lock_after_import=lock_after_import,
            idempotency_key=f"{idempotency_key}:create",
        )
        self._require_storage().put_bytes(
            bucket=str(upload.get("bucket") or ""),
            key=str(upload.get("key") or ""),
            body=body,
            content_type=content_type,
        )
        return self.complete_upload_session(
            upload_token=str(upload.get("upload_token") or ""),
            checksums=checksums,
            metadata=metadata,
            idempotency_key=f"{idempotency_key}:complete",
        )

    def register_artifact(
        self,
        *,
        artifact_type: str,
        storage_backend: str,
        bucket: str,
        key: str,
        version_id: str | None,
        size: int | None,
        checksums: dict[str, Any] | None,
        content_type: str | None,
        original_filename: str | None,
        producer_system: str | None,
        producer_object_euid: str | None,
        storage_class: str | None,
        availability_status: str | None,
        metadata: dict[str, Any] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = self._artifact_payload(
            artifact_type=artifact_type,
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=version_id,
            size=size,
            checksums=checksums,
            content_type=content_type,
            original_filename=original_filename,
            producer_system=producer_system,
            producer_object_euid=producer_object_euid,
            storage_class=storage_class,
            availability_status=availability_status,
            metadata=metadata,
            source_uri=self._storage_uri(
                str(storage_backend or "s3").strip().lower() or "s3",
                str(bucket or "").strip(),
                str(key or "").strip().lstrip("/"),
            ),
            import_mode="register",
            storage_status="registered",
        )
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            self.backend.ensure_templates(session)
            replay = self._idempotency_replay(
                session,
                operation="artifact.register",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            status_code, body = self._upsert_artifact_record(
                session,
                payload=payload,
                created_at=utc_now_iso(),
            )
            self._store_idempotency(
                session,
                operation="artifact.register",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def get_artifact(self, artifact_euid: str) -> dict[str, Any]:
        with self.backend.session_scope(commit=False) as session:
            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=str(artifact_euid or "").strip(),
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {artifact_euid}")
            return self._artifact_response(artifact)

    def list_artifacts(
        self,
        *,
        artifact_type: str | None = None,
        producer_system: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clean_type = str(artifact_type or "").strip().lower()
        clean_producer = str(producer_system or "").strip().lower()
        with self.backend.session_scope(commit=False) as session:
            items = self.backend.list_by_template(
                session,
                template_code=ARTIFACT_TEMPLATE,
                limit=max(1, min(limit, 2000)),
            )
            rows: list[dict[str, Any]] = []
            for item in items:
                payload = normalize_instance_payload(item)
                if clean_type and str(payload.get("artifact_type") or "").lower() != clean_type:
                    continue
                if (
                    clean_producer
                    and str(payload.get("producer_system") or "").lower() != clean_producer
                ):
                    continue
                rows.append(self._artifact_response(item))
            return rows

    def verify_artifact_storage(
        self,
        *,
        artifact_euid: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {"artifact_euid": str(artifact_euid or "").strip()}
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.storage.verify",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
                for_update=True,
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            artifact_payload = normalize_instance_payload(artifact)
            if not self._artifact_is_object(artifact_payload):
                raise ValueError("storage verification requires an object-backed artifact")
            storage = self._require_storage()
            status_code = 200
            try:
                obj = storage.head_object(
                    bucket=str(artifact_payload.get("bucket") or ""),
                    key=str(artifact_payload.get("key") or ""),
                    version_id=str(artifact_payload.get("version_id") or "").strip() or None,
                )
                updates = {
                    **self._object_updates(obj),
                    "storage_status": "verified",
                    "storage_verified_at": utc_now_iso(),
                }
            except StorageObjectNotFoundError:
                updates = {
                    "availability_status": "missing",
                    "storage_status": "missing",
                    "storage_verified_at": utc_now_iso(),
                }
            self.backend.update_instance_json(session, artifact, updates)
            body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.storage.verify",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def lock_artifact_storage(
        self,
        *,
        artifact_euid: str,
        mode: str,
        retain_until: str,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "artifact_euid": str(artifact_euid or "").strip(),
            "mode": str(mode or "GOVERNANCE").strip().upper() or "GOVERNANCE",
            "retain_until": str(retain_until or "").strip(),
        }
        if not payload["artifact_euid"]:
            raise ValueError("artifact_euid is required")
        retain_until_dt = self._parse_iso8601(payload["retain_until"], field_name="retain_until")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="artifact.storage.lock",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            artifact = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=payload["artifact_euid"],
                for_update=True,
            )
            if artifact is None:
                raise DeweyNotFoundError(f"Artifact not found: {payload['artifact_euid']}")

            artifact_payload = normalize_instance_payload(artifact)
            if not self._artifact_is_object(artifact_payload):
                raise ValueError("storage lock requires an object-backed artifact")
            self._lock_artifact_payload(
                artifact_payload=artifact_payload,
                mode=payload["mode"],
                retain_until=retain_until_dt,
            )
            self.backend.update_instance_json(
                session,
                artifact,
                {
                    "retention_mode": payload["mode"],
                    "retain_until": retain_until_dt.isoformat().replace("+00:00", "Z"),
                },
            )
            body = self._artifact_response(artifact)
            self._store_idempotency(
                session,
                operation="artifact.storage.lock",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body
