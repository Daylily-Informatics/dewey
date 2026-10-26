"""User CLI: authenticated HTTP operations, with no local database requirement."""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests
import typer
from cli_core_yo import ccyo_out
from cli_core_yo.spec import CommandPolicy


def _connection():
    base = os.environ.get("DEWEY_API_URL", "").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("DEWEY_API_URL must be an explicit HTTPS service origin")
    token_path = Path(os.environ.get("DEWEY_API_TOKEN_FILE", ""))
    if not token_path.is_absolute() or not token_path.is_file() or token_path.stat().st_mode & 0o077:
        raise ValueError("DEWEY_API_TOKEN_FILE must name an absolute private file (mode 600)")
    token = token_path.read_text().strip()
    if not token or any(c.isspace() for c in token):
        raise ValueError("Token file must contain one nonempty bearer token")
    return base, token


def _request(method, path, *, data=None, params=None, key=None, body=None):
    base, token = _connection()
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if key:
        headers["Idempotency-Key"] = key
    elif method == "DELETE":
        headers["Idempotency-Key"] = str(uuid.uuid4())
    if body is not None:
        headers["Content-Type"] = "application/octet-stream"
    response = requests.request(method, base + path, headers=headers, json=data if body is None else None,
        data=body, params=params, timeout=(10, 300), allow_redirects=False)
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(f"Dewey returned HTTP {response.status_code} without a JSON response") from None
    if not response.ok or response.is_redirect:
        raise RuntimeError(f"Dewey HTTP {response.status_code}: {result.get('detail', 'request failed')}")
    return result


def _emit(action):
    try:
        ccyo_out.emit_json(action())
    except (ValueError, OSError, RuntimeError, requests.RequestException) as exc:
        # Never render requests' exception URLs: delivery parameters can contain credentials.
        ccyo_out.error("Dewey network request failed" if isinstance(exc, requests.RequestException) else str(exc))
        raise typer.Exit(1) from None


