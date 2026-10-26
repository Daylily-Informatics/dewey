"""Scoped release-template preparation with the real native exporter.

SQLite stores only this test's plain fixture rows; no TapDB database or native
identity allocator is used. The governed seeder is recorded, not executed.
"""

import hashlib
import json
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
from sqlalchemy import JSON, Boolean, Column, Integer, String, create_engine, select
from sqlalchemy.orm import Session, declarative_base

from dewey_service.cli import db


@pytest.fixture
def template_command(tmp_path, monkeypatch):
    import daylily_tapdb
    from daylily_tapdb.templates import loader, repository

    base = declarative_base()
    attributes = {
        "__tablename__": "fixture_template_rows",
        "uid": Column(Integer, primary_key=True),
        "euid": Column(String, unique=True),
        "domain_code": Column(String),
        "issuer_app_code": Column(String),
        "is_deleted": Column(Boolean, default=False),
    }
    for field in repository.SEEDABLE_FIELDS:
        column_type = (
            JSON
            if field in {"json_addl", "json_addl_schema"}
            else Boolean
            if field == "is_singleton"
            else String
        )
        attributes[field] = Column(column_type)
    row_type = type("FixtureTemplateRow", (base,), attributes)
    engine = create_engine("sqlite://")
    base.metadata.create_all(engine)
    pack_path = (
        Path(__file__).resolve().parents[1]
        / "config/tapdb_templates/dewey/sharing3.repository-pack.json"
    )
    pack = json.loads(pack_path.read_text())
    registry_path = tmp_path / "prefixes.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": "fixture",
                "ownership": {"testdomain": {"DGX": {"owner_repo_name": "dewey"}}},
            }
        )
    )
    operator = tmp_path / "operator.yaml"
    operator.write_text("fixture: true\n")
    attribution = tmp_path / "attribution.json"
    attribution.write_text(
        json.dumps(
            {
                "version": 1,
                "actor_kind": "service",
                "actor_issuer": "fixture",
                "actor_subject": "template-scope-test",
                "service_identity": "dewey",
                "request_id": "fixture-request",
                "operation_id": "fixture-operation",
            }
        )
    )
    cfg = {
        "database": "fixture",
        "host": "localhost",
        "port": 5432,
        "schema_name": "fixture",
        "domain_code": "testdomain",
        "owner_repo_name": "dewey",
        "operator_configured": True,
        "operator_user": "fixture_operator",
        "user": "fixture_runtime",
        "engine_type": "local",
        "region": "us-west-2",
        "domain_registry_path": str(tmp_path / "domains.json"),
        "prefix_ownership_registry_path": str(registry_path),
    }
    seed_calls, outputs = [], []

    def stored(item, reference):
        return row_type(
            **repository.serialize_template(SimpleNamespace(**item)),
            euid=reference,
            domain_code=cfg["domain_code"],
            issuer_app_code="dewey",
            is_deleted=False,
        )

    # The unrelated historical definition reproduces the production rejection.
    legacy = deepcopy(pack["templates"][0])
    legacy.update(
        name="Historical user definition",
        type="user",
        json_addl={"properties": {"password_hash": ""}},
    )
    with Session(engine) as session, session.begin():
        session.add(
            row_type(
                **legacy,
                euid="fixture-historical-reference",
                domain_code=cfg["domain_code"],
                issuer_app_code="dewey",
                is_deleted=False,
            )
        )
        session.add(stored(pack["templates"][0], "fixture-existing-release-reference"))

    class Connection:
        def __init__(self, **kwargs):
            assert kwargs["connection_role"] == "operator"
            assert kwargs["db_user"] == cfg["operator_user"]
            self.engine = SimpleNamespace(update_execution_options=lambda **kwargs: None)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @contextmanager
        def session_scope(self, commit=False):
            with Session(engine) as session:
                transaction = session.begin()
                try:
                    yield session
                    transaction.commit() if commit else transaction.rollback()
                except Exception:
                    transaction.rollback()
                    raise

    def seed(session, templates, **kwargs):
        assert kwargs["overwrite"] is False
        assert kwargs["domain_code"] == cfg["domain_code"]
        assert kwargs["owner_repo_name"] == "dewey"
        assert kwargs["prefix_registry_path"] == registry_path
        seed_calls.append(deepcopy(templates))
        inserted = skipped = 0
        for item in templates:
            key = repository.template_key(item)
            existing = (
                session.query(row_type)
                .filter_by(
                    domain_code=cfg["domain_code"],
                    issuer_app_code="dewey",
                    **dict(zip(("category", "type", "subtype", "version"), key)),
                )
                .one_or_none()
            )
            if existing is None:
                session.add(stored(item, "fixture-created-reference-" + item["type"]))
                inserted += 1
            else:
                skipped += 1
        session.flush()
        return loader.SeedSummary(len(templates), inserted, 0, skipped, 1)

    monkeypatch.setattr(daylily_tapdb, "TAPDBConnection", Connection)
    monkeypatch.setattr(daylily_tapdb, "generic_template", row_type)
    monkeypatch.setattr(repository, "generic_template", row_type)
    monkeypatch.setattr(loader, "seed_templates", seed)
    monkeypatch.setattr("daylily_tapdb.cli.db_config.get_db_config", lambda **kwargs: cfg)
    monkeypatch.setattr("dewey_service.settings.get_settings", lambda: object())
    monkeypatch.setattr(
        "dewey_service.integrations.tapdb_runtime.load_runtime_config", lambda settings: cfg
    )
    monkeypatch.setattr(db.ccyo_out, "print_text", lambda value: outputs.append(json.loads(value)))
    kwargs = dict(
        operator_config=operator,
        repository_pack=pack_path,
        receipt_pack=tmp_path / "release.json",
        actor="template-scope-test",
        attribution=attribution,
    )
    yield SimpleNamespace(
        engine=engine,
        row_type=row_type,
        pack=pack,
        kwargs=kwargs,
        seed_calls=seed_calls,
        outputs=outputs,
        repository=repository,
        registry_path=registry_path,
    )
    engine.dispose()


