# Dewey Branch Triage

Date: 2026-04-02

## Summary

This triage was run against current `origin/main` after `git fetch --all --prune`.

Classification used:

- direct-ancestry merge: branch tip is reachable from `main`
- merged via PR merge commit or equivalent: branch content is on `main`, even if the branch tip is not an ancestor
- historical or obsolete: not suitable to merge as-is

Current result:

- no open Dewey PRs need attention
- no local branch appears to contain product work that still belongs merged into `main`
- most remaining branches are cleanup candidates

## Verified Merge Evidence

Direct-ancestry merges confirmed with `git branch --merged main`:

- `codex/artifact-detail-download`
- `codex/artifacts-ui-restore`
- `codex/cli-consolidation`
- `codex/deploy-name-activate-contract`
- `codex/dewey-0.2.3-release`
- `codex/dewey-metapub-mvp`
- `codex/hardened-cognito-web-session`
- `codex/incoming-dewey-main`
- `codex/integrate-dewey-main`
- `codex/publish-dewey-mainline-merge`
- `codex/release-dewey-0.2.4`
- `codex/thin-conda-no-siblings-dewey`

Merged via PR merge commit or equivalent:

- `codex/deployment-banner-release-dewey`
  - `git cherry -v main codex/deployment-banner-release-dewey` reports the branch commit as already applied
- `codex/dewey-tapdb-hard-cut-v3`
  - merged as `main` commit `a029abb` (`Hard-cut Dewey TapDB config and DGX prefixes (#26)`)
- `codex/lsmc5-dewey-standalone`
  - merged as `main` commit `44c9553` (`Set Dewey TapDB client code (#27)`)
- `fix/cognito-managed-login-logout-flow`
  - merged by PR `#7`
- `codex/solo-dewey-file-parity`
  - merged by PR `#11`
  - GitHub PR `#11` records `merge_commit_sha=1040ec39a2fce52ec9a9bdbda4d7f11c785c3b15`
  - `git diff --stat 1040ec3 codex/solo-dewey-file-parity` is empty

## Historical Or Obsolete Branches

These should not be merged as-is:

- `archive-dewey-pre-main-merge`
  - explicit archive snapshot
- `wip/pre-stash-changes`
  - based on obsolete `dewey_service/cli.py` shape rather than the current `dewey_service/cli/` package
- `forge/tapdb-0-2-5-release-train`
  - one-commit scratch branch with message `X` and a symlinked `activate`

## Note On `git cherry`

`git cherry` was useful for identifying several squash-equivalent branches, but it was misleading for `codex/solo-dewey-file-parity`.

That branch contains the original two commits from PR `#11`, while `main` contains the GitHub merge commit `1040ec3` with the same tree content. In that situation:

- `git cherry -v main codex/solo-dewey-file-parity` still shows the original commits as absent
- `git diff 1040ec3 codex/solo-dewey-file-parity` is the stronger check and shows no content difference

For Dewey branch triage, PR merge metadata plus tree equality is the authoritative check when ancestry and patch-id checks disagree.

## Cleanup Candidates

Branches that are safe cleanup candidates because their content is already on `main`:

- `codex/artifact-detail-download`
- `codex/artifacts-ui-restore`
- `codex/cli-consolidation`
- `codex/deploy-name-activate-contract`
- `codex/deployment-banner-release-dewey`
- `codex/dewey-0.2.3-release`
- `codex/dewey-metapub-mvp`
- `codex/dewey-tapdb-hard-cut-v3`
- `codex/hardened-cognito-web-session`
- `codex/incoming-dewey-main`
- `codex/integrate-dewey-main`
- `codex/lsmc5-dewey-standalone`
- `codex/publish-dewey-mainline-merge`
- `codex/release-dewey-0.2.4`
- `codex/solo-dewey-file-parity`
- `codex/thin-conda-no-siblings-dewey`
- `fix/cognito-managed-login-logout-flow`

Suggested local-only cleanup commands, if wanted later:

```bash
git branch -d codex/artifact-detail-download
git branch -d codex/artifacts-ui-restore
git branch -d codex/cli-consolidation
git branch -d codex/deploy-name-activate-contract
git branch -d codex/deployment-banner-release-dewey
git branch -d codex/dewey-0.2.3-release
git branch -d codex/dewey-metapub-mvp
git branch -d codex/dewey-tapdb-hard-cut-v3
git branch -d codex/hardened-cognito-web-session
git branch -d codex/incoming-dewey-main
git branch -d codex/integrate-dewey-main
git branch -d codex/lsmc5-dewey-standalone
git branch -d codex/publish-dewey-mainline-merge
git branch -d codex/release-dewey-0.2.4
git branch -d codex/solo-dewey-file-parity
git branch -d codex/thin-conda-no-siblings-dewey
git branch -d fix/cognito-managed-login-logout-flow
```
