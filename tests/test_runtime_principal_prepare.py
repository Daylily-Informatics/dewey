"""New one-time principal wrapper checks; no database, credentials or AWS calls."""

from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/dewey_runtime_principal_prepare.py"
SPEC = importlib.util.spec_from_file_location("dewey_principal_capsule", SCRIPT)
assert SPEC and SPEC.loader
capsule = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capsule)


def mappings():
    runtime = {
        **capsule.EXPECTED,
        "config_path": capsule.LANES["rehearsal"]["directory"] + "/tapdb-runtime.yaml",
        "database": capsule.LANES["rehearsal"]["database"],
        "user": capsule.LANES["rehearsal"]["user"],
        "password": "",
        "secret_arn": "runtime-secret-reference",
        "iam_auth": "false",
        "tenant_id": "",
        "allow_global_claims": True,
        "operator_user": "",
        "operator_password": "",
        "operator_secret_arn": "",
        "operator_iam_auth": False,
        "operator_configured": False,
    }
    operator = {
        **runtime,
        "config_path": capsule.LANES["rehearsal"]["operator"],
        "operator_user": "dayhoff",
        "operator_secret_arn": "operator-secret-reference",
        "operator_configured": True,
    }
    return runtime, operator


def test_overlay_changes_only_five_operator_fields_and_preserves_runtime_identity():
    runtime, operator = mappings()
    result = capsule.reviewed_overlay(
        runtime, operator, expected_operator_secret="operator-secret-reference"
    )
    assert result["config_path"] == runtime["config_path"]
    assert {key for key in result if result[key] != runtime[key]} <= set(capsule.OPERATOR_FIELDS)
    assert runtime["operator_configured"] is False


@pytest.mark.parametrize(
    "field", ["database", "schema_name", "secret_arn", "host", "tenant_id", "user"]
)
def test_overlay_rejects_any_scope_transport_or_secret_mismatch(field):
    runtime, operator = mappings()
    operator[field] = "different-input"
    with pytest.raises(capsule.PreparationError, match="disagree"):
        capsule.reviewed_overlay(
            runtime, operator, expected_operator_secret="operator-secret-reference"
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("operator_user", "other-operator"),
        ("operator_password", "test-only-secret"),
        ("operator_iam_auth", True),
    ],
)
def test_overlay_rejects_unapproved_operator(field, value):
    runtime, operator = mappings()
    operator[field] = value
    with pytest.raises(capsule.PreparationError):
        capsule.reviewed_overlay(
            runtime, operator, expected_operator_secret="operator-secret-reference"
        )


def test_runtime_config_must_not_contain_operator_fields():
    runtime, _ = mappings()
    runtime["operator_secret_arn"] = "operator-secret-reference"
    with pytest.raises(capsule.PreparationError, match="operator fields"):
        capsule.validate_runtime(runtime, "rehearsal", Path(runtime["config_path"]))


def test_stale_bootstrap_receipt_never_calls_native_apply(monkeypatch, tmp_path):
    import daylily_tapdb.runtime_principal as native

    calls = []
    monkeypatch.setattr(capsule, "resolve_inputs", lambda _args: ({}, {"hash": "new"}))
    monkeypatch.setattr(
        native, "bootstrap_runtime_principal", lambda cfg, *, apply: calls.append(apply)
    )
    receipt = tmp_path / "bootstrap.json"
    capsule.write_new(
        receipt, capsule.sealed({"operation": "bootstrap", "inputs": {"hash": "old"}, "native": {}})
    )
    with pytest.raises(capsule.PreparationError, match="inputs changed"):
        capsule.prepare(SimpleNamespace(phase="bootstrap-apply", receipt=str(receipt)))
    assert calls == []


