#!/usr/bin/env python3
"""Install the reviewed recipient listeners and exact private Login assertion boundary."""
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
from pathlib import Path


def main():
    os.umask(0o077)
    root = Path("/home/ubuntu/dewey12-release-20261026T021700Z")
    spec = importlib.util.spec_from_file_location("recipient_ingress", root / "scripts/dewey_recipient_ingress.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = module.load_config(root / "docs/plans/20261026_dewey12_recipient_ingress.json")
    secrets = json.loads((root / "origin-secrets.json").read_text())
    private_login = Path("/etc/apache2/sites-enabled/lsmc-oauth-login-day.conf").resolve(strict=True)
    previous = private_login.read_text()
    candidate_login = (root / "login-private-origin.conf").read_text()
    assert module.render_private_login(config, secrets, previous) == candidate_login
    candidate = (root / "dewey12-recipient.conf").read_text()
    assert module.render_origin(config, secrets) == candidate
    destination = Path("/etc/apache2/sites-available/dewey12-recipient.conf")
    enabled = Path("/etc/apache2/sites-enabled/dewey12-recipient.conf")
    assert not destination.exists() and not enabled.exists() and not enabled.is_symlink()
    for port in (8443, 8444):
        with socket.socket() as sock:
            sock.bind((config["private_ip"], port))
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in Path("/etc/apache2/sites-enabled").iterdir() if p.is_file()}
    (root / "apache-before.json").open("x").write(json.dumps(before, indent=2))
    (root / "login-origin-before.conf").open("x").write(previous)
    destination.open("x").write(candidate)
    destination.chmod(0o600)
    temporary = private_login.with_name(private_login.name + ".dewey12-new")
    temporary.open("x").write(candidate_login)
    temporary.chmod(0o600)
    os.replace(temporary, private_login)
    enabled.symlink_to(destination)
    with (root / "apache-configtest.log").open("x") as output:
        checked = subprocess.run(["apache2ctl", "configtest"], stdout=output, stderr=subprocess.STDOUT)
    if checked.returncode:
        # Restore only this attempted installation; leave the running configuration untouched.
        private_login.write_text(previous)
        enabled.unlink()
        destination.unlink()
        raise RuntimeError("Apache rejected candidate; selected files restored without reload")
    with (root / "apache-graceful.log").open("x") as output:
        subprocess.run(["apache2ctl", "-k", "graceful"], stdout=output, stderr=subprocess.STDOUT, check=True)
    untouched = [path for path, checksum in before.items()
                 if Path(path).resolve() != private_login
                 and hashlib.sha256(Path(path).read_bytes()).hexdigest() == checksum]
    assert len(untouched) == len(before) - 1
    receipt = {"installed": str(destination), "private_login": str(private_login),
               "new_listeners": [8443, 8444], "shared_443_retained": True,
               "unchanged_other_site_configs": untouched, "configtest": "pass", "reload": "graceful"}
    (root / "origin-install.json").open("x").write(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
