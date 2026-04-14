# Sync triggers and UI status (issue #60)

This stage connects sync workers to lifecycle hooks and exposes sync state via Layer C for UI display.

## Trigger points

- **Post registration** (`sql` / `api`)
  - Called after registration completes.
  - Records trigger + timestamp in Layer C.
- **Post task finalize**
  - Called when a task definition is finalized.
  - Records trigger + timestamp for that task context.
- **Manual refresh**
  - SQL manual sync and REST manual sync both record trigger, rows, time, and error.

## Layer C status keys

Per registration id, keys are stored as:

- `sync:<registration_id>:last_sync_time`
- `sync:<registration_id>:last_sync_error`
- `sync:<registration_id>:last_sync_rows`
- `sync:<registration_id>:last_sync_trigger`

These keys are intended for UI status badges and inspector views.

## Visibility requirement: last sync time/error

CLI exposes status directly:

```bash
python -m rpa_plugin_skill --sync-status-source sql-medical-alpha
```

Output includes:

- `last_time`
- `last_error`
- `last_rows`
- `last_trigger`

This satisfies the "last sync time / error visible" acceptance criterion and mirrors what the iframe UI should render from Layer C state.
