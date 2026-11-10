# MultiQC collateral registration repair

## Current continuation state

Objective: register Ursa hybrid manifest M-RGX-3PBDV and the current production command catalog without treating declared MultiQC collateral as independent report entrypoints. Source implementation complete; release/deployment/runtime acceptance pending. No tests run. Existing report access and bundle boundary rules remain unchanged.

Gate 0: repo Daylily-Informatics/dewey, branch codex/qeo2-internal-multiqc-20261109, baseline e481aaa08687b65faa2673f35192aa01194ba4c4, deployed 12.0.34. Final image builds only on existing Dayhoff EC2 i-07df3a933e4839f52/us-west-2. Ursa campaign/registration repair authorized in the parent ENG-179 work; no new credentials or sibling rollout.

## Native failure and fix

Ursa import M-RGX-3PX03 returned HTTP400: `MultiQC bundle links a different report outside its report-specific assets`. The manifest explicitly classifies `results/day/hg38/reports/DAY_final_multiqc.original.html` as `multiqc_report_asset`. Dewey nevertheless inspected this archived original as an independent report, inferred its owned directory as `DAY_final_multiqc.original_files`, and rejected its real link to `DAY_final_multiqc_files/runtime/DAY_rule_timeline.html`. The main report and section links use their correct report-owned paths.

The repair honors the explicit artifact role during automatic registration. Collateral remains registered as manifest-listed artifacts and is served within the main report bundle. Actual report entrypoints retain the existing inspection and sharing rules. No source artifacts are rewritten, omitted, or re-exported. Retry the same Ursa import identity after deployment; do not rerun science.

| Owner | Work | State | Evidence |
|---|---|---|---|
| Dewey | Honor declared collateral role | Implemented | dewey_service/services/report_bundles.py |
| Coordinator | Tagged release / EC2 build / scoped deployment | Pending | Native receipts to follow |
| Ursa | Same import retry and delivered webshare | Pending | M-RGX-3PX03 |
