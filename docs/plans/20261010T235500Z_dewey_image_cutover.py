"""Replace only Dewey with its exact tagged image; preserve configuration and siblings."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,subprocess,sys,time,yaml
assert os.getuid()==1000
root=Path('/opt/dayhoff/deployments/day')
out=Path('/home/ubuntu/dewey-delete-disabled-20261010')
out.mkdir(mode=0o700,exist_ok=False)
expected_tag='11.0.3'
expected_commit='eba14993e342386641803fa99b58ce63cf51e5a1'
old_image='108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:df7bca9ea7cf9e999a24d4d8e8f1369182104d989fc20c25b3cc4209ecb31499'
old_id='7a34c472d7e6e0d6c000f977d3e06513660510963869e2dca11bb1d03d6089c2'
name='dayhoff-day-dewey-1'
receipt=json.loads(Path(sys.argv[1]).read_text())
assert receipt['source_tag']==expected_tag and receipt['source_commit']==expected_commit
assert receipt['builder_instance']=='i-07df3a933e4839f52'
image=receipt['image']
assert image.startswith('108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:')
def inspect(identity):return json.loads(subprocess.check_output(['docker','inspect',identity]))[0]
def read(path):return subprocess.check_output(['sudo','cat',str(path)])
def digest(data):return hashlib.sha256(data).hexdigest()
def siblings():
 names=subprocess.check_output(['docker','ps','-a','--filter','label=com.docker.compose.project=dayhoff-day','--format','{{.Names}}'],text=True).splitlines()
 return {n:{k:inspect(n)[k] for k in ('Id','Image')} for n in names if n!=name}
old=inspect(name)
assert old['Id']==old_id and old['Config']['Image']==old_image and old['State']['Running']
labels=inspect(image)['Config']['Labels']
assert labels['org.opencontainers.image.revision']==expected_commit and labels['org.opencontainers.image.version']==expected_tag
compose=root/'compose/docker-compose.yml';manifest=root/'container-release-manifest.json'
raw_compose=read(compose);raw_manifest=read(manifest)
c=yaml.safe_load(raw_compose);m=json.loads(raw_manifest)
assert c['services']['dewey']['image']==old_image and m['images']['dewey']['image']==old_image
assert raw_compose.count(old_image.encode())==1
new_compose=raw_compose.replace(old_image.encode(),image.encode())
expected=yaml.safe_load(raw_compose);expected['services']['dewey']['image']=image
previous_commit='3f782eebc6e43ded3fa655c3fcdc1c2c616bcd89'
for key in ('DEWEY_BUILD_SHA','LSMC_RELEASE_SHA'):
 assert expected['services']['dewey']['environment'][key]==previous_commit
 expected['services']['dewey']['environment'][key]=expected_commit
assert new_compose.count(previous_commit.encode())==2
new_compose=new_compose.replace(previous_commit.encode(),expected_commit.encode())
assert yaml.safe_load(new_compose)==expected
m['images']['dewey'].update(image=image,source_commit=expected_commit,source_tag=expected_tag)
new_manifest=(json.dumps(m,indent=2,sort_keys=True)+'\n').encode()
files=[Path(m['Source']) for m in old['Mounts'] if Path(m['Source']).suffix in {'.yaml','.yml','.json','.pem','.txt'}]
config_hashes={str(p):digest(read(p)) for p in files}
before=siblings()
intent={'tag':expected_tag,'commit':expected_commit,'image':image,'started_at':datetime.now(timezone.utc).isoformat(),'old_id':old_id,'configuration_hashes':config_hashes,'sibling_identities':before,'compose_before_sha256':digest(raw_compose),'manifest_before_sha256':digest(raw_manifest)}
(out/'intent.json').write_text(json.dumps(intent,indent=2)+'\n')
assert read(compose)==raw_compose and read(manifest)==raw_manifest
# Infinite Docker timeout means SIGKILL is never sent by Docker.
drain=subprocess.Popen(['docker','stop','--signal','SIGTERM','--timeout','-1',old_id],stdout=subprocess.DEVNULL)
deadline=time.monotonic()+120
while inspect(old_id)['State']['Running'] and time.monotonic()<deadline:time.sleep(1)
assert not inspect(old_id)['State']['Running'], 'Graceful drain incomplete; no configuration or sibling changed; do not force kill'
assert drain.wait(timeout=5)==0
assert siblings()==before and read(compose)==raw_compose and read(manifest)==raw_manifest
for path,data in [(compose,new_compose),(manifest,new_manifest)]:
 temp=str(path)+'.dewey1103'
 subprocess.run(['sudo','cp','--preserve=mode,ownership',str(path),temp],check=True)
 subprocess.run(['sudo','tee',temp],input=data,stdout=subprocess.DEVNULL,check=True)
 subprocess.run(['sudo','mv',temp,str(path)],check=True)
subprocess.run(['sudo','docker','compose','-p','dayhoff-day','-f',str(compose),'up','-d','--no-deps','--pull','never','--no-build','dewey'],check=True)
current=inspect(name)
assert current['Config']['Image']==image and current['State']['Running']
assert siblings()==before
assert {str(p):digest(read(p)) for p in files}==config_hashes
result={'at':datetime.now(timezone.utc).isoformat(),'source_tag':expected_tag,'source_commit':expected_commit,'image':image,'container':current['Id'],'state':current['State']['Status'],'siblings_unchanged':True,'configuration_unchanged':True,'forced_kill':False,'data_or_db_mutations':False,'tests_run':False}
(out/'deployment-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
