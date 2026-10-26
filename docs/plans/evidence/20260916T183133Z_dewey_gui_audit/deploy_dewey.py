"""One image-only Dewey deployment; run in the authorized EC2 ubuntu shell.

Retains private configuration receipts on EC2. Never changes application data.
Rollback, if required for unavailability, restores only Dewey image/configuration.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import yaml

COMPOSE = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
MANIFEST = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
REPOSITORY = '108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey'
PREVIOUS = REPOSITORY + '@sha256:91bce850ad777244f443e933e9ced92664a1d70dc092f632881810e3a0860687'
BASELINE_SHA = 'aef0b6b96b3ad1aadf008062a765271b97f6d5307776cf33ca1293a941dccf78'

def read(path):
    return subprocess.check_output(['sudo', 'cat', str(path)])

def sha(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def save(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2) + '\n').encode()
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())

def containers():
    ids = subprocess.check_output(['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=dayhoff-day'], text=True).split()
    return [{"name": r['Name'], "id": r['Id'], "image": r['Image'],
             "status": r['State']['Status'], "restart_count": r['RestartCount']}
            for r in json.loads(subprocess.check_output(['docker', 'inspect', *ids]))]

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['deploy', 'rollback'])
parser.add_argument('--receipt-dir', type=Path, required=True)
parser.add_argument('--image', required=True)
parser.add_argument('--commit', required=True)
parser.add_argument('--tag', required=True)
parser.add_argument('--branch', required=True)
args = parser.parse_args()
if pwd.getpwuid(os.getuid()).pw_name != 'ubuntu':
    raise SystemExit('Run as ubuntu on the authorized EC2 instance')
if not args.receipt_dir.is_absolute() or not re.fullmatch(re.escape(REPOSITORY) + r'@sha256:[a-f0-9]{64}', args.image):
    raise SystemExit('Explicit absolute receipt directory and immutable Dewey image required')
if not re.fullmatch(r'\d+\.\d+\.\d+', args.tag) or not re.fullmatch(r'[a-f0-9]{40}', args.commit):
    raise SystemExit('Numeric release tag and exact source commit required')

raw_compose, raw_manifest = read(COMPOSE), read(MANIFEST)
current, manifest = yaml.safe_load(raw_compose), json.loads(raw_manifest)
old = copy.deepcopy(current['services']['dewey'])
before = containers()
candidate = copy.deepcopy(old)
if args.mode == 'deploy':
    if sha(raw_compose) != BASELINE_SHA or old['image'] != PREVIOUS:
        raise SystemExit('Production differs from captured baseline; reconcile before deploying')
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', args.image]))[0]
    labels = image['Config']['Labels']
    if labels.get('org.opencontainers.image.revision') != args.commit or labels.get('org.opencontainers.image.version') != args.tag:
        raise SystemExit('Image provenance differs from exact release commit/tag')
    args.receipt_dir.mkdir(mode=0o700, exist_ok=False)
    save(args.receipt_dir / 'previous-compose.yml', raw_compose)
    save(args.receipt_dir / 'previous-manifest.json', raw_manifest)
    save(args.receipt_dir / 'containers-before.json', before)
    candidate['image'] = args.image
    candidate['environment'].update(DEWEY_BUILD_SHA=args.commit,
        LSMC_RELEASE_SHA=args.commit, DEWEY_BUILD_BRANCH=args.branch)
    manifest['images']['dewey'].update(image=args.image, source_commit=args.commit, source_tag=args.tag)
else:
    if old['image'] != args.image:
        raise SystemExit('Unexpected current Dewey image; refusing rollback')
    candidate = yaml.safe_load((args.receipt_dir / 'previous-compose.yml').read_bytes())['services']['dewey']
    manifest['images']['dewey'] = json.loads((args.receipt_dir / 'previous-manifest.json').read_bytes())['images']['dewey']

# Database/service configuration, mounts, identities, and all siblings are preserved.
new = copy.deepcopy(current)
new['services']['dewey'] = candidate
siblings = {k: v for k, v in current['services'].items() if k != 'dewey'}
assert siblings == {k: v for k, v in new['services'].items() if k != 'dewey'}
assert old['volumes'] == candidate['volumes']
config_hashes = {v['source']: sha(read(v['source'])) for v in candidate['volumes']
                 if v['target'] in {candidate['environment']['DEWEY_CONFIG'], candidate['environment']['TAPDB_CONFIG_PATH']}}
save(args.receipt_dir / (args.mode + '-config-hashes.json'), config_hashes)
for label, target, value in [('compose', COMPOSE, yaml.safe_dump(new, sort_keys=False).encode()),
                             ('manifest', MANIFEST, (json.dumps(manifest, indent=2) + '\n').encode())]:
    staging = args.receipt_dir / (args.mode + '-' + label)
    save(staging, value)
    subprocess.run(['sudo', 'install', '-m', '600', str(staging), str(target)], check=True)
subprocess.run(['sudo', 'docker', 'compose', '-f', str(COMPOSE), 'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'dewey'], check=True)
after = containers()
before_siblings = {r['name']: r for r in before if r['name'] != '/dayhoff-day-dewey-1'}
after_siblings = {r['name']: r for r in after if r['name'] != '/dayhoff-day-dewey-1'}
assert before_siblings == after_siblings, 'Sibling container state changed during deployment'
assert all(sha(read(path)) == value for path, value in config_hashes.items()), 'Configuration changed'
receipt = {'mode': args.mode, 'tag': args.tag, 'commit': args.commit, 'branch': args.branch,
    'image': candidate['image'], 'previous_image': old['image'], 'containers_before': before,
    'containers_after': after, 'siblings_unchanged': True, 'configuration_unchanged': True,
    'config_hashes': config_hashes, 'compose_sha256': sha(read(COMPOSE)),
    'manifest_sha256': sha(read(MANIFEST)), 'application_data_operations': []}
save(args.receipt_dir / (args.mode + '-receipt.json'), receipt)
print(json.dumps(receipt))
