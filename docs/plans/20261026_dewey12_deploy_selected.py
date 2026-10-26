#!/usr/bin/env python3
"""Prepare/apply the exact Dewey-only Compose cutover with preservation receipts."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.open('x').write(json.dumps(value, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'apply'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    assert args.manifest.is_absolute() and args.manifest.parent == ROOT
    assert len(args.commit) == 40 and all(c in '0123456789abcdef' for c in args.commit)
    image = json.loads(args.manifest.read_text())['images']['dewey']['image']
    assert '@sha256:' in image
    metadata = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
    assert metadata['Config']['Labels']['org.opencontainers.image.revision'] == args.commit
    candidate = ROOT / 'compose-dewey.yml'
    receipt_path = ROOT / 'compose-dewey-prepare.json'
    if args.phase == 'prepare':
        assert sha(LIVE) == '416ba61b0c380aa6bb8c6610977cd5881172940077e48cc1f0d0148505acc24e'
        before = yaml.safe_load(LIVE.read_text())
        after = copy.deepcopy(before)
        selected = after['services']['dewey']
        selected['image'] = image
        selected['environment']['LSMC_RELEASE_SHA'] = args.commit
        selected['environment']['DEWEY_BUILD_SHA'] = args.commit
        target = selected['environment']['DEWEY_CONFIG']
        bindings = [v for v in selected['volumes'] if v['target'] == target]
        assert len(bindings) == 1 and bindings[0]['read_only'] is True
        bindings[0]['source'] = str(ROOT / 'dewey-config.yaml')
        assert Path(bindings[0]['source']).is_file()
        for name, value in before['services'].items():
            if name != 'dewey':
                assert value == after['services'][name]
        assert {k:v for k,v in before.items() if k != 'services'} == {k:v for k,v in after.items() if k != 'services'}
        (ROOT / 'compose-before-dewey.yml').open('xb').write(LIVE.read_bytes())
        candidate.open('x').write(yaml.safe_dump(after, sort_keys=False))
        subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(candidate), 'config', '--quiet'], check=True)
        receipt = {'source_sha256': sha(LIVE), 'candidate_sha256': sha(candidate), 'image': image,
                   'commit': args.commit, 'selected_service': 'dewey',
                   'unchanged_services': sorted(set(before['services']) - {'dewey'})}
        write(receipt_path, receipt)
    else:
        receipt = json.loads(receipt_path.read_text())
        assert receipt['commit'] == args.commit and receipt['image'] == image
        assert sha(LIVE) == receipt['source_sha256'] and sha(candidate) == receipt['candidate_sha256']
        migration = json.loads((ROOT / 'migration-verify.json').read_text())
        assert migration['status'] == 'verified' and migration['schema_version'] == 3
        assert migration['share_count'] == 42 and migration['retired'] == migration['deleted'] == 0
        old = json.loads(subprocess.check_output(['docker', 'inspect', 'dayhoff-day-dewey-1']))[0]
        assert not old['State']['Running']
        temp = LIVE.with_name(LIVE.name + '.dewey12-selected')
        temp.open('xb').write(candidate.read_bytes())
        temp.chmod(0o640)
        os.replace(temp, LIVE)
        started = datetime.now(timezone.utc).isoformat()
        with (ROOT / 'dewey-deploy.log').open('x') as output:
            result = subprocess.run(['docker', 'compose', '-p', 'dayhoff-day', '-f', str(LIVE), 'up', '-d',
                                     '--no-deps', '--no-build', '--pull', 'never', '--timeout', '60', 'dewey'],
                                    stdout=output, stderr=subprocess.STDOUT)
        receipt = {**receipt, 'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(),
                   'exit_code': result.returncode}
        write(ROOT / 'dewey-deploy-exit.json', receipt)
        assert result.returncode == 0
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
