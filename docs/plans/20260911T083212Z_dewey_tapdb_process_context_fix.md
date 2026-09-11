# Dewey TapDB process context repair

- Owner: D; independent acceptance: E; live operator: O.
- Baseline: Dewey branch commit `3c1a355ea78206426c086fc458a6a4668ce99667`.
- Released dependencies remain exactly TapDB `10.1.1rc1` and Meridian `0.4.8`.
- Status: local repair verified; complete rebuilt image and deployed application acceptance remain O/F work.

The isolated candidate stopped during backend construction: native TapDB engine metrics
resolved the shared `cli_core_yo` context's Dewey YAML as a TapDB config. Supplying an
explicit path to `get_db` alone did not bind TapDB's subsequent no-path settings calls.

`load_runtime_config` now calls the released public
`daylily_tapdb.cli.context.set_cli_context` with the explicit TapDB path, client and
database after the existing path/config/domain/owner/engine checks pass. The binding
persists for the single-target Dewey process, including later metrics and embedded GUI
calls. It does not replace or modify Dewey's `cli_core_yo` context. Both the normal
server/container and QEO CLI service factories construct `TapDBBackend` through this
function before calling native `get_db`.

No installed package, database, principal binding, allocator state, deployment config,
dependency lock, migration receipt or previously published image was changed.

## Focused verification

Activated the repository with `source ./activate day`; the environment installed the
declared dependencies and reports TapDB `10.1.1rc1` / Meridian `0.4.8`.

Before applying the repair, the new container and QEO CLI context regressions both
failed at the actual released `get_db -> maybe_install_engine_metrics -> get_admin_settings`
boundary with `TapDB config metadata is required`. The three invalid-scope checks passed.

After the repair, **28 focused cases passed**:

```text
python -m pytest tests/test_tapdb_process_context.py tests/test_tapdb_runtime_unit.py tests/test_tapdb_backend_unit.py::test_backend_init_rejects_invalid_config_before_connect tests/test_tapdb_backend_unit.py::test_backend_init_uses_public_scoped_runtime -q
ruff check dewey_service/integrations/tapdb_runtime.py tests/test_tapdb_process_context.py
git diff --check
```

The new tests use the installed released context/config/engine/metrics APIs and a
nonconnecting local PostgreSQL engine. Only Dewey's settings provider is substituted
for the isolated fixture. They assert that both entrypoint contexts retain the same
Dewey runtime object/path and that rejected domain/owner/engine settings do not bind
TapDB. The unchanged full application suite was not repeated. Actual migrated-Aurora
runtime/session/application acceptance remains required with the rebuilt image.
