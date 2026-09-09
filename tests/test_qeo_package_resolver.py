"""Bounded contract proofs; no AWS or live database calls."""

import copy
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from dewey_service.app import create_app
from dewey_service.auth import require_api_auth
from dewey_service.cli import app as cli_app
from dewey_service.qeo_package_contract import PackageRegistration
from dewey_service.qeo_resolver_auth import issue_resolver_credential, require_qeo_resolver_auth
from dewey_service.service import DeweyConflictError, DeweyNotFoundError
from dewey_service.tapdb_backend import ARTIFACT_TEMPLATE


def manifest(backend):
    files = []
    for role, name in [
        ("report", "report.html"),
        ("data", "unknown/tool-new.tsv"),
        ("data", "data/notes.txt"),
    ]:
        artifact = backend.create_instance(
            backend,
            template_code=ARTIFACT_TEMPLATE,
            name=name,
            json_addl={
                "storage_backend": "s3",
                "storage_uri": "s3://owner/" + name,
                "size": 4,
                "checksums": {"sha256": "a" * 64},
            },
        )
        files.append(
            {
                "artifact_euid": artifact.euid,
                "role": role,
                "relative_path": name,
                "sha256": "a" * 64,
                "size_bytes": 4,
            }
        )
    return {
        "contract": "dewey.multiqc-package/v1",
        "complete_data_package": True,
        "label": "Fixture package",
        "files": files,
    }


def test_register_replay_resolve_uses_lineage_and_no_writes(service, backend, monkeypatch):
    request = PackageRegistration.model_validate(manifest(backend))
    status, result = service.register_qeo_package(request, idempotency_key="fixture.package")
    assert status == 201
    assert len(backend.lineages) == len(request.files)
    assert service.register_qeo_package(request, idempotency_key="fixture.package") == (
        status,
        result,
    )
    before = copy.deepcopy((backend.instances, backend.lineages))

    @contextmanager
    def readonly(*, commit=False):
        assert commit is False
        yield backend

    monkeypatch.setattr(backend, "session_scope", readonly)

    def forbidden(*args, **kwargs):
        pytest.fail("Resolver attempted a write or bootstrap")

    for method in ["create_instance", "create_lineage", "update_instance_json", "ensure_templates"]:
        monkeypatch.setattr(backend, method, forbidden)
    assert (
        service.resolve_qeo_package(kind="artifact", euid=request.files[0].artifact_euid) == result
    )
    assert (
        service.resolve_qeo_package(kind="artifact_set", euid=result["artifact_set_euid"]) == result
    )
    assert (backend.instances, backend.lineages) == before
    assert [f["relative_path"] for f in result["files"]] == [f.relative_path for f in request.files]


def test_absent_ambiguous_and_broken_membership_fail_closed(service, backend):
    request = PackageRegistration.model_validate(manifest(backend))
    report = request.files[0].artifact_euid
    with pytest.raises(DeweyNotFoundError):
        service.resolve_qeo_package(kind="artifact", euid=report)
    _, result = service.register_qeo_package(request, idempotency_key="first")
    backend.lineages[-1].is_deleted = True
    with pytest.raises(DeweyConflictError, match="lineage"):
        service.resolve_qeo_package(kind="artifact_set", euid=result["artifact_set_euid"])
    backend.lineages[-1].is_deleted = False
    service.register_qeo_package(request, idempotency_key="second")
    with pytest.raises(DeweyConflictError, match="Multiple"):
        service.resolve_qeo_package(kind="artifact", euid=report)


@pytest.mark.parametrize("path", ["../escape", "/absolute", "a//b", "a/./b", "a\\b", "a\nb"])
def test_manifest_rejects_unsafe_paths(backend, path):
    body = manifest(backend)
    body["files"][1]["relative_path"] = path
    with pytest.raises(ValueError):
        PackageRegistration.model_validate(body)


def test_manifest_requires_explicit_completeness_and_unambiguous_roles(backend):
    body = manifest(backend)
    for amendment in [{"complete_data_package": False}, {"analysis_euid": "fixture.external"}]:
        with pytest.raises(ValueError):
            PackageRegistration.model_validate({**body, **amendment})
    body["files"][1]["role"] = "archive"
    with pytest.raises(ValueError, match="archive OR"):
        PackageRegistration.model_validate(body)


def test_token_private_exclusive_expiring_and_not_a_general_api_credential(tmp_path, test_settings):
    path = tmp_path / "token"
    receipt = issue_resolver_credential(path, lifetime_days=90)
    token = path.read_text().strip()
    assert path.stat().st_mode & 0o777 == 0o600
    assert token not in json.dumps(receipt)
    assert receipt["token_sha256"] == hashlib.sha256(token.encode()).hexdigest()
    with pytest.raises(FileExistsError):
        issue_resolver_credential(path, lifetime_days=90)
    test_settings.qeo_resolver_token_sha256 = receipt["token_sha256"]
    test_settings.qeo_resolver_token_expires_at = receipt["expires_at"]
    test_settings.api_bearer_tokens = (
        token  # Even accidental broad configuration cannot promote it.
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert require_qeo_resolver_auth(test_settings)(credentials) == "qeo"
    with pytest.raises(HTTPException) as exc:
        require_api_auth(test_settings)(credentials)
    assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc:
        require_qeo_resolver_auth(test_settings)(None)
    assert exc.value.status_code == 401
    test_settings.qeo_resolver_token_expires_at = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(HTTPException) as exc:
        require_qeo_resolver_auth(test_settings)(credentials)
    assert exc.value.status_code == 503


def test_public_credential_cli_is_runtime_exempt_and_never_prints_secret(tmp_path, monkeypatch):
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("CONDA_DEFAULT_ENV", raising=False)
    path = tmp_path / "token"
    result = CliRunner().invoke(
        cli_app, ["--json", "qeo", "resolver-credential-create", "--token-output-file", str(path)]
    )
    assert result.exit_code == 0, result.stdout
    receipt = json.loads(result.stdout)
    assert receipt["scope"] == "multiqc-package:resolve"
    assert path.read_text().strip() not in result.stdout


def test_real_route_accepts_only_dedicated_credential(tmp_path, test_settings, fake_service):
    path = tmp_path / "token"
    credential = issue_resolver_credential(path, lifetime_days=1)
    test_settings.qeo_resolver_token_sha256 = credential["token_sha256"]
    test_settings.qeo_resolver_token_expires_at = credential["expires_at"]
    calls = []

    def resolve(**kw):
        calls.append(kw)
        return {"fixture": "result"}

    fake_service.resolve_qeo_package = resolve
    with TestClient(
        create_app(settings=test_settings, service=fake_service), base_url="https://localhost:8914"
    ) as client:
        body = {"kind": "artifact", "euid": "fixture.report"}
        for token in ["", "token-123", "wrong"]:
            assert (
                client.post(
                    "/api/v1/resolve/multiqc",
                    json=body,
                    headers={"Authorization": "Bearer " + token},
                ).status_code
                == 401
            )
        assert not calls
        headers = {"Authorization": "Bearer " + path.read_text().strip()}
        assert client.post("/api/v1/resolve/multiqc", json=body, headers=headers).status_code == 200
        assert calls == [body]
        assert (
            client.post(
                "/api/v1/resolve/artifact",
                json={"artifact_euid": "fixture.report"},
                headers=headers,
            ).status_code
            == 401
        )
