"""Promote a Dewey-only presentation patch; retain converted data and configuration."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import yaml

root = Path('/home/ubuntu/dewey_ops/registry10-20260912')
release = json.loads(Path('release.json').read_text())
image_receipt = json.loads(Path('image-receipt.json').read_text())
image = release['repository'] + '@' + image_receipt['digest']
prior = json.loads((root / '10.0.2/promotion-receipt.json').read_text())
compose_path = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
manifest_path = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
def read(path):
    return subprocess.check_output(['sudo', 'cat', str(path)])
def save(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
compose_bytes, manifest_bytes = read(compose_path), read(manifest_path)
compose, manifest = yaml.safe_load(compose_bytes), json.loads(manifest_bytes)
old = compose['services']['dewey']
if old['image'] != prior['image'] or old['environment']['DEWEY_BUILD_SHA'] != prior['commit']:
    raise SystemExit('Live Dewey changed from the reviewed 10.0.2 deployment')
labels = json.loads(subprocess.check_output(['sudo','docker','image','inspect',image]))[0]['Config']['Labels']
if labels['org.opencontainers.image.version'] != release['tag'] or labels['org.opencontainers.image.revision'] != release['commit']:
    raise SystemExit('Image labels differ from the exact tagged source')
directory = root / release['tag']
directory.mkdir(mode=0o700, exist_ok=False)
save(directory / 'previous-dewey.json', json.dumps(old,indent=2).encode())
new = copy.deepcopy(old)
new['image'] = image
new['environment'].update(DEWEY_BUILD_SHA=release['commit'], LSMC_RELEASE_SHA=release['commit'])
compose['services']['dewey'] = new
manifest['images']['dewey'].update(image=image, source_commit=release['commit'], source_tag=release['tag'])
if read(compose_path) != compose_bytes or read(manifest_path) != manifest_bytes:
    raise SystemExit('Deployment configuration changed during preparation')
for name, path, data in [('compose.yml',compose_path,yaml.safe_dump(compose,sort_keys=False).encode()),
                         ('manifest.json',manifest_path,(json.dumps(manifest,indent=2)+'\n').encode())]:
    staging = directory / name
    save(staging,data)
    subprocess.run(['sudo','install','-m','600',str(staging),str(path)+'.dewey-patch'],check=True)
    subprocess.run(['sudo','mv',str(path)+'.dewey-patch',str(path)],check=True)
subprocess.run(['sudo','docker','compose','-f',str(compose_path),'up','-d','--no-deps','--pull','never','dewey'],check=True)
receipt = dict(status='promoted',tag=release['tag'],commit=release['commit'],image=image,
               prior_image=prior['image'],config_sha256=hashlib.sha256(read(old['environment']['DEWEY_CONFIG'])).hexdigest(),
               conversion_manifest_sha256=prior['conversion_manifest_sha256'],data_changes=False,siblings_changed=False)
save(directory / 'promotion-receipt.json',(json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps(receipt))
