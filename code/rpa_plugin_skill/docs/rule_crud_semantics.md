# Rule CRUD semantics (issue #54)

Rules are represented in two places:

1. Layer C metadata (`gr_rule_definition` + source binding)
2. Layer A schema logic (TypeQL query text stored as `gr_rule_typeql_fun`)

## Update semantics

- **Rule metadata update**: use `upsert_rule_for_source(...)`
  - updates Layer C metadata fields via `put`
  - optionally applies TypeQL schema query to the source-specific Layer A DB
- **Rule status transition**: `archive_rule_for_source(...)`
  - tombstone behavior in Layer C (`rule_status = archived`)
  - no schema removal by default

## Delete semantics

- **Soft delete (recommended default)**: archive/tombstone only
  - preserves auditability and replay context
- **Hard delete**: `delete_rule_for_source(...)`
  - removes Layer C binding + `gr_rule_definition` entity
  - can optionally remove Layer A logic with `undefine_query`

This split keeps replay-safe history while allowing explicit schema cleanup when needed.
