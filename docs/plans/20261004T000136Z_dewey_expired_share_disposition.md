# Proposed disposition of expired Dewey shares

Status: pending explicit user disposition. No production mutation has occurred.

The approved implementation plan requires ambiguous records to block conversion. The final native inventory found the following 22 expired records. The proposed disposition preserves their EUIDs, URLs, existing payloads, recipient evidence, lineage and audit as non-serving history. It grants no access, reconstructs no missing membership and does not revive or delete a share. Manager access to historical evidence would still require Tailscale and sign-in.

The active set share `M-DGX-K2PP` is excluded from this proposal. Complete native evidence established its two current members; the reviewed converter can now preserve that share without a separate disposition.

Current inventory SHA256: `394a18a5ca47bcffe44bb4f402ecdd3d7630019d1d884485b2565703632aca1d`. Private inventory: `/home/ubuntu/dewey-sharing-20261004T000136Z/disposition-inventory-v3.json`. Before any apply, refresh native inventory and verify exact identity, revisions and policy evidence.

| Share | Stored status | Expiration (UTC) | Conversion blocker |
|---|---|---|---|
| M-DGX-9YHS | unset | 2026-06-03T10:55:12.137999+00:00 | Historical set conversion requires exactly one active has_share set parent |
| M-DGX-9YKN | unset | 2026-06-03T10:55:12.300264+00:00 | Historical set conversion requires exactly one active has_share set parent |
| M-DGX-A1PA | active | 2026-06-09T18:38:40.527846+00:00 | Historical set conversion requires exactly one active has_share set parent |
| M-DGX-K3NQ | revoked | 2026-07-14T22:44:33.943450+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K3QK | revoked | 2026-07-14T22:44:34.037574+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K3SF | revoked | 2026-07-14T22:44:34.109573+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K3VB | revoked | 2026-07-14T22:44:34.179936+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K3Z3 | revoked | 2026-07-14T23:06:31.862298+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K41Z | revoked | 2026-07-14T23:06:31.961582+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K43V | revoked | 2026-07-14T23:06:32.033277+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K45Q | revoked | 2026-07-14T23:06:32.101637+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K47K | revoked | 2026-07-14T23:16:00.682508+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K49F | revoked | 2026-07-14T23:16:00.779559+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K4BB | revoked | 2026-07-14T23:16:00.853926+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K4D7 | revoked | 2026-07-14T23:16:00.937454+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K8ZY | active | 2026-07-18T15:26:40.734667+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-K91T | active | 2026-07-18T15:26:41.014693+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-M61V | active | 2026-07-18T21:13:45.608592+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-M63Q | active | 2026-07-18T21:13:45.836191+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-MDQ7 | active | 2026-07-19T14:59:11.577443+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-MDWX | active | 2026-07-31T21:30:59.250742+00:00 | CloudFront or unknown delivery needs explicit disposition |
| M-DGX-ME1K | active | 2026-07-31T21:31:00.129877+00:00 | CloudFront or unknown delivery needs explicit disposition |

Alternative: require an individually supplied repair/disposition for each row and keep deployment blocked. No permissions or targets will be inferred from metadata.

The requested disposition scope remains the same exact 22 identities across the evidence revisions. Native record revisions and payload hashes are in `evidence/20261004_sharing/proposed_expired_disposition.json`; that artifact is a pending proposal, not approval.
