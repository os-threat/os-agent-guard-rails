# Layer B schema migrations

`schema/layer_b` contains versioned TypeQL schema changes for the **Layer B** Promise Graph subset.

## Versioning approach

- Migrations are declared in `manifest.json` and applied in listed order.
- Each migration has:
  - `id`
  - `file`
  - `marker_label` (label existence means the migration is already present)
- The runner loads current Layer B schema and skips already-present markers.

This is deterministic and idempotent for additive schema migrations in this stage.

## Mapping table (PLAN §3)

- **OpenClaw agent** -> `grb_agent`
- **Guard check event** -> `grb_action`
- **Guard check trace payload** (`rule id`, `schema hash`, `sync watermark`) -> `grb_data_trace`
- Link guard check to trace -> relation `grb_action_data_trace_binding`

## Apply migrations

From `code/rpa_plugin_skill`:

```bash
python -m scripts.migrate_layer_b
```

Or via npm script:

```bash
npm run layerb:migrate
```

The runner ensures core databases exist before applying Layer B schema changes.

## TypeQL requirements

All migration files follow `skills/typedb/SKILL.md`:

- semicolon-terminated statements
- schema changes in `schema` transactions
- valid TypeDB 3.x roots (`entity`, `relation`, `attribute`)
