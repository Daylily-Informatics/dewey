"""Append GUI observations and render the durable audit ledger/report. No service calls."""
import datetime as dt
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PLANS = ROOT.parent.parent
STEM = '20260916T183133Z_dewey_gui_audit'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read(name, default):
    path = ROOT / name
    return json.loads(path.read_text()) if path.exists() else default

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def render():
    state = read('state.json', {})
    observations = [json.loads(line) for line in (ROOT / 'observations.jsonl').read_text().splitlines()] if (ROOT / 'observations.jsonl').exists() else []
    features = read('features.json', [])
    bugs = read('bugs.json', [])
    latest = {(o['feature'], o['attempt']): o for o in observations}
    def esc(value):
        return str(value).replace('|', '\\|').replace('\n', '<br>')
    gates = state.get('gates', {})
    ledger = [f'# Dewey GUI audit control ledger\n\nUpdated: {now()}\n',
      '## Controlling instructions\n\nExactly two iterations: two GUI attempts per feature on the current deployment; freeze the entire baseline before code fixes; one scoped tagged Dewey release/deployment; two attempts per feature after deployment; stop. Preserve all records and files. No deletes, overwrites, replacements, archives, member removal, upload abort, revocation, purge, data restore or cleanup. No pytest/lint/coverage/CI, PR, merge, dependency deployment or laptop container build.\n',
      '## Gate 0 baseline\n\n' + json.dumps(state.get('baseline', {}), indent=2) + '\n',
      '## Execution ledger\n\n| ID | Requirement | Status | Category | Approval gate | Owner | Evidence | Root cause | Terminal note |\n|---|---|---|---|---|---|---|---|---|']
    for key, gate in gates.items():
        ledger.append('| ' + ' | '.join(esc(x) for x in [key, gate['requirement'], gate['status'], gate.get('category','active_product_contract'), gate.get('depends','user-approved plan'), 'primary', gate.get('evidence',''), gate.get('root_cause',''),gate.get('note','')]) + ' |')
    ledger += ['\n## Bug ledger\n\n| ID | Severity | Description | Status | Owner | Evidence | Root cause / next action |\n|---|---|---|---|---|---|---|']
    for bug in bugs:
        ledger.append('| ' + ' | '.join(esc(bug.get(k,'')) for k in ['id','severity','description','status','owner','evidence','root_cause']) + ' |')
    ledger += ['\n## Coverage and evidence\n\nFeature inventory: `evidence/'+STEM+'/features.json`. Append-only attempts: `evidence/'+STEM+'/observations.jsonl`. Full matrix and attempt details are in `'+STEM+'_report.md`.\n',
      '## Amendments and limits\n\n' + '\n'.join('- '+x for x in state.get('notes',[])),
      '\n## Closeout\n\n'+json.dumps(state.get('closeout', {'all_rows_terminal':False,'objective_complete':False}),indent=2)]
    (PLANS / (STEM+'_ledger.md')).write_text('\n'.join(ledger)+'\n')
    report = [f'# Dewey GUI audit report\n\nUpdated: {now()}\n\nStatus: {state.get("report_status","IN PROGRESS; no acceptance claim")}\n',
      'Two independent GUI attempts are recorded per iteration. Inspection-only exclusions and blocked actions are not passes. Signed URLs, credentials, passwords and verification codes are excluded from durable evidence.\n',
      '## Deployment\n\n'+json.dumps(state.get('deployment',state.get('baseline',{})),indent=2)+'\n',
      '## Feature matrix\n\n| ID | Feature | URL / surface | I1-A | I1-B | I2-A | I2-B |\n|---|---|---|---|---|---|---|']
    for f in features:
        cells=[f['id'],f['name'],f['url']]+[latest.get((f['id'],a),{}).get('result','PENDING') for a in ['I1-A','I1-B','I2-A','I2-B']]
        report.append('| '+' | '.join(esc(c) for c in cells)+' |')
    report += ['\n## Counts\n\n'+json.dumps({a:dict(Counter(latest.get((f['id'],a),{}).get('result','PENDING') for f in features)) for a in ['I1-A','I1-B','I2-A','I2-B']},indent=2),
      '\n## Bugs\n\n'+json.dumps(bugs,indent=2,ensure_ascii=False),
      '\n## Attempt records\n']
    for o in observations:
        report += [f"### {o['feature']} {o['attempt']} — {o['result']}\n",
          '\n'.join(f'- **{key}**: {esc(value)}' for key,value in o.items() if key not in {'feature','attempt','result'})+'\n']
    report += ['\n## Retained fixtures\n\n'+json.dumps(read('fixtures.json',[]),indent=2,ensure_ascii=False),
      '\n## Limits and exclusions\n\n'+'\n'.join('- '+x for x in state.get('notes',[])),
      '\n## Completion\n\n'+json.dumps(state.get('closeout',{'all_rows_terminal':False,'objective_complete':False}),indent=2)]
    (PLANS / (STEM+'_report.md')).write_text('\n'.join(report)+'\n')
    print(json.dumps({'features':len(features),'observations':len(observations),'gates':dict(Counter(g['status'] for g in gates.values()))}))

if len(sys.argv)>1 and sys.argv[1]=='record':
    data=json.load(sys.stdin)
    if isinstance(data,dict): data=[data]
    with (ROOT/'observations.jsonl').open('a') as out:
        for o in data:
            o.setdefault('timestamp',now()); o.setdefault('version','10.0.5'); o.setdefault('role','johnm@lsmc.com / ADMIN')
            out.write(json.dumps(o,ensure_ascii=False)+'\n')
elif len(sys.argv)>1 and sys.argv[1]=='state':
    data=json.load(sys.stdin); state=read('state.json',{}); state.update(data); write('state.json',state)
elif len(sys.argv)>1 and sys.argv[1]=='features':
    write('features.json',json.load(sys.stdin))
elif len(sys.argv)>1 and sys.argv[1]=='bugs':
    write('bugs.json',json.load(sys.stdin))
render()
