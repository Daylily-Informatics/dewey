#!/usr/bin/env python3
"""Exact, selected 12.0.2 -> 12.0.3 deployment; no database or sibling changes."""
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
COMMIT = 'a5d6c05df2337a9b87dff1ab19c0b109f910a986'
BEFORE_SHA = '74dc32111e0f1cc7840e82d1ba4fe8021498725bae0cb5b47392109d5c0dfe30'
MANIFEST_SHA = '5470c88942a8a758da177bcb5b58bce7b7ef97aeee28f0b23fb4e1cc02fcafeb'
CONTAINER_ID = 'c7ad8ffeebdee1c1d7c7baea9bb7597735d45e9455c6e42dbe62e32229505cf0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'apply', 'manifest'))
    args = parser.parse_args()
    os.umask(0o077)
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    previous = json.loads((ROOT / 'manifest-12.0.2.json').read_text())
    current = json.loads((ROOT / 'manifest-12.0.3.json').read_text())
    assert previous.keys() == current.keys()
    assert previous['images'].keys() == current['images'].keys()
    assert [k for k in previous['images'] if previous['images'][k] != current['images'][k]] == ['dewey']
    assert {k:v for k,v in previous.items() if k != 'images'} == {k:v for k,v in current.items() if k != 'images'}
    selected = current['images']['dewey']
    assert selected['source_commit'] == COMMIT and selected['source_tag'] == '12.0.3'
    metadata = json.loads(subprocess.check_output(['docker', 'image', 'inspect', selected['image']]))[0]
    labels = metadata['Config']['Labels']
    assert labels['org.opencontainers.image.revision'] == COMMIT
    assert labels['org.opencontainers.image.version'] == '12.0.3'
    candidate = ROOT / 'compose-dewey-12.0.3.yml'
    prepared = ROOT / 'compose-dewey-12.0.3-prepare.json'
    if args.phase == 'prepare':
        assert sha(LIVE) == BEFORE_SHA and sha(MANIFEST) == MANIFEST_SHA
        before = yaml.safe_load(LIVE.read_text())
        after = copy.deepcopy(before)
        service = after['services']['dewey']
        service['image'] = selected['image']
        service['environment']['DEWEY_BUILD_SHA'] = COMMIT
        service['environment']['LSMC_RELEASE_SHA'] = COMMIT
        check = copy.deepcopy(after)
        for key in ('DEWEY_BUILD_SHA', 'LSMC_RELEASE_SHA'):
            check['services']['dewey']['environment'][key] = before['services']['dewey']['environment'][key]
        check['services']['dewey']['image'] = before['services']['dewey']['image']
        assert check == before
        (ROOT / 'compose-before-12.0.3.yml').open('xb').write(LIVE.read_bytes())
        candidate.open('x').write(yaml.safe_dump(after, sort_keys=False))
        subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(candidate), 'config', '--quiet'], check=True)
        receipt = {'source_sha256': sha(LIVE), 'candidate_sha256': sha(candidate),
                   'image': selected['image'], 'commit': COMMIT, 'version': '12.0.3',
                   'selected_service': 'dewey', 'only_changed_fields': ['image', 'DEWEY_BUILD_SHA', 'LSMC_RELEASE_SHA'],
                   'unchanged_services': sorted(set(before['services']) - {'dewey'})}
        write(prepared, receipt)
    elif args.phase == 'apply':
        receipt = json.loads(prepared.read_text())
        assert sha(LIVE) == BEFORE_SHA and sha(candidate) == receipt['candidate_sha256']
        assert sha(MANIFEST) == MANIFEST_SHA
        old = json.loads(subprocess.check_output(['docker', 'inspect', 'dayhoff-day-dewey-1']))[0]
        assert old['Id'] == CONTAINER_ID and old['State']['Running']
        started = datetime.now(timezone.utc).isoformat()
        with (ROOT / 'dewey-deploy-12.0.3.log').open('x') as output:
            subprocess.run(['docker', 'stop', '--time', '-1', CONTAINER_ID], stdout=output, stderr=subprocess.STDOUT, check=True)
            stopped = json.loads(subprocess.check_output(['docker', 'inspect', CONTAINER_ID]))[0]
            assert not stopped['State']['Running'] and stopped['State']['ExitCode'] == 0
            temp = LIVE.with_name(LIVE.name + '.12.0.3-selected')
            temp.open('xb').write(candidate.read_bytes())
            temp.chmod(0o640)
            os.replace(temp, LIVE)
            result = subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(LIVE), 'up', '-d',
                                     '--no-deps', '--no-build', '--pull', 'never', 'dewey'],
                                    stdout=output, stderr=subprocess.STDOUT)
        receipt.update(started_at=started, finished_at=datetime.now(timezone.utc).isoformat(),
                       exit_code=result.returncode, previous_exit_code=stopped['State']['ExitCode'])
        write(ROOT / 'dewey-deploy-12.0.3-exit.json', receipt)
        assert result.returncode == 0
    else:
        receipt = json.loads(prepared.read_text())
        assert sha(LIVE) == receipt['candidate_sha256'] and sha(MANIFEST) == MANIFEST_SHA
        for role, entry in current['images'].items():
            name = {'lsmc-oauth-login':'login', 'zebra_day':'zebra-day'}.get(role, role)
            container = json.loads(subprocess.check_output(['docker', 'inspect', 'dayhoff-day-' + name + '-1']))[0]
            assert container['State']['Running'] and container['Config']['Image'] == entry['image'], role
        (ROOT / 'manifest-before-12.0.3.json').open('xb').write(MANIFEST.read_bytes())
        temp = MANIFEST.with_name(MANIFEST.name + '.12.0.3-selected')
        temp.open('xb').write((ROOT / 'manifest-12.0.3.json').read_bytes())
        temp.chmod(0o640)
        os.replace(temp, MANIFEST)
        receipt = {'previous_sha256': MANIFEST_SHA, 'installed_sha256': sha(MANIFEST), 'matched_running_images': 8}
        write(ROOT / 'manifest-install-12.0.3.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
