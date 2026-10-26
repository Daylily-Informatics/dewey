# Dewey 9 source reconciliation receipt

Recorded 2026-09-11T03:53:19Z. Owner: Agent A. Controlling row: L01 in
[the migration ledger](20260910T185538Z_dewey_tapdb10_major_ledger.md).
The coordinator owns that ledger, integration and all live operations.

## Result and source boundary

Local source reconciliation is complete. A normal merge makes the verified
remote `main` an ancestor of the migration branch while preserving every
non-documentation file from the approved deployed source. This receipt is
source/Git evidence; the coordinator must separately accept fresh live-source
parity under L00 before closing the dependent L01 gate. No dependency, runtime,
image, database, live service, default branch, remote branch or tag changed here.
TapDB 10.1.0 adoption and Dewey 9.0.0 release remain later work.

| Ref or baseline | Exact identity | Disposition |
| --- | --- | --- |
| Approved deployed source | `556dfcf936ea11e25f6126931fe1f655482d00a6` | Controls all non-documentation files in this reconciliation |
| Coordinator start | `5c75e7b889ccb6136549500e7edb7519c0672449` | Deployed source plus the approved migration ledger; ledger unchanged by Agent A |
| Refreshed remote main | `ef7f5412b5c7a4d3a8c47fb55500fa66f165b0ca` | Merged normally; five documentation/evidence files |
| Refreshed resolver branch | `598be4d5f31525e982de01b36a284704fa603042` | Seven receipt/manifest documents retained; later helper code excluded |
| Refreshed remote jemdev10 | `6a0e86a14798997f22daa2aa381ba2946fd15766` | Preserved on its existing ref; undeployed product delta excluded |
| Common source/main ancestor | `dea0009b743ad5b627177acdf21c87dd5c1d67c1` | Annotated 8.0.2 source baseline |
| Local reconciliation merge | `17a0edfe2a4655ce8183fa85d516b619a5506c96` | Parents are coordinator start and remote main above |

Agent worktree:
`/Users/jmajor/projects/mega_dayhoff/.codex-worktrees/dewey-source-reconcile-20260911`.
Agent branch: `codex/dewey-source-reconcile-20260911`.
Initial and post-merge working trees were clean. Existing worktrees were left
in place. `git fetch origin` refreshed refs, and `git ls-remote --symref origin
HEAD refs/heads/main refs/heads/jemdev10
refs/heads/codex/dewey-qeo-resolver-20260909 refs/tags/9.0.0` confirmed the same
remote commits, `jemdev10` as the unchanged default, and no 9.0.0 tag.

## Merge method and integration

1. Created the isolated worktree and branch from exact coordinator commit
   `5c75e7b889ccb6136549500e7edb7519c0672449`.
2. Ran `git merge --no-ff --no-commit
   ef7f5412b5c7a4d3a8c47fb55500fa66f165b0ca`. The ordinary merge completed
   without conflicts. Its staged diff contained only `docs/` paths.
3. Proved the complete non-documentation staged tree matched deployed
   `556dfcf936ea11e25f6126931fe1f655482d00a6`, then committed merge `17a0edf`.
4. Imported the selected resolver documents, added historical scope notices and
   this receipt, and retained machine-readable Git blob/mode parity evidence.

Main's delta from the common ancestor is exactly five documentation/evidence
files. It contains no Labcore product code. Therefore the ordinary merge keeps
all intended contributions and needs neither an `ours` strategy nor manual
runtime replacement. Relative to current main, the release branch also carries
the already-deployed resolver and container CLI additions; these are production
source reconciliation, not new undeployed features.

The coordinator must integrate this branch with a **Git merge preserving its
parents**, not a cherry-pick of the documentation delta. If the coordinator has
made no further commits, `git merge --ff-only
codex/dewey-source-reconcile-20260911` preserves this ancestry. Otherwise a normal
merge from that branch retains coordinator work and the main ancestor. Before the
eventual PR, refresh main again and review any new commits deliberately. A PR to
unchanged main can then merge normally after the later qualification gates.
This work creates no PR and changes no remote ref.

## Retained evidence and historical claim limits

The five main documents remain in the release tree:

- `docs/README.md`, with the dated migration reference and historical index label.
- `docs/derived_features_and_capabilities.md`, with a historical-snapshot notice.
- `docs/evidence/production_template_snapshots/20260719T044748Z/README.md`.
- `docs/evidence/production_template_snapshots/20260719T044748Z/generic_templates.json`.
- `docs/plans/20260901T064703Z_dewey_prod_reconciliation_capabilities_ledger.md`.

The last three files retain their exact main blobs. The July template snapshot
is evidence only, never a seed pack or current migration inventory. The
September 1 capability reference preserves useful findings and Phase 2 intake;
its old image/source/domain statements do not override fresh production
evidence or the approved preserved domain `M`.

