"""Major-12 management contracts replacing removed bearer S3/CloudFront sharing."""

import pytest
from fastapi import HTTPException

from tests.support.sharing_v12_fakes import OWNER, READER, Harness, actor


def service_fixture(monkeypatch):
    h = Harness()
    h.service._idempotency_replay = lambda *args, **kwargs: None
    h.service._store_idempotency = lambda *args, **kwargs: None
    monkeypatch.setattr("dewey_service.services.share_revisions.require_record", lambda *args: None)
    h.service._require_storage = lambda: pytest.fail(
        "Creating a share must not scan or mint storage credentials"
    )
    return h


@pytest.mark.parametrize(
    "mode",
    [
        "presigned",
        "presigned_s3",
        "presigned_s3_manifest",
        "cloudfront_signed_cookie",
        "dewey_html_browser",
    ],
)
def test_removed_bearer_delivery_modes_fail_explicitly(monkeypatch, mode):
    h = service_fixture(monkeypatch)
    target = h.artifact()
    with actor():
        with pytest.raises(ValueError, match="gateway"):
            h.service.create_share(
                target_kind="artifact_object",
                target_euid=target.euid,
                allowed_users=[READER.email],
                delivery_modes=[mode],
                expires_at=None,
                idempotency_key="removed-mode",
            )
        with pytest.raises(HTTPException) as gone:
            h.service.create_share_access_package("unknown-share", delivery_mode=mode)
        assert gone.value.status_code == 410
        with pytest.raises(HTTPException) as presign:
            h.service.presign_share_object("unknown-share", target.euid)
        assert presign.value.status_code == 410
    assert not [r for r in h.rows if r.type == "share"]


def test_object_package_is_authenticated_stable_fetch_and_contains_no_storage_credentials(
    monkeypatch,
):
    h = service_fixture(monkeypatch)
    target = h.artifact()
    h.service.requester_pays_buckets = {target.json_addl["bucket"]}
    with actor():
        code, share = h.service.create_share(
            target_kind="artifact_object",
            target_euid=target.euid,
            allowed_users=[READER.email],
            expires_at=None,
            idempotency_key="gateway-object",
        )
    assert code == 201
    with actor(READER):
        package = h.service.create_share_access_package(share["share_euid"])
        receipt = h.service.resolve_share_fetch(share["share_euid"])
    assert package == {
        "share_euid": share["share_euid"],
        "delivery_mode": "gateway",
        "browser_path": "/fetch/" + share["share_euid"],
        "manifest_path": "/fetch/" + share["share_euid"] + "?format=manifest",
        "archive_path": "/fetch/" + share["share_euid"] + "?format=tar",
    }
    assert receipt["target_euid"] == target.euid
    assert h.service._request_payer_for_bucket(target.json_addl["bucket"]) == "requester"
    assert h.service._request_payer_for_bucket("another-bucket") is None


def test_revoke_blocks_future_packages_and_retains_native_audit(monkeypatch):
    h = service_fixture(monkeypatch)
    target = h.artifact()
    share = h.share([target])
    with actor():
        revoked = h.service.revoke_share(share.euid, policy_revision=1, reason="review complete")
    assert revoked["status"] == "revoked" and revoked["policy_revision"] == 2
    with actor(READER), pytest.raises(HTTPException) as denied:
        h.service.create_share_access_package(share.euid)
    assert denied.value.status_code == 403
    (event,) = h.related(share, "share_event", "share_event")
    assert event.json_addl["event_type"] == "revoked" and event.json_addl["decision"] == "revoke"
    assert h.service._historical_share_members(h.session, share) == [target]


def test_www_share_retains_bundle_contract_without_cloudfront_cookies_or_listing(monkeypatch):
    h = service_fixture(monkeypatch)
    target = h.artifact(prefix=True)
    with actor():
        _, share = h.service.create_share(
            target_kind="artifact_prefix",
            target_euid=target.euid,
            allowed_users=[READER.email],
            content_mode="www",
            report_entrypoint="reports/multiqc.html",
            report_bundle_root="reports/",
            expires_at=None,
            idempotency_key="gateway-www",
        )
    assert share["content_mode"] == "www" and share["report_bundle_root"] == "reports/"
    with actor(READER):
        resolved = h.service.resolve_share_identifier(share["share_euid"])
        assert resolved["report_entrypoint"] == "reports/multiqc.html"
        assert resolved["members"][0]["target_kind"] == "artifact_prefix"
        assert "cookies" not in h.service.create_share_access_package(share["share_euid"])


def test_tracked_root_retains_exact_prefix_and_rejects_outside_subset(monkeypatch):
    h = service_fixture(monkeypatch)
    inside = h.artifact(key="root/inside.txt")
    outside = h.artifact("fixture-outside", key="root-lookalike/outside.txt")
    with actor():
        _, root = h.service.create_share_root(
            root_uri="s3://fixture-source/root",
            name="Reviewed root",
            purpose="recipient sharing",
            owner_email=OWNER.email,
            allowed_delivery_modes=["gateway"],
            idempotency_key="fixture-root",
        )
        args = {
            "name": "Reviewed subset",
            "purpose": None,
            "owner_email": OWNER.email,
            "allowed_users": [READER.email],
            "allowed_domains": [],
            "allowed_groups": [],
            "delivery_modes": ["gateway"],
            "expires_at": None,
            "ttl_seconds": None,
        }
        _, share = h.service.create_share_root_subset(
            root["share_root_euid"],
            targets=[{"target_kind": "artifact_object", "target_euid": inside.euid}],
            idempotency_key="fixture-subset",
            **args,
        )
        assert share["target_kind"] == "mixed_set" and share["expires_at"] is None
        with pytest.raises(ValueError, match="outside the registered share root"):
            h.service.create_share_root_subset(
                root["share_root_euid"],
                targets=[{"target_kind": "artifact_object", "target_euid": outside.euid}],
                idempotency_key="fixture-outside-subset",
                **args,
            )
    assert root["root_uri"] == "s3://fixture-source/root/"


def test_management_descriptor_uses_current_native_grants_and_redacts_recipient_view(monkeypatch):
    h = service_fixture(monkeypatch)
    target = h.artifact()
    share = h.share([target], purpose="review")
    with actor():
        managed = h.service.get_share(share.euid)
        assert managed["can_manage"] and managed["schema_version"] == 3
        assert managed["grants"][0]["target_euids"] == [target.euid]
        assert managed["targets"] == [{"euid": target.euid, "name": target.name, "kind": "object"}]
    with actor(READER):
        recipient = h.service.get_share(share.euid)
        assert (
            recipient["can_manage"] is False and recipient["fetch_path"] == "/fetch/" + share.euid
        )
        assert not {"grants", "targets", "members", "owner_email", "aliases"}.intersection(
            recipient
        )
