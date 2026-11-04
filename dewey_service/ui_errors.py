"""Recovery links for standalone Dewey browser errors."""

from html import escape

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse


def standalone_error_response(
    request: Request, detail, *, status_code: int, headers=None, application_origin=None
):
    # The configured application origin also works from an isolated report host.
    origin = (
        application_origin
        if application_origin is not None
        else request.app.state.settings.share_application_origin
    )
    logout_href = origin + "/auth/logout"
    content = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Unable to open page · Dewey</title></head><body><main>'
        '<h1>Dewey could not open this page</h1>'
        f'<p>Status {status_code}</p><p>{escape(str(detail or ""))}</p>'
        '<p>To use a different account, sign out of Dewey and sign in again.</p>'
        f'<p><a href="{escape(logout_href, quote=True)}">Log out of Dewey / switch accounts</a></p>'
        '</main></body></html>'
    )
    return HTMLResponse(content, status_code=status_code, headers=headers)


def access_error_response(
    request: Request, detail, *, status_code: int, headers=None, application_origin=None
):
    """Offer browser recovery while retaining API and credential-client JSON."""
    if (
        "text/html" in request.headers.get("accept", "").lower()
        and not request.url.path.startswith("/api/")
        and not request.headers.get("authorization")
    ):
        return standalone_error_response(
            request, detail, status_code=status_code, headers=headers,
            application_origin=application_origin,
        )
    return JSONResponse({"detail": detail}, status_code=status_code, headers=headers)
