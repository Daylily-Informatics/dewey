from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import dewey_service.tapdb_backend as backend_mod


class _FakeField:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object):
        return ("eq", self.name, other)

    def is_(self, other: object):
        return ("is", self.name, other)

    def desc(self):
        return ("desc", self.name)

    def as_string(self):
        return self


class _FakeJSONAccessor:
    def __getitem__(self, key: str) -> _FakeField:
        return _FakeField(f"json_addl.{key}")


class _FakeGenericInstanceModel:
    template_uid = _FakeField("template_uid")
    is_deleted = _FakeField("is_deleted")
    euid = _FakeField("euid")
    created_dt = _FakeField("created_dt")
    uid = _FakeField("uid")
    json_addl = _FakeJSONAccessor()


class _FakeLineageModel:
    parent_instance_uid = _FakeField("parent_instance_uid")
    child_instance_uid = _FakeField("child_instance_uid")
    relationship_type = _FakeField("relationship_type")
    is_deleted = _FakeField("is_deleted")

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.is_deleted = False
        self.bstatus = kwargs.get("bstatus", "active")


class _FakeQuery:
    def __init__(self, *, first_result=None, all_result=None) -> None:
        self.first_result = first_result
        self.all_result = [] if all_result is None else all_result
        self.filters: list[object] = []
        self.joins: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.with_for_update_called = False
        self.orderings: list[object] = []
        self.limit_value: int | None = None

    def filter(self, *args):
        self.filters.extend(args)
        return self

    def with_for_update(self):
        self.with_for_update_called = True
        return self

    def order_by(self, *args):
        self.orderings.extend(args)
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def join(self, *args, **kwargs):
        self.joins.append((args, kwargs))
        return self

    def first(self):
        return self.first_result

    def all(self):
        return self.all_result


class _FakeSession:
    def __init__(self, query_map: dict[object, list[_FakeQuery]] | None = None) -> None:
        self.query_map = query_map or {}
        self.added: list[object] = []
        self.flush_count = 0

    def query(self, model):
        queue = self.query_map.get(model)
        if not queue:
            raise AssertionError(f"No fake query registered for {model!r}")
        return queue.pop(0)

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flush_count += 1


def _backend() -> backend_mod.TapDBBackend:
    backend = object.__new__(backend_mod.TapDBBackend)
    backend.domain_code = "Z"
    backend.templates = SimpleNamespace()
    backend.factory = SimpleNamespace()
    backend.connection = SimpleNamespace()
    backend.observability = None
    return backend


def test_backend_init_wraps_config_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backend_mod,
        "get_settings",
        lambda: SimpleNamespace(
            tapdb_client_id="dewey",
            tapdb_database_name="dewey",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_code="Z",
            tapdb_config_path="",
            aws_region="us-west-2",
        ),
    )
    monkeypatch.setattr(
        backend_mod,
        "resolve_context",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("bad config")),
    )
    with pytest.raises(RuntimeError, match="TapDB is not configured for Dewey"):
        backend_mod.TapDBBackend()


def test_backend_init_builds_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backend_mod,
        "get_settings",
        lambda: SimpleNamespace(
            tapdb_client_id="dewey",
            tapdb_database_name="dewey",
            tapdb_owner_repo_name="dewey",
            tapdb_domain_code="Z",
            tapdb_config_path="",
            aws_region="us-west-2",
        ),
    )
    monkeypatch.setattr(
        backend_mod,
        "resolve_context",
        lambda **_kwargs: SimpleNamespace(client_id="dewey", database_name="dewey"),
    )
    monkeypatch.setattr(
        backend_mod,
        "get_db_config",
        lambda **_kwargs: {
            "host": "localhost",
            "port": "5432",
            "user": "dewey",
            "password": "secret",
            "database": "dewey_dev",
            "schema_name": "tapdb_dewey_dev",
            "engine_type": "local",
            "region": "us-west-2",
            "iam_auth": "true",
            "secret_arn": "arn:aws:secretsmanager:example",
        },
    )

    seen: dict[str, object] = {}

    class FakeConnection:
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(backend_mod, "TAPDBConnection", FakeConnection)
    monkeypatch.setattr(backend_mod, "TemplateManager", lambda: "templates")
    monkeypatch.setattr(
        backend_mod,
        "InstanceFactory",
        lambda templates, *, domain_code=None: ("factory", templates, domain_code),
    )

    backend = backend_mod.TapDBBackend(app_username="svc")

    assert seen["db_hostname"] == "localhost:5432"
    assert seen["db_hostaddr"] is None
    assert seen["db_user"] == "dewey"
    assert seen["db_pass"] == "secret"
    assert seen["db_name"] == "dewey_dev"
    assert seen["schema_name"] == "tapdb_dewey_dev"
    assert seen["app_username"] == "svc"
    assert seen["engine_type"] == "local"
    assert seen["iam_auth"] is True
    assert backend.domain_code == "Z"
    assert backend.templates == "templates"
    assert backend.factory == ("factory", "templates", "Z")


