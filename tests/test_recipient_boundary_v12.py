"""Public transport must not turn recipient access into management authority."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dewey_service.registry_access import Principal, principal_context
from dewey_service.share_context import (
    ManagedShareIngressMiddleware,
    share_context_available,
    share_context_context,
)
from dewey_service.share_routing import ShareHostBoundaryMiddleware, validate_sharing_configuration


def settings():
    return SimpleNamespace(
        share_trusted_proxy_peer="127.0.0.1",
        share_ingress_assertion_header="X-Dewey-Tailnet-Assertion",
        share_ingress_assertion="private-fixture-" * 3,
        share_public_ingress_assertion_header="X-Dewey-Recipient-Assertion",
        share_public_ingress_assertion="public-fixture-" * 3,
        share_application_origin="https://dewey.example.test",
        share_content_host_suffix="content.example.test",
        share_session_generation="generation-fixture",
    )


def client():
    config = settings()
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "DELETE"])
    def echo(path: str):
        return {"reached": path}

    app.add_middleware(ShareHostBoundaryMiddleware, settings=config)
    app.add_middleware(ManagedShareIngressMiddleware, settings=config)
    return TestClient(app, base_url=config.share_application_origin, client=("127.0.0.1", 40000))


def public_headers():
    return {"X-Dewey-Recipient-Assertion": settings().share_public_ingress_assertion}


@pytest.mark.parametrize(
    "path", ["/api/v1/registry/admin", "/api/v1/account/tokens", "/tapdb", "/ui", "/shares"]
)
def test_public_assertion_cannot_reach_manager_surfaces(path):
    assert client().get(path, headers=public_headers()).status_code == 404


@pytest.mark.parametrize(
    "path", ["/fetch/share-fixture", "/api/v2/recipient/shares/share-fixture", "/recipient/account"]
)
def test_exact_public_recipient_routes(path):
    assert client().get(path, headers=public_headers()).status_code == 200
    assert client().get(path).status_code == 403


def test_public_spoof_conflicting_and_duplicate_assertions_fail():
    c = client()
    assert (
        c.get("/fetch/share-fixture", headers={"X-Dewey-Recipient-Assertion": "forged"}).status_code
        == 403
    )
    headers = [*public_headers().items(), *public_headers().items()]
    assert c.get("/fetch/share-fixture", headers=headers).status_code == 403
    headers = {**public_headers(), "X-Dewey-Tailnet-Assertion": settings().share_ingress_assertion}
    assert c.get("/fetch/share-fixture", headers=headers).status_code == 403


def test_origin_and_host_are_exact():
    c = client()
    assert (
        c.get(
            "/fetch/share-fixture", headers={**public_headers(), "Host": "unapproved.example.test"}
        ).status_code
        == 404
    )
    assert (
        c.post(
            "/api/v2/recipient/tokens",
            headers={**public_headers(), "Origin": "https://unapproved.example.test"},
        ).status_code
        == 403
    )
    assert c.delete("/fetch/share-fixture", headers=public_headers()).status_code == 404


def test_isolated_host_does_not_expose_application_routes():
    c = client()
    host = "pv-" + "a" * 32 + ".content.example.test"
    headers = {**public_headers(), "Host": host}
    assert c.get("/api/v2/recipient/tokens", headers=headers).status_code == 404
    assert c.get("/__dewey_preview/assets/file.css", headers=headers).status_code == 200
    assert c.post("/__dewey_preview/assets/file.css", headers=headers).status_code == 404
    assert c.get("/__dewey_preview/assets/file.css", headers=public_headers()).status_code == 404


def test_verified_ingress_requires_verified_current_email():
    ctx = {"public_recipient": True, "trusted_tailnet": False, "managed_origin": True}
    with share_context_context(ctx):
        with principal_context(Principal("recipient-fixture", "recipient@example.test")):
            assert not share_context_available()
        with principal_context(
            Principal("recipient-fixture", "recipient@example.test", email_verified=True)
        ):
            assert share_context_available()
        with principal_context(
            Principal("service-fixture", "service@example.test", service=True, email_verified=True)
        ):
            assert not share_context_available()


def test_identical_public_private_secret_rejected():
    config = settings()
    config.share_public_ingress_assertion = config.share_ingress_assertion
    with pytest.raises(RuntimeError, match="must differ"):
        validate_sharing_configuration(config)


def test_revoked_cookie_cannot_block_new_login_or_logout(monkeypatch):
    from fastapi import HTTPException

    from dewey_service.registry_access import RegistryPrincipalMiddleware

    app = FastAPI()
    app.state.settings = SimpleNamespace(registry_internal_domains=[], api_tokens=lambda: [])
    profile = {
        "email": "recipient@example.test",
        "sub": "fixture-user",
        "roles": ["READ_ONLY"],
        "groups": [],
        "identity_grant_id": "fixture-expired",
        "identity_revision": 1,
    }
    monkeypatch.setattr("dewey_service.auth._load_ui_profile", lambda request: profile)

    def revoked(*args, **kwargs):
        raise HTTPException(401, "Credential revoked")

    monkeypatch.setattr("dewey_service.recipient_identity.verify_recipient_binding", revoked)

    @app.get("/{path:path}")
    def reachable(path: str):
        return {"path": path}

    app.add_middleware(RegistryPrincipalMiddleware)
    client = TestClient(app)
    assert client.get("/fetch/fixture-share").status_code == 401
    for path in ("/auth/login", "/auth/lsmc/callback", "/auth/logout"):
        assert client.get(path).status_code == 200
