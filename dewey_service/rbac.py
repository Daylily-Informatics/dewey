"""Role and group helpers for Dewey auth."""

from __future__ import annotations

from enum import Enum
from typing import Any


class Role(str, Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    ADMIN = "ADMIN"


DEFAULT_COGNITO_GROUP_ROLE_MAP: dict[str, str] = {
    "platform-admin": Role.ADMIN.value,
    "dewey-admin": Role.ADMIN.value,
    "dewey-readwrite": Role.READ_WRITE.value,
    "dewey-readonly": Role.READ_ONLY.value,
}


def _normalize_group(group: Any) -> str:
    return str(group or "").strip()


def _normalize_role(role: Any) -> str:
    cleaned = str(role or "").strip().upper()
    if cleaned not in {item.value for item in Role}:
        raise ValueError(f"Unsupported Dewey role: {role!r}")
    return cleaned


def normalize_group_role_map(raw: Any) -> dict[str, str]:
    if raw is None:
        return dict(DEFAULT_COGNITO_GROUP_ROLE_MAP)
    if not isinstance(raw, dict):
        raise ValueError("cognito_group_role_map must be a mapping")

    normalized: dict[str, str] = {}
    for group, role in raw.items():
        clean_group = _normalize_group(group)
        clean_role = _normalize_role(role)
        if not clean_group:
            raise ValueError("cognito_group_role_map contains an empty group name")
        normalized[clean_group] = clean_role
    return normalized


def normalize_group_list(groups: Any) -> list[str]:
    if isinstance(groups, str) or groups is None:
        return []
    if not isinstance(groups, (list, tuple, set)):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in groups:
        clean = _normalize_group(item)
        if clean and clean not in seen:
            out.append(clean)
            seen.add(clean)
    return out


def roles_from_groups(groups: Any, group_role_map: dict[str, str] | None = None) -> tuple[str, ...]:
    mapping = group_role_map or DEFAULT_COGNITO_GROUP_ROLE_MAP
    roles: list[str] = []
    seen: set[str] = set()
    for group in normalize_group_list(groups):
        role = mapping.get(group)
        if not role:
            continue
        clean_role = _normalize_role(role)
        if clean_role not in seen:
            roles.append(clean_role)
            seen.add(clean_role)
    return tuple(roles)


def normalize_session_profile(
    *,
    email: Any,
    sub: Any,
    groups: Any,
    group_role_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    normalized_groups = normalize_group_list(groups)
    return {
        "email": str(email or "").strip().lower(),
        "sub": str(sub or "").strip(),
        "groups": normalized_groups,
        "roles": list(roles_from_groups(normalized_groups, group_role_map)),
    }


def profile_roles(profile: dict[str, Any] | None) -> tuple[str, ...]:
    payload = dict(profile or {})
    raw_roles = payload.get("roles")
    if isinstance(raw_roles, list):
        roles: list[str] = []
        seen: set[str] = set()
        for item in raw_roles:
            try:
                role = _normalize_role(item)
            except ValueError:
                continue
            if role not in seen:
                roles.append(role)
                seen.add(role)
        return tuple(roles)
    return roles_from_groups(payload.get("groups") or [], DEFAULT_COGNITO_GROUP_ROLE_MAP)


def profile_has_role(profile: dict[str, Any] | None, role: Role) -> bool:
    return role.value in profile_roles(profile)
