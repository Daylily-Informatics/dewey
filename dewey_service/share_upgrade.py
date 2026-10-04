"""Explicit inventory/apply/verify of canonical sharing; never invoked at startup."""
from __future__ import annotations

from datetime import datetime, timezone

from dewey_service.registry_conversion import digest, identity, write_private
from dewey_service.registry_access import POLICY_TEMPLATE
from dewey_service.services.share_policy import GRANT_TEMPLATE, EVENT_TEMPLATE, normalized_policy, normalize_grants, patterns, expiry
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso


def _record_receipt(record):
    from dewey_service.registry_conversion import coordinates
    return {"euid": record.euid, "record_revision": record.record_revision,
        "type": record.type, "bstatus": record.bstatus, "is_deleted": bool(record.is_deleted),
        "domain_code": record.domain_code, "issuer_app_code": record.issuer_app_code,
        "coordinates_sha256": digest(coordinates(record))}


def _edge_receipt(edge, parent, child):
    return {"euid": edge.euid, "record_revision": edge.record_revision,
        "relationship_type": edge.relationship_type, "bstatus": edge.bstatus,
        "is_deleted": bool(edge.is_deleted), "parent_euid": parent.euid, "child_euid": child.euid}


def _share_authority_rows(session, share):
    from daylily_tapdb import generic_instance, generic_instance_lineage
    return session.query(generic_instance_lineage, generic_instance).outerjoin(generic_instance,
        generic_instance.uid == generic_instance_lineage.parent_instance_uid).filter(
        generic_instance_lineage.child_instance_uid == share.uid,
        generic_instance_lineage.relationship_type == "has_share",
        generic_instance_lineage.is_deleted.is_(False)).order_by(generic_instance_lineage.euid).all()


def _historical_set_scope(service, session, share, *, canonical_members=None):
    """Explicit conversion-time native scope. Never called by runtime access."""
    from daylily_tapdb import generic_instance, generic_instance_lineage
    parents = _share_authority_rows(session, share)
    permitted_direct = set(canonical_members or [])
    set_parents = []
    observed_direct = []
    for edge, parent in parents:
        if parent is None or parent.is_deleted or edge.bstatus != "active" or parent.bstatus != "active":
            raise ValueError("Historical set share has inactive or missing native authority")
        if parent.type == "artifact_set":
            set_parents.append((edge, parent))
        elif canonical_members is not None and parent.type == "artifact" and parent.euid in permitted_direct:
            observed_direct.append(parent.euid)
        else:
            raise ValueError("Historical set share has mixed or conflicting native authority")
    if len(set_parents) != 1:
        raise ValueError("Historical set conversion requires exactly one active has_share set parent")
    if canonical_members is not None and (set(observed_direct) != permitted_direct or len(observed_direct) != len(permitted_direct)):
        raise ValueError("Canonical direct member relationships differ from the reviewed set selection")
    share_edge, artifact_set = set_parents[0]
    if (artifact_set.domain_code, artifact_set.issuer_app_code) != (share.domain_code, share.issuer_app_code):
        raise ValueError("Historical share and set authority belong to different namespaces")
    rows = session.query(generic_instance_lineage, generic_instance).outerjoin(generic_instance,
        generic_instance.uid == generic_instance_lineage.child_instance_uid).filter(
        generic_instance_lineage.parent_instance_uid == artifact_set.uid,
        generic_instance_lineage.relationship_type == "artifact_set_member",
        generic_instance_lineage.is_deleted.is_(False)).order_by(generic_instance_lineage.euid).limit(1001).all()
    if not rows or len(rows) > 1000:
        raise ValueError("Historical set membership is empty or exceeds the complete 1000-member conversion bound")
    members, receipts, seen = [], [], set()
    for edge, member in rows:
        if member is None or member.is_deleted or member.bstatus != "active" or edge.bstatus != "active" or member.type != "artifact":
            raise ValueError("Historical set contains inactive, missing, or non-artifact membership")
        if (member.domain_code, member.issuer_app_code) != (artifact_set.domain_code, artifact_set.issuer_app_code):
            raise ValueError("Historical set member belongs to a different namespace")
        if member.euid in seen:
            raise ValueError("Historical set contains duplicate active membership edges")
        data = normalize_instance_payload(member)
        if data.get("storage_backend") != "s3" or data.get("storage_kind") not in {"object", "prefix"}:
            raise ValueError("Historical set requires explicit S3 object/prefix storage coordinates")
        bucket, key, version = data.get("bucket"), data.get("key"), data.get("version_id")
        if not isinstance(bucket, str) or not bucket or any(c.isspace() or c in "/?#@:" for c in bucket) or not isinstance(key, str) or "\x00" in key:
            raise ValueError("Historical set member storage coordinates are malformed")
        if data["storage_kind"] == "object" and not key or data["storage_kind"] == "prefix" and key and not key.endswith("/"):
            raise ValueError("Historical set requires exact object keys or canonical prefix boundaries")
        if version is not None and (not isinstance(version, str) or not version or version != version.strip()):
            raise ValueError("Historical set member has an invalid explicit version identity")
        service._artifact_member_from_instance(member)
        seen.add(member.euid)
        members.append(member)
        receipts.append({"lineage": _edge_receipt(edge, artifact_set, member), "member": _record_receipt(member)})
    return members, {"kind": "historical_set_membership", "set": _record_receipt(artifact_set),
        "share_parent_lineage": _edge_receipt(share_edge, artifact_set, share),
        "member_lineage": receipts, "complete": True, "member_limit": 1000}