def test_backend_helpers_cover_utility_functions() -> None:
    assert backend_mod.utc_now_iso().endswith("Z")
    assert (
        backend_mod.sha256_json({"a": 1})
        == hashlib.sha256(str({"a": 1}).encode("utf-8")).hexdigest()
    )
    assert backend_mod._parse_template_code(backend_mod.ARTIFACT_TEMPLATE) == (
        backend_mod.DEWEY_TEMPLATE_CATEGORY,
        "data",
        "artifact",
        "1.0",
    )
    with pytest.raises(ValueError, match="Invalid template code"):
        backend_mod._parse_template_code("bad/template")


def test_session_scope() -> None:
    backend = _backend()
    events: list[tuple[str, bool | None]] = []

    class Connection:
        def session_scope(self, *, commit: bool = False):
            class _Ctx:
                def __enter__(self_nonlocal):
                    events.append(("enter", commit))
                    return "session"

                def __exit__(self_nonlocal, exc_type, exc, tb):
                    events.append(("exit", commit))

            return _Ctx()

    backend.connection = Connection()

    with backend.session_scope(commit=True) as session:
        assert session == "session"

    assert events == [("enter", True), ("exit", True)]


def test_template_definitions_are_required_codes() -> None:
    assert backend_mod.TEMPLATE_DEFINITIONS == (
        backend_mod.ARTIFACT_TEMPLATE,
        backend_mod.ARTIFACT_SET_TEMPLATE,
        backend_mod.SHARE_REFERENCE_TEMPLATE,
        backend_mod.EXTERNAL_OBJECT_TEMPLATE,
        backend_mod.EXTERNAL_OBJECT_RELATION_TEMPLATE,
        backend_mod.LITERATURE_SAVE_TEMPLATE,
        backend_mod.ANOMALY_TEMPLATE,
        backend_mod.IDEMPOTENCY_TEMPLATE,
        backend_mod.REGISTRATION_RECEIPT_TEMPLATE,
        backend_mod.OUTBOX_EVENT_TEMPLATE,
    )
    assert backend_mod.BOOT_TEMPLATE_DEFINITIONS == (
        backend_mod.ARTIFACT_TEMPLATE,
        backend_mod.ARTIFACT_SET_TEMPLATE,
        backend_mod.SHARE_REFERENCE_TEMPLATE,
        backend_mod.EXTERNAL_OBJECT_TEMPLATE,
        backend_mod.EXTERNAL_OBJECT_RELATION_TEMPLATE,
        backend_mod.LITERATURE_SAVE_TEMPLATE,
        backend_mod.ANOMALY_TEMPLATE,
        backend_mod.IDEMPOTENCY_TEMPLATE,
    )
    assert backend_mod.REGISTRATION_RECEIPT_TEMPLATE not in backend_mod.BOOT_TEMPLATE_DEFINITIONS
    assert backend_mod.OUTBOX_EVENT_TEMPLATE not in backend_mod.BOOT_TEMPLATE_DEFINITIONS


def test_ensure_templates_raises_on_missing() -> None:
    backend = _backend()
    session = _FakeSession()
    calls: list[tuple[str, str]] = []
    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: (
            calls.append((code, domain_code)),
            None,
        )[1]
    )

    with pytest.raises(RuntimeError, match="Missing Dewey templates"):
        backend.ensure_templates(session)
    assert calls
    assert all(domain_code == "Z" for _, domain_code in calls)


def test_ensure_templates_passes_when_seeded() -> None:
    backend = _backend()
    session = _FakeSession()
    calls: list[tuple[str, str]] = []
    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: (
            calls.append((code, domain_code)),
            SimpleNamespace(uid=1),
        )[1]
    )

    backend.ensure_templates(session)
    assert calls
    assert all(domain_code == "Z" for _, domain_code in calls)


