# Task run orchestrator (issue #69)

Implements PLAN §5.6 state machine for OpenClaw-invoked runs:

```text
Sync → Precheck (Guard MCP) → Deny (assessment + appeal)  or  Act (RPA + Promise log) → Review
```

## Entry point

`rpa_plugin_skill.core.task_run_orchestrator.run_task_orchestration`

Parameters:

- `registration_id`, `task_id` — Layer C task must exist with a non-empty `extract_plan_ref`
- `guard_tool` — e.g. `guard.gr_guard_fp_r99`
- `subject_key` — passed into the guard `fun`
- `agent_id` / `agent_name` — Promise graph actor labels

## Guard convention

Matches Guard MCP integration tests: **`decision is True` ⇒ precheck passed** (proceed to Act). `False` or `None` ⇒ Deny path (blocked).

## Deny path

- `promise.declare` for the run
- `promise.assess` with `outcome=deny`, data trace fields, and `correlation_id` for dashboard / appeal trace (`promise.query` by correlation)

## Act path

- `promise.declare` (accepted)
- `promise.chain` linking the Layer C task id
- Stub RPA step labels in `TaskRunResult.rpa_steps` (real RPA replaces this later)
- `promise.assess` with `outcome=allow`

## CLI

```bash
python -m rpa_plugin_skill --task-run \
  --task-source <REG_ID> \
  --task-id <TASK_ID> \
  --task-guard-tool guard.gr_guard_fp_r99 \
  --task-guard-subject-key ALLOW
```

Optional: `--task-run-agent-id`, `--task-run-agent-name`.

Output: `[rpa_plugin_skill] TASK_RUN ...` with JSON payload (`path`, `phases_completed`, `sync_rows_loaded`, promise/correlation ids, `review` hints).

## Resync

`resync_task_layer_a_from_plan` re-runs the JSON plan produced by `prepare_task_for_schedule` (SQL or API), using the current `source_url` from Layer C.
