# Layer C schema migrations

`schema/layer_c` contains versioned TypeQL schema changes for the **Layer C** database.

## Versioning approach

- Migrations are defined in `manifest.json` and applied in listed order.
- Each migration has:
  - `id`
  - `file`
  - `marker_label` (a schema label that proves migration is already present)
- The runner checks current Layer C schema and skips migrations whose marker already exists.

This approach is deterministic and idempotent for additive schema changes in this phase.

## Apply migrations

From `code/rpa_plugin_skill`:

```bash
python -m scripts.migrate_layer_c
```

Or via npm script:

```bash
npm run layerc:migrate
```

The runner ensures core databases exist (Layer C and Layer B) before applying Layer C schema changes.

## TypeQL requirements

All migration files must follow `skills/typedb/SKILL.md`:

- semicolon-terminated statements
- schema changes in `schema` transactions
- valid TypeDB 3.x roots (`entity`, `relation`, `attribute`)

