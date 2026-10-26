"""Staged unit-test backend; database concurrency is verified separately."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from dewey_service.tapdb_backend import (
    ARTIFACT_TEMPLATE,
    EXTERNAL_OBJECT_RELATION_TEMPLATE,
    EXTERNAL_OBJECT_TEMPLATE,
    IDEMPOTENCY_TEMPLATE,
    REGISTRATION_RECEIPT_TEMPLATE,
)


@dataclass
class LocalInstance:
    uid: int
    euid: str
    template_code: str
    name: str
    json_addl: dict[str, Any]
    is_deleted: bool = False
    created_dt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_dt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    polymorphic_discriminator: str = "data_instance"


@dataclass
class LocalLineage:
    parent_uid: int
    child_uid: int
    relationship_type: str
    is_deleted: bool = False


class LocalSession:
    def __init__(self, backend: "LocalTransactionalBackend") -> None:
        self.backend = backend
        self.pending_instances: list[LocalInstance] = []
        self.pending_lineages: list[LocalLineage] = []

    def finalize(self, commit: bool) -> None:
        if commit:
            with self.backend.guard:
                for item in self.pending_instances:
                    self.backend.instances.setdefault(item.template_code, []).append(item)
                self.backend.lineages.extend(self.pending_lineages)


class LocalTransactionalBackend:
    """Stage unit-test rows to exercise service failure handling."""

    prefixes = {
        ARTIFACT_TEMPLATE: "AT",
        EXTERNAL_OBJECT_TEMPLATE: "EX",
        EXTERNAL_OBJECT_RELATION_TEMPLATE: "ER",
        IDEMPOTENCY_TEMPLATE: "ID",
        REGISTRATION_RECEIPT_TEMPLATE: "RC",
    }

    def __init__(self) -> None:
        self.guard = threading.RLock()
        self.instances: dict[str, list[LocalInstance]] = {}
        self.lineages: list[LocalLineage] = []
        self.next_uid = 1
        self.next_sequence = {template: 1 for template in self.prefixes}
        self.fail_template: str | None = None

    @contextmanager
    def session_scope(self, commit: bool = False):
        session = LocalSession(self)
        try:
            yield session
        except Exception:
            session.finalize(False)
            raise
        else:
            session.finalize(commit)

    def claim_global_instance(
        self, session, *, template_code, identity_key, name, json_addl, command_evidence
    ):
        existing = self.find_by_json_field(
            session, template_code=template_code, field="identity_key", value=identity_key
        )
        if existing is not None:
            return existing, False
        item = self.create_instance(
            session,
            template_code=template_code,
            name=name,
            json_addl={**json_addl, "identity_key": identity_key},
        )
        return item, True

    def ensure_templates(self, _session, _templates=None) -> None:
        return

    def _new_instance(self, *, template_code: str, name: str, json_addl) -> LocalInstance:
        with self.guard:
            sequence = self.next_sequence[template_code]
            self.next_sequence[template_code] += 1
            item = LocalInstance(
                uid=self.next_uid,
                euid=f"{self.prefixes[template_code]}-{sequence:06d}",
                template_code=template_code,
                name=name,
                json_addl={"properties": {}, **json_addl},
            )
            self.next_uid += 1
            return item

    def create_instance(
        self, session, *, template_code: str, name: str, json_addl, status="active"
    ):
        _ = status
        if template_code == self.fail_template:
            raise RuntimeError("forced persistence failure")
        item = self._new_instance(template_code=template_code, name=name, json_addl=json_addl)
        if session is None:
            with self.guard:
                self.instances.setdefault(template_code, []).append(item)
        else:
            session.pending_instances.append(item)
        return item

    def update_instance_json(self, _session, instance: LocalInstance, updates) -> None:
        instance.json_addl = {**instance.json_addl, **dict(updates)}

    def _rows(self, session: LocalSession | None, template_code: str) -> list[LocalInstance]:
        with self.guard:
            committed = list(self.instances.get(template_code, []))
        pending = (
            []
            if session is None
            else [item for item in session.pending_instances if item.template_code == template_code]
        )
        return [*pending, *committed]

    def find_by_euid(self, session, *, template_code: str, euid: str, for_update=False):
        _ = for_update
        return next(
            (
                item
                for item in self._rows(session, template_code)
                if not item.is_deleted and item.euid == euid
            ),
            None,
        )

    def find_by_json_field(self, session, *, template_code: str, field: str, value: str):
        return next(
            (
                item
                for item in self._rows(session, template_code)
                if not item.is_deleted and item.json_addl.get(field) == value
            ),
            None,
        )

    def create_lineage(
        self,
        session: LocalSession,
        *,
        parent: LocalInstance,
        child: LocalInstance,
        relationship_type: str,
    ):
        with self.guard:
            committed = list(self.lineages)
        pending = list(session.pending_lineages)
        existing = next(
            (
                row
                for row in [*pending, *committed]
                if row.parent_uid == parent.uid
                and row.child_uid == child.uid
                and row.relationship_type == relationship_type
                and not row.is_deleted
            ),
            None,
        )
        if existing is not None:
            return existing
        row = LocalLineage(parent.uid, child.uid, relationship_type)
        session.pending_lineages.append(row)
        return row

    def count(self, template_code: str) -> int:
        with self.guard:
            return len(self.instances.get(template_code, []))
