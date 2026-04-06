from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

import dewey_service.domain_access as domain_access
import dewey_service.schema_drift as schema_drift


def test_domain_host_normalization_and_approval() -> None:
    assert domain_access._normalize_host("") == ""
    assert domain_access._normalize_host(
        "https://USER@example.daylilyinformatics.com:8443/path"
    ) == ("example.daylilyinformatics.com")
    assert domain_access._normalize_host("localhost:8914") == "localhost"
    assert domain_access._normalize_host("[::1]:8914") == "::1"
    assert domain_access._normalize_host("https://portal.lsmc.bio./") == "portal.lsmc.bio"

    assert domain_access.is_approved_domain("daylilyinformatics.com") is True
    assert domain_access.is_approved_domain("portal.daylilyinformatics.com") is True
    assert domain_access.is_approved_domain("example.org") is False
    assert domain_access.is_local_host("https://localhost:8914") is True
    assert domain_access.is_local_host("api.daylilyinformatics.com") is False


def test_domain_allowed_origin_and_host_lists() -> None:
    assert domain_access.is_allowed_origin("", allow_local=False) is False
    assert (
        domain_access.is_allowed_origin("http://portal.daylilyinformatics.com", allow_local=False)
        is False
    )
    assert (
        domain_access.is_allowed_origin("https://portal.daylilyinformatics.com", allow_local=False)
        is True
    )
    assert domain_access.is_allowed_origin("https://localhost:8914", allow_local=False) is False
    assert domain_access.is_allowed_origin("https://localhost:8914", allow_local=True) is True
    assert domain_access.is_allowed_origin("https://example.org", allow_local=True) is False

    trusted_no_local = domain_access.build_trusted_hosts(allow_local=False)
    trusted_local = domain_access.build_trusted_hosts(allow_local=True)
    assert "localhost" not in trusted_no_local
    assert "localhost" in trusted_local
    assert "*.daylilyinformatics.com" in trusted_local
    assert "daylilyinformatics.com" in trusted_local

    regex_no_local = re.compile(domain_access.build_allowed_origin_regex(allow_local=False))
    regex_local = re.compile(domain_access.build_allowed_origin_regex(allow_local=True))
    assert regex_no_local.match("https://portal.daylilyinformatics.com:8443")
    assert regex_no_local.match("https://sub.api.lsmc.bio")
    assert not regex_no_local.match("https://localhost:8914")
    assert regex_local.match("https://localhost:8914")
    assert regex_local.match("https://[::1]:8914")
    assert not regex_local.match("https://example.org")


def test_default_schema_drift_payload_and_tool_version(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as ctx:
        ctx.setattr(schema_drift, "_tool_version", lambda: "4.0.6")
        assert schema_drift.default_schema_drift_payload("dev") == {
            "status": "not_run",
            "checked_at": None,
            "environment": "dev",
            "tool_version": "4.0.6",
            "summary": "Schema drift check has not been run.",
            "report": {},
            "strict": False,
        }

    monkeypatch.setattr(schema_drift, "version", lambda _name: "4.0.6")
    assert schema_drift._tool_version() == "4.0.6"

    def raise_not_found(_name: str) -> str:
        raise schema_drift.PackageNotFoundError

    monkeypatch.setattr(schema_drift, "version", raise_not_found)
    assert schema_drift._tool_version() == ""


def test_load_schema_drift_payload_returns_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    source_payload = {"status": "clean", "report": {"counts": {"expected": 1}}}
    monkeypatch.setattr(schema_drift, "_cached_schema_drift_payload", lambda *args: source_payload)

    settings = SimpleNamespace(
        database_target="local",
        tapdb_client_id="dewey",
        aws_profile="lsmc",
        aws_region="us-west-2",
        tapdb_database_name="dewey",
        tapdb_env="dev",
    )
    loaded = schema_drift.load_schema_drift_payload(settings)
    loaded["status"] = "changed"

    assert source_payload["status"] == "clean"


def test_cached_schema_drift_payload_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    schema_drift._cached_schema_drift_payload.cache_clear()
    calls: list[dict[str, object]] = []

    def fake_run(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "clean", "summary": "ok"}

    monkeypatch.setattr(schema_drift, "run_tapdb_schema_drift_check", fake_run)
    success = schema_drift._cached_schema_drift_payload(
        "local",
        "dewey",
        "lsmc",
        "us-west-2",
        "dewey",
        "dev",
    )

    assert success == {"status": "clean", "summary": "ok"}
    assert calls == [
        {
            "target": "local",
            "client_id": "dewey",
            "profile": "lsmc",
            "region": "us-west-2",
            "namespace": "dewey",
            "tapdb_env": "dev",
        }
    ]

    schema_drift._cached_schema_drift_payload.cache_clear()
    monkeypatch.setattr(
        schema_drift,
        "default_schema_drift_payload",
        lambda environment="": {
            "status": "not_run",
            "checked_at": None,
            "environment": environment,
            "tool_version": "4.0.6",
            "summary": "Schema drift check has not been run.",
            "report": {},
            "strict": False,
        },
    )
    monkeypatch.setattr(
        schema_drift,
        "run_tapdb_schema_drift_check",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("tapdb broke")),
    )

    failure = schema_drift._cached_schema_drift_payload(
        "local",
        "dewey",
        "lsmc",
        "us-west-2",
        "dewey",
        "dev",
    )

    assert failure == {
        "status": "check_failed",
        "checked_at": None,
        "environment": "dev",
        "tool_version": "4.0.6",
        "summary": "Unable to execute tapdb drift-check: tapdb broke",
        "report": {},
        "strict": False,
    }
