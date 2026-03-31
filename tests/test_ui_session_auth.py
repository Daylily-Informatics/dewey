from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient


def _login_user(
    monkeypatch,
    client,
    *,
    email: str = "operator@example.com",
    sub: str = "sub-1",
    name: str = "Operator Example",
    groups: list[str] | None = None,
) -> None:
    monkeypatch.setattr(
        "dewey_service.app.exchange_code",
        lambda settings, code: {"id_token": "header.payload.sig"},
    )
    monkeypatch.setattr(
        "dewey_service.app.decode_jwt_claims_noverify",
        lambda token: {
            "email": email,
            "sub": sub,
            "name": name,
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )

    login = client.get("/auth/login", follow_redirects=False)
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
    assert "Quick Register" in ui.text
    assert "/admin" not in ui.text


def test_dashboard_quick_register_infers_artifact_type_for_local_file(
    monkeypatch, client, fake_service
) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={"artifact_type": "n/a"},
        files=[("file_data", ("sample.vcf.gz", b"##fileformat=VCF", "application/gzip"))],
    )

    assert response.status_code == 200
    assert "Registered sample.vcf.gz as vcf." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "vcf"

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert f'href="/artifacts/euid/{artifact["artifact_euid"]}"' in ui.text
    assert f'action="/artifacts/euid/{artifact["artifact_euid"]}/download"' in ui.text


def test_dashboard_quick_register_imports_public_url(monkeypatch, client, fake_service) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={
            "artifact_type": "n/a",
            "source_url": "https://example.com/results/report.pdf",
        },
    )

    assert response.status_code == 200
    assert "Imported https://example.com/results/report.pdf as pdf." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "pdf"
    assert artifact["import_mode"] == "copy"
    assert artifact["source_uri"] == "https://example.com/results/report.pdf"


def test_dashboard_quick_register_references_s3_uri(monkeypatch, client, fake_service) -> None:
    _login_user(monkeypatch, client)

    response = client.post(
        "/ui/register",
        data={
            "artifact_type": "n/a",
            "source_s3_uri": "s3://demo-bucket/path/sample.bam",
        },
    )

    assert response.status_code == 200
    assert "Registered s3://demo-bucket/path/sample.bam as bam." in response.text
    artifact = next(iter(fake_service.artifacts.values()))
    assert artifact["artifact_type"] == "bam"
    assert artifact["import_mode"] == "reference"
    assert artifact["storage_uri"] == "s3://demo-bucket/path/sample.bam"


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
    assert params["logout_uri"] == [test_settings.cognito_logout_url.rstrip("/")]
    assert params["state"][0]

    ui = client.get("/ui")
    assert ui.status_code == 401


def test_two_browsers_can_keep_distinct_authenticated_sessions(monkeypatch, client) -> None:
    _login_user(
        monkeypatch,
        client,
        email="operator-a@example.com",
        sub="sub-a",
        name="Operator A",
    )

    with TestClient(client.app) as other_client:
        _login_user(
            monkeypatch,
            other_client,
            email="operator-b@example.com",
            sub="sub-b",
            name="Operator B",
        )

        ui_a = client.get("/ui")
        ui_b = other_client.get("/ui")

        assert ui_a.status_code == 200
        assert ui_b.status_code == 200
        assert "operator-a@example.com" in ui_a.text
        assert "operator-b@example.com" not in ui_a.text
        assert "operator-b@example.com" in ui_b.text
        assert "operator-a@example.com" not in ui_b.text


def test_logout_from_one_browser_does_not_clear_the_other(monkeypatch, client) -> None:
    _login_user(
        monkeypatch,
        client,
        email="shared@example.com",
        sub="sub-shared",
        name="Shared Operator",
    )

    with TestClient(client.app) as other_client:
        _login_user(
            monkeypatch,
            other_client,
            email="shared@example.com",
            sub="sub-shared",
            name="Shared Operator",
        )

        logout = client.post("/logout", follow_redirects=False)
        assert logout.status_code == 303

        assert client.get("/ui").status_code == 401
        ui_other = other_client.get("/ui")
        assert ui_other.status_code == 200
        assert "shared@example.com" in ui_other.text
