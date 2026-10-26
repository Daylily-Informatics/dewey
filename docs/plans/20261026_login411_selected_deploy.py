#!/usr/bin/env python3
"""Apply the reviewed Login 4.1.1 correction, preserving all other services."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path('/home/ubuntu/dewey12-release-20261026T021700Z')
LIVE = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
MANIFEST = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
BEFORE_SHA = 'a89a5f72035f81ba2689450229eb865713299da094ebdd116d4bb7f85f3f5641'
MANIFEST_SHA = '6bb966982c88dc5a964825d13809e1e45e3ab5b70cca1c4df55c0f5117cb1efd'
CONTAINER_ID = 'c4b81adc70f0258f76a31e535029b7b64c4911b5e7550afb20aee73344eb5c7b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(*args):
    return json.loads(subprocess.check_output(['docker', *args]))[0]


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'apply', 'manifest'))
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    assert len(args.commit) == 40 and all(c in '0123456789abcdef' for c in args.commit)
    previous = json.loads((ROOT / 'manifest-12.0.3.json').read_text())
    current = json.loads((ROOT / 'manifest-login-4.1.1.json').read_text())
    expected = copy.deepcopy(previous)
    expected['images']['lsmc-oauth-login'] = current['images']['lsmc-oauth-login']
    assert expected == current
    selected = current['images']['lsmc-oauth-login']
    assert selected['source_commit'] == args.commit and selected['source_tag'] == '4.1.1'
    metadata = inspect('image', 'inspect', selected['image'])
    labels = metadata['Config']['Labels']
    assert labels['org.opencontainers.image.revision'] == args.commit
    assert labels['org.opencontainers.image.version'] == '4.1.1'
    candidate = ROOT / 'compose-login-4.1.1.yml'
    prepared = ROOT / 'compose-login-4.1.1-prepare.json'
    if args.phase == 'prepare':
        assert sha(LIVE) == BEFORE_SHA and sha(MANIFEST) == MANIFEST_SHA
        before = yaml.safe_load(LIVE.read_text())
        after = copy.deepcopy(before)
        service = after['services']['login']
        service['image'] = selected['image']
        service['environment']['LSMC_RELEASE_SHA'] = args.commit
        restored = copy.deepcopy(after)
        restored['services']['login']['image'] = before['services']['login']['image']
        restored['services']['login']['environment']['LSMC_RELEASE_SHA'] = before['services']['login']['environment']['LSMC_RELEASE_SHA']
        assert restored == before
        (ROOT / 'compose-before-login-4.1.1.yml').open('xb').write(LIVE.read_bytes())
        candidate.open('x').write(yaml.safe_dump(after, sort_keys=False))
        subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(candidate), 'config', '--quiet'], check=True)
        receipt = {'source_sha256': sha(LIVE), 'candidate_sha256': sha(candidate),
                   'image': selected['image'], 'commit': args.commit, 'version': '4.1.1',
                   'selected_service': 'login', 'only_changed_fields': ['image', 'LSMC_RELEASE_SHA'],
                   'unchanged_services': sorted(set(before['services']) - {'login'})}
        write(prepared, receipt)
    elif args.phase == 'apply':
        receipt = json.loads(prepared.read_text())
        assert receipt['commit'] == args.commit and receipt['image'] == selected['image']
        assert sha(LIVE) == BEFORE_SHA and sha(candidate) == receipt['candidate_sha256']
        assert sha(MANIFEST) == MANIFEST_SHA
        old = inspect('inspect', 'dayhoff-day-login-1')
        assert old['Id'] == CONTAINER_ID and old['State']['Running']
        started = datetime.now(timezone.utc).isoformat()
        with (ROOT / 'login-deploy-4.1.1.log').open('x') as output:
            subprocess.run(['docker', 'stop', '--time', '-1', CONTAINER_ID], stdout=output, stderr=subprocess.STDOUT, check=True)
            stopped = inspect('inspect', CONTAINER_ID)
            assert not stopped['State']['Running'] and stopped['State']['ExitCode'] == 0
            temp = LIVE.with_name(LIVE.name + '.login-4.1.1-selected')
            temp.open('xb').write(candidate.read_bytes())
            temp.chmod(0o640)
            os.replace(temp, LIVE)
            result = subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(LIVE), 'up', '-d',
                                     '--no-deps', '--no-build', '--pull', 'never', 'login'],
                                    stdout=output, stderr=subprocess.STDOUT)
        receipt.update(started_at=started, finished_at=datetime.now(timezone.utc).isoformat(),
                       exit_code=result.returncode, previous_exit_code=stopped['State']['ExitCode'])
        write(ROOT / 'login-deploy-4.1.1-exit.json', receipt)
        assert result.returncode == 0
    else:
        receipt = json.loads(prepared.read_text())
        assert receipt['commit'] == args.commit
        assert sha(LIVE) == receipt['candidate_sha256'] and sha(MANIFEST) == MANIFEST_SHA
        for role, entry in current['images'].items():
            name = {'lsmc-oauth-login': 'login', 'zebra_day': 'zebra-day'}.get(role, role)
            container = inspect('inspect', 'dayhoff-day-' + name + '-1')
            assert container['State']['Running'] and container['Config']['Image'] == entry['image'], role
        (ROOT / 'manifest-before-login-4.1.1.json').open('xb').write(MANIFEST.read_bytes())
        temp = MANIFEST.with_name(MANIFEST.name + '.login-4.1.1-selected')
        temp.open('xb').write((ROOT / 'manifest-login-4.1.1.json').read_bytes())
        temp.chmod(0o640)
        os.replace(temp, MANIFEST)
        receipt = {'previous_sha256': MANIFEST_SHA, 'installed_sha256': sha(MANIFEST), 'matched_running_images': 8}
        write(ROOT / 'manifest-install-login-4.1.1.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
