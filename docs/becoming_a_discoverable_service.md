# Dewey As A Discoverable Service

This page describes how Dewey fits the Dayhoff-managed service contract today.

The goal is not to restate Dayhoff's generic guidance. The goal is to show how Dewey already satisfies that contract in concrete, repo-local terms.

## Summary

Dewey is already a named Dayhoff role. In the current stack, it is discoverable because Dayhoff can:

- name it
- configure it
- launch it through Dewey-owned commands
- probe it through stable health paths
- inject auth and runtime wiring
- expose it as a routable base URL in the stack

That discoverability does not make Dayhoff the owner of Dewey's business behavior. It makes Dewey a well-modeled service in the broader ecology.

## The Concrete Dewey Contract

### Repo-root activation entrypoint

Dewey exposes the repo-owned activation script expected by the workspace:

```bash
source ./activate <deploy-name>
```

That script creates or reuses a deployment-scoped conda environment and exports deployment-scoped env such as:

- `DEWEY_DEPLOYMENT_CODE`
- `DEPLOYMENT_CODE`
- `LSMC_DEPLOYMENT_CODE`

### Deployment-scoped config file

Dewey uses deployment-scoped config paths shaped like:

```text
~/.config/dewey-<deploy>/dewey-config-<deploy>.yaml
```

The CLI exposes this contract directly through:

- `dewey config path`
- `dewey config init`
- `dewey config validate`
- `dewey config status`

### CLI-owned lifecycle

Dewey already owns its own runtime lifecycle through the `dewey` CLI:

- `dewey server start`
- `dewey server stop`
- `dewey server status`
- `dewey server logs`
- `dewey db build`
- `dewey db reset`
- `dewey db nuke`

That is exactly the shape Dayhoff needs: service-owned lifecycle, not hidden shell glue.

### Stable health and readiness endpoints

Dewey exposes the probe paths Dayhoff expects:

- `/healthz`
- `/readyz`

It also exposes richer authenticated observability endpoints:

- `/health`
- `/obs_services`
- `/api_health`
- `/endpoint_health`
- `/db_health`
- `/my_health`
- `/auth_health`

### Routable base URL

The current local CLI and config template assume:

- `https://localhost:8914` for the standard local browser/API surface

That base URL is used by:

- login and logout redirect wiring
- health checks
- service discovery and deployment metadata in the wider stack
- cross-service configuration in Dayhoff-managed environments

### Auth and base-URL handoff

Dewey consumes auth and browser-session wiring through config/env values such as:

- Cognito domain
- app client ID
- redirect URI
- logout URL
- user pool ID
- allowed email domains
- group-role mapping

Dayhoff can synthesize and hand off these deployment-scoped values without needing to own Dewey's route logic.

## Why Dewey Is Discoverable In Practice

Dayhoff's idea of discoverability is operational, not marketing-oriented. A service is discoverable when the control plane can describe and operate it consistently.

Dewey already gives Dayhoff what it needs:

- stable repo identity
- service-owned activation
- service-owned runtime commands
- stable probe endpoints
- config patch targets
- auth wiring inputs
- a routable base URL

That is why Dewey can appear in the Dayhoff service map without Dewey needing to embed Dayhoff-specific business logic.

## How Bloom And Ursa Consume Dewey

### Bloom

Bloom treats Dewey as the artifact authority, not as a workflow orchestrator.

Current Bloom-facing usage:

- Bloom produces wet-lab outputs
- Bloom can register run artifacts with Dewey
- Bloom keeps Bloom lineage and workflow state separate from Dewey artifact authority

This split is documented in the adjacent Bloom repo and matches current Dewey API ownership.

### Ursa

Ursa treats Dewey as the source of truth for artifact references involved in analysis ingest and output linkage.

Current Ursa-facing usage:

- resolve Dewey artifact references
- register or attach analysis outputs back into Dewey
- consume artifact-location facts without taking over artifact authority

## What Discoverability Does Not Mean

Dewey being discoverable does not mean:

- Dayhoff owns Dewey's GUI or API semantics
- Dewey owns stack-wide orchestration
- Dewey becomes the owner of lab, analysis, or portal truth
- Dewey exposes a generic service catalog or message bus for the rest of the platform

Discoverability is an operations and runtime contract. Ownership still stays local to Dewey for artifact concerns.

## Current-State Caveat

The discoverability contract remains stable in the current April 6, 2026 verification run. The repo now measures `256` collected tests with `254 passed`, `2 skipped`, and `84%` coverage. Dayhoff still depends mainly on these service-contract facts:

- activation
- config pathing
- CLI lifecycle
- health/readiness
- base URL
- observability endpoints

That means Dewey is discoverable in the Dayhoff sense, with the remaining runtime sensitivity concentrated in environment-specific browser auth rather than the discoverability contract itself.
