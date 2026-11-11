# Dewey Google Fonts and Ursa compute provenance

## Current continuation state

User authorized support for Ursa cluster/controller provenance and asked for Google Fonts support instead of changing the existing ONT Run QC capsule. Source baseline Dewey 12.0.38 / b5f7b66074d172ae6f80bf3de1c132a45469156a on codex/qeo2-internal-multiqc-20261109. Worktree /Users/jmajor/projects/dewey-registration-pool-20261108. Build only the final tagged Dewey image on EC2 i-07df3a933e4839f52 in us-west-2. No test campaign, PR, merge, or capsule changes.

| Gate | State | Native evidence |
| --- | --- | --- |
| Diagnose | Complete | ONT Run QC M-RGX-3YXP6 live 0/0/0. Dewey returned HTTP 400 for fonts.googleapis.com/css2 during report registration. Dewey also rejected the cluster edge for Bjuice because the verified Ursa native compute cluster template had no reviewed kind (SSM d41feb7c-23be-40f1-8138-fa68bd952da3); no edge was written. |
| Source | Complete | Recognize exactly Ursa compute/cluster/generic/1.0. Allow Google Fonts stylesheet links and CSS imports from the HTTPS /css and /css2 endpoints; permit those stylesheets and Google-hosted font files in isolated preview CSP. Existing script and connection origins and referrer policy remain. |
| Release and deployment | Pending | Dewey 12.0.39 candidate. Coordinate the Ursa 15.0.48 deployment already in flight. |
| Production acceptance | Pending | Retry the existing ONT Run QC import unchanged. Attach requested missing compute lineage to completed Bjuice and Illumina Sentieon results from their existing receipts. |
