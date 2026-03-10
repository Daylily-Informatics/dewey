"""TapDB backend wiring for Dewey artifact persistence."""

from __future__ import annotations

import datetime as dt
import os
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Generator, Optional, cast

from daylily_tapdb import (
    InstanceFactory,
    TAPDBConnection,
    TemplateManager,
    generic_instance,
    generic_instance_lineage,
    generic_template,
)
from daylily_tapdb.cli.context import resolve_context
from daylily_tapdb.cli.db_config import get_db_config_for_env
from daylily_tapdb.sequences import ensure_instance_prefix_sequence
from sqlalchemy import and_
from sqlalchemy.orm import Session


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    payload = str(value).encode("utf-8")
    return sha256(payload).hexdigest()


def _parse_template_code(template_code: str) -> tuple[str, str, str, str]:
    parts = template_code.strip("/").split("/")
    if len(parts) != 4:
        raise ValueError(f"Invalid template code: {template_code}")
    return parts[0], parts[1], parts[2], parts[3]


@dataclass(frozen=True)
class TemplateDefinition:
    template_code: str
    template_discriminator: str
    instance_discriminator: str
    instance_prefix: str
    name: str


ARTIFACT_TEMPLATE = "dewey/data/artifact/1.0/"
ARTIFACT_SET_TEMPLATE = "dewey/data/artifact_set/1.0/"
SHARE_REFERENCE_TEMPLATE = "dewey/data/share_reference/1.0/"
EXTERNAL_OBJECT_TEMPLATE = "dewey/integration/external_object/1.0/"
EXTERNAL_OBJECT_RELATION_TEMPLATE = "dewey/integration/external_object_relation/1.0/"
IDEMPOTENCY_TEMPLATE = "dewey/system/idempotency_request/1.0/"


TEMPLATE_DEFINITIONS: tuple[TemplateDefinition, ...] = (
    TemplateDefinition(
        ARTIFACT_TEMPLATE,
        "data_template",
        "data_instance",
        "AT",
        "Dewey Artifact",
    ),
    TemplateDefinition(
        ARTIFACT_SET_TEMPLATE,
        "data_template",
        "data_instance",
        "AS",
        "Dewey Artifact Set",
    ),
    TemplateDefinition(
        SHARE_REFERENCE_TEMPLATE,
        "data_template",
        "data_instance",
        "SH",
        "Dewey Share Reference",
    ),
    TemplateDefinition(
        EXTERNAL_OBJECT_TEMPLATE,
        "data_template",
        "data_instance",
        "EX",
        "Dewey External Object",
    ),
    TemplateDefinition(
        EXTERNAL_OBJECT_RELATION_TEMPLATE,
        "data_template",
        "data_instance",
        "ER",
        "Dewey External Object Relation",
    ),
    TemplateDefinition(
        IDEMPOTENCY_TEMPLATE,
        "data_template",
        "data_instance",
        "KDP",
        "Dewey Idempotency",
    ),
)


