# Promise Graph MCP tools (issue #63)

Promise MCP keeps a **static tool surface** with dynamic data in Layer B.

## Static tool set

- `promise.declare`
- `promise.chain`
- `promise.assess`
- `promise.query`

This surface is stable while records in Layer B evolve per run/session/task.

## Tool behavior and transaction usage

Per `skills/typedb/SKILL.md`:

- Mutations (`declare`, `chain`, `assess`) run in **write** transactions.
- Reads (`query`) run in **read** transactions.

## Contract test coverage

`tests/test_promise_mcp_service.py` validates:

1. declare a promise and participants
2. chain promise to task
3. assess promise outcome
4. query promise summary with assessment/action counts
5. query by correlation id for dashboard trace linkage

## CLI examples

```bash
python -m rpa_plugin_skill --mcp-promise-invoke-tool promise.declare --mcp-promise-payload-json "{\"creator_id\":\"agent-a\",\"target_id\":\"agent-b\",\"promise_id\":\"promise-001\",\"promise_title\":\"Guarded run\"}"
python -m rpa_plugin_skill --mcp-promise-invoke-tool promise.query --mcp-promise-payload-json "{\"promise_id\":\"promise-001\"}"
```
