# OS-Agent RPA Guard Rails — OpenClaw plugin / skill

Implementation will live here per [`a_seed/os-agent-guard-rails-overview.md`](../../a_seed/os-agent-guard-rails-overview.md). The canonical implementation plan is [`plan/rpa_guidelines_plan/PLAN.md`](../../plan/rpa_guidelines_plan/PLAN.md).

## Package skeleton (issues #41–#50)

This folder contains a minimal Python package that can start with environment config, probe TypeDB health, manage deterministic Layer A database names for source registrations, apply Layer C and Layer B schema migrations, and run SQL registration flow checks.

### Package layout

```text
code/rpa_plugin_skill/
  .env.example
  .gitignore
  package.json                # npm-style scripts for dev/health/db/migrate/test/lint/format
  pyproject.toml              # Ruff baseline
  requirements.txt            # typedb-driver + ruff
  docs/
    sql_ddl_ingestion.md
    sql_to_typeql_transpiler.md
    manual_sql_registration_check.md
    openapi_ingestion.md
    openapi_to_typeql_mapping.md
    manual_api_registration_check.md
    rule_crud_semantics.md
    rule_composer_ui.md
    nl_to_horn_codegen.md
    guard_mcp_hot_reload.md
    sql_sync_worker.md
    rest_sync_worker.md
    sync_triggers.md
    mcp_server_scaffold.md
    guard_mcp_tools.md
    promise_mcp_tools.md
    correlation_trace.md
    task_crud_semantics.md
    task_composer_ui.md
    manual_task_composer_check.md
    task_plan_load.md
    manual_task_ready_schedule_check.md
    openclaw_schedule_contract.md
    task_run_orchestrator.md
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
    core/sql_ddl_ingest.py
    core/sql_to_typeql.py
    core/sql_registration_service.py
    core/openapi_ingest.py
    core/openapi_to_typeql.py
    core/openapi_registration_service.py
    core/rule_service.py
    core/rule_composer.py
    core/nl_rule_codegen.py
    core/guard_mcp_registry.py
    core/sql_sync_worker.py
    core/rest_sync_worker.py
    core/sync_trigger_service.py
    core/mcp_server.py
    core/promise_mcp_service.py
    core/task_service.py
    core/task_composer.py
    core/task_plan_loader.py
    core/task_schedule_service.py
    core/task_run_orchestrator.py
  examples/
    openclaw_cron_task_executor.example.json
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
  scripts/check_layer_b_contract.py
  tests/test_config.py
  tests/test_database_lifecycle.py
  tests/test_layer_c_migrations.py
  tests/test_layer_b_migrations.py
  tests/test_layer_c_store.py
  tests/test_sql_ddl_ingest.py
  tests/test_sql_to_typeql.py
  tests/test_sql_registration_service.py
  tests/test_openapi_ingest.py
  tests/test_openapi_to_typeql.py
  tests/test_openapi_registration_service.py
  tests/test_rule_service.py
  tests/test_rule_composer.py
  tests/test_nl_rule_codegen.py
  tests/test_guard_mcp_registry.py
  tests/test_sql_sync_worker.py
  tests/test_rest_sync_worker.py
  tests/test_sync_trigger_service.py
  tests/test_mcp_server.py
  tests/test_guard_mcp_invoke.py
  tests/test_promise_mcp_service.py
  tests/test_task_service.py
  tests/test_task_composer.py
  tests/test_task_plan_loader.py
  tests/test_task_schedule_service.py
  tests/test_task_run_orchestrator.py
  tests/fixtures/rule_ast/
  tests/golden/sql_to_typeql_sample.tql
  tests/golden/openapi_to_typeql_sample.tql
  dev/docker-compose.yml
  typeql_ci/
```

## SQL register flow (PLAN §5.1)

CLI now supports SQL registration workflow:

- provide SQL source name
- provide DDL source (inline, file path, or URL)
- provide SQL source URL label
- auto-generate and apply Layer A schema
- persist source metadata in Layer C
- set active registration context in Layer C setting `active_registration_id`
- list and switch active source context

