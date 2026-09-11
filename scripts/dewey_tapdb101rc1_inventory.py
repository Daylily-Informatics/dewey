"""Run the reviewed native RC discovery commands from interactive EC2 ubuntu.

Read-only database operations. Full native output stays in the private operator
directory; only the operation result is displayed. This is discovery, not final
fenced evidence or permission to migrate. Existing outputs are never overwritten.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import os
from pathlib import Path
import pwd
import subprocess
import time

ROOT = Path("/home/ubuntu/dewey_ops/tapdb101-20260911")
CONFIG = ROOT / "source-operator.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("census", "inventory"))
    args = parser.parse_args()
    os.umask(0o077)
    if pwd.getpwuid(os.geteuid()).pw_name != "ubuntu":
        raise RuntimeError("Run from the approved interactive ubuntu SSM session")
    if importlib.metadata.version("daylily-tapdb") != "10.1.1rc1":
        raise RuntimeError("The operator must run exactly TapDB 10.1.1rc1")
    stem = f"source-{args.operation}-10.1.1rc1"
    receipt = ROOT / "receipts" / f"{stem}.json"
    log = ROOT / "logs" / f"{stem}.log"
    result = ROOT / "receipts" / f"{stem}-execution.json"
    if any(path.exists() or path.is_symlink() for path in (receipt, log, result)):
        raise RuntimeError("A reviewed output already exists; inspect before retry")
    command = [
        "sudo", "env", "AWS_PROFILE=lsmc", "AWS_REGION=us-west-2",
        "AWS_CONFIG_FILE=/home/ubuntu/.aws/config",
        "AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials",
        "PYTHONDONTWRITEBYTECODE=1", str(ROOT / "venv/bin/tapdb"),
        "--config", str(CONFIG), "--json", "db",
    ]
    if args.operation == "census":
        command.extend([
            "census", "--database", "dewey_prod_tapdb10",
            "--statement-timeout-ms", "10000", "--max-catalog-rows", "100000",
        ])
    else:
        command.extend(["identity", "inventory", "--source-version", "9.0.9"])
    command.extend(["--receipt", str(receipt)])
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    clock = time.monotonic()
    with log.open("x", encoding="utf-8") as output:
        completed = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    summary = {
        "operation": args.operation, "command": command, "started_at": started,
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.monotonic() - clock, 3),
        "returncode": completed.returncode, "receipt_exists": receipt.exists(),
        "receipt": str(receipt), "log": str(log),
        "production_mutation_authorized": False,
    }
    with result.open("x", encoding="utf-8") as output:
        json.dump(summary, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(summary, sort_keys=True), flush=True)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
