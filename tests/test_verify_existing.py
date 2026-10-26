"""Startup reads existing records and cannot invoke allocators or bootstrap paths."""

from contextlib import contextmanager
from importlib.util import find_spec
from types import SimpleNamespace

import pytest
from daylily_tapdb.templates.manager import TemplateManager

from dewey_service.service import DeweyService
from dewey_service.tapdb_backend import BOOT_TEMPLATE_DEFINITIONS, TapDBBackend


class ReadOnlyTemplateSession:
    def __init__(self, *, missing=False, prefix="DGX"):
        self.reads = []
        self.missing = missing
        self.prefix = prefix

    def query(self, model):
        self.reads.append(model.__tablename__)
        return self

    def filter(self, *criteria):
        return self

    def first(self):
        if self.missing:
            return None
        return SimpleNamespace(
            uid="persisted-template-test",
            euid="persisted-template-test",
            instance_prefix=self.prefix,
            is_deleted=False,
        )

    def get(self, model, uid):
        self.reads.append(model.__tablename__)
        return self.first()

    def __getattr__(self, name):
        raise AssertionError(f"Startup attempted forbidden session operation: {name}")


@pytest.mark.parametrize("missing,prefix", [(False, "DGX"), (True, "DGX"), (False, "TPX")])
def test_verify_existing_uses_only_template_reads(missing, prefix):
    session = ReadOnlyTemplateSession(missing=missing, prefix=prefix)
    commits = []

    @contextmanager
    def session_scope(*, commit=False):
        commits.append(commit)
        yield session

    backend = object.__new__(TapDBBackend)
    backend.domain_code = "Z"
    backend.templates = TemplateManager()
    backend.session_scope = session_scope
    service = DeweyService(backend)
    if missing or prefix != "DGX":
        with pytest.raises(RuntimeError, match="Missing Dewey templates|retain its DGX"):
            service.verify_existing()
    else:
        service.verify_existing()
        assert len(session.reads) == len(BOOT_TEMPLATE_DEFINITIONS)
    assert commits == [False]
    assert set(session.reads) == {"generic_template"}


def test_seed_module_and_mutating_shortcuts_are_absent():
    assert find_spec("dewey_service.db_seed") is None
    import dewey_service.cli.db as db

    for name in ("build", "seed", "repair_templates", "reset", "nuke"):
        assert not hasattr(db, name)
    assert not hasattr(DeweyService, "bootstrap")


def test_native_lifecycle_guidance_does_not_connect(monkeypatch):
    import dewey_service.cli.db as db

    seen = []
    monkeypatch.setattr(db.ccyo_out, "print_text", seen.append)
    monkeypatch.setattr(
        TapDBBackend, "__init__", lambda self, **kwargs: pytest.fail("must not connect")
    )
    db.lifecycle()
    assert "tapdb --config /absolute/operator-config.yaml" in seen[0]
    assert "Do not seed or overwrite historical Dewey templates" in seen[0]
