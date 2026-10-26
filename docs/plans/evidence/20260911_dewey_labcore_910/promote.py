"""Bounded Dewey 9.1.0 image-only promotion; preserve DB/config and siblings."""
import argparse,copy,hashlib,json,os,pathlib,subprocess,yaml
ROOT=pathlib.Path('/home/ubuntu/dewey_ops/labcore-910')
COMPOSE=pathlib.Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
MANIFEST=pathlib.Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
OLD='108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:382bc96a15e70b06d2e4c865b4922f27ce67229a4f3e8522b6246e3c9a706234'
def sha(data): return hashlib.sha256(data).hexdigest()
def save(path,data):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f: f.write(data)
def inspect():
 ids=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=dayhoff-day'],text=True).split()
 rows=json.loads(subprocess.check_output(['docker','inspect',*ids]))
 return {r['Config']['Labels']['com.docker.compose.service']:{'id':r['Id'],'image':r['Image'],'started':r['State']['StartedAt'],'restarts':r['RestartCount']} for r in rows if r['Config']['Labels']['com.docker.compose.service']!='dewey'}
a=argparse.ArgumentParser();a.add_argument('mode',choices=['prepare','isolated','promote']);a.add_argument('--image',required=True);a.add_argument('--commit',required=True);args=a.parse_args()
assert args.image.startswith(OLD.split('@')[0]+'@sha256:') and len(args.image.split(':')[-1])==64
assert len(args.commit)==40 and all(c in '0123456789abcdef' for c in args.commit)
planfile=ROOT/'promotion-plan.json'
if args.mode=='prepare':
 old=COMPOSE.read_bytes(); mraw=MANIFEST.read_bytes(); c=yaml.safe_load(old); m=json.loads(mraw)
 assert c['services']['dewey']['image']==OLD and m['images']['dewey']['image']==OLD
 n=copy.deepcopy(c); d=n['services']['dewey']; d['image']=args.image
 oldconfig=pathlib.Path(d['environment']['DEWEY_CONFIG']); newconfig=pathlib.Path('/opt/dewey/day/releases/9.1.0/dewey-config.yaml')
 oldpayload=yaml.safe_load(oldconfig.read_text()); newpayload=yaml.safe_load(newconfig.read_text())
 owner=newpayload.pop('labcore_owner'); oldpayload.pop('labcore_owner',None)
 assert oldpayload==newpayload and owner['api_enabled'] and len(owner['service_principals'])==1
 assert owner['service_principals'][0]['principal_id']=='labcore-synthetic-acceptance-910'
 d['environment']['DEWEY_CONFIG']=str(newconfig)
 mounts=[v for v in d['volumes'] if v.get('source')==str(oldconfig)]
 assert len(mounts)==1
 mounts[0]['source']=str(newconfig); mounts[0]['target']=str(newconfig)
 for k in ('DEWEY_BUILD_SHA','LSMC_RELEASE_SHA'):
  assert k in d['environment']; d['environment'][k]=args.commit
 mn=copy.deepcopy(m); mn['images']['dewey'].update(image=args.image,source_commit=args.commit,source_tag='9.1.0')
 save(ROOT/'previous-compose.yml',old);save(ROOT/'previous-manifest.json',mraw)
 save(ROOT/'next-compose.yml',yaml.safe_dump(n,sort_keys=False).encode());save(ROOT/'next-manifest.json',(json.dumps(mn,indent=2)+'\n').encode())
 isolated=copy.deepcopy(n); isolated['services']={'dewey':isolated['services']['dewey']}
 isolated.pop('name',None); di=isolated['services']['dewey'];di['restart']='no'
 for k in ('PORT','DEWEY_PORT'):di['environment'][k]='18915'
 for k in ('HOST','DEWEY_HOST'):di['environment'][k]='127.0.0.1'
 for k in ('DEWEY_QEO_INGEST_URL','DEWEY_QEO_API_TOKEN','DEWEY_QEO_CONSUMER_GROUP'):di['environment'][k]=''
 save(ROOT/'isolated-compose.yml',yaml.safe_dump(isolated,sort_keys=False).encode())
 plan={'image':args.image,'commit':args.commit,'compose_before':sha(old),'manifest_before':sha(mraw),'compose_after':sha((ROOT/'next-compose.yml').read_bytes()),'manifest_after':sha((ROOT/'next-manifest.json').read_bytes()),'siblings':inspect(),'database_configuration_changed':False,'application_config_sha256':sha(newconfig.read_bytes()),'changed_service_fields':['image','environment.DEWEY_BUILD_SHA','environment.LSMC_RELEASE_SHA','environment.DEWEY_CONFIG','volumes.dewey_config']}
 save(planfile,(json.dumps(plan,indent=2)+'\n').encode());print(json.dumps(plan))
else:
 plan=json.loads(planfile.read_text());assert plan['image']==args.image and plan['commit']==args.commit
 assert sha(COMPOSE.read_bytes())==plan['compose_before'] and sha(MANIFEST.read_bytes())==plan['manifest_before']
 if args.mode=='isolated':
  subprocess.run(['docker','compose','-p','dewey-labcore-910','-f',str(ROOT/'isolated-compose.yml'),'up','-d','--no-deps','--pull','never','dewey'],check=True)
 else:
  acceptance=json.loads((ROOT/'candidate-acceptance.json').read_text());assert acceptance['status']=='passed' and acceptance['synthetic'] and acceptance['mode']=='create'
  assert sha(pathlib.Path('/opt/dewey/day/releases/9.1.0/dewey-config.yaml').read_bytes())==plan['application_config_sha256']
  assert inspect()==plan['siblings']
  subprocess.run(['docker','compose','-p','dewey-labcore-910','-f',str(ROOT/'isolated-compose.yml'),'stop','dewey'],check=True)
  for src,dst,key in [('next-compose.yml',COMPOSE,'compose_after'),('next-manifest.json',MANIFEST,'manifest_after')]:
   content=(ROOT/src).read_bytes();assert sha(content)==plan[key]
   temp=dst.with_name(dst.name+'.dewey910-new');save(temp,content);os.replace(temp,dst)
  subprocess.run(['docker','compose','-f',str(COMPOSE),'up','-d','--no-deps','--pull','never','dewey'],check=True)
  assert inspect()==plan['siblings']
  save(ROOT/'promotion-result.json',(json.dumps({'image':args.image,'commit':args.commit,'siblings_unchanged':True,'database_configuration_changed':False})+'\n').encode())
  print('Dewey-only promotion complete')
