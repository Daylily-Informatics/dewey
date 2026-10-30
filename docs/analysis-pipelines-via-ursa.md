# Analysis pipelines through Ursa

The [versioned Ursa API guide](https://github.com/lsmc-bio/daylily-ursa/blob/14.1.104/docs/analysis-pipelines-via-ursa.md) documents all eleven production catalog commands, exact policy-mode submissions, idempotent replay, job/execution monitoring, failure evidence, full-root S3 results, Dewey registration and native cleanup. Its release contract is Ursa14.1.104 / DYEC22.0.1 / DayOA20.0.0; actual deployment and catalog publication are separate facts.

Dewey owns input artifacts, their storage/provenance and registered result prefixes. Ursa verifies exact input bindings and registers exported results with typed external references and lineage. A successful Ursa terminal receipt includes the Dewey result-prefix identity; do not add S3 readbacks as a second acceptance gate. Workflow success and clinical acceptance remain separate.

This release also includes [token governance](token-administration.md). Shared Login/Cognito configuration is unchanged: Dewey may request up to365days, but effective lifetime remains bounded by the currently deployed issuer/provider grant. This release alone does not establish365-day credentials.
