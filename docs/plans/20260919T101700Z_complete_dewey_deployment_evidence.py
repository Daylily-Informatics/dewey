"""Complete the canonical receipt from preserved Dewey cutover evidence only.

No service/configuration/provider operations. Preserve the original receipt and
its observation time. The additional preparation time is not a live observation.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path('/home/ubuntu/dewey-10.0.7-cutover-20260919T100700Z')
ORIGINAL_SHA = '7d92be3bec61ab3e354d95d00c931045d7d0e9393580b330178c8d0ee9193c8a'
BEFORE_SHA = '7db0ab90d6a45d8660f02680ad977f318f57c17aa0cd9624902ecc82f7eca8ad'
BUILD_SHA = '7463bd1fab97f1a6cf108c25923c3efe9fd58ec550fe32ba64ae8d9befa55560'
ROLE = 'dayhoff-day-dewey-1'
OUTPUT = ROOT / 'canonical-completion-20260919T101700Z.json'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


raw = (ROOT / 'deployment-receipt.json').read_bytes()
require(sha(raw) == ORIGINAL_SHA, 'Original immutable cutover receipt changed')
receipt = json.loads(raw)
require(receipt['schema'] == 'ursa-owy-kahlo.deployment/v1'
        and receipt['service'] == 'dewey' and receipt['phase'] == 'SUCCESS'
        and receipt['siblings_unchanged'] is True, 'Exact successful Dewey cutover required')
before_raw = (ROOT / 'previous-manifest.json').read_bytes()
require(sha(before_raw) == BEFORE_SHA, 'Preserved before-manifest changed')
before = json.loads(before_raw)
previous = before['images']['dewey']
require(previous['image'] == receipt['previous_image'], 'Previous image mismatch')
selected = deepcopy(before)
selected['images']['dewey'].update(image=receipt['image'],
    source_commit=receipt['source_commit'], source_tag=receipt['source_tag'])
selected_raw = (json.dumps(selected, indent=2) + '\n').encode()
require(selected_raw == (ROOT / 'selected-manifest').read_bytes()
        and sha(selected_raw) == receipt['manifest_sha256'], 'Selected manifest differs from exact single-service change')
compose_before = (ROOT / 'previous-compose.yml').read_bytes()
compose_after = (ROOT / 'selected-compose').read_bytes()
require(sha(compose_after) == receipt['compose_sha256'], 'Selected Compose evidence changed')
build_path = Path(receipt['builder_receipt']['path'])
build_raw = build_path.read_bytes()
require(sha(build_raw) == BUILD_SHA == receipt['builder_receipt']['sha256'], 'Build evidence changed')
build = json.loads(build_raw)
require(all(build[field] == receipt[field] for field in ('service', 'source_tag', 'source_commit', 'image')),
        'Exact build/deployment identity mismatch')
old, new = receipt['containers_before'], receipt['containers_after']
require({k: v for k, v in old.items() if k != ROLE} == {k: v for k, v in new.items() if k != ROLE},
        'Recorded sibling observations differ')
role = deepcopy(new[ROLE])
require(role['status'] == 'running' and role['configured_image'] == receipt['image'], 'Selected role was not running')
# The original container projection did not collect Docker Health. Do not
# transform the separately recorded HTTP200 into an invented Docker health.
role['health'] = None
result = deepcopy(receipt)
result.update(
    build_receipt=str(build_path), roles={ROLE: role},
    previous_tag=previous['source_tag'], previous_commit=previous['source_commit'],
    compose_before_sha256=sha(compose_before), compose_after_sha256=sha(compose_after),
    evidence_prepared_at=datetime.now(timezone.utc).isoformat(),
    evidence_completion={
        'kind': 'canonical-fields-from-immutable-cutover-evidence',
        'original_receipt': {'path': str(ROOT / 'deployment-receipt.json'), 'sha256': ORIGINAL_SHA},
        'manifest_before': {'path': str(ROOT / 'previous-manifest.json'), 'sha256': BEFORE_SHA},
        'docker_health': 'NOT_CAPTURED_IN_ORIGINAL_CONTAINER_PROJECTION',
        'runtime_operations': [],
    },
)
output_raw = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
with os.fdopen(os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as handle:
    handle.write(output_raw)
    handle.flush()
    os.fsync(handle.fileno())
print(json.dumps({'path': str(OUTPUT), 'sha256': sha(output_raw),
    'source_observed_at': result['observed_at'], 'roles': list(result['roles']),
    'original_unchanged': sha((ROOT / 'deployment-receipt.json').read_bytes()) == ORIGINAL_SHA}, sort_keys=True))
