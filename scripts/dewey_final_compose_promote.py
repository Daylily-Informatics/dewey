#!/usr/bin/env python3
"""Promote the reviewed Dewey-only release after actual final-data acceptance."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/home/ubuntu/dewey_ops/tapdb101-20260911')
RENDERED = ROOT / 'deployment-final-1f634ef66082/rendered'
OUTPUT = ROOT / 'receipts/production-promotion-1f634ef66082'
ACCEPTANCE = ROOT / 'receipts/production-application-1f634ef66082'
COMPOSE = Path('/opt/dayhoff/deployments/day/compose/docker-compose.yml')
MANIFEST = Path('/opt/dayhoff/deployments/day/container-release-manifest.json')
FINAL_CONTAINER = 'dewey-tapdb10-final-1f634ef66082'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def inspect(names):
    return json.loads(subprocess.check_output(['docker', 'inspect', *names], text=True))


def siblings():
    names = subprocess.check_output(['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=dayhoff-day'], text=True).split()
    result = {}
    for row in inspect(names):
        service = row['Config']['Labels'].get('com.docker.compose.service')
        if service != 'dewey':
            result[service] = {'id': row['Id'], 'image': row['Image'], 'running': row['State']['Running'],
                               'started_at': row['State']['StartedAt'], 'restart_count': row['RestartCount']}
    assert len(result) == 12
    return result


def replace_exact(source, destination):
    temporary = destination.with_name(destination.name + '.dewey9-1f634ef66082')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(source.read_bytes())
        handle.flush()
        os.fchmod(handle.fileno(), 0o640)
        os.fsync(handle.fileno())
    os.replace(temporary, destination)


def main():
    assert os.geteuid() == 0 and os.environ.get('SUDO_USER') == 'ubuntu'
    os.umask(0o077)
    assert OUTPUT.is_dir() and not (OUTPUT / 'promotion.started.json').exists()
    assert digest(RENDERED / 'deployment-inputs.json') == 'b6d51838b7a71a072a797b2689427e54227577c2c15ee7c949348cf7203a315c'
    plan = read(RENDERED / 'deployment-inputs.json')
    for path, key in ((COMPOSE, 'source_compose_sha256'), (MANIFEST, 'source_manifest_sha256'),
                      (RENDERED / 'docker-compose.yml', 'rendered_compose_sha256'),
                      (RENDERED / 'container-release-manifest.json', 'rendered_manifest_sha256')):
        assert digest(path) == plan[key]
    assert read(ACCEPTANCE / 'runtime-verified.json')['status'] == 'verified'
    for phase in ('read', 'write', 'replay'):
        assert read(ACCEPTANCE / ('app-' + phase + '.json'))['status'] == 'passed'
    for phase in ('metadata', 'reference'):
        proof = read(ROOT / ('receipts/final-native/' + phase + '-verify.stdout'))
        assert proof['ok'] is True and not proof['violations']
    candidate = inspect([FINAL_CONTAINER])[0]
    assert not candidate['State']['Running'] and candidate['Config']['Image'] == plan['image_reference']
    original = inspect(['dayhoff-day-dewey-1'])[0]
    assert not original['State']['Running']
    from dewey_rehearsal_copy import cfg_at
    from dewey_xrf_template_setup_port_fix import frozen_source

    frozen_source(cfg_at('control-operator.yaml', 'postgres'))
    before = siblings()
    for source, name in ((COMPOSE, 'previous-compose.yml'), (MANIFEST, 'previous-release-manifest.json')):
        with (OUTPUT / name).open('xb') as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
    write_new(OUTPUT / 'promotion.started.json', {'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'deployment_plan_sha256': digest(RENDERED / 'deployment-inputs.json'), 'siblings': before,
              'old_dewey_id': original['Id'], 'acceptance_container_id': candidate['Id']})
    replace_exact(RENDERED / 'docker-compose.yml', COMPOSE)
    replace_exact(RENDERED / 'container-release-manifest.json', MANIFEST)
    command = ['/usr/bin/docker', 'compose', '-f', str(COMPOSE), 'up', '-d', '--no-deps', '--pull', 'never', 'dewey']
    with (OUTPUT / 'compose.stdout').open('x') as out, (OUTPUT / 'compose.stderr').open('x') as err:
        process = subprocess.run(command, stdout=out, stderr=err)
    write_new(OUTPUT / 'compose-result.json', {'command': command, 'returncode': process.returncode})
    assert process.returncode == 0
    after = siblings()
    assert after == before
    current = inspect(['dayhoff-day-dewey-1'])[0]
    assert current['Config']['Image'] == plan['image_reference'] and current['State']['Running']
    result = {'status': 'promoted', 'completed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'container_id': current['Id'], 'image': plan['image_reference'], 'source_sha': plan['release_sha'],
              'siblings_unchanged': True, 'compose_sha256': digest(COMPOSE), 'manifest_sha256': digest(MANIFEST)}
    write_new(OUTPUT / 'promotion.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