Manual test guide: [`docs/manual_sql_registration_check.md`](docs/manual_sql_registration_check.md).

## Scripts (`package.json`)

From `code/rpa_plugin_skill`:

```bash
pip install -r requirements.txt
npm run dev
npm run health
npm run db:list
npm run db:register:example
npm run db:archive:example
npm run sql:register:example
npm run sql:list:sources
npm run api:register:example
npm run rule:list:example
npm run rule:compose:example
npm run task:compose:example
npm run task:prepare:example
npm run task:schedule:example
npm run task:schedule:list:example
npm run task:run:example
npm run rule:codegen:example
npm run rule:archive:example
npm run guard:mcp:list:example
npm run sync:sql:example
npm run sync:rest:example
npm run sync:status:example
npm run sync:task:finalize:example
npm run mcp:namespaces:example
npm run mcp:promise:tools:example
npm run mcp:guard:tools:example
npm run mcp:guard:introspect:example
npm run mcp:guard:invoke:example
npm run mcp:promise:declare:example
npm run mcp:promise:query:example
npm run mcp:promise:trace:example
npm run layerc:migrate
npm run layerb:migrate
npm run layerb:contract
npm run test
npm run lint
npm run format
```

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
| **4.2** SQL -> TypeQL schema transpiler | [#49](https://github.com/os-threat/os-agent-guard-rails/issues/49) (closed) |
| **4.3** SQL register flow | [#50](https://github.com/os-threat/os-agent-guard-rails/issues/50) (closed) |
| **5.1** OpenAPI fetch + parse | [#51](https://github.com/os-threat/os-agent-guard-rails/issues/51) (closed) |
| **5.2** OpenAPI -> TypeQL transpiler | [#52](https://github.com/os-threat/os-agent-guard-rails/issues/52) (closed) |
| **5.3** API register flow | [#53](https://github.com/os-threat/os-agent-guard-rails/issues/53) (closed) |
| **6.1** Rule list CRUD | [#54](https://github.com/os-threat/os-agent-guard-rails/issues/54) (closed) |
| **6.2** Rules composer UI | [#55](https://github.com/os-threat/os-agent-guard-rails/issues/55) (closed) |
| **6.3** NL -> Horn AST -> TypeQL fun codegen | [#56](https://github.com/os-threat/os-agent-guard-rails/issues/56) (closed) |
| **6.4** Guard MCP hot reload | [#57](https://github.com/os-threat/os-agent-guard-rails/issues/57) (closed) |
| **7.1** SQL sync worker | [#58](https://github.com/os-threat/os-agent-guard-rails/issues/58) (closed) |
| **7.2** REST sync worker | [#59](https://github.com/os-threat/os-agent-guard-rails/issues/59) (closed) |
| **7.3** Sync triggers + status | [#60](https://github.com/os-threat/os-agent-guard-rails/issues/60) (closed) |
| **8.1** MCP scaffold + namespaces | [#61](https://github.com/os-threat/os-agent-guard-rails/issues/61) (closed) |
| **8.2** Guard MCP dynamic tools | [#62](https://github.com/os-threat/os-agent-guard-rails/issues/62) (closed) |
| **9.1** Promise MCP tools | [#63](https://github.com/os-threat/os-agent-guard-rails/issues/63) (closed) |
| **9.2** Guard/assessment correlation | [#64](https://github.com/os-threat/os-agent-guard-rails/issues/64) (closed) |
| **10.1** Task list CRUD | [#65](https://github.com/os-threat/os-agent-guard-rails/issues/65) (closed) |
| **10.2** Task composer UI | [#66](https://github.com/os-threat/os-agent-guard-rails/issues/66) (closed) |
| **10.3** Task plan + Layer A load | [#67](https://github.com/os-threat/os-agent-guard-rails/issues/67) (closed) |
| **11.1** OpenClaw schedules | [#68](https://github.com/os-threat/os-agent-guard-rails/issues/68) (closed) |
| **11.2** Run orchestrator | [#69](https://github.com/os-threat/os-agent-guard-rails/issues/69) |




