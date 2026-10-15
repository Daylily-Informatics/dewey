# Dewey native graph performance release

Controlling ledger: sibling Kahlo docs/plans/20261015T075127Z_seqnas_performance_annotations_ledger.md. User prioritizes Dewey/Kahlo graphs and SeqNAS responsiveness, Ursa <=4s; QEO optimization excluded.

Pin TapDB11.0.7/b04257f551442bf2aa9074e9103720a89574f073 and matching runtime package contract. Native graph uses bounded adjacency, retained payload hydration, synchronous DB routes in worker threads, and explicit cycle-closing foreign boundaries. Native schema apply changes only the domain/owner read-policy query plan for instance/lineage; tenant and write authority remain unchanged. No permission expansion or graph cache. Existing11.0.4 managed human uploads are preserved.

Build only the final11.0.5 image on EC2i-07df3a933e4839f52. Apply packaged schema through the native TapDB lifecycle to the exact existing Dewey database; deploy selected Dewey container, retaining other service identities. Read-only timing and human GUI observations remain pending. Tests/lint/coverage not run; no PR or merge.
