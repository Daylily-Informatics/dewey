"""Schema-driven helpers for the Dewey artifacts browser surface."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Mapping

ARTIFACT_TYPES = [
    "bam",
    "csv",
    "fastq",
    "json",
    "pdf",
    "report",
    "tsv",
    "vcf",
]

ARTIFACT_SET_TYPES = [
    "analysis_output",
    "batch",
    "collection",
    "delivery",
    "release",
]

ARTIFACT_METADATA_FIELDS: tuple[dict[str, str], ...] = (
    {"name": "title", "label": "Title", "type": "text"},
    {"name": "sample_id", "label": "Sample ID", "type": "text"},
    {"name": "study_id", "label": "Study ID", "type": "text"},
    {"name": "assay", "label": "Assay", "type": "text"},
    {"name": "pipeline", "label": "Pipeline", "type": "text"},
    {"name": "recorded_at", "label": "Recorded At", "type": "datetime"},
    {"name": "tags", "label": "Tags", "type": "csv"},
    {"name": "notes", "label": "Notes", "type": "textarea"},
)

ARTIFACT_SET_METADATA_FIELDS: tuple[dict[str, str], ...] = (
    {"name": "program", "label": "Program", "type": "text"},
    {"name": "cohort", "label": "Cohort", "type": "text"},
    {"name": "release_label", "label": "Release Label", "type": "text"},
    {"name": "recorded_at", "label": "Recorded At", "type": "datetime"},
    {"name": "tags", "label": "Tags", "type": "csv"},
    {"name": "notes", "label": "Notes", "type": "textarea"},
)

BULK_TEMPLATE_BASE_COLUMNS = [
    "source_mode",
    "artifact_type",
    "source_uri",
    "bucket",
    "key",
    "original_filename",
    "producer_system",
    "producer_object_euid",
    "artifact_set_type",
    "artifact_set_label",
    "artifact_set_description",
]


def metadata_fields(kind: str) -> list[dict[str, str]]:
    if kind == "artifact":
        return [dict(item) for item in ARTIFACT_METADATA_FIELDS]
    if kind == "artifact_set":
        return [dict(item) for item in ARTIFACT_SET_METADATA_FIELDS]
    raise ValueError(f"Unsupported metadata field kind: {kind}")


def parse_json_object(raw: str | None, *, label: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must decode to a JSON object")
    return dict(payload)


def split_lines(raw: str | None) -> list[str]:
    return [line.strip() for line in str(raw or "").splitlines() if line.strip()]


def split_csv(raw: str | None) -> list[str]:
    text = str(raw or "").replace("\n", ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def coerce_metadata_value(field: Mapping[str, str], raw: Any) -> Any:
    field_type = str(field.get("type") or "text")
    if field_type == "csv":
        values = split_csv(str(raw or ""))
        return values or None
    text = str(raw or "").strip()
    if not text:
        return None
    return text


def collect_metadata(
    values: Mapping[str, Any],
    *,
    fields: list[dict[str, str]],
    prefix: str,
    extra_json_field: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields:
        value = coerce_metadata_value(field, values.get(f"{prefix}_{field['name']}"))
        if value is not None:
            payload[field["name"]] = value
    payload.update(parse_json_object(values.get(extra_json_field), label=extra_json_field))
    return payload


def collect_metadata_search_filters(
    values: Mapping[str, Any],
    *,
    fields: list[dict[str, str]],
    prefix: str,
    greedy: bool,
    metadata_prefix: str = "metadata",
) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    for field in fields:
        path = f"{metadata_prefix}.{field['name']}"
        field_type = str(field.get("type") or "text")
        if field_type == "datetime":
            start_value = str(values.get(f"{prefix}_{field['name']}_start") or "").strip()
            end_value = str(values.get(f"{prefix}_{field['name']}_end") or "").strip()
            if start_value:
                filters.append({"path": path, "op": "gte", "value": start_value})
            if end_value:
                filters.append({"path": path, "op": "lte", "value": end_value})
            continue
        raw_value = values.get(f"{prefix}_{field['name']}")
        if field_type == "csv":
            values_list = split_csv(str(raw_value or ""))
            if not values_list:
                continue
            if greedy:
                filters.extend({"path": path, "op": "contains", "value": item} for item in values_list)
            else:
                filters.append({"path": path, "op": "in", "value": values_list})
            continue
        text = str(raw_value or "").strip()
        if not text:
            continue
        filters.append({"path": path, "op": "contains" if greedy else "eq", "value": text})
    return filters


def bulk_template_tsv() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=BULK_TEMPLATE_BASE_COLUMNS
        + [field["name"] for field in ARTIFACT_METADATA_FIELDS],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerow(
        {
            "source_mode": "reference",
            "artifact_type": "vcf",
            "source_uri": "s3://example-bucket/path/sample.vcf.gz",
            "bucket": "",
            "key": "",
            "original_filename": "sample.vcf.gz",
            "producer_system": "atlas",
            "producer_object_euid": "REL-123",
            "artifact_set_type": "batch",
            "artifact_set_label": "Example Batch",
            "artifact_set_description": "Optional grouping for this row.",
            "study_id": "STUDY-1",
            "sample_id": "SAMPLE-1",
            "notes": "Example row",
        }
    )
    writer.writerow(
        {
            "source_mode": "register",
            "artifact_type": "report",
            "source_uri": "",
            "bucket": "example-bucket",
            "key": "reports/case-report.pdf",
            "original_filename": "case-report.pdf",
            "producer_system": "bloom",
            "producer_object_euid": "DOC-9",
            "artifact_set_type": "release",
            "artifact_set_label": "Release 2026-03",
            "artifact_set_description": "Optional grouping for registered objects.",
            "title": "Case Report",
            "notes": "Register an existing S3 object without copying bytes.",
        }
    )
    return output.getvalue()