def _conversion_scope(service, session, share):
    members = service._share_members(session, share)
    if members:
        # Existing direct member links are the selected set. Never consult current
        # set children to enlarge an already explicit or canonical share.
        selected = {member.euid for member in members}
        links = [{"lineage": _edge_receipt(edge, parent, share), "member": _record_receipt(parent)}
            for edge, parent in _share_authority_rows(session, share)
            if parent is not None and parent.type == "artifact" and parent.euid in selected]
        return members, {"kind": "direct_artifact_lineage", "member_lineage": links}
    if normalize_instance_payload(share).get("schema_version") == 2:
        raise ValueError("Canonical share lacks direct persisted artifact member lineage")
    return _historical_set_scope(service, session, share)


def _lock_inventory_authority(service, session, reviewed):
    """Lock the exact reviewed source objects and edges before native reinspection.

    Dewey membership writers acquire the set row lock; these locks also prevent
    its selected objects/edges from changing during the conversion transaction.
    """
    from daylily_tapdb import generic_instance, generic_instance_lineage
    object_euids, edge_euids = set(), set()
    for row in reviewed["shares"]:
        basis = row.get("conversion_basis") or {}
        if basis.get("kind") == "historical_set_membership":
            object_euids.add(basis["set"]["euid"])
            edge_euids.add(basis["share_parent_lineage"]["euid"])
        for member in basis.get("member_lineage", []):
            object_euids.add(member["member"]["euid"])
            edge_euids.add(member["lineage"]["euid"])
    if object_euids:
        records = session.query(generic_instance).filter(generic_instance.euid.in_(sorted(object_euids)),
            generic_instance.domain_code == service.backend.domain_code).order_by(generic_instance.euid).with_for_update().all()
        if {record.euid for record in records} != object_euids:
            raise ValueError("A reviewed source object is missing")
    if edge_euids:
        edges = session.query(generic_instance_lineage).filter(generic_instance_lineage.euid.in_(sorted(edge_euids))).order_by(
            generic_instance_lineage.euid).with_for_update().all()
        if {edge.euid for edge in edges} != edge_euids:
            raise ValueError("A reviewed authority edge is missing")


