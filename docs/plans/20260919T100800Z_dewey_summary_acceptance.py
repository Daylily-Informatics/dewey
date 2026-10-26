"""One read-only observation per GUI backend route using existing OWY authority."""
import hashlib
import json
import os
import pwd
import socket
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("Redirect refused")


if pwd.getpwuid(os.getuid()).pw_name != "sysman" or socket.gethostname() != "sfo1-xfer1.sfo.lsmc.com":
    raise RuntimeError("Existing sysman transfer-host authority required")
if os.environ.get("AWS_PROFILE") != "lsmc":
    raise RuntimeError("Expected configured lsmc profile")
token = os.environ.get("OWY_DEWEY_API_TOKEN", "").strip()
if not token:
    raise RuntimeError("Configured OWY Dewey credential unavailable")
receipt = {
    "schema": "dewey.gui-backend-route-observation/1",
    "host": socket.gethostname(), "uid": os.getuid(),
    "credential_source_reference": "/home/sysman/.config/offwithyou/owy-dayhoff-env",
    "auth_scheme": "existing OWY_DEWEY_API_TOKEN bearer",
    "credential_values_or_hashes_recorded": False,
    "requests": [], "owner_or_runtime_mutations": False,
    "scope": "one normal public read per route; POST registry/search is read-only",
}
opener = build_opener(NoRedirect())

receipt["schema"]="dewey.gui-summary-production-acceptance/1"
receipt["source_tag"]="10.0.7"
receipt["source_commit"]="8d04719a6ad82a6808bf38933b39cadb210b43d0"
values={}
queries=[]
for label,scopes in (("library",["artifact","artifact_set"]),("sets",["artifact_set"])):
 payload={"q":"","page":1,"page_size":25,"scopes":scopes,"property_filters":[],"sort_field":"created_at","sort_dir":"desc"}
 queries.append((label+"_summary","POST","/api/v1/registry/search",{**payload,"projection":"summary"}))
 queries.append((label+"_full","POST","/api/v1/registry/search",payload))
queries.append(("p1_registered_set","GET","/api/v1/records/M-DGX-VVW1",None))
for label,method,path,payload in queries:
 started=time.perf_counter();row={"label":label,"method":method,"path":path,"request":payload,"started_at":datetime.now(timezone.utc).isoformat()}
 try:
  request=Request("https://dewey.day.lsmc.bio"+path,method=method,data=json.dumps(payload).encode() if payload is not None else None,headers={"Authorization":"Bearer "+token,"X-LSMC-Service-ID":"offwithyou-seqnas-xfer","Accept":"application/json","Content-Type":"application/json"})
  try: response=opener.open(request,timeout=90)
  except HTTPError as error: response=error
  with response:
   row["status"]=response.status;row["time_to_headers_ms"]=round((time.perf_counter()-started)*1000,3)
   raw=response.read(24*1024*1024+1);row["source_date"]=response.headers.get("Date")
  if len(raw)>24*1024*1024:raise RuntimeError("Responsebound exceeded")
  row.update(duration_ms=round((time.perf_counter()-started)*1000,3),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  value=json.loads(raw);values[label]=value
  row["response_fields"]=sorted(value);row["counts"]={k:len(v) for k,v in value.items() if isinstance(v,list)}
  row["summary"]={k:value[k] for k in ("total","page","page_size","has_more","timing_ms","member_count","euid","kind","facets","capabilities","projection") if k in value}
  if row["status"]!=200:row["error"]={k:value[k] for k in ("detail","code") if k in value}
 except Exception as error:row.update(error_type=type(error).__name__,duration_ms=round((time.perf_counter()-started)*1000,3))
 row["finished_at"]=datetime.now(timezone.utc).isoformat();receipt["requests"].append(row)
receipt["parity"]={}
for label in ("library","sets"):
 summary,full=values.get(label+"_summary",{}),values.get(label+"_full",{})
 rows=summary.get("items",[]);fullrows=full.get("items",[])
 same_ids=[r.get("euid") for r in rows]==[r.get("euid") for r in fullrows]
 parity={"same_row_ids_and_order":same_ids,"complete_count_page_facets_equal":all(summary.get(k)==full.get(k) for k in ("facets","total","page","page_size","has_more")),"explicit_summary_projection":summary.get("projection")=="summary","full_response_keeps_historical_shape":"projection" not in full}
 if same_ids:
  parity["every_returned_table_field_matches_full"]=all(all(k in f and f[k]==v for k,v in s.items()) for s,f in zip(rows,fullrows))
  parity["visible_member_counts_match_full_distinct_members"]=all(s.get("member_count")==len({m["artifact_euid"] for m in f["members"]}) for s,f in zip(rows,fullrows) if s.get("kind")=="set")
 parity["summary_contains_no_members_or_external_details"]=all(not any(k in r for k in ("members","artifact_euids","external_objects","metadata")) for r in rows)
 receipt["parity"][label]=parity
receipt["detail"]= {"same_persisted_set":values.get("p1_registered_set",{}).get("euid")=="M-DGX-VVW1","visible_member_count":values.get("p1_registered_set",{}).get("member_count"),"actual_returned_member_count":len(values.get("p1_registered_set",{}).get("members",[])),"capabilities":values.get("p1_registered_set",{}).get("capabilities")}
print(json.dumps(receipt,sort_keys=True))
