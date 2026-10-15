# Native graph node error boundaries

Dewey 11.0.10 pins TapDB 11.0.9 / baab96e47bbf5e02c8cbad85ab6445b37ed6a968.
Shared native DAG projection now retains valid branches around attributable
malformed nodes/references, invalid relationships, missing endpoints and cycles.
Bounded diagnostics and partial-result counts reach Kahlo and the native viewer.
Root authorization, service identity and owner/tenant/domain isolation remain
mandatory. This changes no stored records, schema, templates or workflows.

Dependency and lock coordinates were reviewed. No test campaign was run.
Exact EC2 image/deployment and read-only acceptance observations are recorded
under K31 in Kahlo's controlling 20261015T075127Z SeqNAS ledger.

The first candidate, Dewey 11.0.9, failed the existing EC2 build-time runtime
guard: dependency 11.0.9 was installed but the guard still required 11.0.8.
No image was published or deployed. The immutable source tag is retained;
11.0.10 aligns the guard, CLI lifecycle text and regression fixture. Kahlo
reads its installed package version and has no corresponding stale guard.
