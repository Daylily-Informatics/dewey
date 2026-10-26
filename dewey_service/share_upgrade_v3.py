"""Explicit preserving sharing conversion. No cutoff, retirement, or startup migration."""
from __future__ import annotations

from dewey_service.registry_conversion import digest, identity
from dewey_service.registry_access import POLICY_TEMPLATE, maintenance_mode, principal
from dewey_service.services.share_policy import normalized_policy
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso, SHARE_REVISION_TEMPLATE, SHARE_ALIAS_TEMPLATE, ARTIFACT_LOCATION_REVISION_TEMPLATE


FORMAT = "dewey.sharing-upgrade/v3"


def _grant_fingerprint(service, session, grant):
    return {"euid": grant.euid, "record_revision": grant.record_revision,
            "payload_sha256": digest(grant.json_addl),
            "target_euids": sorted(t.euid for t in service._grant_targets(session, grant))}


def _record(service, session, share):
    from daylily_tapdb import generic_instance_lineage
    from sqlalchemy import or_
    data = normalize_instance_payload(share)
    members = service._share_members(session, share) if data.get("schema_version") == 3 else service._historical_share_members(session, share)
    authority_uids = [share.uid] + [g.uid for g in service._share_grants(session, share)]
    edges = session.query(generic_instance_lineage).filter(or_(generic_instance_lineage.parent_instance_uid.in_(authority_uids),
        generic_instance_lineage.child_instance_uid.in_(authority_uids))).order_by(generic_instance_lineage.euid).all()
    events = service._share_related(session, share, relationship="share_event", kind="share_event")
    return {"euid": share.euid, "schema_version": data.get("schema_version"), "record_revision": share.record_revision,
        "bstatus": share.bstatus, "status": data.get("status"), "payload_sha256": digest(share.json_addl),
        "members": [{"euid": m.euid, "record_revision": m.record_revision, "payload_sha256": digest(m.json_addl)} for m in sorted(members, key=lambda x:x.euid)],
        "grants": [_grant_fingerprint(service, session, g) for g in sorted(service._share_grants(session, share), key=lambda x:x.euid)],
        "history": [{"euid": e.euid, "record_revision": e.record_revision, "payload_sha256": digest(e.json_addl)} for e in sorted(events, key=lambda x:x.euid)],
        "lineage": [{"euid": e.euid, "record_revision": e.record_revision, "deleted": e.is_deleted} for e in edges]}


def _proposal(service, session, share):
    data = normalize_instance_payload(share)
    if data.get("schema_version") != 2:
        raise ValueError("An active share must already have an unambiguous schema-2 conversion")
    if type(data.get("policy_revision")) is not int or data["policy_revision"] < 1:
        raise ValueError("Share has no positive policy revision")
    if data.get("audience") not in {"recipients", "private"}:
        raise ValueError("Existing audience needs explicit review; never convert it to public_registered")
    members = service._historical_share_members(session, share)
    if not members:
        raise ValueError("Share has no authoritative native artifact members")
    values = []
    for grant in service._share_grants(session, share):
        rule = normalize_instance_payload(grant)
        if rule.get("status") != "active":
            continue
        if rule.get("policy_revision") != data["policy_revision"]:
            raise ValueError("Active grant revision differs from share revision")
        values.append({**{k:v for k,v in rule.items() if k in {"recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at"}},
            "target_euids": [t.euid for t in service._grant_targets(session, grant)]})
    proposal = normalized_policy({**data, "audience": "recipients", "content_mode": "download",
        "delivery_modes": ["gateway"], "grants": values}, share_expiry=data["expires_at"], member_euids=[m.euid for m in members])
    proposal.pop("grants")
    return proposal


def _snapshot(service, session):
    rows, ambiguous = [], []
    for share in service._share_query(session).order_by("euid").all():
        row = _record(service, session, share)
        if row["schema_version"] == 3:
            row["disposition"] = "already_v3"
        elif row["schema_version"] != 2 and (row["bstatus"] == "archived" or row["status"] in {"revoked", "retired", "expired"}):
            row["disposition"] = "preserve_inactive_history"
        else:
            row["disposition"] = "convert_preserving"
            try:
                row["proposal_sha256"] = digest(_proposal(service, session, share))
            except (ValueError, KeyError, TypeError) as exc:
                ambiguous.append({"euid": share.euid, "reason": str(exc)})
        rows.append(row)
    return {"format": FORMAT, "database": identity(session), "domain_code": service.backend.domain_code,
            "share_count": len(rows), "shares": rows, "ambiguous": ambiguous}


def inventory(service):
    with service.backend.session_scope(commit=False) as session:
        result = _snapshot(service, session)
        return {**result, "inventory_sha256": digest(result)}


def _reviewed(reviewed, expected_sha256):
    unsigned = {k:v for k,v in reviewed.items() if k != "inventory_sha256"}
    if reviewed.get("format") != FORMAT or digest(unsigned) != expected_sha256 or reviewed.get("inventory_sha256") != expected_sha256:
        raise ValueError("Reviewed schema-3 inventory digest or format differs")
    if reviewed.get("ambiguous"):
        raise ValueError("Ambiguous shares must be resolved before preserving conversion")
    if not maintenance_mode() or not principal().admin:
        raise ValueError("Conversion requires explicit administrator maintenance attribution")
    return unsigned


