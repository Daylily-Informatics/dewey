"""Literature search and save workflows for Dewey service."""

from __future__ import annotations

from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import requests

from dewey_service.literature import (
    LiteratureUnavailableError,
    ViewerContext,
    classify_fulltext,
    dedupe_strings,
    normalize_doi,
    normalize_email_list,
    normalize_group_list,
    normalize_pmcid,
    normalize_pmid,
)
from dewey_service.services.base import DeweyConflictError, DeweyNotFoundError
from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    LITERATURE_SAVE_TEMPLATE,
    normalize_instance_payload,
    utc_now_iso,
)


class LiteratureServiceMixin:
    def search_literature(
        self,
        *,
        viewer: ViewerContext,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        adapter = self._require_literature()
        started = perf_counter()
        try:
            raw_items = adapter.search(query=query, page=page, page_size=page_size)
        except LiteratureUnavailableError:
            raise
        except Exception as exc:
            raise LiteratureUnavailableError(
                "Literature search is unavailable. Verify the Dewey container can read its "
                "metapub/NCBI configuration, including the staged NCBI API key."
            ) from exc
        with self.backend.session_scope(commit=False) as session:
            items = [
                self._enrich_literature_search_item(
                    session,
                    record=item,
                    viewer=viewer,
                )
                for item in raw_items
            ]
        timing_ms = int((perf_counter() - started) * 1000)
        return {
            "items": items,
            "total": len(items),
            "page": max(1, int(page)),
            "page_size": max(1, int(page_size)),
            "has_more": len(items) >= max(1, int(page_size)),
            "timing_ms": timing_ms,
        }

    def save_literature(
        self,
        *,
        viewer: ViewerContext,
        pmid: str,
        save_mode: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        clean_mode = str(save_mode or "").strip().lower() or "auto"
        if clean_mode not in {"auto", "managed_artifact", "external_reference"}:
            raise ValueError("save_mode must be auto, managed_artifact, or external_reference")
        visibility = self._normalize_literature_visibility(
            visibility_scope=visibility_scope,
            allowed_users=allowed_users,
            allowed_groups=allowed_groups,
        )
        clean_pmid = normalize_pmid(pmid)
        fingerprint_payload = {
            "viewer_subject": viewer.subject,
            "pmid": clean_pmid,
            "save_mode": clean_mode,
            **visibility,
        }
        fingerprint = self._fingerprint(fingerprint_payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="literature.save",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            adapter = self._require_literature()
            record = adapter.fetch_record(clean_pmid)
            artifact_status_code, artifact = self._create_or_update_literature_artifact(
                session,
                record=record,
                save_mode=clean_mode,
            )
            artifact_instance = self.backend.find_by_euid(
                session,
                template_code=ARTIFACT_TEMPLATE,
                euid=artifact["artifact_euid"],
                for_update=True,
            )
            if artifact_instance is None:
                raise DeweyNotFoundError(f"Artifact not found: {artifact['artifact_euid']}")

            self._ensure_literature_external_identities(
                session,
                artifact_instance=artifact_instance,
                record=record,
            )
            save_status_code, literature_save = self._upsert_literature_save(
                session,
                artifact_instance=artifact_instance,
                viewer=viewer,
                visibility=visibility,
            )
            body = {
                "artifact": self._artifact_response(artifact_instance),
                "literature_save": literature_save,
            }
            status_code = 201 if artifact_status_code == 201 or save_status_code == 201 else 200
            self._store_idempotency(
                session,
                operation="literature.save",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=status_code,
                response=body,
            )
            return status_code, body

    def update_literature_save_visibility(
        self,
        *,
        viewer: ViewerContext,
        literature_save_euid: str,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
        idempotency_key: str,
    ) -> tuple[int, dict[str, Any]]:
        visibility = self._normalize_literature_visibility(
            visibility_scope=visibility_scope,
            allowed_users=allowed_users,
            allowed_groups=allowed_groups,
        )
        payload = {
            "viewer_subject": viewer.subject,
            "literature_save_euid": str(literature_save_euid or "").strip(),
            **visibility,
        }
        if not payload["literature_save_euid"]:
            raise ValueError("literature_save_euid is required")
        fingerprint = self._fingerprint(payload)

        with self.backend.session_scope(commit=True) as session:
            replay = self._idempotency_replay(
                session,
                operation="literature.save.visibility.update",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if replay is not None:
                return replay.status_code, replay.response

            instance = self.backend.find_by_euid(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                euid=payload["literature_save_euid"],
                for_update=True,
            )
            if instance is None:
                raise DeweyNotFoundError(
                    f"Literature save not found: {payload['literature_save_euid']}"
                )

            existing_payload = normalize_instance_payload(instance)
            if str(existing_payload.get("owner_subject") or "") != viewer.subject:
                raise DeweyConflictError("Only the owner can update literature save visibility")

            self.backend.update_instance_json(
                session,
                instance,
                {
                    **visibility,
                    "updated_at": utc_now_iso(),
                },
            )
            body = self._literature_save_response(session, instance)
            self._store_idempotency(
                session,
                operation="literature.save.visibility.update",
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                status_code=200,
                response=body,
            )
            return 200, body

    def list_my_literature_saves(
        self,
        *,
        viewer: ViewerContext,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        with self.backend.session_scope(commit=False) as session:
            rows = self.backend.list_by_template(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                limit=max(1, min(int(limit), 2000)),
            )
            return [
                self._literature_save_response(session, row)
                for row in rows
                if str(normalize_instance_payload(row).get("owner_subject") or "") == viewer.subject
            ]

    def _normalize_literature_visibility(
        self,
        *,
        visibility_scope: str,
        allowed_users: list[str] | None,
        allowed_groups: list[str] | None,
    ) -> dict[str, Any]:
        clean_scope = str(visibility_scope or "").strip().lower() or "private"
        if clean_scope not in {"private", "restricted", "all_users"}:
            raise ValueError("visibility_scope must be private, restricted, or all_users")
        if clean_scope == "private":
            return {
                "visibility_scope": "private",
                "allowed_users": [],
                "allowed_groups": [],
            }
        if clean_scope == "all_users":
            return {
                "visibility_scope": "all_users",
                "allowed_users": [],
                "allowed_groups": [],
            }
        return {
            "visibility_scope": "restricted",
            "allowed_users": normalize_email_list(allowed_users),
            "allowed_groups": normalize_group_list(allowed_groups),
        }

    def _enrich_literature_search_item(
        self,
        session,
        *,
        record: dict[str, Any],
        viewer: ViewerContext,
    ) -> dict[str, Any]:
        artifact = self._resolve_literature_artifact(
            session,
            pmid=record.get("pmid"),
            doi=record.get("doi"),
            pmcid=record.get("pmcid"),
        )
        visibility = {
            "saved_by_me": False,
            "saved_by_others_count": 0,
            "visible_owner_labels": [],
        }
        artifact_euid = None
        storage_mode = "external_reference"
        if artifact is not None:
            artifact_payload = self._artifact_response(artifact)
            artifact_euid = artifact.euid
            metadata = dict(artifact_payload.get("metadata") or {})
            storage_mode = str(metadata.get("storage_mode") or "external_reference")
            visibility = self._visible_literature_save_summary(session, artifact, viewer)
        fulltext = classify_fulltext(
            best_fulltext_url=record.get("best_fulltext_url"),
            findit_reason=record.get("findit_reason"),
            allowed_domains=self.literature_allowed_domains,
        )
        if artifact is None:
            storage_mode = "managed" if fulltext["downloadable"] else "external_reference"
        return {
            **record,
            **fulltext,
            "storage_mode": storage_mode,
            "artifact_euid": artifact_euid,
            "already_in_dewey": artifact is not None,
            **visibility,
        }

    def _create_or_update_literature_artifact(
        self,
        session,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> tuple[int, dict[str, Any]]:
        existing = self._resolve_literature_artifact(
            session,
            pmid=record.get("pmid"),
            doi=record.get("doi"),
            pmcid=record.get("pmcid"),
        )
        desired = self._determine_literature_storage(record=record, save_mode=save_mode)
        if desired["storage_mode"] == "managed":
            try:
                managed = self._download_managed_literature_pdf(record)
            except Exception:
                payload = self._literature_external_artifact_payload(
                    record=record,
                    save_mode=save_mode,
                )
            else:
                payload = self._literature_managed_artifact_payload(
                    record=record,
                    save_mode=save_mode,
                    managed=managed,
                )
        else:
            payload = self._literature_external_artifact_payload(record=record, save_mode=save_mode)

        if existing is None:
            artifact = self.backend.create_instance(
                session,
                template_code=ARTIFACT_TEMPLATE,
                name=f"literature:{record['pmid']}",
                json_addl={
                    **payload,
                    "created_at": utc_now_iso(),
                },
            )
            if payload["storage_backend"] == "s3":
                self._tag_artifact_object(
                    artifact_payload=payload,
                    artifact_euid=artifact.euid,
                )
            return 201, self._artifact_response(artifact)

        current = normalize_instance_payload(existing)
        current_metadata = dict(current.get("metadata") or {})
        if (
            str(current_metadata.get("storage_mode") or "") == "managed"
            and str(dict(payload.get("metadata") or {}).get("storage_mode") or "") != "managed"
        ):
            payload = {
                **payload,
                "storage_backend": str(
                    current.get("storage_backend") or payload.get("storage_backend") or ""
                ),
                "bucket": str(current.get("bucket") or payload.get("bucket") or ""),
                "key": str(current.get("key") or payload.get("key") or ""),
                "version_id": current.get("version_id"),
                "size": current.get("size"),
                "content_type": current.get("content_type"),
                "storage_class": current.get("storage_class"),
                "availability_status": current.get("availability_status"),
                "storage_uri": current.get("storage_uri"),
                "source_uri": current.get("source_uri"),
                "import_mode": current.get("import_mode"),
                "storage_status": current.get("storage_status"),
                "storage_verified_at": current.get("storage_verified_at"),
                "metadata": {
                    **dict(payload.get("metadata") or {}),
                    "storage_mode": "managed",
                    "fulltext_status": "downloadable",
                    "best_fulltext_url": current_metadata.get("best_fulltext_url")
                    or dict(payload.get("metadata") or {}).get("best_fulltext_url"),
                },
            }
        updates = dict(current)
        updates.update(payload)
        updates["updated_at"] = utc_now_iso()
        self.backend.update_instance_json(session, existing, updates)
        if payload["storage_backend"] == "s3":
            self._tag_artifact_object(
                artifact_payload=payload,
                artifact_euid=existing.euid,
            )
        return 200, self._artifact_response(existing)

    def _determine_literature_storage(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> dict[str, str]:
        fulltext = classify_fulltext(
            best_fulltext_url=record.get("best_fulltext_url"),
            findit_reason=record.get("findit_reason"),
            allowed_domains=self.literature_allowed_domains,
        )
        if save_mode == "external_reference":
            return {
                "storage_mode": "external_reference",
                "fulltext_status": fulltext["fulltext_status"],
            }
        if fulltext["downloadable"] and self.managed_storage_bucket:
            return {"storage_mode": "managed", "fulltext_status": "downloadable"}
        return {
            "storage_mode": "external_reference",
            "fulltext_status": "external_link_only"
            if fulltext["external_link_only"]
            else "unavailable",
        }

    def _literature_external_artifact_payload(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
    ) -> dict[str, Any]:
        landing_url = self._literature_landing_url(record)
        storage_backend, bucket, key = self._external_url_storage_parts(landing_url)
        return self._artifact_payload(
            artifact_type="literature",
            storage_backend=storage_backend,
            bucket=bucket,
            key=key,
            version_id=None,
            size=None,
            checksums=None,
            content_type=None,
            original_filename=str(record.get("title") or "").strip() or None,
            producer_system="pubmed",
            producer_object_euid=str(record.get("pmid") or ""),
            storage_class=None,
            availability_status="external_only",
            metadata=self._literature_metadata(
                record=record,
                storage_mode="external_reference",
                acquisition_mode=save_mode,
                fulltext_status=self._determine_literature_storage(
                    record=record,
                    save_mode=save_mode,
                )["fulltext_status"],
            ),
            source_uri=landing_url,
            import_mode="reference",
            storage_status="registered",
            artifact_identity_key=f"literature:pmid:{record['pmid']}",
        )

    def _literature_managed_artifact_payload(
        self,
        *,
        record: dict[str, Any],
        save_mode: str,
        managed: dict[str, Any],
    ) -> dict[str, Any]:
        obj = managed["storage_object"]
        return self._artifact_payload(
            artifact_type="literature",
            storage_backend="s3",
            bucket=str(obj.bucket or ""),
            key=str(obj.key or ""),
            version_id=obj.version_id,
            size=obj.size,
            checksums=None,
            content_type=obj.content_type or "application/pdf",
            original_filename=f"pmid-{record['pmid']}.pdf",
            producer_system="pubmed",
            producer_object_euid=str(record.get("pmid") or ""),
            storage_class=obj.storage_class,
            availability_status="available",
            metadata=self._literature_metadata(
                record=record,
                storage_mode="managed",
                acquisition_mode=save_mode,
                fulltext_status="downloadable",
            ),
            source_uri=str(record.get("best_fulltext_url") or self._literature_landing_url(record)),
            import_mode="copy",
            storage_status="verified",
            storage_verified_at=utc_now_iso(),
            artifact_identity_key=f"literature:pmid:{record['pmid']}",
        )

    def _literature_metadata(
        self,
        *,
        record: dict[str, Any],
        storage_mode: str,
        acquisition_mode: str,
        fulltext_status: str,
    ) -> dict[str, Any]:
        return {
            "record_family": "literature",
            "title": str(record.get("title") or "").strip(),
            "authors": list(record.get("authors") or []),
            "journal": record.get("journal"),
            "year": record.get("year"),
            "abstract": record.get("abstract"),
            "abstract_snippet": record.get("abstract_snippet"),
            "pmid": str(record.get("pmid") or ""),
            "doi": normalize_doi(record.get("doi")),
            "pmcid": normalize_pmcid(record.get("pmcid")),
            "source_urls": dedupe_strings(list(record.get("source_urls") or [])),
            "best_fulltext_url": record.get("best_fulltext_url"),
            "findit_reason": record.get("findit_reason"),
            "storage_mode": storage_mode,
            "acquisition_mode": acquisition_mode,
            "fulltext_status": fulltext_status,
        }

    def _literature_landing_url(self, record: dict[str, Any]) -> str:
        return (
            str(record.get("best_fulltext_url") or "").strip()
            or next(
                (item for item in list(record.get("source_urls") or []) if str(item or "").strip()),
                "",
            )
            or f"https://pubmed.ncbi.nlm.nih.gov/{record['pmid']}/"
        )

    def _external_url_storage_parts(self, url: str) -> tuple[str, str, str]:
        parsed = urlparse(str(url or "").strip())
        backend = str(parsed.scheme or "https").strip().lower() or "https"
        bucket = str(parsed.netloc or "").strip()
        path = str(parsed.path or "").strip().lstrip("/")
        if parsed.query:
            path = f"{path}?{parsed.query}" if path else f"landing?{parsed.query}"
        key = path or "landing"
        if backend not in {"http", "https"}:
            raise ValueError("literature external URLs must use http or https")
        if not bucket:
            raise ValueError("literature landing URL must include a host")
        return backend, bucket, key

    def _download_managed_literature_pdf(self, record: dict[str, Any]) -> dict[str, Any]:
        if not self.managed_storage_bucket:
            raise ValueError("managed_storage_bucket is required for managed literature copies")
        source_url = str(record.get("best_fulltext_url") or "").strip()
        if not source_url:
            raise ValueError("Managed literature save requires a verified fulltext URL")
        response = requests.get(source_url, timeout=self.literature_request_timeout_seconds)
        response.raise_for_status()
        body = response.content
        content_type = str(response.headers.get("content-type") or "").strip().lower()
        if not body.startswith(b"%PDF-"):
            raise ValueError("Managed literature save requires a PDF response body")
        key = self._managed_key(
            namespace="literature",
            seed=f"pmid:{record['pmid']}",
            filename=f"pmid-{record['pmid']}.pdf",
        )
        storage = self._require_storage()
        obj = storage.put_bytes(
            bucket=self.managed_storage_bucket,
            key=key,
            body=body,
            content_type="application/pdf" if "pdf" not in content_type else content_type,
        )
        return {"storage_object": obj}

    def _ensure_literature_external_identities(
        self,
        session,
        *,
        artifact_instance,
        record: dict[str, Any],
    ) -> None:
        for external_system, external_type, external_id in [
            ("pubmed", "pmid", record.get("pmid")),
            ("pubmedcentral", "pmcid", record.get("pmcid")),
            ("doi", "doi", record.get("doi")),
        ]:
            clean_id = str(external_id or "").strip()
            if not clean_id:
                continue
            external = self._find_or_create_external_object(
                session,
                external_system=external_system,
                external_object_type=external_type,
                external_object_id=clean_id,
                external_uri=self._external_identity_uri(
                    external_system=external_system,
                    external_id=clean_id,
                ),
            )
            self._ensure_external_object_relation(
                session,
                artifact_instance=artifact_instance,
                external_object=external,
                relation_type="source_record",
            )

    def _external_identity_uri(self, *, external_system: str, external_id: str) -> str | None:
        if external_system == "pubmed":
            return f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/"
        if external_system == "pubmedcentral":
            return f"https://pmc.ncbi.nlm.nih.gov/articles/{external_id}/"
        if external_system == "doi":
            return f"https://doi.org/{external_id}"
        return None

    def _resolve_literature_artifact(
        self,
        session,
        *,
        pmid: str | None,
        doi: str | None,
        pmcid: str | None,
    ):
        normalized_pmid = normalize_pmid(pmid) if str(pmid or "").strip() else None
        for external_system, external_type, external_id in [
            ("pubmed", "pmid", normalized_pmid),
            ("pubmedcentral", "pmcid", normalize_pmcid(pmcid)),
            ("doi", "doi", normalize_doi(doi)),
        ]:
            if not external_id:
                continue
            artifact = self._find_artifact_by_external_identity(
                session,
                external_system=external_system,
                external_object_type=external_type,
                external_object_id=external_id,
            )
            if artifact is not None:
                return artifact
        if normalized_pmid:
            return self.backend.find_by_json_field(
                session,
                template_code=ARTIFACT_TEMPLATE,
                field="artifact_identity_key",
                value=f"literature:pmid:{normalized_pmid}",
            )
        return None

    def _upsert_literature_save(
        self,
        session,
        *,
        artifact_instance,
        viewer: ViewerContext,
        visibility: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        identity_key = f"{artifact_instance.euid}:{viewer.subject}"
        existing = self.backend.find_by_json_field(
            session,
            template_code=LITERATURE_SAVE_TEMPLATE,
            field="literature_save_identity_key",
            value=identity_key,
        )
        if existing is None:
            instance = self.backend.create_instance(
                session,
                template_code=LITERATURE_SAVE_TEMPLATE,
                name=identity_key,
                json_addl={
                    "artifact_euid": artifact_instance.euid,
                    "owner_subject": viewer.subject,
                    "owner_email": viewer.email,
                    "owner_label": viewer.owner_label,
                    **visibility,
                    "literature_save_identity_key": identity_key,
                    "created_at": utc_now_iso(),
                    "updated_at": utc_now_iso(),
                },
            )
            self.backend.create_lineage(
                session,
                parent=artifact_instance,
                child=instance,
                relationship_type="has_literature_save",
            )
            return 201, self._literature_save_response(session, instance)
        self.backend.update_instance_json(
            session,
            existing,
            {
                **visibility,
                "owner_email": viewer.email,
                "owner_label": viewer.owner_label,
                "updated_at": utc_now_iso(),
            },
        )
        self.backend.create_lineage(
            session,
            parent=artifact_instance,
            child=existing,
            relationship_type="has_literature_save",
        )
        return 200, self._literature_save_response(session, existing)

    def _user_can_view_literature_save(
        self,
        payload: dict[str, Any],
        *,
        viewer: ViewerContext,
    ) -> bool:
        owner_subject = str(payload.get("owner_subject") or "")
        if owner_subject == viewer.subject:
            return True
        scope = str(payload.get("visibility_scope") or "private")
        if scope == "all_users":
            return True
        if scope != "restricted":
            return False
        allowed_users = set(normalize_email_list(payload.get("allowed_users")))
        if viewer.email and viewer.email in allowed_users:
            return True
        allowed_groups = set(normalize_group_list(payload.get("allowed_groups")))
        return bool(set(viewer.groups) & allowed_groups)

    def _visible_literature_save_summary(
        self,
        session,
        artifact_instance,
        viewer: ViewerContext,
    ) -> dict[str, Any]:
        saves = self.backend.list_children(
            session,
            parent=artifact_instance,
            relationship_type="has_literature_save",
        )
        saved_by_me = False
        visible_owners: list[str] = []
        for item in saves:
            payload = normalize_instance_payload(item)
            if not self._user_can_view_literature_save(payload, viewer=viewer):
                continue
            owner_label = str(
                payload.get("owner_label")
                or payload.get("owner_email")
                or payload.get("owner_subject")
                or ""
            ).strip()
            if str(payload.get("owner_subject") or "") == viewer.subject:
                saved_by_me = True
            elif owner_label and owner_label not in visible_owners:
                visible_owners.append(owner_label)
        return {
            "saved_by_me": saved_by_me,
            "saved_by_others_count": len(visible_owners),
            "visible_owner_labels": visible_owners,
        }

    def _literature_save_response(self, session, instance) -> dict[str, Any]:
        payload = normalize_instance_payload(instance)
        artifact = self.backend.find_by_euid(
            session,
            template_code=ARTIFACT_TEMPLATE,
            euid=str(payload.get("artifact_euid") or ""),
        )
        artifact_summary = None
        if artifact is not None:
            artifact_payload = self._artifact_response(artifact)
            metadata = dict(artifact_payload.get("metadata") or {})
            artifact_summary = {
                "artifact_euid": artifact.euid,
                "title": metadata.get("title"),
                "pmid": metadata.get("pmid"),
                "doi": metadata.get("doi"),
                "pmcid": metadata.get("pmcid"),
                "storage_mode": metadata.get("storage_mode"),
                "fulltext_status": metadata.get("fulltext_status"),
            }
        return {
            "literature_save_euid": instance.euid,
            "artifact_euid": payload.get("artifact_euid"),
            "owner_subject": payload.get("owner_subject"),
            "owner_email": payload.get("owner_email"),
            "owner_label": payload.get("owner_label"),
            "visibility_scope": payload.get("visibility_scope"),
            "allowed_users": normalize_email_list(payload.get("allowed_users")),
            "allowed_groups": normalize_group_list(payload.get("allowed_groups")),
            "artifact": artifact_summary,
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at") or payload.get("created_at"),
        }
