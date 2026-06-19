from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from dewey_service.app import create_app
from dewey_service.cloudfront import NullCloudFrontShareSigner
from dewey_service.service import DeweyService
from dewey_service.settings import Settings
from tests.support.service_fakes import _FakeLiteratureAdapter, _FakeStorageClient, _InMemoryBackend


def _service(
    *,
    storage: _FakeStorageClient | None = None,
    cloudfront: bool = False,
    requester_pays_buckets: set[str] | None = None,
    share_approved_origins: list[str] | None = None,
) -> DeweyService:
    return DeweyService(
        _InMemoryBackend(),
        default_share_ttl_seconds=120,
        storage_client=storage or _FakeStorageClient(),
        managed_storage_bucket="managed-bucket",
        managed_storage_prefix="artifacts",
        upload_session_ttl_seconds=900,
        upload_token_secret="upload-secret",
        search_export_max_rows=1000,
        literature_adapter=_FakeLiteratureAdapter(),
        literature_allowed_domains={"europepmc.org", "ncbi.nlm.nih.gov"},
        literature_request_timeout_seconds=5,
        qeo_ingest_url="https://qeo.test/api/v1/ingest/dewey-events",
        qeo_api_token="qeo-token",
        qeo_consumer_group="qeo.test",
        cloudfront_signer=NullCloudFrontShareSigner() if cloudfront else None,
        requester_pays_buckets=requester_pays_buckets or set(),
        share_approved_origins=share_approved_origins or [],
    )


def _register_object(service: DeweyService, storage: _FakeStorageClient, *, bucket: str, key: str):
    storage.seed_object(bucket=bucket, key=key, content_type="text/plain")
    _, artifact = service.register_artifact(
        artifact_type="report",
        storage_backend="s3",
        bucket=bucket,
        key=key,
        version_id=None,
        size=128,
        checksums={},
        content_type="text/plain",
        original_filename=key.rsplit("/", 1)[-1],
        producer_system="dewey-test",
        producer_object_euid="OBJ-1",
        storage_class="STANDARD",
        availability_status="available",
        metadata={},
        idempotency_key=f"artifact:{bucket}:{key}",
    )
    return artifact


def _settings() -> Settings:
    return Settings(
        api_bearer_token="token-123",
        session_secret_key="session-secret",
        cognito_domain="dewey-auth.example.com",
        cognito_app_client_id="client-123",
        cognito_app_client_secret="secret-123",
        cognito_redirect_uri="https://localhost:8914/auth/callback",
        cognito_logout_url="https://localhost:8914/login",
    )


def _login_user(monkeypatch, client: TestClient, *, groups: list[str] | None = None) -> None:
    monkeypatch.setattr(
        "daylily_auth_cognito.browser.session.exchange_authorization_code_async",
        lambda **kwargs: asyncio.sleep(0, result={"id_token": "header.payload.sig"}),
    )
    monkeypatch.setattr(
        "dewey_service.auth.decode_jwt_claims_noverify",
        lambda token: {
            "email": "operator@lsmc.bio",
            "sub": "sub-1",
            "cognito:groups": groups or ["dewey-readwrite"],
        },
    )
    login = client.get("/auth/login", follow_redirects=False)
    parsed = urlparse(login.headers["location"])
    state = parse_qs(parsed.query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": "code-1", "state": state},
        follow_redirects=False,
    )


def test_object_share_mints_requester_pays_presigned_package_and_audit() -> None:
    storage = _FakeStorageClient()
    service = _service(storage=storage, requester_pays_buckets={"requester-bucket"})
    artifact = _register_object(
        service,
        storage,
        bucket="requester-bucket",
        key="reports/sample.html",
    )

    status_code, share = service.create_share(
        target_kind="artifact_object",
        target_euid=artifact["artifact_euid"],
        targets=[],
        name="Sample report",
        purpose="collaborator review",
        owner_email="owner@lsmc.com",
        allowed_users=[],
        allowed_domains=["lsmc.com"],
        allowed_groups=[],
        delivery_modes=["presigned_s3"],
        expires_at=None,
        ttl_seconds=3600,
        idempotency_key="share-object-1",
    )

    assert status_code == 201
    assert share["share_euid"].startswith("SHR-")
    assert share["target_kind"] == "artifact_object"

    package = service.create_share_access_package(
        share["share_euid"],
        delivery_mode="presigned_s3",
        actor_email="reader@lsmc.com",
        actor_groups=[],
    )

    assert package["signed_url"].startswith("https://downloads.example.com/requester-bucket/")
    assert "x-amz-request-payer=requester" in package["signed_url"]
    assert package["manifest"][0]["requester_pays"] is True
    audit = service.list_share_audit(share["share_euid"])
    assert audit["items"][-1]["decision"] == "allow"
    assert audit["items"][-1]["actor_email"] == "reader@lsmc.com"


