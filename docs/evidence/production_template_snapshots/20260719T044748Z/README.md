# Production Template Snapshot: Dewey

This directory is a read-only evidence log of every Dewey production
`generic_template` row captured from `dewey.day.lsmc.bio`, including rows
where `is_deleted=true`.

- Captured: `2026-07-19T04:47:48Z`
- Records: 22 active, 0 deleted, 22 total
- Canonical records SHA-256: `69ed2438ea654e973519cdba59f0624bc332339ff5b7705cfc307595bc460f97`
- Access: explicit Dewey TapDB config through a rollback-only runtime session

`generic_templates.json` is not an active template pack and must not be
seeded. A later review must reconcile it with
`config/tapdb_templates/dewey/templates.json` before any packaged-template
change.
