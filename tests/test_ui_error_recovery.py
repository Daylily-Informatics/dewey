"""Account-switch recovery without widening access or changing API errors."""

from html import escape

import pytest
from fastapi import HTTPException

from dewey_service.literature import LiteratureUnavailableError
from dewey_service.service import DeweyNotFoundError


@pytest.mark.parametrize(
    "error,status_code,message",
    [
        (HTTPException(403, "No current recipient grant"), 403, "No current recipient grant"),
        (HTTPException(410, "Share expired"), 410, "Share expired"),
        (DeweyNotFoundError("Share missing"), 404, "Share missing"),
        (LiteratureUnavailableError("Literature unavailable"), 503, "Literature unavailable"),
        (HTTPException(403, '<script>alert("x")</script>'), 403, '<script>alert("x")</script>'),
    ],
)
def test_standalone_errors_offer_logout_and_preserve_api_errors(client, error, status_code, message):
    def fail():
        raise error

    client.app.add_api_route("/recovery-fixture", fail)
    client.app.add_api_route("/api/recovery-fixture", fail)
    response = client.get("/recovery-fixture", headers={"Accept": "text/html"})
    assert response.status_code == status_code
    assert escape(message) in response.text
    assert '<script>' not in response.text
    assert 'href="https://localhost/auth/logout"' in response.text
    assert "Log out of Dewey / switch accounts" in response.text

    api = client.get("/api/recovery-fixture", headers={"Accept": "text/html"})
    assert api.status_code == status_code
    assert api.json() == {"detail": message}


@pytest.mark.parametrize("recipient_only,path", [(True, "/ui"), (False, "/admin")])
def test_browser_middleware_denials_offer_logout(client, monkeypatch, recipient_only, path):
    monkeypatch.setattr(
        "dewey_service.auth._load_ui_profile",
        lambda request: {
            "sub": "account-fixture", "email": "recipient@example.test",
            "roles": ["READ_ONLY"], "groups": [], "recipient_only": recipient_only,
        },
    )
    browser = client.get(path, headers={"Accept": "text/html"})
    assert browser.status_code == 403
    assert 'href="https://localhost/auth/logout"' in browser.text
    machine = client.get(path)
    assert machine.status_code == 403
    assert machine.headers["content-type"].startswith("application/json")


def test_share_boundary_browser_denial_preserves_status_and_headers(client):
    response = client.get("/fetch/fixture", headers={"Accept": "text/html"})
    assert response.status_code == 403
    assert response.headers["cache-control"] == "no-store"
    assert "Verified sharing ingress is required" in response.text
    assert 'href="https://localhost/auth/logout"' in response.text


def test_authentication_error_offers_existing_logout_route(client):
    response = client.get("/auth/error?reason=not_authorized")
    assert response.status_code == 403
    assert 'href="/auth/logout"' in response.text
    assert "Log out of Dewey / switch accounts" in response.text
