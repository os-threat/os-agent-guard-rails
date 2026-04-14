# OpenClaw schedule/executor contract (issue #68)

The plugin persists schedule intent in Layer C and delegates execution to OpenClaw cron/service.
The plugin does **not** run an OS-level scheduler.

## Layer C schedule intent

Persist via CLI:

`--task-schedule-upsert --task-source <REG_ID> --task-id <TASK_ID> --task-schedule-id <SCHED_ID> --task-schedule-mode cron --task-cron "<expr>" --task-openclaw-job-ref "<job-ref>" --task-schedule-enabled`

Stored fields:

- `gr_schedule_id`
- `gr_schedule_mode`
- `gr_cron_expression`
- `gr_openclaw_job_ref`
- `gr_schedule_enabled`
- relation: `gr_task_schedule_binding(task, schedule)`

## Execution ownership

- **OpenClaw cron/service/skill owns timing and retries**
- Plugin exposes task-run contract and idempotent execution semantics
- OpenClaw passes `registration_id` + `task_id` so plugin targets correct Layer A DB mapping

## Run payload contract

Recommended payload shape (MCP or HTTP executor wrapper):

```json
{
  "registration_id": "sql-medical-alpha",
  "task_id": "task-001",
  "task_name": "Client extraction",
  "task_description": "Extract clients and validate status before review",
  "trigger_source": "openclaw-cron"
}
```

## Auth + idempotency

- **Auth**: bearer token from OpenClaw secret store (`Authorization: Bearer <token>`)
- **Idempotency**: send deterministic `Idempotency-Key` header:
  - `registration_id:task_id:scheduled_at`
- Plugin-side task processing should treat duplicate idempotency keys as safe retries.

## Example config

See:

- `examples/openclaw_cron_task_executor.example.json`
