"""Canonical managed-share predicates. S3 keys are literal, case sensitive strings."""
from __future__ import annotations

import re
from datetime import datetime, timezone

SCHEMA_VERSION = 3
GRANT_TEMPLATE = "access/share_grant/generic/1.0/"
EVENT_TEMPLATE = "operational/share_event/generic/1.0/"
UPGRADE_IDENTITY = "dewey:sharing-schema-v3"
UNSET = object()


def expiry(value: str | None) -> datetime:
    """Compare an explicit indefinite deadline without persisting a fake date."""
    if value is None:
        return datetime.max.replace(tzinfo=timezone.utc)
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
    if not email or email.count("@") != 1:
        return False
    if grant["recipient_type"] == "registered":
        return True
    recipient = grant["recipient"]
    if grant["recipient_type"] == "email":
        return email == recipient
    domain = email.rpartition("@")[2]
    return domain == recipient or bool(grant["include_subdomains"] and domain.endswith("." + recipient))


def normalize_grants(values, *, share_expiry: str | None, member_euids: list[str], public_registered=False):
    if not isinstance(values, list):
        raise ValueError("grants must be a list of explicit email or domain grants")
    result = []
    for value in values:
        if not isinstance(value, dict) or set(value) - {"recipient_type", "recipient", "include_subdomains", "include_patterns", "exclude_patterns", "expires_at", "target_euids", "grant_euid", "recipient_status"}:
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
        if value.get("recipient_status", "pending" if kind == "email" else "verified_on_access") not in {"pending", "verified_on_access"}:
            raise ValueError("recipient_status must be pending or verified_on_access; access always requires a verified identity")
        # Omission inherits the share. Explicit null is indefinite, never falsy-defaulted.
        raw_deadline = value.get("expires_at", share_expiry)
        deadline = expiry(raw_deadline)
        if deadline > expiry(share_expiry):
            raise ValueError("Grant expiry exceeds share expiry")
        targets = value.get("target_euids", member_euids)
        if not isinstance(targets, list) or not targets or any(t not in member_euids for t in targets):
            raise ValueError("Grant targets must be a nonempty subset of the reviewed share members")
        result.append({"recipient_type": kind, "recipient": recipient,
            "include_subdomains": value.get("include_subdomains", False),
            "include_patterns": patterns(value.get("include_patterns"), default=["**"]),
            "exclude_patterns": patterns(value.get("exclude_patterns")),
            "expires_at": None if raw_deadline is None else deadline.isoformat(),
            "recipient_status": value.get("recipient_status", "pending" if kind == "email" else "verified_on_access"),
            "target_euids": list(dict.fromkeys(targets))})
    if public_registered:
        result.append({"recipient_type": "registered", "recipient": "*", "include_subdomains": False,
            "include_patterns": ["**"], "exclude_patterns": [], "expires_at": share_expiry,
            "recipient_status": "verified_on_access", "target_euids": list(member_euids)})
    return result


def normalized_policy(data, *, share_expiry, member_euids):
    audience = data.get("audience", "recipients")
    if audience not in {"recipients", "public_registered"} or data.get("allowed_groups"):
        raise ValueError("audience must be recipients or public_registered; anonymous shares are forbidden")
    grants = data.get("grants")
    if grants is None:
        grants = [{"recipient_type": "email", "recipient": v} for v in data.get("allowed_users", [])]
        grants += [{"recipient_type": "domain", "recipient": v} for v in data.get("allowed_domains", [])]
    modes = data.get("delivery_modes", ["gateway"])
    if modes != ["gateway"]:
        raise ValueError("Only authenticated gateway delivery is supported; raw presigns were removed")
    content_mode = data.get("content_mode", "download")
    if content_mode not in {"download", "www"}:
        raise ValueError("content_mode must be download or www")
    entrypoint = data.get("report_entrypoint")
    bundle = data.get("report_bundle_root", "")
    if content_mode == "www" and (not isinstance(entrypoint, str) or not entrypoint or entrypoint.startswith("/")
            or any(p in {"", ".", ".."} for p in entrypoint.split("/")) or "\\" in entrypoint or "\x00" in entrypoint
            or not entrypoint.lower().endswith((".html", ".htm"))):
        raise ValueError("WWW shares require an explicit root-relative report_entrypoint")
    if not isinstance(bundle, str) or bundle and (not bundle.endswith("/") or bundle.startswith("/")
            or any(p in {"", ".", ".."} for p in bundle.rstrip("/").split("/")) or "\\" in bundle or "\x00" in bundle):
        raise ValueError("report_bundle_root must be an exact relative directory ending with / or empty")
    denied = data.get("denied_emails", [])
    if not isinstance(denied, list) or any(not isinstance(e, str) or e.count("@") != 1 for e in denied):
        raise ValueError("denied_emails must contain email addresses")
    return {"schema_version": SCHEMA_VERSION, "audience": audience, "content_mode": content_mode,
        "report_entrypoint": entrypoint if content_mode == "www" else None,
        "report_bundle_root": bundle if content_mode == "www" else "",
        "include_patterns": patterns(data.get("include_patterns"), default=["**"]),
        "exclude_patterns": patterns(data.get("exclude_patterns")), "denied_emails": sorted({e.strip().lower() for e in denied}),
        "delivery_modes": list(dict.fromkeys(modes)),
        "grants": normalize_grants(grants, share_expiry=share_expiry, member_euids=member_euids,
            public_registered=audience == "public_registered")}