class TapDBBackend:
    """TapDB-backed repository for Dewey domain entities."""

    def __init__(self, app_username: str = "dewey"):
        os.environ.setdefault("TAPDB_STRICT_NAMESPACE", "1")
        env = (os.environ.get("TAPDB_ENV") or "").strip()
        if not env:
            raise RuntimeError("TAPDB_ENV is required (dev|test|prod)")

        try:
            resolve_context(require_keys=True)
            cfg = get_db_config_for_env(env)
        except Exception as exc:
            raise RuntimeError(
                "TapDB is not configured for Dewey.\n"
                "Required env: TAPDB_CLIENT_ID, TAPDB_DATABASE_NAME, TAPDB_ENV"
            ) from exc

        db_hostname = f"{cfg['host']}:{cfg['port']}"
        engine_type = (cfg.get("engine_type") or "local").strip().lower()
        region = (cfg.get("region") or os.environ.get("AWS_REGION") or "us-west-2").strip()
        iam_auth_raw = str(cfg.get("iam_auth") or "").strip().lower()
        iam_auth = iam_auth_raw in {"1", "true", "yes", "on"}
        secret_arn = cfg.get("secret_arn") or cfg.get("master_secret_arn")

        self.connection = TAPDBConnection(
            db_hostname=db_hostname,
            db_user=cfg["user"],
            db_pass=cfg["password"],
            db_name=cfg["database"],
            app_username=app_username,
            engine_type=engine_type if engine_type != "local" else None,
            region=region,
            iam_auth=iam_auth,
            secret_arn=secret_arn,
        )
        self.templates = TemplateManager()
        self.factory = InstanceFactory(self.templates)

    @contextmanager
    def session_scope(self, commit: bool = False) -> Generator[Session, None, None]:
        with self.connection.session_scope(commit=commit) as session:
            yield session

    def _normalize_prefix(self, prefix: str) -> str:
        return prefix.strip().upper()

    def ensure_templates(self, session: Session) -> None:
        for spec in TEMPLATE_DEFINITIONS:
            self._ensure_template(session, spec)
        for spec in TEMPLATE_DEFINITIONS:
            ensure_instance_prefix_sequence(session, self._normalize_prefix(spec.instance_prefix))

    def _ensure_template(self, session: Session, spec: TemplateDefinition) -> generic_template:
        template = self.templates.get_template(session, spec.template_code)
        if template is not None:
            if template.instance_prefix != spec.instance_prefix:
                template.instance_prefix = spec.instance_prefix
                session.flush()
            if template.instance_polymorphic_identity != spec.instance_discriminator:
                template.instance_polymorphic_identity = spec.instance_discriminator
                session.flush()
            return template

        category, type_, subtype, version = _parse_template_code(spec.template_code)
        template = generic_template(
            name=spec.name,
            polymorphic_discriminator=spec.template_discriminator,
            category=category,
            type=type_,
            subtype=subtype,
            version=version,
            bstatus="active",
            json_addl={},
            is_singleton=False,
            instance_prefix=spec.instance_prefix,
            instance_polymorphic_identity=spec.instance_discriminator,
            json_addl_schema=None,
        )
        session.add(template)
        session.flush()
        self.templates.clear_cache()
        return template

    def create_instance(
        self,
        session: Session,
        *,
        template_code: str,
        name: str,
        json_addl: dict[str, Any],
        status: str = "active",
    ) -> generic_instance:
        template = self.templates.get_template(session, template_code)
        if template is None:
            self.ensure_templates(session)
            template = self.templates.get_template(session, template_code)
        if template is None:
            raise RuntimeError(f"Missing template: {template_code}")

        prefix = str(template.instance_prefix or "").strip()
        if prefix:
            ensure_instance_prefix_sequence(session, self._normalize_prefix(prefix))

        instance = self.factory.create_instance(
            session=session,
            template_code=template_code,
            name=name,
            properties={},
            create_children=False,
        )
        instance.json_addl = dict(json_addl)
        instance.bstatus = status
        instance.is_singleton = False
        session.flush()
        return instance

    def update_instance_json(
        self, session: Session, instance: generic_instance, updates: dict[str, Any]
    ) -> None:
        payload = dict(instance.json_addl or {})
        payload.update(updates)
        instance.json_addl = payload
        session.flush()

    def _template_query(
        self,
        session: Session,
        *,
        template_code: str,
        for_update: bool = False,
    ):
        template = self.templates.get_template(session, template_code)
        if template is None:
            return None
        query = session.query(generic_instance).filter(
            generic_instance.template_uid == template.uid,
            generic_instance.is_deleted.is_(False),
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
    ) -> Optional[generic_instance]:
        query = self._template_query(session, template_code=template_code)
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
            version="1.0.0",
            bstatus="active",
            json_addl={},
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
        lineage.is_deleted = True
        lineage.bstatus = "deleted"
        session.flush()
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
            )
        )
        if relationship_type:
            query = query.filter(generic_instance_lineage.relationship_type == relationship_type)
        return cast(list[generic_instance], query.all())

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
        relation_template = self.templates.get_template(session, relation_template_code)
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
    payload = dict(instance.json_addl or {})
    payload.setdefault("euid", instance.euid)
    payload.setdefault("name", instance.name)
    payload.setdefault(
        "created_at",
        instance.created_dt.isoformat().replace("+00:00", "Z")
        if instance.created_dt
        else utc_now_iso(),
    )
    payload.setdefault(
        "updated_at",
        instance.modified_dt.isoformat().replace("+00:00", "Z")
        if instance.modified_dt
        else payload["created_at"],
    )
    return payload
