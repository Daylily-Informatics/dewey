from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Page, expect


def perform_login(page: Page, *, base_url: str, email: str, password: str) -> None:
    page.goto(f"{base_url}/login")
    expect(page.locator("body")).to_be_visible()
    page.locator("a:has-text('Continue with LSMC Login')").click()
    _complete_identity_provider_login(page, email=email, password=password)
    page.wait_for_url(f"{base_url}/**", timeout=30000)
    assert_authenticated_page(page)


def perform_logout(page: Page) -> None:
    page.locator("button:has-text('Logout')").click()


def assert_authenticated_page(page: Page) -> None:
    expect(page.locator("body")).to_be_visible()
    body = page.locator("body").inner_text().lower()
    for snippet in ("authentication failed", "admin access required", "login required"):
        assert snippet not in body, f"Unexpected auth failure content detected: {snippet}"


def _is_google_identity_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "accounts.google.com" or host.endswith(".accounts.google.com")


def _complete_identity_provider_login(page: Page, *, email: str, password: str) -> None:
    page.wait_for_load_state("domcontentloaded")
    try:
        if _is_google_identity_host(page.url):
            _complete_google_login(page, email=email, password=password)
            return
        if page.locator("input[type='email']").first.is_visible(
            timeout=3000
        ) and _is_google_identity_host(page.url):
            _complete_google_login(page, email=email, password=password)
            return
    except Exception:
        pass
    _complete_cognito_login(page, email=email, password=password)


def _complete_cognito_login(page: Page, *, email: str, password: str) -> None:
    user_input = page.locator("input[name='username']:visible, input[type='email']:visible").first
    pass_input = page.locator(
        "input[name='password']:visible, input[type='password']:visible"
    ).first
    submit_btn = page.locator(
        "input[name='signInSubmitButton']:visible, button[type='submit']:visible"
    ).first

    expect(user_input).to_be_visible(timeout=15000)
    user_input.fill(email)
    pass_input.fill(password)
    submit_btn.click()


def _complete_google_login(page: Page, *, email: str, password: str) -> None:
    email_input = page.locator("input[type='email']").first
    expect(email_input).to_be_visible(timeout=15000)
    email_input.fill(email)
    page.locator("#identifierNext, button:has-text('Next')").first.click()

    password_input = page.locator("input[type='password']").first
    expect(password_input).to_be_visible(timeout=15000)
    password_input.fill(password)
    page.locator("#passwordNext, button:has-text('Next')").first.click()
