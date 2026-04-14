# REST sync worker (issue #59)

`rest_sync_worker.py` executes OpenAPI extract bundles and writes response rows into the
registration's Layer A database with TypeQL `put` in `write` transactions.

## Flow

1. Resolve `registration_id` -> named Layer A DB.
2. Execute REST call for the extract bundle path/method.
3. Extract row payload from:
   - explicit `response_records_key`, or
   - fallback keys `data`, `items`, `results`, or
   - root array payload.
4. Map each row into target entity attributes:
   - entity: configured `target_entity` (example `gra_client`)
   - attributes: `<entity>_<field>` (example `gra_client_id`, `gra_client_name`)
5. Write with TypeQL `put` for idempotent upserts.

## Pagination and rate limits

Supported pagination mode:

- `none` - single request
- `next_link` - follows `next` link in response object (absolute or relative URL)

Controls:

- `max_pages` prevents unbounded crawl loops.
- `rate_limit_sleep_ms` inserts sleep between paged requests to respect source API limits.

Example:

- mode: `next_link`
- max pages: `5`
- sleep: `250ms`

## Idempotency

- Enforce non-null `key_field` for each row.
- Use `put` so replaying previously fetched rows does not create duplicates when keys match.