def test_release_templates_ignore_unrelated_sensitive_history_and_export_native_receipts(
    template_command,
):
    state = template_command
    with Session(state.engine) as session:
        with pytest.raises(ValueError, match="sensitive key: password_hash"):
            state.repository.export_repository_pack(
                session,
                state.kwargs["receipt_pack"].with_name("unscoped.json"),
                domain_code="testdomain",
                issuer_app_code="dewey",
                prefix_registry_path=state.registry_path,
                actor="template-scope-test",
            )
    assert not state.kwargs["receipt_pack"].with_name("unscoped.json").exists()

    db.registry_templates(**state.kwargs)

    assert state.seed_calls == [state.pack["templates"]]
    result = state.outputs[0]
    assert result["summary"]["inserted"] == 2
    assert result["summary"]["skipped"] == 1
    assert len(result["exports"]) == 3
    expected = {state.repository.template_key(item) for item in state.pack["templates"]}
    assert {tuple(item["template_key"]) for item in result["exports"]} == expected
    for item in result["exports"]:
        path = Path(item["export_pack"])
        receipt = json.loads(Path(item["receipt"]).read_text())
        exported = json.loads(path.read_text())
        assert len(exported["templates"]) == receipt["template_count"] == 1
        assert state.repository.template_key(exported["templates"][0]) == tuple(
            item["template_key"]
        )
        assert receipt["format"] == "tapdb.repository-template-receipt/v1"
        assert (
            receipt["content_sha256"]
            == item["export_sha256"]
            == hashlib.sha256(path.read_bytes()).hexdigest()
        )
        assert "password_hash" not in path.read_text()
    with Session(state.engine) as session:
        legacy = session.execute(
            select(state.row_type).where(state.row_type.type == "user")
        ).scalar_one()
        assert legacy.json_addl == {"properties": {"password_hash": ""}}
        assert len(session.execute(select(state.row_type)).scalars().all()) == 4

    # An exact rerun uses new native receipt paths and skips all persisted definitions.
    db.registry_templates(
        **(state.kwargs | {"receipt_pack": state.kwargs["receipt_pack"].with_name("rerun.json")})
    )
    assert state.outputs[1]["summary"]["inserted"] == 0
    assert state.outputs[1]["summary"]["skipped"] == 3


@pytest.mark.parametrize("change", ["definition", "deleted"])
def test_requested_template_conflict_stops_before_seeding_or_export(template_command, change):
    state = template_command
    with Session(state.engine) as session, session.begin():
        row = session.execute(
            select(state.row_type).where(state.row_type.type == "share_revision")
        ).scalar_one()
        if change == "definition":
            row.name = "Conflicting persisted definition"
        else:
            row.is_deleted = True
    with pytest.raises(ValueError, match="conflicts|deleted"):
        db.registry_templates(**state.kwargs)
    assert not state.seed_calls and not state.outputs
    assert not list(state.kwargs["receipt_pack"].parent.glob("release.*.json"))


def test_existing_native_receipt_is_rejected_before_seeding(template_command):
    state = template_command
    path = state.kwargs["receipt_pack"].with_name(
        "release.access.share_alias.generic.1.0.receipt.json"
    )
    path.write_text("preserved receipt")
    with pytest.raises(typer.BadParameter, match="overwrite"):
        db.registry_templates(**state.kwargs)
    assert path.read_text() == "preserved receipt"
    assert not state.seed_calls and not state.outputs
