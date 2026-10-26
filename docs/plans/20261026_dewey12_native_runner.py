#!/usr/bin/env python3
"""Run a native command in a final selected image with frozen production bindings.

All runtime details and command output stay in the private EC2 release directory.
This helper never builds images or starts/restarts Compose services.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--service", choices=("dewey", "login"), required=True)
    parser.add_argument("--prepared", action="store_true")
    parser.add_argument("--operator", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.umask(0o077)
    assert args.root.is_absolute() and args.output.is_absolute() and args.output.parent == args.root
    assert args.command and args.command[0] in ("dewey", "tapdb", "lsmc-login", "python")
    assert not args.output.exists()
    snapshot = json.loads((args.root / "frozen-selected-containers.json").read_text())[args.service]
    assert args.manifest.is_absolute() and args.manifest.is_file()
    manifest = json.loads(args.manifest.read_text())
    role = "dewey" if args.service == "dewey" else "lsmc-oauth-login"
    image = manifest["images"][role]["image"]
    assert "@sha256:" in image
    env_file = args.root / (args.service + "-oneoff.env")
    environment = snapshot["Config"]["Env"]
    assert all("\n" not in value and "\r" not in value for value in environment)
    if env_file.exists():
        assert env_file.read_text() == "\n".join(environment) + "\n"
    else:
        env_file.open("x").write("\n".join(environment) + "\n")
    command = ["docker", "run", "--rm", "--pull=never", "--network=host", "--user=0:0",
               "--env-file", str(env_file), "--entrypoint", "/app/.venv/bin/" + args.command[0]]
    mounts = {item["Destination"]: (item["Source"], not item["RW"]) for item in snapshot["Mounts"]}
    assert all(item["Type"] == "bind" for item in snapshot["Mounts"])
    mounts[str(args.root)] = (str(args.root), False)
    if args.prepared:
        target = next(value.split("=", 1)[1] for value in environment if value.startswith(
            "DEWEY_CONFIG=" if args.service == "dewey" else "LSMC_OAUTH_LOGIN_CONFIG="))
        mounts[target] = (str(args.root / (args.service + "-config.yaml")), True)
    if args.operator:
        assert args.service == "dewey"
        for path, readonly in (
            ("/home/ubuntu/dewey-sharing-20261004T000136Z/operator.yaml", True),
            ("/home/ubuntu/dayhoff-tapdb11-fleet-20261001T205909Z/backups/dewey", False),
            ("/home/ubuntu/dewey_ops/tapdb101-20260911/receipts/final-native-journal", False),
        ):
            mounts[path] = (path, readonly)
    for target, (source, readonly) in mounts.items():
        assert Path(source).exists(), "Required binding missing: " + source
        command += ["--mount", "type=bind,src=" + source + ",dst=" + target + (",readonly" if readonly else "")]
    for host in snapshot["HostConfig"].get("ExtraHosts") or []:
        command += ["--add-host", host]
    command += [image, *args.command[1:]]
    with args.output.open("x") as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=False)
    receipt = {"service": args.service, "image": image, "exit_code": result.returncode,
               "output": str(args.output), "prepared_configuration": args.prepared}
    args.output.with_suffix(args.output.suffix + ".exit.json").open("x").write(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
