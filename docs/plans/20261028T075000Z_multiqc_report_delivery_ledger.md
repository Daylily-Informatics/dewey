# Current continuation state
Updated: 2026-10-28T17:24:21.741518+00:00.

Follow-up diagnosis COMPLETE. User asked why initial MultiQC opening and section changes remain slow, and how to improve them. Read-only browser/source investigation; no software tests, source implementation, deployment, permission/limit changes, extra controls or monitors. Existing12.0.16/81690f9 build/deploy/proxy successes remain valid, 3/user12/process unchanged. These new task records are included in this versioned-branch publication.

Current findings: actual Coverage tab navigation took5888ms (interactive5169ms), with12resource requests transferring3600assetbytes (navigation-body bytes not recorded). Actual negotiated protocolhttp/1.1; JavaScript asset requests1842–3428ms, TTFB roughly1.1–1.9s. Existing QC Metrics navigation load4949ms. Timings from browser Performance API via DevTools in the isolated frame, normal cache settings. No exact cold-open wall time obtained: stopped further native browser input when the user's concurrent Chrome input was detected; browser access host unavailable. No credentials/cookies/headers captured.

Source trace: every section opens another HTML document and reinitializes MultiQC. private,no-cache retains live revalidation. Each asset goes through context/session/lineage, Login identity, share authorization and audit, native delivery reservation and S3conditional response. recipient_identity._request creates/closes a new httpx.Client each time, preventing connection reuse across asset checks. create_preview always creates a new pv-hostname; cache from previous preview hostname cannot be reused on a fresh opening. EntryHTML1215633bytes,15commonassets2785869bytes; sectionHTML1.4–3.0MB declared. Private-proxy no-gzip rule from16 preserves validators but increases cold payload. Individual Login/DB/S3 timing fractions were not instrumented; avoid attributing exact elapsed time to any single one.

Recommended next work, PROPOSED ONLY: application-lifetime pooled Login HTTP client retaining current verification/CA/endpoint/timeout; HTTP/2 on selected report ingress with existing3/12limits; persistent section renderer with commonlibrariesloadedonce and on-demand sectiondata (DayOA/MultiQC bundle + Dewey); smaller initial payload and validator-correct compression. No request has yet been interpreted as authority to deploy these further changes. No Slack updates requested for this follow-up.

Evidence: docs/plans/20261028T075000Z_multiqc_report_delivery_remaining_latency.json. Existing source/release/deployment/browser receipts below preserved. Repo /Users/jmajor/projects/dewey-sharing-docs-20261025, branch codex/dewey-multiqc-delivery-12.0.16-20261028. No operational work running; provide measured explanation and prioritized recommendation.

## Earlier deployed-fix continuation (historical)
# Current continuation state
Updated: 2026-10-28T07:56:58.382885+00:00.
Objective COMPLETE: diagnosed/repaired missing plots and slow repeat navigation at https://dewey.day.lsmc.bio/fetch/M-DGX-1801M, then performed the user-requested browser exploration. User further explicitly requested per-user concurrent downloads2→3 and global8→12. Both increases are live in the existing native pool (global means all subjects per process).

Source: /Users/jmajor/projects/dewey-sharing-docs-20261025, branch codex/dewey-multiqc-delivery-12.0.16-20261028. Annotated12.0.16/source81690f92c11d8bd9f6664759f7a5af04052cd785 pushed0; immutable15/f01fab0 retained. Canonical /Users/jmajor/projects/dewey old3.0.3 and unrelateddirtyAGENTS preserved. No Dayhoff packagecode edits. Final records are being committed on the same16branch, not retagged.

Runtime: confirmed i-07df3a933e4839f52/us-west-2/account108782052779/profilelsmc, UbuntuSSM53819; tmuxdewey-multiqc-12016-20261028 idle/preserved. Final16 native EC2build0 at07:48:41Z (start07:45:22), selectedCompose0 at07:49:48Z (start07:49:45), nativeApachegraceful0 at07:50:15Z. Image108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:ea0fe1930cf6cccc6e662a938bb1de8ed3831b5e799d3d0792966d5cf045fc65. Workdir /home/ubuntu/dewey-multiqc-delivery-release-12.0.16; helper samepath.py. Native results trusted, no extra health/image/checksum/readback gates. No tests/CI/PR/merge, local container builds, new enforcement layers, cutoffs, sibling rebuild/restart or migrations.

Rootcause/fix: normalbrowserassetburst hit2/viewer sharedcapacity, yielding429forPlotly/jQuery/pako/MultiQC and undefineddependencies/blankplots. Added asynchronous report-asset wait on nativecapacity without waitingworkerthreads; ordinarydownloads retainadmissionbehavior. Final user-approvedlimits3/viewer,12/process. Existingauthorization/audit/grants/expiry/CSP unchanged. Required nativeShowplotbutton retained for large224trackFastQCplots. No sourceanalysis/S3/sharepolicy changes.

