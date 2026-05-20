# AWS Dewey External Reference Graph Links Ledger

Date: 2026-05-20 UTC

## Scope

User corrected scope: the stale local Dewey checkout must not be used as source of truth. Work was redone against the AWS EC2 Dayhoff deployment serving `https://dewey.dev.lsmc.life`.

Control ledger path: `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey/docs/plans/20260520T060300Z_aws_dewey_external_refs_live_ledger.md`

## Gate 0: Inventory Freeze

| Item | Evidence |
|---|---|
| AWS account/profile | `AWS_PROFILE=lsmc`, account `108782052779` |
| Region | `us-west-2` |
| Active host | `i-09126000eb19643b0`, Name `Dayhoff-aws3041-Compute/Hostprimary`, public IP `52.41.146.74`, private IP `10.0.0.77`, SSM Online |
| Deployed service | Dewey on deploy `lsmcok1`, port `8914`, public host `dewey.dev.lsmc.life` via ngrok |
| Running checkout | `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey` |
| Running process before restart | PID `248915`, `/home/ubuntu/miniconda3/envs/DEWEY-lsmcok1/bin/python -m uvicorn dewey_service.app:create_app --factory --host 0.0.0.0 --port 8914` |
| Source baseline | Detached HEAD `5e8f566`, tag description `3.0.12-dirty`, branch context `origin/codex/aurora-hostaddr-release-20260518` |
| Pre-existing dirty files not owned by this patch | `dewey_service/app.py`, `dewey_service/services/base.py`, `dewey_service/services/sharing.py`, `dewey_service/settings.py`, `dewey_service/static/console.css`, `dewey_service/templates/_artifact_links.html`, `dewey_service/templates/artifact_detail.html`, `tests/conftest.py`, `tests/test_artifacts_ui.py`, `tests/test_service_relationships.py`, `tests/test_share_references.py`, untracked `dewey_service/templates/shares.html`, untracked `docs/plans/` |
| Scope guard | Modify deployed Dewey only. Do not modify Bloom, Kahlo, Atlas, Dayhoff service code, or stale local Dewey checkout. Do not revert existing dirty deployed changes. |