def _proposal(service, session, share, *, members=None):
    data = normalize_instance_payload(share)
    if members is None:
        members, _ = _conversion_scope(service, session, share)
    if not members:
        raise ValueError("No persisted artifact member lineage; explicit disposition required")
    for member in members:
        service._artifact_member_from_instance(member)
    if not data.get("owner_subject") and not data.get("owner_email"):
        raise ValueError("Owner identity missing; explicit disposition required")
    if data.get("status") not in {"active", "revoked", "expired"}:
        raise ValueError("Unknown share lifecycle status")
    expiry(data.get("expires_at"))
    if data.get("schema_version") == 2:
        if type(data.get("policy_revision")) is not int or data["policy_revision"] < 1:
            raise ValueError("Canonical policy revision is missing")
        if not isinstance(data.get("delivery_modes"), list) or not data["delivery_modes"] or set(data["delivery_modes"]) - {"gateway", "presigned"}:
            raise ValueError("Canonical delivery modes are invalid")
        patterns(data["include_patterns"])
        patterns(data["exclude_patterns"])
        if not isinstance(data.get("denied_emails"), list):
            raise ValueError("Canonical deny list is missing")
        grants = service._share_grants(session, share)
        for grant in grants:
            rule = normalize_instance_payload(grant)
            if rule.get("status") not in {"active", "revoked", "superseded"}:
                raise ValueError("Unknown grant status")
            expiry(rule.get("expires_at"))
            targets = service._grant_targets(session, grant)
            if not targets or any(t.euid not in {m.euid for m in members} for t in targets):
                raise ValueError("Canonical grant lacks exact member lineage")
            normalized = {k: rule[k] for k in ("recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at")}
            normalize_grants([{**normalized, "target_euids": [t.euid for t in targets]}],
                share_expiry=data["expires_at"], member_euids=[m.euid for m in members])
            if rule["status"] == "active" and rule.get("policy_revision") != data["policy_revision"]:
                raise ValueError("Active grant revision differs from canonical policy")
        if not grants: raise ValueError("Canonical share lacks typed grants")
        return None
    if service._share_grants(session, share):
        raise ValueError("Legacy share has conflicting existing canonical grant authority")
    if data.get("audience", "recipients") not in {None, "recipients", "private"} or data.get("allowed_groups"):
        raise ValueError("Broad audience/group grant requires explicit recipient disposition")
    modes = data.get("delivery_modes")
    if not isinstance(modes, list) or not modes:
        raise ValueError("Delivery permission is missing")
    if set(modes) - {"presigned_s3", "presigned_s3_manifest", "dewey_html_browser"}:
        raise ValueError("CloudFront or unknown delivery needs explicit disposition")
    grants = [{"recipient_type": "email", "recipient": e} for e in data.get("allowed_users", [])]
    # Existing domain semantics included subdomains; preserve this explicit conversion fact.
    grants += [{"recipient_type": "domain", "recipient": d, "include_subdomains": True} for d in data.get("allowed_domains", [])]
    policy = normalized_policy({"grants": grants, "delivery_modes": list(dict.fromkeys(
        "gateway" if m == "dewey_html_browser" else "presigned" for m in modes))},
        share_expiry=data["expires_at"], member_euids=[m.euid for m in members])
    return policy