def test_share_denies_unauthorized_actor_and_revoke_blocks_future_packages() -> None:
    storage = _FakeStorageClient()
    service = _service(storage=storage)
    artifact = _register_object(service, storage, bucket="bucket-1", key="reports/a.txt")
    _, share = service.create_share(
        target_kind="artifact_object",
        target_euid=artifact["artifact_euid"],
        targets=[],
        name="Private report",
        purpose=None,
        owner_email="owner@lsmc.com",
        allowed_users=["allowed@lsmc.com"],
        allowed_domains=[],
        allowed_groups=[],
        delivery_modes=["presigned_s3"],
        expires_at=None,
        ttl_seconds=3600,
        idempotency_key="share-deny-1",
    )

    with pytest.raises(PermissionError):
        service.create_share_access_package(
            share["share_euid"],
            delivery_mode="presigned_s3",
            actor_email="other@example.com",
            actor_groups=[],
        )

    revoked = service.revoke_share(
        share["share_euid"],
        revoked_by="owner@lsmc.com",
        reason="test complete",
    )
    assert revoked["status"] == "revoked"
    with pytest.raises(ValueError, match="share is not active"):
        service.create_share_access_package(
            share["share_euid"],
            delivery_mode="presigned_s3",
            actor_email="allowed@lsmc.com",
            actor_groups=[],
        )

    audit = service.list_share_audit(share["share_euid"])
    decisions = [item["decision"] for item in audit["items"]]
    assert decisions == ["deny", "revoke", "deny"]


def test_prefix_share_uses_cloudfront_signed_cookies_without_listing_children() -> None:
    storage = _FakeStorageClient()
    storage.seed_object(bucket="html-bucket", key="multiqc/index.html", content_type="text/html")
    service = _service(
        storage=storage,
        cloudfront=True,
        share_approved_origins=["s3://html-bucket/multiqc"],
    )
    _, prefix_artifact = service.register_artifact_prefix(
        root_uri="s3://html-bucket/multiqc/",
        artifact_type="multiqc_site",
        producer_system="dewey-test",
        producer_object_euid="RUN-1",
        metadata={},
        idempotency_key="prefix-1",
    )

    _, share = service.create_share(
        target_kind="artifact_prefix",
        target_euid=prefix_artifact["artifact_euid"],
        targets=[],
        name="MultiQC",
        purpose="browser review",
        owner_email="owner@lsmc.com",
        allowed_users=["reader@lsmc.com"],
        allowed_domains=[],
        allowed_groups=[],
        delivery_modes=["cloudfront_signed_cookie", "dewey_html_browser"],
        expires_at=None,
        ttl_seconds=900,
        idempotency_key="share-prefix-1",
    )

    assert not any(call[0] == "list_objects" for call in storage.calls)
    package = service.create_share_access_package(
        share["share_euid"],
        delivery_mode="cloudfront_signed_cookie",
        actor_email="reader@lsmc.com",
        actor_groups=[],
    )

    assert package["cookies"]["CloudFront-Key-Pair-Id"] == "test-key"
    assert package["manifest"][0]["resource"].endswith("/multiqc/*")


def test_tracked_share_root_does_not_scan_and_subset_must_stay_under_root() -> None:
    storage = _FakeStorageClient()
    service = _service(storage=storage)
    inside = _register_object(service, storage, bucket="share-bucket", key="collab/a.txt")
    outside = _register_object(service, storage, bucket="share-bucket", key="private/b.txt")

    _, root = service.create_share_root(
        root_uri="s3://share-bucket/collab/",
        name="collab root",
        purpose="external collaboration",
        owner_email="owner@lsmc.com",
        allowed_delivery_modes=["presigned_s3_manifest"],
        idempotency_key="root-1",
    )
    assert root["root_uri"] == "s3://share-bucket/collab/"
    assert not any(call[0] == "list_objects" for call in storage.calls)

    _, subset = service.create_share_root_subset(
        root["share_root_euid"],
        targets=[{"target_kind": "artifact_object", "target_euid": inside["artifact_euid"]}],
        name="subset",
        purpose="subset review",
        owner_email="owner@lsmc.com",
        allowed_users=["reader@lsmc.com"],
        allowed_domains=[],
        allowed_groups=[],
        delivery_modes=["presigned_s3_manifest"],
        expires_at=None,
        ttl_seconds=900,
        idempotency_key="subset-1",
    )
    assert subset["target_kind"] == "mixed_set"

    with pytest.raises(ValueError, match="outside the registered share root"):
        service.create_share_root_subset(
            root["share_root_euid"],
            targets=[{"target_kind": "artifact_object", "target_euid": outside["artifact_euid"]}],
            name="bad subset",
            purpose=None,
            owner_email="owner@lsmc.com",
            allowed_users=[],
            allowed_domains=[],
            allowed_groups=[],
            delivery_modes=["presigned_s3_manifest"],
            expires_at=None,
            ttl_seconds=900,
            idempotency_key="subset-bad",
        )


