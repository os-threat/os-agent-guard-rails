# Guard MCP tools + introspection (issue #62)

Guard MCP dynamically exposes **one tool per TypeQL `fun`** in the active registration's Layer A schema.

## Dynamic tool registry contract

- Source of truth: Layer C rule metadata (`gr_rule_definition` + source binding)
- Tool identity: function label extracted from `gr_rule_typeql_fun`
- Namespace projection: `guard.<fun_label>`
- Hot update: `set_guard_source(...)` + registry refresh; no process restart required

## Invocation behavior

`PluginMcpServer.invoke_guard_tool(tool, subject_key)`:

1. Resolves active registration -> Layer A DB.
2. Executes function in a **read transaction**:
   - `match`
   - `let $decision in <fun>("subject_key");`
   - `fetch {"decision": $decision};`
3. Returns decision plus `data-trace` payload.

No write transaction is used for guard invocation.

## Data-trace inputs

Each invocation/introspection includes:

- `rule_id` (from Layer C rule metadata)
- `schema_hash` (SHA-256 hash of active Layer A schema string)
- `sync_watermark` (currently `sync:<registration_id>:last_sync_time` from Layer C settings)

## CLI checks

```bash
python -m rpa_plugin_skill --mcp-guard-source sql-medical-alpha --mcp-list-tools-namespace guard
python -m rpa_plugin_skill --mcp-guard-source sql-medical-alpha --mcp-guard-introspect-tool guard.gr_guard_fp_r01
python -m rpa_plugin_skill --mcp-guard-source sql-medical-alpha --mcp-guard-invoke-tool guard.gr_guard_fp_r01 --mcp-guard-subject-key C-ALLOW
```