def test_ensure_templates_can_verify_startup_subset() -> None:
    backend = _backend()
    session = _FakeSession()
    calls: list[str] = []

    def get_template(_session, code, *, domain_code=None):
        calls.append(code)
        if code in backend_mod.BOOT_TEMPLATE_DEFINITIONS:
            return SimpleNamespace(uid=1)
        return None

    backend.templates = SimpleNamespace(get_template=get_template)

    backend.ensure_templates(session, backend_mod.BOOT_TEMPLATE_DEFINITIONS)

    assert tuple(calls) == backend_mod.BOOT_TEMPLATE_DEFINITIONS
    assert backend_mod.REGISTRATION_RECEIPT_TEMPLATE not in calls
    assert backend_mod.OUTBOX_EVENT_TEMPLATE not in calls


def test_create_instance_covers_success_and_missing_template() -> None:
    backend = _backend()
    session = _FakeSession()
    created = SimpleNamespace(json_addl={}, bstatus="", is_singleton=True)
    template = SimpleNamespace(instance_prefix=" AT ", uid=11)

    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: template
    )
    backend.factory = SimpleNamespace(create_instance=lambda **kwargs: created)

    instance = backend.create_instance(
        session,
        template_code=backend_mod.ARTIFACT_TEMPLATE,
        name="artifact",
        json_addl={"foo": "bar"},
    )

    assert instance is created
    assert created.json_addl == {"foo": "bar"}
    assert created.bstatus == "active"
    assert created.is_singleton is False
    assert session.flush_count == 1

    backend_missing = _backend()
    backend_missing.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: None
    )
    backend_missing.factory = SimpleNamespace()
    with pytest.raises(RuntimeError, match="Missing template"):
        backend_missing.create_instance(
            session,
            template_code=backend_mod.ARTIFACT_TEMPLATE,
            name="artifact",
            json_addl={},
        )


def test_update_instance_json_and_query_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _backend()
    template = SimpleNamespace(uid=7)
    seen_domain_codes: list[str | None] = []
    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: (
            seen_domain_codes.append(domain_code),
            template,
        )[1]
    )
    monkeypatch.setattr(backend_mod, "generic_instance", _FakeGenericInstanceModel)

    found = SimpleNamespace(euid="DGX-000001", created_dt=datetime.now(timezone.utc))
    q_template = _FakeQuery(first_result=found, all_result=[found])
    session = _FakeSession(
        {
            _FakeGenericInstanceModel: [
                q_template,
                _FakeQuery(first_result=found),
                _FakeQuery(first_result=found),
                _FakeQuery(all_result=[found]),
            ]
        }
    )

    query = backend._template_query(
        session, template_code=backend_mod.ARTIFACT_TEMPLATE, for_update=True
    )
    assert query is q_template
    assert q_template.with_for_update_called is True
    assert q_template.filters

    assert (
        backend.find_by_euid(
            session, template_code=backend_mod.ARTIFACT_TEMPLATE, euid="DGX-000001"
        )
        is found
    )
    assert (
        backend.find_by_json_field(
            session,
            template_code=backend_mod.ARTIFACT_TEMPLATE,
            field="artifact_identity_key",
            value="identity",
        )
        is found
    )
    assert backend.list_by_template(
        session, template_code=backend_mod.ARTIFACT_TEMPLATE, limit=3
    ) == [found]
    assert (
        backend.find_by_euid(session, template_code=backend_mod.ARTIFACT_TEMPLATE, euid="") is None
    )

    instance = SimpleNamespace(json_addl={"a": 1})
    backend.update_instance_json(session, instance, {"b": 2})
    assert instance.json_addl == {"a": 1, "b": 2}

    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: None
    )
    assert backend._template_query(session, template_code=backend_mod.ARTIFACT_TEMPLATE) is None
    assert seen_domain_codes
    assert all(domain_code == "Z" for domain_code in seen_domain_codes)


