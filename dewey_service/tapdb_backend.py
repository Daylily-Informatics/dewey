"""TapDB backend wiring for Dewey artifact persistence."""

from __future__ import annotations

import datetime as dt
import inspect
from contextlib import contextmanager
from hashlib import sha256
from time import monotonic
from typing import Any, Generator, Optional, cast

from daylily_tapdb import (
    InstanceFactory,
    TemplateManager,
    generic_instance,
    generic_instance_lineage,
)
from daylily_tapdb.web.runtime import get_db
from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from dewey_service.audit import creation_audit_fields, update_audit_fields, transaction_attribution
from daylily_tapdb.revisions import RevisionConflict
from daylily_tapdb.services.object_operations import ObjectSelector, update_object, soft_delete_object
from fastapi import HTTPException
from dewey_service.integrations.tapdb_runtime import ensure_tapdb_version, load_runtime_config
from dewey_service.settings import get_settings
from dewey_service.ui_metadata import resolve_package_version
from dewey_service.registry_access import (
    POLICY_TEMPLATE, TOKEN_TEMPLATE, OPERATION_TEMPLATE, default_policy,
    maintenance_mode, principal, require_record, visibility_clause,
)

SERVICE_VERSION = resolve_package_version()


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    payload = str(value).encode("utf-8")
    return sha256(payload).hexdigest()


def validate_instance_envelope(payload: Any) -> dict[str, Any]:
    """Require TapDB's object properties while retaining Dewey's flat app fields."""
    if not isinstance(payload, dict) or not isinstance(payload.get("properties"), dict):
        raise ValueError("Dewey instances require json_addl.properties to be an object")
    properties = payload["properties"]
    if any(
        key in {"object_euid", "target_object_euid"} or key.endswith("_object_euid")
        for key in properties
    ):
        raise ValueError("External relationships require canonical TapDB XRF lineage")
    external_payload = properties.get("external_payload")
    if isinstance(external_payload, dict) and "tapdb_graph" in external_payload:
        raise ValueError("Metadata tapdb_graph is unsupported; use canonical TapDB XRF lineage")
    return dict(payload)


def _parse_template_code(template_code: str) -> tuple[str, str, str, str]:
    parts = template_code.strip("/").split("/")
    if len(parts) != 4:
        raise ValueError(f"Invalid template code: {template_code}")
    return parts[0], parts[1], parts[2], parts[3]


DEWEY_TEMPLATE_EUID_PREFIX = "DGX"
ARTIFACT_TEMPLATE = "data/artifact/generic/1.0/"
ARTIFACT_SET_TEMPLATE = "data/artifact_set/generic/1.0/"
SHARE_TEMPLATE = "access/share/generic/1.0/"
SHARE_GRANT_TEMPLATE = "access/share_grant/generic/1.0/"
SHARE_EVENT_TEMPLATE = "operational/share_event/generic/1.0/"
SHARE_ROOT_TEMPLATE = "access/share_root/generic/1.0/"
EXTERNAL_OBJECT_TEMPLATE = "integration/external_object/generic/1.0/"
EXTERNAL_OBJECT_RELATION_TEMPLATE = "integration/external_object_relation/generic/1.0/"
LITERATURE_SAVE_TEMPLATE = "access/literature_save/generic/1.0/"
ANOMALY_TEMPLATE = "operational/anomaly/generic/1.0/"
IDEMPOTENCY_TEMPLATE = "system/idempotency_request/generic/1.0/"
REGISTRATION_RECEIPT_TEMPLATE = "system/registration_receipt/generic/1.0/"
OUTBOX_EVENT_TEMPLATE = "system/outbox_event/generic/1.0/"