The following seven documents were selected explicitly from resolver `598be4d`:

- `docs/plans/20260909T233800Z_qeo_resolver_ledger.md`.
- `docs/plans/20260910T005100Z_complete_multiqc_package.json`.
- `docs/plans/evidence/20260910_dewey_container_cli/github/base.json`.
- `docs/plans/evidence/20260910_dewey_container_cli/github/candidate.json`.
- `docs/plans/evidence/20260910_dewey_container_cli/github/container-cli-runtime.txt`.
- `docs/plans/evidence/20260910_dewey_container_cli/github/receipt.json`.
- `docs/plans/evidence/20260910_dewey_container_cli/package-registration.json`.

Five manifest/JSON receipts retain exact source blobs. The container CLI text
receipt has only trailing spaces removed from three lines; its recorded output
is otherwise unchanged. The resolver ledger retains the completion evidence
with the operator email replaced by a role description. Existing service-issued
EUIDs in these receipts remain historical
owner-issued identifiers; none were generated by this reconciliation. The
existing package contract gains a notice directing readers from its historical
pending-deployment section to the completion receipt.

The GitHub image receipt binds the deployed image
`sha256:4fe9907f2d3443f2360cad2463974a60f8158aea90cbf2aa7fbc56349d45a91f`
to source `556dfcf936ea11e25f6126931fe1f655482d00a6`. The container CLI receipt
records 4 pass, 0 warn, 0 fail and 4 skip. Those are historical build/runtime
receipts, not fresh production inspection or complete migration acceptance.

Resolver `598be4d` is **not a strictly documentation-only commit**: it also
changes `scripts/deploy_qeo_resolver.py` to reference a subsequent deployment and
preserve an existing credential. That script remains byte-identical to `556dfcf`
here. The one-off `docs/plans/20260910T005000Z_complete_package_source.py` operator
helper is not imported. Neither historical helper is a Dewey 9 deployment or
migration procedure; use the later reviewed full-image deployment work instead.

## Phase 2 preservation

No main, jemdev10, feature, resolver or user-worktree ref is deleted or rewritten.
Main's complete history is retained as a merge parent. Resolver `598be4d` remains
reachable on its existing local and remote branch. Existing jemdev10 and feature
refs retain their original commits for independent Phase 2 evaluation.

Jemdev10's delta from deployed ancestor `dea0009` has 23 paths, 2,378 insertions
and 97 deletions. It includes the Labcore contract/API, owner transaction
hardening, TapDB GUI/surface changes, configuration, service code and tests.
None enters this source tree. Relevant original commits are:

- `0944115` — Labcore sequencing owner contract.
- `3f1ccf1` — Labcore sequencing owner API (also existing `origin/GH-151`).
- `ae2ff79` — Labcore owner transaction boundary hardening.
- `6a0e86a14798997f22daa2aa381ba2946fd15766` — jemdev10 tip containing their merges.

The separate existing `origin/GH-146` ref at `e9f8caf` is also untouched.
No branch name or retained documentation implies deployment. Reassess these
changes after Phase 1 acceptance against the released TapDB 10.1.0 contract.

## Validation evidence

Machine-readable evidence:
[source-parity.json](evidence/20260911_dewey_source_reconciliation/source-parity.json).

| Check | Result |
| --- | --- |
| `git diff dea0009 origin/main --name-status` | Exactly five `docs/` paths |
| Normal main merge | No conflict; parents `5c75e7b` and `ef7f541` |
| Non-documentation tree comparison | All 181 Git paths, blobs and modes identical to `556dfcf` |
| Application plus lock/package inputs | All 71 `dewey_service/` files plus `pyproject.toml` and `uv.lock`: 73 identical |
| Full Dockerfile inputs | Runtime, config, package/lock, README, Dockerfile and entrypoint unchanged; covered by all 181 paths |
| Canonical non-documentation manifest SHA-256 | `08005910797bd82c1c06c59962a8d617f00c5f867509687ad979d34bd4eb5558` |
| Resolver application parity | All non-documentation files except its later deployment helper match `556dfcf`; that helper change is excluded |
| Main ancestor check | `git merge-base --is-ancestor ef7f541 HEAD` succeeds |
| Jemdev10 ancestor check | `git merge-base --is-ancestor 6a0e86a HEAD` returns 1, as required |
| Patch hygiene | `git diff --check` and `git diff --cached --check` pass |

No runtime test, installation, activation, build or live operation was performed
for this documentation/Git-only change. Source and build-input parity is the
bounded verification; it does not assert reproducibility of a future image or
replace L00/L06-L14 acceptance.
