#!/usr/bin/env python3
"""Read-only cookie-size diagnosis using retained handoff and native binding.

Run on the deployment host as an operator with Docker access. The private handoff
stays in process memory and is passed directly to the Dewey process on stdin.
Only integer lengths/counts and booleans reach stdout. No HTTP authentication,
grants, cookies, users, or files are created by this probe.
"""
import argparse
import json
import subprocess


LOGIN_READ = r'''
import json, os
from pathlib import Path
from psycopg2 import sql
from lsmc_oauth_login.settings import load_settings_file
from lsmc_oauth_login.postgres_state import _connect
from lsmc_oauth_login.handoff import HandoffPayload
settings = load_settings_file(Path(os.environ["LSMC_OAUTH_LOGIN_CONFIG"]))
connection = _connect(settings.state_database)
connection.set_session(readonly=True)
try:
    with connection, connection.cursor() as cursor:
        cursor.execute(sql.SQL("select payload from {}.handoff_codes where consumed_at is not null and payload->>'service' = %s and payload->'recipient_identity' is not null order by consumed_at desc limit 1").format(sql.Identifier(settings.state_database.schema_name)), ("dewey",))
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No retained consumed Dewey identity handoff")
        result = HandoffPayload.model_validate(row[0]).model_dump(mode="json", exclude_none=True)
        print(json.dumps(result))
finally:
    connection.close()
'''


DEWEY_MEASURE = r'''
import json, os, sys
from base64 import b64encode
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from dewey_service.container_entry import _initialize_runtime_context
_initialize_runtime_context(Path(os.environ["DEWEY_CONFIG"]))
from dewey_service.settings import get_settings
from dewey_service.auth import build_web_session_config, resolve_external_broker_principal
from daylily_auth_cognito.browser.session import store_session_principal
from dewey_service.tapdb_backend import TapDBBackend, normalize_instance_payload
from daylily_tapdb import generic_instance

handoff = json.load(sys.stdin)
settings = get_settings()
config = build_web_session_config(settings=settings)
user = dict(handoff["user"], recipient_identity=handoff["recipient_identity"])
app = SimpleNamespace(state=SimpleNamespace(settings=settings, web_session_config=config))
request = Request({"type": "http", "method": "GET", "path": "/auth/lsmc/callback", "headers": [], "session": {}, "app": app})
principal = resolve_external_broker_principal(user, request)
backend = TapDBBackend()
with backend.session_scope(commit=False) as session:
    row = session.query(generic_instance).filter(
        generic_instance.json_addl["operation"].astext == "browser_session_binding",
        generic_instance.json_addl["actor"].astext == principal.user_sub,
        generic_instance.is_deleted.is_(False),
    ).order_by(generic_instance.created_dt.desc()).first()
    if row is None:
        raise RuntimeError("No native browser binding for retained handoff")
    binding_euid = row.euid
    native = normalize_instance_payload(row)

same_grant = native["principal"]["identity_grant_id"] == handoff["recipient_identity"]["grant_id"]
if not same_grant:
    raise RuntimeError("Latest native binding and retained handoff do not match")
# Runtime server instance IDs have the same fixed byte length as this new config.
# Use the persisted callback creation time to preserve its UTC timestamp width.
authenticated_at = datetime.fromisoformat(native["created_at"].replace("Z", "+00:00")).isoformat(timespec="microseconds")
principal = replace(principal, authenticated_at=authenticated_at,
    app_context={**principal.app_context, "dewey_session_binding_euid": binding_euid})
middleware = SessionMiddleware(lambda *args: None, secret_key=config.session_secret_key,
    session_cookie=config.session_cookie_name, max_age=config.session_max_age,
    same_site=config.same_site, https_only=config.https_only)

def measure(value):
    probe = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "session": {}, "app": app})
    store_session_principal(probe, config, value)
    raw = json.dumps(probe.session).encode("utf-8")
    signed = middleware.signer.sign(b64encode(raw)).decode("utf-8")
    name_value = config.session_cookie_name + "=" + signed
    header = name_value + "; path=/; Max-Age=" + str(config.session_max_age) + "; " + middleware.security_flags
    return len(raw), len(name_value.encode()), len(header.encode())

current = measure(principal)
minimal = replace(principal, app_context={**principal.app_context,
    "canonical_user": {"canonical_user_id": principal.user_sub}})
reduced = measure(minimal)
output = {
    "canonical_user_json_bytes": len(json.dumps(user).encode()),
    "recipient_identity_json_bytes": len(json.dumps(handoff["recipient_identity"]).encode()),
    "current_session_json_bytes": current[0], "current_cookie_name_value_bytes": current[1],
    "current_set_cookie_header_bytes": current[2], "current_exceeds_4096": current[1] > 4096,
    "minimal_session_json_bytes": reduced[0], "minimal_cookie_name_value_bytes": reduced[1],
    "minimal_set_cookie_header_bytes": reduced[2], "minimal_below_4096": reduced[2] < 4096,
    "current_canonical_contains_duplicate_identity": "recipient_identity" in principal.app_context.get("canonical_user", {}),
    "native_generation_matches": native["generation"] == settings.share_session_generation,
    "native_active": native["status"] == "active",
    "native_unexpired": datetime.fromisoformat(native["expires_at"]) > datetime.now(timezone.utc),
    "native_subject_matches": native["principal"]["subject"] == native["actor"] == principal.user_sub,
    "native_grant_matches_handoff": same_grant,
    "group_count": len(principal.cognito_groups), "role_count": len(principal.roles),
}
print(json.dumps(output, sort_keys=True))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--login-container", required=True)
    parser.add_argument("--dewey-container", required=True)
    args = parser.parse_args()
    first = subprocess.run(["docker", "exec", args.login_container, "/app/.venv/bin/python", "-c", LOGIN_READ],
                           capture_output=True, text=True, check=False)
    if first.returncode:
        raise RuntimeError("Read-only Login metadata stage failed; private output withheld")
    # Validate the private transport without echoing or persisting it.
    payload = json.loads(first.stdout)
    if not isinstance(payload, dict) or "user" not in payload or "recipient_identity" not in payload:
        raise RuntimeError("Retained handoff projection is incomplete")
    second = subprocess.run(["docker", "exec", "-i", args.dewey_container, "/app/.venv/bin/python", "-c", DEWEY_MEASURE],
                            input=first.stdout, capture_output=True, text=True, check=False)
    if second.returncode:
        raise RuntimeError("Read-only Dewey metadata stage failed; private output withheld")
    output = json.loads(second.stdout)
    if not isinstance(output, dict) or not output or not all(type(value) in (int, bool) for value in output.values()):
        raise RuntimeError("Metadata projection must contain only lengths/counts and booleans")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