TEMPLATE_DEFINITIONS: tuple[str, ...] = (
    POLICY_TEMPLATE, TOKEN_TEMPLATE, OPERATION_TEMPLATE,
    ARTIFACT_TEMPLATE,
    ARTIFACT_SET_TEMPLATE,
    SHARE_TEMPLATE,
    SHARE_GRANT_TEMPLATE,
    SHARE_EVENT_TEMPLATE,
    SHARE_ROOT_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    LITERATURE_SAVE_TEMPLATE,
    ANOMALY_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
)
BOOT_TEMPLATE_DEFINITIONS: tuple[str, ...] = (
    POLICY_TEMPLATE, TOKEN_TEMPLATE, OPERATION_TEMPLATE,
    ARTIFACT_TEMPLATE,
    ARTIFACT_SET_TEMPLATE,
    SHARE_TEMPLATE,
    SHARE_GRANT_TEMPLATE,
    SHARE_EVENT_TEMPLATE,
    SHARE_ROOT_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    LITERATURE_SAVE_TEMPLATE,
    ANOMALY_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
    OUTBOX_EVENT_TEMPLATE,
)


class TapDBBackend:
    """TapDB-backed repository for Dewey domain entities."""

    def __init__(self, app_username: str = "dewey"):
        settings = get_settings()

        ensure_tapdb_version()
        cfg = load_runtime_config(settings)
        self.config_path = settings.tapdb_config_path
        self.settings = settings
        self.connection = get_db(settings.tapdb_config_path)
        self.connection.app_username = app_username
        self.domain_code = cfg["domain_code"]
        self.templates = TemplateManager()
        self.factory = InstanceFactory(self.templates, domain_code=self.domain_code)
        self.observability = None

    @contextmanager
    def session_scope(self, commit: bool = False) -> Generator[Session, None, None]:
        started = monotonic()
        success = False
        try:
            connection = get_db(self.config_path)
            connection.app_username = self.connection.app_username
            connection.attribution = transaction_attribution(self.settings, self._operation_label(), commit=commit)
            with connection.session_scope(commit=commit) as session:
                from dewey_service.performance import instrument_engine
                instrument_engine(session.get_bind())
                yield session
                success = True
        except RevisionConflict as exc:
            raise HTTPException(409, "TapDB revision conflict; reread and explicitly reconcile the change") from exc
        finally:
            if self.observability is not None:
                self.observability.record_db_operation(
                    label=self._operation_label(),
                    duration_ms=(monotonic() - started) * 1000,
                    success=success,
                )

    def lock_external_key(self, session: Session, *, operation: str, key: str) -> None:
        """Serialize one canonical operation key across service processes."""
        value = int.from_bytes(sha256(f"{operation}:{key}".encode()).digest()[:8], "big", signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": value})

    def _operation_label(self) -> str:
        for frame_info in inspect.stack(context=0):
            filename = str(frame_info.filename or "")
            if "/dewey_service/services/" in filename and filename.endswith(".py"):
                return f"service:{frame_info.function}"
            if filename.endswith("/dewey_service/service.py"):
                return f"service:{frame_info.function}"
            if filename.endswith("/dewey_service/app.py"):
                return f"app:{frame_info.function}"
        return "tapdb_session"

    def ensure_templates(
        self,
        session: Session,
        template_codes: tuple[str, ...] = TEMPLATE_DEFINITIONS,
    ) -> None:
        missing = []
        for code in template_codes:
            template = self.templates.get_template(session, code, domain_code=self.domain_code)
            if template is None:
                missing.append(code)
            elif template.instance_prefix != DEWEY_TEMPLATE_EUID_PREFIX:
                raise RuntimeError(f"Dewey template {code} must retain its DGX instance prefix")
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(
                "Missing Dewey templates. Complete the reviewed external TapDB lifecycle "
                f"and preservation checks before starting Dewey: {joined}"
            )

    def create_instance(
        self,
        session: Session,
        *,
        template_code: str,
        name: str,
        json_addl: dict[str, Any],
        status: str = "active",
    ) -> generic_instance:
        if not isinstance(json_addl, dict):
            raise ValueError("Dewey instance payload must be an object")
        supplied_properties = json_addl.get("properties", {})
        if not isinstance(supplied_properties, dict):
            raise ValueError("Dewey instances require json_addl.properties to be an object")
        if {"action_groups", "audit_log"}.intersection(json_addl):
            raise ValueError("TapDB owns instance action_groups and audit_log")
        validate_instance_envelope({"properties": supplied_properties})
        template = self.templates.get_template(session, template_code, domain_code=self.domain_code)
        if template is None:
            raise RuntimeError(f"Missing template: {template_code}")

        instance = self.factory.create_instance(
            session=session,
            template_code=template_code,
            name=name,
            properties={},
            create_children=False,
        )
        envelope = validate_instance_envelope(instance.json_addl)
        payload = {
            **envelope,
            **json_addl,
            **creation_audit_fields(),
            "properties": {**envelope["properties"], **supplied_properties},
        }
        self.update_persisted_fields(session, instance, {"json_addl": payload, "bstatus": status})
        if template_code in {ARTIFACT_TEMPLATE, ARTIFACT_SET_TEMPLATE} and not maintenance_mode():
            actor = principal()
            if not actor.writable:
                raise PermissionError("Registry write permission is required")
            policy = self.create_instance(
                session, template_code=POLICY_TEMPLATE,
                name=f"Access for {instance.euid}", json_addl=default_policy(actor),
            )
            self.create_lineage(session, parent=instance, child=policy, relationship_type="registry_policy")
        return instance

    def claim_global_instance(
        self, session, *, template_code, identity_key, name, json_addl, command_evidence
    ):
        """Claim through TapDB without committing the caller's transaction."""
        from daylily_tapdb import IdentityScope
        from daylily_tapdb.factory.instance import IdentityClaimOutcome

        claim = self.factory.claim_instance_by_identity(
            session,
            template_code=template_code,
            identity_key=identity_key,
            name=name,
            scope=IdentityScope.GLOBAL,
            properties={},
            command_evidence=command_evidence,
            create_children=False,
        )
        created = claim.outcome is IdentityClaimOutcome.CREATED
        if created:
            self.update_instance_json(
                session,
                claim.instance,
                {
                    **json_addl,
                    **creation_audit_fields(),
                },
            )
            self.update_persisted_fields(session, claim.instance, {"bstatus": "active"})
        return claim.instance, created

    def update_instance_json(
        self, session: Session, instance: generic_instance, updates: dict[str, Any],
        *, expected_revision: int | None = None,
    ) -> None:
        if instance.type in {"artifact", "artifact_set"} and not maintenance_mode():
            derived = {"share_status", "share_last_issued_at"}
            require_record(self, session, instance, "metadata" if set(updates) <= derived else "edit")
        payload = validate_instance_envelope(instance.json_addl)
        payload.update(updates)
        payload.update(update_audit_fields())
        self.update_persisted_fields(
            session, instance, {"json_addl": validate_instance_envelope(payload)},
            expected_revision=expected_revision,
        )

    def update_persisted_fields(self, session, instance, changes, *, expected_revision: int | None = None):
        """Apply the proposal against the revision observed before native locking."""
        expected = instance.record_revision if expected_revision is None else expected_revision
        update_object(session, ObjectSelector(euid=instance.euid,
            record_type="lineage" if isinstance(instance, generic_instance_lineage) else "instance"),
            changes, actor=self.connection.app_username, dry_run=False, expected_revision=expected)

    def delete_persisted(self, session, instance):
        expected = instance.record_revision
        soft_delete_object(session, ObjectSelector(euid=instance.euid,
            record_type="lineage" if isinstance(instance, generic_instance_lineage) else "instance"),
            actor=self.connection.app_username, dry_run=False, expected_revision=expected)

    def _template_query(
        self,
        session: Session,
        *,
        template_code: str,
        for_update: bool = False,
    ):
        template = self.templates.get_template(session, template_code, domain_code=self.domain_code)
        if template is None:
            return None
        query = session.query(generic_instance).filter(
            generic_instance.template_uid == template.uid,
            generic_instance.type == template.type,
            generic_instance.is_deleted.is_(False),
            visibility_clause(session, generic_instance, types=(template.type,)),
        )
        if for_update:
            query = query.with_for_update()
        return query

    def find_by_euid(
        self,
        session: Session,
        *,
        template_code: str,
        euid: str,
        for_update: bool = False,
    ) -> Optional[generic_instance]:
        if not euid:
            return None
        query = self._template_query(session, template_code=template_code, for_update=for_update)
        if query is None:
            return None
        return query.filter(generic_instance.euid == euid).first()

    def find_by_json_field(
        self,
        session: Session,
        *,
        template_code: str,
        field: str,
        value: str,
        for_update: bool = False,
    ) -> Optional[generic_instance]:
        query = self._template_query(session, template_code=template_code, for_update=for_update)
        if query is None:
            return None
        return query.filter(generic_instance.json_addl[field].as_string() == value).first()

    def list_by_template(
        self,
        session: Session,
        *,
        template_code: str,
        limit: int = 200,
    ) -> list[generic_instance]:
        query = self._template_query(session, template_code=template_code)
        if query is None:
            return []
        return cast(
            list[generic_instance],
            query.order_by(generic_instance.created_dt.desc()).limit(limit).all(),
        )

    def create_lineage(
        self,
        session: Session,
        *,
        parent: generic_instance,
        child: generic_instance,
        relationship_type: str,
        name: str | None = None,
    ) -> generic_instance_lineage:
        if relationship_type == "artifact_set_member" and not maintenance_mode():
            require_record(self, session, parent, "edit")
            if child.type != "artifact":
                raise ValueError("Sets may contain Object and Prefix artifacts only")
            require_record(self, session, child, "metadata")
        existing = (
            session.query(generic_instance_lineage)
            .filter(
                generic_instance_lineage.parent_instance_uid == parent.uid,
                generic_instance_lineage.child_instance_uid == child.uid,
                generic_instance_lineage.relationship_type == relationship_type,
                generic_instance_lineage.is_deleted.is_(False),
            )
            .first()
        )
        if existing is not None:
            return existing

        lineage = generic_instance_lineage(
            name=name or f"{parent.euid}->{child.euid}:{relationship_type}",
            polymorphic_discriminator="generic_instance_lineage",
            category="generic",
            type="lineage",
            subtype="instance_lineage",
            version=SERVICE_VERSION,
            bstatus="active",
            json_addl={"properties": {}},
            is_singleton=False,
            parent_type=parent.polymorphic_discriminator,
            child_type=child.polymorphic_discriminator,
            relationship_type=relationship_type,
            parent_instance_uid=parent.uid,
            child_instance_uid=child.uid,
        )
        session.add(lineage)
        session.flush()
        return lineage

    def delete_lineage(
        self,
        session: Session,
        *,
        parent: generic_instance,
        child: generic_instance,
        relationship_type: str,
    ) -> bool:
        if relationship_type == "artifact_set_member" and not maintenance_mode():
            require_record(self, session, parent, "edit")
        lineage = (
            session.query(generic_instance_lineage)
            .filter(
                generic_instance_lineage.parent_instance_uid == parent.uid,
                generic_instance_lineage.child_instance_uid == child.uid,
                generic_instance_lineage.relationship_type == relationship_type,
                generic_instance_lineage.is_deleted.is_(False),
            )
            .first()
        )
        if lineage is None:
            return False
        self.update_persisted_fields(session, lineage, {"bstatus": "deleted"})
        self.delete_persisted(session, lineage)
        return True

    def list_children(
        self,
        session: Session,
        *,
        parent: generic_instance,
        relationship_type: str | None = None,
    ) -> list[generic_instance]:
        query = (
            session.query(generic_instance)
            .join(
                generic_instance_lineage,
                generic_instance_lineage.child_instance_uid == generic_instance.uid,
            )
            .filter(
                generic_instance_lineage.parent_instance_uid == parent.uid,
                generic_instance_lineage.is_deleted.is_(False),
                generic_instance.is_deleted.is_(False),
                visibility_clause(session, generic_instance),
            )
        )
        if relationship_type:
            query = query.filter(generic_instance_lineage.relationship_type == relationship_type)
        return cast(list[generic_instance], query.all())

    def list_children_many(
        self, session: Session, *, parents, relationship_type: str
    ) -> dict[Any, list[generic_instance]]:
        """Load children for a result set in one scoped, read-only query."""
        grouped = {parent.uid: [] for parent in parents}
        if not grouped:
            return grouped
        rows = (
            session.query(generic_instance_lineage.parent_instance_uid, generic_instance)
            .join(
                generic_instance,
                generic_instance_lineage.child_instance_uid == generic_instance.uid,
            )
            .filter(
                generic_instance_lineage.parent_instance_uid.in_(list(grouped)),
                generic_instance_lineage.relationship_type == relationship_type,
                generic_instance_lineage.is_deleted.is_(False),
                generic_instance.is_deleted.is_(False),
                visibility_clause(session, generic_instance),
            )
            .all()
        )
        for parent_uid, child in rows:
            # Match ORM entity-query deduplication when duplicate edges exist.
            if all(existing.uid != child.uid for existing in grouped[parent_uid]):
                grouped[parent_uid].append(child)
        return grouped

    def list_parents(
        self,
        session: Session,
        *,
        child: generic_instance,
        relationship_type: str | None = None,
    ) -> list[generic_instance]:
        query = (
            session.query(generic_instance)
            .join(
                generic_instance_lineage,
                generic_instance_lineage.parent_instance_uid == generic_instance.uid,
            )
            .filter(
                generic_instance_lineage.child_instance_uid == child.uid,
                generic_instance_lineage.is_deleted.is_(False),
                generic_instance.is_deleted.is_(False),
                visibility_clause(session, generic_instance),
            )
        )
        if relationship_type:
            query = query.filter(generic_instance_lineage.relationship_type == relationship_type)
        return cast(list[generic_instance], query.all())

    def find_lineage_instance(
        self,
        session: Session,
        *,
        source: generic_instance,
        relation_template_code: str,
        parent_relationship_type: str,
        child_relationship_type: str,
    ) -> Optional[generic_instance]:
        # Resolve relation instances by traversing lineages through the relation object.
        relation_template = self.templates.get_template(
            session, relation_template_code, domain_code=self.domain_code
        )
        if relation_template is None:
            return None

        candidates = (
            session.query(generic_instance)
            .join(
                generic_instance_lineage,
                and_(
                    generic_instance_lineage.parent_instance_uid == source.uid,
                    generic_instance_lineage.child_instance_uid == generic_instance.uid,
                    generic_instance_lineage.relationship_type == parent_relationship_type,
                    generic_instance_lineage.is_deleted.is_(False),
                ),
            )
            .filter(
                generic_instance.template_uid == relation_template.uid,
                generic_instance.is_deleted.is_(False),
            )
            .all()
        )
        for candidate in candidates:
            parents = self.list_parents(
                session,
                child=candidate,
                relationship_type=child_relationship_type,
            )
            if parents:
                return candidate
        return None


def normalize_instance_payload(instance: generic_instance) -> dict[str, Any]:
    payload = validate_instance_envelope(instance.json_addl)
    if not payload.get("euid"):
        payload["euid"] = instance.euid
    if not payload.get("name"):
        payload["name"] = instance.name
    if not payload.get("created_at"):
        payload["created_at"] = (
            instance.created_dt.isoformat().replace("+00:00", "Z")
            if instance.created_dt
            else utc_now_iso()
        )
    if not payload.get("updated_at"):
        payload["updated_at"] = (
            instance.modified_dt.isoformat().replace("+00:00", "Z")
            if instance.modified_dt
            else payload["created_at"]
        )
    return payload