def _disposition_evidence(service, session, share, data):
    """Non-recipient evidence only; JSON references never become target authority."""
    from daylily_tapdb import generic_instance, generic_instance_lineage

    def count(value):
        return len(value) if isinstance(value, list) else None

    def literal(value, allowed):
        # Malformed policy fields must not smuggle names or credentials into the
        # operator's safe disposition summary. Their private payload hash remains.
        return value if isinstance(value, str) and value in allowed else None

    modes = data.get("delivery_modes")
    known_modes = {"gateway", "presigned", "presigned_s3", "presigned_s3_manifest",
        "dewey_html_browser", "cloudfront_signed_url", "cloudfront_signed_cookie"}
    mode_values = modes if isinstance(modes, list) else []
    safe_modes = [value for value in mode_values if isinstance(value, str) and value in known_modes]
    unknown_modes = [digest(value) for value in mode_values if not isinstance(value, str) or value not in known_modes]
    raw_expiry = data.get("expires_at")
    try:
        expiry_value = expiry(raw_expiry).isoformat()
    except (ValueError, TypeError, AttributeError):
        expiry_value = None

    parents = session.query(generic_instance_lineage, generic_instance).join(generic_instance,
        generic_instance.uid == generic_instance_lineage.parent_instance_uid).filter(
        generic_instance_lineage.child_instance_uid == share.uid).order_by(
        generic_instance_lineage.relationship_type, generic_instance.euid,
        generic_instance_lineage.euid).all()
    known_relationships = {"has_share", "has_share_reference"}
    known_parent_types = {"artifact", "artifact_set"}
    parent_lineage = [{"lineage_euid": edge.euid,
        "relationship_type": literal(edge.relationship_type, known_relationships),
        "unknown_relationship_type_sha256": None if edge.relationship_type in known_relationships else digest(edge.relationship_type),
        "lineage_deleted": bool(edge.is_deleted), "parent_euid": parent.euid,
        "parent_type": literal(parent.type, known_parent_types),
        "unknown_parent_type_sha256": None if parent.type in known_parent_types else digest(parent.type),
        "parent_deleted": bool(parent.is_deleted),
        "parent_bstatus": literal(parent.bstatus, {"active", "archived", "inactive", "deleted", "draft", "pending"})}
        for edge, parent in parents]
    # Inspect only one native membership hop from the exact persisted set parents.
    # This evidence does not expand _proposal or grant any target authority.
    from dewey_service.registry_conversion import coordinates

    def timestamp(value):
        return value.isoformat() if value is not None else None

    set_parents = {}
    for edge, parent in parents:
        if parent.type == "artifact_set":
            entry = set_parents.setdefault(parent.uid, {"parent": parent, "edges": []})
            entry["edges"].append(edge)
    set_membership = []
    for entry in sorted(set_parents.values(), key=lambda item: item["parent"].euid):
        parent = entry["parent"]
        membership_rows = session.query(generic_instance_lineage, generic_instance).outerjoin(generic_instance,
            generic_instance.uid == generic_instance_lineage.child_instance_uid).filter(
            generic_instance_lineage.parent_instance_uid == parent.uid,
            generic_instance_lineage.relationship_type == "artifact_set_member").order_by(
            generic_instance_lineage.euid).limit(1001).all()
        complete = len(membership_rows) <= 1000
        items = []
        for edge, member in membership_rows[:1000]:
            member_data = normalize_instance_payload(member) if member is not None else {}
            backend = member_data.get("storage_backend")
            kind = member_data.get("storage_kind")
            known_backends = {"s3", "http", "https", "url"}
            known_kinds = {"object", "prefix"}
            known_child_types = {"artifact", "artifact_set"}
            items.append({
                "lineage_euid": edge.euid, "relationship_type": "artifact_set_member",
                "lineage_deleted": bool(edge.is_deleted), "lineage_record_revision": edge.record_revision,
                "lineage_created_at": timestamp(edge.created_dt), "lineage_modified_at": timestamp(edge.modified_dt),
                "child_missing": member is None,
                "child_euid": member.euid if member is not None else None,
                "child_type": literal(member.type, known_child_types) if member is not None else None,
                "unknown_child_type_sha256": digest(member.type) if member is not None and member.type not in known_child_types else None,
                "child_deleted": bool(member.is_deleted) if member is not None else None,
                "child_bstatus": literal(member.bstatus, {"active", "archived", "inactive", "deleted", "draft", "pending"}) if member is not None else None,
                "child_record_revision": member.record_revision if member is not None else None,
                "child_created_at": timestamp(member.created_dt) if member is not None else None,
                "child_modified_at": timestamp(member.modified_dt) if member is not None else None,
                "same_domain_as_set": member.domain_code == parent.domain_code if member is not None else None,
                "same_issuer_as_set": member.issuer_app_code == parent.issuer_app_code if member is not None else None,
                "storage_backend": literal(backend, known_backends),
                "unknown_storage_backend_sha256": None if isinstance(backend, str) and backend in known_backends else digest(backend),
                "storage_kind": literal(kind, known_kinds),
                "unknown_storage_kind_sha256": None if isinstance(kind, str) and kind in known_kinds else digest(kind),
                "coordinates_sha256": digest(coordinates(member)) if member is not None else None,
            })
        set_membership.append({
            "set_euid": parent.euid, "set_deleted": bool(parent.is_deleted),
            "set_record_revision": parent.record_revision,
            "set_created_at": timestamp(parent.created_dt), "set_modified_at": timestamp(parent.modified_dt),
            "share_parent_edges": [{"lineage_euid": edge.euid,
                "relationship_type": literal(edge.relationship_type, known_relationships),
                "unknown_relationship_type_sha256": None if edge.relationship_type in known_relationships else digest(edge.relationship_type),
                "lineage_deleted": bool(edge.is_deleted), "lineage_record_revision": edge.record_revision,
                "lineage_created_at": timestamp(edge.created_dt), "lineage_modified_at": timestamp(edge.modified_dt)}
                for edge in entry["edges"]],
            "relationship_type": "artifact_set_member", "recursive": False,
            "read_limit": 1001, "member_limit": 1000, "complete": complete,
            "observed_edge_count": len(membership_rows), "returned_edge_count": len(items),
            "items": items,
        })
    grants = service._share_grants(session, share)
    grant_counts = {"email": 0, "domain": 0, "other": 0}
    grant_status_counts = {"active": 0, "revoked": 0, "superseded": 0, "other": 0}
    for grant in grants:
        rule = normalize_instance_payload(grant)
        kind = rule.get("recipient_type")
        grant_counts[kind if isinstance(kind, str) and kind in {"email", "domain"} else "other"] += 1
        status = rule.get("status")
        grant_status_counts[status if isinstance(status, str) and status in {"active", "revoked", "superseded"} else "other"] += 1
    typed_events = service._share_related(session, share, relationship="share_event", kind="share_event")
    return {
        "status": literal(data.get("status"), {"active", "revoked", "expired"}),
        "bstatus": literal(share.bstatus, {"active", "archived", "inactive", "deleted", "draft", "pending"}),
        "expires_at": expiry_value,
        "expires_at_invalid": expiry_value is None,
        "delivery_modes": safe_modes,
        "delivery_modes_invalid_type": not isinstance(modes, list),
        "unknown_delivery_mode_sha256": unknown_modes,
        "legacy_recipient_counts": {"email": count(data.get("allowed_users", [])),
            "domain": count(data.get("allowed_domains", [])), "group": count(data.get("allowed_groups", []))},
        "audience": literal(data.get("audience"), {"private", "recipients", "authenticated", "internal"}),
        "grant_count": len(grants),
        "grant_recipient_type_counts": grant_counts,
        "grant_status_counts": grant_status_counts,
        "legacy_audit_event_count": count(data.get("audit_events", [])),
        "typed_audit_event_count": len(typed_events),
        "parent_lineage": parent_lineage,
        "artifact_set_parent_membership": set_membership,
        "metadata_reference_evidence": {
            "target_kind": literal(data.get("target_kind"), {"artifact_object", "artifact_prefix", "artifact_set", "mixed_set"}),
            "target_euid_present": bool(data.get("target_euid")),
            "targets_count": count(data.get("targets", [])),
            "authoritative": False,
        },
    }


