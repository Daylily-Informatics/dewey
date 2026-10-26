#!/usr/bin/env python3
import os,secrets,sys,yaml
from pathlib import Path
p=Path(sys.argv[1]); assert str(p)=='/opt/dewey/day/releases/9.1.0/dewey-config.yaml'
c=yaml.safe_load(p.read_text()); assert not c.get('labcore_owner',{}).get('api_enabled')
assert not c.get('labcore_owner',{}).get('service_principals')
c['labcore_owner']={'api_enabled':True,'service_principals':[{
 'principal_id':'labcore-synthetic-acceptance-910',
 'bearer_token':secrets.token_urlsafe(48),
 'tenant_euid':'synthetic-labcore-tenant-910',
 'scopes':['dewey.labcore-owner.write/v1']}]}
p.write_text(yaml.safe_dump(c,sort_keys=False)); os.chmod(p,0o640)
print('Configured scoped synthetic Labcore acceptance principal; token redacted.')
