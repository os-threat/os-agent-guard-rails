# OS-Agent RPA Guard Rails — OpenClaw plugin / skill

Implementation will live here per [`a_seed/os-agent-guard-rails-overview.md`](../../a_seed/os-agent-guard-rails-overview.md). The canonical implementation plan is [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md).

## Package skeleton (issues #41, #42)

This folder now contains a minimal Python package that can start with environment config, probe TypeDB health, and bootstrap named databases on a single TypeDB instance.

### Package layout

```text
code/rpa_plugin_skill/
  .env.example
  .gitignore
  package.json                # npm-style scripts for dev/health/test/lint/format
  pyproject.toml              # Ruff baseline
  requirements.txt            # typedb-driver + ruff
  rpa_plugin_skill/
    __main__.py
    cli/main.py
    core/config.py
    core/health.py
    core/typedb_bootstrap.py
  tests/test_config.py
  dev/docker-compose.yml
  typeql_ci/
```

## Local development — TypeDB (single instance)

The plugin uses **one TypeDB server instance** (one host/port). On that instance you create **multiple named databases**:

| Database | Role |
|----------|------|
| **Layer C** | Plugin/skill UI state (registrations, rules metadata, tasks, settings) |
| **Layer B** | Promise graph (`17-promise-graphs.md` model) |
| **Layer A** (one per app) | Shadow domain for each registered SQL or OpenAPI source |

Normative **TypeQL** for TypeDB **3.8+** is in [`skills/typedb/SKILL.md`](../../skills/typedb/SKILL.md) (transaction types, `define` / `redefine`, semicolon-terminated queries, entity/relation/attribute roots, `@key`, etc.).

### Prerequisites

- **Docker Desktop** on Windows (Linux containers), or Docker Engine on Linux/macOS  
- Optional: **WSL 2** on Windows if you prefer a Linux shell for `docker compose` and scripts; Docker Desktop integrates with WSL2

### Start TypeDB

From this package’s `dev` folder:

```bash
cd code/rpa_plugin_skill/dev
docker compose up -d
docker compose ps
```

- **Driver gRPC** (default for clients): `localhost:1729` — set e.g. `TYPEDB_ADDRESS=localhost:1729` in plugin config.  
- Port **8000** is also exposed by the official image (see [TypeDB CE install — Docker](https://typedb.com/docs/home/install/ce/)).

### Health check

With the container running:

```bash
docker compose logs typedb --tail 20
```

And from `code/rpa_plugin_skill`:

```bash
pip install -r requirements.txt
npm run health
```

### Skeleton scripts (`package.json`)

From `code/rpa_plugin_skill`:

```bash
pip install -r requirements.txt
npm run dev      # python -m rpa_plugin_skill --bootstrap
npm run health   # python -m rpa_plugin_skill --health
npm run test     # unittest
npm run lint     # ruff check
npm run format   # ruff format
```

`npm run dev` reads env vars and can create missing named DBs (`Layer C`, `Layer B`, `Layer A test`) on the configured TypeDB instance.

### Connection settings (`.env.example`)

- `TYPEDB_ADDRESS` (default `127.0.0.1:1729`)
- `TYPEDB_USER` (default `admin`)
- `TYPEDB_PASSWORD` (default `password`)
- `TYPEDB_TLS_ENABLED` (default `false`)
- `TYPEDB_CONNECT_RETRIES` (default `5`)
- `TYPEDB_CONNECT_RETRY_DELAY_SEC` (default `1.0`)

### Stop / reset

```bash
docker compose down
docker compose down -v
```

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

Environment variables (optional): `TYPEDB_ADDRESS`, `TYPEDB_USER`, `TYPEDB_PASSWORD`.

**CI:** workflow [`.github/workflows/typeql-ci.yml`](../../.github/workflows/typeql-ci.yml) runs the same script against `typedb/typedb:3.8.3`.

## GitHub tracking

| Epic | Issue |
|------|--------|
| **0.1** Local dev stack | [#39](https://github.com/os-threat/os-agent-guard-rails/issues/39) (closed) |
| **0.2** CI TypeQL validation | [#40](https://github.com/os-threat/os-agent-guard-rails/issues/40) (closed) |
| **0.3** package skeleton | [#41](https://github.com/os-threat/os-agent-guard-rails/issues/41) (closed) |
| **1.1** TypeDB connection configuration | [#42](https://github.com/os-threat/os-agent-guard-rails/issues/42) |