def snapshot(service, session):
    rows, ambiguous = [], []
    for share in service._share_query(session).order_by("euid").all():
        data = normalize_instance_payload(share)
        members = service._share_members(session, share)
        direct_members = sorted(member.euid for member in members)
        basis = None
        try:
            members, basis = _conversion_scope(service, session, share)
            proposal = _proposal(service, session, share, members=members)
        except (ValueError, KeyError, TypeError) as exc:
            proposal = None
            ambiguous.append({"euid": share.euid, "reason": str(exc)})
        rows.append({"euid": share.euid, "record_revision": share.record_revision,
            "payload_sha256": digest(data), "member_euids": sorted(m.euid for m in members),
            "direct_member_euids": direct_members, "conversion_basis": basis,
            "legacy_audit_sha256": digest(data.get("audit_events") or []),
            "member_coordinates_sha256": digest([{ "euid": m.euid, "payload": normalize_instance_payload(m)} for m in sorted(members, key=lambda m: m.euid)]),
            "proposal": proposal, "audit_event_count": len(data.get("audit_events") or []),
            "disposition_evidence": _disposition_evidence(service, session, share, data)})
    return {"format": "dewey.sharing-upgrade/v2", "disposition_evidence_version": 3,
        "database": identity(session), "domain_code": service.backend.domain_code,
        "shares": rows, "ambiguous": ambiguous}


def inventory(service):
    with service.backend.session_scope(commit=False) as session:
        result = snapshot(service, session)
    return {**result, "inventory_sha256": digest(result)}