def _data(path: Path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("Input must be a JSON object")
    return value


def _get(euid: str = typer.Argument(..., help="Dewey Object, Prefix, or Set EUID.")):
    _emit(lambda: _request("GET", f"/api/v1/records/{quote(euid, safe='')}"))


def _contents(euid: str = typer.Argument(...), relative_prefix: str = typer.Option(""), continuation_token: str | None = typer.Option(None)):
    _emit(lambda: _request("GET", f"/api/v1/records/{quote(euid, safe='')}/contents", params={"relative_prefix": relative_prefix, "continuation_token": continuation_token}))


def _access(euid: str = typer.Argument(...), relative_key: str = typer.Option(""), ttl_seconds: int | None = typer.Option(None, min=1, max=3600)):
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/access", data={"relative_key":relative_key,"ttl_seconds":ttl_seconds}))


def _register(manifest: Path = typer.Option(..., exists=True, dir_okay=False), idempotency_key: str = typer.Option(...)):
    _emit(lambda: _request("POST", "/api/v1/records", data=_data(manifest), key=idempotency_key))


def _search(query: str = typer.Argument(""), filters: Path | None = typer.Option(None), page: int = typer.Option(1, min=1), page_size: int = typer.Option(25, min=1, max=1000)):
    def run():
        data = _data(filters) if filters else {}
        return _request("POST", "/api/v1/registry/search", data={**data,"q":query,"page":page,"page_size":page_size})
    _emit(run)


def _edit(euid: str = typer.Argument(...), changes: Path = typer.Option(..., exists=True, dir_okay=False)):
    _emit(lambda: _request("PATCH", f"/api/v1/records/{quote(euid, safe='')}", data=_data(changes)))


def _permissions(euid: str = typer.Argument(...), policy: Path = typer.Option(..., exists=True, dir_okay=False)):
    _emit(lambda: _request("PATCH", f"/api/v1/records/{quote(euid, safe='')}/permissions", data=_data(policy)))


def _archive(euid: str = typer.Argument(...), confirm: bool = typer.Option(False, help="Archive registration and revoke its shares; retain S3 bytes.")):
    if not confirm:
        raise typer.BadParameter("Supply --confirm to archive this registration; S3 bytes are retained")
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/archive", data={}))


def _share(euid: str = typer.Argument(...), policy: Path = typer.Option(..., exists=True, dir_okay=False), idempotency_key: str = typer.Option(...)):
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/shares", data=_data(policy), key=idempotency_key))


def _share_get(euid: str = typer.Argument(...)):
    _emit(lambda: _request("GET", f"/api/v1/registry/shares/{quote(euid, safe='')}"))


def _share_edit(euid: str = typer.Argument(...), changes: Path = typer.Option(..., exists=True, dir_okay=False)):
    _emit(lambda: _request("PATCH", f"/api/v1/registry/shares/{quote(euid, safe='')}", data=_data(changes)))


def _revoke(euid: str = typer.Argument(...), reason: str = typer.Option(...), policy_revision: int = typer.Option(..., min=1)):
    _emit(lambda: _request("POST", f"/api/v1/registry/shares/{quote(euid, safe='')}/revoke", data={"reason":reason,"policy_revision":policy_revision}))


def _share_contents(euid: str = typer.Argument(...), relative_path: str = typer.Option(""), continuation_token: str | None = typer.Option(None), limit: int = typer.Option(100, min=1, max=200)):
    """List only current permitted files within this share; preserve exact relative keys."""
    _emit(lambda: _request("GET", f"/api/v2/recipient/shares/{quote(euid, safe='')}/contents", params={"path":relative_path,"continuation_token":continuation_token,"limit":limit}))


def _share_selection_preview(euid: str = typer.Argument(..., help="Persisted target record EUID."), policy: Path = typer.Option(..., exists=True, dir_okay=False)):
    """Preview a draft policy using bounded metadata; incomplete is not a complete inventory."""
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/shares/preview", data=_data(policy)))


def _share_activity(euid: str = typer.Argument(...), continuation_token: str | None = typer.Option(None), limit: int = typer.Option(100, min=1, max=200)):
    """Export one page of append-only share activity as JSON; follow continuation_token."""
    _emit(lambda: _request("GET", f"/api/v1/registry/shares/{quote(euid, safe='')}/activity", params={"continuation_token":continuation_token,"limit":limit}))


def _share_revoke_grant(euid: str = typer.Argument(...), grant_euid: str = typer.Argument(...), policy_revision: int = typer.Option(..., min=1), reason: str = typer.Option(...)):
    """Revoke one persisted recipient grant at the explicit current policy revision."""
    _emit(lambda: _request("POST", f"/api/v1/registry/shares/{quote(euid, safe='')}/grants/{quote(grant_euid, safe='')}/revoke", data={"policy_revision":policy_revision,"reason":reason}))


def _share_report(euid: str = typer.Argument(...)):
    """Show the authenticated share page for isolated report viewing in a browser."""
    def run():
        base, _ = _connection()
        detail = _request("GET", f"/api/v2/recipient/shares/{quote(euid, safe='')}")
        path = "/fetch/" + quote(euid, safe="")
        if detail.get("report_entrypoint"):
            path += "/" + quote(detail["report_entrypoint"], safe="/")
        return {"share_euid":detail["share_euid"], "browser_url":base + path,
            "requirements":["Verified-email browser sign-in", "Current share grant"], "action":"Open this durable URL in a browser"}
    _emit(run)


def _alias(euid: str = typer.Argument(...), slug: str = typer.Argument(...), policy_revision: int = typer.Option(..., min=1)):
    """Claim one available human-readable URL; claims cannot be reassigned."""
    _emit(lambda: _request("POST", f"/api/v1/registry/shares/{quote(euid, safe='')}/aliases",
        data={"slug": slug, "policy_revision": policy_revision}))


def _alias_list(euid: str = typer.Argument(...)):
    """List active and retired human-readable URLs for a managed share."""
    _emit(lambda: _request("GET", f"/api/v1/registry/shares/{quote(euid, safe='')}/aliases"))


def _alias_revoke(euid: str = typer.Argument(...), slug: str = typer.Argument(...), policy_revision: int = typer.Option(..., min=1)):
    """Permanently retire a slug without changing the canonical share URL."""
    _emit(lambda: _request("POST", f"/api/v1/registry/shares/{quote(euid, safe='')}/aliases/{quote(slug, safe='')}/revoke",
        data={"policy_revision": policy_revision}))


def _rebind(euid: str = typer.Argument(...), storage_uri: str = typer.Option(...), expected_location_revision: int = typer.Option(..., min=1),
            reason: str = typer.Option(...), version_id: str | None = typer.Option(None)):
    """Rebind a stable artifact to a verified equivalent S3 location; no storage objects are moved or deleted."""
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/location-rebind",
        data={"storage_uri": storage_uri, "expected_location_revision": expected_location_revision, "reason": reason, "version_id": version_id}))


