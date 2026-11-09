"""Run only the selected final Dewey QEO2 source capability build or native Compose deployment.

Release helper for the user-authorized QEO2 internal MultiQC source capability.
Native Compose readiness only; no separate probes, image audits, or sibling inventories.
Private build inputs and native build stdout never reach this runner's stdout.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import shutil

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
    print(json.dumps({'phase': 'build', 'exit_code': 0, 'service': 'dewey', 'image': selected['image'], 'source_tag': selected['source_tag'],
                      'source_commit': selected['source_commit'],
                      'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
    return 0


def credential(args):
    selected=json.loads((args.work_dir/'manifest.json').read_text())['images']['dewey']
    container='qeo2-dewey-source-credential-day-'+args.tag
    command=['docker','run','--name',container,'-e','DEWEY_DEPLOYMENT_CODE=day','-e','DEWEY_EXECUTION_BACKEND=dewey-container','--entrypoint','dewey',selected['image'],
        'qeo','source-credential-create','--token-output-file','/tmp/dewey-source.token','--lifetime-days','90']
    with (args.work_dir/'source-credential.json').open('x') as output:
        result=subprocess.run(command,stdout=output)
    if not result.returncode:
        subprocess.run(['docker','cp',container+':/tmp/dewey-source.token','/opt/qeo2/day/config/dewey-source.token'],check=True)
    print(json.dumps({'phase':'credential','exit_code':result.returncode,'scope':'multiqc:register-internal-webshare'}))
    return result.returncode


def deploy(args):
    started_at = datetime.now(timezone.utc).isoformat()
    release = json.loads((args.work_dir / 'manifest.json').read_text())
    selected = release['images']['dewey']
    original_compose = LIVE_COMPOSE.read_bytes()
    original_manifest = LIVE_MANIFEST.read_bytes()
    (args.work_dir / 'previous-compose.yml').write_bytes(original_compose)
    (args.work_dir / 'previous-manifest.json').write_bytes(original_manifest)
    compose = yaml.safe_load(original_compose)
    service = compose['services']['dewey']
    service['image'] = selected['image']
    service['environment']['LSMC_RELEASE_SHA'] = args.commit
    service['environment']['DEWEY_BUILD_SHA'] = args.commit
    credential = json.loads((args.work_dir / 'source-credential.json').read_text())
    service['environment']['DEWEY_QEO_SOURCE_TOKEN_SHA256'] = credential['token_sha256']
    service['environment']['DEWEY_QEO_SOURCE_TOKEN_EXPIRES_AT'] = credential['expires_at']
    config_mount = next(v for v in service['volumes'] if v['target'] == service['environment']['DEWEY_CONFIG'])
    source_config = Path(config_mount['source'])
    source_settings = yaml.safe_load(source_config.read_text())
    source_settings['qeo_source_s3_roots'] = ['s3://lsmc-ssf-sequencing-data/derived/']
    selected_config = args.work_dir / 'dewey-config.yaml'
    selected_config.write_text(yaml.safe_dump(source_settings, sort_keys=False))
    shutil.copymode(source_config, selected_config)
    config_mount['source'] = str(selected_config)
    service['environment'].pop('DEWEY_QEO_SOURCE_S3_ROOTS', None)
    temporary = LIVE_COMPOSE.with_name(LIVE_COMPOSE.name + '.dewey-qeo-source-selected')
    with temporary.open('x') as stream:
        yaml.safe_dump(compose, stream, sort_keys=False)
    temporary.chmod(0o640)
    os.replace(temporary, LIVE_COMPOSE)
    command = ['docker', 'compose', '-p', 'dayhoff-day', '-f', str(LIVE_COMPOSE),
               'up', '-d', '--wait', '--wait-timeout', '180', '--no-deps', '--no-build', '--pull', 'never', 'dewey']
    result = subprocess.run(command)
    if result.returncode:
        print(json.dumps({'phase': 'deploy', 'exit_code': result.returncode, 'service': 'dewey',
                          'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
        return result.returncode
    current_release = json.loads(LIVE_MANIFEST.read_text())
    current_release['images']['dewey'] = selected
    temporary = LIVE_MANIFEST.with_name(LIVE_MANIFEST.name + '.dewey-qeo-source-selected')
    with temporary.open('x') as stream:
        json.dump(current_release, stream, indent=2)
        stream.write('\n')
    temporary.chmod(0o640)
    os.replace(temporary, LIVE_MANIFEST)
    print(json.dumps({'phase': 'deploy', 'exit_code': 0, 'service': 'dewey', 'image': selected['image'], 'source_tag': selected['source_tag'],
                      'source_commit': selected['source_commit'],
                      'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat()}))
    return 0



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['build', 'credential', 'deploy'])
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--work-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.tag != '12.0.32' or not re.fullmatch(r'[0-9a-f]{40}', args.commit) or not args.work_dir.is_absolute():
        parser.error('Provide the coordinator-authorized final 12.0.32 commit and explicit absolute work directory')
    raise SystemExit({'build': build, 'credential': credential, 'deploy': deploy}[args.phase](args))
