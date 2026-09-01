#!/usr/bin/env python3
"""Exercise Dewey share delivery without exposing signed credentials.

The caller supplies real, persisted Dewey EUIDs. Output contains EUIDs,
response statuses, sizes, and checksums, but never bearer tokens, signed URLs,
or CloudFront cookies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import httpx

ALL_MODES = [
    "presigned_s3",
    "presigned_s3_manifest",
    "cloudfront_signed_url",
    "cloudfront_signed_cookie",
    "dewey_html_browser",
]


class AcceptanceFailure(RuntimeError):
    """Raised after a production acceptance assertion fails."""


class DeweyAcceptance:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        owner_email: str,
        object_euid: str,
        artifact_set_euid: str,
        prefix_root_uri: str,
        prefix_probe_key: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.owner_email = owner_email.strip().lower()
        self.object_euid = object_euid.strip()
        self.artifact_set_euid = artifact_set_euid.strip()
        self.prefix_root_uri = prefix_root_uri.strip()
        self.prefix_probe_key = prefix_probe_key.strip().lstrip("/")
        self.api = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=90.0,
            follow_redirects=True,
        )
        self.download = httpx.Client(timeout=120.0, follow_redirects=True)
        self.created_shares: list[str] = []
        self.expected: dict[str, dict[str, Any]] = {}
        self.results: list[dict[str, Any]] = []

    def close(self) -> None:
        self.api.close()
        self.download.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        expected_status: int | set[int] = 200,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.api.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=body,
        )
        expected = {expected_status} if isinstance(expected_status, int) else expected_status
        if response.status_code not in expected:
            detail = response.text[:500]
            raise AcceptanceFailure(
                f"{method} {path} returned {response.status_code}, expected "
                f"{sorted(expected)}: {detail}"
            )
        if not response.content:
            return {}
        payload = response.json()
        if not isinstance(payload, dict):
            raise AcceptanceFailure(f"{method} {path} did not return a JSON object")
        return payload

    @staticmethod
    def _checksum(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _artifact_expected(artifact: dict[str, Any]) -> dict[str, Any]:
        checksums = dict(artifact.get("checksums") or {})
        return {
            "artifact_euid": str(artifact.get("artifact_euid") or ""),
            "key": str(artifact.get("key") or ""),
            "size": int(artifact.get("size") or 0),
            "sha256": str(checksums.get("sha256") or "").lower(),
        }

    def load_fixture_contract(self) -> dict[str, Any]:
        object_artifact = self.request(
            "GET", f"/api/v1/artifacts/{self.object_euid}"
        )
        artifact_set = self.request(
            "GET", f"/api/v1/artifact-sets/{self.artifact_set_euid}"
        )
        members = [
            dict(item)
            for item in list(artifact_set.get("members") or [])
            if isinstance(item, dict)
        ]
        if not members:
            raise AcceptanceFailure("artifact-set fixture has no members")
        for artifact in [object_artifact, *members]:
            expected = self._artifact_expected(artifact)
            if not expected["artifact_euid"] or not expected["key"]:
                raise AcceptanceFailure("fixture artifact is missing EUID or S3 key")
            if not expected["sha256"]:
                raise AcceptanceFailure(
                    f"fixture {expected['artifact_euid']} has no SHA-256 checksum"
                )
            self.expected[expected["artifact_euid"]] = expected
        object_expected = self.expected.get(self.object_euid)
        if object_expected is None:
            raise AcceptanceFailure("object fixture was not loaded")
        if self.prefix_probe_key != object_expected["key"]:
            raise AcceptanceFailure("prefix probe key must be the object fixture key")
        return {
            "object_euid": self.object_euid,
            "artifact_set_euid": self.artifact_set_euid,
            "artifact_set_members": sorted(self.expected),
            "prefix_root_uri": self.prefix_root_uri,
            "prefix_probe_key": self.prefix_probe_key,
        }

    def ensure_prefix_fixture(self) -> str:
        existing = self.request(
            "GET",
            "/api/v1/artifacts?artifact_type=dewey_share_acceptance_prefix&limit=2000",
        )
        expected_uri = self.prefix_root_uri.rstrip("/") + "/"
        for item in list(existing.get("items") or []):
            if not isinstance(item, dict):
                continue
            storage_uri = str(
                item.get("storage_uri") or item.get("source_uri") or ""
            ).rstrip("/") + "/"
            if storage_uri == expected_uri:
                prefix_euid = str(item.get("artifact_euid") or "").strip()
                if prefix_euid:
                    return prefix_euid
        payload = self.request(
            "POST",
            "/api/v1/artifact-prefixes",
            headers={"Idempotency-Key": "dewey-prod-share-acceptance-prefix-v1"},
            body={
                "root_uri": self.prefix_root_uri,
                "artifact_type": "dewey_share_acceptance_prefix",
                "producer_system": "dewey-prod-share-acceptance",
                "producer_object_euid": None,
                "metadata": {
                    "test_fixture": True,
                    "purpose": "production share delivery acceptance",
                },
            },
        )
        prefix_euid = str(payload.get("artifact_euid") or "").strip()
        if not prefix_euid:
            raise AcceptanceFailure("prefix registration did not return artifact_euid")
        return prefix_euid

    def create_share(
        self,
        *,
        run_id: str,
        target_kind: str,
        target_euid: str | None,
        targets: list[dict[str, str]],
        modes: list[str],
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        suffix = f"{target_kind}-{len(self.created_shares) + 1}"
        share = self.request(
            "POST",
            "/api/v1/shares",
            headers={"Idempotency-Key": f"{run_id}-{suffix}"},
            body={
                "target_kind": target_kind,
                "target_euid": target_euid,
                "targets": targets,
                "name": f"Dewey production delivery acceptance {run_id}",
                "purpose": "automated production delivery-mode acceptance",
                "owner_email": self.owner_email,
                "allowed_users": [self.owner_email],
                "allowed_domains": [],
                "allowed_groups": [],
                "delivery_modes": modes,
                "expires_at": expires_at,
                "ttl_seconds": 600,
            },
        )
        share_euid = str(share.get("share_euid") or "").strip()
        if not share_euid:
            raise AcceptanceFailure("share create did not return share_euid")
        self.created_shares.append(share_euid)
        return share

    def package(
        self,
        *,
        share_euid: str,
        mode: str,
        actor_email: str,
        expected_status: int | set[int] = 200,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/v1/shares/{share_euid}/access-package",
            expected_status=expected_status,
            body={
                "delivery_mode": mode,
                "actor_email": actor_email,
                "actor_groups": [],
                "signed_ttl_seconds": 300,
            },
        )

    def _verify_download(
        self,
        *,
        url: str,
        cookies: dict[str, str] | None,
        expected: dict[str, Any],
    ) -> dict[str, Any]:
        response = self.download.get(url, cookies=cookies)
        payload = response.content
        digest = self._checksum(payload)
        expected_size = int(expected["size"])
        expected_sha = str(expected["sha256"])
        if response.status_code != 200:
            raise AcceptanceFailure(
                f"download for {expected['artifact_euid']} returned {response.status_code}"
            )
        if len(payload) != expected_size or digest != expected_sha:
            raise AcceptanceFailure(
                f"download integrity mismatch for {expected['artifact_euid']}: "
                f"size={len(payload)}/{expected_size} sha256={digest}/{expected_sha}"
            )
        return {
            "artifact_euid": expected["artifact_euid"],
            "status": response.status_code,
            "bytes": len(payload),
            "sha256": digest,
            "host": urlparse(str(response.url)).hostname,
        }

    def exercise_package(
        self,
        *,
        share_euid: str,
        mode: str,
        prefix_probe: bool = False,
    ) -> dict[str, Any]:
        package = self.package(
            share_euid=share_euid,
            mode=mode,
            actor_email=self.owner_email,
        )
        manifest = [
            dict(item)
            for item in list(package.get("manifest") or [])
            if isinstance(item, dict)
        ]
        downloads: list[dict[str, Any]] = []
        if mode in {"presigned_s3", "presigned_s3_manifest", "cloudfront_signed_url"}:
            if prefix_probe:
                if not manifest or manifest[0].get("status") != "prefix_not_presigned":
                    raise AcceptanceFailure("prefix manifest did not report prefix_not_presigned")
            else:
                for member in manifest:
                    artifact_euid = str(member.get("artifact_euid") or "")
                    signed_url = str(member.get("signed_url") or "")
                    if artifact_euid not in self.expected or not signed_url:
                        raise AcceptanceFailure(
                            f"{mode} package has an incomplete object member"
                        )
                    downloads.append(
                        self._verify_download(
                            url=signed_url,
                            cookies=None,
                            expected=self.expected[artifact_euid],
                        )
                    )
        else:
            if not manifest:
                raise AcceptanceFailure(f"{mode} package has no manifest")
            for member in manifest:
                artifact_euid = str(member.get("artifact_euid") or "")
                expected = self.expected.get(artifact_euid)
                key = str(member.get("key") or "")
                if prefix_probe:
                    expected = self.expected[self.object_euid]
                    key = self.prefix_probe_key
                if expected is None:
                    raise AcceptanceFailure(f"unknown package artifact {artifact_euid}")
                resource = str(member.get("resource") or "")
                hostname = urlparse(resource).hostname
                cookies = dict(member.get("cookies") or {})
                if not hostname or set(cookies) != {
                    "CloudFront-Policy",
                    "CloudFront-Signature",
                    "CloudFront-Key-Pair-Id",
                }:
                    raise AcceptanceFailure(f"{mode} package is missing signed cookies")
                url = f"https://{hostname}/{quote(key, safe='/')}"
                downloads.append(
                    self._verify_download(url=url, cookies=cookies, expected=expected)
                )
                if prefix_probe:
                    break
        result = {
            "share_euid": share_euid,
            "mode": mode,
            "manifest_count": len(manifest),
            "downloads": downloads,
        }
        self.results.append(result)
        return result

    def revoke_and_verify(self, share_euid: str) -> dict[str, Any]:
        revoked = self.request(
            "POST",
            f"/api/v1/shares/{share_euid}/revoke",
            body={"reason": "production acceptance complete"},
        )
        self.package(
            share_euid=share_euid,
            mode="presigned_s3_manifest",
            actor_email=self.owner_email,
            expected_status=409,
        )
        return {
            "share_euid": share_euid,
            "status": revoked.get("status"),
            "post_revoke_status": 409,
        }

    def cleanup(self) -> list[dict[str, Any]]:
        receipts: list[dict[str, Any]] = []
        for share_euid in list(self.created_shares):
            try:
                current = self.request("GET", f"/api/v1/shares/{share_euid}")
                if str(current.get("status") or "").lower() == "active":
                    receipts.append(self.revoke_and_verify(share_euid))
            except Exception as exc:  # preserve the original acceptance failure
                receipts.append(
                    {
                        "share_euid": share_euid,
                        "status": "cleanup_failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        return receipts

    def load_and_assert_audits(
        self,
        *,
        object_share_euid: str,
        expiry_share_euid: str,
    ) -> dict[str, dict[str, Any]]:
        audits: dict[str, dict[str, Any]] = {}
        for share_euid in self.created_shares:
            audit = self.request("GET", f"/api/v1/shares/{share_euid}/audit")
            items = list(audit.get("items") or [])
            audits[share_euid] = {
                "event_count": len(items),
                "decisions": [str(item.get("decision") or "") for item in items],
                "denial_reasons": [
                    str(item.get("denial_reason") or "")
                    for item in items
                    if str(item.get("decision") or "") == "deny"
                ],
            }

        object_audit = audits[object_share_euid]
        object_decisions = object_audit["decisions"]
        object_reasons = object_audit["denial_reasons"]
        if "policy_denied" not in object_reasons:
            raise AcceptanceFailure("object-share policy denial audit was not persisted")
        if "revoke" not in object_decisions:
            raise AcceptanceFailure("object-share revoke audit was not persisted")
        if "inactive_or_revoked" not in object_reasons:
            raise AcceptanceFailure("post-revoke denial audit was not persisted")

        expiry_audit = audits[expiry_share_euid]
        if "expired" not in expiry_audit["denial_reasons"]:
            raise AcceptanceFailure("expired-share denial audit was not persisted")
        return audits

    def run(self) -> dict[str, Any]:
        run_id = datetime.now(timezone.utc).strftime("dewey-prod-share-%Y%m%dT%H%M%SZ")
        fixture = self.load_fixture_contract()
        prefix_euid = self.ensure_prefix_fixture()
        fixture["prefix_euid"] = prefix_euid

        object_share = self.create_share(
            run_id=run_id,
            target_kind="artifact_object",
            target_euid=self.object_euid,
            targets=[],
            modes=ALL_MODES,
        )
        set_share = self.create_share(
            run_id=run_id,
            target_kind="artifact_set",
            target_euid=self.artifact_set_euid,
            targets=[],
            modes=ALL_MODES,
        )
        prefix_share = self.create_share(
            run_id=run_id,
            target_kind="artifact_prefix",
            target_euid=prefix_euid,
            targets=[],
            modes=[
                "presigned_s3_manifest",
                "cloudfront_signed_cookie",
                "dewey_html_browser",
            ],
        )
        mixed_share = self.create_share(
            run_id=run_id,
            target_kind="mixed_set",
            target_euid=None,
            targets=[
                {"target_kind": "artifact_object", "target_euid": self.object_euid},
                {
                    "target_kind": "artifact_set",
                    "target_euid": self.artifact_set_euid,
                },
            ],
            modes=ALL_MODES,
        )

        self.package(
            share_euid=str(object_share["share_euid"]),
            mode="presigned_s3",
            actor_email="dewey-acceptance-outsider@example.invalid",
            expected_status=403,
        )
        for mode in ALL_MODES:
            self.exercise_package(
                share_euid=str(object_share["share_euid"]), mode=mode
            )
        for mode in ALL_MODES:
            self.exercise_package(share_euid=str(set_share["share_euid"]), mode=mode)
        for mode in [
            "presigned_s3_manifest",
            "cloudfront_signed_cookie",
            "dewey_html_browser",
        ]:
            self.exercise_package(
                share_euid=str(prefix_share["share_euid"]),
                mode=mode,
                prefix_probe=True,
            )
        for mode in ALL_MODES:
            self.exercise_package(
                share_euid=str(mixed_share["share_euid"]), mode=mode
            )

        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=5)
        ).isoformat().replace("+00:00", "Z")
        expiry_share = self.create_share(
            run_id=run_id,
            target_kind="artifact_object",
            target_euid=self.object_euid,
            targets=[],
            modes=["presigned_s3"],
            expires_at=expires_at,
        )
        self.exercise_package(
            share_euid=str(expiry_share["share_euid"]), mode="presigned_s3"
        )
        time.sleep(6)
        self.package(
            share_euid=str(expiry_share["share_euid"]),
            mode="presigned_s3",
            actor_email=self.owner_email,
            expected_status=409,
        )

        cleanup = self.cleanup()
        audits = self.load_and_assert_audits(
            object_share_euid=str(object_share["share_euid"]),
            expiry_share_euid=str(expiry_share["share_euid"]),
        )
        return {
            "status": "passed",
            "run_id": run_id,
            "fixture": fixture,
            "mode_results": self.results,
            "policy_denial_status": 403,
            "expiry_denial_status": 409,
            "audits": audits,
            "cleanup": cleanup,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("DEWEY_BASE_URL", ""))
    parser.add_argument("--token-env", default="DEWEY_API_TOKEN")
    parser.add_argument("--owner-email", required=True)
    parser.add_argument("--object-euid", required=True)
    parser.add_argument("--artifact-set-euid", required=True)
    parser.add_argument("--prefix-root-uri", required=True)
    parser.add_argument("--prefix-probe-key", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = str(os.environ.get(args.token_env) or "").strip()
    if not str(args.base_url or "").strip():
        raise SystemExit("--base-url or DEWEY_BASE_URL is required")
    if not token:
        raise SystemExit(f"{args.token_env} is required")
    acceptance = DeweyAcceptance(
        base_url=args.base_url,
        token=token,
        owner_email=args.owner_email,
        object_euid=args.object_euid,
        artifact_set_euid=args.artifact_set_euid,
        prefix_root_uri=args.prefix_root_uri,
        prefix_probe_key=args.prefix_probe_key,
    )
    try:
        payload = acceptance.run()
    except Exception as exc:
        payload = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "cleanup": acceptance.cleanup(),
        }
    finally:
        acceptance.close()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if payload.get("status") == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
