"""Dewey external-reference assertions from persisted local lineage."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from daylily_tapdb import generic_instance, generic_instance_lineage
from daylily_tapdb.external_references import (
    ExternalIdentifierTarget,
    ExternalLinkSpec,
    ExternalReferenceService,
    TapDBObjectTarget,
)

ASSERTION_AUTHORITY = "dewey.external_object_relation"
EXPLICIT_TARGET_TYPES = {
    ("labcore", "sequencing_run"): {
        "kind": "opaque",
        "namespace": "labcore",
        "identifier_kind": "sequencing_run",
        "scope": "public_global",
    },
    ("atlas", "patient"): {"kind": "tapdb_object"},
    ("bloom", "sequencer"): {"kind": "tapdb_object"},
    ("bloom", "sequencing_run"): {"kind": "tapdb_object"},
    ("ursa", "analysis"): {"kind": "tapdb_object"},
    ("ursa", "analysis_job"): {"kind": "tapdb_object"},
    ("dyec", "dayoa_analysis_directory"): {"kind": "non_federated"},
    ("ursa", "run_directory_analysis_trigger"): {"kind": "non_federated"},
    ("pubmed", "pmid"): {
        "kind": "opaque",
        "namespace": "pmid",
        "identifier_kind": "article",
        "scope": "public_global",
    },
    ("pubmedcentral", "pmcid"): {
        "kind": "opaque",
        "namespace": "pmcid",
        "identifier_kind": "article",
        "scope": "public_global",
    },
    ("doi", "doi"): {
        "kind": "opaque",
        "namespace": "doi",
        "identifier_kind": "article",
        "scope": "public_global",
    },
}


class DeweyExternalReferenceError(ValueError):
    """The persisted Dewey relationship cannot establish a native assertion."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DeweyExternalReferenceError(message)


def _coordinates(instance) -> tuple[str, str, str, str]:
    return (instance.category, instance.type, instance.subtype, instance.version)


def _payload(instance) -> dict[str, Any]:
    payload = instance.json_addl
    _require(isinstance(payload, dict), "Dewey external object metadata must be an object")
    return payload


@dataclass(frozen=True)
class NonFederatedTarget:
    """An explicitly local DGX external identity with no canonical remote EUID."""

    system: str
    object_type: str
    value: str


@dataclass(frozen=True)
class NonFederatedOutcome:
    status: str = "non_federated"
    reference: None = None
    lineage: None = None


def build_external_target(payload: dict[str, Any]):
    """Use an explicit semantic type, never the apparent shape of an identifier."""
    system, kind, value = (
        payload.get("external_system"),
        payload.get("external_object_type"),
        payload.get("external_object_id"),
    )
    _require(
        all(isinstance(item, str) and item for item in (system, kind, value)),
        "External system, object type and exact identifier are required",
    )
    descriptor = payload.get("reference_target")
    binding = EXPLICIT_TARGET_TYPES.get((system, kind))
    if binding is not None:
        if descriptor is not None:
            _require(
                isinstance(descriptor, dict)
                and all(descriptor.get(key) == item for key, item in binding.items()),
                "reference_target contradicts the declared external object type",
            )
        else:
            descriptor = binding
    else:
        _require(
            descriptor is not None,
            "Unknown external object type requires an explicit reference_target",
        )
    _require(isinstance(descriptor, dict), "reference_target must be an object")
    if descriptor.get("kind") == "non_federated":
        _require(set(descriptor) == {"kind"}, "Unexpected non-federated descriptor fields")
        return NonFederatedTarget(system, kind, value)
    if descriptor.get("kind") == "tapdb_object":
        _require(
            set(descriptor) <= {"kind", "target_tenant_id"},
            "Unexpected TapDB target descriptor fields",
        )
        tenant = descriptor.get("target_tenant_id")
        _require(tenant is None or isinstance(tenant, str), "Target tenant must be a UUID string")
        return TapDBObjectTarget(
            target_service_id=system,
            target_object_euid=value,
            target_tenant_id=UUID(tenant) if tenant is not None else None,
            target_object_kind=kind,
        )
    _require(descriptor.get("kind") == "opaque", "Unknown external reference target kind")
    _require(
        set(descriptor) <= {"kind", "namespace", "identifier_kind", "scope", "tenant_id"},
        "Unexpected opaque target descriptor fields",
    )
    tenant = descriptor.get("tenant_id")
    _require(tenant is None or isinstance(tenant, str), "Identifier tenant must be a UUID string")
    return ExternalIdentifierTarget(
        namespace=descriptor.get("namespace"),
        kind=descriptor.get("identifier_kind"),
        value=value,
        scope=descriptor.get("scope"),
        tenant_id=UUID(tenant) if tenant is not None else None,
    )


@dataclass(frozen=True)
class RelationEndpoints:
    source: generic_instance
    external_object: generic_instance
    source_lineage: generic_instance_lineage
    external_lineage: generic_instance_lineage


def resolve_relation_endpoints(session, relation) -> RelationEndpoints:
    """Resolve exact active endpoints from their two authoritative local lineages."""
    return resolve_relation_endpoints_many(session, [relation])[relation.uid]