def test_bootstrap_apply_compares_offline_plan_before_one_native_apply(monkeypatch, tmp_path):
    import daylily_tapdb.runtime_principal as native

    calls = []
    plan = {"status": "planned"}
    monkeypatch.setattr(capsule, "resolve_inputs", lambda _args: ({}, {"hash": "unchanged"}))

    def bootstrap(cfg, *, apply):
        calls.append(apply)
        return {"status": "applied"} if apply else plan

    monkeypatch.setattr(native, "bootstrap_runtime_principal", bootstrap)
    receipt = tmp_path / "bootstrap.json"
    capsule.write_new(
        receipt,
        capsule.sealed({"operation": "bootstrap", "inputs": {"hash": "unchanged"}, "native": plan}),
    )
    result = capsule.prepare(SimpleNamespace(phase="bootstrap-apply", receipt=str(receipt)))
    assert calls == [False, True]
    assert capsule.read_sealed(result)["native"]["status"] == "applied"
    with pytest.raises(capsule.PreparationError, match="Result exists"):
        capsule.prepare(SimpleNamespace(phase="bootstrap-apply", receipt=str(receipt)))
    assert calls == [False, True]


def test_receipts_reject_nonprivate_parent_before_native_apply(monkeypatch, tmp_path):
    import daylily_tapdb.runtime_principal as native

    monkeypatch.setattr(capsule, "resolve_inputs", lambda _args: ({}, {}))
    monkeypatch.setattr(
        native, "bootstrap_runtime_principal", lambda *a, **kw: pytest.fail("native called")
    )
    tmp_path.chmod(0o755)
    with pytest.raises(capsule.PreparationError, match="directory must be private"):
        capsule.prepare(
            SimpleNamespace(phase="bootstrap-apply", receipt=str(tmp_path / "plan.json"))
        )


def test_bind_apply_rejects_changed_inputs_without_native_call(monkeypatch, tmp_path):
    import daylily_tapdb.runtime_principal as native

    monkeypatch.setattr(capsule, "resolve_inputs", lambda _args: ({}, {"role": "changed"}))
    monkeypatch.setattr(
        native, "bind_runtime_principal", lambda *a, **kw: pytest.fail("native called")
    )
    receipt = tmp_path / "bind.json"
    capsule.write_new(
        tmp_path / "bind.inputs.json",
        capsule.sealed({"operation": "bind", "inputs": {"role": "reviewed"}}),
    )
    with pytest.raises(capsule.PreparationError, match="inputs changed"):
        capsule.prepare(SimpleNamespace(phase="bind-apply", receipt=str(receipt)))


def test_no_overwrite_and_digest_tampering(tmp_path):
    path = tmp_path / "receipt.json"
    capsule.write_new(path, capsule.sealed({"operation": "test"}))
    with pytest.raises(capsule.PreparationError, match="already exists"):
        capsule.write_new(path, {})
    path.write_text('{"operation":"tampered","sha256":"wrong"}')
    with pytest.raises(capsule.PreparationError, match="Invalid review"):
        capsule.read_sealed(path)


