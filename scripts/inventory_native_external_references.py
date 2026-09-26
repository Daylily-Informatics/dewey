"""Dewey XRF inventory for an operator-owned native read-only TapDB Session.

Load this file into the native operator process and call ``inventory(session)``.
The caller opens a scoped, read-only transaction; this module never constructs
an application adapter, connection, engine, or session, and never commits.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import aliased

from daylily_tapdb import generic_instance, generic_instance_lineage
from daylily_tapdb.external_references import ExternalIdentifierTarget, TapDBObjectTarget

EXPLICIT_TARGET_TYPES = {
    ("labcore", "sequencing_run"): "opaque",
    ("atlas", "patient"): "tapdb_object",
    ("bloom", "sequencer"): "tapdb_object",
    ("bloom", "sequencing_run"): "tapdb_object",
    ("ursa", "analysis"): "tapdb_object",
    ("ursa", "analysis_job"): "tapdb_object",
    ("dyec", "dayoa_analysis_directory"): "non_federated",
    ("ursa", "run_directory_analysis_trigger"): "non_federated",
    ("pubmed", "pmid"): "opaque",
    ("pubmedcentral", "pmcid"): "opaque",
    ("doi", "doi"): "opaque",
}


def _require_read_only(session) -> None:
    if session.new or session.dirty or session.deleted:
        raise RuntimeError("inventory session has pending ORM writes")
    if session.execute(text("SHOW transaction_read_only")).scalar_one() != "on":
        raise RuntimeError("inventory requires an already read-only transaction")


def inventory(session, *, maximum: int = 5000) -> dict:
    if not 1 <= maximum <= 10000:
        raise ValueError("maximum must be 1..10000")
    _require_read_only(session)
    with session.no_autoflush:
        return _inventory(session, maximum=maximum)


def _native_items(session, *, maximum, tapdb_version):
    xrf_model = aliased(generic_instance)
    rows = (
        session.query(generic_instance_lineage, xrf_model)
        .join(xrf_model, generic_instance_lineage.child_instance_uid == xrf_model.uid)
        .filter(
            generic_instance_lineage.is_deleted.is_(False),
            generic_instance_lineage.category == "lineage",
            generic_instance_lineage.type == "lineage",
            generic_instance_lineage.subtype == "external_reference",
            generic_instance_lineage.version == "1.0",
            xrf_model.is_deleted.is_(False),
            xrf_model.category == "reference",
            xrf_model.type == "external_identifier",
            or_(
                and_(xrf_model.subtype == "tapdb_object", xrf_model.version == tapdb_version),
                and_(xrf_model.subtype == "opaque", xrf_model.version == "1.0"),
            ),
        )
        .order_by(generic_instance_lineage.uid)
        .limit(maximum + 1)
        .all()
    )
    if len(rows) > maximum:
        raise RuntimeError(f"active XRF lineage exceeds maximum {maximum}; no partial inventory emitted")
    items = []
    for lineage, xrf in rows:
        source = session.get(generic_instance, lineage.parent_instance_uid)
        if source is None or source.is_deleted:
            raise RuntimeError(f"active XRF lineage {lineage.euid} has no visible active source")
        template = xrf.parent_template
        coords = (xrf.category, xrf.type, xrf.subtype, xrf.version)
        if template is None or tuple(getattr(template, key) for key in ("category", "type", "subtype", "version")) != coords:
            raise RuntimeError(f"XRF {xrf.euid} lacks its exact template")
        if (xrf.domain_code, xrf.issuer_app_code) != (template.domain_code, template.issuer_app_code):
            raise RuntimeError(f"XRF {xrf.euid} differs from template owner")
        envelope = xrf.json_addl
        properties = envelope.get("properties") if isinstance(envelope, dict) else None
        if not isinstance(properties, dict):
            raise RuntimeError(f"XRF {xrf.euid} has no canonical properties")
        if xrf.subtype == "tapdb_object":
            if set(properties) != {"target_service_id", "target_object_euid", "target_tenant_id", "target_object_kind"}:
                raise RuntimeError(f"XRF {xrf.euid} has noncanonical owner fields")
            tenant = UUID(properties["target_tenant_id"]) if properties["target_tenant_id"] else None
            target = TapDBObjectTarget(
                target_service_id=properties["target_service_id"],
                target_object_euid=properties["target_object_euid"],
                target_tenant_id=tenant,
                target_object_kind=properties["target_object_kind"],
            )
        else:
            if set(properties) != {"namespace", "kind", "value", "scope", "canonical_uri"}:
                raise RuntimeError(f"XRF {xrf.euid} has noncanonical opaque fields")
            target = ExternalIdentifierTarget(
                namespace=properties["namespace"], kind=properties["kind"],
                value=properties["value"], scope=properties["scope"],
                tenant_id=xrf.tenant_id, canonical_uri=properties["canonical_uri"],
            )
        if xrf.identity_key != target.identity_key:
            raise RuntimeError(f"XRF {xrf.euid} identity key differs")
        assertion_envelope = lineage.json_addl
        assertion = assertion_envelope.get("properties") if isinstance(assertion_envelope, dict) else None
        if not isinstance(assertion, dict) or set(assertion) != {
            "assertion_authority", "asserted_at", "assertion_provenance",
            "approved_global_link", "deactivated_at", "deactivation_provenance",
        }:
            raise RuntimeError(f"XRF lineage {lineage.euid} has noncanonical assertion")
        if not all(isinstance(assertion[key], str) and assertion[key] for key in (
            "assertion_authority", "asserted_at", "assertion_provenance"
        )):
            raise RuntimeError(f"XRF lineage {lineage.euid} lacks assertion evidence")
        stamp = datetime.fromisoformat(assertion["asserted_at"])
        if stamp.utcoffset() is None:
            raise RuntimeError(f"XRF lineage {lineage.euid} assertion timestamp lacks timezone")
        items.append((source, xrf, lineage, target, assertion))
    return items


def _native_summary(items, *, candidate_from_opaque=None):
    counts = Counter()
    records = []
    for source, xrf, lineage, target, assertion in items:
        target_type = xrf.subtype
        xrf_scope = "tenant" if xrf.tenant_id is not None else "global"
        target_scope = (
            target.scope if isinstance(target, ExternalIdentifierTarget)
            else ("tenant_claimed" if target.target_tenant_id else "unspecified")
        )
        authority = assertion["assertion_authority"]
        counts[(target_type, xrf_scope, target_scope, authority)] += 1
        record = {
            "source_euid": source.euid, "xrf_euid": xrf.euid, "lineage_euid": lineage.euid,
            "source_tenant_scope": "tenant" if source.tenant_id is not None else "global",
            "xrf_tenant_scope": xrf_scope, "target_type": target_type,
            "target_scope_claim": target_scope, "assertion_authority": authority,
            "relationship_type": lineage.relationship_type,
            "asserted_at": assertion["asserted_at"],
            "assertion_provenance_sha256": hashlib.sha256(assertion["assertion_provenance"].encode()).hexdigest(),
        }
        if isinstance(target, TapDBObjectTarget):
            record["target_service_id"] = target.target_service_id
            record["candidate_target_euid"] = target.target_object_euid
        elif candidate_from_opaque is not None:
            candidate = candidate_from_opaque(authority, target)
            if candidate is not None:
                record["target_service_id"], record["candidate_target_euid"] = candidate
        records.append(record)
    summary = [
        {"target_type": kind, "xrf_tenant_scope": scope, "target_scope_claim": claim,
         "authority": authority, "count": count}
        for (kind, scope, claim, authority), count in sorted(counts.items())
    ]
    return records, summary


def _inventory(session, *, maximum: int) -> dict:
    items = _native_items(session, maximum=maximum, tapdb_version="1.0")
    records, counts = _native_summary(items)
    domain_rows = (
        session.query(generic_instance)
        .filter(
            generic_instance.is_deleted.is_(False),
            generic_instance.category == "integration",
            generic_instance.type == "external_object",
            generic_instance.subtype == "generic",
            generic_instance.version == "1.0",
        )
        .order_by(generic_instance.uid)
        .limit(maximum + 1)
        .all()
    )
    if len(domain_rows) > maximum:
        raise RuntimeError(f"active domain objects exceed --maximum {maximum}; no partial inventory emitted")
    missing = []
    domain_counts = Counter()
    for domain in domain_rows:
        payload = domain.json_addl if isinstance(domain.json_addl, dict) else {}
        system = payload.get("external_system")
        kind = payload.get("external_object_type")
        descriptor = payload.get("reference_target")
        if not isinstance(system, str) or not isinstance(kind, str):
            missing.append({"domain_reference_euid": domain.euid, "reason": "missing_owner_kind"})
            continue
        binding = EXPLICIT_TARGET_TYPES.get((system, kind))
        if descriptor is None and binding is None:
            missing.append({"domain_reference_euid": domain.euid, "system": system, "kind": kind, "reason": "missing_target_descriptor"})
        elif descriptor is not None and not isinstance(descriptor, dict):
            missing.append({"domain_reference_euid": domain.euid, "system": system, "kind": kind, "reason": "invalid_target_descriptor"})
        else:
            declared = descriptor if isinstance(descriptor, dict) else binding
            domain_counts[(system, kind, declared.get("kind", "invalid") if isinstance(declared, dict) else declared)] += 1
    return {
        "service": "dewey",
        "active_xrf_count": len(records),
        "counts": counts,
        "records": records,
        "active_domain_reference_count": len(domain_rows),
        "domain_target_counts": [
            {"system": system, "kind": kind, "target_type": target_type, "count": count}
            for (system, kind, target_type), count in sorted(domain_counts.items())
        ],
        "missing_domain_descriptors": missing,
    }
