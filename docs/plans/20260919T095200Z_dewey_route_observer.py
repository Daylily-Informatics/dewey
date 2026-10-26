"""One read-only observation per GUI backend route using existing OWY authority."""
import hashlib
import json
import os
import pwd
import socket
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("Redirect refused")


if pwd.getpwuid(os.getuid()).pw_name != "sysman" or socket.gethostname() != "sfo1-xfer1.sfo.lsmc.com":
    raise RuntimeError("Existing sysman transfer-host authority required")
if os.environ.get("AWS_PROFILE") != "lsmc":
    raise RuntimeError("Expected configured lsmc profile")
token = os.environ.get("OWY_DEWEY_API_TOKEN", "").strip()
if not token:
    raise RuntimeError("Configured OWY Dewey credential unavailable")
receipt = {
    "schema": "dewey.gui-backend-route-observation/1",
    "host": socket.gethostname(), "uid": os.getuid(),
    "credential_source_reference": "/home/sysman/.config/offwithyou/owy-dayhoff-env",
    "auth_scheme": "existing OWY_DEWEY_API_TOKEN bearer",
    "credential_values_or_hashes_recorded": False,
    "requests": [], "owner_or_runtime_mutations": False,
    "scope": "one normal public read per route; POST registry/search is read-only",
}
opener = build_opener(NoRedirect())
queries = [
    ("library", "POST", "/api/v1/registry/search", {"q": "", "page": 1, "page_size": 25, "scopes": ["artifact", "artifact_set"], "property_filters": [], "sort_field": "created_at", "sort_dir": "desc"}),
    ("sets", "POST", "/api/v1/registry/search", {"q": "", "page": 1, "page_size": 25, "scopes": ["artifact_set"], "property_filters": [], "sort_field": "created_at", "sort_dir": "desc"}),
    ("p1_registered_set", "GET", "/api/v1/records/M-DGX-VVW1", None),
]
for label, method, path, payload in queries:
    started = time.perf_counter()
    row = {"label": label, "method": method, "path": path,
           "request": payload, "started_at": datetime.now(timezone.utc).isoformat()}
    try:
        request = Request("https://dewey.day.lsmc.bio" + path, method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": "Bearer " + token,
                     "X-LSMC-Service-ID": "offwithyou-seqnas-xfer",
                     "Accept": "application/json", "Content-Type": "application/json"})
        try:
            response = opener.open(request, timeout=90)
        except HTTPError as error:
            response = error
        with response:
            row["status"] = response.status
            row["time_to_headers_ms"] = round((time.perf_counter() - started) * 1000, 3)
            raw = response.read(24 * 1024 * 1024 + 1)
            row["source_date"] = response.headers.get("Date")
        if len(raw) > 24 * 1024 * 1024:
            raise RuntimeError("Response exceeded24MiB bound")
        row.update(duration_ms=round((time.perf_counter() - started) * 1000, 3),
                   bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise RuntimeError("Expected native JSON object")
        row["response_fields"] = sorted(value)
        row["counts"] = {k: len(v) for k, v in value.items() if isinstance(v, list)}
        row["summary"] = {k: value[k] for k in ("total", "page", "page_size", "has_more", "timing_ms", "member_count", "euid", "kind", "facets", "capabilities") if k in value}
        if row["status"] != 200:
            row["error"] = {k: value[k] for k in ("detail", "code") if k in value}
    except Exception as error:
        row.update(error_type=type(error).__name__, duration_ms=round((time.perf_counter() - started) * 1000, 3))
    row["finished_at"] = datetime.now(timezone.utc).isoformat()
    receipt["requests"].append(row)
print(json.dumps(receipt, sort_keys=True))
