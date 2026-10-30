"""Run only the selected final Dewey multiqc-delivery build or native Compose deployment.

Release helper for the user-authorized report navigation/plot correction.
No hashes, readbacks, health probes, image audits, or sibling inventories.
Private build inputs and native build stdout never reach this runner's stdout.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

import yaml

PRIOR = Path('/home/ubuntu/dewey-scoped-expiry-release-20261027T225600Z')
LIVE_COMPOSE = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
LIVE_MANIFEST = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
TOKEN_SECRET_ARN = 'arn:aws:secretsmanager:us-east-1:108782052779:secret:dayhoff/container-build/github/token/iamh2o-gh-repo-awtQQ9'


def build(args):
    started_at = datetime.now(timezone.utc).isoformat()
    os.umask(0o077)
    args.work_dir.mkdir(mode=0o700)
    # Existing private owner inputs are transformed internally, never displayed.
    payload = json.loads((PRIOR / 'payload.json').read_text())
    payload['roles']['dewey']['tag'] = args.tag
    (args.work_dir / 'payload.json').write_text(json.dumps(payload) + '\n')
    pins = (PRIOR / 'pins.toml').read_text()
    pins, count = re.subn(r'(\[services\.dewey\]\n(?:(?!\[).)*?tag = ")[^"]+(")',
                         lambda m: m[1] + args.tag + m[2], pins, flags=re.S)
    if count != 1:
        raise ValueError('Expected one explicit [services.dewey] tag in the native pins file')
    (args.work_dir / 'pins.toml').write_text(pins)
    base_manifest = args.work_dir / 'base-manifest.json'
    with base_manifest.open('x') as stream:
        subprocess.run(['sudo', 'cat', str(LIVE_MANIFEST)], stdout=stream, check=True)
    scripts = PRIOR / 'scripts'
    command = ['python3', str(scripts / 'aws_host_container_release_build.py'),
        '--payload-file', str(args.work_dir / 'payload.json'),
        '--pins', str(args.work_dir / 'pins.toml'),
        '--manifest-builder', str(scripts / 'build_push_container_release_manifest.py'),
        '--output', str(args.work_dir / 'manifest.json'), '--repos-root', str(args.work_dir / 'repos'),
        '--github-token-secret-arn', TOKEN_SECRET_ARN, '--region', 'us-west-2',
        '--account-id', '108782052779', '--deploy-name', 'day', '--platform', 'linux/amd64',
        '--cache-mode', 'registry', '--parallelism', '1', '--service', 'dewey',
        '--base-manifest', str(base_manifest)]
    with (args.work_dir / 'build.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print(json.dumps({'phase': 'build', 'exit_code': result.returncode, 'service': 'dewey',
                          'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
        return result.returncode
    # Consume the native successful build result; do not second-guess it.
    selected = json.loads((args.work_dir / 'manifest.json').read_text())['images']['dewey']
    print(json.dumps({'phase': 'build', 'exit_code': 0, 'service': 'dewey', 'image': selected['image'],
                      'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
    return 0


def deploy(args):
    started_at = datetime.now(timezone.utc).isoformat()
    release = json.loads((args.work_dir / 'manifest.json').read_text())
    selected = release['images']['dewey']
    compose = yaml.safe_load(LIVE_COMPOSE.read_text())
    service = compose['services']['dewey']
    service['image'] = selected['image']
    service['environment']['LSMC_RELEASE_SHA'] = args.commit
    service['environment']['DEWEY_BUILD_SHA'] = args.commit
    temporary = LIVE_COMPOSE.with_name(LIVE_COMPOSE.name + '.dewey-multiqc-delivery-selected')
    with temporary.open('x') as stream:
        yaml.safe_dump(compose, stream, sort_keys=False)
    temporary.chmod(0o640)
    os.replace(temporary, LIVE_COMPOSE)
    command = ['docker', 'compose', '-p', 'dayhoff-day', '-f', str(LIVE_COMPOSE),
               'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'dewey']
    result = subprocess.run(command)
    if result.returncode:
        print(json.dumps({'phase': 'deploy', 'exit_code': result.returncode, 'service': 'dewey',
                          'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
        return result.returncode
    current_release = json.loads(LIVE_MANIFEST.read_text())
    current_release['images']['dewey'] = selected
    temporary = LIVE_MANIFEST.with_name(LIVE_MANIFEST.name + '.dewey-multiqc-delivery-selected')
    with temporary.open('x') as stream:
        json.dump(current_release, stream, indent=2)
        stream.write('\n')
    temporary.chmod(0o640)
    os.replace(temporary, LIVE_MANIFEST)
    print(json.dumps({'phase': 'deploy', 'exit_code': 0, 'service': 'dewey', 'image': selected['image'],
                      'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
    return 0


def content_proxy(args):
    """Apply the existing byte-preserving delivery rule to the private content vhost."""
    started_at = datetime.now(timezone.utc).isoformat()
    os.umask(0o077)
    path = Path('/etc/apache2/sites-available/dewey-content-day.conf')
    original = path.read_text()
    marker = '    ServerAlias *.dewey-content.day.lsmc.bio\n'
    directive = '    SetEnvIf Request_URI "^/__dewey_preview/assets/" no-gzip=1\n'
    if original.count(marker) != 1 or directive in original:
        raise ValueError('Expected the selected private Dewey content vhost without this delivery rule')
    (args.work_dir / 'private-content-before.conf').write_text(original)
    temporary = path.with_name(path.name + '.multiqc-delivery-selected')
    with temporary.open('x') as stream:
        stream.write(original.replace(marker, marker + directive, 1))
    temporary.chmod(path.stat().st_mode & 0o777)
    os.replace(temporary, path)
    result = subprocess.run(['apache2ctl', 'graceful'], capture_output=True, text=True)
    (args.work_dir / 'content-proxy-graceful.log').write_text(result.stdout + result.stderr)
    print(json.dumps({'phase': 'content-proxy', 'exit_code': result.returncode,
                      'file': str(path), 'native_operation': 'apache2ctl graceful',
                      'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
    return result.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['build', 'deploy', 'content-proxy'])
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--work-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.tag != '12.0.16' or not re.fullmatch(r'[0-9a-f]{40}', args.commit) or not args.work_dir.is_absolute():
        parser.error('Provide the coordinator-authorized final12.0.16 commit and explicit absolute work directory')
    raise SystemExit({'build': build, 'deploy': deploy, 'content-proxy': content_proxy}[args.phase](args))