def resolve_relation_endpoints_many(session, relations) -> dict[Any, RelationEndpoints]:
    """Batch authoritative endpoints; apply the same strict checks to every relation."""
    if not relations:
        return {}
    grouped = {relation.uid: {} for relation in relations}
    rows = (
        session.query(generic_instance_lineage)
        .filter(
            generic_instance_lineage.child_instance_uid.in_(list(grouped)),
            generic_instance_lineage.relationship_type.in_(
                ["has_external_relation", "is_external_relation_for"]
            ),
            generic_instance_lineage.is_deleted.is_(False),
        )
        .all()
    )
    parent_uids = {lineage.parent_instance_uid for lineage in rows}
    parents = (
        {
            node.uid: node
            for node in session.query(generic_instance)
            .filter(generic_instance.uid.in_(parent_uids))
            .all()
        }
        if parent_uids
        else {}
    )
    for lineage in rows:
        grouped[lineage.child_instance_uid].setdefault(lineage.relationship_type, []).append(
            lineage
        )
    return {
        relation.uid: _validated_relation_endpoints(relation, grouped[relation.uid], parents)
        for relation in relations
    }


def _validated_relation_endpoints(relation, grouped, parents) -> RelationEndpoints:
    _require(
        _coordinates(relation) == ("integration", "external_object_relation", "generic", "1.0"),
        "Expected a Dewey external-object relation",
    )
    _require(
        relation.uid is not None and not relation.is_deleted,
        "External relation must be persisted and active",
    )
    _require(relation.issuer_app_code == "dewey", "Dewey must own the external relation")
    endpoints = []
    for relationship in ("has_external_relation", "is_external_relation_for"):
        rows = grouped.get(relationship, [])
        _require(len(rows) == 1, f"Expected exactly one active {relationship} lineage")
        lineage = rows[0]
        _require(
            lineage.domain_code == relation.domain_code
            and lineage.issuer_app_code == relation.issuer_app_code
            and lineage.tenant_id == relation.tenant_id,
            "Dewey relation lineage scope mismatch",
        )
        node = parents.get(lineage.parent_instance_uid)
        _require(
            node is not None and not node.is_deleted, "Relation endpoint is not visible and active"
        )
        _require(
            node.domain_code == relation.domain_code
            and node.issuer_app_code == relation.issuer_app_code
            and node.tenant_id == relation.tenant_id,
            "Dewey relation endpoint scope mismatch",
        )
        endpoints.append((node, lineage))
    (source, source_lineage), (external, external_lineage) = endpoints
    _require(
        _coordinates(source)
        in {
            ("data", "artifact", "generic", "1.0"),
            ("data", "artifact_set", "generic", "1.0"),
        },
        "External relation source must be a Dewey artifact or artifact set",
    )
    _require(
        _coordinates(external) == ("integration", "external_object", "generic", "1.0"),
        "External relation endpoint must be a Dewey external object",
    )
    return RelationEndpoints(source, external, source_lineage, external_lineage)


def lock_external_relation_source(session, source):
    """Serialize Dewey relation lookup/creation before the native XRF source lock."""
    locked = (
        session.query(generic_instance)
        .filter_by(uid=source.uid, is_deleted=False)
        .with_for_update()
        .one_or_none()
    )
    _require(locked is not None and locked.euid == source.euid, "Relation source is not visible")
    return locked


def build_external_link_spec(relation, endpoints: RelationEndpoints) -> ExternalLinkSpec | None:
    """Use stable persisted assertion evidence so an attach replay is immutable."""
    target = build_external_target(_payload(endpoints.external_object))
    if isinstance(target, NonFederatedTarget):
        return None
    asserted_at = relation.created_dt
    _require(
        isinstance(asserted_at, datetime)
        and asserted_at.tzinfo is not None
        and asserted_at.utcoffset() is not None,
        "External relation requires its persisted timezone-aware creation timestamp",
    )
    evidence = {
        "contract": "dewey.external_object_relation/v1",
        "relation_uid": relation.uid,
        "source_lineage_uid": endpoints.source_lineage.uid,
        "external_lineage_uid": endpoints.external_lineage.uid,
    }
    _require(
        all(
            isinstance(evidence[key], int) and evidence[key] > 0
            for key in ("relation_uid", "source_lineage_uid", "external_lineage_uid")
        ),
        "External assertion requires persisted relation and lineage UIDs",
    )
    return ExternalLinkSpec(
        target=target,
        relationship_type=_payload(relation).get("relation_type"),
        assertion_authority=ASSERTION_AUTHORITY,
        asserted_at=asserted_at,
        assertion_provenance=json.dumps(evidence, sort_keys=True, separators=(",", ":")),
    )


def attach_external_relation(session, relation):
    """Attach native XRF lineage without committing or changing historical DGX rows."""
    endpoints = resolve_relation_endpoints(session, relation)
    spec = build_external_link_spec(relation, endpoints)
    if spec is None:
        return NonFederatedOutcome()
    return ExternalReferenceService(session).attach(endpoints.source, spec)
