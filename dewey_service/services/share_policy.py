"""Canonical managed-share predicates. S3 keys are literal, case sensitive strings."""
from __future__ import annotations

import re
from datetime import datetime, timezone

SCHEMA_VERSION = 2
GRANT_TEMPLATE = "access/share_grant/generic/1.0/"
EVENT_TEMPLATE = "operational/share_event/generic/1.0/"
UPGRADE_IDENTITY = "dewey:sharing-schema-v2"


def expiry(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("expires_at must be a timezone-bearing ISO8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("expires_at must include a timezone")
    return result.astimezone(timezone.utc)


def patterns(value, *, default=None):
    if value is None:
        value = default if default is not None else []
    if not isinstance(value, list) or any(not isinstance(p, str) or not p or p.startswith("/") or "\x00" in p for p in value):
        raise ValueError("Patterns must be nonempty, root-relative strings")
    if len(value) > 100 or any(len(p) > 1024 for p in value):
        raise ValueError("Selection exceeds pattern limits")
    for pattern in value:
        glob_regex(pattern)
    return list(dict.fromkeys(value))


def glob_regex(pattern: str):
    # Double-star is a complete segment; **/ can match zero segments.
    chunks = pattern.split("/")
    result = ""
    for index, chunk in enumerate(chunks):
        if "**" in chunk and chunk != "**":
            raise ValueError("** must occupy a complete path segment")
        last = index == len(chunks) - 1
        if chunk == "**":
            result += ".*" if last else "(?:[^/]*/)*"
        else:
            result += "".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in chunk)
            if not last:
                result += "/"
    return re.compile(r"\A" + result + r"\Z", re.DOTALL)


def selected(key: str, includes: list[str], excludes: list[str]) -> bool:
    return any(glob_regex(p).fullmatch(key) for p in includes) and not any(glob_regex(p).fullmatch(key) for p in excludes)


def recipient_matches(grant: dict, email: str) -> bool:
    email = email.lower()
    recipient = grant["recipient"]
    if grant["recipient_type"] == "email":
        return email == recipient
    domain = email.rpartition("@")[2]
    return domain == recipient or bool(grant["include_subdomains"] and domain.endswith("." + recipient))


def normalize_grants(values, *, share_expiry: str, member_euids: list[str]):
    if not isinstance(values, list) or not values:
        raise ValueError("At least one explicit email or domain grant is required")
    result = []
    for value in values:
        if not isinstance(value, dict) or set(value) - {"recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at", "target_euids", "grant_euid"}:
            raise ValueError("Unsupported grant fields")
        kind, recipient = value.get("recipient_type"), str(value.get("recipient") or "").strip().lower()
        if kind not in {"email", "domain"} or not recipient or any(c.isspace() for c in recipient):
            raise ValueError("A grant requires an explicit email or domain")
        if kind == "email" and (recipient.count("@") != 1 or not all(recipient.split("@"))):
            raise ValueError("Invalid recipient email")
        if kind == "domain" and ("@" in recipient or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", recipient) or ".." in recipient):
            raise ValueError("Invalid recipient domain")
        if type(value.get("include_subdomains", False)) is not bool or kind == "email" and value.get("include_subdomains"):
            raise ValueError("include_subdomains is a boolean for domain grants only")
        deadline = expiry(value.get("expires_at") or share_expiry)
        if deadline > expiry(share_expiry):
            raise ValueError("Grant expiry exceeds share expiry")
        targets = value.get("target_euids", member_euids)
        if not isinstance(targets, list) or not targets or any(t not in member_euids for t in targets):
            raise ValueError("Grant targets must be a nonempty subset of the reviewed share members")
        result.append({"recipient_type": kind, "recipient": recipient,
            "include_subdomains": value.get("include_subdomains", False),
            "include_patterns": patterns(value.get("include_patterns"), default=["**"]),
            "exclude_patterns": patterns(value.get("exclude_patterns")),
            "expires_at": deadline.isoformat(), "target_euids": list(dict.fromkeys(targets))})
    return result


def normalized_policy(data, *, share_expiry, member_euids):
    if data.get("audience", "recipients") not in {"recipients", "private"} or data.get("allowed_groups"):
        raise ValueError("Managed shares require explicit email/domain grants")
    grants = data.get("grants")
    if grants is None:
        grants = [{"recipient_type": "email", "recipient": v} for v in data.get("allowed_users", [])]
        grants += [{"recipient_type": "domain", "recipient": v} for v in data.get("allowed_domains", [])]
    modes = data.get("delivery_modes", ["gateway"])
    if not isinstance(modes, list) or not modes or set(modes) - {"gateway", "presigned"}:
        raise ValueError("delivery_modes must select gateway and/or presigned explicitly")
    denied = data.get("denied_emails", [])
    if not isinstance(denied, list) or any(not isinstance(e, str) or e.count("@") != 1 for e in denied):
        raise ValueError("denied_emails must contain email addresses")
    return {"schema_version": SCHEMA_VERSION, "include_patterns": patterns(data.get("include_patterns"), default=["**"]),
        "exclude_patterns": patterns(data.get("exclude_patterns")), "denied_emails": sorted({e.strip().lower() for e in denied}),
        "delivery_modes": list(dict.fromkeys(modes)),
        "grants": normalize_grants(grants, share_expiry=share_expiry, member_euids=member_euids)}
