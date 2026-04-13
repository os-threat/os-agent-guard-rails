# OS-Agent RPA Guard Rails — OpenClaw plugin / skill

Implementation will live here per [`a_seed/os-agent-guard-rails-overview.md`](../../a_seed/os-agent-guard-rails-overview.md). The canonical implementation plan is [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md).

## Package skeleton (issues #41–#44)

This folder contains a minimal Python package that can start with environment config, probe TypeDB health, manage deterministic Layer A database names for source registrations, and apply Layer C schema migrations.

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
  schema/layer_c/
    manifest.json
    MIGRATIONS.md
    v1/001_define_layer_c.tql
  scripts/migrate_layer_c.py
  tests/test_config.py
  tests/test_database_lifecycle.py
  tests/test_layer_c_migrations.py
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

## Layer C schema migrations

Layer C schema is versioned under [`schema/layer_c/`](schema/layer_c/):

- `manifest.json` defines ordered migrations + marker labels
- `v1/001_define_layer_c.tql` defines source/rule/task/schedule/settings entities and relations
- `scripts/migrate_layer_c.py` applies missing migrations in **schema transactions**

Details: [`schema/layer_c/MIGRATIONS.md`](schema/layer_c/MIGRATIONS.md).

## Prerequisites

- **Docker Desktop** on Windows (Linux containers), or Docker Engine on Linux/macOS  
- Optional: **WSL 2** on Windows if you prefer a Linux shell for `docker compose` and scripts; Docker Desktop integrates with WSL2

## Start TypeDB

From this package’s `dev` folder:

```bash
cd code/rpa_plugin_skill/dev
docker compose up -d
docker compose ps
```

- **Driver gRPC**: `localhost:1729` (set `TYPEDB_ADDRESS` accordingly)
- Port **8000** is also exposed by the official image (see [TypeDB CE install — Docker](https://typedb.com/docs/home/install/ce/)).

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
| **2.1** Layer C schema | [#44](https://github.com/os-threat/os-agent-guard-rails/issues/44) |