def _lock(service, session, reviewed):
    from daylily_tapdb import generic_instance, generic_instance_lineage
    service.backend.lock_external_key(session, operation="sharing.upgrade", key="schema-v3")
    # Lock every recorded authority node/edge before comparing the reviewed digest.
    euids = set()
    edges = set()
    for row in reviewed["shares"]:
        euids.add(row["euid"])
        euids.update(x["euid"] for name in ("members", "grants", "history") for x in row[name])
        edges.update(x["euid"] for x in row["lineage"])
    session.query(generic_instance).filter(generic_instance.euid.in_(sorted(euids))).order_by(generic_instance.euid).with_for_update().all()
    session.query(generic_instance_lineage).filter(generic_instance_lineage.euid.in_(sorted(edges))).order_by(generic_instance_lineage.euid).with_for_update().all()


def apply(service, reviewed, expected_sha256):
    unsigned = _reviewed(reviewed, expected_sha256)
    with service.backend.session_scope(commit=True) as session:
        _lock(service, session, reviewed)
        marker = service.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE, field="policy_kind", value="sharing_schema", for_update=True)
        if marker is None:
            raise ValueError("The verified schema-2 marker is required")
        previous = normalize_instance_payload(marker)
        if previous.get("schema_version") == 3:
            if previous.get("v3_inventory_sha256") != expected_sha256:
                raise ValueError("A different schema-3 conversion already exists")
            return {"status": previous["status"], "inventory_sha256": expected_sha256, "already_applied": True}
        if previous.get("schema_version") != 2 or previous.get("status") != "verified":
            raise ValueError("The verified schema-2 marker is required")
        if _snapshot(service, session) != unsigned:
            raise ValueError("Native sharing inventory changed; review a new inventory")
        service.backend.ensure_templates(session, template_codes=(SHARE_REVISION_TEMPLATE, SHARE_ALIAS_TEMPLATE, ARTIFACT_LOCATION_REVISION_TEMPLATE))
        receipts = []
        for row in reviewed["shares"]:
            if row["disposition"] != "convert_preserving":
                continue
            share = service._share_query(session).filter_by(euid=row["euid"]).one()
            data = normalize_instance_payload(share)
            proposal = _proposal(service, session, share)
            if digest(proposal) != row["proposal_sha256"]:
                raise ValueError("Share conversion proposal changed")
            members = service._historical_share_members(session, share)
            scope = service._write_share_revision(session, share, members, data["policy_revision"], policy={**proposal, "expires_at": data["expires_at"]})
            service.backend.update_instance_json(session, share, {**proposal, "v3_inventory_sha256": expected_sha256, "v3_converted_at": utc_now_iso()})
            event = service._event(session, share, event_type="schema3_converted", decision="change", details={"policy_revision": data["policy_revision"], "reason": "Preserving inventory " + expected_sha256})
            session.refresh(share)
            receipts.append({"share_euid": share.euid, "scope_euid": scope.euid, "event_euid": event,
                "payload_sha256": digest(share.json_addl), "record_revision": share.record_revision})
        service.backend.update_instance_json(session, marker, {"schema_version": 3, "status": "applied",
            "v3_inventory_sha256": expected_sha256, "v3_applied_at": utc_now_iso(), "v3_receipts": receipts,
            "v2_marker_sha256": digest(previous)})
        return {"status": "applied", "inventory_sha256": expected_sha256, "converted": len(receipts), "receipts": receipts,
                "retired": 0, "deleted": 0, "readiness": "blocked_until_verify"}


def verify(service, reviewed, expected_sha256):
    _reviewed(reviewed, expected_sha256)
    with service.backend.session_scope(commit=True) as session:
        _lock(service, session, reviewed)
        marker = service.backend.find_by_json_field(session, template_code=POLICY_TEMPLATE, field="policy_kind", value="sharing_schema", for_update=True)
        if marker is None:
            raise ValueError("No schema-3 conversion marker")
        marker_data = normalize_instance_payload(marker)
        if marker_data.get("schema_version") != 3 or marker_data.get("v3_inventory_sha256") != expected_sha256 or marker_data.get("status") not in {"applied", "verified"}:
            raise ValueError("No matching applied schema-3 conversion")
        if identity(session) != reviewed["database"] or service.backend.domain_code != reviewed["domain_code"]:
            raise ValueError("Database identity changed")
        shares = service._share_query(session).all()
        if {s.euid for s in shares} != {r["euid"] for r in reviewed["shares"]}:
            raise ValueError("Share inventory changed during cutover")
        receipts = {r["share_euid"]:r for r in marker_data["v3_receipts"]}
        for before in reviewed["shares"]:
            share = next(s for s in shares if s.euid == before["euid"])
            after = _record(service, session, share)
            if before["disposition"] != "convert_preserving":
                if any(after[k] != before[k] for k in after):
                    raise ValueError("An unchanged historical share was modified")
                continue
            receipt = receipts.get(share.euid)
            if receipt is None or after["schema_version"] != 3 or after["payload_sha256"] != receipt["payload_sha256"] or after["record_revision"] != receipt["record_revision"]:
                raise ValueError("Converted share differs from its applied receipt")
            for key in ("bstatus", "status", "members", "grants"):
                if before[key] != after[key]:
                    raise ValueError("Conversion changed existing lifecycle, targets, or grants")
            history = {r["euid"]:r for r in after["history"]}
            lineage = {r["euid"]:r for r in after["lineage"]}
            if any(history.get(r["euid"]) != r for r in before["history"]) or any(lineage.get(r["euid"]) != r for r in before["lineage"]):
                raise ValueError("Conversion rewrote existing history or lineage")
            if service._share_revision(session, share).euid != receipt["scope_euid"]:
                raise ValueError("Converted scope differs")
        service.backend.update_instance_json(session, marker, {"status": "verified", "v3_verified_at": utc_now_iso()})
        return {"status": "verified", "schema_version": 3, "inventory_sha256": expected_sha256,
                "share_count": len(shares), "converted": len(receipts), "retired": 0, "deleted": 0}
