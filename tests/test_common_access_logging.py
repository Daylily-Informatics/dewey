from __future__ import annotations

import json
import logging
from types import SimpleNamespace

from dewey_service.app import _access_log_payload, _emit_access_log


def test_common_access_log_payload_is_json(caplog) -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(
            request_id="req-1",
            correlation_id="corr-1",
            auth_mode="cognito",
            authorized_by_email="johnm@lsmc.com",
        ),
        client=SimpleNamespace(host="127.0.0.1"),
        method="GET",
        url=SimpleNamespace(path="/api/v1/artifacts"),
    )
    payload = _access_log_payload(
        request=request,
        service_id="dewey",
        status_code=200,
        duration_ms=12.34,
        route_template="/api/v1/artifacts",
    )

    with caplog.at_level(logging.INFO, logger="lsmc.access"):
        _emit_access_log(payload)

    body = json.loads([record for record in caplog.records if record.name == "lsmc.access"][-1].getMessage())
    assert body["event"] == "request_completed"
    assert body["request_id"] == "req-1"
    assert body["service_id"] == "dewey"
    assert body["actor"] == "johnm@lsmc.com"
    assert body["ai_agent_id"] is None
    assert body["authorizing_human"] == "johnm@lsmc.com"
    assert body["ip"] == "127.0.0.1"
    assert body["route_template"] == "/api/v1/artifacts"
    assert body["status"] == 200
    assert body["denial_reason"] is None
    assert body["auth_mode"] == "cognito"
