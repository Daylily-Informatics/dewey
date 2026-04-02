from __future__ import annotations

import pytest

from dewey_service.rbac import (
    DEFAULT_COGNITO_GROUP_ROLE_MAP,
    Role,
    normalize_group_role_map,
    normalize_session_profile,
    profile_has_role,
    roles_from_groups,
)


def test_default_group_role_map_and_role_normalization() -> None:
    assert DEFAULT_COGNITO_GROUP_ROLE_MAP == {
        "platform-admin": "ADMIN",
        "dewey-admin": "ADMIN",
        "dewey-readwrite": "READ_WRITE",
        "dewey-readonly": "READ_ONLY",
    }

    assert roles_from_groups(
        ["platform-admin", "dewey-readwrite", "dewey-readonly", "platform-admin"],
        DEFAULT_COGNITO_GROUP_ROLE_MAP,
    ) == ("ADMIN", "READ_WRITE", "READ_ONLY")

    profile = normalize_session_profile(
        email="USER@example.com",
        sub="sub-1",
        groups=["dewey-admin", "dewey-readwrite"],
        group_role_map=DEFAULT_COGNITO_GROUP_ROLE_MAP,
    )
    assert profile["email"] == "user@example.com"
    assert profile["sub"] == "sub-1"
    assert profile["groups"] == ["dewey-admin", "dewey-readwrite"]
    assert profile["roles"] == ["ADMIN", "READ_WRITE"]
    assert profile_has_role(profile, Role.ADMIN)


def test_normalize_group_role_map_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        normalize_group_role_map("not-a-map")

    with pytest.raises(ValueError):
        normalize_group_role_map({"": "ADMIN"})
