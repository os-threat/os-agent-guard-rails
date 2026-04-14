# Task CRUD semantics (issue #65)

Layer C task management stores task definitions scoped to a registered source.

## CRUD operations

- **Create / Update**: `upsert_task(...)`
  - Replaces an existing `gr_task_definition` with the same `gr_task_id`
  - Rebinds the task to `gr_registered_source` via `gr_source_task_binding`
- **Read**: `fetch_tasks_for_source(registration_id)`
  - Returns only tasks bound to that registration id
- **Status update**: `set_task_status(task_id, status)`
  - Rewrites `gr_task_status` on the existing task
- **Delete**: `delete_task(registration_id, task_id)`
  - Removes source-task binding and task entity

## Service wrapper

`rpa_plugin_skill.core.task_service` provides UI-facing helpers:

- `upsert_task_for_source(...)`
- `list_tasks_for_source(...)`
- `set_task_status_for_source(...)`
- `delete_task_for_source(...)`

These helpers keep Task Composer/Task Manager logic constrained to Layer C for issue #65 scope.
