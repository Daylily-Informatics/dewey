"""Focused capture of native nullable defaults and domain-neutral explicit expiry.

No pytest, provider requests, database, credentials, or email dispatch.
"""
import json
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError
from dewey_service.registry_api import RegistryDefaultsUpdate, ShareRequest
from dewey_service.registry_access import Principal, principal_context
from dewey_service.services.registry import RegistryServiceMixin
from dewey_service.services.sharing import SharingServiceMixin
from dewey_service.services.share_policy import UNSET, normalized_policy


class CaptureBackend:
    def __init__(self):
        self.row = SimpleNamespace(euid='capture-defaults',name='Capture defaults',
            created_dt=datetime.now(timezone.utc),modified_dt=datetime.now(timezone.utc),
            json_addl={'properties':{},'action_groups':{},'audit_log':[],
                       'share_lifetime_days':30,'delivery_lifetime_seconds':900,'listing_cache_ttl_seconds':30})
        self.changes=[]
    @contextmanager
    def session_scope(self, *, commit):
        yield object()
    def find_by_json_field(self,*args,**kwargs):return self.row
    def lock_external_key(self,*args,**kwargs):pass
    def update_instance_json(self,session,row,changes):
        self.changes.append(deepcopy(changes));row.json_addl.update(changes)


class CaptureService(RegistryServiceMixin,SharingServiceMixin):
    def __init__(self):
        self.backend=CaptureBackend();self.storage=None;self.share_max_lifetime_days=3650;self.events=[]
    def _registry_event(self,session,row,action):self.events.append(action)


def main():
    service=CaptureService();before=service.registry_defaults()
    assert before['share_lifetime_days']==30
    actor=Principal(subject='capture-admin',email='admin@example.test',roles=('ADMIN',),email_verified=True)
    stored_finite={'expires_at':(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}
    original=deepcopy(stored_finite)
    with principal_context(actor):
        data=RegistryDefaultsUpdate(share_lifetime_days=None).model_dump(exclude_unset=True)
        result=service.update_registry_defaults(data)
    assert data=={'share_lifetime_days':None} and result['share_lifetime_days'] is None
    assert service.registry_defaults()['share_lifetime_days'] is None
    assert result['delivery_lifetime_seconds']==900 and result['listing_cache_ttl_seconds']==30
    assert service._normalize_share_expiry(UNSET) is None and service._normalize_share_expiry(None) is None
    assert stored_finite==original
    finite=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    assert service._normalize_share_expiry(finite)==finite
    domain_cases=[]
    for domain in ['lsmc.com','lsmc.bio','external.example']:
        for recipient_type,recipient in [('domain',domain),('email','viewer@'+domain)]:
            policy=normalized_policy({'grants':[{'recipient_type':recipient_type,'recipient':recipient,'expires_at':finite}]},share_expiry=None,member_euids=['capture-persisted-object'])
            assert policy['grants'][0]['expires_at']==finite
            inherited=normalized_policy({'grants':[{'recipient_type':recipient_type,'recipient':recipient}]},share_expiry=None,member_euids=['capture-persisted-object'])
            assert inherited['grants'][0]['expires_at'] is None
            domain_cases.append(recipient)
    rejected=0
    for payload in [{'share_lifetime_days':0},{'share_lifetime_days':True},{'share_lifetime_days':'30'},{'delivery_lifetime_seconds':None},{'listing_cache_ttl_seconds':None}]:
        try:RegistryDefaultsUpdate(**payload)
        except ValidationError:rejected+=1
        else:raise AssertionError(payload)
    for value in [(datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),(datetime.now(timezone.utc)+timedelta(days=3651)).isoformat(),'2030-01-01T00:00:00']:
        try:service._normalize_share_expiry(value)
        except ValueError:rejected+=1
        else:raise AssertionError(value)
    with principal_context(actor):
        service.update_registry_defaults({'share_lifetime_days':5})
    assert service.registry_defaults()['share_lifetime_days']==5
    assert service._normalize_share_expiry(UNSET) is not None
    assert ShareRequest().model_dump(exclude_unset=True)=={}
    assert ShareRequest(expires_at=None).model_dump(exclude_unset=True)=={'expires_at':None}
    assert ShareRequest(lifetime_days=None).model_dump(exclude_unset=True)=={'lifetime_days':None}
    result={'status':'PASS','before_native_days':30,'patch_null_native_days':result['share_lifetime_days'],
        'persisted_finite_share_unchanged':stored_finite==original,'native_finite_default_still_settable':5,
        'explicit_share_and_grant_domain_cases':domain_cases,'negative_validation_cases':rejected,
        'network_calls':0,'mail_sent':0,'pytest':False}
    print(json.dumps(result))


if __name__=='__main__':main()
