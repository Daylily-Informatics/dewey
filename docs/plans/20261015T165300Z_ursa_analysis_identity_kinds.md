# Ursa analysis identity registration

The human authorized fixing the Dewey registration blocker, retiring the current
eleven Ursa catalog requests and submitting eleven fresh after the correction.
The controlling ledger is OWY's
`docs/plans/20261014T202934Z_ursa21_owy_catalog_ledger.md`.

Production Dewey11.0.6/016f9c7 rejected Ursa executionM-RGX-2QC0K with HTTP400:
`No unique reviewed ursa business kind for native owner template ('analysis', 'execution', 'generic', '2.0')`.
The live analysis completed0/0/0 and native exporttask-058dafa5a57384999 succeeded,
detached and verified4218objects/698292669bytes. This is a registration failure.

The correction registers exact owner template coordinates for
`analysis_execution` (analysis/execution/generic/2.0) and `analysis_unit`
(analysis/unit/generic/1.0), both with explicit TapDB object semantics. Existing
Ursa run coordinates retain the established `analysis` business kind. Ursa's
publisher must use that declared wire name for its internal analysis_run role.
No aliases, guessed templates, opaque-identity conversion or validation bypass
is introduced. Exact native owner, EUID and tenant verification remains intact.

Only this service's tagged final image is built on the existing day deployment
EC2i-07df3a933e4839f52. Database schema, credentials, budgets, deletion policy and
sibling configuration remain unchanged. DayOA19.0.2/DYEC21.0.3 are unchanged.
Regression cases are added but not run under the production-first policy.
Source syntax and diff inspection do not establish runtime acceptance; the
fresh catalog campaign must independently complete export and registration.
