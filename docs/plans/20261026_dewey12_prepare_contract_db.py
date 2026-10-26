#!/usr/bin/env python3
"""Prepare a new, isolated local native TapDB contract target via supported CLI."""
import argparse
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from uuid import uuid4

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--postgres-bin", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resume-phase", choices=("schema", "seed", "verify"), default="schema")
    args = parser.parse_args()
    if not all(p.is_absolute() for p in (args.root, args.repo, args.postgres_bin)) or (args.root.exists() and not args.resume):
        parser.error("Use explicit absolute paths and a new isolated root")
    with socket.socket() as probe:
        running = probe.connect_ex(("127.0.0.1", 54389)) == 0
    if running and not args.resume:
        parser.error("Dedicated contract port 54389 is occupied")
    args.root.mkdir(mode=0o700, exist_ok=args.resume)
    seed = args.root / "templates"
    seed.mkdir(exist_ok=args.resume)
    seed_app = seed / "dewey"
    seed_app.mkdir(exist_ok=args.resume)
    shutil.copyfile(args.repo / "config/tapdb_templates/dewey/templates.json", seed_app / "templates.json")
    # The application registry intentionally contains only Dewey's allocation.
    # A fresh native database also needs TapDB's core allocation registry.
    # Copy both into this isolated fixture; never alter either source registry.
    import daylily_tapdb
    native_etc = Path(daylily_tapdb.__file__).parent / "etc"
    domains = json.loads((args.repo / "dewey_service/etc/domain_code_registry.json").read_text())
    prefixes = json.loads((native_etc / "prefix_ownership_registry.json").read_text())
    application_prefixes = json.loads((args.repo / "dewey_service/etc/prefix_ownership_registry.json").read_text())
    for domain, entries in application_prefixes["ownership"].items():
        for prefix, owner in entries.items():
            if prefix in prefixes["ownership"].setdefault(domain, {}) and prefixes["ownership"][domain][prefix] != owner:
                parser.error("Conflicting native/application allocation registry")
            prefixes["ownership"][domain][prefix] = owner
    domain_registry = args.root / "domain_code_registry.json"
    prefix_registry = args.root / "prefix_ownership_registry.json"
    domain_registry.write_text(json.dumps(domains, indent=2) + "\n")
    prefix_registry.write_text(json.dumps(prefixes, indent=2) + "\n")
    config = args.root / "tapdb.yaml"
    if args.resume:
        previous = yaml.safe_load(config.read_text())
        if previous["target"]["database"] != "dewey12_contract" or previous["target"]["host"] != "localhost" or str(previous["target"]["port"]) != "54389":
            parser.error("Resume target does not match the isolated contract database")
    config.write_text(yaml.safe_dump({"meta": {"config_version": 4, "client_id": "dewey12test",
        "database_name": "dewey12_contract", "owner_repo_name": "dewey", "domain_code": "Z",
        "domain_registry_path": str(domain_registry),
        "prefix_ownership_registry_path": str(prefix_registry)},
        "target": {"domain_code": "Z", "engine_type": "local", "host": "localhost", "port": "54389", "ui_port": "54390",
        "database": "dewey12_contract", "schema_name": "tapdb_dewey", "user": "dewey12_runtime",
        "password": "", "operator": {"user": "dewey12_operator", "password": ""}, "audit_log_euid_prefix": "DGX",
        "unix_socket_dir": str(args.root / "socket"), "region": "us-west-2", "allow_global_claims": True},
        "safety": {"safety_tier": "local", "destructive_operations": "confirm_required"}}))
    config.chmod(0o600)
    attribution = args.root / "attribution.json"
    attribution.write_text(json.dumps({"actor_kind": "service", "actor_issuer": "dewey12-contract",
        "actor_subject": "approved-release-contract-tests", "service_identity": "dewey",
        "request_id": str(uuid4()), "operation_id": "dewey12-contract-bootstrap"}))
    attribution.chmod(0o600)
    env = dict(os.environ, PATH=str(args.postgres_bin) + os.pathsep + os.environ["PATH"],
               XDG_STATE_HOME=str(args.root / "state"))
    cli = str(args.repo / ".venv/bin/tapdb")
    base = [cli, "--config", str(config)]
    commands = ([] if args.resume else [["pg", "init"], ["pg", "start-local"], ["db", "create"]])
    if args.resume and not running:
        parser.error("Resume requires the retained isolated PostgreSQL instance to be running")
    commands += [["pg", "status"]]
    if not args.resume or args.resume_phase == "schema":
        commands.append(["db", "schema", "apply"])
    if not args.resume or args.resume_phase in {"schema", "seed"}:
        commands.append(["db", "data", "seed", "--config", str(seed), "--include-workflow", "--skip-existing"])
    commands.append(["db", "schema", "status"])
    with (args.root / "bootstrap.log").open("a" if args.resume else "x") as log:
        for command in commands:
            log.write("COMMAND " + " ".join(base + command) + "\n"); log.flush()
            subprocess.run(base + command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        from daylily_tapdb import TemplateManager
        from daylily_tapdb.cli.context import set_cli_context
        from daylily_tapdb.web.runtime import get_db
        from dewey_service.tapdb_backend import TEMPLATE_DEFINITIONS
        set_cli_context(config_path=str(config))
        connection = get_db(str(config))
        connection.app_username = "dewey12-contract-bootstrap"
        from daylily_tapdb.security_context import Attribution
        connection.attribution = Attribution(**json.loads(attribution.read_text()))
        with connection.session_scope(commit=False) as session:
            manager = TemplateManager()
            missing = [code for code in TEMPLATE_DEFINITIONS if manager.get_template(session, code, domain_code="Z") is None]
            if missing:
                raise RuntimeError("Native fixture is missing templates: " + ", ".join(missing))
        log.write("READINESS Native runtime connection and all Dewey templates verified\n")
    print(json.dumps({"config": str(config), "state_home": env["XDG_STATE_HOME"],
        "dsn": "postgresql://dewey12_runtime@localhost:54389/dewey12_contract",
        "log": str(args.root / "bootstrap.log")}))


if __name__ == "__main__":
    main()