@pytest.mark.parametrize("probe_mode", ["context_failure", "ddl_success", "ddl_denied"])
def test_fresh_runtime_ddl_proof_requires_denial_after_session_setup(
    probe_mode, monkeypatch, tmp_path
):
    import daylily_tapdb
    import daylily_tapdb.cli.db_config as native_config
    import daylily_tapdb.web.runtime as native_runtime
    from sqlalchemy.exc import DBAPIError

    runtime_path = tmp_path / "runtime.yaml"
    runtime_path.write_text("private test config")
    runtime_path.chmod(0o600)
    cfg, _ = mappings()
    cfg["config_path"] = str(runtime_path)
    row = {
        key: False
        for key in (
            "temp",
            "db_create",
            "schema_create",
            "rolsuper",
            "rolbypassrls",
            "rolcreatedb",
            "rolcreaterole",
            "rolreplication",
            "rolinherit",
        )
    }
    row.update(
        connect=True,
        database=cfg["database"],
        role=cfg["user"],
        login=cfg["user"],
        config_identity=str(runtime_path),
        domain="M",
        owner="dewey",
        tenant="",
        allow_global="true",
        backend_pid=1,
    )
    monkeypatch.setattr(native_config, "get_db_config", lambda **kwargs: cfg)
    monkeypatch.setattr(capsule, "validate_runtime", lambda *args: None)
    monkeypatch.setattr(capsule.importlib.metadata, "version", lambda name: "9.0.0")
    monkeypatch.setattr(
        daylily_tapdb,
        "TemplateManager",
        lambda: SimpleNamespace(
            get_template=lambda *args, **kwargs: SimpleNamespace(
                instance_prefix="DGX", euid="template-reference"
            )
        ),
    )
    disposals, sessions = [], []
    monkeypatch.setattr(
        native_runtime, "dispose_all_runtime_engines", lambda: disposals.append(True)
    )

    class Denied(Exception):
        pgcode = "42501"

    class Session:
        def __init__(self, index):
            self.index = index

        def execute(self, *args):
            if self.index == 0:
                return SimpleNamespace(mappings=lambda: SimpleNamespace(one=lambda: row))
            if probe_mode == "ddl_denied":
                raise DBAPIError("test DDL", {}, Denied(), False)

    class DB:
        @contextmanager
        def session_scope(self, *, commit):
            assert commit is False
            index = len(sessions)
            sessions.append(index)
            if index > 0 and probe_mode == "context_failure":
                raise DBAPIError("test context", {}, Denied(), False)
            yield Session(index)

    monkeypatch.setattr(native_runtime, "get_db", lambda path: DB())
    args = SimpleNamespace(
        runtime_config=str(runtime_path), lane="rehearsal", receipt=str(tmp_path / "verified.json")
    )
    if probe_mode == "ddl_denied":
        result = capsule.verify_runtime(args)
        assert capsule.read_sealed(result)["status"] == "verified"
        assert len(disposals) == 4 and len(sessions) == 3
    else:
        expected = DBAPIError if probe_mode == "context_failure" else capsule.PreparationError
        with pytest.raises(expected):
            capsule.verify_runtime(args)
        assert not Path(args.receipt).exists()


@pytest.mark.parametrize("invalid_input", [None, "config", "version", "output"])
def test_runtime_verify_binds_native_context_only_after_input_validation(
    invalid_input, monkeypatch, tmp_path, explicit_tapdb_test_config
):
    from cli_core_yo import runtime as cli_runtime
    from daylily_tapdb.cli.context import active_config_path, clear_cli_context
    from daylily_tapdb.cli.db_config import get_admin_settings
    from daylily_tapdb.web import runtime as native_runtime

    cli_runtime._reset()
    clear_cli_context()
    calls = []
    native_get_db = native_runtime.get_db

    class EngineCreated(Exception):
        pass

    def check_runtime(cfg, lane, path):
        assert cfg["config_path"] == str(explicit_tapdb_test_config)
        assert path == explicit_tapdb_test_config and lane == "rehearsal"
        if invalid_input == "config":
            raise capsule.PreparationError("rejected isolated fixture")

    def get_db(path):
        calls.append(path)
        # Exercise the real engine/metrics construction, without opening a session.
        native_get_db(path)
        assert active_config_path() == explicit_tapdb_test_config
        assert get_admin_settings()["config_path"] == str(explicit_tapdb_test_config)
        raise EngineCreated

    receipt = tmp_path / "verified.json"
    if invalid_input == "output":
        receipt.write_text("existing receipt")
    monkeypatch.setattr(capsule, "validate_runtime", check_runtime)
    monkeypatch.setattr(
        capsule.importlib.metadata,
        "version",
        lambda name: "8.0.2" if invalid_input == "version" else "9.0.0",
    )
    monkeypatch.setattr(native_runtime, "get_db", get_db)
    try:
        expected = capsule.PreparationError if invalid_input else EngineCreated
        with pytest.raises(expected):
            capsule.verify_runtime(
                SimpleNamespace(
                    runtime_config=str(explicit_tapdb_test_config),
                    lane="rehearsal",
                    receipt=str(receipt),
                )
            )
        if invalid_input:
            assert calls == []
            assert active_config_path() is None
        else:
            assert calls == [str(explicit_tapdb_test_config)]
        assert receipt.exists() is (invalid_input == "output")
    finally:
        native_runtime.dispose_all_runtime_engines()
        clear_cli_context()
        cli_runtime._reset()
