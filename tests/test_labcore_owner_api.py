from __future__ import annotations

import inspect
import json
from pathlib import Path

from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.labcore_owner_api import LabcoreOwnerRegistrationResponse
from dewey_service.labcore_owner_command import (
    COMMAND_TYPE,
    COMMAND_VERSION,
    HASH_DOMAIN,
    bind_registration_command,
)
from dewey_service.labcore_owner_config import (
    LABCORE_OWNER_WRITE_SCOPE,
    LabcoreOwnerApiConfig,
)
from dewey_service.labcore_owner_contracts import bind_request_hash
from dewey_service.service import DeweyConflictError, DeweyNotFoundError
from dewey_service.settings import Settings
from tests.conftest import FakeDeweyService

GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "contracts/dynamic_workflow/labcore_sequencing_run_owner.v1.golden.json"
)


class ReceiptService(FakeDeweyService):
    response_code = 201

    def register_labcore_sequencing_run_owner(self, *, request_body, principal_id):
        assert principal_id == "owy-v4"
        request = request_body.owner_request
        return self.response_code, {
            "registration_receipt_euid": "RCP-000001",
            "request_sha256": request.request_sha256,
            "command_sha256": request_body.command_sha256,
            "tenant_euid": request.tenant_euid,
            "external_object_euid": "EX-000001",
            "external_object_relation_euid": "ER-000001",
        }


def _settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


def _command() -> dict[str, object]:
    raw = json.loads(GOLDEN.read_text(encoding="utf-8"))["raw"]
    frozen = bind_request_hash(raw)
    return bind_registration_command(
        {
            "command_type": COMMAND_TYPE,
            "command_version": COMMAND_VERSION,
            "hash_domain": HASH_DOMAIN,
            "test_euid": "TEST-A",
            "owner_request": frozen,
        }
    )


def _config() -> LabcoreOwnerApiConfig:
    return LabcoreOwnerApiConfig.model_validate(
        {
            "api_enabled": True,
            "service_principals": [
                {
                    "principal_id": "owy-v4",
                    "bearer_token": "owner-token",
                    "tenant_euid": "TENANT-INTERNAL-TEST",
                    "scopes": [LABCORE_OWNER_WRITE_SCOPE],
                }
            ],
        }
    )


def _headers(command: dict[str, object]) -> dict[str, str]:
    return {
        "Authorization": "Bearer owner-token",
        "Idempotency-Key": str(command["command_sha256"]),
    }


def test_default_off_routes_are_absent(monkeypatch) -> None:
    monkeypatch.setattr(
        "dewey_service.labcore_owner_api.load_labcore_owner_config", lambda: LabcoreOwnerApiConfig()
    )
    with TestClient(create_app(settings=_settings(), service=ReceiptService())) as client:
        assert client.post("/api/v2/sequencer-runs/register").status_code == 404


