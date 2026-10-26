"""Changed-code policy, identity, scope, and equivalence contracts; no AWS calls."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dewey_service.registry_access import Principal, principal_context
from dewey_service.services.share_policy import expiry, normalized_policy, recipient_matches
from dewey_service.services.share_rebind import equivalent_objects
from dewey_service.services.share_revisions import normalize_slug
from dewey_service.services.sharing import SharingServiceMixin
from dewey_service.storage import StorageObject


def row(kind, fixture_id, **payload):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        type=kind,
        euid=fixture_id,
        uid=fixture_id,
        name=fixture_id,
        bstatus="active",
        domain_code="fixture",
        created_dt=now,
        modified_dt=now,
        json_addl={"properties": {}, **payload},
    )


def test_omission_and_explicit_null_are_distinct_and_grant_bounds_hold():
    service = SharingServiceMixin()
    service.share_max_lifetime_days = 365
    finite = service._normalize_share_expiry()
    assert 29.99 < (expiry(finite) - datetime.now(timezone.utc)).total_seconds() / 86400 < 30.01
    assert service._normalize_share_expiry(None) is None
    policy = normalized_policy(
        {"grants": [{"recipient_type": "email", "recipient": "recipient@example.test"}]},
        share_expiry=None,
        member_euids=["artifact-fixture"],
    )
    assert policy["grants"][0]["expires_at"] is None
    with pytest.raises(ValueError, match="exceeds"):
        normalized_policy(
            {
                "grants": [
                    {
                        "recipient_type": "email",
                        "recipient": "recipient@example.test",
                        "expires_at": None,
                    }
                ]
            },
            share_expiry=finite,
            member_euids=["artifact-fixture"],
        )


def test_registration_open_is_authenticated_and_never_a_domain_tenant_grant():
    policy = normalized_policy(
        {"audience": "public_registered", "grants": []},
        share_expiry=None,
        member_euids=["artifact-fixture"],
    )
    grant = policy["grants"][0]
    assert grant["recipient_type"] == "registered"
    assert recipient_matches(grant, "person@outside.example")
    assert not recipient_matches(grant, "")
    for audience in ("public", "anonymous", "private"):
        with pytest.raises(ValueError, match="anonymous"):
            normalized_policy(
                {"audience": audience}, share_expiry=None, member_euids=["artifact-fixture"]
            )


def test_named_mixed_recipients_and_denial_patterns_remain_literal():
    policy = normalized_policy(
        {
            "grants": [
                {"recipient_type": "email", "recipient": "Person@inside.example"},
                {"recipient_type": "email", "recipient": "Other@outside.example"},
            ],
            "exclude_patterns": ["private/**"],
        },
        share_expiry=None,
        member_euids=["artifact-fixture"],
    )
    assert [g["recipient"] for g in policy["grants"]] == [
        "person@inside.example",
        "other@outside.example",
    ]
    assert all(g["recipient_status"] == "pending" for g in policy["grants"])
    with pytest.raises(ValueError, match="presigns"):
        normalized_policy(
            {"delivery_modes": ["presigned"]}, share_expiry=None, member_euids=["artifact-fixture"]
        )


@pytest.mark.parametrize(
    "slug", ["UPPER", "aa", "-foo", "foo-", "fetch", "m-dgx-example", "../escape", "a" * 64]
)
def test_alias_namespace_rejects_ambiguous_or_reserved_identifiers(slug):
    with pytest.raises(ValueError):
        normalize_slug(slug)


def test_slug_keeps_requested_spelling_and_allows_digit_start():
    assert normalize_slug("2026-report") == "2026-report"


def test_recipient_grant_is_sufficient_without_underlying_recipient_acl():
    artifact = row(
        "artifact",
        "artifact-fixture",
        storage_backend="s3",
        storage_kind="object",
        bucket="fixture",
        key="new-location/data.dat",
        original_filename="stable.dat",
    )
    share = row(
        "share",
        "share-fixture",
        status="active",
        policy_revision=1,
        expires_at=None,
        denied_emails=[],
        include_patterns=["stable.dat"],
        exclude_patterns=[],
        delivery_modes=["gateway"],
        content_mode="download",
    )
    grant = row(
        "share_grant",
        "grant-fixture",
        status="active",
        policy_revision=1,
        expires_at=None,
        recipient_type="email",
        recipient="person@outside.example",
        include_subdomains=False,
        include_patterns=["**"],
        exclude_patterns=[],
    )
    service = SharingServiceMixin()
    service._share_members = lambda session, s: [artifact]
    service._share_grants = lambda session, s: [grant]
    service._grant_targets = lambda session, g: [artifact]
    service._protected_share_path = lambda *a, **k: pytest.fail(
        "Recipient ACL must not intersect an intentional grant"
    )
    with principal_context(
        Principal(subject="recipient", email="person@outside.example", email_verified=True)
    ):
        result = service._evaluate_share(None, share, artifact.euid, "", "gateway")
        assert result["expires_at"] is None
        assert result["filename"] == "stable.dat"
        assert result["key"] == "new-location/data.dat"
    with (
        principal_context(
            Principal(subject="recipient", email="person@outside.example", email_verified=False)
        ),
        pytest.raises(HTTPException) as denied,
    ):
        service._evaluate_share(None, share, artifact.euid, "", "gateway")
    assert denied.value.status_code == 403
    share.json_addl["denied_emails"] = ["person@outside.example"]
    with (
        principal_context(
            Principal(subject="recipient", email="person@outside.example", email_verified=True)
        ),
        pytest.raises(HTTPException),
    ):
        service._evaluate_share(None, share, artifact.euid, "", "gateway")


def test_rebind_equivalence_requires_qualified_checksum_not_etag():
    a = StorageObject(
        bucket="source",
        key="data",
        size=10,
        etag="same",
        sha256="digest",
        checksum_type="FULL_OBJECT",
        version_id="source-version",
    )
    b = StorageObject(
        bucket="destination",
        key="data",
        size=10,
        etag="same",
        sha256="digest",
        checksum_type="FULL_OBJECT",
        version_id="destination-version",
    )
    assert equivalent_objects(a, b)["size"] == 10
    with pytest.raises(ValueError, match="FULL_OBJECT"):
        equivalent_objects(
            a,
            StorageObject(
                bucket="destination",
                key="data",
                size=10,
                etag="same",
                sha256="digest",
                checksum_type="COMPOSITE",
            ),
        )
    with pytest.raises(ValueError, match="byte counts"):
        equivalent_objects(
            a,
            StorageObject(
                bucket="destination",
                key="data",
                size=11,
                sha256="digest",
                checksum_type="FULL_OBJECT",
            ),
        )


def test_www_requires_exact_entrypoint_and_bundle_boundary():
    source = {
        "audience": "public_registered",
        "content_mode": "www",
        "report_entrypoint": "reports/multiqc.html",
        "report_bundle_root": "reports/",
    }
    assert (
        normalized_policy(source, share_expiry=None, member_euids=["artifact-fixture"])[
            "report_bundle_root"
        ]
        == "reports/"
    )
    for entry in ("../multiqc.html", "/multiqc.html", "a//b.html", "report.txt"):
        with pytest.raises(ValueError):
            normalized_policy(
                {**source, "report_entrypoint": entry},
                share_expiry=None,
                member_euids=["artifact-fixture"],
            )


def test_www_selected_target_and_bundle_are_validated_before_persisting():
    service = SharingServiceMixin()
    target = row(
        "artifact",
        "artifact-fixture",
        storage_backend="s3",
        storage_kind="prefix",
        bucket="fixture",
        key="reports/",
    )
    policy = normalized_policy(
        {
            "content_mode": "www",
            "report_entrypoint": "bundle/report.html",
            "report_bundle_root": "bundle/",
        },
        share_expiry=None,
        member_euids=[target.euid],
    )
    service._validate_report_selection(policy, [target])
    with pytest.raises(ValueError, match="bundle root"):
        service._validate_report_selection({**policy, "report_bundle_root": "elsewhere/"}, [target])
    with pytest.raises(ValueError, match="excluded"):
        service._validate_report_selection({**policy, "exclude_patterns": ["**"]}, [target])
