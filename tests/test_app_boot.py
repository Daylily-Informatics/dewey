from __future__ import annotations

from dewey_service.app import create_app


def test_create_app_boots_with_injected_service(test_settings, fake_service) -> None:
    app = create_app(settings=test_settings, service=fake_service)
    assert app.title == "Dewey Artifact Service"
    assert app.state.observability is not None
