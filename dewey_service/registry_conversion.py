"""Explicit, reversible Dewey 10 policy/kind conversion. Never runs at startup.

Plan files retain only affected fields and protected ownership predicates. Store
them privately on the operator host; publish their hashes and aggregate receipts.
Existing identities, coordinates, relationship edges and historical receipts are
neither reassigned nor rewritten by this conversion.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from daylily_tapdb import generic_instance, generic_instance_lineage
from sqlalchemy import text

from dewey_service.audit import authenticated_user_email_context, explicit_attribution_context
from contextlib import nullcontext
from dewey_service.registry_access import POLICY_TEMPLATE, Principal, default_policy, principal_context, validate_policy
from dewey_service.service import DeweyService
from dewey_service.tapdb_backend import TapDBBackend, normalize_instance_payload, utc_now_iso


FIELDS = ("storage_kind", "node_kind", "is_terminal")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_private(path: Path, value):
    if not path.is_absolute():
        raise ValueError("Manifest and receipt paths must be absolute")
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def identity(session):
    row = session.execute(text("SELECT current_database() AS database, current_schema() AS schema, inet_server_addr()::text AS server, inet_server_port() AS port, (SELECT oid FROM pg_database WHERE datname=current_database()) AS database_oid")).mappings().one()
    return dict(row)


def coordinates(record):
    data = normalize_instance_payload(record)
    return {"euid": record.euid, "template_uid": str(record.template_uid), "domain_code": record.domain_code,
        "issuer_app_code": record.issuer_app_code, "storage": {k: data.get(k) for k in
            ("storage_backend", "bucket", "key", "version_id", "storage_uri", "source_uri", "artifact_identity_key")}}


def projection(data):
    return {field: {"present": field in data, "value": data.get(field)} for field in FIELDS}


def plan(service, actor):
    rows, ambiguous = [], []
    with service.backend.session_scope(commit=False) as session:
        target = identity(session)
        records = service._registry_query(session, authorize=False).order_by(generic_instance.euid).all()
        for record in records:
            data = normalize_instance_payload(record)
            policies = service.backend.list_children(session, parent=record, relationship_type="registry_policy")
            if len(policies) > 1:
                ambiguous.append({"euid": record.euid, "reason": "Multiple registry policies"})
                continue
            owner_email = str(data.get("created_by_email") or data.get("owner_email") or "").strip().lower()
            owner_subject = str(data.get("owner_subject") or owner_email or "dewey:admin-stewardship")
            policy = default_policy(Principal(subject=owner_subject, email=owner_email))
            if data.get("visibility_scope") in {"private", "restricted"} or data.get("allowed_users") or data.get("allowed_domains") or data.get("allowed_groups"):
                scope = "private" if data.get("visibility_scope") == "private" else "recipients"
                audience = {"scope": scope, "users": data.get("allowed_users", []),
                    "domains": data.get("allowed_domains", []), "groups": data.get("allowed_groups", [])}
                policy.update(metadata=audience, download=copy.deepcopy(audience), explicit_restriction=True)
                try:
                    validate_policy({"metadata": audience, "download": audience})
                except ValueError as exc:
                    ambiguous.append({"euid": record.euid, "reason": "Existing audience requires individual resolution: " + str(exc)})
                    continue
            changes = {}
            if record.type == "artifact":
                kind = data.get("storage_kind")
                declared_owy = data.get("artifact_type") == "sequencing_run_dir" and data.get("producer_system") in {"owy", "offwithyou"}
                if declared_owy:
                    if data.get("storage_backend") != "s3" or not str(data.get("key", "")).endswith("/"):
                        ambiguous.append({"euid": record.euid, "reason": "Declared OWY directory lacks explicit S3 directory coordinates"})
                        continue
                    kind = "prefix"
                if kind not in {"object", "prefix"}:
                    ambiguous.append({"euid": record.euid, "reason": "Missing or invalid explicit storage_kind"})
                    continue
                if kind == "object" and data.get("node_kind") in {"directory", "prefix", "folder", "run_folder", "analysis_result_folder", "sample_folder"}:
                    ambiguous.append({"euid": record.euid, "reason": "Contradictory object and directory declaration"})
                    continue
                desired = {"storage_kind": kind, "node_kind": "folder" if kind == "prefix" else "file", "is_terminal": kind == "object"}
                changes = {k: v for k, v in desired.items() if data.get(k) != v}
            if changes or not policies:
                rows.append({"euid": record.euid, "record_type": record.type, "coordinates_sha256": digest(coordinates(record)),
                    "record_json_sha256": digest(record.json_addl),
                    "before": projection(data), "changes": changes, "initialize_policy": None if policies else policy,
                    "reason": "Declared producer contract / authoritative storage_kind; explicit access initialization"})
        record_count = len(records)
        inventory_sha256 = digest([record.euid for record in records])
    return {"format": "dewey.registry-conversion/v1", "created_at": utc_now_iso(), "actor": actor,
        "target": target, "rows": rows, "ambiguous": ambiguous, "record_count": record_count,
        "inventory_sha256": inventory_sha256,
        "preserved": ["EUIDs", "storage coordinates", "artifact identity keys", "existing lineage", "external references", "idempotency records", "historical receipts"]}


def apply(service, manifest, actor, *, expected_sha256, receipt_path):
    if digest(manifest) != expected_sha256 or manifest.get("format") != "dewey.registry-conversion/v1":
        raise ValueError("Conversion manifest digest or format differs from the reviewed input")
    if manifest.get("ambiguous"):
        raise ValueError("Ambiguous records require individual resolution before conversion")
    receipt = {"format": "dewey.registry-conversion-receipt/v1", "manifest_sha256": expected_sha256,
        "actor": actor, "started_at": utc_now_iso(), "target": manifest["target"], "rows": []}
    # A durable prepared receipt exists before any database mutation.
    prepared = receipt_path.with_name(receipt_path.name + ".prepared")
    write_private(prepared, receipt)
    with service.backend.session_scope(commit=True) as session:
        if identity(session) != manifest["target"]:
            raise ValueError("Conversion database identity changed")
        service.backend.ensure_templates(session)
        inventory = service._registry_query(session, authorize=False).order_by(generic_instance.euid).all()
        if len(inventory) != manifest["record_count"] or digest([record.euid for record in inventory]) != manifest["inventory_sha256"]:
            raise ValueError("Registry inventory changed since review; stop writers and re-plan")
        for entry in manifest["rows"]:
            record = service._registry_query(session, authorize=False).filter(generic_instance.euid == entry["euid"]).with_for_update().one()
            data = normalize_instance_payload(record)
            if digest(coordinates(record)) != entry["coordinates_sha256"] or projection(data) != entry["before"] or digest(record.json_addl) != entry["record_json_sha256"]:
                raise ValueError(f"Record changed since review: {record.euid}")
            policies = service.backend.list_children(session, parent=record, relationship_type="registry_policy")
            if entry["initialize_policy"] and policies:
                raise ValueError(f"Policy already exists for {record.euid}; re-plan explicitly")
            policy = None
            if entry["initialize_policy"]:
                policy = service.backend.create_instance(session, template_code=POLICY_TEMPLATE, name=f"Access for {record.euid}",
                    json_addl={**entry["initialize_policy"], "conversion_manifest_sha256": expected_sha256,
                        "initialized_by": actor, "initialized_at": utc_now_iso()})
                service.backend.create_lineage(session, parent=record, child=policy, relationship_type="registry_policy")
            if entry["changes"]:
                service.backend.update_instance_json(session, record, entry["changes"])
            receipt["rows"].append({"euid": record.euid, "policy_euid": policy.euid if policy else None,
                "policy_sha256": digest(normalize_instance_payload(policy)) if policy else None,
                "after": projection(normalize_instance_payload(record)), "coordinates_sha256": entry["coordinates_sha256"]})
        receipt["completed_at"] = utc_now_iso()
        # Write reversal identity evidence before commit. A crash leaves a clearly marked
        # prepared receipt; inspect the database before any retry or rollback.
        write_private(receipt_path.with_name(receipt_path.name + ".pending-commit"), receipt)
    receipt["status"] = "committed"
    write_private(receipt_path, receipt)
    return {"status": "committed", "records": len(receipt["rows"]), "manifest_sha256": expected_sha256,
        "receipt_sha256": digest(receipt), "receipt_path": str(receipt_path)}


def reverse(service, manifest, receipt, actor, *, expected_sha256):
    if digest(manifest) != expected_sha256 or receipt.get("manifest_sha256") != expected_sha256 or receipt.get("status") != "committed":
        raise ValueError("Reversal requires the exact manifest and committed receipt")
    by_euid = {entry["euid"]: entry for entry in receipt["rows"]}
    with service.backend.session_scope(commit=True) as session:
        if identity(session) != manifest["target"] or receipt["target"] != manifest["target"]:
            raise ValueError("Reversal database identity changed")
        for entry in manifest["rows"]:
            done = by_euid[entry["euid"]]
            record = service._registry_query(session, authorize=False).filter(generic_instance.euid == entry["euid"]).with_for_update().one()
            data = normalize_instance_payload(record)
            if digest(coordinates(record)) != done["coordinates_sha256"] or projection(data) != done["after"]:
                raise ValueError(f"Record changed after conversion: {record.euid}; individual reversal required")
            if done["policy_euid"]:
                policy = service.backend.find_by_euid(session, template_code=POLICY_TEMPLATE, euid=done["policy_euid"], for_update=True)
                if policy is None or digest(normalize_instance_payload(policy)) != done["policy_sha256"]:
                    raise ValueError(f"Policy changed after conversion: {record.euid}; individual reversal required")
                edges = session.query(generic_instance_lineage).filter(generic_instance_lineage.parent_instance_uid == record.uid,
                    generic_instance_lineage.child_instance_uid == policy.uid, generic_instance_lineage.relationship_type == "registry_policy",
                    generic_instance_lineage.is_deleted.is_(False)).all()
                if len(edges) != 1:
                    raise ValueError("Policy lineage changed after conversion")
                service.backend.delete_persisted(session, edges[0])
                service.backend.delete_persisted(session, policy)
            raw = dict(record.json_addl)
            for field in entry["changes"]:
                before = entry["before"][field]
                if before["present"]:
                    raw[field] = before["value"]
                else:
                    raw.pop(field, None)
            service.backend.update_persisted_fields(session, record, {"json_addl": raw})
        session.flush()
    return {"status": "reversed", "records": len(manifest["rows"]), "actor": actor,
        "manifest_sha256": expected_sha256, "completed_at": utc_now_iso(), "storage_deleted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["plan", "apply", "reverse"])
    parser.add_argument("--actor", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--attribution", type=Path)
    args = parser.parse_args(argv)
    if args.mode != "plan" and (args.attribution is None or not args.attribution.is_absolute()):
        parser.error("Writes require --attribution with an explicit absolute native Attribution JSON path")
    service = DeweyService(TapDBBackend(app_username=args.actor))
    with (explicit_attribution_context(args.attribution) if args.attribution else nullcontext()), principal_context(Principal(subject=args.actor, roles=("ADMIN",), internal=True), maintenance=True), authenticated_user_email_context(args.actor if "@" in args.actor else None):
        if args.mode == "plan":
            result = plan(service, args.actor)
            write_private(args.manifest, result)
            print(json.dumps({"status": "planned", "records": result["record_count"], "changes": len(result["rows"]),
                "ambiguous": len(result["ambiguous"]), "manifest_sha256": digest(result), "manifest_path": str(args.manifest)}))
        else:
            if not args.receipt or not args.expected_sha256:
                parser.error("apply/reverse require --receipt and --expected-sha256")
            manifest = json.loads(args.manifest.read_text())
            result = apply(service, manifest, args.actor, expected_sha256=args.expected_sha256, receipt_path=args.receipt) if args.mode == "apply" else reverse(service, manifest, json.loads(args.receipt.read_text()), args.actor, expected_sha256=args.expected_sha256)
            print(json.dumps(result))


if __name__ == "__main__":
    main()