def apply(service, reviewed, expected_sha256):
    from daylily_tapdb import generic_instance
    unsigned = {k: v for k, v in reviewed.items() if k != "inventory_sha256"}
    if digest(unsigned) != reviewed.get("inventory_sha256") or reviewed.get("inventory_sha256") != expected_sha256:
        raise ValueError("Reviewed inventory digest does not match")
    if reviewed.get("ambiguous"):
        raise ValueError("Ambiguous inventory records require explicit disposition before apply")
    with service.backend.session_scope(commit=True) as session:
        service.backend.ensure_templates(session, template_codes=(GRANT_TEMPLATE, EVENT_TEMPLATE))
        service.backend.lock_external_key(session, operation="sharing.upgrade", key="schema-v2")
        # Lock all reviewed shares before comparing their native revisions and member coordinates.
        service._share_query(session).with_for_update().all()
        _lock_inventory_authority(service, session, reviewed)
        current = snapshot(service, session)
        if current != unsigned:
            raise ValueError("Sharing inventory changed; review a new inventory")
        changed = []
        historical_set_conversions = []
        for row in current["shares"]:
            if row["proposal"] is None: continue
            share = service._share_query(session).filter(generic_instance.euid == row["euid"]).one()
            old = normalize_instance_payload(share)
            proposal = dict(row["proposal"])
            grants = proposal.pop("grants")
            members, basis = _conversion_scope(service, session, share)
            if basis != row["conversion_basis"] or sorted(member.euid for member in members) != row["member_euids"]:
                raise ValueError("Reviewed authority changed before canonical member creation")
            new_member_lineages = []
            if basis["kind"] == "historical_set_membership":
                for member in members:
                    edge = service.backend.create_lineage(session, parent=member, child=share, relationship_type="has_share")
                    new_member_lineages.append({"lineage_euid": edge.euid, "member_euid": member.euid})
            service._write_grants(session, share, grants, members, 1)
            for index, event in enumerate(old.get("audit_events") or []):
                # Preserve historical events as append-only typed records without copying credentials.
                service._event(session, share, event_type="historical_share_event", decision=str(event.get("decision", "unknown")),
                    details={"source_event_index": index, "policy_revision": 1, "reason": event.get("denial_reason"), "outcome": "historical_import",
                        "historical_timestamp": event.get("timestamp"), "historical_actor": event.get("actor_email"),
                        "historical_route": event.get("route")})
            service.backend.update_instance_json(session, share, {**proposal, "policy_revision": 1,
                "canonical_upgrade_inventory": expected_sha256, "canonical_upgraded_at": utc_now_iso(),
                "canonical_upgrade_basis": basis, "canonical_upgrade_member_lineages": new_member_lineages})
            service._event(session, share, event_type="canonical_upgrade", decision="change",
                details={"policy_revision": 1, "action": basis["kind"], "reason": "Reviewed native authority SHA256 " + digest(basis)})
            for edge in new_member_lineages:
                member = next(member for member in members if member.euid == edge["member_euid"])
                service._event(session, share, event_type="canonical_member_link_created", decision="change", target=member,
                    details={"policy_revision": 1, "action": "historical_set_membership", "reason": edge["lineage_euid"]})
            changed.append(share.euid)
            if basis["kind"] == "historical_set_membership":
                historical_set_conversions.append({"share_euid": share.euid, "set_euid": basis["set"]["euid"],
                    "conversion_basis_sha256": digest(basis), "member_euids": sorted(member.euid for member in members),
                    "new_member_lineages": new_member_lineages})
        marker = service.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE, field="policy_kind", value="sharing_schema", for_update=True)
        values = {"policy_kind": "sharing_schema", "schema_version": 2, "status": "applied",
            "inventory_sha256": expected_sha256, "applied_at": utc_now_iso()}
        if marker is None:
            marker = service.backend.create_instance(session, template_code=POLICY_TEMPLATE, name="Canonical sharing schema", json_addl=values)
        else:
            service.backend.update_instance_json(session, marker, values)
        return {"status": "applied", "inventory_sha256": expected_sha256, "changed_share_euids": changed,
            "historical_set_conversions": historical_set_conversions, "readiness": "blocked_until_verify"}


