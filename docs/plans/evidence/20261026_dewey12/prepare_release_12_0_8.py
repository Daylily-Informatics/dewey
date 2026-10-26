from pathlib import Path
import copy, hashlib, json, os, pwd, re, subprocess, tomllib
ROOT=Path("/home/ubuntu/dewey12-release-20261026T021700Z")
LIVE=Path("/opt/dayhoff/deployments/day/compose/docker-compose.yml")
MANIFEST=Path("/opt/dayhoff/deployments/day/container-release-manifest.json")
EXPECTED_COMPOSE="a96e18fd4dac6d6a28500c31e7b84e44346e4509b0e506899c736005bf8c7572"
EXPECTED_MANIFEST="3d73c45eb8b2d360090fba4e71bba9ab28622d5756da17f9f0f5464cc98a2e0f"
CID="9a3e9079db4675d3cbf680c2c170a43d093d1a8298f68066b3214ef3a945825a"
assert os.geteuid()==0 and os.environ.get("SUDO_USER")=="ubuntu"
os.umask(0o077)
u=pwd.getpwnam("ubuntu")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value):
    p=ROOT/name
    with p.open("x") as f:f.write(value)
    os.chown(p,u.pw_uid,u.pw_gid)
assert sha(LIVE)==EXPECTED_COMPOSE and sha(MANIFEST)==EXPECTED_MANIFEST
old=json.loads((ROOT/"manifest-12.0.7.json").read_text())
assert old==json.loads(MANIFEST.read_text()) and len(old["images"])==8
ids=subprocess.check_output(["docker","ps","-aq","--filter","label=com.docker.compose.project=dayhoff-day"],text=True).split()
rows=json.loads(subprocess.check_output(["docker","inspect",*ids],text=True))
state={}
for r in rows:
    if r["Config"]["Labels"].get("com.docker.compose.oneoff","").lower()=="true":continue
    svc=r["Config"]["Labels"]["com.docker.compose.service"]
    assert svc not in state
    state[svc]={"id":r["Id"],"name":r["Name"],"image":r["Config"]["Image"],"image_id":r["Image"],"running":r["State"]["Running"],"started_at":r["State"]["StartedAt"],"restart_count":r["RestartCount"]}
assert len(state)==13 and state["dewey"]["id"]==CID and all(r["running"] for r in state.values())
write("runtime-before-12.0.8.json",json.dumps(state,indent=2)+"\n")
write("base-manifest-12.0.8.json",MANIFEST.read_text())
pins=(ROOT/"pins-12.0.7.toml").read_text()
new,count=re.subn(r'(\[services\.dewey\][\s\S]*?^tag\s*=\s*)"12\.0\.7"',r'\g<1>"12.0.8"',pins,count=1,flags=re.M)
assert count==1
a=tomllib.loads(pins);b=tomllib.loads(new);a["services"]["dewey"]["tag"]="12.0.8";assert a==b
write("pins-12.0.8.toml",new)
runner=(ROOT/"run_build_12.0.7.py").read_text()
assert "manifest-12.0.6.json" in runner
runner=runner.replace("12.0.7","12.0.8").replace("manifest-12.0.6.json","base-manifest-12.0.8.json")
write("run_build_12.0.8.py",runner)
deploy=(ROOT/"deploy-dewey-12.0.7.py").read_text()
for old_value in ("e7acb6f9edcb66acb9f2d9e7c583ea389e2ed0da5f61214ef4abc6a15597ce12","c3370d378379cab28cdc49ace4c524a13a18da3114cbb62aa36c3f69adb6f3f3","ebb22ba30aaeba369859af8bcbc71e628b7bc22fed2c6ac6142d08a9dab7c55a"):
    assert deploy.count(old_value)==1
deploy=deploy.replace("12.0.7","NEXT_VERSION").replace("12.0.6","12.0.7").replace("NEXT_VERSION","12.0.8")
deploy=deploy.replace("MultiQC export correction","validated search/readiness corrections")
deploy=deploy.replace("e7acb6f9edcb66acb9f2d9e7c583ea389e2ed0da5f61214ef4abc6a15597ce12",EXPECTED_COMPOSE).replace("c3370d378379cab28cdc49ace4c524a13a18da3114cbb62aa36c3f69adb6f3f3",EXPECTED_MANIFEST).replace("ebb22ba30aaeba369859af8bcbc71e628b7bc22fed2c6ac6142d08a9dab7c55a",CID)
write("deploy-dewey-12.0.8.py",deploy)
receipt={"version":"12.0.8","previous_version":"12.0.7","compose_sha256":EXPECTED_COMPOSE,"manifest_sha256":EXPECTED_MANIFEST,"previous_container":CID,"container_count":13,"unchanged_selected_build_helpers":True,"selected":["dewey"],"base_roles":sorted(old["images"]),"source_commit":"c8a73360fcb6b908c2e575cb381e359dd425f838","baseline_ci":"40399463503","runtime_build_lock_inputs_equal_main":True}
write("prepare-12.0.8.json",json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt))
