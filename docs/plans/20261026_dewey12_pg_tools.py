#!/usr/bin/env python3
"""Fetch signed PGDG bookworm client tools for native backup operator use only."""
import argparse
import gzip
import hashlib
import json
import re
import subprocess
import urllib.request
from pathlib import Path

BASE = "https://apt.postgresql.org/pub/repos/apt/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory
    assert root.is_absolute() and not root.exists()
    root.mkdir(mode=0o700)

    def fetch(url, name):
        data = urllib.request.urlopen(url, timeout=60).read()
        (root / name).open("xb").write(data)
        return data

    key = fetch("https://www.postgresql.org/media/keys/ACCC4CF8.asc", "pgdg.asc")
    del key
    subprocess.run(["gpg", "--batch", "--dearmor", "--output", str(root / "pgdg.gpg"), str(root / "pgdg.asc")], check=True)
    release = fetch(BASE + "dists/bookworm-pgdg/InRelease", "InRelease")
    subprocess.run(["gpgv", "--keyring", str(root / "pgdg.gpg"), str(root / "InRelease")], check=True)
    entries = re.findall(r"^\s+([0-9a-f]{64})\s+(\d+)\s+(\S+)$", release.decode(), re.M)
    checksum, size, _ = next(row for row in entries if row[2] == "main/binary-amd64/Packages.gz")
    packages = fetch(BASE + "dists/bookworm-pgdg/main/binary-amd64/Packages.gz", "Packages.gz")
    assert len(packages) == int(size) and hashlib.sha256(packages).hexdigest() == checksum
    rows = []
    for stanza in gzip.decompress(packages).decode().split("\n\n"):
        row = dict(line.split(": ", 1) for line in stanza.splitlines() if ": " in line and not line.startswith(" "))
        if row.get("Package") in {"postgresql-client-16", "libpq5"} and row.get("Architecture") == "amd64":
            if not re.search(r"(?:alpha|beta|rc)", row["Version"]):
                rows.append(row)
    selected = []
    for name in ("postgresql-client-16", "libpq5"):
        candidates = [row for row in rows if row["Package"] == name]
        assert candidates, "Required signed package absent"
        chosen = candidates[0]
        for row in candidates[1:]:
            if subprocess.run(["dpkg", "--compare-versions", row["Version"], "gt", chosen["Version"]]).returncode == 0:
                chosen = row
        filename = Path(chosen["Filename"]).name
        data = fetch(BASE + chosen["Filename"], filename)
        assert hashlib.sha256(data).hexdigest() == chosen["SHA256"]
        selected.append({key: chosen[key] for key in ("Package", "Version", "Architecture", "Filename", "SHA256", "Depends")})
        subprocess.run(["dpkg-deb", "-x", str(root / filename), str(root / "tools")], check=True)
    receipt = {"source": BASE, "distribution": "bookworm-pgdg", "signature_verified": True,
               "inrelease_sha256": hashlib.sha256(release).hexdigest(), "packages_sha256": checksum,
               "selected": selected, "installed_system_packages": False, "container_image_changed": False}
    (root / "receipt.json").open("x").write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
