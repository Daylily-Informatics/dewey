"""Read-only, sanitized correlation of existing Dewey and Apache incident logs."""
import collections
import datetime as dt
import json
import re
import subprocess

CUTOFF = dt.datetime(2026, 9, 23, 20, 40, tzinfo=dt.timezone.utc)
UNTIL = dt.datetime(2026, 9, 23, 21, 1, tzinfo=dt.timezone.utc)
CONTAINER = "dayhoff-day-dewey-1"

def route(value):
    path = value.split("?")[0]
    return re.sub(r"M-[A-Z0-9-]+|[a-f0-9]{20,}", ":id", path)

raw = subprocess.run(
    ["docker", "logs", "--since", CUTOFF.isoformat(), "--until", UNTIL.isoformat(),
     "--tail", "5000", "--timestamps", CONTAINER],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True,
).stdout
app = []
for line in raw.splitlines():
    match = re.search(r'^(\S+).*"(GET|POST|PUT|DELETE|PATCH|HEAD) (\S+) HTTP/[^\"]+" (\d{3})', line)
    if match:
        app.append({"end": dt.datetime.fromisoformat(match[1].replace("Z", "+00:00")),
                    "key": (match[2], match[3], match[4]), "used": False})
raw = subprocess.check_output(
    ["sudo", "tail", "-n", "1200", "/var/log/apache2/dewey-access.log"], text=True)
clients, requests = {}, []
for line in raw.splitlines():
    match = re.match(r'(\S+) \S+ \S+ \[([^\]]+)\] "(GET|POST|PUT|DELETE|PATCH|HEAD) (\S+) HTTP/[^\"]+" (\d{3}) (\d+)', line)
    if not match:
        continue
    start = dt.datetime.strptime(match[2], "%d/%b/%Y:%H:%M:%S %z")
    if not CUTOFF <= start < UNTIL:
        continue
    client = clients.setdefault(match[1], "client_" + str(len(clients) + 1))
    key = (match[3], match[4], match[5])
    candidates = [r for r in app if not r["used"] and r["key"] == key
                  and 0 <= (r["end"] - start).total_seconds() < 900]
    paired = min(candidates, key=lambda r: r["end"]) if candidates else None
    if paired:
        paired["used"] = True
    path = route(match[4])
    if path.startswith("/static/") or path == "/favicon.ico":
        continue
    requests.append({
        "start_utc": start.isoformat(), "app_headers_utc": paired["end"].isoformat() if paired else None,
        "method": match[3], "route": path, "status": int(match[5]), "response_wire_bytes": int(match[6]),
        "client_label": client, "approx_to_app_headers_seconds":
        round((paired["end"] - start).total_seconds(), 3) if paired else None,
    })
raw = subprocess.check_output(
    ["sudo", "tail", "-n", "250", "/var/log/apache2/dewey-error.log"], text=True)
errors = []
for line in raw.splitlines():
    if "Sep 23" not in line:
        continue
    stamp = re.match(r"^\[([^\]]+)\]", line)
    codes = re.findall(r"AH\d+", line)
    errors.append({"time": stamp[1] if stamp else None, "codes": codes,
                   "category": "backend_timeout" if "timeout" in line.lower() else "backend_error",
                   "registry_search": "/api/v1/registry/search" in line})
identity = json.loads(subprocess.check_output(["docker", "inspect", CONTAINER]))[0]
print(json.dumps({
    "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "scope": "Existing logs only; no requests replayed; no data or service mutation.",
    "method": "Match Apache request-start timestamp to application response-header timestamp by method, exact original URI and status. URI values and client addresses are never emitted.",
    "limitations": "Apache starts have one-second precision. Repeated identical request pairing can be ambiguous. No identity-to-client or role-to-client assertion is made.",
    "container": {"name": CONTAINER, "id": identity["Id"], "image": identity["Image"],
                  "started_at": identity["State"]["StartedAt"], "restart_count": identity["RestartCount"],
                  "oom_killed": identity["State"]["OOMKilled"]},
    "requests": requests, "proxy_errors": errors,
}, indent=2))
