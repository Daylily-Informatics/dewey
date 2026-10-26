#!/usr/bin/env python3
"""Prepare exact private recipient configuration; never emit configuration secrets."""
import argparse
import base64
import copy
import hashlib
import json
import os
import secrets
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login-source", type=Path, required=True)
    parser.add_argument("--dewey-source", type=Path, required=True)
    parser.add_argument("--login-sha256", required=True)
    parser.add_argument("--dewey-sha256", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    assert all(p.is_absolute() for p in (args.login_source, args.dewey_source, args.output_directory))
    assert args.output_directory.is_dir()
    login_bytes, dewey_bytes = args.login_source.read_bytes(), args.dewey_source.read_bytes()
    assert hashlib.sha256(login_bytes).hexdigest() == args.login_sha256, "Login source changed"
    assert hashlib.sha256(dewey_bytes).hexdigest() == args.dewey_sha256, "Dewey source changed"
    login, dewey = yaml.safe_load(login_bytes), yaml.safe_load(dewey_bytes)
    assert login.get("recipient_access") is None, "Recipient configuration already exists"
    assert login["public_base_url"].rstrip("/") == "https://login.day.lsmc.bio"
    assert dewey["share"]["application_origin"] == "https://dewey.day.lsmc.bio"
    assertions = {
        "dewey_private_assertion": dewey["share"]["ingress_assertion"],
        **{name: secrets.token_urlsafe(48) for name in (
            "dewey_public_assertion", "login_public_assertion", "login_private_assertion")},
    }
    assert len(set(assertions.values())) == 4 and min(map(len, assertions.values())) >= 32
    candidate = copy.deepcopy(login)
    candidate["recipient_access"] = {
        "grant_encryption_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "public_ingress_assertion": assertions["login_public_assertion"],
        "private_ingress_assertion": assertions["login_private_assertion"],
        "trusted_proxy_peer": "127.0.0.1",
        "provider_grant_lifetime_seconds": 2592000,
        "positive_cache_seconds": 60,
        "browser_grant_lifetime_seconds": 28800,
    }
    candidate["email"] = {"backend": "ses", "region": "us-west-2", "sender": "sharing@lsmc.com"}
    assert all(candidate[key] == value for key, value in login.items() if key != "email")
    broker = "https://login.day.lsmc.bio"
    contract = {
        "public_ingress_assertion": assertions["dewey_public_assertion"],
        "auth": {"external_broker": {
            "share_login_url": broker + "/auth/share",
            "identity_url": broker + "/api/v1/dewey/identity/introspect",
            "identity_mint_url": broker + "/api/v1/dewey/identity/credentials",
            "identity_revoke_url": broker + "/api/v1/dewey/identity/revoke",
        }},
    }
    outputs = {
        "login-config.yaml": yaml.safe_dump(candidate, sort_keys=False),
        "origin-secrets.json": json.dumps(assertions),
        "recipient-contract.json": json.dumps(contract),
    }
    assert all(not (args.output_directory / name).exists() for name in outputs)
    assert args.login_source.read_bytes() == login_bytes and args.dewey_source.read_bytes() == dewey_bytes
    hashes = {}
    for name, content in outputs.items():
        with (args.output_directory / name).open("x") as handle:
            handle.write(content)
        hashes[name] = hashlib.sha256(content.encode()).hexdigest()
    receipt = {"login_source_sha256": args.login_sha256, "dewey_source_sha256": args.dewey_sha256,
               "output_sha256": hashes, "cognito_unchanged": True,
               "existing_login_fields_preserved_except_email": True,
               "dewey_private_assertion_preserved": True}
    (args.output_directory / "private-config-receipt.json").open("x").write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
