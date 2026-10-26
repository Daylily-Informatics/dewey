"""Selection and audience boundaries for externally delegated sharing."""

from datetime import datetime, timedelta, timezone

import pytest

from dewey_service.services.share_policy import (
    expiry,
    normalize_grants,
    normalized_policy,
    patterns,
    recipient_matches,
    selected,
)
from dewey_service.services.sharing import SharingServiceMixin


@pytest.mark.parametrize("value", ["2026-01-01", "not-a-date", 23, "2026-01-01T03:00:00"])
def test_expiry_rejects_missing_or_invalid_timezone(value):
    with pytest.raises(ValueError, match="timezone"):
        expiry(value)


def test_expiry_normalizes_timezone_and_preserves_indefinite_semantics():
    assert expiry("2026-01-01T01:00:00+01:00") == expiry("2026-01-01T00:00:00Z")
    assert expiry(None) == datetime.max.replace(tzinfo=timezone.utc)
    service = SharingServiceMixin()
    service.share_max_lifetime_days = 365
    for deadline in (
        datetime.now(timezone.utc) - timedelta(seconds=1),
        datetime.now(timezone.utc) + timedelta(days=366),
    ):
        with pytest.raises(ValueError):
            service._normalize_share_expiry(deadline.isoformat())


@pytest.mark.parametrize(
    "value", ["**", [""], ["/root/*"], ["a\0b"], [None], ["x"] * 101, ["x" * 1025], ["a**b"]]
)
def test_selection_rejects_ambiguous_or_unbounded_patterns(value):
    with pytest.raises(ValueError):
        patterns(value)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("report.html", True),
        ("nested/report.html", True),
        ("nested/deep/report.html", True),
        ("nested/reportXhtml", False),
        ("private/report.html", False),
        ("REPORT.html", False),
    ],
)
def test_recursive_selection_is_literal_case_sensitive_and_exclusion_wins(key, expected):
    assert selected(key, ["**/report.html"], ["private/**"]) is expected
    assert patterns(["**", "**", "a?.txt"]) == ["**", "a?.txt"]
    assert selected("a1.txt", ["a?.txt"], [])
    assert not selected("a/1.txt", ["a*.txt"], [])


@pytest.mark.parametrize(
    "overrides",
    [
        {"recipient_type": "group"},
        {"recipient": ""},
        {"recipient": "a b@example.test"},
        {"recipient": "@example.test"},
        {"recipient": "a@"},
        {"recipient": "a@b@c"},
        {"recipient_type": "domain", "recipient": "a@example.test"},
        {"recipient_type": "domain", "recipient": ".example.test"},
        {"recipient_type": "domain", "recipient": "a..example.test"},
        {"include_subdomains": True},
        {"include_subdomains": "true"},
        {"recipient_status": "trusted"},
        {"target_euids": []},
        {"target_euids": "fixture-target"},
        {"target_euids": ["outside-target"]},
        {"invented_permission": "download"},
    ],
)
def test_invalid_grants_fail_before_persistence(overrides):
    with pytest.raises(ValueError):
        normalize_grants(
            [{"recipient_type": "email", "recipient": "reader@example.test", **overrides}],
            share_expiry=None,
            member_euids=["fixture-target"],
        )


@pytest.mark.parametrize("values", [{}, [None]])
def test_grants_require_a_list_of_explicit_predicates(values):
    with pytest.raises(ValueError):
        normalize_grants(values, share_expiry=None, member_euids=["fixture-target"])


def test_grant_scope_deduplicates_targets_without_expanding_them():
    result = normalize_grants(
        [
            {
                "recipient_type": "email",
                "recipient": " Reader@EXAMPLE.test ",
                "target_euids": ["fixture-target-b", "fixture-target-b"],
            }
        ],
        share_expiry=None,
        member_euids=["fixture-target-a", "fixture-target-b"],
    )
    assert result[0]["recipient"] == "reader@example.test"
    assert result[0]["target_euids"] == ["fixture-target-b"]
    assert result[0]["recipient_status"] == "pending"


@pytest.mark.parametrize(
    ("include_subdomains", "email", "expected"),
    [
        (False, "reader@example.test", True),
        (False, "reader@lab.example.test", False),
        (True, "reader@lab.example.test", True),
        (True, "reader@badexample.test", False),
        (True, "reader@example.test.evil", False),
        (True, "reader", False),
        (True, "", False),
    ],
)
def test_domain_recipients_do_not_grant_sibling_or_lookalike_domains(
    include_subdomains, email, expected
):
    assert (
        recipient_matches(
            {
                "recipient_type": "domain",
                "recipient": "example.test",
                "include_subdomains": include_subdomains,
            },
            email,
        )
        is expected
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"audience": "anonymous"},
        {"allowed_groups": ["admin"]},
        {"delivery_modes": ["gateway", "presigned"]},
        {"content_mode": "inline"},
        {"denied_emails": "reader@example.test"},
        {"denied_emails": ["not-an-email"]},
        {"content_mode": "www", "report_entrypoint": "report.html", "report_bundle_root": "a//b/"},
        {"content_mode": "www", "report_entrypoint": "report.html", "report_bundle_root": "../"},
        {"content_mode": "www", "report_entrypoint": "report.html", "report_bundle_root": "a\\b/"},
    ],
)
def test_policy_rejects_removed_or_unsafe_contracts(changes):
    with pytest.raises(ValueError):
        normalized_policy(changes, share_expiry=None, member_euids=["fixture-target"])


def test_public_registered_grant_preserves_named_grants_and_inherits_deadline():
    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    result = normalized_policy(
        {
            "audience": "public_registered",
            "allowed_users": ["named@example.test"],
            "allowed_domains": ["outside.example"],
            "denied_emails": [" BLOCKED@example.test ", "blocked@example.test"],
        },
        share_expiry=deadline,
        member_euids=["fixture-target"],
    )
    assert [g["recipient_type"] for g in result["grants"]] == ["email", "domain", "registered"]
    assert all(g["expires_at"] == deadline for g in result["grants"])
    assert result["denied_emails"] == ["blocked@example.test"]
    assert recipient_matches(result["grants"][-1], "verified@any.example")
    assert not recipient_matches(result["grants"][-1], "")
