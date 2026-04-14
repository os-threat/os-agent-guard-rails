# Correlation trace for deny/appeal flow (issue #64)

This extends Promise MCP to correlate Guard actions and Layer B assessments with optional Layer A references.

## Correlation model

- `correlation_id` is accepted on `promise.assess`.
- On deny outcomes, service records:
  - assessment row with `grb_correlation_id`
  - action row (`guard_deny`) linked to promise
  - data-trace row with:
    - `grb_rule_id`
    - `grb_schema_hash`
    - `grb_sync_watermark`
    - `grb_correlation_id`
    - optional `grb_layer_a_ref`

## Cross-layer linkage (C/B/A)

- **Layer B** stores assessment/action/data-trace objects.
- **Layer C** stores dashboard lookup keys:
  - `dashboard:<correlation_id>:promise_id`
  - `dashboard:<correlation_id>:assessment_id`
  - `dashboard:<correlation_id>:layer_a_ref` (optional)
- **Layer A** reference is carried as a string pointer (`layer_a_ref`) to specific domain row context.

## Dashboard trace query

`promise.query` supports `{ "correlation_id": "..." }` and returns:

- `dashboard_row_id`
- `promise_id`
- `assessment_id`
- `assessment_outcome`
- `layer_a_ref` (optional)

This provides direct trace from dashboard row to assessments and optional Layer A references.
