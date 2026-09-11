# Dewey 9.0.0 service-only production promotion preparation

Prepared locally after the candidate image qualification and native migration/
preservation passed. Sequence-apply E review and isolated application acceptance
have not run and remain required future gates. This is a Dewey-only deployment
definition and ownership-resolution checklist. It does not run Docker, edit the
production Compose/proxy/manifest, start a container, restart a sibling service,
or change production.

## Fixed accepted inputs

| Field | Accepted value |
| --- | --- |
| Candidate manifest digest | `sha256:59a0cad2e005b5940dc3eeac1dd9a72691d23386c8dfc4d72c37cd85f880759f` |
| Candidate source revision | `c484c95768a4147acdcabd12a2da0332c4c750dc` |
| Runtime packages | Dewey `9.0.0`; TapDB `10.1.1rc1`; Meridian `0.4.8`; Python 3.12 |
| Old container | `dayhoff-day-dewey-1`; ID `872434f0530335fd5a985a920f498fe39a36fd5eab40b9cb3934b185ceddeb36`; deliberately stopped since 2026-09-11T06:56:35Z |
| Old source Compose | `/opt/dewey/day/releases/qeo-resolver-556dfcf936ea/docker-compose.yml` |
| Owning Compose | `/opt/dayhoff/deployments/day/compose/docker-compose.yml`; SHA256 `35a37f2c5df1cc84ebfd57ad19a9d56b14f88b3e6bc322aebadd3db081da8509`; project `dayhoff-day` |
| Release manifest | `/opt/dayhoff/deployments/day/container-release-manifest.json`; SHA256 `b958136a7b15492042cb6b7e06023b63cb164daf5ff8532950b3ebe8c6bc3cd2` |
| Non-Dewey manifest images | Canonical SHA256 `c788b60baa92c05b2daa99ce7abd3303017e63c0434c70f6eaadd88bd200d31e` |
| Boot control | Enabled/active `dayhoff-container-compose.service`; fragment SHA256 `8ca48be506f650bbb7102e63f3ec51a3e5841f0f8d53e1b1ecd658095da62c31`; shared all-service unit remains unchanged and is not restarted |
| Production backend | `/etc/apache2/sites-available/dewey-day.conf`, enabled through `sites-enabled`; SHA256 `0fab11a8293b060f926bf54fd36bbe029ee8cf6039246a2bfa11cfcd7dc929a5`; `ProxyPass` and `ProxyPassReverse` use `http://localhost:8914/` |
| New runtime configs | `/opt/dewey/day/releases/9.0.0/dewey-config.yaml`; `/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml` |
| Environment preparer | D commit `1d8d7197bf7f0eacb960ffe94dbb2873bdc3bdde`; script SHA256 `a838970fe9f6bf0f3809166af721e29f25c7c718a6bf46ef6b0d6a38d3c75b8c` |

The final release image will have a new exact source SHA and manifest digest.
The renderer requires both as explicit inputs and never substitutes the
candidate identity.

## Complete Dewey service replacement mapping

The template at
`evidence/20260911_dewey_900_deployment_capsule/dewey-service.yaml.template`
defines the complete replacement structure for the owning Compose file's
`.services.dewey` mapping. `scripts/dewey_compose_release_prepare.py` combines
it with D's private production `runtime.env`, then structurally replaces only
that mapping in an exact copy of the reviewed owning Compose. It does not use a
Compose override: Compose merges volume lists by target and could retain
superseded source/operator/broad-deployment mounts.

The replacement contains only the accepted production runtime shape:

- final immutable `repository@sha256` image whose OCI labels match the final
  SHA, plus that SHA in `DEWEY_BUILD_SHA`/`LSMC_RELEASE_SHA`;
- user `0:0`, `HOME=/home/ubuntu`, host network, `HOST=0.0.0.0`, `PORT=8914`;
- all eight reviewed loopback `extra_hosts` entries from the owning service;
- explicit Dewey/TapDB production identity and fixed new config paths;
- explicit `lsmc` AWS profile/region/config paths and localhost OTEL endpoint;
- read-only new Dewey/TapDB configs, AWS directory, RDS CA, CloudFront key, NCBI
  key, AI grants and both TapDB registries;
