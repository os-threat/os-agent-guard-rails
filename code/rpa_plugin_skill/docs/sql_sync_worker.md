# SQL sync worker (issue #58)

`sql_sync_worker.py` executes generated SQL and materializes rows into a named Layer A database using TypeQL `put` statements in a `write` transaction.

## Flow

1. Resolve `registration_id` -> Layer A database name.
2. Execute SQL query against source Postgres (`psycopg`).
3. Map each row to TypeQL attributes using the SQL table namespace:
   - entity: `gra_<table>`
   - attributes: `gra_<table>_<column>`
4. Write to TypeDB with `put` so keyed entities are upserted.

## Idempotency and watermark strategy

- **Idempotency default:** use `put` plus SQL-transpiled `@key` attributes (`id` style keys) so re-syncing the same row does not duplicate entities.
- **Required key column:** `SqlSyncPlan.key_column` must be present and non-null in every synced row; sync fails fast otherwise.
- **Watermark option:** supply `watermark_column` + `watermark_gt` in `SqlSyncPlan` to only fetch incremental rows.
  - Worker wraps source SQL as a subquery and applies:
    - `WHERE <watermark_column> > <watermark_gt>`
    - `ORDER BY <watermark_column> ASC`
  - `SqlSyncResult.watermark_max` returns the last processed watermark for next runs.

## Integration test coverage

`tests/test_sql_sync_worker.py` validates:

- target is the correct named Layer A DB
- Postgres -> TypeDB write path works end-to-end
- repeated runs stay idempotent for keyed entities (single entity remains)
