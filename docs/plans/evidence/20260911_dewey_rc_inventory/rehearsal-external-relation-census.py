from pathlib import Path
import collections, datetime, hashlib, json, os, sys
from sqlalchemy import text
from daylily_tapdb.cli.context import set_cli_context
from daylily_tapdb.cli.db_config import get_db_config
from daylily_tapdb.web.runtime import get_db, dispose_all_runtime_engines
from daylily_tapdb.euid import validate_euid

path=Path("/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml")
cfg=get_db_config(config_path=path,client_id="dewey",database_name="dewey-day")
assert cfg["database"]=="dewey_tapdb10_rehearsal_20260911" and cfg["user"]=="dewey_rehearsal_9"
set_cli_context(config_path=path,client_id="dewey",database_name="dewey-day")
db=get_db(str(path))
db.app_username="dewey-migration-census"
with db.session_scope(commit=False) as s:
    s.execute(text("SET TRANSACTION READ ONLY"))
    physical=dict(s.execute(text("SELECT current_database() AS database,current_user AS role,pg_backend_pid() AS pid")).mappings().one())
    allrows=[dict(x) for x in s.execute(text("SELECT uid,euid,category,type,subtype,is_deleted,tenant_id,domain_code FROM generic_instance")).mappings()]
    external=[dict(x) for x in s.execute(text("SELECT uid,euid,type,is_deleted,created_dt,tenant_id,json_addl FROM generic_instance WHERE category='integration' AND type IN ('external_object','external_object_relation')")).mappings()]
    lines=[dict(x) for x in s.execute(text("SELECT uid,euid,parent_instance_uid,child_instance_uid,relationship_type,is_deleted FROM generic_instance_lineage WHERE relationship_type IN ('has_external_relation','is_external_relation_for')")).mappings()]
    graphs=[dict(x) for x in s.execute(text("SELECT uid,euid,is_deleted,json_addl->'properties'->'external_payload'->'tapdb_graph' AS graph FROM generic_instance WHERE json_addl->'properties'->'external_payload' ? 'tapdb_graph'")).mappings()]
    templates=[dict(x) for x in s.execute(text("SELECT category,type,subtype,version,instance_prefix,is_deleted FROM generic_template WHERE category='reference'")).mappings()]
dispose_all_runtime_engines()
byuid={str(x["uid"]):x for x in allrows}
extuid={str(x["uid"]):x for x in external if x["type"]=="external_object"}
exts=[x for x in external if x["type"]=="external_object"]
rels=[x for x in external if x["type"]=="external_object_relation"]
def table(counter, fields):
    return [dict(zip(fields,key),count=count) for key,count in sorted(counter.items(),key=lambda v: str(v[0]))]
type_counts=collections.Counter()
metadata_shapes=collections.Counter()
for r in exts:
    p=r["json_addl"]
    type_counts[(p.get("external_system"),p.get("external_object_type"),r["is_deleted"],r["tenant_id"] is None,bool(validate_euid(str(p.get("external_object_id","")))))]+=1
    md=p.get("metadata")
    metadata_shapes[(p.get("external_system"),p.get("external_object_type"),tuple(sorted(md)) if isinstance(md,dict) else str(type(md).__name__))]+=1
pair_counts=collections.Counter()
errors=collections.Counter()
ref_index={}
for r in rels:
    p=r["json_addl"]
    edges=[l for l in lines if l["child_instance_uid"]==r["uid"]]
    has=[l for l in edges if l["relationship_type"]=="has_external_relation" and not l["is_deleted"]]
    via=[l for l in edges if l["relationship_type"]=="is_external_relation_for" and not l["is_deleted"]]
    if len(has)!=1 or len(via)!=1:
        errors[("parent_cardinality",r["is_deleted"],len(has),len(via))]+=1
        continue
    target=byuid.get(str(has[0]["parent_instance_uid"]))
    ext=extuid.get(str(via[0]["parent_instance_uid"]))
    if target is None or ext is None:
        errors[("missing_endpoint",r["is_deleted"],target is None,ext is None)]+=1
        continue
    ep=ext["json_addl"]
    if p.get("target_euid")!=target["euid"] or p.get("external_object_euid")!=ext["euid"]:
        errors[("denormalized_mismatch",r["is_deleted"],p.get("target_euid")==target["euid"],p.get("external_object_euid")==ext["euid"])]+=1
    pair_counts[(ep.get("external_system"),ep.get("external_object_type"),p.get("relation_type"),target["type"],r["is_deleted"],ext["is_deleted"],target["is_deleted"])]+=1
    ref_index[r["euid"]]=(target,ext,r)
graph_counts=collections.Counter()
graph_keys=collections.Counter()
graph_mismatch=collections.Counter()
for g in graphs:
    if not isinstance(g["graph"],list):
        graph_mismatch[("not_list",)]+=1
        continue
    graph_counts[("rows",g["is_deleted"])]+=1
    graph_counts[("entries",g["is_deleted"])]+=len(g["graph"])
    for ref in g["graph"]:
        if not isinstance(ref,dict):
            graph_mismatch[("entry_not_object",)]+=1
            continue
        graph_keys[(ref.get("source_field"),ref.get("system"),tuple(sorted(ref)))]+=1
        match=ref_index.get(ref.get("external_object_relation_euid"))
        if match is None:
            graph_mismatch[("missing_authoritative_relation",ref.get("source_field"),ref.get("system"))]+=1
            continue
        t,e,r=match
        ep=e["json_addl"];rp=r["json_addl"]
        checks={"target":t["uid"]==g["uid"],"external_object":e["euid"]==ref.get("external_object_euid"),"system":ep.get("external_system")==ref.get("system"),"external_identity":ep.get("external_object_id")==ref.get("root_euid"),"relationship":rp.get("relation_type")==ref.get("relationship_type")}
        for field,good in checks.items():
            if not good:graph_mismatch[("mismatch",field)]+=1
duplicate_assertions=collections.Counter()
for t,e,r in ref_index.values():
    if not any(x["is_deleted"] for x in (t,e,r)):
        ep=e["json_addl"];rp=r["json_addl"]
        duplicate_assertions[(t["euid"],ep.get("external_system"),ep.get("external_object_type"),ep.get("external_object_id"),rp.get("relation_type"))]+=1
result={
"kind":"dewey_historical_external_relation_census_v1","captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"physical":physical,
"visible_instances":len(allrows),"external_objects":len(exts),"relation_objects":len(rels),"authoritative_lineages":len(lines),
"external_type_counts":table(type_counts,["system","object_type","deleted","null_tenant","identifier_validates_as_euid"]),
"external_metadata_key_shapes":table(metadata_shapes,["system","object_type","metadata_keys"]),
"relation_type_counts":table(pair_counts,["system","object_type","relationship","target_type","relation_deleted","external_deleted","target_deleted"]),
"endpoint_issues":[{"issue":list(k),"count":v} for k,v in errors.items()],
"graph_counts":[{"measure":k[0],"deleted":k[1],"count":v} for k,v in graph_counts.items()],
"graph_entry_key_shapes":table(graph_keys,["source_field","system","keys"]),
"graph_issues":[{"issue":list(k),"count":v} for k,v in graph_mismatch.items()],
"duplicate_native_assertion_groups":sum(v>1 for v in duplicate_assertions.values()),
"native_templates":templates
}
out=Path("/run/dewey-acceptance-output/external-relation-census.json")
data=(json.dumps(result,indent=2,sort_keys=True,default=str)+"\n").encode()
with os.fdopen(os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"wb") as h:
    h.write(data);h.flush();os.fsync(h.fileno())
print(json.dumps({"receipt":str(out),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}))
