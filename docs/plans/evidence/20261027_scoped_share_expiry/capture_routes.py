"""Focused actual native HTTP-route captures over an isolated in-memory backend.

No cloud, mail, database, pytest or lint. Authentication/target ACL transports
are captured; native expiry, grant normalization, revision and revival execute.
"""
import copy
import sys
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import QueryParams
from dewey_service.registry_api import attach_registry_api
from dewey_service.registry_access import Principal,principal,principal_context
from dewey_service.services.sharing import SharingServiceMixin
from dewey_service.services.registry import RegistryServiceMixin
from dewey_service.services.share_expiry import lifetime_policy,normalize_lifetime,validate_activation_generation,validate_access_package
from dewey_service.services.share_policy import UNSET
from dewey_service.share_context import share_context_context
from dewey_service.tapdb_backend import normalize_instance_payload

checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def later(days):return (datetime.now(timezone.utc)+timedelta(days=days)).isoformat()
def node(label,kind,payload):return SimpleNamespace(euid=label,uid=label,type=kind,domain_code='capture',name=payload.get('name',label),bstatus='active',json_addl={'properties':{},**payload},created_dt=None,modified_dt=None)
class Backend:
    def __init__(self):self.nodes={};self.edges=[];self.domain_code='capture'
    @contextmanager
    def session_scope(self,commit):
        previous=copy.deepcopy((self.nodes,self.edges))
        try:yield self
        except Exception:
            self.nodes,self.edges=previous
            raise
    def create_instance(self,session,template_code,name,json_addl):
        kind=template_code.split('/')[1];label='captured-'+kind+'-'+str(len(self.nodes));r=node(label,kind,{'name':name,**json_addl});self.nodes[label]=r;return r
    def create_lineage(self,session,parent,child,relationship_type):self.edges.append((parent.euid,child.euid,relationship_type))
    def update_instance_json(self,session,row,changes):row.json_addl={**row.json_addl,**changes}
    def refresh(self,row):pass
    def find_by_euid(self,session,template_code,euid,**kwargs):return self.nodes.get(euid)
    def find_by_json_field(self,session,template_code,field,value,**kwargs):return next((n for n in self.nodes.values() if n.json_addl.get(field)==value),None)
    def lock_external_key(self,*args,**kwargs):pass
