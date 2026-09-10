"""Focused generated-Compose mutation boundaries; no Docker or AWS calls."""

import importlib.util
from pathlib import Path

import pytest
import yaml

spec = importlib.util.spec_from_file_location(
    "resolver_deploy", Path(__file__).parents[1] / "scripts/deploy_qeo_resolver.py"
)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def test_replaces_only_dewey_and_preserves_surrounding_bytes():
    before = (
        b"name: dayhoff-day\nservices:\n  qeo:\n    image: qeo-exact\n"
        b"  dewey:\n    image: old\n    environment:\n      PRESERVE: original\n"
        b"  kahlo:\n    image: kahlo-exact\nnetworks:\n  default: {}\n"
    )
    service = {"image": "new", "environment": {"PRESERVE": "original", "NEW": "digest-only"}}
    after = deploy.replace_dewey(before, service)
    assert after.split(b"  dewey:")[0] == before.split(b"  dewey:")[0]
    assert after.split(b"  kahlo:")[1] == before.split(b"  kahlo:")[1]
    expected = yaml.safe_load(before)
    expected["services"]["dewey"] = service
    assert yaml.safe_load(after) == expected


@pytest.mark.parametrize(
    "base",
    [
        b"services:\n  qeo: {}\n",
        b"services: {dewey: {image: old}}\n",
        b"services:\n  dewey:\n    image: first\n  dewey:\n    image: second\n",
    ],
)
def test_ambiguous_or_unexpected_layout_rejected(base):
    with pytest.raises(ValueError):
        deploy.replace_dewey(base, {"image": "new"})


def test_backups_are_private_and_never_overwritten(tmp_path):
    path = tmp_path / "backup"
    deploy.private_write(path, b"original")
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        deploy.private_write(path, b"replacement")
    assert path.read_bytes() == b"original"
