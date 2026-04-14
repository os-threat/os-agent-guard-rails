# MCP server scaffold + namespaces (issue #61)

`PluginMcpServer` provides a long-lived in-process scaffold with two logical MCP namespaces:

- `guard` (Layer A decision functions, hot-reload capable)
- `promise` (Layer B promise graph operations)

## Namespace listing

Clients can list namespaces:

```bash
python -m rpa_plugin_skill --mcp-list-namespaces
```

Expected output includes both: `guard,promise`.

## Tool listing

List Promise tools:

```bash
python -m rpa_plugin_skill --mcp-list-tools-namespace promise
```

List Guard tools for a source:

```bash
python -m rpa_plugin_skill --mcp-guard-source sql-medical-alpha --mcp-list-tools-namespace guard
```

Guard tools are projected from `GuardMcpRegistry` and therefore support hot refresh as rules evolve.

