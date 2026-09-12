"""Short-lived, isolated S3 report delivery with authorization on every asset."""
from __future__ import annotations

import hashlib
import hmac
import logging
import mimetypes
import re
import secrets
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from daylily_tapdb import generic_instance, generic_instance_lineage
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, literal

from dewey_service.registry_access import OPERATION_TEMPLATE, Principal, principal, principal_context, record_clause
from dewey_service.tapdb_backend import normalize_instance_payload, utc_now_iso


def redacted_path(path):
    return re.sub(r"(/previews/[^/]+/)[^/]+", r"\1[redacted]", path)


class PreviewLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(redacted_path(value) if isinstance(value, str) else value for value in record.args)
        if isinstance(record.msg, str):
            record.msg = redacted_path(record.msg)
        return True


def attach_report_preview(app, router, service):
    logging.getLogger("uvicorn.access").addFilter(PreviewLogFilter())

    @router.post("/records/{euid}/preview", tags=["EUID registry"])
    def create_preview(euid: str):
        actor = principal()
        with service.backend.session_scope(commit=True) as session:
            record = service._registry_record(session, euid, action="download")
            data = normalize_instance_payload(record)
            if data.get("storage_kind") != "object" or data.get("storage_backend") != "s3":
                raise ValueError("Report preview requires an S3 Object EUID")
            bucket, key = data["bucket"], data["key"]
            if not key.lower().endswith((".html", ".htm")):
                raise ValueError("Report preview supports HTML reports")
            service.require_storage_access(bucket, key, action="download", session=session)
            # Relative report assets live beneath this exact folder. Any registered
            # restriction is checked again for each asset; never enumerate the folder.
            root, separator, filename = key.rpartition("/")
            root = root + separator
            prefix = service._registry_query(session, scopes=("artifact",), authorize=False).filter(
                generic_instance.json_addl["storage_backend"].astext == "s3",
                generic_instance.json_addl["storage_kind"].astext == "prefix",
                generic_instance.json_addl["bucket"].astext == bucket,
                generic_instance.bstatus != "archived",
                func.left(literal(key), func.length(generic_instance.json_addl["key"].astext)) == generic_instance.json_addl["key"].astext,
                record_clause(session, generic_instance, "download"),
            ).order_by(func.length(generic_instance.json_addl["key"].astext).desc()).first()
            if prefix is not None:
                root = normalize_instance_payload(prefix)["key"]
            filename = key[len(root):]
            secret = secrets.token_urlsafe(32)
            ttl = min(900, service.registry_defaults()["delivery_lifetime_seconds"])
            expires = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            operation = service.backend.create_instance(session, template_code=OPERATION_TEMPLATE,
                name="Isolated report preview", json_addl={"operation": "report_preview", "actor": actor.subject,
                    "principal": asdict(actor), "token_sha256": hashlib.sha256(secret.encode()).hexdigest(),
                    "bucket": bucket, "root": root, "report_key": key, "version_id": data.get("version_id"),
                    "created_at": utc_now_iso(), "expires_at": expires.isoformat(), "status": "issued"})
            service.backend.create_lineage(session, parent=record, child=operation, relationship_type="has_storage_operation")
            path = f"/previews/{quote(operation.euid, safe='')}/{secret}/{quote(filename, safe='/')}"
            return {"euid": euid, "preview_path": path, "expires_in": ttl,
                "receipt_euid": operation.euid, "download_completion_observed": False}

    @app.get("/previews/{operation_euid}/{token}/{asset_path:path}", include_in_schema=False)
    def preview_asset(operation_euid: str, token: str, asset_path: str, request: Request):
        if not asset_path or asset_path.startswith("/") or any(part in {".", ".."} for part in asset_path.split("/")):
            raise HTTPException(400, "Invalid report asset path")
        with service.backend.session_scope(commit=False) as session:
            template = service.backend.templates.get_template(session, OPERATION_TEMPLATE, domain_code=service.backend.domain_code)
            operation = session.query(generic_instance).filter(generic_instance.template_uid == template.uid,
                generic_instance.euid == operation_euid, generic_instance.is_deleted.is_(False)).first()
            if operation is None:
                raise HTTPException(404, "Preview not available")
            data = normalize_instance_payload(operation)
            if data.get("operation") != "report_preview" or data.get("status") != "issued" or not hmac.compare_digest(
                    str(data.get("token_sha256", "")), hashlib.sha256(token.encode()).hexdigest()):
                raise HTTPException(404, "Preview not available")
            if datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                raise HTTPException(410, "Preview expired; reopen it from Dewey")
            sources = session.query(generic_instance).join(generic_instance_lineage,
                generic_instance_lineage.parent_instance_uid == generic_instance.uid).filter(
                generic_instance_lineage.child_instance_uid == operation.uid,
                generic_instance_lineage.relationship_type == "has_storage_operation",
                generic_instance_lineage.is_deleted.is_(False), generic_instance.is_deleted.is_(False)).all()
            if len(sources) != 1:
                raise HTTPException(409, "Preview source relationship is unavailable")
            actor = Principal(**data["principal"])
            key = data["root"] + asset_path
            with principal_context(actor):
                service._registry_record(session, sources[0].euid, action="download")
                service.require_storage_access(data["bucket"], key, action="download", session=session)
                stream, content_type = service._require_storage().open_object(
                    bucket=data["bucket"], key=key,
                    version_id=data.get("version_id") if key == data["report_key"] else None)
        origin = str(request.base_url).rstrip("/")
        asset_root = origin + f"/previews/{quote(operation_euid, safe='')}/{quote(token, safe='')}/"
        headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff", "Access-Control-Allow-Origin": "*",
            "Content-Security-Policy": "sandbox allow-scripts; default-src 'none'; "
                f"script-src 'unsafe-inline' 'unsafe-eval' {asset_root}; style-src 'unsafe-inline' {asset_root}; "
                f"img-src data: blob: {asset_root}; font-src data: {asset_root}; connect-src {asset_root}; "
                "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"}
        media = mimetypes.guess_type(key)[0] or content_type or "application/octet-stream"
        def chunks():
            try:
                yield from stream.iter_chunks(chunk_size=256 * 1024)
            finally:
                stream.close()
        return StreamingResponse(chunks(), media_type=media, headers=headers)
