# OS-Agent RPA Guard Rails — OpenClaw plugin / skill

Implementation will live here per [`a_seed/os-agent-guard-rails-overview.md`](../../a_seed/os-agent-guard-rails-overview.md). The canonical implementation plan is [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md).

## Package skeleton (issues #41–#46)

This folder contains a minimal Python package that can start with environment config, probe TypeDB health, manage deterministic Layer A database names for source registrations, and apply Layer C and Layer B schema migrations.

### Package layout

```text
code/rpa_plugin_skill/
  .env.example
  .gitignore
  package.json                # npm-style scripts for dev/health/db/migrate/test/lint/format
  pyproject.toml              # Ruff baseline
  requirements.txt            # typedb-driver + ruff
  rpa_plugin_skill/
    __main__.py
    cli/main.py
    core/config.py
    core/health.py
    core/database_lifecycle.py
    core/typedb_bootstrap.py
    core/layer_c_migrations.py
    core/layer_b_migrations.py
    core/layer_c_store.py
  schema/layer_c/
    manifest.json
    MIGRATIONS.md
    v1/001_define_layer_c.tql
  schema/layer_b/
    manifest.json
    MIGRATIONS.md
    v1/001_define_layer_b.tql
  scripts/migrate_layer_c.py
  scripts/migrate_layer_b.py
  tests/test_config.py
  tests/test_database_lifecycle.py
  tests/test_layer_c_migrations.py
  tests/test_layer_b_migrations.py
  tests/test_layer_c_store.py
  dev/docker-compose.yml
  typeql_ci/
```

## Single TypeDB instance model

The plugin uses **one TypeDB server instance** (one host/port). On that instance you create **multiple named databases**:

| Database | Role |
|----------|------|
| **Layer C** | Plugin/skill UI state (registrations, rules metadata, tasks, settings) |
| **Layer B** | Promise graph (`17-promise-graphs.md` model) |
| **Layer A** (one per app) | Shadow domain for each registered SQL or OpenAPI source |

Normative **TypeQL** for TypeDB **3.8+** is in [`skills/typedb/SKILL.md`](../../skills/typedb/SKILL.md) (transaction types, `define` / `redefine`, semicolon-terminated queries, entity/relation/attribute roots, `@key`, etc.).

## Layer B mapping (PLAN §3)

- **OpenClaw agent** -> `grb_agent`
- **Guard check** -> `grb_action`
- **Guard data trace** (`rule id`, `schema hash`, `sync watermark`) -> `grb_data_trace`
- Link action to trace -> `grb_action_data_trace_binding`

## Deterministic Layer A naming and lifecycle

Registration id -> Layer A database mapping is deterministic:

- Sanitize id to safe chars (`a-z`, `0-9`, `_`, `-`) and collapse separators
- Append an 8-char SHA1 suffix for collision resistance
- Enforce `MAX_DATABASE_NAME_LENGTH` (default `64`) with safe trimming

Example shape: `guardrails_layer_a_{sanitized}_{hash8}`

### Lifecycle operations (v1)

- **Bootstrap core:** create Layer C and Layer B once
- **Register source:** create/get mapped Layer A DB for source id
- **List:** list databases on configured instance
- **Archive source:** in v1, archive is implemented as delete of the mapped Layer A DB

## Layer C and Layer B schema migrations

Schema migrations are versioned under [`schema/layer_c/`](schema/layer_c/) and [`schema/layer_b/`](schema/layer_b/):

- `manifest.json` defines ordered migrations + marker labels
- `v1/001_define_layer_c.tql` defines source/rule/task/schedule/settings schema
- `v1/001_define_layer_b.tql` defines promise-graph subset schema
- migration scripts apply missing migrations in **schema transactions**

Details:

- [`schema/layer_c/MIGRATIONS.md`](schema/layer_c/MIGRATIONS.md)
- [`schema/layer_b/MIGRATIONS.md`](schema/layer_b/MIGRATIONS.md)

## Scripts (`package.json`)

From `code/rpa_plugin_skill`:

```bash
pip install -r requirements.txt
npm run dev                 # bootstrap Layer C/B
npm run health              # TypeDB health probe
npm run db:list             # list DBs
npm run db:register:example # create/get Layer A DB mapping
npm run db:archive:example  # archive/delete mapped Layer A DB
npm run layerc:migrate      # apply pending Layer C schema migrations
npm run layerb:migrate      # apply pending Layer B schema migrations
npm run test                # unittest
npm run lint                # ruff check
npm run format              # ruff format
```

## Connection settings (`.env.example`)

- `TYPEDB_ADDRESS` (default `127.0.0.1:1729`)
- `TYPEDB_USER` (default `admin`)
- `TYPEDB_PASSWORD` (default `password`)
- `TYPEDB_TLS_ENABLED` (default `false`)
- `TYPEDB_CONNECT_RETRIES` (default `5`)
- `TYPEDB_CONNECT_RETRY_DELAY_SEC` (default `1.0`)
- `LAYER_A_PREFIX` (default `guardrails_layer_a_`)
- `MAX_DATABASE_NAME_LENGTH` (default `64`)

## Limits and constraints (v1)

- **Single instance target only** for this phase (`TYPEDB_ADDRESS`)
- **Name charset** enforced by sanitizer for registration ids
- **Collision handling** uses deterministic hash suffix
- **Max database length** enforced by trimming + hash preservation

## TypeQL CI (local and GitHub Actions)

Hand-written and generated TypeQL must match a live **TypeDB 3.8+** server and the rules in [`skills/typedb/SKILL.md`](../../skills/typedb/SKILL.md). The script [`typeql_ci/validate_typeql.py`](typeql_ci/validate_typeql.py) applies **passing** schema/write fixtures and ensures **failing** fixtures are rejected.

**Locally** (start TypeDB first — see above):

```bash
cd code/rpa_plugin_skill/typeql_ci
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python validate_typeql.py
```

**CI:** workflow [`.github/workflows/typeql-ci.yml`](../../.github/workflows/typeql-ci.yml) runs the same script against `typedb/typedb:3.8.3`.

## GitHub tracking

| Epic | Issue |
|------|--------|
| **0.1** Local dev stack | [#39](https://github.com/os-threat/os-agent-guard-rails/issues/39) (closed) |
| **0.2** CI TypeQL validation | [#40](https://github.com/os-threat/os-agent-guard-rails/issues/40) (closed) |
| **0.3** package skeleton | [#41](https://github.com/os-threat/os-agent-guard-rails/issues/41) (closed) |
| **1.1** TypeDB connection configuration | [#42](https://github.com/os-threat/os-agent-guard-rails/issues/42) (closed) |
| **1.2** logical database lifecycle | [#43](https://github.com/os-threat/os-agent-guard-rails/issues/43) (closed) |
| **2.1** Layer C schema | [#44](https://github.com/os-threat/os-agent-guard-rails/issues/44) (closed) |
| **2.2** Layer C API layer | [#45](https://github.com/os-threat/os-agent-guard-rails/issues/45) (closed) |
| **3.1** Layer B schema subset | [#46](https://github.com/os-threat/os-agent-guard-rails/issues/46) (closed) |
| **3.2** Layer B seed/query tests | [#47](https://github.com/os-threat/os-agent-guard-rails/issues/47) (closed) |
| **4.1** SQL DDL ingestion | [#48](https://github.com/os-threat/os-agent-guard-rails/issues/48) (closed) |
| **4.2** SQL -> TypeQL schema transpiler | [#49](https://github.com/os-threat/os-agent-guard-rails/issues/49) |


