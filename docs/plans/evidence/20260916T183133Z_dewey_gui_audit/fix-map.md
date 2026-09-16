# Frozen bugfix mapping

## D01

Deployment operator updates only exact Dewey image and source SHA/branch environment fields. Post-deploy GUI verification pending.

## D02

Keep set member query and serialization in the authorization session; capture the persisted receipt EUID before commit expires the ORM instance. APIs, lineage, and permissions are unchanged.

## D04

Field and textarea helpers assign unique DOM IDs; API form names remain unchanged. Prevents background/modal label collisions.

## D05

Dewey globally forced Referrer-Policy no-referrer, which gives native POST navigations Origin null under Fetch. Default same-origin now preserves a same-site form Origin and suppresses cross-site referrers; explicit preview no-referrer is retained. Origin enforcement remains intact. Inference from reproduced form rejection, actual form action, deployed header, source, and https://fetch.spec.whatwg.org/#append-a-request-origin-header; verify after deploy.

## D06

Registry pages now carry their exact path/query into the existing /login?next= flow.

Validation: source diff/manual review only before deployment. GUI iteration2 provides runtime evidence. No data migration, API change, dependency release, PR or merge.
