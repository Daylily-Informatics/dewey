"""Focused real native defaults routes over capture persistence; zero network."""
import json
from pathlib import Path
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates
from dewey_service.registry_api import attach_registry_api
from dewey_service.registry_access import Principal,principal,principal_context
from capture_defaults import CaptureService

service=CaptureService();app=FastAPI();app.state.service=service
actor=Principal(subject='capture-admin',email='admin@example.test',roles=('ADMIN',),email_verified=True)
app.state.settings=SimpleNamespace(share_trusted_proxy_peer='testclient',share_ingress_assertion='capture-private-assertion',share_ingress_assertion_header='X-Capture-Private')
app.dependency_overrides[principal]=lambda:actor
@app.middleware('http')
async def context(request,call_next):
    request.state.registry_principal=actor;request.state.public_recipient=False;request.state.trusted_tailnet=True
    with principal_context(actor):
        return await call_next(request)
templates=Jinja2Templates(directory=str(Path('dewey_service/templates').resolve()))
attach_registry_api(app,templates=templates)
with TestClient(app,base_url='https://dewey.example.test') as client:
    before=client.get('/api/v1/registry/defaults');assert before.status_code==200 and before.json()['share_lifetime_days']==30
    patch=client.patch('/api/v1/registry/defaults',json={'share_lifetime_days':None});assert patch.status_code==200,patch.text
    current=client.get('/api/v1/registry/defaults');assert current.json()['share_lifetime_days'] is None
    assert current.json()['delivery_lifetime_seconds']==900
    bad=client.patch('/api/v1/registry/defaults',json={'delivery_lifetime_seconds':None});assert bad.status_code==422
    finite=client.patch('/api/v1/registry/defaults',json={'share_lifetime_days':14});assert finite.status_code==200 and finite.json()['share_lifetime_days']==14
print(json.dumps({'status':'PASS','native_http_before':30,'native_http_patch_null':patch.json()['share_lifetime_days'],'native_http_get_null':current.json()['share_lifetime_days'],'explicit_finite_default':14,'delivery_null_http_status':bad.status_code,'network_calls':0}))
