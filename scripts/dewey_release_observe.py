#!/usr/bin/env python3
"""Bounded, read-only foreground observation of this exact Dewey deployment."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import ProxyHandler, build_opener

ROOT = Path('/home/ubuntu/dewey_ops/tapdb101-20260911')
OUTPUT = ROOT / 'receipts/production-promotion-1f634ef66082'
START = dt.datetime.fromisoformat('2026-09-11T11:07:45.461224+00:00')
DEADLINE = START + dt.timedelta(minutes=60)
CONTAINER_ID = '8ef3589605c69072c5e6a5b89e98a4edf12ca2d85a8150c056ed06f2c8ac8e73'
BUILD = {'version': '9.0.0', 'sha': '1f634ef66082eee32c788e0d8c386a20c2b8563e'}


def main():
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    os.umask(0o077)
    opener = build_opener(ProxyHandler({}))
    samples = []
    with (OUTPUT / 'observation.jsonl').open('x') as handle:
        while True:
            now = dt.datetime.now(dt.timezone.utc)
            row = {'observed_at': now.isoformat(), 'seconds_since_start': (now - START).total_seconds()}
            try:
                container = json.loads(subprocess.check_output(['docker', 'inspect', 'dayhoff-day-dewey-1'], text=True))[0]
                assert container['Id'] == CONTAINER_ID and container['State']['Running']
                assert container['RestartCount'] == 0
                row['container_id'] = container['Id']
                row['restart_count'] = container['RestartCount']
                with opener.open('https://dewey.day.lsmc.bio/readyz', timeout=20) as response:
                    assert response.status == 200
                    payload = json.load(response)
                assert payload['build'] == BUILD and payload['status'] == 'ok' and payload['ready'] is True
                row['ready'] = True
                row['build'] = payload['build']
                row['database'] = payload['checks']['database']['status']
                assert row['database'] == 'ok'
                row['status'] = 'passed'
            except Exception as exc:
                row['status'] = 'failed'
                row['error_class'] = type(exc).__name__
            samples.append(row)
            handle.write(json.dumps(row, sort_keys=True) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
            print(json.dumps(row), flush=True)
            if row['status'] != 'passed':
                raise RuntimeError('Observation failed; inspect the retained sample without restarting or changing production')
            remaining = (DEADLINE - dt.datetime.now(dt.timezone.utc)).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(300, remaining))
    logs = subprocess.check_output(['docker', 'logs', '--timestamps', '--since', START.isoformat(), CONTAINER_ID], stderr=subprocess.STDOUT)
    with (OUTPUT / 'observation-container.log').open('xb') as handle:
        handle.write(logs)
    text = logs.decode(errors='replace')
    result = {'status': 'observed', 'deployment_started_at': START.isoformat(),
              'completed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'required_minutes': 60,
              'samples': len(samples), 'all_ready': all(row['status'] == 'passed' for row in samples),
              'container_id': CONTAINER_ID, 'restart_count': 0, 'build': BUILD,
              'log_sha256': hashlib.sha256(logs).hexdigest(),
              'http_5xx_log_lines': len(re.findall(r'HTTP/[^\n]+" 5\d\d ', text)),
              'tracebacks': text.count('Traceback (most recent call last):')}
    with (OUTPUT / 'observation.json').open('x') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