def _sharing_report(starts_at: str = typer.Option(...), ends_at: str | None = typer.Option(None), owner_subject: str | None = typer.Option(None),
                    status: str | None = typer.Option(None), audience: str | None = typer.Option(None), content_mode: str | None = typer.Option(None),
                    older_than_days: int | None = typer.Option(None, min=0), never_accessed: bool = typer.Option(False),
                    inventory: bool = typer.Option(False), page: int = typer.Option(1, min=1),
                    observed_at: str | None = typer.Option(None), expected_inventory_sha256: str | None = typer.Option(None),
                    created_from: str | None = typer.Option(None), created_before: str | None = typer.Option(None),
                    output: Path | None = typer.Option(None, dir_okay=False, help="Export all frozen inventory pages to a new JSON file.")):
    """Read authorized share aggregates or paginated lifecycle inventory with explicit observation coverage."""
    params = {"starts_at": starts_at, "ends_at": ends_at, "owner_subject": owner_subject, "status": status,
        "audience": audience, "content_mode": content_mode, "older_than_days": older_than_days, "never_accessed": never_accessed,
        "created_from": created_from, "created_before": created_before}
    if inventory:
        params.update(page=page, page_size=100, observed_at=observed_at, expected_inventory_sha256=expected_inventory_sha256)
    def run():
        if page > 1 and (not inventory or not observed_at or not expected_inventory_sha256):
            raise ValueError("Inventory page 2 onward requires --observed-at and --expected-inventory-sha256 from page 1")
        if output:
            if not inventory or page != 1:
                raise ValueError("Complete inventory export requires --inventory and --page 1")
            return _export_sharing_inventory(params, output)
        return _request("GET", "/api/v1/registry/" + ("sharing-inventory" if inventory else "sharing-report"), params=params)
    _emit(run)


def _export_sharing_inventory(params, output):
    if output.exists() or output.is_symlink():
        raise ValueError("Inventory export output already exists")
    partial = output.with_name(output.name + ".partial")
    query, count, first = dict(params), 0, True
    frozen = None
    with partial.open("x") as stream:
        stream.write('{"items":[')
        while True:
            result = _request("GET", "/api/v1/registry/sharing-inventory", params=query)
            stamp = (result["observed_at"], result["inventory_sha256"])
            if frozen is not None and stamp != frozen:
                raise RuntimeError("Sharing inventory changed; partial export retained, restart with a new output")
            frozen = stamp
            for row in result["items"]:
                stream.write(("" if first else ",") + json.dumps(row, separators=(",", ":")))
                first = False
                count += 1
            if not result["has_more"]:
                break
            query.update(page=result["page"] + 1, observed_at=frozen[0], expected_inventory_sha256=frozen[1])
        if count != result["total"]:
            raise RuntimeError("Sharing inventory count differs from its frozen total")
        stream.write('],"complete":true,"observed_at":' + json.dumps(frozen[0])
            + ',"inventory_sha256":' + json.dumps(frozen[1]) + ',"coverage":' + json.dumps(result["coverage"]) + "}")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, output)
    partial.unlink()
    return {"status": "complete", "output": str(output.resolve()), "shares": count,
        "observed_at": frozen[0], "inventory_sha256": frozen[1]}


def _invite(euid: str = typer.Argument(...), email: str = typer.Option(...)):
    """Explicitly send a login invitation to an email already included in the share."""
    _emit(lambda: _request("POST", f"/api/v1/registry/shares/{quote(euid, safe='')}/invite", data={"email":email}))


def _member_add(euid: str = typer.Argument(...), member_euid: str = typer.Argument(...), idempotency_key: str = typer.Option(...)):
    _emit(lambda: _request("POST", f"/api/v1/records/{quote(euid, safe='')}/members", data={"artifact_euid":member_euid}, key=idempotency_key))


def _member_remove(euid: str = typer.Argument(...), member_euid: str = typer.Argument(...)):
    _emit(lambda: _request("DELETE", f"/api/v1/records/{quote(euid, safe='')}/members/{quote(member_euid, safe='')}"))


def _buckets(continuation_token: str | None = typer.Option(None), locations_page: int = typer.Option(1, min=1)):
    _emit(lambda: _request("GET", "/api/v1/storage/buckets", params={"continuation_token":continuation_token,"locations_page":locations_page}))


def _share_list(query: str = typer.Argument(""), page: int = typer.Option(1, min=1)):
    _emit(lambda: _request("GET", "/api/v1/registry/shares", params={"q":query,"page":page,"page_size":50,"sort":"created_at"}))


def _owner(euid: str = typer.Argument(...), email: str = typer.Option(...)):
    _emit(lambda: _request("PATCH", f"/api/v1/records/{quote(euid, safe='')}/owner", data={"email":email}))


def _preview(euid: str = typer.Argument(...), share_euid: str = typer.Option(..., help="Explicit managed share to view this report; verified browser sign-in required.")):
    """View through an explicit managed share rather than issuing a bearer preview."""
    _share_report(share_euid)


def _browse(uri: str = typer.Argument(...), continuation_token: str | None = typer.Option(None), limit: int = typer.Option(100, min=1, max=1000)):
    _emit(lambda: _request("GET", "/api/v1/storage/browse", params={"root_uri":uri,"continuation_token":continuation_token,"limit":limit}))