## Requirement Rows

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| AWSCTX-001 | AWS context | Identify active AWS host and deployed Dewey checkout instead of stale local tree. | SUCCESS | feature_implementation | Gate 0 | orchestrator | SSM/EC2 probes found active host `i-09126000eb19643b0`, deploy `lsmcok1`, checkout `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey`. |  | Active deployed context established before patching. |
| AWSCTX-002 | Deployed source inspection | Inspect deployed `/external-reference/create` route and service implementation. | SUCCESS | feature_implementation | Gate 0 | orchestrator | Remote snippets showed routes in `dewey_service/app.py`, UI in `dewey_service/templates/artifact_detail.html`, service behavior in `dewey_service/services/external_objects.py`. |  | Confirmed deployed code already had create route but relation projection/link rendering was incomplete. |
| AWSCTX-003 | Dewey graph projection | Make external reference creation/listing emit TapDB graph refs and link metadata on the target Dewey artifact/artifact set. | SUCCESS | feature_implementation | Gate 3 | orchestrator | Patched `dewey_service/services/external_objects.py` to sync `json_addl.properties.external_payload.tapdb_graph` refs with `source_field=dewey.external_object_relation`, enrich relation responses, and lazily repair existing relations during listing. |  | Implemented in deployed Dewey checkout only. |
| AWSCTX-004 | UI link | Make the artifact detail external relation show the referenced external EUID as an actual link when a validated URI exists. | SUCCESS | feature_implementation | Gate 3 | orchestrator | Patched `dewey_service/templates/artifact_detail.html` relation table to render `external_object_id` as an anchor to `external_uri`, with system/type metadata. |  | UI now links to the external system record from the external relation row. |
| AWSCTX-005 | Validation metadata carry-through | Preserve explicit target metadata from configured external references for graph/link payloads. | SUCCESS | feature_implementation | Gate 3 | orchestrator | Patched `dewey_service/app.py` to carry `base_url`, `graph_data_path`, and `object_detail_path_template` from target config into external object/relation metadata. |  | Does not infer fallback targets; it only carries explicit configured values. |
| AWSCTX-006 | Remote tests | Compile and run focused tests in the deployed checkout. | SUCCESS | contract_test | Gate 5 | orchestrator | `/home/ubuntu/dayhoff_remote_work/logs/dewey_external_graph_refs_tests_20260520T055711Z.log`: `python -m compileall dewey_service/app.py dewey_service/services/external_objects.py`; `pytest tests/test_artifacts_ui.py::test_artifact_detail_external_reference_validate_and_create tests/test_service_relationships.py::test_external_object_relation_lifecycle -q` -> `2 passed`. |  | Focused deployed checkout tests passed. |
| AWSCTX-007 | Contract smoke | Prove emitted graph refs parse through the shared TapDB external refs parser. | SUCCESS | contract_test | Gate 5 | orchestrator | `/home/ubuntu/dayhoff_remote_work/logs/dewey_graph_ref_contract_smoke_20260520T055742Z.log`: in-memory Dewey service emitted Bloom graph ref with `system=bloom`, `root_euid=Z-DGX-1RA`, `href=https://bloom.dev.lsmc.life/object/Z-DGX-1RA`; `daylily_tapdb.services.external_refs.external_ref_payloads` parsed it. |  | Contract smoke passed. |
| AWSCTX-008 | Restart | Restart deployed Dewey so the public service serves patched code. | SUCCESS | feature_implementation | Gate 5 | orchestrator | `/home/ubuntu/dayhoff_remote_work/logs/dewey_restart_external_graph_refs_20260520T055809Z.log`: stopped PID `248915`, started tmux `dewey-external-refs-20260520T055809Z`, new PID `256838`, readyz OK locally and at `https://dewey.dev.lsmc.life/readyz`. |  | Live service restarted and healthy. |
| AWSCTX-009 | Live artifact probe | Probe live artifact `Z-DGX-1RA` and its external relations through the deployed service API. | SUCCESS | contract_test | Gate 5 | orchestrator | Initial probe `3b2246e9-51bb-4c55-a05d-072c4222f557` failed because remote shell lacked bare `python`; retry `369d80af-b730-48f1-902a-f4ee7ad91582` failed because SSM default `/bin/sh` lacks `pipefail`; final retry `39edfc0a-a53f-45d1-8aa8-38fdb21fad91` succeeded with log `/home/ubuntu/dayhoff_remote_work/logs/dewey_live_artifact_probe_envpy_20260520T060127Z.log`. |  | Live API returns artifact `Z-DGX-1RA` and one external Bloom relation with `external_uri=https://bloom.dev.lsmc.life/object/Z-BEQ-2Z` and `external_graph_ref.source_field=dewey.external_object_relation`. |

## Changed Files

- `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey/dewey_service/app.py`
- `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey/dewey_service/services/external_objects.py`
- `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey/dewey_service/templates/artifact_detail.html`
- `/home/ubuntu/.cache/dayhoff/local/lsmcok1/repos/dewey/docs/plans/20260520T060300Z_aws_dewey_external_refs_live_ledger.md`

## Final Terminal-State Report

All rows in this ledger are terminal `SUCCESS`. The deployed AWS Dewey service has been patched and restarted. Live artifact `Z-DGX-1RA` now exposes its existing Bloom external relation through the API with link metadata and a TapDB graph external ref suitable for cross-system DAG ingestion.

Residual note: this work did not modify Bloom, Kahlo, Atlas, or Dayhoff service code. If Kahlo still does not render the new Dewey/Bloom edge, the next scope is Kahlo's external-ref ingestion/view refresh against the live Dewey graph payload, not local Dewey source.