def test_lineage_helpers_cover_create_delete_and_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _backend()
    parent = SimpleNamespace(uid=1, euid="DGX-000002", polymorphic_discriminator="data_instance")
    child = SimpleNamespace(uid=2, euid="DGX-000001", polymorphic_discriminator="data_instance")
    monkeypatch.setattr(backend_mod, "generic_instance", _FakeGenericInstanceModel)
    monkeypatch.setattr(backend_mod, "generic_instance_lineage", _FakeLineageModel)

    existing_lineage = SimpleNamespace()
    create_session = _FakeSession(
        {
            _FakeLineageModel: [
                _FakeQuery(first_result=None),
                _FakeQuery(first_result=existing_lineage),
                _FakeQuery(first_result=None),
                _FakeQuery(first_result=SimpleNamespace(is_deleted=False, bstatus="active")),
                _FakeQuery(first_result=None),
            ],
            _FakeGenericInstanceModel: [
                _FakeQuery(all_result=[child]),
                _FakeQuery(all_result=[parent]),
            ],
        }
    )

    lineage = backend.create_lineage(
        create_session, parent=parent, child=child, relationship_type="artifact_set_member"
    )
    assert lineage in create_session.added
    assert create_session.flush_count >= 1

    assert (
        backend.create_lineage(
            create_session, parent=parent, child=child, relationship_type="artifact_set_member"
        )
        is existing_lineage
    )

    assert (
        backend.delete_lineage(
            create_session, parent=parent, child=child, relationship_type="artifact_set_member"
        )
        is False
    )

    deletable = SimpleNamespace(is_deleted=False, bstatus="active")
    delete_session = _FakeSession(
        {
            _FakeLineageModel: [_FakeQuery(first_result=deletable)],
            _FakeGenericInstanceModel: [
                _FakeQuery(all_result=[child]),
                _FakeQuery(all_result=[parent]),
            ],
        }
    )
    assert (
        backend.delete_lineage(
            delete_session, parent=parent, child=child, relationship_type="artifact_set_member"
        )
        is True
    )
    assert deletable.is_deleted is True
    assert deletable.bstatus == "deleted"

    assert backend.list_children(
        delete_session, parent=parent, relationship_type="artifact_set_member"
    ) == [child]
    assert backend.list_parents(
        delete_session, child=child, relationship_type="artifact_set_member"
    ) == [parent]


def test_find_lineage_instance_and_normalize_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _backend()
    relation_template = SimpleNamespace(uid=10)
    seen_domain_codes: list[str | None] = []
    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: (
            seen_domain_codes.append(domain_code),
            relation_template,
        )[1]
    )
    monkeypatch.setattr(backend_mod, "generic_instance", _FakeGenericInstanceModel)
    monkeypatch.setattr(backend_mod, "generic_instance_lineage", _FakeLineageModel)
    monkeypatch.setattr(backend_mod, "and_", lambda *clauses: clauses)

    candidate_a = SimpleNamespace(uid=3, euid="DGX-000003")
    candidate_b = SimpleNamespace(uid=4, euid="DGX-000004")
    session = _FakeSession(
        {_FakeGenericInstanceModel: [_FakeQuery(all_result=[candidate_a, candidate_b])]}
    )
    backend.list_parents = lambda session, child, relationship_type=None: (
        [] if child is candidate_a else [SimpleNamespace(uid=1)]
    )

    source = SimpleNamespace(uid=1)
    assert (
        backend.find_lineage_instance(
            session,
            source=source,
            relation_template_code=backend_mod.EXTERNAL_OBJECT_RELATION_TEMPLATE,
            parent_relationship_type="has_external_relation",
            child_relationship_type="is_external_relation_for",
        )
        is candidate_b
    )

    backend.templates = SimpleNamespace(
        get_template=lambda session, code, *, domain_code=None: None
    )
    assert (
        backend.find_lineage_instance(
            session,
            source=source,
            relation_template_code=backend_mod.EXTERNAL_OBJECT_RELATION_TEMPLATE,
            parent_relationship_type="has_external_relation",
            child_relationship_type="is_external_relation_for",
        )
        is None
    )
    assert seen_domain_codes
    assert all(domain_code == "Z" for domain_code in seen_domain_codes)

    instance = SimpleNamespace(
        json_addl={"artifact_type": "fastq"},
        euid="DGX-000001",
        name="artifact",
        created_dt=datetime(2026, 1, 1, tzinfo=timezone.utc),
        modified_dt=None,
    )
    payload = backend_mod.normalize_instance_payload(instance)
    assert payload["euid"] == "DGX-000001"
    assert payload["name"] == "artifact"
    assert payload["created_at"] == "2026-01-01T00:00:00Z"
    assert payload["updated_at"] == "2026-01-01T00:00:00Z"
