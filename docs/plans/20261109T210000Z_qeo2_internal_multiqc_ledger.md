# QEO2 scoped internal MultiQC source capability

## Current continuation state

Status: Dewey12.0.31 / 58473c0a07110c05bcdd2ff037f0ff16a4460966 deployed, native Compose Healthy. Image sha256:29713f5404aaf0c15cd67e36f07bc5fecd92106e3dbda47749d7aa01b1796073. Both environment list forms failed in separate settings layers; final root list is in native mounted YAML /home/ubuntu/dewey-qeo2-source-12.0.31/dewey-config.yaml, preserving prior config/mode and changing only QEO roots. Dedicated credential issued successfully and retained. Real source call now reaches application and returns403 Trusted Tailscale ingress required; no source records imported. Existing private management gateway10.0.0.222:8444 identified from owning Apache config. QEO2 2.0.15 config/client explicitly selects it with canonical Host and TLS validation, final EC2 build running. No proxy/auth changes. Repo /Users/jmajor/projects/dewey-registration-pool-20261108; branch codex/qeo2-internal-multiqc-20261109; EC2 i-07df3a933e4839f52 us-west-2, interactive ubuntu session76985. Next: QEO2-only deploy and exact17 source jobs, then documentation receipts. No tests/CI/PR/merge.

User authority: explicitly answered “Add scoped QEO2 service support” to the 403 service-account sharing restriction. Scope: one new QEO2 credential/endpoint for MultiQC report registration and internal webshare creation. This supersedes the earlier QEO2-only deployment boundary only for this Dewey capability. No purge, broad service API grant, human impersonation, global sharing-policy relaxation, recipients emails, or source search. Existing resolver credential remains read-only.

Endpoint POST /api/v1/qeo/report-source requires its own hash/expiry credential, native trusted-tailnet ingress, and a source in configured production roots. It establishes a real READ_WRITE service principal. Native MultiQC registration/lineage is required. A request-local exact report scope allows share delegation only for nonrestricted internal-download policy; protected target/ancestor controls remain in native record_clause. Existing single-report webshare lookup uses current revision lineage. Generic routes cannot obtain this scope. Human verified-email requirement remains unchanged outside this operation.

New webshares have exact lsmc.com and lsmc.bio domain recipients, native service lifetime14 days, no user emails. Existing eligible webshare reused; revoked/expired native idempotency is not automatically revived. All writes retain native service attribution and share events. New credential cannot become a generic registry token even if misconfigured in api_tokens.

Next: consume native build result /home/ubuntu/dewey-qeo2-source-12.0.30.result, issue credential via new native dewey qeo source-credential-create, deploy Dewey-only Compose. Then QEO2 2.0.14 build/deploy and 17 source revisions tracked in /Users/jmajor/Documents/ChatGPT/QEO/docs/plans/20261109T061500Z_qeo_requirements_extraction_ledger.md. Trust native results; no secondary probes.

## Gate 0

Native container inventory: dayhoff-day-dewey-1 release12.0.29 revision886b5cdeb70bb3e1769c51d43c8463fa59885f8c; image108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:2b24a82aa35c5351d04a12875eb738b4f18553ab29cd5eca563dee9316544297. Ordinary service-token GET of a known source share returned403: managed sharing requires verified ingress/current verified-email identity. No writes attempted through that rejected path. Source environment activated successfully. Source review only, no tests or compilation.

```mermaid
flowchart LR
  QEO[QEO2 scoped credential] --> Gate[Exact endpoint + trusted ingress + configured S3 roots]
  Gate --> Actor[Real QEO2 service principal]
  Actor --> Artifact[Native MultiQC registration]
  Artifact --> Scope[Exact report target scope]
  Scope --> Policy[Existing protected record and ancestor policy]
  Policy --> Share[Native internal webshare + audit]
  Share --> Receipt[Persisted artifact/share EUIDs and canonical URL]
```

## Native operation receipts / correction

12.0.30 native build exit0 (22:15:47–22:18:48Z), image sha256:6038f5aca90094bb0b2b681cbd718bdac7132f5263126861143c0869ddf8b698. Compose Healthy/exit0 at22:20:04Z. First real import exposed startup failure; native status was trusted until that failure. No additional success gate was added. Credential helper first needed the image application user, then explicit DEWEY_DEPLOYMENT_CODE=day; native credential issuance and private docker cp succeeded. Deployment uses targeted sudo for protected Compose/manifest files. Existing credential retained for12.0.31; no extra credential issuance.

12.0.31 / 58473c0a07110c05bcdd2ff037f0ff16a4460966 native EC2 build exit0, 22:21:33–22:24:05Z. Image sha256:29713f5404aaf0c15cd67e36f07bc5fecd92106e3dbda47749d7aa01b1796073. Native12.0.30 credential receipt copied into12.0.31 workdir for deployment; credential remains unchanged.

12.0.31 deployed exit0 at22:24:39Z; initial environment-form setting caused EnvSettingsSource parse failure. Corrected configuration to native YAML list, removed environment override, recreated Dewey-only; Compose Healthy. First real request then403 ingress, triggering QEO2 transport correction instead of weakening sharing controls.

##12.0.32 source response correction

Private management ingress succeeded. First native operation took172.476seconds and returned400 because the new endpoint passed the compact artifact response into saved_bundle; that API deliberately omits report_bundle. Native registration succeeded, but no QEO revision was written. Reissuing the same native idempotent request returned the exact error quickly. Move the required MultiQC type/bundle check into the already-required record policy query using its full payload. No extra readback or generic API behavior change. QEO2 removes its prematurely shorter120-second client timeout and waits for the owning service result. Native source policy remains unchanged.
