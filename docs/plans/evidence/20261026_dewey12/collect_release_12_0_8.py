from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,urllib.request
ROOT=Path("/home/ubuntu/dewey12-release-20261026T021700Z")
REPO=ROOT/"repos-12.0.8/dewey"
SHA="c8a73360fcb6b908c2e575cb381e359dd425f838"
def run(args):return subprocess.check_output(args,text=True)
def write(name,value):
    (ROOT/name).open("x").write(json.dumps(value,indent=2)+"\n")
def snapshot():
    ids=run(["docker","ps","-aq","--filter","label=com.docker.compose.project=dayhoff-day"]).split()
    out={}
    for r in json.loads(run(["docker","inspect",*ids])):
        if r["Config"]["Labels"].get("com.docker.compose.oneoff","").lower()=="true":continue
        svc=r["Config"]["Labels"]["com.docker.compose.service"]
        assert svc not in out
        out[svc]={"id":r["Id"],"name":r["Name"],"image":r["Config"]["Image"],"image_id":r["Image"],"running":r["State"]["Running"],"started_at":r["State"]["StartedAt"],"restart_count":r["RestartCount"]}
    return out
before=json.loads((ROOT/"runtime-before-12.0.8.json").read_text());after=snapshot()
assert len(before)==len(after)==13
unchanged={k:before[k]==after[k] for k in before if k!="dewey"}
assert len(unchanged)==12 and all(unchanged.values())
assert after["dewey"]["running"] and after["dewey"]["restart_count"]==0 and after["dewey"]["id"]!=before["dewey"]["id"]
image=json.loads((ROOT/"image-verified-12.0.8.json").read_text())
assert after["dewey"]["image"]==image["image"]
assert run(["git","-C",str(REPO),"rev-parse","HEAD"]).strip()==SHA
assert run(["git","-C",str(REPO),"status","--porcelain"]).strip()==""
assert run(["git","-C",str(REPO),"rev-parse","12.0.8^{}"]).strip()==SHA
files=run(["git","-C",str(REPO),"ls-tree","-r","--name-only","HEAD","--","dewey_service"]).splitlines()
expected={f:hashlib.sha256((REPO/f).read_bytes()).hexdigest() for f in files}
pc="from pathlib import Path;import hashlib,json; p=Path('/app');print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'dewey_service').rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ('.pyc','.pyo')}))"
actual=json.loads(run(["docker","exec","dayhoff-day-dewey-1","/app/.venv/bin/python","-c",pc]))
assert len(expected)==113 and actual==expected
mounts=json.loads(run(["docker","inspect","--format","{{json .Mounts}}","dayhoff-day-dewey-1"]))
assert not any(m["Destination"]=="/app" or m["Destination"].startswith("/app/dewey_service") for m in mounts)
ready=json.loads((ROOT/"ready-12.0.8.json").read_text())
assert ready["ready"] and ready["status"]=="ok" and ready["build"]=={"version":"12.0.8","sha":SHA}
assert "sharing_schema" not in ready and ready["checks"]["database"]["details"]["sharing_schema"]=="verified"
req=urllib.request.Request("http://127.0.0.1:8914/healthz",headers={"Host":"dewey.day.lsmc.bio"})
with urllib.request.urlopen(req,timeout=20) as res:
    assert res.status==200
    health=json.load(res)
assert health["build"]=={"version":"12.0.8","sha":SHA} and health["status"]=="ok"
at=datetime.now(timezone.utc).isoformat()
binding={"observed_at":at,"version":"12.0.8","source_commit":SHA,"file_count":len(expected),"all_files_match":True,"no_source_override_mounts":True,"files":actual}
write("running-source-binding-12.0.8.json",binding)
siblings={"observed_at":at,"unchanged_count":12,"includes_login":True,"all_unchanged":True,"differences":[],"before":{k:before[k] for k in unchanged},"after":{k:after[k] for k in unchanged}}
write("sibling-invariance-12.0.8.json",siblings)
provenance={"observed_at":at,"instance":"i-07df3a933e4839f52","region":"us-west-2","version":"12.0.8","source_commit":SHA,"tag_object":"0f3513b8bdad207db3c49f2c935a0e44eb0c897b","runtime":after["dewey"],"image_verification":image,"readyz":ready,"healthz":health,"source_files_verified":113,"siblings_unchanged":12,"validation_reused":{"main_commit":"74b426b82829be852f128b9541c38d49ea05c983","ci_run":40399463503,"runtime_build_lock_inputs_identical":True}}
write("running-provenance-12.0.8.json",provenance)
print(json.dumps({"provenance":provenance,"binding":binding,"siblings":siblings}))
