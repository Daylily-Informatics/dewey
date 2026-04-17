from __future__ import annotations

import re

from dewey_service.domain_access import (
    build_allowed_origin_regex,
    build_trusted_hosts,
    is_allowed_origin,
)


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


def test_domain_access_allows_explicit_dns_and_ip_hosts() -> None:
    configured_hosts = ["dewey.dev2.lsmc.life", "54.218.100.68", "2600:1f14::1234"]

    assert "dewey.dev2.lsmc.life" in build_trusted_hosts(
        allow_local=False,
        additional_hosts=configured_hosts,
    )
    assert "54.218.100.68" in build_trusted_hosts(
        allow_local=False,
        additional_hosts=configured_hosts,
    )
    assert "[2600:1f14::1234]" in build_trusted_hosts(
        allow_local=False,
        additional_hosts=configured_hosts,
    )
    assert is_allowed_origin(
        "https://dewey.dev2.lsmc.life",
        allow_local=False,
        additional_hosts=configured_hosts,
    )
    assert is_allowed_origin(
        "https://54.218.100.68:8914",
        allow_local=False,
        additional_hosts=configured_hosts,
    )
    assert re.fullmatch(
        build_allowed_origin_regex(
            allow_local=False,
            additional_hosts=configured_hosts,
        ),
        "https://[2600:1f14::1234]:8914",
    )


def test_domain_access_allows_explicit_localhost_in_production_mode() -> None:
    assert is_allowed_origin(
        "http://localhost:8914",
        allow_local=False,
        additional_hosts=["localhost"],
    )
