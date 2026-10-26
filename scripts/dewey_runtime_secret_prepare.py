"""Prepare two new Dewey runtime secrets through the owning AWS service.

Run locally with the explicitly authorized lsmc operator profile. Passwords are
generated in memory and sent only to Secrets Manager, never files or stdout.
Existing names are a refusal. This does not create database roles or change IAM.
"""

import argparse
import datetime as dt
import json
from pathlib import Path
import secrets
import uuid

import boto3

CHOICES = {
    "production": ("/dayhoff/day/dewey/9.0.0/runtime", "dewey_runtime_9"),
    "rehearsal": ("/dayhoff/day/dewey/9.0.0/rehearsal-runtime-20260911", "dewey_rehearsal_9"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=tuple(CHOICES))
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if not args.receipt.is_absolute() or args.receipt.exists() or args.receipt.is_symlink():
        raise RuntimeError("Require a new exact absolute receipt file")
    client = boto3.Session(profile_name="lsmc").client("secretsmanager", region_name="us-west-2")
    name, role = CHOICES[args.target]
    try:
        client.describe_secret(SecretId=name)
    except client.exceptions.ResourceNotFoundException:
        pass
    else:
        raise RuntimeError("The named secret exists; inspect instead of overwriting")
    token = str(uuid.uuid4())
    result = client.create_secret(
        Name=name, ClientRequestToken=token,
        Description=f"Dewey9 {args.target} constrained TapDB runtime principal",
        SecretString=json.dumps({"username": role, "password": secrets.token_urlsafe(40)}),
        Tags=[{"Key": "Service", "Value": "dewey"}, {"Key": "Release", "Value": "9.0.0"},
              {"Key": "Purpose", "Value": args.target}],
    )
    receipt = {"created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "target": args.target,
               "role": role, "secret_name": name, "secret_arn": result["ARN"],
               "version_id": result["VersionId"], "client_request_token": token,
               "password_written_to_file_or_output": False, "database_role_changed": False}
    with args.receipt.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
