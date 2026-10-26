#!/usr/bin/env python3
"""Explicit loopback-only Dewey 9 read/write/replay acceptance; never dispatch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

HOST = "dewey.day.lsmc.bio"
FIXTURE_MANIFEST_SHA = "4ed7e3e6938edb309a277042a42125d2ac58e99579809973e369054e1a67f4e9"
DIRECTORIES = {
    "rehearsal": "/opt/dewey/day/releases/tapdb10-rehearsal-20260911",
    "production": "/opt/dewey/day/releases/9.0.0",
}


class AcceptanceError(RuntimeError):
    """Credential-free failure that leaves the partial receipt intact."""


def require(condition, message):
    if not condition:
        raise AcceptanceError(message)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def absolute_file(value, *, private=False):
    path = Path(value)
    require(path.is_absolute() and path.is_file() and path.resolve() == path, "Exact file required")
    if private:
        require(path.stat().st_mode & 0o077 == 0, "Private file permissions required")
    return path


def validate_base_url(base_url):
    parsed = urlsplit(base_url)
    require(
        parsed.scheme == "http"
        and parsed.hostname == "127.0.0.1"
        and parsed.port is not None
        and not parsed.username
        and not parsed.password
        and not parsed.path
        and not parsed.query
        and not parsed.fragment,
        "Base URL must be explicit http://127.0.0.1:PORT with no extra URL components",
    )
    require(base_url == f"http://127.0.0.1:{parsed.port}", "Canonical loopback URL required")


def verify_effective_primary(settings):
    primary = os.environ.get("DEWEY_API_BEARER_TOKEN")
    require(isinstance(primary, str) and primary.strip(), "Explicit deployed primary required")
    require(
        settings.api_bearer_token == primary.strip(),
        "Effective primary differs from selected deployed environment credential",
    )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Capsule:
    def __init__(self, args, settings, inputs, fixture):
        self.args = args
        self.settings = settings
        self.inputs = inputs
        self.fixture = fixture
        self.token = str(settings.api_bearer_token or "").strip()
        require(self.token in settings.api_tokens(), "Primary configured API bearer is invalid")
        self.resolver = absolute_file(args.resolver_token_file, private=True).read_text().strip()
        require(
            hashlib.sha256(self.resolver.encode()).hexdigest()
            == settings.qeo_resolver_token_sha256,
            "Resolver token does not match this runtime configuration",
        )
        expires = datetime.fromisoformat(settings.qeo_resolver_token_expires_at)
        require(expires > datetime.now(UTC), "Configured resolver credential expired")
        self.opener = build_opener(ProxyHandler({}), NoRedirect())
        self.receipt = {"phase": args.phase, "status": "started", "inputs": inputs, "checks": []}
        path = Path(args.receipt)
        require(path.is_absolute() and path.parent.is_dir(), "Absolute receipt parent required")
        require(path.parent.resolve() == path.parent, "Canonical receipt directory required")
        require(path.parent.stat().st_mode & 0o077 == 0, "Receipt directory must be private")
        self.handle = os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600), "w+")
        self.persist()

    def persist(self):
        self.receipt["updated_at"] = datetime.now(UTC).isoformat()
        self.receipt["sha256"] = digest({k: v for k, v in self.receipt.items() if k != "sha256"})
        self.handle.seek(0)
        json.dump(self.receipt, self.handle, indent=2, sort_keys=True)
        self.handle.write("\n")
        self.handle.truncate()
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def request(self, method, path, *, body=None, auth="general", key=None, expected=200):
        headers = {"Host": HOST, "Accept": "application/json"}
        if auth != "none":
            headers["Authorization"] = "Bearer " + (
                self.resolver if auth == "resolver" else self.token
            )
        if key:
            headers["Idempotency-Key"] = key
        data = None if body is None else json.dumps(body).encode()
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.args.base_url + path, data=data, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=30)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read(16 * 1024 * 1024 + 1)
            status = response.code
        check = {
            "method": method,
            "path": path,
            "http_status": status,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
        payload = None
        if len(raw) <= 16 * 1024 * 1024:
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError):
                payload = None
        if method == "POST" and isinstance(payload, dict):
            # Keep returned identifiers even on an unexpected response status.
            check["returned_identifiers"] = {
                key: payload[key]
                for key in ("artifact_set_euid", "artifact_euid", "lineage_euid")
                if isinstance(payload.get(key), str) and payload[key]
            }
        self.receipt["checks"].append(check)
        self.persist()
        require(len(raw) <= 16 * 1024 * 1024, "Response exceeded capsule bound")
        require(status == expected, "Unexpected HTTP status; inspect sanitized check receipt")
        require(isinstance(payload, dict), "Expected JSON object")
        return payload

    def accepted_prior(self, path, phase):
        receipt = json.loads(absolute_file(path, private=True).read_text())
        require(
            receipt["sha256"] == digest({k: v for k, v in receipt.items() if k != "sha256"}),
            "Prior receipt digest mismatch",
        )
        require(
            receipt["phase"] == phase and receipt["status"] == "passed", "Prior stage incomplete"
        )
        require(receipt["inputs"] == self.inputs, "Prior stage input/image/config changed")
        return receipt

    def reads(self):
        artifact = self.fixture["report_artifact_euid"]
        package = self.fixture["artifact_set_euid"]
        for path in ("/healthz", "/readyz"):
            payload = self.request("GET", path)
            require(
                payload["build"] == {"version": "9.0.0", "sha": self.args.image_sha},
                "Wrong running version/revision",
            )
            if path == "/readyz":
                require(payload["ready"] is True, "Runtime not ready")
        payload = self.request("GET", f"/api/v1/artifacts/{artifact}")
        require(payload["artifact_euid"] == artifact, "Artifact identity changed")
        payload = self.request("GET", f"/api/v1/artifact-sets/{package}")
        require(
            payload["artifact_set_euid"] == package and payload["member_count"] == 20,
            "Historical package changed",
        )
        for body in (
            {"kind": "artifact", "euid": artifact},
            {"kind": "artifact_set", "euid": package},
        ):
            payload = self.request("POST", "/api/v1/resolve/multiqc", body=body, auth="resolver")
            require(
                payload["artifact_set_euid"] == package
                and len(payload["files"]) == 20
                and payload["complete_data_package"] is True,
                "Resolver package changed",
            )
        self.request(
            "POST",
            "/api/v1/resolve/artifact",
            body={"artifact_euid": artifact},
            auth="resolver",
            expected=401,
        )
        self.request("GET", "/api/dag/manifest", auth="none", expected=401)
        manifest = self.request("GET", "/api/dag/manifest")
        require(
            manifest["contract"] == "dag:v2" and manifest["service_id"] == "dewey",
            "Unexpected DAG contract",
        )
        require(manifest["features"]["outbound_fetch"] is False, "Unexpected outbound DAG feature")
        detail = self.request("GET", f"/api/dag/v2/object/{artifact}")
        require(
            detail["euid"] == artifact and detail["service_id"] == "dewey", "DAG object mismatch"
        )
        graph = self.request("GET", f"/api/dag/v2/data?start_euid={package}&depth=1&max_nodes=100")
        node_ids = {node["data"]["euid"] for node in graph["elements"]["nodes"]}
        require(
            {artifact, package} <= node_ids and graph["meta"]["contract"] == "dag:v2",
            "Historical typed package graph missing",
        )
        search = self.request("GET", f"/api/dag/v2/search?euid={artifact}&limit=1")
        require(
            [item["euid"] for item in search["items"]] == [artifact], "DAG exact search mismatch"
        )
        self.receipt["historical_fixture"] = {
            "artifact_set_euid": package,
            "report_artifact_euid": artifact,
            "members": 20,
        }

    def body_and_keys(self):
        prefix = f"dewey-9.0.0-{self.args.lane}-20260911-acceptance"
        body = {
            "artifact_set_type": "migration_acceptance",
            "label": f"Dewey 9.0.0 {self.args.lane} acceptance",
            "description": "Retained controlled DB-only migration acceptance record.",
            "metadata": {"acceptance_release": "9.0.0", "acceptance_lane": self.args.lane},
        }
        return body, prefix + "-set", prefix + "-member"

    def writes(self):
        self.accepted_prior(self.args.prior_receipt, "read")
        body, set_key, member_key = self.body_and_keys()
        created = self.request("POST", "/api/v1/artifact-sets", body=body, key=set_key)
        euid = created["artifact_set_euid"]
        require(isinstance(euid, str) and bool(euid), "Missing returned artifact-set EUID")
        # Persist the actual returned identifier before any further mutation.
        self.receipt.update(returned_artifact_set_euid=euid, create_response_sha256=digest(created))
        self.persist()
        require(created["status_code"] == 201, "Creation receipt is not successful")
        member_path = f"/api/v1/artifact-sets/{quote(euid, safe='')}/members"
        member = self.request(
            "POST",
            member_path,
            key=member_key,
            body={"artifact_euid": self.fixture["report_artifact_euid"]},
        )
        self.receipt["membership_response_sha256"] = digest(member)
        self.persist()
        payload = self.request("GET", f"/api/v1/artifact-sets/{quote(euid, safe='')}")
        require(
            payload["artifact_set_euid"] == euid
            and payload["member_count"] == 1
            and payload["artifact_euids"] == [self.fixture["report_artifact_euid"]],
            "Persisted acceptance membership mismatch",
        )
        self.receipt["persisted_artifact_set_euid"] = euid

    def replay(self):
        prior = self.accepted_prior(self.args.prior_receipt, "write")
        euid = prior["persisted_artifact_set_euid"]
        body, set_key, member_key = self.body_and_keys()
        created = self.request("POST", "/api/v1/artifact-sets", body=body, key=set_key)
        self.receipt["returned_artifact_set_euid"] = created.get("artifact_set_euid")
        self.persist()
        require(
            created["artifact_set_euid"] == euid
            and digest(created) == prior["create_response_sha256"],
            "Create replay changed receipt",
        )
        member = self.request(
            "POST",
            f"/api/v1/artifact-sets/{quote(euid, safe='')}/members",
            key=member_key,
            body={"artifact_euid": self.fixture["report_artifact_euid"]},
        )
        require(
            digest(member) == prior["membership_response_sha256"],
            "Membership replay changed receipt",
        )
        self.request(
            "POST",
            "/api/v1/artifact-sets",
            body={**body, "label": body["label"] + " changed"},
            key=set_key,
            expected=409,
        )
        self.receipt["persisted_artifact_set_euid"] = euid

    def run(self):
        try:
            {"read": self.reads, "write": self.writes, "replay": self.replay}[self.args.phase]()
            self.receipt["status"] = "passed"
        except Exception as exc:
            self.receipt["status"] = "failed"
            self.receipt["error_class"] = type(exc).__name__
            if isinstance(exc, AcceptanceError):
                self.receipt["reason"] = str(exc)
            raise
        finally:
            self.persist()
            self.handle.close()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("read", "write", "replay"))
    parser.add_argument("--lane", choices=tuple(DIRECTORIES), required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--dewey-config", required=True)
    parser.add_argument("--resolver-token-file", required=True)
    parser.add_argument("--fixture-inputs", required=True)
    parser.add_argument("--fixture-manifest", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--image-sha", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--prior-receipt")
    args = parser.parse_args()
    try:
        validate_base_url(args.base_url)
        require(
            re.fullmatch(r"sha256:[0-9a-f]{64}", args.image_digest), "Exact image digest required"
        )
        require(re.fullmatch(r"[0-9a-f]{40}", args.image_sha), "Exact source revision required")
        config = absolute_file(args.dewey_config, private=True)
        require(str(config) == DIRECTORIES[args.lane] + "/dewey-config.yaml", "Wrong lane config")
        require(os.environ.get("DEWEY_CONFIG") == str(config), "Dewey config environment mismatch")
        runtime = absolute_file(os.environ["TAPDB_CONFIG_PATH"], private=True)
        require(
            str(runtime) == DIRECTORIES[args.lane] + "/tapdb-runtime.yaml", "Wrong runtime config"
        )
        require(args.phase == "read" or args.prior_receipt, "Prior passed receipt required")
        for package, version in (
            ("dewey-service", "9.0.0"),
            ("daylily-tapdb", "10.1.1rc1"),
            ("meridian-euid", "0.4.8"),
        ):
            require(
                importlib.metadata.version(package) == version, "Unexpected image package version"
            )
        fixture_path = absolute_file(args.fixture_inputs)
        fixture = json.loads(fixture_path.read_text())["existing_fixtures"]
        manifest = absolute_file(args.fixture_manifest)
        require(
            file_digest(manifest) == fixture["manifest_sha256"] == FIXTURE_MANIFEST_SHA,
            "Historical package manifest changed",
        )
        from daylily_tapdb.cli.db_config import get_db_config
        from dewey_runtime_principal_prepare import validate_runtime

        from dewey_service.settings import get_settings

        runtime_cfg = get_db_config(
            config_path=runtime, client_id="dewey", database_name="dewey-day"
        )
        validate_runtime(runtime_cfg, args.lane, runtime)
        settings = get_settings()
        verify_effective_primary(settings)
        inputs = {
            "lane": args.lane,
            "base_url": args.base_url,
            "host": HOST,
            "image_digest": args.image_digest,
            "image_sha": args.image_sha,
            "dewey_config_sha256": file_digest(config),
            "runtime_config_sha256": file_digest(runtime),
            "fixture_inputs_sha256": file_digest(fixture_path),
            "manifest_sha256": file_digest(manifest),
            "general_bearer_selector": "DEWEY_API_BEARER_TOKEN (effective primary)",
            "capsule_sha256": file_digest(Path(__file__).resolve()),
            "runtime_target": {
                key: runtime_cfg[key] for key in ("database", "schema_name", "user", "domain_code")
            },
        }
        Capsule(args, settings, inputs, fixture).run()
        print(json.dumps({"status": "passed", "phase": args.phase, "receipt": args.receipt}))
        return 0
    except Exception as exc:
        payload = {"status": "failed", "phase": args.phase, "error_class": type(exc).__name__}
        if isinstance(exc, AcceptanceError):
            payload["reason"] = str(exc)
        print(json.dumps(payload))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