class Service(SharingServiceMixin,RegistryServiceMixin):
    share_max_lifetime_days=365
    def __init__(self):
        self.backend=Backend();self.dispatches=0;self.delegations=0;self.storage=None
        defaults=node('captured-defaults','registry_policy',{'policy_kind':'service_defaults','share_lifetime_days':None,'delivery_lifetime_seconds':900,'listing_cache_ttl_seconds':15});self.backend.nodes[defaults.euid]=defaults
        self.target=node('captured-object','artifact',{'storage_kind':'object','name':'Report.html','bucket':'capture','key':'Report.html','filename':'Report.html','size':4});self.backend.nodes[self.target.euid]=self.target
    def _require_sharing(self):pass
    def _registry_record(self,session,euid,**kwargs):return self.backend.nodes[euid]
    def _canonical_share(self,session,euid,**kwargs):
        r=self.backend.nodes.get(euid)
        if r is None or r.type!='share':raise HTTPException(404,'Capture share missing')
        return r
    def _share_related(self,session,share,relationship,kind):return [self.backend.nodes[c] for p,c,r in self.backend.edges if p==share.euid and r==relationship and self.backend.nodes[c].type==kind]
    def _share_grants(self,session,share):return self._share_related(session,share,relationship='share_grant',kind='share_grant')
    def _grant_targets(self,session,grant):return [self.backend.nodes[c] for p,c,r in self.backend.edges if p==grant.euid and r=='share_grant_target']
    def _share_members(self,session,share):
        revision=self._share_revision(session,share);return self._share_related(session,revision,relationship='share_revision_target',kind='artifact')
    def _share_response(self,share):return {**normalize_instance_payload(share),'share_euid':share.euid}
    def _artifact_member_from_instance(self,target,**kwargs):return {'artifact_euid':target.euid,'target_kind':'artifact_object','filename':'Report.html','bucket':'capture','key':'Report.html','size':4}
    def _expand_share_targets(self,*args,**kwargs):return [self._artifact_member_from_instance(self.target)]
    def _assert_share_delegation(self,*args):self.delegations+=1
    def _protected_share_path(self,*args,**kwargs):pass
    def _idempotency_replay(self,*args,**kwargs):return None
    def _store_idempotency(self,*args,**kwargs):pass
    def _fingerprint(self,value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    def _notification_rows(self,session,share):return [r for r in self._share_related(session,share,relationship='has_storage_operation',kind='storage_operation') if normalize_instance_payload(r).get('operation')=='share_notification']
    def _dispatch_share_notifications(self,euid):self.dispatches+=1;return []
    def _share_aliases(self,session,share):return [{'slug':r.json_addl['slug'],'status':r.json_addl['status'],'alias_euid':r.euid} for r in self._share_related(session,share,relationship='capture_alias',kind='share_alias')]
    def _find_share_alias(self,session,slug,**kwargs):return next((r for r in self.backend.nodes.values() if r.type=='share_alias' and r.json_addl['slug']==slug),None)
    def resolve_share_identifier(self,identifier):
        share=self._canonical_share(None,identifier);self._require_recipient(None,share);d=normalize_instance_payload(share)
        return {'share_euid':identifier,'policy_revision':d['policy_revision'],'activation_generation':d.get('activation_generation',0),'content_mode':'download','members':[],'namespaced':False}
service=Service();app=FastAPI();app.state.service=service;app.state.settings=SimpleNamespace()
actors={'internal':Principal(subject='creator-internal',email='owner@lsmc.com',roles=('ADMIN',),email_verified=True),
        'external':Principal(subject='creator-external',email='outside@example.net',roles=('ADMIN',),email_verified=True),
        'other-admin':Principal(subject='other-admin',email='other@lsmc.bio',roles=('ADMIN',),email_verified=True),
        'reader':Principal(subject='reader',email='reader@lsmc.bio',roles=('READ_ONLY',),email_verified=True),
        'stranger':Principal(subject='stranger',email='stranger@example.net',roles=('READ_ONLY',),email_verified=True)}
@app.middleware('http')
async def capture_identity(request,call_next):
    actor=actors[request.headers.get('x-capture-actor','internal')]
    request.state.trusted_tailnet=True
    request.state.public_recipient=False
    with principal_context(actor),share_context_context({'request_id':'capture-request','trusted_tailnet':True,'managed_origin':True}):return await call_next(request)
attach_registry_api(app,templates=SimpleNamespace())
client=TestClient(app);seq=0
def request(method,path,body=None,actor='internal'):
    global seq
    seq+=1;return client.request(method,path,json=body,headers={'x-capture-actor':actor,'Idempotency-Key':'capture-'+str(seq)})
def create(body,actor='internal'):
    response=request('POST','/api/v1/records/captured-object/shares',body,actor)
    return response
internal={'allowed_users':['reader@lsmc.bio']}
outside={'allowed_users':['someone@example.net']}
# Actual defaults route truthfully exposes scoped policy with legacy setting.
r=request('GET','/api/v1/registry/defaults');check('native defaults historical null cannot authorize global infinity',r.status_code==200 and r.json()['share_lifetime_days'] is None and r.json()['share_expiry_policy']['bounded_default_lifetime_days']==14 and r.json()['share_expiry_policy']['internal_default_lifetime_days'] is None)
r=request('PATCH','/api/v1/registry/defaults',{'delivery_lifetime_seconds':1200,'listing_cache_ttl_seconds':20});check('native delivery and listing controls remain editable',r.status_code==200 and r.json()['delivery_lifetime_seconds']==1200 and r.json()['listing_cache_ttl_seconds']==20)
# Actual native creation and preview endpoints, omitted/null are distinct.
r=create(internal);check('create internal omitted expiry is indefinite',r.status_code==201 and r.json()['expires_at'] is None);internal_id=r.json()['euid']
r=create({**internal,'expires_at':later(900)});check('internal explicit finite beyond365days permitted',r.status_code==201)
r=create(outside);check('create external omitted default14days',r.status_code==201 and 13.99<(datetime.fromisoformat(r.json()['expires_at'])-datetime.now(timezone.utc)).total_seconds()/86400<14.01)
check('create external explicit null rejected',create({**outside,'expires_at':None}).status_code==400)
check('create mixed null rejected',create({'allowed_users':['reader@lsmc.bio','x@example.net'],'expires_at':None}).status_code==400)
check('create external366days rejected',create({**outside,'expires_at':later(366)}).status_code==400)
check('create external365days allowed',create({**outside,'expires_at':later(365)}).status_code==201)
check('external creator internal audience null rejected',create({**internal,'expires_at':None},'external').status_code==400)
r=create(internal,'external');check('external creator internal audience defaults14days',r.status_code==201 and r.json()['expires_at'] is not None);external_id=r.json()['euid']
check('internal explicit lifetime_days800 allowed',create({**internal,'lifetime_days':800}).status_code==201)
check('bounded explicit lifetime_days366 rejected',create({**outside,'lifetime_days':366}).status_code==400)
check('exact internal domains eligible',create({'allowed_domains':['lsmc.com','lsmc.bio'],'expires_at':None}).status_code==201)
check('subdomain audience bounded',create({'allowed_domains':['lab.lsmc.com'],'expires_at':None}).status_code==400)
check('explicit include-subdomains bounded',create({'grants':[{'recipient_type':'domain','recipient':'lsmc.bio','include_subdomains':True}],'expires_at':None}).status_code==400)
check('public registration bounded',create({'audience':'public_registered','expires_at':None}).status_code==400)
for body,expected in [(internal,200),({**outside,'expires_at':None},400),({'allowed_users':['reader@lsmc.bio','x@example.net'],'expires_at':None},400),({**outside,'expires_at':later(366)},400)]:
    response=request('POST','/api/v1/records/captured-object/shares/preview',body);check('actual preview route policy '+str(len(checks)),response.status_code==expected)
# Actual update route cannot substitute an editor's identity for the creator.
r=request('PATCH','/api/v1/registry/shares/'+external_id,{'policy_revision':1,'expires_at':None},'other-admin');check('internal admin cannot unlimited external-created share',r.status_code==400)
r=request('PATCH','/api/v1/registry/shares/'+external_id,{'policy_revision':1,'name':'Explicit metadata edit'},'other-admin');check('external-created finite deadline retained on metadata edit',r.status_code==200 and r.json()['expires_at'] is not None)
r=request('PATCH','/api/v1/registry/shares/'+internal_id,{'policy_revision':1,'allowed_users':['reader@lsmc.bio','x@example.net']});check('mixed audience edit bounds prior indefinite default14days',r.status_code==200 and r.json()['expires_at'] is not None)
r=request('PATCH','/api/v1/registry/shares/'+internal_id,{'policy_revision':2,'expires_at':None});check('mixed update explicit null rejected',r.status_code==400)
# Original creator verification comes from native creation event when no snapshot.
r=create(internal);legacy_id=r.json()['euid'];legacy=service.backend.nodes[legacy_id];legacy.json_addl.pop('creator_email_verified');legacy.json_addl.pop('creator_service')
r=request('GET','/api/v1/registry/shares/'+legacy_id);check('historical original creator proof recovered from created event',r.status_code==200 and r.json()['expiry_policy']['creator']['proof']=='native_created_event' and r.json()['expiry_policy']['indefinite_allowed'])
# Global lifetime edits are unsupported in the actual native defaults API.
check('global lifetime null rejected',request('PATCH','/api/v1/registry/defaults',{'share_lifetime_days':None}).status_code==422)
check('global lifetime30 rejected',request('PATCH','/api/v1/registry/defaults',{'share_lifetime_days':30}).status_code==422)
# Revival: explicit prior recipients, old individual revocation, contexts, aliases.
r=create({'allowed_users':['reader@lsmc.bio','revoked@lsmc.com'],'denied_emails':['denied@lsmc.bio']});revive_id=r.json()['euid'];share=service.backend.nodes[revive_id]
grants=service._share_grants(None,share);good=next(g for g in grants if g.json_addl['recipient']=='reader@lsmc.bio');bad=next(g for g in grants if g!=good)
bad.json_addl['status']='revoked';bad.json_addl['revoked_at']='preserved-original-revocation'
alias=node('captured-alias','share_alias',{'slug':'captured-readable','status':'active'});service.backend.nodes[alias.euid]=alias;service.backend.edges.append((revive_id,alias.euid,'capture_alias'))
context=node('captured-context','storage_operation',{'operation':'isolated_report_context','status':'active','expires_at':later(1)});service.backend.nodes[context.euid]=context;service.backend.edges.append((revive_id,context.euid,'has_storage_operation'))
with principal_context(actors['internal']):
    package=service.create_share_access_package(revive_id)
    cursor=service._save_listing_cursor(None,share,'captured-old-policy-context',{'member_index':0,'s3_token':None})
check('access package includes policy and activation pins','policy_revision=1&activation_generation=0' in package['browser_path'])
r=request('POST','/api/v1/registry/shares/'+revive_id+'/revoke',{'policy_revision':1,'reason':'Capture revoke'});check('actual revoke route',r.status_code==200)
check('ordinary update cannot revive',request('PATCH','/api/v1/registry/shares/'+revive_id,{'policy_revision':2,'expires_at':later(2)}).status_code==400)
check('revival requires explicit new finite expiry',request('POST','/api/v1/registry/shares/'+revive_id+'/revive',{'policy_revision':2,'expires_at':None,'grant_euids':[good.euid],'reason':'Capture'}).status_code==422)
check('revival cannot restore revoked recipient',request('POST','/api/v1/registry/shares/'+revive_id+'/revive',{'policy_revision':2,'expires_at':later(2),'grant_euids':[bad.euid],'reason':'Capture'}).status_code==400)
check('revival requires reviewed revision',request('POST','/api/v1/registry/shares/'+revive_id+'/revive',{'policy_revision':1,'expires_at':later(2),'grant_euids':[good.euid],'reason':'Capture'}).status_code==409)
check('revival requires management authorization',request('POST','/api/v1/registry/shares/'+revive_id+'/revive',{'policy_revision':2,'expires_at':later(2),'grant_euids':[good.euid],'reason':'Capture'},'stranger').status_code==403)
dispatches=service.dispatches;r=request('POST','/api/v1/registry/shares/'+revive_id+'/revive',{'policy_revision':2,'expires_at':later(800),'grant_euids':[good.euid],'reason':'Explicit captured recipient review'})
check('internal inactive share explicitly revives with finite800days',r.status_code==200);after=r.json();share=service.backend.nodes[revive_id]
check('revival increments revision and activation',after['policy_revision']==3 and after['activation_generation']==1)
check('revival does not dispatch or prepare new mail',service.dispatches==dispatches and all(o.json_addl.get('status')!='pending' for o in service._notification_rows(None,share)))
check('denied rules preserved',after['denied_emails']==['denied@lsmc.bio'])
check('old revoked grant receipt preserved',service.backend.nodes[bad.euid].json_addl['status']=='revoked' and service.backend.nodes[bad.euid].json_addl['revoked_at']=='preserved-original-revocation')
check('old alias retired',service.backend.nodes[alias.euid].json_addl['status']=='retired')
check('old preview context permanently revoked',service.backend.nodes[context.euid].json_addl['status']=='revoked')
check('old listing cursor rejected at actual contents route',request('GET','/api/v1/registry/shares/'+revive_id+'/contents?continuation_token='+cursor).status_code==409)
from dewey_service.share_exports import _pinned_entry
class OldArchive:
    def authorize_share_object(self,*args,**kwargs):return {'policy_revision':after['policy_revision']}
try:_pinned_entry(OldArchive(),{'share_euid':revive_id,'policy_revision':1,'members':[]},{'target_euid':'captured-object','relative_key':''})
except HTTPException as exc:check('old TAR inventory revision rejected before storage access',exc.status_code==409)
else:raise AssertionError('old archive inventory was accepted')

check('only selected recipient reauthorized',[g['recipient'] for g in after['grants'] if g['status']=='active']==['reader@lsmc.bio'])
events=service._share_related(None,share,relationship='share_event',kind='share_event');last=normalize_instance_payload(events[-1])
check('revival audit retains previous inactive receipt',last['event_type']=='revived' and last['details']['previous_status']=='revoked' and last['details']['previous_policy_revision']==2)
with patch('dewey_service.fetch.manifest_page',return_value={'items':[],'continuation_token':None,'incomplete':False}):
    check('old access package cannot regain validity at actual fetch route',request('GET',package['manifest_path'],actor='reader').status_code==410)
    with principal_context(actors['internal']):fresh=service.create_share_access_package(revive_id)
    check('fresh access package reauthorizes actual fetch route',request('GET',fresh['manifest_path'],actor='reader').status_code==200)
    check('ordinary canonical locator still requires current grant',request('GET','/fetch/'+revive_id+'?format=manifest',actor='stranger').status_code==403)
try:validate_activation_generation({'share_activation_generation':0},{'activation_generation':1})
except HTTPException as exc:check('old preview generation is fenced',exc.status_code==410)
else:raise AssertionError('old preview generation accepted')
# Bounded revival is measured from current time, not the previous expiration.
r=create(internal,'external');eid=r.json()['euid'];sg=service._share_grants(None,service.backend.nodes[eid])[0];request('POST','/api/v1/registry/shares/'+eid+'/revoke',{'policy_revision':1})
check('external-created revival cannot exceed365days',request('POST','/api/v1/registry/shares/'+eid+'/revive',{'policy_revision':2,'expires_at':later(366),'grant_euids':[sg.euid],'reason':'Capture'},'other-admin').status_code==400)
# Expired shares use the explicit revival route too; no normal edit reactivation.
r=create(internal);expired_id=r.json()['euid'];expired=service.backend.nodes[expired_id];expired.json_addl['expires_at']=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat();oldgrant=service._share_grants(None,expired)[0]
check('expired normal edit cannot reactivate',request('PATCH','/api/v1/registry/shares/'+expired_id,{'policy_revision':1,'expires_at':later(1)}).status_code==400)
check('expired share revival requires explicit selected recipient',request('POST','/api/v1/registry/shares/'+expired_id+'/revive',{'policy_revision':1,'expires_at':later(1),'grant_euids':[],'reason':'Capture'}).status_code==400)
check('expired share explicitly revives without expanding audience',request('POST','/api/v1/registry/shares/'+expired_id+'/revive',{'policy_revision':1,'expires_at':later(1),'grant_euids':[oldgrant.euid],'reason':'Capture expiry review'}).status_code==200)
# Existing outside infinity remains a visible exception pending explicit action.
r=create(outside);exception_id=r.json()['euid'];service.backend.nodes[exception_id].json_addl['expires_at']=None
r=request('GET','/api/v1/registry/shares/'+exception_id);check('preexisting outside noexpiry flagged for explicit review',r.status_code==200 and r.json()['expires_at'] is None and r.json()['expiry_policy']['requires_explicit_review'])
# Unknown/service/unverified creator proof never grants indefinite scope.
for creator in [{'email':'x@lsmc.com','email_verified':False,'service':False},{'email':'x@lsmc.com','email_verified':True,'service':True},{'email':'x@sub.lsmc.com','email_verified':True,'service':False}]:
    scope=lifetime_policy(creator,internal);check('unverified service subdomain creator bounded '+str(len(checks)),not scope['indefinite_allowed'] and scope['default_lifetime_days']==14)
receipt={'observed_at':datetime.now(timezone.utc).isoformat(),'status':'PASS','checks':checks,'check_count':len(checks),'actual_native_routes':['POST /api/v1/records/{euid}/shares','POST /api/v1/records/{euid}/shares/preview','PATCH /api/v1/registry/shares/{euid}','POST /api/v1/registry/shares/{euid}/revoke','POST /api/v1/registry/shares/{euid}/revive','PATCH /api/v1/registry/defaults','GET /fetch/{identifier}'],
 'external_network_calls':0,'mail_sends':0,'cloud_or_database_mutations':0,'limits':['Native TapDB backend, target ACL and authentication transport captured in memory; production persistence/browser acceptance remains separate.','Unversioned stable URLs are locators, not bearer access packages; every request requires current identity/grants.']}
Path(__file__).with_name('route_capture_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