- one explicit writable production state-directory mount for XDG state/cache and
  metapub cache; and
- the reviewed existing `unless-stopped` restart policy.

It omits the acceptance script/output/fixture/resolver-token mounts, old source
or operator config directories, broad Dayhoff deployment mounts, Docker socket
and TapDB overlay. D adds three empty QEO dispatch variables only to isolate its
acceptance lanes. The final renderer compares those keys to the pinned owning
service, restores an exact deployed value if present, and otherwise removes the
isolated override. All three are absent in the reviewed owning service, so the
final mapping omits them and the unchanged Dewey YAML owns configured dispatch.

The private environment preparer preserves all literal owning-service values,
including bearer/auth, service URLs, managed storage and legacy environment
keys. The final renderer overrides only the reviewed production runtime,
database identity, image-SHA, listener and state-path keys. It writes those
values directly under `environment`; it does not add `env_file`, `extends`,
interpolation or credential values to a public receipt. Its secret-free receipt
records `removed_isolated_override` or `restored_from_owning_compose` for each
dispatch key without recording any value.

Prepare D's private production environment first, using the exact accepted
production config and an existing mode-0700 directory:

```bash
python3 scripts/dewey_launch_environment_prepare.py \
  --compose /opt/dayhoff/deployments/day/compose/docker-compose.yml \
  --dewey-config /opt/dewey/day/releases/9.0.0/dewey-config.yaml \
  --lane production \
  --image-sha <exact-final-40-character-release-sha> \
  --output-dir <exact-existing-private-environment-directory>
```

After the final release image exists, render the complete Compose and manifest
replacements into an absent private directory:

```bash
python3 scripts/dewey_compose_release_prepare.py \
  --compose /opt/dayhoff/deployments/day/compose/docker-compose.yml \
  --manifest /opt/dayhoff/deployments/day/container-release-manifest.json \
  --runtime-environment <private-environment-directory>/runtime.env \
  --runtime-environment-receipt <private-environment-directory>/receipt.json \
  --extra-hosts <private-environment-directory>/extra-hosts.args \
  --release-sha <exact-final-40-character-release-sha> \
  --image-digest sha256:<exact-final-manifest-digest> \
  --state-dir <exact-existing-private-production-state-directory> \
  --output-dir /absolute/absent/private/path/dewey-9.0.0-production-service
```

The output contains `dewey-service.yaml`, the complete `docker-compose.yml`, the
complete `container-release-manifest.json`, a secret-free
`deployment-inputs.json`, and `SHA256SUMS`. Inputs must match the reviewed
Compose and manifest hashes; the D receipt must be `prepared` for `production`
and match both protected input files. All non-Dewey service mappings remain
canonical-data identical. The manifest update changes only `.images.dewey`; its
existing Dewey entry is already known to be stale relative to the stopped live
container, so it is source metadata rather than proof of that container.

## Resolved control shape and remaining final inputs

The owning Compose has top-level `name: dayhoff-day`; the stopped container's
labels identify project/service `dayhoff-day`/`dewey`, container number `1`, and
the older release Compose as its creation source. The canonical owning and old
release Compose files currently have identical `.services.dewey` mappings.
The canonical service restart policy is `unless-stopped`, its listener is
`0.0.0.0:8914`, and it has the exact eight loopback host mappings pinned in the
template.

The shared unit is `/etc/systemd/system/dayhoff-container-compose.service`,
with working directory `/opt/dayhoff/deployments/day/compose`. Its `ExecStart`
is `/usr/bin/docker compose -f
/opt/dayhoff/deployments/day/compose/docker-compose.yml up -d
--remove-orphans`; its `ExecStop` uses the same Compose path with `stop`; it has
no environment files. These facts explain why the unit is not used for this
promotion: its all-service/orphan behavior exceeds the Dewey-only scope.

Only three deployment inputs remain future-bound:

1. the verified clean main release commit tagged `9.0.0`;
2. the final `linux/amd64` manifest digest whose OCI source/revision/version and
   package receipt bind to that commit; and
3. the exact existing private host state directory used for all final XDG and
   metapub paths.

