from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest


def _login_user(
    monkeypatch,
    client,
    *,
    email: str = "operator@lsmc.com",
    groups: list[str] | None = None,
) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": email,
            "sub": "sub-1",
            "name": "Operator Example",
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )
    login = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    callback = client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302


def _register_object(service, *, bucket: str = "bucket-cf", key: str = "reports/a.txt"):
    service._require_storage().seed_object(bucket=bucket, key=key, size=11)
    _, artifact = service.register_artifact(
        artifact_type="txt",
        storage_backend="s3",
        bucket=bucket,
        key=key,
        version_id=None,
        size=11,
        checksums=None,
        content_type="text/plain",
        original_filename=key.rsplit("/", 1)[-1],
        producer_system=None,
        producer_object_euid=None,
        storage_class=None,
        availability_status=None,
        metadata=None,
        idempotency_key=f"idem-artifact-{key}",
    )
    return artifact


def test_cloudfront_authenticated_share_authorizes_exact_domain(service) -> None:
    artifact = _register_object(service)

    _, share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="external-review",
        scope="cloudfront",
        expires_at=None,
        issued_by="creator@lsmc.com",
        transport="cloudfront",
        transport_config={},
        ttl_seconds=900,
        idempotency_key="idem-cf-auth",
        visibility="authenticated",
        permissions=["view_metadata", "download"],
        recipient_domains=["example.com"],
        mode="snapshot",
    )

    opened = service.open_share_reference(
        share["share_reference_euid"],
        viewer_email="recipient@example.com",
    )
    assert opened["presigned_access_url"].startswith(
        "https://d111111abcdef8.cloudfront.net/reports/a.txt"
    )
    assert opened["access_count"] == 1

    with pytest.raises(ValueError, match="wrong_email_or_domain"):
        service.open_share_reference(
            share["share_reference_euid"],
            viewer_email="recipient@example.org",
        )
    denied = service.get_share_reference(share["share_reference_euid"])
    assert denied["last_denial_reason"] == "wrong_email_or_domain"


def test_cloudfront_public_share_requires_lsmc_share_writer(service) -> None:
    artifact = _register_object(service, key="reports/public.txt")

    with pytest.raises(ValueError, match="lsmc.com"):
        service.create_share_reference(
            target_type="artifact",
            target_euid=artifact["artifact_euid"],
            purpose="public-review",
            scope="cloudfront",
            expires_at=None,
            issued_by="creator@lsmc.life",
            transport="cloudfront",
            transport_config={},
            ttl_seconds=900,
            idempotency_key="idem-cf-public-bad-domain",
            visibility="public",
            permissions=["download"],
            mode="snapshot",
            creator_profile={"email": "creator@lsmc.life", "groups": ["lsmc:dewey:share-writer"]},
        )

    _, share = service.create_share_reference(
        target_type="artifact",
        target_euid=artifact["artifact_euid"],
        purpose="public-review",
        scope="cloudfront",
        expires_at=None,
        issued_by="creator@lsmc.com",
        transport="cloudfront",
        transport_config={},
        ttl_seconds=900,
        idempotency_key="idem-cf-public-ok",
        visibility="public",
        permissions=["download"],
        mode="snapshot",
        creator_profile={"email": "creator@lsmc.com", "groups": ["lsmc:dewey:share-writer"]},
    )

    assert share["access_url"].startswith("/public-shares/")
    assert share["public_share_id"]
    opened = service.open_share_reference(share["share_reference_euid"])
    assert "Signature=test" in opened["presigned_access_url"]


def test_cloudfront_prefix_share_blocks_nonrecursive_descendant(service) -> None:
    service._require_storage().seed_object(bucket="bucket-cf", key="runs/run1/direct.txt", size=1)
    service._require_storage().seed_object(
        bucket="bucket-cf", key="runs/run1/nested/child.txt", size=1
    )
    _, imported = service.import_run_prefix(
        root_uri="s3://bucket-cf/runs/run1/",
        platform="ultima",
        owner_email="owner@lsmc.com",
        run_id="RUN123",
        finalize=False,
        idempotency_key="idem-cf-prefix-import",
    )
    root = imported["run_artifact"]

    _, share = service.create_share_reference(
        target_type="artifact",
        target_euid=root["artifact_euid"],
        purpose="prefix-review",
        scope="cloudfront",
        expires_at=None,
        issued_by="creator@lsmc.com",
        transport="cloudfront",
        transport_config={},
        ttl_seconds=900,
        idempotency_key="idem-cf-prefix-share",
        visibility="authenticated",
        permissions=["list", "download"],
        recipient_domains=["example.com"],
        mode="snapshot",
        recursive=False,
    )

    opened = service.open_share_reference(
        share["share_reference_euid"],
        viewer_email="reader@example.com",
        requested_key="runs/run1/direct.txt",
    )
    assert "direct.txt" in opened["presigned_access_url"]
    with pytest.raises(ValueError, match="object_outside_snapshot"):
        service.open_share_reference(
            share["share_reference_euid"],
            viewer_email="reader@example.com",
            requested_key="runs/run1/nested/child.txt",
        )


def test_cloudfront_routes_and_admin_report(monkeypatch, client, fake_service) -> None:
    _login_user(
        monkeypatch,
        client,
        email="operator@lsmc.com",
        groups=["dewey-admin", "lsmc:dewey:share-writer"],
    )
    artifact = client.post(
        "/api/v1/artifacts",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "idem-cf-route-art"},
        json={
            "artifact_type": "txt",
            "storage_backend": "s3",
            "bucket": "bucket-cf",
            "key": "routes/a.txt",
        },
    ).json()

    created = client.post(
        "/shares/cloudfront",
        data={
            "target_type": "artifact",
            "target_euid": artifact["artifact_euid"],
            "visibility": "public",
            "mode": "snapshot",
            "permissions": "view_metadata,download",
            "share_duration_days": "1",
        },
    )
    assert created.status_code == 200
    assert "Share Created" in created.text
    share = next(iter(fake_service.share_references.values()))
    share_euid = share["share_reference_euid"]
    public_id = share["public_share_id"]

    new_page = client.get("/shares/cloudfront/new")
    assert new_page.status_code == 200
    detail = client.get(f"/shares/cloudfront/{share_euid}")
    assert detail.status_code == 200
    browse = client.get(f"/shares/cloudfront/{share_euid}/browse")
    assert browse.status_code == 200
    programmatic = client.get(f"/shares/cloudfront/{share_euid}/programmatic")
    assert programmatic.status_code == 200
    public_open = client.get(f"/public-shares/{public_id}", follow_redirects=False)
    assert public_open.status_code in {303, 307}

    report = client.get("/admin/external-shares")
    assert report.status_code == 200
    assert "External Shares" in report.text
    assert "cloudfront" not in report.text.lower() or "SH-" in report.text
