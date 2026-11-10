# MultiQC collateral registration repair

## Current continuation state

Objective: register Ursa hybrid manifest M-RGX-3PBDV and the current production command catalog without treating declared MultiQC collateral as independent report entrypoints. Source/release/deployment complete:12.0.36/0ef1d750ba741e35eac2d20310c6c3cfc1bdb8aa, native Compose success13:37:35Z. Same-import delivery acceptance pending. No tests run. Existing report access and bundle boundary rules remain unchanged.

Gate 0: repo Daylily-Informatics/dewey, branch codex/qeo2-internal-multiqc-20261109, baseline e481aaa08687b65faa2673f35192aa01194ba4c4, deployed 12.0.34. Final image builds only on existing Dayhoff EC2 i-07df3a933e4839f52/us-west-2. Ursa campaign/registration repair authorized in the parent ENG-179 work; no new credentials or sibling rollout.

## Native failure and fix

Ursa import M-RGX-3PX03 returned HTTP400: `MultiQC bundle links a different report outside its report-specific assets`. The manifest explicitly classifies `results/day/hg38/reports/DAY_final_multiqc.original.html` as `multiqc_report_asset`. Dewey nevertheless inspected this archived original as an independent report, inferred its owned directory as `DAY_final_multiqc.original_files`, and rejected its real link to `DAY_final_multiqc_files/runtime/DAY_rule_timeline.html`. The main report and section links use their correct report-owned paths.

The repair honors the explicit artifact role during automatic registration. Collateral remains registered as manifest-listed artifacts and is served within the main report bundle. Actual report entrypoints retain the existing inspection and sharing rules. No source artifacts are rewritten, omitted, or re-exported. Retry the same Ursa import identity after deployment; do not rerun science.

| Owner | Work | State | Evidence |
|---|---|---|---|
| Dewey | Honor declared collateral role | Implemented | dewey_service/services/report_bundles.py |
| Coordinator | Tagged release / EC2 build / scoped deployment | Pending | Native receipts to follow |
| Ursa | Same import retry and delivered webshare | Pending | M-RGX-3PX03 |

## Predeployment source review

12.0.35 was tagged and its final-candidate build started before source review found that the detached registry path also needs the same classification before it creates an inspection inventory.12.0.36 supersedes35 before deployment and moves the collateral decision into the shared HTML candidate selector, covering both paths without adding checks. No35 deployment or runtime retry occurred. No tests run.

## Build interruption

Final36 build failed ResourceExhausted during runtime COPY because the EC2 root968G filesystem filled. Native Docker unused-cache cleanup reclaimed61.74GB and returned0. Same immutable36 tag retried through native release builder at /home/ubuntu/dewey-multiqc-collateral-12.0.36-retry1, SSM52f8a8ba-e1be-4356-b745-6b3876107985. No runtime images, volumes, or AWS resources deleted. Scoped deployment helper preserves existing service credentials/config and changes only the selected Dewey image/source identity. Native deployment and same-import delivery acceptance pending.

## Native build and deployment results

Final12.0.36 build retry succeeded13:36:37Z, SSM52f8a8ba-e1be-4356-b745-6b3876107985. Image sha256:faa2d45fbec0bcc9180b18b1d4034e638b9df61979a544832abc17e85f099687. Scoped native Compose deployment247dad28-5e7e-4cf6-ad19-d9e35c925db5 returned0 at13:37:35Z. Existing credentials/config retained. Native build/deployment success is accepted without secondary checks. Runtime acceptance uses the existing Ursa importM-RGX-3PX03.
