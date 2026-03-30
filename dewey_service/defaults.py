"""Canonical Dewey runtime defaults."""

from __future__ import annotations

import os
import re

DEFAULT_APP_PORT = 8914
DEFAULT_AUTH_PORT = DEFAULT_APP_PORT
DEFAULT_DB_PORT = 5432


def default_cognito_redirect_uri() -> str:
    return f"https://localhost:{DEFAULT_AUTH_PORT}/auth/callback"


def default_cognito_logout_url() -> str:
    return f"https://localhost:{DEFAULT_AUTH_PORT}/login"


def build_default_config_template() -> bytes:
    deployment = _sanitize_deployment_code(
        os.environ.get("DEWEY_DEPLOYMENT_CODE")
        or os.environ.get("DEPLOYMENT_CODE")
        or os.environ.get("LSMC_DEPLOYMENT_CODE")
        or "local"
    )
    return f"""# Dewey Configuration
# ===================
# Create this file with:
#   dewey config init
#
# Stored by default at ~/.config/dewey-{deployment}/dewey-config-{deployment}.yaml unless XDG_CONFIG_HOME is set.

application:
  environment: development
  api_bearer_token: dewey-dev-token
  session_secret_key: dewey-session-secret-change-me
  host: 127.0.0.1
  port: {DEFAULT_APP_PORT}
  verify_ssl: true

auth:
  cognito:
    domain: https://dewey-auth.example.com
    app_client_id: dewey-client-id
    app_client_secret: ""
    redirect_uri: {default_cognito_redirect_uri()}
    logout_url: {default_cognito_logout_url()}
    user_pool_id: us-west-2_example
    region: us-west-2
    group_role_map:
      platform-admin: ADMIN
      dewey-admin: ADMIN
      dewey-readwrite: READ_WRITE
      dewey-readonly: READ_ONLY

database:
  backend: tapdb
  target: local
  client_id: dewey
  namespace: dewey
  env: dev
  config_path: ""

aws:
  profile: lsmc
  region: us-west-2

deployment:
  name: dev
  color: "#0f766e"
  is_production: false
""".encode("utf-8")


def _sanitize_deployment_code(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip("-")
    return cleaned or "local"
