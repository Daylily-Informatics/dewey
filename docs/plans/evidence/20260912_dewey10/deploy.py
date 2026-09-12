"""Prepare/promote only Dewey; preserve live sibling configuration and containers.

Run as ubuntu. Protected deployment files use targeted sudo. This operator never
applies data conversion implicitly; promotion requires its committed receipt.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import yaml

ROOT = Path('/home/ubuntu/dewey_ops/registry10-20260912')
COMPOSE = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
MANIFEST = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
OLD_IMAGE = '108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:7982b35d67ae54f12103d7bec8cf0e4f84de1eb730b0a1138041de1572b2b0a3'
REPOSITORY = OLD_IMAGE.split('@')[0]

def read(path):
    return subprocess.check_output(['sudo', 'cat', str(path)])

def sha(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()

def save(path, value):
    if not isinstance(value, bytes):
        value = (json.dumps(value, indent=2) + '\n').encode()
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['prepare', 'promote'])
parser.add_argument('--image', required=True)
parser.add_argument('--commit', required=True)
parser.add_argument('--tag', required=True)
parser.add_argument('--conversion-receipt', type=Path)
args = parser.parse_args()
if not re.fullmatch(r'\d+\.\d+\.\d+', args.tag) or not re.fullmatch(r'[a-f0-9]{40}', args.commit) or not re.fullmatch(re.escape(REPOSITORY) + r'@sha256:[a-f0-9]{64}', args.image):
    raise SystemExit('Exact numeric tag, commit and immutable Dewey image are required')
directory = ROOT / args.tag
config = directory / 'dewey-config.yaml'
config_target = f'/opt/dewey/day/releases/{args.tag}/dewey-config.yaml'
plan_path = directory / 'deployment-plan.json'
current = yaml.safe_load(read(COMPOSE))
current_dewey = current['services']['dewey']
if args.mode == 'prepare':
    directory.mkdir(mode=0o700, exist_ok=False)
    if current_dewey['image'] != OLD_IMAGE:
        raise SystemExit('Live Dewey image changed; reconcile before preparing promotion')
    source_config = current_dewey['environment']['DEWEY_CONFIG']
    save(directory / 'previous-dewey.json', current_dewey)
    save(directory / 'previous-config.yaml', read(source_config))
    operator = copy.deepcopy(current)
    operator['services'] = {'dewey': copy.deepcopy(current_dewey)}
    operator.pop('name', None)
    candidate = operator['services']['dewey']
    candidate['image'] = args.image
    candidate['restart'] = 'no'
    candidate.pop('container_name', None)
    candidate['environment'].update(DEWEY_BUILD_SHA=args.commit, LSMC_RELEASE_SHA=args.commit,
        DEWEY_BUILD_BRANCH='codex/dewey-labcore-910')
    candidate['volumes'].append({'type':'bind','source':str(ROOT),'target':str(ROOT),'read_only':False})
    ncbi = '/home/ubuntu/.config/ncbi/key.txt'
    candidate['volumes'].append({'type':'bind','source':ncbi,'target':ncbi,'read_only':True})
    candidate['environment']['DEWEY_NCBI_API_KEY_FILE'] = ncbi
    save(directory / 'operator-compose.yml', yaml.safe_dump(operator, sort_keys=False).encode())
    fingerprints = ['1c4e120de6145abc1627db06c6f7a238e8cefde6bae1f7247af697088989733b',
        '81b98e1c3a8f6bffe0735dc416136e59d0ee7f3a0fad46609612f53edcc3a7fe',
        '87b37bd82a81011908c22e3f21340cf30b025649205667a43fcd5a8bd38c7e5c']
    # Preserve existing general service-bearer authority, with explicit credential
    # subjects. These labels make no claim about which producer owns a credential.
    save(directory / 'service-principals.json', {key:{'subject':'existing-service-credential:' + key[:16], 'roles':['ADMIN']} for key in fingerprints})
    save(plan_path, {'tag':args.tag,'commit':args.commit,'image':args.image,
        'previous_dewey_sha256':sha(current_dewey),'previous_config_sha256':sha(read(source_config)),
        'source_config':source_config,'new_config':str(config),'new_config_target':config_target})
    print(json.dumps({'status':'prepared','operator_compose':str(directory / 'operator-compose.yml'),
        'destination_config':str(config),'principal_manifest':str(directory / 'service-principals.json'),
        'production_changed':False}))
else:
    plan = json.loads(plan_path.read_text())
    if any(plan[k] != getattr(args,k) for k in ('image','commit','tag')):
        raise SystemExit('Promotion inputs differ from the prepared plan')
    if sha(current_dewey) != plan['previous_dewey_sha256'] or sha(read(plan['source_config'])) != plan['previous_config_sha256']:
        raise SystemExit('Dewey config changed; reconcile explicitly before promotion')
    if not args.conversion_receipt or not args.conversion_receipt.is_absolute():
        raise SystemExit('A committed conversion receipt is required')
    receipt = json.loads(read(args.conversion_receipt))
    if receipt.get('status') != 'committed' or receipt['target']['database'] != 'dewey_prod_tapdb10':
        raise SystemExit('Conversion is not confirmed committed in the production database')
    new = copy.deepcopy(current_dewey)
    new['image'] = args.image
    new['environment'].update(DEWEY_CONFIG=config_target, DEWEY_BUILD_SHA=args.commit,
        LSMC_RELEASE_SHA=args.commit, DEWEY_BUILD_BRANCH='codex/dewey-labcore-910',
        DEWEY_NCBI_API_KEY_FILE='/home/ubuntu/.config/ncbi/key.txt')
    mounts = [v for v in new['volumes'] if v.get('target') == plan['source_config']]
    if len(mounts) != 1:
        raise SystemExit('Expected exactly one existing Dewey configuration mount')
    mounts[0].update(source=str(config), target=config_target, read_only=True)
    new['volumes'].append({'type':'bind','source':'/home/ubuntu/.config/ncbi/key.txt',
        'target':'/home/ubuntu/.config/ncbi/key.txt','read_only':True})
    if not config.is_file():
        raise SystemExit('Prepared Dewey configuration is missing')
    current['services']['dewey'] = new
    manifest = json.loads(read(MANIFEST))
    manifest['images']['dewey'].update(image=args.image, source_commit=args.commit, source_tag=args.tag)
    for name, target, value in [('promotion-compose.yml',COMPOSE,yaml.safe_dump(current,sort_keys=False).encode()),
        ('promotion-manifest.json',MANIFEST,(json.dumps(manifest,indent=2)+'\n').encode())]:
        staging = directory / name
        save(staging,value)
        temporary = str(target) + '.dewey10-new'
        subprocess.run(['sudo','install','-m','600',str(staging),temporary],check=True)
        subprocess.run(['sudo','mv',temporary,str(target)],check=True)
    subprocess.run(['sudo','docker','compose','-f',str(COMPOSE),'up','-d','--no-deps','--pull','never','dewey'],check=True)
    result = {'status':'promoted','image':args.image,'commit':args.commit,'tag':args.tag,
        'conversion_manifest_sha256':receipt['manifest_sha256'],'config_sha256':sha(read(config))}
    save(directory / 'promotion-receipt.json',result)
    print(json.dumps(result))
