# Dewey Google Fonts and Ursa compute provenance

## Current continuation state

User authorized support for Ursa cluster/controller provenance and asked for Google Fonts support instead of changing the existing ONT Run QC capsule. Source baseline Dewey 12.0.38 / b5f7b66074d172ae6f80bf3de1c132a45469156a on codex/qeo2-internal-multiqc-20261109. Worktree /Users/jmajor/projects/dewey-registration-pool-20261108. Build only the final tagged Dewey image on EC2 i-07df3a933e4839f52 in us-west-2. No test campaign, PR, merge, or capsule changes.

| Gate | State | Native evidence |
| --- | --- | --- |
| Diagnose | Complete | ONT Run QC M-RGX-3YXP6 live 0/0/0. Dewey returned HTTP 400 for fonts.googleapis.com/css2 during report registration. Dewey also rejected the cluster edge for Bjuice because the verified Ursa native compute cluster template had no reviewed kind (SSM d41feb7c-23be-40f1-8138-fa68bd952da3); no edge was written. |
| Source | Complete | Recognize exactly Ursa compute/cluster/generic/1.0. Allow Google Fonts stylesheet links and CSS imports from the HTTPS /css and /css2 endpoints; permit those stylesheets and Google-hosted font files in isolated preview CSP. Existing script and connection origins and referrer policy remain. |
| Release and deployment | Complete | 12.0.39 / 533c55eeeed4a966d317d796ec5a234e378db0d5. Final EC2 build 7f6bac6f-ebfc-4afd-b58a-f6603df9e64a exit 0 at 19:44:28Z. Scoped native Compose 5243c741-57c0-44d0-8063-bb916092c7fd exit 0 at 19:45:09Z. Ursa 15.0.48 followed at 19:45:38Z. |
| Compute lineage acceptance | Complete | SSM 63e32006-69a3-4c7d-9d8f-0b6b80a0317c exit 0 added seven relations across Bjuice and Illumina Sentieon. Native cluster EUIDs M-RGX-3WVA5 and M-RGX-3YMQD; existing controller references preserved. |
| Google Fonts acceptance | ONT registration complete; Illumina pending | Exact ONT Run QC import M-RGX-3Z5SP succeeded at 20:22:21Z; Dewey registered 156 artifacts. The same previously rejected report was accepted without a capsule edit or workflow rerun. Older Illumina Run QC import M-RGX-3XGE6 is queued separately. |
