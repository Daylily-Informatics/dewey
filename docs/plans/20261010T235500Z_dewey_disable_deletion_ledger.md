# Dewey GUI/API deletion prohibition

## Current continuation state
ACTIVE: user requested disable all deletion from Dewey GUI/API and release/deploy new Dewey. Repo `/Users/jmajor/projects/mega_dayhoff/repos_work/dewey-tapdb-globaldag-20260926`, branch `codex/dewey-tapdb-globaldag-20260926`, clean baseline cb8116e; production11.0.2 source3f782eebc6e43ded3fa655c3fcdc1c2c616bcd89, EC2 i-07df3a933e4839f52/us-west-2, container7a34c472d7e6e0d6c000f977d3e06513660510963869e2dca11bb1d03d6089c2, immutable imagedf7bca9ea7cf9e999a24d4d8e8f1369182104d989fc20c25b3cc4209ecb31499; running/restarts0. Stop after exact new tagged Dewey image deployed and runtime/GUI readback. No tests/PR/merge, data deletion, cleanup, credential/access/budget changes, sibling deployments or schedules authorized. Existing native deployment image replacement retained. Implemented: unconditional outer ASGI403, removed service delete/archive/member-removal bodies and GUI controls; upload replacement/abort forbidden, embedded native bridge nonadmin+all mutations403. PythonAST and JavaScript syntax review passed; no tests. Next: publish11.0.3 then finalEC2build.

## Gate 0 inventory
Source sweep: registry S3 POST deletion preview/execute, HTTP DELETE member removal in registry and legacy artifact-set routes, POST archive, upload abort/replacement, embedded TapDB objectDELETE and generic mutation/backup restore surfaces. Existing share/token revocation changes access status while retaining records; preserve these security controls. Use role-independent HTTP prohibition and service guards; embedded raw TapDB browser read-only to prevent generic field/restore deletion bypass. Preserve ordinary registry registration/metadata/upload-new/download/sharing operations. Clean source baseline; tests disabled under explicit user policy. NativeGUI permissions inspected from packaged TapDB11.0.2. Production identity read-only verified in interactiveubuntu session.

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| DEL-01 | Reject deletion API routes for everyone, including administrators | SUCCESS | deletion_policy.py/serviceguards |
| DEL-02 | Remove GUI destructive controls and fence embedded generic mutations | SUCCESS | registry.js/nativeTapDBbridge |
| DEL-03 | Annotated release, EC2 final build, Dewey-only deployment | OPEN | pending11.0.3 |
| DEL-04 | Runtime/GUI readback and exact receipts | OPEN | pending |
