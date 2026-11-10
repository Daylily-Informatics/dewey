"""Deploy the selected Dewey image; preserve existing configuration and credentials."""
from datetime import datetime,timezone
import json,os,subprocess
from pathlib import Path
import yaml
stage=Path('/home/ubuntu/dewey-multiqc-collateral-12.0.36-retry1')
root=Path('/opt/dayhoff/deployments/day')
if os.geteuid()!=0 or os.environ.get('SUDO_USER')!='ubuntu':
    raise RuntimeError('Run with targeted sudo from ubuntu')
selected=json.loads((stage/'manifest.json').read_text())['images']['dewey']
compose_path=root/'compose/docker-compose.yml'
manifest_path=root/'container-release-manifest.json'
(stage/'compose-before.yaml').write_bytes(compose_path.read_bytes())
compose=yaml.safe_load(compose_path.read_text())
service=compose['services']['dewey']
service['image']=selected['image']
service['environment']['LSMC_RELEASE_SHA']=selected['source_commit']
service['environment']['DEWEY_BUILD_SHA']=selected['source_commit']
compose_path.write_text(yaml.safe_dump(compose,sort_keys=False))
with (stage/'deployment.log').open('x') as output:
    r=subprocess.run(['docker','compose','-p','dayhoff-day','-f',str(compose_path),'up','-d','--wait','--wait-timeout','180','--no-deps','--no-build','--pull','never','dewey'],stdout=output,stderr=subprocess.STDOUT)
if r.returncode==0:
    manifest=json.loads(manifest_path.read_text())
    manifest['images']['dewey']=selected
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
receipt={'source_tag':selected['source_tag'],'source_commit':selected['source_commit'],'image':selected['image'],'exit_code':r.returncode,'completed_at':datetime.now(timezone.utc).isoformat()}
(stage/'deployment-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(r.returncode)
