# Applied binding, explicit runtime context and deferred final bootstrap

E independently accepts the actual rehearsal bind result and both exact Dewey
context fixes below. The fixed TapDB release remains `10.1.1rc1`; no native
migration, allocator or principal operation needs repeating for this startup
correction. O owns live execution, rebuilt-image acceptance and the ledger.

## Actual rehearsal binding accepted

The actual bind result is 6274 bytes, file SHA-256
`27515410a7f3d1167d0f0722d88b951b96d01bb88447a2266e36daf31c3690ea`, native seal
`87c5999fe15c27ccd6af5b06038b18085ad441dfc34b6e73b7ffb5120d4cd83b`, applied at
`2026-09-11T08:23:22.234072Z`. E independently recomputed its seal and compared
its exact plan, target, scope, grants, revokes and default privileges to the
accepted plan `e65fdff7d846d58730696f5e54cb34936d470d8073d25f0c04ac2606cc360f86`.
`privileges_verified` and `runtime_temp_denied` are true. Runtime CONNECT is true,
TEMP is false and existing operator TEMP is preserved.

The candidate then exited before HTTP while constructing the runtime engine.
O reports no application writes. This does not change the accepted binding
or allocator receipts. Fresh runtime sessions and image acceptance remain
separate from native bind's successful result.

## Released context boundary and accepted application repair

The released call chain is `daylily_tapdb/web/runtime.py:194–196` calling
`admin.db_metrics.maybe_install_engine_metrics` without a config path. At
`admin/db_metrics.py:280–282`, the metrics toggle reads normalized admin settings
through `get_admin_settings(None)`. Without a TapDB-local binding,
`daylily_tapdb/cli/context.py:148–164` takes the shared `cli_core_yo` runtime's
config path, which in this process identifies Dewey's YAML.

The public `daylily_tapdb.cli.context.set_cli_context` interface at
`context.py:122–139` binds only TapDB's module-local client/database/path state.
Its explicit path takes precedence over the shared runtime path. It does not
replace Dewey's `cli_core_yo` context. For this single-target Dewey process, the
binding must persist after engine creation so later metrics/GUI calls continue
to use the same validated TapDB configuration.

**Accepted application commit:**
`5251d1e6a42452284b36dc511c73b1446ff21ee0`.

- `dewey_service/integrations/tapdb_runtime.py` SHA-256:
  `91fa5122a22cfa5cb00f83055a26d099324ca77e258f6c3bdd665f62e6a76fa4`.
- New regression file `tests/test_tapdb_process_context.py` SHA-256:
  `f8a539b5e3636ffac34eb109470ff16408d268c353eaee61e9f456386e03311d`.

E reviewed the complete diff. `load_runtime_config` calls the public setter
only after existing absolute-file, native config, domain, owner and engine
validation succeeds, before returning to backend `get_db` construction.
There is no installed-package patch, runtime monkeypatch, inferred config or
shared-context replacement. No must-fix finding remains in this exact change.

D reproduced the original failure with both actual initialized container and
QEO CLI contexts using released native engine/metrics APIs. The fixed tests
prove correct TapDB settings, unchanged Dewey context object/path, and no
binding after invalid domain/owner/engine input. E read these five new cases
and D's **28 affected cases passing** report; E did not rerun them. Engines in
these regressions were constructed without opening database sessions.

## Accepted runtime-verifier-only repair

**Accepted commit:** `ddf3b1b5f87ddada7ad2053446869619b110bb1b`.
New helper SHA-256:
`ed71f502750e4041c7b6cabe6b03e1c4e5134eb92f9cc06a8f017849d8961680`.

Only `verify_runtime` adds the public setter import and call, after strict
config/lane, image-version and new-output checks, before disposing/creating
native engines. Bootstrap and bind bodies are unchanged. E reviewed all four
new helper cases and reused D's **23 affected helper cases passing** report.
They exercise actual released engine/metrics construction and fail before
context binding for invalid config, image version or occupied output.

Stage this new hash only for fresh runtime verification. Keep the historical
helper `9921210bd5b3ee4fcc52f06184dd88a6efa986e23e608f3672ccffcd529372f2`
and its existing bootstrap/bind receipts intact. Use that historical helper for
the already accepted deferred final bootstrap plan below. The whole candidate
image must be rebuilt from the accepted application source; the previous failed
candidate is preserved. No broader test suite was repeated by E.

## Deferred final bootstrap plan accepted

E independently accepts the offline final bootstrap plan for its later stage
after the final database-copy gates:

| Input | Exact SHA-256 |
|---|---|
| Plan file, 2821 bytes | `54f17f91911b12ae725390f01c8e00cfa75a0eacfb9902d5b8c899b442d5a5ce` |
| Outer plan seal | `4cc516773ac1b104815b5dc29064ab0734567f9671f4c093c3be2d78d5d5773b` |
| Native plan seal | `e24812eea9970538c46f48227970a09b73a5314a7c05d747fa64caf19f427218` |
| Production runtime configuration | `987b25f1659a1e72593bd4231307b1f7f6c7122d5cb20193c3681ba41a2fe353` |
| Replacement operator configuration | `c7bb450c5f24575d6c2ea4593f82083883ed0ba0e09e3a498412875121996607` |
| Production runtime secret reference record | `68b1107ffee7be03e16ba45e6c720b8b6080d01227c76e46fc095a75aaac0e8d` |

The target is exactly `dewey_prod_tapdb10`, role `dewey_runtime_9`, and fixed
runtime identity `/opt/dewey/day/releases/9.0.0/tapdb-runtime.yaml`. It uses
`replacement-operator.yaml` with the same dayhoff operator reference, CA and
registry hashes. E compared the dedicated production secret reference's exact
role, lane, ARN and version to the plan; it is separate from the rehearsal and
operator secrets. E read only reference metadata, never secret material.

Both plan seals validate. All target fields equal the accepted rehearsal plan
except the three explicitly intended database, role and runtime-path changes.
The plan requests LOGIN only, all elevated/INHERIT attributes false, no
memberships or schema changes, and CONNECT only on the fixed final database.
Its helper hash is the original `9921210…`. This configuration-only plan proves
neither database nor role existence; actual final-copy, bootstrap-result and
binding acceptance remain required in their planned order.

E made no live/database calls and no code changes. O can integrate the two
accepted code commits and rebuild without waiting for this documentation.
Runtime-only login/scope/privilege checks, eleven historical DGX bindings,
HTTP/authentication and isolated application acceptance still require actual
receipts from the rebuilt candidate.
