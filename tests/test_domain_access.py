from __future__ import annotations


def test_dewey_allows_approved_origin_preflight(client) -> None:
    response = client.options(
        "/ui",
        headers={
            "Origin": "https://portal.lsmc.bio",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://portal.lsmc.bio"


def test_dewey_rejects_disallowed_origin(client) -> None:
    response = client.options(
        "/ui",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 403
    assert response.text == "Origin not allowed"


def test_dewey_rejects_disallowed_host(client) -> None:
    response = client.get("/ui", headers={"host": "evil.example.com"}, follow_redirects=False)

    assert response.status_code == 400
