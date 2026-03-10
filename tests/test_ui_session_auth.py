from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def test_ui_requires_session_login(client) -> None:
    response = client.get("/ui")
    assert response.status_code == 401


def test_cognito_callback_sets_session(monkeypatch, client) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {"email": "operator@example.com", "sub": "sub-1"},
    )

    login = client.get("/auth/login", follow_redirects=False)
    assert login.status_code in {307, 302}
    redirect_url = login.headers["location"]
    parsed = urlparse(redirect_url)
    state = parse_qs(parsed.query)["state"][0]

    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 303
    assert callback.headers["location"] == "/ui"

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "Dewey Operator Console" in ui.text
