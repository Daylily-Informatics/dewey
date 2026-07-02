"""CloudFront signing helpers for Dewey share packages."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _cloudfront_safe_b64(payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return encoded.replace("+", "-").replace("=", "_").replace("/", "~")


def _normalize_domain(value: str) -> str:
    domain = str(value or "").strip().removeprefix("https://").removeprefix("http://")
    domain = domain.strip().strip("/")
    if not domain:
        raise ValueError("CloudFront distribution domain is required")
    if "/" in domain or "?" in domain or "#" in domain:
        raise ValueError("CloudFront distribution domain must be a bare host")
    return domain


def _normalize_key(value: str) -> str:
    key = str(value or "").strip().lstrip("/")
    if not key:
        raise ValueError("CloudFront object key is required")
    if ".." in {part for part in key.split("/") if part}:
        raise ValueError("CloudFront object key must not contain path traversal segments")
    return key


def _normalize_prefix(value: str) -> str:
    return _normalize_key(value).rstrip("/") + "/"


@dataclass(frozen=True)
class CloudFrontSignedPackage:
    """Short-lived package minted only after Dewey authorizes share access."""

    access_url: str | None
    cookies: dict[str, str]
    resource: str
    expires_at: str


class CloudFrontShareSigner:
    """Narrow CloudFront private-content signer.

    Dewey owns target validation, policy, and auth decisions. This signer only signs
    a concrete object URL or prefix wildcard after that decision has already passed.
    """

    def __init__(
        self,
        *,
        distribution_domain: str,
        key_pair_id: str,
        private_key_path: str,
        default_ttl_seconds: int = 900,
        cookie_ttl_seconds: int = 900,
    ) -> None:
        self.distribution_domain = _normalize_domain(distribution_domain)
        self.key_pair_id = str(key_pair_id or "").strip()
        if not self.key_pair_id:
            raise ValueError("CloudFront key_pair_id is required")
        private_key = Path(str(private_key_path or "").strip()).expanduser()
        if not private_key.is_absolute():
            raise ValueError("CloudFront private_key_path must be an absolute path")
        if not private_key.is_file():
            raise ValueError(f"CloudFront private key does not exist: {private_key}")
        self.private_key_path = str(private_key)
        self.default_ttl_seconds = max(60, int(default_ttl_seconds))
        self.cookie_ttl_seconds = max(60, int(cookie_ttl_seconds))

    def resource_url(self, key: str) -> str:
        safe_key = quote(_normalize_key(key), safe="/")
        return f"https://{self.distribution_domain}/{safe_key}"

    def resource_prefix(self, prefix: str) -> str:
        safe_prefix = quote(_normalize_prefix(prefix), safe="/")
        return f"https://{self.distribution_domain}/{safe_prefix}*"

    def sign_url(self, *, key: str, expires_in: int | None = None) -> CloudFrontSignedPackage:
        from botocore.signers import CloudFrontSigner

        expires_at = _now_utc() + timedelta(
            seconds=max(60, int(expires_in or self.default_ttl_seconds))
        )
        url = self.resource_url(key)
        signed = CloudFrontSigner(self.key_pair_id, self._rsa_sign).generate_presigned_url(
            url,
            date_less_than=expires_at,
        )
        return CloudFrontSignedPackage(
            access_url=str(signed),
            cookies={},
            resource=url,
            expires_at=expires_at.isoformat().replace("+00:00", "Z"),
        )

    def sign_prefix_cookies(
        self,
        *,
        prefix: str,
        expires_in: int | None = None,
    ) -> CloudFrontSignedPackage:
        from botocore.signers import CloudFrontSigner

        expires_at = _now_utc() + timedelta(
            seconds=max(60, int(expires_in or self.cookie_ttl_seconds))
        )
        resource = self.resource_prefix(prefix)
        signer = CloudFrontSigner(self.key_pair_id, self._rsa_sign)
        policy = signer.build_policy(resource, date_less_than=expires_at)
        signature = self._rsa_sign(policy.encode("utf-8"))
        return CloudFrontSignedPackage(
            access_url=None,
            cookies={
                "CloudFront-Policy": _cloudfront_safe_b64(policy.encode("utf-8")),
                "CloudFront-Signature": _cloudfront_safe_b64(signature),
                "CloudFront-Key-Pair-Id": self.key_pair_id,
            },
            resource=resource,
            expires_at=expires_at.isoformat().replace("+00:00", "Z"),
        )

    def _rsa_sign(self, message: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("cryptography is required for CloudFront signing") from exc

        private_key = serialization.load_pem_private_key(
            Path(self.private_key_path).read_bytes(),
            password=None,
        )
        # CloudFront canned/custom policy signatures require RSA-SHA1.
        return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())  # nosec B303


class NullCloudFrontShareSigner:
    """Deterministic test signer with no private key material."""

    def __init__(self, *, distribution_domain: str = "d111111abcdef8.cloudfront.net") -> None:
        self.distribution_domain = _normalize_domain(distribution_domain)

    def resource_url(self, key: str) -> str:
        safe_key = quote(_normalize_key(key), safe="/")
        return f"https://{self.distribution_domain}/{safe_key}"

    def resource_prefix(self, prefix: str) -> str:
        safe_prefix = quote(_normalize_prefix(prefix), safe="/")
        return f"https://{self.distribution_domain}/{safe_prefix}*"

    def sign_url(self, *, key: str, expires_in: int | None = None) -> CloudFrontSignedPackage:
        _ = expires_in
        url = self.resource_url(key)
        return CloudFrontSignedPackage(
            access_url=f"{url}?Signature=test&Key-Pair-Id=test-key",
            cookies={},
            resource=url,
            expires_at="2026-03-10T01:15:00Z",
        )

    def sign_prefix_cookies(
        self,
        *,
        prefix: str,
        expires_in: int | None = None,
    ) -> CloudFrontSignedPackage:
        _ = expires_in
        resource = self.resource_prefix(prefix)
        return CloudFrontSignedPackage(
            access_url=None,
            cookies={
                "CloudFront-Policy": "test-policy",
                "CloudFront-Signature": "test-signature",
                "CloudFront-Key-Pair-Id": "test-key",
            },
            resource=resource,
            expires_at="2026-03-10T01:15:00Z",
        )
