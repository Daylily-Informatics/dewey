"""Read-only Dewey source drain and host-writer census for the approved SOP.

Use the released public operator connection, with an explicit read-only
transaction. Only projected queue/expiry metadata is selected. No bearer upload
material, payloads, credentials, database changes or storage mutations occur.
"""

from collections import Counter
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess

from daylily_tapdb.cli.db_config import get_db_config
from daylily_tapdb.runtime_principal import operator_connection
from sqlalchemy import text

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def write(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def main():
    os.umask(0o077)
    if os.geteuid() != 0 or os.environ.get("SUDO_USER") != "ubuntu":
        raise RuntimeError("Use targeted sudo from interactive ubuntu")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("Wrong operator package")
    output = ROOT / "receipts/writer-census-20260911.json"
    detail = ROOT / "receipts/writer-drain-private-20260911.json"
    if output.exists() or detail.exists():
        raise RuntimeError("Census evidence exists; preserve it")
    cfg = get_db_config(config_path=ROOT / "source-operator.yaml")
    expected = {"engine_type": "aurora", "database": "dewey_prod", "schema_name": "tapdb_dewey_lsmcok1_local",
                "domain_code": "M", "operator_user": "dayhoff", "cluster_identifier": "dayhoff-lsmcok1-tapdb",
                "host": "dayhoff-lsmcok1-tapdb.cluster-ch4mq8a6wcdf.us-west-2.rds.amazonaws.com"}
    if any(cfg.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Source configuration differs from the approved Dewey target")
    with operator_connection(cfg, read_only=True) as connection:
        physical = dict(connection.execute(text("SELECT oid::bigint AS oid, pg_get_userbyid(datdba) AS owner FROM pg_catalog.pg_database WHERE datname=current_database()")).mappings().one())
        if physical != {"oid": 16749, "owner": "dayhoff"}:
            raise RuntimeError("Source physical identity differs from the approved census")
        queue = [dict(row) for row in connection.execute(text("""
            SELECT i.euid, i.json_addl->>'dispatch_status' AS dispatch_status,
                   i.json_addl->>'status' AS status,
                   i.json_addl->>'local_only' AS local_only,
                   i.json_addl->>'event_type' AS event_type,
                   i.json_addl->>'dispatch_attempt_count' AS dispatch_attempt_count,
                   i.json_addl->>'occurred_at' AS occurred_at
              FROM tapdb_dewey_lsmcok1_local.generic_instance i
              JOIN tapdb_dewey_lsmcok1_local.generic_template t ON t.uid=i.template_uid
             WHERE t.category='system' AND t.type='outbox_event'
               AND t.subtype='generic' AND t.version='1.0'
               AND i.domain_code='M' AND i.is_deleted=false
             ORDER BY i.uid
        """)).mappings()]
        uploads = [dict(row) for row in connection.execute(text("""
            SELECT i.euid, i.json_addl->'response'->>'created_at' AS created_at,
                   i.json_addl->'response'->>'expires_in' AS expires_in
              FROM tapdb_dewey_lsmcok1_local.generic_instance i
              JOIN tapdb_dewey_lsmcok1_local.generic_template t ON t.uid=i.template_uid
             WHERE t.category='system' AND t.type='idempotency_request'
               AND t.subtype='generic' AND t.version='1.0'
               AND i.domain_code='M' AND i.is_deleted=false
               AND i.json_addl->>'operation'='artifact.upload_session.create'
             ORDER BY i.uid
        """)).mappings()]
    now = dt.datetime.now(dt.timezone.utc)
    malformed = []
    unexpired = []
    expirations = []
    for row in uploads:
        try:
            created = dt.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            if created.tzinfo is None:
                raise ValueError("Missing timezone")
            seconds = int(row["expires_in"])
            if seconds <= 0:
                raise ValueError("Nonpositive expiry")
            expires = created + dt.timedelta(seconds=seconds)
            expirations.append(expires)
            if expires > now:
                unexpired.append({"euid": row["euid"], "expires_at": expires.isoformat()})
        except (TypeError, ValueError, AttributeError, OverflowError):
            malformed.append(row["euid"])
    processes = []
    proc_errors = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit() or int(path.name) == os.getpid():
            continue
        try:
            cmd = (path / "cmdline").read_bytes()
            if b"dewey" not in cmd.lower() and b"tapdb" not in cmd.lower():
                continue
            status = (path / "status").read_text()
            processes.append({"pid": int(path.name), "command_sha256": hashlib.sha256(cmd).hexdigest(),
                              "comm": (path / "comm").read_text().strip(),
                              "uid": next(line.split()[1] for line in status.splitlines() if line.startswith("Uid:")),
                              "operator_capsule": bytes(str(ROOT), "utf-8") in cmd})
        except FileNotFoundError:
            proc_errors.append({"pid": int(path.name), "reason": "process exited during census"})
    cron = []
    for user in ("ubuntu", "root"):
        result = subprocess.run(["crontab", "-u", user, "-l"], capture_output=True, text=True)
        if result.returncode and "no crontab for" not in result.stderr:
            raise RuntimeError("Unable to inspect explicit crontab")
        for index, line in enumerate(result.stdout.splitlines(), 1):
            if line.strip() and not line.lstrip().startswith("#") and any(name in line.lower() for name in ("dewey", "tapdb")):
                cron.append({"user": user, "line": index, "command_sha256": hashlib.sha256(line.encode()).hexdigest()})
    timers = command(["systemctl", "list-timers", "--all", "--no-pager", "--no-legend"])
    units = command(["systemctl", "list-units", "--all", "--type=service", "--no-pager", "--no-legend"])
    containers = [json.loads(line) for line in command(["docker", "ps", "--no-trunc", "--format", "{{json .}}"] ).splitlines()]
    container_index = [{key: row[key] for key in ("ID", "Names", "Image", "Status", "Ports")} for row in containers]
    write(detail, {"queue": queue, "upload_expirations": uploads, "malformed_upload_euids": malformed,
                   "unexpired_uploads": unexpired})
    summary = {
        "captured_at": now.isoformat(), "purpose": "Read-only writer/drain census; not proof of exclusion",
        "source_physical": physical,
        "queue_rows": len(queue),
        "queue_state_counts": dict(Counter(json.dumps([row["dispatch_status"], row["status"], row["local_only"]]) for row in queue)),
        "queue_event_type_counts": dict(Counter(row["event_type"] or "<missing>" for row in queue)),
        "upload_create_rows": len(uploads), "malformed_upload_expiry_count": len(malformed),
        "unexpired_upload_count": len(unexpired), "latest_upload_expiry": max(expirations).isoformat() if expirations else None,
        "processes": processes, "process_races": proc_errors, "matching_crontabs": cron,
        "matching_timers": [line for line in timers.splitlines() if "dewey" in line.lower() or "tapdb" in line.lower()],
        "matching_services": [line for line in units.splitlines() if "dewey" in line.lower() or "tapdb" in line.lower()],
        "containers": container_index, "private_detail": str(detail),
        "private_detail_sha256": hashlib.sha256(detail.read_bytes()).hexdigest(),
        "limitations": ["External operator/client admission must be controlled by the outage SOP", "An upload begun before expiry can complete after expiry", "Pending old-layout events remain preserved; census never relabels or dispatches them"],
    }
    write(output, summary)
    print(json.dumps(summary, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