def test_v2_auth_command_header_and_redacted_validation(monkeypatch) -> None:
    monkeypatch.setattr("dewey_service.labcore_owner_api.load_labcore_owner_config", _config)
    command = _command()
    with TestClient(create_app(settings=_settings(), service=ReceiptService())) as client:
        path = "/api/v2/sequencer-runs/register"
        assert client.post(path, json=command).status_code == 401
        assert (
            client.post(path, headers={"Authorization": "Bearer bad"}, json=command).status_code
            == 401
        )
        assert (
            client.post(
                path, headers={"Authorization": "Bearer owner-token"}, json=command
            ).status_code
            == 422
        )
        assert client.post(path, headers=_headers(command), json=command).status_code == 201
        bad = {
            "test_euid": "TEST-A",
            "owner_request": {"dataset_root_uri": "s3://private/raw.fastq"},
        }
        response = client.post(
            path, headers={**_headers(command), "Idempotency-Key": "0" * 64}, json=bad
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid Labcore owner registration"}
        assert "private" not in response.text and "fastq" not in response.text


def test_openapi_and_actual_statuses_are_closed(monkeypatch) -> None:
    monkeypatch.setattr("dewey_service.labcore_owner_api.load_labcore_owner_config", _config)
    command = _command()
    schema = create_app(settings=_settings(), service=ReceiptService()).openapi()
    operation = schema["paths"]["/api/v2/sequencer-runs/register"]["post"]
    header = next(item for item in operation["parameters"] if item["name"] == "Idempotency-Key")
    assert header["required"] is True
    assert {"200", "201", "400", "401", "403", "404", "409", "422", "503"} <= set(
        operation["responses"]
    )
    assert LabcoreOwnerRegistrationResponse.model_json_schema()["additionalProperties"] is False

    app = create_app(settings=_settings(), service=ReceiptService())

    def all_routes(routes):
        for route in routes:
            yield route
            nested = getattr(route, "routes", None)
            if nested is None:
                nested = getattr(getattr(route, "original_router", None), "routes", ())
            yield from all_routes(nested)

    registration_route = next(
        route
        for route in all_routes(app.routes)
        if getattr(route, "path", None) == "/api/v2/sequencer-runs/register"
    )
    assert not inspect.iscoroutinefunction(registration_route.endpoint)

    cases = (
        (ReceiptService(), 201),
        (type("Replay", (ReceiptService,), {"response_code": 200})(), 200),
    )
    for service, expected in cases:
        with TestClient(create_app(settings=_settings(), service=service)) as client:
            assert (
                client.post(
                    "/api/v2/sequencer-runs/register", headers=_headers(command), json=command
                ).status_code
                == expected
            )

    for error, expected in (
        (DeweyNotFoundError("x"), 404),
        (DeweyConflictError("x"), 409),
        (RuntimeError("x"), 503),
    ):
        service = ReceiptService()
        service.register_labcore_sequencing_run_owner = lambda **_: (_ for _ in ()).throw(error)
        with TestClient(create_app(settings=_settings(), service=service)) as client:
            assert (
                client.post(
                    "/api/v2/sequencer-runs/register", headers=_headers(command), json=command
                ).status_code
                == expected
            )


def test_single_route_bounds_and_principal_separation(monkeypatch):
    import pytest

    monkeypatch.setattr("dewey_service.labcore_owner_api.load_labcore_owner_config", _config)
    config = _settings().model_copy(update={"api_bearer_tokens": "owner-token"})
    with pytest.raises(ValueError, match="distinct"):
        create_app(settings=config, service=ReceiptService())
    with TestClient(create_app(settings=_settings(), service=ReceiptService())) as client:
        command = _command()
        for old in ("/api/v2/external-objects", "/api/v2/external-object-relations"):
            assert client.post(old, headers=_headers(command), json=command).status_code == 404
        path = "/api/v2/sequencer-runs/register"
        assert (
            client.post(
                path, headers=_headers(command), content=b"x" * (16 * 1024 * 1024 + 1)
            ).status_code
            == 413
        )
        assert (
            client.post(
                path, headers={**_headers(command), "Idempotency-Key": "0" * 64}, json=command
            ).status_code
            == 409
        )
        raw = dict(command["owner_request"])
        raw["tenant_euid"] = "different-tenant"
        changed = bind_registration_command({**command, "owner_request": bind_request_hash(raw)})
        assert client.post(path, headers=_headers(changed), json=changed).status_code == 403


def test_inventory_limits_preserve_valid_command_hashes():
    import pytest
    from pydantic import ValidationError

    from dewey_service.labcore_owner_command import LabcoreSequencingRunRegistrationCommandV2

    original = _command()
    raw = dict(original["owner_request"])
    raw["expected_files"] = [{**raw["expected_files"][0], "relative_path": "a" * 1024}]
    valid = bind_registration_command({**original, "owner_request": bind_request_hash(raw)})
    parsed = LabcoreSequencingRunRegistrationCommandV2.model_validate(valid)
    assert parsed.command_sha256 == valid["command_sha256"]
    raw["expected_files"][0]["relative_path"] = "é" * 513
    invalid = bind_registration_command({**original, "owner_request": bind_request_hash(raw)})
    with pytest.raises(ValidationError, match="1,024 UTF-8"):
        LabcoreSequencingRunRegistrationCommandV2.model_validate(invalid)
    base = original["owner_request"]["expected_files"][0]
    raw["expected_files"] = [{**base, "relative_path": str(i)} for i in range(50_001)]
    invalid = bind_registration_command({**original, "owner_request": bind_request_hash(raw)})
    with pytest.raises(ValidationError, match="50,000"):
        LabcoreSequencingRunRegistrationCommandV2.model_validate(invalid)