At deployment time, reread only the current owning Compose and manifest hashes,
the stopped source container identity/evidence, the final image identity and the
`8914` listener. A changed reviewed hash stops this capsule for a focused
review. Existing runtime-config/key hashes and the 13-sibling baseline need no
gratuitous repeat.

## Promotion sequence

1. Create fresh private environment, rendered-output and receipt directories.
   Copy the owning Compose and release manifest into the receipt directory
   before mutation; preserve their hashes and modes.
2. Assert the old container is the exact expected ID, remains stopped, and its
   old image is still inspectable. Preserve its inspect/config/log evidence and
   the old image, configs and database. Compose may normally replace this
   stopped container during the approved Dewey deployment; do not rename it or
   create a second Compose project to preserve its ID.
3. Assert the final image digest/platform/OCI labels/package receipt match the
   final release SHA and tag. Assert no listener owns port `8914`.
4. Run both preparation helpers and review `dewey-service.yaml`, the canonical
   non-Dewey hashes and `SHA256SUMS`. Validate the rendered Compose with
   `/usr/bin/docker compose -f <rendered>/docker-compose.yml config --quiet`.
5. Install the rendered complete Compose over only the reviewed owning Compose,
   preserving root ownership and mode `0640`. Do not edit the shared systemd
   unit. The prepared manifest remains staged until service acceptance. Use an
   adjacent new file and one rename:

```bash
: "${D_RENDERED:?Set D_RENDERED to the exact private rendered output directory}"
sudo install -o root -g root -m 0640 \
  "$D_RENDERED/docker-compose.yml" \
  /opt/dayhoff/deployments/day/compose/docker-compose.yml.dewey-9.0.0.next
sudo mv -T \
  /opt/dayhoff/deployments/day/compose/docker-compose.yml.dewey-9.0.0.next \
  /opt/dayhoff/deployments/day/compose/docker-compose.yml
```
6. Run only:

```bash
/usr/bin/docker compose \
  -f /opt/dayhoff/deployments/day/compose/docker-compose.yml \
  up -d --no-deps --pull never dewey
```

   Do not run `down`, `stop`, `rm`, `--remove-orphans`, prune, the shared boot
   unit, or an all-service `up`.
7. Verify the new container is `dayhoff-day`/`dewey`, uses the final exact image
   digest/config ID and expected mounts/environment-key names, owns port `8914`,
   and passes local readiness plus the existing external vhost check.
8. After service acceptance, install the prepared manifest with root ownership
   and mode `0640`. Its only changed value is `.images.dewey`:

```bash
sudo install -o root -g root -m 0640 \
  "$D_RENDERED/container-release-manifest.json" \
  /opt/dayhoff/deployments/day/container-release-manifest.json.dewey-9.0.0.next
sudo mv -T \
  /opt/dayhoff/deployments/day/container-release-manifest.json.dewey-9.0.0.next \
  /opt/dayhoff/deployments/day/container-release-manifest.json
```

```json
{
  "image": "108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:<final-digest>",
  "repository": "dayhoff/day/dewey",
  "source_commit": "<final-release-sha>",
  "source_tag": "9.0.0"
}
```

   Require the pre/post canonical hash of `.images | del(.dewey)` to equal the
   reviewed `c788b60b...` value.
9. Apache already proxies to the unchanged loopback `8914` backend. Do not
   edit or reload Apache. Promotion occurs when the accepted Dewey process owns
   that listener. Verify local health/readiness and the existing external vhost.
10. Compare only the bounded non-Dewey container identity/state/start-time
   baseline and the canonical non-Dewey Compose/manifest hashes. Any sibling
   difference fails promotion evidence.
11. Record the new container ID, Compose project/service/config files, exact
    image digest/config ID, mounts/env names, restart policy, listener, health,
    readiness and proxy response. Retain the old image and the replaced
    container's diagnostic evidence.

The retained old container/image are evidence and recovery inputs. They are not
an automatic rollback: once Dewey 9 accepts writes, an image-only return to the
old source database cannot preserve those writes or allocator exposure.

## Local validation boundary

Only Python compilation, one pure final-dispatch projection check, template YAML
parse and diff checks are appropriate here. Candidate image build/smoke and the
completed native migration/preservation evidence are reused. Sequence-apply E
review and isolated application acceptance remain future gates; this capsule
does not claim or replace either gate.
