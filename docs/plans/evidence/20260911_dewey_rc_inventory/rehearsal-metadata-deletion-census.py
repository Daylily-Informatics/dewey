from pathlib import Path
import datetime,hashlib,json,os
from sqlalchemy import text
from daylily_tapdb.cli.context import set_cli_context
from daylily_tapdb.web.runtime import get_db,dispose_all_runtime_engines
p=Path("/opt/dewey/day/releases/tapdb10-rehearsal-20260911/tapdb-runtime.yaml")
set_cli_context(config_path=p,client_id="dewey",database_name="dewey-day")
db=get_db(str(p)); db.app_username="dewey-migration-census"
r={"captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}
with db.session_scope(commit=False) as s:
 s.execute(text("SET TRANSACTION READ ONLY"))
 for table in ("generic_instance","generic_instance_lineage"):
  r[table]=[dict(x) for x in s.execute(text("SELECT is_deleted,jsonb_typeof(json_addl->'properties') AS properties_type,json_addl ? 'dewey_tapdb10_archive' AS archive_key_exists,count(*) AS rows FROM "+table+" GROUP BY 1,2,3 ORDER BY 1,2,3")).mappings()]
dispose_all_runtime_engines()
out=Path("/run/dewey-acceptance-output/metadata-deletion-census.json");data=(json.dumps(r,sort_keys=True,indent=2)+"\n").encode()
with os.fdopen(os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"wb") as h:h.write(data);h.flush();os.fsync(h.fileno())
print(json.dumps({"receipt":str(out),"sha256":hashlib.sha256(data).hexdigest(),"counts":r}))
