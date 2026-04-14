# Guard MCP hot reload (issue #57)

The Guard MCP surface is backed by `GuardMcpRegistry` in
`rpa_plugin_skill/core/guard_mcp_registry.py`.

## Behavior

- After Layer C rules change (and optionally Layer A `fun` schema updates), call
  `GuardMcpRegistry.refresh(registration_id)` in the **same process** that serves MCP.
- The registry rebuilds the tool list from Layer C (`gr_rule_definition` + binding), extracting
  each tool name from the `fun` label inside `gr_rule_typeql_fun`.
- **No MCP host process restart** is required; only `refresh()` must run after commits.

## Thread safety and in-flight calls

- All reads and writes to the in-memory tool map use one `threading.RLock` shared by
  `refresh`, `list_tools`, `list_tool_names`, and `get_tool`.
- `refresh` replaces the entire `dict` in one critical section, so list/get see a consistent
  snapshot for that generation.
- **In-flight MCP tool calls** that started before `refresh` may still execute against the
  previous TypeDB schema until their transaction completes; new calls after `refresh` should use
  the updated tool list. For strict alignment, optionally gate `refresh` behind a generation
  counter and have callers re-list tools after rule edits.
- Avoid holding the lock while performing TypeDB I/O inside future invoke handlers; the registry
  only locks around map updates and short reads.

## CLI

```bash
python -m rpa_plugin_skill --guard-mcp-refresh --guard-mcp-source sql-medical-alpha
python -m rpa_plugin_skill --guard-mcp-list-tools --guard-mcp-source sql-medical-alpha
```
