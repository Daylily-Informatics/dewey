#!/usr/bin/env python3
"""Bounded unauthenticated recipient boundary checks; no fixture writes or emails."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ALB = 'Dayhof-LoadB-yTZ2WPqXCI1t-291525477.us-west-2.elb.amazonaws.com'
ROOT = Path('/home/ubuntu/dewey12-release-20261026T021700Z')


def main():
    os.umask(0o077)
    assert not (ROOT / 'boundary-checks.json').exists()
    checks = [
        ('login-recipient', 'login.day.lsmc.bio', '/auth/share?state=boundary-check', 'GET', {}, 200),
        ('machine-auth', 'dewey.day.lsmc.bio', '/fetch/boundary-probe', 'GET', {'Accept':'application/octet-stream'}, 401),
        ('browser-auth', 'dewey.day.lsmc.bio', '/fetch/boundary-probe', 'GET', {'Accept':'text/html'}, 303),
        ('recipient-tokens-auth', 'dewey.day.lsmc.bio', '/api/v2/recipient/tokens', 'GET', {}, 401),
        ('management-denied', 'dewey.day.lsmc.bio', '/api/v1/records', 'GET', {}, 403),
        ('general-login-denied', 'login.day.lsmc.bio', '/auth/login', 'GET', {}, 403),
        ('backchannel-denied', 'login.day.lsmc.bio', '/api/v1/dewey/identity/introspect', 'POST', {}, 403),
        ('fetch-method-denied', 'dewey.day.lsmc.bio', '/fetch/boundary-probe', 'POST', {}, 403),
        ('forged-headers-denied', 'dewey.day.lsmc.bio', '/api/v1/records', 'GET',
         {'X-Forwarded-For':'12.201.135.248', 'X-Dewey-Management-Assertion':'invalid',
          'X-Dewey-Recipient-Assertion':'invalid', 'X-Login-Management-Assertion':'invalid'}, 403),
        ('invalid-content-host', 'probe.dewey-content.day.lsmc.bio', '/__dewey_preview/challenge', 'GET', {}, 403),
        ('nonexistent-content-context', 'pv-00000000000000000000000000000000.dewey-content.day.lsmc.bio',
         '/__dewey_preview/assets/report.html', 'GET', {}, 404),
    ]
    rows = []
    for name, host, path, method, headers, expected in checks:
        header_path = ROOT / ('boundary-' + name + '.headers')
        command = ['curl', '--silent', '--show-error', '--connect-timeout', '10', '--max-time', '20',
                   '--output', '/dev/null', '--dump-header', str(header_path), '--write-out', '%{http_code}',
                   '--request', method, '--connect-to', f'{host}:443:{ALB}:443']
        for key, value in headers.items():
            command += ['--header', key + ': ' + value]
        command.append('https://' + host + path)
        result = subprocess.run(command, capture_output=True, text=True)
        rows.append({'name': name, 'host': host, 'path': path, 'method': method,
                     'status': result.stdout, 'expected': expected, 'exit_code': result.returncode,
                     'pass': result.returncode == 0 and result.stdout == str(expected),
                     'error': result.stderr})
    receipt = {'observed_at': datetime.now(timezone.utc).isoformat(), 'source': 'deployment EC2 outside approved management IP conditions',
               'load_balancer': ALB, 'tls_verification': True, 'checks': rows, 'ok': all(r['pass'] for r in rows)}
    (ROOT / 'boundary-checks.json').open('x').write(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
    raise SystemExit(0 if receipt['ok'] else 1)


if __name__ == '__main__':
    main()