def verify(service, reviewed, expected_sha256):
    if reviewed.get("inventory_sha256") != expected_sha256 or digest({k: v for k, v in reviewed.items() if k != "inventory_sha256"}) != expected_sha256:
        raise ValueError("Reviewed inventory digest does not match")
    with service.backend.session_scope(commit=True) as session:
        service.backend.lock_external_key(session, operation="sharing.upgrade", key="schema-v2")
        marker = service.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE, field="policy_kind", value="sharing_schema", for_update=True)
        if marker is None or normalize_instance_payload(marker).get("inventory_sha256") != expected_sha256:
            raise ValueError("No matching applied upgrade")
        service._share_query(session).with_for_update().all()
        _lock_inventory_authority(service, session, reviewed)
        result = snapshot(service, session)
        if result["database"] != reviewed["database"] or result["domain_code"] != reviewed["domain_code"]:
            raise ValueError("Database identity changed")
        expected = {r["euid"]: r for r in reviewed["shares"]}
        if {r["euid"] for r in result["shares"]} != set(expected):
            raise ValueError("Share inventory changed during cutover")
        historical_set_conversions = []
        for row in result["shares"]:
            before = expected[row["euid"]]
            if row["member_euids"] != before["member_euids"] or row["member_coordinates_sha256"] != before["member_coordinates_sha256"]:
                raise ValueError("Reviewed member identity or coordinates changed")
            if row["proposal"] is not None:
                raise ValueError("An unconverted share remains")
            proposal = before.get("proposal")
            if proposal is not None:
                share = service._share_query(session).filter_by(euid=row["euid"]).one()
                data = normalize_instance_payload(share)
                if any(data.get(k) != v for k, v in proposal.items() if k != "grants"):
                    raise ValueError("Converted policy differs from the reviewed proposal")
                basis = before["conversion_basis"]
                if data.get("canonical_upgrade_basis") != basis:
                    raise ValueError("Persisted conversion basis differs from the reviewed native authority")
                if digest(data.get("audit_events") or []) != before["legacy_audit_sha256"]:
                    raise ValueError("Original historical audit evidence changed")
                prior_edges = {item["lineage_euid"]: item for item in before["disposition_evidence"]["parent_lineage"]}
                current_edges = {item["lineage_euid"]: item for item in row["disposition_evidence"]["parent_lineage"]}
                if any(current_edges.get(euid) != edge for euid, edge in prior_edges.items()):
                    raise ValueError("Original share authority lineage was not preserved")
                new_links = data.get("canonical_upgrade_member_lineages")
                if not isinstance(new_links, list):
                    raise ValueError("Canonical member conversion receipt is missing")
                if basis["kind"] == "historical_set_membership":
                    _, observed_basis = _historical_set_scope(service, session, share, canonical_members=before["member_euids"])
                    if observed_basis != basis:
                        raise ValueError("Historical set source authority changed during cutover")
                    if len(new_links) != len(before["member_euids"]) or {link["member_euid"] for link in new_links} != set(before["member_euids"]):
                        raise ValueError("Canonical member linkage differs from the complete reviewed set")
                elif new_links:
                    raise ValueError("Direct-member shares must not acquire membership from a set")
                if set(current_edges) - set(prior_edges) != {link["lineage_euid"] for link in new_links}:
                    raise ValueError("Unexpected added share authority relationships")
                for link in new_links:
                    edge = current_edges[link["lineage_euid"]]
                    if edge["relationship_type"] != "has_share" or edge["parent_euid"] != link["member_euid"] or edge["parent_type"] != "artifact" or edge["lineage_deleted"] or edge["parent_deleted"]:
                        raise ValueError("A created canonical member relationship is invalid")
                if basis["kind"] == "historical_set_membership":
                    historical_set_conversions.append({"share_euid": share.euid, "set_euid": basis["set"]["euid"],
                        "conversion_basis_sha256": digest(basis), "member_euids": before["member_euids"],
                        "new_member_lineages": new_links})
                observed = []
                for grant in service._share_grants(session, share):
                    rule = normalize_instance_payload(grant)
                    if rule.get("status") != "active": continue
                    observed.append({k: rule[k] for k in ("recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at")})
                    observed[-1]["target_euids"] = sorted(t.euid for t in service._grant_targets(session, grant))
                proposed = [{**g, "target_euids": sorted(g["target_euids"])} for g in proposal["grants"]]
                if sorted(observed, key=digest) != sorted(proposed, key=digest):
                    raise ValueError("Converted grants differ from reviewed predicates or target lineage")
                events = service._share_related(session, share, relationship="share_event", kind="share_event")
                imported = [e for e in events if normalize_instance_payload(e).get("event_type") == "historical_share_event"]
                if len(imported) != before["audit_event_count"]:
                    raise ValueError("Historical audit import count differs")
        if result["ambiguous"]:
            raise ValueError("Canonical share verification found ambiguous records")
        service.backend.update_instance_json(session, marker, {"status": "verified", "verified_at": utc_now_iso()})
        return {"status": "verified", "inventory_sha256": expected_sha256, "share_count": len(result["shares"]),
            "historical_set_conversions": historical_set_conversions, "readiness": "ready"}
