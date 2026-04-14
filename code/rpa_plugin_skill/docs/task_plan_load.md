# Task description to extract plan + Layer A load (issue #67)

Implements PLAN §5.5 background behavior:

- convert task description into SQL/API extract plan
- execute load in Layer A via write transaction path from sync workers
- persist task with status `ready` for scheduling
- return preview counts/rows

## Entry point

`rpa_plugin_skill.core.task_plan_loader.prepare_task_for_schedule(...)`

Inputs:

- `registration_id`
- `task_id`
- `task_name`
- `task_description`

Flow:

1. Read registration metadata from Layer C (`source_kind`, `source_url`).
2. Reuse Task Composer schema highlights to infer target table/entity.
3. Build SQL or REST sync plan.
4. Execute sync worker (Layer A writes).
5. Persist task in Layer C with:
   - `gr_task_status = "ready"`
   - `gr_extract_plan_ref = <plan summary json>`
6. Return preview payload including loaded row count.

## CLI

`--task-prepare-load --task-source <REG_ID> --task-id <TASK_ID> --task-name "<name>" --task-description "<text>"`

Output includes:

- `TASK_READY_TO_SCHEDULE`
- `status=ready`
- `rows_loaded=<count>`
- plan summary JSON
