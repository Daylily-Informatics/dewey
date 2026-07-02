"""Search and export workflows for Dewey service."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from dewey_service.literature import ViewerContext
from dewey_service.tapdb_backend import (
    ARTIFACT_SET_TEMPLATE,
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    SHARE_TEMPLATE,
)


class SearchServiceMixin:
    def query_search_v2(
        self,
        request: dict[str, Any] | None,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        query = dict(request or {})
        scopes = self._normalize_search_scopes(query.get("scopes"))
        page = max(1, int(query.get("page") or 1))
        page_size = max(1, min(int(query.get("page_size") or 25), self.search_export_max_rows))
        sort_field = str(query.get("sort_field") or "created_at").strip() or "created_at"
        sort_dir = str(query.get("sort_dir") or "desc").strip().lower() or "desc"

        with self.backend.session_scope(commit=False) as session:
            rows: list[dict[str, Any]] = []
            if "artifact" in scopes:
                rows.extend(self._search_artifact_items(session, viewer_context=viewer_context))
            if "artifact_set" in scopes:
                rows.extend(self._search_artifact_set_items(session))
            if "share" in scopes:
                rows.extend(self._search_share_items(session))

        filtered = self._apply_search_filters(rows, query)
        filtered = self._sort_search_rows(filtered, sort_field=sort_field, sort_dir=sort_dir)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = filtered[start:end]
        timing_ms = int((perf_counter() - started) * 1000)
        facets = {
            "artifact": sum(1 for row in filtered if row["record_type"] == "artifact"),
            "artifact_set": sum(1 for row in filtered if row["record_type"] == "artifact_set"),
            "share": sum(1 for row in filtered if row["record_type"] == "share"),
        }
        return {
            "items": items,
            "facets": facets,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": end < total,
            "timing_ms": timing_ms,
        }

    def collect_search_export_rows(
        self,
        request: dict[str, Any] | None,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> tuple[list[dict[str, Any]], int, bool]:
        started = perf_counter()
        query = dict(request or {})
        max_rows = max(
            1,
            min(
                int(query.get("max_rows") or self.search_export_max_rows),
                self.search_export_max_rows,
            ),
        )
        query["page"] = 1
        query["page_size"] = max_rows
        result = self.query_search_v2(query, viewer_context=viewer_context)
        filtered_total = int(result["total"])
        items = list(result["items"])
        truncated = filtered_total > max_rows
        timing_ms = int((perf_counter() - started) * 1000)
        return items, timing_ms, truncated

    @staticmethod
    def _normalize_search_scopes(raw: Any) -> list[str]:
        allowed = {"artifact", "artifact_set", "share"}
        if raw is None:
            return ["artifact", "share"]
        values = raw if isinstance(raw, list) else [raw]
        scopes = [str(item or "").strip().lower() for item in values if str(item or "").strip()]
        normalized = [scope for scope in scopes if scope in allowed]
        return normalized or ["artifact", "share"]

    def _search_artifact_items(
        self,
        session,
        *,
        viewer_context: ViewerContext | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(session, template_code=ARTIFACT_TEMPLATE, limit=5000)
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._artifact_response(row)
            payload["external_objects"] = self._artifact_external_objects(session, row)
            metadata = dict(payload.get("metadata") or {})
            if str(payload.get("artifact_type") or "") == "literature":
                payload.update(
                    {
                        "title": metadata.get("title"),
                        "pmid": metadata.get("pmid"),
                        "doi": metadata.get("doi"),
                        "pmcid": metadata.get("pmcid"),
                        "storage_mode": metadata.get("storage_mode"),
                        "fulltext_status": metadata.get("fulltext_status"),
                        "authors": list(metadata.get("authors") or []),
                        "journal": metadata.get("journal"),
                        "year": metadata.get("year"),
                        "abstract_snippet": metadata.get("abstract_snippet"),
                    }
                )
                if viewer_context is not None:
                    payload.update(
                        self._visible_literature_save_summary(session, row, viewer_context)
                    )
                else:
                    payload.update(
                        {
                            "saved_by_me": False,
                            "saved_by_others_count": 0,
                            "visible_owner_labels": [],
                        }
                    )
            items.append(
                {
                    "record_type": "artifact",
                    "source_kind": "dewey.artifact",
                    "euid": payload["artifact_euid"],
                    "name": (
                        payload.get("title")
                        or payload.get("original_filename")
                        or payload["artifact_euid"]
                    ),
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _artifact_external_objects(self, session, artifact_instance) -> list[dict[str, Any]]:
        relations = self.backend.list_children(
            session,
            parent=artifact_instance,
            relationship_type="has_external_relation",
        )
        rows: list[dict[str, Any]] = []
        for relation in relations:
            relation_payload = self._external_object_relation_response(relation)
            external = self.backend.find_by_euid(
                session,
                template_code=EXTERNAL_OBJECT_TEMPLATE,
                euid=str(relation_payload.get("external_object_euid") or ""),
            )
            if external is None:
                continue
            rows.append(
                {
                    **self._external_object_response(external),
                    "relation_type": relation_payload.get("relation_type"),
                }
            )
        return rows

    def _search_share_items(self, session) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(
            session,
            template_code=SHARE_TEMPLATE,
            limit=5000,
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._share_response(row)
            items.append(
                {
                    "record_type": "share",
                    "source_kind": "dewey.share",
                    "euid": payload["share_euid"],
                    "name": payload.get("name") or payload["share_euid"],
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _search_artifact_set_items(self, session) -> list[dict[str, Any]]:
        rows = self.backend.list_by_template(
            session,
            template_code=ARTIFACT_SET_TEMPLATE,
            limit=5000,
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._artifact_set_response(session, row)
            items.append(
                {
                    "record_type": "artifact_set",
                    "source_kind": "dewey.artifact_set",
                    "euid": payload["artifact_set_euid"],
                    "name": payload.get("label") or payload["artifact_set_euid"],
                    "created_at": payload.get("created_at"),
                    "modified_at": payload.get("created_at"),
                    **payload,
                }
            )
        return items

    def _apply_search_filters(
        self,
        rows: list[dict[str, Any]],
        query: dict[str, Any],
    ) -> list[dict[str, Any]]:
        q = str(query.get("q") or "").strip().lower()
        created_at_start = str(query.get("created_at_start") or "").strip()
        created_at_end = str(query.get("created_at_end") or "").strip()
        property_filters = query.get("property_filters") or []
        filtered: list[dict[str, Any]] = []

        for row in rows:
            if q and not self._row_matches_text(row, q):
                continue
            if created_at_start and not self._row_in_created_range(
                row,
                created_at_start,
                is_start=True,
            ):
                continue
            if created_at_end and not self._row_in_created_range(
                row,
                created_at_end,
                is_start=False,
            ):
                continue
            if not all(self._row_matches_property_filter(row, item) for item in property_filters):
                continue
            filtered.append(row)
        return filtered

    @staticmethod
    def _row_matches_text(row: dict[str, Any], query: str) -> bool:
        haystacks = [
            str(row.get("euid") or ""),
            str(row.get("name") or ""),
            str(row.get("artifact_type") or ""),
            str(row.get("artifact_set_type") or ""),
            str(row.get("label") or ""),
            str(row.get("description") or ""),
            str(row.get("producer_system") or ""),
            str(row.get("title") or ""),
            str(row.get("pmid") or ""),
            str(row.get("doi") or ""),
            str(row.get("journal") or ""),
            str(row.get("year") or ""),
            str(row.get("abstract_snippet") or ""),
            str(row.get("storage_uri") or ""),
            str(row.get("target_euid") or ""),
            str(row.get("purpose") or ""),
            json.dumps(row.get("metadata") or {}, sort_keys=True),
            json.dumps(row.get("manifest") or [], sort_keys=True),
            json.dumps(row.get("connection") or {}, sort_keys=True),
            json.dumps(row.get("external_objects") or [], sort_keys=True),
            json.dumps(row.get("visible_owner_labels") or [], sort_keys=True),
        ]
        return any(query in item.lower() for item in haystacks if item)

    def _row_in_created_range(self, row: dict[str, Any], raw_value: str, *, is_start: bool) -> bool:
        row_value = str(row.get("created_at") or "").strip()
        if not row_value:
            return False
        row_dt = self._parse_iso8601(row_value, field_name="created_at")
        bound = self._parse_iso8601(raw_value, field_name="created_at")
        return row_dt >= bound if is_start else row_dt <= bound

    def _row_matches_property_filter(self, row: dict[str, Any], raw_filter: Any) -> bool:
        if not isinstance(raw_filter, dict):
            return True
        path = str(raw_filter.get("path") or "").strip()
        op = str(raw_filter.get("op") or "eq").strip().lower()
        value = raw_filter.get("value")
        values = self._extract_path_values(row, path)
        if op == "exists":
            return bool(values) if bool(value or value is None) else not bool(values)
        if op == "eq":
            return any(candidate == value for candidate in values)
        if op == "neq":
            return bool(values) and all(candidate != value for candidate in values)
        if op == "contains":
            needle = str(value or "").lower()
            return any(needle in str(candidate or "").lower() for candidate in values)
        if op == "in":
            acceptable = value if isinstance(value, list) else [value]
            return any(candidate in acceptable for candidate in values)
        if op in {"gte", "lte"}:
            if not values:
                return False
            left = values[0]
            if self._looks_like_datetime(str(left or "")) and self._looks_like_datetime(
                str(value or "")
            ):
                left_value = self._parse_iso8601(str(left), field_name=path)
                right_value = self._parse_iso8601(str(value), field_name=path)
            else:
                try:
                    left_value = float(left)
                    right_value = float(value)
                except (TypeError, ValueError):
                    return False
            return left_value >= right_value if op == "gte" else left_value <= right_value
        return True

    @staticmethod
    def _looks_like_datetime(value: str) -> bool:
        return "T" in value and ("Z" in value or "+" in value or "-" in value[10:])

    def _extract_path_values(self, payload: Any, path: str) -> list[Any]:
        if not path:
            return []
        parts = [part for part in path.split(".") if part]
        if not parts:
            return []
        return self._extract_nested_values(payload, parts)

    def _extract_nested_values(self, payload: Any, parts: list[str]) -> list[Any]:
        if not parts:
            return [payload]
        head, *tail = parts
        values: list[Any] = []
        if isinstance(payload, list):
            for item in payload:
                values.extend(self._extract_nested_values(item, parts))
            return values
        if not isinstance(payload, dict):
            return []
        if head not in payload:
            return []
        return self._extract_nested_values(payload[head], tail)

    @staticmethod
    def _sort_search_rows(
        rows: list[dict[str, Any]],
        *,
        sort_field: str,
        sort_dir: str,
    ) -> list[dict[str, Any]]:
        reverse = sort_dir != "asc"
        key_name = (
            sort_field
            if sort_field in {"created_at", "modified_at", "name", "euid"}
            else "created_at"
        )
        return sorted(
            rows,
            key=lambda item: (
                str(item.get(key_name) or ""),
                str(item.get("euid") or ""),
            ),
            reverse=reverse,
        )
