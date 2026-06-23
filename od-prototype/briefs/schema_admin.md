# OpenDesign Brief — Schema Admin

Feature: Schema version and migration visibility

Primary user: admin / curator

Screens:

1. Schema versions list
2. Schema version detail
3. Migration impact preview
4. Import/backfill job status

Must show:

- current schema_version
- source data release
- affected entities
- DB/API/frontend propagation status
- rollback notes

RBAC:

- admin: publish schema
- curator: propose schema change
- reviewer/reader: read-only or forbidden
