# Dewey GUI/API deletion prohibition

## Current continuation state
Updated2026-10-11T00:02Z. DEPLOYED: user requested disable all deletion from Dewey GUI/API and release/deploy new Dewey. Annotated11.0.3 tagbe76d8d33b49df7441c39204c65d02ff5486f2f8, sourceeba14993e342386641803fa99b58ce63cf51e5a1, branchcodex/dewey-tapdb-globaldag-20260926 in this repository. FinalEC2image5605870c2bf4cbafa89049ef08997ea50b73ca1cc557fff2255ad0752af126fb built23:58:45Z on i-07df3a933e4839f52/us-west-2. Finalcontainer132a4e648ac6b674468981bcf75ac713c0bf76fc51e4553f5c17b8933ffa9c18 deployed00:00:14Z; readytrue/exactversion+SHA. Siblingidentities and mountedapplicationconfig unchanged; two releaseprovenanceenvfields corrected. No forcedkill or data/DBmutation. Objective COMPLETE; all4rowsSUCCESS. No tests, PR/merge, deletion, budgets, credentials/access changes or schedules.

Source: unconditional outer ASGI403 independent of roles/authentication for DELETE and POST deletion/archive/abort endpoints. Service deletion/archive/member-removal bodies replaced with explicit403; existing deletepreviews cannotexecute. Uploadreplacement disallowed, newkeys preserve IfNoneMatch. EmbeddedTapDBbrowser nativebridge userrole and allunsafeHTTP blocked to preventgenericedit/backuprestore deletion. GUIbuttons/handlers removed; share/tokenrevocation remains because records retained. Runtimepolicy and servedregistryJS matchreleasehashes. Authenticatedsharedlogin/adminrecord loaded11.0.3 with noDelete/Archivecontrols. Authenticatedadministrator S3folder/objectdialog also verified: Download/Register only, noDelete/Replace; recordpage noArchive. SharedLogin existingauthenticatedsession resolveddirectlytoLibrary; no credentialentry or OAuthconfigurationchange. GUIreceipt/screenshot saved. Next: none after ownedreceiptcommit. Evidence `docs/plans/evidence/20261010T235500Z_dewey_deletion_disabled/`.

Runtime provenance issue: initial11.0.3 image deployed23:59:04Z correctly but Compose retained predecessorDEWEY_BUILD_SHA andLSMC_RELEASE_SHA. Readback exposed11.0.3/oldSHA; no source/image defect. Guarded standardimagecutover corrected exactlythose2metadatafields using sameimage, preservednativeconfigs/siblings. Finalreadyz00:00:14Z+ confirmedexacteba1499SHA. Originalreceipts retained.

## Gate 0 inventory
Source sweep: registry S3 POST deletion preview/execute, HTTP DELETE member removal in registry and legacy artifact-set routes, POST archive, upload abort/replacement, embedded TapDB objectDELETE and generic mutation/backup restore surfaces. Existing share/token revocation changes access status while retaining records; preserve these security controls. Use role-independent HTTP prohibition and service guards; embedded raw TapDB browser read-only to prevent generic field/restore deletion bypass. Preserve ordinary registry registration/metadata/upload-new/download/sharing operations. Clean source baseline; tests disabled under explicit user policy. NativeGUI permissions inspected from packaged TapDB11.0.2. Production identity read-only verified in interactiveubuntu session.

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| DEL-01 | Reject deletion API routes for everyone, including administrators | SUCCESS | deletion_policy.py/serviceguards |
| DEL-02 | Remove GUI destructive controls and fence embedded generic mutations | SUCCESS | registry.js/nativeTapDBbridge |
| DEL-03 | Annotated release, EC2 final build, Dewey-only deployment | SUCCESS | image.json; final_deployment.json; exactreadyz |
| DEL-04 | Runtime/GUI readback and exact receipts | SUCCESS | readyz-final.json; gui.json; gui-admin-no-delete.png; runtime-source-readback.json |

Operator helper upload first stopped on SSM nested multiline shell quoting before writing or mutation (04c3c06f-fc72-4150-8f8f-aeb91feaac9e). Corrected single-line helper write succeeded64955dcd-50b8-456f-a372-3da3cedcca9e; local/remote SHA256 both0d8dd2a08cb00c982b9402dd335d7edd01f45cc67c40ac63ecfbcb8f3500c954. No image rebuild required.

## Final report
All rows terminal: yes. Objective complete: yes. SUCCESS4, no blocked/failed rows. No automated tests, lint or destructive API requests issued under standing policy. Source AST/JavaScript syntax/diff reviewed; runtime readiness, exact version/commit/image, source content hashes and authenticated administrator GUI observed. Data was preserved; sibling identities and mounted config unchanged. Release provenance fields corrected separately without rebuilding the exact image. User acceptance remains theirs to provide.
