"""QEO2-only MultiQC registration and internal webshare capability.

The credential is accepted by the report-source and report-evidence routes,
never by the general registry or human
sharing routes. The target scope exists only while this server-owned operation
runs. Existing private target/ancestor policies and native share lifecycle apply.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import secrets
from typing import Literal
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field

SUBJECT = "qeo2:multiqc-source"
_TARGET = ContextVar("qeo_source_target", default=None)
_REFERENCE_TARGET = ContextVar("qeo_evidence_reference_target", default=None)


class QeoSourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["artifact", "source"]
    value: str = Field(min_length=1)


class QeoEvidenceReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_artifact_euid: str = Field(min_length=1)
    evidence_euid: str = Field(min_length=1)
    tenant_id: UUID
    canonical_uri: str = Field(min_length=1)


def current_reference_target():
    from dewey_service.registry_access import current_principal
    actor = current_principal()
    return _REFERENCE_TARGET.get() if actor and actor.service and actor.subject == SUBJECT else None


def require_allowed_source(settings, uri):
    location = urlsplit(uri)
    if location.scheme != "s3" or not location.netloc or not location.path or location.query or location.fragment:
        raise ValueError("QEO source must name an exact S3 report object")
    if not any(root.endswith("/") and uri.startswith(root) for root in settings.qeo_source_s3_roots):
        raise HTTPException(403, "Report is outside the configured QEO production source roots")


def link_evidence(service, settings, body):
    """Accept the authenticated QEO2 owner's persisted evidence identity.

    This capability can only attach a QEO2 evidence reference to one source
    report; it cannot edit report content, policy, or arbitrary relationships.
    """
    artifact = service.get_artifact(body.report_artifact_euid)
    require_allowed_source(settings, artifact["storage_uri"])
    location = urlsplit(body.canonical_uri)
    if location.scheme != "https" or not location.netloc or location.username or location.password:
        raise ValueError("QEO2 evidence URL must use HTTPS")
    token = _REFERENCE_TARGET.set(body.report_artifact_euid)
    try:
        _, external = service.create_external_object(
            external_system="qeo2", external_object_type="evidence",
            external_object_id=body.evidence_euid, external_uri=body.canonical_uri,
            metadata={"assertion_authority": "qeo2.persisted_evidence_receipt"},
            reference_target={"kind": "tapdb_object", "target_tenant_id": str(body.tenant_id)},
            idempotency_key="qeo2-evidence:" + body.evidence_euid)
        _, relation = service.attach_external_object_relation(
            target_type="artifact", target_euid=body.report_artifact_euid,
            external_object_euid=external["external_object_euid"], relation_type="qeo2_evidence",
            metadata={"assertion_authority": "qeo2.persisted_evidence_receipt"},
            idempotency_key="qeo2-report-evidence:" + body.report_artifact_euid + ":" + body.evidence_euid)
        return {"external_object": external, "relation": relation}
    finally:
        _REFERENCE_TARGET.reset(token)


def issue_source_credential(path: Path, *, lifetime_days: int):
    from datetime import timedelta
    if not path.is_absolute() or not 1 <= lifetime_days <= 366:
        raise ValueError("An absolute output path and 1..366 day lifetime are required")
    token="dewey_qeo_source_"+secrets.token_urlsafe(48)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as stream:stream.write(token+"\n")
    return {"principal":SUBJECT,"scope":"multiqc:register-internal-webshare","token_file":str(path),
            "token_sha256":hashlib.sha256(token.encode()).hexdigest(),
            "expires_at":(datetime.now(timezone.utc)+timedelta(days=lifetime_days)).isoformat()}


def require_qeo_source_auth(settings):
    bearer=HTTPBearer(auto_error=False)
    def authenticate(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        try:
            expires=datetime.fromisoformat(settings.qeo_source_token_expires_at)
            valid=expires.tzinfo is not None and expires>datetime.now(timezone.utc)
        except (ValueError,TypeError):valid=False
        if not settings.qeo_source_token_sha256 or not valid or not settings.qeo_source_s3_roots:
            raise HTTPException(503,"QEO source capability is not configured or has expired")
        supplied=credentials.credentials if credentials else ""
        if not supplied.startswith("dewey_qeo_source_") or not secrets.compare_digest(hashlib.sha256(supplied.encode()).hexdigest(),settings.qeo_source_token_sha256):
            raise HTTPException(401,"Invalid QEO source credential")
        return SUBJECT
    return authenticate


def current_target():
    from dewey_service.registry_access import current_principal
    actor=current_principal()
    return _TARGET.get() if actor and actor.service and actor.subject==SUBJECT else None


@contextmanager
def target_context(euid):
    token=_TARGET.set(euid)
    try:yield
    finally:_TARGET.reset(token)


def share_target_clause(model):
    """Read only shares whose current authoritative revision targets this report."""
    from sqlalchemy import exists, literal, select
    from sqlalchemy.orm import aliased
    from daylily_tapdb import generic_instance, generic_instance_lineage
    target=current_target()
    if not target:return literal(False)
    scope,member=aliased(generic_instance),aliased(generic_instance)
    parent,edge=aliased(generic_instance_lineage),aliased(generic_instance_lineage)
    return exists(select(literal(1)).select_from(parent).join(scope,scope.uid==parent.child_instance_uid)
        .join(edge,edge.parent_instance_uid==scope.uid).join(member,member.uid==edge.child_instance_uid)
        .where(model.json_addl["member_count"].astext=="1",parent.parent_instance_uid==model.uid,parent.relationship_type=="share_revision",parent.is_deleted.is_(False),
            scope.is_deleted.is_(False),scope.type=="share_revision",scope.json_addl["policy_revision"].astext==model.json_addl["policy_revision"].astext,
            edge.relationship_type=="share_revision_target",edge.is_deleted.is_(False),member.is_deleted.is_(False),member.euid==target)).correlate(model)


def ensure_source(service, settings, body):
    from dewey_service.multiqc_bundle import saved_bundle
    from dewey_service.tapdb_backend import normalize_instance_payload
    from dewey_service.registry_access import require_record
    from dewey_service.services.share_policy import expiry
    def allowed(uri):
        require_allowed_source(settings, uri)
    if body.kind=="source":
        allowed(body.value)
        from daylily_tapdb import generic_instance
        # Resolve the exact declared source using native registry visibility.
        # A persisted complete registration is the owning result: do not read
        # or register its report/dependencies again merely to create a share.
        with service.backend.session_scope(commit=False) as session:
            matches=service._registry_query(session,scopes=("artifact",)).filter(
                generic_instance.json_addl["storage_uri"].astext==body.value,
                generic_instance.json_addl["storage_kind"].astext=="object").limit(2).all()
            if len(matches)>1:
                raise ValueError("Multiple registered versions exist at this source; specify the exact Dewey artifact EUID")
            artifact=(service._artifact_response(matches[0]) if matches and
                      saved_bundle(normalize_instance_payload(matches[0])) is not None else None)
        if artifact is None:
            _,artifact=service.import_artifact_from_uri(artifact_type="multiqc_report",source_uri=body.value,
                import_mode="reference",metadata={"registration_purpose":"QEO2 source MultiQC"},producer_system="qeo2",
                idempotency_key="qeo2-source-report:"+hashlib.sha256(body.value.encode()).hexdigest())
    else:
        artifact=service.get_artifact(body.value)
        allowed(artifact["storage_uri"])
    euid=artifact["artifact_euid"]
    with target_context(euid):
        # The capability does not override private targets or protected ancestors.
        with service.backend.session_scope(commit=False) as session:
            record=service._registry_record(session,euid,action="download")
            if saved_bundle(normalize_instance_payload(record)) is None:
                raise ValueError("The artifact lacks Dewey's complete MultiQC registration; register its exact S3 report source")
            require_record(service.backend,session,record,"share")
        shares=service.list_shares(target_kind="artifact_object",target_euid=euid,limit=2000)
        now=datetime.now(timezone.utc)
        eligible=[s for s in shares if s["status"]=="active" and expiry(s["expires_at"])>now
                  and s["content_mode"]=="www" and euid in s.get("report_bundles",{}) and len(s["members"])==1]
        if eligible:
            share=eligible[0]
        else:
            # Native lifetime policy remains authoritative: service shares default to 14 days.
            _,share=service.create_share(target_kind="artifact_object",target_euid=euid,
                name="QEO2 MultiQC source",purpose="Internal source evidence for QEO2",content_mode="www",
                audience="recipients",allowed_users=[],allowed_domains=["lsmc.com","lsmc.bio"],
                idempotency_key="qeo2-source-webshare:"+euid)
        if share["status"]!="active" or expiry(share["expires_at"])<=now:
            raise ValueError("QEO source webshare is inactive; use Dewey's explicit lifecycle controls")
        return {"report_artifact_euid":euid,"webshare_euid":share["euid"],
                "report_url":settings.share_application_origin.rstrip("/")+share["fetch_path"],
                "policy_revision":share["policy_revision"],"expires_at":share["expires_at"],
                "provenance":"Dewey QEO2 source capability; native registration, lineage and webshare receipt"}