def test_share_api_routes_round_trip() -> None:
    storage = _FakeStorageClient()
    service = _service(storage=storage)
    artifact = _register_object(service, storage, bucket="route-bucket", key="reports/route.txt")
    app = create_app(
        settings=_settings(),
        service=service,
    )
    client = TestClient(app)

    created = client.post(
        "/api/v1/shares",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "route-share-1"},
        json={
            "target_kind": "artifact_object",
            "target_euid": artifact["artifact_euid"],
            "owner_email": "owner@lsmc.com",
            "allowed_users": ["reader@lsmc.com"],
            "delivery_modes": ["presigned_s3"],
            "ttl_seconds": 900,
        },
    )
    assert created.status_code == 200
    share_euid = created.json()["share_euid"]

    fetched = client.get(
        f"/api/v1/shares/{share_euid}",
        headers={"Authorization": "Bearer token-123"},
    )
    assert fetched.status_code == 200

    package = client.post(
        f"/api/v1/shares/{share_euid}/access-package",
        headers={"Authorization": "Bearer token-123"},
        json={"delivery_mode": "presigned_s3", "actor_email": "reader@lsmc.com"},
    )
    assert package.status_code == 200
    assert package.json()["signed_url"].startswith("https://downloads.example.com/")

    audit = client.get(
        f"/api/v1/shares/{share_euid}/audit",
        headers={"Authorization": "Bearer token-123"},
    )
    assert audit.status_code == 200
    assert audit.json()["items"][-1]["decision"] == "allow"

    revoked = client.post(
        f"/api/v1/shares/{share_euid}/revoke",
        headers={"Authorization": "Bearer token-123"},
        json={"reason": "route smoke"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    root = client.post(
        "/api/v1/share-roots",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "route-root-1"},
        json={"root_uri": "s3://route-bucket/reports/", "owner_email": "owner@lsmc.com"},
    )
    assert root.status_code == 200
    root_euid = root.json()["share_root_euid"]
    subset = client.post(
        f"/api/v1/share-roots/{root_euid}/subsets",
        headers={"Authorization": "Bearer token-123", "Idempotency-Key": "route-subset-1"},
        json={
            "target_kind": "mixed_set",
            "targets": [{"target_kind": "artifact_object", "target_euid": artifact["artifact_euid"]}],
            "owner_email": "owner@lsmc.com",
            "allowed_users": ["reader@lsmc.com"],
            "delivery_modes": ["presigned_s3_manifest"],
            "ttl_seconds": 900,
        },
    )
    assert subset.status_code == 200


def test_share_manager_gui_uses_new_share_records(monkeypatch) -> None:
    storage = _FakeStorageClient()
    service = _service(storage=storage)
    artifact = _register_object(service, storage, bucket="gui-bucket", key="reports/gui.txt")
    app = create_app(settings=_settings(), service=service)

    with TestClient(app, base_url="https://localhost:8914") as client:
        _login_user(monkeypatch, client, groups=["platform-admin"])
        empty_page = client.get("/shares")
        assert empty_page.status_code == 200
        assert "Dewey Share Manager" in empty_page.text
        assert "Share References" not in empty_page.text
        admin_page = client.get("/admin/shares")
        assert admin_page.status_code == 200

        created = client.post(
            "/shares/create",
            data={
                "target_kind": "artifact_object",
                "target_euid": artifact["artifact_euid"],
                "name": "GUI share",
                "purpose": "route test",
                "owner_email": "operator@lsmc.bio",
                "allowed_domains": "lsmc.bio",
                "delivery_modes": "presigned_s3",
                "ttl_seconds": "900",
            },
        )
        assert created.status_code == 201, created.text
        assert "Share created." in created.text
        assert "GUI share" in created.text
        share_euid = service.list_shares(limit=1)[0]["share_euid"]

        detail = client.get(f"/shares/{share_euid}")
        assert detail.status_code == 200
        assert share_euid in detail.text

        package = client.post(
            f"/shares/{share_euid}/access-package",
            data={"delivery_mode": "presigned_s3", "signed_ttl_seconds": "900"},
        )
        assert package.status_code == 200
        assert "Access Package" in package.text
        assert "https://downloads.example.com/gui-bucket/reports/gui.txt" in package.text

        revoked = client.post(
            f"/shares/{share_euid}/revoke",
            data={"reason": "gui route smoke"},
        )
        assert revoked.status_code == 200
        assert "Share revoked." in revoked.text
        assert service.get_share(share_euid)["status"] == "revoked"

        root = client.post(
            "/share-roots/create",
            data={
                "root_uri": "s3://gui-bucket/reports/",
                "name": "GUI root",
                "purpose": "route test root",
                "allowed_delivery_modes": "presigned_s3_manifest",
            },
        )
        assert root.status_code == 201, root.text
        root_euid = service.list_share_roots(limit=1)[0]["share_root_euid"]
        subset = client.post(
            f"/share-roots/{root_euid}/subsets/create",
            data={
                "name": "GUI subset",
                "targets_json": (
                    '[{"target_kind":"artifact_object",'
                    f'"target_euid":"{artifact["artifact_euid"]}"}}]'
                ),
                "allowed_domains": "lsmc.bio",
                "delivery_modes": "presigned_s3_manifest",
                "ttl_seconds": "900",
            },
        )
        assert subset.status_code == 201, subset.text
        assert "Share root subset created." in subset.text