def _object(uri: str = typer.Argument(...)):
    _emit(lambda: _request("GET", "/api/v1/storage/object", params={"uri":uri}))


def _upload(file: Path = typer.Argument(..., exists=True, dir_okay=False), uri: str = typer.Option(...), register: bool = typer.Option(True), replace_etag: str | None = typer.Option(None, help="Admin only: replace the exact reviewed ETag.")):
    def run():
        size = file.stat().st_size
        operation = _request("POST", "/api/v1/storage/uploads", data={"uri":uri,"size":size,"replace_etag":replace_etag})
        path = f"/api/v1/storage/uploads/{quote(operation['operation_euid'], safe='')}"
        try:
            with file.open("rb") as stream:
                number = 1
                while True:
                    part = stream.read(operation["part_size"])
                    if not part and number > 1:
                        break
                    _request("PUT", f"{path}/parts/{number}", body=part)
                    number += 1
                    if not part:
                        break
            result = _request("POST", path + "/complete", data={})
        except Exception:
            ccyo_out.error(f"Upload did not complete. Inspect or abort operation {operation['operation_euid']}.")
            raise
        if register:
            result["registration"] = _request("POST", "/api/v1/records", data={"kind":"object","uri":uri,"name":file.name}, key=str(uuid.uuid4()))
        return result
    _emit(run)


def _operation(euid: str = typer.Argument(...)):
    _emit(lambda: _request("GET", f"/api/v1/storage/operations/{quote(euid, safe='')}"))


def _abort(euid: str = typer.Argument(...)):
    _emit(lambda: _request("POST", f"/api/v1/storage/uploads/{quote(euid, safe='')}/abort", data={}))


def _delete_preview(uri: str = typer.Argument(...), kind: str = typer.Option(...)):
    _emit(lambda: _request("POST", "/api/v1/storage/deletions/preview", data={"uri":uri,"kind":kind}))


def _delete_execute(euid: str = typer.Argument(...), manifest_sha256: str = typer.Option(...), confirmation: str = typer.Option(..., help="DELETE confirms the exact reviewed targets.")):
    _emit(lambda: _request("POST", f"/api/v1/storage/deletions/{quote(euid, safe='')}/execute", data={"manifest_sha256":manifest_sha256,"confirmation":confirmation}))


def register(registry, spec):
    from dewey_service.cli.share_fetch import fetch, manifest
    read = CommandPolicy(runtime_guard="exempt", supports_json=True)
    write = CommandPolicy(runtime_guard="exempt", supports_json=True, mutates_state=True)
    for group in ("artifacts", "sets", "shares", "storage"):
        registry.add_group(group)
    common = [("get",_get,"Resolve an EUID without storing a URL.",read),
        ("contents",_contents,"Browse a Prefix or inspect Set membership by EUID.",read),
        ("access",_access,"Request authorized delivery using only an EUID.",write),
        ("preview",_preview,"View an HTML report through an explicit managed share.",write),
        ("register",_register,"Register an explicit object, prefix, or set manifest.",write),
        ("search",_search,"Search the authorized registry before pagination.",read),
        ("update",_edit,"Update name, description, or arbitrary JSON metadata.",write),
        ("permissions",_permissions,"Manage metadata, download, and delegation policies.",write),
        ("owner",_owner,"Transfer ownership to an explicit email; owner or admin only.",write),
        ("archive",_archive,"Archive a registration while retaining storage bytes.",write),
        ("share",_share,"Create a stable authenticated Dewey share link.",write)]
    for group in ("artifacts", "sets"):
        for name, command, help_text, policy in common:
            registry.add_command(group, name, command, help_text=help_text, policy=policy)
    for group, commands in {
        "sets": [("add-member",_member_add,write),("remove-member",_member_remove,write)],
        "artifacts": [("location-rebind",_rebind,write)],
        "shares": [("list",_share_list,read),("get",_share_get,read),("create",_share,write),("update",_share_edit,write),("revoke",_revoke,write),("invite",_invite,write),("contents",_share_contents,read),("preview",_share_selection_preview,read),("activity",_share_activity,read),("revoke-grant",_share_revoke_grant,write),("fetch",fetch,write),("manifest",manifest,write),("report",_share_report,read),("aliases",_alias_list,read),("claim-slug",_alias,write),("retire-slug",_alias_revoke,write),("audit-report",_sharing_report,read)],
        "storage": [("buckets",_buckets,read),("browse",_browse,read),("object",_object,read),("upload",_upload,write),
            ("operation",_operation,read),("abort-upload",_abort,write),("delete-preview",_delete_preview,write),("delete-execute",_delete_execute,write)],
    }.items():
        for name, command, policy in commands:
            registry.add_command(group, name, command, help_text=command.__doc__ or name.replace("-", " ").capitalize(), policy=policy)