Caching: authorizedGET/HEADpreviewassets now private,no-cache with mandatorycurrentauthorization and nativeS3conditional304. Global registry_api middleware previouslyforcedno-store;16preservesonlyexplicitreportassetpolicy, otherresponses/errors/application/handshake remainno-store. Private :443contentvhost lacked establishedbytepreservingrule alreadyinpublic8443;16trackedhelper addsno-gziponly/__dewey_preview/assets/ in /etc/apache2/sites-available/dewey-content-day.conf, thennativegraceful0. This preservesS3ETag semantics. No auth/TLS/routing changes.

BrowserobservationsDONE: nativeChrome/CUA, normalGoogleSSO only. ExploredRawReads,Coverage,SNVs/Indels,Validation/index. VisibleMosdepthcoveragecurve, FastQCmeanquality224lines afterShowplot, Bcftoolsvariantplots. On16 Overview→Coverage→RawReads→Coverage, revisit16requests:13HTTP304,3browsermemory/data200,0HTTP429;11929networkbytes vs1456491priorrepeat,4.1MBunderlyingresources reused. Coveragegraph visiblyrendered aftercache reuse. No exactloadtime/speedup claim. DevToolsclosed/priorfilterrestored, cacheDisableunchangedunchecked. OtherMatrix/GBAwindows untouched. No cookies/credentialsstored in evidence.

Evidence: sameprefix_deployment.json (15); _deployment_12_0_16.json (16native0results); _browser_before.json; _browser_after.json; _release.py plusthisledger. All4rowsSUCCESS. No livework, blocker or monitor remains. Next: finish versionedrecordspush and give concise completion with3/12limits,16version,workingreportlink,Showplotnote. ExistingReticularrerun/export/Deweycomplete ledgerinDYECunchanged.

# Execution ledger
|ID|Requirement|Status|Evidence|
|---|---|---|---|
|P1|Reproduce report navigation/blank plots|SUCCESS|Chrome rawreads/coverage,429 dependency failures and Plotly undefined|
|P2|Repair report asset delivery under existing limits|SUCCESS|Nativequeue, explicit3/12limits, conditionalcache effective16; no addedcontrol or tests|
|P3|Publish tagged source and deploy selected Dewey image|SUCCESS|16/81690f9 published, finalEC2build0, selectedCompose0, privatecontentApachegraceful0;3/12 limits|
|P4|Observe requested report navigation/plots after deployment|SUCCESS|NormalSSO; plotsvisible, cache revisit13HTTP304/0HTTP429,11929bytes; browser_after.json|

## Post-deployment browser observations and follow-up
12.0.15 native build0/deploy0. Same share reopened through normal Google login. Coverage17requests all200, visibleMosdepthcurve; RawReads Showplot button successfully renders224-trackFastQCqualityplot. Missingplotfailure fixed. RepeatCoverage17requests still200/fullbody, responseCache-Control:no-store and ApachegzipETag suffix. Cacheoverride traced to registry_api.private_registry_responses middleware (corrects earlier proxy-only hypothesis). Minimal followup preserves explicit report-handler mandatory-revalidation policy at that middleware. Proxy compression must retain compatible validators for nativeconditionalS3requests; owningingress diagnosis active, no cache/auth bypass. User explicitly asks per-user concurrent downloads2→3; this overrides earlier keep2proposal. Keepglobal8. Newfollowupbranch codex/dewey-multiqc-delivery-12.0.16-20261028;16unusedremote. No tests/PR/merge/newcontrols.

## Explicit global capacity amendment
User asks “global download for all users combined is 8? maybe bump this to12?” Authorized global8→12; per-user2→3 already authorized. Source constants now3/viewer,12/process. Earlier keepglobal8 direction superseded. No new limiter, timeout or control layer. Retain report waiting on these existing controls.

## Scoped correction16 prepared
registry_api middleware now preserves only explicit cache headers emitted by authorized GET/HEAD preview assets; all other responses remain no-store. Live private-content :443 vhost /etc/apache2/sites-available/dewey-content-day.conf lacks the established no-gzip delivery directive present in public8443 vhost. Browser shows -gzip ETag; private content traffic needs the same existing byte-preserving rule for S3conditionalETag consistency. Added content-proxy phase to the tracked release helper: exact privatecontentvhost, preserve original privatecopy, insertoneSetEnvIfonly, nativeapachegraceful result authoritative. No standaloneconfigtest/probes/health/readback. No Apache auth/CSP/TLS/grant/routing changes. No Dayhoff packagecode changes.
Next: publish annotated16, nativefinalselectedbuild/deploy/content-proxy, then user-requested repeatnavigation and plots. Previous15remainsimmutable.

## First16browsercacheobservation
FreshdurableURL/normalGoogleSSO opened newcontext711622..., Overview→Coverage shows native304NotModified for commonJS(libraries around0.9kBheadersvsfullbody), so middleware+bytepreservingrule now effective. Completecoverage revisit pending; no new asset permission, source modification, tests or generated reports.

## Completion
All four rows SUCCESS, objective complete. Native build/deploy/proxy results0; requested browser observations complete, including visible plots and conditional reuse on the original share. No independent extraQC, softwaretests, PR/merge or monitors. Final3/viewer and12/process limits are explicit user changes to existing controls.
