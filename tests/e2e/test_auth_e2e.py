from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.auth_helpers import assert_authenticated_page, perform_login, perform_logout


@pytest.mark.e2e
def test_login_round_trip(page: Page, base_url: str, e2e_email: str, e2e_password: str):
    perform_login(page, base_url=base_url, email=e2e_email, password=e2e_password)
    expect(page).to_have_url(f"{base_url}/ui")
    assert_authenticated_page(page)


@pytest.mark.e2e
def test_logout_round_trip(page: Page, base_url: str, e2e_email: str, e2e_password: str):
    perform_login(page, base_url=base_url, email=e2e_email, password=e2e_password)
    page.goto(f"{base_url}/ui")
    perform_logout(page)
    page.wait_for_url(f"{base_url}/**", timeout=30000)

    response = page.goto(f"{base_url}/ui")
    assert response is not None
    assert response.status in {200, 302, 303}
    page.wait_for_url(f"{base_url}/login**", timeout=15000)
