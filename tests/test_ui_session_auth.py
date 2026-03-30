from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def _login_user(monkeypatch, client, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@example.com",
            "sub": "sub-1",
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
    redirect_url = login.headers["location"]
    parsed = urlparse(redirect_url)
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )


def test_root_redirects_to_ui(client) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui"


def test_ui_requires_session_login(client) -> None:
    response = client.get("/ui")
    assert response.status_code == 401


def test_cognito_callback_sets_session(monkeypatch, client) -> None:
    _login_user(monkeypatch, client)

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "Dewey Console" in ui.text
    assert "/admin" not in ui.text


def test_admin_session_exposes_admin_tab_and_page(monkeypatch, client) -> None:
    _login_user(monkeypatch, client, groups=["platform-admin"])

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "/admin" in ui.text

    admin = client.get("/admin")
    assert admin.status_code == 200
    assert "Dewey Admin" in admin.text
    assert "Operator Anomalies" in admin.text


def test_logout_clears_session_and_redirects_to_cognito(monkeypatch, client, test_settings) -> None:
    _login_user(monkeypatch, client)

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 303

    parsed = urlparse(logout.headers["location"])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "dewey-auth.example.com"
    assert parsed.path == "/logout"
    assert params["client_id"] == [test_settings.cognito_app_client_id]
    assert params["redirect_uri"] == [test_settings.cognito_logout_url.rstrip("/")]
    assert params["response_type"] == ["code"]
    assert params["state"][0]

    ui = client.get("/ui")
    assert ui.status_code == 401
