"""Explicit synthetic fixture; never dispatch, copy S3 data, or impersonate a Labcore run."""
import json,hashlib,sys,uuid
from pathlib import Path
import httpx
from dewey_service.settings import get_settings
from dewey_service.labcore_owner_config import load_labcore_owner_config
from dewey_service.labcore_owner_command import COMMAND_TYPE,COMMAND_VERSION,HASH_DOMAIN,bind_registration_command
from dewey_service.labcore_owner_contracts import bind_request_hash

port=int(sys.argv[1]); mode=sys.argv[2]
assert port in (8914,18915) and mode in ('create','verify')
settings=get_settings(); owner=load_labcore_owner_config()
assert owner.is_enabled and len(owner.service_principals)==1
principal=owner.service_principals[0]; assert principal.principal_id=='labcore-synthetic-acceptance-910'
state=Path('/run/dewey-production-state/labcore-910'); state.mkdir(mode=0o700,exist_ok=True)
client=httpx.Client(base_url=f'http://127.0.0.1:{port}',headers={'Host':'dewey.day.lsmc.bio'},timeout=30)
api_tokens=settings.api_tokens(); assert api_tokens
regular={'Authorization':'Bearer '+next(iter(api_tokens))}
owner_headers={'Authorization':'Bearer '+principal.bearer_token}
if mode=='create':
 assert not (state/'command.json').exists()
 run='synthetic-labcore-run-'+uuid.uuid4().hex
 # Registration-only URI; no S3 object is asserted to exist or touched.
 root='s3://'+settings.managed_storage_bucket+'/acceptance/labcore-910/'+run+'/'
 expected=[{'relative_path':'synthetic-manifest.json','sha256':hashlib.sha256(b'synthetic').hexdigest(),'size_bytes':9,'object_version_id':'synthetic-version-not-an-s3-object'}]
 raw={'contract_type':'dewey.labcore-sequencing-run-owner/v1','contract_version':1,
 'hash_domain':'dewey.labcore-sequencing-run-owner.request/v1',
 'external_system':'labcore','external_object_type':'sequencing_run','external_object_id':run,
 'labcore_sequencing_run_euid':run,'tenant_euid':principal.tenant_euid,
 'processing_site_euid':'synthetic-labcore-site-910','platform':'ILMN',
 'target_type':'artifact','relation_type':'labcore_sequencing_run','dataset_root_uri':root,
 'dataset_revision':hashlib.sha256(run.encode()).hexdigest(),
 'inventory_sha256':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest(),
 'labcore_binding_receipt_id':'synthetic-binding-'+run,
 'labcore_binding_receipt_sha256':hashlib.sha256(('binding:'+run).encode()).hexdigest(),
 'expected_files':expected}
 evidence={k:raw[k] for k in ('tenant_euid','processing_site_euid','platform','dataset_root_uri','dataset_revision','inventory_sha256','labcore_binding_receipt_id','labcore_binding_receipt_sha256','labcore_sequencing_run_euid','expected_files')}
 evidence['test_euid']='synthetic-labcore-test-910'
 response=client.post('/api/v1/artifact-prefixes',headers={**regular,'Idempotency-Key':run},json={'root_uri':root,'artifact_type':'sequencing_run','producer_system':'labcore','producer_object_euid':run,'metadata':{'synthetic_acceptance':True,'acceptance_purpose':'Dewey 9.1.0 API qualification; not a real Labcore run','availability_status':'unavailable','labcore_owner':evidence}})
 assert response.status_code==200,(response.status_code,response.text[:500])
 result=response.json(); assert result['status_code']==201
 raw['target_euid']=result['artifact_euid']
 command=bind_registration_command({'command_type':COMMAND_TYPE,'command_version':COMMAND_VERSION,'hash_domain':HASH_DOMAIN,'test_euid':evidence['test_euid'],'owner_request':bind_request_hash(raw)})
 (state/'command.json').write_text(json.dumps(command,indent=2)+'\n')
else:
 command=json.loads((state/'command.json').read_text())
headers={**owner_headers,'Idempotency-Key':command['command_sha256']}
path='/api/v2/sequencer-runs/register'
a=client.post(path,headers=headers,json=command); assert a.status_code==(201 if mode=='create' else 200),(a.status_code,a.text[:500])
b=client.post(path,headers=headers,json=command); assert b.status_code==200 and b.json()==a.json()
# Header mismatch rejects before domain writes.
c=client.post(path,headers={**headers,'Idempotency-Key':'0'*64},json=command); assert c.status_code==409
# Authenticated, correctly hashed conflicting command for the same run.
conflict=bind_registration_command({**command,'test_euid':'synthetic-conflicting-test'})
c=client.post(path,headers={**owner_headers,'Idempotency-Key':conflict['command_sha256']},json=conflict);assert c.status_code==409
assert client.get('/api/v1/artifacts',headers=owner_headers).status_code==401
assert client.post('/api/v2/external-objects',headers=headers,json=command).status_code==404
for health in ('/healthz','/readyz'):
 r=client.get(health);assert r.status_code==200,(health,r.status_code)
s=client.post('/api/search/v2/query',headers=regular,json={'q':'','scopes':['artifact','share'],'page_size':25});assert s.status_code==200
from dewey_service.tapdb_backend import TapDBBackend,ARTIFACT_TEMPLATE,EXTERNAL_OBJECT_TEMPLATE,EXTERNAL_OBJECT_RELATION_TEMPLATE,REGISTRATION_RECEIPT_TEMPLATE
from dewey_service.integrations.tapdb_external_references import resolve_relation_endpoints
from sqlalchemy import text
backend=TapDBBackend()
with backend.session_scope() as session:
 assert session.execute(text("select has_database_privilege(current_user,current_database(),'TEMP')")).scalar() is False
 receipt=a.json()
 relation=backend.find_by_euid(session,template_code=EXTERNAL_OBJECT_RELATION_TEMPLATE,euid=receipt['external_object_relation_euid'])
 endpoints=resolve_relation_endpoints(session,relation)
 assert endpoints.source.euid==command['owner_request']['target_euid']
 assert endpoints.external_object.euid==receipt['external_object_euid']
 r=backend.find_by_euid(session,template_code=REGISTRATION_RECEIPT_TEMPLATE,euid=receipt['registration_receipt_euid'])
 assert r.json_addl['principal_id']==principal.principal_id
 assert len(backend.list_parents(session,child=r,relationship_type='has_registration_receipt'))==3
 assert len(backend.list_children(session,parent=endpoints.source,relationship_type='labcore_sequencing_run'))==1
result={'status':'passed','mode':mode,'synthetic':True,'receipt':a.json(),'artifact_euid':command['owner_request']['target_euid'],'search_seconds':s.elapsed.total_seconds(),'codes':[a.status_code,b.status_code,409],'runtime_temp':False}
(state/(mode+'-acceptance.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
