# OS-Agent RPA Guard Rails — OpenClaw plugin / skill

Implementation will live here per [`a_seed/os-agent-guard-rails-overview.md`](../../a_seed/os-agent-guard-rails-overview.md). The canonical implementation plan is [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md).

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

- **Driver gRPC** (default for clients): `localhost:1729` — set e.g. `TYPEDB_ADDRESS=localhost:1729` in plugin config when implemented.  
- Port **8000** is also exposed by the official image (see [TypeDB CE install — Docker](https://typedb.com/docs/home/install/ce/)).

### Health check

With the container running:

```bash
docker compose logs typedb --tail 20
```

You should see the server listening; use your TypeDB client or Studio to open `localhost:1729` when you add connectivity tests.

### Stop / reset

```bash
docker compose down
```

To remove persisted data as well:

```bash
docker compose down -v
```

### Integration testing (later)

Full-stack integration tests are planned to use this (or CI) compose plus optional Postgres/API fixtures; see [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md) §6 (testing approach).

## GitHub tracking

Epic **0.1** (local dev stack): [issue #39](https://github.com/os-threat/os-agent-guard-rails/issues/39).
