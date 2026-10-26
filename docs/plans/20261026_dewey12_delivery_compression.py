#!/usr/bin/env python3
"""Install reviewed Dewey-only byte-preserving Apache directives."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path('/home/ubuntu/dewey12-release-20261026T021700Z')
ORIGIN = Path('/etc/apache2/sites-available/dewey12-recipient.conf')
PRIVATE = Path('/etc/apache2/sites-available/dewey-day.conf')
DIRECTIVE = '  SetEnvIf Request_URI "^/(?:fetch/|__dewey_preview/assets/|shares/[^/]+/files/)" no-gzip=1'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    os.umask(0o077)
    receipt_path = ROOT / 'delivery-compression-install.json'
    assert not receipt_path.exists()
    before = {path: path.read_bytes() for path in (ORIGIN, PRIVATE)}
    metadata = {path: path.stat() for path in before}
    for path, data in before.items():
        (ROOT / (path.name + '.before-byte-correction')).open('xb').write(data)
    base = ['python3', str(ROOT / 'dewey_ingress_compression.py')]
    config = ['--config', str(ROOT / 'ingress-compression-config.json')]
    candidates = {ORIGIN: ROOT / 'recipient-byte-candidate.conf', PRIVATE: ROOT / 'private-dewey-byte-candidate.conf'}
    subprocess.run(base + ['render-origin'] + config + ['--secrets', str(ROOT / 'origin-secrets.json'),
        '--output', str(candidates[ORIGIN])], check=True, capture_output=True)
    subprocess.run(base + ['render-private-dewey'] + config + ['--existing-origin', str(PRIVATE),
        '--output', str(candidates[PRIVATE])], check=True, capture_output=True)
    rendered = {path: candidate.read_bytes() for path, candidate in candidates.items()}
    origin_text = rendered[ORIGIN].decode()
    assert origin_text.count(DIRECTIVE) == 3
    assert origin_text.replace(DIRECTIVE + '\n', '').replace(', mod_setenvif.', '.') == before[ORIGIN].decode()
    private_insertion = '\n  # Dewey managed delivery preserves byte representation\n' + DIRECTIVE
    assert rendered[PRIVATE].decode().count(private_insertion) == 1
    assert rendered[PRIVATE].decode().replace(private_insertion, '', 1) == before[PRIVATE].decode()
    assert all(path.read_bytes() == data for path, data in before.items())

    def install(path, data):
        temporary = path.with_name(path.name + '.dewey-byte-selected')
        temporary.open('xb').write(data)
        temporary.chmod(metadata[path].st_mode & 0o777)
        os.chown(temporary, metadata[path].st_uid, metadata[path].st_gid)
        os.replace(temporary, path)

    for path, data in rendered.items():
        install(path, data)
    check = subprocess.run(['apache2ctl', 'configtest'], capture_output=True, text=True)
    (ROOT / 'apache-byte-configtest.log').open('x').write(check.stdout + check.stderr)
    if check.returncode:
        for path, data in before.items():
            install(path, data)
        raise RuntimeError('Apache rejected candidates; original files restored before reload')
    reload_result = subprocess.run(['apache2ctl', 'graceful'], capture_output=True, text=True)
    (ROOT / 'apache-byte-graceful.log').open('x').write(reload_result.stdout + reload_result.stderr)
    receipt = {'observed_at': datetime.now(timezone.utc).isoformat(), 'configtest_exit': check.returncode,
        'graceful_exit': reload_result.returncode, 'added_directive_count': 4,
        'containers_restarted': False, 'images_built': False,
        'only_change': 'Disable Apache gzip for Dewey managed byte-delivery paths',
        'files': [{'path': str(path), 'before_sha256': digest(before[path]),
                   'after_sha256': digest(path.read_bytes())} for path in before]}
    receipt_path.open('x').write(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
    assert reload_result.returncode == 0


if __name__ == '__main__':
    main()
